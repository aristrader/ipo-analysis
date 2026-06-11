# Boom-cohort sector / industry / market-cap recovery

## Problem
The boom screener enrichment (`pipeline/03b_fill_financials_screener.py`) grabbed only
financials from screener — not the sector/industry/market-cap breadcrumb. As a result
`data/raw/screener/company_meta.csv` covers the longterm cohort well but barely touches
boom, so in `data/master/universe.csv`:

- boom `broad_sector` coverage = **276 / 1269 (21.7%)**  (vs longterm 738/1027 ≈ 72%)
- boom `market_cap_cr` coverage = **277 / 1269 (21.8%)**

These companies already resolved on screener (their financials prove it), so this was a
cheap, targeted **re-pull of just the breadcrumb** — not a fresh resolution problem.

## Target list
Boom-cohort ISINs that (a) appear in `data/raw/screener/financials.csv` (resolved on
screener) AND (b) currently lack `broad_sector` in `universe.csv`, AND (c) have an
NSE/BSE code in the boom base masters to re-resolve with.

- boom missing `broad_sector`: 993
- of those, resolved on screener (in `financials.csv`): **400** ← the target list
  (the other ~593 never resolved on screener and are out of scope for this pass)

The earlier `match_log.csv` slug map did not cover these (financials were written in a
prior run whose slugs weren't retained), so each target is re-resolved via the SAME
name-verified `scrapers/screener.resolve()` path that originally found the financials,
using its NSE/BSE code + company name from `_base_mainboard.csv` / `_base_sme.csv`.

## Fetch approach
`pipeline/03f_sector_mcap.py`:
- REUSES `scrapers/screener.py` — `resolve()` (name-verified), `page_sector()`,
  `page_marketcap()`. No parallel scraper.
- 1 worker, internal + between-company sleeps (default DELAY=1.2s), circuit-breaker after
  8 consecutive errors. RESUME-SAFE: re-run skips ISINs already in the output or skip file.
- STRICT: a row is written only when `resolve()` name-matches the page. A non-match is
  logged to `data/raw/screener/sector_mcap_skipped.csv` and NOT guessed (project rule:
  flag/skip, never mis-assign).
- Output: `data/raw/screener/sector_mcap.csv` with columns
  `isin,broad_sector,sector,industry,market_cap_cr,source` (source='screener').
  `broad_sector` is screener's "Broad Sector" breadcrumb — the SAME field 08's
  `company_meta` fold reads for longterm, kept so the fold fills `broad_sector` faithfully
  rather than inventing a sector→broad_sector mapping the pipeline doesn't have.

## Result (run 2026-05-31, DELAY=1.2s, single uninterrupted pass)
- targets fetched: **400**
- **recovered: 376** (375 with full sector breadcrumb + market cap; 1 had market cap but
  no sector breadcrumb on the page)
- skipped: **24** — all `no-name-match` (page did not verify to the right company; correctly
  skipped, see `data/raw/screener/sector_mcap_skipped.csv`)
- errors: 0; circuit-breaker: not tripped (screener did not throttle this pass)

### Projected boom coverage after folding in (simulated + verified via a 08 dry-run)
| metric | before | after | delta |
|---|---|---|---|
| boom `broad_sector` | 276 / 1269 (21.7%) | **651 / 1269 (51.3%)** | +375 |
| boom `market_cap_cr` | 277 / 1269 (21.8%) | **652 / 1269 (51.4%)** | +375 |

A 08 dry-run confirmed **longterm rows are completely untouched** (0 `broad_sector` and 0
`market_cap_cr` changes) and the recovered boom `market_cap_class` buckets are sensible
(micro 241 / small 162 / mid 187 / large 62). `universe.csv` was restored to its pre-fold
state afterwards — the user applies the fold by running 08 (below).

## The fold (wired in `pipeline/08_build_universe.py`, new step `[3b]`)
After the existing `company_meta` fold (step `[3]`), 08 now left-joins
`data/raw/screener/sector_mcap.csv` by ISIN and fills **only where `broad_sector` /
`market_cap_cr` are currently empty** — it never overwrites values already set (so longterm
stays untouched). `market_cap_class` is computed with the SAME existing `mktcap_class()`
bucketing (micro <300, small <2000, mid <20000, large ≥20000 ₹cr). If
`sector_mcap.csv` is absent, step `[3b]` prints a hint and skips.

## Skipped / ambiguous ISINs
24 ISINs, all `no-name-match` — the screener page reached via the exchange code did not
name-verify to our company (e.g. code reassigned/merged entity), so no sector/mcap was
written. Listed in `data/raw/screener/sector_mcap_skipped.csv`. These are NOT regressions;
they simply remain in the existing boom gap.

## Re-running / resuming
To fetch (or resume after a screener block — re-run continues where it stopped):

    source .venv/bin/activate
    PYTHONPATH=. python pipeline/03f_sector_mcap.py        # default DELAY=1.2s
    PYTHONPATH=. python pipeline/03f_sector_mcap.py 2.0     # slower if throttled

## Command to fold it into universe.csv
    PYTHONPATH=. python pipeline/08_build_universe.py

(Then run `09_assemble` yourself as usual. This pass did not run 09 or touch
`data/master/ipo_analysis.csv`.)
