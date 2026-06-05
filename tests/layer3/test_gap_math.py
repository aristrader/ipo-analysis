"""Showdown P2 — direct unit tests for the previously-untested result-critical math
(audit: docs/research/showdown_audit.md). Synthetic frames, hand-computed expectations.

Guards: MIN_N_TRADABLE=30, MIN_N_HINT=10 — frames are sized 40 to clear both.
maturity_gated() keys on alpha_<h> being non-null, so every frame carries it.
"""
import numpy as np
import pandas as pd
import pytest

from layer3 import spine
from layer3.backtest import engine
from layer3.predictor import analogs, scorecard


def _rep(vals, n):
    """Tile per-case values to n rows (n must be len(vals)*k)."""
    k = n // len(vals)
    return [v for v in vals for _ in range(k)]


# ------------------------------------------------------- combined_exit_strategy
def test_combined_exit_tp_sl_ordering_hand_computed():
    # five cases x8 = 40 rows (>= MIN_N_TRADABLE)
    # (mfe, mae, end, day_peak, day_trough) -> expected capture under tp=.5, sl=.3
    cases = [
        (0.6, -0.1, 0.20, 30, 60),   # only TP        -> +.5
        (0.2, -0.5, -0.20, 30, 10),  # only SL        -> -.3
        (0.8, -0.4, 0.10, 10, 50),   # both, peak 1st -> +.5
        (0.8, -0.4, -0.10, 50, 10),  # both, trough 1st-> -.3
        (0.2, -0.1, 0.05, 20, 40),   # neither        -> end .05
    ]
    n = 40
    g = pd.DataFrame({
        "mfe_1y": _rep([c[0] for c in cases], n), "mae_1y": _rep([c[1] for c in cases], n),
        "return_from_issue_1y": _rep([c[2] for c in cases], n),
        "days_to_mfe_1y": _rep([c[3] for c in cases], n), "days_to_mae_1y": _rep([c[4] for c in cases], n),
    })
    r = spine.combined_exit_strategy(g, entry="issue", horizon="1y", tp=0.50, sl=0.30)
    assert r["n"] == 40
    assert r["pct_took_profit"] == 40.0      # cases 1 & 3
    assert r["pct_stopped_out"] == 40.0      # cases 2 & 4
    assert r["pct_held_to_end"] == 20.0      # case 5
    assert r["rule_mean_%"] == pytest.approx(9.0)        # (.5-.3+.5-.3+.05)/5
    assert r["rule_median_%"] == pytest.approx(5.0)      # middle of [-.3 x16, .05 x8, .5 x16]
    assert r["buy_hold_mean_%"] == pytest.approx(1.0)    # (.2-.2+.1-.1+.05)/5
    assert r["beats_hold_mean"] is True
    assert r["n_ambiguous_order"] == 0


# ------------------------------------------------------------ basket_dispersion
def test_basket_dispersion_top_slice_carries_the_mean():
    g = pd.DataFrame({"return_from_listing_1y": [-0.10] * 36 + [9.0] * 4})
    r = spine.basket_dispersion(g, horizon="1y", entry="listing", top_frac=0.05)
    assert r["n"] == 40
    assert r["mean_%"] == pytest.approx(81.0)            # (36*-0.1 + 4*9)/40
    assert r["median_%"] == pytest.approx(-10.0)         # the typical name LOSES
    assert r["top_5%_mean_%"] == pytest.approx(900.0)    # k=2 biggest
    assert r["mean_ex_top_%"] == pytest.approx(37.9)     # (36*-0.1 + 2*9)/38
    assert r["pct_positive"] == pytest.approx(0.1)       # 4/40


# ------------------------------------------------------------ allotment_capture
def test_allotment_capture_inversion():
    g = pd.DataFrame({
        "sub_total_x": [2.0] * 12 + [20.0] * 12,
        "adj_listing_gain_open": [0.10] * 12 + [0.40] * 12,
        "listing_metrics_status": ["ok"] * 24,
    })
    r = spine.allotment_capture(g)
    b = {row["sub_bucket"]: row for row in r["buckets"]}
    lo, hi = b["1-5x"], b["15-50x"]
    assert lo["median_allot_odds_%"] == 50.0 and hi["median_allot_odds_%"] == 5.0
    assert lo["median_pop_%"] == 10.0 and hi["median_pop_%"] == 40.0
    # THE flip trap: 4x the pop, LESS capture per application
    assert lo["E_capture_per_application_%"] == pytest.approx(5.0)   # 0.5 * 10%
    assert hi["E_capture_per_application_%"] == pytest.approx(2.0)   # 0.05 * 40%


