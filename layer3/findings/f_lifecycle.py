"""F · IPO lifecycle — WHEN does the move happen (time-to-peak / trough / break-even).

We have the SIZE of the within-horizon peak/trough (MFE/MAE); this finding adds the TIMING:
how many days from listing until the peak, the trough, and (for the allottee) until first back at
issue. Answers 'when does the average IPO actually peak?' and 'how long is the holder underwater?'.
Timing is entry-independent (the peak is the same price extreme for allottee and secondary buyer).
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
                lc = spine.lifecycle(sub, h)
                if lc["n_peak"] < config.MIN_N_HINT:
                    continue
                rows.append({"segment": seg, "cohort": cohort, "horizon": h, "N": lc["n_peak"],
                             "median_days_to_PEAK": lc["median_days_to_peak"],
                             "peak_IQR_days": f"{lc['p25_days_to_peak']}–{lc['p75_days_to_peak']}",
                             "% peak in 1st quarter": lc["pct_peak_in_first_quarter"],
                             "median_days_to_TROUGH": lc["median_days_to_trough"],
                             "median_days_to_breakeven(allottee)": lc["median_days_to_breakeven"]})
    tables.append(("WHEN the move happens (days from listing, maturity-gated). 'days_to_PEAK' = when the "
                   "within-horizon high was set; 'days_to_breakeven' = when the allottee first traded back at/above "
                   "issue (0 = above issue from day one). The peak clusters early — a large share of the 1-year "
                   "high is in by the first quarter — which is the timing behind 'sooner-is-better' for sellers.",
                   pd.DataFrame(rows)))
    caveats += [
        "Timing is entry-independent (the peak/trough is one price extreme); the % gain at that peak differs by "
        "entry (see the reach-curve / exit findings).",
        "Daily resolution from bhavcopy; the ~331 screener-weekly (mostly SME) names are weekly-resolution and "
        "~75 split-remediated rows have clamped extremes — timing there is approximate.",
        "Peak-timing is descriptive, not a sell signal you can act on in advance (you only know the peak in "
        "hindsight). It explains WHY holding past the early window tends to give back gains, but the no-exit-rule "
        "headline still stands: you can't reliably catch the peak.",
    ]
    narrative = ("We know how FAR IPOs move (peak/trough); this asks WHEN. How many days after listing does the "
                 "typical IPO hit its high, its low, and — for the allottee — first get back to the issue price? "
                 "The peak clusters early in year one, which is the mechanism behind the holding-period decay: the "
                 "move is front-loaded, the rest is the holder's tax.")
    return Finding(id="f_lifecycle", title="F · IPO lifecycle — when does the move happen?",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
