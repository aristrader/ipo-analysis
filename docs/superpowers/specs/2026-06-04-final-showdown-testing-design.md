# Final-Showdown Testing & Verification — Design Spec

**Date:** 2026-06-04 · **Approved by user:** yes (auto-mode authorized through execution + cleanup + report)

## Goal
Prove, concretely, that everything in the IPO-analysis project is correct and runs — data, logic,
pipelines, entry points, app — and leave behind a regression net dense enough that any future
breaking change trips a failing test. Then: cleanup + a final did/found/fixed report.

## Constraints (standing, non-negotiable)
- The real `data/master/` stays **byte-identical** throughout (asserted vs `archive/pre_drhp_20260601/`
  every turn by the verify hook). Execution proofs happen in a **/tmp sandbox copy** only.
- Git is **LOCAL-ONLY** — never add a remote. Commit per phase (rollback net).
- Network-dependent pipeline steps (00, 06, lt/02) cannot be identity-checked offline (live web moved
  since the freeze): compile/import checks + documented exclusion, not re-runs.
- Default `pytest tests` stays fast (~90s). Slow execution proofs are marked `@pytest.mark.showdown`
  and run via `pytest -m showdown`.
- Token discipline: ≤3 audit subagents; mutation testing as one scripted batch; tail-only output reads.

## Phases

