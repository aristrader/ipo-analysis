"""Tier-1 wave 1a: T2f (regime vs year as vintage — gating decision) + F3 (regime-gated
junk bounce, 3 layers). Read-only; compact output."""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config, regimes

df = spine.load_substrate()
df = regimes.add_regime_features(df)
N = lambda c: pd.to_numeric(df[c], errors="coerce")
ld = pd.to_datetime(df["listing_date"], errors="coerce")
df["_yr"] = ld.dt.year

# ---------------- T2f: nested R^2 — year dummies vs regime (dir60, vol20, phase) ----------------
print("=" * 72); print("T2f — VINTAGE: calendar-year vs rolling regime (nested R²)")
def r2(X, y):
    X = np.column_stack([np.ones(len(X))] + [X[:, i] for i in range(X.shape[1])]) if X.size else np.ones((len(y), 1))
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    ss_res = ((y - pred) ** 2).sum(); ss_tot = ((y - y.mean()) ** 2).sum()
    n, k = len(y), X.shape[1] - 1
    r2v = 1 - ss_res / ss_tot
    adj = 1 - (1 - r2v) * (n - 1) / (n - k - 1)
    return adj

results = []
for target_name in ("alpha_1y", "alpha_1m"):
    for coh in ("boom", "longterm"):
        m = (df["cohort"] == coh) & N(target_name).notna() & df["dir60"].notna() & df["vol20"].notna() & df["phase"].notna()
        sub = df[m]
        y = pd.to_numeric(sub[target_name], errors="coerce").values
        yrs = pd.get_dummies(sub["_yr"].astype(int), drop_first=True).values.astype(float)
        reg = sub[["dir60", "vol20", "phase"]].astype(float).values
        a_year = r2(yrs, y)
        a_reg = r2(reg, y)
        a_both = r2(np.column_stack([yrs, reg]), y)
        results.append((target_name, coh, len(sub), round(a_year, 4), round(a_reg, 4), round(a_both, 4),
                        round(a_both - a_reg, 4), round(a_both - a_year, 4)))
print(f"{'target':9s} {'coh':9s} {'n':>5s} {'R2_year':>8s} {'R2_regime':>9s} {'R2_both':>8s} {'yr_increm':>9s} {'reg_increm':>10s}")
for r in results:
    print(f"{r[0]:9s} {r[1]:9s} {r[2]:>5d} {r[3]:>8} {r[4]:>9} {r[5]:>8} {r[6]:>9} {r[7]:>10}")
reg_wins = sum(1 for r in results if r[7] > r[6])
print(f"VERDICT input: regime adds more beyond year in {reg_wins}/{len(results)} cells "
      f"(regime-increment > year-increment)")

