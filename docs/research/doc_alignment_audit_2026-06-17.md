# Doc-Alignment Audit — 2026-06-17 (discovery-only catalog)

**Role:** READ-ONLY discovery pass. NOTHING was changed except writing this one file. Triggered by the owner
concern: *"too many docs, too many places, things scattered — it should all be aligned properly."* This is the
COMPLETE catalog a later fix pass (queued in `improvement_backlog.md` §DOC-ALIGNMENT, after D-1 ships) will consume.

**Method:** inventoried `docs/` + `docs/research/**` + `thinktank/` + the root pointer files; cross-referenced the
two prior reviews (`structure_review_2026-06-16.md` SR-1…14, `doc_drift_review_2026-06-16.md` DD-1…8) and verified
their current status against disk — most are now FIXED by PRs #2/#3. Every concrete claim below was re-checked with
`ls`/`grep`/`verify.py` against the working tree. `git log` history, dated `task_log.md` entries, and `archive/`
contents were NOT flagged (correct-by-design). `verify.py` currently PASSES.

This catalog is itself a TEMP doc — archive it once the fix pass lands.

---

## Summary

- **Total NEW/STILL-OPEN issues: 14** (grouped: 5 stale/drift, 3 hand-nav, 2 duplication, 2 orphan, 2 misplacement).
- **Most of the prior reviews are already FIXED** (verified): rules registry now lives at root `rules/index.md`
  (SR-6/7/11, DD-5 resolved); `nodes.py` task_log read repointed to `docs/tracker/` (DD-4 fixed); the three
  GENERATED files (`unresolved_88_mismatches_audit.md`, `enrichment_recovery_log.csv`, `longterm_inwindow_log.csv`)
  now exist live and are gone from `archive/` (DD-1/2/3 fixed); `FILE_KINDS` + kind-enforcement added to
  `project_map.py`/`verify.py` (DD-7 prevention shipped); improvement_backlog/STATUS path drift swept (SR-8/9).
- **Top 3 consolidations still needed:**
  1. **`docs/research/INDEX.md` is badly drifted** (DA-1) — lists 6 archived files as ACTIVE, misses ~37 subdir
     docs + all 7 audit/D-1 docs, header self-admits "no live generator." It half-violates the rule it states.
     The on-brand fix = GENERATE it (matches MAP.md). This is the single biggest hand-nav problem.
  2. **CLAUDE.md references 5 run-scripts as bare root paths** (DA-2) but they all live in `scripts/` — a new
     agent following CLAUDE.md literally runs `python predict_ipo.py` and 404s. Same class as the (now-fixed)
     task_log drift, just for the entrypoint scripts.
  3. **CLAUDE.md internal contradiction: "8-component scorecard" (line 26) vs the 5-component list (line 116)**
     (DA-3) — pick one truth for the component count.

- **TEMP working docs safe to archive ONCE their thread closes** (per backlog §DOC-ALIGNMENT lines 61-62, but
  note the 4th D-1 doc is omitted there):
  - `alignment_audit_2026-06-16.md` — retire only after its **14 UNVERIFIED items** are worked through (still OPEN).
  - `structure_review_2026-06-16.md`, `doc_drift_review_2026-06-16.md` — superseded by THIS catalog; archive now-ish.
  - D-1 review set (thread closes when D-1 ships): `d1_join_strategy_2026-06-17.md`, `d1_plan_review_2026-06-17.md`,
    `d1_plan_rereview_2026-06-17.md`, **`d1_plan_final_verify_2026-06-17.md`** (← backlog line 62 lists the trilogy
    but MISSES this 4th file — add it to the archive list).
  - THIS file (`doc_alignment_audit_2026-06-17.md`) — archive after the fix pass consumes it.
  - CANONICAL (keep, do NOT archive): everything under `docs/tracker/`, `rules/index.md`, `CLAUDE.md`,
    `project_map.py`, the standing briefs in `docs/research/` (execution_pipeline, hypothesis_protocol,
    app_phase2_design, trusted_sources, phase2_playbooks, app_iteration_charter).

---

## (A) Stale / drift