### Phase 0 — Coverage audit (subagents, parallel)
Two read-only subagents produce a gap matrix → `docs/research/showdown_audit.md`:
- **Agent A (logic side):** every function in `layer3/` (spine, predictor/*, backtest/*, validate,
  report, charts, findings commons) + `pipeline/lib.py`/`listing_remediation.py`/07 helpers — which of
  the 139 tests cover it; classify each gap: result-critical / supporting / display-only.
- **Agent B (data+pipeline side):** every column of `ipo_analysis.csv` (via `docs/schema.md`) — which
  invariant could catch silent corruption; every pipeline step + scraper parser — covered / not /
  not-coverable(network); entry points and their smoke-status.
Output format (both): a table `target | what could break | covered-by | gap | priority`.

### Phase 1 — Data-integrity suite (fast, always-on) — `tests/data/test_substrate_integrity.py`
Invariants on the frozen CSVs (read-only). At minimum:
1. ipo_analysis: exactly 2296 csv records; `isin` unique, matches `^INE|^INF` ISIN shape (12 chars).
2. Cohort partition: boom=1269, longterm=1027; `type` ∈ {MB, SME}.
3. Movement invariant per row (where all three present): `mae_h ≤ return_from_issue_h ≤ mfe_h`
   (h ∈ 1y/3y/5y), same for `*_lst_*` vs return_from_listing.
4. `outcome_class` consistent with `current_return_from_issue` thresholds (−0.90/−0.20/0.20/1.00).
5. `listing_metrics_status` ∈ {ok, inferred_split, recovered_bhavcopy, unreliable_coverage};
   unreliable_coverage ⇒ listing_open/close + listing_gain_* are null.
6. Delisted with compulsory/liquidation reason ⇒ current_return_from_issue == −1.0 (±1e-9).
7. Join integrity: every ipo_analysis isin exists in universe.csv and (where priced) returns_summary;
   row counts consistent; no duplicate isin in any master file.
8. Bounds: returns > −1.001; listing dates within 2006-01-01..AS_OF_DATE; issue_price > 0 where present.
9. alpha sanity on a 50-row sample: alpha_1y ≈ return_from_listing_1y − nifty_return_1y (±2bp),
   recomputed from `data/reference/indices/nifty50.csv`.
Tolerances explicit;每 failure message names the offending isins (first 5).

### Phase 2 — Logic-gap tests (fast, always-on)
Driven by the Phase-0 matrix; at minimum the two known gaps:
- `tests/pipeline/test_merge_math.py`: synthetic weekly series through
  `scrapers/screener_prices_merge.py`'s MFE/MAE + clamp + timing logic (same treatment 07 got).
- `tests/scrapers/test_bhavcopy_parse.py`: `bhavcopy.parse_bhavcopy` + `bhavcopy_ohlc.parse_day`/`_num`
  against small inline fixture payloads (they feed ALL prices).
Plus every result-critical gap the audit marks priority-1 (audit decides the exact list; display-only
gaps are explicitly skipped and recorded as such in the audit doc).

### Phase 3 — Execution proofs (`@pytest.mark.showdown`, opt-in)
- `tests/showdown/test_pipeline_sandbox.py`: rsync repo+data (exclude .venv, archive, .git) →
  `/tmp/ipo_showdown_sandbox/`; run there in order: 03b, 03c, 03d, 03e, 04, 05, 07, merge, 08, 09
  (each must exit 0); then categorized diff of sandbox `data/master/*.csv` vs the real ones:
  every differing cell must fall in an EXPLAINED category (the known post-pipeline hand-remediations,
  enumerated in the test) — unexplained diffs fail. Produces `docs/research/showdown_pipeline_diff.md`.
- `tests/showdown/test_entrypoints.py`: `run_layer3_report.py` (report exists, 29 findings),
  `predict_ipo.py` (one MB + one SME query, exit 0, sane output), `run_backtest.py`, `run_validation.py`,
  `run_weights.py` — all exit 0 (read-only; run with cwd=repo, PYTHONPATH=.).
- `tests/showdown/test_app_smoke.py`: launch streamlit headless, Playwright opens all 5 tabs, asserts
  no traceback/exception text; teardown kills the server.
- 00 / 06 / lt-02: `py_compile` + "imports resolve" checks only, + exclusion note in the audit doc.

### Phase 4 — Mutation validation of existing tests (one scripted batch)
`tools/mutation/run_mutations.py` (kept in repo): a mutation table of ~30–60 deliberate breaks across
spine.py, predictor/scorecard.py, predictor/weights.py, 07 helpers, listing_remediation.py, merge math,
pipeline/lib.py — each entry = (file, exact old text, mutated text, scope of tests to run). Loop:
apply via exact string replace → run the routed test scope → record pass/fail → `git checkout` restore →
clear __pycache__ (the stale-pyc lesson). Output: kill-rate report → `docs/research/showdown_mutation.md`.
Every SURVIVED mutation = vacuous coverage → write the missing test in the same phase, re-run, must kill.
Repo must be committed-clean before the batch starts; the runner refuses to start otherwise.

### Phase 5 — Change-aware test routing (mechanical, not memory)
- `project_map.py` gains `TEST_ROUTING`: ordered (glob-pattern → pytest target(s)) pairs, e.g.
  `pipeline/07*` → `tests/pipeline -m ''` + note "showdown pipeline-sandbox before release";
  `layer3/predictor/*` → predictor/weights/oos tests; `app.py` → showdown app smoke;
  `data/master/*` → `tests/data`; `scrapers/X.py` → its parse tests; fallback `*` → full fast suite.
- `verify.py --quiet` (already hook-run before EVERY turn) additionally: `git status --porcelain` →
  map changed files through TEST_ROUTING → print `CHANGED: <file> → RUN: <pytest cmd>` lines.
  This guarantees the AI sees the routing every turn (hook-injected context, not memory).
- `verify.py --route` = the same report on demand for the human.
- `docs/WORKFLOWS.md`: routing rule + "`pytest -m showdown` = the pre-release/major-change gate".
- `tests/test_project_map.py`: new test — every TEST_ROUTING target resolves to an existing path/marker.

### Phase 6 — Cleanup + final report
- STATUS: showdown summary line only (details → DONE.md per the move-rule). DONE.md: full entry.
- project_map.py: new files registered; INVARIANTS test-count updated; MAP.md regenerated; verify PASS.
- pytest.ini (or pyproject [tool.pytest]) registers the `showdown` marker (no unknown-marker warnings).
- One commit per phase, descriptive messages.
- Final user report: what was done / what issues were found / what was fixed (plain language).

## Success criteria
1. Fast suite green and still <~2 min; `pytest -m showdown` green end-to-end.
2. Sandbox pipeline diff: zero unexplained cells.
3. Mutation kill-rate 100% after fixes (every deliberate break trips a test).
4. verify.py PASS; real data/master byte-identical to backup; git clean, LOCAL-ONLY.
5. The audit doc + diff doc + mutation doc exist as evidence; final report delivered.

## Out of scope
Re-running network scrapers; changing any analytical logic/results; the microcap extension; CI (no
remote exists — the verify hook + routing is the local equivalent).
