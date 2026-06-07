"""Wave-2 part 2 — price-path scan: F5a (issue magnet), F5c (volume-confirmed crossings),
F5d (double-reference ordering), F5e (capitulation flag, incremental vs N14), F5f (round-number
tiers), T2i (day-1 flipping proxy). One pass over data/prices/<isin>.csv, listing-anchored.
Conventions: adjusted issue price (issue_price_adj), exclude unreliable_coverage, min-N 30,
fwd returns Nifty-adjusted. Placebo level for F5a = 0.90x issue (same approach structure, no
breakeven anchor)."""
import sys, os, csv, bisect, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine
from layer3.predictor import scorecard as SC

def srho(a, b):
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
df = df[df["ld"].notna()]
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["ipx"] = N("issue_price_adj")
df["ipx_raw"] = N("issue_price")

# nifty
nd, nc = [], []
for r in csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try: nd.append(pd.Timestamp(r["date"])); nc.append(float(r["close"]))
    except ValueError: continue
pairs = sorted(zip(nd, nc)); nd = [p[0] for p in pairs]; nc = [p[1] for p in pairs]
def nifty_at(t):
    i = bisect.bisect_right(nd, t) - 1
    return nc[i] if i >= 0 else None

def round_tier(p):
    if pd.isna(p): return None
    p = float(p)
    if p % 50 == 0: return "A"        # x100 / x50
    if p % 10 == 0: return "B"
    return "C"

def approach_episodes(closes, level, dates):
    """F5a episodes vs a level: close enters [0.97,1.00)*level having closed <0.95*level in prior
    10d. Outcome over next 10d: clear (>1.02), reject (<0.97), stall (neither). Returns dicts."""
    eps, t = [], 12
    while t < len(closes) - 12:
        c = closes[t]
        if 0.97 * level <= c < 1.00 * level and min(closes[max(0, t-10):t]) < 0.95 * level:
            depth = min(closes[max(0, t-10):t]) / level - 1
            out = "stall"; res_day = None
            for k in range(1, 11):
                if closes[t+k] > 1.02 * level: out = "clear"; res_day = k; break
                if closes[t+k] < 0.97 * level: out = "reject"; res_day = k; break
            f_end = min(t + 10, len(closes) - 1)
            n0, n1 = nifty_at(dates[t]), nifty_at(dates[f_end])
            fwd = (closes[f_end]/closes[t]-1) - ((n1/n0-1) if n0 and n1 else 0.0)
            eps.append({"t": t, "out": out, "depth": depth, "fwd10": fwd, "res_day": res_day})
            t += 11           # don't double-count the same approach
        else:
            t += 1
    return eps

