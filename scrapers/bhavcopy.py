"""
Bhavcopy fetch and parse helpers for NSE/BSE daily OHLC data.

Handles both old and new formats:
  - NSE old   (listing < 2024-07-08): cm<DD><MON><YYYY>bhav.csv.zip — cols SYMBOL,OPEN
  - NSE UDiFF (>= 2024-07-08):         BhavCopy_NSE_CM_..._YYYYMMDD_F_0000.csv.zip — ISIN,OpnPric
  - BSE UDiFF (all dates):             BhavCopy_BSE_CM_..._YYYYMMDD_F_0000.CSV — ISIN,OpnPric

Usage:
    from scrapers.bhavcopy import first_day_open, get_bhavcopy
    price = first_day_open('INFY', '2023-10-27')
    lookup = get_bhavcopy('NSE', datetime(2023, 10, 27))
"""

import csv
import io
import logging
import os
import sys
import warnings
import zipfile
from datetime import datetime, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOLERANCE = 10.0
NSE_UDIFF_CUTOVER = datetime(2024, 7, 8)   # NSE switched to UDiFF format here

MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
     'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.9'}

log = logging.getLogger(__name__)


# ── Bhavcopy fetch + parse → {isin: open, 'SYM:'+symbol: open} ─────────────────

def _cache_path(exchange, d):
    return config.reference_dir() / 'bhavcopy' / f'{exchange}_{d.strftime("%Y%m%d")}.csv'


def fetch_nse(d):
    """Return (text, status) for NSE bhavcopy on date d.

    status is one of:
      'ok'          — got real data
      'holiday'     — HTTP 404; confirmed no file (market closed)
      'fetch_error' — transient/network/blocked error; do not cache
    """
    if d >= NSE_UDIFF_CUTOVER:
        url = f'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d.strftime("%Y%m%d")}_F_0000.csv.zip'
    else:
        url = (f'https://archives.nseindia.com/content/historical/EQUITIES/'
               f'{d.year}/{MON[d.month-1]}/cm{d.strftime("%d")}{MON[d.month-1]}{d.year}bhav.csv.zip')
    try:
        r = requests.get(url, headers={**H, 'Referer': 'https://www.nseindia.com/'}, timeout=30)
        if r.status_code == 200 and r.content[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(r.content))
            return z.read(z.namelist()[0]).decode(), 'ok'
        if r.status_code == 404:
            return None, 'holiday'
        log.debug(f'NSE fetch {d.date()} HTTP {r.status_code}')
        return None, 'fetch_error'
    except Exception as e:
        log.debug(f'NSE fetch {d.date()} err {e}')
        return None, 'fetch_error'


