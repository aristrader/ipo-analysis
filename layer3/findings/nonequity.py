"""Non-equity instruments — a SEPARATE view (FPO / InvIT / REIT), kept apart from the equity IPO
analysis (per the user's decision). These are NOT ordinary IPOs and behave very differently:
  - FPO = follow-on offer by an ALREADY-listed company (not a debut),
  - REIT / InvIT = yield/income instruments (real-estate / infra trusts), not growth equities.
Small, heterogeneous set (~51 rows) → directional only, heavily caveated. This finding loads the
non-equity rows itself (the main report's substrate is equity-only)."""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def compute(_df_ignored=None):
    full = spine.load_substrate(equity_only=False)
    ne = full[full["instrument_type"] != config.CORE_INSTRUMENT].copy()

    rows = []
    for itype, g in ne.groupby("instrument_type"):
        g1 = spine.maturity_gated(g, "1y"); g3 = spine.maturity_gated(g, "3y")
        cri = pd.to_numeric(g.get("current_return_from_issue"), errors="coerce").dropna()
        wb = spine.wipeout_band(g)
        rows.append({"instrument_type": itype, "N": len(g),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]),
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]),
                     "median_current_return_%": _p(cri.median() if len(cri) else None),
                     "wipeout_lower_%": _p(wb["wipeout_lower_rate"])})
    tables = [("Non-equity instruments by type — separate from the equity IPO analysis. Small N → directional only.",
               pd.DataFrame(rows))]
    caveats = [
        "These are NOT ordinary IPOs: FPO = follow-on by an already-listed company; REIT/InvIT = yield/income "
        "trusts, not growth equities. Their alpha-vs-Nifty framing is a poor fit (income instruments aren't "
        "meant to beat an equity index) — read returns descriptively, not as IPO base rates.",
        "Total ~51 rows across 3 types → every cell is a hint at best; sub-floor types suppressed. Excluded from "
        "ALL equity findings by design; shown here only for completeness.",
    ]
    narrative = ("A separate, clearly-fenced look at the non-equity instruments in the dataset (follow-on offers and "
                 "REIT/InvIT trusts). They're excluded from every equity IPO finding because they're a different "
                 "animal; this section reports them on their own, with heavy caveats and small samples.")
    return Finding(id="nonequity", title="X · Non-equity instruments (FPO / InvIT / REIT) — separate",
                   narrative=narrative, tables=tables, charts=[], caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
