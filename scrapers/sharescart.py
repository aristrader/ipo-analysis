"""
scrapers/sharescart.py

Two-phase scraper for Sharescart IPO data.

Usage:
    python scrapers/sharescart.py --phase list
    python scrapers/sharescart.py --phase detail [--limit N] [--workers N]
    python scrapers/sharescart.py --phase all    [--workers N]

    --limit N    Only scrape first N rows per type (test run)
    --workers N  Parallel detail workers (default 1, max 3 recommended)
                 3 workers ≈ 3x speedup, ~5 min for full 939 run

Logs: written to logs/scraper_TIMESTAMP.log
      Terminal shows progress only; full request details in the log file.
"""

import argparse
import concurrent.futures
import csv
import logging
import os
import re
import threading
import time
import traceback
from datetime import datetime

# One session per worker thread — reused across all IPOs that thread processes
_thread_local = threading.local()

def get_thread_session():
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = make_session()
    return _thread_local.session

import requests
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys as _sys
_sys.path.insert(0, BASE_DIR)
from foundation import config, ingest

LOGS_DIR   = str(config.logs_dir())
MB_URLS    = str(config.raw_dir('sharescart') / 'mb_urls.csv')
SME_URLS   = str(config.raw_dir('sharescart') / 'sme_urls.csv')
MB_EVENTS  = str(config.raw_dir('sharescart') / 'mainboard_events.csv')
SME_EVENTS = str(config.raw_dir('sharescart') / 'sme_events.csv')

API_URL    = 'https://www.sharescart.com/web-services/ipo-stocks-intermediary.php'
YEARS      = [2023, 2024, 2025]
RATE_LIMIT = 0.5   # seconds between requests per worker
# Rate probe result (2026-05-30): no blocking detected even at 0.1s delay over 8 requests.
# Actual request RTT is ~0.15s. Using 0.5s as a conservative buffer.
# With --workers 2: ~4 req/s total. With --workers 3: ~6 req/s.
# If you see 403s or small response sizes in the log, increase this.

# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging():
    config.ensure(config.logs_dir())
    log_file = str(config.logs_dir() / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    fmt = '%(asctime)s [%(levelname)-7s] %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))

    # Terminal: only INFO and above (key progress + errors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
    log = logging.getLogger(__name__)
    log.info(f'Log file: {log_file}')
    return log

log = logging.getLogger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA_COLS = [
    # Identity
    'company_name', 'type', 'exchange', 'industry', 'incorporation_year',
    'age_at_ipo_years', 'sharescart_url', 'ticker_ns', 'ticker_bo',
    # IPO Basics
    'issue_price', 'price_band_low', 'price_band_width_pct', 'book_built',
    'lot_size_shares', 'min_investment_rs', 'issue_size_cr',
    # Timetable
    'open_date', 'close_date', 'listing_date',
    # Subscription
    'sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x',
    'sub_qib_cr', 'sub_nii_cr', 'sub_retail_cr', 'sub_total_cr',
    # GMP
    'gmp_pct',
    # Listing (high/low/close filled by Layer 2)
    'listing_open', 'listing_gain_pct', 'listing_high', 'listing_low', 'listing_close',
    # Promoter
    'promoter_pre_issue_pct', 'promoter_post_issue_pct',
    # Lead / market maker
    'lead_manager', 'market_maker',
    # Objectives
    'objectives_of_issue',
    # TTM snapshot
    'pe_ratio', 'pat_ttm_cr', 'sales_ttm_cr', 'eps_ttm',
    # Financials 3yr — yr3 = most recent full year in DRHP
    'fin_year_yr3', 'fin_year_yr2', 'fin_year_yr1',
    'net_sales_yr3', 'net_sales_yr2', 'net_sales_yr1',
    'operating_profit_yr3', 'operating_profit_yr2', 'operating_profit_yr1',
    'pat_yr3', 'pat_yr2', 'pat_yr1',
    'eps_yr3', 'eps_yr2', 'eps_yr1',
    # Balance sheet
    'shareholder_funds_yr3', 'shareholder_funds_yr2', 'shareholder_funds_yr1',
    'borrowings_yr3', 'borrowings_yr2', 'borrowings_yr1',
    'total_current_liabilities_yr3', 'total_current_liabilities_yr2', 'total_current_liabilities_yr1',
    'total_liabilities_yr3', 'total_liabilities_yr2', 'total_liabilities_yr1',
    'fixed_assets_yr3', 'fixed_assets_yr2', 'fixed_assets_yr1',
    'total_current_assets_yr3', 'total_current_assets_yr2', 'total_current_assets_yr1',
    'total_assets_yr3', 'total_assets_yr2', 'total_assets_yr1',
    # Cash flow
    'operating_cf_yr3', 'operating_cf_yr2', 'operating_cf_yr1',
    'investing_cf_yr3', 'investing_cf_yr2', 'investing_cf_yr1',
    'financing_cf_yr3', 'financing_cf_yr2', 'financing_cf_yr1',
    'closing_cash_yr3', 'closing_cash_yr2', 'closing_cash_yr1',
    # Ratios
    'ebitda_margin_pct', 'ebit_margin_pct', 'pat_margin_pct', 'cash_profit_margin_pct',
    'roa_pct', 'roe_pct', 'roce_pct',
    'receivable_days', 'inventory_days', 'payable_days',
    'price_to_book', 'ev_sales', 'ev_ebitda',
    'debt_equity', 'current_ratio', 'quick_ratio', 'interest_cover',
    # Per-share & market ratios (yr3 only)
    'book_nav_per_share', 'ceps', 'total_debt_mcap',
    # Growth
    'sales_cagr_1y', 'sales_cagr_3y', 'sales_cagr_5y',
    'operating_profit_cagr_1y', 'operating_profit_cagr_3y',
    'pat_cagr_1y', 'pat_cagr_3y',
    'roe_avg', 'roce_avg',
]

URL_COLS = [
    'company_name', 'type', 'exchange', 'sharescart_url',
    'open_date', 'close_date', 'issue_price', 'min_investment_rs',
    'listing_open', 'listing_gain_pct',
]

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def make_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.sharescart.com/ipo/',
    })
    t0 = time.time()
    r = s.get('https://www.sharescart.com/ipo/', timeout=15)
    log.debug(f'SESSION INIT  GET https://www.sharescart.com/ipo/ → {r.status_code} ({len(r.content):,}B) {time.time()-t0:.2f}s')
    return s


def _get(session, url, retries=3, backoff=2.0):
    """GET with retry + request/response logging."""
    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            r = session.get(url, timeout=20)
            elapsed = time.time() - t0
            log.debug(f'GET  {url} → {r.status_code} ({len(r.content):,}B) {elapsed:.2f}s  attempt={attempt}')
            if r.status_code == 200:
                return r
            log.warning(f'Non-200 status {r.status_code} for {url}  attempt={attempt}')
        except Exception as e:
            elapsed = time.time() - t0
            log.warning(f'GET  {url} → ERROR after {elapsed:.2f}s  attempt={attempt}: {e}')
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise RuntimeError(f'Failed to fetch {url} after {retries} attempts')


def _post(session, url, data, retries=3, backoff=2.0):
    """POST with retry + request/response logging."""
    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            r = session.post(url, data=data,
                             headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=15)
            elapsed = time.time() - t0
            log.debug(f'POST {url} data={data} → {r.status_code} ({len(r.content):,}B) {elapsed:.2f}s  attempt={attempt}')
            if r.status_code == 200:
                return r
            log.warning(f'Non-200 status {r.status_code} for POST {url}  attempt={attempt}')
        except Exception as e:
            elapsed = time.time() - t0
            log.warning(f'POST {url} → ERROR after {elapsed:.2f}s  attempt={attempt}: {e}')
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise RuntimeError(f'Failed to POST {url} after {retries} attempts')

# ── Parse helpers ─────────────────────────────────────────────────────────────

