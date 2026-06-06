# Data-Refresh Flow (v1+v2 combined) + 2026 Forward-Test — Design Spec

**Date:** 2026-06-06 · **Approved:** yes (auto-mode through build → real refresh → forward-test report)

## Goal
One safe CLI command that brings the dataset to today: ingests the IPOs listed since the freeze
(newest in dataset: 2026-01-07 — ~5 months missing), extends prices/outcomes for everyone, re-runs
the pipeline, and consciously updates every safety rail. Then: score the newly-ingested 2026 IPOs
as a genuine out-of-sample holdout and report how the system's signals held up (EARLY read only).

## Interface
`PYTHONPATH=. python run_refresh.py` → **dry-run report** (days of prices missing, new IPOs detected,
what would change). `--apply` executes. Resume-safe; each phase logged; aborts before the pipeline
if any pull fails. The existing app button keeps working (detection) and its caption now points to
the real command.

## The movable-facts file — `data/master/substrate_meta.json`
`{as_of, rows, archive_pointer, last_refresh}` — written ONLY by the refresh (and seeded once at
build time with today's frozen values). Read by: `layer3/config.AS_OF_DATE` (falls back to the
hardcoded date if absent), `verify.py` (rows + backup-pointer checks), `tests/data` (row count).
Golden numbers move to `data/reference/golden_numbers.json` (values + tolerances), read by
`tests/data/test_headline_numbers.py`; the refresh re-derives them and prints OLD → NEW before
writing. Net effect: a refresh is a data operation; scripts never edit source files.

## Apply sequence (phases; each idempotent/resume-safe)
0. **Preflight:** git clean; fast suite green (`--skip-tests` override exists but discouraged).
1. **Snapshot:** `data/master/` → `archive/pre_refresh_<YYYYMMDD>/`; recorded in meta.
2. **Detect new IPOs:** existing `find_new()` (Chittorgarh by year) → list of new ISINs.
3. **Ingest new IPOs** (only the new ISINs; every scraper already exists, this wires them):
   a. Append rows to the Chittorgarh raw list + pull each one's DETAIL page (issue price, dates,
      lot, listing prices, promoter, objects — same raw schema step 01/02 already consume).
   b. Subscription (NSE for MB, ipowatch for SME), GMP (ipowatch/investorgain), sector/mcap
      (03f path), financials via screener (RATE-LIMITED: 1 worker + cooldowns; partial results
      acceptable — gaps recorded, never blocking).
   c. Ticker validation for the new ISINs (06 logic, yahoo) — failures flag, not block.
4. **Prices for everyone:** `bhavcopy_ohlc.run(last_price_date+1 → today)` (native incremental,
   covers old + new ISINs in the same daily files). New ISINs' history starts at listing.
5. **Aux reference pulls:** indices (nifty50 + smallcap), corp_actions (current year, merged+deduped
   into the reference CSV), delistings (full re-pull; cheap).
6. **Move the clock:** meta.as_of = today.
7. **Pipeline:** full chain `01 → 09` via run_all steps (00/lt are longterm-only, skipped; 06 ran in
   3c above for new ISINs only). The 30s offline chain is showdown-certified; 01-03 rebuild base
   including the new raw rows.
8. **Rails re-derive:** meta.rows; goldens re-derived (printed OLD → NEW); fast suite MUST pass;
   `SHOWDOWN`-lite: the sandbox identity test's allowed-diff buckets refresh by design (post-refresh,
   the substrate IS the new pipeline output, so the sandbox test gets STRONGER: expected diffs → 0
   except the 3 market-maker folds, which the refresh re-applies from a new override file
   `data/reference/manual_overrides.csv` — closing that wart permanently).
9. **Outputs:** `run_weights` re-derive; report rebuild; summary printed (days pulled, new IPOs in,
   horizons newly matured, golden changes).

## Rollback
`cp archive/pre_refresh_<date>/* data/master/` + restore meta from the snapshot (the snapshot
includes meta). One documented command in WORKFLOWS.md.

## The forward test (after the refresh lands)
New module `layer3/forward_test.py` + `run_forward_test.py` (read-only): for the newly-ingested
2026 cohort (listed after 2026-01-07, never seen by any weight/threshold derivation):
- Score each with the frozen `data_informed` scorecard AS IF at IPO time (features only).
- Compare score quintiles vs realized EARLY outcomes: listing pop, 1m/3m return-from-listing,
  early MAE (worst dip), wipeout-flag hit-rate vs early losers.
- GMP→pop relation check on the new cohort (the strongest short-horizon signal).
- HONESTY RAILS: N is small (~100-200), horizons ≤5 months, no 1y/3y verdicts — every output
  labeled "EARLY READ"; min-N floors enforced; result → `docs/research/forward_test_2026.md`
  (+ printed). This becomes a repeatable command to re-run as the cohort ages.

## Testing the new machinery itself
- Unit: meta read/write round-trip; golden re-derive math; manual-overrides application;
  ingest-row schema mapping (fixture HTML/JSON → raw row, no network).
- The real proof: the executed refresh ends with the FULL suite green on the new substrate.
- New tests register in project_map (TEST_ROUTING entries for run_refresh.py + forward_test).

## Out of scope (recorded)
App-button-triggered apply (CLI only; button stays detection+instructions). Intraday/live prices.
Auto-scheduling (cron) — manual command by design. v2 SME-board migrations.

## Success criteria
1. Dry-run prints a sane plan. 2. `--apply` runs end-to-end on real data. 3. Full suite green
AFTER the refresh (goldens consciously re-derived). 4. App shows the 2026 IPOs + prices through
today. 5. Old substrate restorable from archive. 6. Forward-test report delivered with honest
labels. 7. Git LOCAL-ONLY throughout.
