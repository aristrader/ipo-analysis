"""Phase 2: attach Chittorgarh detail fields to base by ISIN (in place)."""
import csv
det={r['isin']:r for r in csv.DictReader(open('data/raw/chittorgarh/details.csv')) if r.get('isin')}
ATTACH=['market_maker','fresh_issue_cr','ofs_cr','ofs_pct','anchor_allocation_cr',
        'listing_open','listing_high','listing_low','listing_close','objects_of_issue','issue_size_cr']
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    rows=list(csv.DictReader(open(p))); cols=list(rows[0].keys())
    for c in ATTACH:
        if c not in cols: cols.append(c)
        for c2 in [c+'_src']:
            if c2 not in cols: cols.append(c2)
    for r in rows:
        d=det.get(r['isin'],{})
        for c in ATTACH:
            v=d.get(c,'')
            if v: r[c]=v; r[c+'_src']='chittorgarh'
            else: r.setdefault(c,''); r.setdefault(c+'_src','')
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f"{seg}: detail attached")
