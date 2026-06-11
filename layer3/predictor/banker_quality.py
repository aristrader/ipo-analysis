"""A1c — banker-quality measure (transparent, point-in-time; NO ML).

Judges a lead manager on the QUALITY + SCALE + TRAJECTORY of its prior book, not the count of IPOs.
Spec: docs/superpowers/specs/2026-06-11-a1c-banker-quality-design.md. The construction (for banker b
scoring an IPO at date t in segment s):

  - take b's PRIOR IPOs in segment s that listed BEFORE t (strictly point-in-time, segment-specific);
  - weight each prior by `log1p(issue_size_cr) · 0.5^(age_years / H)` — size-damped × recency (half-life H);
  - per-prior value:
      * target='alpha' → horizon-tapered alpha `Σ τ_h·α_h`, with each horizon DROPPED+renormalized if it has
        not MATURED by t (a prior's 1y-alpha is usable only once 1y has elapsed — the look-ahead-safe rule);
      * target='bad'   → the bad-outcome indicator (wipeout|dead-money), usable only once the prior has had
        DOWNSIDE_MATURITY_DAYS to reveal early failure (a PIT proxy — we can't know an eventual outcome at t);
  - shrink the weighted banker value toward the PIT segment base: `(W·raw + k·μ_seg)/(W + k)`, W = Σweights.
    Confidence (evidence mass W) sets how much we trust the banker's own record vs the segment base — so a thin
    record leans on the base and a deep record stands on its own. This replaces A1b's MIN_PRIOR/freq cliff.

Everything here is a closed-form formula over owned columns; nothing learned, nothing peeking at the future.
"""
import numpy as np
import pandas as pd

HORIZON_DAYS = {"3m": 91, "6m": 182, "1y": 365, "3y": 1095}
TAPER = {"3m": 0.45, "6m": 0.30, "1y": 0.20, "3y": 0.05}   # early horizons weigh more; 3y barely (pre-registered)
DEFAULT_H = 3.0              # recency half-life in years
DEFAULT_K = 5.0             # shrinkage pseudocount (evidence-mass equivalent)
DOWNSIDE_MATURITY_DAYS = 365  # a prior needs ≥1y to reveal early failure before its bad-label is PIT-usable


def _weight(issue_size_cr, age_years, H=DEFAULT_H):
    """Per-prior weight = size-damped × recency-decayed."""
    return float(np.log1p(max(0.0, issue_size_cr or 0.0))) * (0.5 ** (age_years / H))


def _tapered_alpha(prior, age_days, taper=TAPER, horizon_days=HORIZON_DAYS):
    """Horizon-tapered alpha for one prior, using ONLY horizons matured by `age_days`.
    Returns (value, any_matured); value is None if no horizon has matured."""
    num = den = 0.0
    for h, w in taper.items():
        if age_days >= horizon_days[h]:
            a = prior.get(f"alpha_{h}")
            if a is not None and not (isinstance(a, float) and np.isnan(a)):
                num += w * float(a)
                den += w
    return (num / den, True) if den > 0 else (None, False)


def _shrink(raw, W, mu_seg, k=DEFAULT_K):
    """Shrink a banker's weighted value toward the segment base by evidence mass W."""
    denom = W + k
    return (W * raw + k * mu_seg) / denom if denom > 0 else mu_seg


def _alpha_value_weight(idx, t, ld_a, size_a, alpha_cols, taper, H):
    """Vectorized matured-tapered-alpha value + weight for the prior rows `idx` (np int array)."""
    ages = (t - ld_a[idx]).astype("timedelta64[D]").astype(float)
    num = np.zeros(len(idx)); den = np.zeros(len(idx))
    for h, w in taper.items():
        matured = ages >= HORIZON_DAYS[h]
        av = alpha_cols[h][idx]
        ok = matured & ~np.isnan(av)
        num[ok] += w * av[ok]; den[ok] += w
    usable = den > 0
    val = num[usable] / den[usable]
    wt = np.log1p(np.maximum(0.0, size_a[idx][usable])) * (0.5 ** ((ages[usable] / 365.0) / H))
    return val, wt


