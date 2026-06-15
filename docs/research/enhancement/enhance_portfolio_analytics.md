# Enhancing the portfolio sim + were-we-right scorecard — analytical depth

Lens: statistical rigour within the no-ML, honest-uncertainty ethos. For each item: WHAT · pure-Python/numpy HOW
(no scipy/statsmodels) · feasible from current data? · effort · the honesty guard. NON-recommendations called out.
Current state: `layer3/portfolio.py` (per-position frame, sum-of-values mult, win_rate, median_mult, matched-Nifty
basket) + `layer3/calibration.py` (Wilson, Brier stub, scorecard, score_reliability). Indices on hand:
nifty50 (full) + niftysmallcap250 (2017+ only). Ledger logs `score`/`alpha_1m/3m/1y` but NO predicted prob yet.

## PORTFOLIO

### 1. Outlier-decomposition of the 2.09x (distribution, not the sum) — **TOP**
- WHAT: the sum-of-values mult is dominated by a few multibaggers. Show median position mult (already computed!),
  P10/P90, top-3 positions' share of total terminal value, and the mult with the single best name removed.
- HOW: numpy/pandas quantiles on `secondary_val`; `sorted(vals)[-3:].sum()/total`; recompute mult dropping argmax.
- FEASIBLE: yes, the per-position frame already exists. EFFORT: S.
- GUARD: report N and the matched basket; never hide that the mean is outlier-driven — that IS the insight.

### 2. Bootstrap CI on the portfolio multiple — **TOP**
- WHAT: a 90% confidence band on the equal-weight mult, so 2.09x isn't read as precise.
- HOW: pure-Python resample-with-replacement of the per-position mults (`random.choices`, B=2000), recompute the
  equal-weight mult each draw, take the 5th/95th percentiles. No scipy needed.
- FEASIBLE: yes. EFFORT: S. GUARD: fix a seed (reproducible); state B and that it captures sampling, not
  model, uncertainty; suppress band if N<12 (min-N floor from the protocol).

### 3. Per-position attribution table — **HIGH**
- WHAT: rank positions by ₹-contribution to terminal value; show name, entry lens, mult, ₹ contributed, alpha vs
  its own-period Nifty. Answers "what actually drove the result".
- HOW: trivial sort/groupby on the existing frame. FEASIBLE: yes. EFFORT: S.
- GUARD: show wipeouts (₹0) explicitly so survivorship isn't masked; tag mode.

### 4. Benchmark robustness vs Smallcap250 (2017+) — **HIGH**
- WHAT: IPOs are small-caps; Nifty50 is an easy benchmark. Re-run the matched-basket vs-benchmark mult against
  Smallcap250 for positions whose listing ≥2017.
- HOW: add a `_smallcap_at()` twin of `_nifty_at()`; second benchmark column; matched basket per benchmark.
- FEASIBLE: yes but PARTIAL — index only starts 2017-04, so longterm-cohort calls have no smallcap leg.
  EFFORT: M. GUARD: label coverage ("Smallcap250 basket: N of M positions"); never extrapolate the index back.

### 5. Time-weighted return / CAGR by realized holding period — **MEDIUM**
- WHAT: positions have wildly different hold lengths (delisted-stale vs live). Annualise: per-position CAGR =
  mult**(365/hold_days)−1, then summarise the distribution; report alongside the raw mult.
- HOW: hold_days = exit_date − listing_date (both already available in `_exit_price`); pure arithmetic.
- FEASIBLE: yes. EFFORT: M. GUARD: CAGR on <~90-day holds explodes — floor the holding period or show it as a
  distribution with a min-hold filter, never a single pooled CAGR.

### 6. Max drawdown of the portfolio equity curve — **MEDIUM**
- WHAT: peak-to-trough on the aggregated daily equity curve (sum of per-position `growth_of_1l` series).
- HOW: align the per-stock series by date, sum to a portfolio curve, running-max then max((peak−v)/peak).
- FEASIBLE: yes but heavier — must build the daily curve (positions enter on their own listing date → a growing
  basket, not a fixed one). EFFORT: L. GUARD: be explicit it's a GROWING basket (new calls add capital), not a
  fixed-NAV fund, else the drawdown number misleads.

