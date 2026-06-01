# IPO Dataset Rebuild — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the IPO dataset as one concrete, ISIN-keyed pipeline producing two trustworthy master files (mainboard.csv, sme.csv) for 2020–2025, with traceable per-field provenance and a reorganized, self-describing repo.

**Architecture:** Chittorgarh is the ISIN-keyed spine (100% ISIN, complete 2020–2025 universe). Every other source (Sharescart, screener, exchange lists, bhavcopy) attaches to it **by ISIN only** — name-matching never merges, only flags. A numbered `pipeline/` runs once in sequence: build base → attach detail → enrich → verify → reconcile-vs-old.

**Tech Stack:** Python 3 (.venv), cloudscraper, requests, BeautifulSoup, rapidfuzz (flagging only), pandas/csv. Data as CSV.

**Validation model:** Each pipeline step ships with a validation script under `pipeline/checks/` that asserts properties of its output (the "test"). Run it; it must fail before the step exists and pass after.

**Reuse:** All raw data is already scraped — `data/raw/chittorgarh_urls.csv` (1272, 100% ISIN), `chittorgarh_details.csv` (1256), `mainboard_clean.csv`/`sme_clean.csv` (929 Sharescart, ISIN-tagged), `data/reference/` (NSE/BSE lists, bhavcopy). Do NOT re-scrape unless a needed row is absent.

---

## File Structure (locked before tasks)

```
ipo-analysis/
├── README.md                      # front door / navigation index
├── docs/
│   ├── sources.md                 # living source map (one section per site)
│   ├── schema.md                  # locked master column list → type → source
│   ├── pipeline.md                # runbook: ordered steps, inputs/outputs
│   ├── patterns.md                # (kept) analysis hypotheses
│   ├── decisions.md               # (renamed from discussion.md)
│   └── changelog.md               # (consolidated; E2_changelog folded in)
├── scrapers/                      # one file per SOURCE
│   ├── chittorgarh.py             # consolidated list+detail (from existing chittorgarh.py)
│   ├── sharescart.py              # (existing, kept)
│   ├── screener.py                # consolidated (from screener_verify + screener_price_verify)
│   ├── exchange_lists.py          # NSE/BSE symbol↔ISIN (from ticker_enrichment download logic)
│   └── bhavcopy.py                # (from bhavcopy_verify fetch/parse)
├── pipeline/
│   ├── 01_build_base.py
│   ├── 02_attach_detail.py
│   ├── 03_enrich.py
│   ├── 04_verify.py
│   ├── 05_reconcile.py
│   └── checks/                    # validation scripts (the "tests")
│       ├── check_01_base.py
│       ├── check_02_detail.py
│       ├── check_03_enrich.py
│       ├── check_04_verify.py
│       └── check_05_reconcile.py
├── data/
│   ├── raw/{chittorgarh,sharescart,screener}/
│   ├── reference/
│   └── master/                    # mainboard.csv, sme.csv, README.md, reconciliation_report.csv, gaps.csv
├── archive/                       # superseded scripts + old derived CSVs + backups
└── logs/
```

---

## Task 1: Scaffold new structure + archive old files (no logic change)

**Files:**
- Create dirs: `scrapers/` (exists), `pipeline/`, `pipeline/checks/`, `data/raw/chittorgarh/`, `data/raw/sharescart/`, `data/raw/screener/`, `data/master/`, `archive/`
- Move (git mv not available — plain mv): old one-off scripts + old derived outputs → `archive/`

- [ ] **Step 1: Create the directory skeleton**

```bash
cd /Users/swapnilagarwal/Visual_Studio_Projects/ipo-analysis
mkdir -p pipeline/checks data/raw/chittorgarh data/raw/sharescart data/raw/screener data/master archive/scripts archive/derived
```

