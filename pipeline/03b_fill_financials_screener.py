"""Phase 3b: (RE-)SOURCE pre-IPO financials/KPIs from screener.in for ALL rows, by ISIN.

Why re-source everything: Sharescart's yr1/yr2/yr3 roll forward post-listing (yr2/yr3 are POST-IPO
for 2023+ IPOs); only its pre_ipo_* and yr1 are pre-listing. Screener has the correctly-dated full
history, so we rebuild the true pre-IPO 3-year trajectory consistently for every row.

Source cache: data/raw/screener/financials.csv (isin, fy, metric, value) — each value already verified
by exchange-code match at fetch time (scrapers/screener.py): a CONCRETE match, never name-based.

Year mapping: last pre-listing FY = listing-year if listing-month>=April else listing-year-1.
  yr3 = last pre-listing FY, yr2 = yr3-1, yr1 = yr3-2 (yr1 oldest → yr3 newest pre-IPO year).
  pre_ipo_* are derived from yr3.

SAFETY GUARD: where a trusted Sharescart pre_ipo value already exists, we cross-check screener's fy3
value against it; >5% disagreement is logged to screener_financials_review.csv (possible wrong match
or restatement) — but screener still wins (correctly-dated). Where screener lacks fy3 we KEEP the
existing pre_ipo_* (don't destroy good data). Financials we write are tagged pat_yr3_src='screener'.
"""
import csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # pipeline dir, for `lib`
from lib import fnum, num, last_pre_listing_fy

fin = {}
path = 'data/raw/screener/financials.csv'
if not os.path.exists(path):
    raise SystemExit("run scrapers/screener.py first (cache missing)")
for r in csv.DictReader(open(path)):
    try:
        fy = int(r['fy']); val = float(r['value'])
    except (ValueError, TypeError):
        continue
    fin.setdefault(r['isin'], {}).setdefault(fy, {})[r['metric']] = val


# fnum / num / last_pre_listing_fy moved to pipeline/lib.py (imported above)


YR_METRICS = {'net_sales': 'sales', 'operating_profit': 'operating_profit', 'pat': 'net_profit',
              'eps': 'eps', 'borrowings': 'borrowings', 'total_assets': 'total_assets',
              'operating_cf': 'operating_cf'}
YR_COLS = list(YR_METRICS) + ['shareholder_funds']

stats = {'rows_resourced': 0, 'fields': 0}
review = []   # cross-check disagreements vs trusted Sharescart pre_ipo_*
for seg in ['mainboard', 'sme']:
    p = f'data/master/_base_{seg}.csv'
    rows = list(csv.DictReader(open(p)))
    cols = list(rows[0].keys())
    for r in rows:
        byfy = fin.get(r['isin'])
        fy3 = last_pre_listing_fy(r.get('listing_date', ''))
        if not byfy or not fy3:
            continue
        m3 = byfy.get(fy3)
        if not m3:
            continue                              # screener lacks the pre-listing year → keep existing
        # cross-check screener fy3 sales/pat vs trusted existing Sharescart pre_ipo_* (guard)
        for fld, metric in [('pre_ipo_net_sales', 'sales'), ('pre_ipo_pat', 'net_profit')]:
            old, new = fnum(r.get(fld)), num(m3.get(metric))
            if old and new is not None and old != 0 and abs(new - old) / abs(old) > 0.05:
                review.append({'isin': r['isin'], 'company': r['company_name'], 'field': fld,
                               'sharescart': old, 'screener': new, 'fy': f'Mar {fy3}'})
        # overwrite yr1/yr2/yr3 with screener's pre-listing trajectory (clear stale first)
        for i, fy in enumerate([fy3 - 2, fy3 - 1, fy3], start=1):
            m = byfy.get(fy)
            for stem in YR_COLS:
                r[f'{stem}_yr{i}'] = ''            # clear (remove Sharescart rolling/post-IPO values)
            if not m:
                continue
            for stem, metric in YR_METRICS.items():
                v = num(m.get(metric))
                if v is not None:
                    r[f'{stem}_yr{i}'] = v; stats['fields'] += 1
            eq, res = num(m.get('equity_capital')), num(m.get('reserves'))
            if eq is not None and res is not None:
                r[f'shareholder_funds_yr{i}'] = round(eq + res, 2); stats['fields'] += 1
        # pre_ipo_* from fy3 (screener-authoritative, correctly dated)
        sales, pat = num(m3.get('sales')), num(m3.get('net_profit'))
        eq, res, brw = num(m3.get('equity_capital')), num(m3.get('reserves')), num(m3.get('borrowings'))
        sf = (eq + res) if (eq is not None and res is not None) else None
        r['pre_ipo_fin_year'] = f'Mar {fy3}'
        if sales is not None: r['pre_ipo_net_sales'] = sales
        if pat is not None:   r['pre_ipo_pat'] = pat
        if sales and pat is not None: r['pre_ipo_pat_margin_pct'] = round(pat / sales * 100, 2)
        if sf and pat is not None:    r['pre_ipo_roe_pct'] = round(pat / sf * 100, 2)
        if sf and brw is not None:    r['pre_ipo_debt_equity'] = round(brw / sf, 2)
        r['pre_ipo_years_available'] = sum(1 for fy in (fy3 - 2, fy3 - 1, fy3) if byfy.get(fy))
        r['pat_yr3_src'] = 'screener'
        stats['rows_resourced'] += 1
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    print(f"{seg}: screener financials re-sourced")

os.makedirs('data/master/review', exist_ok=True)
with open('data/master/review/screener_financials_review.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['isin', 'company', 'field', 'sharescart', 'screener', 'fy'])
    w.writeheader(); w.writerows(review)
print(f"re-sourced {stats['rows_resourced']} rows / {stats['fields']} year-fields from screener; "
      f"{len(review)} cross-check disagreements vs Sharescart → data/master/review/screener_financials_review.csv")
