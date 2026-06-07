"""Wave-2 part 1 (substrate-only): F7-confirm, F12, F9, F4, T2b, T2c, T2e, T2g, T2h, T2j."""
import sys, os, warnings, bisect
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, regimes, config

def srho(a, b):
    a, b = pd.Series(a), pd.Series(b); m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")

df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
df = regimes.add_regime_features(df)
N = lambda c: pd.to_numeric(df[c], errors="coerce")
df["pop"]=N("adj_listing_gain_open"); df["a1m"]=N("alpha_1m"); df["a3m"]=N("alpha_3m"); df["a1y"]=N("alpha_1y")
df["size"]=N("issue_size_cr"); df["retail"]=N("sub_retail_x")
df["ld"]=pd.to_datetime(df["listing_date"],errors="coerce")
d = df.dropna(subset=["ld"]).sort_values("ld").reset_index(drop=True)
dates=d["ld"].tolist(); pops=d["pop"].tolist(); sizes=d["size"].tolist()

# trailing climates: count, median-pop, SIZE-WEIGHTED P&L (F12)
trail_med, trail_pnl, trail_cnt = [], [], []
for i,t in enumerate(dates):
    lo=bisect.bisect_left(dates,t-pd.Timedelta(days=60)); hi=bisect.bisect_left(dates,t)
    w=[(pops[j],sizes[j]) for j in range(lo,hi) if not pd.isna(pops[j])]
    trail_cnt.append(hi-lo)
    if len(w)>=5:
        ps=np.array([x[0] for x in w]); ss=np.array([x[1] if not pd.isna(x[1]) else 0 for x in w])
        trail_med.append(np.median(ps))
        trail_pnl.append(float((ps*ss).sum()/ss.sum()) if ss.sum()>0 else np.nan)
    else:
        trail_med.append(np.nan); trail_pnl.append(np.nan)
d["t_med"]=trail_med; d["t_pnl"]=trail_pnl; d["t_cnt"]=trail_cnt

print("="*70); print("F7 CONFIRMATION — cold-vs-hot tape, cross-regime cells + OOS split")
for coh in ("boom","longterm"):
    for seg in ("MB","SME"):
        g=d[(d["cohort"]==coh)&(d["type"]==seg)&d["t_med"].notna()&d["a3m"].notna()]
        if len(g)<60: print(f"  {coh}/{seg}: n={len(g)} THIN"); continue
        q1=g[g["t_med"]<=g["t_med"].quantile(.25)]; q4=g[g["t_med"]>=g["t_med"].quantile(.75)]
        print(f"  {coh}/{seg}: cold {100*q1['a3m'].median():+.1f}% (n={len(q1)}) vs hot {100*q4['a3m'].median():+.1f}% (n={len(q4)})  edge {100*(q1['a3m'].median()-q4['a3m'].median()):+.1f}pp")
# OOS: thresholds from <=2021, applied to >=2022
tr=d[d["ld"]<="2021-12-31"]; te=d[(d["ld"]>="2022-01-01")&d["t_med"].notna()&d["a3m"].notna()]
lo_thr=tr["t_med"].quantile(.25); hi_thr=tr["t_med"].quantile(.75)
cold=te[te["t_med"]<=lo_thr]; hot=te[te["t_med"]>=hi_thr]
print(f"  OOS(train<=2021 thresholds, test>=2022): cold {100*cold['a3m'].median():+.1f}% (n={len(cold)}) vs hot {100*hot['a3m'].median():+.1f}% (n={len(hot)})")

print("="*70); print("F12 — retail P&L climate (size-weighted) vs count-heat vs median-pop-heat")
m=d["a1y"].notna()
print(f"  IC vs fwd alpha_1y:  count-heat {srho(d.loc[m,'t_cnt'],d.loc[m,'a1y']):+.3f}   "
      f"median-pop {srho(d.loc[m,'t_med'],d.loc[m,'a1y']):+.3f}   SIZE-WEIGHTED P&L {srho(d.loc[m,'t_pnl'],d.loc[m,'a1y']):+.3f}")
