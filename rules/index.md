# Rules Index — master table (read first)

Seeded from `docs/strategies.md`; now updated with **Layer-3 build results** (2026-05-31). Each rule links to
its implementation + the report/backtest it produced. Status: `hypothesis` → `reported` (descriptive truth
computed, method-spine-guarded) → `backtested` (strategy run vs do-nothing) → `validated` (held cross-regime).

**Implementations:** descriptive findings → `layer3/findings/<id>.py` → `report/layer3_partA.html`.
Predictor components → `layer3/predictor/scorecard.py`. Strategies → `layer3/backtest/engine.py` → `run_backtest.py`.
**KEY:** `alpha` = FROM-LISTING alpha (return_from_listing − Nifty); the allottee additionally gets the listing pop.

## SCORE POLICY — the "evolve-only-if-robust" rule (locked 2026-06-01, user-approved)
The combined predictor score MAY evolve, but a new component enters the WEIGHTED score **only if it
improves-or-holds the out-of-sample top-quintile lift ROBUSTLY across splits** (3y AND 1y horizons, ≥2
train/test cutoffs, MB AND SME) — with weights from cross-regime rank-IC, **never search-fitted to the OOS
number** (that would overfit the test set). Otherwise the signal stays DISPLAY-ONLY. Every tested signal is
recorded below with its verdict, so we never re-test blindly and always know the full landscape (negative
results are kept on purpose).

