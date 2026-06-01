"""Layer-3 METHOD SPINE — the shared, non-negotiable methodology every finding uses.

Encodes docs/strategies.md §0 + the methodology review must-fixes:
  - hard SME/MB split + cohort slicing (never pool)
  - maturity-gating (a horizon stat uses only IPOs old enough to have it)
  - distributions over means (P10/median/P90 + N) and proportions with Wilson CIs
  - competing-risks terminal state as a BAND (wipeout lower/upper) — reasons are sparse
  - alpha access with benchmark policy (Nifty-50 default; Smallcap-250 for small/micro 2017+)
  - listing-pop uses RAW return_from_listing (NOT alpha — alpha is issue-anchored)
  - min-N guards that callers + the report enforce
Read-only on the substrate.
"""
import math
import pandas as pd
from layer3 import config

# ---------------------------------------------------------------- load + slice
def load_substrate(path=None, equity_only=True, exclude_low_quality=False):
    """Load the Layer-3 substrate. equity_only drops fpo/reit/invit (core IPO analysis).
    Honest curation: any ISIN listed in data/master/exclusions.csv (isin,reason) is dropped — for
    GENUINELY-BAD rows only (data errors), logged with a reason; never for cherry-picking outcomes."""
    df = pd.read_csv(path or config.SUBSTRATE, low_memory=False)
    exc_path = config.ROOT / "data/master/exclusions.csv"
    if exc_path.exists():
        try:
            exc = set(pd.read_csv(exc_path)["isin"].dropna().astype(str))
            if exc:
                df = df[~df["isin"].astype(str).isin(exc)]
        except (KeyError, ValueError, pd.errors.EmptyDataError):
            pass
    if equity_only:
        df = df[df["instrument_type"] == config.CORE_INSTRUMENT].copy()
    if exclude_low_quality:
        df = df[df["data_quality_tier"] != "low"].copy()
    return df.reset_index(drop=True)


def segment(df, segment=None, cohort=None, mcap=None, sector=None):
    """Hard MB/SME split (`type`) + optional cohort/mcap/sector slice."""
    out = df
    if segment is not None:
        out = out[out["type"] == segment]
    if cohort is not None:
        out = out[out["cohort"] == cohort]
    if mcap is not None:
        out = out[out["market_cap_class"] == mcap]
    if sector is not None:
        out = out[out["broad_sector"] == sector]
    return out.copy()


def investable(df):
    """Liquidity filter (§5): keep only liquidity_flag == 'ok'."""
    return df[df["liquidity_flag"] == "ok"].copy()


# ---------------------------------------------------------------- maturity + alpha
def maturity_gated(df, horizon):
    """§1: only IPOs old enough to HAVE this horizon's alpha (non-null)."""
    col = f"alpha_{horizon}"
    return df[df[col].notna()].copy()


def alpha_series(df, horizon, benchmark="nifty"):
    """Alpha at a horizon. benchmark='nifty' -> alpha_<h> (vs Nifty50, full history);
    'smallcap' -> alpha_sc_<h> (vs Nifty Smallcap 250, 2017+ only)."""
    col = f"alpha_sc_{horizon}" if benchmark == "smallcap" else f"alpha_{horizon}"
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def listing_return(df, horizon):
    """RAW return-from-listing at a horizon (the secondary buyer's gross return).
    NOTE: this is NOT alpha. Used by T3 pop-fade — bucketing by listing-pop and then
    measuring issue-anchored alpha would double-count the pop (methodology fix #1)."""
    col = f"return_from_listing_{horizon}"
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def benchmark_for(mcap_class):
    """Benchmark policy: small/micro -> smallcap (where available), else nifty."""
    return "smallcap" if mcap_class in config.SMALLCAP_MCAP else "nifty"


