"""Scorecard — 5 transparent component scores (0–100) from the analog cohort's REALIZED
outcomes (+ the query's own quality), blended into one IPO score with preset OR data-informed
weights. Every component shows its underlying numbers and N; sub-floor components return None
('insufficient analogs') rather than a fake score. No ML.
"""
import math
import numpy as np
import pandas as pd
from layer3 import spine, config

# weight presets (data-informed weights from Part C backtest can replace these later).
# tradeable_upside is weight 0 EVERYWHERE = shown for context, NOT in the combined score. It's a
# movement-lens display (P(cohort reached +X%)); weighting it in would need a weights re-fit + OOS
# re-validation — deferred (see NEEDS_YOUR_INPUT.md).
PRESETS = {
    "balanced":     dict(return_potential=1.0, multibagger_odds=1.0, downside_safety=1.0, liquidity=0.7, quality=0.8, tradeable_upside=0.0, wipeout_safety=0.0, crowded_window=0.0),
    "conservative": dict(return_potential=0.5, multibagger_odds=0.4, downside_safety=1.5, liquidity=1.2, quality=1.2, tradeable_upside=0.0, wipeout_safety=0.0, crowded_window=0.0),
    "aggressive":   dict(return_potential=1.4, multibagger_odds=1.4, downside_safety=0.6, liquidity=0.5, quality=0.6, tradeable_upside=0.0, wipeout_safety=0.0, crowded_window=0.0),
}


def _squash(x, scale):
    """Monotonic map of a signed quantity to 0..100 (50 = neutral)."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return float(np.clip(50 + 50 * math.tanh(x / scale), 0, 100))


def _comp(score, **detail):
    detail["score"] = score
    return detail


def _drop_unreliable_listing(g):
    """Listing-anchored cuts must exclude `unreliable_coverage` listing rows (bad listing-day prices),
    matching the findings/backtest policy (CLAUDE.md)."""
    if "listing_metrics_status" in g.columns:
        return g[g["listing_metrics_status"] != "unreliable_coverage"]
    return g


def pick_horizon(cohort):
    """One horizon for the WHOLE scorecard (avoids a combined score that mixes 1y + 3y parts)."""
    return "3y" if len(spine.maturity_gated(cohort, "3y")) >= config.MIN_N_HINT else "1y"


def return_potential(cohort, h):
    g = spine.maturity_gated(cohort, h)
    d = spine.distribution(spine.alpha_series(g, h))
    return _comp(_squash(d["median"], 0.5) if d["n"] >= config.MIN_N_HINT else None,
                 horizon=h, n=d["n"], median_alpha=d["median"], p10=d["p10"], p90=d["p90"])


def multibagger_odds(cohort, h):
    # consistent with the from-LISTING framing: 2x/5x from the listing price (secondary buyer)
    g = spine.maturity_gated(cohort, h)
    g = _drop_unreliable_listing(g)
    # SCORE stays anchored to the ENDPOINT 2x rate (what buy-and-hold actually keeps) so the
    # cross-regime / OOS-validated weights remain valid. But we ALSO report the truer "the upside
    # was on the table" number: P(price EVER touched 2x/5x within the horizon) via MFE — the gap
    # between the two is the timing/capture tax. (mv-multibagger-ever)
    # Both proportions share ONE denominator (rows with endpoint AND mfe present) so the invariant
    # "touched ≥ ended" is guaranteed and the two numbers are directly comparable.
    rfl = pd.to_numeric(g.get(f"return_from_listing_{h}"), errors="coerce")
    mfe = pd.to_numeric(g.get(f"mfe_lst_{h}"), errors="coerce")
    both = rfl.notna() & mfe.notna()
    rfl_c, mfe_c = rfl[both], mfe[both]
    p2 = spine.proportion(rfl_c >= 1.0); p5 = spine.proportion(rfl_c >= 4.0)
    ever2 = spine.proportion(mfe_c >= 1.0) if len(mfe_c) else {"rate": None}
    ever5 = spine.proportion(mfe_c >= 4.0) if len(mfe_c) else {"rate": None}
    score = None if p2["n"] < config.MIN_N_HINT else float(np.clip(p2["rate"] / 0.40 * 100, 0, 100))
    return _comp(score, horizon=h, n=p2["n"], pct_2x_from_listing=p2["rate"],
                 pct_5x_from_listing=p5["rate"], pct_ever_2x=ever2["rate"], pct_ever_5x=ever5["rate"],
                 ci_lo=p2["ci_lo"], ci_hi=p2["ci_hi"])


def tradeable_upside(cohort, h, entry="listing", level=0.30):
    """Movement-lens component: P(the analog cohort EVER touched +level within the horizon) via MFE,
    from the secondary buyer's entry by default. Scaled 0–100 (so 60% reach → 60). Shown WITH the
    capture gap (median endpoint) so it's never read as guaranteed — reaching ≠ booking."""
    g = spine.maturity_gated(cohort, h)
    if entry == "listing":
        g = _drop_unreliable_listing(g)
    mfe_c, _, end_c = spine._entry_cols(entry, h)
    mfe = pd.to_numeric(g.get(mfe_c), errors="coerce").dropna()
    end = pd.to_numeric(g.get(end_c), errors="coerce").dropna()
    if len(mfe) < config.MIN_N_HINT:
        return _comp(None, n=len(mfe))
    reach = float((mfe >= level).mean())
    return _comp(round(100 * reach, 1), horizon=h, n=int(len(mfe)), entry=entry,
                 reach_level="+%d%%" % round(level * 100), pct_reached=reach,
                 median_endpoint=float(end.median()) if len(end) else None)


