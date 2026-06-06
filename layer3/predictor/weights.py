"""Data-informed scorecard weights.

Derives each component's weight from its HISTORICAL predictive power, point-in-time:
  1. For every matured past IPO, compute its 5 component scores using ONLY analogs that listed
     BEFORE it (freeze the analog set to pre-listing-date IPOs — no look-ahead on the analog SET).
  2. Measure each component's Spearman rank-IC vs that IPO's realized forward alpha, per cohort.
  3. Weight a component by its lift ONLY if the lift holds the SAME sign in boom AND longterm
     (cross-regime); sign-flippers and negatives → weight 0. Normalize.
This is transparent ("we weight X most because it predicted best, in both regimes") and is itself
an insight. NOT a black-box optimizer. Weights persist to data/master/scorecard_weights.json.
"""
import json
import pandas as pd
from layer3 import spine, config
from layer3.predictor import analogs, scorecard

COMPONENTS = ["return_potential", "multibagger_odds", "downside_safety", "liquidity", "quality", "wipeout_safety", "crowded_window"]
WEIGHTS_PATH = config.ROOT / "data/master/scorecard_weights.json"

_QUERY_FEATS = ["ctx_ipo_heat_90d", "broad_sector", "market_cap_class", "ofs_pct", "sub_total_x", "sub_qib_x",
                "pe_ratio", "pre_ipo_roe_pct", "pre_ipo_debt_equity", "pre_ipo_pat_margin_pct",
                "promoter_post_issue_pct", "gmp_pct", "issue_size_cr", "pre_ipo_pat",
                "pre_ipo_net_sales", "lead_manager"]   # last two feed the wipeout-safety component


def _query_from_row(r):
    q = {"type": r["type"]}
    for f in _QUERY_FEATS:
        v = r.get(f)
        if pd.notna(v):
            q[f] = v
    return q


_H_DAYS = {"1d": 1, "1w": 7, "1m": 30, "3m": 91, "6m": 182, "1y": 365,
           "2y": 730, "3y": 1095, "5y": 1825, "10y": 3650}


