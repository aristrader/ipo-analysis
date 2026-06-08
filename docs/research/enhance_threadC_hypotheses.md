# Thread C — Expanded hypothesis space (NEW, second-order, current-data-testable)

_Generated 2026-06-08. Bar (per hypothesis_protocol §1): INTERACTIONS / SEQUENCES / REGIME-CONDITIONS /
CROSS-IPO mechanics with a stated MECHANISM — not first-order screens. Every candidate below was
cross-checked against `rules/index.md` (full registry, ~100 verdicts) and is **confirmed not already
tested** in the form stated. Uses ONLY substrate columns we hold. Min-N floors per §3._

## Why these are open (the gap I'm exploiting)
The graveyard kills almost every *single-snapshot* and *single-feature* idea. But three rich seams are
barely touched: (1) **financial TRAJECTORY** — we hold `net_sales/pat/operating_cf/borrowings/total_assets
_yr1..3`, yet every fundamentals test used only the latest snapshot or a binary flag; trend/acceleration
is unmined. (2) **CROSS-IPO sequence by shared agent** (same lead manager / same week), as an INTERACTION
with the IPO's own demand — not the rejected banker→alpha main effect. (3) **PATH × FUNDAMENTAL conditioning**
— `path_ratio_1m` is robust alone; whether fundamentals *change its meaning* is untested.

## Ranked shortlist (mechanism × feasibility × not-yet-tested)

