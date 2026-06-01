"""N6 — Valuation: PE relative to sector → forward alpha (mean-reversion test).

A raw PE isn't comparable across sectors (a 30x is cheap for IT, dear for a bank). So we use
pe_vs_sector = pe_ratio / the sector's median PE, tertile it, and track forward alpha + wipeout.
Hypothesis: the 'expensive vs sector' tertile mean-reverts (weaker forward alpha). BOOM-ONLY
(pe_ratio is boom-era) and gated on sector coverage. MB/SME never pooled. Single-regime flag.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rows(sub):
    pe = pd.to_numeric(sub["pe_ratio"], errors="coerce")
    s = sub[pe.notna() & (pe > 0) & sub["broad_sector"].notna()].copy()
    s["_pe"] = pe[pe.notna() & (pe > 0) & sub["broad_sector"].notna()]
    if len(s) < 3 * config.MIN_N_HINT:
        return []
    med = s.groupby("broad_sector")["_pe"].transform("median")
    s["_rel"] = s["_pe"] / med                       # PE relative to its sector
    q1, q2 = s["_rel"].quantile([1 / 3, 2 / 3])
    bands = [("cheap vs sector", -1, q1), ("in-line", q1, q2), ("expensive vs sector", q2, 1e9)]
    rows = []
    for label, lo, hi in bands:
        b = s[(s["_rel"] > lo) & (s["_rel"] <= hi)] if label != "cheap vs sector" else s[s["_rel"] <= hi]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        rows.append({"pe_vs_sector": label, "median_pe": round(float(b["_pe"].median()), 1) if len(b) else None,
                     "N": len(b), "N_1y": len(g1), "N_3y": len(g3),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]) if len(g1) >= config.MIN_N_HINT else None,
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]) if len(g3) >= config.MIN_N_HINT else None,
                     "wipeout_lower_%": _p(spine.wipeout_band(b)["wipeout_lower_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    boom = spine.segment(df, cohort="boom")
    for seg in config.SEGMENTS:
        rows = _rows(boom[boom["type"] == seg])
        if rows:
            tables.append((f"{seg} (BOOM): PE relative to sector median, tertile → forward alpha + wipeout. "
                           f"Does the 'expensive vs sector' bucket mean-revert (weaker forward alpha)?",
                           pd.DataFrame(rows)))
    if not tables:
        tables.append(("Insufficient PE × sector coverage for tertile analysis.",
                       pd.DataFrame([{"note": "see caveats", "N": 0}])))
    caveats += [
        "⚠ Single-regime (boom only): pe_ratio is a boom-era field; gated on sector coverage (now ~94% boom-MB). "
        "Not cross-regime validated.",
        "PE is normalised by SECTOR median (a raw PE isn't comparable across industries). Negative/zero PE "
        "(loss-makers) excluded — they have no meaningful PE. Sub-floor tertiles suppressed.",
        "Valuation is a noisier signal than profitability/leverage — treat as exploratory; feeds a return-potential "
        "penalty at extremes, not a standalone call.",
    ]
    narrative = ("Are richly-valued IPOs set up to disappoint? Because a PE only means something relative to its "
                 "sector, we measure each IPO's PE against its sector's median, tertile it, and check whether the "
                 "'expensive vs sector' group mean-reverts to weaker forward alpha. Boom cohort only.")
    return Finding(id="n6", title="N6 · Valuation: PE-vs-sector (mean-reversion, boom-only)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
