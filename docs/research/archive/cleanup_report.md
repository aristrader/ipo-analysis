# Repo cleanup pass — report

Date: 2026-05-31. Conservative pass (no `rm` except `.DS_Store`; everything else `mv`'d into `archive/`).

## (a) Files moved (from → to)

### Superseded scripts → `archive/scripts/`
- `scrapers/niftyindices.py` → `archive/scripts/scrapers/niftyindices.py`
  (superseded by `scrapers/indices.py`; niftyindices POST endpoint is blocked from here. Grep confirmed: only self-references, nothing imports it.)
- `pipeline/checks/explore_chittorgarh.py` → `archive/scripts/pipeline_checks/explore_chittorgarh.py`
  (one-off exploration; zero references anywhere.)

### Pre-rebuild analysis + derived outputs → `archive/`
- `analysis/clean.py` → `archive/analysis/clean.py`
  (operated on `data/raw/*_events.csv` → `data/derived/*_clean.csv`, the OLD pre-ISIN-rebuild flow; no module imports `analysis.clean`.)
- `data/derived/backfill_2020_2022_chittorgarh.csv` → `archive/data_derived/`
- `data/derived/mainboard_clean.csv` → `archive/data_derived/`
- `data/derived/sme_clean.csv` → `archive/data_derived/`
- `data/derived/manual_review_tickers.csv` → `archive/data_derived/`
- `data/derived/missing_ipos_2023_2025.csv` → `archive/data_derived/`
- `data/derived/ticker_review.csv` → `archive/data_derived/`
- `data/derived/backups/` (5 timestamped pre-merge backup dirs) → `archive/data_derived/backups/`
  (All of `data/derived/` was pre-rebuild staging, fully superseded by `data/master/`. `.gitkeep` left in `analysis/` and `data/derived/`.)

### `data/master/` tidy → `data/master/review/`
Moved (review/flag CSVs): `gaps.csv`, `name_isin_review.csv`, `price_source_review.csv`,
`screener_financials_review.csv`, `ticker_conflicts.csv`, `xcheck_review.csv`,
`reconciliation_report.csv`, `ticker_validation.csv`, `price_missing.csv`
→ all into `data/master/review/`.

`data/master/` top level now holds exactly: the 7 final products
(`ipo_analysis.csv`, `universe.csv`, `returns_summary.csv`, `mainboard.csv`, `sme.csv`,
`longterm_mainboard.csv`, `longterm_sme.csv`), the `_base_*.csv` staging, `delisting.csv`, `README.md`, and `review/`.

## (b) `.DS_Store` removed: 2
`./.DS_Store` and `./data/.DS_Store` (the only allowed `rm`).

## (c) Needs human decision / flagged (left in place)

1. **`data/reference/bhavcopy/` (~37M) — NOT archived (intentionally left).**
   The spec said to archive it ONLY if nothing in `pipeline/` reads that exact path at runtime.
   It IS read/written at runtime: `scrapers/bhavcopy.py` uses it as `CACHE_DIR`, and
   `scrapers/delisting.py` globs `data/reference/bhavcopy/*.csv` (`BHAVCOPY_DIR`) to derive last-appearance/
   delist dates. Moving it would break `delisting.py` (which feeds `delisting.csv` → step 07 + the price merge).
   Left in place and flagged. To archive later, the path constants in those two scrapers must be updated first.

2. **`data/master/delisting.csv` — NOT moved into `review/` (intentionally).**
   Although the TODO lists it among "review/flag CSVs", it is actually a price-pipeline DATA INPUT:
   read by `pipeline/07_returns_summary.py` and `scrapers/screener_prices_merge.py` via `data/master/delisting.csv`.
   Moving it is a dependency change (and an agent may be running the pipeline concurrently), so it was left top-level and flagged.

3. **Docs consolidation — NOT done; left as-is and flagged.**
   The spec's premise (overlap among `design.md`/`decisions.md`/`changelog.md`/`discussion.md`) does not hold here:
   - There is NO `docs/discussion.md`.
   - `docs/decisions.md` is actually titled "Discussion — Full Thought Process & Context" (the discussion doc).
   - `docs/design.md` is a distinct design spec.
   - `docs/changelog.md` is the "E2 Session Record" changelog.
   These three are distinct (design spec vs thought-process vs changelog), not redundant duplicates.
   Per "when in doubt, leave them and note", all docs were left untouched. A human may want to rename
   `decisions.md` → `discussion.md` for accuracy, but that's a judgement call, not a cleanup.

4. **`archive/E2_changelog.md` — already folded; left in archive.**
   `docs/changelog.md` is a strict superset: identical headers through "Update 5" PLUS an extra
   "Task 12: ISIN-keyed rebuild finalized" section. So `archive/E2_changelog.md` is the older copy already
   reflected in the main changelog, and it already lives in `archive/`. No fold needed; left as-is.

## (d) `run_all.py` created: YES (repo root)
Orchestrator that runs each step as `PYTHONPATH=. python <path>`, prints each step, stops on first non-zero exit,
supports `--from <step>` (resume) and `--list`. Canonical order (step keys → path):

```
00     pipeline/00_build_longterm_spine.py
lt/02  pipeline/longterm/02_detail.py
lt/03  pipeline/longterm/03_subscription.py
lt/04  pipeline/longterm/04_financials.py
01     pipeline/01_build_base.py
02     pipeline/02_attach_detail.py
03     pipeline/03_enrich.py
03b    pipeline/03b_fill_financials_screener.py
03c    pipeline/03c_fill_subscription_nse.py
03d    pipeline/03d_fill_ipowatch.py
03e    pipeline/03e_fill_gmp_investorgain.py
04     pipeline/04_verify.py
05     pipeline/05_reconcile.py
06     pipeline/06_validate_tickers.py
07     pipeline/07_returns_summary.py
merge  scrapers/screener_prices_merge.py
08     pipeline/08_build_universe.py
09     pipeline/09_assemble.py
```
(Longterm enrichment `lt/02–04` placed right after the `00` spine, before the boom-cohort numbered steps,
matching how those scripts enrich the long-term masters. `pipeline/listing_remediation.py` is NOT a standalone
step — it is imported inside step 07 and the merge, per CLAUDE.md.) Not executed, only created.

## (e) Code path references updated (review CSVs → `data/master/review/`)
Each write path was repointed to the new location (with an `os.makedirs('data/master/review', exist_ok=True)` guard;
added `import os` to the two files that lacked it). All edited files `py_compile`-clean.
- `pipeline/03_enrich.py` — `gaps.csv` (+ makedirs target changed to review/)
- `pipeline/04_verify.py` — `ticker_conflicts.csv`, `name_isin_review.csv` (+ added makedirs)
- `pipeline/03b_fill_financials_screener.py` — `screener_financials_review.csv` (+ added makedirs)
- `pipeline/05_reconcile.py` — `reconciliation_report.csv` (+ added `import os`, makedirs)
- `pipeline/06_validate_tickers.py` — `ticker_validation.csv` + docstring path (+ added `import os`, makedirs)
- `pipeline/09_assemble.py` — `xcheck_review.csv` (+ added makedirs)
- `pipeline/checks/check_05_reconcile.py` — reads `reconciliation_report.csv` from the new path

(`price_source_review.csv` and `price_missing.csv` are not referenced by any code — moved file-only, no edits.)

### Doc references updated
- `CLAUDE.md` — repo-map "Review/flag files" line now points to `data/master/review/` and notes `delisting.csv` stays top-level;
  "Running" section now documents `run_all.py`.
- `README.md` — folder map (pipeline 00→09, review subdir, longterm cohort, 2006–2025) + Build section now uses `run_all.py`.
- `data/master/README.md` — documents `delisting.csv` (top-level input) and the `review/` subdir contents.
