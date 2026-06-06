"""OOS fold test for ctx_ipo_heat_90d per the evolve-only-if-robust policy:
does adding a crowded-window component improve the OOS top-quintile lift
robustly across cutoffs and horizons? Mirrors the wipeout_safety fold protocol."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd
from layer3 import spine, config, context
from layer3.predictor import weights as W

df = spine.load_substrate()
df = context.add_context_features(df)
df["_yr"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.year

def heat_score_pit(test_rows, train_rows):
    """0-100, crowded -> LOW (negative signal inverted), percentile within TRAIN per segment."""
    out = pd.Series(index=test_rows.index, dtype=float)
    for seg in ("MB", "SME"):
        ref = pd.to_numeric(train_rows.loc[train_rows["type"] == seg, "ctx_ipo_heat_90d"], errors="coerce").dropna()
        sub = test_rows[test_rows["type"] == seg]
        h = pd.to_numeric(sub["ctx_ipo_heat_90d"], errors="coerce")
        if len(ref) < 30:
            continue
        out.loc[sub.index] = h.map(lambda v: (1 - (ref < v).mean()) * 100 if pd.notna(v) else None)
    return out

print(f"{'cutoff':>6} {'h':>3} {'n_test':>6} {'base_lift':>9} {'heat_lift':>9} {'delta':>6}  heat_w")
results = []
for horizon in ("1y", "3y"):
    scored = W.score_all_pointintime(df, horizon).merge(df[["isin", "_yr", "type", "ctx_ipo_heat_90d"]], on="isin", how="left")
    for cutoff in (2021, 2022, 2023):
        train = scored[scored["_yr"] <= cutoff]
        test = scored[scored["_yr"] > cutoff].dropna(subset=["realized_alpha"]).copy()
        if len(train) < config.MIN_N_TRADABLE or len(test) < config.MIN_N_HINT:
            continue
        test["heat_score"] = heat_score_pit(test, train)
        train = train.copy(); train["heat_score"] = heat_score_pit(train, train)
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
        heat, w2 = lift(W.COMPONENTS + ["heat_score"])
        results.append((cutoff, horizon, len(test), base, heat, round(heat - base, 1)))
        print(f"{cutoff:>6} {horizon:>3} {len(test):>6} {base:>9} {heat:>9} {round(heat-base,1):>6}  {round(w2.get('heat_score',0),3)}")
wins = sum(1 for r in results if r[5] > 0)
print(f"\nVERDICT input: heat improved lift in {wins}/{len(results)} splits")
