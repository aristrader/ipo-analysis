# Final-Showdown Testing & Verification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.
> THIS RUN: executed inline by the main session (user-authorized auto-mode), subagents for Task 1 only.

**Goal:** Prove data+logic+pipelines+app are correct and runnable, and leave a regression net where any
future breaking change trips a failing test.

**Architecture:** Six phases — audit → always-on data-integrity + logic-gap tests → opt-in (`-m showdown`)
execution proofs in a /tmp sandbox → scripted mutation validation of the existing suite → mechanical
change→tests routing through project_map + the verify hook → cleanup + report. Real `data/master/` stays
byte-identical throughout; every phase ends with a commit.

**Tech stack:** pytest (+`showdown` marker), rsync sandbox, Playwright (already installed), git-restore
mutation harness, the existing project_map.py/verify.py machinery.

**Spec:** `docs/superpowers/specs/2026-06-04-final-showdown-testing-design.md` (approved). Tolerances,
invariant list, and success criteria live there — this plan is the task breakdown.

---

### Task 1: Coverage audit (2 parallel read-only subagents)
**Files:** Create `docs/research/showdown_audit.md`
- [ ] Dispatch Agent A (logic side): inventory functions in `layer3/spine.py`, `layer3/predictor/*.py`,
      `layer3/backtest/*.py`, `layer3/validate.py`, `layer3/report.py`, `pipeline/lib.py`,
      `pipeline/listing_remediation.py`, 07 helpers; map against `tests/` (read test files); emit table
      `target | what could break | covered-by | gap | priority(P1 result-critical / P2 supporting / P3 display)`.
- [ ] Dispatch Agent B (data+pipeline side): every `ipo_analysis.csv` column (via `docs/schema.md`) →
      candidate invariant; every pipeline step + scraper parse fn → covered / gap / not-coverable(network);
      entry points → smoke status. Same table format.
- [ ] Merge both into `docs/research/showdown_audit.md`; P1 gaps become the Task-3 worklist.
- [ ] Commit: `git add docs/research/showdown_audit.md && git commit -m "Showdown P0: coverage audit"`

### Task 2: Data-integrity suite (always-on)
**Files:** Create `tests/data/__init__.py`, `tests/data/conftest.py` (session-scoped DataFrame fixtures
loading ipo_analysis/universe/returns_summary via `csv`-safe pandas read), `tests/data/test_substrate_integrity.py`
- [ ] Implement the 9 invariant groups from the spec §Phase 1 (row count/ISIN shape; cohort partition
      1269/1027; mae≤endpoint≤mfe for issue+listing entries ×1y/3y/5y; outcome_class↔current_return
      thresholds; listing_metrics_status enum + unreliable⇒nulled; compulsory/liquidation⇒−1.0;
      join integrity across the three masters; bounds (returns>−1.001, dates in 2006-01..AS_OF, issue_price>0);
      alpha recomputation on a deterministic 50-row sample ±2bp). Failure messages: first 5 offending isins.
- [ ] Run: `PYTHONPATH=. pytest tests/data -q` → expect PASS (or: real findings → triage; data bugs found
      here are FINDINGS for the report, fix only if genuinely wrong, data/master stays frozen → document).
- [ ] Full fast suite still green; commit.

### Task 3: Logic-gap tests (always-on)
**Files:** Create `tests/pipeline/test_merge_math.py`, `tests/scrapers/test_bhavcopy_parse.py`, plus one
file per P1 gap from the audit (paths per audit).
- [ ] Read `scrapers/screener_prices_merge.py` weekly MFE/MAE+clamp+timing block; write synthetic weekly
      fixture tests mirroring `test_compute_synthetic.py` style (hand-computed expectations + traps).
- [ ] `tests/scrapers/test_bhavcopy_parse.py`: inline fixture payloads for `bhavcopy.parse_bhavcopy`
      (NSE+BSE row shapes) and `bhavcopy_ohlc._num`/`parse_day`; exact-value asserts.
- [ ] Implement remaining P1 audit gaps (audit table = the worklist; each test behavior-pinned vs current code).
- [ ] Fast suite green; commit.

### Task 4: Execution proofs (`@pytest.mark.showdown`)
**Files:** Create `pytest.ini` (registers `showdown` marker + `addopts = -m "not showdown"` is NOT used —
default exclusion via marker expression in WORKFLOWS docs instead), `tests/showdown/__init__.py`,
`tests/showdown/test_pipeline_sandbox.py`, `tests/showdown/test_entrypoints.py`, `tests/showdown/test_app_smoke.py`
- [ ] `pytest.ini`: `[pytest] markers = showdown: slow end-to-end execution proofs (pytest -m showdown)`.
      Default fast runs use `pytest tests -m "not showdown"`? NO — keep plain `pytest tests` fast by
      auto-skipping: put `pytestmark = pytest.mark.showdown` in tests/showdown files + a conftest skip
      unless `-m showdown` or env SHOWDOWN=1: simplest reliable = `tests/showdown/conftest.py` with
      `collect_ignore` removed and a module-level `pytest.mark.skipif(os.environ.get("SHOWDOWN") != "1")`.
      DECISION: use env-gate (SHOWDOWN=1) + marker both; document `SHOWDOWN=1 pytest tests/showdown -q`.