def clean(text):
    if text is None:
        return None
    t = re.sub(r'[\xa0​]', ' ', str(text))
    t = re.sub(r'\s+', ' ', t).strip()
    return t if t else None


def parse_num(text):
    if not text:
        return None
    text = re.sub(r'[,\s]', '', str(text))
    m = re.search(r'-?[\d]+(?:\.[\d]+)?', text)
    return m.group() if m else None


def count_pages(pagination_html):
    nums = re.findall(r'data-pageno=(\d+)', pagination_html)
    return max(int(n) for n in nums) + 1 if nums else 1


def p_tag_value(block, label_substr):
    for p in block.find_all('p'):
        if label_substr.lower() in p.get_text().lower():
            span = p.find('span', class_='float-right')
            if span:
                return clean(span.get_text(strip=True))
    return None

# ── Phase 1: list ─────────────────────────────────────────────────────────────

def fetch_list_page(session, year, page_no):
    r = _post(session, API_URL, {
        'status': 'Listed', 'year[]': str(year), 'industry': '',
        'page_no': page_no, 'limit': 50, 'action': 'getipodataAccord',
    })
    return r.json()


def parse_list_rows(table_html):
    soup = BeautifulSoup(table_html, 'lxml')
    rows = []
    for tr in soup.find_all('tr'):
        cells = tr.find_all('td')
        if len(cells) < 11:
            continue
        a = cells[0].find('a', href=True)
        rows.append({
            'company_name':     clean(cells[0].get_text(strip=True)),
            'type':             clean(cells[10].get_text(strip=True)),
            'exchange':         clean(cells[11].get_text(strip=True)) if len(cells) > 11 else None,
            'sharescart_url':   a['href'] if a else '',
            'open_date':        clean(cells[2].get_text(strip=True)),
            'close_date':       clean(cells[3].get_text(strip=True)),
            'issue_price':      parse_num(cells[4].get_text(strip=True)),
            'min_investment_rs': parse_num(re.sub(r'[,\s]', '', cells[5].get_text(strip=True))),
            'listing_open':     parse_num(cells[6].get_text(strip=True)),
            'listing_gain_pct': parse_num(cells[7].get_text(strip=True)),
        })
    return rows


def run_list_phase(session):
    config.ensure(config.raw_dir('sharescart'))
    mb_rows, sme_rows = [], []

    for year in YEARS:
        log.info(f'  Fetching year {year}...')
        data = fetch_list_page(session, year, 0)
        pages = count_pages(data['pagination'])
        all_rows = parse_list_rows(data['table'])
        for page in range(1, pages):
            time.sleep(RATE_LIMIT)
            data = fetch_list_page(session, year, page)
            all_rows.extend(parse_list_rows(data['table']))
            log.info(f'    page {page+1}/{pages} — {len(all_rows)} rows so far')
        time.sleep(RATE_LIMIT)

        for row in all_rows:
            if row['type'] == 'Mainboard':
                mb_rows.append(row)
            elif row['type'] == 'SME':
                sme_rows.append(row)
        log.info(f'  Year {year} done: {sum(1 for r in all_rows if r["type"]=="Mainboard")} MB, {sum(1 for r in all_rows if r["type"]=="SME")} SME')

    _write_csv(MB_URLS, mb_rows, URL_COLS)
    _write_csv(SME_URLS, sme_rows, URL_COLS)
    log.info(f'  Written {len(mb_rows)} mainboard URLs → {MB_URLS}')
    log.info(f'  Written {len(sme_rows)} SME URLs      → {SME_URLS}')

# ── Phase 2: detail ───────────────────────────────────────────────────────────

def _book_built_fields(price_band_low, issue_price):
    """SC-1 fix: derive book_built and price_band_width_pct ONLY when price_band_low was found.

    Returns (book_built, price_band_width_pct) as strings, or (None, None) when the source had no
    price-band data — never fabricates 'False'/'0' as a hard default.
    Pure function — no network; testable offline.
    """
    if price_band_low is None or issue_price is None:
        return None, None
    try:
        low = float(price_band_low)
        high = float(issue_price)
    except (ValueError, TypeError):
        return None, None
    bb = str(low != high)
    width = f'{(high - low) / low * 100:.2f}' if low > 0 else None
    return bb, width


