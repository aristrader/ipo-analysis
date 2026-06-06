"""F1 — anchor-unlock supply waves: L1 event study (day-30/90 + pre-2022 placebo),
L2 dose-response, L3 buy-the-dip grid. Alpha = stock daily return minus Nifty."""
import sys, os, csv, bisect, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config

df = spine.load_substrate()
m = (df["type"] == "MB") & pd.to_numeric(df["anchor_allocation_cr"], errors="coerce").gt(0)
mb = df[m].copy()
mb["anchor_share"] = pd.to_numeric(mb["anchor_allocation_cr"], errors="coerce") / pd.to_numeric(mb["issue_size_cr"], errors="coerce")
mb["ld"] = pd.to_datetime(mb["listing_date"], errors="coerce")
mb = mb[mb["ld"].notna() & mb["anchor_share"].notna()]
post = mb[mb["open_date"] >= "2022-04-01"]
pre = mb[(mb["open_date"] < "2022-04-01") & (mb["open_date"] >= "2015-01-01")]
print(f"cohorts: post-2022 (30/90 rule) n={len(post)}, pre-2022 placebo n={len(pre)}")

# nifty closes
nd, nc = [], []
for r in csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try: nd.append(pd.Timestamp(r["date"])); nc.append(float(r["close"]))
    except ValueError: continue
pairs = sorted(zip(nd, nc)); nd = [p[0] for p in pairs]; nc = [p[1] for p in pairs]
def nifty_at(t):
    i = bisect.bisect_right(nd, t) - 1
    return nc[i] if i >= 0 else None

def daily_alpha_series(isin, ld):
    p = f"data/prices/{isin}.csv"
    if not os.path.exists(p): return None
    rows = []
    for r in csv.DictReader(open(p)):
        try: rows.append((pd.Timestamp(r["date"]), float(r["close"])))
        except ValueError: continue
    rows = [x for x in rows if x[0] >= ld]
    if len(rows) < 100: return None
    out = []
    for i in range(1, len(rows)):
        n0, n1 = nifty_at(rows[i-1][0]), nifty_at(rows[i][0])
        if not n0 or not n1: continue
        out.append((i, (rows[i][1]/rows[i-1][1]-1) - (n1/n0-1)))   # t (trading day from listing), daily alpha
    return out

def window_car(series, lo, hi):
    vals = [a for t, a in series if lo <= t <= hi]
    return sum(vals) if len(vals) >= (hi-lo)//2 else None

def event_study(cohort, label):
    cars30, cars90, base, shares, run85 = [], [], [], [], []
    for _, r in cohort.iterrows():
        s = daily_alpha_series(r["isin"], r["ld"])
        if not s: continue
        c30 = window_car(s, 27, 36); c90 = window_car(s, 87, 96); b = window_car(s, 45, 80)
        if c90 is None: continue
        cars30.append(c30); cars90.append(c90); base.append(b)
        shares.append(r["anchor_share"]); run85.append(sum(a for t, a in s if t <= 85))
    c90 = pd.Series(cars90); c30 = pd.Series([x for x in cars30 if x is not None])
    b = pd.Series([x for x in base if x is not None])
    print(f"\n{label}: n={len(c90)}")
    print(f"  W30 median CAR: {100*c30.median():+.2f}%   W90 median CAR: {100*c90.median():+.2f}%   "
          f"baseline(d45-80, ~3.6x longer): {100*b.median():+.2f}%")
    print(f"  P(W90 negative): {100*(c90<0).mean():.0f}%")
    sh = pd.Series(shares); ru = pd.Series(run85)
    ic = sh.rank().corr(c90.rank())
    print(f"  dose-response Spearman(anchor_share, W90 CAR): {ic:+.3f} (expect negative)")
    # runup interaction
    hi_run = c90[ru > ru.median()]; lo_run = c90[ru <= ru.median()]
    print(f"  W90 CAR | high run-up: {100*hi_run.median():+.2f}%  | low run-up: {100*lo_run.median():+.2f}%")
    return c90, sh

c90_post, sh_post = event_study(post, "POST-2022 (treatment: 50% unlocks at day 90)")
c90_pre, _ = event_study(pre, "PRE-2022 (placebo: no day-90 tranche existed)")

# L3 playbook: E2 = buy at d93 if W90 alpha <= -3%, hold +1m (d93->d114)
print("\nL3 — buy-the-dip E2 (post-2022): buy d93 if W90 CAR <= -3%, hold ~1m:")
pay = []
for _, r in post.iterrows():
    s = daily_alpha_series(r["isin"], r["ld"])
    if not s: continue
    c90 = window_car(s, 87, 96)
    if c90 is None or c90 > -0.03: continue
    fwd = window_car(s, 97, 118)
    if fwd is not None: pay.append(fwd)
pay = pd.Series(pay)
if len(pay) >= 10:
    print(f"  n={len(pay)} win_rate={100*(pay>0).mean():.0f}% median={100*pay.median():+.1f}% "
          f"P10={100*pay.quantile(.1):+.1f}% P90={100*pay.quantile(.9):+.1f}%")
else:
    print(f"  n={len(pay)} — thin")
