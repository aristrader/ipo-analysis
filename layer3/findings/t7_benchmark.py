"""T7 — Benchmarking discipline + alpha coverage + data-integrity (bias) audit.

Correctness-infra that doubles as a finding (and N12 from the enhancement list): makes every
other finding's denominators transparent, documents the benchmark policy, and audits whether
the rows we EXCLUDE (unreliable_coverage / low quality) are systematically worse outcomes —
which would silently bias every base rate.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def compute(df):
    tables, charts, caveats = [], [], []

    # ---- alpha coverage by horizon × cohort (the denominators behind every finding)
    rows = []
    for cohort in config.COHORTS:
        sub = spine.segment(df, cohort=cohort)
        for h in config.HORIZONS:
            n = int(spine.alpha_series(sub, h).notna().sum())
            rows.append({"cohort": cohort, "horizon": h, "N_with_alpha": n,
                         "pct_of_cohort": round(100 * n / max(len(sub), 1), 1)})
    cov = pd.DataFrame(rows)
    tables.append(("Alpha (vs Nifty 50) coverage by horizon × cohort — the maturity-gated "
                   "denominators. Note boom long-horizon N collapses (IPOs aren't old enough): "
                   "3y/5y/10y truths are carried by the longterm cohort.", cov))
    charts.append(("Alpha coverage by horizon (boom vs longterm) — why long horizons are longterm-carried",
                   _cov_chart(df)))

    # ---- Smallcap-250 coverage (secondary benchmark, 2017+)
    sc = pd.DataFrame([{"horizon": h,
                        "N_nifty_alpha": int(spine.alpha_series(df, h, "nifty").notna().sum()),
                        "N_smallcap_alpha": int(spine.alpha_series(df, h, "smallcap").notna().sum())}
                       for h in config.KEY_HORIZONS])
    tables.append(("Nifty-50 vs Smallcap-250 alpha coverage. Small/micro caps are benchmarked to "
                   "Smallcap-250 where available (2017+); pre-2017 and mid/large use Nifty-50.", sc))

    # ---- data-integrity / selection-bias audit (N12): are EXCLUDED rows worse?
    df2 = df.copy()
    df2["trusted_listing"] = df2["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)
    audit = []
    for label, mask in [("listing OK/recovered (kept in T3)", df2["trusted_listing"]),
                        ("listing unreliable (excluded from T3)", ~df2["trusted_listing"]),
                        ("data_quality high+med", df2["data_quality_tier"].isin(["high", "med"])),
                        ("data_quality low (often excluded)", df2["data_quality_tier"] == "low")]:
        g = df2[mask]
        wb = spine.wipeout_band(g)
        med = spine.distribution(spine.alpha_series(g, "1y"))
        audit.append({"group": label, "N": len(g),
                      "median_alpha_1y_%": _pct(med["median"]),
                      "wipeout_rate_lower_%": _pct(wb["wipeout_lower_rate"]),
                      "wipeout_rate_upper_%": _pct(wb["wipeout_upper_rate"])})
    tables.append(("Selection-bias audit (N12): if the EXCLUDED groups have systematically worse "
                   "outcomes, every base rate is optimistically biased. Compare the kept vs excluded rows.",
                   pd.DataFrame(audit)))

    caveats += [
        "Alpha is vs Nifty 50 for all; Smallcap-250 alpha (alpha_sc_*) covers only listings from 2017-04-03. "
        "Do not read a benchmark switch as a real alpha change.",
        "Long-horizon (3y/5y/10y) findings default to the LONGTERM cohort; boom long-horizon N is too small "
        "(maturity-gating) to be a base rate.",
        "If the bias-audit shows excluded rows are much worse, treat headline survival/return rates as upper bounds.",
    ]
    narrative = ("Before any pattern: what can we actually measure, against what benchmark, and is what we "
                 "drop biasing the rest? Alpha is measured vs Nifty 50 (Smallcap-250 for small/micro, 2017+). "
                 "Coverage shrinks with horizon — long-horizon base rates come from the 2006–19 cohort, "
                 "not the boom cohort. The bias audit checks our exclusions aren't hiding the losers.")
    return Finding(id="t7", title="T7 · Benchmarking, coverage & bias audit",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _cov_chart(df):
    from layer3 import charts
    xs = config.HORIZONS
    series = {c: [int(spine.alpha_series(spine.segment(df, cohort=c), h).notna().sum())
                  for h in xs] for c in config.COHORTS}
    return charts.line_png(xs, series, title="Alpha coverage (N) by horizon",
                           ylabel="N with alpha", xlabel="horizon")


def _pct(x):
    return None if x is None else round(100 * x, 1)
