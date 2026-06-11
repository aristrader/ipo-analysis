# Backtester — improvement ideas (THINK + PROPOSE, no code yet)

Scope: extend `layer3/backtest/engine.py` + `score_backtest.py` honestly. Bar = point-in-time,
net of costs, allotment-realism honest, beats do-nothing, computable from our DAILY-summary data
(no intraday/path timing), non-duplicative, not overfit. SME/MB never pooled; cross-regime verdict.

## Data we actually have (verified, equity rows)
- Full horizon grid `return_from_issue_* / return_from_listing_* / alpha_* / alpha_sc_*` for
  1d,1w,1m,3m,6m,1y,2y,3y,5y,10y. alpha_* (vs Nifty) well-populated (1y≈1867, 3y≈1272); alpha_sc_*
  (Smallcap250) **2017+ only & thinner** (1y≈1262, 3y≈670).
- `max_drawdown_pct`, `max_gain_pct`, `all_time_high/low` — path EXTREMES, **no timing/sequence**.
- `sub_total_x` (oversubscription) **boom-only** (≈1169 ≈ boom N; longterm sub≈0).
- `median_daily_turnover_inr`, `volatility_annual`, `liquidity_flag`, `market_cap_class`, `broad_sector`,
  `listing_date`, `issue_size_cr`. No intraday, no allotment actuals, no weekly path in the summary.

## Top BUILD picks (lead with these)
1. **Holding-period sweep** — exit-horizon table per existing strategy.
2. **Portfolio-level equity curve + risk-adjusted metrics** (equal-weight basket vs do-nothing curve).
3. **Flip allotment-realism EV** (proper 1/oversubscription × adverse-selection calc; boom-only).
4. **Smallcap-250 benchmark for small/micro** secondary strategies (alpha_sc, the honest benchmark).
5. **Drawdown-band reporting** on portfolio strategies (max_drawdown_pct distribution, clearly "extreme not path").

---

## Prioritized table

