"""Benchmark index daily history (reachable sources; niftyindices POST is blocked from here).

Nifty 50        -> Yahoo ^NSEI (daily, 2007->now)
Nifty Smallcap 250 -> investing.com financialdata id 1141645 via cloudscraper (daily, 2019->now)
Output: <config.reference_dir()>/indices/{nifty50,niftysmallcap250}.csv  (date,close)
"""
import json, os, sys, time, urllib.request, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}


def _out_dir():
    return config.reference_dir() / 'indices'


def pull_yahoo(symbol, start='2006-01-01'):
    """Fetch daily closes from Yahoo Finance for `symbol`. Returns list of (date_str, close).

    Dropped rows (None closes) are counted and logged via the returned drop_count.
    Returns (rows, drop_count).
    """
    p1 = int(time.mktime(datetime.datetime.strptime(start, '%Y-%m-%d').timetuple()))
    p2 = int(time.time())
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
           f'?period1={p1}&period2={p2}&interval=1d')
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'replace')
    # Save raw API response before parsing
    ingest.save_raw('indices', f'yahoo_{symbol.replace("%", "pct")}_{datetime.date.today()}.json', raw)
    d = json.loads(raw)
    r = d['chart']['result'][0]
    ts = r['timestamp']
    close = r['indicators']['quote'][0]['close']
    out = []
    drop_count = 0
    for t, c in zip(ts, close):
        if c is not None:
            out.append((datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d'), round(c, 2)))
        else:
            drop_count += 1
    return out, drop_count


def _parse_investing_rows(rows):
    """Normalize investing.com historical rows -> ([(iso_date, close)], drop_count). Pure (no network).

    Prefers the unambiguous ISO `rowDateTimestamp` + numeric `last_closeRaw`; falls back to the display
    strings. NOTE: the old code did `dt[:11]` on 'Jun 17, 2026' (12 chars), chopping the year's last
    digit, so EVERY 2-digit-day row failed to parse -> all dropped. Fixed by not truncating.
    """
    out, drop_count = [], 0
    for row in rows:
        dt = row.get('rowDateTimestamp') or row.get('rowDate') or row.get('date')
        close = (row.get('last_closeRaw') or row.get('last_close')
                 or row.get('close') or row.get('last'))
        try:
            if dt and 'T' in dt:                      # ISO 'YYYY-MM-DDT00:00:00Z'
                iso = dt[:10]
            elif dt and ',' in dt:                    # display 'Jun 17, 2026'
                iso = datetime.datetime.strptime(dt.strip(), '%b %d, %Y').strftime('%Y-%m-%d')
            elif dt:
                iso = dt[:10]
            else:
                raise ValueError('no date')
            out.append((iso, float(str(close).replace(',', ''))))
        except Exception:
            drop_count += 1
    return out, drop_count


def pull_investing(pair_id, start='2019-01-01'):
    """Fetch daily closes from investing.com for `pair_id`. Returns (rows, drop_count).

    An empty data list from the API is treated as a fetch anomaly, not data; the caller
    must guard against overwriting existing data. Malformed rows are counted as dropped.
    """
    import cloudscraper
    s = cloudscraper.create_scraper()
    end = datetime.date.today().strftime('%Y-%m-%d')
    url = (f'https://api.investing.com/api/financialdata/historical/{pair_id}'
           f'?start-date={start}&end-date={end}&time-frame=Daily&add-missing-rows=false')
    r = s.get(url, headers={**UA, 'Referer': 'https://www.investing.com/', 'domain-id': 'www'}, timeout=60)
    raw_text = r.text
    # Save raw API response before parsing
    ingest.save_raw('indices', f'investing_{pair_id}_{datetime.date.today()}.json', raw_text)
    payload = json.loads(raw_text)
    return _parse_investing_rows(payload.get('data', []))


if __name__ == '__main__':
    import csv
    out_dir = _out_dir()
    os.makedirs(out_dir, exist_ok=True)
    log_path = config.logs_dir() / 'indices.log'
    os.makedirs(log_path.parent, exist_ok=True)
    log = open(log_path, 'w')
    # Nifty 50
    try:
        n50, n50_dropped = pull_yahoo('%5ENSEI')
        n50.sort()
        if n50_dropped:
            print(f"nifty50: WARNING dropped {n50_dropped} None-close rows", flush=True)
            log.write(f"nifty50: WARNING dropped {n50_dropped} None-close rows\n")
        n50_path = out_dir / 'nifty50.csv'
        with open(n50_path, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['date', 'close']); w.writerows(n50)
        msg = f"nifty50: {len(n50)} rows {n50[0][0]}..{n50[-1][0]}"
    except Exception as e:
        msg = f"nifty50 FAILED: {type(e).__name__} {e}"
    print(msg, flush=True); log.write(msg + '\n'); log.flush()
    # Nifty Smallcap 250
    sc_path = out_dir / 'niftysmallcap250.csv'
    try:
        sc, sc_dropped = pull_investing(1141645)
        sc.sort()
        if sc_dropped:
            print(f"smallcap250: WARNING dropped {sc_dropped} malformed rows", flush=True)
            log.write(f"smallcap250: WARNING dropped {sc_dropped} malformed rows\n")
        if not sc:
            # Guard: empty response — do NOT overwrite existing file with header-only
            existing = os.path.exists(sc_path)
            msg = (f"smallcap250: API returned 0 rows — {'existing file preserved' if existing else 'nothing to write'}")
            print(msg, flush=True); log.write(msg + '\n')
        else:
            with open(sc_path, 'w', newline='') as f:
                w = csv.writer(f); w.writerow(['date', 'close']); w.writerows(sc)
            msg = f"smallcap250: {len(sc)} rows {sc[0][0]}..{sc[-1][0]}"
            print(msg, flush=True); log.write(msg + '\n')
    except Exception as e:
        msg = f"smallcap250 FAILED: {type(e).__name__} {e}"
        print(msg, flush=True); log.write(msg + '\n')
    log.close()
