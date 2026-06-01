"""T9 — Profitable-at-IPO premium.

Profitable (pre_ipo_pat > 0) vs loss-making at IPO: median alpha at 1y/3y/5y + wipeout — and
does the gap WIDEN with horizon? Stratified by COHORT, because the profitable flag is
boom-skewed (90% boom vs ~27–34% longterm-MB), so a pooled comparison would be a cohort
confound (methodology caveat). Per segment within cohort where N allows.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _profit_flag(g):
    pat = pd.to_numeric(g.get("pre_ipo_pat"), errors="coerce")
    return pat > 0, pat.notna()


def _rows(sub, cohort, seg, horizons):
    prof_mask, known = _profit_flag(sub)
    rows = []
    for label, mask in [("profitable at IPO", prof_mask & known),
                        ("loss-making at IPO", (~prof_mask) & known)]:
        g = sub[mask]
        rec = {"cohort": cohort, "segment": seg, "group": label, "N": len(g)}
        for h in horizons:
            gm = spine.maturity_gated(g, h)
            # guard each horizon by its OWN matured N (the row's N is the group total)
            med = spine.distribution(spine.alpha_series(gm, h))["median"] if len(gm) >= config.MIN_N_HINT else None
            rec[f"median_alpha_{h}_%"] = _p(med)
        rec["wipeout_lower_%"] = _p(spine.wipeout_band(g)["wipeout_lower_rate"])
        rows.append(rec)
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    for cohort in config.COHORTS:
        horizons = ["1y", "3y"] if cohort == "boom" else config.KEY_HORIZONS   # boom 5y too young
        for seg in config.SEGMENTS:
            rows += _rows(spine.segment(df, segment=seg, cohort=cohort), cohort, seg, horizons)
    tables.append(("Profitable vs loss-making at IPO, BY COHORT × SEGMENT (the flag is boom-skewed and SME≠MB, so "
                   "neither is pooled). 5y shown for longterm only. Each horizon cell is guarded by its own matured "
                   "N (a sub-floor horizon shows '—'). Does the profitable premium widen with horizon?",
                   pd.DataFrame(rows)))

    # longterm MB has both groups matured at 5y -> the clean widening test there
    from layer3 import charts as ch
    lt = pd.DataFrame(_rows(spine.segment(df, segment="MB", cohort="longterm"), "longterm", "MB",
                            config.KEY_HORIZONS))
    series = {}
    for _, r in lt.iterrows():
        series[r["group"]] = [r.get(f"median_alpha_{h}_%") or 0 for h in config.KEY_HORIZONS]
    charts.append(("Longterm Mainboard: median alpha by horizon, profitable vs loss-making at IPO",
                   ch.line_png(config.KEY_HORIZONS, series,
                               title="Profitable-at-IPO premium by horizon (longterm MB)",
                               ylabel="median alpha %", xlabel="horizon")))

    caveats += [
        "pre_ipo_pat coverage is boom-heavy (90%+ boom vs ~27–34% longterm-MB) — comparisons are WITHIN cohort to "
        "avoid a profitability×era confound.",
        "Profitability is the cleanest quality signal; PE/growth are noisier and deferred to the composite.",
        "pre-IPO financials come from RHP/screener — provenance-graded as moderately reliable.",
    ]
    narrative = ("Do companies already profitable at IPO outperform the loss-makers — and does that edge widen the "
                 "longer you hold? Profitability is the one quality signal hard to dress up, so we test it directly, "
                 "kept within each era because recent IPOs are far more often profitable than old ones.")
    return Finding(id="t9", title="T9 · Profitable-at-IPO premium",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
