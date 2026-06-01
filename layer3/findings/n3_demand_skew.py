"""N3 — QIB-vs-Retail demand skew ('smart vs dumb money').

Ratio sub_qib_x / sub_retail_x, tertiled. Per tertile: forward alpha + wipeout + below-issue.
Hypothesis: QIB-led demand (institutions piling in harder than retail) → better forward outcomes.
SINGLE-REGIME (subscription is boom-only). MB and SME never pooled.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rows(sub):
    qib = pd.to_numeric(sub["sub_qib_x"], errors="coerce")
    ret = pd.to_numeric(sub["sub_retail_x"], errors="coerce")
    skew = qib / ret.replace(0, pd.NA)
    s = sub[skew.notna()].copy(); s["_skew"] = skew[skew.notna()]
    if len(s) < 3 * config.MIN_N_HINT:
        return []
    q1, q2 = s["_skew"].quantile([1 / 3, 2 / 3])
    bands = [("retail-led (low QIB/retail)", -1, q1), ("balanced", q1, q2), ("QIB-led (high QIB/retail)", q2, 1e18)]
    rows = []
    for label, lo, hi in bands:
        b = s[(s["_skew"] > lo) & (s["_skew"] <= hi)] if label != "retail-led (low QIB/retail)" else s[s["_skew"] <= hi]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        cri = pd.to_numeric(b.get("current_return_from_issue"), errors="coerce").dropna()
        rows.append({"qib_retail_skew": label, "median_skew": round(float(b["_skew"].median()), 2) if len(b) else None,
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
            tables.append((f"{seg} (BOOM): QIB/retail demand-skew tertile → forward alpha + wipeout. Does "
                           f"institution-led demand (high QIB/retail) predict better outcomes?", pd.DataFrame(rows)))
    caveats += [
        "⚠ SINGLE-REGIME (boom only) — subscription category splits don't exist for the longterm cohort; cannot be "
        "cross-regime validated.",
        "QIB (institutions) is the 'smart money' leg; the ratio normalizes for overall hype. Sub-floor tertiles suppressed.",
        "Subscription is official/hard-to-fake; but resist over-slicing — read the tertile gradient, not single bands.",
    ]
    narrative = ("Do IPOs where institutions (QIB) pile in harder than retail go on to do better — the classic "
                 "'smart money vs dumb money' read? We tertile the QIB/retail subscription ratio and track forward "
                 "alpha and wipeout. Boom-cohort only (category subscription doesn't exist pre-2020).")
    return Finding(id="n3", title="N3 · QIB-vs-Retail demand skew (boom-only)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
