"""Part C — strategy backtester.

A strategy = entry rule + exit rule applied POINT-IN-TIME (only info known at the decision;
no look-ahead). Each strategy maps each eligible IPO to a realized RETURN and (for secondary
strategies) market-adjusted ALPHA at a fixed horizon, net of costs, with access realism noted.
Every strategy is compared to the do-nothing baseline (the index = alpha 0). Honesty: alpha is
from the LISTING price (what a public investor can buy at); allottee strategies report raw
return (the allottee's pocket) since from-issue alpha isn't stored. SME and MB never pooled.
"""
import numpy as np
import pandas as pd
from layer3 import spine, config

# rough round-trip frictions (STT + brokerage + slippage), as return drag
COST_SECONDARY = 0.005      # buy at listing + sell later
COST_FLIP = 0.005           # allotment + sell on listing day


def _num(df, col):
    return pd.to_numeric(df.get(col), errors="coerce")


# ---- strategies: each returns a DataFrame with columns ret, alpha (may be NaN), kind ----
def strat_allottee_hold(df, h):
    """Allottee buys at ISSUE, holds h. Raw return (allottee's pocket). Access: needs allotment."""
    g = spine.maturity_gated(df, h)
    return pd.DataFrame({"ret": _num(g, f"return_from_issue_{h}"), "alpha": np.nan},
                        index=g.index), "allottee", "needs allotment (≈1/oversubscription)"


def strat_flip_listing(df, h):
    """Allottee buys at ISSUE, sells at LISTING. Raw listing gain minus cost. Held ~0 days."""
    g = df[df["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)]
    ret = _num(g, "adj_listing_gain_open") - COST_FLIP
    return pd.DataFrame({"ret": ret, "alpha": np.nan}, index=g.index), "allottee", \
        "needs allotment; adverse selection (you get the duds, not the hot ones)"


def strat_secondary_hold(df, h):
    """Public investor buys at LISTING price, holds h. Market-adjusted ALPHA (from listing)."""
    g = spine.maturity_gated(df, h)
    alpha = _num(g, f"alpha_{h}") - COST_SECONDARY
    ret = _num(g, f"return_from_listing_{h}") - COST_SECONDARY
    return pd.DataFrame({"ret": ret, "alpha": alpha}, index=g.index), "secondary", "freely accessible"


def strat_secondary_filtered(df, h):
    """Secondary buy-and-hold, but only IPOs passing a Tier-1 filter known PRE-LISTING
    (profitable-at-IPO + meaningful OFS). NOTE: we deliberately do NOT gate on liquidity_flag —
    that is computed from post-listing turnover and would be look-ahead/survivorship bias."""
    g = spine.maturity_gated(df, h)
    prof = _num(g, "pre_ipo_pat") > 0
    ofs = _num(g, "ofs_pct") >= 25
    g = g[prof & ofs]
    alpha = _num(g, f"alpha_{h}") - COST_SECONDARY
    ret = _num(g, f"return_from_listing_{h}") - COST_SECONDARY
    return pd.DataFrame({"ret": ret, "alpha": alpha}, index=g.index), "secondary", \
        "filter: profitable-at-IPO & OFS≥25% (both pre-listing-known)"


def strat_secondary_avoid_hot(df, h):
    """Secondary buy-and-hold, but skip IPOs that popped >25% on listing (avoid the froth)."""
    g = spine.maturity_gated(df, h)
    g = g[g["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)]
    pop = _num(g, "adj_listing_gain_open")
    g = g[pop <= 0.25]
    alpha = _num(g, f"alpha_{h}") - COST_SECONDARY
    ret = _num(g, f"return_from_listing_{h}") - COST_SECONDARY
    return pd.DataFrame({"ret": ret, "alpha": alpha}, index=g.index), "secondary", "filter: listing pop ≤ 25%"


STRATEGIES = {
    "allottee_hold": strat_allottee_hold,
    "flip_at_listing": strat_flip_listing,
    "secondary_hold": strat_secondary_hold,
    "secondary_filtered": strat_secondary_filtered,
    "secondary_avoid_hot": strat_secondary_avoid_hot,
}


def _measure(res, kind):
    use = "alpha" if kind == "secondary" else "ret"
    return use, pd.to_numeric(res[use], errors="coerce").dropna()


def _metrics(res, kind):
    """Aggregate a strategy result. For secondary -> alpha-based; allottee -> raw-return-based."""
    use, s = _measure(res, kind)
    n = len(s)
    if n == 0:
        return {"N": 0, "measure": use}
    return {
        "N": n, "measure": use,
        "mean_%": round(100 * s.mean(), 1), "median_%": round(100 * s.median(), 1),
        "win_rate_%": round(100 * (s > 0).mean(), 1),
        "p10_%": round(100 * s.quantile(0.10), 1), "p90_%": round(100 * s.quantile(0.90), 1),
        "worst_%": round(100 * s.min(), 1),
    }


def _cohort_median(df, fn, h, kind, cohort):
    res, _, _ = fn(spine.segment(df, cohort=cohort), h)
    _, s = _measure(res, kind)
    return float(s.median()) if len(s) >= config.MIN_N_HINT else None


def run(df, horizon="1y", segment=None, cohort=None):
    """Run all strategies on a (segment[, cohort]) slice at a horizon -> a comparison table.
    `verdict` is CROSS-REGIME for secondary (alpha) strategies: 'beats' only if median alpha > 0
    in BOTH boom and longterm; 'mixed' if signs disagree. Allottee/flip raw-return strategies get
    'n/a (raw)' — a raw return isn't benchmark-relative, so it can't be judged vs do-nothing here."""
    base = spine.segment(df, segment=segment)
    rows = []
    for name, fn in STRATEGIES.items():
        res, kind, access = fn(spine.segment(base, cohort=cohort), horizon)
        m = _metrics(res, kind)
        if kind == "secondary":
            bm = _cohort_median(base, fn, horizon, kind, "boom")
            lm = _cohort_median(base, fn, horizon, kind, "longterm")
            if bm is None or lm is None:
                verdict = "insufficient cohort N"
            elif bm > 0 and lm > 0:
                verdict = "beats (cross-regime)"
            elif bm <= 0 and lm <= 0:
                verdict = "loses (cross-regime)"
            else:
                verdict = "MIXED (sign flips by regime)"
            m["boom_median_%"] = None if bm is None else round(100 * bm, 1)
            m["long_median_%"] = None if lm is None else round(100 * lm, 1)
        else:
            verdict = "n/a (raw return — not benchmark-relative)"
        rows.append({"strategy": name, "kind": kind, **m, "verdict": verdict, "access_realism": access})
    return pd.DataFrame(rows)
