"""Thread C / H2: does pe_vs_sector (rich issue-time P/E vs sector median → underperformance),
validated MB-only (−43pp), replicate on SME now that we have 632 SME P/Es?
3-layer: L1 existence (rank-IC + high/low split), L2 magnitude, L3 cross-regime honesty.
Conventions: alpha vs Nifty; exclude unreliable_coverage; min-N floors; srho (no scipy)."""
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
df = df[df["listing_metrics_status"].isin(("ok","inferred_split","recovered_bhavcopy"))].copy()
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["ip"] = N("issue_price"); df["eps"] = N("eps_ttm")
df["pe"] = np.where((df["ip"]>0)&(df["eps"]>0), df["ip"]/df["eps"], np.nan)
# fall back to provided pe_ratio where our compute is null
df["pe"] = df["pe"].fillna(N("pe_ratio"))
df["a1y"] = N("alpha_1y"); df["a3y"] = N("alpha_3y")

def rel_pe(sub):
    """issue-time P/E relative to the sector median (within the same cohort+type)."""
    out = sub.copy()
    out["pe_rel"] = np.nan
    for (sec), g in out.groupby("broad_sector"):
        med = g["pe"].median()
        if pd.notna(med) and med > 0:
            out.loc[g.index, "pe_rel"] = g["pe"] / med
    return out

print("="*70); print("H2 — rich P/E vs sector median -> underperformance? (SME replication)")
for typ in ("MB","SME"):
    sub = rel_pe(df[(df["type"]==typ) & df["pe"].notna() & df["broad_sector"].notna()])
    sub = sub[sub["pe_rel"].notna() & sub["a1y"].notna()]
    if len(sub) < 30:
        print(f"  {typ}: thin (n={len(sub)})"); continue
    ic = srho(sub["pe_rel"], sub["a1y"])
    hi = sub[sub["pe_rel"] > sub["pe_rel"].median()]; lo = sub[sub["pe_rel"] <= sub["pe_rel"].median()]
    spread = 100*(hi["a1y"].median() - lo["a1y"].median())
    print(f"  {typ}: n={len(sub)}  IC(rel_PE, alpha_1y)={ic:+.3f}  "
          f"rich-PE median a1y {100*hi['a1y'].median():+.1f}% vs cheap {100*lo['a1y'].median():+.1f}%  "
          f"spread {spread:+.1f}pp  (negative = rich underperforms = the MB pattern)")

print("="*70); print("Cross-regime (SME by cohort — the validation gate):")
for coh in ("boom","longterm"):
    sub = rel_pe(df[(df["type"]=="SME") & (df["cohort"]==coh) & df["pe"].notna() & df["broad_sector"].notna()])
    sub = sub[sub["pe_rel"].notna() & sub["a1y"].notna()]
    if len(sub) < 30:
        print(f"  SME/{coh}: thin (n={len(sub)}) — cannot validate this cell"); continue
    ic = srho(sub["pe_rel"], sub["a1y"])
    hi = sub[sub["pe_rel"] > sub["pe_rel"].median()]; lo = sub[sub["pe_rel"] <= sub["pe_rel"].median()]
    print(f"  SME/{coh}: n={len(sub)} IC={ic:+.3f} spread {100*(hi['a1y'].median()-lo['a1y'].median()):+.1f}pp")