# ---------------------------------------------------------------- distributions
def distribution(series):
    """§6: distributions over means. Returns N, percentiles, mean, and the min-N tier."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    n = int(len(s))
    q = s.quantile([0.10, 0.25, 0.50, 0.75, 0.90]) if n else {}
    return {
        "n": n,
        "p10": float(q.get(0.10)) if n else None,
        "p25": float(q.get(0.25)) if n else None,
        "median": float(q.get(0.50)) if n else None,
        "p75": float(q.get(0.75)) if n else None,
        "p90": float(q.get(0.90)) if n else None,
        "mean": float(s.mean()) if n else None,
        "tier": config.n_tier(n),
    }


def wilson_ci(k, n, z=1.96):
    """Wilson score interval for a proportion k/n (robust at small n + extreme p)."""
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_median_ci(series, n_boot=1000, ci=0.90, seed=0):
    """Percentile-bootstrap CI for the MEDIAN + sign-stability (fraction of resamples with median>0).
    Headline numbers are median alphas/lifts — Wilson only covers proportions, so this fills the gap.
    Seeded for reproducibility."""
    import numpy as np
    s = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    n = len(s)
    if n < config.MIN_N_HINT:
        return {"median": None, "lo": None, "hi": None, "p_positive": None, "n": n}
    rng = np.random.default_rng(seed)
    meds = np.array([np.median(rng.choice(s, size=n, replace=True)) for _ in range(n_boot)])
    a = (1 - ci) / 2
    return {"median": float(np.median(s)), "lo": float(np.quantile(meds, a)),
            "hi": float(np.quantile(meds, 1 - a)), "p_positive": float((meds > 0).mean()), "n": n}


def proportion(mask):
    """Base rate for a boolean mask (over its non-null rows): rate, k, n, Wilson CI, tier."""
    m = pd.Series(mask).dropna().astype(bool)
    n = int(len(m)); k = int(m.sum())
    lo, hi = wilson_ci(k, n)
    return {"k": k, "n": n, "rate": (k / n if n else None),
            "ci_lo": lo, "ci_hi": hi, "tier": config.n_tier(n)}


# ---------------------------------------------------------------- competing risks
WIPEOUT_REASONS = {"Compulsory Delisting", "Delisting - Liquidation"}

def terminal_state(df):
    """§2 competing-risks: alive | wipeout (~-100%) | payout (winner leaving) |
    alive_delisted_unknown. Never drops delisted rows."""
    delisted = df["delisted"].fillna(False).astype(bool)
    reason = df["delist_reason"]
    oclass = df["outcome_class"]
    state = pd.Series("alive", index=df.index)
    state[delisted] = "alive_delisted_unknown"
    state[delisted & (reason == "Voluntary Delisting")] = "payout"
    state[delisted & reason.isin(WIPEOUT_REASONS)] = "wipeout"
    state[oclass == "wipeout"] = "wipeout"   # outcome_class wipeout is authoritative for ~-100%
    return state


def wipeout_band(df):
    """Because delist_reason covers only a fraction of delistings, report wipeout as a
    BAND: lower = confirmed wipeout-class; upper = lower + delisted-with-unknown-reason."""
    t = terminal_state(df)
    n = int(len(df))
    lower = int((t == "wipeout").sum())
    upper = lower + int((t == "alive_delisted_unknown").sum())
    return {"n": n,
            "wipeout_lower": lower, "wipeout_lower_rate": (lower / n if n else None),
            "wipeout_upper": upper, "wipeout_upper_rate": (upper / n if n else None)}


# ---------------------------------------------------------------- guards
def outcome_profile(g, horizon="3y"):
    """The FULL outcome picture for a set of IPOs (not just the endpoint): the horizon alpha PLUS
    the journey — highest point reached, deepest fall, multibagger odds, % below issue, wipeout.
    All from-issue figures use issue_price_adj (split-adjusted)."""
    gm = maturity_gated(g, horizon)
    a = alpha_series(gm, horizon)
    mg = pd.to_numeric(g.get("max_gain_pct"), errors="coerce")          # best ever, from issue
    dd = pd.to_numeric(g.get("max_drawdown_pct"), errors="coerce")      # worst peak→trough fall
    atl = pd.to_numeric(g.get("all_time_low"), errors="coerce")
    iss = pd.to_numeric(g.get("issue_price_adj"), errors="coerce")
    trough = (atl / iss - 1).replace([float("inf"), float("-inf")], pd.NA)   # lowest point, from issue
    rfi = pd.to_numeric(gm.get(f"return_from_issue_{horizon}"), errors="coerce").dropna()
    wb = wipeout_band(g)

    def pc(x):
        return None if (x is None or (isinstance(x, float) and pd.isna(x))) else round(100 * x, 1)
    return {
        "n": len(g), "n_matured_%s" % horizon: len(gm),
        "median_alpha_%s_%%" % horizon: pc(distribution(a)["median"]),
        "median_peak_gain_%": pc(mg.median()),
        "pct_ever_2x": pc(proportion(mg >= 1.0)["rate"]),
        "pct_ever_5x": pc(proportion(mg >= 4.0)["rate"]),
        "median_trough_from_issue_%": pc(trough.median()),
        "median_max_drawdown_%": pc(dd.median()),
        "pct_below_issue_%s_%%" % horizon: pc(proportion(rfi < 0)["rate"]),
        "wipeout_lower_%": pc(wb["wipeout_lower_rate"]),
        "wipeout_upper_%": pc(wb["wipeout_upper_rate"]),
    }


# 5% steps through the decision range (per user), then wider tail markers for the multibagger reach.
REACH_UP = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00,
            1.50, 2.00, 3.00, 5.00)
REACH_DOWN = (-0.05, -0.10, -0.15, -0.20, -0.25, -0.30, -0.40, -0.50, -0.70, -0.90)
EXIT_LEVELS = (0.0, 0.10, 0.20, 0.30, 0.50, 1.00)


def _entry_cols(entry, horizon):
    """Column names for the chosen ENTRY point: 'issue' (allottee) or 'listing' (secondary buyer)."""
    if entry == "listing":
        return "mfe_lst_%s" % horizon, "mae_lst_%s" % horizon, "return_from_listing_%s" % horizon
    return "mfe_%s" % horizon, "mae_%s" % horizon, "return_from_issue_%s" % horizon


def reach_curve(g, horizon="1y", entry="issue", ups=REACH_UP, downs=REACH_DOWN):
    """The 'how likely to get there' ladder: P(the stock REACHED +X% at some point within the
    horizon) and P(it FELL to −X%), using within-horizon peak/trough (MFE/MAE) from the chosen
    ENTRY (issue=allottee / listing=secondary buyer). Paired with the buy-and-hold ENDPOINT so you
    see the gap between 'the move was available' and 'you'd have to time the exit'."""
    mfe_c, mae_c, end_c = _entry_cols(entry, horizon)
    mfe = pd.to_numeric(g.get(mfe_c), errors="coerce")
    mae = pd.to_numeric(g.get(mae_c), errors="coerce")
    v = mfe.notna()
    n = int(v.sum())
    rfi = pd.to_numeric(g.get(end_c), errors="coerce").dropna()
    up = [{"move": "+%d%%" % round(x * 100), "pct_reached": (round(100 * (mfe[v] >= x).mean(), 1) if n else None)}
          for x in ups]
    down = [{"move": "%d%%" % round(x * 100), "pct_fell_to": (round(100 * (mae[v] <= x).mean(), 1) if n else None)}
            for x in downs]
    return {"n": n, "horizon": horizon, "entry": entry, "reach_up": up, "reach_down": down,
            "median_peak_pct": round(100 * mfe[v].median(), 1) if n else None,
            "median_trough_pct": round(100 * mae[v].median(), 1) if n else None,
            "median_endpoint_pct": round(100 * rfi.median(), 1) if len(rfi) else None,
            "pct_ended_positive": round(100 * (rfi > 0).mean(), 1) if len(rfi) else None}


