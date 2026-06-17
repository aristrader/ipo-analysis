"""DELISTING / STATUS flags for the IPO universe (Layer 2 survivorship).

NEW file — does not touch existing scrapers/pipeline/masters. Reads the four
universe masters (mainboard, sme, longterm_mainboard, longterm_sme) and writes
data/master/delisting.csv with one row per universe ISIN:

    isin, company_name, status, delist_date, reason, last_price, source_flags

Sources (in priority order):
  1. BSE ListofScripData API   -> status flag (active/suspended/delisted),
     ISIN-keyed, also matches by bse_script_code; covers SME.
  2. NSE delisted.csv          -> delist_date + reason, matched by nse_symbol
     (NSE-only, mostly <=2020, no ISIN).
  3. Bhavcopy cache inference  -> last-traded date + last price fallback, from
     data/reference/bhavcopy/ (the date a scrip last appears ~ delist/suspend
     date). Used to fill delist_date / last_price where not otherwise known.

source_flags is a '+'-joined list of the sources that contributed, e.g.
"bse:Delisted+nse_csv+bhavcopy".

Usage:
    PYTHONPATH=. .venv/bin/python -m scrapers.delisting
"""

import csv
import glob
import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta as _timedelta

import cloudscraper
from curl_cffi import requests as cr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from foundation import ingest
MASTER_DIR = os.path.join(BASE_DIR, 'data', 'master')
BHAVCOPY_DIR = os.path.join(BASE_DIR, 'data', 'reference', 'bhavcopy')
OUT_PATH = os.path.join(MASTER_DIR, 'delisting.csv')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'delisting.log')

UNIVERSE_FILES = ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']

OUT_FIELDS = ['isin', 'company_name', 'status', 'delist_date', 'reason',
              'last_price', 'source_flags']

# BSE status string -> our normalised status
_BSE_STATUS = {'active': 'active', 'suspended': 'suspended', 'delisted': 'delisted'}

log = logging.getLogger('delisting')

# Set in build() from the bhavcopy cache's end date; scrips last seen on/after
# this date are treated as still trading.
_RECENT_THRESHOLD = '9999-99-99'


# ── Universe ────────────────────────────────────────────────────────────────

def load_universe():
    """Return {isin: {company_name, nse_symbol, bse_code}} de-duped across the
    four masters (first occurrence wins for company_name)."""
    uni = {}
    for name in UNIVERSE_FILES:
        path = os.path.join(MASTER_DIR, f'{name}.csv')
        if not os.path.exists(path):
            log.warning('master missing: %s', path)
            continue
        n = 0
        for r in csv.DictReader(open(path, encoding='utf-8')):
            isin = (r.get('isin') or '').strip()
            if not isin:
                continue
            n += 1
            if isin not in uni:
                uni[isin] = {
                    'company_name': (r.get('company_name') or '').strip(),
                    'nse_symbol': (r.get('nse_symbol') or '').strip().upper(),
                    'bse_code': (r.get('bse_script_code') or '').strip(),
                }
            else:
                # backfill identifiers if this master has them and we don't
                for k, col in (('nse_symbol', 'nse_symbol'), ('bse_code', 'bse_script_code')):
                    v = (r.get(col) or '').strip()
                    if v and not uni[isin][k]:
                        uni[isin][k] = v.upper() if k == 'nse_symbol' else v
        log.info('loaded %s: %d rows', name, n)
    log.info('universe: %d unique ISINs', len(uni))
    return uni


# ── Pure helpers ─────────────────────────────────────────────────────────────

def bse_fail_flags(failed_tiers):
    """Return a sorted list of 'bse_fetch_failed:<Tier>' flag strings for the given
    failed tier names.  Pure function — extracted for testability.

    These flags are appended to source_flags for ISINs that had no BSE match AND
    at least one BSE tier failed all retries.  They distinguish:
      - status='unknown' because genuinely not in BSE  (no bse_fetch_failed flags)
      - status='unknown' because we couldn't ask BSE   (has bse_fetch_failed flags)
    """
    return ['bse_fetch_failed:' + t for t in sorted(failed_tiers)]


# ── Source 1: BSE ListofScripData ────────────────────────────────────────────

