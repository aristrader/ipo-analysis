"""Phase 1: Chittorgarh urls → ISIN-keyed base, split MB/SME, 2020 → the as-of year.

The boom-cohort year window is DYNAMIC: 2020 through the substrate as-of year (+1 for
listings that straddle a year boundary). It was hardcoded '2020'..'2025', which silently
DROPPED 2026 IPOs from the dataset — found while building the refresh flow (2026-06-06).
"""
import csv, json, os

RAW = 'data/raw/chittorgarh/urls.csv'; OUT = 'data/master'
os.makedirs(OUT, exist_ok=True)


def _boom_years():
    """'2020' .. as_of_year+1, from substrate_meta.json (fallback: current span)."""
    try:
        as_of = json.load(open('data/master/substrate_meta.json'))['as_of']
        hi = int(as_of[:4]) + 1
    except (OSError, KeyError, ValueError):
        import datetime
        hi = datetime.date.today().year
    return {str(y) for y in range(2020, hi + 1)}


YEARS = _boom_years()
rows = [r for r in csv.DictReader(open(RAW)) if r.get('isin') and r.get('year') in YEARS]
# dedupe by ISIN (keep first)
seen = set(); uniq = []
for r in rows:
    if r['isin'] in seen: continue
    seen.add(r['isin']); uniq.append(r)
cols = ['isin', 'company_name', 'type', 'nse_symbol', 'bse_script_code', 'open_date', 'close_date',
        'listing_date', 'issue_price', 'issue_amount_cr', 'pricing_method', 'listing_at', 'lead_manager', 'year']
for seg, val in [('mainboard', 'MB'), ('sme', 'SME')]:
    sub = [{c: r.get(c, '') for c in cols} for r in uniq if r['type'] == val]
    with open(f'{OUT}/_base_{seg}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(sub)
    print(f"{seg}: {len(sub)} rows (years {min(YEARS)}-{max(YEARS)})")