F5A, F5A_PLC, F5C, F5D, F5E, T2I = [], [], [], [], [], []
n_files = 0
for _, r in df.iterrows():
    p = f"data/prices/{r['isin']}.csv"
    if not os.path.exists(p) or pd.isna(r["ipx"]) or r["ipx"] <= 0: continue
    try: pr = pd.read_csv(p)
    except Exception: continue
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[pr["date"] >= r["ld"]].reset_index(drop=True)
    if len(pr) < 70: continue
    n_files += 1
    closes = pr["close"].astype(float).values
    highs = pr["high"].astype(float).values
    vols = pr["volume"].astype(float).values
    dates = pr["date"].tolist()
    ipx = float(r["ipx"]); ldh = float(highs[0]) if not pd.isna(highs[0]) else None
    tier = round_tier(r["ipx_raw"])

    # ---- F5a + F5f: approach episodes vs issue level (and 0.90x placebo level)
    for e in approach_episodes(closes, ipx, dates):
        e.update(type=r["type"], tier=tier); F5A.append(e)
    for e in approach_episodes(closes, 0.90 * ipx, dates):
        F5A_PLC.append(e)

    # ---- F5c: volume-confirmed upward crossings of the issue level (first crossing only)
    below = closes[1:31] < ipx
    if below.any():
        start = 1 + int(np.argmax(below))           # first day below issue
        for t in range(start + 1, min(len(closes) - 11, 130)):
            if closes[t] > ipx and closes[t-1] <= ipx:
                v20 = np.nanmedian(vols[max(0, t-20):t])
                if not v20 or pd.isna(v20): break
                conf = vols[t] >= 1.5 * v20
                hold5 = all(closes[t+k] > ipx for k in range(1, 6))
                n0, n1 = nifty_at(dates[t]), nifty_at(dates[t+10])
                fwd = (closes[t+10]/closes[t]-1) - ((n1/n0-1) if n0 and n1 else 0.0)
                F5C.append({"conf": conf, "hold5": hold5, "fwd10": fwd, "type": r["type"]})
                break

    # ---- F5d: double-reference ordering (dipped below 0.97x issue in d1-30; LDH live above)
    if ldh and ldh > ipx and (closes[1:31] < 0.97 * ipx).any() and len(closes) > 120:
        reclaim_day = next((t for t in range(1, 61) if closes[t] > 1.02 * ipx), None)
        ldh_day = next((t for t in range(1, 121) if closes[t] > ldh), None)
        F5D.append({"reclaimed60": reclaim_day is not None,
                    "cleared_ldh120": ldh_day is not None, "type": r["type"]})

    # ---- F5e: capitulation flag = never closed above issue in d1-90
    if len(closes) > 95:
        F5E.append({"isin": r["isin"], "capit": bool(max(closes[1:91]) < ipx), "type": r["type"]})

    # ---- T2i: day-1 flipping proxy (MB only; shares_offered from issue size / raw price)
    iss = pd.to_numeric(r.get("issue_size_cr"), errors="coerce")
    if r["type"] == "MB" and pd.notna(iss) and iss > 0 and pd.notna(r["ipx_raw"]) and r["ipx_raw"] > 0:
        sh_off = iss * 1e7 / float(r["ipx_raw"])
        flip = vols[0] / sh_off if sh_off > 0 else np.nan
        plc20 = vols[20] / sh_off if len(vols) > 20 else np.nan     # placebo: day-20 turnover
        rev15 = closes[5]/closes[0] - 1 if len(closes) > 5 else np.nan
        T2I.append({"isin": r["isin"], "flip": flip, "plc20": plc20, "rev15": rev15,
                    "pop": pd.to_numeric(r.get("adj_listing_gain_open"), errors="coerce"),
                    "a6m": pd.to_numeric(r.get("alpha_6m"), errors="coerce"),
                    "a1y": pd.to_numeric(r.get("alpha_1y"), errors="coerce")})

print(f"scanned {n_files} price files")

# ============================== F5a ==============================
ea, ep = pd.DataFrame(F5A), pd.DataFrame(F5A_PLC)
print("=" * 70); print(f"F5a — issue-price magnet: {len(ea)} episodes (placebo level 0.90x: {len(ep)})")
for lab, e in (("ISSUE level", ea), ("PLACEBO 0.90x", ep)):
    if len(e) < 30: print(f"  {lab}: thin ({len(e)})"); continue
    cl, rj = (e["out"] == "clear").mean(), (e["out"] == "reject").mean()
    print(f"  {lab}: clear {100*cl:.0f}% / reject {100*rj:.0f}% / stall {100*(e['out']=='stall').mean():.0f}%"
          f"  median fwd10 alpha {100*e['fwd10'].median():+.1f}%")
print("  by approach depth (issue level):")
ea["dbin"] = pd.cut(ea["depth"], [-1, -0.20, -0.10, -0.049], labels=["deep<-20", "-10..-20", "-5..-10"])
for b, g in ea.groupby("dbin"):
    if len(g) >= 12:
        print(f"    {b:>9}: n={len(g)} clear {100*(g['out']=='clear').mean():.0f}% "
              f"reject {100*(g['out']=='reject').mean():.0f}% fwd10 {100*g['fwd10'].median():+.1f}%")
print("  L3 grid — buy-on-touch (all episodes) vs buy-on-confirmed-clear:")
tch = ea
clr = ea[ea["out"] == "clear"]
print(f"    touch-buy : n={len(tch)} median fwd10 {100*tch['fwd10'].median():+.1f}% win {100*(tch['fwd10']>0).mean():.0f}%")
print(f"    clear-only: n={len(clr)} (post-clear drift folded into fwd10 from episode start — see F5c for clean entry)")

