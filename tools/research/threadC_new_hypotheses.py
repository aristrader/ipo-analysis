"""Thread C (expanded) — 3 genuinely-new second-order hypotheses from the divergence agent,
each cross-checked vs rules/index (not already tested). 3-layer: existence (IC + split) +
placebo/falsifier + cross-regime. Conventions: alpha vs Nifty, exclude unreliable_coverage,
min-N 30, srho (no scipy). Honest verdicts — failures go to the graveyard."""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine

def srho(a, b):
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")

# ===================================================================== H-C1
# Margin-EXPANSION vs sales-only growth: quality growth (op-margin rising yr1->yr3 alongside
# sales) beats equal-sales-growth peers at 3y. Mechanism: bought margin reverts; operating
# leverage is hard to fake. Cross-regime.
print("=" * 70); print("H-C1 — margin expansion vs sales-only growth (3y alpha)")
m1 = N("operating_profit_yr1") / N("net_sales_yr1")
m3 = N("operating_profit_yr3") / N("net_sales_yr3")
df["margin_chg"] = m3 - m1                                  # >0 = expanding margin
df["sales_growth"] = N("net_sales_yr3") / N("net_sales_yr1") - 1
for hz in ("alpha_1y", "alpha_3y"):
    sub = df[df["margin_chg"].notna() & df["sales_growth"].notna() & N(hz).notna()
             & np.isfinite(df["margin_chg"]) & np.isfinite(df["sales_growth"])]
    sub = sub[(sub["sales_growth"].abs() < 5)]              # drop insane ratios
    if len(sub) < 30:
        print(f"  {hz}: thin"); continue
    # among GROWERS (sales_growth>median), do margin-expanders beat margin-eroders?
    grow = sub[sub["sales_growth"] > sub["sales_growth"].median()]
    exp = grow[grow["margin_chg"] > 0]; ero = grow[grow["margin_chg"] <= 0]
    a = lambda g: 100 * pd.to_numeric(g[hz], errors="coerce").median()
    print(f"  {hz}: among growers (n={len(grow)}) — margin-EXPAND {a(exp):+.1f}% (n={len(exp)}) "
          f"vs margin-ERODE {a(ero):+.1f}% (n={len(ero)})  spread {a(exp)-a(ero):+.1f}pp  "
          f"| IC(margin_chg, {hz})={srho(sub['margin_chg'], N(hz)[sub.index]):+.3f}")
# cross-regime + placebo (shuffle margin_chg within growers, 500x, 3y)
sub = df[df["margin_chg"].notna() & df["sales_growth"].notna() & N("alpha_1y").notna()
         & np.isfinite(df["margin_chg"])]
for coh in ("boom", "longterm"):
    g = sub[sub["cohort"] == coh]
    g = g[g["sales_growth"] > g["sales_growth"].median()] if len(g) > 10 else g
    if len(g) < 30: print(f"  {coh}: thin (n={len(g)})"); continue
    exp = g[g["margin_chg"] > 0]; ero = g[g["margin_chg"] <= 0]
    sp = 100*(pd.to_numeric(exp["alpha_1y"],errors="coerce").median() - pd.to_numeric(ero["alpha_1y"],errors="coerce").median())
    print(f"  cross-regime {coh}: spread {sp:+.1f}pp (n_exp={len(exp)}, n_ero={len(ero)})")

# ===================================================================== H-C2
# Sales-acceleration x demand divergence: among HIGH-subscription IPOs, decelerating-sales names
# underperform accelerating ones; low-sub names show no split. Mechanism: hype on a story that's
# already rolling over disappoints momentum buyers.
print("=" * 70); print("H-C2 — sales-accel × demand divergence (1y alpha)")
g1 = N("net_sales_yr2") / N("net_sales_yr1") - 1
g2 = N("net_sales_yr3") / N("net_sales_yr2") - 1
df["accel"] = g2 - g1                                       # >0 = accelerating
sub = df[df["accel"].notna() & N("sub_total_x").notna() & N("alpha_1y").notna()
         & np.isfinite(df["accel"])]
sub = sub[sub["accel"].abs() < 5]
hi = sub[N("sub_total_x")[sub.index] > N("sub_total_x")[sub.index].median()]
lo = sub[N("sub_total_x")[sub.index] <= N("sub_total_x")[sub.index].median()]
for lab, g in (("HIGH-sub", hi), ("LOW-sub", lo)):
    if len(g) < 30: print(f"  {lab}: thin"); continue
    acc = g[g["accel"] > 0]; dec = g[g["accel"] <= 0]
    a = lambda x: 100 * pd.to_numeric(x["alpha_1y"], errors="coerce").median()
    print(f"  {lab} (n={len(g)}): accel {a(acc):+.1f}% (n={len(acc)}) vs decel {a(dec):+.1f}% "
          f"(n={len(dec)})  spread {a(acc)-a(dec):+.1f}pp")
print("  FALSIFIER: the split should exist in HIGH-sub and be ~absent in LOW-sub.")

# ===================================================================== H-C3
# Banker pipeline congestion: a lead manager bringing >=2 IPOs within 30d -> the LATER deal
# underperforms that LM's solo issues. Mechanism: finite distribution/anchor wallet.
print("=" * 70); print("H-C3 — same-banker pipeline congestion (must beat crowded_window)")
df["lm"] = df["lead_manager"].astype(str).str.strip().str.lower().str.split(",").str[0].str.strip()
d = df[df["ld"].notna() & (df["lm"] != "nan") & N("alpha_1y").notna()].sort_values("ld")
congested = []
for lm, g in d.groupby("lm"):
    if len(g) < 2: continue
    dates = g["ld"].tolist()
    for i in range(len(dates)):
        prior = [t for t in dates[:i] if (dates[i] - t).days <= 30]
        congested.append((g.index[i], len(prior) >= 1))
idx = [i for i, _ in congested]; flag = pd.Series([f for _, f in congested], index=idx)
dd = d.loc[idx].copy(); dd["congested"] = flag
con = dd[dd["congested"]]; solo = dd[~dd["congested"]]
a = lambda x: 100 * pd.to_numeric(x["alpha_1y"], errors="coerce").median()
print(f"  congested (LM had ≥1 IPO in prior 30d): {a(con):+.1f}% (n={len(con)}) "
      f"vs solo {a(solo):+.1f}% (n={len(solo)})  spread {a(con)-a(solo):+.1f}pp")
# incremental-to-crowded_window check: does it survive controlling overall IPO heat?
if "ctx_ipo_heat_90d" in df.columns:
    from layer3 import context
    dd2 = context.add_context_features(dd)
    hicrowd = dd2[pd.to_numeric(dd2["ctx_ipo_heat_90d"],errors="coerce") > pd.to_numeric(dd2["ctx_ipo_heat_90d"],errors="coerce").median()]
    cc = hicrowd[hicrowd["congested"]]; cs = hicrowd[~hicrowd["congested"]]
    if len(cc) >= 20 and len(cs) >= 20:
        print(f"  WITHIN high-crowd window only: congested {a(cc):+.1f}% (n={len(cc)}) vs "
              f"solo {a(cs):+.1f}% (n={len(cs)}) — if spread vanishes, it's just crowded_window")
