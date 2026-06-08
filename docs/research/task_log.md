# Task log — append-only, one entry per non-trivial task (execution_pipeline.md §artifact)

The on-disk PROOF that the pipeline ran (red-team fix: a slogan with no record stops being followed
silently). Also crash-resume. Trivial one-liners/hotfix-minimal need no entry. Newest at the bottom.

## 2026-06-08 — Harden the execution pipeline itself (3-lens self-review)  [path: FULL]
scope: artifacts on disk (the pipeline doc + hook + CLAUDE.md) · diverge: 3 parallel lenses
(completeness a5c9420, structure a65a45e, red-team ab7eb57 — re-run after a net-drop killed the first) ·
converge: IN = data-truth-invariants box + scope-first step-0 + standing-constraints footer
(completeness); agent output-contract + keep/cut test + review stop-rule + DONE-gate + triage ladder
+ dedup + kickoff-once + authority boundary (structure); the checkable artifact = this task_log +
commit trailer + verify tripwire, plus conditional hook noise (red-team). CUT = heavyweight
"model-must-emit-self-audit" (too heavy; the log is the right weight).
build: rewrote execution_pipeline.md; created task_log.md; verify.py tripwire + conditional reminder.
review: the 3 lenses WERE the review (red-team flagged the no-record gap → fixed by this very log).
tests: full suite green · verify: clean.
verdict: pipeline now self-documenting + auditable; "followed the pipeline" is a fact on disk.

## 2026-06-08 — News/catalyst capability: intensive RESEARCH only (map the full opportunity)  [path: HYPOTHESIS/RESEARCH]
scope: owner wants the WHOLE space mapped, not built — sources beyond NSE, news categories→move-types,
drift/fade/fake-move mechanics, entry-timing, in/out/hold, news×IPO hypotheses, AND the far-tangent
ladder (IPO hold/exit → IPO buy/sell → all-stocks → TA+FA+news fusion). Output = a documented
opportunity map + hypothesis catalog + source table + layered task breakdown; scope-down decided LATER.
constraints (owner, away): trusted sites only · NO downloads · web search/fetch are read-only.
diverge wave-1 (6 parallel agents): sources(a381743) · taxonomy(a4b039b) · mechanics(aa6ac5a) ·
hypotheses(af261c8) · red-team(a7e5515) · grand-vision(ae05952).
diverge wave-2 (2 agents): synthesis+expand(a3edd3e) · coverage-critic(a2df0b8).
converge: docs/research/newsfeed_opportunity_map.md (authoritative) over 8 detail docs.
verdict: DONE (research). News-REACTION trading killed (structural slowness); 3 worth-doing —
delivery-%% [first, free/historical/backtestable-now], H7 corp-action backtest, RUNG 1 explanatory
feed; predictive news gated behind ~18-36mo forward-collection; all-stocks/TA+FA+news fusion KILLED
(negative-ROI/moat-breaking). Scope-down decision left to owner. NO BUILD.

## 2026-06-09 — Grade Fujiyama/Park calls + build the canonical improvement backlog  [path: LIGHT]
scope: (1) grade the two frozen point-in-time calls vs realized outcome; (2) capture every open improvement
idea (today's grading insights + prior threads) into ONE deduped, status-tagged menu (de-sprawl the 5+ next/roadmap docs).
grade: Fujiyama APPLY = CORRECT (+44% allottee on our data, brutal −24.6% MAE path, peak day 160); Park NEUTRAL
= a MISS (+73.9% allottee) caused SOLELY by the obscure-banker flag false-positiving on Nuvama (10 prior IPOs < 12
threshold; Nuvama is top-tier). Regret ≈ ₹74k/₹1L. Confirmed via banker freq count + verdict logic in calls.py.
build: docs/research/fujiyama_park_case.md GRADE section · docs/research/improvement_backlog.md (NEW canonical
menu: themes A grading-fixes / B miss-mining / C app / D news / E factors / F close-loop / G beyond-IPO) ·
NEXT.md banner → backlog is the live menu · project_map CONTEXTS "improvement backlog" + verify wires it.
verify: PASS (274 tests collected, 29 findings, 2384 rows, no drift). no code logic changed (docs + map only).
verdict: DONE. do-first for the 6hr batch = A1 banker-flag fix (proof: Park); high-value companion = B1 miss-mining.
- addendum (2026-06-09): B1 reframed as symmetric two-sided miss-mining (false-negatives=missed winners/opportunity
  + false-positives=APPLY'd losers/real capital — the latter flagged higher-priority per downside-first ethos).
  Added THEME H to improvement_backlog: relative-valuation-vs-peers + intrinsic value (FA dimension; ember = existing
  n6/pe_vs_sector −43pp MB). Honest blockers: look-ahead, all-stocks point-in-time peer panel (collides w/ extension_roadmap),
  fuzzy peer-ID. MVP = peers as earlier-IPOs-in-industry (owned point-in-time data, clean). Phased ~10-50 tasks, gated.
