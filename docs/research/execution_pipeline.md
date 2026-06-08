# Execution pipeline — THE standing way to do any non-trivial task (owner mandate 2026-06-08)

Default for every substantive task (a feature, an enhancement, a hypothesis, a fix that isn't a
one-line typo). Slower per task; produces exceptional results with few/no bugs. The owner has
asked for this explicitly and more than once — DO NOT shortcut it for speed unless the owner says
"quick/MVP" for that specific item.

## The pipeline (per task)
1. **Brainstorm** the idea (what + why + success criteria).
2. **DIVERGE — thinking agents, multiple lenses.** Spawn 2-3 agents that expand the idea into its
   2nd/3rd dimensions, each a DISTINCT lens (e.g. user-value · analytical-depth · RED-TEAM;
   for hypotheses: expand-the-space · test-design · falsifier). One dimension is never enough.
3. **CONVERGE** — synthesize the lenses into a pruned spec (YAGNI — not every idea earns its place).
4. **PLAN** — break the work into small, independently-testable tasks.
5. **BUILD** — TDD: failing test → minimal code → green → commit. Small steps.
6. **REVIEW — independent agent, AFTER the build.** NON-NEGOTIABLE on anything showing numbers the
   owner trusts. The post-build review repeatedly catches what pre-build divergence cannot —
   including NEW errors introduced *during* the build/fix itself.
7. **FIX** review findings → re-test. Loop review↔fix until clean.
8. **TEST + verify** — full suite + verify.py green.
9. **CLEAN UP** — STATUS/DONE/rules/project_map current; commit; honest verdict recorded.

## Why (the evidence — all from the 2026-06-08 session that earned this mandate)
- DIVERGE changed real outputs: the red-team lens proved the shipped "2.09x vs Nifty" headline
  misled on 4 axes → corrected to lead with the median.
- REVIEW caught what nothing else did, TWICE: review #1 found 2 latent benchmark bugs; review #2
  caught that the honesty-FIX itself had introduced a new ~2.5x overclaim in the lift column.
- PLACEBO (the hypothesis-equivalent of review) killed H-C2, which had PASSED the directional
  falsifier — without it, a noise pattern (p=0.156) would have shipped as a finding.
- Conclusion: single-dimension work, even careful work, ships subtle errors. Multi-perspective +
  adversarial review is what removes them.

## Right-sizing (honest, not dogma)
- User-facing / money-number / score-touching work → the FULL pipeline, always (incl. an
  independent post-build review agent).
- Infra / data-capture → diverge can be 2 lenses incl. a red-team; the red-team often doubles as
  the review; still TDD + tests.
- Research hypotheses → diverge = expand-the-space; "review" = placebo/falsifier per
  `hypothesis_protocol.md`; register every verdict, kill honestly.
- A genuine one-liner / typo → just do it (don't perform the ceremony).
- A FUTURE build (deferred) → run its divergence WHEN you build it, not pre-emptively.

## The standing rule
When the owner says "do X" for anything non-trivial, the answer is this pipeline — not a
one-dimensional implementation. If skipping a stage for a real reason, SAY SO up front and why.

## TASK-KICKOFF PROMPT  (run this at the START of every non-trivial task — copy verbatim)
> A task has been picked. Before any code, execute the standing pipeline
> (docs/research/execution_pipeline.md):
> 1. State the task + success criteria in one line.
> 2. DIVERGE: spawn 2-3 thinking agents with DISTINCT lenses (user-value · analytical-depth ·
>    RED-TEAM; for a hypothesis: expand-the-space · test-design · falsifier). Wait for all.
> 3. CONVERGE: synthesize into a pruned spec (YAGNI). Show the owner the dimensions surfaced.
> 4. PLAN: break into small, independently-testable sub-tasks.
> 5. BUILD with TDD (failing test → minimal code → green → commit), small steps.
> 6. REVIEW: spawn an INDEPENDENT review agent AFTER the build (non-negotiable if it shows money
>    numbers/scores). For a hypothesis, the review = placebo/falsifier.
> 7. FIX review findings → re-test; loop review↔fix until clean.
> 8. TEST + verify.py green; CLEAN UP (STATUS/DONE/rules/project_map); commit; record the verdict.
> Right-size per the doc (infra = lighter; one-liner = just do it) and if you skip a stage, say why.

(CLAUDE.md "HOW we work" points here; the per-turn verify hook injects a reminder so it can't be
forgotten. To run it deliberately, paste the block above when a task starts.)