def fetch_bse_status():
    """Snapshot all three BSE statuses. Returns:
        by_isin:      {ISIN: status}   (status in {active, suspended, delisted})
        by_code:      {SCRIP_CD: status}
        names:        {ISIN_or_CD:CODE -> bse company name} for fallback naming
        failed_tiers: set of tier names (e.g. {'Suspended'}) that failed all retries

    failed_tiers is non-empty when network/API errors prevented a full snapshot;
    callers stamp 'bse_fetch_failed:<tier>' on affected ISINs so a fetch failure
    is distinguishable from a genuine BSE absence (status='unknown' because not
    listed on BSE vs status='unknown' because we couldn't ask BSE).
    """
    s = cr.Session(impersonate='chrome')
    s.get('https://www.bseindia.com/', timeout=30)        # prime cookies
    hdr = {'Referer': 'https://www.bseindia.com/', 'Origin': 'https://www.bseindia.com'}
    by_isin, by_code, names = {}, {}, {}
    failed_tiers = set()
    # Active first, then Suspended, then Delisted, so the most "terminal" status
    # wins if a scrip code happens to appear in multiple lists.
    for status in ['Active', 'Suspended', 'Delisted']:
        url = (f'https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w'
               f'?segment=Equity&status={status}')
        rows = None
        for attempt in range(4):
            try:
                r = s.get(url, headers=hdr, timeout=90)
                if r.status_code == 200:
                    rows = r.json()
                    break
                log.warning('BSE %s HTTP %s (attempt %d)', status, r.status_code, attempt + 1)
            except Exception as e:
                log.warning('BSE %s err %s (attempt %d)', status, e, attempt + 1)
            time.sleep(2 * (attempt + 1))
            s = cr.Session(impersonate='chrome')
            s.get('https://www.bseindia.com/', timeout=30)
        if not isinstance(rows, list):
            log.error('BSE %s: no rows after all retries — marking tier as failed', status)
            failed_tiers.add(status)
            continue
        # Save raw API payload so the file can be reprocessed offline (Rule 2).
        raw_name = f'bse_listofscripdata_{status.lower()}.json'
        ingest.save_raw('bse_delisting', raw_name, json.dumps(rows, ensure_ascii=False))
        st = _BSE_STATUS[status.lower()]
        for row in rows:
            isin = (row.get('ISIN_NUMBER') or '').strip()
            code = (row.get('SCRIP_CD') or '').strip()
            nm = (row.get('Issuer_Name') or row.get('Scrip_Name') or '').strip()
            if isin:
                by_isin[isin] = st
                if nm:
                    names.setdefault(isin, nm)
            if code:
                by_code[code] = st
                if nm:
                    names.setdefault('CD:' + code, nm)
        log.info('BSE %s: %d rows', status, len(rows))
    log.info('BSE totals: %d isins, %d codes, failed_tiers=%s',
             len(by_isin), len(by_code), failed_tiers or 'none')
    return by_isin, by_code, names, failed_tiers


# ── Source 2: NSE delisted.csv ───────────────────────────────────────────────

def fetch_nse_delisted():
    """Return {SYMBOL(upper): {delist_date 'YYYY-MM-DD', reason, company}}."""
    out = {}
    try:
        s = cloudscraper.create_scraper()
        s.get('https://www.nseindia.com/', timeout=30)
        r = s.get('https://nsearchives.nseindia.com/content/equities/delisted.csv',
                  timeout=60, headers={'Referer': 'https://www.nseindia.com/'})
        if r.status_code != 200:
            log.error('NSE delisted.csv HTTP %s', r.status_code)
            return out
        for row in csv.DictReader(io.StringIO(r.text)):
            sym = (row.get('Symbol') or '').strip().upper()
            if not sym:
                continue
            out[sym] = {
                'delist_date': _norm_nse_date(row.get('Delisted Date')),
                'reason': (row.get('Type of Delisting') or '').strip(),
                'company': (row.get('Company') or '').strip(),
            }
        log.info('NSE delisted.csv: %d symbols', len(out))
    except Exception as e:
        log.error('NSE delisted.csv err %s', e)
    return out


