# Discussion — Full Thought Process & Context

**Created:** 2026-05-30
**Purpose:** Capture every decision, every idea, every rejected option, and every nuance discussed so far.
A future session reading only this file + design.md + TODO.md should have zero context loss.

---

## 1. Problem Statement

The Indian IPO market (especially post-COVID, 2020–present) has had a huge boom — both Mainboard and SME segments.
The question: **are there conditions under which something (a listing pop, a recovery, a 30%+ gain, a sustained move) is statistically more likely to happen again?**

The goal is not to predict individual IPOs. It's to find **repeatable patterns over a large dataset** — conditions that tilt probability in one direction. Think: "IPOs with >30x retail subscription and GMP > 15% of issue price opened above issue 87% of the time" — that kind of statement.

This is a **personal research / pattern-finding project. Not financial advice.**

---

## 2. Why Build This — Existing Tools Don't Do What We Need

**What existing sites (Chittorgarh, Trendlyne, Screener, IPO Central) already do:**
- Show listing gains, above/below issue price, subscription numbers, sector
- Good enough for "how many IPOs went up?"

**What no off-the-shelf tool does:**
- Conditional backtesting: "if subscription < 10x AND GMP < 5%, what's the average 1-month return?"
- Strategy simulation: "if I didn't get allotment, should I buy on listing day or wait for a dip?"
- Combined conditions: "low issue price + high retail sub + positive GMP → listing gain distribution"
- SME-specific patterns vs Mainboard-specific patterns

That custom strategy logic is the part that justifies building. Everything else is already on those sites.

---

## 3. The Core Cost Rule (most important principle)

> **Scrape with deterministic code (free, zero AI tokens). Use AI only on already-structured data (Layer 3).**

Feeding raw HTML pages through an AI model is expensive and pointless — a 20-line script extracts the same table for free. The AI's job is querying, slicing, and generating new pattern ideas over a tidy table. Never data extraction.

This rule shapes every tooling decision in the project.

---

## 4. Architecture — How We Got Here

**Starting point:** "just put everything in Google Sheets"

**The problem we identified:** Several patterns need full daily price series, not snapshots.
- "Did it sustain above issue price for a month?" → need 30 days of closing prices
- "What was the max gain in the first 30 days?" → need daily highs
- "Buy after X% fall, hold 1 month" → need daily OHLC

GOOGLEFINANCE can't answer these. IMPORTXML is rate-limited and breaks constantly — explicitly rejected as a backbone. SME tickers don't resolve in GOOGLEFINANCE at all.

**The split we landed on:**

| Layer | What | Storage |
|---|---|---|
| 1 — Raw event data | One row per IPO, fixed forever once listed | CSV (Google Sheets as front-end) |
| 2 — Daily price history | Per-stock OHLC for listing → +3 months | CSV/SQLite in Python |
| 3 — Derived patterns | Computed on top of 1+2, re-runnable freely | CSV / pandas |

**Key principle:** Every new pattern is just a new function over Layers 1 and 2. You never re-scrape to add a pattern. This is what makes the project extensible.

**Only the genuinely live number** ("price today / current vs issue") goes back into Google Sheets via GOOGLEFINANCE for mainboard names actively watched. Everything historical stays in Python.

---

## 5. Mainboard vs SME — Why Kept Separate

Decided early: **separate CSVs, separate analysis, never mixed.**

Reasons:
- Scale is completely different: Mainboard issue sizes are 10–100x larger than SME
- Institutional dynamics differ: QIB participation means something different at each tier
- SME listing mechanics differ: market maker involvement, lower liquidity post-listing
- A pattern that holds in SME may not transfer to Mainboard and vice versa
- SME price data is harder to collect (GOOGLEFINANCE unreliable, need bhavcopy)
- Each segment needs its own holdout set for validation

Same schema — rows just live in different files.

---

## 6. Source Discovery — What We Checked and What Happened

We started assuming Chittorgarh would be the primary source. Before building anything, we did a live source check.

### Sites we attempted to fetch (programmatically)

