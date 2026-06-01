"""N12 — Lead-manager (banker) league table — DESCRIPTIVE ONLY.

lead_manager is 100% covered. Users always ask "is a top banker's IPO safer?". We show, per
lead manager (min-N), the deal count + median forward alpha + wipeout rate. IMPORTANT: the
ideation check found NO clean banker→alpha signal, so this is reported as descriptive context
ONLY and is deliberately NOT a scorecard input (avoids a spurious 'trust the banker' signal).
MB and SME apart (different banker universes).
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

MIN_DEALS = 15


def _split_managers(s):
    # a deal can list multiple lead managers separated by | , ; / and
    parts = []
    for sep in ["|", ";", ",", " and "]:
        if sep in str(s):
            return [p.strip() for p in str(s).replace(";", "|").replace(",", "|").replace(" and ", "|").split("|") if p.strip()]
    return [str(s).strip()] if pd.notna(s) and str(s).strip() else []


def _rows(sub):
    sub = sub.copy()
    sub["_mgrs"] = sub["lead_manager"].map(_split_managers)
    ex = sub.explode("_mgrs")
    rows = []
    for mgr, g in ex.groupby("_mgrs"):
        if not mgr or len(g) < MIN_DEALS:
            continue
        g1 = spine.maturity_gated(g, "1y")
        rows.append({"lead_manager": mgr[:34], "N_deals": len(g),
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]),
                     "pct_below_issue_1y": _p(spine.proportion(
                         pd.to_numeric(g1.get("return_from_issue_1y"), errors="coerce").dropna() < 0)["rate"]),
                     "wipeout_lower_%": _p(spine.wipeout_band(g)["wipeout_lower_rate"])})
    return sorted(rows, key=lambda r: -r["N_deals"])[:15]


def compute(df):
    tables, charts, caveats = [], [], []
    for seg in config.SEGMENTS:
        rows = _rows(df[df["type"] == seg])
        if rows:
            tables.append((f"{seg}: most active lead managers (≥{MIN_DEALS} deals) — deal count + median 1y alpha + "
                           f"wipeout. DESCRIPTIVE ONLY (no clean banker→alpha signal — not a score input).",
                           pd.DataFrame(rows)))
    caveats += [
        "DESCRIPTIVE ONLY: the ideation/empirical check found no robust banker-tier → alpha relationship, so this is "
        "NOT a scorecard component and should not be read as 'this banker = safer'. It's context users ask for.",
        "A deal with multiple lead managers is counted under each (exploded); min 15 deals to appear. MB/SME apart "
        "(different banker universes).",
        "Selection effects abound (top bankers take bigger/better deals anyway) — do not infer causation.",
    ]
    narrative = ("Does a marquee investment bank running the IPO mean it's safer? We tabulate the most active lead "
                 "managers with their deal count, median 1-year alpha, and wipeout rate. We show it because everyone "
                 "asks — but flag clearly that there's no clean banker→outcome signal, so it never feeds the score.")
    return Finding(id="n12", title="N12 · Lead-manager league table (descriptive only)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