### DA-1 — HIGH — `docs/research/INDEX.md` is heavily drifted (hand-nav that should be generated)
- Header (line 3) self-admits: *"SNAPSHOT (no live generator), last rebuilt ~2026-06-10 — may not list the newest docs."*
- **Lists 6 ARCHIVED files as ACTIVE "concluded write-up" (INDEX.md:30,36,54,77,79,80):** `CLEANUP_FINDINGS.md`,
  `deep_hypotheses_2026-06.md`, `hypothesis_batch_2026-06-06.md`, `showdown_audit.md`, `showdown_pipeline_diff.md`,
  `structure_audit.md` — ALL six physically live in `docs/research/archive/` (verified), not the ACTIVE tree.
- **Misses ~37 subdir docs:** none of `signals/` (e.g. `a1b_coverage_guard_2026-06-10`, `a1c_banker_quality_2026-06-11`
  → grep count 0 in INDEX), and most of `newsfeed/`/`enhancement/`/`data/`/`app_iterations/`/`backlog/` are absent.
  Actual non-archive `docs/research/*.md` = 30 top-level + 37 in subdirs; INDEX claims "ACTIVE (63)".
- **Lists `batch_run_2026-06-09.md` (INDEX.md:26) as a live `docs/research/` LOG** — it's in `archive/` (verified).
- **Misses all 7 audit/planning docs entirely** (grep count 0): `alignment_audit`, `structure_review`, `doc_drift_review`,
  the 4 `d1_*` docs, and this file.
- **Canonical home:** research-doc index → `docs/research/INDEX.md`, but it **should be GENERATED** (CLAUDE.md
  §nav target). SR-10/SR-11 flagged this; still open.
- **Fix:** write a tiny generator (mirror the MAP.md-is-generated pattern) that walks the tree + reads each file's
  H1 + a status tag, OR demote INDEX.md to a thin pointer (`ls docs/research/**/*.md` + git log + rules/index.md).

### DA-2 — HIGH — CLAUDE.md references run-scripts as bare root paths; they live in `scripts/`
- CLAUDE.md cites `predict_ipo.py` (3×, lines 26/30…), `run_backtest.py` (2×, line 27…), `run_validation.py` (2×,
  lines 28/…), `run_weights.py` (1×, line 29), and the resume footer's `run_layer3_report.py` — all as bare names.
- On disk: ONLY `run_all.py` is at root. `predict_ipo.py`, `run_backtest.py`, `run_validation.py`, `run_weights.py`,
  `run_layer3_report.py`, `run_calls.py`, `run_refresh.py`, etc. ALL live in `scripts/` (verified `ls scripts/`).
- A new agent following CLAUDE.md literally runs `python predict_ipo.py` → file-not-found. (DD-8 spot-check flagged
  this as "borderline LOW"; re-rating HIGH because CLAUDE.md is the primary onboarding authority.)
- **Canonical home:** conventions/run-commands → CLAUDE.md (keep), but paths must be correct.
- **Fix:** prefix the bare script names with `scripts/` throughout CLAUDE.md (and any doc that copies them).

### DA-3 — MED — CLAUDE.md self-contradicts on scorecard component count
- CLAUDE.md:26 says "analog predictor + **8-component** scorecard". CLAUDE.md:116 says
  "Score = a SCORECARD of components (return-potential, multibagger-odds, downside-safety, liquidity, quality)" — **5**.
  (The 5-list also predates the `tradeable_upside` 6th + later additions referenced elsewhere.)
- **Canonical home:** capability/convention → CLAUDE.md (single doc, so this is internal drift, not cross-doc).
- **Fix:** reconcile to one number; if 8, update line 116's parenthetical list to match (or point it at the
  scorecard module as SSOT instead of re-listing components inline).

### DA-4 — MED — `docs/research/README.md` still says live state → "`STATUS.md` (root)"
- `docs/research/README.md:18`: *"live project state → `STATUS.md` (root)."* The file is at `docs/tracker/STATUS.md`
  (verified; there is no root STATUS.md). SR-9 flagged the same "(root)" claim; PR #2/#3 fixed CLAUDE.md's bare
  refs but this README line survived.