def scrape_detail(session, url, list_row):
    r = _get(session, url)
    # Save raw HTML before parsing
    slug = url.rstrip('/').rsplit('/', 1)[-1] or 'unknown'
    ingest.save_raw('sharescart', f'{slug}.html', r.text)
    soup = BeautifulSoup(r.text, 'lxml')
    rec = {col: None for col in SCHEMA_COLS}

    for col in URL_COLS:
        rec[col] = list_row.get(col)

    tables = soup.find_all('table')

    # ── Identity ──────────────────────────────────────────────────────────────
    h1 = soup.find('h1')
    if h1:
        rec['company_name'] = clean(h1.get_text(strip=True).replace(' IPO', '').strip())

    for el in soup.find_all(True):
        txt = el.get_text(strip=True)
        if txt.startswith('Inc. Year:'):
            rec['incorporation_year'] = parse_num(txt.replace('Inc. Year:', ''))
            break

    # ── Basic Info block ──────────────────────────────────────────────────────
    basic_block = None
    for h2 in soup.find_all('h2'):
        if h2.get_text(strip=True) == 'Basic Info':
            basic_block = h2.find_parent('div', class_='step-market-club-news')
            break

    if basic_block:
        rec['pe_ratio']     = parse_num(p_tag_value(basic_block, 'P/E'))
        rec['sales_ttm_cr'] = parse_num(p_tag_value(basic_block, 'Sales'))
        rec['pat_ttm_cr']   = parse_num(p_tag_value(basic_block, 'PAT'))
        rec['eps_ttm']      = parse_num(p_tag_value(basic_block, 'EPS'))
        exch = p_tag_value(basic_block, 'Exchange')
        if exch:
            rec['exchange'] = exch
        for p in basic_block.find_all('p'):
            txt = p.get_text(' ', strip=True)
            if re.search(r'\bPrice\b', txt) and 'to' in txt:
                nums = re.findall(r'[\d]+(?:\.[\d]+)?', txt)
                if len(nums) >= 2:
                    rec['price_band_low'] = nums[0]
                    if not rec['issue_price']:
                        rec['issue_price'] = nums[1]
                break
    else:
        log.warning(f'Basic Info block not found for {url}')

    # ── Issue size ────────────────────────────────────────────────────────────
    # Shows '--' for listed IPOs on Sharescart — will be null in those cases
    for el in soup.find_all('div', class_='stat-card'):
        lbl = el.find('small')
        val = el.find('span')
        if lbl and val and lbl.get_text(strip=True) == 'Issue Size':
            m = re.search(r'([\d.]+)', val.get_text(strip=True))
            if m:
                rec['issue_size_cr'] = m.group(1)
            break

    # ── Derived (SC-1 fix: only set when source had price-band data; never fabricate 'False'/'0') ──
    rec['book_built'], rec['price_band_width_pct'] = _book_built_fields(
        rec.get('price_band_low'), rec.get('issue_price')
    )

    # ── Timetable ─────────────────────────────────────────────────────────────
    timeline = soup.find('div', class_='ipo-timeline')
    if timeline:
        for row in timeline.find_all('div', class_='timeline-row'):
            title_el = row.find('span', class_='title')
            date_el  = row.find('span', class_='date')
            if not (title_el and date_el):
                continue
            title = title_el.get_text(strip=True)
            date  = clean(date_el.get_text(strip=True))
            if title == 'Opening Date':
                rec['open_date']   = rec['open_date'] or date
            elif title == 'Closing Date':
                rec['close_date']  = rec['close_date'] or date
            elif title == 'Listing Date':
                rec['listing_date'] = date
    else:
        log.warning(f'Timeline block not found for {url}')

    # ── age_at_ipo_years ──────────────────────────────────────────────────────
    if rec['incorporation_year'] and rec['listing_date']:
        listing_year = _parse_year(rec['listing_date'])
        if listing_year:
            rec['age_at_ipo_years'] = str(listing_year - int(rec['incorporation_year']))

    # ── Lot size ──────────────────────────────────────────────────────────────
    if tables:
        for row in tables[0].find_all('tr'):
            cells = [c.get_text(strip=True) for c in row.find_all('td')]
            if cells and cells[0] == 'Retail (Min)' and len(cells) >= 3:
                rec['lot_size_shares']   = parse_num(cells[2])
                rec['min_investment_rs'] = rec['min_investment_rs'] or parse_num(re.sub(r'[,\s]', '', cells[3]))
                break

    # ── Subscription ─────────────────────────────────────────────────────────
    if len(tables) > 1:
        issue_price_val = float(rec['issue_price']) if rec.get('issue_price') else None
        sub_shares = {}
        for row in tables[1].find_all('tr'):
            cells = [c.get_text(strip=True) for c in row.find_all('td')]
            if len(cells) < 4:
                continue
            cat    = cells[0]
            shares = parse_num(re.sub(r'[,\s]', '', cells[2]))
            bid_x  = cells[3].replace('x', '').strip()
            if cat == 'QIB':
                rec['sub_qib_x']     = parse_num(bid_x)
                sub_shares['qib']    = shares
            elif cat == 'NII':
                rec['sub_nii_x']     = parse_num(bid_x)
                sub_shares['nii']    = shares
            elif cat == 'Retail':
                rec['sub_retail_x']  = parse_num(bid_x)
                sub_shares['retail'] = shares
            elif cat == 'Total':
                rec['sub_total_x']   = parse_num(bid_x)
                sub_shares['total']  = shares
        if issue_price_val:
            for key, col in [('qib','sub_qib_cr'), ('nii','sub_nii_cr'),
                              ('retail','sub_retail_cr'), ('total','sub_total_cr')]:
                if sub_shares.get(key):
                    rec[col] = f'{float(sub_shares[key]) * issue_price_val / 1_00_00_000:.2f}'

    # ── GMP & Listing ─────────────────────────────────────────────────────────
    for p in soup.find_all('p'):
        txt  = p.get_text(strip=True)
        span = p.find('span', class_='float-right')
        val  = clean(span.get_text(strip=True)) if span else None
        if not val or val in ('--', '-- %'):
            continue
        if 'GMP %' in txt:
            rec['gmp_pct'] = parse_num(val.replace('%', ''))
        elif txt.startswith('Listing Price:'):
            rec['listing_open']     = rec['listing_open']     or parse_num(val)
        elif txt.startswith('Listing Gain:'):
            rec['listing_gain_pct'] = rec['listing_gain_pct'] or parse_num(val.replace('%', ''))

    # ── Promoter ──────────────────────────────────────────────────────────────
    for h2 in soup.find_all('h2'):
        if 'Promoter' in h2.get_text():
            block = h2.find_parent('div', class_='step-market-club-news')
            if block:
                for p in block.find_all('p'):
                    ptxt = p.get_text(' ', strip=True)
                    span = p.find('span', class_='float-right')
                    if not span:
                        continue
                    val = clean(span.get_text(strip=True)).replace('%', '')
                    if 'Pre Issue Share Holding' in ptxt:
                        rec['promoter_pre_issue_pct']  = parse_num(val)
                    elif 'Post Issue Share Holding' in ptxt:
                        rec['promoter_post_issue_pct'] = parse_num(val)
            break

    # ── Objectives ────────────────────────────────────────────────────────────
    for h2 in soup.find_all('h2'):
        if 'Objective' in h2.get_text():
            nxt = h2.find_next('p')
            if nxt:
                rec['objectives_of_issue'] = clean(nxt.get_text(strip=True))
            break

    # ── Lead Manager ─────────────────────────────────────────────────────────
    for h2 in soup.find_all('h2', string=re.compile(r'Lead Manager')):
        outer = h2.find_parent('div', class_=lambda c: c and 'info-box' in c)
        if outer:
            names = [
                clean(p.get_text(strip=True))
                for p in outer.find_all('p')
                if 'h5' not in (p.get('class') or []) and clean(p.get_text(strip=True))
            ]
            rec['lead_manager'] = ' | '.join(names) if names else None
        break

    # ── Financials ────────────────────────────────────────────────────────────
    if len(tables) > 2:
        _extract_pl(rec, tables[2])
    if len(tables) > 3:
        _extract_bs(rec, tables[3])
    if len(tables) > 4:
        _extract_cf(rec, tables[4])
    if len(tables) > 5:
        _extract_ratios(rec, tables[5])
    if len(tables) > 6:
        _extract_growth(rec, tables[6], tables[7] if len(tables) > 7 else None)

    # ── Log null summary ──────────────────────────────────────────────────────
    expected_null = {
        'ticker_ns', 'ticker_bo', 'market_maker', 'industry',
        'listing_high', 'listing_low', 'listing_close',
        'issue_size_cr', 'gmp_pct',
    }
    nulls = [c for c in SCHEMA_COLS if not rec.get(c) and c not in expected_null]
    if nulls:
        log.debug(f'  {rec["company_name"]}: unexpected nulls: {nulls}')

    return rec


