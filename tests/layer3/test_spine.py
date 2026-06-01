import pandas as pd
import pytest
from layer3 import spine, config


@pytest.fixture(scope="module")
def df():
    return spine.load_substrate()


def test_load_equity_only_default(df):
    assert len(df) > 2000
    assert set(df["instrument_type"].unique()) == {"equity"}
    for col in ["isin", "type", "cohort", "outcome_class", "alpha_1y",
                "alpha_sc_1y", "return_from_listing_1y", "data_quality_tier"]:
        assert col in df.columns


def test_load_options():
    assert spine.load_substrate(equity_only=False)["instrument_type"].nunique() >= 2
    assert "low" not in set(spine.load_substrate(exclude_low_quality=True)["data_quality_tier"])


def test_segment_hard_split(df):
    s = spine.segment(df, segment="SME", cohort="boom")
    assert (s["type"] == "SME").all() and (s["cohort"] == "boom").all()
    assert 0 < len(s) < len(df)


def test_investable(df):
    assert (spine.investable(df)["liquidity_flag"] == "ok").all()


def test_maturity_gated(df):
    g = spine.maturity_gated(df, "5y")
    assert g["alpha_5y"].notna().all() and len(g) <= len(df)


def test_alpha_benchmarks(df):
    assert spine.alpha_series(df, "1y", "nifty").notna().sum() > 1000
    assert spine.alpha_series(df, "1y", "smallcap").notna().sum() > 500   # 2017+ only
    # listing return is RAW (exists, separate from alpha)
    assert spine.listing_return(df, "1y").notna().sum() > 500


def test_benchmark_policy():
    assert spine.benchmark_for("micro") == "smallcap"
    assert spine.benchmark_for("large") == "nifty"


def test_distribution_shape_and_tier(df):
    d = spine.distribution(df["alpha_1y"])
    assert set(["n", "p10", "p25", "median", "p75", "p90", "mean", "tier"]).issubset(d)
    assert d["tier"] == "tradable"
    assert spine.distribution(pd.Series([0.1, 0.2, 0.3]))["tier"] == "insufficient"


def test_wilson_and_proportion():
    lo, hi = spine.wilson_ci(50, 100)
    assert 0.39 < lo < 0.5 < hi < 0.61
    p = spine.proportion(pd.Series([True, False, True, True]))
    assert p["k"] == 3 and p["n"] == 4 and abs(p["rate"] - 0.75) < 1e-9


def test_terminal_state_and_band(df):
    t = spine.terminal_state(df)
    assert len(t) == len(df)
    assert set(t.unique()).issubset({"alive", "wipeout", "payout", "alive_delisted_unknown"})
    band = spine.wipeout_band(df)
    # band is a real band: upper >= lower, and lower is ~the wipeout-class count
    assert band["wipeout_upper"] >= band["wipeout_lower"] >= 140


def test_guarded_blocks_subfloor():
    assert "insufficient" in spine.guarded(0.5, 3)
    assert spine.guarded(0.5, 50) == "0.50"
