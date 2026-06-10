# Autonomous session log — 2026-05-31 (Layer-3 build window)

Running autonomously while user is away (~6h). This log is the single place to see what happened.

## ✅ DONE — Integration pass (substrate refresh)
Applied all verified fixes and recomputed the substrate (`data/master/ipo_analysis.csv`). Backups in
`archive/pre_integration_20260531/` (masters + corp_actions). Canonical run: 07 → screener_prices_merge → 08 → 09.

| change | how | result |
|---|---|---|
| 5 verified splits | appended to `corp_actions.csv` (by isin+symbol) | Aditya Vision/Insolation/Angel One 1:10, Trident 14:10 bonus, MIC 5:1 |
| 79 recovered listing days | `data/reference/listing_day_recovered.csv` + 12 new price files; `remediate_listing(recovered=)` in 07 AND merge | `recovered_bhavcopy`=79 (73 equity); `unreliable_coverage` 142→59 |
| pre-2007 alpha | Nifty50 extended to 1990 → step-07 recompute | 129/151 pre-2007 IPOs now have alpha_1y (was ~0) |
| Smallcap-250 alpha | new `alpha_sc_*` cols in step 07 (niftysmallcap250.csv, 2017+) | alpha_sc_1y on 1262 stocks |
| boom sector/mcap | `03f_sector_mcap.py` re-pull (376/400) + fold in 08 step [3b] | boom-MB sector 3%→94%; overall 44%→60% |
| Tantia FPO issue_price | 5000→50 in longterm_mainboard.csv | garbage outlier removed |

Engine code touched: `pipeline/07_returns_summary.py` (smallcap alpha + listing-override consumption),
`pipeline/listing_remediation.py` (branch-0 recovered, raw/raw scale-invariant gain),
`scrapers/screener_prices_merge.py` (override honored), `pipeline/08_build_universe.py` (+step 3b), `pipeline/03f_sector_mcap.py` (new).

Residuals (flagged, non-blocking): 24 boom-SME sector unresolved (no-match, logged in `sector_mcap_skipped.csv`);
59 `unreliable_coverage` (scale-inversion — needs a recompute decision, not data); 14 xcheck listing mismatches;
3 market-maker + SoftTech corrections deprioritized (not used in any finding; values partly already present).

## 🔬 Enhancement + methodology review (subagents) — incorporated into the build
- `docs/research/layer3_enhancements_ideas.md` — 15 new metric/rule ideas (N1–N15) + per-finding enhancements.
- `docs/research/layer3_methodology_review.md` — 6 must-fixes. Baked into the spine/report:
  1. **T3 uses RAW `return_from_listing_*`, NOT alpha** (alpha is issue-anchored, contains the pop → fake correlation).
  2. **Long-horizon (3y+) panels are longterm-only** (boom is maturity-gated; no cohort-swap "trend").
  3. **boom-MB sector suppressed where N<floor** (even at 94% coverage, guard cells).
  4. **Competing-risks = a BAND** (40/195 delistings have a reason; show wipeout lower/upper + at-risk per year).
  5. **`current_return_from_issue` BANNED from base rates** (age-mixing look-ahead; use maturity-gated horizon alpha).
  6. **Min-N suppression UNBYPASSABLE** in the report assembler; sub-floor chart bars greyed.

## ✅ DONE — Layer 3 Part A (engine + 8 findings + report)
Built `layer3/` package: `config.py`, `spine.py` (method spine), `charts.py`, `report.py` (unbypassable N-guard),
8 findings (`t1`base-rates, `t2`survival-band, `t3`pop-fade[raw-return], `t5`ofs, `t6`sector, `t7`benchmark+bias-audit,
`t8`drawdown, `t9`profitable), `run_layer3_report.py`. **28/28 tests pass** (`tests/layer3/`) incl. the 5-traps suite.
Report: `report/layer3_partA.html` (8/8 findings, 309 KB; 75 sub-floor cells auto-suppressed).
All 6 methodology must-fixes honored (T3 raw-return not alpha; long-horizon=longterm; competing-risks band;
current_return banned from base rates; min-N unbypassable; bias-audit included).
Early real results: MB IPOs mostly underperform (MB longterm 5y median alpha ≈ −82%, 59% below issue); SME boom 3y
median ≈ +7% but enormous dispersion; data_quality=low rows have 21–33% wipeout (so excluding them biases optimistic).

