"""
scrapers/chittorgarh.py

E2 — Chittorgarh as the unified source: back-fill 2020-2022, enrich, cross-validate.

Chittorgarh's list API (report 82 = full MB+SME IPO list) is reachable via cloudscraper:
    https://webnodejs.chittorgarh.com/cloud/report/data-read/82/<page>/5/<YEAR>/2026-27/0/all/0?search=&v=13-44
  - Serves 5 rows/page. The totalRecords field LIES (always 5) — paginate until empty / repeat.
  - The FY slot (2026-27) is current-FY context, not a data filter.
  - Each row already carries: ~isin, ~nse_symbol, ~bse_script_code, slug, dates, issue price,
    issue amount, lead manager, listing exchanges, Issue Category (Mainboard/SME).

Phases:
  list   → pull all years, write data/raw/chittorgarh_urls.csv (identity + ISIN + tickers + basics)
  detail → scrape each detail page for market_maker, OFS, anchor, subscription, financials (TODO)

Usage:
    python scrapers/chittorgarh.py --phase list [--years 2020-2025]
    python scrapers/chittorgarh.py --phase detail [--workers 6]

Logs to logs/chittorgarh_TIMESTAMP.log
"""

import argparse
import csv
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import cloudscraper
from bs4 import BeautifulSoup

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys as _sys
_sys.path.insert(0, BASE_DIR)
from foundation import config, ingest

LOGS_DIR  = str(config.logs_dir())
URLS_CSV    = str(config.raw_dir('chittorgarh') / 'urls.csv')
DETAILS_CSV = str(config.raw_dir('chittorgarh') / 'details.csv')

LIST_API = ('https://webnodejs.chittorgarh.com/cloud/report/data-read/82/'
            '{page}/5/{year}/2026-27/0/all/0?search=&v=13-44')
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
RATE = 0.3

log = logging.getLogger(__name__)

LIST_COLS = [
    'company_name', 'type', 'chittorgarh_slug', 'chittorgarh_id', 'detail_url',
    'isin', 'nse_symbol', 'bse_script_code',
    'open_date', 'close_date', 'listing_date',
    'issue_price', 'issue_amount_cr', 'pricing_method', 'listing_at', 'lead_manager', 'year',
]


def setup_logging():
    config.ensure(config.logs_dir())
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    lf = os.path.join(LOGS_DIR, f'chittorgarh_{ts}.log')
    logging.basicConfig(level=logging.INFO,
        handlers=[logging.FileHandler(lf, encoding='utf-8'), logging.StreamHandler()],
        format='%(asctime)s [%(levelname)-7s] %(message)s', datefmt='%H:%M:%S')
    log.info(f'Log: {lf}')


