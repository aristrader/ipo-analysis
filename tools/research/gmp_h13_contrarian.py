import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from layer3 import spine

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok","inferred_split","recovered_bhavcopy"))].copy()

# Try to find the open/close columns
open_col = 'adj_listing_open' if 'adj_listing_open' in df.columns else 'listing_open'
close_col = 'adj_listing_close' if 'adj_listing_close' in df.columns else 'listing_close'

for horizon in ["1m", "3m"]:
    rfl_col = f"return_from_listing_{horizon}"
    alpha_col = f"alpha_{horizon}"
    if rfl_col in df.columns and alpha_col in df.columns:
        rfl = pd.to_numeric(df[rfl_col], errors="coerce")
        alpha_close = pd.to_numeric(df[alpha_col], errors="coerce")
        bench = rfl - alpha_close
        
        c = pd.to_numeric(df[close_col], errors="coerce")
        o = pd.to_numeric(df[open_col], errors="coerce")
        
        val = c * (1 + rfl)
        r_open = val / o - 1
        df[f"alpha_open_{horizon}"] = r_open - bench
    else:
        df[f"alpha_open_{horizon}"] = np.nan

print("="*70)
print("H13 — Hated Contrarian: Are IPOs with GMP <= 0 contrarian opportunities?")
print("="*70)

for typ in ("MB", "SME"):
    sub = df[(df["type"] == typ) & df["gmp_pct"].notna()]
    if len(sub) == 0: continue
    
    hated = sub[sub["gmp_pct"] <= 0]
    loved = sub[sub["gmp_pct"] > 0]
    
    print(f"[{typ}] All IPOs with GMP data: n={len(sub)}")
    print(f"[{typ}] Hated (GMP <= 0): n={len(hated)}")
    print(f"[{typ}] Loved (GMP >  0): n={len(loved)}")
    print("-" * 70)
    
    for horizon in ["1m", "3m"]:
        col = f"alpha_open_{horizon}"
        if col not in df.columns:
            print(f"  {typ} alpha_{horizon}: Column missing")
            continue
            
        h_alpha = hated[col].dropna()
        l_alpha = loved[col].dropna()
        
        if len(h_alpha) > 0 and len(l_alpha) > 0:
            h_med = h_alpha.median() * 100
            l_med = l_alpha.median() * 100
            h_win = (h_alpha > 0).mean() * 100
            l_win = (l_alpha > 0).mean() * 100
            
            print(f"  {typ} alpha_{horizon} (from listing open):")
            print(f"    Hated: Median Alpha = {h_med:+.1f}%, Win Rate = {h_win:.1f}% (n={len(h_alpha)})")
            print(f"    Loved: Median Alpha = {l_med:+.1f}%, Win Rate = {l_win:.1f}% (n={len(l_alpha)})")
            print(f"    Spread (Hated - Loved) = {h_med - l_med:+.1f}pp")
        else:
            print(f"  {typ} alpha_{horizon}: Not enough data")
    print("=" * 70)
