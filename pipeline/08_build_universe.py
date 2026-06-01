"""Phase 08: build data/master/universe.csv — ONE unified feature table, one row per ISIN.

Merges the four master files (boom: mainboard/sme; longterm: longterm_mainboard/longterm_sme)
into a single schema-unified table, then folds in the screener financials, screener company_meta
(sector + market_cap_class), gmp_extra, and derives instrument_type.

Does NOT modify any source master CSV. Output: data/master/universe.csv.

Dedup: 4 ISINs appear in both a boom file and a longterm file (boom rows are FPOs reusing an
earlier IPO's ISIN). We keep ONE row per ISIN; the boom row wins (richer schema, more recent event).
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*a):
    return os.path.join(ROOT, *a)


# ---------------------------------------------------------------------------
# 1. Union the four master files into rows keyed by ISIN (boom wins on collision)
# ---------------------------------------------------------------------------
SOURCES = [
    ('boom', 'mainboard'),
    ('boom', 'sme'),
    ('longterm', 'longterm_mainboard'),
    ('longterm', 'longterm_sme'),
]

union_cols = []          # ordered union of all source columns
rows_by_isin = {}        # isin -> dict
order = []               # preserve first-seen ISIN order

for cohort, fname in SOURCES:
    reader = csv.DictReader(open(p('data/master', f'{fname}.csv')))
    for c in reader.fieldnames:
        if c not in union_cols:
            union_cols.append(c)
    for r in reader:
        isin = r['isin'].strip()
        if not isin:
            continue
        r = dict(r)
        r['cohort'] = cohort                 # authoritative cohort = which file set it came from
        if isin in rows_by_isin:
            continue                         # boom seen first → boom wins, skip longterm dup
        rows_by_isin[isin] = r
        order.append(isin)

if 'cohort' not in union_cols:
    union_cols.append('cohort')

# Fill blanks so every row has every union column
for isin in order:
    r = rows_by_isin[isin]
    for c in union_cols:
        r.setdefault(c, '')

print(f"[1] unioned 4 masters → {len(order)} unique ISINs, {len(union_cols)} union columns")
print("    cohort split:", {c: sum(1 for i in order if rows_by_isin[i]['cohort'] == c)
                             for c in ('boom', 'longterm')})


# ---------------------------------------------------------------------------
# 2. Screener financials — fill pre-IPO financials for ANY row lacking them
#    (reuses the exact year-mapping logic from pipeline/03b)
# ---------------------------------------------------------------------------
fin = {}
fpath = p('data/raw/screener/financials.csv')
for r in csv.DictReader(open(fpath)):
    try:
        fy = int(r['fy']); val = float(r['value'])
    except (ValueError, TypeError):
        continue
    fin.setdefault(r['isin'], {}).setdefault(fy, {})[r['metric']] = val


def last_pre_listing_fy(listing_date):
    if not listing_date or len(listing_date) < 7:
        return None
    y, m = int(listing_date[:4]), int(listing_date[5:7])
    return y if m >= 4 else y - 1


def num(v):
    return v if isinstance(v, (int, float)) else None


def fnum(s):
    try:
        return float(str(s).replace(',', ''))
    except (ValueError, TypeError):
        return None


YR_METRICS = {'net_sales': 'sales', 'operating_profit': 'operating_profit', 'pat': 'net_profit',
              'eps': 'eps', 'borrowings': 'borrowings', 'total_assets': 'total_assets',
              'operating_cf': 'operating_cf'}
YR_COLS = list(YR_METRICS) + ['shareholder_funds']

# ensure all financial cols exist in the schema
for stem in YR_COLS:
    for i in (1, 2, 3):
        c = f'{stem}_yr{i}'
        if c not in union_cols:
            union_cols.append(c)
for c in ['pre_ipo_net_sales', 'pre_ipo_pat', 'pre_ipo_pat_margin_pct', 'pre_ipo_roe_pct',
          'pre_ipo_debt_equity', 'pre_ipo_fin_year', 'pre_ipo_years_available', 'pat_yr3_src']:
    if c not in union_cols:
        union_cols.append(c)

fin_filled = 0
for isin in order:
    r = rows_by_isin[isin]
    if str(r.get('pre_ipo_pat', '')).strip() != '':
        continue                              # already has pre-IPO financials → skip
    byfy = fin.get(isin)
    fy3 = last_pre_listing_fy(r.get('listing_date', ''))
    if not byfy or not fy3:
        continue
    m3 = byfy.get(fy3)
    if not m3:
        continue                              # screener lacks the pre-listing year → keep existing
    # overwrite yr1/yr2/yr3 with screener's pre-listing trajectory (clear stale first)
    for i, fy in enumerate([fy3 - 2, fy3 - 1, fy3], start=1):
        m = byfy.get(fy)
        for stem in YR_COLS:
            r[f'{stem}_yr{i}'] = ''
        if not m:
            continue
        for stem, metric in YR_METRICS.items():
            v = num(m.get(metric))
            if v is not None:
                r[f'{stem}_yr{i}'] = v
        eq, res = num(m.get('equity_capital')), num(m.get('reserves'))
        if eq is not None and res is not None:
            r[f'shareholder_funds_yr{i}'] = round(eq + res, 2)
    # pre_ipo_* from fy3
    sales, pat = num(m3.get('sales')), num(m3.get('net_profit'))
    eq, res, brw = num(m3.get('equity_capital')), num(m3.get('reserves')), num(m3.get('borrowings'))
    sf = (eq + res) if (eq is not None and res is not None) else None
    r['pre_ipo_fin_year'] = f'Mar {fy3}'
    if sales is not None:
        r['pre_ipo_net_sales'] = sales
    if pat is not None:
        r['pre_ipo_pat'] = pat
    if sales and pat is not None:
        r['pre_ipo_pat_margin_pct'] = round(pat / sales * 100, 2)
    if sf and pat is not None:
        r['pre_ipo_roe_pct'] = round(pat / sf * 100, 2)
    if sf and brw is not None:
        r['pre_ipo_debt_equity'] = round(brw / sf, 2)
    r['pre_ipo_years_available'] = sum(1 for fy in (fy3 - 2, fy3 - 1, fy3) if byfy.get(fy))
    r['pat_yr3_src'] = 'screener'
    fin_filled += 1

print(f"[2] screener financials: filled pre-IPO financials for {fin_filled} rows lacking them")


# ---------------------------------------------------------------------------
# 3. Screener company_meta — sector/industry/market_cap_cr + market_cap_class
# ---------------------------------------------------------------------------
META_COLS = ['broad_sector', 'sector', 'industry', 'market_cap_cr', 'market_cap_class']
for c in META_COLS:
    if c not in union_cols:
        union_cols.append(c)

meta = {}
for r in csv.DictReader(open(p('data/raw/screener/company_meta.csv'))):
    meta[r['isin'].strip()] = r


def mktcap_class(v):
    x = fnum(v)
    if x is None:
        return ''
    if x < 300:
        return 'micro'
    if x < 2000:
        return 'small'
    if x < 20000:
        return 'mid'
    return 'large'


meta_filled = 0
for isin in order:
    r = rows_by_isin[isin]
    m = meta.get(isin)
    if not m:
        r.setdefault('broad_sector', ''); r.setdefault('sector', '')
        r.setdefault('industry', ''); r.setdefault('market_cap_cr', '')
        r['market_cap_class'] = ''
        continue
    r['broad_sector'] = m.get('broad_sector', '')
    r['sector'] = m.get('sector', '')
    r['industry'] = m.get('industry', '')
    r['market_cap_cr'] = m.get('market_cap_cr', '')
    r['market_cap_class'] = mktcap_class(m.get('market_cap_cr', ''))
    meta_filled += 1

print(f"[3] company_meta: attached sector/market_cap for {meta_filled} rows")


# ---------------------------------------------------------------------------
# 3b. Screener sector_mcap (03f recovery) — fill the BOOM sector/market-cap gap.
#     company_meta covered longterm well but barely touched boom (the boom enrichment
#     grabbed financials only). 03f re-pulls just the breadcrumb for boom ISINs that
#     resolved on screener. Fill ONLY where broad_sector / market_cap_cr are still empty;
#     NEVER overwrite values already set above (longterm stays untouched).
# ---------------------------------------------------------------------------
SECTOR_MCAP_PATH = p('data/raw/screener/sector_mcap.csv')
sm_sector_filled = 0
sm_mcap_filled = 0
if os.path.exists(SECTOR_MCAP_PATH):
    sm = {}
    for r in csv.DictReader(open(SECTOR_MCAP_PATH)):
        sm[r['isin'].strip()] = r
    for isin in order:
        rec = sm.get(isin)
        if not rec:
            continue
        r = rows_by_isin[isin]
        # sector breadcrumb: fill only when broad_sector currently empty (don't clobber)
        if not (r.get('broad_sector') or '').strip():
            bs = (rec.get('broad_sector') or '').strip()
            sec = (rec.get('sector') or '').strip()
            ind = (rec.get('industry') or '').strip()
            if bs or sec or ind:
                r['broad_sector'] = bs
                r['sector'] = sec
                r['industry'] = ind
                sm_sector_filled += 1
        # market cap: fill only when market_cap_cr currently empty
        if not (r.get('market_cap_cr') or '').strip():
            mc = (rec.get('market_cap_cr') or '').strip()
            if mc:
                r['market_cap_cr'] = mc
                r['market_cap_class'] = mktcap_class(mc)
                sm_mcap_filled += 1
    print(f"[3b] sector_mcap (03f): filled broad_sector for {sm_sector_filled} rows, "
          f"market_cap for {sm_mcap_filled} rows (boom gap recovery; fill-only, no overwrite)")
else:
    print(f"[3b] sector_mcap: {SECTOR_MCAP_PATH} not present — run pipeline/03f_sector_mcap.py "
          f"to recover the boom sector/market-cap gap (skipping)")


# ---------------------------------------------------------------------------
# 4. gmp_extra/found.csv — fill gmp_pct where empty (numeric gmp_pct rows only)
# ---------------------------------------------------------------------------
for c in ['gmp_pct', 'gmp_pct_src']:
    if c not in union_cols:
        union_cols.append(c)

gmp_extra = {}
for r in csv.DictReader(open(p('data/raw/gmp_extra/found.csv'))):
    v = fnum(r.get('gmp_pct'))
    if v is not None:
        gmp_extra[r['isin'].strip()] = (v, r.get('source', '') or 'gmp_extra')

gmp_filled = 0
for isin in order:
    r = rows_by_isin[isin]
    if str(r.get('gmp_pct', '')).strip() != '':
        continue
    if isin in gmp_extra:
        v, src = gmp_extra[isin]
        r['gmp_pct'] = v
        r['gmp_pct_src'] = src
        gmp_filled += 1

print(f"[4] gmp_extra: filled gmp_pct for {gmp_filled} rows")


# ---------------------------------------------------------------------------
# 5. instrument_type — derive from company_name
# ---------------------------------------------------------------------------
if 'instrument_type' not in union_cols:
    union_cols.append('instrument_type')

KNOWN_INVIT = ['anantam highways trust', 'capital infra trust', 'bharat highways invit',
               'powergrid invit', 'knowledge realty trust']
KNOWN_REIT = ['mindspace', 'nexus select trust', 'property share', 'propshare',
              'brookfield', 'biret']


def instrument_type(name):
    n = (name or '').lower()
    if 'fpo' in n:
        return 'fpo'
    if any(k in n for k in KNOWN_REIT) or 'reit' in n or 'real estate investment trust' in n:
        return 'reit'
    if (any(k in n for k in KNOWN_INVIT) or 'invit' in n or 'inv it' in n
            or 'infrastructure investment trust' in n):
        return 'invit'
    # A bare 'trust' in the name is NOT enough — it mis-tags brand/trusteeship/fintech
    # names ("Beacon Trusteeship", "Trust Fintech"). Only tag genuine REIT/InvIT names
    # (the keyword/known-list checks above); everything else stays equity.
    if 'ruchi soya' in n:
        return 'fpo'
    return 'equity'


itype_counts = {}
for isin in order:
    r = rows_by_isin[isin]
    t = instrument_type(r.get('company_name', ''))
    r['instrument_type'] = t
    itype_counts[t] = itype_counts.get(t, 0) + 1

print(f"[5] instrument_type: {itype_counts}")


# ---------------------------------------------------------------------------
# 6. Order columns sensibly and write universe.csv
# ---------------------------------------------------------------------------
IDENTITY_FIRST = ['isin', 'company_name', 'type', 'cohort', 'instrument_type',
                  'nse_symbol', 'bse_script_code', 'ticker_ns', 'ticker_bo',
                  'open_date', 'close_date', 'listing_date',
                  'issue_price', 'issue_size_cr', 'issue_amount_cr',
                  'fresh_issue_cr', 'ofs_cr', 'ofs_pct',
                  'sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x',
                  'gmp_pct', 'promoter_pre_issue_pct', 'promoter_post_issue_pct',
                  'anchor_allocation_cr', 'lead_manager', 'market_maker',
                  'year', 'broad_sector', 'sector', 'industry',
                  'market_cap_cr', 'market_cap_class']

final_cols = [c for c in IDENTITY_FIRST if c in union_cols]
final_cols += [c for c in union_cols if c not in final_cols]

out = p('data/master/universe.csv')
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=final_cols, extrasaction='ignore')
    w.writeheader()
    for isin in order:
        w.writerow(rows_by_isin[isin])

print(f"[6] wrote {out}: {len(order)} rows × {len(final_cols)} columns")
