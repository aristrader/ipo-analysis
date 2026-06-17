"""
Daily OHLCV price puller (Layer 2) — per-ISIN daily open/high/low/close/volume.

Builds per-ISIN price series for our IPO universe from official bhavcopy files.
Model: ONE file per trading day per exchange holds ALL stocks; we download each
day once, extract the rows for our universe (by ISIN where present, else by
symbol via our symbol<->ISIN map), and append to per-ISIN CSV series.

This is a SEPARATE module from scrapers/bhavcopy.py (which stores OPEN only and
is used elsewhere). It reuses the URL/format knowledge but parses full OHLCV.

Source formats (all validated):
  - NSE old   (< 2024-07-08): archives.nseindia.com .../cm<DD><MON><YYYY>bhav.csv.zip
        cols SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,...,TOTTRDQTY,...,TIMESTAMP   (NO ISIN -> match by SYMBOL)
  - NSE UDiFF (>= 2024-07-08): nsearchives .../BhavCopy_NSE_CM_0_0_0_<YYYYMMDD>_F_0000.csv.zip
        cols ISIN,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol  (has ISIN)
  - BSE UDiFF (>= 2024):       bseindia .../BhavCopy_BSE_CM_0_0_0_<YYYYMMDD>_F_0000.CSV
        same UDiFF cols (has ISIN)
  - BSE legacy(~2017 .. 2023): bseindia .../EQ_ISINCODE_<DDMMYY>.zip
        cols SC_CODE,...,OPEN,HIGH,LOW,CLOSE,...,NO_OF_SHRS,...,ISIN_CODE     (has ISIN)

Output: data/prices/<isin>.csv  with header  date,open,high,low,close,volume
Manifest: data/prices/_days_done.csv  (exchange,date) — resume-safe.
Progress log: logs/prices.log

Usage:
    # build the universe symbol/isin map and run a date window:
    PYTHONPATH=. .venv/bin/python3 -m scrapers.bhavcopy_ohlc \
        --start 2024-12-20 --end 2024-12-31
    PYTHONPATH=. .venv/bin/python3 -m scrapers.bhavcopy_ohlc \
        --start 2006-01-01 --end 2026-05-31          # full pull (resumable)
"""

import argparse
import csv
import io
import logging
import os
import sys
import time
import warnings
import zipfile
from datetime import datetime, timedelta

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DIR = os.path.join(BASE_DIR, 'data', 'master')

# Output paths from config (under OUTPUT_ROOT)
def _prices_dir():
    return config.prices_dir()

def _log_dir():
    return config.logs_dir()

def _manifest():
    return config.prices_dir() / '_days_done.csv'

MASTER_FILES = ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']

NSE_UDIFF_CUTOVER = datetime(2024, 7, 8)
# Earliest reliably-available BSE legacy ISINCODE bhavcopy. Pre-2017 returns HTML
# error pages. NSE old format covers everything back to 2006 for matching.
BSE_LEGACY_START = datetime(2017, 1, 1)

MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
     'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.9'}

log = logging.getLogger('bhavcopy_ohlc')


# ── universe ─────────────────────────────────────────────────────────────────

def load_universe():
    """Return (isin_set, sym2isin) for our ~2300-ISIN universe.

    isin_set:  set of all ISINs we care about.
    sym2isin:  {NSE_SYMBOL(upper): isin}  — used to match NSE old (no-ISIN) rows.
    """
    isin_set = set()
    sym2isin = {}
    for name in MASTER_FILES:
        path = os.path.join(MASTER_DIR, f'{name}.csv')
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                isin = (r.get('isin') or '').strip().upper()
                sym = (r.get('nse_symbol') or '').strip().upper()
                if not isin:
                    continue
                isin_set.add(isin)
                if sym and sym not in sym2isin:
                    sym2isin[sym] = isin
    return isin_set, sym2isin


# ── fetch one day's raw bhavcopy text ────────────────────────────────────────

def _get_zip_text(url, referer):
    try:
        r = requests.get(url, headers={**H, 'Referer': referer}, timeout=40)
        if r.status_code == 200 and r.content[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(r.content))
            return z.read(z.namelist()[0]).decode('utf-8', 'replace')
    except Exception as e:
        log.debug(f'zip fetch err {url}: {e}')
    return None


