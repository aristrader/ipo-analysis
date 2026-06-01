"""F · Averaging down on a fallen IPO — lowers your cost, rarely your loss (a 'what NOT to do').

"A quality IPO that's fallen 30–50% is on sale — average down." The apparent improvement from
averaging down is ARITHMETIC dilution (you lowered your cost), not recovery. The decision-relevant
numbers: among names that fell to −D within the horizon, only a small minority END back above the
buyer's entry, and the SECOND tranche (bought at −D) is itself a median loser at 1y in both cohorts.
A deep early drawdown is information (momentum/quality), not a discount.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            for h in ("1y", "3y"):
                sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), h)
                sub = sub[sub.get("listing_metrics_status") != "unreliable_coverage"] \
                    if "listing_metrics_status" in sub.columns else sub
                ad = spine.average_down(sub, entry="listing", horizon=h)
                for lad in ad["ladder"]:
                    if lad.get("insufficient"):
                        continue
                    rows.append({"segment": seg, "cohort": cohort, "horizon": h, "dip": lad["dip"],
                                 "dipper_N": lad["dipper_n"],
                                 "hold_median_%": lad["hold_median_%"],
                                 "avg_down_blended_median_%": lad["blended_median_%"],
                                 "pct_recovered_above_entry": lad["pct_recovered_above_entry"],
                                 "2nd_tranche_median_%": lad["tranche2_median_%"],
                                 "2nd_tranche_pct_positive": lad["tranche2_pct_positive"]})
    tables.append(("Among secondary-buyer names that fell to −D within the horizon: HOLD vs AVERAGE-DOWN "
                   "(a second equal tranche at −D). The blended number looks 'better' but that's just "
                   "arithmetic (lower cost). The honest columns are the last three: how few recover above "
                   "entry, and that the SECOND tranche (buying more at −D) is itself a median loser.",
                   pd.DataFrame(rows)))
    caveats += [
        "The blended 'improvement' is guaranteed dilution (you lowered average cost), NOT a recovery signal — "
        "read it as a warning, not an endorsement.",
        "Decision-relevant: `pct_recovered_above_entry` (a minority at 1y in both cohorts) and the 2nd-tranche "
        "standalone outcome (median LOSER at 1y). The one exception — SME/boom 3y — is the boom liquidity tide, "
        "not a cross-regime truth (it flips negative in longterm), so the sign is NOT stable → don't trust it.",
        "Mechanism: a deep early IPO drawdown is momentum/quality information (the long left body of the barbell), "
        "so averaging down doubles your exposure to exactly the population that keeps falling.",
        "Secondary-buyer view; excludes `unreliable_coverage`; ~75 clamped rows floor the trough (conservative).",
    ]
    narrative = ("'It's fallen 40% — average down and lower your cost.' We test it: among IPOs that cratered to "
                 "−30/−50% within the horizon, how many actually climb back above where you bought, and is buying "
                 "a SECOND tranche at the bottom a winner? Mostly no — the dip is information, not a discount, and "
                 "the lower 'blended cost' is arithmetic that hides a second losing trade stacked on the first.")
    return Finding(id="f_avgdown", title="F · Averaging down rarely recovers (a 'what NOT to do')",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
