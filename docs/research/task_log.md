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

## 2026-06-09 — Autonomous batch (owner away; ended early by owner)  [path: FULL, multi-task]
Branch auto/6hr-batch (main untouched). SHIPPED: App C1 honesty/nav polish (d51d7fe/7f8a47f, walked, +7 tests) ·
B1 two-sided miss-mining of 364 recent IPOs (3dfc129; obscure-banker = sole blocker on 34/52 missed winners,
weak-sub = false-APPLY tell) · News R&D (e71dc61; delivery-% demoted, H7 promoted, D1 spec). WIP: A1 banker-flag
fix (8c87960, INCOMPLETE/UNREVIEWED — impl in scorecard.py passes tests but missing new-tests+robustness-verdict+
review). NOT STARTED: A3/H7/E1/H-MVP/A2 + weak-sub guard. Each shipped task ran diverge→build→(walk/grade)→commit;
A1 stopped before its test+verdict+review stages. Full record: docs/research/batch_run_2026-06-09.md.

## 2026-06-09 — Add RunAtLoad login-catch-up to the notifier launchd agent  [path: HOTFIX]
Owner Q surfaced that a missed 9:30/14:30/20:30 slot (Mac off/logged-out) isn't retroactively run by launchd.
Added <key>RunAtLoad</key><true/> to tools/notify/com.ipo.calls.plist → fires a catch-up run shortly after
login. Safe: the pipeline is idempotent gap-fill + .notified dedup (no-op + no re-spam when nothing missed).
plutil -lint OK; reinstalled to ~/Library/LaunchAgents + reloaded (unload→load); verified loaded (PID assigned,
RunAtLoad fired one bg catch-up run). Repo plist committed. Behaviour documented in batch_run_2026-06-09.md.

## 2026-06-10 — Policy reversal: Playwright ALWAYS ON (localhost-pinned)  [path: HOTFIX/config]
Owner deemed always-on safe given the localhost origin-pin (+ isolated/headless/version-lock + dangerous-tools
denied = no external-network surface). Flipped settings.local.json → enabledMcpjsonServers. Updated the policy
in CLAUDE.md, STATUS.md, trusted_sources.md, playwright_on_off.md (OFF-by-default → ALWAYS-ON). Flagged + documented
the ONE residual the pin doesn't cover (leftover Chrome-for-Testing → OS notifications) with the one-time OS
mitigation (Notifications → Chrome for Testing → OFF). verify clean.

