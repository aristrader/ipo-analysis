"""Phase 4: derive authoritative ticker via ISIN↔symbol, set confidence + provenance,
write final master files. ISIN drives ticker; price is a secondary cross-check flag.

Exchange-aware ticker:
  - ISIN in an NSE list  -> <NSE symbol>.NS
  - ISIN BSE-only        -> <BSE numeric code>.BO   (Yahoo uses the numeric scrip code)
  - else Chittorgarh nse_symbol -> <symbol>.NS

Human-verified renames / confirmed symbols live in data/reference/name_overrides.csv.
An ISIN listed there is treated as resolved: company_name is updated to the latest name
(original kept in name_at_ipo) and it is excluded from the conflict/review files.
Any name<->ISIN mismatch NOT in that file is still flagged for review (safety net)."""
import csv, os
from scrapers.exchange_lists import load
sym2isin, isin2sym = load()
all_conflicts=[]

_STOPWORDS={'ltd','limited','the','and','india','indian','of','company','co','pvt','private'}
def _tokens(name):
    out=set()
    for tok in ''.join(c.lower() if (c.isalnum() or c==' ') else ' ' for c in (name or '')).split():
        if tok and tok not in _STOPWORDS:
            out.add(tok)
    return out

# isin -> official entity name (for the name<->ISIN check); first non-empty wins, prefer NSE
isin2name={}
# isin -> NSE symbol (NSE listing only; decides .NS vs .BO)
isin2nse={}
for path,namecol,isincol,symcol,is_nse in [
    ('data/reference/nse_mainboard.csv','NAME OF COMPANY',' ISIN NUMBER','SYMBOL',True),
    ('data/reference/nse_emerge_sme.csv','NAME_OF_COMPANY','ISIN_NUMBER','SYMBOL',True),
    ('data/reference/bse_master.csv','Scrip_Name','ISIN_NUMBER','scrip_id',False),
]:
    for rr in csv.DictReader(open(path)):
        isin=(rr.get(isincol) or '').strip()
        if not isin: continue
        nm=(rr.get(namecol) or '').strip()
        if nm and not isin2name.get(isin): isin2name[isin]=nm
        if is_nse:
            sym=(rr.get(symcol) or '').strip()
            if sym and not isin2nse.get(isin): isin2nse[isin]=sym

# Human-verified renames / confirmed ISIN↔symbol decisions
overrides={}
opath='data/reference/name_overrides.csv'
if os.path.exists(opath):
    for rr in csv.DictReader(open(opath)):
        i=(rr.get('isin') or '').strip()
        if i: overrides[i]=(rr.get('latest_name') or '').strip()

