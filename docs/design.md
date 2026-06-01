# Design Document — IPO Analysis Project

**Created:** 2026-05-30
**Status:** Approved — ready for implementation

---

## 1. Goal

Build a clean, flat dataset of every Indian IPO since ~2020 (Mainboard + SME) and mine it for repeatable patterns to inform IPO investment decisions. Personal research tool, not financial advice.

Pattern hypotheses are in `docs/patterns.md`.

---

## 2. Architecture

Three layers, strictly separated:

### Layer 1 — Raw event data
One row per IPO. Written once, never modified after listing.
Source: Sharescart (primary, 2023–2025). Gap years (2020–2022) from a second source (TBD).
Storage: `data/raw/mainboard_events.csv`, `data/raw/sme_events.csv`

### Layer 2 — Daily price history
Per-stock daily OHLC for listing date → +3 months.
Source: yfinance (.NS/.BO) for mainboard; NSE/BSE bhavcopy CSVs for SME.
Storage: `data/raw/prices/<ticker>.csv`

### Layer 3 — Derived metrics & pattern flags
Computed on top of layers 1+2. Re-runnable at any time. New pattern = new function, never re-scrape.
Storage: `data/derived/`

---

## 3. Data separation: Mainboard vs SME

Kept in separate CSVs throughout. Reasons:
- Scale of operations differs hugely (issue size, institutional vs retail dynamics)
- SME patterns may not transfer to mainboard and vice versa
- Different scraping complexity (SME price data is harder — bhavcopy needed)
- Separate analysis runs, separate holdout sets

Same schema — rows just live in different files.

---

## 4. Primary source: Sharescart

**List page:** `https://www.sharescart.com/ipo/`
- Filters: type (SME/Mainboard), year. Year range confirmed: 2023–2025.
- Columns available: company name + detail URL, status, open/close date, issue price, cost of 1 lot, listing price, listing gain %, type, exchange
- Pages are JS-rendered — scraper will need Playwright or XHR endpoint discovery

**Detail page:** `https://www.sharescart.com/ipo/companies/<slug>/`
- Financials: 3 years P&L (+ TTM row), balance sheet, cash flow
- Subscription: QIB / S-HNI / B-HNI / Retail / Total (x-times + ₹Cr)
- Lead Manager confirmed present. Market maker: NOT present (deferred). Tickers: NOT present (deferred).
- Also JS-rendered

**Scraping approach:**
- `requests` with browser-like headers first
- Fall back to `cloudscraper` if Cloudflare blocks
- If still blocked: find XHR/JSON API endpoint via DevTools (preferred over Playwright)
- Last resort: Playwright headless browser
- Rate limit: 1–2 seconds between requests

---

## 5. Full schema

Mainboard and SME share this schema. One row per IPO.

### Identity
| Column | Type | Notes |
|---|---|---|
| company_name | str | As shown on Sharescart |
| type | str | MB or SME |
| exchange | str | NSE / BSE / BSE-SME / NSE-SME |
| industry | str | Sharescart category |
| incorporation_year | int | Year company was incorporated |
| age_at_ipo_years | int | listing_year − incorporation_year. Company maturity at IPO. |
| sharescart_url | str | Source URL — scraping reference, not an analysis column |
| ticker_ns | str | NSE ticker with .NS suffix — null until enriched |
| ticker_bo | str | BSE ticker with .BO suffix — null until enriched |

### IPO Basics
| Column | Type | Notes |
|---|---|---|
| issue_price | float | Upper band for book-built; fixed for fixed-price |
| price_band_low | float | Lower band; same as issue_price for fixed-price IPOs |
| price_band_width_pct | float | (issue_price − price_band_low) / price_band_low × 100. Proxy for valuation uncertainty at pricing. Zero for fixed-price. |
| book_built | bool | True = book-built (price discovered via bidding). False = fixed-price (price set upfront). |
| lot_size_shares | int | Shares per lot |
| min_investment_rs | float | Cost of 1 lot at upper band. Key for retail accessibility analysis. |
| issue_size_cr | float | Total issue size in ₹ Crore — shows as `--` for listed IPOs on Sharescart. Will be null for all scraped rows. |

### Timetable
| Column | Type | Notes |
|---|---|---|
| open_date | date | YYYY-MM-DD. IPO subscription opens. Useful for seasonality analysis. |
| close_date | date | IPO subscription closes. |
| listing_date | date | First day of trading. Pivot for Layer 2 price history. |

