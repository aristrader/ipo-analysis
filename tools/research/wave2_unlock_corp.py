"""Wave-2 part 2 — T2a (day-180 pre-IPO-holder unlock; post-Aug-2021 6m vs pre 1y regime,
crossed-window design = built-in placebo) + F10 (early corp-action tells: bonus/split within
year 1 of listing -> forward alpha, run-up controlled). Reuses the F1 daily-alpha harness."""
import sys, os, csv, bisect, warnings
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
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
df = df[df["ld"].notna()]

nd, nc = [], []
for r in csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try: nd.append(pd.Timestamp(r["date"])); nc.append(float(r["close"]))
    except ValueError: continue
pairs = sorted(zip(nd, nc)); nd = [p[0] for p in pairs]; nc = [p[1] for p in pairs]
def nifty_at(t):
    i = bisect.bisect_right(nd, t) - 1
    return nc[i] if i >= 0 else None

def daily_alpha_series(isin, ld, min_len=100):
    p = f"data/prices/{isin}.csv"
    if not os.path.exists(p): return None
    rows = []
    for r in csv.DictReader(open(p)):
        try: rows.append((pd.Timestamp(r["date"]), float(r["close"])))
        except ValueError: continue
    rows = [x for x in rows if x[0] >= ld]
    if len(rows) < min_len: return None
    out = []
    for i in range(1, len(rows)):
        n0, n1 = nifty_at(rows[i-1][0]), nifty_at(rows[i][0])
        if not n0 or not n1: continue
        out.append((i, (rows[i][1]/rows[i-1][1]-1) - (n1/n0-1)))
    return out

def window_car(series, lo, hi):
    vals = [a for t, a in series if lo <= t <= hi]
    return sum(vals) if len(vals) >= (hi - lo) // 2 else None

# ===================== T2a — pre-IPO-holder unlock =====================
# 6m lock (post-Aug-2021 listings) -> event ~ calendar day 180 ~ trading day 124;
# 1y lock (pre-Aug-2021)           -> event ~ trading day 248.
# Crossed design: each cohort is the other's placebo at the other window.
print("=" * 70); print("T2a — pre-IPO-holder unlock (W180=[td120,131], W365=[td244,255], base=[td150,230])")
mb = df[df["type"] == "MB"]
post = mb[mb["ld"] >= "2021-09-01"]
pre = mb[(mb["ld"] < "2021-07-01") & (mb["ld"] >= "2010-01-01")]
for lab, cohort, need in (("POST-Aug-2021 (6m lock -> td~124 event)", post, 270),
                          ("PRE-Aug-2021 (1y lock -> td~248 event)", pre, 270)):
    w180, w365, base = [], [], []
    for _, r in cohort.iterrows():
        s = daily_alpha_series(r["isin"], r["ld"], min_len=need)
        if not s: continue
        c180 = window_car(s, 120, 131); c365 = window_car(s, 244, 255); b = window_car(s, 150, 230)
        if c180 is None or c365 is None: continue
        w180.append(c180); w365.append(c365); base.append(b)
    w180, w365 = pd.Series(w180), pd.Series(w365)
    base = pd.Series([x for x in base if x is not None])
    # baseline is ~80td -> scale to a 12-td-equivalent for comparability
    bl12 = base.median() * 12 / 80 if len(base) else float("nan")
    print(f"  {lab}: n={len(w180)}")
    print(f"    W180 median CAR {100*w180.median():+.2f}% (P(neg) {100*(w180<0).mean():.0f}%)   "
          f"W365 median CAR {100*w365.median():+.2f}% (P(neg) {100*(w365<0).mean():.0f}%)   baseline-12td-equiv {100*bl12:+.2f}%")

# ===================== F10 — early corp-action tells =====================
print("=" * 70); print("F10 — bonus/split announced early (ex_date within 365d of listing)")
ca = pd.read_csv("data/reference/corp_actions.csv")
ca["ex_date"] = pd.to_datetime(ca["ex_date"], errors="coerce")
ca = ca[ca["action_type"].isin(("bonus", "split")) & ca["ex_date"].notna()]
sym_map = {}
if "nse_symbol" in df.columns:
    for _, r in df.iterrows():
        s = r.get("nse_symbol")
        if isinstance(s, str) and s.strip(): sym_map.setdefault(s.strip().upper(), r["isin"])