def exit_strategy(g, entry="issue", horizon="1y", levels=EXIT_LEVELS):
    """Take-profit / break-even EXIT discipline. For each target T: if the price reached T at any
    point within the horizon you exit at T (capture +T); otherwise you hold to the endpoint. Shows
    the trade-off — tight exits hit more often but cap the upside. entry='issue' (allottee) or
    'listing' (secondary buyer). Also reports whether the stock EVER gave an exit ≥ break-even."""
    import numpy as np
    mfe_c, _, end_c = _entry_cols(entry, horizon)
    mfe = pd.to_numeric(g.get(mfe_c), errors="coerce")
    end = pd.to_numeric(g.get(end_c), errors="coerce")
    v = mfe.notna() & end.notna()
    mfe, end = mfe[v], end[v]
    n = int(len(mfe))
    rows = []
    for t in levels:
        reached = (mfe >= t)
        captured = np.where(reached, t, end)            # exit at T if reached, else hold to endpoint
        rows.append({"exit_rule": ("break-even" if t == 0 else "+%d%%" % round(t * 100)),
                     "pct_got_the_exit": round(100 * reached.mean(), 1) if n else None,
                     "median_captured_%": round(100 * float(pd.Series(captured).median()), 1) if n else None,
                     "mean_captured_%": round(100 * float(pd.Series(captured).mean()), 1) if n else None})
    return {"entry": entry, "horizon": horizon, "n": n, "ladder": rows,
            "pct_ever_gave_an_exit": round(100 * (mfe >= 0).mean(), 1) if n else None}