## 2026-06-09 — H7 corp-action euphoria-top backtest (widens F10)  [path: hypothesis/research]
Tested H7: corp action (bonus/split) on a recent IPO marks a euphoria top → negative post-ex-date fwd alpha,
conditioned on prior run-up. 3-layer + same-name random-date PLACEBO + matched control, 4 horizons, cross-regime.
RESULT: DISPLAY-ONLY EXIT FLAG (confirms+narrows F10, NOT a score input — post-listing signal). Min-N binding
(n=31 total, boom 13 / longterm 18, below per-cohort floor; SAME sample as F10 — no dividend ex-dates exist, so
no independent N). Real action-specific edge at 1m/3m only (treated 1m -27% / 3m -22% beats control AND placebo);
6m/1y collapse into the placebo (generic euphoria fade — DON'T double-count F5e). Driver = run-up dose srho -0.74;
HIGH-run-up names -81% win 0% at 1m. Files: tools/research/h7_corp_action.py, docs/research/h7_corp_action_2026-06.md,
data/master/review/h7_corp_action_events.csv. verify.py exit 0. Did NOT touch rules/index.md/scorecard.py/n14 (A1
editing concurrently) — proposed rules line in the return report. Commit on auto/6hr-batch.

## 2026-06-09 — A1 obscure-banker flag redefinition: freq → quality-aware PIT (LIVE)  [path: FULL]
Completed the WIP A1 (commit 8c87960). Replaced the frequency-based (freq<12, quality-blind) obscure-lead-manager
wipeout flag — B1's documented false-veto driver (sole blocker on 34/52 missed winners; 12/34 reputable coverage
artifacts) — with a QUALITY-AWARE POINT-IN-TIME rule: fire iff the banker's prior IPOs (>=5, listed strictly before
this IPO) failed >=40% (wipeout|dead-money); ABSTAIN on a thin prior record (no frequency fallback). DIVERGE: 4
candidates (current / size-aware / quality-PIT / hybrid). BUILD: scorecard.py logic was in the WIP; I added the
behaviour tests + ran the decisive evidence + decided the verdict. EVIDENCE (independently re-run, not trusted from
WIP): (1) cross-regime bad-outcome discrimination POSITIVE 3/4 N14 panels vs old rule's 1/4 (SME-boom +24.3pp CI-sep);
(2) placebo-clean (real 16.9pp vs null 5.8±3.6 p=0.00, but null mean>0 → ~1/3 mechanical); (3) un-vetoes 33/34 B1
missed winners (recomputed from miss_mining_grades.csv), all named reputable banks exonerated; (4) OOS lift A/B
(a1_fold_test): 1y better-2/same-1/worse-0 (no degrade), 3y mixed-but-thin. VERDICT: LIVE under evolve-only-if-robust
(improves purpose + fixes false-veto + no OOS degrade at high-N 1y). Conservative call honest about 3y ambiguity +
abstention coverage loss (607 rows silent). TESTS: tests/layer3/test_banker_flag.py (9 new — clean/bad/PIT/abstain/
series-consistency/real-data reputable exoneration). Full suite 280p/12s, verify exit 0. n14 NOT changed (it's a
descriptive historical anatomy; the LIVE predictor flag is what changed). Files: scorecard.py, test_banker_flag.py,
rules/index.md, docs/research/a1_banker_flag_2026-06.md, tools/research/a1_*.py (WIP). Adversarial review pending.
Commit on auto/6hr-batch only.

## A3 — 90-day capitulation EXIT re-test (2026-06-09, branch auto/6hr-batch)
VERDICT: NO — selling on the F5e day-90 flag does NOT beat HOLD cross-regime. Boom flagged-basket
forward-term alpha mean +29.1% [bootstrap +6..+56%, excludes 0] → selling DESTROYS value; longterm
noisy (CI straddles 0). Per-name "sell wins" 57-78% is the MEDIAN TRAP — placebo: non-flagged names
drift identically (boom −7.8% vs −15.4%; longterm −124.6% vs −132.4%) so the negative median is
universe-wide post-d90, not flag-specific. False-exit rate 22-43% dumps recoverers (Garden Reach
+3050%, IRFC/Kalyan/KFin near-misses; Fujiyama max90=0.987 tripped → +44% terminal, owner's
counterexample CONFIRMED). F5e stays a display-only FLAG/LEAN, NOT an act-on sell; score unchanged
(post-listing → never a score input). Confirms M1's right-tail mechanism (not independent). METHOD:
PIT (capit uses sessions 1..90 only; fwd alpha from d90), survivorship-honest terminals, Wilson CI,
pure-Python bootstrap, no scipy. FILES: docs/research/a3_capitulation_2026-06.md,
tools/research/a3_capitulation.py, data/master/review/a3_capitulation_false_exits.csv. Did NOT touch
rules/index.md (A1 owns concurrently) — proposed registry line is in the writeup for the controller.

