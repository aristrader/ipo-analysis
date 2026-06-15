# Repo structure audit + target layout + migration plan

**Compiled:** 2026-06-02 · **Scope:** READ-ONLY structural audit of the whole repo (root tracking files,
`docs/` + `docs/research/`, `data/master/`, `layer3/`, `pipeline/`, `scrapers/`, `tests/`, entry-point
scripts, `archive/`, `logs/`). Nothing was changed in producing this doc.

**Purpose:** the structural decisions were made very early. This is ONE deliberate, aligned restructure —
not another reactive patch. Goal: one purpose per file/dir, no overlapping "where are we" docs, no stale
map in `CLAUDE.md`, and an explicit list of the early decisions that are still correct and must NOT change.

**Distinct from `CLEANUP_FINDINGS.md`:** that doc is a *code-level* audit (duplicated functions, god-functions,
missing deps, no git). THIS doc is a *structural/layout* audit (which files exist, what they're for, what
overlaps, what's stale, what to move/merge/archive). The two are complementary; where they touch (git,
.gitignore, archive hygiene) this doc defers to `CLEANUP_FINDINGS.md` for the how.

---

## A. Current-state map — coherent vs sprawled/stale/dead

### A1. Root-level tracking files — SPRAWLED (the user's main pain)
Seven markdown files at root, of which 4-5 try to answer "where are we / what's left":

| File | Size | Purpose (as written) | Verdict |
|---|---|---|---|
| `CLAUDE.md` | 10 KB | Stable project brain (3 layers, conventions, repo map, run order) | KEEP — but repo map is stale (see C) |
| `README.md` | 3 KB | Human entry point (start-here + run commands) | KEEP — folder map slightly stale (mentions 20 then 62 findings) |
| `TODO.md` | 10 KB | "Living checklist" + active autonomous-run state + queue + discussion backlog | MERGE — overlaps EXECUTION_STATUS + NEEDS_YOUR_INPUT |
| `EXECUTION_STATUS.md` | 5 KB | "Live execution truth" (done / in-progress / waiting-on-user / deferred) | MERGE — created 2026-06-01 as a patch over TODO; now a 3rd "where are we" |
| `NEEDS_YOUR_INPUT.md` | 4 KB | Open decisions awaiting the user (each with a recommendation) | MERGE — its "open decisions" duplicate TODO's "awaiting your input" + EXECUTION_STATUS's "waiting on user" |
| `DONE.md` | 19 KB | Append-only completed-work history, most-recent-first | KEEP — this is the one history file, working as intended |
| `CLEANUP_FINDINGS.md` | 19 KB | Code-level cleanup findings (2026-06-02 handoff) | RELOCATE — it's a research/handoff artifact, not a root tracker |

**The core problem, confirmed:** "where are we / what's left / what do you need from me" is answered in THREE
places that have already drifted out of sync:
- finding count: `TODO.md` says **29**, `NEEDS_YOUR_INPUT.md` says **28**, `DONE.md` older entries say 20/26/28,
  `CLAUDE.md` says **20** (in the report), `README.md` says **20** then **62** then 73/77. Ground truth
  (`ls layer3/findings/*.py | grep -v __init__ | wc -l`) = **29**; tests = **77** (per `CLEANUP_FINDINGS.md`,
  verified by collect-only). `README.md` says 62.
- the single open decision ("fold wipeout-safety into data_informed?") is written out in full in `TODO.md`,
  `EXECUTION_STATUS.md`, AND `NEEDS_YOUR_INPUT.md` — three copies of the same pending question.
- This is exactly the "risk of confusion/hallucination about what's where" the user named.

### A2. `docs/` (top level) — COHERENT
Durable reference, one concern each: `sources.md`, `schema.md`, `pipeline.md`, `strategies.md`, `layer2.md`,
`layer3.md`, `design.md`, `decisions.md`, `patterns.md`, `data_review.md`, `changelog.md`. These match the
"where to start" pointers and are stable. `docs/superpowers/` (plans + specs from the build) is a build
artifact — harmless, but it's process history, not project reference (candidate to archive, low priority).