# ---------------- F3: regime-gated junk bounce ----------------
print("=" * 72); print("F3 — REGIME-GATED JUNK BOUNCE (L1-L3)")
# quality proxy: use the substrate's combined data-informed components? No per-row stored score —
# use the forward-test convention: score terciles via gmp/sub/size? The SPEC says score bottom tercile.
# Per-row score isn't persisted; use the validated wipeout-flag count + downside proxies is heavy.
# PRAGMATIC quality proxy (declared): data_quality-independent composite = within-cohort tercile of
# alpha-RANK predictors already in-score is circular; instead use the PRE-LISTING demand-quality proxy:
# gmp_pct & sub_total_x BOTH below segment median = "junk-proxy" (weak demand). Declared deviation
# from spec (no persisted per-row score); revisit with score_all_pointintime later (expensive).
g = df[df["cohort"].isin(["boom", "longterm"])].copy()
g = g[g["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))]
gmp_med = g.groupby("type")["gmp_pct"].transform(lambda s: pd.to_numeric(s, errors="coerce").median())
sub_med = g.groupby("type")["sub_total_x"].transform(lambda s: pd.to_numeric(s, errors="coerce").median())
gmp_v = pd.to_numeric(g["gmp_pct"], errors="coerce"); sub_v = pd.to_numeric(g["sub_total_x"], errors="coerce")
g["junk"] = (gmp_v < gmp_med) & (sub_v < sub_med)
g["bull"] = g["dir60_t"] == "hi"
mfe1 = pd.to_numeric(g["mfe_lst_1m"], errors="coerce")
r1m = pd.to_numeric(g["return_from_listing_1m"], errors="coerce")

print("L1/L2 — median month-1 peak (mfe_lst_1m) by junk x regime:")
print(f"{'seg':4s} {'cell':16s} {'n':>5s} {'med_MFE1m%':>10s} {'P(MFE>=15%)':>11s} {'med_end_1m%':>11s}")
cells = {}
for seg in ("MB", "SME"):
    for jl, jv in (("junk", True), ("non-junk", False)):
        for bl, bv in (("bull", True), ("non-bull", False)):
            m = (g["type"] == seg) & (g["junk"] == jv) & (g["bull"] == bv) & mfe1.notna()
            n = int(m.sum())
            if n < config.MIN_N_HINT:
                continue
            cells[(seg, jl, bl)] = (mfe1[m], r1m[m])
            print(f"{seg:4s} {jl+'×'+bl:16s} {n:>5d} {100*mfe1[m].median():>10.1f} "
                  f"{100*(mfe1[m]>=0.15).mean():>11.1f} {100*r1m[m].median():>11.1f}")

# placebo: shuffle bull labels 200x, junk-bull-minus-junk-bear MFE gap must beat p95
rng = np.random.default_rng(0)
for seg in ("MB", "SME"):
    try:
        real_gap = cells[(seg, "junk", "bull")][0].median() - cells[(seg, "junk", "non-bull")][0].median()
    except KeyError:
        continue
    sub_g = g[(g["type"] == seg) & g["junk"] & mfe1.notna()]
    vals = pd.to_numeric(sub_g["mfe_lst_1m"], errors="coerce").values
    bulls = sub_g["bull"].values.copy()
    gaps = []
    for _ in range(200):
        rng.shuffle(bulls)
        gaps.append(np.median(vals[bulls]) - np.median(vals[~bulls]))
    p95 = np.quantile(gaps, 0.95)
    print(f"PLACEBO {seg}: real junk bull-vs-nonbull MFE gap {100*real_gap:.1f}pp vs shuffle p95 {100*p95:.1f}pp "
          f"-> {'BEATS' if real_gap > p95 else 'fails'}")

# L3 playbook: TP grid on junk x bull (entry listing close), TP {15,25,40}% x cap {21d->1m proxy}
print("L3 — take-profit grid on junk×bull (vs buy&hold-1m), per segment:")
print(f"{'seg':4s} {'TP':>5s} {'n':>5s} {'hit%':>6s} {'rule_med%':>9s} {'bh_med%':>8s} {'delta':>6s}")
for seg in ("MB", "SME"):
    if (seg, "junk", "bull") not in cells:
        continue
    mfe_c, end_c = cells[(seg, "junk", "bull")]
    for tp in (0.15, 0.25, 0.40):
        hit = mfe_c >= tp
        rule = np.where(hit, tp, end_c)
        print(f"{seg:4s} {int(tp*100):>4d}% {len(mfe_c):>5d} {100*hit.mean():>6.1f} "
              f"{100*np.median(rule):>9.1f} {100*end_c.median():>8.1f} {100*(np.median(rule)-end_c.median()):>6.1f}")
    # failure cell: same rule in junk x non-bull
    mfe_n, end_n = cells[(seg, "junk", "non-bull")]
    hit = mfe_n >= 0.25
    rule = np.where(hit, 0.25, end_n)
    print(f"{seg:4s} FAILURE-CELL junk×non-bull TP25: rule {100*np.median(rule):.1f}% vs bh {100*end_n.median():.1f}%")