- [ ] Sandbox test: rsync `-a --delete --exclude .git --exclude .venv --exclude archive --exclude logs`
      repo → `/tmp/ipo_showdown_sandbox/`; symlink sandbox/.venv → real .venv; run steps
      03b 03c 03d 03e 04 05 07 merge 08 09 via `subprocess.run([sys.executable, step], cwd=sandbox,
      env PYTHONPATH=sandbox)` each rc==0; then per-CSV cell-level diff vs real data/master for
      returns_summary/universe/ipo_analysis: classify diffs into EXPLAINED buckets (the post-pipeline
      remediation set — discover+enumerate from the actual diff; the test embeds the allowed bucket
      predicates) vs UNEXPLAINED (fail). Write `docs/research/showdown_pipeline_diff.md` with counts.
- [ ] Entry-point test: subprocess each of run_layer3_report.py / predict_ipo.py (MB+SME args) /
      run_backtest.py / run_validation.py / run_weights.py with cwd=REAL repo (read-only scripts),
      rc==0 + cheap output sanity (report html exists & mentions 29 findings; predictor stdout contains
      a score). Guard: assert data/master hash unchanged after each (catches accidental writers!).
- [ ] App smoke: start `streamlit run app.py --server.headless true` on a free port, Playwright chromium
      opens it, clicks all 5 tabs, asserts no "Traceback"/"Exception" text nodes; kill server in teardown.
- [ ] Network-step exclusions: py_compile 00/06/lt-02 + note in audit doc.
- [ ] Run `SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q` → all green; commit.

### Task 5: Mutation validation (one scripted batch)
**Files:** Create `tools/mutation/run_mutations.py`, `tools/mutation/mutations.py` (the table),
output `docs/research/showdown_mutation.md`
- [ ] mutations.py: list of dicts {file, old, new, tests} — ~40 entries across layer3/spine.py,
      layer3/predictor/scorecard.py, layer3/predictor/weights.py, pipeline/07 helpers,
      pipeline/listing_remediation.py, merge math, pipeline/lib.py (each old-string verified unique
      in file before inclusion).
- [ ] run_mutations.py: refuse if `git status --porcelain` non-empty for target files; for each entry:
      exact-replace → clear pycache → `pytest <tests> -q -x` (expect FAIL) → `git checkout -- file`;
      collect KILLED/SURVIVED; write the markdown report; exit non-zero if any SURVIVED.
- [ ] Run the batch; for every SURVIVED: write the missing test (always-on suites), re-run that mutation → killed.
- [ ] Re-run full fast suite green; commit (runner + report + any new tests).

### Task 6: Change-aware test routing
**Files:** Modify `project_map.py` (add `TEST_ROUTING` + include in render_map), `verify.py` (route
changed files; `--route` flag), `docs/WORKFLOWS.md`, `tests/test_project_map.py` (+1 test)
- [ ] TEST_ROUTING = ordered [(glob, [pytest targets/commands])] incl. fallback `*` → fast suite;
      showdown pointers for pipeline/07*, merge, 08/09, app.py.
- [ ] verify.py: `_changed_files()` via `git status --porcelain` (paths only) + `_route(paths)`;
      in --quiet mode print `CHANGED → RUN:` lines (only when non-empty); `--route` prints full table.
- [ ] New test: every routing target path exists / command references existing dir; globs compile.
- [ ] WORKFLOWS.md: routing + "SHOWDOWN=1 pytest tests/showdown = pre-release gate" + after-change rule.
- [ ] verify.py PASS; fast suite green; commit.

### Task 7: Cleanup + final report
- [ ] project_map.py: register new dirs/files (tests/data, tests/showdown, tools/mutation, pytest.ini)
      in DIRS/CONTEXTS; INVARIANTS unchanged (test count not stored there).
- [ ] STATUS.md: one summary line under NOW/backlog; DONE.md full entry; counts updated everywhere
      (CLAUDE.md three spots) to the new totals from `pytest --co`.
- [ ] `python verify.py` PASS; fast suite green; `git status` clean; data/master byte-identical.
- [ ] Commit; deliver the final did/found/fixed report to the user in plain language.

## Self-review (done at write time)
- Spec coverage: P0→T1, P1→T2, P2→T3, P3→T4, P4→T5, P5→T6, P6→T7. ✓
- No placeholders: decisions made inline (env-gate for showdown; rsync excludes; runner refuse-if-dirty). ✓
- Consistency: marker name `showdown`, env `SHOWDOWN=1`, sandbox path `/tmp/ipo_showdown_sandbox/` used
  uniformly. ✓