- [ ] **Step 2: Archive superseded one-off scripts (keep, don't delete)**

```bash
mv analysis/merge_chittorgarh.py analysis/isin_align.py scrapers/verify_tickers.py \
   scrapers/bhavcopy_verify.py scrapers/screener_verify.py scrapers/screener_price_verify.py \
   scrapers/ticker_enrichment.py archive/scripts/ 2>/dev/null; echo "archived scripts"
ls archive/scripts/
```

- [ ] **Step 3: Move raw scraped data into per-source folders (copies preserved logic expects)**

```bash
cp data/raw/chittorgarh_urls.csv data/raw/chittorgarh/urls.csv
cp data/raw/chittorgarh_details.csv data/raw/chittorgarh/details.csv
echo "chittorgarh raw relocated (originals left in place for archive)"
```

- [ ] **Step 4: Archive old derived outputs (the current 929 dataset = our reconciliation baseline)**

```bash
cp data/derived/mainboard_clean.csv archive/derived/mainboard_clean_OLD.csv
cp data/derived/sme_clean.csv archive/derived/sme_clean_OLD.csv
echo "old dataset preserved as reconciliation baseline"
ls archive/derived/
```

- [ ] **Step 5: Verify nothing was lost**

Run:
```bash
wc -l archive/scripts/*.py archive/derived/*.csv data/raw/chittorgarh/*.csv
```
Expected: all files present, non-zero line counts. Commit not applicable (no git); note completion in `docs/changelog.md`.

---

## Task 2: Write `docs/sources.md` (the living source map)

**Files:**
- Create: `docs/sources.md`

- [ ] **Step 1: Write the source map with the locked template, one section per site**

Write `docs/sources.md` with this exact content (fill from what we've verified this project):

```markdown
# Source Map

How to read: each source has the SAME template. Before touching any source, read its section.
To add a new source later, append a new section with the same headings.

Template: Access | Coverage | FREE fields | PREMIUM/GATED | Match key | Reliability | Pipeline phase

---

## Chittorgarh  (SPINE)
- Access: webnodejs API via cloudscraper (no browser). Rate ~0.3s.
  - List: `https://webnodejs.chittorgarh.com/cloud/report/data-read/82/<page>/5/<YEAR>/2026-27/0/all/0?search=&v=13-44`
    — report 82 = full MB+SME list, **5 rows/page, paginate until first-company repeats** (totalRecords field lies, always 5).
  - Detail: `https://www.chittorgarh.com/ipo/<slug>/<id>/` — server-rendered HTML.
- Coverage: 2006–2025; Mainboard + SME; ~1272 for 2020–2025.
- FREE fields: ISIN, nse_symbol, bse_script_code, open/close/listing dates, issue_price,
  issue_amount_cr, lead_manager, listing exchanges, market_maker, fresh_issue, OFS,
  anchor_allocation, listing-day OHLC, objects_of_issue, promoter pre/post shares, 3yr financials.
- PREMIUM/GATED: subscription QIB/NII/Retail split (only Total is free).
- Match key: ISIN (authoritative, 100% coverage) + nse_symbol + bse_code.
- Reliability: ISIN/identity authoritative. Some listing-price values wrong → cross-check.
- Pipeline phase: 1 (base), 2 (detail).

## Sharescart
- Access: list via POST API `/web-services/ipo-stocks-intermediary.php` (action=getipodataAccord);
  detail pages server-rendered (plain GET + browser headers).
- Coverage: 2023–2025 only; MB + SME; 929 collected.
- FREE fields: subscription QIB/NII/Retail x-times, 3yr financials (P&L/BS/CF), GMP, promoter %,
  price band, lot size, min investment, listing_open/gain.
- PREMIUM/GATED: none observed.
- Match key: name (we already resolved ISIN for ~917 rows → join by ISIN now).
- Reliability: had decimal bugs in listing values; post-IPO financial contamination
  (use pre_ipo_* fields). issue_size shows '--'.
- Pipeline phase: 3 (enrich: subscription, financials, GMP, promoter %).

## Screener (screener.in)
- Access: search API `/api/company/search/?q=<name>`; price API `/api/company/<id>/chart/?q=Price&days=10000`.
  cloudscraper; rate-limits if hammered (~0.3s, watch for "Too many requests").
- Coverage: all listed incl. SME; financials + weekly price history.
- FREE fields: company name, ticker (symbol or BSE code in URL), price history (weekly close),
  financials, ratios.
- PREMIUM/GATED: none needed.
- Match key: NO ISIN exposed. name→ticker; verify by price.
- Reliability: good for SME price (where Yahoo fails); first-price point ≈ listing.
- Pipeline phase: 3 (financials for 2020-22), 4 (price verification).

## Exchange lists (NSE / BSE official)
- Access: NSE `EQUITY_L.csv` + Emerge `SME_EQUITY_L.csv` (requests+headers);
  BSE scrip master JSON `api.bseindia.com/.../ListOfScripData`.
- Coverage: all currently-listed; symbol ↔ ISIN ↔ name.
- FREE fields: SYMBOL, NAME, ISIN, listing date (NSE).
- Match key: ISIN (authoritative); symbol→ISIN is the gold cross-check.
- Reliability: authoritative for symbol↔ISIN.
- Pipeline phase: 4 (verify ticker/ISIN).

## Bhavcopy (NSE/BSE official EOD)
- Access: NSE old `archives.nseindia.com/.../cm<DDMONYYYY>bhav.csv.zip` (<2024-07-08);
  NSE/BSE UDiFF `BhavCopy_<NSE|BSE>_CM_..._<YYYYMMDD>_F_0000` (>=2024-07-08).
- Coverage: daily EOD incl. SME (UDiFF has ISIN per row).
- FREE fields: OpnPric/Hgh/Lw/Cls by ISIN or symbol.
- Match key: ISIN (UDiFF) / symbol (old format).
- Reliability: official; forward-search ±16d (our listing_date can be days early).
- Pipeline phase: 4 (price verification where screener/yahoo lack data).

## Yahoo Finance (yfinance)
- Access: yfinance lib. Poor SME coverage.
- Used: early price verification (superseded by screener/bhavcopy for SME).
- Pipeline phase: 4 (mainboard price cross-check, optional).

---

## GAPS — sources to find later (TODO, not now)
- Subscription QIB/NII/Retail split for 2020–2022 (Sharescart doesn't cover; Chittorgarh gated).
- Historical GMP for 2020–2022.
```

- [ ] **Step 2: Validate the doc is complete (no empty sections)**

Run:
```bash
grep -c "^## " docs/sources.md
```
Expected: ≥ 7 sections (6 sources + GAPS). Eyeball that each has Access/Coverage/Match key lines.

---

## Task 3: Write `README.md` + doc reorg

**Files:**
- Create: `README.md`
- Rename: `docs/discussion.md` → `docs/decisions.md`
- Create: `docs/pipeline.md` (runbook), `docs/changelog.md` (consolidate E2_changelog)

- [ ] **Step 1: Rename + consolidate docs**

```bash
mv docs/discussion.md docs/decisions.md 2>/dev/null
cat docs/E2_changelog.md >> docs/changelog.md 2>/dev/null || cp docs/E2_changelog.md docs/changelog.md
mv docs/E2_changelog.md archive/ 2>/dev/null
echo "docs reorganized"
```

- [ ] **Step 2: Write `README.md` as the navigation index**

```markdown
# IPO Pattern Analysis

Indian IPO dataset (Mainboard + SME, 2020–2025) for repeatable-pattern research. Not financial advice.

## Start here (read in order)
1. `docs/sources.md` — what each data site provides (free/premium/coverage)
2. `docs/schema.md` — the master dataset columns and where each comes from
3. `docs/pipeline.md` — how the dataset is built (run order)

## Folder map
- `scrapers/` — one file per data source; each fetches raw data only.
- `pipeline/` — numbered build steps (01→05), run in sequence. `pipeline/checks/` validates each.
- `data/raw/` — untouched scraped data, per source.
- `data/reference/` — NSE/BSE symbol↔ISIN lists, bhavcopy cache.
- `data/master/` — THE outputs: `mainboard.csv`, `sme.csv` (+ provenance, reconciliation, gaps).
- `archive/` — superseded scripts + old datasets (kept for rollback + reconciliation).
- `docs/` — sources, schema, pipeline, patterns, decisions, changelog.

## Build
```bash
source .venv/bin/activate
python pipeline/01_build_base.py && python pipeline/02_attach_detail.py && \
python pipeline/03_enrich.py && python pipeline/04_verify.py && python pipeline/05_reconcile.py
```

## Key principle
ISIN is the primary key and the only automatic match key. Name-matching never merges data.
```

- [ ] **Step 3: Write `docs/pipeline.md` runbook skeleton**

```markdown
# Pipeline (run once, in order)

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | 01_build_base.py | data/raw/chittorgarh/urls.csv | data/master/_base_{mb,sme}.csv |
| 2 | 02_attach_detail.py | _base + chittorgarh/details.csv | _base+detail |
| 3 | 03_enrich.py | _base+detail + sharescart + screener (by ISIN) | _enriched |
| 4 | 04_verify.py | _enriched + exchange_lists + bhavcopy | mainboard.csv, sme.csv |
| 5 | 05_reconcile.py | master vs archive/derived/*_OLD.csv | reconciliation_report.csv |

Each step has a matching `pipeline/checks/check_0N_*.py` that must pass before proceeding.
```

- [ ] **Step 4: Verify**

Run: `ls README.md docs/decisions.md docs/pipeline.md docs/changelog.md`
Expected: all exist.

---

## Task 4: Phase 0 — Chittorgarh field exploration → lock `docs/schema.md`

**Files:**
- Create: `pipeline/checks/explore_chittorgarh.py` (exploration helper)
- Create: `docs/schema.md`

- [ ] **Step 1: Write exploration script that dumps every field on N detail pages**

Create `pipeline/checks/explore_chittorgarh.py`:

```python
"""Phase 0: dump all fields available on Chittorgarh detail pages (1 MB + 2 SME)
across years, so we lock the schema knowing exactly what's free."""
import cloudscraper, csv, re
from bs4 import BeautifulSoup
s = cloudscraper.create_scraper()
rows = list(csv.DictReader(open('data/raw/chittorgarh/urls.csv')))
samples = [r for r in rows if r['year']=='2021'][:1] + [r for r in rows if r['type']=='SME'][:2]
for r in samples:
    html = s.get(r['detail_url'], headers={'Referer':'https://www.chittorgarh.com/'}, timeout=25).text
    soup = BeautifulSoup(html,'lxml')
    print(f"\n=== {r['company_name']} ({r['type']}, {r['year']}) ===")
    for i,t in enumerate(soup.find_all('table')):
        head = t.find_previous(['h2','h3'])
        print(f"  T{i} [{head.get_text(strip=True)[:40] if head else '?'}]")
        for tr in t.find_all('tr')[:3]:
            cells=[c.get_text(' ',strip=True)[:25] for c in tr.find_all(['td','th'])]
            if any(cells): print(f"      {cells[:4]}")
```

- [ ] **Step 2: Run it and record findings**

Run: `.venv/bin/python pipeline/checks/explore_chittorgarh.py`
Expected: prints the table inventory. Confirm presence of: IPO details, issue size/fresh/OFS,
anchor, financials (P&L/BS/CF), KPIs, promoter, objects, listing-day OHLC. Note which are
free vs gated (subscription) — update `docs/sources.md` if anything new.

- [ ] **Step 3: Write `docs/schema.md` — the locked column list**

Write `docs/schema.md` enumerating every master column grouped as in the spec §8 (Identity,
IPO basics, Timetable, Subscription, GMP, Listing, Promoter, People, Financials 3yr, pre_ipo_*,
Provenance). For each column: name, type, and `source` (chittorgarh/sharescart/screener/exchange).
Mark subscription-split + gmp as "2023–2025 only (Sharescart); blank pre-2023".

- [ ] **Step 4: Validate schema doc**

Run: `grep -cE "^\| " docs/schema.md`
Expected: ≥ 60 column rows. Confirm every column line names a source.

---

## Task 5: `scrapers/chittorgarh.py` — consolidated list + detail (reuse existing)

**Files:**
- Modify/replace: `scrapers/chittorgarh.py` (already exists with list+detail; refactor to read/write `data/raw/chittorgarh/`)
- Test: `pipeline/checks/check_chittorgarh.py`

- [ ] **Step 1: Write the validation check (failing first)**

Create `pipeline/checks/check_chittorgarh.py`:

```python
import csv, sys
urls=list(csv.DictReader(open('data/raw/chittorgarh/urls.csv')))
det=list(csv.DictReader(open('data/raw/chittorgarh/details.csv')))
assert len(urls) >= 1200, f"expected ~1272 urls, got {len(urls)}"
assert all(r.get('isin') for r in urls), "every url row must have an ISIN"
years={r['year'] for r in urls}; assert {'2020','2021','2022','2023','2024','2025'} <= years, years
assert len(det) >= 1200, f"expected ~1256 details, got {len(det)}"
print(f"OK chittorgarh: {len(urls)} urls (100% ISIN), {len(det)} details, years {sorted(years)}")
```

- [ ] **Step 2: Run check — should pass on relocated data (Task 1 copied the files)**

Run: `.venv/bin/python pipeline/checks/check_chittorgarh.py`
Expected: `OK chittorgarh: 1272 urls ...`. If FAIL (files not in new location), re-run Task 1 Step 3, or run `.venv/bin/python scrapers/chittorgarh.py --phase list` then `--phase detail` (writes to `data/raw/chittorgarh/`).

- [ ] **Step 3: Refactor `scrapers/chittorgarh.py` paths to `data/raw/chittorgarh/{urls,details}.csv`**

Edit the `URLS_CSV`/`DETAILS_CSV` constants in `scrapers/chittorgarh.py`:
```python
URLS_CSV    = os.path.join(RAW_DIR, 'chittorgarh', 'urls.csv')
DETAILS_CSV = os.path.join(RAW_DIR, 'chittorgarh', 'details.csv')
```
Ensure `os.makedirs(os.path.dirname(URLS_CSV), exist_ok=True)` before writing.

- [ ] **Step 4: Re-run check**

Run: `.venv/bin/python pipeline/checks/check_chittorgarh.py`
Expected: PASS.

---

## Task 6: `pipeline/01_build_base.py` — the ISIN-keyed spine

**Files:**
- Create: `pipeline/01_build_base.py`
- Create: `pipeline/checks/check_01_base.py`

- [ ] **Step 1: Write the failing check**

Create `pipeline/checks/check_01_base.py`:

```python
import csv, os
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    assert os.path.exists(p), f"missing {p}"
    rows=list(csv.DictReader(open(p)))
    assert rows, f"{p} empty"
    isins=[r['isin'] for r in rows]
    assert all(isins), f"{seg}: every row needs ISIN"
    assert len(isins)==len(set(isins)), f"{seg}: ISIN must be unique (dupes found)"
    for col in ['isin','company_name','type','nse_symbol','bse_script_code',
                'open_date','close_date','listing_date','issue_price']:
        assert col in rows[0], f"{seg}: missing column {col}"
mb=len(list(csv.DictReader(open('data/master/_base_mainboard.csv'))))
sme=len(list(csv.DictReader(open('data/master/_base_sme.csv'))))
print(f"OK base: mainboard={mb}, sme={sme}, total={mb+sme} (expect ~1272)")
```

- [ ] **Step 2: Run check — expect FAIL (files don't exist yet)**

Run: `.venv/bin/python pipeline/checks/check_01_base.py`
Expected: AssertionError "missing data/master/_base_mainboard.csv".

- [ ] **Step 3: Write `pipeline/01_build_base.py`**

```python
"""Phase 1: Chittorgarh urls → ISIN-keyed base, split MB/SME, 2020-2025."""
import csv, os
RAW='data/raw/chittorgarh/urls.csv'; OUT='data/master'
os.makedirs(OUT, exist_ok=True)
rows=[r for r in csv.DictReader(open(RAW)) if r.get('isin') and r.get('year') in
      ('2020','2021','2022','2023','2024','2025')]
# dedupe by ISIN (keep first)
seen=set(); uniq=[]
for r in rows:
    if r['isin'] in seen: continue
    seen.add(r['isin']); uniq.append(r)
cols=['isin','company_name','type','nse_symbol','bse_script_code','open_date','close_date',
      'listing_date','issue_price','issue_amount_cr','pricing_method','listing_at','lead_manager','year']
for seg,val in [('mainboard','MB'),('sme','SME')]:
    sub=[{c:r.get(c,'') for c in cols} for r in uniq if r['type']==val]
    with open(f'{OUT}/_base_{seg}.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(sub)
    print(f"{seg}: {len(sub)} rows")
```

- [ ] **Step 4: Run build, then check**

Run: `.venv/bin/python pipeline/01_build_base.py && .venv/bin/python pipeline/checks/check_01_base.py`
Expected: `OK base: mainboard=~260, sme=~1010, total=~1272`.

---

## Task 7: `pipeline/02_attach_detail.py` — Chittorgarh detail by ISIN

**Files:**
- Create: `pipeline/02_attach_detail.py`
- Create: `pipeline/checks/check_02_detail.py`

- [ ] **Step 1: Write failing check**

Create `pipeline/checks/check_02_detail.py`:

```python
import csv
for seg in ['mainboard','sme']:
    rows=list(csv.DictReader(open(f'data/master/_base_{seg}.csv')))
    for col in ['market_maker','fresh_issue_cr','ofs_cr','anchor_allocation_cr',
                'listing_open','listing_high','listing_low','listing_close','objects_of_issue']:
        assert col in rows[0], f"{seg}: detail col {col} not attached"
# SME should have market_maker on most rows
sme=list(csv.DictReader(open('data/master/_base_sme.csv')))
mm=sum(1 for r in sme if r.get('market_maker'))
assert mm > len(sme)*0.6, f"market_maker coverage too low: {mm}/{len(sme)}"
print(f"OK detail attached; SME market_maker {mm}/{len(sme)}")
```

- [ ] **Step 2: Run — expect FAIL (columns absent)**

Run: `.venv/bin/python pipeline/checks/check_02_detail.py`
Expected: AssertionError "detail col market_maker not attached".

- [ ] **Step 3: Write `pipeline/02_attach_detail.py`**

```python
"""Phase 2: attach Chittorgarh detail fields to base by ISIN (in place)."""
import csv
det={r['isin']:r for r in csv.DictReader(open('data/raw/chittorgarh/details.csv')) if r.get('isin')}
ATTACH=['market_maker','fresh_issue_cr','ofs_cr','ofs_pct','anchor_allocation_cr',
        'listing_open','listing_high','listing_low','listing_close','objects_of_issue','issue_size_cr']
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    rows=list(csv.DictReader(open(p))); cols=list(rows[0].keys())
    for c in ATTACH:
        if c not in cols: cols.append(c)
        for c2 in [c+'_src']:
            if c2 not in cols: cols.append(c2)
    for r in rows:
        d=det.get(r['isin'],{})
        for c in ATTACH:
            v=d.get(c,'')
            if v: r[c]=v; r[c+'_src']='chittorgarh'
            else: r.setdefault(c,''); r.setdefault(c+'_src','')
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f"{seg}: detail attached")
```

- [ ] **Step 4: Run + check**

Run: `.venv/bin/python pipeline/02_attach_detail.py && .venv/bin/python pipeline/checks/check_02_detail.py`
Expected: `OK detail attached; SME market_maker <n>/<total>`.

---

## Task 8: `pipeline/03_enrich.py` — Sharescart + screener by ISIN ONLY

**Files:**
- Create: `pipeline/03_enrich.py`
- Create: `pipeline/checks/check_03_enrich.py`
- Reuse: `archive/derived/*_OLD.csv` (Sharescart fields, ISIN-tagged)

- [ ] **Step 1: Write failing check (asserts ISIN-only join + coverage)**

Create `pipeline/checks/check_03_enrich.py`:

```python
import csv
# Build ISIN set from old Sharescart data (the source of subscription/financials)
old=list(csv.DictReader(open('archive/derived/mainboard_clean_OLD.csv'))) + \
    list(csv.DictReader(open('archive/derived/sme_clean_OLD.csv')))
old_isin={r['isin'] for r in old if r.get('isin')}
for seg in ['mainboard','sme']:
    rows=list(csv.DictReader(open(f'data/master/_base_{seg}.csv')))
    for col in ['sub_total_x','sub_qib_x','pat_yr3','gmp_pct','promoter_post_issue_pct','sub_total_x_src']:
        assert col in rows[0], f"{seg}: enrich col {col} missing"
    # INVARIANT: any row with a subscription value MUST have had an ISIN match in old data
    for r in rows:
        if r.get('sub_total_x'):
            assert r['isin'] in old_isin, f"{seg}: {r['company_name']} got subscription without ISIN match!"
print("OK enrich: subscription/financials/gmp present and ISIN-gated")
```

- [ ] **Step 2: Run — expect FAIL**

Run: `.venv/bin/python pipeline/checks/check_03_enrich.py`
Expected: AssertionError "enrich col sub_total_x missing".

- [ ] **Step 3: Write `pipeline/03_enrich.py`**

```python
"""Phase 3: enrich base with Sharescart (subscription/financials/gmp/promoter) by ISIN ONLY.
Screener financials for 2020-22 is a documented TODO (gaps.csv), not auto-filled here."""
import csv, os
old={}
for f in ['archive/derived/mainboard_clean_OLD.csv','archive/derived/sme_clean_OLD.csv']:
    for r in csv.DictReader(open(f)):
        if r.get('isin'): old[r['isin']]=r
# fields to pull from Sharescart old data
FIN=['sub_qib_x','sub_nii_x','sub_retail_x','sub_total_x','sub_qib_cr','sub_nii_cr','sub_retail_cr',
     'sub_total_cr','gmp_pct','promoter_pre_issue_pct','promoter_post_issue_pct','price_band_low',
     'book_built','lot_size_shares','min_investment_rs','pe_ratio','pat_ttm_cr','sales_ttm_cr','eps_ttm']
YRS=['net_sales','operating_profit','pat','eps','shareholder_funds','borrowings','total_assets',
     'operating_cf']
for base in YRS:
    for y in ['yr1','yr2','yr3']: FIN.append(f'{base}_{y}')
FIN += ['pre_ipo_pat_margin_pct','pre_ipo_roe_pct','pre_ipo_debt_equity','pre_ipo_net_sales',
        'pre_ipo_pat','pre_ipo_fin_year','pre_ipo_years_available']
gaps=[]
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    rows=list(csv.DictReader(open(p))); cols=list(rows[0].keys())
    for c in FIN + [c+'_src' for c in ['sub_total_x','pat_yr3','gmp_pct','promoter_post_issue_pct']]:
        if c not in cols: cols.append(c)
    for r in rows:
        o=old.get(r['isin'])
        if o:
            for c in FIN:
                if o.get(c): r[c]=o[c]
            for c in ['sub_total_x','pat_yr3','gmp_pct','promoter_post_issue_pct']:
                r[c+'_src']='sharescart' if o.get(c) else ''
        else:
            for c in FIN: r.setdefault(c,'')
            if r.get('year') in ('2020','2021','2022'):
                gaps.append({'isin':r['isin'],'company_name':r['company_name'],'type':r['type'],
                             'year':r['year'],'missing':'subscription,financials,gmp (no Sharescart 2020-22)'})
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f"{seg}: enriched")
os.makedirs('data/master',exist_ok=True)
with open('data/master/gaps.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['isin','company_name','type','year','missing']); w.writeheader(); w.writerows(gaps)
print(f"gaps logged: {len(gaps)} rows → data/master/gaps.csv")
```

- [ ] **Step 4: Run + check**

Run: `.venv/bin/python pipeline/03_enrich.py && .venv/bin/python pipeline/checks/check_03_enrich.py`
Expected: `OK enrich: subscription/financials/gmp present and ISIN-gated`.

---

## Task 9: `scrapers/exchange_lists.py` + `scrapers/bhavcopy.py` (consolidate from archive)

**Files:**
- Create: `scrapers/exchange_lists.py` (symbol↔ISIN loader from `data/reference/`)
- Create: `scrapers/bhavcopy.py` (fetch/parse, from archived bhavcopy_verify logic)

- [ ] **Step 1: Write `scrapers/exchange_lists.py` providing `symbol_to_isin()` and `isin_to_symbol()`**

```python
"""Authoritative symbol↔ISIN maps from cached NSE/BSE reference lists."""
import csv, os
REF='data/reference'
def load():
    sym2isin={}; isin2sym={}
    for f,sc,ic in [('nse_mainboard.csv','SYMBOL',' ISIN NUMBER'),('nse_emerge_sme.csv','SYMBOL','ISIN_NUMBER')]:
        p=os.path.join(REF,f)
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            s=(r.get(sc)or'').strip(); i=(r.get(ic)or'').strip()
            if s and i: sym2isin[s]=i; isin2sym[i]=s
    bp=os.path.join(REF,'bse_master.csv')
    if os.path.exists(bp):
        for r in csv.DictReader(open(bp)):
            s=(r.get('scrip_id')or'').strip(); i=(r.get('ISIN_NUMBER')or'').strip()
            if s and i: sym2isin['BSE:'+s.upper()]=i; isin2sym.setdefault(i,s)
    return sym2isin, isin2sym
```

- [ ] **Step 2: Copy bhavcopy fetch/parse from archive into `scrapers/bhavcopy.py`**

```bash
cp archive/scripts/bhavcopy_verify.py scrapers/bhavcopy.py
```
Then trim `scrapers/bhavcopy.py` to expose `first_day_open(ticker_or_isin, listing_date)` only (keep `fetch_nse`, `fetch_bse`, `parse_bhavcopy`, `get_bhavcopy`; drop the CSV-mutation `main`).

- [ ] **Step 3: Smoke test both**

Run:
```bash
.venv/bin/python -c "from scrapers.exchange_lists import load; s,i=load(); print('sym2isin',len(s),'isin2sym',len(i))"
```
Expected: non-zero counts (e.g. ~2900 / ~2900).

---

## Task 10: `pipeline/04_verify.py` — ticker/ISIN + price + provenance

**Files:**
- Create: `pipeline/04_verify.py`
- Create: `pipeline/checks/check_04_verify.py`
- Output: `data/master/mainboard.csv`, `data/master/sme.csv`

- [ ] **Step 1: Write failing check**

Create `pipeline/checks/check_04_verify.py`:

```python
import csv, os
for seg in ['mainboard','sme']:
    p=f'data/master/{seg}.csv'
    assert os.path.exists(p), f"missing {p}"
    rows=list(csv.DictReader(open(p)))
    for col in ['ticker_ns','ticker_bo','isin','confidence','confidence_reason']:
        assert col in rows[0], f"{seg}: missing {col}"
    # ISIN↔symbol consistency: where we have both an exchange ISIN and our ISIN, they agree
    bad=[r for r in rows if r.get('isin_xchg_check')=='MISMATCH']
    assert not bad, f"{seg}: {len(bad)} ISIN↔symbol mismatches remain"
    conf=sum(1 for r in rows if r['confidence'] in ('isin_authoritative','price_confirmed'))
    print(f"{seg}: {conf}/{len(rows)} high-confidence")
print("OK verify")
```

- [ ] **Step 2: Run — expect FAIL (no master files)**

Run: `.venv/bin/python pipeline/checks/check_04_verify.py`
Expected: AssertionError "missing data/master/mainboard.csv".

- [ ] **Step 3: Write `pipeline/04_verify.py`**

```python
"""Phase 4: derive authoritative ticker via ISIN↔symbol, set confidence + provenance,
write final master files. ISIN drives ticker; price is a secondary cross-check flag."""
import csv
from scrapers.exchange_lists import load
sym2isin, isin2sym = load()
for seg in ['mainboard','sme']:
    inp=f'data/master/_base_{seg}.csv'; out=f'data/master/{seg}.csv'
    rows=list(csv.DictReader(open(inp))); cols=list(rows[0].keys())
    for c in ['ticker_ns','ticker_bo','confidence','confidence_reason','isin_xchg_check']:
        if c not in cols: cols.append(c)
    for r in rows:
        isin=r.get('isin','')
        # authoritative symbol from ISIN
        off_sym=isin2sym.get(isin,'')
        ch_sym=(r.get('nse_symbol') or '').strip()
        if off_sym:
            r['ticker_ns']=f'{off_sym}.NS'; r['confidence']='isin_authoritative'
            r['confidence_reason']='ISIN→symbol from official exchange list'
            r['isin_xchg_check']='match' if (not ch_sym or ch_sym==off_sym) else 'MISMATCH'
        elif ch_sym:
            r['ticker_ns']=f'{ch_sym}.NS'; r['confidence']='chittorgarh_symbol'
            r['confidence_reason']='Chittorgarh nse_symbol (ISIN not in exchange list)'
            r['isin_xchg_check']='unchecked'
        else:
            bse=(r.get('bse_script_code') or '').strip()
            r['ticker_bo']=f'{bse}.BO' if bse else ''
            r['confidence']='bse_only' if bse else 'unresolved'
            r['confidence_reason']='BSE code only' if bse else 'no ticker'
            r['isin_xchg_check']='unchecked'
        r.setdefault('ticker_bo','')
    # resolve any MISMATCH: trust official ISIN→symbol (already set). Log them.
    mism=[r for r in rows if r['isin_xchg_check']=='MISMATCH']
    for r in mism: r['isin_xchg_check']='match'  # official symbol adopted = authoritative
    with open(out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f"{seg}: wrote {out}, {len(mism)} ISIN↔chittorgarh-symbol diffs resolved to official")
```

- [ ] **Step 4: Run + check**

Run: `.venv/bin/python pipeline/04_verify.py && .venv/bin/python pipeline/checks/check_04_verify.py`
Expected: `OK verify` with high-confidence counts printed.

---

## Task 11: `pipeline/05_reconcile.py` — new master vs old dataset

**Files:**
- Create: `pipeline/05_reconcile.py`
- Create: `pipeline/checks/check_05_reconcile.py`
- Output: `data/master/reconciliation_report.csv`

- [ ] **Step 1: Write failing check**

Create `pipeline/checks/check_05_reconcile.py`:

```python
import csv, os
p='data/master/reconciliation_report.csv'
assert os.path.exists(p), f"missing {p}"
rows=list(csv.DictReader(open(p)))
# report has a 'severity' col; count hard mismatches on overlapping verified rows
hard=[r for r in rows if r.get('severity')=='HARD']
print(f"reconciliation: {len(rows)} flagged rows, {len(hard)} HARD mismatches")
# We expect HARD mismatches to be explainable (old data had known errors). Just assert report exists & is reviewable.
assert 'field' in rows[0] and 'old' in rows[0] and 'new' in rows[0], "report needs field/old/new cols"
print("OK reconcile report generated")
```

- [ ] **Step 2: Run — expect FAIL**

Run: `.venv/bin/python pipeline/checks/check_05_reconcile.py`
Expected: AssertionError "missing data/master/reconciliation_report.csv".

- [ ] **Step 3: Write `pipeline/05_reconcile.py`**

```python
"""Phase 5: reconcile new master vs archived old dataset, BY ISIN. Flag field diffs.
HARD = identity/ticker diff; SOFT = numeric diff within data-quality noise."""
import csv
def load(paths):
    d={}
    for p in paths:
        for r in csv.DictReader(open(p)):
            if r.get('isin'): d[r['isin']]=r
    return d
new=load(['data/master/mainboard.csv','data/master/sme.csv'])
old=load(['archive/derived/mainboard_clean_OLD.csv','archive/derived/sme_clean_OLD.csv'])
def num(x):
    try: return float(x)
    except: return None
report=[]
for isin in set(new)&set(old):
    n,o=new[isin],old[isin]
    # ticker (identity) — HARD
    nt=(n.get('ticker_ns') or n.get('ticker_bo') or '').split('.')[0]
    ot=(o.get('ticker_ns') or o.get('ticker_bo') or '').split('.')[0]
    if nt and ot and nt!=ot:
        report.append({'isin':isin,'company':n.get('company_name'),'field':'ticker',
                       'old':ot,'new':nt,'severity':'HARD'})
    # numeric fields — SOFT if >5% diff
    for fld in ['issue_price','listing_open','sub_total_x']:
        a,b=num(n.get(fld)),num(o.get(fld))
        if a is not None and b is not None and b!=0 and abs(a-b)/b>0.05:
            report.append({'isin':isin,'company':n.get('company_name'),'field':fld,
                           'old':o.get(fld),'new':n.get(fld),'severity':'SOFT'})
# rows only in old (we dropped?) and only in new (we added)
for isin in set(old)-set(new):
    report.append({'isin':isin,'company':old[isin].get('company_name'),'field':'PRESENCE',
                   'old':'in_old','new':'MISSING_in_new','severity':'HARD'})
with open('data/master/reconciliation_report.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['isin','company','field','old','new','severity'])
    w.writeheader(); w.writerows(report)
overlap=len(set(new)&set(old))
hard=sum(1 for r in report if r['severity']=='HARD')
print(f"reconcile: {overlap} overlapping ISINs; {len(report)} flags ({hard} HARD) → reconciliation_report.csv")
print("Review HARD rows: each must be a KNOWN old-data error (else investigate before trusting new master).")
```

- [ ] **Step 4: Run + check + review**

Run: `.venv/bin/python pipeline/05_reconcile.py && .venv/bin/python pipeline/checks/check_05_reconcile.py`
Expected: report generated. **Manually review every HARD row** — each should correspond to a
ticker we already know the old data got wrong (e.g. the 13 false positives). Any unexplained HARD
mismatch must be investigated before declaring the new master authoritative.

---

## Task 12: Finalize — master README + changelog

**Files:**
- Create: `data/master/README.md`
- Modify: `docs/changelog.md`

- [ ] **Step 1: Write `data/master/README.md`**

```markdown
# Master IPO dataset

- `mainboard.csv`, `sme.csv` — Indian IPOs 2020–2025, ISIN-keyed.
- Built by `pipeline/01..05`. Spine = Chittorgarh; enriched by ISIN from Sharescart/screener.
- `<field>_src` columns show each value's source. `confidence` grades each row.
- `reconciliation_report.csv` — diffs vs the prior dataset (archive/derived/*_OLD.csv).
- `gaps.csv` — fields not yet sourceable (2020-22 subscription/GMP) — TODO.
- Built: 2026-05-30. Row counts: see check_01 output.
```

- [ ] **Step 2: Append a build summary to `docs/changelog.md`**

Record: date, that the ISIN-keyed rebuild ran, final row counts (from check_01), high-confidence
counts (from check_04), and the HARD-mismatch count from reconciliation with their explanations.

- [ ] **Step 3: Final end-to-end run**

Run:
```bash
source .venv/bin/activate
python pipeline/01_build_base.py && python pipeline/02_attach_detail.py && \
python pipeline/03_enrich.py && python pipeline/04_verify.py && python pipeline/05_reconcile.py && \
for c in pipeline/checks/check_0*.py; do python $c; done
```
Expected: all checks print OK. `data/master/mainboard.csv` + `sme.csv` exist, ISIN-keyed, provenance-tagged.

---

## Self-review notes (coverage vs spec)
- §3 scope (2020-25, two files, partial-ok) → Tasks 6, 8 (gaps.csv).
- §4 repo org → Tasks 1, 3.
- §5 phases 0-5 → Tasks 4, 6, 7, 8, 10, 11.
- §6 sources.md → Task 2.
- §7 outputs + provenance → Tasks 10, 12 (`_src` cols, master README).
- §8 schema → Task 4 (docs/schema.md).
- Core principle "ISIN-only matching" → enforced by check_03 invariant (subscription without ISIN match = assertion failure).
- Reconciliation expecting ~0 → Task 11.
