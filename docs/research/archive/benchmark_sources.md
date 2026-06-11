# Benchmark index sources — research log (2026-05-31)

Goal: fill two benchmark gaps for ALPHA computation, FREE sources only.
1. Extend **Nifty 50** daily close back before 2007-09-17 (existing Yahoo start) → at least 2006.
2. Populate **Nifty Smallcap 250** daily close for its full available history (secondary benchmark, small-cap IPOs 2019+).

Output files (schema `date,close`, ISO dates, ascending):
- `data/reference/indices/nifty50.csv`
- `data/reference/indices/niftysmallcap250.csv`

---

## FINAL COVERAGE ACHIEVED

| Index | Source used | Date range now | Rows | Gap remaining |
|---|---|---|---|---|
| Nifty 50 | GitHub `Sdaas/nifty-analysis` (pre-2007) + existing Yahoo `^NSEI` (2007-09-17+) | **1990-07-03 → 2026-05-29** | 8,681 | none (covers full 2006 cohort and far beyond) |
| Nifty Smallcap 250 | NSE official archives `ind_close_all_DDMMYYYY.csv` | **2017-04-03 → 2026-05-29** | 2,259 | pre-2017-04 unavailable from any free daily source (index introduced ~2017; the Apr-2005 "base date" is a backfilled base value, not freely downloadable daily history). The 2019+ requirement is fully met. |

Both writes verified: ascending, unique dates, no nonpositive values, clean seam.

---

## NIFTY 50 — sources tried

### ✅ WORKING — GitHub `Sdaas/nifty-analysis` (USED for pre-2007 back-extension)
- URL: `https://raw.githubusercontent.com/Sdaas/nifty-analysis/master/NIFTY%2050_Data.csv`
- Method: plain `curl`/`urllib` GET. HTTP 200, ~338 KB.
- Format: `"Date","Open","High","Low","Close"`, descending, dates like `03 May 2019`.
- Range: **1990-07-03 → 2019-05-03** (6,974 rows with a Close value).
- **Validation (decisive):** 2,840 dates overlap the existing authoritative Yahoo series; **max abs diff = 0.00**
  (byte-identical close values, e.g. 2007-09-17=4494.65, 09-18=4546.2, 09-19=4732.35). Historical anchors plausible:
  2006-01-02=2835.95, 2007-01-02=4007.40, 2008-01-08=6287.85, 2000-01-03=1592.20, 1996-01-01=908.01.
- Used: prepended only the 4,096 rows with date `< 2007-09-17` (no overlap, no dup) ahead of the untouched existing rows.
- Fetch snippet:
  ```python
  import csv, datetime, urllib.request
  url='https://raw.githubusercontent.com/Sdaas/nifty-analysis/master/NIFTY%2050_Data.csv'
  txt=urllib.request.urlopen(url, timeout=60).read().decode()
  rows=[]
  for r in csv.DictReader(txt.splitlines()):
      c=r['Close'].strip().strip('"')
      if not c: continue
      iso=datetime.datetime.strptime(r['Date'].strip().strip('"'),'%d %b %Y').strftime('%Y-%m-%d')
      rows.append((iso, round(float(c.replace(',','')),2)))
  rows.sort()  # ascending; keep iso < '2007-09-17' for prepend
  ```

### Yahoo `^NSEI` — only from 2007-09-17 (confirmed, known)
- `https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?period1=...&period2=...&interval=1d`
- HTTP 200 but earliest timestamp is 2007-09-17 even with `period1` set to 1990. Cannot back-extend. (This is the existing source for 2007+.)
- Related Yahoo tickers probed: `^CRSLDX` = **NIFTY 500** (n=5107, from 2005-09-26) and `^CNX100` = NIFTY 100 (from 2005-11-30) resolve but are different indices; `^CNXSC`, `NIFTYSMLCAP250.NS`, `^CNX500`, `^CNXSMCAP` etc. return 1 row or 404.

### stooq.com — DEAD END (now apikey/captcha gated)
- `https://stooq.com/q/d/l/?s=^nse&i=d` (and `^nsei`, `nifty`, `^cnx50`) → returns a "Get your apikey" message requiring a captcha-gated key, not CSV. Not usable for automated free fetch from this environment.

### niftyindices.com — DEAD END (POST hangs; confirmed again)
- GET pages reachable **via cloudscraper only** (plain curl times out, HTTP 000): `https://www.niftyindices.com/reports/historical-data` → 200.
- The data POST `https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString` (payload `cinfo={name,startDate,endDate,indexName}`) **ReadTimeout after 30s even via cloudscraper**. Matches the prior documented dead-end (POST hangs from this environment). Do not retry.

