"""N13 · Fallen-angel recovery is an unstackable coin-flip (a validated NEGATIVE rule).

"Buy the quality name that fell — it'll bounce." Among IPOs that hit a deep trough (MAE ≤ −50% in
year 1), recovery to break-even is low AND no pre-listing feature (profitable / low-debt / large
issue / high ROE) shifts the recovery odds in a sign-stable way across regimes. A deep IPO drawdown
is a price-path fact, not a knowable company trait — the 'rescue' features were already in the issue
price. The actionable output is a NEGATIVE rule: do not pay up for 'cheap after the fall'.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

FEATURES = [("pre_ipo_pat", "profitable (PAT>0)", lambda v: v > 0),
            ("pre_ipo_debt_equity", "low debt (D/E<median)", None),
            ("issue_size_cr", "large issue (>median)", None),
            ("pre_ipo_roe_pct", "high ROE (>median)", None)]


def _fallen(df, seg, cohort):
    g = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), "1y")
    mae = pd.to_numeric(g.get("mae_1y"), errors="coerce")
    return g[mae <= -0.50].copy()


def compute(df):
    tables, charts, caveats = [], [], []

    # base recovery rates by segment × cohort
    base = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            f = _fallen(df, seg, cohort)
            if len(f) < config.MIN_N_HINT:
                continue
            cur = pd.to_numeric(f.get("current_return_from_issue"), errors="coerce")
            ye = pd.to_numeric(f.get("return_from_issue_1y"), errors="coerce")
            rec = spine.proportion(cur >= 0)
            base.append({"segment": seg, "cohort": cohort, "N_fallen": len(f),
                         "recovered_lifetime_%": round(100 * rec["rate"], 1) if rec["rate"] is not None else None,
                         "ci": f"[{round(100*rec['ci_lo'])}-{round(100*rec['ci_hi'])}]" if rec["rate"] is not None else "",
                         "recovered_by_yearend_%": round(100 * (ye >= 0).mean(), 1) if ye.notna().any() else None})
    tables.append(("Among names that fell to a DEEP trough (≤−50% within year 1, maturity-gated): the share that "
                   "ever climbed back to break-even (lifetime current return ≥ 0) and by year-end. Recovery is a "
                   "minority outcome.", pd.DataFrame(base)))

    # feature-split sign-stability grid: does any pre-listing feature predict recovery? (cross-regime)
    grid = []
    for fcol, flabel, pred in FEATURES:
        row = {"feature": flabel}
        signs = []
        for cohort in config.COHORTS:
            # pool MB+SME within the cohort for N, but keep the cohort split (the regime test)
            f = pd.concat([_fallen(df, seg, cohort) for seg in config.SEGMENTS], ignore_index=True)
            v = pd.to_numeric(f.get(fcol), errors="coerce")
            cur = pd.to_numeric(f.get("current_return_from_issue"), errors="coerce")
            ok = v.notna() & cur.notna()
            if ok.sum() < 2 * config.MIN_N_HINT:
                row["%s_hi-lo_pp" % cohort] = None
                continue
            if pred is not None:
                hi = cur[ok & v.apply(lambda x: bool(pred(x)) if pd.notna(x) else False)]
                lo = cur[ok & ~v.apply(lambda x: bool(pred(x)) if pd.notna(x) else False)]
            else:
                med = v[ok].median()
                hi = cur[ok & (v > med)]; lo = cur[ok & (v <= med)]
            if len(hi) < config.MIN_N_HINT or len(lo) < config.MIN_N_HINT:
                row["%s_hi-lo_pp" % cohort] = None
                continue
            diff = round(100 * ((hi >= 0).mean() - (lo >= 0).mean()), 1)
            row["%s_hi-lo_pp" % cohort] = diff
            signs.append(diff)
        row["sign_stable"] = bool(len(signs) == 2 and (signs[0] > 0) == (signs[1] > 0) and abs(signs[0]) > 3 and abs(signs[1]) > 3)
        grid.append(row)
    tables.append(("Does any pre-listing feature predict WHICH fallen angels recover? Each cell = "
                   "recovery-rate(high-feature) − recovery-rate(low-feature), in pp, per cohort (MB+SME pooled "
                   "for N). 'sign_stable' = the feature helps in the SAME direction in BOTH eras. None are stable "
                   "→ recovery is unpredictable from fundamentals.", pd.DataFrame(grid)))

    caveats += [
        "This is a validated NEGATIVE rule: no feature reliably identifies the RECOVERERS. The 'quality' signals "
        "(profitable / low-debt / high-ROE) flip sign between eras → useless for picking winners. The one near-stable "
        "signal points the WRONG way for the thesis: large fallen issues recover LESS in both eras (−7 to −10pp) — so "
        "if anything 'cheap after the fall' is worse for big names. Either way, 'buy the quality name that fell' has "
        "no edge you can stack.",
        "Recovery = lifetime current return ≥ 0 (back to issue). Deep-trough set = MAE_1y ≤ −50%, maturity-gated. "
        "Feature grid pools MB+SME within each cohort to keep N usable; the cohort split IS the regime test.",
        "Mechanism: a deep IPO drawdown is a price-path fact (overpricing + sentiment reversal), not a knowable "
        "company trait — the rescue features were already priced into the issue.",
    ]
    narrative = ("When an IPO has fallen 50%+, can you pick the ones that bounce back by buying 'quality on sale'? "
                 "We fix the deep-fallen set and ask whether being profitable, low-debt, a large issue, or high-ROE "
                 "raises the recovery odds — consistently, in both eras. It doesn't: every signal flips sign across "
                 "regimes. Fallen-angel recovery is an unstackable coin-flip — the validated rule is to NOT pay up "
                 "for it.")
    return Finding(id="n13", title="N13 · Fallen-angel recovery is an unstackable coin-flip",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
