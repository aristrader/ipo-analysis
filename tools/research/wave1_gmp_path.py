"""Wave-1 Groups C+B-core: F6a-d (GMP second-order) + F5b (LDH trapped-supply breakout)."""
import sys, os, csv, warnings, bisect
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine

def srho(a, b):
    a, b = pd.Series(a), pd.Series(b)
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["gmp_imp"] = N("gmp_pct") / 100.0
df["pop"] = N("adj_listing_gain_open"); df["a1w"] = N("alpha_1w"); df["a1m"] = N("alpha_1m")
df["surprise"] = df["pop"] - df["gmp_imp"]
df["retail_share"] = N("sub_retail_x") / (N("sub_retail_x") + N("sub_qib_x") + N("sub_nii_x"))
ld = pd.to_datetime(df["listing_date"], errors="coerce")

print("=" * 70); print("F6a — GMP-surprise residual -> drift")
m = df["surprise"].notna() & df["a1m"].notna()
# control raw pop: residualize a1m on pop, then IC vs surprise
sub = df[m]
beta = np.polyfit(sub["pop"], sub["a1m"], 1)
res = sub["a1m"] - np.polyval(beta, sub["pop"])
print(f"  n={len(sub)}  IC(surprise, alpha_1m)={srho(sub['surprise'], sub['a1m']):+.3f}  "
      f"| pop-controlled: {srho(sub['surprise'], res):+.3f}")
q = pd.qcut(sub["surprise"], 5, labels=False, duplicates="drop")
for qq in (0, 4):
    g = sub[q == qq]
    print(f"  surprise Q{qq+1}: n={len(g)} median alpha_1w {100*g['a1w'].median():+.1f}%  alpha_1m {100*g['a1m'].median():+.1f}%")

print("=" * 70); print("F6b — GMP x retail-share interaction on pop")
m = df["gmp_imp"].notna() & df["retail_share"].notna() & df["pop"].notna()
sub = df[m]
hi_r = sub[sub["retail_share"] > sub["retail_share"].median()]
lo_r = sub[sub["retail_share"] <= sub["retail_share"].median()]
print(f"  GMP->pop IC | high retail-share: {srho(hi_r['gmp_imp'], hi_r['pop']):+.3f} (n={len(hi_r)})  "
      f"| low(QIB-led): {srho(lo_r['gmp_imp'], lo_r['pop']):+.3f} (n={len(lo_r)})")

print("=" * 70); print("F6c — GMP meaning by regime (hot vs cold IPO climate)")
d = df.dropna(subset=["gmp_imp"]).copy()
d["ld"] = ld[d.index]
d = d.sort_values("ld")
dates = d["ld"].tolist(); pops = d["pop"].tolist()
climate = []
for i, t in enumerate(dates):
    lo = bisect.bisect_left(dates, t - pd.Timedelta(days=60)); hi = bisect.bisect_left(dates, t)
    w = [pops[j] for j in range(lo, hi) if not pd.isna(pops[j])]
    climate.append(np.median(w) if len(w) >= 5 else np.nan)
d["climate"] = climate
hot = d[d["climate"] > np.nanquantile(climate, 0.67)]; cold = d[d["climate"] < np.nanquantile(climate, 0.33)]
print(f"  GMP->alpha_1m IC | HOT climate: {srho(hot['gmp_imp'], hot['a1m']):+.3f} (n={int(hot['a1m'].notna().sum())})  "
      f"| COLD: {srho(cold['gmp_imp'], cold['a1m']):+.3f} (n={int(cold['a1m'].notna().sum())})  (sign flip?)")

print("=" * 70); print("F6d — T+3 natural experiment (GMP->pop transmission)")
pre = df[(ld <= "2023-08-31") & (ld >= "2021-01-01") & df["gmp_imp"].notna() & df["pop"].notna()]
post = df[(ld >= "2023-12-01") & df["gmp_imp"].notna() & df["pop"].notna()]
for lab, g in (("clean-pre T+6 (2021-2023.08)", pre), ("clean-post T+3 (>=2023.12)", post)):
    ic = srho(g["gmp_imp"], g["pop"])
    err = (g["pop"] - g["gmp_imp"]).abs().median()
    print(f"  {lab}: n={len(g)} GMP->pop IC={ic:+.3f}  median |forecast error|={100*err:.1f}pp")

print("=" * 70); print("F5b — listing-day-high trapped-supply ceiling (price-path scan)")
rows = []
take = df[ld.notna()].copy()
for _, r in take.iterrows():
    p = f"data/prices/{r['isin']}.csv"
    if not os.path.exists(p): continue
    try:
        pr = pd.read_csv(p)
    except Exception: continue
    if len(pr) < 80: continue
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[pr["date"] >= ld[r.name]].reset_index(drop=True)
    if len(pr) < 80: continue
    ldh = float(pr.iloc[0]["high"]) if not pd.isna(pr.iloc[0]["high"]) else None
    if not ldh: continue
    closes = pr["close"].astype(float).values
    highs = pr["high"].astype(float).values
    # search day 2..60 for touch / confirmed breakout
    touch_day = conf_day = None
    for t in range(2, min(61, len(pr) - 25)):
        if highs[t] >= 0.99 * ldh and touch_day is None:
            touch_day = t
        if closes[t] > 1.02 * ldh and all(closes[t+k] > ldh for k in (1, 2, 3)):
            conf_day = t; break
    if touch_day is None: continue
    ev = conf_day if conf_day is not None else touch_day
    fwd_end = ev + 20
    if fwd_end >= len(pr): continue
    fwd = closes[fwd_end] / closes[ev] - 1
    rows.append({"kind": "confirm" if conf_day is not None else "fail", "fwd20": fwd, "type": r["type"]})
ev = pd.DataFrame(rows)
print(f"  events n={len(ev)} (confirm {int((ev['kind']=='confirm').sum())} / touch-fail {int((ev['kind']=='fail').sum())})")
for k in ("confirm", "fail"):
    g = ev[ev["kind"] == k]
    if len(g) >= 30:
        print(f"  {k:8s}: median fwd-20d {100*g['fwd20'].median():+.1f}%  win {100*(g['fwd20']>0).mean():.0f}%  "
              f"P10 {100*g['fwd20'].quantile(.1):+.1f}%")
