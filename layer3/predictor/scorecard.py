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


# ── Obscure-lead-manager flag definition (A1, 2026-06-09) ─────────────────────────────────────────
# OLD (frequency-based, quality-blind): fire when the banker has < OBSCURE_FREQ_CUTOFF IPOs in our
# window. B1 (miss_mining_2026-06.md) showed this false-vetoes reputable but UNDER-SAMPLED banks
# (Nuvama, Morgan Stanley, Smart Horizon, Choice, Indorient) — it measured "under-represented in OUR
# window", not "low quality" — and was the SOLE blocker on 34/52 missed winners.
# NEW (quality-aware, point-in-time): fire only when the banker's PRIOR IPOs (>= OBSCURE_MIN_PRIOR,
# listed STRICTLY BEFORE this IPO) FAILED at >= OBSCURE_BAD_RATE (wipeout|dead-money). ABSTAIN (never
# fire) when the banker's prior record is too thin (< OBSCURE_MIN_PRIOR) — we do NOT fall back to
# frequency (that re-introduces the artifact). So the flag now fires only on an EVIDENCED bad track
# record, exonerating the clean reputable banks while still catching genuinely-bad small shops.
# A1 verdict: NEW improves cross-regime bad-outcome discrimination (3/4 panels positive vs the old
# rule's 1/4 meaningful) AND un-vetoes 33/34 B1 missed winners → wired LIVE. See docs/research/
# a1_banker_flag_2026-06.md. Toggle below lets the fold harness A/B the two defs.
OBSCURE_FREQ_CUTOFF = 12      # the OLD rule's banker-IPO-count threshold (kept for A/B + ref)
OBSCURE_MIN_PRIOR = 5         # min PIT prior IPOs by the banker before we trust its track record
OBSCURE_BAD_RATE = 0.40       # PIT prior bad-outcome rate above which the banker is "bad"
# obscure-lead-manager flag definition (A/B-able; the live value is set after the A1b verdict below):
#   "legacy"         — freq<12 over the full window. High recall (25.4%) but a COVERAGE ARTIFACT:
#                      false-vetoes reputable-but-undersampled banks (Nuvama, Morgan Stanley → the Park
#                      Medi miss). This was the live default after A1's NEW def was downgraded.
#   "quality"        — PIT prior bad-rate (fire iff banker's >=MIN_PRIOR prior IPOs failed >=BAD_RATE;
#                      ABSTAIN when thin). Artifact-free, but abstention HALVED recall (->13.2%) → a new
#                      blind spot on real small-shop SME wipeouts. Downgraded to display-only by review.
#   "coverage_guard" — A1b HYBRID: quality def for record-bearing bankers (exonerates reputable, fires on
#                      evidenced-bad) + a freq<12 leg RESTRICTED TO SME for thin-record bankers. The MB/SME
#                      asymmetry recovers small-shop recall (24.6% ≈ legacy) WITHOUT re-vetoing thin MB
#                      banks. Promote to LIVE only if recall does not regress AND OOS fold lift holds.
# LIVE = coverage_guard (A1b, 2026-06-10): independent adversarial review PROMOTED it — recall 24.6% (≈
# legacy 25.4%, the −3 is a quality-improving swap: drops 48 reputable-MB false-vetoes, adds 45 genuine
# small-shop SME catches), false-veto fixed (Nuvama/MorganStanley→0), 1y OOS better-3/worse-0, placebo-clean,
# param-robust. See docs/research/a1b_coverage_guard_2026-06-10.md.
OBSCURE_BANKER_MODE = "coverage_guard"


def _banker_prior_badrate(lm, df, asof=None):
    """Point-in-time (prior_count, prior_bad_rate) for a banker `lm` over `df`: IPOs by the SAME
    banker that listed STRICTLY BEFORE `asof` (NaN asof → use ALL of df, the live-new-IPO case, since
    every substrate IPO is prior to a not-yet-listed query). bad = wipeout OR dead-money (same mask as
    risk_assessment). Returns (n_prior, bad_rate or None)."""
    if df is None or "lead_manager" not in df.columns:
        return 0, None
    same = df["lead_manager"].astype(str).str.strip() == str(lm).strip()
    g = df[same]
    if asof is not None:
        ld = pd.to_datetime(g.get("listing_date"), errors="coerce")
        a = pd.to_datetime(asof, errors="coerce")
        if pd.notna(a):
            g = g[ld < a]
    n = len(g)
    if n == 0:
        return 0, None
    return n, float(_bad_outcome_mask(g).mean())


def _obscure_banker_fires(lm, df, query=None):
    """Decide the obscure-lead-manager flag for ONE query banker. Returns (fires: bool, why: str).
    Definition selected by OBSCURE_BANKER_MODE ('legacy' | 'quality' | 'coverage_guard')."""
    if OBSCURE_BANKER_MODE == "legacy":
        freq = int((df["lead_manager"].astype(str).str.strip() == str(lm).strip()).sum())
        return (freq < OBSCURE_FREQ_CUTOFF), f"only {freq} IPOs by this banker in our data"
    asof = (query or {}).get("listing_date")
    n_prior, bad = _banker_prior_badrate(lm, df, asof=asof)
    if n_prior >= OBSCURE_MIN_PRIOR and bad is not None:  # record-bearing → quality verdict
        fires = bad >= OBSCURE_BAD_RATE
        return fires, f"banker's prior IPOs failed {100*bad:.0f}% of the time (N={n_prior}, ≥{int(100*OBSCURE_BAD_RATE)}% = poor)"
    # thin prior record:
    if OBSCURE_BANKER_MODE == "coverage_guard":
        is_sme = str((query or {}).get("type", "")).strip().upper() == "SME"
        if is_sme:
            freq = int((df["lead_manager"].astype(str).str.strip() == str(lm).strip()).sum())
            if freq < OBSCURE_FREQ_CUTOFF:
                return True, f"thin-record small-shop SME banker (only {freq} IPOs, no proven track record)"
    return False, f"banker track record too thin to judge ({n_prior} prior IPOs)"  # quality: ABSTAIN


