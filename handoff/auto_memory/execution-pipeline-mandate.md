---
name: execution-pipeline-mandate
description: "Owner's standing way-of-working — full diverge/converge/build/review pipeline per non-trivial task, not one-dimensional shortcuts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 01820f2d-c29a-4f29-84ad-349ce26b70fa
---

For any non-trivial task the owner expects the FULL pipeline, not a one-dimensional implementation:
brainstorm → DIVERGE (2-3 thinking agents, distinct lenses incl. a red-team) → converge (YAGNI) →
plan → BUILD (TDD) → independent REVIEW agent AFTER the build → fix → test+verify → cleanup. Slower
per task, but exceptional results and few/no bugs.

**Why:** proven in the 2026-06-08 session — the post-build review caught a bug the honesty-FIX
itself introduced; a placebo killed a hypothesis that had passed its falsifier; the red-team lens
showed a shipped headline number misled on 4 axes. Single-dimension work, even careful work, ships
subtle errors; multi-perspective + adversarial review removes them.

**How to apply:** codified in this repo at `docs/research/execution_pipeline.md` (right-sizing
rules included) + CLAUDE.md "HOW we work" + project_map CONTEXTS. The independent REVIEW step is
NON-NEGOTIABLE on anything showing money numbers / scores. Only skip the ceremony for a genuine
one-liner/typo, and if skipping a stage, say so and why up front. The owner has restated this more
than once — treat it as a hard default. See [[project_ipo_state]].