# ----------------------------------------------------------------- average_down
def test_average_down_blend_is_arithmetic_not_recovery():
    g = pd.DataFrame({
        "mae_1y": [-0.40] * 12 + [-0.05] * 28,
        "return_from_issue_1y": [0.10] * 12 + [0.0] * 28,
        "mfe_1y": [0.5] * 40,
    })
    r = spine.average_down(g, entry="issue", horizon="1y", dips=(0.30, 0.50))
    d30 = r["ladder"][0]
    assert d30["dipper_n"] == 12
    assert d30["hold_median_%"] == pytest.approx(10.0)
    assert d30["blended_median_%"] == pytest.approx(29.4)    # 1.1/0.85 - 1
    assert d30["tranche2_median_%"] == pytest.approx(57.1)   # 1.1/0.70 - 1
    assert d30["pct_recovered_above_entry"] == 100.0
    assert r["ladder"][1].get("insufficient") is True        # nobody dipped -50%


# -------------------------------------------------------------------- lifecycle
def test_lifecycle_timing_quantiles():
    g = pd.DataFrame({"days_to_mfe_1y": [80] * 40, "days_to_mae_1y": [40] * 40,
                      "days_to_breakeven_1y": [5] * 40})
    r = spine.lifecycle(g, horizon="1y")
    assert (r["median_days_to_peak"], r["median_days_to_trough"], r["median_days_to_breakeven"]) == (80, 40, 5)
    assert r["pct_peak_in_first_quarter"] == 100.0           # 80 <= 90


# ---------------------------------------------------------- partial_exit_strategy
def test_partial_exit_blends_half_at_target():
    g = pd.DataFrame({"mfe_1y": [0.6] * 40, "return_from_issue_1y": [0.2] * 40})
    r = spine.partial_exit_strategy(g, entry="issue", horizon="1y", frac=0.5)
    ladder = {row["sell_50%_at"]: row for row in r["ladder"]}
    assert r["hold_median_%"] == pytest.approx(20.0)
    assert ladder["+50%"]["median_captured_%"] == pytest.approx(35.0)   # .5*.5 + .5*.2
    assert ladder["+100%"]["median_captured_%"] == pytest.approx(20.0)  # never reached -> hold
    assert ladder["+50%"]["pct_reached"] == 100.0


# --------------------------------------------------------- bootstrap_median_ci
def test_bootstrap_median_ci_deterministic_constant_series():
    r = spine.bootstrap_median_ci(pd.Series([0.2] * 40))
    assert r["median"] == pytest.approx(0.2)
    assert r["lo"] == pytest.approx(0.2) and r["hi"] == pytest.approx(0.2)
    assert r["p_positive"] == 1.0
    assert spine.bootstrap_median_ci(pd.Series([0.1] * 5))["median"] is None  # < MIN_N_HINT


def test_bootstrap_reports_median_not_mean():
    # skewed series: median 1.0, mean 3.0 — a median->mean regression must fail here
    # (mutation survivor fix: the constant-series test couldn't tell them apart)
    r = spine.bootstrap_median_ci(pd.Series([1.0, 1.0, 1.0, 9.0] * 10))
    assert r["median"] == pytest.approx(1.0)


def test_wipeout_safety_unknown_is_none_not_unsafe():
    # no risk inputs -> score must be None (excluded from the blend), NEVER 0/"max risk"
    # (mutation survivor fix: the unknown!=unsafe contract had no direct test)
    c = scorecard.wipeout_safety({}, df=_cohort40())
    assert c["score"] is None
    assert c.get("n_checked", 0) == 0 or c.get("n", 0) == 0


# --------------------------------------------------------------- outcome_profile
def test_outcome_profile_hand_computed():
    g = pd.DataFrame({
        "alpha_3y": [0.10] * 40,                                   # gates maturity + median alpha
        "return_from_issue_3y": [0.30] * 28 + [-0.20] * 12,        # 30% below issue
        "max_gain_pct": [1.5] * 20 + [0.2] * 20,                   # 50% ever-2x
        "max_drawdown_pct": [-0.30] * 40,
        "all_time_low": [80.0] * 40, "issue_price_adj": [100.0] * 40,
        "outcome_class": ["flat"] * 40, "delisted": [False] * 40, "delist_reason": [""] * 40,
    })
    r = spine.outcome_profile(g, horizon="3y")
    assert r["n"] == 40 and r["n_matured_3y"] == 40
    assert r["median_alpha_3y_%"] == pytest.approx(10.0)
    assert r["pct_ever_2x"] == pytest.approx(50.0)
    assert r["pct_ever_5x"] == pytest.approx(0.0)
    assert r["median_trough_from_issue_%"] == pytest.approx(-20.0)
    assert r["pct_below_issue_3y_%"] == pytest.approx(30.0)
    assert r["wipeout_lower_%"] == pytest.approx(0.0)


