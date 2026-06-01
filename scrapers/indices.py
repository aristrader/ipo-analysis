"""Benchmark index daily history (reachable sources; niftyindices POST is blocked from here).

Nifty 50        -> Yahoo ^NSEI (daily, 2007->now)
Nifty Smallcap 250 -> investing.com financialdata id 1141645 via cloudscraper (daily, 2019->now)
Output: data/reference/indices/{nifty50,niftysmallcap250}.csv  (date,close)
"""
import json, os, time, urllib.request, datetime

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
OUT = 'data/reference/indices'


def pull_yahoo(symbol, start='2006-01-01'):
    p1 = int(time.mktime(datetime.datetime.strptime(start, '%Y-%m-%d').timetuple()))
    p2 = int(time.time())
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
           f'?period1={p1}&period2={p2}&interval=1d')
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
    r = d['chart']['result'][0]
    ts = r['timestamp']; close = r['indicators']['quote'][0]['close']
    out = []
    for t, c in zip(ts, close):
        if c is not None:
            out.append((datetime.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d'), round(c, 2)))
    return out


def pull_investing(pair_id, start='2019-01-01'):
    import cloudscraper
    s = cloudscraper.create_scraper()
    end = datetime.date.today().strftime('%Y-%m-%d')
    url = (f'https://api.investing.com/api/financialdata/historical/{pair_id}'
           f'?start-date={start}&end-date={end}&time-frame=Daily&add-missing-rows=false')
    r = s.get(url, headers={**UA, 'Referer': 'https://www.investing.com/', 'domain-id': 'www'}, timeout=60)
    rows = json.loads(r.text).get('data', [])
    out = []
    for row in rows:
        # investing rows carry a date + last/close; normalize
        dt = row.get('rowDate') or row.get('date')
        close = row.get('last_close') or row.get('close') or row.get('last')
        try:
            iso = datetime.datetime.strptime(dt[:11], '%b %d, %Y').strftime('%Y-%m-%d') if dt and ',' in dt else dt[:10]
            out.append((iso, float(str(close).replace(',', ''))))
        except Exception:
            continue
    return out


if __name__ == '__main__':
    import csv
    os.makedirs(OUT, exist_ok=True)
    log = open('logs/indices.log', 'w')
    # Nifty 50
    try:
        n50 = pull_yahoo('%5ENSEI')
        n50.sort()
        with open(f'{OUT}/nifty50.csv', 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['date', 'close']); w.writerows(n50)
        msg = f"nifty50: {len(n50)} rows {n50[0][0]}..{n50[-1][0]}"
    except Exception as e:
        msg = f"nifty50 FAILED: {type(e).__name__} {e}"
    print(msg, flush=True); log.write(msg + '\n'); log.flush()
    # Nifty Smallcap 250
    try:
        sc = pull_investing(1141645)
        sc.sort()
        with open(f'{OUT}/niftysmallcap250.csv', 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['date', 'close']); w.writerows(sc)
        msg = f"smallcap250: {len(sc)} rows {sc[0][0]}..{sc[-1][0]}" if sc else "smallcap250: 0 rows"
    except Exception as e:
        msg = f"smallcap250 FAILED: {type(e).__name__} {e}"
    print(msg, flush=True); log.write(msg + '\n'); log.close()