def downside_safety(cohort):
    wb = spine.wipeout_band(cohort)
    g3 = spine.maturity_gated(cohort, "3y")
    rfi = pd.to_numeric(g3.get("return_from_issue_3y"), errors="coerce")
    below = spine.proportion(rfi < 0)
    dd = pd.to_numeric(cohort.get("max_drawdown_pct"), errors="coerce")
    deep = spine.proportion(dd <= -0.50)
    n = len(cohort)
    if n < config.MIN_N_HINT:
        return _comp(None, n=n)
    # risk in 0..1: wipeout (upper, worst-case) + below-issue + deep-drawdown, weighted
    risk = (0.5 * (wb["wipeout_upper_rate"] or 0)
            + 0.3 * (below["rate"] or 0)
            + 0.2 * (deep["rate"] or 0))
    base = float(np.clip(100 * (1 - risk / 0.6), 0, 100))
    # LIQUIDITY-REALIZABILITY HAIRCUT: a −60% you can't exit is worse than a liquid one.
    illiq = float((cohort["liquidity_flag"] != "ok").mean())
    haircut = 1 - 0.4 * illiq            # up to −40% if the analog cohort is entirely illiquid
    return _comp(round(base * haircut, 1),
                 n=n, wipeout_upper=wb["wipeout_upper_rate"], pct_below_issue=below["rate"],
                 pct_deep_drawdown=deep["rate"], illiquid_frac=round(illiq, 2),
                 liquidity_haircut=round(haircut, 2))


def liquidity(cohort):
    n = len(cohort)
    if n < config.MIN_N_HINT:
        return _comp(None, n=n)
    ok = spine.proportion(cohort["liquidity_flag"] == "ok")
    medturn = pd.to_numeric(cohort.get("median_daily_turnover_inr"), errors="coerce").median()
    return _comp(float(np.clip(ok["rate"] * 100, 0, 100)),
                 n=n, pct_investable=ok["rate"], median_turnover_inr=float(medturn) if pd.notna(medturn) else None)


def wipeout_flags(query, df=None):
    """Check a NEW IPO against the VALIDATED, prospectus-readable wipeout red flags (N14, cross-regime):
    tiny pre-IPO sales (<25cr), loss-making at IPO (PAT<=0), obscure lead manager (infrequent banker).
    Only flags fields the query actually provides (unknown ≠ safe — reported as 'unknown'). Returns the
    tripped flags + how many of the checkable ones fired — the input to the prominent red-flag badge.
    NOTE: micro-cap / low-promoter-holding / GMP are deliberately NOT here (reverse-causation / wrong
    sign — see rules/index.md tested-signal registry)."""
    flags, checked = [], 0
    sales = query.get("pre_ipo_net_sales")
    if sales is not None:
        checked += 1
        if float(sales) < 25:
            flags.append(("tiny pre-IPO sales", f"₹{float(sales):.0f}cr < 25cr"))
    pat = query.get("pre_ipo_pat")
    if pat is not None:
        checked += 1
        if float(pat) <= 0:
            flags.append(("loss-making at IPO", "latest-year PAT ≤ 0"))
    lm = query.get("lead_manager")
    if lm and df is not None and "lead_manager" in df.columns:
        checked += 1
        freq = int((df["lead_manager"].astype(str).str.strip() == str(lm).strip()).sum())
        if freq < 12:
            flags.append(("obscure lead manager", f"only {freq} IPOs by this banker in our data"))
    return {"n_flags": len(flags), "n_checked": checked, "flags": flags,
            "unknown": [k for k, present in
                        [("pre_ipo_net_sales", sales is not None), ("pre_ipo_pat", pat is not None),
                         ("lead_manager", bool(lm))] if not present]}