- **Canonical home:** live state → `docs/tracker/STATUS.md`.
- **Fix:** change "`STATUS.md` (root)" → "`docs/tracker/STATUS.md`".

### DA-5 — LOW — `docs/research/INDEX.md` line 27 lists `task_log.md` under the `docs/research/` LOG section
- INDEX.md:27 lists `docs/tracker/task_log.md` inside the "ACTIVE (63) … LOG" block of a `docs/research/` index —
  the path string is correct but its placement implies it's a research-dir file (it's a tracker file). Minor;
  folds into the DA-1 INDEX regeneration.
- **Fix:** absorbed by DA-1 (regenerated INDEX won't mis-section it).

---

## (B) Hand-maintained navigation that should be generated

### DA-6 — HIGH — INDEX.md (see DA-1) — the headline hand-nav offender; should be generated like MAP.md.
(Cross-ref DA-1; called out separately here so the fix-pass classifies it as a "generate it" task, not a "re-edit it" task.)

### DA-7 — LOW — `docs/research/README.md` partially restates the placement rules also in CLAUDE.md §DOC DISCIPLINE
- README.md:15-18 re-states "open WORK → improvement_backlog / verdicts → rules/index.md / history → git log /
  superseded → archive" — the same rule set as CLAUDE.md §DOC DISCIPLINE. Low risk (it's a local placement note,
  not a competing authority) but it's a second copy that can drift.
- **Canonical home:** doc-discipline rules → CLAUDE.md.
- **Fix:** trim README.md to point at CLAUDE.md §DOC DISCIPLINE rather than restate it.

---

## (C) Duplication

### DA-8 — MED — Two way-of-working architecture homes: `docs/setup.md` + thinktank architecture docs
- `docs/setup.md` ("AI Analysis Pipeline Setup Blueprint" — LangGraph workspace/directory design) overlaps
  `thinktank/orchestration/docs/{think_tank_architecture,app_think_tank_architecture}.md` and the orchestration
  code. It describes the same LangGraph "Think Tank" the thinktank/ tree implements. Two homes for "how the
  orchestration is structured." (Not flagged by SR/DD.)
- **Canonical home:** orchestration architecture → ONE of the thinktank docs (or `project_map.py` for structure).
- **Fix:** decide — fold `docs/setup.md` into the thinktank architecture doc (or archive it as build-era), or make
  it a thin pointer. Verify nothing references `docs/setup.md` before moving.

### DA-9 — LOW — `docs/PRODUCT.md` vs CLAUDE.md "What this is" (carry-over from SR-4, still open)
- `docs/PRODUCT.md` (honest current-scope spec) overlaps CLAUDE.md §"What this is" + §"3 layers". Two living homes
  for "what the product is/does." PRODUCT.md is referenced only by archived docs + one structure_review (verified)
  — i.e. lightly wired.
- **Canonical home:** user-facing capability spec → keep PRODUCT.md as the one; CLAUDE.md's overlap should be a pointer.
- **Fix:** ensure CLAUDE.md §3-layers stays a summary and points to PRODUCT.md; OR retire PRODUCT.md if it adds no
  delta over CLAUDE.md. (SR-4 decision still pending — surface to owner.)

---

## (D) Misplacement

### DA-10 — MED — Open architectural decisions live in an orphan handoff doc, not in improvement_backlog
- `docs/tracker/claude_transition_and_open_threads.md` Part 2 holds 3 genuinely-OPEN architectural decisions
  (meta-orchestration architecture / who orchestrates what / where API keys go; the human-in-the-loop rebuild;
  execution-pipeline rigor testing) — these are OPEN WORK whose canonical home is `improvement_backlog.md`.
- This is the file freshly `git add`-ed (git status `A`) yet referenced by NOTHING (see DA-12). SR-5 flagged it
  HIGH "harvest then delete"; it is STILL present and unharvested.
- **Canonical home:** open work → `docs/tracker/improvement_backlog.md`; the doc's Part 1 (token tips) duplicates
  CLAUDE.md §"Token Saving & Multi-Model Meta-Orchestration".