# ── Financial extractors ──────────────────────────────────────────────────────

def _parse_year(date_str):
    if not date_str:
        return None
    m = re.search(r'\b(\d{4})\b', str(date_str))
    return int(m.group(1)) if m else None


def _table_to_dict(table):
    rows = {}
    for tr in table.find_all('tr'):
        cells = [c.get_text(strip=True) for c in tr.find_all(['th', 'td'])]
        if cells and cells[0] not in ('#', '#(Fig in Cr.)'):
            rows[cells[0]] = cells[1:]
    return rows


def _extract_pl(rec, table):
    headers = [th.get_text(strip=True) for th in table.find('tr').find_all(['th', 'td'])]
    rows = _table_to_dict(table)
    year_cols = [i for i, h in enumerate(headers) if re.match(r'\w+ \d{4}', h)]
    year_cols = year_cols[-3:]

    def get(label, offset):
        vals = rows.get(label, [])
        col = (year_cols[-(offset + 1)] - 1) if offset < len(year_cols) else None
        return parse_num(vals[col]) if col is not None and col < len(vals) else None

    year_labels = [headers[i] for i in year_cols]
    if len(year_labels) >= 1: rec['fin_year_yr3'] = year_labels[-1]
    if len(year_labels) >= 2: rec['fin_year_yr2'] = year_labels[-2]
    if len(year_labels) >= 3: rec['fin_year_yr1'] = year_labels[-3]

    for label, prefix in [('Net Sales', 'net_sales'), ('Operating Profit', 'operating_profit'),
                           ('Profit After Tax', 'pat'), ('Adjusted Earnings Per Share', 'eps')]:
        for i, sfx in enumerate(['yr3', 'yr2', 'yr1']):
            rec[f'{prefix}_{sfx}'] = get(label, i)