def score_all_pointintime(df, horizon="3y", max_ipos=None):
    """Score each matured IPO using only analogs whose OUTCOME was observable at the query's
    listing date — i.e. analog_listing + horizon <= query_listing. This removes look-ahead: an
    analog's matured alpha can only inform a query that listed AFTER the analog's horizon completed.
    Returns one row per IPO with its 5 component scores + realized alpha at `horizon`."""
    import pandas as _pd
    from layer3 import context as _ctx
    df = df.copy()
    if "ctx_ipo_heat_90d" not in df.columns:
        df = _ctx.add_context_features(df)        # point-in-time crowded-window feature
    df["_ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
    hd = _pd.Timedelta(days=_H_DAYS.get(horizon, 1095))
    matured = df[df[f"alpha_{horizon}"].notna() & df["_ld"].notna()].sort_values("_ld")
    if max_ipos and len(matured) > max_ipos:                     # even subsample for speed
        matured = matured.iloc[:: max(1, len(matured) // max_ipos)]
    rows = []
    for _, r in matured.iterrows():
        # analogs whose `horizon` outcome had ALREADY completed by the query's listing date
        prior = df[(df["_ld"] + hd) <= r["_ld"]]
        if len(prior) < config.MIN_N_TRADABLE:
            continue
        q = _query_from_row(r)
        ar = analogs.find_analogs(q, df=prior, exclude_isin=r["isin"])
        coh = ar["cohort"]
        if len(coh) < config.MIN_N_HINT:
            continue
        h = scorecard.pick_horizon(coh)
        rows.append({
            "isin": r["isin"], "cohort": r["cohort"], "realized_alpha": float(r[f"alpha_{horizon}"]),
            "return_potential": scorecard.return_potential(coh, h)["score"],
            "multibagger_odds": scorecard.multibagger_odds(coh, h)["score"],
            "downside_safety": scorecard.downside_safety(coh)["score"],
            "liquidity": scorecard.liquidity(coh)["score"],
            "quality": scorecard.quality(q)["score"],
            "wipeout_safety": scorecard.wipeout_safety(q, df=df)["score"],
            "crowded_window": scorecard.crowded_window(q, df=df)["score"],
        })
    return pd.DataFrame(rows)


def component_lift(scored):
    """Spearman rank-IC of each component score vs realized alpha, per cohort."""
    lift = {}
    for c in COMPONENTS:
        if c not in scored.columns:          # component absent from the scored frame -> no signal
            lift[c] = {coh: None for coh in config.COHORTS}
            continue
        per = {}
        for coh in config.COHORTS:
            s = scored[scored["cohort"] == coh][[c, "realized_alpha"]].dropna()
            # Spearman = Pearson on ranks (no scipy dependency); NaN (zero-variance) -> None
            ic = s[c].rank().corr(s["realized_alpha"].rank()) if len(s) >= config.MIN_N_TRADABLE else None
            per[coh] = float(ic) if (ic is not None and pd.notna(ic)) else None
        lift[c] = per
    return lift


def derive_weights(df=None, horizon="3y", max_ipos=None):
    """Returns (normalized_weights dict, report DataFrame, scored DataFrame)."""
    if df is None:
        df = spine.load_substrate()
    scored = score_all_pointintime(df, horizon, max_ipos)
    lift = component_lift(scored)
    raw, rep = {}, []
    for c in COMPONENTS:
        b, l = lift[c]["boom"], lift[c]["longterm"]
        if b is None or l is None:
            w, note = 0.0, "insufficient N → 0"
        elif (b > 0) == (l > 0):
            w = max(0.0, (b + l) / 2)
            note = "consistent (cross-regime)" if w > 0 else "consistently negative → 0"
        else:
            w, note = 0.0, "MIXED sign across regimes → 0"
        raw[c] = w
        rep.append({"component": c, "boom_IC": _r(b), "long_IC": _r(l),
                    "raw_weight": round(w, 3), "note": note})
    tot = sum(raw.values())
    weights = {c: (round(w / tot, 3) if tot > 0 else 0.0) for c, w in raw.items()}
    return weights, pd.DataFrame(rep), scored


CALIB_PATH = config.ROOT / "data/master/scorecard_calibration.json"


def save_weights(weights, path=WEIGHTS_PATH):
    path.write_text(json.dumps(weights, indent=2))


def load_weights(path=WEIGHTS_PATH):
    """Persisted data-informed weights, or None if not yet derived."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return None


def _combined(row, w):
    num = den = 0.0
    for k in COMPONENTS:
        v = row.get(k)
        if pd.notna(v) and w.get(k):
            num += w[k] * v; den += w[k]
    return (num / den) if den else None


def derive_calibration(df=None, horizon="3y"):
    """Combined-score quintile thresholds + the historical top-quintile lift, so the predictor can
    tell a user where their IPO's score falls and what that meant historically. Reuses the
    point-in-time scored set (one pass)."""
    if df is None:
        df = spine.load_substrate()
    scored = score_all_pointintime(df, horizon)
    w = load_weights() or {}
    scored = scored.copy()
    scored["combined"] = scored.apply(lambda r: _combined(r, w), axis=1)
    s = scored.dropna(subset=["combined", "realized_alpha"])
    quintiles = [round(float(s["combined"].quantile(q)), 1) for q in (0.2, 0.4, 0.6, 0.8)]
    thr = s["combined"].quantile(0.8)
    top = s[s["combined"] >= thr]
    lift = round(100 * (top["realized_alpha"].median() - s["realized_alpha"].median()), 1)
    return {"score_quintiles": quintiles, "top_quintile_lift_pp": lift, "n_scored": int(len(s))}


def oos_evaluate(df=None, cutoff_year=2022, horizon="1y"):
    """The HONEST report card: fit weights on IPOs listed <= cutoff_year (with matured outcomes),
    then apply them to score IPOs listed AFTER the cutoff and measure the top-quintile-vs-field lift
    on that TEST set — genuinely out-of-sample (the test IPOs were never used to fit the weights).
    Weights here = pooled train rank-IC (negatives→0, normalized); the cross-regime check is the
    separate validator. Returns the OOS lift (expected smaller than in-sample — that's the point)."""
    if df is None:
        df = spine.load_substrate()
    df = df.copy()
    df["_yr"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.year
    scored = score_all_pointintime(df, horizon).merge(df[["isin", "_yr"]], on="isin", how="left")
    train = scored[scored["_yr"] <= cutoff_year]
    test = scored[scored["_yr"] > cutoff_year].dropna(subset=["realized_alpha"])
    if len(train) < config.MIN_N_TRADABLE or len(test) < config.MIN_N_HINT:
        return {"cutoff": cutoff_year, "horizon": horizon, "n_train": len(train), "n_test": len(test),
                "error": "insufficient train or test N"}
    # fit weights on TRAIN only (pooled rank-IC vs realized alpha; clip negatives; normalize)
    w = {}
    for c in COMPONENTS:
        s = train[[c, "realized_alpha"]].dropna()
        ic = s[c].rank().corr(s["realized_alpha"].rank()) if len(s) >= config.MIN_N_TRADABLE else None
        w[c] = max(0.0, float(ic)) if (ic is not None and pd.notna(ic)) else 0.0
    tot = sum(w.values()); w = {c: (v / tot if tot else 0.0) for c, v in w.items()}
    test = test.copy()
    test["combined"] = test.apply(lambda r: _combined(r, w), axis=1)
    t = test.dropna(subset=["combined"])
    thr = t["combined"].quantile(0.8); top = t[t["combined"] >= thr]
    fld_med = t["realized_alpha"].median(); top_med = top["realized_alpha"].median()
    return {"cutoff": cutoff_year, "horizon": horizon, "n_train": len(train), "n_test": len(t),
            "weights": {k: round(v, 3) for k, v in w.items()},
            "test_field_median_%": round(100 * fld_med, 1),
            "test_topquintile_median_%": round(100 * top_med, 1),
            "oos_lift_pp": round(100 * (top_med - fld_med), 1),
            "top_win_rate_%": round(100 * (top["realized_alpha"] > 0).mean(), 1)}


def save_calibration(c, path=CALIB_PATH):
    path.write_text(json.dumps(c, indent=2))


def load_calibration(path=CALIB_PATH):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return None


def _r(x):
    return None if x is None else round(x, 3)