# ============================== F5f ==============================
print("=" * 70); print("F5f — round-number tiers (issue-level episodes)")
for t in ("A", "B", "C"):
    g = ea[ea["tier"] == t]
    if len(g) >= 12:
        print(f"  tier {t}: n={len(g)} stall {100*(g['out']=='stall').mean():.0f}% clear {100*(g['out']=='clear').mean():.0f}%"
              f" reject {100*(g['out']=='reject').mean():.0f}% fwd10 {100*g['fwd10'].median():+.1f}%")

# ============================== F5c ==============================
ec = pd.DataFrame(F5C)
print("=" * 70); print(f"F5c — volume-confirmed issue-reclaim crossings: n={len(ec)}")
for lab, g in (("confirmed >=1.5x vol", ec[ec["conf"]]), ("naked", ec[~ec["conf"]])):
    if len(g) >= 30:
        print(f"  {lab:20s}: n={len(g)} hold5 {100*g['hold5'].mean():.0f}% median fwd10 alpha {100*g['fwd10'].median():+.1f}%"
              f" win {100*(g['fwd10']>0).mean():.0f}%")

# ============================== F5d ==============================
ed = pd.DataFrame(F5D)
print("=" * 70); print(f"F5d — double-reference ordering: n={len(ed)} (dipped <0.97x issue, LDH above issue)")
for lab, g in (("reclaimed issue by d60", ed[ed["reclaimed60"]]), ("never reclaimed by d60", ed[~ed["reclaimed60"]])):
    if len(g) >= 30:
        print(f"  {lab:24s}: n={len(g)} P(clear LDH by d120) = {100*g['cleared_ldh120'].mean():.0f}%")

# ============================== F5e ==============================
ee = pd.DataFrame(F5E).merge(df, on="isin", how="left", suffixes=("", "_d"))
print("=" * 70); print(f"F5e — capitulation flag (never closed above issue d1-90): n={len(ee)} flag-rate {100*ee['capit'].mean():.0f}%")
bad = SC._bad_outcome_mask(ee)
fl = ee["capit"]
print(f"  P(bad outcome | capit) = {100*bad[fl].mean():.0f}% (n={int(fl.sum())})  vs no-capit {100*bad[~fl].mean():.0f}% (n={int((~fl).sum())})")
qf = SC._query_flag_series(ee, df)
nflags = sum((s.fillna(False)).astype(int) for s in qf.values() if s is not None)
print("  INCREMENTAL vs N14 flag-count:")
for k in (0, 1, 2):
    m = nflags == k if k < 2 else nflags >= 2
    klab = str(k) if k < 2 else "2+"
    a, b = bad[m & fl], bad[m & ~fl]
    if len(a) >= 12 and len(b) >= 12:
        print(f"    N14 flags={klab}: bad-rate capit {100*a.mean():.0f}% (n={len(a)}) vs no-capit {100*b.mean():.0f}% (n={len(b)})"
              f"  lift {100*(a.mean()-b.mean()):+.0f}pp")

# ============================== T2i ==============================
ti = pd.DataFrame(T2I).dropna(subset=["flip"])
print("=" * 70); print(f"T2i — day-1 flipping proxy (MB): n={len(ti)}")
for h in ("a6m", "a1y"):
    m = ti[h].notna() & ti["pop"].notna()
    sub = ti[m]
    if len(sub) < 50: continue
    beta = np.polyfit(sub["pop"], sub[h], 1)
    res = sub[h] - np.polyval(beta, sub["pop"])
    print(f"  IC(flip, {h}) = {srho(sub['flip'], sub[h]):+.3f}  pop-controlled {srho(sub['flip'], res):+.3f}"
          f"  | PLACEBO day-20 turnover: {srho(sub['plc20'], res):+.3f}")
q = pd.qcut(ti["flip"], 5, labels=False, duplicates="drop")
for qq in (0, 4):
    g = ti[q == qq]
    print(f"  flip Q{qq+1}: n={len(g)} median alpha_6m {100*g['a6m'].median():+.1f}%  alpha_1y {100*g['a1y'].median():+.1f}%")
hi = ti[(q == 4) & (ti["rev15"] < 0)]
print(f"  high-flip + reversed-by-d5: n={len(hi)} median alpha_1y {100*hi['a1y'].median():+.1f}%")