def _extract_bs(rec, table):
    headers = [th.get_text(strip=True) for th in table.find('tr').find_all(['th', 'td'])]
    rows = _table_to_dict(table)
    year_cols = [i for i, h in enumerate(headers) if re.match(r'\w+ \d{4}', h)]
    year_cols = year_cols[-3:]

    def get(label, offset):
        vals = rows.get(label, [])
        col = (year_cols[-(offset + 1)] - 1) if offset < len(year_cols) else None
        return parse_num(vals[col]) if col is not None and col < len(vals) else None

    for label, prefix in [
        ("Shareholder's Funds", 'shareholder_funds'), ('Borrowings', 'borrowings'),
        ('Total Current Liabilities', 'total_current_liabilities'),
        ('Total Liabilities', 'total_liabilities'), ('Fixed Assets', 'fixed_assets'),
        ('Total Current Assets', 'total_current_assets'), ('Total Assets', 'total_assets'),
    ]:
        for i, sfx in enumerate(['yr3', 'yr2', 'yr1']):
            rec[f'{prefix}_{sfx}'] = get(label, i)


def _extract_cf(rec, table):
    headers = [th.get_text(strip=True) for th in table.find('tr').find_all(['th', 'td'])]
    rows = _table_to_dict(table)
    year_cols = [i for i, h in enumerate(headers) if re.match(r'\w+ \d{4}', h)]
    year_cols = year_cols[-3:]

    def get(label, offset):
        vals = rows.get(label, [])
        col = (year_cols[-(offset + 1)] - 1) if offset < len(year_cols) else None
        return parse_num(vals[col]) if col is not None and col < len(vals) else None

    for label, prefix in [
        ('Cash Flow from Operating Activities', 'operating_cf'),
        ('Cash Flow from Investing Activities', 'investing_cf'),
        ('Cash Flow from Financing Activities', 'financing_cf'),
        ('Closing Cash & Cash Equivalent', 'closing_cash'),
    ]:
        for i, sfx in enumerate(['yr3', 'yr2', 'yr1']):
            rec[f'{prefix}_{sfx}'] = get(label, i)