### Tested-signal registry (score components)
| signal | state | evidence |
|---|---|---|
| return_potential | **IN SCORE** | rank-IC boom .13 / long .12 — predicts in both eras |
| multibagger_odds | **IN SCORE** | .15 / .11 |
| downside_safety | **IN SCORE** | .16 / .18 |
| tradeable_upside | **DISPLAY-ONLY** | predicts (.14/.07) BUT adding it CUT the 3y OOS lift 55.1→47.4pp (redundant with multibagger) → not robust → out of the score |
| liquidity | **DISPLAY-ONLY** (weight 0) | IC .04 / −.01 — flips sign → no signal |
| quality (query's own fundamentals) | **DISPLAY-ONLY** (weight 0) | IC −.02 / .01 — no signal (the cohort-derived components predict; the query's own fundamentals don't) |
| wipeout red-flags (tiny-sales, loss-making, obscure-banker) | **DISPLAY (badge)** — score-candidate | validated as descriptive cross-regime flags (N14); OOS-into-downside-score test pending before any weight |
| micro market-cap (as a wipeout flag) | **REJECTED** | reverse-causation — `market_cap_class` is CURRENT mcap, so a wipeout reads 'micro' because it crashed |
| low promoter holding (as a wipeout flag) | **REJECTED** | WRONG sign — high retention = thin illiquid float = the zombie profile |
| high GMP (as a wipeout flag) | **REJECTED** | WRONG sign — protective (hyped names stay liquid; the dead are the unwanted) |
| high debt/equity (as a wipeout flag) | **REJECTED** | only MB-longterm (N=13); flat on the high-N SME panels → not cross-regime |
| contrarian listing-gain entry | **REJECTED** | sign flips by cohort — listing-day gain is not a secondary-buyer signal |
| wipeout-safety (own flags → return) | **IN SCORE (data_informed, weight ~0.10–0.13)** — user-approved, folded 2026-06-02 | The FIRST signal to earn its way in under 'evolve-only-if-robust'. Cross-regime rank-IC boom .080 / long .048 → weight 0.13. OOS RE-VALIDATED after wiring: 3y lift **55→77pp** (train≤2019→test2020+), 1y +1.9→+3.6pp, +5.0pp on the other cutoff — holds across all splits. Component = 100−50·(validated flag count) on the query's OWN features; presets unchanged (weight 0). Standalone risk gauge also stays. |
| INTERACTION: low-debt × high-ROE (upside) | **VALIDATED (separate layer)** | the ONE combination that cleared super-additive + cross-regime + N≥~30/cell (N15). Does NOT feed the score yet (needs OOS-robust to graduate). |
| INTERACTION: any risk combination | **REJECTED (cross-regime)** | the risk-side hunt found NONE — single wipeout flags are the whole story; pairs overlap or sub-add. high-debt×loss-making is dramatic but longterm-only. |
| INTERACTION: tiny-sales × loss-making | **single-regime** | clean super-additive in longterm only; boom verdict was an artifact (loss-making-alone ≈ 0% in boom). |
| obscure-banker flag → false-negative driver | **CONFIRMED (fix → A1)** | B1 miss-mining (`miss_mining_2026-06.md`): on 364 recent IPOs the obscure-banker flag is the SOLE blocker on 34/52 missed winners; 17 are top-quintile (flag-only veto → would flip to APPLY, ~₹0.93M/₹1L recoverable); 12/34 bankers have ≥10 IPOs in full data (pure coverage artifact — Nuvama/Motilal/Morgan Stanley mis-tagged). Frequency-based + quality-blind → seeds A1 (size/quality-aware banker flag). |
| low-subscription veto on analog-top-quintile APPLYs | **CANDIDATE (display-first, untested)** | B1 miss-mining: all 59 FALSE-POS (losers we APPLY'd) carried 0 flags; sub_total_x median 2.2× vs 6.6× for true-pos winners; 32/58 were <3× subscribed; SME/small-issue took the −48% median hit. Proposed 2nd-order veto (weak demand AMONG analog-top-quintile names). MUST clear 3-layer + placebo (1st-order undersub-screens are dead) before any gate. |

| id | name | type | status | impl | headline result |
|---|---|---|---|---|---|
| desc-lasting-wealth | Lasting-wealth base rate | descriptive | **VALIDATED** (cross-regime) | findings/t1_base_rates | MB underperforms the index in BOTH regimes (median 1y alpha boom −10.7%, longterm −23.3%; longterm 5y ≈ −82%, 59% below issue). Robust. |
| desc-survival-hazard | Competing-risks wipeout band | descriptive | reported | findings/t2_survival | MB ever-wiped-out 14.6%→28% (≥1y→≥10y, lower bound; upper 38%). SME reads lower but is a survivorship UNDER-count |
| desc-sector-matrix | Sector alpha × survival matrix | descriptive | reported | findings/t6_sector | longterm sector matrix (alpha+2x+wipeout together); sub-floor sectors suppressed; boom sector for predictor |
| desc-drawdown-tax | MFE/MAE drawdown-tax map | descriptive | reported | findings/t8_drawdown | eventual winners still endure deep drawdowns en route (full vs investable subset) |
| desc-benchmark | Benchmarking + coverage + bias audit | descriptive | reported | findings/t7_benchmark | bias audit: data_quality=low rows have 21–33% wipeout vs 6–9% → excluding them biases optimistic |
| n4-issue-size | Issue-size 'Goldilocks' + size-survival | descriptive | reported | findings/n4_issue_size | issue_size_cr 100% covered; outcomes + wipeout band by size band & mcap class. Size-survival (small→more wipeout) holds in SME/longterm; MB issues rarely tiny (x-regime N insufficient for MB) |
| n2-subscription | Subscription-vs-outcome saturation | descriptive | reported — **boom-only** | findings/n2_subscription | demand→listing-pop vs demand→forward-alpha split; saturation test. SINGLE-REGIME (longterm subscription ≈0) — cannot be cross-validated |
| n3-demand-skew | QIB-vs-retail demand skew | predicate | reported — **boom-only** | findings/n3_demand_skew | QIB/retail subscription ratio tertiles → forward alpha + wipeout. Single-regime (boom). |
| n5-anchor | Anchor-conviction gradient | predicate | reported — **boom-MB** | findings/n5_anchor | anchor allocation % of issue, tertiled → outcomes. Boom-MB primary (SME anchor disclosure thin). |
| n7-fundamentals | Graded fundamentals (ROE/margin/debt) | descriptive | reported | findings/n7_fundamentals | tertiles vs alpha+wipeout. **Debt/Equity death signal holds**: MB top-debt tertile wipeout 8.9% vs 5.1%, worst 3y alpha. Not yet x-regime-validated. |
| n8-accrual | Accrual / cash-flow red-flag | predicate | reported | findings/n8_accrual | **strong signal**: 'PAT>0 but operating cash≤0' underperforms even loss-makers (MB 3y alpha −59% vs −23% clean; wipeout 12.6% vs 6.9%). Hard-to-fake earnings-quality flag. |
| n6-valuation | PE-vs-sector (mean-reversion) | predicate | reported — **boom-only** | findings/n6_valuation | PE normalized by sector median, tertiled → forward alpha. Expensive-vs-sector mean-reversion test. Boom-only. |
| n9-zombie | Zombie / dead-money base rate | descriptive | reported | findings/n9_zombie | the missing 3rd outcome: SME true 'bad outcome' ≈18–19% is mostly DEAD MONEY (alive, <−50%, illiquid), not formal wipeout. Key downside insight. |
| n10-migration | Outcome-class migration (listing→3y) | descriptive | reported | findings/n10_migration | dud-to-star / star-to-dud flows, cohort-constant. Distinct from T3. |
| n11-sc-divergence | Nifty vs Smallcap-250 alpha gap | descriptive | reported | findings/n11_sc_divergence | quantifies how much small-cap 'alpha' is borrowed beta (shifts a few pp at the right benchmark). |
| n12-banker | Lead-manager league table | descriptive | reported — **not scored** | findings/n12_banker | descriptive only; no clean banker→alpha signal (deliberately not a score input). |
| strat-holding-sweep | Holding-period sweep (1m→10y exit) | strategy | backtested | backtest/analyses | MB secondary alpha worsens monotonically with horizon (1y −16% → 5y −80%) — sooner-is-better / don't-hold. |
| strat-portfolio | Equal-weight basket vs do-nothing | strategy | backtested | backtest/analyses | dispersion-adjusted (NOT Sharpe); SME basket mean +38% but median −12% (huge dispersion) → typical name loses. |
| strat-flip-ev | Flip allotment-realism EV | strategy | backtested | backtest/analyses | **demolishes the flip myth**: naive +21% (MB) collapses to **+2%** after 3.5% median allotment prob + adverse selection. |
| x-nonequity | Non-equity instruments (FPO/InvIT/REIT) | descriptive | reported — **separate** | findings/nonequity | SEPARATE from equity IPOs (per user decision). FPO −30% 1y alpha / 21% wipeout; REIT/InvIT ~flat (income instruments). Small N, directional. |
| strat-combined-score | Buy top-quintile predictor-score IPOs (at listing, hold) | strategy | **OOS-VALIDATED at 3y** (weak at 1y) | backtest/score_backtest + weights/oos_evaluate (`run_oos.py`) | True out-of-sample test (weights fit ≤cutoff, tested on later-listed IPOs never seen): **3y horizon (train≤2019 → test 2020+): +55pp lift, top-quintile +54% vs field −1%, 61% win-rate** — real, generalizing. **1y horizon (train≤2022 → test 2023+): only +1.9pp** (and +5pp ≤2021→2022+). So: a 3-YEAR ranking tool with genuine OOS evidence; NOT a 1-year/flip signal. (The earlier in-sample +11pp is superseded by this OOS test.) |
| pred-pop-fade | Listing-pop → fade gradient | predicate | cross-regime only (**within-vintage WEAK**) | findings/t3_pop_fade | holds sign in both boom & longterm, but within-vintage check (2/4 yrs) DOWNGRADED it — not as robust as the 2-bucket check suggested. Allottee-vs-secondary wedge still holds. |
| pred-ofs-skin | OFS / skin-in-the-game gradient | predicate | reported — **MIXED x-regime** | findings/t5_ofs | high-OFS-better is a LONGTERM effect that REVERSES in boom (boom −29 vs longterm +48 alpha gradient; boom N=14) → NOT regime-robust. Don't trust as a standalone signal. |
| pred-profitable-ipo | Profitable-at-IPO premium | predicate | reported — **MIXED x-regime** | findings/t9_profitable | premium sign FLIPS across regimes (boom +20 vs longterm −15, MB; small N 16/11) → NOT robust in the MB cut. Re-examine with SME + larger N. |
| pred-anchor-unlock | Anchor lock-in unlock dip | predicate | hypothesis | (not built — needs daily event study + unlock dates) | — |
| pred-demand-skew | QIB-vs-RII demand skew | predicate | hypothesis | (Tier-2, not built) | — |
| score-return-potential | Score: expected alpha vs analogs | score-component | built | predictor/scorecard.return_potential | cohort median alpha (3y/1y) → 0–100 |
| score-multibagger-odds | Score: % analogs 2x/5x | score-component | built | predictor/scorecard.multibagger_odds | % of analogs ≥2x → 0–100 |
| score-downside-safety | Score: inverse of wipeout/below-issue/deep-DD | score-component | built | predictor/scorecard.downside_safety | 100·(1 − risk blend) |
| score-liquidity | Score: realizability | score-component | built | predictor/scorecard.liquidity | % investable analogs |
| score-quality | Score: query's own fundamentals | score-component | built | predictor/scorecard.quality | profitable/ROE/D-E/margin → 0–100 |
| score-tradeable-upside | Score: P(cohort ever reached +30%) | score-component | built — **weight 0 (display-only)** | predictor/scorecard.tradeable_upside | movement-lens component (MFE-based). Shown with the capture gap; NOT in the combined blend until a weights re-fit + OOS re-validation (deferred — see NEEDS_YOUR_INPUT.md). |
| mv-exit-discipline | Exit discipline & stop-losses (allottee vs secondary) | descriptive | reported (cross-regime nuance verified) | findings/m1_exit_discipline | **Take-profit & stop-loss base rates, entry-split.** Take-profit never beats hold cross-regime. Stop-losses: the validated truth is the MECHANISM, not 'stops never help' — stops/exits trade the right tail for the body, so they LOSE wherever IPOs show their tail (boom both segments + SME; tight −10% stops HURT the secondary buyer there) but BEAT hold in net-losing tail-less cohorts (MB/longterm). A stop is a bet that this IPO has no right tail (true for the median name, false for the cohort average). Same mechanism as f-partial-exit. |
| mv-multibagger-ever | Multibagger ODDS = P(ever touched 2x/5x) | predicate | reported | scorecard.multibagger_odds (+predict text) | the endpoint-2x rate UNDERCOUNTS the upside that was on the table: e.g. MB analog cohort 18.8% *ended* 2x vs 37.5% *ever touched* 2x. Both shown; the gap = the timing/exit tax. Score still anchored to endpoint-2x (keeps validated weights/OOS valid). |
| mv-T3-reach | Pop-fade, movement view (reach-curve by pop bucket) | descriptive | reported (texture on pred-pop-fade) | findings/t3_pop_fade (table 3) | the secondary buyer's UPSIDE OPPORTUNITY barely fades across pop buckets even where the ENDPOINT does (MB: 63–76% ever touch +20% across all buckets, but only 36–50% end positive) → the fade is a timing/discipline tax, not a vanished opportunity. Descriptive (T3 within-vintage WEAK). |
| mv-exit-backtest | Take-profit ladder vs buy-and-hold | strategy | backtested | backtest/analyses.exit_discipline_backtest | take-profit (+20/+50/+100%) NEVER beats buy-and-hold cross-regime (0 cells beat hold in BOTH cohorts); capping the upside sacrifices the right tail. SL-only stop-loss similarly never beats holding. Combined TP+SL is NOT backtestable (MFE/MAE can't reveal which fired first — disclosed). |
| f-partial-exit | Partial exit ('sell half') paradox | descriptive | **HEADLINE (both cohorts)** | findings/f_partial_exit | selling half at +T ALWAYS lifts the MEDIAN but SACRIFICES the MEAN wherever a right tail exists (SME/longterm 3y: median −2%→+22% but mean 104%→79%). It's a median-vs-mean trade, not a free lunch — converts a tail-harvester into a typical-name harvester. |
| f-basket-barbell | Buy-every-IPO basket is a barbell | descriptive | **HEADLINE (both cohorts)** | findings/f_basket_dispersion | in every segment×cohort the MEDIAN is at/below ~0 and ≤~50% end positive; the mean is a top-5% mirage (strip them → SME/longterm 3y 104%→45%). Report the distribution, never the mean; never concentrate. |
| f-lifecycle | When does the IPO peak? (timing) | descriptive | reported | findings/f_lifecycle | the median IPO peaks ~108 days into year 1 and ~half the 1y high is in by the first quarter — the move is front-loaded, the rest is the holder's tax (the timing behind 'sooner-is-better'). Descriptive (you only know the peak in hindsight). |
| n13-fallen-angel | Fallen-angel recovery is unpredictable | predicate | **VALIDATED-NULL (cross-regime)** | findings/n13_fallen_angel | among names ≤−50% in yr1, recovery is 16–47% and NO pre-listing feature (profitable/low-debt/high-ROE) predicts WHICH recover in a sign-stable way (the one near-stable signal — large fallen issues recover LESS — is the opposite of the thesis). Negative rule: don't pay up for 'cheap after the fall'. |
| n9-deadmoney | SME's real risk = dead money, not −100% | descriptive | **HEADLINE (SME cross-regime)** | findings/n9_zombie | dead money (alive, <−50%, illiquid) dwarfs confirmed wipeout for SME (boom 17.8% vs 1.1% = 16×; longterm 12.7% vs 8.5%), inverting MB (wipeout dominates). And the zombie DID give a yr-1 exit (51% of dead SME traded +20% from issue) then the thin float closed it → in SME, treat the first-year peak as the exit. |
| n14-wipeout-anatomy | Anatomy of a wipeout (pre-listing flags) | predicate | reported (partial cross-regime) | findings/n14_wipeout_anatomy | VALIDATED pre-listing flags: tiny pre-IPO sales (<25cr) + loss-making at IPO (PAT≤0). Additive red-flag count sorts SME-boom bad-outcome 14.6%→46.4%. REJECTED: micro market-cap (reverse-causation — current mcap is tiny BECAUSE it crashed). NOT robust: high debt, accrual, valuation. REVERSE: high OFS is protective. |
| reject-contrarian-entry | 'Buy the discount lister' (secondary) | entry-signal | **REJECTED (sign flips by cohort)** | (not built — documented null) | listing-day gain carries NO actionable secondary-buyer signal: discount-vs-pop forward returns flip sign across boom/longterm. T3 pop-fade is about the ALLOTTEE's issue-anchored decay, not a tradable secondary edge. Don't pay up to avoid 'weak' listers or chase 'hot' ones. |
| n15-clean-compounder | Low-debt × high-ROE (the one validated interaction) | predicate (interaction) | **VALIDATED (cross-regime, separate layer)** | findings/n15_clean_compounder | the ONE combination that cleared super-additive + cross-regime: neither low-debt nor high-ROE alone escapes a deep-negative base, but TOGETHER they're the best cohort everywhere (MB/longterm base −43% medα→ BOTH +1%; SME/boom →+91%; multibagger 19%→37%). 'Clean compounder' = real ROE not debt-juiced. Separate layer, not in the score (yet). |
| f-flip-trap | The flip trap (hot IPO = big pop, tiny allotment) | strategy | reported — **boom-only** | findings/f_flip_trap | pop and allotment are mechanically inverse → expected capture PER APPLICATION is flat-to-tiny (~0.2–0.6%) across subscription buckets, often LOWEST for the hottest >50x names despite ~100% pop-positive. The pop is a selection illusion you can't size into. (Identity mechanism; boom-only data.) |
| f-average-down | Averaging down rarely recovers ('what NOT to do') | descriptive | reported | findings/f_average_down | among names that fell to −30/−50% in-horizon, only 4–17% (1y) end back above entry; the 2nd tranche bought at the dip is itself a median LOSER in both cohorts at 1y. The dip is information, not a discount. (SME/boom 3y is the lone winner — boom tide, not robust.) |
| risk-gauge | Standalone wipeout-risk gauge (per-IPO) | predictor-aux | built — **separate from the return score** | predictor/scorecard.risk_assessment | a per-IPO 0–100 risk read (50=segment-typical) from the validated flags + the historical fail-rate at the query's flag-load, with per-flag with/without base rates. Shown always; NOT folded into the return score (risk ≠ return; OOS test is the gate). |
| strat-flip-listing | Flip at listing (allottee) | strategy | backtested | backtest/strat_flip_listing | raw median ≈ +5–7%, ~70% win — BUT allotment + adverse-selection gut the real EV |
| strat-hold-1y | Buy at listing, hold 1y/3y (secondary) | strategy | backtested | backtest/strat_secondary_hold | LOSES cross-regime (MB median alpha −16.8%/1y, −51.6%/3y). SME 3y is MIXED (boom +6.8% vs longterm −40.9%) — a regime effect, not an edge. Naive IPO-buying doesn't beat the index. |
| strat-buy-filtered | Secondary + Tier-1 filter (profitable & OFS≥25%, both pre-listing-known) | strategy | backtested | backtest/strat_secondary_filtered | **CORRECTED (B/C review):** the filter REDUCES the loss (MB 1y mean +5.9% vs −2.3%, median −9.1% vs −16.8%) but median alpha stays NEGATIVE → still "loses (cross-regime)". The earlier "+28% SME beats do-nothing" was a small-N, single-regime, look-ahead artifact (liquidity gate removed; verdict now cross-regime). "Reduces downside", NOT "beats the index". |
| strat-avoid-hot | Secondary, skip >25% listing pop | strategy | backtested | backtest/strat_secondary_avoid_hot | no improvement over unfiltered secondary_hold; loses cross-regime |

> Combined predictor score = weighted blend of `score-*` (preset profiles in scorecard.PRESETS; data-informed
> weights from strat-* backtest lift are the next step). See `docs/layer3.md`.
>
> **Cross-regime validation (`layer3/validate.py` → `run_validation.py`):** ran 2026-06-01.
> **VALIDATED (sign holds in boom AND longterm):** desc-lasting-wealth (MB underperforms), pred-pop-fade (big pop →
> worse secondary forward return). **MIXED (sign flips → regime effect, NOT robust):** pred-ofs-skin, pred-profitable-ipo
> (both also small-N — do not trust as standalone signals). **insufficient N:** pred-size-survival (MB). **single-regime:**
> n2-subscription. Lesson: only 2 of the directional claims are regime-robust; the rest are `reported`, not `validated`.
> **Data-informed scorecard weights (`layer3/predictor/weights.py` → `run_weights.py`):** ran 2026-06-01 over 1,241
> point-in-time-scored matured IPOs. Cross-regime rank-IC vs realized 3y alpha: return-potential (boom .15/long .26),
> multibagger-odds (.15/.23), downside-safety (.12/.25) are all positive in BOTH regimes → weights ≈ 0.35/0.33/0.33.
> liquidity (.05/−.01) and quality (−.04/.07) FLIP sign → weight 0. Used via `predict_ipo.py --profile data_informed`.
> Lesson: the analog-cohort-derived components predict (modestly, consistently); the query's own fundamentals don't.
>
> **V2 verification round (2026-06-01) — fixed, important:** the point-in-time scoring had a LOOK-AHEAD (read analogs'
> fully-matured outcomes, ~33% of which completed after the query listed) → now gated so an analog only counts if its
> horizon finished before the query listed. This DEFLATED the headline: combined-score pooled lift +38pp → +11pp;
> weights are in-sample-fit (not OOS); the validated quality/debt flags are SHOWN but get 0 weight under data-informed
> (so they don't move that combined score — disclosed in the predictor output). Treat the score as in-sample/indicative.
>
> **V3 review round (2026-06-01) — movement-lens code, adversarially reviewed + remediated:** the core machinery
> (stop-loss math, maturity-gating/no-look-ahead, monotonicity, tradeable_upside weight-0, the cross-regime "no exit
> rule beats hold in both cohorts") all held up. FIXED: (1) `exit_discipline_backtest` computed the buy-and-hold
> baseline on a LARGER sample than the rule (endpoint-only vs endpoint+MFE; up to a 40% N gap biased toward older/
> weaker names) → now both share the `mfe & endpoint` mask. (2) step-07 MFE/MAE had NO upper-coverage guard → a
> name whose price series ended before the horizon got a TRUNCATED-window peak/trough → now gated on `end <= data_last`
> (or delisted), matching the endpoint guard; window also lower-bounded at `>= listing_date` (truncated non-delisted
> rows → 0). PLUS a final INVARIANT CLAMP in step 09 (peak>=endpoint>=trough on the assembled columns) — root cause
> was `remediate_listing` rescaling RETURNS by an inferred split factor AFTER MFE/MAE were computed (so MFE was on a
> different price scale); the clamp floors MFE/MAE at the canonical return for ~75 split-remediated rows (flag
> `mfe_mae_clamped`, the known scale-inversion subset), conservatively understating their upside, never overstating.
> Invariant violations now 0/2296. (3) `multibagger_odds` ever-2x
> vs ended-2x now on ONE denominator (guarantees touched≥ended). (4) scorecard listing-anchored components now exclude
> `unreliable_coverage`. HONESTY: the secondary-buyer "100% ever gave an exit / break-even mean 0.0%" is a listing-day
> tautology (the listing day is in-window) — now explicitly caveated in M1 + the app (only the +profit targets are
> informative for the secondary buyer). Verdict: sound to ship after these fixes.

## Context-signal verdicts (2026-06-06 — docs/research/context_signals_verdict.md)
- **ctx_ipo_heat_90d (crowded IPO window)** — DISPLAY-ONLY, fold-candidate: negative in all 4 regime
  cells (IC −0.13…−0.26; tercile spread −16…−29pp). In-score pending an OOS fold test.
- ctx_nifty_mom_3m — REJECTED (IC ≈ 0 everywhere).
- ctx_heat_pop_90d / ctx_sector_heat_180d — REJECTED (sign flips across cells).
- SHORT score (GMP+subscription percentiles) — REJECTED (33→39% sliver on train; inverted on the 2026
  holdout; high-short names have NEGATIVE 1y). The LONG score is the better short-horizon predictor.
- "Hot pop then fades" — NOT SUPPORTED: first-month strength PERSISTS (hot 25-60% → +14% MB / +30% SME
  at 1y; cold → −11%/−15%). m2 lens: drift after month 1 ≈ flat; P(1y<1m) ≈ coin flip.

## Hypothesis batch 2026-06-06 (48 agent-generated; docs/research/hypothesis_batch_2026-06-06.md)
- **FOLDED: crowded_window** (5/5 OOS splits improved, +10..+56pp; weight 0.254 in data_informed).
- **ROBUST CONDITIONING (not in score): path_ratio_1m** — month-1 up/down asymmetry predicts the year
  (IC +0.23..+0.49 all 4 cells); the persistence rule for hold/exit decisions.
- REJECTED (mixed/thin across regime cells — do not re-test without new evidence): band_position,
  anchor_ratio/has_anchor, fixed_price, promoter_dilution_pp, size_z, min_investment, all_ofs,
  banker_prior_alpha, nii_froth, gmp_sub_disagree, gmp_z, undersubscribed, demand_per_size,
  breadth_hot_count, qib_cold_retail_hot, sales_accel_spike, cf_conversion, borrow_ramp, opm_trend,
  sales_vs_asset_growth, fresh_dilution, profitable_stagnant, objects_debt_repay, lday_close_position,
  lday_green, lday_giveback, volatility-early, circuit_lock, days_to_peak (mechanical),
  turnover_to_size (look-ahead).
- WATCHLIST: pe_vs_sector (MB-only lean-negative, −43pp spread; blocked on SME PE data),
  qib_retail_ratio (lean-positive, display-only candidate).

## Tier-1 wave-1a verdicts (2026-06-06 — docs/research/tier1_wave1_verdicts.md)
- T2f vintage: YEAR > regime 4/4 cells — regime does not subsume vintage; year stays the gate.
- F3 regime-gated junk bounce: FALSIFIED on demand-proxy (placebo failed both segments; TP delta ≈0).
  One PIT-score re-test permitted later.
- F1 anchor-unlock day-30/90 dip: FALSIFIED — placebo inverted (pre-2022 more negative than
  treatment), dose-response wrong sign, dip-buy loses (38% win). No Indian replication of the
  US lockup-expiry effect. Calendar = information only, no edge chip.

## Wave-1b verdicts (2026-06-07 — docs/research/tier1_wave1_verdicts.md)
- REJECTED: F2a neglected-member (zero fwd catch-up, swept W), F2b tone-setting (shared GMP),
  F8 unfilled-demand (inverted), F6b/F6c/F6d GMP-interaction/regime/T+3, F5b LDH-breakout trade
  (+ look-ahead trap in fail-classification recorded).
- VALIDATED-DIRECTIONAL: **F7 disposition contagion** — cold-tape listers +7.6pp over hot-chase at 3m
  (chase +0.454, tax −0.088 Nifty-controlled). Pending cross-regime + OOS fold before any score role.
- MECHANISM-ONLY: F2d retail-specific congestion tax (supports crowded_window); F2c SME demand fatigue.
- DISPLAY-WATCH: F6a GMP-surprise (weak lean).
- NEW QUEUED: F9 copycat decay, F10 early corp-action tells, F11 serial promoters (gated), F12 retail
  P&L climate index (priority — may upgrade crowded_window).

## Wave-2 part-1 verdicts (2026-06-07)
- **F7 disposition contagion: VALIDATED CROSS-REGIME (4/4 cells, +2.6..+18.2pp) + OOS-directional.**
  Queued: fold test as climate component (may upgrade crowded_window).
- REJECTED: F12 size-weighted climate (median-pop wins), F9 copycat decay, F4 bear-window stop-loss
  (stops lose even in bears), T2b, T2c (thin), T2e, T2g banker collision, T2h ASBA echo (sign opposite
  — supports congestion tax), T2j circuit-cage (inconsistent).

## Wave-2 part-2 verdicts (2026-06-07) — PHASE-2 RESEARCH PROGRAM COMPLETE
- **⭐ F5e capitulation flag: VALIDATED CROSS-REGIME, NO LOOK-AHEAD — display-only red flag.**
  Never closed above issue in td 1–90 (12% of IPOs) → bad-outcome 55% vs 13%; INCREMENTAL to N14
  at every flag count (+39/+44/+45pp); post-flag fwd-1y alpha gap negative in all 4 cells
  (−7.5..−32.7pp). The day-90 portfolio checkpoint flag. NOT in score (post-listing signal).
- **⭐ F10 early corp-action tell: validated-THIN (n=31) — display-only EXIT flag.** Bonus/split
  within yr 1 (after median +184% run-up) → fwd-3m −22.2% win 16% vs matched controls +2.2% win 55%.
  Marks the TOP, not a bad company (their alpha_1y is still above average). Revisit as N grows.
- **F7 fold test: 1/5 splits — NOT in score.** F7 = 3m timing signal; 1y/3y selection horizons
  don't capture it (crowded_window already holds the long-horizon climate seat). Stays VALIDATED
  display ("hot tape = wait, cold tape = engage"). Score remains 8 components.
- **F3 closed: REJECTED on PIT re-test** — bull-gate flips across cohorts (boom bull>bear;
  longterm bear>bull); junk terminal alpha negative everywhere.
- REJECTED: F5a issue magnet (placebo-identical: 33/65 vs 37/62 clear/reject; dose OPPOSITE —
  momentum not anchor; touch-buy dead money), F5f round numbers (flat tiers), F5c volume-confirmed
  reclaim (INVERTED: confirmation volume = distribution; fwd −3.0% vs −1.4%), F5d ordering
  (mechanical), T2i flipping (INVERTED: day-1 turnover = demand, IC +0.103 pop-controlled, placebo
  clean), T2a day-180 unlock (weak ~1–2%, attribution unclean, ≈costs).
- Gated remainder: F11 serial-promoter fingerprints (needs entity-matching infra — a build).

## Swing-trade take-profit (2026-06-08, owner idea — REJECTED, definitive)
- ENTRY listing close, SELL first close >=+20% else hold 1y, vs buy-and-hold. Take-profit lifts
  WIN-RATE (67% vs 46%) + median (+21% vs −7%) but CUTS MEAN (+1% vs +41%) and P90 (+28% vs +140%)
  — negative Δmean in all 4 regime cells (−9.7 / −47.2 / −36.9 / −51.1pp). Conditional good-entry
  (month-1 strong) makes holding MORE valuable (hold mean +104%). The right tail carries IPO
  returns; take-profit decapitates it. Bot will not emit sell-at-X calls. See future_ideas.md.

## Thread C verdicts (2026-06-08)
- **pe_vs_sector: WATCHLIST → DISPLAY-ONLY** (both segments, boom). Rich issue-time P/E vs sector
  median underperforms: SME −48.9pp/IC−0.245 (n=68), MB −13.1pp (n=161). NOT in score — SME is
  boom-only (no longterm P/E data) so it fails the cross-regime gate. Placebo: 1000x shuffle
  p=0.019 (SURVIVES the falsifier) — real, not noise; still display-only (n=68, no cross-regime).
  h2_pe_vs_sector_sme.py.
- **accruals (Modified-Jones DCA): DATA-GATED** — needs receivables + CFO (not in substrate). Parked.
- **SME→MB migration: DATA-GATED** — needs a migration-date source (Chittorgarh r123/BSE/NSE). Parked.

## Thread C round 2 (2026-06-08) — 3 new hypotheses, ALL REJECTED (graveyard)
- margin-expansion-vs-sales-growth (opposite + regime sign-flip) · sales-accel×demand-divergence
  (suggestive +7.1pp but FAILS shuffle placebo p=0.156, boom-only) · same-banker-pipeline-congestion
  (+0.2pp null). threadC_new_hypotheses.py. Do not re-test without new data/framing.