### Subscription (at close)
| Column | Type | Notes |
|---|---|---|
| sub_qib_x | float | QIB oversubscription times |
| sub_nii_x | float | NII total (S-HNI + B-HNI combined). Sharescart does not break out S-HNI / B-HNI separately. |
| sub_retail_x | float | Retail (bids up to ₹2L) |
| sub_total_x | float | Overall subscription |
| sub_qib_cr | float | QIB amount applied ₹Cr — null (Sharescart shows shares applied, not ₹Cr directly) |
| sub_nii_cr | float | NII amount applied ₹Cr — null |
| sub_retail_cr | float | Retail amount applied ₹Cr — null |
| sub_total_cr | float | Total amount applied ₹Cr — null |

### GMP
| Column | Type | Notes |
|---|---|---|
| gmp_pct | float | Grey market premium as % of issue price. Cross-IPO comparable. Caveat: Sharescart shows current GMP, not GMP at subscription close. |

### Listing
| Column | Type | Notes |
|---|---|---|
| listing_open | float | Opening price on listing day |
| listing_gain_pct | float | (listing_open − issue_price) / issue_price × 100. Pre-computed convenience column. |
| listing_high | float | Intraday high on listing day — from Layer 2, null in Layer 1 |
| listing_low | float | Intraday low on listing day — from Layer 2, null in Layer 1 |
| listing_close | float | Closing price on listing day — from Layer 2, null in Layer 1 |

### Promoter Holding
| Column | Type | Notes |
|---|---|---|
| promoter_pre_issue_pct | float | Promoter stake before IPO |
| promoter_post_issue_pct | float | Promoter stake after IPO dilution |

### Lead Manager & Market Maker
| Column | Type | Notes |
|---|---|---|
| lead_manager | str | Investment bank managing the IPO. Single name from Sharescart — may be incomplete for multi-banker mainboard deals. |
| market_maker | str | SME-specific. Firm providing post-listing liquidity support. Not on Sharescart — null until filled. Critical for SME pattern analysis. |

### Objectives of Issue
| Column | Type | Notes |
|---|---|---|
| objectives_of_issue | str | Free text. What proceeds are used for — e.g. "capex, working capital, debt repayment, GCP". A debt-repayment raise is fundamentally different from a capex raise. |

### TTM Snapshot (at time of IPO filing)
Trailing twelve month figures shown as a summary on the detail page — distinct from the 3-year annual data.
Note: verify on rendered page whether these are labelled TTM or are the same as yr3.
| Column | Type | Notes |
|---|---|---|
| pe_ratio | float | P/E at issue price |
| pat_ttm_cr | float | PAT trailing 12 months, ₹Cr |
| sales_ttm_cr | float | Revenue trailing 12 months, ₹Cr |
| eps_ttm | float | EPS trailing 12 months |

### Financials — 3 years (yr3 = most recent full year in DRHP)
| Column | Type | Notes |
|---|---|---|
| fin_year_yr3 | str | e.g. "Mar 2025" — most recent full year |
| fin_year_yr2 | str | e.g. "Mar 2024" |
| fin_year_yr1 | str | e.g. "Mar 2023" — oldest of the three |

**P&L**
| Column | Type | Notes |
|---|---|---|
| net_sales_yr3 | float | ₹Cr — revenue from operations |
| net_sales_yr2 | float | |
| net_sales_yr1 | float | |
| operating_profit_yr3 | float | EBITDA equivalent |
| operating_profit_yr2 | float | |
| operating_profit_yr1 | float | |
| pat_yr3 | float | Profit after tax |
| pat_yr2 | float | |
| pat_yr1 | float | |
| eps_yr3 | float | |
| eps_yr2 | float | |
| eps_yr1 | float | |

**Balance Sheet**
| Column | Type | Notes |
|---|---|---|
| shareholder_funds_yr3 | float | ₹Cr |
| shareholder_funds_yr2 | float | |
| shareholder_funds_yr1 | float | |
| borrowings_yr3 | float | |
| borrowings_yr2 | float | |
| borrowings_yr1 | float | |
| total_current_liabilities_yr3 | float | |
| total_current_liabilities_yr2 | float | |
| total_current_liabilities_yr1 | float | |
| total_liabilities_yr3 | float | |
| total_liabilities_yr2 | float | |
| total_liabilities_yr1 | float | |
| fixed_assets_yr3 | float | |
| fixed_assets_yr2 | float | |
| fixed_assets_yr1 | float | |
| total_current_assets_yr3 | float | |
| total_current_assets_yr2 | float | |
| total_current_assets_yr1 | float | |
| total_assets_yr3 | float | |
| total_assets_yr2 | float | |
| total_assets_yr1 | float | |