def _strip_html(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def _iso_to_date(s):
    """'2022-12-30T00:00:00.000Z' → '2022-12-30'."""
    if not s:
        return ''
    m = re.match(r'(\d{4}-\d{2}-\d{2})', s)
    return m.group(1) if m else ''


def parse_list_row(r):
    company_html = r.get('Company', '')
    m = re.search(r'/ipo/([a-z0-9\-]+)-ipo/(\d+)/', company_html)
    slug = (r.get('~URLRewrite_Folder_Name') or (m.group(1) + '-ipo' if m else '')).strip()
    cid  = m.group(2) if m else ''
    cat  = (r.get('Issue Category') or '').strip()
    typ  = 'MB' if cat.lower().startswith('main') else ('SME' if 'sme' in cat.lower() else cat)
    return {
        'company_name':    _strip_html(r.get('~compare_name') or company_html).replace(' IPO', '').strip(),
        'type':            typ,
        'chittorgarh_slug': slug,
        'chittorgarh_id':  cid,
        'detail_url':      f'https://www.chittorgarh.com/ipo/{slug}/{cid}/' if slug and cid else '',
        'isin':            (r.get('~isin') or '').strip(),
        'nse_symbol':      (r.get('~nse_symbol') or '').strip(),
        'bse_script_code': str(r.get('~bse_script_code') or '').strip(),
        'open_date':       _iso_to_date(r.get('~Issue_Open_Date')),
        'close_date':      _iso_to_date(r.get('~IssueCloseDate')),
        'listing_date':    _iso_to_date(r.get('~ListingDate')),
        'issue_price':     str(r.get('Issue Price (Rs.)') or '').strip(),
        'issue_amount_cr': str(r.get('Total Issue Amount (Incl.Firm reservations) (Rs.cr.)') or '').strip(),
        'pricing_method':  (r.get('Pricing Method') or '').strip(),
        'listing_at':      (r.get('Listing at') or '').strip(),
        'lead_manager':    _strip_html(r.get('Lead Manager')),
    }


def pull_year(scraper, year):
    rows, page, seen_first = [], 1, set()
    while page <= 300:
        url = LIST_API.format(page=page, year=year)
        try:
            resp = scraper.get(url, headers={'Referer': 'https://www.chittorgarh.com/'}, timeout=20)
            raw_text = resp.text
            j = resp.json()
        except Exception as e:
            log.warning(f'  {year} p{page} error: {e}')
            break
        # Save raw list API payload before parsing
        ingest.save_raw('chittorgarh', f'list_{year}_p{page}.json', raw_text)
        d = j.get('reportTableData') or []
        if not d:
            break
        first = d[0].get('Company', '')
        if first in seen_first:   # pagination wrapped — no new data
            break
        seen_first.add(first)
        rows.extend(parse_list_row(r) for r in d)
        page += 1
        time.sleep(RATE)
    return rows


def run_list_phase(years):
    config.ensure(config.raw_dir('chittorgarh'))
    scraper = cloudscraper.create_scraper()
    all_rows = []
    for y in years:
        t = time.time()
        rows = pull_year(scraper, y)
        for r in rows:
            r['year'] = y
        all_rows.extend(rows)
        n_mb = sum(1 for r in rows if r['type'] == 'MB')
        n_sme = sum(1 for r in rows if r['type'] == 'SME')
        log.info(f'  {y}: {len(rows)} rows (MB={n_mb} SME={n_sme}) in {time.time()-t:.0f}s')

    with open(URLS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=LIST_COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(all_rows)

    have_isin = sum(1 for r in all_rows if r['isin'])
    have_nse  = sum(1 for r in all_rows if r['nse_symbol'])
    have_bse  = sum(1 for r in all_rows if r['bse_script_code'])
    log.info(f'Written {len(all_rows)} rows → {URLS_CSV}')
    log.info(f'  with ISIN={have_isin}  nse_symbol={have_nse}  bse_code={have_bse}')


# ── Detail phase ──────────────────────────────────────────────────────────────

DETAIL_COLS = [
    'chittorgarh_id', 'isin', 'company_name', 'type',
    'fetch_status',
    'market_maker', 'anchor_allocation_cr',
    'issue_size_cr', 'fresh_issue_cr', 'ofs_cr', 'ofs_pct',
    'sub_total_x',
    'listing_open', 'listing_high', 'listing_low', 'listing_close',
    'promoter_pre_shares', 'promoter_post_shares', 'objects_of_issue', 'detail_url',
    'face_value', 'kpi_pe_pre_ipo', 'kpi_market_cap_post_ipo', 'kpi_roe_pre_ipo',
    'kpi_roce_pre_ipo', 'issue_expenses_cr'
]

def _num(s):
    if not s:
        return None
    m = re.search(r'-?[\d,]+(?:\.\d+)?', str(s).replace(',', ''))
    return m.group() if m else None

def _cr_from_text(s):
    """Extract '₹ 66 Cr' style amount → 66."""
    if not s:
        return None
    m = re.search(r'₹?\s*([\d,]+(?:\.\d+)?)\s*Cr', s)
    return m.group(1).replace(',', '') if m else None


def _ofs_from_kv(kv):
    """CG-1 fix: return (ofs_cr, ofs_pct) ONLY from source-published 'Offer for Sale' field.

    Never derives ofs_cr from (total - fresh): that derivation belongs in the assembly step and must be
    stamped 'derived'. Returns (None, None) when the source has no OFS field, so the caller writes None
    rather than a fabricated 0.
    Pure function — no network, no side-effects; testable offline.
    """
    total_cr = _cr_from_text(kv.get('Total Issue Size', ''))
    ofs_raw = _cr_from_text(kv.get('Offer for Sale', ''))
    if ofs_raw is None:
        return None, None
    ofs_pct = None
    if total_cr is not None:
        try:
            t = float(total_cr)
            if t > 0:
                ofs_pct = f'{float(ofs_raw) / t * 100:.1f}'
        except ValueError:
            pass
    return ofs_raw, ofs_pct


def scrape_detail(scraper, row):
    rec = {c: None for c in DETAIL_COLS}
    rec.update({'chittorgarh_id': row.get('chittorgarh_id'), 'isin': row.get('isin'),
                'company_name': row.get('company_name'), 'type': row.get('type'),
                'detail_url': row.get('detail_url')})
    url = row.get('detail_url')
    if not url:
        # CG-2: distinguish no-URL from a fetch failure
        rec['fetch_status'] = 'no_url'
        return rec
    r = scraper.get(url, headers={'Referer': 'https://www.chittorgarh.com/'}, timeout=25)
    if r.status_code != 200:
        rec['fetch_status'] = f'http_{r.status_code}'
        return rec
    # Save raw HTML before parsing
    cid = row.get('chittorgarh_id') or 'unknown'
    ingest.save_raw('chittorgarh', f'{cid}.html', r.text)
    rec['fetch_status'] = 'ok'
    soup = BeautifulSoup(r.text, 'lxml')
    tables = soup.find_all('table')

    # Build a label→value map from all 2-col key-value rows
    kv = {}
    for t in tables:
        for tr in t.find_all('tr'):
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
            if len(cells) == 2 and cells[0]:
                kv.setdefault(cells[0].strip(), cells[1].strip())

    # Issue size / fresh / OFS (CG-1: only publish what the source says; no derivation here)
    total_cr = _cr_from_text(kv.get('Total Issue Size', ''))
    fresh_cr = _cr_from_text(kv.get('Fresh Issue', '')) or _cr_from_text(kv.get('Fresh Issue (Ex Market Maker)', ''))
    ofs_cr, ofs_pct = _ofs_from_kv(kv)
    rec['issue_size_cr'] = total_cr
    rec['fresh_issue_cr'] = fresh_cr
    rec['ofs_cr'] = ofs_cr
    rec['ofs_pct'] = ofs_pct

    rec['promoter_pre_shares']  = _num(kv.get('Share Holding Pre Issue', ''))
    rec['promoter_post_shares'] = _num(kv.get('Share Holding Post Issue', ''))
    rec['anchor_allocation_cr'] = _num(kv.get('Anchor Portion (₹ Cr.)', ''))
    
    # New KPIs
    for k, v in kv.items():
        k_low = k.lower()
        if 'face value' in k_low: rec['face_value'] = rec['face_value'] or _num(v)
        if 'p/e (x)' in k_low: rec['kpi_pe_pre_ipo'] = rec['kpi_pe_pre_ipo'] or _num(v)
        if 'market cap' in k_low: rec['kpi_market_cap_post_ipo'] = rec['kpi_market_cap_post_ipo'] or _num(v)
        if 'roe' in k_low: rec['kpi_roe_pre_ipo'] = rec['kpi_roe_pre_ipo'] or _num(v)
        if 'roce' in k_low: rec['kpi_roce_pre_ipo'] = rec['kpi_roce_pre_ipo'] or _num(v)
        if 'issue expenses' in k_low: rec['issue_expenses_cr'] = rec['issue_expenses_cr'] or _num(v)

    # Market maker — from "Reserved for Market Maker" row (firm name after the amount)
    mm = kv.get('Reserved for Market Maker', '')
    if mm:
        m = re.search(r'Cr\)\s*(.+)$', mm)
        rec['market_maker'] = m.group(1).strip() if m else None
    if not rec['market_maker']:
        mt = re.search(r'Market Maker of the company is\s+(.+?)\s*\.', soup.get_text(' ', strip=True))
        if mt:
            rec['market_maker'] = mt.group(1).strip()

    # Subscription total + Listing-day OHLC + objects: scan specific tables
    for t in tables:
        head = [c.get_text(strip=True) for c in t.find_all('tr')[0].find_all(['td', 'th'])] if t.find_all('tr') else []
        # Subscription status table
        if 'Subscription (times)' in head:
            for tr in t.find_all('tr'):
                cells = [c.get_text(' ', strip=True) for c in tr.find_all('td')]
                if cells and cells[0] == 'Total' and len(cells) >= 2:
                    rec['sub_total_x'] = _num(cells[1])
        # Listing day trading info (Price Details | BSE | NSE)
        if head[:1] == ['Price Details']:
            for tr in t.find_all('tr'):
                cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
                if len(cells) >= 2:
                    lbl = cells[0].lower()
                    val = _num(cells[1]) or (_num(cells[2]) if len(cells) > 2 else None)
                    if lbl == 'open':       rec['listing_open']  = rec['listing_open'] or val
                    elif lbl == 'high':     rec['listing_high']  = val
                    elif lbl == 'low':      rec['listing_low']   = val
                    elif lbl == 'last trade': rec['listing_close'] = val

    # Objects of the issue
    for t in tables:
        prev = t.find_previous(['h2', 'h3'])
        if prev and 'Objects of the Issue' in prev.get_text():
            objs = []
            for tr in t.find_all('tr')[1:]:
                cells = [c.get_text(' ', strip=True) for c in tr.find_all('td')]
                if len(cells) >= 2 and cells[1]:
                    objs.append(cells[1])
            rec['objects_of_issue'] = ' | '.join(objs) if objs else None
            break

    return rec


def run_detail_phase(workers):
    config.ensure(config.raw_dir('chittorgarh'))
    rows = list(csv.DictReader(open(URLS_CSV, encoding='utf-8'))) if os.path.exists(URLS_CSV) else []
    # Include rows without a detail_url so they get 'no_url' status
    log.info(f'Detail phase: {len(rows)} rows, {workers} workers')
    scraper = cloudscraper.create_scraper()
    out, lock, done = [], threading.Lock(), [0]

    def handle(row):
        try:
            rec = scrape_detail(scraper, row)
        except Exception as e:
            # CG-2: exception path → 'error_out', not all-None/indistinguishable
            rec = {c: None for c in DETAIL_COLS}
            rec.update({'chittorgarh_id': row.get('chittorgarh_id'), 'isin': row.get('isin'),
                        'company_name': row.get('company_name'), 'fetch_status': 'error_out'})
            log.warning(f'  ERR {row.get("company_name","")[:30]}: {str(e)[:50]}')
        with lock:
            out.append(rec); done[0] += 1
            if done[0] % 50 == 0:
                log.info(f'  {done[0]}/{len(rows)}')
        time.sleep(RATE)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(handle, rows))

    with open(DETAILS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=DETAIL_COLS, extrasaction='ignore')
        w.writeheader(); w.writerows(out)
    mm = sum(1 for r in out if r.get('market_maker'))
    lo = sum(1 for r in out if r.get('listing_high'))
    log.info(f'Written {len(out)} → {DETAILS_CSV}  (market_maker={mm}, listing_ohlc={lo})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['list', 'detail'], required=True)
    ap.add_argument('--years', default='2020-2025')
    ap.add_argument('--workers', type=int, default=6)
    args = ap.parse_args()

    setup_logging()
    a, b = args.years.split('-')
    years = list(range(int(a), int(b) + 1))

    if args.phase == 'list':
        log.info(f'=== Chittorgarh list phase  years={years} ===')
        run_list_phase(years)
    else:
        log.info(f'=== Chittorgarh detail phase  workers={args.workers} ===')
        run_detail_phase(args.workers)
    log.info('=== Done ===')


if __name__ == '__main__':
    main()
