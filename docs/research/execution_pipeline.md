# Execution pipeline — THE standing way to do any non-trivial task (owner mandate 2026-06-08)

Default for every substantive task. Slower per task; exceptional results, few/no bugs. The owner
has mandated this more than once — do NOT shortcut it unless the triage ladder says so.
Hardened 2026-06-08 by a 3-lens self-review (completeness · structure · red-team); the review docs
are `docs/research/pipeline_review_*.md`. **Authority:** this doc = the OUTER loop for ALL tasks;
`hypothesis_protocol.md` WINS for research-test mechanics (placebo/falsifier/look-ahead/data conv.).

## TRIAGE FIRST — which path? (top-down, FIRST match wins; never self-rationalize)
- **FULL pipeline** — anything that touches money numbers, the score, the ledger, a user-facing
  surface, a data product, or adds/changes a signal. (Independent post-build REVIEW agent required.)
- **LIGHT** — infra / data-capture / refactor: diverge = 1 red-team lens (doubles as review) + TDD.
- **HYPOTHESIS** — research: diverge = expand-the-space; "review" = placebo/falsifier per
  hypothesis_protocol.md; register every verdict (kill honestly).
- **HOTFIX (urgent)** — say "hotfix" out loud, do the MINIMAL safe change + test, LOG it, and
  backfill the review next turn. (The only sanctioned skip.)
- **TRIVIAL** — a true one-liner/typo/doc-tweak: just do it (no ceremony, no log).
"Non-trivial" = more than a one-liner OR touches data/score/money/a public surface. When unsure,
go one tier heavier, not lighter.

## THE STEPS (run ONCE per task at pickup — the per-turn hook is a reminder, not a restart)
0. **SCOPE THE DATA FIRST.** Confirm the inputs exist/are clean BEFORE designing (2/3 Thread-C
   hypotheses were data-gated; the day-1 idea was forward-only). State the task + success criteria
   in one line. Open a `docs/research/task_log.md` entry (template below).
1. **DIVERGE — thinking agents (Task tool), 2-3 DISTINCT lenses, spawned in PARALLEL, wait for all.**
   Lenses: user-value · analytical-depth · RED-TEAM (for a hypothesis: expand-space · test-design ·
   falsifier). Each agent returns a FIXED contract: `PROPOSALS (each: what · feasibility-from-owned-
   data · effort S/M/L · ethos-fit) · TOP PICK · BLOCKERS/TRAPS`. (Essays don't converge.)
2. **CONVERGE** with an explicit keep/cut test — keep an item ONLY if (high owner value) AND
   (feasible now) AND (fits ethos); else CUT or OPEN-QUESTION. Output an `IN / CUT / OPEN` spec.
   Show the owner the dimensions surfaced.
3. **PLAN** — break into small, independently-testable sub-tasks. Builds are SEQUENTIAL (parallel
   edits to the same files conflict).
4. **BUILD** — TDD: failing test → minimal code → green → commit. Small steps, frequent commits.
5. **REVIEW — INDEPENDENT agent AFTER the build** (FULL path only; non-negotiable for money/score
   numbers). The post-build review repeatedly catches what pre-build divergence cannot — INCLUDING
   new errors the build/fix itself introduced (proven twice on 2026-06-08). Check output against the
   DATA-TRUTH INVARIANTS below.
6. **FIX → re-review. STOP RULE:** loop review↔fix until a pass finds ZERO new substantive findings.
   If a 3rd pass still finds new bugs → STOP and escalate to the owner (don't grind).
   **Disagreement rule:** if lenses/reviews conflict on anything showing a NUMBER, the red-team/
   falsifier wins; else surface the trade-off to the owner.
7. **TEST + VERIFY** — `PYTHONPATH=. .venv/bin/pytest tests -q` green + `.venv/bin/python verify.py`
   clean (incl. the schema gate).
8. **CLEAN UP + RECORD** — STATUS/DONE/rules/index/project_map current; commit with the PIPELINE
   TRAILER (below); finish the task_log entry with the honest verdict.

## DONE = ALL of: criteria met · review clean (or placebo passed) · suite+verify green · docs updated · committed with trailer · task_log entry closed · verdict honest. Anything open → not done.

## DATA-TRUTH INVARIANTS (check at REVIEW + VERIFY — the hard-won rules; violating one = a wrong number)
- **Survivorship-honest:** delisted → terminal (compulsory/wipeout = −100%, else last price); failed
  names STAY in the denominator (never silently dropped).
- **Never pool** modes (live/gap_filled/backfilled/historical_sim) or segments — judge MB/SME ×
  boom/longterm separately (the 4-cell check).
- **Min-N floors** (suppress <12, "thin" 12-29, full ≥30) + **distributions over means** (median +
  P10/P90; a few winners drive the mean — the 2.09×-mean-vs-1.18×-median lesson).
- **Evidence-strength labeled** always (live = forward truth · sim/backfill = rehearsal/OOS);
  headline the HONEST number (median, correct benchmark, correct units) — never the flattering one.
- **No look-ahead** (no future-window classification, lifetime stats, days_to_peak) — see
  hypothesis_protocol.md. **No reverse-causation** (a feature that's actually an outcome, e.g.
  post-crash market_cap).
- **Refactor = behavior-identical PROOF** (before/after on real rows; data/master byte-identical)
  before calling a dedup/cleanup safe.

## STANDING CONSTRAINTS (always)
Verify from GROUND TRUTH, never memory (`wc -l` LIES on the CSVs — count via csv/DuckDB). Env:
`PYTHONPATH=. .venv/bin/python`; NO scipy/statsmodels (use the srho/Wilson/bootstrap pure-Python
helpers). **GIT IS LOCAL-ONLY** — never add a remote / push. Company laptop: Playwright OFF by
default (`docs/playwright_on_off.md`), Streamlit localhost-only, no secrets tracked.

## THE CHECKABLE ARTIFACT (red-team #1 fix — makes "followed the pipeline" a FACT on disk)
- **`docs/research/task_log.md`** — append-only, ONE entry per non-trivial task. Doubles as
  crash-resume (an agent died mid-task on 2026-06-08; a log survives that). Template:
  ```
  ## YYYY-MM-DD — <task one-liner>  [path: FULL|LIGHT|HYPOTHESIS|HOTFIX]
  scope: <data confirmed?>  · diverge: <lenses / agent ids>  · converge: <spec / IN-CUT>
  build: <commits>  · review: <agent verdict / placebo result>  · tests: <suite> · verify: <clean?>
  verdict: <honest outcome>
  ```
- **Commit trailer** on the task's final commit: `Pipeline: path=FULL diverge=3 review=agent tests=green`.
- **verify.py tripwire:** warns when the latest commit changed substantive code (layer3/pipeline/
  scrapers/app/tools) but didn't touch task_log.md — so a skipped pipeline is visible, not silent.

## KICKOFF (paste at task start, or just follow steps 0-8 above)
> A non-trivial task is picked. Triage the path, then execute steps 0-8 of
> docs/research/execution_pipeline.md: scope-data → diverge (parallel multi-lens agents, fixed
> output contract) → converge (keep/cut) → plan → build (TDD) → independent review → fix-to-stop-rule
> → test+verify → cleanup with task_log entry + pipeline commit trailer. Honor the DATA-TRUTH
> INVARIANTS and STANDING CONSTRAINTS. If skipping a stage, say which and why up front.