### A3. `docs/research/` — SPRAWLED (~45 files, mixed durability)
This is the second-worst offender. It mixes four very different kinds of file with no separation:

- **Durable reference / decision-relevant (KEEP active):** `ideas_findings.md`, `ideas_predictor.md`,
  `ideas_backtest.md`, `ideas_validation.md`, `ideas_movement_lens.md`, `extension_roadmap.md`,
  `microcap_extension_thinking.md`, `benchmark_sources.md`, `financials_extra_sources.md`,
  `longterm_financials_sources.md`, `drhp_feasibility.md`, `headlines_entry_exit.md`,
  `headlines_selection_survival.md`, `interactions_risk.md`, `interactions_upside.md`,
  `wipeout_anatomy_v2.md`. (These inform future work or document live design rationale.)
- **One-off review / verification logs (superseded — ARCHIVE):** `adversarial_verification.md`,
  `verification.md`, `cleanup_report.md`, `layer3_methodology_review.md`, `layer3_partA_code_review.md`,
  `layer3_partA_stats_review.md`, `layer3_partBC_review.md`, `layer3_enhancements_ideas.md`,
  `review_new_findings.md`, `review_new_pbcv.md`, `price_recovery.md`, `enrichment_recovery.md`,
  `boom_sector_recovery.md`, `sme38_recovery.md`, `unreliable75_recovery.md`, `drhp_recovery.md`,
  `drhp_crossvalidation.md`, `wipeout_anatomy.md` (superseded by `_v2`).
- **Session logs (ARCHIVE — pure history):** `autonomous_session_log.md`.
- **CSVs intermixed with prose docs (RELOCATE — data, not docs):** `_drhp_targets.csv`, `drhp_recovered.csv`,
  `drhp_review_queue.csv`, `enrichment_recovery_log.csv`, `longterm_inwindow_log.csv`, `recovered_listing_day.csv`,
  `sme38_listing.csv`, `unreliable75_corp_actions.csv`, `unreliable75_listing.csv`, `verification_corrections.csv`.
  Recovery-staging/working CSVs do not belong in `docs/`; they are scratch data outputs.

### A4. `data/master/` + `data/master/review/` — COHERENT
Clear and well-organized. Top level = THE products (`ipo_analysis.csv`, `universe.csv`, `returns_summary.csv`,
the 4 cohort CSVs, `_base_*` staging, `delisting.csv` as a documented pipeline INPUT, the two scorecard JSONs,
`exclusions.csv`, a `README.md`). `review/` cleanly isolates the 9 flag/review CSVs. No change needed.
Minor: `_base_*.csv` (staging) and `delisting.csv` (input) sit alongside outputs — acceptable and documented,
but a `data/master/staging/` could tidy it later (LOW priority, not worth the churn).

### A5. `layer3/` — COHERENT (one drift to watch)
`spine.py` (28 KB), `findings/` (29 modules), `predictor/` (analogs, predict, scorecard, weights),
`backtest/` (engine, analyses, score_backtest), plus `config.py`, `charts.py`, `report.py`, `validate.py`.
Clean engine separation, UI-agnostic — exactly as designed. **Drift:** `spine.py` at ~28 KB is the largest
non-test module and is becoming a grab-bag (method spine + reach/exit/stop/lifecycle/dispersion). Not urgent,
but it's the file most likely to become a god-module; flagged for eventual split (LOW). `findings/` naming is
slightly archaeological (`t1`-`t9` Tier-1, `n2`-`n15` enhancements, `f_*` movement, `m1_*`) — readable but the
prefixes encode build history rather than category; acceptable, not worth renaming.

### A6. `pipeline/` — COHERENT
Numbered `00`-`09` + `03b`-`03f` + `checks/` + `longterm/` + `listing_remediation.py`. Matches the documented
run order. **Two items:** (1) `pipeline/research/` (`enrich_recovery.py`, `recover_inwindow_financials.py`) —
one-off recovery scripts living inside the pipeline dir; these are not part of the canonical chain and blur
"pipeline = the build chain." Candidate to move under a clearly non-canonical location. (2) `03f_sector_mcap.py`
exists but `CLAUDE.md`'s pipeline list stops at `03e` (stale — see C).