def _bad_outcome_mask(pool):
    """Lifetime 'did it fail' = confirmed wipeout OR dead-money (alive, <−50%, illiquid)."""
    wipe = pool["outcome_class"].astype(str) == "wipeout"
    alive = pool["delisted"].fillna(False) == False
    cr = pd.to_numeric(pool.get("current_return_from_issue"), errors="coerce")
    dead = alive & (cr < -0.50) & (pool.get("liquidity_flag") == "low")
    return wipe | dead


def _query_flag_series(pool, df):
    """The validated pre-listing wipeout flags evaluated over a pool (same defs as N14)."""
    sales = pd.to_numeric(pool.get("pre_ipo_net_sales"), errors="coerce")
    pat = pd.to_numeric(pool.get("pre_ipo_pat"), errors="coerce")
    lm = pool.get("lead_manager")
    freq = lm.astype(str).str.strip().map(df["lead_manager"].astype(str).str.strip().value_counts()) if lm is not None else None
    return {
        "tiny sales (<25cr)": (sales < 25),
        "loss-making at IPO": (pat <= 0),
        "obscure lead manager": (freq < 12) if freq is not None else None,
    }


def risk_assessment(query, df):
    """Standalone WIPEOUT-RISK gauge (separate from the return score, per the locked policy). Always
    returns a read — even 0 flags is informative. Combines: (a) which validated pre-listing flags THIS
    IPO trips (with the base rate behind each — 'of same-segment IPOs with this flag, X% failed vs Y%
    without'), and (b) an overall risk band from the historical bad-outcome rate at the query's flag
    count, within its own segment. Failure = wipeout OR dead-money (lifetime)."""
    seg = query.get("type")
    pool = df[df["type"] == seg].copy() if seg else df.copy()
    pool = pool[pool.get("listing_metrics_status") != "unreliable_coverage"] if "listing_metrics_status" in pool.columns else pool
    bad = _bad_outcome_mask(pool)
    pool_flags = _query_flag_series(pool, df)

    wf = wipeout_flags(query, df=df)
    if wf["n_checked"] < 1:
        # nothing to assess — 'unknown ≠ safe'; never emit a LOW/score from zero inputs
        return {"segment": seg, "n_flags": 0, "n_checked": 0, "unknown": wf["unknown"],
                "insufficient_inputs": True, "risk_score_0_100": None, "risk_band": None, "basis": None,
                "fail_rate_at_this_flag_load_%": None, "segment_base_fail_%": round(100 * float(bad.mean()), 1) if len(bad) else None,
                "per_flag": [], "flags": []}
    tripped = {name for name, _ in wf["flags"]}
    # per-flag base rate (with vs without) in the segment — the "richer detail"
    detail = []
    name_map = {"tiny pre-IPO sales": "tiny sales (<25cr)", "loss-making at IPO": "loss-making at IPO",
                "obscure lead manager": "obscure lead manager"}
    for qname, _why in wf["flags"]:
        col = name_map.get(qname)
        s = pool_flags.get(col)
        if s is None:
            continue
        with_m = s.fillna(False) & bad.notna()
        nf = int(s.fillna(False).sum())
        if nf >= config.MIN_N_HINT:
            wr = round(100 * float(bad[s.fillna(False)].mean()), 1)
            wo = round(100 * float(bad[~s.fillna(False) & s.notna()].mean()), 1)
            detail.append({"flag": qname, "failed_with_flag_%": wr, "failed_without_%": wo, "n_with": nf})
    # overall: place the query in its flag-count BAND (0/1/2/3+) and read that band's historical
    # bad-outcome rate, RELATIVE TO the segment's own base (MB and SME have very different base risk).
    cnt = sum(s.fillna(False).astype(int) for s in pool_flags.values() if s is not None)
    qcount = wf["n_flags"]
    seg_base = round(100 * float(bad.mean()), 1) if len(bad) else None
    overall, basis = None, None
    if qcount == 0:                                   # compare a clean IPO to OTHER clean IPOs
        m = cnt == 0
        if int(m.sum()) >= config.MIN_N_HINT:
            overall, basis = round(100 * float(bad[m].mean()), 1), "0 flags"
    else:                                             # descend k = qcount→1, use strongest populated band
        for k in range(qcount, 0, -1):
            m = cnt >= k
            if int(m.sum()) >= config.MIN_N_HINT:
                overall = round(100 * float(bad[m].mean()), 1)
                basis = ("≥%d flags" % k) if k < qcount else ("%d flags" % k)
                break
    band, score = None, None
    if overall is not None and seg_base:
        ratio = overall / seg_base
        band = "HIGH" if ratio >= 1.5 else ("ELEVATED" if ratio >= 1.1 else "LOW")
        score = round(min(100.0, 50.0 * ratio), 0)          # 50 = segment-typical; 100 = ~2x typical risk
    return {"segment": seg, "n_flags": qcount, "n_checked": wf["n_checked"], "unknown": wf["unknown"],
            "risk_score_0_100": score, "risk_band": band, "basis": basis,
            "fail_rate_at_this_flag_load_%": overall, "segment_base_fail_%": seg_base,
            "per_flag": detail, "flags": wf["flags"]}


