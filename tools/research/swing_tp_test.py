"""Owner swing-trade test (2026-06-08): buy at listing close, SELL the first day it closes
>= +X% ('take profit'), else hold to 1y. Counterfactual = buy-and-hold to 1y on the SAME entry.
Question: does locking +20% beat holding? Report median AND mean AND P90 (the right tail is the
whole point) + win-rate. Conditional variant: only enter when month-1 was strong (up-day ratio
>= 0.5 — the one validated post-listing lean). Raw returns (TP vs hold on identical entries —
market drift hits both equally, so the relative read is clean)."""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
df = df[df["ld"].notna()]

HORIZON = 252            # ~1 trading year
TPS = (0.20, 0.30, 0.50)

rows = []
for _, r in df.iterrows():
    p = f"data/prices/{r['isin']}.csv"
    if not os.path.exists(p):
        continue
    try:
        pr = pd.read_csv(p)
    except Exception:
        continue
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[pr["date"] >= r["ld"]].sort_values("date").reset_index(drop=True)
    if len(pr) < 30:
        continue
    closes = pr["close"].astype(float).values
    entry = closes[0]
    if entry <= 0:
        continue
    window = closes[1:HORIZON + 1]
    if len(window) < 20:
        continue
    hold = window[-1] / entry - 1                         # buy-and-hold to end of window
    # month-1 strength (up-day ratio over first 21 sessions)
    m1 = closes[1:22]
    updays = np.mean(np.diff(np.r_[entry, m1]) > 0) if len(m1) >= 10 else np.nan
    rec = {"isin": r["isin"], "type": r["type"], "cohort": r["cohort"],
           "hold": hold, "m1_strong": (updays >= 0.5) if not np.isnan(updays) else None}
    for tp in TPS:
        hit = np.where(window >= entry * (1 + tp))[0]
        if len(hit):
            # sell at that day's close (>= the +tp threshold)
            rec[f"tp{int(tp*100)}"] = window[hit[0]] / entry - 1
        else:
            rec[f"tp{int(tp*100)}"] = hold                # never hit -> hold to end
    rows.append(rec)

t = pd.DataFrame(rows)
print(f"names tested: {len(t)} (entry=listing close, window={HORIZON}td)\n")

def line(label, s):
    s = pd.Series(s).dropna()
    return (f"  {label:24s} n={len(s):4d}  median {100*s.median():+6.1f}%  "
            f"mean {100*s.mean():+7.1f}%  P90 {100*s.quantile(.9):+7.1f}%  win {100*(s>0).mean():3.0f}%")

for scope, mask in (("ALL listed", t.index == t.index),
                    ("month-1 STRONG entry", t["m1_strong"] == True)):
    g = t[mask]
    if len(g) < 30:
        print(f"{scope}: thin ({len(g)})"); continue
    print(f"=== {scope} (n={len(g)}) ===")
    print(line("buy & hold 1y", g["hold"]))
    for tp in TPS:
        print(line(f"take-profit +{int(tp*100)}%", g[f"tp{int(tp*100)}"]))
    # how often did TP20 actually fire vs ride to end?
    fired = (g["tp20"] != g["hold"]).mean()
    print(f"  (TP+20% fired on {100*fired:.0f}% of names; the rest never reached +20% in 1y)\n")

# cross-regime: TP20 vs hold delta in mean, per cohort×type
print("=== TP+20% minus B&H (MEAN return delta) — negative = take-profit HURTS ===")
for (coh, typ), g in t.groupby(["cohort", "type"]):
    if len(g) < 30:
        continue
    d_mean = 100 * (g["tp20"].mean() - g["hold"].mean())
    d_med = 100 * (g["tp20"].median() - g["hold"].median())
    print(f"  {coh:>9}/{typ:<3} n={len(g):4d}  Δmean {d_mean:+6.1f}pp  Δmedian {d_med:+5.1f}pp")
