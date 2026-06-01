"""N4 — Issue-size 'Goldilocks' + size-survival gradient.

issue_size_cr is 100% covered across all cohorts/segments — the strongest always-available
downside input. Per issue-size band (and market_cap_class): median forward alpha (maturity-
gated) + 2x-rate + wipeout band. Tests both ends — very large issues may digest poorly
short-term; tiny issues have far higher wipeout (the size-survival signal). MB/SME never pooled.
"""
import numpy as np
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

# ₹-cr issue-size bands (span SME-tiny → MB-jumbo); sparse bands get suppressed by the N-guard
BANDS = [("<25", -1, 25), ("25–100", 25, 100), ("100–500", 100, 500),
         ("500–2000", 500, 2000), ("2000–10000", 2000, 10000), (">10000", 10000, 1e12)]


def _rows(sub):
    rows = []
    for label, lo, hi in BANDS:
        sz = pd.to_numeric(sub["issue_size_cr"], errors="coerce")
        b = sub[(sz > lo) & (sz <= hi)]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        rfl1 = spine.listing_return(b, "1y").dropna()
        wb = spine.wipeout_band(b)
        rows.append({"issue_size_cr_band": label, "N": len(b),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]),
                     "N_1y": len(g1),
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]),
                     "N_3y": len(g3),
                     "pct_2x_from_listing": _p(spine.proportion(rfl1 >= 1.0)["rate"]),
                     "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                     "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    for seg in config.SEGMENTS:
        tables.append((f"{seg}: outcomes by issue-size band (issue_size_cr, 100% covered). Watch BOTH ends — "
                       f"jumbo issues' short-term alpha and the small-issue WIPEOUT rate.",
                       pd.DataFrame(_rows(df[df["type"] == seg]))))

    # market_cap_class view (lean on longterm + boom-MB re-pull; 'unknown' kept separate)
    mc_rows = []
    for seg in config.SEGMENTS:
        for mc in config.MCAP_ORDER + ["unknown"]:
            sub = df[(df["type"] == seg) &
                     ((df["market_cap_class"] == mc) if mc != "unknown" else df["market_cap_class"].isna())]
            if len(sub) == 0:
                continue
            wb = spine.wipeout_band(sub)
            g1 = spine.maturity_gated(sub, "1y")
            mc_rows.append({"segment": seg, "market_cap_class": mc, "N": len(sub),
                            "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]),
                            "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                            "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    tables.append(("By market-cap class (the 'unknown' bucket is rows without a screener mcap — not imputed).",
                   pd.DataFrame(mc_rows)))

    from layer3 import charts as ch
    mb = pd.DataFrame(_rows(df[df["type"] == "MB"]))
    charts.append(("Mainboard: wipeout rate (lower) by issue-size band — the size-survival gradient",
                   ch.bar_png(mb["issue_size_cr_band"].tolist(),
                              [v if v is not None else 0 for v in mb["wipeout_lower_%"]],
                              ns=mb["N"].tolist(), title="MB: wipeout % by issue size",
                              ylabel="wipeout % (lower)")))

    caveats += [
        "issue_size_cr is 100% covered → the most reliable always-available size proxy. market_cap_class is sparse "
        "for boom-MB historically (now re-pulled); 'unknown' mcap is shown as its own bucket, never imputed.",
        "Long-horizon (3y) cells lean on the longterm cohort (maturity-gating); sub-floor bands are suppressed.",
        "Size-survival predicate: the smallest-issue bands carry materially higher wipeout — a core downside signal.",
    ]
    narrative = ("Is there a 'Goldilocks' issue size? Very large issues can digest poorly short-term, while the "
                 "tiniest issues carry far higher wipeout risk. Because issue size is fully covered for every IPO, "
                 "this is the most dependable downside input — we show forward alpha, the 2x-rate, and the wipeout "
                 "band across size bands, MB and SME apart.")
    return Finding(id="n4", title="N4 · Issue-size & size-survival gradient",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