all_name_reviews=[]
for seg in ['mainboard','sme']:
    inp=f'data/master/_base_{seg}.csv'; out=f'data/master/{seg}.csv'
    rows=list(csv.DictReader(open(inp))); cols=list(rows[0].keys())
    for c in ['ticker_ns','ticker_bo','confidence','confidence_reason','isin_xchg_check',
              'ticker_needs_review','name_at_ipo','official_isin_name','name_isin_check']:
        if c not in cols: cols.append(c)
    conflicts=[]
    for r in rows:
        isin=r.get('isin','')
        r.setdefault('ticker_ns',''); r.setdefault('ticker_bo','')
        r['ticker_needs_review']=''
        confirmed = isin in overrides
        off_sym=isin2sym.get(isin,'')          # official symbol (NSE pref, else BSE scrip_id)
        nse_sym=isin2nse.get(isin,'')           # set only if ISIN is on an NSE list
        ch_sym=(r.get('nse_symbol') or '').strip()
        bse_code=(r.get('bse_script_code') or '').strip()
        # BSE ticker uses the numeric scrip code on Yahoo; set whenever a BSE code exists
        r['ticker_bo']=f'{bse_code}.BO' if bse_code else ''
        if confirmed:                            # human-verified rename / symbol
            r['ticker_ns']=f'{(nse_sym or ch_sym)}.NS' if (nse_sym or ch_sym) else ''
            r['confidence']='isin_authoritative'
            r['confidence_reason']='human-verified rename / confirmed ISIN↔symbol'
            r['isin_xchg_check']='renamed_confirmed'
        elif nse_sym:                            # official NSE listing
            r['ticker_ns']=f'{nse_sym}.NS'
            if not ch_sym or ch_sym==nse_sym:
                r['confidence']='isin_authoritative'
                r['confidence_reason']='ISIN→symbol from official NSE list'
                r['isin_xchg_check']='match'
            else:                                # Chittorgarh disagrees with official NSE symbol
                r['confidence']='isin_symbol_conflict'
                r['confidence_reason']=f'Chittorgarh symbol {ch_sym} != official NSE {nse_sym} for ISIN {isin} (rename or wrong ISIN — REVIEW)'
                r['isin_xchg_check']='CONFLICT'; r['ticker_needs_review']='True'
                conflicts.append({'company_name':r.get('company_name',''),'isin':isin,
                                  'chittorgarh_nse_symbol':ch_sym,'official_symbol':nse_sym,'type':seg})
        elif ch_sym:                             # Chittorgarh says NSE but ISIN not in official NSE list — trust it
            r['ticker_ns']=f'{ch_sym}.NS'
            r['confidence']='chittorgarh_symbol'
            r['confidence_reason']='Chittorgarh nse_symbol (ISIN not in NSE exchange list)'
            r['isin_xchg_check']='unchecked'
        elif off_sym or bse_code:                # BSE-listed, no NSE evidence -> .BO only
            r['ticker_ns']=''
            r['confidence']='isin_authoritative' if off_sym else 'bse_only'
            r['confidence_reason']='ISIN→symbol from official BSE list' if off_sym else 'BSE code only'
            r['isin_xchg_check']='match' if off_sym else 'unchecked'
        else:
            r['ticker_ns']=''
            r['confidence']='unresolved'; r['confidence_reason']='no ticker'; r['isin_xchg_check']='unchecked'

        # company_name <-> official ISIN entity name check (+ apply human-verified overrides)
        off_name=isin2name.get(isin,'')
        r['official_isin_name']=off_name
        r['name_at_ipo']=r.get('company_name','')
        if confirmed:                            # resolved rename: adopt latest name, clear flag
            r['company_name']=overrides[isin] or r.get('company_name','')
            r['name_isin_check']='renamed_confirmed'
            r['ticker_needs_review']=''
        elif not off_name:
            r['name_isin_check']='no_ref'
        elif _tokens(r.get('company_name','')) & _tokens(off_name):
            r['name_isin_check']='match'
        else:
            r['name_isin_check']='REVIEW'
            r['ticker_needs_review']='True'
            all_name_reviews.append({'company_name':r.get('company_name',''),'official_isin_name':off_name,
                                     'isin':isin,'ticker_ns':r.get('ticker_ns',''),'type':seg,
                                     'confidence':r.get('confidence','')})
    with open(out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    _m=sum(1 for r in rows if r.get('name_isin_check')=='match')
    _rv=sum(1 for r in rows if r.get('name_isin_check')=='REVIEW')
    _nr=sum(1 for r in rows if r.get('name_isin_check')=='no_ref')
    _rc=sum(1 for r in rows if r.get('name_isin_check')=='renamed_confirmed')
    _bo=sum(1 for r in rows if r.get('ticker_bo') and not r.get('ticker_ns'))
    print(f"{seg}: wrote {out}, {len(conflicts)} unresolved ISIN↔symbol conflicts; .BO-only tickers={_bo}")
    print(f"{seg}: name_isin_check -> match={_m} REVIEW={_rv} no_ref={_nr} renamed_confirmed={_rc}")
    all_conflicts.extend(conflicts)

os.makedirs('data/master/review',exist_ok=True)
cpath='data/master/review/ticker_conflicts.csv'
cfields=['company_name','isin','chittorgarh_nse_symbol','official_symbol','type']
with open(cpath,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cfields); w.writeheader(); w.writerows(all_conflicts)
print(f"wrote {cpath}, {len(all_conflicts)} total unresolved conflict rows")

npath='data/master/review/name_isin_review.csv'
nfields=['company_name','official_isin_name','isin','ticker_ns','type','confidence']
with open(npath,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=nfields); w.writeheader(); w.writerows(all_name_reviews)
print(f"wrote {npath}, {len(all_name_reviews)} unresolved name<->ISIN REVIEW rows")