def partial_exit_strategy(g, entry="issue", horizon="1y", levels=EXIT_LEVELS, frac=0.5):
    """Partial exit ('sell a FRACTION at +T, ride the rest'). captured = frac*T + (1-frac)*endpoint
    if the price reached T (mfe>=T) else hold to endpoint. The natural rescue after 'no full exit
    beats hold' — but it trades the MEAN (the right tail) for the MEDIAN (the body). Returns the
    partial ladder plus pure-hold for contrast."""
    import numpy as np
    mfe_c, _, end_c = _entry_cols(entry, horizon)
    mfe = pd.to_numeric(g.get(mfe_c), errors="coerce")
    end = pd.to_numeric(g.get(end_c), errors="coerce")
    v = mfe.notna() & end.notna()
    mfe, end = mfe[v], end[v]
    n = int(len(mfe))
    hold_med = round(100 * float(end.median()), 1) if n else None
    hold_mean = round(100 * float(end.mean()), 1) if n else None
    rows = []
    for t in levels:
        if t == 0:
            continue
        reached = (mfe >= t)
        captured = np.where(reached, frac * t + (1 - frac) * end, end)
        rows.append({"sell_%d%%_at" % round(frac * 100): "+%d%%" % round(t * 100),
                     "pct_reached": round(100 * reached.mean(), 1) if n else None,
                     "median_captured_%": round(100 * float(pd.Series(captured).median()), 1) if n else None,
                     "mean_captured_%": round(100 * float(pd.Series(captured).mean()), 1) if n else None})
    return {"entry": entry, "horizon": horizon, "n": n, "frac": frac,
            "hold_median_%": hold_med, "hold_mean_%": hold_mean, "ladder": rows}


def basket_dispersion(g, horizon="1y", entry="listing", top_frac=0.05):
    """The 'buy every IPO' basket as a barbell: mean vs median, % positive, and how much of the mean
    is just the top few %. Strip the top_frac and watch the mean collapse — the average is a mirage
    the typical (median) name never sees."""
    _, _, end_c = _entry_cols(entry, horizon)
    s = pd.to_numeric(g.get(end_c), errors="coerce").dropna()
    n = int(len(s))
    if n < MIN_N_TRADABLE_GUARD():
        return {"n": n, "entry": entry, "horizon": horizon, "insufficient": True}
    pos = proportion(s > 0)
    k = max(1, int(round(top_frac * n)))
    top = s.nlargest(k)
    ex_top = s.drop(top.index)
    return {"n": n, "entry": entry, "horizon": horizon,
            "mean_%": round(100 * float(s.mean()), 1), "median_%": round(100 * float(s.median()), 1),
            "pct_positive": pos["rate"], "pct_positive_ci": (pos["ci_lo"], pos["ci_hi"]),
            "p90_%": round(100 * float(s.quantile(0.90)), 1),
            "top_%d%%_mean_%%" % round(top_frac * 100): round(100 * float(top.mean()), 1),
            "mean_ex_top_%": round(100 * float(ex_top.mean()), 1) if len(ex_top) else None}


def MIN_N_TRADABLE_GUARD():
    return config.MIN_N_TRADABLE


SUB_BUCKETS = [("1-5x", 1, 5), ("5-15x", 5, 15), ("15-50x", 15, 50), (">50x", 50, 1e9)]


