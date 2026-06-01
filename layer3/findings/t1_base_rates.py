"""T1 — Lasting-wealth base rates (the anchor truth of the tool).

Per segment (MB/SME) × cohort × horizon: maturity-gated alpha distribution + the headline
base rates, all horizon-specific (NOT lifetime current_return — that age-mixes, methodology
fix #5). Multibagger here = horizon return_from_issue >= 1.0 (a 2x), measured only on IPOs
old enough for that horizon. Wipeout is reported separately as a competing-risks BAND.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rates(sub, h):
    g = spine.maturity_gated(sub, h)                       # only IPOs old enough for horizon h
    n = len(g)
    a = spine.alpha_series(g, h)
    rfi = pd.to_numeric(g.get(f"return_from_issue_{h}"), errors="coerce").dropna()
    d = spine.distribution(a)
    return {
        "N": n,
        "median_alpha_%": _p(d["median"]),
        "p10_%": _p(d["p10"]), "p90_%": _p(d["p90"]),
        "pct_positive_alpha": _p(spine.proportion(a > 0)["rate"]),
        "pct_2x_from_issue": _p(spine.proportion(rfi >= 1.0)["rate"]),
        "pct_below_issue": _p(spine.proportion(rfi < 0)["rate"]),
    }


def compute(df):
    tables, charts, caveats = [], [], []

    # base-rate table: segment × cohort × horizon (long horizons -> longterm carries them)
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.segment(df, segment=seg, cohort=cohort)
            # boom long-horizon (5y) is early-survivor-biased and tiny -> longterm carries it
            horizons = ["1y", "3y"] if cohort == "boom" else config.KEY_HORIZONS
            for h in horizons:
                r = {"segment": seg, "cohort": cohort, "horizon": h}
                r.update(_rates(sub, h))
                rows.append(r)
    tables.append(("Base rates by segment × cohort × horizon (alpha vs Nifty 50, maturity-gated). "
                   "5y is shown for the longterm cohort only (boom IPOs aren't mature enough — that "
                   "long-horizon truth is longterm-carried). Sub-floor cells (N<10) are suppressed.",
                   pd.DataFrame(rows)))

    # lifetime wipeout / survival band by segment × cohort (competing risks)
    wb_rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.segment(df, segment=seg, cohort=cohort)
            wb = spine.wipeout_band(sub)
            wb_rows.append({"segment": seg, "cohort": cohort, "N": wb["n"],
                            "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                            "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    tables.append(("Lifetime wipeout BAND by segment × cohort (competing risks). Lower = confirmed "
                   "~-100% outcomes; upper adds delisted-with-unknown-reason. The truth is in between.",
                   pd.DataFrame(wb_rows)))

    # chart: median 1y alpha, MB vs SME, by cohort (short horizon both cohorts have N)
    from layer3 import charts as ch
    labs, vals, ns = [], [], []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), "1y")
            d = spine.distribution(spine.alpha_series(sub, "1y"))
            labs.append(f"{seg}-{cohort}"); vals.append((d["median"] or 0) * 100); ns.append(d["n"])
    charts.append(("Median 1-year alpha (%) by segment × cohort", ch.bar_png(
        labs, vals, ns=ns, title="Median 1y alpha by segment × cohort", ylabel="median alpha %")))

    caveats += [
        "Alpha is measured FROM THE LISTING PRICE (the price a public investor can buy at) vs Nifty over the same "
        "window — the secondary-buyer's market-adjusted return. The allottee additionally captures the listing pop "
        "(%2x and %below-issue columns are from the ISSUE price = the allottee's view). So 'median alpha' (secondary) "
        "and '%2x from issue' (allottee) answer two different questions — read them together.",
        "Multibagger here = horizon return ≥ 2x (return_from_issue ≥ 1.0), maturity-gated — NOT the lifetime "
        "outcome_class label (which age-mixes a 1y-old IPO with a 19y-old one).",
        "SME long-horizon survivors are illiquid; treat SME 5y medians as directional, not tradable.",
        "Wipeout is a band because delist_reason exists for only ~40 of ~200 delistings.",
    ]
    narrative = ("How often does an Indian IPO actually build lasting wealth — beat the index, double, or go to "
                 "near-zero — split by Mainboard vs SME and by era, always maturity-gated and shown as a "
                 "distribution with N. This is the anchor every other finding and the predictor lean on.")
    return Finding(id="t1", title="T1 · Lasting-wealth base rates",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
