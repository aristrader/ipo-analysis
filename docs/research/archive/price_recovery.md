# Price-coverage recovery research

Investigation of the two Layer-2 price-coverage gaps, with a concrete recovery plan.
Date: 2026-05-31. Scope: RESEARCH + safe recovery only — no `data/master` or pipeline edits.

Affected-ISIN lists (machine-readable) live in `docs/research/_gaps.json`.
Recovered listing-day OHLC lives in `docs/research/recovered_listing_day.csv` (79 rows).
Probe script: `docs/research/_recover_listing.py`. Raw results: `docs/research/_recover_results.json`.

Daily-price schema (verified from an existing file): `date,open,high,low,close,volume` — **no source column**.

---

## TL;DR

| Gap | Count | Genuine source gap? | Recovered | How |
|---|---|---|---|---|
| **Gap 1 — `unreliable_coverage`** | 142 | partial | — | split into two sub-causes below |
| ├─ `bhavcopy_daily` subset | 73 | **NO** — false positive | n/a (data already present) | listing-day row already in `data/prices/<isin>.csv`; flag is a remediation artifact |
| └─ `none_listing_era` subset | 69 | **YES** | **67/69** | BSE bhavcopy archive by SC_CODE |
| **Gap 2 — no returns row (26)** | 26 | partial | — | split into two below |
| ├─ no price file at all | 12 | **YES** | **12/12** | BSE bhavcopy archive by SC_CODE |
| └─ has full price file, excluded | 14 | **NO** — join artifact | n/a (full history present) | Layer-2 join/dedup issue, not a source gap |

**Net: 79 of the genuinely-missing listing rows recovered (67 + 12) out of 81 true gaps.**
Of the headline "142 + 26", the truly source-solvable subset was 81; the rest are pipeline
issues (already-present data mis-flagged or mis-joined). All 72 recovered stocks that have a
Chittorgarh listing_open cross-check **match within 2% (100%)**.

---

## Gap composition (what's actually wrong)

### Gap 1 — 142 `listing_metrics_status == 'unreliable_coverage'`
Breakdown by `price_source`: 73 `bhavcopy_daily`, 69 `none_listing_era`. 90 SME / 52 MB.

- **73 `bhavcopy_daily`: NOT a data gap.** Every one of these 73 stocks **already has a price
  row on its listing day** in `data/prices/<isin>.csv` (verified: min(price dates) == listing_date,
  delta 0 for all 73). They were flagged `unreliable_coverage` by `pipeline/listing_remediation.py`
  because of its *Chittorgarh-anchor / scale-inversion* branch (`implied_factor > 12`,
  `chittor_listing_open is None`, or `scale_inverted`), **not** the coverage-gap branch.
  Spot-check (price-file listing-day open vs Chittorgarh listing_open):
  ASTRAL 103/115(bonus chain), RAJMET 35/35, SECL 36/36, IEX 1500/1500, KRITIKA 34.1/34.10,
  IRISDOREME 92/92 — the listing-day OHLC is present and correct. A genuine handful (e.g.
  Wonderla INE066O01014: file 308 vs chittor 164.75 vs issue 125) are real split/bonus-scale
  cases. **Recovery for these 73 = a Layer-2 recompute decision, not a new source.**
- **69 `none_listing_era`: REAL gap.** These have a `screener_weekly` price file whose series
  **starts 305–4363 days after listing** — the listing day is genuinely absent. All 69 have a
  BSE numeric code. This is the recoverable subset → BSE bhavcopy (below).

### Gap 2 — 26 universe ISINs missing from `returns_summary.csv`
(`price_source_review.csv` is stale: all 39 of its rows now have price files and are NOT the gap.)

- **12 have NO `data/prices/<isin>.csv` at all** (real gap). Old BSE-only MB/FPO, 2006–2013, all
  with BSE numeric codes → BSE bhavcopy (below).
- **14 have a full price file but no returns row** (NOT a source gap). e.g. Tech Mahindra
  (4873 days), Sun TV (4961), Allcargo (4917), Lokesh Machines (4952). These are FPOs or
  renamed/duplicate-ISIN entities with a blank `listing_date` in `universe.csv`; they were
  dropped by a Layer-2 join/dedup step. Price data exists — fix is a pipeline join decision.

---

## Sources tried (concrete results)

### 1. BSE bhavcopy archive — **THE WINNER** ✅
Whole-market EOD by **numeric SC_CODE** (no ISIN-mismatch problem, which is exactly why the
ISIN-keyed pipeline missed these). Three date-format regimes, all return HTTP 200 with
`User-Agent` + `Referer: https://www.bseindia.com/` only (no cookies/Akamai games):