- **Fix:** harvest Part 2's 3 open decisions into improvement_backlog (DISCUSSION threads), then delete/archive the file.

### DA-11 — LOW — `docs/setup.md` directory-structure prose overlaps `project_map.py` (structure SSOT)
- `docs/setup.md` "Directory Structure" section narrates repo layout in prose; structure's canonical home is
  `project_map.py` → MAP.md. (Sub-issue of DA-8.)
- **Fix:** absorbed by DA-8 (fold/archive setup.md); structure description belongs only in project_map.py.

---

## (E) Orphans / temp / superseded

### DA-12 — HIGH — `docs/tracker/claude_transition_and_open_threads.md` is an orphan (referenced by nothing)
- `grep -rl` over `*.md`/`*.py` returns only the file itself (verified). Not in project_map, CLAUDE.md, verify,
  or INDEX. One-time "save state for the Claude switch" snapshot; Part 1 duplicates CLAUDE.md token tips, Part 2 =
  open decisions that belong in the backlog (DA-10). SR-5's "harvest + delete" recommendation is unactioned.
- **Fix:** DA-10 (harvest) then delete/archive. This is the clearest single orphan.

### DA-13 — MED — `d1_plan_final_verify_2026-06-17.md` is omitted from the backlog's temp-doc list (and from INDEX)
- The 4th D-1 review doc (`d1_plan_final_verify_2026-06-17.md`) exists (verified) but: (a) is NOT in INDEX (DA-1),
  and (b) backlog §DOC-ALIGNMENT line 62 lists the D-1 set as "d1_plan_review/rereview/final_verify, d1_join_strategy"
  — "final_verify" is named there, so it IS covered — BUT the suffix dates/exact filenames aren't, and a reader may
  miss it. The 4 D-1 review docs are all TEMP-working, archive-after-D-1-ships.
- **Canonical home:** these are concluded-evidence write-ups → leave/archive after thread closes; verdict → the D-1
  task_log entry + git log.
- **Fix:** when D-1 ships, archive all 4 `d1_*` docs together; ensure the backlog list + INDEX both reflect all four.

### DA-14 — LOW — `structure_review_2026-06-16.md` + `doc_drift_review_2026-06-16.md` are now superseded by THIS file
- Both are TEMP review docs whose findings have been re-verified here (most FIXED, the rest carried forward as
  DA-1…13). They can be archived now (their unique open items are folded into this catalog).
- **Fix:** archive both into `docs/research/archive/` as part of the fix pass; keep THIS file as the live catalog
  until the fix pass consumes it too.

---

## Proposed fix-order (for the post-D-1 consolidation pass)

1. **DA-12 + DA-10** — harvest `claude_transition_and_open_threads.md` Part 2 → improvement_backlog, then delete it.
   (Highest signal, lowest effort, removes the only true orphan + an open-work misplacement.)
2. **DA-2 + DA-3 + DA-4** — CLAUDE.md script-path prefix sweep, scorecard-count reconcile, README "(root)" fix.
   (Pure text edits to the authorities; correctness wins.)
3. **DA-1 / DA-6 + DA-5** — regenerate INDEX.md (write the generator; or demote to a pointer). Biggest structural win.
4. **DA-8 + DA-11 + DA-9 + DA-7** — duplication consolidation: decide setup.md vs thinktank-arch; PRODUCT.md vs
   CLAUDE.md; trim README's rule-restatement. (Needs an owner decision per pair.)
5. **DA-14 + DA-13** — archive the spent review docs (`structure_review`, `doc_drift_review`, and the 4 `d1_*` after
   D-1 ships); finally archive THIS catalog. Regenerate MAP.md via `verify.py` after all moves.

**Already-fixed (no action — confirmation only):** SR-6/7/11, DD-5 (rules at root), DD-4 (nodes.py task_log),
DD-1/2/3 (generated files live, archive copies gone), DD-7 (FILE_KINDS enforcement), SR-8/9 (backlog/STATUS paths).
`verify.py` PASSES on current tree.
</content>
</invoke>
