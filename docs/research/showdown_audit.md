# Showdown Phase 0 — Coverage Audit (2026-06-04)

Two independent read-only subagents audited (A) logic-side and (B) data+pipeline-side coverage;
their raw matrices were then RECONCILED against ground truth by the main session (the agents had no
session context and missed several recently-added test files). This doc = the corrected audit + the
worklist that drives Phases 1–3.

## Reconciliation corrections (agent claims vs ground truth)
| Agent claim | Ground truth |
|---|---|
| B: `remediate_listing`/`_outcome_class` untested | **Wrong** — `tests/pipeline/test_listing_remediation.py` (11 tests, all 4 branches + boundaries) |
| A: 07 compute helpers untested | **Covered** — `test_compute_synthetic.py` (7 hand-computed tests incl. traps) + the 2,296-row pre/post-split identity proof (DONE.md 2026-06-04) |
| A: `reach_curve`/`exit_strategy`/`stop_loss_strategy`/`outcome_breakdown`/`wipeout_flags` gaps | **Covered directly** — `tests/layer3/test_reach.py` |
| A: `weights.oos_evaluate` untested | **Covered** — `tests/layer3/test_oos.py` (contract + genuinely-OOS check) |
| B: merge step P3 | **Raised to P1** — it recomputes MFE/MAE for the screener-weekly fix-set rows in the substrate |

## CONFIRMED REAL GAPS → the worklist
**P1 (result-critical, always-on tests to write — Phase 2/3):**
1. `spine.combined_exit_strategy` — TP+SL timing approximation (peak-first logic, ambiguous count)
2. `spine.basket_dispersion` — top-N concentration / mean-vs-median (the "average is a mirage" claim)
3. `spine.allotment_capture` — flip-trap inverse-allotment math
4. `spine.outcome_profile` — the predictor's outcome picture (peak/trough/best/worst/median/wipeout band)
5. `backtest/engine._metrics` — the final aggregation (mean/median/win-rate) every strategy reports
6. `analogs.resolve_sector` + `robust_ranges` — wrong sector resolution silently shifts analog cohorts
7. Scorecard component math pinned directly: `return_potential`, `multibagger_odds`, `downside_safety`, `tradeable_upside`
8. `scrapers/screener_prices_merge.py` weekly MFE/MAE + clamp + timing (synthetic, like 07 got)
9. `scrapers/bhavcopy.parse_bhavcopy` + `bhavcopy_ohlc.parse_day`/`_num` — they feed ALL prices
**P2 (supporting, include where cheap):** `spine.partial_exit_strategy`, `average_down`, `lifecycle`,
`bootstrap_median_ci`, `pct_num`/`pct`.
**P3 (display-only — explicitly skipped):** report/charts formatting, findings table prose, `format_text`
(already has a render test), `guarded` label text.

## Data invariants (Phase 1 source list — agent B §A + spec §Phase 1)
Identity (isin unique/12-char; cohort 1269/1027; type ∈ {MB,SME}) · timetable (open<close<listing) ·
listing (low ≤ open/close ≤ high where present) · movement envelope (mae ≤ endpoint ≤ mfe, both entries
× 1y/3y/5y) · outcome_class ↔ current_return thresholds (−0.90/−0.20/0.20/1.00) · listing_metrics_status
enum + unreliable_coverage ⇒ nulled listing fields · compulsory/liquidation delist ⇒ −100% · join
integrity (ipo_analysis ⊇ keys of universe/returns_summary; no dup isin anywhere) · bounds (returns >
−1.001; dates 2006-01-01..AS_OF; issue_price>0; gmp_pct ∈ [−100,500]; sub_*_x ≥ 0) · alpha recomputation
(50-row sample vs nifty50.csv ±2bp). Financial cross-field checks (pat ≤ sales etc.) = OBSERVATIONAL
(report-only): real-world restatements make hard asserts too brittle.

## Not coverable offline (documented exclusions — py_compile only)
`00_build_longterm_spine` (cloudscraper), `06_validate_tickers` (yahoo), `longterm/02_detail`,
all scraper FETCH paths incl. `nse_session.prime_nse_session` live priming (wiring is tested; HTTP isn't,
by design). These depend on live web state — an offline identity check is impossible *in principle*
(the web moved since the freeze), not a missing test.

## Entry points (Phase 3 smoke list)
Safe read-only smokes: run_layer3_report (writes report/ only), predict_ipo, run_backtest,
run_validation, run_oos (stdout) — plus app.py via headless Playwright. `run_weights` WRITES
data/master/scorecard_weights.json + calibration.json → smoke it in the SANDBOX only, never in-place.
`run_refresh` needs network → excluded. `run_all` = the sandbox pipeline test itself.

## Raw agent matrices
Agent A (logic) and Agent B (data/pipeline) full tables retained in the session transcript; the
corrected verdicts above supersede them where they conflict.