## ✅ DONE — Part A reviewed (2 subagents) + all issues fixed
Code review + statistical-output review (`docs/research/layer3_partA_code_review.md`, `..._stats_review.md`).
Fixed every Critical/Important: T5 OFS unit bug (ofs_pct is 0–100, not 0–1 — gradient was missing, now a clean
monotonic signal); per-cell N-guard (metrics on maturity-gated subsets now suppressed via min-count guard +
in-finding nulling); T9 now segments MB/SME (was pooled); boom long-horizon (5y) dropped → longterm-carried;
report guard detects count cols by pattern; proportion NaN-as-False fixed; T2 re-framed honestly ("ever-wiped-out
among IPOs ≥Y years", + strong SME-survivorship-undercount caveat); T8 mislabel; benchmark header softened.
**34/34 tests pass.** Report regenerated (8/8, 318 KB).
**KEY CORRECTION (verified empirically):** `alpha_*` is measured FROM THE LISTING price (alpha =
return_from_listing − benchmark), NOT issue-anchored as a reviewer claimed. So alpha = the secondary-buyer's
market-adjusted return; the allottee additionally gets the listing pop. Now labeled clearly in the report + T1/T3.

## ✅ DONE — Part B (analog predictor + scorecard)
`layer3/predictor/` — `analogs.py` (hard-gate → weighted-Gower soft-distance → widening ladder; forgiving sector
resolver; never self-matches; keeps delisted), `scorecard.py` (5 components: return-potential/multibagger-odds/
downside-safety/liquidity/quality + combined w/ preset profiles + confidence checklist), `predict.py` (orchestrate +
plain-text one-pager). CLI: `predict_ipo.py`. Tests pass. Honesty layer: min-N gating, "insufficient analogs",
RELAXED/confidence flags, shows named comparables + distribution, never forecasts the query's own number.

## ✅ DONE — Part C (backtester)
`layer3/backtest/engine.py` — 5 strategies (allottee-hold, flip-at-listing, secondary-hold, secondary-FILTERED,
secondary-avoid-hot), point-in-time + maturity-gated, net of costs, vs do-nothing (index). `run_backtest.py`.
Results (CORRECTED after B/C review): naive secondary buy-at-listing LOSES cross-regime (MB 1y median alpha
−16.8%). The Tier-1 filter (profitable & OFS≥25%, both pre-listing-known) only REDUCES the loss (MB 1y mean
+5.9% vs −2.3%, median −9.1% vs −16.8%) — median alpha stays NEGATIVE, so it does NOT beat the index cross-regime.
The earlier "+28% SME beats" was a small-N, single-regime, look-ahead (liquidity-gate) artifact the B/C review
caught — fixed: removed the look-ahead gate + verdict is now CROSS-REGIME (beats only if median>0 in boom AND
longterm). flip-at-listing looks great raw but is allotment/adverse-selection gated. 5 tests pass.
Robust takeaway: IPOs are hard to beat the market with, especially as a secondary buyer.

## ✅ DONE — rules registry + all project docs updated
`rules/index.md` populated with every finding/predicate/score-component/strategy + its impl + headline result +
status (reported/built/backtested). CLAUDE.md, DONE.md, TODO.md updated (Layer 3 = BUILT).

## ✅ DONE — B+C review folded (`docs/research/layer3_partBC_review.md`)
Fixed all Critical/Important: removed look-ahead liquidity gate from the filtered strategy (C2); backtest verdict is
now CROSS-REGIME, allottee/flip raw strategies marked 'n/a (not benchmark-relative)' (C1, C3); multibagger_odds now
uses from-LISTING 2x/5x for framing consistency (I1); scorecard picks ONE horizon for all components (I2).
**Corrected the overstated "filter beats do-nothing" claim** in rules/index.md + DONE.md + this log — the honest
result is the filter REDUCES the loss but median alpha stays negative (no cross-regime edge). 39 tests pass.

## ✅ DONE — 2026-06-01 batch (data-quality + findings + loop-closer)
- **Era-aware data_quality** (`09_assemble.py`): stop penalising IPOs for era-impossible fields (GMP pre-2020,
  pre-2017 subscription). low tier 210→12; high 1619→1931. Resolves most of the "low-quality bias" concern
  (it was conflating 'old IPO' with 'bad data'). Decision: keep-all-rows (honest).
- **N6 valuation (PE-vs-sector)** added → 20 findings. **Combined-score backtest** (`layer3/backtest/score_backtest.py`,
  the loop-closer): top-quintile predictor-score IPOs beat the field in BOTH regimes (boom +52% vs −4%, longterm
  −21% vs −48%; +38pp overall) → **VALIDATED cross-regime** (the score reliably RANKS IPOs). 62 tests pass.
- **Digging agents RUNNING** (per user: dig the high-value rows case-by-case):
  (1) the 75 `unreliable_coverage` split-driven rows → `docs/research/unreliable75_*` (find missing splits + correct
      listing prices: Astral/IEX/Wonderla/Rajnandini etc.). (2) remaining enrichment (24 boom-SME sectors, 12 low
      rows, longterm-financials sample) → `docs/research/enrichment_recovery.md`.
  **TODO on their completion:** verify their staged findings, append to corp_actions / listing_day_recovered /
  sector_mcap, re-run 07→merge→08→09, re-report. (Same verify-then-integrate pattern as the earlier recoveries.)

## ✅ DONE — 2026-06-01 final batch: data hunts + adversarial verification sweep + fixes
- **Data hunts:** 37/38 SME listing pops recovered (35 from our own price files) → `recovered_bhavcopy`=153, `unreliable_coverage`=1.
  24 renamed-company sectors. 61 longterm financials folded (the rest are DRHP-PDF-only → defer). Market-makers applied.
- **Verification sweep (2 skeptic agents) — found REAL issues, all fixed:**
  - Findings (V1): N3/N5/N6/N8 printed maturity-gated alpha on sub-floor N the guard missed (e.g. N6 +313% on N=2) →
    per-cell guard + N_1y/N_3y; guard erased band labels → added to `_ID_COLS`; N11 pooled MB+SME → split.
  - Predictor/backtest/validation (V2): **LOOK-AHEAD** in point-in-time scoring (read analogs' future-matured
    outcomes) → gated by horizon-completion; this DEFLATED combined-score lift +38pp→**+11pp** (honest: boom +76 /
    long +5, IN-SAMPLE/indicative). Removed the overstated hardcoded "cross-regime validated" string. Disclosed that
    quality/liquidity get 0 weight under data-informed (validated flags shown but don't move that score). Refreshed
    stale weights/calibration. Fixed validator mislabeling insufficient-N as FRAGILE.
- **62 tests pass.** Report 20 findings. The verification was worth it — it caught an inflated headline + a real look-ahead.

## OPEN at hand-off (all in TODO.md — none blocking; all 3 parts built+reviewed)
- [ ] Cross-regime sign-validation (reported→validated); data-informed scorecard weights from backtest lift.
- [ ] Optional Streamlit app (engine is UI-agnostic). Fold review-doc Minors + enhancement N-list ideas (N2/N4 etc).
- [ ] Integration residuals: 75 scale-inversion listing rows, 24 boom-SME sectors, 14 xcheck, 3 market-makers.

## How to use what was built
- Report:   `source .venv/bin/activate && PYTHONPATH=. python run_layer3_report.py` → open `report/layer3_partA.html`
- Predict:  `PYTHONPATH=. python predict_ipo.py --type MB --sector Finance --mcap mid --profitable 1 --ofs_pct 60 ...`
- Backtest: `PYTHONPATH=. python run_backtest.py`
- Tests:    `PYTHONPATH=. pytest tests/layer3/ -q`  (39 pass)
</content>

---

## 2026-06-01 — Movement lens (autonomous "keep developing" session)

Reframed the tool around the MOVE + the LIKELIHOOD (the user's philosophy), all entry-split (allottee vs secondary).

**Built & verified (69 tests green; app Playwright-verified end-to-end):**
- Step 07: within-horizon peak/trough MFE/MAE from BOTH entries — `mfe_*`/`mae_*` (issue), `mfe_lst_*`/`mae_lst_*` (listing). Full pipeline recompute (07→merge→08→09; ipo_analysis.csv = 2296 rows).
- `layer3/spine.py`: `reach_curve` (entry-aware), `exit_strategy` (take-profit ladder), `stop_loss_strategy` (SL-only — the flagship).
- Finding **M1** `findings/m1_exit_discipline` (exit-discipline & stop-loss base rates, entry-split + reach wedge). Report now 21 findings.
- `scorecard.multibagger_odds`: + P(EVER 2x/5x) via MFE (the endpoint-2x undercounts). `scorecard.tradeable_upside`: new component, WEIGHT 0 (display-only).
- `findings/t3_pop_fade`: + reach-curve-by-pop-bucket table.
- `backtest/analyses.exit_discipline_backtest`: take-profit ladder vs buy-and-hold, per segment×cohort×entry.
- `app.py`: dual-entry exit display (Score), entry toggle + stop-loss (Explorer), exit backtest (Backtester), tradeable-upside + ever-2x (Score).

**Key empirical truths:**
- NO take-profit or stop-loss rule beats buy-and-hold cross-regime (0 cells beat hold in BOTH cohorts) — the right tail carries IPO returns.
- Tight stops HURT the secondary buyer via whipsaw (MB −10% stop: mean 9.0% → 1.2%; 85% stopped, 37% of those recover).
- Allottee ~95–97% ever gave a ≥break-even exit; secondary 100% (listing day itself = break-even touch — framed honestly, not sold as a signal).
- multibagger gap: MB analog cohort 18.8% *ended* 2x vs 37.5% *ever touched* 2x.

**Deferred (judgment calls):** `NEEDS_YOUR_INPUT.md` — weight tradeable_upside into the score? promote stop-loss finding to validated? exit thresholds? prices re-pass for time-to-peak/trailing-stops (NOT computable now)?

Catalog of all reframes + deliberate skips: `docs/research/ideas_movement_lens.md`.
Adversarial review of the new code: launched (a second agent) — see below / rules/index.md.

### V3 adversarial review of the movement-lens code (2026-06-01) — fixed + verified

A second agent adversarially reviewed the new code. Core machinery (stop-loss math, no-look-ahead,
monotonicity, tradeable_upside weight-0, the cross-regime "no exit rule beats hold") all held. Fixed all
findings:
1. **[BUG] exit_discipline_backtest sample mismatch** — buy-and-hold baseline was on a larger (endpoint-only)
   sample than the rule (endpoint+MFE), up to a 40% N gap biased toward older/weaker names → now both share
   the `mfe & endpoint` mask. Headline ("0 cells beat hold in both cohorts") survives.
2. **[STAT] truncated-window MFE/MAE** — step 07 had no upper-coverage guard → now `end <= data_last` (or
   delisted), window lower-bounded at `>= listing_date`. Non-delisted truncated rows → 0.
3. **[STAT] root cause of the lone invariant violation** — `remediate_listing` rescales RETURNS by an inferred
   split factor AFTER MFE/MAE are computed (MFE left on the old price scale). Fix: a final vectorized INVARIANT
   CLAMP in step 09 (peak>=endpoint>=trough on the assembled columns) + an auditable `mfe_mae_clamped` flag.
   75 split-remediated rows (the known scale-inversion subset) now floored at the canonical return —
   conservatively understated, never overstated. **Invariant violations: 0/2296.**
4. **[STAT] multibagger_odds** ever-2x vs ended-2x now on one denominator (guarantees touched>=ended).
5. **[NIT] scorecard listing-anchored components** now exclude `unreliable_coverage`.
6. **[HONESTY]** secondary-buyer "100% ever gave an exit / break-even 0.0%" is a listing-day tautology →
   caveated in M1 + flagged in the app (only +profit targets are informative for the secondary buyer).

Verified: 70 layer3 tests pass (added an invariant-regression test), report = 21 findings, app Playwright-clean.

### Autonomous window 2 (2026-06-01) — eval report + wipeout deepening + score policy
Built the "Evaluate this IPO" report (B1: `spine.outcome_breakdown` → full outcome breakdown + best/median/worst +
terminal risk) and the wipeout red-flag badge (A2: `scorecard.wipeout_flags`). Ran a 3rd wipeout-deepening subagent
→ `obscure_lead_mgr` graduated; low-promoter-holding + high-GMP REJECTED (wrong sign). Built f_flip_trap + f_average_down
(28 findings). Settled tradeable_upside via OOS (hurts 3y → display-only). LOCKED "evolve-only-if-robust" + a
tested-signal registry in rules/index.md. Stop-loss cross-regime nuance recorded. 73 tests, app Playwright-verified.
Caught + fixed the micro-cap reverse-causation trap in the subagent's wipeout finding before trusting it.
