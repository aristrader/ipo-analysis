"""
Long-term IPO IDENTITY SPINE for 2006-2019 (survivorship-bias fix).

Reuses scrapers/chittorgarh.py machinery (pull_year / parse_list_row) to pull the
Chittorgarh list API (report 82, MB+SME) for each year 2006-2019, caches raw rows to
data/raw/chittorgarh/urls_longterm.csv, then builds ISIN-keyed identity bases split
MB/SME exactly as pipeline/01_build_base.py does.

INCLUDES delisted/failed IPOs (whatever the API returns) — that is the whole point.
Identity only: NO GMP/subscription/financials enrichment.

Outputs:
    data/master/longterm_mainboard.csv
    data/master/longterm_sme.csv

Does NOT touch the existing 2020-2025 masters / _base files / urls.csv.

Usage:
    PYTHONPATH=. .venv/bin/python pipeline/00_build_longterm_spine.py
"""
import csv
import os
import time
import logging
from datetime import datetime

import cloudscraper

from scrapers.chittorgarh import pull_year, LIST_COLS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'chittorgarh')
MASTER_DIR = os.path.join(BASE_DIR, 'data', 'master')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

URLS_LONGTERM = os.path.join(RAW_DIR, 'urls_longterm.csv')
OUT_MB = os.path.join(MASTER_DIR, 'longterm_mainboard.csv')
OUT_SME = os.path.join(MASTER_DIR, 'longterm_sme.csv')
LOG_FILE = os.path.join(LOGS_DIR, 'longterm_spine.log')

YEARS = list(range(2006, 2020))  # 2006..2019
COHORT = '2006-2019'

# Identity columns matching existing _base / master (subset, identity only) + cohort.
IDENTITY_COLS = [
    'isin', 'company_name', 'type', 'nse_symbol', 'bse_script_code',
    'open_date', 'close_date', 'listing_date',
    'issue_price', 'issue_amount_cr', 'pricing_method', 'listing_at',
    'lead_manager', 'year', 'cohort',
]

log = logging.getLogger('longterm_spine')


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()],
        format='%(asctime)s [%(levelname)-7s] %(message)s', datefmt='%H:%M:%S')


def pull_lists():
    """Pull all years via the reused scraper, cache to urls_longterm.csv. Returns rows."""
    os.makedirs(RAW_DIR, exist_ok=True)
    scraper = cloudscraper.create_scraper()
    all_rows = []
    per_year = {}
    for y in YEARS:
        t = time.time()
        rows = pull_year(scraper, y)
        for r in rows:
            r['year'] = y
        n_mb = sum(1 for r in rows if r['type'] == 'MB')
        n_sme = sum(1 for r in rows if r['type'] == 'SME')
        per_year[y] = (len(rows), n_mb, n_sme)
        all_rows.extend(rows)
        log.info(f'  {y}: {len(rows)} rows (MB={n_mb} SME={n_sme}) in {time.time()-t:.0f}s')

    with open(URLS_LONGTERM, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=LIST_COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(all_rows)
    log.info(f'Cached {len(all_rows)} raw rows -> {URLS_LONGTERM}')
    return all_rows, per_year


def build_bases(rows):
    """ISIN-keyed, dedupe by ISIN (keep first), split MB/SME as 01_build_base does."""
    year_strs = {str(y) for y in YEARS}
    rows = [r for r in rows if r.get('isin') and str(r.get('year')) in year_strs]
    seen, uniq = set(), []
    for r in rows:
        if r['isin'] in seen:
            continue
        seen.add(r['isin'])
        uniq.append(r)

    counts = {}
    for seg, val, path in [('mainboard', 'MB', OUT_MB), ('sme', 'SME', OUT_SME)]:
        sub = []
        for r in uniq:
            if r['type'] != val:
                continue
            rec = {c: r.get(c, '') for c in IDENTITY_COLS}
            rec['cohort'] = COHORT
            sub.append(rec)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=IDENTITY_COLS)
            w.writeheader()
            w.writerows(sub)
        counts[seg] = sub
        log.info(f'{seg}: {len(sub)} rows -> {path}')
    return uniq, counts


def verify(uniq, per_year, counts):
    log.info('=== VERIFY ===')
    year_strs = {str(y): y for y in YEARS}
    # rows per year (deduped, with ISIN), MB vs SME
    by_year = {y: {'MB': 0, 'SME': 0, 'other': 0} for y in YEARS}
    for r in uniq:
        ys = str(r.get('year'))
        if ys not in year_strs:
            continue
        y = year_strs[ys]
        t = r['type'] if r['type'] in ('MB', 'SME') else 'other'
        by_year[y][t] += 1
    for y in YEARS:
        d = by_year[y]
        raw = per_year.get(y, (0, 0, 0))[0]
        log.info(f'  {y}: deduped MB={d["MB"]} SME={d["SME"]} other={d["other"]} '
                 f'(raw API rows={raw})')

    total_mb = len(counts['mainboard'])
    total_sme = len(counts['sme'])
    log.info(f'  TOTAL deduped identity rows: MB={total_mb} SME={total_sme} '
             f'all={total_mb + total_sme}')

    # % non-empty ISIN over raw rows
    all_raw = sum(per_year[y][0] for y in YEARS)
    # uniq already filtered to non-empty isin; report against raw count cached
    log.info(f'  raw rows pulled across years: {all_raw}; deduped-with-ISIN: {len(uniq)}')

    # 0 SME before 2012 check
    pre2012_sme = sum(by_year[y]['SME'] for y in YEARS if y < 2012)
    status = 'OK (0 as expected)' if pre2012_sme == 0 else f'WARN ({pre2012_sme} found!)'
    log.info(f'  SME before 2012: {pre2012_sme} -> {status}')

    # years that returned nothing
    empty = [y for y in YEARS if per_year.get(y, (0,))[0] == 0]
    if empty:
        log.info(f'  EMPTY YEARS: {empty}')
    else:
        log.info('  No empty years.')


def main():
    setup_logging()
    log.info(f'=== Long-term spine build  years={YEARS[0]}-{YEARS[-1]} ===')
    rows, per_year = pull_lists()
    uniq, counts = build_bases(rows)
    verify(uniq, per_year, counts)
    log.info('=== Done ===')


if __name__ == '__main__':
    main()
