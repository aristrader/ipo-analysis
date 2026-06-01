"""N8 — Accrual / cash-flow red-flag.

A company can report a PAT profit on paper while generating NO operating cash (aggressive
accruals). Flag = operating_cf_yr3 ≤ 0 WHILE pat_yr3 > 0 ('paper profit, no cash') vs a clean
profitable company (cf > 0 & pat > 0). Compare forward alpha + wipeout. A rarely-surfaced,
hard-to-fake quality signal from the otherwise-unused cash-flow trajectory. MB/SME never pooled.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rows(sub):
    cf = pd.to_numeric(sub.get("operating_cf_yr3"), errors="coerce")
    pat = pd.to_numeric(sub.get("pat_yr3"), errors="coerce")
    known = cf.notna() & pat.notna()
    groups = [("clean (PAT>0 & cash>0)", known & (pat > 0) & (cf > 0)),
              ("RED FLAG (PAT>0 but cash≤0)", known & (pat > 0) & (cf <= 0)),
              ("loss-making (PAT≤0)", known & (pat <= 0))]
    rows = []
    for label, mask in groups:
        b = sub[mask]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        rows.append({"cash_vs_profit": label, "N": len(b), "N_1y": len(g1), "N_3y": len(g3),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]) if len(g1) >= config.MIN_N_HINT else None,
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]) if len(g3) >= config.MIN_N_HINT else None,
                     "wipeout_lower_%": _p(spine.wipeout_band(b)["wipeout_lower_rate"]),
                     "wipeout_upper_%": _p(spine.wipeout_band(b)["wipeout_upper_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    for seg in config.SEGMENTS:
        rows = _rows(df[df["type"] == seg])
        tables.append((f"{seg}: cash-vs-profit at IPO → forward alpha + wipeout. Does 'paper profit, no operating "
                       f"cash' (the accrual red flag) underperform clean profitable companies?", pd.DataFrame(rows)))

    caveats += [
        "Red flag = reported PAT > 0 but operating cash flow ≤ 0 in the latest pre-IPO year (yr3) — profit on paper, "
        "no cash behind it. A classic earnings-quality warning.",
        "Uses pre-IPO RHP/screener cash-flow (provenance-graded moderate); coverage limited by operating_cf_yr3; "
        "sub-floor groups suppressed. Cohorts pooled within segment (earnings quality is a company property).",
        "Not separately cross-regime-validated — descriptive/exploratory quality signal.",
    ]
    narrative = ("Profit on paper isn't the same as cash in the bank. Some companies report a profit (positive PAT) "
                 "while their operations actually burn cash — an 'accrual' red flag. We compare these against clean "
                 "profitable companies to see if the market eventually punishes the paper-only profits.")
    return Finding(id="n8", title="N8 · Accrual / cash-flow red-flag",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
