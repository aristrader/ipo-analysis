# Prompt-engineering review of execution_pipeline.md (structure / executability)

Reviewed as a PROMPT artifact: would a fresh agent follow it correctly and consistently? Overall:
solid intent and good evidence section, but several steps lean on vague verbs, decision points have
NO stop/convergence criteria, and it assumes project context a fresh session won't have. Concrete
issues + exact replacement wording below.

## A. Ambiguous / non-actionable verbs

**A1. "DIVERGE" step (lines 10-12, kickoff 51-52) — under-specified agent spawn.**
"Spawn 2-3 agents that expand the idea into its 2nd/3rd dimensions" gives no OUTPUT contract, so
agents return free-form essays the converge step can't mechanically merge. Add a fixed output shape.
> Replace step 2 with: "DIVERGE — spawn 2-3 parallel agents, ONE lens each (default trio:
> user-value · analytical-depth · RED-TEAM; hypothesis trio: expand-the-space · test-design ·
> falsifier). Give each agent: the one-line task, the success criteria, and this output contract —
> return (a) 3-6 concrete proposals/risks for your lens, (b) the single highest-leverage one, (c)
> anything that would make you NOT ship. No essays; bullets only. Spawn in parallel, wait for all."

**A2. "CONVERGE" / "synthesize into a pruned spec" (line 13) — no criteria for what survives.**
"YAGNI — not every idea earns its place" is a vibe, not a rule. State the include/cut test.
> Append to step 3: "Keep an item only if it (i) moves a success criterion, or (ii) is a red-team
> risk with a plausible failure mode. Cut nice-to-haves, speculative scope, and anything no lens
> backed. Output the spec as: IN (with the lens that argued for it) / CUT (with why) / OPEN
> QUESTIONS for the owner."

**A3. "REVIEW … loop until clean" (lines 19, 58) — no termination rule; risk of infinite loop.**
Add a bounded stop + escalation.
> Replace step 7 with: "FIX every review finding, then re-review. Stop when a review pass returns
> ZERO new substantive findings (cosmetic nits don't count). If a 3rd review still finds NEW
> correctness/number bugs, STOP and surface to the owner — repeated new bugs signal a design
> problem, not a fix list."

## B. Decision points with no guidance

**B1. What if the 3 lenses DISAGREE / contradict?** Currently silent.
> Add to step 3: "When lenses conflict (e.g. user-value wants a feature the red-team flags as
> misleading), the RED-TEAM / falsifier wins by default for anything that shows the owner a number;
> otherwise present the trade-off to the owner rather than silently picking."

**B2. When is BUILD 'done' enough to review?** No exit from step 5.
> Add to step 5: "Exit BUILD when every planned sub-task is green and committed. Do not start
> REVIEW with red/uncommitted work."

**B3. Global DONE-definition is missing.** The pipeline has an entry trigger but no single
exit/done checklist. Add one explicit gate.
> Add a new closing section "## Done = ALL of:" — (1) success criteria met; (2) at least one
> independent post-build review returned clean (or owner-waived with reason); (3) full suite +
> verify.py green; (4) STATUS/DONE/rules/project_map updated; (5) committed; (6) honest verdict
> recorded (incl. anything that did NOT work).

## C. Right-sizing rule (lines 33-41) — the WHEN is fuzzy

The categories overlap and the agent must self-classify with no decision order, so a real feature
could get "just do it" and a typo could get the full ceremony. Make it a top-to-bottom decision
ladder.
> Replace the bullets with an ordered triage (first match wins):
> "Classify the task TOP-DOWN, first match wins:
> 1. Touches a money number / score / user-facing output → FULL pipeline (incl. independent review). No exceptions.
> 2. Research hypothesis → expand-the-space diverge + placebo/falsifier review per hypothesis_protocol.md; register the verdict.
> 3. Infra / data-capture / internal tooling → LIGHT: 2 lenses incl. a red-team (red-team may double as review), TDD + tests, no separate review agent required.
> 4. Genuine one-liner / typo / rename / comment → JUST DO IT, no ceremony.
> If unsure between two tiers, pick the heavier one. The cost of over-doing a typo is minutes; the
> cost of under-doing a feature is a shipped bug."

## D. Structure / redundancy / fresh-session survival

**D1. The numbered list (8-21) and the kickoff prompt (47-60) duplicate the 9 steps** with subtly
different wording (e.g. step count 9 vs 8 — cleanup is split differently). Drift risk: edit one,
forget the other. Fix: make the kickoff prompt say "execute steps 1-9 above verbatim" and carry
ONLY the right-sizing reminder + "say why if you skip a stage," so there's one source of step text.

**D2. Assumes project context a fresh session lacks.** State explicitly inside the doc:
- "thinking agents" = the Task/subagent tool (parallel), NOT the deep-research skill — name it.
- TDD / tests / verify.py: add the actual commands ("`PYTHONPATH=. .venv/bin/python -m pytest`",
  "`PYTHONPATH=. .venv/bin/python verify.py`") so a fresh agent can run step 8 without hunting.
- "commit" must restate the LOCAL-ONLY git rule (never push) — a fresh agent won't know it.
- Define "non-trivial" once at the top with 2 examples each side, so the entry TRIGGER is testable
  rather than judged.

**D3. Contradiction risk with hypothesis_protocol.md — currently OK but make it explicit.** The
hypothesis branch here is a 1-line pointer; good. Add: "For hypotheses, this doc governs the OUTER
loop (diverge/converge/cleanup); hypothesis_protocol.md governs the INNER test method and the
verdict chain. If they ever conflict, hypothesis_protocol.md wins for test mechanics." Prevents two
docs claiming authority over 'review = placebo'.

**D4. Entry trigger vs per-turn hook tension.** The verify hook fires the reminder EVERY turn, but
the doc says run the kickoff "at the START of every non-trivial task." A fresh agent may re-run the
ceremony mid-task. Add: "Run the kickoff ONCE per task, at pickup — not per turn. The per-turn hook
is a reminder the pipeline exists, not an instruction to restart it."

## E. Smaller fixes
- Line 13 "pruned spec" — define the spec's required sections (see A2) so it's a template, not a word.
- Step 4 "small, independently-testable tasks" — add "each sub-task must have a checkable
  pass/fail (a test, an assertion, or an observable output)" so 'testable' isn't aspirational.
- Add an explicit "WAIT for all agents before converging" (already in kickoff line 52; mirror it
  into step 2 of the main list so the two copies match — see D1).