**Cash Flow**
| Column | Type | Notes |
|---|---|---|
| operating_cf_yr3 | float | ₹Cr |
| operating_cf_yr2 | float | |
| operating_cf_yr1 | float | |
| investing_cf_yr3 | float | |
| investing_cf_yr2 | float | |
| investing_cf_yr1 | float | |
| financing_cf_yr3 | float | |
| financing_cf_yr2 | float | |
| financing_cf_yr1 | float | |
| closing_cash_yr3 | float | Closing cash & equivalents |
| closing_cash_yr2 | float | |
| closing_cash_yr1 | float | |

### Ratios (most recent year at time of IPO)

**Profitability**
| Column | Type | Notes |
|---|---|---|
| ebitda_margin_pct | float | |
| ebit_margin_pct | float | |
| pat_margin_pct | float | |
| cash_profit_margin_pct | float | (PAT + depreciation) / revenue |

**Efficiency**
| Column | Type | Notes |
|---|---|---|
| roa_pct | float | |
| roe_pct | float | |
| roce_pct | float | |
| receivable_days | float | Debtor days |
| inventory_days | float | |
| payable_days | float | Creditor days |

**Valuation**
| Column | Type | Notes |
|---|---|---|
| price_to_book | float | P/B at issue price |
| ev_sales | float | EV / Net Sales |
| ev_ebitda | float | EV / Core EBITDA |

**Stability**
| Column | Type | Notes |
|---|---|---|
| debt_equity | float | |
| current_ratio | float | |
| quick_ratio | float | |
| interest_cover | float | |

**Per-share & market**
| Column | Type | Notes |
|---|---|---|
| book_nav_per_share | float | Book value per share (₹). Cannot be derived without total shares count — taken directly from ratios table. |
| ceps | float | Cash EPS = (PAT + Depreciation) / shares. Useful for capex-heavy businesses. Only way to get depreciation implicitly. |
| total_debt_mcap | float | Total debt / market cap at issue price. Leverage vs valuation — cannot compute without total shares. |

### Growth (at IPO time)
| Column | Type | Notes |
|---|---|---|
| sales_cagr_1y | float | % |
| sales_cagr_3y | float | % |
| sales_cagr_5y | float | % — often absent for young SMEs |
| operating_profit_cagr_1y | float | % |
| operating_profit_cagr_3y | float | % |
| pat_cagr_1y | float | % |
| pat_cagr_3y | float | % |
| roe_avg | float | Average ROE over available years |
| roce_avg | float | Average ROCE over available years |

---

## 6. Columns deliberately excluded

| Removed | Reason |
|---|---|
| allotment_date, refund_date, share_delivery_date | Fixed T+6/7/8 process. Zero analytical value. |
| face_value | No pattern value — baked into EPS and P/E already. |
| gmp_rs | Raw ₹ amount — not cross-IPO comparable. gmp_pct is the usable form. |
| registrar | Back-office entity (runs allotment lottery, refunds, demat credit). No influence on listing performance. |
| total_income_yr1/2/3 | Net sales + other income. Other income is non-recurring noise. net_sales is the clean signal. |
| pbt_yr1/2/3 | Profit before tax. PAT is present; the tax line rarely drives IPO patterns. |
| fresh_issue_cr, ofs_cr, ofs_pct | Confirmed absent from Sharescart detail pages — not available for either SME or Mainboard. |
| sub_shni_x, sub_bhni_x | Sharescart subscription table shows only NII combined — S-HNI / B-HNI split not available. |
| industry | Not returned by the list API per row, not on detail pages. Stays null — no source found. |
| issue_size_cr | Sharescart shows `--` for all listed IPOs. Column kept in schema for future enrichment. |
| gmp_pct | Sharescart shows `--` for IPOs that listed some time ago. Only available for recent/upcoming IPOs. |

---

## 7. Methodology cautions

**Survivorship bias:** Must include delisted / suspended / withdrawn IPOs. If Sharescart omits these, a second source is needed. This is a data quality requirement, not optional.

**Holdout set:** Reserve the most recent ~3 months of IPOs. Do not use them during pattern-hunting. Validate any discovered pattern against the holdout before declaring it real.

**Small sample / overfitting:** SME segment especially. Any pattern should hold on the holdout AND across multiple years independently.

---

## 8. Deferred scope (not in v1)

- 2020–2022 historical gap (IPO Platform or Trendlyne — both 403'd, need cloudscraper/XHR approach)
- Ticker enrichment (ticker_ns / ticker_bo — null in v1)
- Price history collector (yfinance + bhavcopy)
- Layer 3 pattern computation (see docs/patterns.md)
- Market maker data for SME — source TBD
- Full BRLM list for multi-banker mainboard deals
- Anchor investor allocation — present on mainboard detail pages, verify on Sharescart