m=d["a3m"].notna()
print(f"  IC vs fwd alpha_3m:  count-heat {srho(d.loc[m,'t_cnt'],d.loc[m,'a3m']):+.3f}   "
      f"median-pop {srho(d.loc[m,'t_med'],d.loc[m,'a3m']):+.3f}   SIZE-WEIGHTED P&L {srho(d.loc[m,'t_pnl'],d.loc[m,'a3m']):+.3f}")

print("="*70); print("F9 — sector copycat decay (ordinal within sector, trailing 365d)")
d2=d.dropna(subset=["broad_sector"]).copy()
ords=[]
sect_dates={}
for i,r in d2.iterrows():
    k=r["broad_sector"]; lst=sect_dates.setdefault(k,[])
    lo=bisect.bisect_left(lst, r["ld"]-pd.Timedelta(days=365))
    ords.append(len(lst)-lo+1)
    lst.append(r["ld"])
d2["sec_ord"]=ords
m=d2["a1y"].notna()
print(f"  IC(sector-ordinal, fwd alpha_1y) = {srho(d2.loc[m,'sec_ord'],d2.loc[m,'a1y']):+.3f}  (copycat decay: −)")
first=d2[m&(d2['sec_ord']==1)]; late=d2[m&(d2['sec_ord']>=4)]
print(f"  pioneer(ord=1) median 1y alpha {100*first['a1y'].median():+.1f}% (n={len(first)}) vs 4th+ {100*late['a1y'].median():+.1f}% (n={len(late)})")

print("="*70); print("F4 — bear-window stop-loss (labs via Nifty fwd-90d drawdown after listing)")
import csv as _csv
nd,nc=[],[]
for r in _csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try: nd.append(pd.Timestamp(r["date"])); nc.append(float(r["close"]))
    except ValueError: continue
pr=sorted(zip(nd,nc)); nd=[p[0] for p in pr]; nc=[p[1] for p in pr]
def nret(t0,days):
    i0=bisect.bisect_right(nd,t0)-1; i1=bisect.bisect_right(nd,t0+pd.Timedelta(days=days))-1
    return nc[i1]/nc[i0]-1 if i0>=60 and i1>i0 else np.nan
d["nifty_fwd90"]=[nret(t,90) for t in d["ld"]]
mae3=N("mae_lst_3m").reindex(d.index); r3=N("return_from_listing_3m").reindex(d.index)
bear=d[(d["nifty_fwd90"]<-0.10)&mae3.notna()&r3.notna()]
calm=d[(d["nifty_fwd90"]>0)&mae3.notna()&r3.notna()]
for lab,g in (("BEAR-window",bear),("calm placebo",calm)):
    mm=mae3[g.index]; rr=r3[g.index]
    for S in (0.12,0.20):
        stopped=mm<=-S
        rule=np.where(stopped,-S,rr)
        print(f"  {lab} SL{int(S*100)}%: n={len(g)} rule median {100*np.median(rule):+.1f}% vs B&H {100*rr.median():+.1f}%  (whipsaw≈{100*(stopped&(rr>0)).mean():.0f}%)")

print("="*70); print("T2b — first-week tape × regime")
# proxy first-week with alpha_1w
a1w=N("alpha_1w").reindex(d.index)
strong=a1w>a1w.quantile(.67)
for reg,lab in ((d["dir60_t"]=="hi","bull"),(d["dir60_t"]=="lo","bear")):
    g=d[strong&reg&d["a3m"].notna()]
    print(f"  strong-wk1 × {lab}: n={len(g)} fwd alpha_3m median {100*g['a3m'].median():+.1f}%")

print("="*70); print("T2c — transition fragility (bull-listed, Nifty fwd90 < −8%)")
bl=d[(d["dir60_t"]=="hi")&strong]
trans=bl[bl["nifty_fwd90"]<-0.08]; stay=bl[bl["nifty_fwd90"]>0]
a6=N("alpha_6m").reindex(d.index)
print(f"  bull-listed strong-wk1: transition fwd 6m {100*a6[trans.index].median():+.1f}% (n={len(trans)}) vs stay-bull {100*a6[stay.index].median():+.1f}% (n={len(stay)})")

