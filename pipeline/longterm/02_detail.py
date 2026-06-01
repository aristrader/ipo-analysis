"""Long-term phase 2: attach Chittorgarh detail fields to longterm_*.csv by ISIN.

Reuses scrapers.chittorgarh.scrape_detail (the SAME parser as pipeline/02_attach_detail.py).
Mirrors 02_attach_detail.py's ATTACH set + *_src provenance tags, but operates ONLY on the
long-term masters and caches raw to data/raw/chittorgarh/details_longterm.csv (resume-safe).

ID RECOVERY: urls_longterm.csv only has chittorgarh_id (hence detail_url) for ~500 of 1031 rows,
because the original parse_list_row regex required slugs ending in '-ipo' while pre-2020 slugs use
underscores (e.g. 'cambridge_technology_ipo'). We re-pull the list API for 2006-2019 with a corrected
slug-agnostic id regex to recover the id for every row, then build detail_url = /ipo/<slug>/<id>/.

Usage:
    PYTHONPATH=. .venv/bin/python pipeline/longterm/02_detail.py [--fetch] [--workers 4]
      --fetch  : scrape detail pages (gentle); without it, only (re)attach from existing cache
"""
import argparse
import csv
import os
import re
import time

import cloudscraper

from scrapers.chittorgarh import scrape_detail, DETAIL_COLS, LIST_API, _strip_html, _iso_to_date

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(BASE, 'data', 'raw', 'chittorgarh')
MASTER = os.path.join(BASE, 'data', 'master')
URLS_LT = os.path.join(RAW, 'urls_longterm.csv')
DETAILS_LT = os.path.join(RAW, 'details_longterm.csv')
MB = os.path.join(MASTER, 'longterm_mainboard.csv')
SME = os.path.join(MASTER, 'longterm_sme.csv')

YEARS = list(range(2006, 2020))
RATE = 0.4  # gentle ~0.3-0.5s

# id-from-href regex that works for both underscore (old) and hyphen (new) slugs
_ID_RE = re.compile(r'/ipo/([a-z0-9_\-]+?)/(\d+)/')

ATTACH = ['market_maker', 'fresh_issue_cr', 'ofs_cr', 'ofs_pct', 'anchor_allocation_cr',
          'listing_open', 'listing_high', 'listing_low', 'listing_close',
          'objects_of_issue', 'issue_size_cr']


def recover_ids(scraper):
    """Re-pull list API 2006-2019, recover chittorgarh_id per ISIN via the corrected regex.
    Returns {isin: {slug, id, detail_url, nse_symbol, bse_script_code}}."""
    by_isin = {}
    for y in YEARS:
        page, seen = 1, set()
        while page <= 300:
            url = LIST_API.format(page=page, year=y)
            try:
                j = scraper.get(url, headers={'Referer': 'https://www.chittorgarh.com/'},
                                timeout=20).json()
            except Exception:
                break
            d = j.get('reportTableData') or []
            if not d:
                break
            first = d[0].get('Company', '')
            if first in seen:
                break
            seen.add(first)
            for r in d:
                isin = (r.get('~isin') or '').strip()
                if not isin:
                    continue
                m = _ID_RE.search(r.get('Company', ''))
                slug = (r.get('~URLRewrite_Folder_Name') or (m.group(1) if m else '')).strip()
                cid = m.group(2) if m else ''
                du = f'https://www.chittorgarh.com/ipo/{slug}/{cid}/' if slug and cid else ''
                by_isin.setdefault(isin, {
                    'isin': isin,
                    'company_name': _strip_html(r.get('~compare_name') or '').replace(' IPO', '').strip(),
                    'type': 'MB' if (r.get('Issue Category') or '').lower().startswith('main') else 'SME',
                    'chittorgarh_slug': slug, 'chittorgarh_id': cid, 'detail_url': du,
                    'nse_symbol': (r.get('~nse_symbol') or '').strip(),
                    'bse_script_code': str(r.get('~bse_script_code') or '').strip(),
                })
            page += 1
            time.sleep(RATE)
    return by_isin


def lt_isins():
    out = set()
    for p in (MB, SME):
        for r in csv.DictReader(open(p)):
            if r.get('isin'):
                out.add(r['isin'])
    return out


def load_cache():
    if not os.path.exists(DETAILS_LT):
        return {}
    return {r['isin']: r for r in csv.DictReader(open(DETAILS_LT, encoding='utf-8')) if r.get('isin')}


def fetch(workers):
    scraper = cloudscraper.create_scraper()
    print('Recovering chittorgarh ids via list API re-pull (2006-2019)...', flush=True)
    by_isin = recover_ids(scraper)
    print(f'  recovered identity for {len(by_isin)} isins '
          f'({sum(1 for v in by_isin.values() if v["detail_url"])} with detail_url)', flush=True)

    targets_isins = lt_isins()
    cache = load_cache()
    # resume: skip isins already in cache that have a detail_url (i.e. were actually fetchable)
    todo = []
    for isin in targets_isins:
        info = by_isin.get(isin)
        if not info or not info['detail_url']:
            continue
        if isin in cache and cache[isin].get('detail_url'):
            continue
        todo.append(info)
    print(f'targets={len(targets_isins)} fetchable_with_url={sum(1 for i in targets_isins if by_isin.get(i,{}).get("detail_url"))} '
          f'todo_this_run={len(todo)} (cached={len(cache)})', flush=True)

    out = dict(cache)
    done = 0
    for info in todo:
        try:
            rec = scrape_detail(scraper, info)
        except Exception as e:
            rec = {c: None for c in DETAIL_COLS}
            rec.update({'isin': info['isin'], 'company_name': info['company_name'],
                        'detail_url': info['detail_url']})
            print(f'  ERR {info["company_name"][:30]}: {str(e)[:50]}', flush=True)
        out[info['isin']] = rec
        done += 1
        if done % 25 == 0:
            print(f'  {done}/{len(todo)}', flush=True)
            _write_cache(out)
        time.sleep(RATE)
    _write_cache(out)
    print(f'cache now {len(out)} rows -> {DETAILS_LT}', flush=True)
    return out


def _write_cache(out):
    with open(DETAILS_LT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=DETAIL_COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(out.values())


def attach(cache):
    for seg, p in [('mainboard', MB), ('sme', SME)]:
        rows = list(csv.DictReader(open(p)))
        cols = list(rows[0].keys())
        for c in ATTACH:
            if c not in cols:
                cols.append(c)
            if c + '_src' not in cols:
                cols.append(c + '_src')
        filled = {c: 0 for c in ATTACH}
        for r in rows:
            d = cache.get(r['isin'], {})
            for c in ATTACH:
                v = (d.get(c) or '') if d else ''
                v = '' if v in ('None', None) else v
                if v:
                    r[c] = v
                    r[c + '_src'] = 'chittorgarh'
                    filled[c] += 1
                else:
                    r.setdefault(c, '')
                    r.setdefault(c + '_src', '')
        with open(p, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        print(f'{seg}: detail attached  ({", ".join(f"{c}={n}" for c, n in filled.items())})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    cache = fetch(args.workers) if args.fetch else load_cache()
    attach(cache)


if __name__ == '__main__':
    main()
