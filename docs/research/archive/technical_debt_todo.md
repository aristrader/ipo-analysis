# Technical Debt & Hacky Workarounds TODO List

*(Note: The MFE/MAE Clamping Hack was removed in `pipeline/07_returns_summary.py` and `pipeline/09_assemble.py` during this audit).*

## 1. Hardcoded Date/Year Limitations
- **Location:** `pipeline/01_build_base.py`
- **Description:** `_boom_years()` uses a hardcoded fallback year (`hi = 2026`) when `substrate_meta.json` is unavailable. The file's own docstring notes that a previous hardcoded range (`2020..2025`) silently dropped 2026 IPOs. The current fallback will cause the exact same bug in 2027.
- **Action:** Replace `hi = 2026` with dynamic logic using `datetime.now().year + 1`.

## 2. Financial Data Dropped (Documented TODO)
- **Location:** `pipeline/03_enrich.py`
- **Description:** Screener financials for 2020-2022 are completely skipped. An explicit comment states: `Screener financials for 2020-22 is a documented TODO (gaps.csv), not auto-filled here.` It relies on legacy cached files (`archive/derived/*_OLD.csv`) and dumps the rest into `gaps.csv`.
- **Action:** Integrate real back-filling functionality instead of dropping data and masking it with old cache files.

## 3. Brittle Search Workaround (DuckDuckGo Scraping)
- **Location:** `scrapers/corporate_actions_trendlyne_advanced.py`
- **Description:** When exact symbol resolution fails on Trendlyne, the script resorts to parsing duckduckgo HTML search results (`https://duckduckgo.com/html/?q=site:trendlyne.com/...`). 
- **Action:** Replace this extremely brittle third-party dependency with a proper URL discovery method or a reliable API call.

## 4. Incomplete Detail Scraper
- **Location:** `scrapers/chittorgarh.py`
- **Description:** The documentation indicates the detail parsing phase is incomplete: `detail → scrape each detail page for market_maker, OFS, anchor, subscription, financials (TODO)`.
- **Action:** Implement the detailed parsing for these fields to avoid missing foundational universe data.

## 5. Multi-Model Orchestration (Postponed)
- **Location:** `thinktank/orchestration/`
- **Description:** Set up the dual-agent architecture (Claude Opus Architect + Gemini Pro Executor) using the underlying LangGraph state machine. This was deliberately postponed by the user.
- **Action:** Modify `nodes.py` and `graph.py` to correctly route and pass state between the high-level Planner agent and the downstream Executor agent.

## 6. NEW: More Hardcoded Timebombs & Caps
- **Location:** `scrapers/chittorgarh.py`
- **Description:** The scraper has `YEARS = [2020, 2021, 2022, 2023, 2024, 2025]` completely hardcoded. Additionally, `LIST_API` hardcodes `2026-27` as the FY parameter. Also, `while page <= 300` acts as a hardcoded pagination cap.
- **Action:** Convert `YEARS` to dynamically scale, and implement robust pagination detection instead of an arbitrary 300-page limit.

## 7. NEW: Silent Try-Except Data Drops
- **Location:** Multiple (`07_returns_summary.py`, `02_detail.py`, `03_subscription.py`, `chittorgarh.py`)
- **Description:** Found 7 instances where the pipeline wraps core logic in a `try...except Exception:` block and either executes a `continue`, `break`, or `pass`. For example, in `07_returns_summary.py`, any parsing anomaly will silently drop the entire ticker from the final summary instead of halting to fix the bug.
- **Action:** Remove naked `Exception` catches. Explicitly handle known errors (e.g., `requests.exceptions.Timeout`) and let structural data bugs crash the build so they can be fixed.