| # | Hypothesis (predicate) | Mechanism (whose money / why) | Columns | Falsifier | X-regime? |
|---|---|---|---|---|---|
| 1 | **Sales-acceleration × demand divergence.** Among HIGH-subscription IPOs, those whose 3-yr sales growth is DECELERATING (yr3/yr2 < yr2/yr1) underperform at 3y vs accelerating ones; LOW-demand names show no such split. | Hype funds the book on a *story*; when the growth curve is already rolling over, post-listing earnings disappoint the marginal momentum buyer who chased subscription, not numbers. Interaction: demand only "costs" you when fundamentals can't follow through. | net_sales_yr1..3, sub_total_x, alpha_3y, type, cohort | Decel−accel 3y-alpha gap is <5pp OR flips sign across the 2 cohorts (subscription is boom-only → test demand-tertile within each cohort separately) | Boom-only on the demand leg (longterm sub≈0) → run the **growth-trajectory leg cross-regime**, demand-interaction boom-only |
| 2 | **Banker pipeline congestion (same-LM cluster).** When a lead manager brings ≥2 IPOs within 30 days, the LATER one in the cluster underperforms its own demand-implied expectation vs that LM's solo issues. | A banker's distribution desk + anchor relationships are a finite wallet; back-to-back books split the same institutional demand, so the trailing deal is priced/placed into a depleted channel. Cross-IPO, agent-mediated — NOT the rejected `banker_prior_alpha` main effect. | lead_manager, open_date/listing_date, sub_total_x (residualize), alpha_1y/3y | Clustered-later vs solo alpha gap <4pp OR not monotone in cluster size OR vanishes after controlling for the market-wide crowded_window (must be INCREMENTAL to crowded_window, which is already folded) | Cross-regime (LM + dates fully populated both cohorts; 58 LMs ≥10 IPOs) |
| 3 | **Margin-expansion vs sales-only growth.** IPOs growing sales WITH expanding operating margin (op_profit/sales rising yr1→yr3) beat equal-sales-growth peers whose margin is flat/falling, at 3y. | Sales growth bought with margin erosion = discounting/channel-stuffing to dress the pre-IPO window; quality growth (operating leverage) is hard to fake and persists. A trajectory refinement of n7 (which used snapshot margin only). | net_sales_yr1..3, operating_profit_yr1..3, alpha_3y | Margin-expanding vs margin-eroding gap <5pp within matched sales-growth tertile, OR sign flips across cohorts | Cross-regime |
| 4 | **Leverage-ramp into the IPO.** Firms whose borrowings/total_assets ROSE yr1→yr3 pre-listing (levering up just before raising equity) underperform de-levering peers; effect concentrates where fresh-issue objects ≠ debt-repayment. | Pre-IPO leverage ramp = stressed balance sheet using the IPO as a bailout; the equity buyer inherits the workout. Trajectory version of the snapshot debt/equity flag (n7, "not yet x-regime"). | borrowings_yr1..3, total_assets_yr1..3, ofs_pct, alpha_3y, outcome_class | Levering-up vs de-levering 3y-alpha gap <5pp OR not present on the high-N SME panels (the debt-flag's known failure mode) | Cross-regime |
| 5 | **Path-meaning flips on quality.** `path_ratio_1m` (month-1 up/down asymmetry, already robust) predicts the year — but its slope is STEEPER for loss-making/tiny-sales names than for clean compounders (strong path in a junk name = a pump that mean-reverts; in a quality name = real demand that persists). | Same price-path, different information content depending on the fundamental anchor. Conditions an already-validated signal — a NEW interaction, not a re-test. | mfe_lst_1m/mae_lst_1m (→ path ratio), pat_ttm_cr, sales_ttm_cr, alpha_1y | Path-ratio IC is NOT higher in the junk subset than the quality subset in ≥3 of 4 cells, OR difference <0.10 IC | Cross-regime (mfe/mae_lst_1m N=2331) |
| 6 | **Anchor-conviction × demand disagreement.** High anchor-allocation-% but TEPID retail/NII subscription = "smart money in, crowd out"; predict this combo beats high-anchor-high-demand at 3y (less froth to unwind). | Anchors do diligence and lock in; when they commit but the crowd doesn't chase, there's no momentum overhang to fade. Interaction of two signals each weak alone (n5 anchor%, demand). | anchor_allocation_cr, issue_size_cr, sub_retail_x/sub_nii_x, alpha_3y | Smart-in-crowd-out vs hot-hot 3y gap <5pp OR sign flips boom-only (anchor disclosure thin pre-2022) | Boom-MB primarily (anchor coverage 897 rows) |
| 7 | **Asset-turnover collapse tell.** Falling sales/total_assets yr1→yr3 (capital piling up faster than revenue) flags pre-IPO over-investment; predict higher dead-money/wipeout, esp. SME. | Building capacity/inventory ahead of revenue that never arrives = the SME zombie profile (n9 dead-money) seen *before* listing rather than diagnosed after. | net_sales_yr1..3, total_assets_yr1..3, outcome_class, type | Turnover-collapse tertile wipeout/dead-money rate ≤ middle tertile OR not monotone | Cross-regime |
| 8 | **Pricing-tightness × demand.** IPOs priced at the TOP of a wide band (price_band_low vs issue_price) AND heavily subscribed underperform vs top-priced-but-cool names — aggressive pricing only bites when the crowd validated it. | Issuer extracts max price when demand is hot, leaving nothing for the secondary buyer; a tight/discounted price into hot demand leaves money on the table that drifts up. | price_band_low, issue_price, sub_total_x, alpha_1y/3y | Top-priced-hot vs top-priced-cool gap <4pp OR not present | Boom-only (band + sub coverage ~886) |

## Cross-check note
None of #1–8 appears in the registry in this form. Closest neighbours and why these are still NEW:
`sales_accel_spike` (REJECTED) was a single-feature spike screen, NOT the **demand-interaction** of #1.
`banker_prior_alpha` (REJECTED) was a main effect, NOT the **same-LM congestion sequence** of #2.
`opm_trend` (REJECTED) was a standalone margin-trend screen, NOT **conditioned on matched sales growth**
(#3). `borrow_ramp` (REJECTED) was a standalone ramp screen, NOT **gated on debt-repayment objects /
de-levering contrast** (#4). `path_ratio_1m` is validated as a main effect — #5 tests whether it's
**fundamentally conditioned** (new). n5-anchor and demand are tested alone — #6 is their **interaction**.

## TOP 3 TO RUN (best mechanism × feasibility × novelty)
1. **#3 Margin-expansion vs sales-only growth** — fully cross-regime, high N (≥100/cell), cleanest
   mechanism (operating leverage is hard to fake), refines a signal (n7) that already half-works.
2. **#1 Sales-acceleration × demand divergence** — strongest second-order story (hype unbacked by the
   growth curve); growth-leg cross-regime, demand-interaction boom-only but high-N.
3. **#2 Banker pipeline congestion** — genuinely cross-IPO + cross-regime, data fully populated, and
   must prove INCREMENTAL to the already-folded crowded_window (a sharp, falsifiable bar).
