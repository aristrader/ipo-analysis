"""Analog engine — find the most similar PAST IPOs to a new one.

Structure (docs/strategies.md "THE PREDICTOR"): hard-gate (define the universe) → soft-distance
(rank within) → widening ladder (relax gates until min-N) → return the analog cohort + which
rung was reached + confidence inputs. NO ML — transparent weighted-Gower distance over the
features the query actually provides; missing features are dropped and weights renormalized.
NEVER self-matches; delisted analogs are KEPT (most important for honest downside).
"""
import math
import numpy as np
import pandas as pd
from layer3 import spine, config

MCAP_ORDER = config.MCAP_ORDER  # micro<small<mid<large

# Tier-2 soft-distance features (weight by group) — only used when the query provides them.
NUMERIC_FEATURES = {
    "ofs_pct": 1.0,
    "log_issue_size": 1.0,          # derived from issue_size_cr
    "sub_total_x": 0.8,
    "sub_qib_x": 0.8,
    "pe_ratio": 0.8,
    "pre_ipo_roe_pct": 0.6,
    "pre_ipo_debt_equity": 0.6,
    "pre_ipo_pat_margin_pct": 0.6,
    "promoter_post_issue_pct": 0.5,
    "gmp_pct": 0.4,                 # grey-market: down-weighted, provenance-graded
}

# widening ladder: each rung is (label, gate-predicate-builder). Tightest first.
def _ladder():
    return [
        ("sector + mcap±1", lambda q: dict(sector=True, mcap_window=1)),
        ("sector + mcap±2", lambda q: dict(sector=True, mcap_window=2)),
        ("sector (any mcap)", lambda q: dict(sector=True, mcap_window=None)),
        ("financial-twin: mcap±1, any sector", lambda q: dict(sector=False, mcap_window=1)),
        ("segment only", lambda q: dict(sector=False, mcap_window=None)),
    ]


def _prep(df):
    """Add derived columns used for distance."""
    d = df.copy()
    d["log_issue_size"] = np.log1p(pd.to_numeric(d["issue_size_cr"], errors="coerce"))
    return d


# common user inputs -> the actual NSE broad_sector taxonomy in the data
SECTOR_ALIASES = {
    "finance": "Financial Services", "financial": "Financial Services", "bank": "Financial Services",
    "banking": "Financial Services", "nbfc": "Financial Services", "fintech": "Financial Services",
    "tech": "Information Technology", "it": "Information Technology", "software": "Information Technology",
    "pharma": "Healthcare", "health": "Healthcare", "hospital": "Healthcare",
    "fmcg": "Fast Moving Consumer Goods", "consumer staples": "Fast Moving Consumer Goods",
    "auto": "Consumer Discretionary", "realty": "Consumer Discretionary", "real estate": "Consumer Discretionary",
    "retail": "Consumer Discretionary", "media": "Consumer Discretionary", "consumer": "Consumer Discretionary",
    "infra": "Industrials", "industrial": "Industrials", "capital goods": "Industrials", "manufacturing": "Industrials",
    "metal": "Commodities", "metals": "Commodities", "chemical": "Commodities", "chemicals": "Commodities",
    "cement": "Commodities", "power": "Utilities", "utility": "Utilities", "energy": "Energy", "oil": "Energy",
    "telecom": "Telecommunication", "services": "Services",
}


def resolve_sector(value, df):
    """Map a free-text sector to the data's broad_sector taxonomy. Returns (resolved, note)."""
    if not value:
        return None, None
    valid = set(df["broad_sector"].dropna().unique())
    if value in valid:
        return value, None
    low = value.strip().lower()
    if low in SECTOR_ALIASES and SECTOR_ALIASES[low] in valid:
        return SECTOR_ALIASES[low], f"interpreted sector '{value}' as '{SECTOR_ALIASES[low]}'"
    for v in valid:
        if v.lower() == low or low in v.lower() or v.lower() in low:
            return v, f"interpreted sector '{value}' as '{v}'"
    return None, (f"sector '{value}' not recognized — sector gate dropped "
                  f"(valid: {', '.join(sorted(valid))})")


def robust_ranges(df, features):
    """P10–P90 spread per numeric feature, for normalising distances (robust to outliers)."""
    r = {}
    for f in features:
        s = pd.to_numeric(df.get(f), errors="coerce").dropna()
        if len(s) >= 10:
            lo, hi = s.quantile(0.10), s.quantile(0.90)
            r[f] = max(hi - lo, 1e-9)
    return r