def fetch_bse(d):
    """Return (text, status) for BSE bhavcopy on date d.

    status is one of:
      'ok'          — got real data
      'holiday'     — HTTP 404; confirmed no file (market closed)
      'fetch_error' — transient/network/blocked error; do not cache
    """
    url = f'https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{d.strftime("%Y%m%d")}_F_0000.CSV'
    try:
        r = requests.get(url, headers={**H, 'Referer': 'https://www.bseindia.com/'}, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000 and b',' in r.content[:200]:
            return r.text, 'ok'
        if r.status_code == 404:
            return None, 'holiday'
        log.debug(f'BSE fetch {d.date()} HTTP {r.status_code}')
        return None, 'fetch_error'
    except Exception as e:
        log.debug(f'BSE fetch {d.date()} err {e}')
        return None, 'fetch_error'


def parse_bhavcopy(text, exchange, d):
    """Return {key: open_price}. Keys: ISIN and 'SYM:'+symbol.

    Equity-series only + first-hit wins (same policy as bhavcopy_ohlc.parse_day):
    a symbol can appear in multiple series (EQ + BL block deals, etc.) and the old
    code let the LAST row overwrite — a BL row could silently replace the real EQ
    open. (Found by the showdown test suite, 2026-06-04.)"""
    out = {}
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return out
    cols = rows[0].keys()
    if 'TckrSymb' in cols:        # UDiFF (NSE new + BSE)
        for r in rows:
            ser = (r.get('SctySrs') or '').strip().upper()
            if ser and ser not in ('EQ', 'BE', 'SM', 'ST'):
                continue
            op = r.get('OpnPric', '').strip()
            if not op:
                continue
            isin = r.get('ISIN', '').strip()
            if isin and isin not in out:
                out[isin] = op
            sym = r.get('TckrSymb', '').strip()
            if sym and ('SYM:' + sym) not in out:
                out['SYM:' + sym] = op
    elif 'SYMBOL' in cols:        # NSE old
        for r in rows:
            ser = (r.get('SERIES') or '').strip().upper()
            if ser and ser not in ('EQ', 'BE', 'SM', 'ST'):
                continue
            op = r.get('OPEN', '').strip()
            sym = r.get('SYMBOL', '').strip()
            if sym and op and ('SYM:' + sym) not in out:
                out['SYM:' + sym] = op
    return out


def get_bhavcopy(exchange, d):
    """Cached fetch+parse. Returns {key: open} or {} if unavailable.

    Cache behaviour:
      - 'ok'          rows written with status='ok'; old files with no status column treated as 'ok'.
      - 'holiday'     sentinel row written (key='', open='', status='holiday'); returns {}.
      - 'fetch_error' nothing written; next run will retry.

    Args:
        exchange: 'NSE' or 'BSE'
        d: datetime.date or datetime object

    Returns:
        Dict mapping ISIN or 'SYM:'+symbol to opening price string.
    """
    cp = _cache_path(exchange, d)

    # ── read cache if present ──────────────────────────────────────────────────
    if os.path.exists(cp):
        with open(cp, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        if rows:
            has_status = 'status' in rows[0]
            if has_status:
                # Holiday sentinel: single row with empty key and status='holiday'
                if rows[0].get('status') == 'holiday' and rows[0].get('key') == '':
                    return {}
                return {row['key']: row['open'] for row in rows
                        if row.get('status', 'ok') == 'ok' and row.get('key')}
            else:
                # Backward compat: old cache files have only key,open — treat as 'ok'
                return {row['key']: row['open'] for row in rows if row.get('key')}
        # Empty file (zero data rows after header) — treat as cache miss so we retry
        # (this handles the poisoned-empty-file case from the old bug)

    # ── fetch ─────────────────────────────────────────────────────────────────
    text, status = fetch_nse(d) if exchange == 'NSE' else fetch_bse(d)

    if status == 'fetch_error':
        log.warning(f'bhavcopy {exchange} {d.date()}: transient/blocked fetch error — not caching, will retry next run')
        return {}

    cache_dir = config.reference_dir() / 'bhavcopy'
    os.makedirs(cache_dir, exist_ok=True)

    if status == 'holiday':
        # Write a sentinel so we don't re-fetch confirmed holidays
        with open(cp, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['key', 'open', 'status'])
            w.writeheader()
            w.writerow({'key': '', 'open': '', 'status': 'holiday'})
        return {}

    # status == 'ok'
    raw_name = f'{exchange}_{d.strftime("%Y%m%d")}.csv'
    ingest.save_raw('bhavcopy', raw_name, text)

    lookup = parse_bhavcopy(text, exchange, d)

    with open(cp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['key', 'open', 'status'])
        w.writeheader()
        for k, v in lookup.items():
            w.writerow({'key': k, 'open': v, 'status': 'ok'})

    return lookup


# ── Verification helper ────────────────────────────────────────────────────────

FWD_DAYS = 16   # forward search window — our listing_date can be several days early


def first_day_open(ticker, listing_date):
    """
    Find ticker's first trading day open price in bhavcopy, searching forward
    from listing_date (which can be days before actual first trade).

    Args:
        ticker: NSE symbol, BSE code, or ISIN.
        listing_date: str 'YYYY-MM-DD' or datetime object.

    Returns:
        First found opening price (str) or None if not found within window.
    """
    if isinstance(listing_date, str):
        base = datetime.strptime(listing_date.strip(), '%Y-%m-%d')
    else:
        base = listing_date

    ticker = (ticker or '').strip().upper()
    if not ticker:
        return None

    # Try both exchanges
    for exch in ['NSE', 'BSE']:
        for off in range(FWD_DAYS):
            d = base + timedelta(days=off)
            if d.weekday() >= 5:        # skip weekends
                continue
            lookup = get_bhavcopy(exch, d)
            # Try ISIN key first, then symbol key
            op = lookup.get(ticker) or lookup.get('SYM:' + ticker)
            if op is not None:
                return op
    return None
