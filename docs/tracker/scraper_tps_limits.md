# Scraper TPS (Transactions Per Second) Limits & Configurations

This document serves as the central reference for rate limiting, bot protection, and TPS settings across all scraping targets in the IPO pipeline.

## 1. Yahoo Finance (`yfinance` / chart API)
- **TPS Limit:** Extremely high / No hard limit.
- **Concurrency:** Can safely run 20+ concurrent workers (achieving ~112 requests/second).
- **Bot Protection:** Minimal. Does not block `curl` or standard Python requests.
- **Coverage:** Excellent for Mainboard stocks (~850+ resolve perfectly). Lacks data for ~403 SME stocks (BSE SME / NSE Emerge).
- **Recommendation:** Always use `concurrent.futures.ThreadPoolExecutor` with max_workers=20. Do NOT run sequentially.

## 2. Screener.in
- **TPS Limit:** Low (~1 TPS).
- **Bot Protection:** High. Actively rate-limits and returns `404 Not Found` or `403 Forbidden` if TPS exceeds 2-3 requests/second without an active session. Requires `time.sleep(1)` between requests.
- **Authentication:** Some endpoints (like Corporate Actions) require an active logged-in session cookie to return data.
- **Recommendation:** Throtte heavily. Use only as a secondary fallback.

## 3. Trendlyne
- **TPS Limit:** N/A (Blocked at Firewall).
- **Bot Protection:** Extreme (Cloudflare).
- **Workaround:** Standard `requests` or `urllib` will instantly fail with `403 Forbidden`. Must use `curl_cffi` (impersonating Chrome) or headless `Playwright` with stealth plugins to bypass Cloudflare.
- **Recommendation:** Very slow (3-5s per request due to browser overhead). Use only for targeted gap-filling (SME stocks), never for the full universe.

## 4. Moneycontrol
- **TPS Limit:** Moderate.
- **Bot Protection:** Moderate to High.
- **Structure:** Tables are rendered dynamically client-side using Next.js. Older `.php` endpoints are deprecated.
- **Workaround:** Requires `Selenium` headless webdriver to wait for DOM elements to render.
- **Recommendation:** Slow (~3s per request). Use as a targeted fallback for SME stocks missing from Yahoo Finance.

## 5. Chittorgarh
- **TPS Limit:** Moderate (~5 TPS).
- **Bot Protection:** Low.
- **Recommendation:** Can run via standard `BeautifulSoup` and `requests`. Sequential scraping is fine, but a small `ThreadPoolExecutor` (3-5 workers) is safe.

## 6. NSE Corporate Actions API (AUTHORITATIVE)
- **TPS Limit:** Low (~1-2 TPS with delays).
- **Bot Protection:** Moderate. Requires a primed browser session via `curl_cffi` (Chrome impersonation) + NSE cookie priming + Referer header.
- **Authentication:** Session cookies must be primed first (see `scrapers/nse_session.py`).
- **Data:** Most comprehensive for Indian equities AND SME. Returns ISIN, symbol, action type, raw subject text, and ex-date.
- **Script:** `scrapers/corp_actions.py` — pulls year-by-year (2006–2025) for both `equities` and `sme` indices.
- **Output:** `data/reference/corp_actions.csv` — **1,509 records** (the pipeline's primary source of truth).
- **Recommendation:** This is the golden source. Use Yahoo/Moneycontrol only for cross-validation.

## 7. Investing.com
- **TPS Limit:** Moderate.
- **Bot Protection:** High (Cloudflare).
- **Workaround:** Must use `curl_cffi` with Chrome impersonation (`impersonate="chrome110"`).
- **Script:** `scrapers/corporate_actions_investing.py`
- **Coverage:** Splits only (no bonus data). Limited to stocks with `company_slug` mapping.
- **Recommendation:** Use as a tertiary verification source only.
