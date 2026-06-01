"""Cross-regime sign-validation — the promotion gate from `reported` → `validated`.

For each rule's core DIRECTIONAL claim, compute its signed signal in the boom (2020–25) AND
longterm (2006–19) cohorts and check: does it hold the SAME sign (and the expected direction)
in both? A finding that flips sign across regimes is a regime effect, not a robust truth.
Single-regime rules (e.g. subscription — longterm coverage ≈0) are flagged, not validated.
"""
import numpy as np
import pandas as pd
from layer3 import spine, config


def _med_alpha(sub, h):
    g = spine.maturity_gated(sub, h)
    d = spine.distribution(spine.alpha_series(g, h))
    return d["median"], d["n"]


def _mb(df):
    return df[df["type"] == "MB"]


# ---- directional signals (value in a cohort, + N for the binding sub-sample) ----
def sig_lasting_wealth(df):           # T1: MB underperforms -> median 1y alpha < 0
    return _med_alpha(_mb(df), "1y")


def sig_ofs_skin(df):                 # T5: high-OFS MB does BETTER -> alpha(OFS>50) - alpha(OFS=0) > 0
    mb = _mb(df); ofs = pd.to_numeric(mb["ofs_pct"], errors="coerce")
    hi, nhi = _med_alpha(mb[ofs > 50], "3y")
    lo, nlo = _med_alpha(mb[ofs <= 0.0001], "3y")
    v = (hi - lo) if (hi is not None and lo is not None) else None
    return v, min(nhi, nlo)


def sig_profitable(df):               # T9: profitable premium -> alpha(prof) - alpha(loss) > 0  (MB)
    mb = _mb(df); pat = pd.to_numeric(mb.get("pre_ipo_pat"), errors="coerce")
    p, npos = _med_alpha(mb[pat > 0], "3y")
    l, nneg = _med_alpha(mb[pat < 0], "3y")
    v = (p - l) if (p is not None and l is not None) else None
    return v, min(npos, nneg)


def sig_pop_fade(df):                 # T3: big pop -> worse fwd return (secondary) -> hi - lo < 0 (MB)
    mb = _mb(df[df["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)])
    pop = pd.to_numeric(mb["adj_listing_gain_open"], errors="coerce")
    hi = spine.listing_return(mb[pop > 0.50], "1y").dropna()
    lo = spine.listing_return(mb[pop <= 0.25], "1y").dropna()
    v = (hi.median() - lo.median()) if (len(hi) and len(lo)) else None
    return v, min(len(hi), len(lo))


def sig_size_survival(df):            # N4: small issue -> more wipeout -> wipe(small) - wipe(large) > 0 (MB)
    mb = _mb(df); sz = pd.to_numeric(mb["issue_size_cr"], errors="coerce")
    small = spine.wipeout_band(mb[sz <= 100]); large = spine.wipeout_band(mb[sz > 500])
    v = (small["wipeout_lower_rate"] - large["wipeout_lower_rate"]) \
        if (small["wipeout_lower_rate"] is not None and large["wipeout_lower_rate"] is not None) else None
    return v, min(small["n"], large["n"])


SIGNALS = [
    ("desc-lasting-wealth", "MB underperforms the index (median 1y alpha < 0)", sig_lasting_wealth, "-", "cross"),
    ("pred-ofs-skin", "High-OFS MB does better (alpha gradient > 0)", sig_ofs_skin, "+", "cross"),
    ("pred-profitable-ipo", "Profitable-at-IPO premium (> 0)", sig_profitable, "+", "cross"),
    ("pred-pop-fade", "Big listing pop -> worse forward return for the secondary buyer (< 0)", sig_pop_fade, "-", "cross"),
    ("pred-size-survival", "Smaller issues have higher wipeout (> 0)", sig_size_survival, "+", "cross"),
    ("pred-sub-saturation", "Subscription saturation/mean-reversion", None, None, "boom-only"),
]


def _sign(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return "+" if x > 0 else ("-" if x < 0 else "0")


def _within_vintage(df, fn, expected):
    """Per-LISTING-YEAR check (closes the vintage=regime trap the 2-bucket check can't): in how many
    individual vintages does the signal hold the expected sign? Returns (consistent, tested)."""
    consistent = tested = 0
    yrs = df["listing_date"].astype(str).str[:4]
    for y in sorted(set(yrs[yrs.str.isdigit()])):
        sl = df[yrs == y]
        if len(sl) < config.MIN_N_HINT:
            continue
        v, n = fn(sl)
        if v is None or n < config.MIN_N_HINT:
            continue
        tested += 1
        if _sign(v) == expected:
            consistent += 1
    return consistent, tested


def validate(df=None):
    if df is None:
        df = spine.load_substrate()
    boom = spine.segment(df, cohort="boom"); long = spine.segment(df, cohort="longterm")
    rows = []
    for rid, claim, fn, expected, regime in SIGNALS:
        if regime == "boom-only" or fn is None:
            rows.append({"rule": rid, "claim": claim, "boom": None, "longterm": None,
                         "expected_sign": expected, "verdict": "single-regime (not cross-validatable)"})
            continue
        bv, bn = fn(boom); lv, ln = fn(long)
        bs, ls = _sign(bv), _sign(lv)
        cons, tested = _within_vintage(df, fn, expected)
        vintage = f"{cons}/{tested} yrs" if tested else "—"
        min_n = min(bn, ln)
        insufficient = (bn < config.MIN_N_HINT or ln < config.MIN_N_HINT or bv is None or lv is None)
        # fragility heuristic: binding sample + within-vintage consistency
        if insufficient:
            fragility = "untestable (insufficient N)"
        elif min_n < 20 or (tested and cons / tested < 0.5):
            fragility = "FRAGILE"
        elif min_n >= config.MIN_N_TRADABLE and tested and cons / tested >= 0.6:
            fragility = "robust"
        else:
            fragility = "moderate"
        if insufficient:
            verdict = f"insufficient N (boom={bn}, long={ln})"
        elif bs == ls and (expected is None or bs == expected):
            # cross-regime AND within-vintage majority required for full VALIDATED
            verdict = ("VALIDATED (both regimes + within-vintage)" if (tested and cons / tested >= 0.6)
                       else "cross-regime only (within-vintage weak)")
        elif bs == ls:
            verdict = f"consistent but sign={bs} (expected {expected}) — revisit claim"
        else:
            verdict = "MIXED — sign flips by regime (regime effect, not robust)"
        rows.append({"rule": rid, "claim": claim, "boom": _r(bv), "longterm": _r(lv),
                     "expected_sign": expected, "boom_N": bn, "long_N": ln,
                     "within_vintage": vintage, "fragility": fragility, "verdict": verdict})
    return pd.DataFrame(rows)


def _r(x):
    return None if (x is None or (isinstance(x, float) and np.isnan(x))) else round(100 * x, 1)
