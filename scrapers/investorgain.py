"""InvestorGain GMP — second-pass GMP source (gap G2), via the webnodejs report API.

Same backend pattern as Chittorgarh. The GMP performance-tracker (report 377) returns ALL IPOs for
a year in one JSON call, each row carrying NSE symbol + BSE code + listing date + GMP(₹) + IPO price.
So matching is CONCRETE by exchange-id + listing-date (no name guessing). One call per year.

Different host from screener.in → safe to run alongside the screener grind.
"""
import json, re, time
import cloudscraper

# NOTE: the '/5/' segment is part of report 377's fixed config — it returns ALL rows for the year
# (totalPages=1) regardless; changing it (e.g. /100/) breaks the response. Do not "fix" it.
_API = 'https://webnodejs.investorgain.com/cloud/v2/report/data-read/377/{page}/5/{year}/2026-27/0/all?search=&v=14-42'
_HDR = {'Referer': 'https://www.investorgain.com/'}
_MONTHS = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def _clean(x):
    return re.sub(r'<[^>]+>', '', str(x or '')).replace('&#8377;', '').replace(',', ' ').strip()


def _to_iso(s):
    """'31-Dec-2024' -> '2024-12-31'."""
    m = re.match(r'(\d{1,2})-([A-Za-z]{3})-(\d{4})', s or '')
    if not m:
        return None
    mo = _MONTHS.get(m.group(2).lower())
    return f'{int(m.group(3)):04d}-{mo:02d}-{int(m.group(1)):02d}' if mo else None


def _num(x):
    s = re.sub(r'[^\d.]', '', _clean(x).split()[0]) if _clean(x) else ''
    try:
        return float(s)
    except ValueError:
        return None


def _split_symbol(sym):
    """'UNIMECH, 544322' -> ('UNIMECH','544322'); handles NSE-only / BSE-only."""
    nse = bse = ''
    for tok in _clean(sym).replace(',', ' ').split():
        if tok.isdigit():
            bse = tok
        elif re.fullmatch(r'[A-Z0-9&\-]+', tok):
            nse = tok
    return nse, bse


def fetch_year(scraper, year):
    """All GMP rows for a year: list of {name,nse,bse,listing_date,gmp_rs,ipo_price,gmp_rating,listing_gain_pct}."""
    out = []
    page = 1
    while True:
        r = scraper.get(_API.format(page=page, year=year), headers=_HDR, timeout=30)
        d = json.loads(r.text)
        rows = d.get('reportTableData') or []
        for row in rows:
            nse, bse = _split_symbol(row.get('Symbol'))
            out.append({
                'year': year, 'name': _clean(row.get('IPO')).replace(' IPO', ''),
                'nse': nse, 'bse': bse,
                'listing_date': _to_iso(row.get('Listing Date')),
                'gmp_rs': _num(row.get('GMP')),
                'ipo_price': _num(row.get('IPO Price')),
                'gmp_rating': _clean(row.get('~srt_gmp_rating')),
                'listing_gain_pct': _clean(row.get('~str_listing_gain_in_per')),
            })
        if page >= int(d.get('totalPages') or 1):
            break
        page += 1
    return out


if __name__ == '__main__':
    import csv, os
    os.makedirs('data/raw/investorgain', exist_ok=True)
    s = cloudscraper.create_scraper()
    allrows = []
    for y in range(2020, 2026):
        rows = fetch_year(s, y)
        allrows += rows
        g = sum(1 for r in rows if r['gmp_rs'])
        print(f"  {y}: {len(rows)} IPOs, {g} with GMP", flush=True)
        time.sleep(0.5)
    with open('data/raw/investorgain/gmp.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'name', 'nse', 'bse', 'listing_date',
                                          'gmp_rs', 'ipo_price', 'gmp_rating', 'listing_gain_pct'])
        w.writeheader(); w.writerows(allrows)
    print(f"\nwrote data/raw/investorgain/gmp.csv ({len(allrows)} rows, "
          f"{sum(1 for r in allrows if r['gmp_rs'])} with GMP)")
