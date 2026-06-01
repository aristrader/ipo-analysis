"""Phase 5: reconcile new master vs archived old dataset, BY ISIN. Flag field diffs.
HARD = identity/ticker diff; SOFT = numeric diff within data-quality noise."""
import csv, os
def load(paths):
    d={}
    for p in paths:
        for r in csv.DictReader(open(p)):
            if r.get('isin'): d[r['isin']]=r
    return d
new=load(['data/master/mainboard.csv','data/master/sme.csv'])
old=load(['archive/derived/mainboard_clean_OLD.csv','archive/derived/sme_clean_OLD.csv'])
def num(x):
    try: return float(x)
    except: return None
report=[]
for isin in set(new)&set(old):
    n,o=new[isin],old[isin]
    # ticker (identity). Join is by ISIN, so same security is guaranteed; classify the diff:
    #   HARD     = NSE symbol genuinely changed (rename / corrected false-positive ticker)
    #   BSE_FMT  = BSE-only both sides, old used alphabetic scrip_id, new uses Yahoo-correct
    #              numeric code (expected format fix, not a regression)
    n_ns=(n.get('ticker_ns') or '').split('.')[0]; o_ns=(o.get('ticker_ns') or '').split('.')[0]
    n_bo=(n.get('ticker_bo') or '').split('.')[0]; o_bo=(o.get('ticker_bo') or '').split('.')[0]
    if n_ns and o_ns and n_ns!=o_ns:
        report.append({'isin':isin,'company':n.get('company_name'),'field':'ticker',
                       'old':o_ns,'new':n_ns,'severity':'HARD'})
    elif (not n_ns and not o_ns) and n_bo and o_bo and n_bo!=o_bo:
        report.append({'isin':isin,'company':n.get('company_name'),'field':'ticker_bo',
                       'old':o_bo,'new':n_bo,'severity':'BSE_FMT'})
    # numeric fields — SOFT if >5% diff
    for fld in ['issue_price','listing_open','sub_total_x']:
        a,b=num(n.get(fld)),num(o.get(fld))
        if a is not None and b is not None and b!=0 and abs(a-b)/b>0.05:
            report.append({'isin':isin,'company':n.get('company_name'),'field':fld,
                           'old':o.get(fld),'new':n.get(fld),'severity':'SOFT'})
# rows only in old (we dropped?) and only in new (we added)
for isin in set(old)-set(new):
    report.append({'isin':isin,'company':old[isin].get('company_name'),'field':'PRESENCE',
                   'old':'in_old','new':'MISSING_in_new','severity':'HARD'})
os.makedirs('data/master/review',exist_ok=True)
with open('data/master/review/reconciliation_report.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['isin','company','field','old','new','severity'])
    w.writeheader(); w.writerows(report)
overlap=len(set(new)&set(old))
hard=sum(1 for r in report if r['severity']=='HARD')
print(f"reconcile: {overlap} overlapping ISINs; {len(report)} flags ({hard} HARD) → reconciliation_report.csv")
print("Review HARD rows: each must be a KNOWN old-data error (else investigate before trusting new master).")