## E1 — pre-IPO accruals (earnings-quality) signal (2026-06-09, branch auto/6hr-batch)
VERDICT: DISPLAY-ONLY (longterm-leaning, NOT cross-regime; NOT in score). DATA RESOLUTION first:
full Modified-Jones DCA stays DATA-GATED (no receivables column confirmed) — instead tested the
computable TOTAL-ACCRUALS proxy TA=(PAT−CFO)/avg total assets on the latest pre-IPO FY (yr3; ~72%
coverage overall but MB-longterm only 31%). This is the graded version of the proven binary n8 flag.
3-layer, PIT, survivorship-honest, placebo (1000× within-cell shuffle), no scipy. RESULT: bad-outcome
(wipeout/dead-money) spread Q3−Q1 works LONGTERM ONLY (MB +17pp p=0.045 N=141; SME +12pp p=0.029
N=318) and is NULL/INVERTED in boom (MB-boom 0 bad outcomes → no discrimination; SME-boom −2pp wrong
sign, placebo p=0.44 = noise). 3y alpha spread negative 3/4 cells but rank-IC ≈0 in 3/4 (only MB-boom
−0.15, one fragile tertile). Incremental over n8 (within n8-clean): adds +8–11pp longterm, nothing in
boom. → fails cross-regime gate + evolve-only-if-robust; would not survive an OOS fold (boom is null).
Modified-Jones formally stays data-gated. FILES: docs/research/e1_accruals_2026-06.md,
tools/research/e1_accruals.py, data/master/review/e1_accruals_{review,summary}.csv. Did NOT touch
rules/index.md or scorecard.py (parallel agents own them) — proposed registry line in the writeup.

## A2 — hold-through-drawdown / post-listing conviction overlay (2026-06-10, branch auto/6hr-batch)
VERDICT: REJECT as an act-on EXIT overlay; faint DISPLAY-ONLY median lean at best; re-confirms M1/A3
(post-listing → never a score input). THE QUESTION (Fujiyama case): among UNDERWATER names at decision
day D, does a PIT strength signal (up-day ratio + reclaim-off-trough + RS-vs-Nifty + volume-trend) that
EXITS the WEAK and HOLDS the STRONG beat do-nothing (always-hold)? DIFFERS from A3 (blanket sell on F5e
flag) — this is a CONDITIONAL exit, best-case for an exit rule. METHOD: PIT (strength from sessions 0..D
only; fwd alpha from day D to 6m/1y/terminal), D∈{90,126}, underwater := close[D]<issue_price_adj,
survivorship-honest terminals (decision A1), composite = within-underwater-group percentile ranks,
Wilson CI + pure-Python bootstrap + 1000× label-shuffle placebo, no scipy, cross-regime boom vs longterm.
RESULT: overlay does NOT beat do-nothing cross-regime — discrimination sign FLIPS boom↔longterm at D=90
(placebo p=0.021/0.027 but gaps +60.5%/−365.5%, opposite signs) and collapses to NOISE at D=126
(p=0.205/0.725). RIGHT-TAIL TRAP: the WEAK basket you'd sell carries a flat-to-POSITIVE mean fwd-term
alpha (boom +3.5% D90, +43.9% [boot +3..+104] D126) → exiting forfeits the right tail (242 weak-but-
recovered names, incl. Fujiyama-type underwater-then-ran). Only a faint median lean survives (strength →
less-negative MEDIAN among underwater, same family as F5e/persistence). FILES:
docs/research/a2_hold_drawdown_2026-06.md, tools/research/a2_hold_drawdown.py,
data/master/review/a2_hold_drawdown.csv. Did NOT touch rules/index.md/scorecard.py/scorecard_weights.json/
substrate (parallel agents own them) — proposed registry line in the writeup for the controller.