| # | idea | what it tests | honest + computable? | effort | recommendation |
|---|------|---------------|----------------------|--------|----------------|
| 1 | **Holding-period sweep** (1m/3m/6m/1y/2y/3y/5y) per strategy | When to EXIT — does median alpha peak then decay (pop-fade implies early exit)? | YES. Point-in-time (exit horizon is a rule, not look-ahead). Each horizon maturity-gated separately; honest cohort-swap caveat (long horizons lean longterm). Pure reuse of existing alpha_* grid. | LOW | **BUILD.** Highest value/effort. Turns 1 number into the exit-timing curve; directly answers "hold or sell". Non-dup (engine currently hard-codes 1y/3y only). |
| 2 | **Portfolio-level basket** (equal-weight buy-all-eligible) + equity curve, Sharpe/Sortino-lite, portfolio max-drawdown | What an investor ACTUALLY earns deploying across the cohort, vs the per-IPO median we show now (which ignores that you hold many at once). Baseline = same-period index curve. | YES with care. Compute per-IPO alpha, equal-weight average = basket alpha; report distribution + worst-decile. **Sharpe/Sortino must use cross-IPO dispersion at a fixed horizon (a one-shot dispersion ratio), NOT a time series** — we have no rebalanced monthly series. Label it "cross-name dispersion-adjusted", not annualized Sharpe, to stay honest. | MED | **BUILD** (the dispersion-adjusted version). Median-per-IPO overstates realism; basket is what you can deploy. SKIP any "annualized Sharpe from a monthly equity curve" — we lack the path. |
| 3 | **Flip allotment-realism EV** | The flip's REAL expected value: retail allotment prob ≈ min(1, 1/sub_total_x), and adverse selection (hot IPOs over-subscribe → you get fewer of the winners). Compute EV = Σ p_allot(i)·gain(i) / Σ p_allot(i), vs the naive equal-weight flip we report now. | YES, **boom-only** (sub_total_x is boom-only). Honest: state it's a retail-RII approximation, lottery is per-application not pro-rata so model as allotment-probability weight. This makes the existing "ignores allotment" caveat QUANTITATIVE. | MED | **BUILD** (boom-only, clearly scoped). Directly delivers the honesty the doc demands; converts a hand-wave caveat into a number. Don't extend to longterm (no sub data). |
| 4 | **Smallcap-250 benchmark for small/micro** secondary strategies | Are small/micro IPOs really losing, or just losing vs the wrong (large-cap Nifty) benchmark? Re-run secondary_hold/filtered using alpha_sc_* for mcap∈{micro,small}. | YES — alpha_sc_* exists, and benchmark policy (`spine.benchmark_for`) already prescribes this. **Caveat: 2017+ only**, so it's a boom-weighted / partial-longterm read; report N + the coverage gap. | LOW-MED | **BUILD.** Fixes a genuine benchmark-mismatch bias (currently all secondary alpha is vs Nifty). Low effort (helper + column swap). Just gate honestly on coverage. |
| 5 | **Drawdown-band on portfolio/strategy** (distribution of max_drawdown_pct for held names) | "How much pain en route" for a strategy's holdings — the risk side of risk-adjusted. | YES but **caveat hard**: max_drawdown_pct is the all-time extreme over full history, NOT path-to-horizon and NOT sequence. Report as "worst peak-to-trough ever observed (extreme, untimed)", a risk texture, not a tradable stop level. | LOW | **BUILD** as a reporting column on #2, not a standalone strategy. Honest only if labeled "extreme, untimed". |
| 6 | **Size/sector-filtered secondary** (from N4 issue-size, T6 sector) | Does restricting to a size band / surviving-sector beat unfiltered secondary cross-regime? | Computable. **Overfit risk: HIGH** if free-form (many bands × sectors × horizons → cherry-pick). Honest only if the filter is fixed a-priori from an already-VALIDATED finding and verdict is cross-regime. T6/N4 are `reported`, NOT validated, so a sector strategy would be fishing. | MED | **MAYBE.** Build ONLY the issue-size-band cut (N4, one pre-registered band) with strict cross-regime + min-N; SKIP per-sector strategies (too many d.o.f., not validated, overfit-prone). |
| 7 | **Stop-loss / take-profit approximation** via max_drawdown / ATH | "Would a −20% stop or +50% take-profit have helped?" | **Computable only as a crude bound, NOT a real backtest.** We have no path/sequence, so we cannot know if the stop hit BEFORE the take-profit, or whether drawdown preceded recovery. Any number here invites a false "stops work" conclusion. | MED | **SKIP** (or at most a one-line "we cannot test path-dependent exits — daily summary lacks the within-horizon sequence"). The doc's honesty bar kills this; an approximated stop-loss is exactly the fragile/misleading thing to avoid. |
| 8 | **SIP-into-IPOs vs lump** | Does spreading entries over time beat lump deployment? | Computable in principle (bucket by listing_date, deploy equal cash per period) but it mostly **re-measures vintage/regime timing** (trap #1: vintage=regime collinearity) — "SIP wins" would just say "boom came after the lull". Adds little over the cohort split we already show, and risks a spurious timing story. | MED | **SKIP.** Conflates strategy with macro-timing; the cross-regime split already exposes the regime dependence more honestly. |
| 9 | **Turnover / capacity limit** (can you deploy ₹X given median_daily_turnover_inr?) | Realism cap: a strategy that needs illiquid SME names can't absorb real capital. | Computable (median_daily_turnover_inr exists). But largely **duplicative** of the existing `liquidity_flag` investability gate, and capacity is a footnote not a strategy. | LOW-MED | **MAYBE / footnote.** Add as a one-column "median turnover of held names + a deployable-₹ note" on the portfolio table, not a separate strategy. Useful honesty, low novelty. |
| 10 | **Do-nothing baseline as explicit equity curve / row** | Make the break-even benchmark a literal row (alpha=0 line, raw=index return) in every table instead of implicit. | YES, trivial, and it sharpens every comparison. | LOW | **BUILD** (folds into #2 as the baseline series; cheap honesty win). |
| 11 | **Drawdown-adjusted return (Calmar-lite)** = median alpha / median max_drawdown | Risk-adjusted ranking across strategies. | Computable but the denominator is the untimed extreme (see #5) → a "Calmar" label would overstate rigor. | LOW | **MAYBE.** Only as a clearly-labeled "alpha-per-unit-of-worst-drawdown (untimed)" texture metric on #2; do not call it Calmar/Sharpe. |
| 12 | **GMP-based entry filter** | Does buying only high-GMP IPOs help? | **SKIP** — GMP is quarantined from scores by decision (trap #3, dirty input) and is boom-only. Would violate an existing rule. | — | **SKIP.** Explicitly out of bounds. |

## Honesty notes that must travel with the build
- **No path/sequence data** → no genuine intra-horizon stop-loss/take-profit, no annualized Sharpe from
  an equity-curve time series. Anything risk-adjusted is a *cross-name dispersion* or *untimed-extreme* statistic — label it so.
- **alpha_sc_* is 2017+** → smallcap-benchmarked strategies are boom-heavy; report coverage N and don't claim a clean cross-regime read.
- **sub_total_x is boom-only** → allotment-EV is a boom retail approximation; lottery allotment is per-application, model as a probability weight, state it.
- **Filtered/size/sector strategies** must be pre-registered from an already-validated finding and judged cross-regime, or they're fishing (conditioning-collapse + overfit, traps #2).