### A7. `scrapers/` — COHERENT
One file per source, fetch-only, as designed. 16 scrapers; `CLAUDE.md`'s list is accurate. No change.

### A8. `tests/` — COHERENT
All under `tests/layer3/` (12 test modules, 77 tests). Layers 1-2 (pipeline) have `pipeline/checks/` as their
validation harness instead of `tests/` — a reasonable split (checks = data-validation gates; tests = logic).
Worth a one-line note in `CLAUDE.md` so it isn't read as "pipeline untested."

### A9. Entry-point `run_*.py` scripts at root — MILDLY SPRAWLED
Eight CLI entry points at root: `run_all.py`, `run_layer3_report.py`, `run_backtest.py`, `run_validation.py`,
`run_weights.py`, `run_oos.py`, `run_refresh.py`, plus `predict_ipo.py` and `app.py`. They are coherent
individually and discoverable (the `run_` prefix groups them in a dir listing). `run_oos.py` and `run_refresh.py`
are NOT mentioned in `CLAUDE.md` (stale map). Grouping them into a `bin/` or `cli/` dir is possible but would
break every documented `PYTHONPATH=. python run_*.py` invocation and the muscle memory — **NOT recommended**;
the prefix already groups them. The real fix is documentation (list all of them in `CLAUDE.md`), not relocation.

### A10. `archive/` — COHERENT (growing, hygiene only)
Dated, purposeful subdirs (`pre_drhp_20260601/`, `pre_integration_20260531/`, `research_scratch/`, `derived/`,
`data_derived/`, `scripts/`, `analysis/`, `E2_changelog.md`). This is the manual rollback substitute for the
absent git (per `CLEANUP_FINDINGS.md` INFRA-1). Working as intended; just growing (17 MB). No structural change —
the right fix is `git init` (deferred decision), tracked in `CLEANUP_FINDINGS.md`.

### A11. `logs/` (47 files, 3.4 MB) + empty `analysis/.gitkeep` — DEAD/CLUTTER
`logs/` is run-output, never reference; `analysis/` is an empty placeholder (real analysis lives in `layer3/`).
Both are clutter. Right fix = gitignore + `make clean` (deferred to `CLEANUP_FINDINGS.md` INFRA-2/4); structurally,
`analysis/` (empty) can be deleted.

---

## B. Recommended target structure (one purpose per file/dir)

### B1. Root tracking files → consolidate the 3 "status" files into ONE
This matches and refines the user's agreed consolidation. Final root set:

```
CLAUDE.md      — stable project brain (conventions, layers, repo map, run order). Changes rarely.
README.md      — human start-here + run commands. Changes rarely.
STATUS.md      — THE single live tracker (NEW). Replaces TODO + EXECUTION_STATUS + NEEDS_YOUR_INPUT.
DONE.md        — append-only completed history, most-recent-first. (unchanged)
```
`STATUS.md` has exactly three sections, one purpose each:
- **## In progress / next** — what is actively being worked or is the immediate next step (from TODO's queue +
  EXECUTION_STATUS's "in progress").
- **## Your decisions** — open questions awaiting the user, each with a one-line recommendation (from
  NEEDS_YOUR_INPUT + the "waiting on user" sections). This is where the single live decision lives — ONCE.
- **## Backlog (optional / deferred)** — non-blocking future work (from TODO's "genuinely open" + DONE's deferred).

Rule (write it at the top of `STATUS.md`): *finding/test counts and "where are we" live ONLY here and in
`rules/index.md` (domain). Never restate counts in CLAUDE.md/README — point to STATUS.md instead.* This kills
the count-drift problem at the source.

