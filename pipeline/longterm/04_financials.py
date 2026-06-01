"""Long-term phase 4: pre-IPO financials from screener.in for the long-term ISINs.

FETCH reuses scrapers.screener.get_verified_financials (concrete exchange-code-verified match) and
APPENDS long-term ISINs to the SHARED ISIN-keyed cache data/raw/screener/financials.csv +
match_log.csv (resume-safe; never rewrites existing rows). 1 worker, ~1.5s delay, circuit-breaker
(stop after 10 consecutive errors) — screener blocks aggressively, so each run is a BOUNDED pass.

APPLY mirrors pipeline/03b_fill_financials_screener.py year-mapping exactly:
  last pre-listing FY = listing-year if listing-month>=April else listing-year-1.
  yr3=last pre-listing FY, yr2=yr3-1, yr1=yr3-2; pre_ipo_* derived from yr3.
Only operates on longterm_*.csv. Financials we write are tagged pat_yr3_src='screener'.

EXPECTATION: survivor + recency limited. Screener carries ~10y history, so pre-listing FY exists only
for ~2015+ listings; delisted / very old IPOs stay blank (fine/expected).

Usage:
    PYTHONPATH=. .venv/bin/python pipeline/longterm/04_financials.py --fetch [--delay 1.5] [--limit N]
    PYTHONPATH=. .venv/bin/python pipeline/longterm/04_financials.py            # apply only
"""
import argparse
import csv
import os
import sys
import time

from scrapers.screener import get_verified_financials

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER = os.path.join(BASE, 'data', 'master')
MB = os.path.join(MASTER, 'longterm_mainboard.csv')
SME = os.path.join(MASTER, 'longterm_sme.csv')
FIN_PATH = os.path.join(BASE, 'data', 'raw', 'screener', 'financials.csv')
LOG_PATH = os.path.join(BASE, 'data', 'raw', 'screener', 'match_log.csv')

MAX_CONSEC_ERR = 10

YR_METRICS = {'net_sales': 'sales', 'operating_profit': 'operating_profit', 'pat': 'net_profit',
              'eps': 'eps', 'borrowings': 'borrowings', 'total_assets': 'total_assets',
              'operating_cf': 'operating_cf'}
YR_COLS = list(YR_METRICS) + ['shareholder_funds']
PRE_COLS = ['pre_ipo_net_sales', 'pre_ipo_pat', 'pre_ipo_pat_margin_pct', 'pre_ipo_roe_pct',
            'pre_ipo_debt_equity', 'pre_ipo_fin_year', 'pre_ipo_years_available']


def fetch(delay, limit):
    os.makedirs(os.path.dirname(FIN_PATH), exist_ok=True)
    # RESUME against the SHARED log: skip ISINs with a definitive (non-ERROR) result
    done_isins = set()
    if os.path.exists(LOG_PATH):
        done_isins = {r['isin'] for r in csv.DictReader(open(LOG_PATH))
                      if not (r.get('verify') or '').startswith('ERROR')}

    targets = []
    for p in (MB, SME):
        for r in csv.DictReader(open(p)):
            if r['isin'] in done_isins:
                continue
            nse = (r.get('nse_symbol') or '').strip()
            bse = (r.get('bse_script_code') or '').strip()
            if nse or bse:
                targets.append({'isin': r['isin'], 'company': r['company_name'], 'nse': nse, 'bse': bse})
    if limit:
        targets = targets[:limit]
    print(f'longterm screener targets this pass={len(targets)} (already-done in shared cache={len(done_isins)})',
          flush=True)

    new_cache = not os.path.exists(FIN_PATH)
    fin_f = open(FIN_PATH, 'a', newline=''); fin_w = csv.writer(fin_f)
    log_f = open(LOG_PATH, 'a', newline=''); log_w = csv.writer(log_f)
    if new_cache:
        fin_w.writerow(['isin', 'fy', 'metric', 'value']); fin_f.flush()
        log_w.writerow(['isin', 'company', 'slug', 'verify', 'n_years']); log_f.flush()

    counts = {'verified': 0, 'none': 0, 'mismatch': 0, 'error': 0}
    done = consec = 0
    blocked = False
    t0 = time.time()
    for t in targets:
        try:
            fin, slug, why = get_verified_financials(t['nse'], t['bse'])
        except Exception as e:
            fin, slug, why = None, '', f'ERROR:{type(e).__name__}'
        done += 1
        if fin:
            counts['verified'] += 1; consec = 0
            for fy, m in fin.items():
                for metric, val in m.items():
                    fin_w.writerow([t['isin'], fy, metric, val])
        elif why.startswith('ERROR'):
            counts['error'] += 1; consec += 1
        else:
            counts['mismatch' if 'mismatch' in why else 'none'] += 1; consec = 0
        log_w.writerow([t['isin'], t['company'], slug, why, len(fin) if fin else 0])
        fin_f.flush(); log_f.flush()
        if done % 20 == 0 or done == len(targets):
            print(f'  {done}/{len(targets)} verified={counts["verified"]} none={counts["none"]} '
                  f'error={counts["error"]} consec={consec} rate={done/(time.time()-t0+0.01):.2f}/s', flush=True)
        if consec >= MAX_CONSEC_ERR:
            blocked = True
            print(f'[circuit-breaker] {consec} consecutive errors — screener blocked, stopping pass', flush=True)
            break
        time.sleep(delay)
    fin_f.close(); log_f.close()
    print(f'pass: verified={counts["verified"]} none={counts["none"]} mismatch={counts["mismatch"]} '
          f'error={counts["error"]} blocked={blocked}', flush=True)
    return blocked


