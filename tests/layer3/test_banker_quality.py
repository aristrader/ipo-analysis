"""A1c — banker-quality measure: PIT correctness contract (synthetic frames, deterministic).

These pin the load-bearing rules from the spec (docs/superpowers/specs/2026-06-11-a1c-banker-quality-design.md):
maturity-gating (a prior's horizon counts only once it has matured by the scoring date), confidence-shrinkage
toward the PIT segment base, size+recency weighting, segment-specificity, and strict point-in-time (no peeking
at priors that listed — or matured — after the scored IPO). No ML; all transparent formulas.
"""
import numpy as np
import pandas as pd
import pytest

from layer3.predictor import banker_quality as bq


# ---- weighting ------------------------------------------------------------------------------
def test_weight_favours_bigger_and_more_recent():
    big_recent = bq._weight(500.0, age_years=0.0)
    small_recent = bq._weight(5.0, age_years=0.0)
    big_old = bq._weight(500.0, age_years=6.0)  # 2 half-lives at H=3
    assert big_recent > small_recent          # bigger issue weighs more
    assert big_recent > big_old               # more recent weighs more
    assert big_old == pytest.approx(big_recent * 0.25, rel=1e-6)  # 6y / 3y half-life = 0.25


# ---- maturity gating ------------------------------------------------------------------------
def test_tapered_alpha_uses_only_matured_horizons():
    # a prior 100 days old: only the 3m horizon (91d) has matured -> tapered alpha == its 3m alpha
    prior = {"alpha_3m": 0.20, "alpha_6m": 0.50, "alpha_1y": 1.0, "alpha_3y": 2.0}
    val, any_matured = bq._tapered_alpha(prior, age_days=100)
    assert any_matured is True
    assert val == pytest.approx(0.20)          # 6m/1y/3y dropped, 3m renormalized to weight 1


def test_tapered_alpha_none_when_nothing_matured():
    prior = {"alpha_3m": 0.20, "alpha_6m": 0.50, "alpha_1y": 1.0, "alpha_3y": 2.0}
    val, any_matured = bq._tapered_alpha(prior, age_days=30)   # <91d, nothing matured
    assert any_matured is False and val is None


def test_tapered_alpha_blends_matured_horizons_by_taper():
    # 200 days old -> 3m + 6m matured (182d), 1y/3y not. Blend by taper 0.45/0.30 renormalized.
    prior = {"alpha_3m": 0.10, "alpha_6m": 0.40, "alpha_1y": 9.0, "alpha_3y": 9.0}
    val, _ = bq._tapered_alpha(prior, age_days=200)
    exp = (0.45 * 0.10 + 0.30 * 0.40) / (0.45 + 0.30)
    assert val == pytest.approx(exp)


# ---- shrinkage ------------------------------------------------------------------------------
def test_shrink_pulls_thin_record_toward_base():
    # tiny evidence mass -> stays near the segment base, not the raw banker number
    near_base = bq._shrink(raw=1.0, W=1.0, mu_seg=0.0, k=5.0)
    assert near_base == pytest.approx(1.0 / 6.0)
    # heavy evidence mass -> trusts the banker's own record
    near_raw = bq._shrink(raw=1.0, W=100.0, mu_seg=0.0, k=5.0)
    assert near_raw > 0.9


# ---- the PIT series: segment-specific, point-in-time, shrink-to-base ------------------------
def _frame(rows):
    """rows = (banker, listing 'YYYY-MM-DD', type, issue_size_cr, a3m,a6m,a1y,a3y)."""
    return pd.DataFrame([{
        "isin": f"X{i:05d}", "lead_manager": b, "listing_date": ld, "type": t,
        "issue_size_cr": sz, "alpha_3m": a3, "alpha_6m": a6, "alpha_1y": a1, "alpha_3y": a3y,
    } for i, (b, ld, t, sz, a3, a6, a1, a3y) in enumerate(rows)])


def test_series_is_segment_specific_and_point_in_time():
    # Banker "B" has 3 SME priors (all matured, +0.5 alpha) before 2024, plus a MB prior and a
    # FUTURE prior that must both be ignored when scoring an SME IPO listing 2024-01-01.
    rows = [("B", "2021-01-01", "SME", 50, 0.5, 0.5, 0.5, 0.5),
            ("B", "2021-02-01", "SME", 50, 0.5, 0.5, 0.5, 0.5),
            ("B", "2021-03-01", "SME", 50, 0.5, 0.5, 0.5, 0.5),
            ("B", "2021-04-01", "MB", 50, -9.0, -9.0, -9.0, -9.0),    # wrong segment -> ignored
            ("B", "2025-01-01", "SME", 50, -9.0, -9.0, -9.0, -9.0),   # future -> ignored
            ("B", "2024-01-01", "SME", 50, 0.0, 0.0, 0.0, 0.0)]       # the row we score
    df = _frame(rows)
    s = bq.banker_quality_series(df, df, target="alpha", k=0.0)  # k=0 -> pure banker record, no shrink
    scored = df.index[(df["lead_manager"] == "B") & (df["listing_date"] == "2024-01-01")][0]
    # only the 3 SME priors (all +0.5, fully matured by 2024) count -> Q == 0.5
    assert s.loc[scored] == pytest.approx(0.5, abs=1e-6)


def test_series_empty_banker_returns_segment_base():
    # a brand-new banker with no priors -> Q equals the PIT segment base (shrinkage to base, W=0)
    rows = [("OLD", "2021-01-01", "SME", 50, 0.2, 0.2, 0.2, 0.2),
            ("OLD", "2021-02-01", "SME", 50, 0.2, 0.2, 0.2, 0.2),
            ("NEW", "2024-01-01", "SME", 50, 0.0, 0.0, 0.0, 0.0)]   # first-ever IPO by NEW
    df = _frame(rows)
    s = bq.banker_quality_series(df, df, target="alpha", k=5.0)
    scored = df.index[df["lead_manager"] == "NEW"][0]
    # segment base = mean matured alpha of SME priors before 2024 = 0.2; NEW has no priors -> Q == base
    assert s.loc[scored] == pytest.approx(0.2, abs=1e-6)


