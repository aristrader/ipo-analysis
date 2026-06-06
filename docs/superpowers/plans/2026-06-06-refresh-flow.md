# Refresh Flow (v1+v2) + Forward Test — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or
> superpowers:executing-plans. THIS RUN: inline auto-mode (user-approved), commits per task.
> Spec: `docs/superpowers/specs/2026-06-06-refresh-flow-design.md` (sequence, meta-file, honesty rails).

**Goal:** `run_refresh.py --apply` brings the dataset to today (new IPOs in + prices extended),
with every safety rail consciously updated; then `run_forward_test.py` scores the new 2026 cohort.

**Found-bug to fix en route:** 01_build_base hardcodes years 2020-2025 → 2026 IPOs silently dropped.

### Task 1: Movable-facts rails (meta + goldens as data)
- Create `data/master/substrate_meta.json` seeded {as_of:"2026-05-31", rows:2296,
  archive_pointer:"archive/pre_drhp_20260601", last_refresh:null}.
- `layer3/config.py`: AS_OF_DATE reads meta if present (fallback unchanged); add SUBSTRATE_META path.
- `verify.py`: rows + backup-pointer checks read meta (drop hardcoded 2296/pre_drhp path).
- `project_map.py` INVARIANTS: substrate_rows/as_of delegate to meta (keep n_findings literal).
- Goldens → `data/reference/golden_numbers.json` (values+tolerances+derived_at);
  `tests/data/test_headline_numbers.py` reads it; `tools/refresh/derive_goldens.py` writes it
  (prints OLD → NEW). Seed with current values.
- Tests: meta round-trip + config fallback + goldens-file schema. Full suite green (same numbers,
  new plumbing). Commit.

### Task 2: Pipeline year-dynamic + manual overrides
- 01_build_base: years = 2020..(meta.as_of year). Verify sandbox-style: re-run 01 in /tmp copy,
  output identical today (2026 rows appear only after ingestion).
- `data/reference/manual_overrides.csv` (isin,column,value,reason,date) seeded with the 3 market
  makers; applied at the END of 09_assemble; sandbox-test ALLOWED_CELLS for them removed (the
  re-run now reproduces them). Commit.

### Task 3: Ingestion wrappers (`tools/refresh/ingest.py`) — per-source, new-ISINs only, append-to-raw
- chittorgarh: pull_year(current years) rows not in urls.csv → append; scrape_detail per new row →
  append to details.csv. (Schema = existing headers; fixture test from a saved detail dict.)
- subscription: NSE (MB symbols) via nse_subscription callables; SME via ipowatch matcher.
- GMP: ipowatch + investorgain for the new names (existing matchers, append to their raw csvs).
- financials/sector/mcap: screener search→fetch per new ISIN (1 worker, cooldown, best-effort —
  failures recorded to refresh log, never block); company_meta + financials.csv append (03b/03f/08
  consume as-is).
- ticker check: 06's yahoo probe for new ISINs only; failures flag into ticker_validation review.
- Each wrapper: idempotent (skips ISINs already in raw), returns counts for the summary. Commit.

### Task 4: `run_refresh.py` orchestrator rewrite
- Default dry-run: days-of-prices missing (per price file max date vs today), find_new() count+list,
  aux staleness; prints the plan. `--apply` phases per spec §Apply (preflight git-clean+tests;
  snapshot to archive/pre_refresh_<date>; ingest; bhavcopy run(last+1, today); indices/corp_actions
  (current-year merge+dedupe)/delisting; meta.as_of=today; chain 01→09 via run_all steps; goldens
  re-derive; meta.rows; fast suite; run_weights; report rebuild; summary).
- `--resume <phase>` (phases are idempotent). App button caption → points at the command. Commit.

### Task 5: Unit tests for the new machinery
- tests/pipeline/test_refresh_lib.py: meta io, goldens derive math (on a synthetic frame),
  overrides application, ingest row-mapping fixtures, year-dynamic filter. Routing entries in
  project_map.TEST_ROUTING for run_refresh.py/tools/refresh. Full fast suite green. Commit.

### Task 6: EXECUTE the real refresh
- `python run_refresh.py` (dry-run) → sanity-check the plan with real numbers.
- `python run_refresh.py --apply` (long: bhavcopy ~110 days x2; screener for ~new IPOs rate-limited;
  background task, monitor logs). On completion: full suite + SHOWDOWN gate green on the NEW
  substrate; app health; summary. Any failure: fix-forward or rollback (documented cmd). Commit
  (new substrate + meta + goldens; the archive snapshot is gitignored like other archives).

### Task 7: Forward test
- `layer3/forward_test.py` + `run_forward_test.py` (read-only): cohort = listing_date > 2026-01-07
  (never seen by weights). Score with frozen data_informed scorecard (features only); compare score
  quintiles vs listing pop / 1m / 3m returns-from-listing / early MAE; wipeout-flag early hit-rate;
  GMP→pop check. Min-N floors; every figure labeled EARLY READ (≤5 months). Output:
  docs/research/forward_test_2026.md + stdout. +tests (structure + honesty rails fire). Commit.

### Task 8: Cleanup + report
- STATUS (live-state lines: as_of now moves with meta; refresh command), DONE entry, CLAUDE.md
  (refresh section + counts), WORKFLOWS (refresh protocol + rollback cmd), project_map (new files),
  verify PASS, suites green. Final user report: built / executed / what the forward test showed.

## Self-review
Spec coverage: meta/goldens→T1, overrides+yearbug→T2, ingest→T3, orchestrator→T4, tests→T5,
execution→T6, forward-test→T7, cleanup→T8 ✓. No placeholders; decisions inline ✓. Names consistent
(substrate_meta.json, golden_numbers.json, manual_overrides.csv, tools/refresh/, run_forward_test.py) ✓.
