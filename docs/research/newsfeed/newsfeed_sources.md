# Newsfeed / catalyst SOURCES scout (2026-06-08)

Research-only scout of news/catalyst sources for Indian listed/IPO stocks. SCOPE, not build. Free
data only; company laptop = ToS/legality-conscious. Builds on `tools/research/scope_news_feed.py`
(NSE announcements probe — already confirmed, carries `sm_isin`). **Columns:** Free? · Parseable? ·
ISIN/symbol-matchable? · Latency · History or live-only · SME/IPO coverage · ToS/laptop risk ·
Ingest effort (S/M/L). Statuses: ✅ probed-OK · ⚠ probed-partial · ◻ not-probed (web-researched).

## Ranked source table (catalyst/official first, then aggregator, then social)

| # | Source (endpoint) | Free | Parse | ISIN/sym match | Latency | History | SME/IPO | ToS/laptop | Effort | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **NSE corporate-announcements** `/api/corporate-announcements?index=equities&symbol=` | Y | JSON | **`sm_isin` IN payload** | ~EOD/intraday | live + back-history per symbol | both (mainboard+SME) | low (public, session-primed, our existing pattern) | S | ✅ 5/8 syms, 18–28 anns, full fields incl `sm_isin`/`desc`/`an_dt`/`attchmntFile`/`smIndustry` |
| 2 | **NSE board-meetings** `/api/corporate-board-meetings?...symbol=` | Y | JSON | symbol→ISIN via our universe | days-ahead (forward calendar) | live | both | low | S | ✅ n=4, keys `bm_date`/`bm_desc`/`bm_purpose` (results/dividend dates = scheduled catalysts) |
| 3 | **NSE events-calendar** `/api/event-calendar?...symbol=` | Y | JSON | symbol | forward-looking | live | both | low | S | ✅ n=2, `date`/`purpose` (earnings/AGM dates → pre-position) |
| 4 | **NSE SAST reg29 / insider-PIT** `/api/corporate-sast-reg29`, `/api/corporates-pit` | Y | JSON | symbol | ~EOD | live | both | low | S | ✅ SAST n=1 (`acquirerName`/`acqType`); PIT n=0 on sample (sparse but live) |
| 5 | **Google News RSS (per company)** `news.google.com/rss/search?q=<name>+NSE&gl=IN&ceid=IN:en` | Y | RSS/XML | **name-query only** (fuzzy→ISIN, our F11 problem) | near-real-time | live-only (forward-collect) | both incl SME/recent-IPO (it aggregates everyone) | low (public RSS) | M | ✅ 69–100 items/query, fields `title/link/pubDate/source`; dedupe + entity-match needed |
| 6 | **BSE announcements** `api.bseindia.com/.../AnnGetData/w` | Y | JSON | scrip code / ISIN | ~EOD/intraday | live + history | both (BSE = most SME) | med (Referer/Origin headers, anti-bot) | M | ⚠ HTTP 200 but "No Record Found" on my param combos — needs correct `strScrip`/date fmt; viable per web, redundant w/ #1 for NSE-listed |
| 7 | **LiveMint markets RSS** `livemint.com/rss/markets` | Y | RSS | name-query (market-wide feed) | near-real-time | live-only | broad, not per-stock | low | M | ✅ 35 items |
| 8 | **Economic Times markets RSS** `economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms` | Y | RSS | name-query (market-wide) | near-real-time | live-only | broad, not per-stock | low | M | ✅ 50 items |
| 9 | **Moneycontrol RSS** `moneycontrol.com/rss/*.xml` | Y | RSS | name-query (market-wide) | near-real-time | live-only | broad | low | M | ✅ marketreports feed live (per-stock RSS not exposed) |
| 10 | **screener.in Documents/Announcements tab** | Y | HTML scrape | page = company (ISIN known) | ~EOD | shows history | both | med (ToS; we already scrape screener, rate-limited) | M | ✅ confirmed page has Announcements (date/title/BSE-source) + credit-rating docs (CARE) + transcripts; no API/RSS |
| 11 | **Credit-rating actions (CRISIL/ICRA/CARE)** | Y | — | — | EOD | — | both | low | — | ◻ NOT a separate ingest: rating actions arrive as **Reg-30 announcements inside #1/#6/#10** — capture there, don't build a 4th scraper |
| 12 | **SEBI orders** `sebi.gov.in` enforcement/orders | Y | HTML scrape | name (no ISIN) | irregular | history | both | low | L | ◻ no RSS; rare per-stock; low priority (most material SEBI actions also hit #1 as a filing) |
| 13 | Business Standard markets RSS | Y | RSS | name-query | near-real-time | live-only | broad | med | M | ⚠ **HTTP 403** to my UA — anti-bot; ET/Mint cover the same ground |
| 14 | NSE bulk/block-deals `/api/block-deal` | Y | JSON | symbol | EOD | live | both | low | S | ⚠ probe returned an index quote, not the deal list — wrong endpoint variant; block/bulk-deal CSVs exist on NSE, low value vs effort |
| 15 | Trendlyne / Tickertape / StockEdge free tiers | partial | HTML | ISIN/sym | EOD | some history | both | **med-high (ToS forbids scraping; free tier = login/widgets)** | L | ◻ web-research: no open API; ToS-risky on a company laptop |
| 16 | Twitter/X cashtags ($TATATECH) | API paid | — | cashtag→fuzzy | real-time | live-only | patchy | **high: API now paid; scraping breaches ToS** | L | ◻ NOT VIABLE free |
| 17 | StockTwits | — | JSON(was) | cashtag | real-time | live-only | thin for India | **API registration CLOSED (under review 2026)** | — | ◻ NOT VIABLE — signups shut |
| 18 | Reddit r/IndianStreetBets | Y(ltd) | JSON | none (free text) | real-time | live-only | meme/large-cap only | med (Reddit API now rate-limited/paid tiers) | L | ◻ very noisy, no SME/IPO catalyst value; sentiment-only |
| 19 | Telegram / Discord IPO-tip channels | Y | text | none | real-time | live-only | pump-prone | **high: pump-and-dump, unverifiable, laptop/ToS risk** | L | ◻ NOT VIABLE — noise/manipulation |

## Probed & CONFIRMED this session (live HTTP)
- **NSE announcements** — 5/8 syms returned 18–28 anns, 0s were very-recent/illiquid; fields incl `sm_isin` (ISIN matching SOLVED for free).
- **NSE board-meetings / events-calendar / SAST-reg29** — all HTTP 200 with usable rows + dated catalyst fields, symbol-keyed.
- **Google News RSS** — 69–100 items per company query, clean RSS (`title/link/pubDate/source`); live-only.
- **ET (50 items) / LiveMint (35) / Moneycontrol RSS** — all live, but market-wide (not per-stock).
- **screener.in** Documents/Announcements tab present (incl credit-rating + transcripts); HTML-only, no API.
- Negative: **BSE** API returned "No Record Found" (param/date-format issue, fixable); **Business Standard RSS 403**.

## Top 5 to actually pursue
1. **NSE corporate-announcements API** — the spine. Free, JSON, `sm_isin` in payload, both segments, our existing session pattern. Effort S. **Build first.**
2. **NSE board-meetings + events-calendar** — forward-dated catalysts (results/dividend/AGM) = pre-position signal, not just post-hoc news. Effort S, same session.
3. **Google News RSS per company** — the only source of *real-world / sector / order-win* news beyond filings; fills the gap filings miss. Cost = entity-match + dedupe (the F11 fuzzy problem). Effort M.
4. **NSE SAST reg29 + insider-PIT** — promoter/large-holder buy-sell = validated-worthy catalyst class, symbol-keyed, free. Effort S.
5. **screener.in Announcements/Documents tab** — fallback + credit-rating actions + transcripts for names where NSE is sparse; we already scrape screener (reuse rate-limits). Effort M.

## Explicitly NOT VIABLE (one-line why)
- **Twitter/X** — API paid, scraping breaches ToS (laptop risk). · **StockTwits** — registration closed 2026; thin India. · **Reddit/Telegram/Discord** — noise + pump-and-dump, no SME/IPO catalyst value, ToS/legality risk. · **Trendlyne/Tickertape/StockEdge** — no open API, scraping forbidden by ToS. · **Any paid news API (Bloomberg/Refinitiv/NewsAPI paid tier)** — violates free-data rule. · **Separate CRISIL/ICRA/CARE scraper** — redundant; rating actions already flow through NSE/BSE Reg-30 filings.

## Key takeaways for a build
- **ISIN matching is free & solved** for the official spine (#1 carries `sm_isin`; #2–4 by symbol→our universe). Only the *aggregator/news* sources (#5 Google, RSS) need fuzzy name→ISIN (the parked F11 problem).
- **History vs live:** official NSE APIs give back-history per symbol; all RSS/social are **live-only → forward-collect** (start a daily staging pull now to accrue history).
- **SME/recent-IPO:** covered by NSE announcements + Google News + BSE; NOT by social or market-wide RSS.
- **Discipline:** stage to `data/live/` keyed on `sm_isin`, never the frozen substrate (same rule as the live board). A raw dated-announcement feed is useful WITHOUT good/bad classification; classification = a separate 3-layer hypothesis test (news edges arbitrage away fast).

_Cited: nseindia.com `/api/corporate-announcements|corporate-board-meetings|event-calendar|corporate-sast-reg29|corporates-pit`; news.google.com/rss/search; economictimes.indiatimes.com/.../2146842.cms; livemint.com/rss/markets; moneycontrol.com/rss; api.bseindia.com/.../AnnGetData/w; business-standard.com/rss-feeds/listing; screener.in/company/<SYM>; sebi.gov.in._

## Addendum 2026-06-09 — delivery-volume% data source (the D2 linchpin)
- **`sec_bhavdata_full_<DDMMYYYY>.csv`** (host `archives.nseindia.com/products/content/...`) is the free,
  daily, security-wise delivery file. Cols incl `DELIV_QTY`, `DELIV_PER` (= DELIV_QTY/TTL_TRD_QNTY×100).
  **This is a SEPARATE file from the cm-bhavcopy our `scrapers/bhavcopy*.py` already pull (those carry NO
  delivery columns)** → delivery% requires a NEW daily pull + ISIN/symbol join. History depth is shallow:
  reliably retrievable ~FY2016-17 (~2017)+ (legacy MTO report older but patchy/unconfirmed) → **boom-only,
  cannot reach the 2006–19 longterm cohort → cannot be cross-regime-validated**. Full availability verdict +
  3-layer test design + sharpened (weak) prior: `newsfeed_rnd_2026-06-09.md` §1, §3e, §4.
