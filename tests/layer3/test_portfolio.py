"""Portfolio sim tests (spec 2026-06-08-portfolio-sim-design.md): ₹1L math, survivorship,
allotment haircut applied to allottee-only, mode never pooled, per-stock 3-series shape."""
import pandas as pd
import pytest

from layer3 import portfolio as P


def test_growth_one_position_no_split():
    # entry 100 -> now 150, ₹1L -> ₹1.5L (allottee, before haircut)
    v = P._position_value(entry=100.0, exit_px=150.0, capital=100000.0)
    assert abs(v - 150000.0) < 1.0


def test_wipeout_position_is_zero_not_dropped():
    v = P._position_value(entry=100.0, exit_px=0.0, capital=100000.0)
    assert v == 0.0                       # dead money = ₹0, still a number (counts in aggregate)


def test_full_capital_no_haircut_both_lenses():
    # owner call: full ₹1L invested, no idle-cash haircut, both entry lenses
    assert P._position_value(100.0, 150.0, 100000.0) == 150000.0
    assert P._position_value(50.0, 100.0, 100000.0) == 200000.0      # entry 50 -> 100 = 2x


def test_mode_split_never_pools(monkeypatch):
    df = pd.DataFrame([
        {"mode": "historical_sim", "mult": 2.0},
        {"mode": "live", "mult": 0.5},
    ])
    g = df.groupby("mode")["mult"].median().to_dict()
    assert g["historical_sim"] == 2.0 and g["live"] == 0.5   # contract: keyed by mode


def test_exit_price_returns_date_for_benchmark_anchoring(tmp_path):
    # P0 fix: _exit_price returns (value, date) so the Nifty leg can match the holding period
    import pandas as pd
    d = pd.bdate_range("2021-01-01", periods=50)
    pd.DataFrame({"date": d.strftime("%Y-%m-%d"), "open": 100, "high": 100, "low": 100,
                  "close": 120.0, "volume": 1}).to_csv(tmp_path / "INEDEL01.csv", index=False)
    val, dt = P._exit_price("INEDEL01", {"delisted": "False"}, prices_root=str(tmp_path))
    assert val == 120.0 and str(dt.date()) == "2021-03-11"   # last date in the file, not today
    # wipeout keeps ₹0 + its terminal date
    val2, dt2 = P._exit_price("INEDEL01", {"delisted": "True", "outcome_class": "wipeout"},
                              prices_root=str(tmp_path))
    assert val2 == 0.0 and dt2 is not None


def test_summary_matches_baskets():
    # P0 fix: a position missing nifty_val must not skew mult vs nifty_mult (same basket)
    import pandas as pd
    pos = pd.DataFrame([
        {"mode": "x", "allottee_val": 200000.0, "secondary_val": 150000.0, "nifty_val": 110000.0},
        {"mode": "x", "allottee_val": 100000.0, "secondary_val": 100000.0, "nifty_val": None},
    ])
    s = P.summary(pos)["x/secondary"]
    assert s["n"] == 1                            # only the row with BOTH values counts
    assert s["mult"] == 1.5 and s["nifty_mult"] == 1.1


def test_summary_outlier_decomposition():
    # mean is one-winner-driven; median/drop-top must expose it (T1)
    import pandas as pd
    pos = pd.DataFrame([{"mode": "m", "secondary_val": v, "allottee_val": v, "nifty_val": 110000.0}
                        for v in [90000, 100000, 110000, 120000, 2500000]])  # one 25x
    s = P.summary(pos)["m/secondary"]
    assert s["mult"] > 5            # mean dragged up by the 25x
    assert s["median_mult"] < 1.2   # typical position ~flat
    assert s["mult_drop_top1"] < s["mult"]      # dropping the winner collapses the mean
    assert 0 < s["top3_share"] <= 1


def test_bootstrap_ci_brackets_mean():
    import pandas as pd
    pos = pd.DataFrame([{"mode": "m", "secondary_val": v} for v in
                        [80000, 100000, 120000, 150000, 200000] * 4])
    ci = P.bootstrap_ci(pos, "secondary_val", "m", b=500)
    assert ci is not None and ci[0] < ci[1]
    assert P.bootstrap_ci(pos.head(3), "secondary_val", "m") is None   # <10 -> None


def test_attribution_orders_by_pnl():
    import pandas as pd
    pos = pd.DataFrame([
        {"mode": "historical_sim", "name": "Win", "type": "MB", "call_date": "2021-01-01",
         "secondary_val": 300000.0},
        {"mode": "historical_sim", "name": "Lose", "type": "SME", "call_date": "2021-02-01",
         "secondary_val": 20000.0}])
    a = P.attribution(pos)
    assert a["best"][0]["name"] == "Win" and a["worst"][0]["name"] == "Lose"


def test_growth_of_1l_three_series_start_at_capital():
    out = P.growth_of_1l("INE14OX01013", capital=100000.0)
    if out is None or out.empty:
        pytest.skip("no price data for sample isin in this env")
    series = set(out["series"].unique())
    assert {"at-IPO (if allotted)", "at-listing", "Nifty"} <= series
    # each series' first point ~= capital
    for s, g in out.groupby("series"):
        first = g.sort_values("date").iloc[0]["value"]
        assert abs(first - 100000.0) < 100000.0 * 0.5     # starts in the ₹1L neighborhood