def _norm_nse_date(s):
    """'15-Apr-02' -> '2002-04-15'. Returns '' on failure."""
    s = (s or '').strip()
    for fmt in ('%d-%b-%y', '%d-%b-%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ''


# ── Source 3: Bhavcopy last-traded inference ─────────────────────────────────

def build_bhavcopy_index():
    """Scan the bhavcopy cache once. Returns {key: (last_date 'YYYY-MM-DD',
    last_open_price)} where key is an ISIN or 'SYM:<symbol>'. The cache files
    are named <EXCH>_<YYYYMMDD>.csv with columns key,open. Older NSE files only
    carry SYM: keys; BSE / new-NSE files carry both ISIN and SYM: keys."""
    index = {}
    files = sorted(glob.glob(os.path.join(BHAVCOPY_DIR, '*.csv')))
    parsed = 0
    for path in files:
        base = os.path.basename(path)
        # <EXCH>_<YYYYMMDD>.csv
        try:
            datestr = base.rsplit('_', 1)[1].split('.')[0]
            d = datetime.strptime(datestr, '%Y%m%d')
        except (IndexError, ValueError):
            continue
        iso = d.strftime('%Y-%m-%d')
        try:
            with open(path, encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
        except Exception:
            continue
        if not rows:
            continue
        parsed += 1
        for row in rows:
            key = row.get('key')
            if not key:
                continue
            price = (row.get('open') or '').strip()
            prev = index.get(key)
            # keep the latest date this key appears on (max iso); update price too
            if prev is None or iso > prev[0]:
                index[key] = (iso, price)
    log.info('bhavcopy index: %d keys from %d non-empty files (of %d cached)',
             len(index), parsed, len(files))
    return index


def bhavcopy_last(index, isin, nse_symbol, bse_code):
    """Return (last_date, last_price) for a scrip from the bhavcopy index, or
    (None, None). Tries ISIN, then NSE symbol, then BSE code; picks the most
    recent across whatever matches."""
    candidates = []
    if isin and isin in index:
        candidates.append(index[isin])
    if nse_symbol:
        k = 'SYM:' + nse_symbol
        if k in index:
            candidates.append(index[k])
    if bse_code:
        k = 'SYM:' + bse_code
        if k in index:
            candidates.append(index[k])
    if not candidates:
        return None, None
    best = max(candidates, key=lambda t: t[0])
    return best[0], (best[1] or None)


# ── Build ─────────────────────────────────────────────────────────────────────

# Bhavcopy cache covers ~2023+. A scrip whose last appearance is at/after this
# date is almost certainly still trading (cache just ends), so we must NOT treat
# its last bhavcopy date as a "delist date". We only treat the bhavcopy last
# date as a delist/suspension signal when it is comfortably before the cache end.
def _cache_bounds(index):
    dates = [v[0] for v in index.values()]
    return (min(dates), max(dates)) if dates else (None, None)


def build():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.FileHandler(LOG_PATH, mode='w'), logging.StreamHandler()],
    )
    log.info('=== delisting build start ===')

    uni = load_universe()
    bse_isin, bse_code, bse_names, bse_failed_tiers = fetch_bse_status()
    nse_del = fetch_nse_delisted()
    bhav = build_bhavcopy_index()
    cache_lo, cache_hi = _cache_bounds(bhav)
    # "still trading" window: last seen within ~60 calendar days of cache end.
    global _RECENT_THRESHOLD
    if cache_hi:
        _RECENT_THRESHOLD = (datetime.strptime(cache_hi, '%Y-%m-%d')
                             - _timedelta(days=60)).strftime('%Y-%m-%d')
    else:
        _RECENT_THRESHOLD = '9999-99-99'
    log.info('bhavcopy cache date range: %s .. %s (recent-threshold %s)',
             cache_lo, cache_hi, _RECENT_THRESHOLD)

    rows = []
    counts = {'active': 0, 'suspended': 0, 'delisted': 0, 'unknown': 0}
    n_date = 0
    n_price = 0

    for isin, info in uni.items():
        sym = info['nse_symbol']
        code = info['bse_code']
        flags = []

        # --- 1. status from BSE (ISIN first, then scrip code) ---
        status = None
        if isin in bse_isin:
            status = bse_isin[isin]
            flags.append('bse_isin:' + status)
        elif code and code in bse_code:
            status = bse_code[code]
            flags.append('bse_code:' + status)
        elif bse_failed_tiers:
            # BSE had no data for this ISIN/code AND at least one tier failed to
            # fetch.  We cannot tell "genuinely not in BSE" from "we failed to ask
            # BSE for this tier" — stamp every failed tier so the ambiguity is
            # visible rather than silently absorbed into status='unknown'.
            flags.extend(bse_fail_flags(bse_failed_tiers))

        # --- 2. NSE delisted.csv (date + reason), matched by symbol ---
        delist_date = ''
        reason = ''
        nrec = nse_del.get(sym) if sym else None
        if nrec:
            delist_date = nrec['delist_date']
            reason = nrec['reason']
            flags.append('nse_csv')
            # NSE confirms delisting; if BSE had no status, mark delisted.
            if status is None:
                status = 'delisted'
                flags.append('status_from_nse')

        # --- 3. bhavcopy last-traded inference (date + price fallback) ---
        last_price = ''
        last_date, last_open = bhavcopy_last(bhav, isin, sym, code)
        if last_date is not None:
            flags.append('bhavcopy')
            if last_open:
                last_price = last_open
                n_price += 1
            # only use as a delist/suspend date signal if the scrip stopped
            # trading well before the cache ends AND it isn't active.
            stopped_early = (cache_hi is None) or (last_date < cache_hi)
            if not delist_date and status in ('delisted', 'suspended') and stopped_early:
                delist_date = last_date
                flags.append('date_from_bhavcopy')

        # If BSE has no status (almost always an NSE-only scrip not in BSE's
        # equity list) but the scrip still appears at the very end of the
        # bhavcopy cache, it is demonstrably still trading -> active.
        if status is None and last_date is not None and cache_hi is not None \
                and last_date >= _RECENT_THRESHOLD:
            status = 'active'
            flags.append('status_from_bhavcopy_recent')

        if status is None:
            status = 'unknown'

        if delist_date:
            n_date += 1
        counts[status] = counts.get(status, 0) + 1

        company = info['company_name'] or bse_names.get(isin) or \
            bse_names.get('CD:' + code) or (nrec['company'] if nrec else '')

        rows.append({
            'isin': isin,
            'company_name': company,
            'status': status,
            'delist_date': delist_date,
            'reason': reason,
            'last_price': last_price,
            'source_flags': '+'.join(flags),
        })

    with open(OUT_PATH, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(rows)

    log.info('wrote %d rows -> %s', len(rows), OUT_PATH)
    log.info('status distribution: %s', counts)
    log.info('rows with delist_date: %d', n_date)
    log.info('rows with last_price: %d', n_price)
    log.info('=== delisting build done ===')
    return rows, counts, n_date


if __name__ == '__main__':
    build()
