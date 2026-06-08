# Red-team: the execution-pipeline mechanism (2026-06-08)

Target: `docs/research/execution_pipeline.md` + its enforcement = a per-turn line printed by
`verify.py --quiet` (the `UserPromptSubmit` hook in `.claude/settings.local.json`) + a CLAUDE.md
"HOW we work" pointer. Question: how does this FAIL / get skipped / become theater / waste budget /
give false confidence IN PRACTICE. Severity tags: [KILLS] / [IMPORTANT] / [NIT].

## 1. ENFORCEMENT — there is none [KILLS]
The hook only `print()`s a sentence; CLAUDE.md is only prose. Nothing reads the model's plan,
nothing gates the commit, nothing records that diverge/review happened. A future session can read
the reminder, ignore it, and one-dimension the task — exactly what already happened once. The
mechanism is 100% reliant on the model voluntarily obeying advisory text it sees every single turn
(and therefore habituates to — see #2). An advisory nudge cannot enforce a "NON-NEGOTIABLE" rule;
calling it non-negotiable while backing it with a `print` is the core contradiction.
FIX (stronger-but-sane, all lightweight, no new infra):
- **A DONE-checklist in the commit trailer.** For any commit touching score/findings/pipeline code,
  require a trailer block the model must fill: `Pipeline: diverge=<lenses|skipped:why>
  review=<agent|skipped:why> tests=<n pass>`. Add a `commit-msg` (or pre-commit) hook that rejects
  the commit if a touched-path-is-substantive AND the trailer is absent. This is checkable, cheap,
  and creates the missing RECORD (also fixes #6).
- **A self-audit line the model must emit** at task start AND task end: start = "Pipeline plan:
  <full|infra-light|one-liner> because <reason>"; end = "Pipeline done: diverge ✔/✘ review ✔/✘
  tests ✔". Forces a conscious right-size decision instead of silent skip. Cheap, no infra.
- **A task-log file** (`docs/research/pipeline_log.md`, append-only): one line per non-trivial task
  with date + the two audit lines. verify.py can warn if HEAD changed substantive files since the
  last log entry. Turns "we ran the pipeline" from a claim into a grep-able fact.

## 2. NOISE / COST — fires every turn, including pure chat [IMPORTANT]
The reminder prints on EVERY `UserPromptSubmit` — "what's 2+2", "explain this function", a one-word
follow-up — all get the full pipeline sermon. Two failure modes: (a) **alert fatigue** — a line
that appears unconditionally every turn is trained-to-ignore within a session; its salience decays
to zero precisely because it is never contextual. (b) **token tax** — it is injected into context
each turn for the whole project's life; small per turn, but it is pure overhead on 100% of turns to
serve the <20% that are actual tasks. Worse, it competes with the *real* signals the same hook
emits (drift, routing) — burying a genuine drift warning under a constant boilerplate line.
FIX: make it **conditional + decaying**. Only print when a task is plausibly starting — heuristics
the hook can cheaply check: prompt length > N words, or contains task verbs (build/add/fix/
investigate/analyze/implement), AND git working tree is about to be touched / is dirty. On a clean
tree + short prompt, stay silent. At minimum, rotate the wording or print only once per session
(touch a sentinel file) so it doesn't habituate. Keep drift/routing unconditional; gate only the
pipeline line.

## 3. THEATER — three lenses that converge to mush [IMPORTANT]
The diverge step spawns 2-3 agents with "distinct lenses", then converges. Failure: the same base
model, same context, same prompt scaffold produces 3 near-identical takes that trivially "agree",
and the model ticks the box feeling validated. Convergence-as-confidence is a trap — agreement
between clones is not corroboration, it's correlated error. The ritual (spawn 3, synthesize, done)
can run with zero adversarial content and still look like the process was followed. The doc's own
evidence (#23-31) shows the VALUE came from genuine disagreement (red-team contradicting the
headline); a ritual that loses the disagreement keeps the cost and drops the value.
DETECT/PREVENT: (a) require each lens to output at least one finding that **contradicts or would
change** the current plan — a lens that only agrees is logged as "no-signal" and doesn't count
toward the 2-3. (b) Make the RED-TEAM lens mandatory and have it state a concrete failure mode +
severity (as this doc does), not a vibe. (c) In the converge step, the model must list *what
changed* because of divergence; "nothing changed" is a valid answer but must be stated — if diverge
never changes the spec across many tasks, that's evidence it's theater and should be down-scoped.

## 4. HALTING / BUDGET — no stop rule, no crash recovery, conflict-prone [KILLS]
Several distinct failures:
- **review↔fix loop has no termination.** "Loop until clean" — but a review agent can always find
  *something*; with no max-iterations or severity floor, a perfectionist loop burns budget on nits
  or oscillates (fix A surfaces B, fix B re-surfaces A). FIX: cap at 2 review rounds; round 2 only
  re-checks issues from round 1 + anything the fix touched; remaining findings are logged as
  known-accepted, not blocking. Define "clean" = no KILLS/IMPORTANT open, not zero findings.
- **Full pipeline on every task = hours + huge tokens.** 9 stages × multi-agent on routine work is
  not free; the doc says "slower per task" as if that's only upside. On a busy session this is the
  thing that gets silently dropped first (cost pressure), which *guarantees* erosion (#critical).
- **Agents die mid-run** (just happened to a prior run of me). The pipeline has no resumability:
  if the build agent dies after stage 5, there's no record of what diverge concluded or which tasks
  are done. FIX: the task-log (#1) doubles as a checkpoint — write the converged spec + task list to
  it before BUILD, so a fresh session resumes from stage 5 instead of restarting at stage 1.
- **Parallel builds conflict.** Nothing coordinates two task-pipelines touching the same files /
  STATUS / project_map; last-writer-wins corruption. FIX: one active pipeline at a time per repo, or
  git-worktree isolation per task (the project already has worktree tooling).

## 5. "NON-TRIVIAL" is undefined and gameable both ways [IMPORTANT]
The model decides what's non-trivial, with no check. Game-low: call real work "basically a
one-liner" to skip the expensive pipeline under time pressure (the dominant direction, and the one
that already bit). Game-high: ceremony a typo fix into a 9-stage epic to look rigorous, wasting
budget. The doc's right-sizing tiers help but the *classification* is unenforced and self-serving.
There is also **no urgent-hotfix path**: a one-line bug breaking the app at 2am should not require
3 diverge agents, but the doc only exempts "genuine one-liner / typo".
FIX: (a) make the right-size call an explicit emitted line (#1 self-audit) so it's at least on the
record and the owner can spot abuse. (b) Add a concrete trigger table instead of a vibe: "touches
score/findings/money-number OR >~40 LOC OR new data source → full; else light; trivial+green-tests
→ just do it." (c) Add an explicit **HOTFIX escape**: "production-broken → fix + test + commit now,
then run the review retroactively and log it." Naming the escape stops it from being an unlogged
silent skip.

## 6. FALSE CONFIDENCE — "we ran the pipeline" with no proof [KILLS]
Because nothing records the stages, "I followed the execution pipeline" becomes an unfalsifiable
trust signal in commit messages / STATUS / to the owner. The owner reads it as "diverged + reviewed
+ verdict honest"; in reality it may have been a single-pass build with the words attached. This is
worse than no pipeline: it manufactures unearned trust in exactly the money-numbers the project
exists to protect. The 2026-06-08 evidence that motivated the mandate is itself only prose in a doc
— there's no artifact proving review #2 caught the 2.5x overclaim; future sessions take it on faith.
FIX: the artifacts from #1 (commit trailer + append-only task-log + the review agent's actual output
saved under `docs/research/reviews/<date>-<task>.md`). Trust must point at a file, not a sentence.
A claim of "reviewed" with no saved review output should be treated as "not reviewed".

## Critical risks (ranked) + the #1
1. **[KILLS] No enforcement + no record (#1, #6)** — the entire mechanism is a printed suggestion;
   "we ran it" is unverifiable, so trust is manufactured.
2. **[KILLS] Budget/halting (#4)** — unbounded review↔fix, no crash-resume, no parallel guard;
   cost pressure makes this the first thing dropped.
3. **[IMPORTANT] Habituated noise (#2)** — an every-turn line trains itself to be ignored and
   buries real drift warnings.
4. **[IMPORTANT] Theater convergence (#3) + gameable "non-trivial" (#5)** — process can run empty
   and still tick the box.

### THE #1 RISK
**The pipeline quietly stops being followed within a few sessions — and nobody can tell.** It is
enforced only by an advisory `print` that the model habituates to (#2), under budget pressure that
makes skipping the cheapest move (#4), with no artifact that records whether diverge/review actually
ran (#6) and a self-judged "non-trivial" gate that rationalizes the skip (#5). Each turn the
reminder fires, the bar to ignore it drops, and there is no tripwire that detects the erosion. The
single highest-leverage fix is to **convert one stage from advice into a checkable artifact** — a
commit trailer / append-only task-log filled by the model and warned-on by verify.py — so that
"followed the pipeline" becomes a fact on disk instead of a habit that silently decays to a slogan.