def wipeout_safety(query, df=None):
    """SCORE component (0–100) = inverse of the validated wipeout-flag load on the query's OWN features:
    100 − 50·n_flags (0 flags→100, 1→50, 2+→0). Folded into the data_informed score (it passed the
    OOS-robust bar: 14/18 cells, strong at 3y). Like `quality`, it's a query-feature signal, so it's
    None when no inputs were given (unknown ≠ safe)."""
    if df is None:
        return _comp(None, n=0)
    wf = wipeout_flags(query, df=df)
    if wf["n_checked"] < 1:
        return _comp(None, n=0, n_flags=0, reason="no risk inputs")
    return _comp(float(max(0.0, 100.0 - 50.0 * wf["n_flags"])), n_flags=wf["n_flags"], n_checked=wf["n_checked"])


def crowded_window(query, df=None):
    """SCORE component (0-100): how CROWDED the IPO window was — inverse percentile of
    ctx_ipo_heat_90d (same-segment listings in the prior 90 days) within the segment.
    Crowded window -> LOW score. FOLDED into data_informed 2026-06-06: negative in all
    4 regime cells AND improved OOS top-quintile lift in 5/5 splits (+10..+56pp) —
    docs/research/context_signals_verdict.md + the heat_fold_test."""
    if df is None:
        return _comp(None, n=0)
    heat = query.get("ctx_ipo_heat_90d")
    seg = query.get("type")
    if heat is None and query.get("listing_date") is None:
        # LIVE query: today's window = listings in the substrate's last 90 days
        from layer3 import config as _cfg
        ld = pd.to_datetime(df.get("listing_date"), errors="coerce")
        asof = pd.Timestamp(_cfg.AS_OF_DATE)
        m = (df.get("type") == seg) & ld.notna() & (ld >= asof - pd.Timedelta(days=90)) & (ld < asof)
        heat = int(m.sum())
    if heat is None or seg not in ("MB", "SME"):
        return _comp(None, n=0)
    ref = _heat_reference(df, seg)
    if ref is None or len(ref) < 30:
        return _comp(None, n=0)
    pct_below = float((ref < float(heat)).mean())
    return _comp(round((1.0 - pct_below) * 100, 1), heat=float(heat), n=int(len(ref)))


_HEAT_REF_CACHE = {}


def _heat_reference(df, seg):
    """Segment heat distribution of the substrate (computed once per frame+segment)."""
    key = (id(df), len(df), seg)
    if key in _HEAT_REF_CACHE:
        return _HEAT_REF_CACHE[key]
    if "ctx_ipo_heat_90d" in df.columns:
        ref = pd.to_numeric(df.loc[df["type"] == seg, "ctx_ipo_heat_90d"], errors="coerce").dropna()
    else:
        from layer3 import context as _ctx
        sub = df[df["type"] == seg]
        ld = pd.to_datetime(sub["listing_date"], errors="coerce").sort_values()
        dl = ld.dropna().tolist()
        import bisect as _b
        ref = pd.Series([_b.bisect_left(dl, t) - _b.bisect_left(dl, t - pd.Timedelta(days=90))
                         for t in dl], dtype=float)
    _HEAT_REF_CACHE[key] = ref
    return ref


