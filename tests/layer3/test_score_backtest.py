from layer3 import spine
from layer3.backtest.score_backtest import combined_score_backtest, _combined


def test_combined_helper():
    w = {"return_potential": 0.5, "downside_safety": 0.5, "liquidity": 0.0}
    # available components renormalize over their weights
    assert abs(_combined({"return_potential": 80, "downside_safety": 60}, w) - 70.0) < 1e-6
    assert _combined({"liquidity": 50}, w) is None        # only zero-weight present -> None


def test_combined_score_backtest_runs():
    df = spine.load_substrate()
    res, verdict = combined_score_backtest(df, horizon="3y")
    assert {"group", "N", "top_median_alpha_%", "lift_vs_all_pp"}.issubset(res.columns)
    assert isinstance(verdict, str) and verdict
    # ALL group present, top quintile is ~20% of the set
    allrow = res[res.group == "ALL"].iloc[0]
    assert 0 < allrow["N_top_quintile"] < allrow["N"]
