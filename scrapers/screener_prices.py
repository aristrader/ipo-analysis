"""Pull WEEKLY split/bonus-ADJUSTED price+volume history from screener.in's chart API
for IPOs whose bhavcopy daily history starts >30 days after listing (listing-era gap).

Identity: reuse scrapers/screener.py resolve logic — fetch /company/<bse_code>/ or
/company/<nse_symbol>/, extract data-company-id, then hit the chart API:
  https://www.screener.in/api/company/<id>/chart/?q=Price-Volume&days=10000
Datasets: 'Price' values = [["YYYY-MM-DD","<price>"],...] (WEEKLY, adjusted),
          'Volume' values = [["YYYY-MM-DD", <int>, {"delivery":..}], ...].

Because the company is keyed by its exchange CODE (BSE script / NSE symbol), a page that
loads for that code IS the right security even after a name change (e.g. Sangam Advisors ->
Waaree Renewable, BSE 534618). We accept on code-load; record whether the name also matched.

GENTLE: 1 worker, ~1.5s between requests, circuit-breaker (stop after 10 consecutive errors),
resume-safe — caches to data/raw/screener_prices/<isin>.csv and logs to .../_resolve_log.csv.

Run: PYTHONPATH=. .venv/bin/python scrapers/screener_prices.py [delay]
"""
import csv, os, sys, re, json, time, urllib.request, urllib.error
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screener  # reuse fetch_company, page_name, name_match, search_company

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = config.raw_dir('screener_prices')
LOG_PATH = OUT_DIR / '_resolve_log.csv'
UA = screener.UA


def pdate(s):
    s = (s or '').strip()
    if not s:
        return None
    for f in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def _get(url, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'ignore')


def extract_company_id(html):
    m = re.search(r'data-company-id="(\d+)"', html)
    return m.group(1) if m else None


def resolve_company_id(nse_symbol, bse_code, company_name, sleep=1.5):
    """Return (company_id, slug, name_matched_bool, why). Identity by exchange CODE
    (page load) primarily; name-match recorded but not required for code hits because
    the code uniquely identifies the security across renames."""
    tried = []
    for kind, slug in [('bse', str(bse_code) if bse_code else None), ('nse', nse_symbol or None)]:
        if not slug:
            continue
        try:
            html = screener.fetch_company(slug, consolidated=False)
        except Exception as e:
            tried.append(f'{kind}:{slug}->ERR:{type(e).__name__}')
            time.sleep(sleep)
            raise
        time.sleep(sleep)
        if not html:
            tried.append(f'{kind}:{slug}->404')
            continue
        cid = extract_company_id(html)
        if not cid:
            tried.append(f'{kind}:{slug}->no-id')
            continue
        pn = screener.page_name(html)
        nm = screener.name_match(pn, company_name, allow_digitstrip=True)
        return cid, slug, nm, f'code-{kind}({pn}){"=name" if nm else "!=name"}'
    # search fallback (handles delisted / renamed not reachable by code)
    try:
        for c in screener.search_company(company_name):
            if screener.name_match(c.get('name', ''), company_name):
                html = screener.fetch_company(c.get('url', ''))
                time.sleep(sleep)
                if html:
                    cid = extract_company_id(html)
                    if cid and screener.name_match(screener.page_name(html), company_name):
                        return cid, c.get('url', ''), True, f'search({c.get("name")})'
    except Exception:
        pass
    return None, (tried[0].split('->')[0] if tried else ''), False, f'no-resolve[{"|".join(tried)[:90]}]'


def fetch_chart(company_id, sleep=1.5):
    """Return list of dicts {date, close, volume} sorted by date, from the chart API."""
    url = f'https://www.screener.in/api/company/{company_id}/chart/?q=Price-Volume&days=10000'
    raw = _get(url)
    # Save raw payload before parsing (honesty rule: raw always preserved)
    ingest.save_raw('screener_prices', f'{company_id}.json', raw)
    data = json.loads(raw)
    time.sleep(sleep)
    ds = {d.get('metric'): d.get('values', []) for d in data.get('datasets', [])}
    price = ds.get('Price') or ds.get('Price on BSE') or ds.get('Price on NSE') or []
    vol = ds.get('Volume') or []
    volmap = {}
    for row in vol:
        if len(row) >= 2:
            try:
                volmap[row[0]] = float(row[1])
            except (TypeError, ValueError):
                pass
    out = []
    for row in price:
        if len(row) < 2:
            continue
        d = row[0]
        try:
            c = float(row[1])
        except (TypeError, ValueError):
            continue
        out.append({'date': d, 'close': c, 'volume': volmap.get(d)})
    out.sort(key=lambda x: x['date'])
    return out


