"""OOS fold test for the F7 trailing-climate signal (cold-tape listers outperform), per the
evolve-only-if-robust score policy. Climate = trailing-60d median listing pop of same-type
listers (point-in-time, >=5 priors). Candidate component = COLD percentile vs TRAIN segment
(cold -> high score). Mirrors heat_fold_test.py exactly."""
import sys, os, bisect
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config
from layer3.predictor import weights as W

df = spine.load_substrate()
df["_yr"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.year
df["_ld"] = pd.to_datetime(df["listing_date"], errors="coerce")

# point-in-time trailing climate per row (same-type, prior 60 calendar days, >=5 priors)
df["_climate"] = np.nan
for typ, g in df[df["_ld"].notna()].groupby("type"):
    g = g.sort_values("_ld")
    dates = g["_ld"].tolist()
    pops = pd.to_numeric(g["adj_listing_gain_open"], errors="coerce").tolist()
    vals = []
    for i, t in enumerate(dates):
        lo = bisect.bisect_left(dates, t - pd.Timedelta(days=60)); hi = bisect.bisect_left(dates, t)
        w = [pops[j] for j in range(lo, hi) if not pd.isna(pops[j])]
        vals.append(np.median(w) if len(w) >= 5 else np.nan)
    df.loc[g.index, "_climate"] = vals

def climate_score_pit(test_rows, train_rows):
    """0-100, COLD tape -> HIGH (the validated direction), percentile within TRAIN per segment."""
    out = pd.Series(index=test_rows.index, dtype=float)
    for seg in ("MB", "SME"):
        ref = pd.to_numeric(train_rows.loc[train_rows["type"] == seg, "_climate"], errors="coerce").dropna()
        sub = test_rows[test_rows["type"] == seg]
        c = pd.to_numeric(sub["_climate"], errors="coerce")
        if len(ref) < 30:
            continue
        out.loc[sub.index] = c.map(lambda v: (ref > v).mean() * 100 if pd.notna(v) else None)
    return out

print(f"{'cutoff':>6} {'h':>3} {'n_test':>6} {'base_lift':>9} {'clim_lift':>9} {'delta':>6}  clim_w")
results = []
for horizon in ("1y", "3y"):
    scored = W.score_all_pointintime(df, horizon).merge(
        df[["isin", "_yr", "type", "_climate"]], on="isin", how="left")
    for cutoff in (2021, 2022, 2023):
        train = scored[scored["_yr"] <= cutoff]
        test = scored[scored["_yr"] > cutoff].dropna(subset=["realized_alpha"]).copy()
        if len(train) < config.MIN_N_TRADABLE or len(test) < config.MIN_N_HINT:
            continue
        test["clim_score"] = climate_score_pit(test, train)
        train = train.copy(); train["clim_score"] = climate_score_pit(train, train)
        def lift(components):
            w = {}
            for c in components:
                s = train[[c, "realized_alpha"]].dropna()
                ic = s[c].rank().corr(s["realized_alpha"].rank()) if len(s) >= config.MIN_N_TRADABLE else None
                w[c] = max(0.0, float(ic)) if (ic is not None and pd.notna(ic)) else 0.0
            tot = sum(w.values()); w = {c: v / tot for c, v in w.items()} if tot else w
            t = test.copy()
            t["combined"] = t[components].mul(pd.Series(w)).sum(axis=1, skipna=True) / \
                            t[components].notna().mul(pd.Series(w)).sum(axis=1)
            t = t.dropna(subset=["combined"])
            thr = t["combined"].quantile(0.8)
            top = t[t["combined"] >= thr]
            return round(100 * (top["realized_alpha"].median() - t["realized_alpha"].median()), 1), w
        base, _ = lift(W.COMPONENTS)
        clim, w2 = lift(W.COMPONENTS + ["clim_score"])
        results.append((cutoff, horizon, len(test), base, clim, round(clim - base, 1)))
        print(f"{cutoff:>6} {horizon:>3} {len(test):>6} {base:>9} {clim:>9} {round(clim-base,1):>6}  {round(w2.get('clim_score',0),3)}")
wins = sum(1 for r in results if r[5] > 0)
print(f"\nVERDICT input: climate improved OOS top-quintile lift in {wins}/{len(results)} splits")
