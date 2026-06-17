# Structure / Sprawl Review — 2026-06-16

Read-only structural audit (tracking/pointer/log files, doc sprawl, orphans, stale pointers,
thinktank-vs-top-level duplication). Judged against the repo's own "ONE home per info type" rule
(CLAUDE.md §DOC DISCIPLINE). Recommendations only — nothing was changed. Companion to
`alignment_audit_2026-06-16.md` (that audit covers claims-vs-truth + code bugs; this one covers structure).

## Summary (5 lines)
- **14 findings**: 4 redundant/overlapping (A), 1 orphan (B), 5 stale pointers (C), 3 thinktank-vs-top-level (D), plus an explicit leave-as-is list (E).
- **Top 3 highest-value consolidations:**
  1. **`thinktank/orchestration/docs/think_tank_architecture.md` claims to "supersede" `execution_pipeline.md` + `hypothesis_protocol.md`, but all three are live** — pick ONE home for the way-of-working brief (SR-1). This is the single biggest "two homes" violation.
  2. **`rules/index.md` is referenced ~20× as a root path, but the file lives ONLY at `thinktank/rules/index.md`** — the app code (`app/screens/*.py`) reads a path that does not exist (SR-7). High: a real broken pointer.
  3. **`docs/research/improvement_backlog.md` and "STATUS.md (root)" are referenced in 6+ places but both actually live under `docs/tracker/`** — re-point the references (SR-8, SR-9).
- The `docs/tracker/` files are mostly DISTINCT info types (STATUS / task_log / improvement_backlog do not duplicate each other) — only one tracker file is sprawl (SR-5).
- `docs/research/INDEX.md` is a hand-maintained snapshot that has drifted from the real tree (wrong locations + missing subdir files) — it half-violates the "don't hand-maintain a second listing" rule it itself states (SR-11).

---

## (A) Redundant or overlapping files

### SR-1 — HIGH — Way-of-working brief has TWO homes (thinktank supersedes, but originals stay canonical)
- `thinktank/orchestration/docs/think_tank_architecture.md` (lines 4-6) says verbatim: *"This is the ONE file. It consolidates and supersedes: `docs/research/execution_pipeline.md` (the 8-step outer loop) … `docs/research/hypothesis_protocol.md` (the 3-layer testing protocol)."*
- BUT `docs/research/execution_pipeline.md` and `docs/research/hypothesis_protocol.md` still exist AND are wired as the canonical standing briefs: `project_map.py:191-195` lists both as CONTEXT files, `CLAUDE.md` §"HOW we work" + §"Standing agent briefs" point every agent at them, `docs/research/INDEX.md:20-21` lists both as STANDING briefs, and `verify.py` asserts they exist. So a research agent is told "your brief is execution_pipeline.md" while a thinktank doc says that file is superseded.
- **Evidence of three live homes for the same content:** execution_pipeline.md (7KB), hypothesis_protocol.md (5KB), think_tank_architecture.md (consolidates both).
- **RECOMMENDATION:** Decide ONE home. Either (a) demote `think_tank_architecture.md`'s "supersedes" claim to "summarizes for the LangGraph orchestrator" (keep the two `docs/research/` briefs canonical, since that's what CLAUDE.md + project_map + verify point at), OR (b) actually retire the two `docs/research/` files into the thinktank doc and re-point CLAUDE.md / project_map / INDEX. Do NOT leave the contradictory "supersedes" sentence standing. Lowest-effort: option (a) — edit one sentence.

### SR-2 — MED — Two parallel "cognitive architecture" docs in thinktank/orchestration/docs/
- `think_tank_architecture.md` ("The Research Lab — Unified Cognitive Architecture v3") and `app_think_tank_architecture.md` ("The Foundry — App Development Cognitive Architecture v2"). Each header declares itself "the ONE file." They are deliberately split (research vs app/SWE), so not strictly duplicate, but the duplicated "this is the ONE file" framing + overlapping outer-loop/diverge-converge content invites drift.
- **RECOMMENDATION:** Leave as two files (the split is intentional) but reconcile the "ONE file" claims — neither is THE one file given execution_pipeline.md is the canonical brief (see SR-1). LOW-effort doc edit; flagged so it's not re-litigated.

