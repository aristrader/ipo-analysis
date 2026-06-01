"""The loop-closer: does the PREDICTOR'S OWN combined score beat the field?

Reuses the point-in-time component scoring (layer3.predictor.weights.score_all_pointintime) +
the data-informed weights to give each past IPO a combined score from PRE-listing-knowable info
only, then tests whether the top-quintile-score IPOs out-performed the rest on realized forward
alpha — per cohort, so a real edge must hold cross-regime. This is the integration test of Part B.
"""
import pandas as pd
from layer3 import spine, config
from layer3.predictor import weights as W, scorecard


def _combined(row, w):
    num = den = 0.0
    for k in W.COMPONENTS:
        v = row.get(k)
        if pd.notna(v) and w.get(k):
            num += w[k] * v; den += w[k]
    return (num / den) if den else None


def combined_score_backtest(df=None, horizon="3y"):
    if df is None:
        df = spine.load_substrate()
    scored = W.score_all_pointintime(df, horizon)
    w = W.load_weights() or scorecard.PRESETS["balanced"]
    scored = scored.copy()
    scored["combined"] = scored.apply(lambda r: _combined(r, w), axis=1)
    rows = []
    for grp in ["ALL", "boom", "longterm"]:
        s = (scored if grp == "ALL" else scored[scored["cohort"] == grp]).dropna(subset=["combined", "realized_alpha"])
        if len(s) < config.MIN_N_TRADABLE:
            continue
        thr = s["combined"].quantile(0.8)
        top, rest = s[s["combined"] >= thr], s[s["combined"] < thr]
        am = s["realized_alpha"].median()
        rows.append({"group": grp, "N": len(s), "N_top_quintile": len(top),
                     "top_median_alpha_%": round(100 * top["realized_alpha"].median(), 1),
                     "rest_median_alpha_%": round(100 * rest["realized_alpha"].median(), 1),
                     "all_median_alpha_%": round(100 * am, 1),
                     "top_win_rate_%": round(100 * (top["realized_alpha"] > 0).mean(), 1),
                     "lift_vs_all_pp": round(100 * (top["realized_alpha"].median() - am), 1)})
    res = pd.DataFrame(rows)
    # bootstrap sign-stability of the ALL-group lift (top-quintile median − field median)
    import numpy as np
    sa = scored.dropna(subset=["combined", "realized_alpha"])
    thr = sa["combined"].quantile(0.8)
    base = sa["realized_alpha"].to_numpy(); topm = (sa["combined"] >= thr).to_numpy()
    rng = np.random.default_rng(0); lifts = []
    for _ in range(1000):
        idx = rng.integers(0, len(base), len(base))
        b = base[idx]; t = topm[idx]
        if t.sum() >= config.MIN_N_HINT and (~t).sum() >= config.MIN_N_HINT:
            lifts.append(np.median(b[t]) - np.median(b))
    lift_p_positive = float(np.mean(np.array(lifts) > 0)) if lifts else None
    # cross-regime verdict: top-quintile must out-perform the field in BOTH regimes
    boom = res[res.group == "boom"]["lift_vs_all_pp"]
    long = res[res.group == "longterm"]["lift_vs_all_pp"]
    if len(boom) and len(long):
        b, l = boom.iloc[0], long.iloc[0]
        if b > 0 and l > 0:
            verdict = (f"top-quintile beats the field WITHIN each regime (boom +{b:.0f}pp, long +{l:.0f}pp) — but "
                       "IN-SAMPLE (weights fit on the same universe) → INDICATIVE, not out-of-sample-validated")
        elif b <= 0 and l <= 0:
            verdict = "score does NOT beat the field in either regime"
        else:
            verdict = "MIXED — top-quintile edge flips sign by regime"
    else:
        verdict = "insufficient cohort N"
    if lift_p_positive is not None:
        verdict += f" | bootstrap (in-sample): lift>0 in {lift_p_positive:.0%} of resamples"
    return res, verdict
