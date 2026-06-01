"""F · The "buy every IPO" basket is a barbell — the mean is a top-5% mirage.

"IPOs make money on average" is true and useless: in every segment×cohort the MEDIAN sits at or
below ~0 and the % positive is ≤~50%, while the mean is carried entirely by a handful of moonshots.
Strip the top 5% and the mean collapses. The lesson the predictor leans on: report the distribution,
size for the body, never bank the mean — and never concentrate (you'll likely miss the moonshot).
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
                bd = spine.basket_dispersion(sub, h, entry="listing")
                if bd.get("insufficient"):
                    continue
                rows.append({"segment": seg, "cohort": cohort, "horizon": h, "N": bd["n"],
                             "mean_%": bd["mean_%"], "MEDIAN_%": bd["median_%"],
                             "pct_positive": round(100 * bd["pct_positive"], 1),
                             "p90_%": bd["p90_%"],
                             "top_5%_mean_%": bd.get("top_5%_mean_%"),
                             "mean_EXCL_top5_%": bd["mean_ex_top_%"]})
    tables.append(("Buy-every-IPO basket (secondary buyer, raw return, maturity-gated). The mean is NOT the "
                   "experience: the MEDIAN is at/below ~0 and ≤~50% end positive, while a top-5% of moonshots "
                   "produce most of the mean — strip them ('mean_EXCL_top5') and it collapses. Same sign in "
                   "both eras.", pd.DataFrame(rows)))
    caveats += [
        "This barbell is GENERAL to IPOs (MB and SME both) — it is the structural reason single-name entry/exit "
        "timing fights a losing battle against dispersion, and why the predictor reports a DISTRIBUTION, not a "
        "point forecast.",
        "Right-skew: returns are bounded at −100% but unbounded up, so the mean is dominated by survivors that "
        "compound while the typical name drifts sideways/down. 'Buy every IPO' needs the WHOLE basket (miss the "
        "moonshot and you get the median) — concentration is ruinous.",
        "Secondary-buyer view; long horizons carried by the longterm cohort.",
    ]
    narrative = ("Is a diversified basket of every IPO a sound passive bet because 'IPOs make money on average'? "
                 "The average is real but un-bankable: in every era and segment the typical (median) IPO returns "
                 "about nothing and barely half end positive — the mean is a mirage produced by the top 5%. "
                 "Report the distribution, never the mean.")
    return Finding(id="f_basket", title="F · Buy-every-IPO basket is a barbell (mean = top-5% mirage)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