def fetch_nse(d):
    """Raw NSE bhavcopy CSV text for date d, and a fetch_ok flag.

    Returns (text, True) on success, (None, False) on any failure.
    """
    if d >= NSE_UDIFF_CUTOVER:
        url = ('https://nsearchives.nseindia.com/content/cm/'
               f'BhavCopy_NSE_CM_0_0_0_{d.strftime("%Y%m%d")}_F_0000.csv.zip')
    else:
        url = ('https://archives.nseindia.com/content/historical/EQUITIES/'
               f'{d.year}/{MON[d.month-1]}/cm{d.strftime("%d")}{MON[d.month-1]}{d.year}bhav.csv.zip')
    text = _get_zip_text(url, 'https://www.nseindia.com/')
    return (text, True) if text is not None else (None, False)


def fetch_bse(d):
    """Raw BSE bhavcopy CSV text for date d, and a fetch_ok flag.

    Returns (text, True) on success, (None, False) on any fetch failure.
    Note: a holiday/no-file is indistinguishable from a fetch error at BSE
    (both may return non-200), so False always means "uncertain — retry".
    """
    if d >= datetime(2024, 1, 1):
        url = ('https://www.bseindia.com/download/BhavCopy/Equity/'
               f'BhavCopy_BSE_CM_0_0_0_{d.strftime("%Y%m%d")}_F_0000.CSV')
        try:
            r = requests.get(url, headers={**H, 'Referer': 'https://www.bseindia.com/'}, timeout=40)
            # real CSV is large; HTML error page is ~12.5 KB and starts with '<'
            if r.status_code == 200 and len(r.content) > 20000 and r.content[:1] != b'<':
                return r.text, True
        except Exception as e:
            log.debug(f'BSE UDiFF fetch {d.date()} err {e}')
        return None, False
    if d >= BSE_LEGACY_START:
        url = ('https://www.bseindia.com/download/BhavCopy/Equity/'
               f'EQ_ISINCODE_{d.strftime("%d%m%y")}.zip')
        text = _get_zip_text(url, 'https://www.bseindia.com/')
        return (text, True) if text is not None else (None, False)
    return None, False


# ── parse one day's text → {isin: (o,h,l,c,v)} ───────────────────────────────

def _num(s):
    s = (s or '').strip()
    return s if s else ''


def parse_day(text, isin_set, sym2isin):
    """Parse raw bhavcopy text into {isin: (open,high,low,close,volume)} for our
    universe only. Volume is share quantity. Returns {} if unparseable/empty."""
    out = {}
    if not text:
        return out
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return out
    cols = set(rows[0].keys())

    if 'TckrSymb' in cols and 'OpnPric' in cols:          # UDiFF (NSE new + BSE new)
        for r in rows:
            isin = (r.get('ISIN') or '').strip().upper()
            if not isin and r.get('TckrSymb'):
                isin = sym2isin.get(r['TckrSymb'].strip().upper(), '')
            if isin not in isin_set:
                continue
            o = _num(r.get('OpnPric'))
            if not o:
                continue
            # prefer first equity-series hit (avoid e.g. duplicate series rows)
            if isin in out:
                continue
            out[isin] = (o, _num(r.get('HghPric')), _num(r.get('LwPric')),
                         _num(r.get('ClsPric')), _num(r.get('TtlTradgVol')))

    elif 'SYMBOL' in cols and 'OPEN' in cols:             # NSE old (no ISIN)
        for r in rows:
            ser = (r.get('SERIES') or '').strip().upper()
            if ser and ser not in ('EQ', 'BE', 'SM', 'ST'):  # equity series only
                continue
            sym = (r.get('SYMBOL') or '').strip().upper()
            isin = sym2isin.get(sym, '')
            if isin not in isin_set:
                continue
            o = _num(r.get('OPEN'))
            if not o or isin in out:
                continue
            out[isin] = (o, _num(r.get('HIGH')), _num(r.get('LOW')),
                         _num(r.get('CLOSE')), _num(r.get('TOTTRDQTY')))

    elif 'ISIN_CODE' in cols and 'OPEN' in cols:          # BSE legacy
        for r in rows:
            isin = (r.get('ISIN_CODE') or '').strip().upper()
            if isin not in isin_set:
                continue
            o = _num(r.get('OPEN'))
            if not o or isin in out:
                continue
            out[isin] = (o, _num(r.get('HIGH')), _num(r.get('LOW')),
                         _num(r.get('CLOSE')), _num(r.get('NO_OF_SHRS')))

    return out


# ── per-ISIN writer + manifest ───────────────────────────────────────────────

def _isin_path(isin):
    return config.prices_dir() / f'{isin}.csv'