`CLEANUP_FINDINGS.md` → move to `docs/research/cleanup_findings.md` (it's a handoff artifact, not a root tracker).

### B2. `docs/research/` → split active vs archive, and evict CSVs
```
docs/research/                 — ACTIVE: durable ideas/sources/design-rationale docs only (the A3 "KEEP" list)
docs/research/archive/         — superseded review logs, verification logs, recovery logs, session logs (A3 lists)
data/research/                 — NEW: the working/staging CSVs currently mis-filed under docs/research (A3 CSV list)
```
(`data/research/` keeps recovery-staging CSVs near the data they stage into, and out of `docs/`. Alternatively
fold them into `archive/research_scratch/` if they're truly inert — but several are still referenced by
`EXECUTION_STATUS.md`/`drhp_*` work, so keep them live under `data/research/` until DRHP is decided.)

### B3. `pipeline/research/` → relocate the non-canonical recovery scripts
Move `pipeline/research/` → `pipeline/recovery/` is NOT enough (still reads as pipeline). Prefer `tools/recovery/`
at root (or `scripts/recovery/`) so `pipeline/` contains ONLY the canonical numbered chain + `checks/` +
`longterm/` + `listing_remediation.py`. (LOW priority — these are dormant.)

### B4. Everything else STAYS as-is
`data/master/` (+`review/`), `layer3/`, `scrapers/`, `tests/`, the root `run_*.py` + `predict_ipo.py` + `app.py`,
`rules/`, `report/`, `archive/`. These are coherent. Resist relocating the entry scripts (breaks all docs/muscle
memory for zero clarity gain).

### B5. Delete the empty placeholder
`analysis/` (only `.gitkeep`, superseded by `layer3/`).

---

## C. `CLAUDE.md` repo-map / "where to start" — what's stale (fix during the restructure)

1. **Pipeline list stops at `03e`** — reality has `03f_sector_mcap.py`. Add it.
2. **"where to start" §1-7 points to `docs/design.md`? No** — it points to sources/schema/pipeline/strategies/
   layer2/layer3/data_review; `docs/design.md` and `docs/patterns.md` exist but aren't in the pointer list.
   Add or explicitly mark them secondary.
3. **Tests count "(62)"** in CLAUDE.md and README; ground truth is **77**. After B1, replace the number with
   a pointer to `STATUS.md` (don't restate the count).
4. **"20 findings"** in CLAUDE.md Part A; ground truth 29 findings (the report renders 20 *headline* + others).
   Clarify "20 in the headline report, 29 modules total" or point to `rules/index.md`.
5. **Tracking-file pointers** — CLAUDE.md's "to resume" line says read `TODO.md` → `rules/index.md`. After B1,
   change to `STATUS.md` → `rules/index.md`. Remove references to `NEEDS_YOUR_INPUT.md`/`EXECUTION_STATUS.md`.
6. **Repo map omits** `run_oos.py`, `run_refresh.py`, `predict_ipo.py`, `app.py` from the "Running" section and
   the `tests/` vs `pipeline/checks/` split. Add a one-line entry-point inventory.
7. README "Folder map" says findings = 20 then 62 — reconcile to a pointer, not a number.

---

## D. Early structural decisions that are STILL VALID — DO NOT TOUCH

These were set early and remain correct; the restructure must preserve them verbatim:
1. **ISIN is the primary key; the only automatic join key. Name-matching only flags, never merges.** (Corp
   actions match by SYMBOL — the documented exception.) Still right.
2. **The numbered `pipeline/` chain (`00`-`09` + `03b`-`03f`), run in order, with `pipeline/checks/` gates.**
   Coherent and matches reality. Keep.
3. **Layer-3 engine separation (`layer3/` UI-agnostic; `app.py` is the only UI).** Clean. Keep.
4. **Survivorship-honesty (delisted included; compulsory/liquidation = −100%; terminal = last price).** Keep.
5. **Returns = ALPHA vs Nifty 50 (+ Smallcap 250 where available); raw return secondary.** Keep.
6. **Prices split/bonus-adjusted; issue price adjusted by the same factor.** Keep.
7. **No ML — analog/comparables predictor + a 5-component scorecard with cross-regime validation.** Keep.
8. **`data/master/` as THE products + `data/master/review/` for flags; `rules/` as the navigable registry.** Keep.
9. **`scrapers/` = one file per source, fetch-raw-only.** Keep.

None of these need to change. The restructure is entirely about the *tracking/docs sprawl* layer sitting on top
of a sound foundation.

---

## E. Concrete migration plan (move / merge / archive / delete)

Ordered. Destructive steps are flagged **[CONFIRM]** (they delete or merge-then-remove content). Per
`CLEANUP_FINDINGS.md` INFRA-1 there is no git safety net yet — ideally `git init` first.

**Merges (content-preserving; review before removing sources):**
1. Create `STATUS.md` (root) with sections In-progress / Your-decisions / Backlog. Populate by pulling the
   live content from `TODO.md` + `EXECUTION_STATUS.md` + `NEEDS_YOUR_INPUT.md` (dedupe the 3 copies of the
   wipeout-safety decision into one).
2. **[CONFIRM]** Delete `TODO.md`, `EXECUTION_STATUS.md`, `NEEDS_YOUR_INPUT.md` after confirming `STATUS.md`
   captured everything. (Destructive: removes 3 files. Their unique content must be verified into STATUS.md first.)

**Moves (non-destructive):**
3. `CLEANUP_FINDINGS.md` → `docs/research/cleanup_findings.md`.
4. Create `docs/research/archive/`; move the A3 "superseded" list (review/verification/recovery/session logs) into it.
5. Create `data/research/`; move the A3 CSV list out of `docs/research/` into it. (Update any references in
   `EXECUTION_STATUS`/`drhp_*` docs — grep first.)
6. Move `pipeline/research/` → `tools/recovery/` (or `scripts/recovery/`). (LOW priority.)

**Deletes:**
7. **[CONFIRM]** Delete empty `analysis/` dir (only `.gitkeep`; superseded by `layer3/`). (Destructive but trivial.)

**Doc fixes (non-destructive, do alongside):**
8. Update `CLAUDE.md` per section C (pipeline `03f`, counts→pointers, tracking-file pointers→`STATUS.md`,
   entry-point inventory, tests-vs-checks note).
9. Update `README.md` folder map: findings count → pointer to `rules/index.md`; add `STATUS.md`; list all
   entry points.

**Deferred to `CLEANUP_FINDINGS.md` (not this doc):** `git init`, `.gitignore`, `pyproject.toml`,
`logs/` + `__pycache__` hygiene, `requirements.txt` pinning. Those are infra/code, not layout.

---

## F. Top 5 cleanup actions, ranked (+ which are destructive)

1. **Consolidate the 3 status files → one `STATUS.md`** (TODO + EXECUTION_STATUS + NEEDS_YOUR_INPUT). This is the
   user's #1 pain and the source of the count/decision drift. **[DESTRUCTIVE — needs confirm]** to delete the 3
   originals after verifying STATUS.md is complete. Highest leverage.
2. **Fix the stale `CLAUDE.md` repo map** (pipeline `03f`, finding/test counts → pointers, tracking-file pointers
   → STATUS.md, missing entry points). Non-destructive. Directly attacks "hallucination about what's where."
3. **Split `docs/research/` into active + `archive/`, and move the staging CSVs to `data/research/`.** ~28 of 45
   files relocate. Non-destructive (moves only). Makes "durable reference vs one-off scratch" obvious at a glance.
4. **Relocate `CLEANUP_FINDINGS.md` → `docs/research/` and `pipeline/research/` → `tools/recovery/`.** Non-destructive.
   Leaves root holding only the 4 intended files and `pipeline/` holding only the canonical chain.
5. **Delete the empty `analysis/` placeholder** and (deferred to CLEANUP_FINDINGS) gitignore `logs/`/`__pycache__`.
   **[MILDLY DESTRUCTIVE — needs confirm]** for the `analysis/` delete (trivial; empty dir).

**Destructive / needs human confirm:** #1 (delete 3 merged files) and #5 (delete empty `analysis/`). Everything
else is moves and doc edits with no data loss. Recommend doing `git init` (per `CLEANUP_FINDINGS.md`) before #1.