def quality(query):
    """From the QUERY's OWN fundamentals (profitable / ROE / margin / debt) + two VALIDATED
    hard-to-fake red flags: the accrual flag (profit but negative operating cash — N8) and the
    extreme-debt cliff (N7). None if no fundamentals given."""
    bits, used = [], []
    pat = query.get("pre_ipo_pat") if query.get("pre_ipo_pat") is not None else query.get("pat_yr3")
    cf = query.get("operating_cf_yr3")
    if pat is not None:
        if pat > 0 and cf is not None and cf <= 0:
            bits.append(15); used.append("⚑ACCRUAL FLAG (profit but negative op-cash — N8)")
        elif pat > 0:
            bits.append(70); used.append("profitable")
        else:
            bits.append(25); used.append("loss-making")
    roe = query.get("pre_ipo_roe_pct")
    if roe is not None:
        bits.append(float(np.clip(50 + (roe - 12) * 2.5, 0, 100))); used.append(f"ROE {roe:.0f}%")
    de = query.get("pre_ipo_debt_equity")
    if de is not None:
        bits.append(float(np.clip(100 - de * 40, 0, 100)))
        used.append(f"⚑HIGH DEBT D/E {de:.2f} (N7 death signal)" if de > 1.5 else f"D/E {de:.2f}")
    mar = query.get("pre_ipo_pat_margin_pct")
    if mar is not None:
        bits.append(float(np.clip(40 + mar * 2, 0, 100))); used.append(f"margin {mar:.0f}%")
    return _comp(float(np.mean(bits)) if bits else None, factors=used, n_factors=len(bits))


def confidence(analog_result, cohort):
    """Honesty checklist -> overall confidence label. Not a single opaque %."""
    n = analog_result["n_cohort"]; rung = analog_result["rung_idx"]
    d3 = spine.distribution(spine.alpha_series(spine.maturity_gated(cohort, "3y"), "3y"))
    dispersion = (d3["p90"] - d3["p10"]) if (d3["p90"] is not None and d3["p10"] is not None) else None
    mat_cov = spine.alpha_series(cohort, "3y").notna().mean()
    dq = cohort["data_quality_tier"].map({"high": 3, "med": 2, "low": 1}).mean()
    if n >= config.MIN_N_TRADABLE and rung <= 1 and (mat_cov or 0) >= 0.4:
        label = "high"
    elif n >= config.MIN_N_HINT and rung <= 2:
        label = "medium"
    else:
        label = "low"
    # cohort recency — DISCLOSE staleness (don't auto-tune): if analogs are mostly old IPOs,
    # the read leans on a different era. We surface it; we do not silently re-weight.
    yrs = pd.to_datetime(cohort["listing_date"], errors="coerce").dt.year
    med_year = int(yrs.median()) if yrs.notna().any() else None
    boom_frac = float((cohort["cohort"] == "boom").mean()) if "cohort" in cohort else None
    return {"label": label, "n_analogs": n, "ladder_rung": analog_result["rung_label"],
            "relaxed": analog_result["relaxed"], "alpha_dispersion_p10_p90": dispersion,
            "maturity_coverage_3y": float(mat_cov) if mat_cov is not None else None,
            "mean_data_quality_1to3": float(dq) if pd.notna(dq) else None,
            "analog_median_listing_year": med_year,
            "analog_boom_frac": round(boom_frac, 2) if boom_frac is not None else None}


def _resolve_weights(profile):
    if profile == "data_informed":
        from layer3.predictor import weights as W   # lazy import (weights imports this module)
        return W.load_weights() or PRESETS["balanced"]
    return PRESETS.get(profile, PRESETS["balanced"])


def scorecard(query, cohort, analog_result, profile="balanced", weights=None, df=None):
    h = pick_horizon(cohort)
    comps = {
        "return_potential": return_potential(cohort, h),
        "multibagger_odds": multibagger_odds(cohort, h),
        "downside_safety": downside_safety(cohort),
        "liquidity": liquidity(cohort),
        "quality": quality(query),
        "tradeable_upside": tradeable_upside(cohort, h),
        "wipeout_safety": wipeout_safety(query, df),
        "crowded_window": crowded_window(query, df),
    }
    w = weights or _resolve_weights(profile)
    num = den = 0.0
    for k, c in comps.items():
        if c.get("score") is not None and w.get(k):
            num += w[k] * c["score"]; den += w[k]
    combined = round(num / den, 1) if den else None
    return {"components": comps, "combined_score": combined, "profile": profile, "horizon": h,
            "weights": w, "confidence": confidence(analog_result, cohort)}