### SR-3 — LOW — `docs/design.md` + `docs/discussion.md` are frozen 2026-05-30 build-era docs living in the active docs/ root
- `docs/design.md` ("Status: Approved — ready for implementation", 2026-05-30) and `docs/discussion.md` (2026-05-30 "capture every decision") are early build-era artifacts. They are still referenced (project_map, tests reference design.md as a schema-ish doc; INDEX/README mention them), so not orphans, but they read as superseded planning that by the repo's own rule ("Superseded → archive/") would belong in `archive/` or be explicitly marked historical.
- **RECOMMENDATION:** Leave in place (they're referenced) but add a one-line "build-era / historical — current truth = CLAUDE.md + STATUS.md" banner to each, OR move to `docs/archive/`. LOW priority; verify which tests depend on `design.md` before moving.

### SR-4 — MED — `docs/PRODUCT.md` vs CLAUDE.md "What this is" overlap
- `docs/PRODUCT.md` ("what the tool actually does today, honest scope") substantially overlaps CLAUDE.md's "What this is" + the 3-layers section. Both are living "what the product is" docs. Not a tracking-file duplicate, but two homes for "current capabilities."
- **RECOMMENDATION:** Keep PRODUCT.md as the single user-facing capability spec; ensure CLAUDE.md's overlap stays a pointer ("capabilities → PRODUCT.md") rather than a parallel description. LOW-MED.

---

## (B) Orphans

### SR-5 — HIGH — `docs/tracker/claude_transition_and_open_threads.md` is an orphan + stale one-time handoff
- `grep -rl "claude_transition_and_open_threads"` over `*.md`/`*.py` returns ONLY the file itself — referenced by nothing (not project_map, not CLAUDE.md, not verify, not INDEX).
- Content is a one-time "save state for the switch to Claude Code" handoff (Part 1 = token-saving tips already folded into CLAUDE.md §Token Saving; Part 2 = "where we left off" on thinktank orchestration, which the live STATUS.md + improvement_backlog have since moved past). It is a snapshot, now stale, and it is the file freshly `git add`-ed (git status A) — i.e. just committed but already dead.
- This is exactly the kind of file the anti-sprawl rule targets: a one-off tracking doc that duplicates STATUS.md ("where we left off") + CLAUDE.md (token tips).
- **RECOMMENDATION:** Harvest the one still-open item — the "finalize meta-orchestration architecture / who orchestrates what / where do API keys go" question (Part 2 §1) is a genuine open decision — into `docs/tracker/improvement_backlog.md` (DISCUSSION threads), then **delete** this file (or move to `docs/research/archive/`). Do not keep it as a live tracker.

---

## (C) Stale pointers

### SR-6 — HIGH — `app/screens/*.py` read `config.ROOT / "rules/index.md"` but no root `rules/` exists
- `app/screens/track_record.py:331`, `app/screens/registry.py:95,99`, `app/screens/evidence.py` all build `ROOT / "rules/index.md"`. There is NO `rules/` directory at the repo root (`ls rules/` → No such file or directory); the registry lives at `thinktank/rules/index.md`.
- `registry.py` has a graceful fallback ("rules/index.md not found"), so the app degrades rather than crashes, but the Track-Record / Signal-Registry / Evidence screens are silently reading a dead path — they will never show the registry.
- **RECOMMENDATION:** Re-point the app code to `thinktank/rules/index.md` (or add a `config.RULES_INDEX` constant). This is a real functional bug, not just doc drift — flag to owner as code-FIX. (Note: this is the path-confusion CLAUDE.md itself warns about — it calls the registry `rules/index.md` while the file is at `thinktank/rules/index.md`.)

### SR-7 — MED — CLAUDE.md + WORKFLOWS.md + README.md refer to the registry as `rules/index.md` (no `thinktank/` prefix)
- `CLAUDE.md` references `rules/index.md` ~6× (lines 34, 42, 69, 131, 166); `docs/WORKFLOWS.md:22,27,28`; `README.md:16`; `docs/research/README.md:7,10,16`. The real path is `thinktank/rules/index.md` (only `project_map.py` + MAP.md use the correct prefix).
- These read as the registry's "short name," so humans cope, but it's the documented source of the SR-6 code bug and a new agent following CLAUDE.md literally will `cat rules/index.md` and fail.
- **RECOMMENDATION:** Either (a) global-replace `rules/index.md` → `thinktank/rules/index.md` in the prose homes, or (b) the cleaner fix the owner may prefer: relocate the registry to a root `rules/` to match all the references + the app code. Decide ONE canonical path. (Already noted in `alignment_audit_2026-06-16.md:321`.)

### SR-8 — HIGH — `improvement_backlog.md` referenced as `docs/research/improvement_backlog.md` but lives at `docs/tracker/`
- File is at `docs/tracker/improvement_backlog.md`. Stale `docs/research/...` references: `docs/tracker/STATUS.md:39`, `docs/research/README.md` (bare `improvement_backlog.md`, implies same dir), `docs/research/INDEX.md:15` (lists it as a docs/research file), `thinktank/memory/README.md:25`, `thinktank/orchestration/docs/think_tank_architecture.md:59,61`. `ls docs/research/improvement_backlog.md` → does not exist.
- **RECOMMENDATION:** Re-point all references to `docs/tracker/improvement_backlog.md`. (project_map.py:208 already uses the correct path — copy that.)

### SR-9 — MED — "STATUS.md (root)" / bare `STATUS.md` references, but it lives at `docs/tracker/STATUS.md`
- `docs/research/README.md:18` says "live project state → `STATUS.md` (root)". CLAUDE.md references bare `STATUS.md` (lines 49, 77, 160, 164, 166) with no path. Actual: `docs/tracker/STATUS.md`. (project_map.py:145,206 + verify use the correct `docs/tracker/STATUS.md`.)
- **RECOMMENDATION:** Fix README.md's "(root)" claim and qualify CLAUDE.md's bare `STATUS.md` to `docs/tracker/STATUS.md` (or at least drop "(root)"). LOW-MED.

### SR-10 — MED — `docs/research/INDEX.md` lists files at wrong locations / misses subdir files (self-violating)
- INDEX.md:26-27 lists `batch_run_2026-06-09.md` and `task_log.md` as `docs/research/` files. Reality: `batch_run_2026-06-09.md` is in `docs/research/archive/`; `task_log.md` is in `docs/tracker/`. INDEX also flat-lists ~54 "concluded write-ups" while many now live in subdirs (`signals/` 11, `newsfeed/` 12, `enhancement/` 7, `data/` 5, `app_iterations/` 3) — those subdir files are largely absent from the listing.
- INDEX.md's own header (line 3) admits it's a "SNAPSHOT (no live generator)" that "may not list the newest docs" — i.e. it knowingly drifts, and `README.md` says "don't hand-maintain a second listing; it drifts."
- **RECOMMENDATION:** Either generate INDEX.md from the tree (a tiny script, matching the MAP.md-is-generated pattern) or demote it to a thin pointer ("for the live picture: `ls docs/research/**/*.md` + git log + rules/index.md") and stop hand-maintaining the 80-line listing. Given the repo already generates MAP.md, a generator is the on-brand fix.

---

## (D) thinktank/ vs top-level duplication

### SR-11 — HIGH — `thinktank/rules/` vs the registry referenced as root `rules/`
- The registry physically lives at `thinktank/rules/index.md` + `thinktank/rules/README.md`. Everything else (CLAUDE.md, app code, WORKFLOWS, README) calls it `rules/`. So there is effectively ONE registry but TWO claimed homes (root vs thinktank). See SR-6/SR-7 for the concrete breakage.
- **RECOMMENDATION:** Pick ONE physical location and make every reference agree. Recommend resolving alongside SR-6/SR-7 as a single "registry path" decision.

### SR-12 — MED — `thinktank/memory/auto_memory/project_ipo_state.md` duplicates project state (and is self-admittedly stale)
- `thinktank/memory/auto_memory/_README.md:6-9` explicitly warns this file is "HISTORICAL, not current" (says "1269 IPOs / 382 mainboard" which predates the ~2,384-row expansion) and tells the reader to trust CLAUDE.md/STATUS instead. It's a verbatim copy of out-of-repo assistant memory.
- This is a duplicate "project state" home that the file itself flags as wrong. Low risk because it's quarantined under `auto_memory/` with a warning, but it's still a stale state-doc a new agent could read.
- **RECOMMENDATION:** Leave the directory (it's a deliberate cross-account memory backup) but consider trimming the stale numeric claims in `project_ipo_state.md`, or strengthen the `_README.md` warning to "do not cite any number from these files." LOW.

### SR-13 — LOW — `thinktank/memory/README.md` re-teaches the onboarding order (READ THESE IN ORDER) that overlaps CLAUDE.md / STATUS
- `thinktank/memory/README.md` is a fresh-session onboarding doc that re-lists CLAUDE.md → STATUS.md → rules/index.md. Useful for a new account (its stated purpose), but it duplicates the "where to start" guidance in CLAUDE.md §"Where to start / how it flows" and references the registry as `rules/index.md` (SR-7 again).
- **RECOMMENDATION:** Keep (distinct purpose: bootstrap a login that lacks the out-of-repo memory) but make it point AT CLAUDE.md's start-here section rather than restate it, and fix the `rules/index.md` path. LOW.

---

## (E) Leave as-is (checked, deemed fine — do not re-litigate)

- **`docs/tracker/STATUS.md` vs `task_log.md` vs `improvement_backlog.md`** — these are THREE DISTINCT info types and do NOT duplicate each other: STATUS = live "now/next" state; task_log = append-only execution-pipeline audit trail (38KB, large-is-OK by design); improvement_backlog = open-WORK menu. Conforms to "ONE home per info type." Keep all three.
- **`docs/tracker/scraper_tps_limits.md`** — distinct reference (per-source rate limits / bot protection), referenced by `pipeline/03h_yfinance_corp_actions.py`. Not a tracker/log file despite living in tracker/; not sprawl. Keep (arguably belongs in `docs/sources.md` neighborhood, but it's referenced and distinct — leave).
- **`docs/research/archive/`** (29 files incl. `structure_audit.md`, old NEXT/roadmap/cleanup, build-era reviews) — explicitly out of scope ("archive/ is fine as-is"); it is correctly serving as the superseded-doc graveyard. Keep.
- **`docs/research/` topic subdirs** (`signals/`, `newsfeed/`, `enhancement/`, `data/`, `backlog/`, `app_iterations/`) — these are concluded-research evidence grouped by topic; not tracking files, not duplicative of each other. Fine (only issue is INDEX.md doesn't list them — see SR-10).
- **`docs/superpowers/plans/` + `specs/`** — formal per-feature plan/spec pairs, the documented home for specs ("formal specs → docs/superpowers/specs/"). Distinct, dated, not sprawl. Keep.
- **`project_map.py` / `MAP.md` / `verify.py`** — the structure home is consistent and mostly uses CORRECT paths (`docs/tracker/STATUS.md`, `thinktank/rules/index.md`, `docs/tracker/improvement_backlog.md`). MAP.md is generated. These are the reliable pointers; the drift is in the prose files (CLAUDE.md/README) NOT here. Keep; use them as the path-of-record when fixing SR-7/SR-8/SR-9.
- **Root `.py` entry points** (`app.py`, `run_all.py`, `project_map.py`, `verify.py`, `get_bse.py`, `get_nse.py`, `search_ddg.py`, `test_url.py`) — `get_bse.py`/`get_nse.py`/`search_ddg.py`/`test_url.py` look like ad-hoc one-off scratch scripts at the root rather than under `scrapers/`/`tools/`, which is a minor tidiness oddity, but none are tracking/pointer/log files and assessing them is code-organization not structural-sprawl. Noted, not actioned (out of this review's scope).