def _extract_ratios(rec, table):
    headers = [th.get_text(strip=True) for th in table.find('tr').find_all(['th', 'td'])]
    rows = _table_to_dict(table)
    year_cols = [i for i, h in enumerate(headers) if re.match(r'\w+ \d{4}', h)]
    if not year_cols:
        return
    yr3_col = year_cols[-1] - 1

    def get(label):
        vals = rows.get(label, [])
        return parse_num(vals[yr3_col]) if yr3_col < len(vals) else None

    rec['ebitda_margin_pct']      = get('Core EBITDA Margin(%)')
    rec['ebit_margin_pct']        = get('EBIT Margin(%)')
    rec['pat_margin_pct']         = get('PAT Margin (%)')
    rec['cash_profit_margin_pct'] = get('Cash Profit Margin (%)')
    rec['roa_pct']                = get('ROA(%)')
    rec['roe_pct']                = get('ROE(%)')
    rec['roce_pct']               = get('ROCE(%)')
    rec['receivable_days']        = get('Receivable days')
    rec['inventory_days']         = get('Inventory Days')
    rec['payable_days']           = get('Payable days')
    rec['price_to_book']          = get('Price/Book(x)')
    rec['ev_sales']               = get('EV/Net Sales(x)')
    rec['ev_ebitda']              = get('EV/Core EBITDA(x)')
    rec['debt_equity']            = get('Debt/Equity(x)')
    rec['current_ratio']          = get('Current Ratio(x)')
    rec['quick_ratio']            = get('Quick Ratio(x)')
    rec['interest_cover']         = get('Interest Cover(x)')
    rec['book_nav_per_share']     = get('Book NAV/Share(Rs)')
    rec['ceps']                   = get('CEPS(Rs)')
    rec['total_debt_mcap']        = get('Total Debt/Mcap(x)')


def _extract_growth(rec, growth_table, avg_table):
    rows = _table_to_dict(growth_table)

    def g(label, idx):
        vals = rows.get(label, [])
        return parse_num(vals[idx].replace('%', '')) if idx < len(vals) else None

    rec['sales_cagr_1y']            = g('Sales CAGR', 0)
    rec['sales_cagr_3y']            = g('Sales CAGR', 1)
    rec['sales_cagr_5y']            = g('Sales CAGR', 2)
    rec['operating_profit_cagr_1y'] = g('Operating Profit CAGR', 0)
    rec['operating_profit_cagr_3y'] = g('Operating Profit CAGR', 1)
    rec['pat_cagr_1y']              = g('PAT CAGR', 0)
    rec['pat_cagr_3y']              = g('PAT CAGR', 1)

    if avg_table:
        avg_rows = _table_to_dict(avg_table)

        def av(label, idx):
            vals = avg_rows.get(label, [])
            return parse_num(vals[idx].replace('%', '')) if idx < len(vals) else None

        rec['roe_avg']  = av('ROE Average', 0)
        rec['roce_avg'] = av('ROCE Average', 0)

