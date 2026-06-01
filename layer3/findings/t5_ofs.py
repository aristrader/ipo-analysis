"""T5 — OFS / skin-in-the-game gradient.

Dose-response of long-term alpha + wipeout across ofs_pct buckets (high OFS = insiders cashing
out, no fresh capital). ofs_pct is 100% covered across all cohorts/segments. Long-horizon
alpha read off the longterm cohort (matured); per segment.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

# ofs_pct is on a 0–100 scale in the data
BUCKETS = [("0% (all fresh)", -0.01, 0.0001), ("0–25%", 0.0001, 25), ("25–50%", 25, 50),
           ("50–75%", 50, 75), ("75–100% (mostly OFS)", 75, 100.01)]


def _rows(sub, horizon):
    rows = []
    for label, lo, hi in BUCKETS:
        ofs = pd.to_numeric(sub["ofs_pct"], errors="coerce")
        b = sub[(ofs > lo) & (ofs <= hi)] if lo > -0.01 else sub[ofs <= hi]
        gm = spine.maturity_gated(b, horizon)
        wb = spine.wipeout_band(b)
        rows.append({"ofs_bucket": label, "N": len(b), "N_matured": len(gm),
                     f"median_alpha_{horizon}_%": _p(spine.distribution(spine.alpha_series(gm, horizon))["median"]),
                     "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                     "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    longt = spine.segment(df, cohort="longterm")
    for seg in config.SEGMENTS:
        sub = longt[longt["type"] == seg]
        tables.append((f"{seg} (longterm): OFS% bucket → median 3y alpha + wipeout band. "
                       f"Is more insider cash-out (higher OFS, no fresh capital) associated with worse outcomes?",
                       pd.DataFrame(_rows(sub, "3y"))))

    from layer3 import charts as ch
    mb = pd.DataFrame(_rows(longt[longt.type == "MB"], "3y"))
    charts.append(("Mainboard (longterm): median 3y alpha by OFS bucket",
                   ch.bar_png(mb["ofs_bucket"].tolist(),
                              [v if v is not None else 0 for v in mb["median_alpha_3y_%"]],
                              ns=mb["N_matured"].tolist(),
                              title="MB: median 3y alpha by OFS%", ylabel="median 3y alpha %")))

    caveats += [
        "ofs_pct is fully covered (100%). High OFS in mature large-caps is often a clean PE exit (confound) — "
        "read the gradient within a segment, and pair with T9 (profitability) and mcap.",
        "Long-horizon alpha is longterm-cohort only; boom OFS effects can't be 3y-validated yet.",
        "Promoter post-issue holding (a related skin-in-game signal) is only ~34% covered — deferred.",
    ]
    narrative = ("When insiders use an IPO mostly to cash out (high Offer-For-Sale, little fresh capital raised), "
                 "do the shares do worse afterwards? We trace the dose-response of long-term alpha and wipeout "
                 "across OFS buckets — a structural, hard-to-game signal available for every IPO.")
    return Finding(id="t5", title="T5 · OFS / skin-in-the-game gradient",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
