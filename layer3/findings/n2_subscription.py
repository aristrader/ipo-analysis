"""N2 — Subscription-vs-outcome curve, with a saturation / mean-reversion test.

Bucket sub_total_x into demand bands → per band: median listing pop, median forward alpha, %
below-issue, wipeout. Key question is the SHAPE: does forward alpha rise with demand, or PEAK
then mean-revert at extreme oversubscription ("everyone piled in → priced for perfection → fades")?
Subscription is OFFICIAL + hard-to-fake (unlike GMP). SINGLE-REGIME: longterm subscription coverage
≈0, so this is a BOOM-cohort rule and cannot be cross-regime validated. MB/SME never pooled.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

BANDS = [("<1x (under)", -1, 1), ("1–5x", 1, 5), ("5–15x", 5, 15),
         ("15–50x", 15, 50), ("50–100x", 50, 100), (">100x", 100, 1e9)]


def _rows(sub):
    rows = []
    for label, lo, hi in BANDS:
        s = pd.to_numeric(sub["sub_total_x"], errors="coerce")
        b = sub[(s > lo) & (s <= hi)]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        pop = pd.to_numeric(b["adj_listing_gain_open"], errors="coerce")
        cri = pd.to_numeric(b.get("current_return_from_issue"), errors="coerce")
        rows.append({"sub_total_x_band": label, "N": len(b),
                     "median_listing_pop_%": _p(pop.median()),                  # the demand→pop leg
                     "median_alpha_1y_%": _p(spine.distribution(spine.alpha_series(g1, "1y"))["median"]),
                     "N_1y": len(g1),
                     "median_alpha_3y_%": _p(spine.distribution(spine.alpha_series(g3, "3y"))["median"]),
                     "N_3y": len(g3),
                     "wipeout_lower_%": _p(spine.wipeout_band(b)["wipeout_lower_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    boom = spine.segment(df, cohort="boom")    # subscription is boom-only
    for seg in config.SEGMENTS:
        tables.append((f"{seg} (BOOM only): subscription band → listing pop + forward alpha + wipeout. Look for "
                       f"SATURATION — does forward alpha peak then fade at extreme oversubscription?",
                       pd.DataFrame(_rows(boom[boom["type"] == seg]))))

    from layer3 import charts as ch
    mb = pd.DataFrame(_rows(boom[boom["type"] == "MB"]))
    charts.append(("Mainboard (boom): listing pop vs forward 1y alpha by subscription band "
                   "(demand→pop should rise; forward alpha is the saturation test)",
                   ch.line_png(mb["sub_total_x_band"].tolist(),
                               {"median listing pop %": [v or 0 for v in mb["median_listing_pop_%"]],
                                "median 1y alpha %": [v or 0 for v in mb["median_alpha_1y_%"]]},
                               title="MB boom: pop & forward alpha vs subscription",
                               ylabel="%", xlabel="subscription band")))

    caveats += [
        "⚠ SINGLE-REGIME (boom only): longterm subscription coverage ≈ 0, so this CANNOT be cross-regime validated — "
        "treat as a boom-cohort hypothesis, not a regime-robust truth.",
        "Two legs kept apart: demand→listing-pop (does subscription predict the day-1 pop?) vs demand→forward-alpha "
        "(does it predict beating the index later?). They can diverge — that IS the saturation story.",
        "Subscription is official/hard-to-fake (unlike GMP), but sub-floor bands are suppressed; MB/SME apart.",
    ]
    narrative = ("Does heavy oversubscription predict a winner — or does it mean-revert? Subscription is the official "
                 "demand number every retail investor sees. We trace listing pop AND forward alpha across demand "
                 "bands: demand should drive the day-1 pop, but a saturation point (where more subscription stops "
                 "predicting and starts hurting forward alpha) would be a genuinely tradable truth. Boom-cohort only.")
    return Finding(id="n2", title="N2 · Subscription-vs-outcome (saturation test, boom-only)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
