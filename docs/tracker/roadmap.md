# Post-D-1 Roadmap — the 3 high-priority foundational items

> Kept SEPARATE (here) so the big rocks don't get lost in the catch-all `improvement_backlog.md`. Owner-set 2026-06-17.
> These come AFTER D-1 (the corp-action fix) + the low-bucket/doc-alignment cleanup land.

## Execution context (owner)
- **Time budget:** ~**3 days**. Each day ≈ **4 hours owner-present** + a ≈**5-hour unattended night run** (~27 hrs total).
- **Model:** all 3 are **compute/reasoning-heavy → use the HIGHEST Claude (Opus)** for design + build.
  *(Subtlety for #3: DESIGNING the orchestration needs Opus; the POINT of it is to route later RUNS to cheaper models.)*
- **Mode:** each is a focused **brainstorm → spec → build** campaign (like D-1), not a point-fix. #1 explicitly **pauses other dev** while reconciling.
- **Reality check:** each item likely spans more than one day — the 3 days *kick them off in order*, they won't all fully finish in 3 days.

## The 3 items — priority order (foundation → fresh data → efficiency)

### 1 · PIPELINING / REPRODUCIBILITY — HIGHEST (the bedrock)
A definite, **deterministic** way to run the initial build + apply rules/fixes as a layered overlay + "once done is done":
`pipeline output + ordered overlay = substrate`, **IDEMPOTENT (same result every time)**. Until this exists, no re-run — of new
rules OR new data — is safe.
- **Process:** build the overlay system → create the overlay file (seed from D-1's Task-8 manual-remediation inventory) → regenerate
  fresh → **DIFF vs the current substrate → every mismatch is a BUG (in new data OR old data) → review + resolve each → trust → go live.**
  Doubles as a full data-integrity sweep. Ordered/idempotent/conflict-aware/provenance (see TODO-D1c for the hard parts).
- **Home:** `improvement_backlog.md` → TODO-D1c (overlay) + the DATA & RULES ARCHITECTURE umbrella.

### 2 · PULL LATEST DATA (live)
Keep the dataset current — new IPOs + new corp actions — flowing **deterministically through #1**. Safe ONLY after #1.
- Wire the corp-action steps (`03h/03j/03k/03l`) into `run_refresh.py`; `corp_actions_as_of` watermark (pull from watermark − ~1mo overlap);
  classify + apply rules/fixes **in-place** for new records (so we never re-accumulate a hand-fix backlog).
- **Home:** `improvement_backlog.md` → TODO-D1d.

### 3 · THINK-TANK ORCHESTRATION — efficiency (gated on the cheaper-plan move)
The multi-model workflow orchestration to operate from — route grunt work to cheap models, frontier only where it matters.
Motivated by the planned move to a **cheaper Claude plan**.
- **Home:** `improvement_backlog.md` → META-O (model-routing tournament) + `thinktank/orchestration/docs/think_tank_architecture.md` (currently WIP).
- **TIMING NUANCE:** if the cheaper-plan switch is **imminent**, pull this EARLIER (so #1/#2 themselves run cost-efficiently); if "after a point", 1→2→3 stands.

## Immediate sequence (before these 3 start)
Finish **D-1** (build + the Task-8 human gate) → the **low-bucket batch** (SR-1/8/9/10 + DA-2/3/4) → **doc-alignment** cleanup → THEN start **#1**.
Full open-work detail lives in `improvement_backlog.md`; live state in `STATUS.md`; history in git log.