def _bad_value_weight(idx, t, ld_a, size_a, bad_a, H):
    """Vectorized bad-outcome value + weight for prior rows `idx`, gated on downside maturity."""
    ages = (t - ld_a[idx]).astype("timedelta64[D]").astype(float)
    usable = (ages >= DOWNSIDE_MATURITY_DAYS) & ~np.isnan(bad_a[idx])
    val = bad_a[idx][usable]
    wt = np.log1p(np.maximum(0.0, size_a[idx][usable])) * (0.5 ** ((ages[usable] / 365.0) / H))
    return val, wt


def _pop_value_weight(idx, t, ld_a, size_a, pop_a, H):
    """Vectorized listing-pop value + weight for prior rows `idx`. NO maturity gate — a listing pop
    is known on the prior's own listing day, so any prior that listed before t is immediately usable
    (this is the 'pricing-discipline' track: does the banker tend to price to pop?)."""
    ages = (t - ld_a[idx]).astype("timedelta64[D]").astype(float)
    usable = ~np.isnan(pop_a[idx])
    val = pop_a[idx][usable]
    wt = np.log1p(np.maximum(0.0, size_a[idx][usable])) * (0.5 ** ((ages[usable] / 365.0) / H))
    return val, wt


def banker_quality_series(pool, panel, target="alpha", H=DEFAULT_H, k=DEFAULT_K,
                          taper=TAPER, asof_col="listing_date"):
    """PIT banker-quality per row in `pool`, using `panel` as the historical book.

    target='alpha' (horizon-tapered, matured alpha — the RETURN arm) or 'bad' (matured bad-outcome
    rate — the DOWNSIDE arm). Returns a float pd.Series aligned to pool.index: the shrunk banker value,
    or the segment base when the banker has no usable priors (W=0)."""
    lm_a = panel["lead_manager"].astype(str).str.strip().values
    ld_a = pd.to_datetime(panel[asof_col], errors="coerce").values
    typ_a = panel["type"].astype(str).values
    size_a = pd.to_numeric(panel.get("issue_size_cr"), errors="coerce").fillna(0.0).values
    alpha_cols = {h: pd.to_numeric(panel.get(f"alpha_{h}"), errors="coerce").values for h in taper}
    bad_a = pop_a = None
    if target == "bad":
        from layer3.predictor.scorecard import _bad_outcome_mask
        bad_a = _bad_outcome_mask(panel).astype(float).values
    elif target == "pop":
        pop_a = pd.to_numeric(panel.get("adj_listing_gain_open"), errors="coerce").values

    pl_lm = pool["lead_manager"].astype(str).str.strip().values
    pl_ld = pd.to_datetime(pool[asof_col], errors="coerce").values
    pl_typ = pool["type"].astype(str).values
    out = pd.Series(np.nan, index=pool.index, dtype=float)

    for pos in range(len(pool)):
        b, t, s = pl_lm[pos], pl_ld[pos], pl_typ[pos]
        if b in ("", "nan") or pd.isna(t):
            continue
        before = (ld_a < t)
        seg_idx = np.where((typ_a == s) & before)[0]
        if len(seg_idx) == 0:
            continue
        prior_idx = np.where((typ_a == s) & before & (lm_a == b))[0]
        if target == "alpha":
            sval, _sw = _alpha_value_weight(seg_idx, t, ld_a, size_a, alpha_cols, taper, H)
            bval, bwt = _alpha_value_weight(prior_idx, t, ld_a, size_a, alpha_cols, taper, H)
        elif target == "pop":
            sval, _sw = _pop_value_weight(seg_idx, t, ld_a, size_a, pop_a, H)
            bval, bwt = _pop_value_weight(prior_idx, t, ld_a, size_a, pop_a, H)
        else:
            sval, _sw = _bad_value_weight(seg_idx, t, ld_a, size_a, bad_a, H)
            bval, bwt = _bad_value_weight(prior_idx, t, ld_a, size_a, bad_a, H)
        if len(sval) == 0:
            continue
        mu_seg = float(np.mean(sval))               # PIT segment base (matured priors only, unweighted)
        if len(bval) and bwt.sum() > 0:
            raw = float(np.sum(bwt * bval) / np.sum(bwt))
            out.iloc[pos] = _shrink(raw, float(bwt.sum()), mu_seg, k)
        else:
            out.iloc[pos] = mu_seg                   # no usable banker priors -> the segment base
    return out