| Date range | URL | Key column | OHLC columns |
|---|---|---|---|
| `>= 2024-01-01` | `…/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_<YYYYMMDD>_F_0000.CSV` | `FinInstrmId` | `OpnPric/HghPric/LwPric/ClsPric/TtlTradgVol` |
| `~2014–2023` | `…/download/BhavCopy/Equity/EQ_ISINCODE_<DDMMYY>.zip` | `SC_CODE` (also has `ISIN_CODE`) | `OPEN/HIGH/LOW/CLOSE/NO_OF_SHRS` |
| pre-2014 | `…/download/BhavCopy/Equity/EQ<DDMMYY>_CSV.ZIP` | `SC_CODE` | `OPEN/HIGH/LOW/CLOSE/NO_OF_SHRS` |

(The `EQ_ISINCODE_<DDMMYY>.zip` legacy format is already the project's known BSE pattern in
`scrapers/bhavcopy_ohlc.py`; the pre-2014 `EQ<DDMMYY>_CSV.ZIP` form extends coverage further back.)

Sample recovered listing-day rows (open/high/low/close/vol):
- Astral 532830 @2007-03-20 → 103 / 113.65 / 100 / 105.35 (PREVCLOSE 0 ⇒ true listing day)
- Axita Cotton 542285 @2019-01-10 → 61 / 64.05 / 61 / 62.10 (group MT = SME)
- R&B Denims 538119 @2014-04-22 → 10.55 / 11.05 / 10.55 / 11.05
- BS Transcomm 533276 @2010-10-27 → 251 / 399 / 247.80 / 378.50
- Mehai Technology 540730 @2017-10-09 → 35.10 / 35.10 / 32.20 / 34.50

Fetch snippet (copy-paste):
```python
import requests, io, zipfile, csv
from datetime import datetime
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
     'Referer': 'https://www.bseindia.com/'}
BASE = 'https://www.bseindia.com/download/BhavCopy/Equity/'

def bse_day(dt):  # dt: datetime -> {sc_code: (o,h,l,c,vol)} or None
    if dt >= datetime(2024, 1, 1):
        r = requests.get(BASE + f'BhavCopy_BSE_CM_0_0_0_{dt:%Y%m%d}_F_0000.CSV', headers=H, timeout=40)
        if r.status_code == 200 and len(r.content) > 20000 and r.content[:1] != b'<':
            return {(x['FinInstrmId'] or '').strip():
                    (x['OpnPric'], x['HghPric'], x['LwPric'], x['ClsPric'], x['TtlTradgVol'])
                    for x in csv.DictReader(io.StringIO(r.text))}
        return None
    for pat in (f'EQ_ISINCODE_{dt:%d%m%y}.zip', f'EQ{dt:%d%m%y}_CSV.ZIP'):  # 2014+ then pre-2014
        r = requests.get(BASE + pat, headers=H, timeout=40)
        if r.status_code == 200 and r.content[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(r.content))
            rows = list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode('latin-1'))))
            return {(x.get('SC_CODE') or '').strip():
                    (x.get('OPEN'), x.get('HIGH'), x.get('LOW'), x.get('CLOSE'), x.get('NO_OF_SHRS'))
                    for x in rows}
    return None
```
Coverage achieved: **67/69 `none_listing_era` + 12/12 Gap-2-no-file = 79/81**, forward-searching
up to 7 calendar days from `listing_date` to skip holidays/listing-day-off-by-one. Validation:
72 of the 79 have a Chittorgarh listing_open; **all 72 match within 2%**.

### 2. NSE old daily bhavcopy — covers EMERGE SME ✅ (for the NSE-only SME tail)
`https://archives.nseindia.com/content/historical/EQUITIES/<YYYY>/<MON>/cm<DD><MON><YYYY>bhav.csv.zip`
(UA + `Referer: https://www.nseindia.com/`). Confirmed it **includes EMERGE SME** — series `SM`
(101 rows) and `ST` (6 rows) on 2018-10-08 — has an `ISIN` column, and contained RAJMET's
listing-day row (open 35, matches Chittorgarh). This is already what the pipeline uses, which is
why the 73 `bhavcopy_daily` stocks have their listing day. Relevant for the few NLE/SME stocks
that are NSE-EMERGE-only with no BSE code (n=0 in the true-gap set — all 69 NLE had BSE codes —
but keep this as the fallback for any future NSE-only SME gap).
**Caveat found:** NSE bhavcopy ISIN can differ from `universe.isin` by 1 char after a face-value
split (RAJMET bhavcopy `INE00KV01014` vs universe `INE00KV01022`) — this ISIN drift is the likely
reason the ISIN-keyed pull missed rows. SC_CODE/symbol matching avoids it.

