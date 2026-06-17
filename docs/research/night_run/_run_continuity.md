# Night-run continuity + standing authority (2026-06-17)

> If my context was cleared/compacted and I'm re-invoked, READ THIS FIRST for the TRUE state. The design run is
> COMPLETE — do NOT re-run it. Below: what's done, what's next (owner action), and the still-active scope-guard.

## ✅ FINAL STATE — DESIGN RUN COMPLETE (2026-06-17)
The data-foundation DESIGN run is functionally DONE. NOTHING to re-run for the design.
- **Group B (data issues) DONE** → `docs/research/data_issue_register_2026-06-17.md` — **29 distinct issues**
  (CRITICAL 4 = I1, D-1, D-2, D-3 · HIGH 9 · MED 11 · LOW 5; status: 19 open · 4 fixed-still-hold ·
  2 fixed-but-regressed · 4 handled-before). Source detail: `night_run/task_14..task_20_*.md`.
- **Group A (architecture) DONE** → `docs/research/data_architecture_design_2026-06-17.md` — 19 sections,
  **24 owner-decisions** pinned (§0), ONE in-thread review pass (§18, findings R1–R6). Source detail: `night_run/cluster_1..3_*.md`.
- **DO NOT re-run Group A or Group B** — complete. (Workflow `wf_362066cc-8dc` ran Group B; Group A finished via lean
  manual agent orchestration. The cluster_*/task_* files are the source detail behind the 2 rollup docs.)
- **Process lesson (keep):** loop-until-dry × multi-lens review = for DIRTY-DATA hunting only; DESIGN = bounded 1–2
  review passes then STOP at "sound." (Over-running it earlier burned budget; the lean Group A cost ~0.6M total.)

## ▶ WHAT'S NEXT — owner action, then BUILD (not design)
1. **Owner reviews** the design doc's 24 decisions + §18's 6 findings (R1–R6) + the 29-issue register. That review is the payload.
2. After decisions → **BUILD** (separate effort, separate budget, NOT this run). Fold HIGH findings R1–R3 into decisions 6/11/9-22 first.
3. **R3 is a real prerequisite:** a `total-shares-outstanding` SOURCE is needed before the D-3 as-of fix + EPS-recompute
   can fully land — not yet planned. Surface it when building.

## THE SCOPE-GUARD — now DISABLED (owner-disabled 2026-06-17, after the design run)
**STATUS: OFF.** The owner renamed the settings key `"hooks"` → `"_hooks"` in `.claude/settings.local.json`, so the
PreToolUse guard no longer runs — build/attended work is unblocked, and the disposables (the action log + the 2
`_tmp_verify_*.py`) have been deleted.
- **To RE-ENABLE** for a future confined/unattended run: rename `"_hooks"` back to `"hooks"`. The script lives at
  `.claude/hooks/guard_bash_scope.py` (inert while the key is `_hooks`).
- **BEFORE reuse, TIGHTEN it** (from the agy log audit): the guard kept everything in scope (zero out-of-scope writes)
  but its regexes OVER-BLOCKED legit *sandboxed* python — variable names `nc`/`rm` and `>` comparison operators inside
  `python -c` bodies tripped the netcat/rm/redirection rules (~14 false-positive blocks). Don't keyword-scan quoted
  python; only check real shell tokens. Also: `agy` after `cd && ...` isn't recognized (only first-token agy is).
- When active it BLOCKED: any Write/Edit outside `docs/research/`, plus rm/mv/truncate/git-commit/push/sudo/network, and
  logged every action to `night_run/bash_action_log.tsv` (now deleted). It was SELF-LOCKING (couldn't edit its own settings).