### NON-recommendation: Sharpe ratio / annualised volatility of the portfolio
- A Sharpe needs a clean periodic-return series on a fixed capital base. Here capital is added per-call over time
  on an irregular, sparse, survivorship-laden basket of ~tens of illiquid names. Annualising vol from that is
  precision we don't have — **statistical theatre**. A drawdown number + the bootstrap band carry the risk story
  honestly without faking a ratio. (If ever wanted: only on the matched, fixed-window secondary basket, clearly
  caveated — not the live ledger.)

## SCORECARD

### 7. Base-rate ("all IPOs") benchmark column — **TOP**
- WHAT: a hit-rate of 60% means nothing without the unconditional rate. Add the field P(alpha>0) for the same
  segment+horizon next to every scorecard hit-rate, so the LIFT (not the level) is judged.
- HOW: from the substrate, P(alpha_h>0) per `type`; one extra column + a lift = hit_rate − base_rate.
- FEASIBLE: yes, substrate has it. EFFORT: S. GUARD: match the cohort/segment/horizon of the base rate to the
  calls being graded (don't compare a boom-SME base rate to mainboard calls).

### 8. Log predicted probability → real Brier score + reliability curve — **HIGH**
- WHAT: `brier()` is a stub because the ledger logs a score, not a probability. The predictor's
  `spine.outcome_breakdown` already yields P(up)/P(double)/P(down). Log that P at call time, then once matured
  compute Brier + a calibration (reliability) curve: bin predicted P, plot mean-predicted vs observed frequency.
- HOW: add a `pred_p_up` column to LEDGER_COLUMNS (write in `make_call` for verdict calls); reliability = bin by
  predicted-P decile, observed = mean(outcome) per bin (same shape as `score_reliability`, already proven).
- FEASIBLE: needs a one-column ledger schema add + populate going forward (not retroactive without re-deriving
  PIT outcome_breakdown). EFFORT: M. GUARD: only score MATURED calls; min-N per bin or merge bins; this measures
  calibration of a SMALL forward sample — wide bands, say so. Don't Brier the historical_sim mode as if it were forward.

### 9. Decay of edge over horizon (1m → 3m → 1y) — **HIGH**
- WHAT: the scorecard already grades 3 horizons; surface them side-by-side per call_type to show whether the
  edge builds (lasting-wealth) or fades (pop-fade) — a known cross-regime truth worth making visible.
- HOW: pivot the existing scorecard across `_GRADE_COL` horizons; one table, hit-rate + median alpha per horizon.
- FEASIBLE: yes, zero new data. EFFORT: S. GUARD: N shrinks at 1y (young calls not yet matured) — show per-horizon
  N; don't read a 1y cell built on 8 names.

### 10. Regime-conditioned hit-rate (tape hot/cold) — **MEDIUM**
- WHAT: split scorecard hit-rate by `tape_state` (already on every ledger row) — does the edge survive cold tapes?
- HOW: add `tape_state` to the scorecard groupby. FEASIBLE: yes. EFFORT: S.
- GUARD: this triples the cells → many fall under the min-N floor; apply the 12/30 floor and suppress thin cells
  rather than reporting a 2/3 = "67%".

### NON-recommendation: per-call_type Sharpe / t-test of alpha difference
- Tiny, skewed, non-normal alpha samples → a t-statistic or a "significant at p<0.05" claim is false precision.
  Wilson CIs on hit-rate + median/IQR of alpha (both already present) are the honest tools. A bootstrap CI on the
  median alpha (same engine as #2) is fine; a parametric significance test is theatre.

## CROSS-CUTTING HONESTY GUARDS (apply to all of the above)
- Min-N floors (protocol §3): <12 suppress · 12–29 "thin" · ≥30 report. Print N on every cut.
- Survivorship: wipeouts must stay in as ₹0 / −100% (decision A1) — both engines already do; any new cut must too.
- Look-ahead: the portfolio/curve uses terminal/exit prices (a realized record, not a forward signal) — fine. Any
  NEW time-series feeding a CALL must be point-in-time (priors strictly before the call date), per protocol §4.
- Mode never pooled: keep live/gap_filled vs backfilled vs historical_sim separate in every new table.
- Reproducible randomness: fixed seed for every bootstrap; state B and that bands are sampling-only uncertainty.

## RANK (insight per effort)
1 (S) outlier decomposition · 7 (S) base-rate lift · 2 (S) bootstrap CI · 9 (S) horizon decay · 3 (S) attribution
· 4 (M) Smallcap250 benchmark · 8 (M) Brier + reliability · 10 (S) regime split · 5 (M) CAGR · 6 (L) drawdown.
