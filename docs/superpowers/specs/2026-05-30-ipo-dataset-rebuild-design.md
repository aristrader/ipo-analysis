# Design — IPO Dataset Rebuild (ISIN-keyed, single concrete pipeline)

**Date:** 2026-05-30
**Status:** Approved (design) — pending spec review
**Goal:** Replace the fragmented, name-matched dataset with ONE concrete, ISIN-keyed
pipeline that produces two trustworthy master files (mainboard, SME) for 2020–2025,
built once, with every field's source traceable, and a clean/navigable repo.

---

## 1. Why we're doing this

The current dataset grew organically: Sharescart as the base (name-matched to get tickers),
then patched with Chittorgarh/screener/bhavcopy. This produced:
- 3 fragmented lists (main 929, missing ~48, backfill 317)
- a name-match foundation that kept yielding wrong tickers/ISINs as we checked
- an incomplete IPO universe (missing ~40 real IPOs)

Root cause: **no reliable unique key at the center.** ISIN (unique per security) fixes this.
Chittorgarh provides ISIN for 100% of rows and the complete 2020–2025 universe, so it becomes
the spine; every other source attaches to it **by ISIN only**.

---

## 2. Core principles (non-negotiable)

1. **ISIN is the primary key and the ONLY automatic match key.** Name-matching is never used
   to merge data — at most it flags a row for human review.
2. **Build once, then stop moving data.** Exploration is allowed up front; once execution
   starts, the pipeline runs in order and produces final files. No iterative re-shuffling.
3. **Every value is traceable.** Key fields carry a `*_src` tag (chittorgarh/sharescart/screener/…).
4. **Fill where a concrete source exists; blank otherwise** — never guess. Unfillable gaps go to
   a TODO list to chase later (not now).
5. **Keep the old data; reconcile against it** as a final safety check (expect ~0 mismatches).
6. **Organized & self-describing repo** — a newcomer can navigate it with no guidance.

---

## 3. Scope

- **Years:** 2020–2025 (post-COVID boom; matches original project goal).
- **Segments:** Mainboard and SME kept as **two separate output files** (analysis differs).
- **2020–2022 reality:** Sharescart never covered these, so subscription-split / GMP will be
  blank there (screener can still supply financials). Accepted as partial; gaps → TODO.

---

## 4. Repository organization (target structure)

```
ipo-analysis/
├── README.md                # front door: goal, folder map, "read sources→schema→pipeline"
├── docs/
│   ├── sources.md           # THE source map — one section per site (see §6)
│   ├── schema.md            # locked master schema: every column → type → source
│   ├── pipeline.md          # ordered build steps + inputs/outputs (runbook)
│   ├── patterns.md          # analysis hypotheses (kept as-is)
│   ├── decisions.md         # why-we-chose log (renamed from discussion.md)
│   └── changelog.md         # consolidated history (E2_changelog folded in)
├── scrapers/                # ONE file per SOURCE; each documents what it provides + how
│   ├── chittorgarh.py
│   ├── sharescart.py
│   ├── screener.py
│   ├── exchange_lists.py    # NSE/BSE official symbol↔ISIN lists
│   └── bhavcopy.py
├── pipeline/                # ordered, run-once-in-sequence
│   ├── 01_build_base.py     # Chittorgarh spine → base (ISIN-keyed)
│   ├── 02_attach_detail.py  # Chittorgarh detail fields by ISIN
│   ├── 03_enrich.py         # Sharescart + screener fields by ISIN
│   ├── 04_verify.py         # ticker/ISIN/price verification + provenance
│   └── 05_reconcile.py      # new vs old → mismatch report
├── data/
│   ├── raw/{chittorgarh,sharescart,screener}/   # untouched scraped data
│   ├── reference/           # NSE/BSE lists, bhavcopy cache
│   └── master/              # OUTPUTS: mainboard.csv, sme.csv, README.md, provenance
├── archive/                 # superseded scripts + old CSVs (kept for rollback + reconcile)
└── logs/
```

**Cleanup:** old one-off scripts (`verify_tickers`, `bhavcopy_verify`, `screener_verify`,
`screener_price_verify`, `merge_chittorgarh`, `isin_align`, `ticker_enrichment`, `clean`) have
their logic consolidated into the new `scrapers/` + `pipeline/` files, then originals MOVE to
`archive/`. Old `data/derived/*` and `backups/` move to `archive/`. Nothing deleted.

---

## 5. The pipeline (6 phases, each runs once)

### Phase 0 — Exploration (no data written)
Thoroughly map every source into `docs/sources.md` (template in §6): for each source, the
access method, fields available, free vs premium/gated, year coverage, reliability notes.
**Output of this phase finalizes `docs/schema.md`** (the master column list) before any build.
Sources to map: Chittorgarh (list + detail), Sharescart, Screener, Exchange lists, Bhavcopy, Yahoo.

