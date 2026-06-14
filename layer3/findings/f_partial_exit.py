"""F · The partial-exit paradox ("sell half" is a median-vs-mean trade, not a free lunch).

After the headline "no full take-profit or stop-loss beats buy-and-hold," the natural rescue is the
PARTIAL exit: book half at +T, ride the rest. This tests it. Result (both cohorts): selling half
ALWAYS lifts the median but SACRIFICES the mean wherever a real right tail exists — because IPO
returns are barbell-shaped (the median tracks the body, the mean tracks the fat tail). Secondary
buyer's view (entry=listing); the allottee additionally keeps the listing pop.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            for h in (["1y", "3y"] if cohort == "boom" else ["1y", "3y"]):
                sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), h)
                sub = sub[sub.get("listing_metrics_status") != "unreliable_coverage"] \
                    if "listing_metrics_status" in sub.columns else sub
                pe = spine.partial_exit_strategy(sub, entry="listing", horizon=h)
                if pe["n"] < config.MIN_N_HINT:
                    continue
                best = max(pe["ladder"], key=lambda r: (r["mean_captured_%"] or -1e9))
                bestmed = max(pe["ladder"], key=lambda r: (r["median_captured_%"] or -1e9))
                rows.append({"segment": seg, "cohort": cohort, "horizon": h, "N": pe["n"],
                             "HOLD_median_%": pe["hold_median_%"], "HOLD_mean_%": pe["hold_mean_%"],
                             "best_partial_median_%": bestmed["median_captured_%"],
                             "best_partial_mean_%": best["mean_captured_%"],
                             "median_lifted": bool((bestmed["median_captured_%"] or -1e9) > (pe["hold_median_%"] or 0)),
                             "mean_winner": ("partial" if (best["mean_captured_%"] or -1e9) > (pe["hold_mean_%"] or 0) else "HOLD")})
    tables.append(("'Sell half at +T, ride the rest' (best target shown) vs pure HOLD, secondary buyer, "
                   "maturity-gated. Watch the two right columns: the median is lifted everywhere, but the "
                   "mean winner is HOLD wherever a right tail exists (it only loses in tail-less losing "
                   "segments). Selling half converts a tail-harvester into a typical-name harvester.",
                   pd.DataFrame(rows)))
    caveats += [
        "Partial = sell 50% at the first touch of +T (else hold to horizon end); upper-bound optimistic "
        "(assumes you exit exactly at T). Net-of-cost effects are small at one round-trip and omitted here.",
        "The median-up / mean-down split is the signature of a barbell distribution (see the basket-dispersion "
        "finding) — it is NOT a free lunch, it is a choice between the typical outcome and the expected outcome.",
        "Secondary-buyer view; excludes `unreliable_coverage` listing rows.",
    ]
    narrative = ("If neither a full take-profit nor a stop beats holding, surely selling HALF does — bank some, "
                 "ride the rest? We test it across both eras. The answer is a paradox: selling half reliably "
                 "improves the TYPICAL (median) outcome but bleeds the AVERAGE (mean) wherever IPOs have a fat "
                 "right tail, because you keep trimming the future multibaggers that carry the average.")
    return Finding(id="f_partial", title="F · The partial-exit paradox (sell half: median up, mean down)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
