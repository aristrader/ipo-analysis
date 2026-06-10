"""A1/A1b evolve-only-if-robust fold test: does the CANDIDATE obscure-banker definition, folded into
wipeout_safety, improve/preserve OOS top-quintile lift vs the legacy (freq<12) definition?

We rebuild wipeout_safety's flag-count two ways and re-derive PIT weights on train, then measure the
test-fold top-quintile alpha lift. Mirrors heat_fold_test. Bar: candidate must not DEGRADE lift.
Usage: a1_fold_test.py [horizon=3y] [candidate_mode=coverage_guard]   (legacy is always the baseline arm).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config
from layer3.predictor import weights as W, scorecard

df = spine.load_substrate()
df = df[df.get("listing_metrics_status") != "unreliable_coverage"].copy()
df["_yr"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.year

# we compare two component frames: wipeout_safety using legacy vs the CANDIDATE obscure-banker def.
HORIZON = sys.argv[1] if len(sys.argv) > 1 else "3y"
CAND = sys.argv[2] if len(sys.argv) > 2 else "coverage_guard"
def scored_frame_h(mode, h):
    scorecard.OBSCURE_BANKER_MODE = mode
    return W.score_all_pointintime(df, h).merge(df[["isin", "_yr", "type"]], on="isin", how="left")
print(f"horizon={HORIZON}; scoring legacy (freq<12) ...")
cur = scored_frame_h("legacy", HORIZON)
print(f"scoring candidate ({CAND}) ...")
new = scored_frame_h(CAND, HORIZON)
scorecard.OBSCURE_BANKER_MODE = "legacy"        # restore the live default

def fold_lift(scored):
    out = []
    for cutoff in (2021, 2022, 2023):
        train = scored[scored["_yr"] <= cutoff]
        test = scored[scored["_yr"] > cutoff].dropna(subset=["realized_alpha"]).copy()
        if len(train) < config.MIN_N_TRADABLE or len(test) < config.MIN_N_HINT:
            continue
        w = {}
        for c in W.COMPONENTS:
            s = train[[c, "realized_alpha"]].dropna()
            ic = s[c].rank().corr(s["realized_alpha"].rank()) if len(s) >= config.MIN_N_TRADABLE else None
            w[c] = max(0.0, float(ic)) if (ic is not None and pd.notna(ic)) else 0.0
        tot = sum(w.values()); w = {c: v / tot for c, v in w.items()} if tot else w
        t = test.copy()
        t["combined"] = t[W.COMPONENTS].mul(pd.Series(w)).sum(axis=1, skipna=True) / \
                        t[W.COMPONENTS].notna().mul(pd.Series(w)).sum(axis=1)
        t = t.dropna(subset=["combined"])
        thr = t["combined"].quantile(0.8)
        top = t[t["combined"] >= thr]
        lift = round(100 * (top["realized_alpha"].median() - t["realized_alpha"].median()), 1)
        out.append((cutoff, len(test), lift, round(w.get("wipeout_safety", 0), 3)))
    return out

print(f"\n{'cutoff':>6} {'n_test':>6} {'CUR_lift':>9} {'NEW_lift':>9} {'delta':>6} {'cur_wsW':>7} {'new_wsW':>7}")
cl = {r[0]: r for r in fold_lift(cur)}
nl = {r[0]: r for r in fold_lift(new)}
better = same = worse = 0
for c in sorted(set(cl) | set(nl)):
    rc, rn = cl.get(c), nl.get(c)
    if rc and rn:
        d = round(rn[2] - rc[2], 1)
        better += d > 0; same += d == 0; worse += d < 0
        print(f"{c:>6} {rn[1]:>6} {rc[2]:>9} {rn[2]:>9} {d:>6} {rc[3]:>7} {rn[3]:>7}")
print(f"\nNEW vs CUR: better {better}, same {same}, worse {worse}")
