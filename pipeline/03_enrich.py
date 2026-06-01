"""Phase 3: enrich base with Sharescart (subscription/financials/gmp/promoter) by ISIN ONLY.
Screener financials for 2020-22 is a documented TODO (gaps.csv), not auto-filled here."""
import csv, os
old={}
for f in ['archive/derived/mainboard_clean_OLD.csv','archive/derived/sme_clean_OLD.csv']:
    for r in csv.DictReader(open(f)):
        if r.get('isin'): old[r['isin']]=r
# fields to pull from Sharescart old data
FIN=['sub_qib_x','sub_nii_x','sub_retail_x','sub_total_x','sub_qib_cr','sub_nii_cr','sub_retail_cr',
     'sub_total_cr','gmp_pct','promoter_pre_issue_pct','promoter_post_issue_pct','price_band_low',
     'book_built','lot_size_shares','min_investment_rs','pe_ratio','pat_ttm_cr','sales_ttm_cr','eps_ttm']
YRS=['net_sales','operating_profit','pat','eps','shareholder_funds','borrowings','total_assets',
     'operating_cf']
for base in YRS:
    for y in ['yr1','yr2','yr3']: FIN.append(f'{base}_{y}')
FIN += ['pre_ipo_pat_margin_pct','pre_ipo_roe_pct','pre_ipo_debt_equity','pre_ipo_net_sales',
        'pre_ipo_pat','pre_ipo_fin_year','pre_ipo_years_available']
gaps=[]
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    rows=list(csv.DictReader(open(p))); cols=list(rows[0].keys())
    for c in FIN + [c+'_src' for c in ['sub_total_x','pat_yr3','gmp_pct','promoter_post_issue_pct']]:
        if c not in cols: cols.append(c)
    for r in rows:
        o=old.get(r['isin'])
        if o:
            for c in FIN:
                if o.get(c): r[c]=o[c]
            for c in ['sub_total_x','pat_yr3','gmp_pct','promoter_post_issue_pct']:
                r[c+'_src']='sharescart' if o.get(c) else ''
        else:
            for c in FIN: r.setdefault(c,'')
            if r.get('year') in ('2020','2021','2022'):
                gaps.append({'isin':r['isin'],'company_name':r['company_name'],'type':r['type'],
                             'year':r['year'],'missing':'subscription,financials,gmp (no Sharescart 2020-22)'})
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f"{seg}: enriched")
os.makedirs('data/master/review',exist_ok=True)
with open('data/master/review/gaps.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['isin','company_name','type','year','missing']); w.writeheader(); w.writerows(gaps)
print(f"gaps logged: {len(gaps)} rows → data/master/review/gaps.csv")
