"""Phase 6 (QA): confirm every master ticker resolves to real price data on Yahoo.

Concurrent (ThreadPoolExecutor) for throughput; writes live progress to
logs/ticker_validation_progress.txt so a long run can be polled.

For each row we test the PRIMARY ticker (ticker_ns if present, else ticker_bo) and record
whether Yahoo returns price bars. Non-resolving tickers are the ones to review before we
build Layer 2 price history on top of them.

Output: data/master/review/ticker_validation.csv  (isin, company, type, ticker, resolves, n_days, last_close, note)
Run:    PYTHONPATH=. .venv/bin/python pipeline/06_validate_tickers.py [WORKERS]
"""
import csv, os, sys, time, threading, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapers.yahoo import fetch_chart

WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
RETRIES = 3
PROGRESS = 'logs/ticker_validation_progress.txt'

src = []
for seg in ['mainboard', 'sme']:
    for r in csv.DictReader(open(f'data/master/{seg}.csv')):
        src.append((seg, r))
total = len(src)


def check(idx, seg, r):
    ticker = (r.get('ticker_ns') or r.get('ticker_bo') or '').strip()
    rec = {'idx': idx, 'isin': r.get('isin', ''), 'company': r.get('company_name', ''),
           'type': seg, 'ticker': ticker, 'resolves': '', 'n_days': 0,
           'last_close': '', 'note': ''}
    if not ticker:
        rec['resolves'] = 'NO_TICKER'; return rec
    bars = None; err = None
    for attempt in range(RETRIES + 1):
        try:
            bars = fetch_chart(ticker, rng='1mo'); err = None; break
        except urllib.error.HTTPError as e:
            err = f'HTTP{e.code}'
            if e.code == 404:
                bars = None; err = None; break       # genuinely absent
            time.sleep(0.5 * (attempt + 1))           # 429/5xx -> back off
        except Exception as e:
            err = type(e).__name__; time.sleep(0.5 * (attempt + 1))
    if err:
        rec['resolves'] = 'ERROR'; rec['note'] = err
    elif bars:
        closes = [b['close'] for b in bars if b['close'] is not None]
        rec['resolves'] = 'YES'; rec['n_days'] = len(closes)
        rec['last_close'] = f'{closes[-1]:.2f}' if closes else ''
    else:
        rec['resolves'] = 'NO_DATA'
    return rec


results = [None] * total
counts = {'YES': 0, 'NO_DATA': 0, 'NO_TICKER': 0, 'ERROR': 0}
lock = threading.Lock()
done = 0
t0 = time.time()


def write_progress():
    el = time.time() - t0
    rate = done / el if el > 0 else 0
    eta = (total - done) / rate if rate > 0 else 0
    with open(PROGRESS, 'w') as f:
        f.write(f"done={done}/{total}  resolved={counts['YES']}  no_data={counts['NO_DATA']}  "
                f"no_ticker={counts['NO_TICKER']}  error={counts['ERROR']}  "
                f"rate={rate:.1f}/s  eta={eta:.0f}s  workers={WORKERS}\n")


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = [ex.submit(check, i, seg, r) for i, (seg, r) in enumerate(src)]
    for fut in as_completed(futs):
        rec = fut.result()
        results[rec['idx']] = rec
        with lock:
            done += 1
            counts[rec['resolves']] = counts.get(rec['resolves'], 0) + 1
            if done % 25 == 0 or done == total:
                write_progress()
                print(f"  {done}/{total} resolved={counts['YES']} no_data={counts['NO_DATA']} error={counts['ERROR']}", flush=True)

os.makedirs('data/master/review', exist_ok=True)
out = 'data/master/review/ticker_validation.csv'
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['isin', 'company', 'type', 'ticker', 'resolves', 'n_days', 'last_close', 'note'],
                       extrasaction='ignore')
    w.writeheader(); w.writerows(results)

print(f"\nwrote {out}  ({time.time()-t0:.0f}s, {WORKERS} workers)")
print(f"total={total}  resolved={counts['YES']}  no_data={counts['NO_DATA']}  "
      f"no_ticker={counts['NO_TICKER']}  error={counts['ERROR']}")
print('Non-resolving tickers (review):')
for rec in results:
    if rec and rec['resolves'] != 'YES':
        print(f"  [{rec['type']}] {rec['ticker'] or '(none)':14} {rec['company'][:40]:40} {rec['resolves']} {rec['note']}")
