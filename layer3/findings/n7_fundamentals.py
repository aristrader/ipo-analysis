"""N7 — Graded fundamentals (ROE / PAT-margin / debt-equity tertiles → outcomes).

Expands the binary profitable-at-IPO (T9) into graded quality. For each fundamental, split into
tertiles and show median forward alpha (maturity-gated) + wipeout band. Debt/equity is the
headline DEATH signal (high leverage → wipeout). MB and SME never pooled. Coverage is boom-skewed
(~67–77%) and this is NOT separately cross-regime-validated yet — descriptive/exploratory.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

METRICS = [("pre_ipo_roe_pct", "ROE %", "higher better"),
           ("pre_ipo_pat_margin_pct", "PAT margin %", "higher better"),
           ("pre_ipo_debt_equity", "Debt/Equity", "LOWER better (death signal)")]


def _tertile_rows(sub, col):
    v = pd.to_numeric(sub[col], errors="coerce")
    s = sub[v.notna()].copy(); s["_v"] = v[v.notna()]
    if len(s) < 3 * config.MIN_N_HINT:
        return []
    q1, q2 = s["_v"].quantile([1 / 3, 2 / 3])
    bands = [("bottom 3rd", -1e18, q1), ("middle 3rd", q1, q2), ("top 3rd", q2, 1e18)]
    rows = []
    for label, lo, hi in bands:
        b = s[(s["_v"] > lo) & (s["_v"] <= hi)] if label != "bottom 3rd" else s[s["_v"] <= hi]
        g3 = spine.maturity_gated(b, "3y")
        wb = spine.wipeout_band(b)
        rows.append({"tertile": label, "median_value": round(float(b["_v"].median()), 2) if len(b) else None,
                     "N": len(b),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(spine.maturity_gated(b,'1y'), "1y"))["median"]),
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]),
                     "N_3y": len(g3),
                     "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                     "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    for col, name, direction in METRICS:
        for seg in config.SEGMENTS:
            rows = _tertile_rows(df[df["type"] == seg], col)
            if not rows:
                continue
            tables.append((f"{seg}: {name} tertiles → forward alpha + wipeout ({direction}).",
                           pd.DataFrame(rows)))

    caveats += [
        "Debt/Equity is the headline death signal: the top-debt tertile should carry the highest wipeout.",
        "Fundamentals coverage is boom-skewed (~67–77%); tertiles pool cohorts (a company's ROE/leverage is a "
        "company property), so this is descriptive — NOT separately cross-regime-validated (cf. T9's profitable "
        "premium, which flipped sign across regimes).",
        "Pre-IPO financials are RHP/screener-sourced (provenance-graded moderate); sub-floor tertiles suppressed.",
    ]
    narrative = ("Beyond the simple profitable-or-not flag: do better fundamentals (higher ROE/margin, lower debt) "
                 "translate into better forward alpha and lower wipeout? We tertile each and show the gradient — "
                 "leverage especially, since high debt is the classic IPO death signal.")
    return Finding(id="n7", title="N7 · Graded fundamentals (ROE / margin / debt)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