def allotment_capture(g):
    """The flip trap: the pop and the retail ALLOTMENT odds are mechanically inverse (allotment ≈
    1/oversubscription), so what a flipper captures PER APPLICATION is flat-to-declining across
    subscription buckets — the visible pop is a selection illusion you can't size into. Boom-only
    (subscription is single-regime). Excludes unreliable_coverage listing rows."""
    g = g[g.get("listing_metrics_status") != "unreliable_coverage"] if "listing_metrics_status" in g.columns else g
    sub = pd.to_numeric(g.get("sub_total_x"), errors="coerce")
    pop = pd.to_numeric(g.get("adj_listing_gain_open"), errors="coerce")
    v = sub.notna() & pop.notna() & (sub > 0)
    sub, pop = sub[v], pop[v]
    rows = []
    for lab, lo, hi in SUB_BUCKETS:
        m = (sub >= lo) & (sub < hi)
        n = int(m.sum())
        if n < config.MIN_N_HINT:
            rows.append({"sub_bucket": lab, "n": n, "insufficient": True})
            continue
        p = pop[m]
        allot = (1.0 / sub[m]).clip(upper=1.0)               # retail allotment prob ≈ 1/oversubscription
        cap = (allot * p)                                    # capture per rupee applied = allot × pop
        rows.append({"sub_bucket": lab, "n": n,
                     "median_pop_%": round(100 * float(p.median()), 1),
                     "median_allot_odds_%": round(100 * float(allot.median()), 1),
                     "E_capture_per_application_%": round(100 * float(cap.mean()), 2),
                     "pct_pop_positive": round(100 * float((p > 0).mean()), 1)})
    return {"n": int(len(sub)), "buckets": rows}


def average_down(g, entry="listing", horizon="1y", dips=(0.30, 0.50)):
    """Does averaging down on a fallen IPO help? Among names that hit −D within the horizon: HOLD vs
    a second equal tranche bought at −D (blended cost). The 'improvement' is arithmetic dilution, not
    recovery — the decision-relevant number is pct_recovered_above_entry + the tranche-2 standalone
    outcome (is buying MORE at −D a winner?)."""
    mfe_c, mae_c, end_c = _entry_cols(entry, horizon)
    mae = pd.to_numeric(g.get(mae_c), errors="coerce")
    end = pd.to_numeric(g.get(end_c), errors="coerce")
    rows = []
    for d in dips:
        dip = (mae <= -d) & end.notna()
        e = end[dip]
        n = int(len(e))
        if n < config.MIN_N_HINT:
            rows.append({"dip": "-%d%%" % round(d * 100), "dipper_n": n, "insufficient": True})
            continue
        # blended (½ at entry, ½ at −D): cost = entry*(1−D/2); end value relative to entry = 1+end
        blended = (1 + e) / (1 - d / 2) - 1
        tranche2 = (1 + e) / (1 - d) - 1                       # the second tranche bought at −D, standalone
        rows.append({"dip": "-%d%%" % round(d * 100), "dipper_n": n,
                     "hold_median_%": round(100 * float(e.median()), 1),
                     "blended_median_%": round(100 * float(blended.median()), 1),
                     "pct_recovered_above_entry": round(100 * float((e > 0).mean()), 1),
                     "tranche2_median_%": round(100 * float(tranche2.median()), 1),
                     "tranche2_pct_positive": round(100 * float((tranche2 > 0).mean()), 1)})
    return {"entry": entry, "horizon": horizon, "ladder": rows}


def lifecycle(g, horizon="1y"):
    """WHEN does the move happen — the timing of the peak/trough (entry-independent) and how long the
    allottee spends underwater. Answers 'when does the average IPO peak / bottom / get back to issue?'"""
    pk = pd.to_numeric(g.get("days_to_mfe_%s" % horizon), errors="coerce").dropna()
    tr = pd.to_numeric(g.get("days_to_mae_%s" % horizon), errors="coerce").dropna()
    be = pd.to_numeric(g.get("days_to_breakeven_%s" % horizon), errors="coerce").dropna()
    q = lambda s, p: int(s.quantile(p)) if len(s) else None
    return {"horizon": horizon, "n_peak": int(len(pk)),
            "median_days_to_peak": q(pk, 0.5), "p25_days_to_peak": q(pk, 0.25), "p75_days_to_peak": q(pk, 0.75),
            "median_days_to_trough": q(tr, 0.5),
            "median_days_to_breakeven": q(be, 0.5), "p75_days_to_breakeven": q(be, 0.75),
            "pct_peak_in_first_quarter": round(100 * float((pk <= 90).mean()), 1) if len(pk) else None}


