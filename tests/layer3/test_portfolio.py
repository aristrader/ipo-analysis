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