### NSE `/api/historical/indicesHistory` — DEAD END (Akamai 503)
- `https://www.nseindia.com/api/historical/indicesHistory?indexType=NIFTY%2050&from=DD-MM-YYYY&to=DD-MM-YYYY` via curl_cffi (chrome impersonate) with full referer priming → **HTTP 503 with embedded Akamai bot-defense script** (`/cW89.../` reference). This endpoint is Akamai-protected, unlike the project's working `/api/public-past-issues` endpoint. Do not retry.

### investing.com — DEAD END (Cloudflare 403, known) — not re-tested.

---

## NIFTY SMALLCAP 250 — sources tried

### ✅ WORKING — NSE official archives `ind_close_all` (USED)
- URL pattern (one file per trading day): `https://archives.nseindia.com/content/indices/ind_close_all_<DDMMYYYY>.csv`
- Method: plain GET with `User-Agent: Mozilla/5.0` + `Referer: https://www.nseindia.com/`. HTTP 200. (Same host the project already uses for bhavcopy.)
- Each file lists ALL NSE index closes for that day; the row of interest starts `Nifty Smallcap 250,` with columns
  `Name,Date,Open,High,Low,Close,...` (Open/High/Low often `-`; **Close is column index 5** and is populated).
- Coverage found by probing: the daily files exist from ~2013; **"Nifty Smallcap 250" first appears 2017-04-03** (the index
  was introduced ~2017). 404s on non-trading days are expected (131 such days skipped, 0 errors).
- Result fetched: **2,259 daily closes, 2017-04-03 (5671.10) → 2026-05-29 (16992.10)**. Anchors sane:
  2018-01-02=7221.62; COVID low 2020-03-24=2967.45 (series min); 2024-09-27=18399.85 (near small-cap top, series max 18623.15).
  No calendar gaps >5 days; no nonpositive values.
- Fetch snippet:
  ```python
  import urllib.request, datetime, csv
  H={'User-Agent':'Mozilla/5.0','Referer':'https://www.nseindia.com/'}
  base="https://archives.nseindia.com/content/indices/ind_close_all_{}.csv"
  out={}
  d=datetime.date(2017,4,1); end=datetime.date.today()
  while d<=end:
      if d.weekday()<5:  # skip weekends
          try:
              txt=urllib.request.urlopen(urllib.request.Request(base.format(d.strftime('%d%m%Y')),headers=H),timeout=30).read().decode('utf-8','replace')
              for line in txt.splitlines():
                  if line.startswith('Nifty Smallcap 250,'):
                      out[d.strftime('%Y-%m-%d')]=round(float(line.split(',')[5]),2); break
          except urllib.error.HTTPError as e:
              if e.code!=404: raise   # 404 = market holiday, skip
      d+=datetime.timedelta(days=1)
  # write sorted(out.items()) as date,close
  ```
- Note: this is the official, authoritative NSE source and is daily — preferred over any ETF proxy.

### Yahoo Finance — DEAD END for the index
- No working index ticker: `NIFTYSMLCAP250.NS`/`NIFTYSMALLCAP250.NS` → 404; `^CNXSC`, `NIFTY_SMLCAP_250.NS` → 1 stale row.
- ETF proxies resolve but start too late and carry tracking error → NOT used as a benchmark:
  `HDFCSML250.NS` (from 2023-02-21), `MOSMALL250.NS` (from 2024-03-18). Documented here only as fallback options.

### Kaggle `ashish090/nifty-smallcap-250-time-series-data-from-2000-23` — DEAD END (login wall)
- `https://www.kaggle.com/.../download` returns HTTP 200 but the body is the Kaggle login HTML page, not a CSV.
  Requires authentication → not a frictionless free source.

### niftyindices.com / NSE indicesHistory — same dead ends as Nifty 50 above (POST hangs / Akamai 503).

---

## Suggested edits to `docs/sources.md` "Tested & NOT viable" list
- **stooq.com** — historical CSV now requires a captcha-gated apikey; not usable for automated free fetch.
- **niftyindices.com data POST** (`Backpage.aspx/getHistoricaldatatabletoString`) — ReadTimeout/hangs even via cloudscraper (GET pages load, the data POST does not).
- **NSE `/api/historical/indicesHistory`** — Akamai-protected, returns 503 + bot-defense script (distinct from the working public-issues API).
- **Kaggle dataset downloads** — login wall (HTML, not CSV) without auth.

## And add as WORKING sources
- **GitHub `Sdaas/nifty-analysis` raw CSV** — full Nifty 50 daily OHLC from 1990; close values verified byte-identical to Yahoo over 2,840 overlapping dates. Used for pre-2007 back-extension.
- **NSE archives `ind_close_all_<DDMMYYYY>.csv`** — official daily all-index closes incl. Nifty Smallcap 250 (from 2017-04-03). Daily-file granularity; 404 = holiday.
