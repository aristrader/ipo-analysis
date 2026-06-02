"""Phase 3e: fill GMP from investorgain (gap G2, second pass) into _base, by exchange-id + date.

Source cache: data/raw/investorgain/gmp.csv (year,name,nse,bse,listing_date,gmp_rs,ipo_price,...).
CONCRETE match: our row matches an investorgain row only when our nse_symbol OR bse_script_code equals
theirs AND the listing_date is identical. gmp_pct = gmp_rs / issue_price * 100 (our issue_price; falls
back to their ipo_price). Only fills rows lacking gmp_pct; tags gmp_pct_src='investorgain'. No guessing.
"""
import csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # pipeline dir, for `lib`
from lib import fnum

src = 'data/raw/investorgain/gmp.csv'
if not os.path.exists(src):
    raise SystemExit("run scrapers/investorgain.py first (cache missing)")

by_nse, by_bse = {}, {}
for r in csv.DictReader(open(src)):
    if r.get('nse'):
        by_nse.setdefault(r['nse'], []).append(r)
    if r.get('bse'):
        by_bse.setdefault(r['bse'], []).append(r)


# fnum moved to pipeline/lib.py (imported above)


def find_match(nse_symbol, bse_code, listing_date):
    """Return an investorgain row matching by exchange-id AND exact listing_date, else None."""
    cands = []
    if nse_symbol:
        cands += by_nse.get(nse_symbol, [])
    if bse_code:
        cands += by_bse.get(str(bse_code), [])
    for c in cands:
        if c.get('listing_date') and listing_date and c['listing_date'] == listing_date:
            return c
    return None


filled = 0
nogmp = 0
for seg in ['mainboard', 'sme']:
    p = f'data/master/_base_{seg}.csv'
    rows = list(csv.DictReader(open(p)))
    cols = list(rows[0].keys())
    for r in rows:
        if (r.get('gmp_pct') or '').strip():
            continue                                  # already has GMP (don't overwrite)
        m = find_match((r.get('nse_symbol') or '').strip(),
                       (r.get('bse_script_code') or '').strip(),
                       (r.get('listing_date') or '').strip())
        if not m:
            continue
        gmp_rs = fnum(m.get('gmp_rs'))
        if gmp_rs is None or gmp_rs == 0:
            nogmp += 1                                # matched but no GMP value (e.g. weak IPO)
            continue
        issue = fnum(r.get('issue_price')) or fnum(m.get('ipo_price'))
        if not issue:
            continue
        r['gmp_pct'] = round(gmp_rs / issue * 100, 2)
        r['gmp_pct_src'] = 'investorgain'
        filled += 1
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    print(f"{seg}: investorgain GMP applied")
print(f"filled GMP on {filled} rows from investorgain (src='investorgain'); "
      f"{nogmp} concrete matches had no GMP value (left blank)")