def combined_exit_strategy(g, entry="issue", horizon="1y", tp=0.50, sl=0.30):
    """Combined 'take-profit at +tp OR stop-loss at −sl, whichever comes first' — now possible because
    the timing columns (days_to_mfe/mae) let us APPROXIMATE which level was hit first. Per name:
      reached_tp = mfe>=tp; reached_sl = mae<=−sl.
      both reached → use timing: peak-day <= trough-day ⇒ TP fired first (capture +tp), else SL (−sl).
      only one → that one. neither → hold to endpoint.
    APPROXIMATION CAVEAT: days_to_mfe/mae are the days of the MAX/MIN, not the first crossing of tp/sl,
    so the order is approximate (it's the best the daily-summary data allows; for screener-weekly /
    clamped rows it's coarser). Compared to plain buy-and-hold."""
    import numpy as np
    mfe_c, mae_c, end_c = _entry_cols(entry, horizon)
    mfe = pd.to_numeric(g.get(mfe_c), errors="coerce")
    mae = pd.to_numeric(g.get(mae_c), errors="coerce")
    end = pd.to_numeric(g.get(end_c), errors="coerce")
    dpk = pd.to_numeric(g.get("days_to_mfe_%s" % horizon), errors="coerce")
    dtr = pd.to_numeric(g.get("days_to_mae_%s" % horizon), errors="coerce")
    v = mfe.notna() & mae.notna() & end.notna()
    mfe, mae, end, dpk, dtr = mfe[v], mae[v], end[v], dpk[v], dtr[v]
    n = int(len(end))
    if n < MIN_N_TRADABLE_GUARD():
        return {"entry": entry, "horizon": horizon, "tp": tp, "sl": sl, "n": n, "insufficient": True}
    rt, rs = mfe >= tp, mae <= -sl
    peak_first = dpk <= dtr                        # approximate ordering
    cap = end.copy().astype(float)
    cap[rt & ~rs] = tp                             # only TP
    cap[rs & ~rt] = -sl                            # only SL
    cap[rt & rs & peak_first] = tp                 # both, peak first → TP
    cap[rt & rs & ~peak_first] = -sl               # both, trough first → SL
    ambiguous = int((rt & rs & (dpk.isna() | dtr.isna())).sum())   # both reached, timing unknown
    hold = end
    return {"entry": entry, "horizon": horizon, "tp": tp, "sl": sl, "n": n,
            "pct_took_profit": round(100 * float((rt & (~rs | peak_first)).mean()), 1),
            "pct_stopped_out": round(100 * float((rs & (~rt | ~peak_first)).mean()), 1),
            "pct_held_to_end": round(100 * float((~rt & ~rs).mean()), 1),
            "rule_mean_%": round(100 * float(cap.mean()), 1),
            "rule_median_%": round(100 * float(cap.median()), 1),
            "buy_hold_mean_%": round(100 * float(hold.mean()), 1),
            "buy_hold_median_%": round(100 * float(hold.median()), 1),
            "beats_hold_mean": bool(cap.mean() > hold.mean()),
            "n_ambiguous_order": ambiguous}


STOP_LEVELS = (0.10, 0.20, 0.30, 0.50)


