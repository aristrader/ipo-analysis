---
name: ticker-validation-price-source
description: "Ticker validation result + the Layer 2 price-source decision (Yahoo can't cover SME; use bhavcopy)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 01820f2d-c29a-4f29-84ad-349ce26b70fa
---

## Ticker validation (2026-05-31) — pipeline/06_validate_tickers.py

Validated all 1269 master tickers against Yahoo (concurrent, 20 workers, ~112/s).
Output: `data/master/ticker_validation.csv` (cols incl. `resolves`, `price_source`).

**Result: 859 resolve on Yahoo, 410 don't (403 of them SME).** The non-resolution is
NOT throttling and NOT wrong tickers — confirmed by: low-concurrency recheck recovered 0,
slow manual tests genuinely fail (404 / no_data), and ETERNAL.NS/544011.BO resolve fine
alongside. It is **Yahoo's poor coverage of Indian SME (NSE Emerge / BSE SME)**.

Cross-checked the 410 against official bhavcopy by ISIN: **371 ARE in bhavcopy** (valid
securities Yahoo just lacks). So **1230/1269 tickers confirmed valid** by Yahoo OR bhavcopy.
The remaining **39** (`data/master/price_source_review.csv`) are almost all very recent SME
(BSE codes 544600+, late-2025/2026) — not yet in the bhavcopy cache; will be covered when
current bhavcopy is pulled. A few older ones (DU Digital, Trekkingtoes, ICL Dairy) to spot-check.

**price_source routing for Layer 2: yahoo=859, bhavcopy=371, none=39.**

### DECISION for Layer 2 (daily price history)
- **Yahoo is NOT viable as the SME price source.** Use **bhavcopy** (official NSE+BSE EOD,
  ISIN-keyed, one file per trading day covers ALL securities incl. SME) as the PRIMARY source.
  `scrapers/bhavcopy.py` already exists. Full history = ~1500 trading-day files for 2020-2025.
- Yahoo can be a convenience secondary for mainboard (859 rows) where it has data.
- Validation speed lesson: 20 concurrent workers on Yahoo chart API = ~112/s, accurate, no ban.
  Live progress written to logs/ticker_validation_progress.txt.

See [[ipo-project-state]].
