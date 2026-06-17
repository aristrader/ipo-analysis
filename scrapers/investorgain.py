"""InvestorGain GMP — second-pass GMP source (gap G2), via the webnodejs report API.

Same backend pattern as Chittorgarh. The GMP performance-tracker (report 377) returns ALL IPOs for
a year in one JSON call, each row carrying NSE symbol + BSE code + listing date + GMP(₹) + IPO price.
So matching is CONCRETE by exchange-id + listing-date (no name guessing). One call per year.

Different host from screener.in → safe to run alongside the screener grind.

gmp_tracked flag (per row):
  True  — source has a non-zero GMP (the source explicitly tracked this IPO's grey-market).
  False — source returned 0 / ₹0 for GMP; this is InvestorGain's placeholder for "never tracked",
          not a genuine zero. gmp_rs is set to None in this case.
  The distinction matters: 380 rows had gmp_rs=0.0 historically, of which ~13 are confirmed
  false-zeros (high gmp_rating + big listing gains). The raw JSON is saved so the placeholder
  can be re-evaluated if InvestorGain changes behaviour.
"""
import json
import os
import re
import sys
import time
import cloudscraper

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

# NOTE: the '/5/' segment is part of report 377's fixed config — it returns ALL rows for the year
# (totalPages=1) regardless; changing it (e.g. /100/) breaks the response. Do not "fix" it.
_API = 'https://webnodejs.investorgain.com/cloud/v2/report/data-read/377/{page}/5/{year}/2026-27/0/all?search=&v=14-42'
_HDR = {'Referer': 'https://www.investorgain.com/'}
_MONTHS = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}
_SOURCE = 'investorgain'


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


def _gmp_value(raw_gmp):
    """Parse the GMP cell from the InvestorGain API, distinguishing a genuine 0 from a placeholder.

    InvestorGain returns '0' / '₹0' for IPOs it never tracked in its grey-market database. This is
    a source placeholder, NOT a genuine GMP-of-zero reading. Returning 0.0 for these created 380
    false-zero rows (the I1/Rule-1 bug).

    Returns (gmp_rs, gmp_tracked):
      gmp_rs      — the numeric GMP in ₹, or None if absent/placeholder.
      gmp_tracked — True if source has a non-zero GMP; False if source returned a 0-placeholder.
    """
    v = _num(raw_gmp)
    if v is None:
        return None, False     # missing / unparseable
    if v == 0.0:
        # InvestorGain's placeholder for "never tracked" — treat as missing, not genuine zero.
        return None, False
    return v, True


def _split_symbol(sym):
    """'UNIMECH, 544322' -> ('UNIMECH','544322'); handles NSE-only / BSE-only."""
    nse = bse = ''
    for tok in _clean(sym).replace(',', ' ').split():
        if tok.isdigit():
            bse = tok
        elif re.fullmatch(r'[A-Z0-9&\-]+', tok):
            nse = tok
    return nse, bse


def _parse_rows(raw_rows, year):
    """Extract structured rows from the raw reportTableData list.

    Pure function — no I/O. Returns list of dicts with:
      year, name, nse, bse, listing_date, gmp_rs, gmp_tracked, ipo_price, gmp_rating,
      listing_gain_pct.
    """
    out = []
    for row in raw_rows:
        nse, bse = _split_symbol(row.get('Symbol'))
        gmp_rs, gmp_tracked = _gmp_value(row.get('GMP'))
        out.append({
            'year': year,
            'name': _clean(row.get('IPO')).replace(' IPO', ''),
            'nse': nse, 'bse': bse,
            'listing_date': _to_iso(row.get('Listing Date')),
            'gmp_rs': gmp_rs,
            'gmp_tracked': gmp_tracked,
            'ipo_price': _num(row.get('IPO Price')),
            'gmp_rating': _clean(row.get('~srt_gmp_rating')),
            'listing_gain_pct': _clean(row.get('~str_listing_gain_in_per')),
        })
    return out


def fetch_year(scraper, year):
    """All GMP rows for a year: list of dicts (see _parse_rows for fields).

    Saves each page's raw JSON via ingest.save_raw before parsing.
    """
    out = []
    page = 1
    while True:
        r = scraper.get(_API.format(page=page, year=year), headers=_HDR, timeout=30)
        # Save raw JSON before parsing — root cause fix for the "raw was discarded" audit finding.
        ingest.save_raw(_SOURCE, f'{year}_page{page}.json', r.text)
        d = json.loads(r.text)
        rows = d.get('reportTableData') or []
        out.extend(_parse_rows(rows, year))
        if page >= int(d.get('totalPages') or 1):
            break
        page += 1
    return out


if __name__ == '__main__':
    import csv
    config.ensure(config.raw_dir(_SOURCE))
    s = cloudscraper.create_scraper()
    allrows = []
    for y in range(2020, 2026):
        rows = fetch_year(s, y)
        allrows += rows
        g = sum(1 for r in rows if r['gmp_tracked'])
        print(f"  {y}: {len(rows)} IPOs, {g} with tracked GMP", flush=True)
        time.sleep(0.5)
    out_csv = config.raw_dir(_SOURCE) / 'gmp.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'name', 'nse', 'bse', 'listing_date',
                                          'gmp_rs', 'gmp_tracked', 'ipo_price',
                                          'gmp_rating', 'listing_gain_pct'])
        w.writeheader(); w.writerows(allrows)
    print(f"\nwrote {out_csv} ({len(allrows)} rows, "
          f"{sum(1 for r in allrows if r['gmp_tracked'])} with tracked GMP)")
