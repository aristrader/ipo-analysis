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

## Screener (screener.in)   — financials/KPIs source (G1b)
- Access: search API `/api/company/search/?q=<name>` → `{id,name,url}` (url has ticker);
  company page `https://www.screener.in/company/<TICKER>/consolidated/` (fall back to non-consolidated
  for standalone-only names). Plain desktop User-Agent is enough (no cloudscraper). ~0.3s/company.
  Price API `/api/company/<id>/chart/?q=Price&days=10000`.
- Coverage: all listed incl. SME; **10+ years of annuals → covers pre-listing FY20/FY21** (verified).
- FREE fields: P&L (Sales, OperatingProfit, OPM, PBT, NetProfit, EPS), Balance Sheet (Equity, Reserves,
  Borrowings, Total Assets, Fixed Assets), Cash Flow (CFO/CFI/CFF), Ratios (PE, ROE, ROCE, BookValue);
  debt/equity + PAT-margin trivially derived. Weekly price history.
- PREMIUM/GATED: none needed.
- Match key: NO ISIN. Map ISIN→ticker (we already have tickers), then hit `/company/<TICKER>/`.
  Backstop ISIN→ticker bridge: moneycontrol autosuggest (below).
- Reliability: verified Gland FY20 Sales ₹2,633cr / PAT ₹773cr / EPS 49.88. Good SME price where Yahoo fails.
- Pipeline phase: 3 (financials/KPIs for 2020-22), 4 (price verification).

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

## Yahoo Finance (chart API / yfinance)
- Access: `https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>?range=&interval=1d` (plain urllib,
  browser UA). NSE=`SYMBOL.NS`, BSE=`numeric-code.BO`. ~112 req/s at 20 workers, no ban observed.
- Coverage: **859/1269 resolve** (≈all mainboard + ~484 SME). **Poor Indian SME coverage** — 403 SME
  don't resolve (Yahoo lacks the data; tickers are still correct, confirmed via bhavcopy).
- FREE fields: daily OHLCV.
- Match key: ticker (.NS/.BO).
- Reliability: accurate where present; NOT a viable SME price source → use bhavcopy.
- Pipeline phase: 6 (ticker validation), Layer 2 fast-path for mainboard.

## NSE Public Issues API (subscription)   — subscription split source (G1a, mainboard)
- Access: curl_cffi `impersonate="chrome"` (plain requests blocked). Prime session: GET nseindia.com →
  GET `/market-data/all-upcoming-issues-ipo` (referer) → then call API with that Referer + Accept json.
  - List: `https://www.nseindia.com/api/public-past-issues?index=equities` (1360 recs, 2003–2026).
  - Subscription: `https://www.nseindia.com/api/ipo-active-category?symbol=<SYMBOL>` → dataList rows
    QIB/NII/RII/Employees/Total, each with shares offered/bid and `noOfTotalMeant` (= the × multiple).
- Coverage: **Mainboard only**, reaches 2020 (2020=56, 2021=109, 2022=105 issues). **SME returns 0.00** (NSE
  doesn't populate SME demand schedule → use ipowatch for SME).
- FREE fields: QIB/NII/Retail/Employees/Total subscription × (authoritative).
- Match key: NSE **symbol** (no ISIN; companyName null pre-2022). Bridge ISIN↔symbol via EQUITY_L.csv.
- Reliability: authoritative (exchange). Verified Zomato 38.25×, Burger King 156.65×, Gland 2.06×.
- Pipeline phase: 3 (subscription back-fill, mainboard).

## IPOWatch (ipowatch.in)   — GMP (G2) + subscription split (G1a, incl. SME)
- Access: WordPress REST `https://ipowatch.in/wp-json/wp/v2/posts?search=<name>&after=&before=` (plain
  requests, default UA, 200; 9,517 posts). ⚠️ Parse `content.rendered` from REST — the front-end HTML
  URL sometimes serves a STALE cached page (wrong IPO). Tables parse with BeautifulSoup.
- Coverage: 2020–2025, **Mainboard + SME**. Separate posts per IPO: `…-details`, `…-gmp…`, `…-subscription-status…`.
- FREE fields: GMP date-by-date series (GMP/Kostak/Subject-to-Sauda); subscription per-category per-day
  (QIB/NII/RII/EMP/Total); listing gain derivable.
- PREMIUM/GATED: none.
- Match key: **company-name slug + listing-date window** (NO ISIN/ticker). Expect manual disambiguation.
- Reliability: verified Zomato sub QIB 51.79/NII 32.96/RII 7.45/Total 38.25×; Zomato GMP series to 23-Jul.
- Pipeline phase: 3 (GMP + SME subscription back-fill).

## InvestorGain (investorgain.com)   — GMP source (G2), via webnodejs API   [USED: scrapers/investorgain.py]
- Access: **webnodejs JSON API (same backend pattern as Chittorgarh)**, cloudscraper + Referer.
  The site itself is a client-side Next.js app (search/tracker/sitemap have NO /ipo/ data in HTML) —
  do NOT scrape pages; hit the API instead. Endpoint discovered via Playwright network capture.
  - GMP performance tracker (report 377), ONE call returns ALL IPOs for a year (totalPages=1):
    `https://webnodejs.investorgain.com/cloud/v2/report/data-read/377/1/5/<YEAR>/2026-27/0/all?search=&v=14-42`
    ⚠️ the `/5/` segment is fixed report config — it returns all rows; changing it (e.g. /100/) returns 0.
- Coverage: 2020–2025, MB + SME. 1271 IPOs, **929 with a GMP value**.
- FREE fields per row: IPO name, **Symbol = "<NSE sym>, <BSE code>"**, Listing Date, **GMP (₹)**, IPO Price,
  ~srt_gmp_rating, ~str_listing_gain_in_per, slug. gmp_pct = GMP / issue_price * 100.
- PREMIUM/GATED: subscription category split (IPOMatrix login). GMP here is a single representative ₹, not a series.
- Match key: **NSE symbol OR BSE code + exact listing_date** (concrete; no name guessing). No ISIN in this API.
- Reliability: verified Markolines 6.41%, Navoday 70%, SVS 20% (exchange-id + date matched).
- Pipeline phase: 3e (GMP fill, second pass after ipowatch). Filled +320 rows.

## moneycontrol autosuggest  — ISIN↔ticker bridge only (NOT financials)
- Access: `https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&query=<name>&type=1&format=json`
  via curl_cffi `impersonate="chrome120"` (plain requests 403). Returns ISIN + NSE ticker + BSE code + sc_id.
- Use: resolve ISIN↔ticker for screener mapping. MC's own financials are only ~5yrs free → NOT used for 2020-22.

---

## Tested & NOT viable (do not re-research)
- **BSE official IPO API** — endpoints 302→error (Akamai). NSE covers mainboard subscription instead.
- **ipocentral.in** — GMP only, sparse/selective (no Zomato post); no subscription splits. Tertiary at best.
- **trendlyne.com** — financials JS-rendered/AJAX-gated; needs login/headless. Not worth it (screener wins).
- **moneycontrol financials** — only ~5 free years (too shallow for 2020-22 pre-listing). Autosuggest API still useful (above).

## GAPS — sources now FOUND (integration pending; see TODO G1/G2)
- Subscription split (MB): NSE Public Issues API. (SME): ipowatch.in.
- 3yr financials/KPIs (2020-22): screener.in.
- GMP: ipowatch.in (series) + investorgain.com (ISIN-keyed single value).
- Still genuinely open: none for G1/G2 — all have a working free source; only integration remains.