# ── CSV helpers ───────────────────────────────────────────────────────────────

def _write_csv(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# ── Phase 2 runner ────────────────────────────────────────────────────────────

def run_detail_phase(limit=None, workers=1):
    config.ensure(config.raw_dir('sharescart'))

    for path in [MB_EVENTS, SME_EVENTS]:
        if os.path.exists(path):
            os.remove(path)

    for url_file, events_file, label in [
        (MB_URLS,  MB_EVENTS,  'Mainboard'),
        (SME_URLS, SME_EVENTS, 'SME'),
    ]:
        rows = _read_csv(url_file)
        if not rows:
            log.warning(f'No URLs in {url_file} — run list phase first.')
            continue
        if limit:
            rows = rows[:limit]

        total = len(rows)
        mode  = f'TEST limit={limit}' if limit else 'FULL'
        log.info(f'Scraping {total} {label} pages  workers={workers}  [{mode}]')

        # Thread-safe counters and CSV lock
        ok_count    = [0]
        err_count   = [0]
        csv_lock    = threading.Lock()
        counter_lock = threading.Lock()
        t_start     = time.time()

        # Track per-worker progress for ETA
        processed = [0]

        def scrape_one(args):
            idx, list_row = args
            url = list_row.get('sharescart_url', '')
            if not url:
                return
            session = get_thread_session()   # reused per worker thread
            try:
                t0 = time.time()
                rec = scrape_detail(session, url, list_row)
                elapsed = time.time() - t0
                with csv_lock:
                    file_exists = os.path.exists(events_file)
                    with open(events_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=SCHEMA_COLS, extrasaction='ignore')
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(rec)
                with counter_lock:
                    ok_count[0] += 1
                    processed[0] += 1
                    done = processed[0]
                    elapsed_total = time.time() - t_start
                    rps  = done / elapsed_total if elapsed_total > 0 else 0
                    eta  = (total - done) / rps if rps > 0 else 0
                log.info(f'  [{done:4}/{total}] ✓  {rec["company_name"][:45]}  ({elapsed:.1f}s)  ETA {eta/60:.1f}m')
                log.debug(f'  Scraped {url} in {elapsed:.2f}s')
            except Exception as e:
                with counter_lock:
                    err_count[0] += 1
                    processed[0] += 1
                log.error(f'  [{idx:4}/{total}] ✗  FAILED {url}\n{traceback.format_exc()}')
            finally:
                time.sleep(RATE_LIMIT)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            executor.map(scrape_one, enumerate(rows, 1))

        elapsed_total = time.time() - t_start
        log.info(f'{label} done: {ok_count[0]} ok, {err_count[0]} errors  '
                 f'total time {elapsed_total/60:.1f}m  avg {elapsed_total/total:.1f}s/IPO')

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Sharescart IPO scraper')
    parser.add_argument('--phase',   choices=['list', 'detail', 'all'], required=True)
    parser.add_argument('--limit',   type=int, default=None,
                        help='Scrape only first N rows per type (test mode)')
    parser.add_argument('--workers', type=int, default=1,
                        help='Parallel detail workers (default 1, max 3 recommended)')
    args = parser.parse_args()

    setup_logging()
    log.info(f'=== Sharescart scraper started  phase={args.phase}  '
             f'workers={args.workers}  limit={args.limit} ===')
    t0 = time.time()

    if args.phase in ('list', 'all'):
        log.info('Phase 1: collecting IPO URLs...')
        session = make_session()
        run_list_phase(session)

    if args.phase in ('detail', 'all'):
        log.info('Phase 2: scraping detail pages...')
        run_detail_phase(limit=args.limit, workers=args.workers)

    log.info(f'=== Done  total time {(time.time()-t0)/60:.1f}m ===')


if __name__ == '__main__':
    main()
