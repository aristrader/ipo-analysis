# WORKFLOWS — "what to do when" (keep the map + state honest)

Procedural rules so changes don't leave the map, tests, or state files stale. The
checkpoint (`verify.py`, run automatically each turn via the `UserPromptSubmit` hook)
catches most drift — these rules tell you what to update so it stays green.

## The three standing principles (from the agent-map pattern)
1. **Verify before relying.** Paths, counts, commands — check against ground truth
   (`verify.py`, `ls`, command output), never memory. `wc -l` lies on the CSVs
   (quoted multiline fields) — count records with the `csv` module.
2. **Update the map the moment it's wrong.** If you add/move/retire a file, step,
   data product, or signal, edit `project_map.py` in the same change.
3. **Suggest improvements** when the structure itself is the friction.

## When you… → do this
- **Add/move/retire any file, pipeline step, or data product**
  → edit `project_map.py` (PIPELINE / DATA_PRODUCTS / LAYER3 / CONTEXTS as relevant).
  `run_all.py` derives its DAG from `project_map.PIPELINE`, so adding a step there wires it.
  Run `python verify.py` (regenerates `MAP.md`, confirms PASS).

- **Add or edit a finding** (`layer3/findings/*.py`)
  → register it in `rules/index.md`; add/extend a test in `tests/layer3/test_findings.py`;
  bump the findings count in `project_map.INVARIANTS`, `STATUS.md`, `CLAUDE.md` if it changed.

- **Add/change a score signal or weight** (`layer3/predictor/scorecard.py` / `weights.py`)
  → it enters the weighted score ONLY if it passes the "evolve-only-if-robust" OOS gate
  (see `rules/index.md`); otherwise display-only. Record the verdict (in-score/display-only/
  rejected) + WHY in `rules/index.md`. Add a test.

- **Add a scraper or pipeline parser**
  → add a node to `project_map.py`; add a parse test under `tests/scrapers/` or
  `tests/pipeline/` (load numbered files via importlib in the suite conftest).

- **Change `layer3/config.py` AS_OF_DATE or a threshold**
  → it's the single source; update `project_map.INVARIANTS["as_of_date"]` to match.

- **Touch the dataset substrate** (`data/master/`)
  → it is FROZEN/post-remediation. Re-running the full pipeline will NOT reproduce it
  byte-for-byte (manual remediation + DRHP staging happened after). Prefer behavior-
  preserving edits verified by the test net; if you must regenerate, snapshot to
  `archive/` first and diff. `verify.py` reports whether it still matches the backup.

- **Finish a chunk of work**
  → `python verify.py` (PASS + MAP.md fresh) → `pytest tests -q` (all green) →
  record what happened in the git commit message, then **REMOVE the item from `STATUS.md`** (STATUS holds ONLY
  live state + what's next — completed work leaves STATUS (history = git log), never accumulate) →
  commit (LOCAL-ONLY, no remote).

## Change → tests routing (mechanical, every turn)
- `project_map.TEST_ROUTING` maps changed files → the pytest commands to run. The per-turn hook
  (`verify.py --quiet`) reads `git status`, routes the changes, and INJECTS "CHANGED → RUN" lines
  into the assistant's context — so the right tests are surfaced every time, by machinery not memory.
- On demand: `python verify.py --route`.
- **`SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q` = the pre-release / major-change gate**
  (sandbox pipeline re-run + diff, entry-point smokes, app browser test; ~3 min).
- Test-suite health: `tools/mutation/run_mutations.py` re-validates that deliberate code breaks
  fail tests (run after any large test refactor; report → docs/research/showdown_mutation.md).

## Refreshing the data (bring the dataset to today)
- `PYTHONPATH=. python run_refresh.py` = DRY-RUN (what would change); `--apply` = do it.
- The refresh snapshots first (`archive/pre_refresh_<date>/`), ingests new IPOs, extends prices,
  re-runs the pipeline, re-derives goldens (OLD → NEW printed), and MUST end with the fast suite
  green. Movable facts (as_of / rows / backup pointer) live in `data/master/substrate_meta.json` —
  the refresh updates them as data; nothing edits source files.
- **ROLLBACK:** `cp archive/pre_refresh_<date>/* data/master/` (the snapshot includes
  substrate_meta.json) — then `python verify.py` to confirm.
- After a refresh: `python run_forward_test.py` re-reads the never-seen cohort (EARLY READ labels).
- Test-design rule learned 2026-06-06: data tests must assert MOVABLE facts via substrate_meta /
  goldens (consistency), never literals — a literal row-count fails every legitimate refresh.

## The checkpoint contract
- `python verify.py` — full report (counts, exact pytest-collected count, backup match), regenerates `MAP.md`.
- `python verify.py --quiet` — fast (~0.1s), prints ONLY on drift; this is what the hook runs each turn.
- It NEVER blocks; it only injects drift warnings into context. Mute by removing the hook
  block from `.claude/settings.local.json`.