# ----------------------------------------------------------- backtest._metrics
def test_engine_metrics_aggregation():
    res = pd.DataFrame({"alpha": [0.1, 0.2, -0.1, 0.4], "ret": [9, 9, 9, 9]})
    m = engine._metrics(res, kind="secondary")          # secondary -> alpha column
    assert m["measure"] == "alpha" and m["N"] == 4
    assert m["mean_%"] == pytest.approx(15.0)
    assert m["median_%"] == pytest.approx(15.0)
    assert m["win_rate_%"] == 75.0
    assert m["worst_%"] == pytest.approx(-10.0)
    m2 = engine._metrics(pd.DataFrame({"alpha": [], "ret": []}), kind="secondary")
    assert m2["N"] == 0


# ---------------------------------------------------------- analogs sector/ranges
def test_resolve_sector_exact_alias_substring_and_miss():
    df = pd.DataFrame({"broad_sector": ["Financial Services", "Healthcare"] * 6})
    assert analogs.resolve_sector("Healthcare", df) == ("Healthcare", None)
    got, note = analogs.resolve_sector("pharma", df)
    assert got == "Healthcare" and "interpreted" in note
    got, note = analogs.resolve_sector("financial", df)
    assert got == "Financial Services"
    got, note = analogs.resolve_sector("zzz-nonsense", df)
    assert got is None and "not recognized" in note


def test_robust_ranges_p10_p90_and_min_count():
    df = pd.DataFrame({"a": list(range(12)), "b": [1, 2, 3] + [None] * 9})   # b: too few non-null (<10)
    r = analogs.robust_ranges(df, ["a", "b"])
    assert r["a"] == pytest.approx(8.8)                          # q90(9.9) - q10(1.1)
    assert "b" not in r


# ------------------------------------------------------- scorecard component math
def _cohort40():
    return pd.DataFrame({
        "alpha_1y": [0.05] * 40,
        "alpha_3y": [0.05] * 40,
        "listing_metrics_status": ["ok"] * 40,
        "return_from_listing_1y": [1.5] * 10 + [0.0] * 30,       # 25% endpoint-2x
        "mfe_lst_1y": [1.6] * 10 + [1.2] * 10 + [0.0] * 20,      # 50% ever-2x
        "return_from_issue_3y": [-0.20] * 12 + [0.30] * 28,      # 30% below issue
        "max_drawdown_pct": [-0.60] * 8 + [-0.20] * 32,          # 20% deep drawdown
        "liquidity_flag": ["ok"] * 40,
        "outcome_class": ["flat"] * 40, "delisted": [False] * 40, "delist_reason": [""] * 40,
    })


def test_multibagger_odds_score_and_timing_tax():
    c = scorecard.multibagger_odds(_cohort40(), "1y")
    assert c["pct_2x_from_listing"] == pytest.approx(0.25)
    assert c["pct_ever_2x"] == pytest.approx(0.50)               # the timing tax = the gap
    assert c["score"] == pytest.approx(62.5)                     # clip(0.25/0.40*100)


def test_tradeable_upside_reach_scaled():
    c = scorecard.tradeable_upside(_cohort40(), "1y", entry="listing", level=0.30)
    assert c["pct_reached"] == pytest.approx(0.50)               # 20/40 touched +30%
    assert c["score"] == pytest.approx(50.0)
    assert c["median_endpoint"] == pytest.approx(0.0)


def test_downside_safety_risk_blend():
    c = scorecard.downside_safety(_cohort40())
    # risk = .5*0 (no wipeouts) + .3*.3 (below issue) + .2*.2 (deep dd) = .13
    # base = 100*(1 - .13/.6) = 78.333; no liquidity haircut (all 'ok')
    assert c["liquidity_haircut"] == 1.0
    assert c["score"] == pytest.approx(78.3, abs=0.05)


def test_return_potential_squash_of_median_alpha():
    c = scorecard.return_potential(_cohort40(), "1y")
    assert c["median_alpha"] == pytest.approx(0.05)
    # _squash(0.05, 0.5) = 50 + 50*tanh(0.1)
    assert c["score"] == pytest.approx(50 + 50 * np.tanh(0.1), abs=0.01)