print("="*70); print("T2e — recovery odds by listing PHASE (among mae_lst_3m < -20%)")
deep=d[mae3<-0.20]
r1y=N("return_from_listing_1y").reindex(d.index)
for ph in ("at_high","mid","correction"):
    g=deep[deep["phase_bin"].astype(str)==ph]
    rec=(r1y[g.index]>0)
    n=int(rec.notna().sum())
    if n>=20: print(f"  listed {ph:10s}: n={n} P(recovered>0 by 1y) {100*rec.mean():.0f}%  median 1y {100*r1y[g.index].median():+.1f}%")

print("="*70); print("T2g — same-banker collision (lead first-token canonical)")
d["lm"]=df["lead_manager"].astype(str).str.split(r"[,/&]").str[0].str.strip().str.lower().reindex(d.index)
d["od"]=pd.to_datetime(df["open_date"],errors="coerce").reindex(d.index)
coll=set()
for lm,g in d[d["lm"].notna()&(d["lm"]!="nan")&d["od"].notna()].groupby("lm"):
    g=g.sort_values("od")
    for i in range(1,len(g)):
        if (g.iloc[i]["od"]-g.iloc[i-1]["od"]).days<=10:
            coll.add(g.index[i]); coll.add(g.index[i-1])
cm=d.index.isin(coll)
g1=d[cm&d["a3m"].notna()]; g0=d[~cm&d["a3m"].notna()&d["lm"].notna()]
print(f"  collision n={len(g1)} fwd 3m {100*g1['a3m'].median():+.1f}%  vs non-collision {100*g0['a3m'].median():+.1f}% (n={len(g0)})")
# calendar placebo: any-banker windows ≤10d apart is basically everyone in boom — use congestion control instead
print(f"  (control: collision vs non within HIGH-congestion only: "
      f"{100*g1[g1['t_cnt']>g1['t_cnt'].median()]['a3m'].median():+.1f}% vs "
      f"{100*g0[g0['t_cnt']>g0['t_cnt'].median()]['a3m'].median():+.1f}%)")

print("="*70); print("T2h — ASBA refund echo (prior big listing's unblock during my open window)")
d["cd"]=pd.to_datetime(df["close_date"],errors="coerce").reindex(d.index)
echo=[]
for i,r in d.iterrows():
    if pd.isna(r["od"]) or pd.isna(r["cd"]): echo.append(np.nan); continue
    # prior IPOs listing (≈unblock T-2) inside my open window, weighted by oversub money
    lo=bisect.bisect_left(dates, r["od"]-pd.Timedelta(days=2)); hi=bisect.bisect_right(dates, r["cd"]+pd.Timedelta(days=2))
    amt=0
    for j in range(lo,hi):
        s=sizes[j]; 
        if not pd.isna(s): amt+=s
    echo.append(amt)
d["echo"]=echo
m=d["retail"].notna()&d["echo"].notna()
print(f"  IC(echo_size, retail_sub) = {srho(d.loc[m,'echo'],np.log1p(d.loc[m,'retail'])):+.3f} (hypothesis: + — freed money pumps the open book)")

print("="*70); print("T2j — SME circuit-cage: days-to-peak by |move| bucket")
d["dtm"]=N("days_to_mfe_3m").reindex(d.index)
mv=N("return_from_listing_3m").abs().reindex(d.index)
for b_lo,b_hi,lab in ((0.2,0.5,"|move| 20-50%"),(0.5,1.5,"|move| 50-150%")):
    mm=(mv>=b_lo)&(mv<b_hi)&d["dtm"].notna()
    s_=d[mm&(d["type"]=="SME")]["dtm"]; m_=d[mm&(d["type"]=="MB")]["dtm"]
    if len(s_)>=30 and len(m_)>=30:
        print(f"  {lab}: median days-to-peak SME {s_.median():.0f} vs MB {m_.median():.0f}  (cage: SME later)")