### 3. BSE `api.bseindia.com` JSON endpoints — partial, not used for history
- `StockReachGraph/w?...&flag=12M` (HTTP 200, UA+Referer) → **intraday tick** data only
  (`dttm/vale1/vole`), not historical daily OHLC. Useless for 2006–2019 listing days.
- `getScripHeaderData/w` (HTTP 200) → current quote + SEO slug; good ISIN/code→name bridge, no history.
- `StockPriceCSVDownload/w` → empty body; `StockPriceHistory/w` → 302 to error page. Dead.
- Consistent with `docs/sources.md` "BSE official IPO API … Akamai" note — the **download/BhavCopy
  static archive (source 1) is the live path**, not the api.bseindia.com JSON history endpoints.

### 4. Not retried (already on the project's dead-list, confirmed still applicable)
Yahoo (no Indian SME), trendlyne, moneycontrol financials, ipocentral. screener.in weekly is the
*origin* of the NLE files and by definition starts too late — the BSE bhavcopy beats it for the
listing day, so no need to re-query screener by name.

---

## CONCRETE RECOVERY PLAN

**Source = BSE bhavcopy archive (source 1 above). It recovers 67 of the 69 `none_listing_era`
listing rows and all 12 of the 26 no-price rows that genuinely lack a file = 79 stocks.**

What I already did (safe, documented — written to `docs/research/`, NOT `data/master`):
- Recovered the **listing-day OHLC** for all 79 → `docs/research/recovered_listing_day.csv`
  (columns: isin, bse_code, nse_symbol, company, type, gap, listing_date, rec_date,
  open, high, low, close, volume, issue_price, chittor_listing_open, source=`bse_bhavcopy`).
- I did **not** write to `data/prices/` because: (a) the 67 NLE stocks already have a
  `screener_weekly` file and prepending one old daily row would create a misleading multi-year
  hole; (b) the 12 no-file stocks would become 1-row files indistinguishable from real history;
  (c) the schema has no `source` column to mark provenance. A single listing-day row is enough
  for **listing-pop** metrics but not for a real price series — see next.

To finish the recovery (a small pipeline task, kept out of scope here):
1. **For listing-pop metrics only** (Layer-3 listing-pop study): join
   `recovered_listing_day.csv` on ISIN to supply `listing_open/high/low/close`, recompute
   `listing_gain_open/close` against `issue_price` (adjust by split factor where Chittorgarh ÷
   recovered open ≥ 1.5), and set `listing_metrics_status='recovered_bse_bhavcopy'`.
2. **For full price series** (return/alpha horizons): the bhavcopy is whole-market, so true
   backfill = re-running `scrapers/bhavcopy_ohlc.py` for these stocks **keyed by SC_CODE /
   symbol instead of ISIN** over their listing→present date span (union ≈ 5,000 trading days
   since 2006-04-26). That is the existing pipeline's job; the only change needed is to add an
   SC_CODE match path (the legacy `EQ_ISINCODE` file already carries both `SC_CODE` and
   `ISIN_CODE`, and the pre-2014 `EQ<DDMMYY>_CSV.ZIP` extends the archive). Cheaper targeted
   alternative: fetch just the **listing week (≈5 trading days)** per stock, which is all the
   listing-pop event study needs.

Per-stock script to extend `recovered_listing_day.csv` into a listing-week window (re-uses
`bse_day()` above): iterate `range(0, 12)` calendar days from `listing_date`, collect each day
the SC_CODE is present, stop after 5 trading-day hits. Write to `data/prices/<isin>.csv` only for
the 12 no-file stocks (purely additive); for the 67 NLE stocks keep the recovered rows in the
research CSV and let the Layer-2 recompute merge them, to avoid the weekly-series gap.

### Not source-recoverable (flag for manual review)
- **2 NLE misses** — `INE02WG01024 / 543449` Wonder Fibromats (listing 2019-08-06) and
  `INE652Z01025 / 543512` Avon Moldplast (listing 2018-07-26): their recorded BSE code does not
  exist in the bhavcopy on/around the recorded listing_date (543xxx codes were allotted ~2021+),
  so either the `bse_script_code` or the `listing_date` in `universe.csv` is wrong. Name-search
  in the bhavcopy returned only false positives (Wonderla 538268). **Do NOT guess a code/ISIN
  match** — flag for manual identity fix, then re-run the recovery.

### Non-gaps (no sourcing needed — recorded so they aren't re-investigated)
- 73 `bhavcopy_daily` Gap-1 stocks: listing-day data already in `data/prices/`. Re-evaluate the
  `listing_remediation.py` scale/anchor branch instead of fetching anything.
- 14 Gap-2 stocks with full files (Tech Mahindra, Sun TV, Allcargo, …): fix the Layer-2 join
  (blank `listing_date` / FPO / duplicate-ISIN handling); the prices exist.
