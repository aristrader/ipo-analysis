"""Long-term phase 3: fill IPO subscription split from the NSE Public Issues API (MAINBOARD only).

Reuses scrapers.nse_subscription (prime_session / fetch_subscription) — the SAME authoritative
per-NSE-symbol source as pipeline/03c_fill_subscription_nse.py. Operates ONLY on longterm_mainboard.csv.

FINDING (verified on probe symbols): the NSE per-symbol endpoint only carries subscription data for
IPOs ~2017 onward (DMART/HDFCLIFE/GICRE/BANDHANBNK/IRCTC return data; COALINDIA-2010, POWERGRID-2007,
MUTHOOTFIN-2011 return None). So for the 2006-2019 cohort only 2017-2019 mainboard rows will fill.
That is expected. SME is skipped (NSE doesn't populate SME subscription).

Cache: data/raw/nse/subscription_longterm.csv (isin, sub_*). Filled rows get sub_total_x_src='nse'.

Usage:
    PYTHONPATH=. .venv/bin/python pipeline/longterm/03_subscription.py [--fetch]
"""
import argparse
import csv
import os
import time

from scrapers.nse_subscription import prime_session, fetch_subscription

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MB = os.path.join(BASE, 'data', 'master', 'longterm_mainboard.csv')
CACHE = os.path.join(BASE, 'data', 'raw', 'nse', 'subscription_longterm.csv')
LOGC = os.path.join(BASE, 'data', 'raw', 'nse', 'subscription_longterm_log.csv')
SUBCOLS = ['sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x']


def load_cache():
    if not os.path.exists(CACHE):
        return {}
    return {r['isin']: r for r in csv.DictReader(open(CACHE)) if r.get('isin')}


def fetch():
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    cache = load_cache()
    done_log = set()
    if os.path.exists(LOGC):
        done_log = {r['isin'] for r in csv.DictReader(open(LOGC))}
    targets = []
    for r in csv.DictReader(open(MB)):
        sym = (r.get('nse_symbol') or '').strip()
        if sym and r['isin'] not in cache and r['isin'] not in done_log:
            targets.append({'isin': r['isin'], 'company': r['company_name'], 'symbol': sym})
    print(f'targets={len(targets)} (cached={len(cache)})', flush=True)

    s = prime_session()
    out, logr, got = list(cache.values()), [], 0
    for i, t in enumerate(targets, 1):
        sub = None
        for attempt in range(3):
            try:
                sub = fetch_subscription(s, t['symbol'])
                break
            except Exception:
                time.sleep(1.0 * (attempt + 1))
                if attempt == 1:
                    s = prime_session()
        if sub:
            got += 1
            out.append({'isin': t['isin'], **sub})
            logr.append({'isin': t['isin'], 'company': t['company'], 'symbol': t['symbol'], 'result': 'ok'})
        else:
            logr.append({'isin': t['isin'], 'company': t['company'], 'symbol': t['symbol'], 'result': 'no_data'})
        if i % 20 == 0 or i == len(targets):
            print(f'  {i}/{len(targets)} got={got}', flush=True)
        time.sleep(0.3)

    with open(CACHE, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin'] + SUBCOLS)
        w.writeheader()
        w.writerows(out)
    # append log (resume-safe)
    mode = 'a' if os.path.exists(LOGC) else 'w'
    with open(LOGC, mode, newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin', 'company', 'symbol', 'result'])
        if mode == 'w':
            w.writeheader()
        w.writerows(logr)
    print(f'got={got}/{len(targets)} -> {CACHE}', flush=True)
    return load_cache()


def apply(cache):
    rows = list(csv.DictReader(open(MB)))
    cols = list(rows[0].keys())
    for c in SUBCOLS + ['sub_total_x_src']:
        if c not in cols:
            cols.append(c)
    filled = 0
    for r in rows:
        s = cache.get(r['isin'])
        if not s or not (s.get('sub_total_x') or '').strip():
            r.setdefault('sub_total_x_src', r.get('sub_total_x_src', ''))
            continue
        wrote = False
        for c in SUBCOLS:
            v = (s.get(c) or '').strip()
            if v and not (r.get(c) or '').strip():
                r[c] = v
                wrote = True
        if wrote:
            r['sub_total_x_src'] = 'nse'
            filled += 1
    for r in rows:
        for c in SUBCOLS + ['sub_total_x_src']:
            r.setdefault(c, '')
    with open(MB, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'mainboard: filled subscription on {filled} rows from NSE')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    args = ap.parse_args()
    cache = fetch() if args.fetch else load_cache()
    apply(cache)


if __name__ == '__main__':
    main()