| Site | Result | Notes |
|---|---|---|
| chittorgarh.com | 403 Forbidden | Cloudflare. Has data going back to 2006 including performance tracker. Unusable via plain HTTP. |
| chittorgarh.com/ipo/ipo_perf_tracker.asp | 403 Forbidden | Same. |
| investorgain.com | 403 Forbidden | Known to have 2020+ data. Blocked. |
| ipoplatform.com | 403 Forbidden | User confirmed it has data. Blocked via HTTP. |
| ipocentral.in | 403 Forbidden | Blocked. |
| ipomonitor.in | Connection refused | Server unreachable. |
| nseindia.com | Timeout | Request timed out. |
| trendlyne.com/ipo/ | 404 | Wrong URL. Different URL structure needed. |
| trendlyne.com/ipo/screener/ | JS-rendered | Table shows "no matches found" — data loaded client-side via JavaScript. pandas.read_html won't work. |
| ticker.finology.in/IPO | Accessible | But thin: company name, price band, issue size, listing price/gain, current return. No subscription data, no GMP in table. |
| **sharescart.com/ipo/** | **Accessible** | **List page + rich detail pages. Primary source chosen.** |

### Why so many 403s?

These sites use Cloudflare or similar bot-detection. They see no browser fingerprint, no cookies, wrong headers → block. A real browser gets through fine.

### Ways to bypass (legitimate, for research use):
1. **Proper headers** — set `User-Agent`, `Accept`, `Referer`, `Accept-Language` to mimic a real browser. Works for sites with basic UA checks only.
2. **`cloudscraper` Python library** — handles Cloudflare JS challenges. One-liner replacement for `requests`. Best first attempt for CF-protected sites.
3. **Find the XHR/JSON API endpoint** — most modern sites load table data via a background JSON call (visible in Chrome DevTools → Network → XHR/Fetch). That endpoint often doesn't have Cloudflare protection and returns clean structured data directly. Best approach for Chittorgarh specifically.
4. **Playwright/Selenium** — real browser, full fingerprint. Works on everything but slow and heavy. Last resort.

### What Sharescart provides (verified by fetching a live page)

**List page columns:** company name (+ detail URL), status, open date, close date, issue price, cost of 1 lot, listing price, listing gain %, current price, return %, type (SME/MB), exchange.

**Year range:** 2023–2025 confirmed. User also confirmed 2023 is accessible. 2020–2022 not available — gap.

**Filters available:** Status (All/Open/Closed/Listed/Upcoming), Industry (150+ categories), Issue Type (SME/Mainboard), Year (2024, 2025 on list — 2023 also visible per user).

**Detail page (verified on Vegorama Punjabi Angithi Ltd):**
- IPO basics: company, industry, incorporation year, exchange, issue size, price band, face value, lot size, min investment
- Timetable: open, close, allotment, refund, share delivery, listing dates
- Lot size by category: retail min/max, S-HNI min/max, B-HNI min
- Subscription: QIB / NII / Retail / Total — shares applied, ₹ amount, x-times
- Listing: listing price, listing gain %, GMP (₹ and %)
- Key metrics: P/E, sales (Cr), PAT (Cr), EPS
- Promoter shareholding: pre-issue %, post-issue %, promoter names
- P&L (3 years + TTM): net sales, total income, operating profit, PBT, tax, PAT, EPS
- Balance sheet (3 years): shareholder funds, borrowings, current liabilities, total liabilities, fixed assets, current assets, total assets
- Cash flow (3 years): operating, investing, financing activities, closing cash
- Ratios: EBITDA margin, EBIT margin, PAT margin, cash profit margin, ROA, ROE, ROCE, receivable days, inventory days, payable days, PER, price/book, EV/sales, EV/EBITDA, debt/equity, current ratio, quick ratio, interest cover
- Growth rates: sales CAGR 1Y/3Y/5Y/10Y, operating profit CAGR, PAT CAGR, ROE/ROCE averages
- Objectives of issue (what they're using the money for)
- Registrar: name + city ✅
- Lead Manager (called "IPO Lead Manager"): single name ✅ — may be incomplete for multi-banker mainboard deals
- Market maker: **NOT present** — SME-specific, source TBD
- Quarterly results: table present but data locked

**What's NOT on Sharescart detail pages:**
- Ticker symbols (NSE/BSE) — need separate enrichment
- Market maker — need separate source
- Full BRLM list for multi-banker mainboard deals
- Listing day intraday OHLC (only listing open/gain, not high/low/close) — comes from Layer 2
- GMP history — only current GMP shown, not GMP at time of subscription close

**JS rendering (discovered programmatically):**
Both list and detail pages are JS-rendered. A `requests` GET returns a 240KB HTML shell with no IPO data — only navigation, footer, and UI scaffolding. The actual table data loads via JavaScript after page paint. Scraper cannot use `requests` + BeautifulSoup directly. Must either: (1) find the XHR/JSON API endpoint the page calls (check Chrome DevTools → Network → XHR/Fetch), or (2) use Playwright as a fallback to render the page fully.

---

## 7. All Patterns & Queries We've Thought Of

Moved to `docs/patterns.md` — that is the live working document for pattern hypotheses.

---

## 8. Schema Decisions — The "Why" Behind Each Choice

### Wide flat CSV (not normalized tables)
Rejected normalisation early. Reasons:
- Total dataset is ~500–700 rows for 2023–2025. Not a scale problem.
- Google Sheets as the front-end can't do relational joins.
- pandas can handle wide tables trivially.
- Different analyses (subscription analysis, financial analysis, listing analysis) are just different column subsets of the same flat table.
- Normalised financials would be a separate `financials` table with 3 rows per IPO — adds join complexity for zero benefit at this scale.

### Relative financial years (yr1/yr2/yr3) not absolute (FY2023/FY2024)
A 2020 IPO and a 2025 IPO show different absolute years in their DRHPs. Using relative labels (`yr3` = most recent, `yr1` = oldest) means `pat_yr3` means "most recent year's PAT" for every company regardless of when they listed. Cross-company comparison is cleaner this way. Actual year label stored in `fin_year_yr3` column so you always know what yr3 means.

### No `current_price` / `current_return_pct` in the event table
These change every day — they'd be stale immediately. Instead: store `ticker_ns` and `ticker_bo`, use GOOGLEFINANCE in Sheets for live mainboard prices when needed. SME prices pulled separately via yfinance/bhavcopy when doing analysis.

### `listing_open` vs full listing day OHLC
Sharescart only provides the listing open price (what they call "listing price"). Listing day `high`, `low`, `close` come from Layer 2 price history (yfinance/bhavcopy). Columns exist in schema with a note that they're null in Layer 1 — they get filled when Layer 2 runs.

### `min_investment_rs` included
Explicitly requested analysis: "does lower share cost IPO have higher chance of opening high?" This is `lot_size_shares × issue_price`. Present on Sharescart list page as "cost of 1 lot". Kept as its own column to make that analysis trivial.

### All subscription sub-columns (QIB, S-HNI, B-HNI, NII total, Retail, Total)
Both x-times and ₹Cr amounts. The x-times tell you demand intensity; the ₹Cr amounts tell you absolute capital inflow. Different questions need different forms. Keeping all columns is cheaper than re-scraping later.

### `market_maker` column kept (null for now)
SME-specific. Important for: understanding who's supporting the price post-listing, whether the market maker's reputation correlates with post-listing stability. Not on Sharescart — source TBD. Column exists with null values so it can be filled later without schema change.

### Python over Java
No contest. Java has no pandas, no read_html, no cloudscraper equivalent. Scraping and data analysis are Python's native territory. The existing repo (`TestingTesting`) is a Java design-patterns learning repo — unrelated to this project.

---

## 9. Known Gaps and Their Status

| Gap | Impact | Plan |
|---|---|---|
| 2020–2022 historical data | Missing ~3 years of IPOs | Deferred. IPO Platform and Trendlyne have this data. Both returned 403 via plain HTTP. Need cloudscraper or DevTools XHR endpoint approach. Schema identical — rows merge into same CSVs. |
| Ticker symbols (ticker_ns / ticker_bo) | Can't pull price history without tickers | Deferred enrichment step. Plan: yfinance fuzzy name→ticker lookup + manual fixes for mismatches. |
| Listing day OHLC (high/low/close) | Can't do "listed below but intraday high > issue" | Layer 2 (price history). Columns exist, filled when price scraper runs. |
| Market maker (SME) | Missing SME-specific analysis dimension | Source TBD. Chittorgarh may have it (if XHR bypass works). Could also come from exchange filings. |
| Full BRLM list | Mainboard multi-banker deals show only 1 name | Low priority for initial patterns. Can add brlm_list as a text column later. |
| GMP at time of subscription close | Sharescart shows current GMP, not historical | Hard to get. Grey market is informal — no official source. May stay as "GMP at time of scraping" with a caveat. |
| Survivorship bias | **Confirmed** — Sharescart only has currently-trading IPOs. Delisted/suspended/withdrawn are absent. | Needs supplementary source. Chittorgarh via cloudscraper is best candidate. |
| Quarterly results | Locked on Sharescart | Not needed for v1 patterns. |
| issue_size_cr | Sharescart shows '--' for all listed IPOs | investorgain.com or NSE/BSE filings |
| issue_size_cr, gmp_pct (historical), industry, fresh_issue/OFS | Not available on Sharescart | See enrichment TODO |
| DRHP-era financials for 2023/2024 IPOs | Sharescart updated with post-listing annual reports | Chittorgarh, NSE/BSE DRHP PDFs, or screener.in (needs tickers) |

---

## 10. Methodology Cautions — The Discipline Rules

These are **data-collection requirements**, not afterthoughts. Build them in from day one.

### Survivorship bias
If we only collect IPOs that are currently trading, "IPOs go up" looks falsely true. The dataset **must** include:
- Delisted companies
- Suspended trading cases
- Withdrawn IPOs (filed but didn't list)
- Hard crashes (>80% down from issue price)

The scraping requirement: pull the full historical list, not any "top performers" or "currently listed" filtered view.

### Overfitting / small samples
Slice any dataset 15 ways and a pattern always appears by luck. SME segment is especially vulnerable (fewer IPOs per year, noisier data).

Mitigation:
- **Holdout set**: reserve the most recent ~3 months of IPOs. Do NOT peek at them while hunting patterns. Validate any discovered pattern against the holdout before declaring it real.
- **Cross-year check**: does the pattern hold in 2023, 2024, AND 2025 independently? Or only in one year?
- **Size check**: how many IPOs does the pattern apply to? A pattern based on 8 data points is noise.

---

## 11. Decisions Still Open

1. **GMP on Sharescart — is it at listing time or current?** — Confirmed: it is the current GMP, not at subscription close. For IPOs listed >4 weeks ago it shows '--'. For pattern analysis, GMP is only usable for 2025 IPOs scraped close to their listing date. Historical GMP needs investorgain.com.

2. **For 2020–2022 gap — IPO Platform or Trendlyne?** — Both blocked via plain HTTP. Need to try: (a) cloudscraper, (b) DevTools to find their XHR JSON endpoint. IPO Platform has a cleaner URL structure (ipoplatform.com/main-board/by-year). Trendlyne is richer but JS-rendered. Test IPO Platform first.

3. **Price window depth: +3 months or +6 months?** — Affects Layer 2 storage. +3 months covers all the "1-month sustain / buy-the-dip" tests. +6 months gives buffer for slower recoveries. Storage cost is low either way. Not yet decided.

4. **For survivorship bias fix — Chittorgarh or exchange filings?** — Chittorgarh has delisted company data going back to 2006. Try cloudscraper first. NSE/BSE publish delisted company lists as CSVs — easier to get but has less detail.

---

## 12. Scraper & Data Build — What We Discovered (Session 2)

### Sharescart is JS-rendered but the API is accessible
The list page and detail pages both return empty HTML shells from plain `requests`. However:
- **List data**: loaded via POST to `/web-services/ipo-stocks-intermediary.php` with `action=getipodataAccord`. Returns JSON with an HTML table and pagination. No browser needed once you know the endpoint.
- **Detail pages**: server-side rendered — direct GET + BeautifulSoup works. No browser needed.
- Rate limit tested down to 0.1s delay with no blocking. Using 0.5s as safe buffer. Actual RTT ~0.15s.
- `type[]` filter in the list API is ignored server-side — always returns all types. Split MB vs SME client-side from the `type` column.

### Final dataset built
- 929 unique IPOs (259 MB + 670 SME) across 2023–2025 after deduplication
- 10 duplicates removed — same company appeared in multiple year pages of the list API (identical rows)
- Scraper: `scrapers/sharescart.py`, 2 workers, 0.5s delay, logs to `logs/`
- Clean data: `data/derived/mainboard_clean.csv` + `sme_clean.csv`, 139 columns each

### Critical finding: Sharescart updated financial data post-listing
For 62% of MB and 68% of SME rows, `fin_year_yr3` is after the listing date. Sharescart continuously updates older IPOs with new annual reports. A Dec 2023 IPO now shows Mar 2025 as its most recent year.
- **Impact**: financial ratios and P&L for 2023/2024 IPOs are post-listing data, not what investors saw
- **Fix applied**: `pre_ipo_*` columns added to clean CSV — always reflect the most recent pre-listing year
- `pre_ipo_years_available`: 3 years for ~30% of dataset, 1 year for ~30%, 0 years for ~10% (mostly SME)
- For 2023 IPOs: only 1 pre-IPO year recoverable (yr1 = Mar 2023). The 2-year growth trajectory investors saw is gone from Sharescart.

### Survivorship bias confirmed
- Known failed/delisted SME IPOs are absent from Sharescart
- The status filter API parameter is a facade — ignores all values, only ever returns currently-trading IPOs
- ~50–100 failed 2023–2025 SME IPOs are missing. Impact is highest for "sustained above issue price" analysis — delisted companies would drag averages down significantly.

### listing_gain_pct data error in Sharescart
~15 companies had listing gains of -900% to -940% — impossible values. Root cause: Sharescart stored the listing_open price with a 10x decimal shift for these companies. The raw listing_open and issue_price values are correct.
- **Fix applied in clean.py**: listing_gain_pct recomputed as `(listing_open - issue_price) / issue_price × 100` for all rows.

### Columns permanently unavailable from Sharescart
`industry`, `issue_size_cr` (shows -- for listed IPOs), `gmp_pct` (shows -- after ~4 weeks), `market_maker`, `fresh_issue_cr` / `ofs_cr` / `ofs_pct`, `sub_shni_x` / `sub_bhni_x` (NII only shown combined), `ticker_ns` / `ticker_bo`.

---

## 13. Explicitly Rejected Options (and Why)

| Option | Rejected because |
|---|---|
| IMPORTXML in Google Sheets | Rate-limited, breaks constantly, unreliable as a backbone |
| GOOGLEFINANCE for SME prices | Unreliable to broken for SME tickers |
| AI/LLM for data extraction from raw HTML | Expensive and pointless — a 20-line script does the same job free |
| Normalised database schema | Adds join complexity for zero benefit at this dataset size |
| Java for the project | No data ecosystem equivalent to Python's pandas/requests/BeautifulSoup |
| Single combined MB+SME CSV | Patterns likely differ; mixing risks false cross-contamination |
| Absolute financial year columns (FY2023, FY2024) | IPOs from different years have different "most recent" years — relative yr1/yr2/yr3 is cleaner for cross-IPO comparison |
| current_price in event table | Changes daily — goes stale immediately. Use ticker + GOOGLEFINANCE instead. |
| Starting with multiple scrapers in parallel | Merge/deduplication complexity, conflict resolution, 3× maintenance burden. Start with one source, add others only to fill gaps. |
