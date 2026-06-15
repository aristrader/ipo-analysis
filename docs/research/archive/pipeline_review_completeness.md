# Pipeline completeness review — does execution_pipeline.md capture every hard-won lesson? (2026-06-08)

Method: enumerated the DISTINCT failure-modes this project actually hit (from DONE.md + tier1_wave1_verdicts.md
+ CLAUDE.md conventions), then checked each against `docs/research/execution_pipeline.md` (doc + TASK-KICKOFF
PROMPT). "Covered" = the doc/prompt names it or hard-routes to a brief that does. Scope note: the pipeline doc is
deliberately a process meta-loop and DELEGATES research/data rigor to `hypothesis_protocol.md`. The gap that matters
is the lessons that fall OUTSIDE both the loop AND that delegation — those are the real MISSING items below.

| # | Lesson / failure-mode (where it bit) | Covered in pipeline? | Fix — exact line to ADD |
|---|---|---|---|
| 1 | Post-build review catches bugs the BUILD/FIX itself introduced (review #2, the honesty-fix overclaim) | YES (steps 6-7 + Why) | — |
| 2 | Placebo kills a hypothesis that PASSED its falsifier (H-C2 p=0.156) | YES (step 38 right-size + Why) | — |
| 3 | Look-ahead traps (days_to_peak, lifetime turnover, future-window classify, day-X forward) | PARTIAL (only via hyp-protocol §4, not named in doc) | Doc Right-sizing/research bullet: "research review = placebo/falsifier AND a look-ahead audit per protocol §4." |
| 4 | Survivorship honesty (delisted→terminal, wipeout=−100% stays counted; silent delisted-drop bias) | MISSING | Add a "DATA-TRUTH INVARIANTS (any task touching numbers)" box: "survivorship-honest — delisted→last price, compulsory→−100%, failures stay in the denominator." |
| 5 | Never pool modes/segments (MB vs SME, boom vs longterm; N11 pooled-bug) | MISSING | Same invariants box: "never pool modes/segments — split MB/SME × boom/longterm; the 4-cell check." |
| 6 | Min-N floors + distributions-over-means (sub-floor N printed +313% on N=2) | MISSING | Same box: "min-N floors (<12 suppress / 12-29 thin / ≥30); medians + P10/P90, never bare means; always print N." |
| 7 | Mode / evidence-strength labeling (live vs sim; in-sample vs OOS; "mostly simulated" mean) | MISSING | Same box: "label evidence strength — live vs sim, in-sample vs OOS-validated; never present sim as realized." |
| 8 | Misleading headline numbers (mean vs median; mislabeled benchmark; 2.09x vs 1.18x median) | PARTIAL (Why cites the 2.09x correction, but no standing RULE) | Kickoff step 6: "REVIEW must check the HEADLINE: lead with median for skewed outcomes; benchmark/labels correct; no apples-to-oranges lift." |
| 9 | Scope-the-data FIRST (2/3 Thread-C hypotheses were data-gated) | MISSING | Kickoff between steps 1-2: "0. SCOPE THE DATA FIRST — confirm the substrate has the columns/N before designing; a data-gated idea is parked, not faked." |
| 10 | Verify from ground truth, never memory (WORKFLOWS principle 1) | MISSING (assumed, never stated) | Kickoff step 8 / doc: "verify from GROUND TRUTH, never memory — re-derive counts/numbers from data each time." |
| 11 | `wc -l` lies on the CSVs (embedded newlines) — count via csv/DuckDB | MISSING | Same invariants box: "`wc -l` lies on the CSVs — count records via the csv module / DuckDB, never line count." |
| 12 | No-scipy / pure-Python; `PYTHONPATH=. .venv/bin/python` (plain python absent) | MISSING (only in hyp-protocol §6) | Doc env note: "Env: run `PYTHONPATH=. .venv/bin/python`; no scipy (use the srho helper); numbered files import via importlib." |
| 13 | Git is LOCAL-ONLY — never add a remote / push | MISSING | Kickoff step 8 / doc cleanup: "commit LOCALLY only — git is local-only, never add a remote or push." |
| 14 | Company-laptop security (playwright off-by-default, localhost-only, telemetry off) | MISSING | Doc note: "Security: playwright stays OFF by default (docs/playwright_on_off.md); Streamlit localhost-only; no secrets in tracked files." |
| 15 | Keep STATUS / DONE / rules / project_map current as work happens | YES (step 9 + standing rule) | — |
| 16 | Honest verdict-recording chain (ledger → rules/index → STATUS), kill or survive | PARTIAL (step 9 "record the verdict"; chain only in hyp-protocol §7) | Kickoff step 8: "record the verdict via the full chain (verdicts ledger → rules/index → STATUS), kill honestly." |
| 17 | DIVERGE actually changes outputs (multi-lens, incl. RED-TEAM) | YES (step 2 + Why) | — |
| 18 | Independent review is NON-NEGOTIABLE on money/score surfaces | YES (step 6) | — |
| 19 | Reverse-causation fences (N14 micro-cap = CURRENT mcap, crashed→reads micro) | MISSING | Look-ahead bullet (#3): "...and reverse-causation (a feature that is an OUTCOME, e.g. current market_cap on a crashed stock)." |
| 20 | "evolve-only-if-robust" score policy — a signal enters score only on robust OOS lift | PARTIAL (hyp-protocol §5 only) | Acceptable as-is if #3's research-review pointer is added (it routes to the protocol). |
| 21 | Right-size honestly; SAY when you skip a stage | YES (Right-sizing + standing rule) | — |
| 22 | Refactor-safety: prove behavior-identical before/after (compute() split: 0/2296 differ; data/master byte-identical) | MISSING | Doc infra bullet: "Refactors/dedup: prove behavior-identical (before/after diff on real rows; data/master byte-identical to backup) before claiming safe." |

## Top gaps to fix (highest-value first)
1. **No DATA-TRUTH INVARIANTS box** — the doc never restates survivorship-honesty, never-pool, min-N/medians,
   evidence-labeling, or the `wc -l` gotcha (#4,5,6,7,11). These bit the project repeatedly and a process loop
   that omits them lets a clean-process build ship a misleading number. Add a short box and reference it from
   kickoff step 6 (REVIEW) and step 8 (verify).
2. **No "SCOPE THE DATA FIRST" step** (#9) — 2/3 recent hypotheses were data-gated; belongs as kickoff step 0.
3. **Headline-honesty not a standing REVIEW rule** (#8) — the 2.09x→1.18x lesson is in "Why" but not an
   actionable check; add it to kickoff step 6.
4. **Verify-from-ground-truth + git-local-only + env/no-scipy + security** (#10,12,13,14) — the standing
   constraints are assumed but never written into THIS doc or its prompt; a fresh agent reading only this doc
   would miss them. Add a compact "Standing constraints" footer linking WORKFLOWS + hypothesis_protocol.
5. **Refactor behavior-identical proof + reverse-causation + look-ahead audit** (#22,19,3) — fold into the
   infra-task and research-review bullets so the review step explicitly hunts them.