def wipeout_flags(query, df=None):
    """Check a NEW IPO against the VALIDATED, prospectus-readable wipeout red flags (N14, cross-regime):
    tiny pre-IPO sales (<25cr), loss-making at IPO (PAT<=0), obscure lead manager (NOW: banker with an
    evidenced poor point-in-time track record — A1). Only flags fields the query actually provides
    (unknown ≠ safe — reported as 'unknown'). Returns the tripped flags + how many of the checkable
    ones fired — the input to the prominent red-flag badge.
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
        fires, why = _obscure_banker_fires(lm, df, query)
        if fires:
            flags.append(("obscure lead manager", why))
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


def _obscure_banker_series(pool, df):
    """Vectorized obscure-lead-manager flag over a pool, using the SAME definition as wipeout_flags so
    risk_assessment base-rates stay consistent with the per-query badge.
    NEW (quality-aware, point-in-time): for each row, fire iff the banker's PRIOR IPOs (>= MIN_PRIOR,
    listed strictly before THIS row's listing_date, within df) failed at >= BAD_RATE. ABSTAIN (NaN)
    when the prior record is thin (< MIN_PRIOR). LEGACY (toggle off): freq<12 over the full window."""
    lm = pool.get("lead_manager")
    if lm is None:
        return None
    if OBSCURE_BANKER_MODE == "legacy":
        freq = lm.astype(str).str.strip().map(df["lead_manager"].astype(str).str.strip().value_counts())
        return (freq < OBSCURE_FREQ_CUTOFF)
    # coverage_guard needs the full-window banker frequency + the row's segment for the thin-record SME leg
    full_freq = df["lead_manager"].astype(str).str.strip().value_counts()
    p_type = pool.get("type")
    d = df.copy()
    d["_lm"] = d["lead_manager"].astype(str).str.strip()
    d["_ld"] = pd.to_datetime(d.get("listing_date"), errors="coerce")
    d["_bad"] = _bad_outcome_mask(d).astype(float)
    # precompute per-banker sorted (date, bad) so each row's PIT prior stats are a slice
    by_banker = {b: (g["_ld"].values, g["_bad"].values)
                 for b, g in d.sort_values("_ld").groupby("_lm")}
    pl = pool["lead_manager"].astype(str).str.strip()
    pld = pd.to_datetime(pool.get("listing_date"), errors="coerce")
    out = pd.Series(np.nan, index=pool.index)
    for idx in pool.index:
        b = pl.loc[idx]
        if b == "" or b == "nan" or b not in by_banker:
            continue
        dates, bads = by_banker[b]
        t = pld.loc[idx] if pld is not None else pd.NaT
        mask = (dates < np.datetime64(t)) if pd.notna(t) else np.ones(len(dates), dtype=bool)
        n_prior = int(mask.sum())
        if n_prior < OBSCURE_MIN_PRIOR:
            # thin prior record. quality → ABSTAIN (NaN). coverage_guard → decisive: fire only on a
            # thin-record SME banker with freq<12 (recall-recovery leg; thin MB names are NOT vetoed).
            if OBSCURE_BANKER_MODE == "coverage_guard":
                is_sme = (str(p_type.loc[idx]).strip().upper() == "SME") if p_type is not None else False
                fires = is_sme and int(full_freq.get(b, 0)) < OBSCURE_FREQ_CUTOFF
                out.loc[idx] = 1.0 if fires else 0.0
            continue
        out.loc[idx] = 1.0 if (np.nanmean(bads[mask]) >= OBSCURE_BAD_RATE) else 0.0
    return out


def _as_bool_flag(s):
    """Coerce a flag series to a clean boolean (NaN/abstain -> False). Flag series may be boolean
    (legacy freq rule) OR float 0.0/1.0/NaN (quality / coverage_guard), so consumers that AND them
    together must normalize first — a raw float `& bool` raises in pandas."""
    return pd.to_numeric(s, errors="coerce").fillna(0) > 0


def _query_flag_series(pool, df):
    """The validated pre-listing wipeout flags evaluated over a pool (same defs as N14 / wipeout_flags)."""
    sales = pd.to_numeric(pool.get("pre_ipo_net_sales"), errors="coerce")
    pat = pd.to_numeric(pool.get("pre_ipo_pat"), errors="coerce")
    return {
        "tiny sales (<25cr)": (sales < 25),
        "loss-making at IPO": (pat <= 0),
        "obscure lead manager": _obscure_banker_series(pool, df),
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
        sb = _as_bool_flag(s)                  # flag series may be float (coverage_guard) — coerce to bool
        nf = int(sb.sum())
        if nf >= config.MIN_N_HINT:
            wr = round(100 * float(bad[sb].mean()), 1)
            wo = round(100 * float(bad[~sb & s.notna()].mean()), 1)
            detail.append({"flag": qname, "failed_with_flag_%": wr, "failed_without_%": wo, "n_with": nf})
    # overall: place the query in its flag-count BAND (0/1/2/3+) and read that band's historical
    # bad-outcome rate, RELATIVE TO the segment's own base (MB and SME have very different base risk).
    cnt = sum(_as_bool_flag(s).astype(int) for s in pool_flags.values() if s is not None)
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
