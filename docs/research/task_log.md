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

## 2026-06-09 — App honesty + nav polish (5 red-team-scoped fixes)  [path: RIGHT-SIZED]
scope: implement EXACTLY 5 fixes from a red-team review (reading-order can mislead despite strong
honesty infra); no scope-creep. diverge/converge: pre-scoped by the briefing (each fix bounded to a
file:line range + DO-NOT-TOUCH list) so no fan-out needed; read the two app briefs first.
build (TDD on pure logic): A median-first ₹1L table (track_record.py); B ui.rate_with_ci() floor helper
+ apply to scorecard/reliability tables (point suppressed <MIN_N_FULL, point+band fused); C COMBINED→
'COMBINED RANK (vs history)' + visible caption + neutral number (ipo_detail.py); D portfolio.py docstring
corrected (full-fill-if-allotted best-case, NOT a probability-weighted blend); E sidebar IPO name search
→ ?isin= via st.switch_page (app.py) + ui.name_options/resolve_label_to_isin.
tests: +7 in tests/app/test_ui_logic.py (rate_with_ci below/at/above floor, missing band, garbage;
resolver sentinel/unknown; name_options unique-by-isin + skips missing). Suite 269p+12s (was 262+12).
verify.py exit 0. left out: scorecard_weights.json + batch_run_2026-06-09.md were pre-existing dirty
(not mine) — NOT committed. commit d51d7fe on auto/6hr-batch.

## 2026-06-09 — B1 two-sided miss-mining of recent-cohort calls  [path: RIGHT-SIZED hypothesis/research]
scope: extend the OOS forward test from bucket-aggregates to a PER-IPO grade for all 364 IPOs listed in
the last ~12mo; mine BOTH error types (FALSE-POS = losers we APPLY'd; FALSE-NEG = winners we waved off);
confirm/deny the obscure-banker false-negative hypothesis. brief: hypothesis_protocol.md + the Fujiyama
grade pattern. build: tools/research/miss_mining.py — point-in-time (analog pool = df._ld<r._ld; weights
derived per listing-month on prior-only data, ~30x cheaper than per-IPO with <0.01 drift verified;
per-segment prior-pool quintiles matching calls.py:add_quintiles). HONESTY: young cohort → realized-to-date
labels, EARLY READ, no 1y/3y; survivorship-honest (wipeout=-100%); restores committed scorecard_weights.json
via raw-bytes finally (no artifact corruption). FINDINGS: confusion matrix TP68/FP59/FN52/TN158; APPLY
hit-rate 44.2%, mean +28.6% vs cohort median -5.1% (ranking works). FALSE-POS = 0-flag blind spot, weak-demand
tell (sub 2.2x vs 6.6x). FALSE-NEG = obscure-banker flag SOLE blocker on 34/52, 17 top-quintile flips
(~Rs0.93M/Rs1L), 12/34 reputable banks mis-tagged → hypothesis CONFIRMED. deliverables: miss_mining_2026-06.md,
miss_mining_grades.csv, miss_mining.py. recording chain: ledger + rules/index (2 new lines) + STATUS + this log.
verify.py exit 0. seeds A1 (banker-flag fix) + new low-sub FALSE-POS guard. no commit of pre-existing dirty
newsfeed_*.md / batch_run docs (not mine). commit on auto/6hr-batch.
