"""Wave-1 Group A: F2a-f (wallet clusters), F7 (contagion), F8 (unfilled demand).
Compact verdict output per spec (docs/research/phase2_playbooks.md)."""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd

def srho(a, b):
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")
from layer3 import spine, config

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
for c in ("open_date", "close_date", "listing_date"):
    df[c] = pd.to_datetime(df[c], errors="coerce")
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["gmp"] = N("gmp_pct"); df["sub"] = N("sub_total_x"); df["size"] = N("issue_size_cr")
df["pop"] = N("adj_listing_gain_open"); df["a1w"] = N("alpha_1w"); df["a1m"] = N("alpha_1m"); df["a3m"] = N("alpha_3m")
df["retail"] = N("sub_retail_x"); df["qib"] = N("sub_qib_x")

def build_clusters(frame, W):
    """Connected components: same type, open-dates within W days AND [open,close] overlap."""
    cl = {}
    for t, g in frame.dropna(subset=["open_date", "close_date"]).groupby("type"):
        g = g.sort_values("open_date")
        cid, last_close, last_open = None, None, None
        for idx, r in g.iterrows():
            if cid is not None and (r["open_date"] - last_open).days <= W and r["open_date"] <= last_close:
                cl[idx] = cid
                last_close = max(last_close, r["close_date"]); last_open = r["open_date"]
            else:
                cid = idx; cl[idx] = cid
                last_close, last_open = r["close_date"], r["open_date"]
    return pd.Series(cl)

print("=" * 70); print("F2a — within-cluster GMP rank -> forward alpha (the owner's pattern)")
for W in (3, 5, 7):
    d = df.copy(); d["cl"] = build_clusters(d, W)
    d = d[d["cl"].notna()]
    sizes = d.groupby("cl")["isin"].transform("count")
    c = d[(sizes >= 2) & d["gmp"].notna()]
    c = c[c.groupby("cl")["gmp"].transform("count") >= 2]
    c["rank_n"] = c.groupby("cl")["gmp"].rank(ascending=False, pct=True)  # 0=top(hot) 1=bottom(neglected)
    # demean within cluster (cluster FE equivalent for IC)
    for out, lab in (("pop", "pop"), ("a1m", "a1m")):
        v = c[out] - c.groupby("cl")[out].transform("mean")
        ic = srho(c["rank_n"], v.rank() if False else v)
        if out == "pop": ic_pop = ic
        else: ic_a1m = ic
    n = len(c)
    print(f"  W={W}: n={n}  IC(neglect_rank, pop)={ic_pop:+.3f} (expect −: hot pops more)  "
          f"IC(neglect_rank, fwd alpha_1m | cluster)={ic_a1m:+.3f} (hypothesis: +)")

print("=" * 70); print("F2b — first-lister tone-setting (spill to later members' pops)")
d = df.copy(); d["cl"] = build_clusters(d, 5)
spills = []
for cid, g in d[d["cl"].notna()].groupby("cl"):
    if len(g) < 2: continue
    g = g.sort_values("listing_date")
    first = g.iloc[0]
    if pd.isna(first["pop"]): continue
    for _, later in g.iloc[1:].iterrows():
        if pd.isna(later["pop"]) or pd.isna(later["listing_date"]) or pd.isna(first["listing_date"]): continue
        if (later["listing_date"] - first["listing_date"]).days > 7 or later["listing_date"] == first["listing_date"]: continue
        spills.append((first["pop"], later["pop"], later["gmp"]))
sp = pd.DataFrame(spills, columns=["first_pop", "later_pop", "later_gmp"]).dropna(subset=["first_pop", "later_pop"])
if len(sp) >= 30:
    raw = srho(sp["first_pop"], sp["later_pop"])
    g_ok = sp.dropna()
    resid = g_ok["later_pop"] - g_ok["later_gmp"] / 100 * 0  # control via partial spearman approx
    # partial: residualize later_pop on later_gmp
    if len(g_ok) >= 30:
        beta = np.polyfit(g_ok["later_gmp"], g_ok["later_pop"], 1)
        res = g_ok["later_pop"] - np.polyval(beta, g_ok["later_gmp"])
        partial = srho(g_ok["first_pop"], res)
    else:
        partial = float("nan")
    print(f"  n={len(sp)}  raw spill IC={raw:+.3f}  | after controlling later's own GMP: {partial:+.3f} (hypothesis: +)")
else:
    print(f"  n={len(sp)} THIN")