def append_day(isin_ohlcv, date_str):
    """Append one day's rows (one per ISIN) to each per-ISIN file.

    Dedupe within a file is handled by the day-manifest: each (exchange,date) is
    fetched at most once, so a given (isin,date,exchange) row is written once.
    NSE is the preferred source; BSE only fills ISINs NSE didn't have that day.
    """
    for isin, (o, h, l, c, v) in isin_ohlcv.items():
        path = _isin_path(isin)
        new = not os.path.exists(path)
        with open(path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if new:
                w.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
            w.writerow([date_str, o, h, l, c, v])


def load_done():
    """Return set of (exchange, 'YYYY-MM-DD') already processed successfully.

    Rows with rows=-1 are fetch errors and are NOT included in done, so they
    are retried on the next run.
    """
    done = set()
    manifest = _manifest()
    if os.path.exists(manifest):
        with open(manifest, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                # rows=-1 is the fetch-error sentinel — do not mark as done
                try:
                    n = int(r.get('rows', 0))
                except (ValueError, TypeError):
                    n = 0
                if n >= 0:
                    done.add((r['exchange'], r['date']))
    return done


def mark_done(exchange, date_str, n_rows):
    """Record a processed (exchange, date) in the manifest.

    n_rows >= 0  : success (0 = holiday / genuine no-data day)
    n_rows == -1 : fetch error — resume will retry this (exchange, date)
    """
    manifest = _manifest()
    new = not os.path.exists(manifest)
    os.makedirs(manifest.parent, exist_ok=True)
    with open(manifest, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['exchange', 'date', 'rows'])
        w.writerow([exchange, date_str, n_rows])


# ── driver ───────────────────────────────────────────────────────────────────

def daterange(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:          # skip weekends; holidays just yield empty
            yield d
        d += timedelta(days=1)


def run(start, end, exchanges=('NSE', 'BSE'), sleep=0.4):
    config.ensure(config.prices_dir())
    config.ensure(config.logs_dir())
    _setup_logging()

    isin_set, sym2isin = load_universe()
    log.info(f'universe: {len(isin_set)} ISINs, {len(sym2isin)} NSE symbols mapped')
    done = load_done()

    fetchers = {'NSE': fetch_nse, 'BSE': fetch_bse}
    days = list(daterange(start, end))
    log.info(f'window {start.date()}..{end.date()}: {len(days)} weekdays x {len(exchanges)} exch')

    for d in days:
        ds = d.strftime('%Y-%m-%d')
        # NSE first (preferred), then BSE fills the gaps for that day.
        seen_today = set()
        for exch in exchanges:
            if (exch, ds) in done:
                # already processed successfully; skip.
                continue
            text, fetch_ok = fetchers[exch](d)
            if not fetch_ok:
                # fetch error (network/blocked/HTTP error) — mark with sentinel -1
                # so resume logic retries this day next run
                mark_done(exch, ds, -1)
                log.warning(f'{ds} {exch}: fetch error — marked for retry (rows=-1)')
                if sleep:
                    time.sleep(sleep)
                continue
            # Save raw payload before parsing (honesty rule: raw always preserved)
            if text:
                raw_name = f'{exch}_{d.strftime("%Y%m%d")}.csv'
                ingest.save_raw('bhavcopy_ohlc', raw_name, text)
            day = parse_day(text, isin_set, sym2isin) if text else {}
            if exch != exchanges[0] and day:
                # for the secondary exchange, only add ISINs not already covered
                # by the primary exchange THIS day (avoid 2 rows same date/isin)
                day = {k: v for k, v in day.items() if k not in seen_today}
            seen_today.update(day.keys())
            if day:
                append_day(day, ds)
            mark_done(exch, ds, len(day))
            done.add((exch, ds))
            log.info(f'{ds} {exch}: {len(day)} universe rows'
                     + ('' if text else ' (holiday / no file)'))
            if sleep:
                time.sleep(sleep)
    log.info('done')


def _setup_logging():
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    log_path = config.logs_dir() / 'prices.log'
    os.makedirs(log_path.parent, exist_ok=True)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    log.addHandler(fh)
    log.addHandler(sh)


def main():
    ap = argparse.ArgumentParser(description='Per-ISIN daily OHLCV bhavcopy puller')
    ap.add_argument('--start', required=True, help='YYYY-MM-DD')
    ap.add_argument('--end', required=True, help='YYYY-MM-DD')
    ap.add_argument('--exchanges', default='NSE,BSE', help='comma list, primary first')
    ap.add_argument('--sleep', type=float, default=0.1,
                    help='seconds between requests (archives are static + tolerant; measured 2026-06-18: '
                         '6 rapid no-delay pulls all HTTP 200)')
    a = ap.parse_args()
    start = datetime.strptime(a.start, '%Y-%m-%d')
    end = datetime.strptime(a.end, '%Y-%m-%d')
    run(start, end, tuple(x.strip().upper() for x in a.exchanges.split(',')), a.sleep)


if __name__ == '__main__':
    main()