isin_set = set(df["isin"])
events = []
for _, a in ca.iterrows():
    isin = a["isin"] if a["isin"] in isin_set else sym_map.get(str(a["symbol"]).strip().upper())
    if not isin: continue
    row = df[df["isin"] == isin].iloc[0]
    dd = (a["ex_date"] - row["ld"]).days
    if 30 <= dd <= 365:
        events.append({"isin": isin, "days": dd, "kind": a["action_type"],
                       "type": row["type"], "cohort": row["cohort"], "ex": a["ex_date"]})
ev = pd.DataFrame(events).drop_duplicates("isin")
print(f"  early-action IPOs matched: n={len(ev)} ({dict(ev['kind'].value_counts()) if len(ev) else {}})")

# forward 3m alpha FROM the ex_date (tradeable) + run-up control via all-IPO pseudo-events
rows = []
for _, e in ev.iterrows():
    ld = df.loc[df["isin"] == e["isin"], "ld"].iloc[0]
    s = daily_alpha_series(e["isin"], ld, min_len=60)
    if not s: continue
    # trading-day index of ex_date ~ calendar days * 0.69
    tdx = int(e["days"] * 0.69)
    runup = sum(a for t, a in s if t <= tdx)
    fwd = window_car(s, tdx + 1, tdx + 63)
    if fwd is None: continue
    rows.append({"runup": runup, "fwd3m": fwd, "type": e["type"], "tdx": tdx, "isin": e["isin"]})
er = pd.DataFrame(rows)
print(f"  with usable price paths: n={len(er)}")
if len(er) >= 12:
    print(f"  median run-up to ex-date {100*er['runup'].median():+.1f}%  median fwd-3m alpha after ex {100*er['fwd3m'].median():+.1f}%"
          f"  win {100*(er['fwd3m']>0).mean():.0f}%")
    for t in ("MB", "SME"):
        g = er[er["type"] == t]
        if len(g) >= 12:
            print(f"    {t}: n={len(g)} fwd-3m {100*g['fwd3m'].median():+.1f}% win {100*(g['fwd3m']>0).mean():.0f}%")
    # CONTROL: matched pseudo-events — same trading-day offset, similar run-up, no corp action
    pool = df[~df["isin"].isin(set(ev["isin"]))]
    ctrl = []
    rng_idx = 0
    for _, e in er.iterrows():
        # sample up to 3 controls per event from same type, runup within +/-25pp
        cands = pool[pool["type"] == e["type"]]
        got = 0
        for _, c in cands.iloc[rng_idx % 7::7].iterrows():     # deterministic stagger, no RNG
            s = daily_alpha_series(c["isin"], c["ld"], min_len=60)
            if not s: continue
            ru = sum(a for t, a in s if t <= e["tdx"])
            if abs(ru - e["runup"]) > 0.25: continue
            f = window_car(s, e["tdx"] + 1, e["tdx"] + 63)
            if f is None: continue
            ctrl.append(f); got += 1
            if got >= 2: break
        rng_idx += 1
    ctrl = pd.Series(ctrl)
    if len(ctrl) >= 30:
        print(f"  CONTROL (matched type+run-up pseudo-events): n={len(ctrl)} fwd-3m {100*ctrl.median():+.1f}% win {100*(ctrl>0).mean():.0f}%")
    print(f"  dose: srho(days-to-action, fwd3m) = {srho(er['days'] if 'days' in er else er['tdx'], er['fwd3m']):+.3f}")
    # long-horizon view from substrate
    sub = df.merge(ev[["isin"]], on="isin")
    a1y = pd.to_numeric(sub["alpha_1y"], errors="coerce"); a3y = pd.to_numeric(sub["alpha_3y"], errors="coerce")
    base1 = pd.to_numeric(df["alpha_1y"], errors="coerce"); base3 = pd.to_numeric(df["alpha_3y"], errors="coerce")
    print(f"  endpoint: early-action alpha_1y {100*a1y.median():+.1f}% (all-IPO {100*base1.median():+.1f}%) | "
          f"alpha_3y {100*a3y.median():+.1f}% (all {100*base3.median():+.1f}%)")