print("=" * 70); print("F2c — ordinal fatigue in streaks (G=3 td)")
for typ in ("MB", "SME"):
    g = df[(df["type"] == typ)].dropna(subset=["open_date"]).sort_values("open_date").copy()
    gaps = g["open_date"].diff().dt.days
    g["streak"] = (gaps > 5).cumsum()
    g["ordinal"] = g.groupby("streak").cumcount() + 1
    m = g["ordinal"].notna() & g["pop"].notna()
    ic_pop = srho(g.loc[m, "ordinal"], g.loc[m, "pop"])
    mr = g["retail"].notna()
    ic_ret = srho(g.loc[mr, "ordinal"], g.loc[mr, "retail"])
    mq = g["qib"].notna()
    ic_qib = srho(g.loc[mq, "ordinal"], g.loc[mq, "qib"])
    print(f"  {typ}: IC(ordinal, pop)={ic_pop:+.3f}  IC(ordinal, retail_sub)={ic_ret:+.3f}  "
          f"IC(ordinal, qib_sub)={ic_qib:+.3f}  (fatigue: all −, retail<qib)")

print("=" * 70); print("F2d — retail congestion tax")
d = df.dropna(subset=["open_date", "close_date"]).copy()
loads = []
arr = d[["open_date", "close_date", "size"]].values
for i, r in enumerate(d.itertuples()):
    o, c0 = r.open_date, r.close_date
    overl = d[(d["open_date"] <= c0) & (d["close_date"] >= o)]
    loads.append(overl["size"].sum() - (r.size_ if hasattr(r, 'size_') else 0))
d["congestion"] = [l for l in loads]
for cat, lab in (("retail", "retail_sub"), ("qib", "qib_sub")):
    m = d[cat].notna() & d["congestion"].notna()
    ic = srho(d.loc[m, "congestion"], np.log1p(d.loc[m, cat]))
    print(f"  IC(congestion_load, {lab}) = {ic:+.3f}  (hypothesis: retail −, qib ~0)")
hidden = d[(d["congestion"] > d["congestion"].quantile(0.67)) & d["a3m"].notna()]
hq = hidden[N("pre_ipo_net_sales").reindex(hidden.index) > 0]
print(f"  congestion-hidden fwd test deferred to quality split (n high-congestion w/ 3m: {len(hidden)})")

print("=" * 70); print("F7 — disposition contagion (trailing 60d cohort outcomes)")
d = df.dropna(subset=["listing_date"]).sort_values("listing_date").copy()
dates = d["listing_date"].tolist(); pops = d["pop"].tolist()
import bisect as bs
trail = []
for i, t in enumerate(dates):
    lo = bs.bisect_left(dates, t - pd.Timedelta(days=60)); hi = bs.bisect_left(dates, t)
    window = [pops[j] for j in range(lo, hi) if not pd.isna(pops[j])]
    trail.append(np.median(window) if len(window) >= 5 else np.nan)
d["trail"] = trail
from layer3 import regimes
d = regimes.add_regime_features(d)
m = d["trail"].notna() & d["retail"].notna()
ic_dem = srho(d.loc[m, "trail"], np.log1p(d.loc[m, "retail"]))
m2 = d["trail"].notna() & d["a3m"].notna() & d["dir60"].notna()
beta = np.polyfit(d.loc[m2, "dir60"], d.loc[m2, "a3m"], 1)
res = d.loc[m2, "a3m"] - np.polyval(beta, d.loc[m2, "dir60"])
ic_fwd = srho(d.loc[m2, "trail"], res)
print(f"  IC(trailing_pop, retail_sub)={ic_dem:+.3f} (contagion: +)   "
      f"IC(trailing_pop, fwd alpha_3m | nifty-controlled)={ic_fwd:+.3f} (tax: −)")
cold = d[m2 & (d["trail"] <= d["trail"].quantile(0.25))]; hot = d[m2 & (d["trail"] >= d["trail"].quantile(0.75))]
print(f"  L3: cold-streak listers fwd alpha_3m median {100*cold['a3m'].median():+.1f}% (n={len(cold)}) "
      f"vs hot-chase {100*hot['a3m'].median():+.1f}% (n={len(hot)})")

print("=" * 70); print("F8 — unfilled-demand kink at sub=1 (longterm+SME primarily)")
d = df[df["sub"].notna() & df["pop"].notna()].copy()
d["d1_strength"] = N("adj_listing_gain_close").reindex(d.index) - d["pop"]
under = d[d["sub"] < 1]; over = d[(d["sub"] >= 1) & (d["sub"] < 3)]
print(f"  undersubscribed n={len(under)} (boom MB: {len(under[(under['cohort']=='boom')&(under['type']=='MB')])})")
if len(under) >= 30:
    print(f"  d1_strength median: undersub {100*under['d1_strength'].median():+.1f}% vs mild-over(1-3x) {100*over['d1_strength'].median():+.1f}%")
    print(f"  fwd alpha_1m: undersub {100*under['a1m'].median():+.1f}% vs mild-over {100*over['a1m'].median():+.1f}%")
else:
    print("  THIN — recorded as untestable in current data")