def load_masters():
    m = {}
    for f in ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']:
        path = config.src('master', f + '.csv')
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            isin = (r.get('isin') or '').strip()
            if not isin or isin in m:
                continue
            m[isin] = {
                'company_name': (r.get('company_name') or '').strip(),
                'nse': (r.get('nse_symbol') or '').strip(),
                'bse': (r.get('bse_script_code') or '').strip(),
                'listing_date': r.get('listing_date', ''),
            }
    return m


def build_fixset():
    """ISINs where first data date in data/prices/<isin>.csv is >30 days after listing_date."""
    fix = []
    for r in csv.DictReader(open(config.src('master', 'returns_summary.csv'))):
        isin = r['isin']
        ld = pdate(r['listing_date'])
        p = config.src('prices', isin + '.csv')
        if not os.path.exists(p) or ld is None:
            continue
        dates = [pdate(pr['date']) for pr in csv.DictReader(open(p))]
        dates = [d for d in dates if d]
        if not dates:
            continue
        first = min(dates)                 # files are NOT date-sorted (validation rows at top) -> use min
        if (first - ld).days > 30:
            fix.append(isin)
    return fix


def main():
    delay = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    MAX_CONSEC_ERR = 10
    os.makedirs(OUT_DIR, exist_ok=True)

    masters = load_masters()
    fixset = build_fixset()

    done = set()
    if os.path.exists(LOG_PATH):
        for r in csv.DictReader(open(LOG_PATH)):
            if not (r.get('why') or '').startswith('ERROR'):
                done.add(r['isin'])

    log_new = (not os.path.exists(LOG_PATH)) or os.path.getsize(LOG_PATH) == 0
    log_f = open(LOG_PATH, 'a', newline='')
    log_w = csv.writer(log_f)
    if log_new:
        log_w.writerow(['isin', 'company', 'company_id', 'slug', 'name_matched', 'n_points', 'first_date', 'why'])
        log_f.flush()

    todo = [i for i in fixset if i not in done]
    print(f"fixset={len(fixset)} already_done={len(done)} todo={len(todo)}", flush=True)

    counts = {'resolved': 0, 'noresolve': 0, 'error': 0}
    n = 0
    consec_err = 0
    blocked = False
    for isin in todo:
        m = masters.get(isin)
        if not m:
            log_w.writerow([isin, '', '', '', '', 0, '', 'no-master-row'])
            log_f.flush()
            continue
        try:
            cid, slug, nm, why = resolve_company_id(m['nse'], m['bse'], m['company_name'], sleep=delay)
            if cid:
                pts = fetch_chart(cid, sleep=delay)
                with open(OUT_DIR / (isin + '.csv'), 'w', newline='') as fh:
                    w = csv.writer(fh)
                    w.writerow(['date', 'close', 'volume'])
                    for p in pts:
                        w.writerow([p['date'], p['close'], '' if p['volume'] is None else p['volume']])
                counts['resolved'] += 1
                consec_err = 0
                log_w.writerow([isin, m['company_name'], cid, slug, nm, len(pts),
                                pts[0]['date'] if pts else '', why])
            else:
                counts['noresolve'] += 1
                consec_err = 0
                log_w.writerow([isin, m['company_name'], '', slug, False, 0, '', why])
        except Exception as e:
            counts['error'] += 1
            consec_err += 1
            log_w.writerow([isin, m['company_name'], '', '', '', 0, '', f'ERROR:{type(e).__name__}:{str(e)[:60]}'])
        log_f.flush()
        n += 1
        if n % 10 == 0 or n == len(todo):
            open(config.logs_dir() / 'screener_prices_progress.txt', 'w').write(
                f"done={n}/{len(todo)} resolved={counts['resolved']} noresolve={counts['noresolve']} "
                f"error={counts['error']} consec_err={consec_err}\n")
            print(f"  {n}/{len(todo)} resolved={counts['resolved']} noresolve={counts['noresolve']} "
                  f"error={counts['error']} consec_err={consec_err}", flush=True)
        if consec_err >= MAX_CONSEC_ERR:
            blocked = True
            print(f"[circuit-breaker] {consec_err} consecutive errors — stopping", flush=True)
            break
        time.sleep(delay)
    log_f.close()
    print(f"\npass done: resolved={counts['resolved']} noresolve={counts['noresolve']} "
          f"error={counts['error']} blocked={blocked}", flush=True)
    sys.exit(2 if blocked else 0)


if __name__ == '__main__':
    main()
