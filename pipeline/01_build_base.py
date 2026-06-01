"""Phase 1: Chittorgarh urls → ISIN-keyed base, split MB/SME, 2020-2025."""
import csv, os
RAW='data/raw/chittorgarh/urls.csv'; OUT='data/master'
os.makedirs(OUT, exist_ok=True)
rows=[r for r in csv.DictReader(open(RAW)) if r.get('isin') and r.get('year') in
      ('2020','2021','2022','2023','2024','2025')]
# dedupe by ISIN (keep first)
seen=set(); uniq=[]
for r in rows:
    if r['isin'] in seen: continue
    seen.add(r['isin']); uniq.append(r)
cols=['isin','company_name','type','nse_symbol','bse_script_code','open_date','close_date',
      'listing_date','issue_price','issue_amount_cr','pricing_method','listing_at','lead_manager','year']
for seg,val in [('mainboard','MB'),('sme','SME')]:
    sub=[{c:r.get(c,'') for c in cols} for r in uniq if r['type']==val]
    with open(f'{OUT}/_base_{seg}.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(sub)
    print(f"{seg}: {len(sub)} rows")
