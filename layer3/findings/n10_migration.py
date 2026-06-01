"""N10 — Outcome-class migration (listing → 1y → 3y): dud-to-star / star-to-dud.

Where do IPOs END UP relative to where they STARTED? We classify each IPO at listing (by listing
pop) and at 3y (by return-from-issue), then show the transition matrix: of the day-1 'pops', how
many are duds by 3y; of the day-1 'flops', how many became stars. COHORT HELD CONSTANT (longterm,
matured) to avoid a horizon-mix bias. Distinct from T3 (which is a pop-bucket → forward-return
gradient); this is the full class-to-class flow. MB/SME apart.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _cls(v):
    if pd.isna(v):
        return None
    if v < -0.20:
        return "loser"
    if v < 0.20:
        return "flat"
    if v < 1.00:
        return "winner"
    return "multibagger"


def _matrix(sub):
    g = spine.maturity_gated(sub, "3y")
    g = g[g["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)].copy()
    g["start"] = pd.to_numeric(g["adj_listing_gain_open"], errors="coerce").map(_cls)
    g["end"] = pd.to_numeric(g["return_from_issue_3y"], errors="coerce").map(_cls)
    g = g.dropna(subset=["start", "end"])
    order = ["loser", "flat", "winner", "multibagger"]
    rows = []
    for s in order:
        sub_s = g[g["start"] == s]
        rec = {"listing_class": s, "N": len(sub_s)}
        for e in order:
            rec[f"→{e}_%"] = _p((sub_s["end"] == e).mean()) if len(sub_s) else None
        rows.append(rec)
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    longt = spine.segment(df, cohort="longterm")
    for seg in config.SEGMENTS:
        rows = _matrix(longt[longt["type"] == seg])
        if any(r["N"] for r in rows):
            tables.append((f"{seg} (longterm): listing-day class → 3-year class (row = where it started on day 1; "
                           f"cells = % landing in each 3y class). Watch the dud-to-star and star-to-dud flows.",
                           pd.DataFrame(rows)))
    caveats += [
        "Cohort held constant (longterm, 3y-matured) so a transition reflects real migration, not a horizon mix.",
        "Listing class by day-1 pop (adj_listing_gain_open, unreliable_coverage excluded); 3y class by "
        "return-from-issue. Distinct from T3 (pop→forward-return gradient).",
        "Read the diagonal (stayed) vs off-diagonal (migrated). Small starting-classes are suppressed.",
    ]
    narrative = ("Do day-one winners stay winners? We track each IPO's class from its listing-day pop to its 3-year "
                 "standing and show the full migration — how many hot listings fade to duds, and how many quiet "
                 "listings quietly compound into stars. The dud-to-star / star-to-dud flows are the story.")
    return Finding(id="n10", title="N10 · Outcome-class migration (listing → 3y)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