## H-MVP — relative valuation via earlier-IPO peers (2026-06-10, branch auto/6hr-batch)
VERDICT: REDUNDANT-WITH-n6 / display-only — no new score role. Theme H P0+P1 owned-data MVP (peers =
earlier IPOs same industry/sector within a size band, valued with point-in-time data we own; did NOT
build the P4 all-stocks panel). P0 hypotheses: (a) RE-RATING cheap-vs-earlier-IPO-peers catches up /
rich fades; (b) PEER-PROXIMITY dose. METHOD: PIT peer-matcher — for each IPO, peers = STRICTLY-earlier-
listed same-segment same-bucket IPOs with issue_size in a factor band + valid issue-time P/E
(=issue_price/eps_ttm fallback pe_ratio; loss-makers excluded); pe_pctl = fraction of peers cheaper;
maturity-gated fwd alpha vs Nifty; Wilson CI + bootstrap median CI + 1000x label-shuffle placebo; 3
configs (fine-industry/×3 band; broad_sector/×3; broad_sector/no-band) to separate weak-signal from
sparse-peers. TWO STRUCTURAL WALLS: (1) P/E coverage ZERO in longterm → valuation re-rating is
structurally boom-only, cross-regime gate uncleardable (same wall as n6/E2); (2) fine-industry matching
catastrophically sparse (13 boom-MB / 0 boom-SME with >=5 prior same-industry peers) → only broad_sector
populates = exactly n6's bucket. RESULT: in the one well-populated placebo-clean cell (boom/MB N=94, 1y)
cheap +14.7% vs rich -23.2% alpha = +37.9pp spread, IC -0.345, placebo p=0.000, bootstrap CIs separate
([+1,+36] vs [-33,-11]) — same sign/magnitude as n6's MB lean. SME directional (-0.40 IC) but thin
(N<=26), sign-unstable under the band; 3y untestable (prior-peer pool fills late in boom). DOSE rejected
(hi vs lo peer-count spreads equal). INCREMENTAL-vs-sector: IC peer -0.345 vs sector-rel -0.309, residual
-0.166 — non-zero but mechanical (peer pool IS the sector pool since fine-industry matching is empty);
NOT meaningfully incremental over n6, at large coverage cost. Recommend folding into n6 lineage, NOT a
new component; do NOT advance to P4 on valuation grounds. FILES: docs/research/hmvp_relative_valuation_
2026-06.md, tools/research/hmvp_relative_valuation.py, data/master/review/hmvp_relative_valuation_review.csv.
Did NOT touch rules/index.md / scorecard.py / scorecard_weights.json / substrate (parallel agents own
them) — proposed registry line in the writeup for the controller.

## B1 — weak-subscription false-APPLY guard (2026-06-10, branch auto/6hr-batch)
VERDICT: REJECT (does not survive cross-regime + placebo). THE QUESTION: among would-be-APPLY IPOs
(top-segment-quintile AND 0 wipeout flags), does adding a low-subscription veto (sub_total_x<3x) cut
false-APPLYs (losers we'd APPLY) WITHOUT killing winners, cross-regime? This is the conditional 2nd-order
angle (a guard ON the APPLY gate / the analog-vs-own-demand disagreement), distinct from the dead 1st-order
undersubscribed->bad screen (already REJECTED in rules/index.md). METHOD: PIT (mirrors miss_mining/calls) —
per-listing-month prior-only weights + per-segment quintiles, would-be-APPLY=top-q+0-flags, 437 APPLYs
(2020+ matured; longterm 2006-19 sub coverage ~9% -> NOT TESTABLE). Split LOW<3x vs ADEQUATE>=3x; bad-rate
Wilson95, fwd alpha_1y/ret_1y, winners-lost-if-vetoed; 2000x shuffle-sub placebo; threshold sweep; no scipy.
RESULT: placebo FAILS both cohorts (gap +7.7pp p=0.137 all / +5.6pp p=0.304 boom = noise); cross-regime
INVERTS (boom-matured low-sub APPLYs OUTPERFORM: a1y +23.8% vs +1.2%, equal win-rate) — B1's tell was a
young 2024-25 cohort artifact (unmatured winners); veto dumps winners ~1:1 with losers (32 winners @ median
+119% to avoid 33 losers, the fat right tail). Redundant with already-rejected first-order screen. FILES:
docs/research/weaksub_guard_2026-06.md, tools/research/weaksub_guard.py,
data/master/review/weaksub_guard_apply_pool.csv. Did NOT touch rules/index.md/scorecard.py/
scorecard_weights.json (parallel agents own them) — proposed registry line in the writeup for the controller.