def stop_loss_strategy(g, entry="issue", horizon="1y", stops=STOP_LEVELS):
    """Stop-loss discipline (the mirror of exit_strategy). For each stop S: if the stock fell to −S
    at any point within the horizon you're stopped out at −S; otherwise you hold to the endpoint.
    This is an SL-ONLY model (no take-profit interaction) so it is unambiguous from MAE alone —
    UNLIKE a combined TP+SL, where MFE/MAE can't tell us which was touched first.

    The decision the user asked for — does cutting losses protect you, given most IPOs eventually
    trade back up? — is captured by two diagnostics among the names that got stopped:
      • stopped_but_recovered_% : of names that touched −S, the share that ENDED above the buyer's
        entry anyway → the stop booked a loss on a name that came back (the cost of the stop).
      • stop_saved_% : of names that touched −S, the share whose ENDPOINT was below −S → the stop
        cut a loss that would otherwise have been worse (the benefit of the stop).
    entry='issue' (allottee) or 'listing' (secondary buyer)."""
    import numpy as np
    mfe_c, mae_c, end_c = _entry_cols(entry, horizon)
    mae = pd.to_numeric(g.get(mae_c), errors="coerce")
    end = pd.to_numeric(g.get(end_c), errors="coerce")
    v = mae.notna() & end.notna()
    mae, end = mae[v], end[v]
    n = int(len(mae))
    base_mean = round(100 * float(end.mean()), 1) if n else None       # buy-and-hold baseline
    rows = []
    for s in stops:
        stopped = (mae <= -s)
        captured = np.where(stopped, -s, end)               # stopped at −S, else hold to endpoint
        nst = int(stopped.sum())
        recov = float((end[stopped] > 0).mean()) if nst else None       # stopped yet ended up
        saved = float((end[stopped] < -s).mean()) if nst else None      # stopped, endpoint worse than −S
        rows.append({"stop_rule": "−%d%%" % round(s * 100),
                     "pct_stopped_out": round(100 * stopped.mean(), 1) if n else None,
                     "stopped_but_recovered_%": round(100 * recov, 1) if recov is not None else None,
                     "stop_saved_%": round(100 * saved, 1) if saved is not None else None,
                     "mean_with_stop_%": round(100 * float(pd.Series(captured).mean()), 1) if n else None,
                     "median_with_stop_%": round(100 * float(pd.Series(captured).median()), 1) if n else None})
    return {"entry": entry, "horizon": horizon, "n": n, "buy_hold_mean_%": base_mean, "ladder": rows}


def outcome_breakdown(cohort, horizon="3y"):
    """The honest 'what happened to IPOs like this' breakdown for a decision: of N similar past IPOs,
    the share that became each fate (multibagger / winner / flat / loser / dead-money / wipeout) PLUS
    the best (P90) / base-rate (median) / worst (P10) realized return-from-issue and the wipeout band.
    Shows ALL outcomes incl. failures — the opposite of survivorship bias. Maturity-gated."""
    g = maturity_gated(cohort, horizon)
    rfi_all = pd.to_numeric(g.get(f"return_from_issue_{horizon}"), errors="coerce")
    rfi = rfi_all.dropna()
    n = int(len(rfi))
    wb = wipeout_band(g)        # on the SAME maturity-gated base as the buckets + dead-money (not full cohort)
    # HORIZON outcome buckets (from the issue-anchored return AT the horizon — sum to 100%, so they
    # pair coherently with best/median/worst below). Distinct from the lifetime outcome_class label.
    def share(mask):
        return round(100 * float(mask.mean()), 1) if n else None
    buckets = {
        "doubled+ (≥2x)_%": share(rfi >= 1.0),
        "up (20–100%)_%": share((rfi >= 0.20) & (rfi < 1.0)),
        "≈flat (±20%)_%": share((rfi > -0.20) & (rfi < 0.20)),
        "down (<−20%)_%": share(rfi <= -0.20),
    }
    # TERMINAL risk overlay (lifetime — 'did it die?'): the dead-money zombie + the confirmed-wipeout band.
    gc = maturity_gated(cohort, horizon)
    alive = gc["delisted"].fillna(False) == False
    cr = pd.to_numeric(gc.get("current_return_from_issue"), errors="coerce")
    dead_rate = round(100 * float((alive & (cr < -0.50) & (gc.get("liquidity_flag") == "low")).mean()), 1) if len(gc) else None
    return {
        "n": n, "horizon": horizon, "horizon_buckets": buckets,
        "best_case_p90_%": round(100 * float(rfi.quantile(0.90)), 1) if n else None,
        "base_rate_median_%": round(100 * float(rfi.median()), 1) if n else None,
        "worst_case_p10_%": round(100 * float(rfi.quantile(0.10)), 1) if n else None,
        "terminal_dead_money_%": dead_rate,
        "terminal_wipeout_band_%": (round(100 * (wb["wipeout_lower_rate"] or 0), 1),
                                    round(100 * (wb["wipeout_upper_rate"] or 0), 1)),
    }


def guarded(value, n, fmt="{:.2f}"):
    """Return a formatted value only if n >= hint floor; else an explicit insufficient tag.
    Findings use this so a sub-floor cell can never be mistaken for a real number."""
    if n is None or n < config.MIN_N_HINT:
        return f"insufficient (N={n or 0})"
    return fmt.format(value) if value is not None else "—"


def pct(x, digits=1):
    return "—" if x is None else f"{100*x:.{digits}f}%"