def _mcap_window(query_mcap, window):
    if query_mcap not in MCAP_ORDER or window is None:
        return None
    i = MCAP_ORDER.index(query_mcap)
    return set(MCAP_ORDER[max(0, i - window): i + window + 1])


def _gate(df, query, sector, mcap_window):
    """Apply a hard gate. type is ALWAYS gated; sector/mcap per the rung."""
    out = df[df["type"] == query["type"]]
    if sector and query.get("broad_sector"):
        out = out[out["broad_sector"] == query["broad_sector"]]
    win = _mcap_window(query.get("market_cap_class"), mcap_window)
    if win is not None:
        out = out[out["market_cap_class"].isin(win)]
    return out


def gower(query, cand, ranges):
    """Weighted Gower distance (0..1) of each candidate row to the query, over the features
    the query provides AND the candidate has. Missing -> dropped + weights renormalised."""
    qnum = {f: query[f] for f in NUMERIC_FEATURES if query.get(f) is not None}
    if "issue_size_cr" in query and query.get("issue_size_cr") and "log_issue_size" not in qnum:
        qnum["log_issue_size"] = math.log1p(query["issue_size_cr"])
    n = len(cand)
    wsum = np.zeros(n); dsum = np.zeros(n)
    for f, qv in qnum.items():
        if f not in ranges:
            continue
        w = NUMERIC_FEATURES.get(f, 0.5)
        cv = pd.to_numeric(cand.get(f), errors="coerce").to_numpy(dtype=float)
        d = np.abs(cv - float(qv)) / ranges[f]
        d = np.clip(d, 0, 1)
        avail = ~np.isnan(d)
        dsum[avail] += w * d[avail]
        wsum[avail] += w
    # mcap ordinal component (if both have it)
    if query.get("market_cap_class") in MCAP_ORDER:
        qi = MCAP_ORDER.index(query["market_cap_class"])
        ci = cand["market_cap_class"].map(lambda m: MCAP_ORDER.index(m) if m in MCAP_ORDER else np.nan).to_numpy(float)
        d = np.abs(ci - qi) / (len(MCAP_ORDER) - 1)
        avail = ~np.isnan(d)
        dsum[avail] += 1.0 * d[avail]; wsum[avail] += 1.0
    dist = np.where(wsum > 0, dsum / np.maximum(wsum, 1e-9), np.nan)
    return pd.Series(dist, index=cand.index), int((wsum > 0).sum()), len(qnum)


def find_analogs(query, df=None, target_n=None, k=50, exclude_isin=None):
    """Return the analog cohort for a query IPO.
    query: dict with at least 'type' (MB/SME); optional broad_sector, market_cap_class,
           and any NUMERIC_FEATURES (+ issue_size_cr).
    Returns dict: cohort (DataFrame, with 'analog_distance'), rung label/index, n_gated,
           n_features_used, relaxed (bool), ranges.
    """
    target_n = target_n or config.MIN_N_TRADABLE
    if df is None:
        df = spine.load_substrate()
    df = _prep(df)
    if exclude_isin:
        df = df[df["isin"] != exclude_isin]
    # forgiving sector resolution ("Finance" -> "Financial Services"); drops gate if unknown
    sector_note = None
    if query.get("broad_sector"):
        resolved, sector_note = resolve_sector(query["broad_sector"], df)
        query = {**query, "broad_sector": resolved}   # None if unrecognized -> sector gate no-ops
    ranges = robust_ranges(df, list(NUMERIC_FEATURES))

    chosen = None
    for idx, (label, cfg) in enumerate(_ladder()):
        c = cfg(query)
        gated = _gate(df, query, c["sector"], c["mcap_window"])
        if len(gated) >= target_n or idx == len(_ladder()) - 1:
            chosen = (idx, label, gated)
            break
        if chosen is None:
            chosen = (idx, label, gated)
    rung_idx, rung_label, gated = chosen

    dist, nfeat_eff, nfeat = gower(query, gated, ranges)
    g = gated.copy()
    g["analog_distance"] = dist
    g = g.sort_values("analog_distance", na_position="last")
    cohort = g.head(k).copy()
    return {
        "cohort": cohort,
        "n_gated": len(gated),
        "n_cohort": len(cohort),
        "rung_idx": rung_idx,
        "rung_label": rung_label,
        "relaxed": rung_idx > 0,
        "n_features_used": nfeat,
        "ranges": ranges,
        "sector_note": sector_note,
    }