def _load_fin():
    fin = {}
    for r in csv.DictReader(open(FIN_PATH)):
        try:
            fy = int(r['fy']); val = float(r['value'])
        except (ValueError, TypeError):
            continue
        fin.setdefault(r['isin'], {}).setdefault(fy, {})[r['metric']] = val
    return fin


def _last_pre_listing_fy(ld):
    if not ld or len(ld) < 7:
        return None
    y, m = int(ld[:4]), int(ld[5:7])
    return y if m >= 4 else y - 1


def _num(v):
    return v if isinstance(v, (int, float)) else None


def apply():
    fin = _load_fin()
    for seg, p in [('mainboard', MB), ('sme', SME)]:
        rows = list(csv.DictReader(open(p)))
        cols = list(rows[0].keys())
        for stem in YR_COLS:
            for i in (1, 2, 3):
                if f'{stem}_yr{i}' not in cols:
                    cols.append(f'{stem}_yr{i}')
        for c in PRE_COLS + ['pat_yr3_src']:
            if c not in cols:
                cols.append(c)
        resourced = 0
        for r in rows:
            byfy = fin.get(r['isin'])
            fy3 = _last_pre_listing_fy(r.get('listing_date', ''))
            if not byfy or not fy3:
                continue
            m3 = byfy.get(fy3)
            if not m3:
                continue  # screener lacks the pre-listing year (too old) → leave blank
            for i, fy in enumerate([fy3 - 2, fy3 - 1, fy3], start=1):
                m = byfy.get(fy)
                for stem in YR_COLS:
                    r[f'{stem}_yr{i}'] = ''
                if not m:
                    continue
                for stem, metric in YR_METRICS.items():
                    v = _num(m.get(metric))
                    if v is not None:
                        r[f'{stem}_yr{i}'] = v
                eq, res = _num(m.get('equity_capital')), _num(m.get('reserves'))
                if eq is not None and res is not None:
                    r[f'shareholder_funds_yr{i}'] = round(eq + res, 2)
            sales, pat = _num(m3.get('sales')), _num(m3.get('net_profit'))
            eq, res, brw = _num(m3.get('equity_capital')), _num(m3.get('reserves')), _num(m3.get('borrowings'))
            sf = (eq + res) if (eq is not None and res is not None) else None
            r['pre_ipo_fin_year'] = f'Mar {fy3}'
            if sales is not None:
                r['pre_ipo_net_sales'] = sales
            if pat is not None:
                r['pre_ipo_pat'] = pat
            if sales and pat is not None:
                r['pre_ipo_pat_margin_pct'] = round(pat / sales * 100, 2)
            if sf and pat is not None:
                r['pre_ipo_roe_pct'] = round(pat / sf * 100, 2)
            if sf and brw is not None:
                r['pre_ipo_debt_equity'] = round(brw / sf, 2)
            r['pre_ipo_years_available'] = sum(1 for fy in (fy3 - 2, fy3 - 1, fy3) if byfy.get(fy))
            r['pat_yr3_src'] = 'screener'
            resourced += 1
        for r in rows:
            for c in YR_COLS:
                for i in (1, 2, 3):
                    r.setdefault(f'{c}_yr{i}', '')
            for c in PRE_COLS + ['pat_yr3_src']:
                r.setdefault(c, '')
        with open(p, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        print(f'{seg}: screener financials applied to {resourced} rows')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--delay', type=float, default=1.5)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    blocked = False
    if args.fetch:
        blocked = fetch(args.delay, args.limit)
    apply()
    sys.exit(2 if blocked else 0)


if __name__ == '__main__':
    main()