### Phase 1 — Base spine  (`pipeline/01_build_base.py`)
Reuse/refresh `data/raw/chittorgarh/urls.csv` (2020–2025, ~1272, 100% ISIN). Emit the base:
one row per IPO **keyed by ISIN**, with Chittorgarh identity fields (company_name, type, ISIN,
nse_symbol, bse_code, open/close/listing dates, issue_price, issue_amount_cr, lead_manager,
listing_exchanges). Split into mainboard/SME by Chittorgarh's Issue Category.

### Phase 2 — Chittorgarh detail fill  (`pipeline/02_attach_detail.py`)
Attach `data/raw/chittorgarh/details.csv` by ISIN: market_maker, fresh_issue, OFS, anchor,
listing OHLC, objects, plus any financials/KPIs Phase 0 confirms are free. Re-scrape detail
pages only for ISINs not already scraped.

### Phase 3 — Enrich by ISIN  (`pipeline/03_enrich.py`)
Left-join other sources onto the spine **by ISIN only**:
- Sharescart (existing `mainboard_clean`/`sme_clean`, which have ISIN): subscription split,
  3-yr financials, GMP, promoter %.
- Screener: financials for years Sharescart lacks (2020–2022); price history (for verify).
Each filled field gets a `<field>_src` tag. No ISIN match → leave blank (never guess).
Append unfillable gaps to a TODO section in `docs/sources.md` or a `data/master/gaps.csv`.

### Phase 4 — Verify & provenance  (`pipeline/04_verify.py`)
Consolidates all prior verification logic:
- Ticker confirmed via official symbol↔ISIN (exchange lists) — authoritative.
- Price cross-check (screener/bhavcopy first-day open vs issue/listing) where available.
- Per-row `confidence` + `confidence_reason`; per-field `*_src` tags.

### Phase 5 — Reconcile vs old  (`pipeline/05_reconcile.py`)
Join new master against the archived old 929 CSVs by ISIN. Diff key fields
(ticker_ns, ticker_bo, issue_price, listing_open, sub_total_x, type). Write
`data/master/reconciliation_report.csv` listing every mismatch. **Expect ~0 on overlapping
rows;** any mismatch is investigated before the new master is trusted.

---

## 6. `docs/sources.md` template (the living source map)

Same template for every site, so adding a new site = append a section:

```
## <Source name>
- Access: <URL/API>, <cloudscraper/requests/browser>, rate <Xs>
- Coverage: <years>, <Mainboard/SME>, <approx count>
- FREE fields: <list>
- PREMIUM / GATED: <list, or "none">
- Match key available: <ISIN / symbol / name-only>
- Reliability notes: <known data-quality caveats>
- Used in pipeline phase(s): <n>
```

Seeded with: Chittorgarh, Sharescart, Screener, Exchange lists (NSE/BSE), Bhavcopy, Yahoo.

---

## 7. Output: `data/master/`

- `mainboard.csv`, `sme.csv` — the two final lists, ISIN-keyed, full schema.
- `*_src` provenance columns on key multi-source fields (issue_price, listing_open, financials,
  subscription, ticker, market_maker) — NOT on every column (keeps it readable).
- `README.md` — what the files are, build date, row counts, confidence summary.
- `reconciliation_report.csv`, `gaps.csv` (TODO sources to chase).

---

## 8. Schema (finalized in Phase 0; expected shape)

Identity (from Chittorgarh/exchange, ISIN-keyed): isin, company_name, type, nse_symbol,
bse_code, ticker_ns, ticker_bo, exchange, incorporation_year, age_at_ipo_years.
IPO basics: issue_price, price_band_low, book_built, lot_size, min_investment, issue_size_cr,
fresh_issue_cr, ofs_cr, ofs_pct, anchor_allocation_cr.
Timetable: open_date, close_date, listing_date.
Subscription (Sharescart, 2023-25): sub_qib_x, sub_nii_x, sub_retail_x, sub_total_x (+_cr).
GMP (Sharescart): gmp_pct.
Listing: listing_open, listing_gain_pct, listing_high, listing_low, listing_close.
Promoter: promoter_pre_issue_pct, promoter_post_issue_pct.
People: lead_manager, market_maker, registrar.
Financials (3yr, Sharescart/screener): net_sales, operating_profit, pat, eps, balance-sheet,
cash-flow, ratios, growth — plus pre_ipo_* normalized fields.
Provenance: <field>_src tags; confidence, confidence_reason.

Exact list locked in `docs/schema.md` after Phase 0.

---

## 9. Out of scope (explicit)
- Filling 2020–2022 subscription-split / GMP (no free source found) — TODO, later.
- Layer 2 daily price history (separate future build).
- Pattern analysis (separate, after dataset is final).
- Pre-2020 IPOs.
