"""N5 — Anchor-conviction gradient (anchor allocation as a % of issue size).

anchor_pct = anchor_allocation_cr / issue_size_cr (capped to a sane 0–60% range). Tertiled.
Hypothesis: heavier anchor participation = stronger institutional pre-commitment = better forward
outcomes / lower wipeout. Anchor allocation is disclosed/official (cleaner than GMP). BOOM-MB
primary (anchor disclosure is boom-era and thin for SME). Single-regime flag.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rows(sub):
    anc = pd.to_numeric(sub["anchor_allocation_cr"], errors="coerce")
    iss = pd.to_numeric(sub["issue_size_cr"], errors="coerce")
    pct = (anc / iss).where((anc.notna()) & (iss > 0))
    pct = pct.where(pct <= 0.60)                       # cap data errors (anchor ≤ ~60% of issue)
    s = sub[pct.notna()].copy(); s["_pct"] = pct[pct.notna()]
    if len(s) < 3 * config.MIN_N_HINT:
        return []
    q1, q2 = s["_pct"].quantile([1 / 3, 2 / 3])
    bands = [("low anchor %", -1, q1), ("mid anchor %", q1, q2), ("high anchor %", q2, 1e9)]
    rows = []
    for label, lo, hi in bands:
        b = s[(s["_pct"] > lo) & (s["_pct"] <= hi)] if label != "low anchor %" else s[s["_pct"] <= hi]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        rows.append({"anchor_pct_tertile": label,
                     "median_anchor_pct": round(float(b["_pct"].median() * 100), 1) if len(b) else None,
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
            tables.append((f"{seg} (BOOM): anchor-allocation % of issue, tertile → forward alpha + wipeout. Does "
                           f"heavier anchor (institutional pre-commitment) predict better outcomes?", pd.DataFrame(rows)))
    if not tables:
        tables.append(("Insufficient anchor coverage for tertile analysis (anchor disclosure is boom-MB-mainly).",
                       pd.DataFrame([{"note": "see caveats", "N": 0}])))
    caveats += [
        "⚠ Single-regime / boom-MB-primary: anchor allocation is a boom-era disclosure; SME coverage is thin → "
        "SME tertiles may be hint-only or suppressed. Not cross-regime validated.",
        "anchor_pct = anchor_allocation_cr / issue_size_cr, capped at 60% to drop data errors. The derived ratio is "
        "more comparable across IPOs than the raw ₹-cr.",
        "Anchor allocation is official/disclosed (cleaner than GMP); feeds a 'sponsorship' sub-signal.",
    ]
    narrative = ("Anchor investors commit money days before the IPO opens — a heavier anchor book signals stronger "
                 "institutional conviction. We tertile the anchor allocation as a % of the issue and check whether "
                 "higher conviction predicts better forward alpha and lower wipeout. Boom mainboard, mainly.")
    return Finding(id="n5", title="N5 · Anchor-conviction gradient (boom-MB)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
