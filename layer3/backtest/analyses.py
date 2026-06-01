"""Extra backtest analyses (Wave-3 additions): holding-period sweep, portfolio-level summary,
the flip's allotment-realism EV, and the exit-discipline backtest. Honest about our data limits —
we have a daily/weekly summary grid (alpha_*, max_drawdown) PLUS within-horizon peak/trough
(MFE/MAE), but NOT intraday paths. So a take-profit / stop-loss can be backtested SINGLY (MFE for
TP, MAE for SL) but NOT combined (we can't see which was touched first); and no Sharpe (no series).
"""
import pandas as pd
from layer3 import spine, config
from layer3.backtest.engine import COST_SECONDARY


def exit_discipline_backtest(df, horizon="1y"):
    """Does a take-profit rule beat just holding? Per segment × cohort × entry (allottee/secondary),
    for each target T: the exit rule captures +T if the price ever touched it (MFE), else holds to
    the endpoint — net of one round-trip cost. Compared to plain buy-and-hold. Reported as RAW
    return (the target is a price level, not an index-relative number). A rule only 'beats hold' if
    its mean > buy-and-hold mean; a real signal must beat in BOTH cohorts (cross-regime)."""
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), horizon)
            for entry in ("issue", "listing"):
                s = sub
                if entry == "listing" and "listing_metrics_status" in s.columns:
                    s = s[s["listing_metrics_status"] != "unreliable_coverage"]
                es = spine.exit_strategy(s, entry=entry, horizon=horizon)
                if es["n"] < config.MIN_N_HINT:
                    continue
                # buy-and-hold baseline = the raw endpoint mean, computed on the SAME sample the rule
                # uses (mfe & endpoint both present) so rule_mean and buy_hold_mean share one denominator
                # — else the older weekly/listing-era rows (endpoint but no daily-high MFE) bias the hold.
                mfe_c, _, end_c = spine._entry_cols(entry, horizon)
                mfe_v = pd.to_numeric(s.get(mfe_c), errors="coerce")
                end_v = pd.to_numeric(s.get(end_c), errors="coerce")
                endser = end_v[mfe_v.notna() & end_v.notna()]
                hold_mean = round(100 * (endser.mean() - COST_SECONDARY), 1) if len(endser) else None
                for lad in es["ladder"]:
                    if lad["exit_rule"] not in ("+20%", "+50%", "+100%"):
                        continue
                    mean_net = round(lad["mean_captured_%"] - 100 * COST_SECONDARY, 1) \
                        if lad["mean_captured_%"] is not None else None
                    rows.append({"segment": seg, "cohort": cohort, "entry": entry, "target": lad["exit_rule"],
                                 "N": es["n"], "pct_hit_target": lad["pct_got_the_exit"],
                                 "rule_mean_%": mean_net, "buy_hold_mean_%": hold_mean,
                                 "beats_hold": (mean_net is not None and hold_mean is not None
                                                and mean_net > hold_mean)})
    return pd.DataFrame(rows)


def holding_period_sweep(df, segment, benchmark="nifty"):
    """Secondary buy-at-listing, exit at each horizon → 'when do I sell?' (alpha, net of cost)."""
    sub = spine.segment(df, segment=segment)
    rows = []
    for h in config.HORIZONS:
        a = (spine.alpha_series(spine.maturity_gated(sub, h), h, benchmark) - COST_SECONDARY).dropna()
        rec = {"exit": h, "N": len(a)}
        if len(a) >= config.MIN_N_HINT:
            rec.update({"median_alpha_%": round(100 * a.median(), 1),
                        "mean_alpha_%": round(100 * a.mean(), 1),
                        "win_rate_%": round(100 * (a > 0).mean(), 1)})
        rows.append(rec)
    return pd.DataFrame(rows)


def portfolio_summary(df, horizon="1y"):
    """Equal-weight 'buy every IPO at listing' BASKET vs the do-nothing baseline (index = alpha 0).
    Reports a dispersion-adjusted return (mean/std) — labelled crudely, NOT a Sharpe (no time series)."""
    rows = []
    for seg in config.SEGMENTS:
        a = (spine.alpha_series(spine.maturity_gated(spine.segment(df, segment=seg), horizon), horizon)
             - COST_SECONDARY).dropna()
        if len(a) < config.MIN_N_TRADABLE:
            continue
        mean, disp = a.mean(), a.std()
        rows.append({"segment": seg, "horizon": horizon, "N": len(a),
                     "basket_mean_alpha_%": round(100 * mean, 1),
                     "basket_median_alpha_%": round(100 * a.median(), 1),
                     "cross_name_dispersion_%": round(100 * disp, 1),
                     "mean_per_unit_dispersion": round(mean / disp, 2) if disp else None,
                     "pct_positive_%": round(100 * (a > 0).mean(), 1),
                     "beats_donothing": bool(a.median() > 0)})
    return pd.DataFrame(rows)


def flip_allotment_ev(df, segment):
    """The flip's realistic EV: retail allotment prob ≈ 1/oversubscription, and ADVERSE SELECTION
    (hot IPOs = high subscription = low allotment, so you rarely get the big pops). Compares the
    naive 'got every IPO' gain to the allotment-weighted gain you'd actually capture. Boom-only."""
    sub = spine.segment(df, segment=segment, cohort="boom")        # subscription is boom-only
    sub = sub[sub["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)].copy()
    g = pd.to_numeric(sub["adj_listing_gain_open"], errors="coerce")
    s = pd.to_numeric(sub["sub_total_x"], errors="coerce")
    m = g.notna() & s.notna() & (s > 0)
    g, s = g[m], s[m]
    if len(g) < config.MIN_N_HINT:
        return None
    p_allot = (1.0 / s).clip(upper=1.0)                            # allotment probability
    naive = 100 * g.mean()
    realized = 100 * (g * p_allot).sum() / p_allot.sum()          # weighted by what you actually get
    return {"segment": segment, "N": int(len(g)), "naive_mean_flip_%": round(naive, 1),
            "allotment_weighted_flip_%": round(realized, 1),
            "adverse_selection_cost_pp": round(naive - realized, 1),
            "median_allotment_prob": round(float(p_allot.median()), 3)}
