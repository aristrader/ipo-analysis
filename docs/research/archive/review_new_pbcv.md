# Adversarial review — predictor / backtester / validation (Layer 3, Part B+C+V)

Scope: `layer3/predictor/{scorecard,predict,weights}.py`, `layer3/backtest/{analyses,score_backtest}.py`,
`layer3/validate.py`, `layer3/spine.py`. Assume bugs exist; verify correctness, look-ahead, overstated claims.
All headline numbers below were RECOMPUTED by hand against `data/master/ipo_analysis.csv` (substrate loaded
via `spine.load_substrate()`, equity-only). Date of review: 2026-06-01.

Severity legend: **CRITICAL** = wrong/misleading result a user would act on; **IMPORTANT** = real bug or
overstated claim, contained; **MINOR** = correctness nit / hygiene.

---

## CRITICAL

### C1 — Point-in-time scoring uses analog outcomes that had NOT matured at the query date (look-ahead in the OUTCOME, not just the SET)
`layer3/predictor/weights.py:34-61` (`score_all_pointintime`), inherited by `derive_weights`,
`derive_calibration`, and `combined_score_backtest`.

The function correctly freezes the analog SET to IPOs that listed before the query (`prior = df[df["_ld"] < r["_ld"]]`).
But every component score reads the analogs' **fully-matured** outcomes — `alpha_3y`, `return_from_listing_3y`,
`max_drawdown_pct`, `outcome_class` — which are computed from prices through 2026. An analog that listed 6 months
before the query has an `alpha_3y` that only becomes observable ~2.5 years AFTER the query's listing date.

Hand check (sampled query IPOs, prior cohorts): **7,496 / 22,424 = 33.4%** of the analog-outcome rows fed into
point-in-time scoring complete their 3y horizon AFTER the query's listing date. So a third of the "knowable at
prediction time" signal was, in fact, not knowable.

Impact: this inflates the apparent predictiveness of every component IC in `derive_weights`, the calibration lift,
and the `combined_score_backtest` lift. The "point-in-time" label oversells what was actually available.
Fix: gate analog outcomes to what was observable as of the query listing date — i.e. for horizon h, only include
analog i if `analog_listing_date_i + h <= query_listing_date`. (This will shrink early-period cohorts; relax the
ladder or report reduced N rather than leak.) At minimum, relabel as "frozen analog SET, mature outcomes" and stop
calling it point-in-time.

### C2 — In-sample weight fitting then tested on the SAME rows → `combined_score_backtest` verdict is overstated
`layer3/predictor/weights.py:78-99` (`derive_weights`) + `layer3/backtest/score_backtest.py:22-70`.

`derive_weights` computes each component's Spearman IC vs `realized_alpha` over the FULL scored set (both regimes,
all years), zeroes sign-flippers, normalizes, and persists. `combined_score_backtest` then loads those same weights
and tests whether the top-quintile score beats the field **on the same IPOs whose realized alphas set the weights**.
The weights were selected using the outcomes of the test rows → in-sample. The resulting verdict
("score ADDS alpha cross-regime") and the bootstrap "lift > 0 in 100% of resamples" are not an out-of-sample edge.

This compounds C1 (the outcomes themselves leak). A clean test needs the weights derived on a strictly earlier slice
than the evaluated rows (e.g. derive on listings ≤ year Y, test on Y+), or k-fold by vintage.

### C3 — Calibration / backtest pool boom + longterm; the pooled "lift" is largely a cohort-composition artifact, and `predict()` shows it to a NEW (boom-era) IPO as "cross-regime validated"
`layer3/predictor/weights.py:126-141` (`derive_calibration`), surfaced at `layer3/predictor/predict.py:62-69`.

Hand recompute (current substrate, loaded weights):
- field (pooled) median alpha_3y = **−37.9%**; top-quintile (combined ≥ Q0.8 = 47.4) median = **+9.8%** → pooled lift **+47.7pp**.
- BUT boom median alpha_3y = −1.1% (n=366) vs longterm = −46.7% (n=964). The two regimes are not comparable.
- Top-quintile cohort mix = **47% boom**; field mix = **28% boom**. The score preferentially selects boom-era IPOs,
  which structurally have ~+46pp higher alpha_3y. So a large part of the +47.7pp pooled "lift" is the score acting
  as a vintage sorter, not a within-regime alpha edge. Honest per-cohort lifts: boom +60.9pp, longterm +26.2pp.

The stored `scorecard_calibration.json` reports `top_quintile_lift_pp = 35.9, n_scored = 1259` (stale — fresh run
gives lift ≈ 47.7, n ≈ 1292; substrate changed after the artifact was saved — see C4). Either number is the POOLED
cross-regime figure.

`predict.py:68-69` then prints, verbatim and hardcoded: *"top-quintile-score IPOs beat the field by +{lift}pp
(cross-regime validated, n={n})."* Two problems: (a) the calibration JSON carries NO cross-regime field — "cross-regime
validated" is a hardcoded literal, not derived from data; (b) the +35.9pp is the pooled, composition-inflated number,
shown to a user evaluating a 2026 IPO whose true comparison set is the boom regime only. Overstated claim a user acts on.
Fix: compute and store/display per-cohort calibration (boom-only lift for boom-era queries), and derive the
"validated" wording from the actual per-cohort signs rather than hardcoding it.

---

## IMPORTANT

### I1 — Persisted weights are STALE and inconsistent with the current derivation rule
`data/master/scorecard_weights.json` has `liquidity = 0.047, quality = 0.0`. Re-running `derive_weights` on the
current substrate gives `liquidity = 0.0` (longterm IC = −0.012, boom = +0.047 → MIXED sign → 0) and renormalizes
return/multibagger/downside to {0.355, 0.327, 0.319}. The saved file (sum 1.001) was produced under a different
substrate where liquidity's IC was same-signed in both regimes. `predict()` and both backtests load the stale file,
so the live scorecard weights do not match what the current data + stated rule produce. Fix: re-derive and re-save
(and ideally version/stamp the artifact with the substrate hash), or fail loudly if the artifact predates the substrate.

### I2 — Under data-informed weights, `quality` (weight 0) and `liquidity` (weight 0) are silently dropped from the combined score
`scorecard.py:147-161`, `_combined` in both `weights.py:117-123` and `score_backtest.py:13-19`.

Renormalization is itself correct: `den` only accumulates `w[k]` when the component score is non-null AND `w.get(k)`
is truthy — so a zero-weight component is excluded, and the combined score renormalizes over available non-zero-weight
components only (verified). The consequence, though, is a real product gap: the two hard-to-fake red flags the
`quality()` docstring sells as "VALIDATED" (the N8 accrual flag and the N7 extreme-debt cliff) have ZERO influence on
the combined score and the calibration, because `quality` weight derived to 0. A user reading the combined score gets
no downside protection from those flags. This is defensible only if disclosed; today it is not. Fix: either floor a
small preset weight on quality/downside red-flags, or surface in `predict()` that the combined score ignores quality.

### I3 — `derive_calibration` quintile thresholds are in-sample and reused as fixed cut-points for future IPOs
`weights.py:137`. Thresholds are the 0.2/0.4/0.6/0.8 quantiles of the (leaky, pooled) combined-score distribution.
A new IPO is bucketed against these fixed cut-points in `predict.py:67`. Because the score distribution is itself
cohort-composition dependent (C3) and computed with leaked outcomes (C1), the quintile a user is told ("quintile 4/5")
is not a stable, regime-honest rank. The quintile-application logic itself (`sum(cs >= t for t) + 1`, 4 thresholds →
1..5) IS consistent with how `derive_calibration` defines them (top = combined ≥ Q0.8 ⇒ quintile 5) — that part is fine.

### I4 — `validate()` emits a `fragility` label even when the verdict is "insufficient N"
`validate.py:111-129`, row `pred-size-survival`: `boom_N=8 (< MIN_N_HINT)` ⇒ verdict "insufficient N (boom=8, long=124)",
yet `fragility = "FRAGILE"` is still shown. The fragility heuristic runs before the N-guard, so it labels a finding it
just declared untestable. Misleading in the output table. Fix: set fragility to "n/a" when the verdict is insufficient-N.

---

## MINOR

### M1 — `flip_allotment_ev` formula is correct and adverse-selection is honest (hand-verified) — but label it
`analyses.py:45-63`. Hand recompute, MB, boom, trusted listing status, N=326:
naive_mean_flip = **+21.2%**; allotment-weighted = **+2.0%**; adverse-selection cost = **19.2pp**; median p_allot = **0.035**.
Reproduces the function exactly. `corr(gain, sub) = +0.64` and `corr(gain, p_allot) = −0.38` confirm the down-weighting
correctly penalizes hot/high-pop IPOs. `Σ(gain·p_allot)/Σ(p_allot)` is the right "per-rupee captured if you apply equal
lots to every IPO" — it is a proper allotment-weighted mean, not double-counting. One nuance to disclose: it assumes
you deploy equal capital to every IPO and ignores the >1 lot / HNI category, so it is the *retail-1-lot* EV; fine, but
the docstring should say so. No bug.

### M2 — `downside_safety` liquidity haircut vs the standalone `liquidity` component: defensible, not a double-count
`scorecard.py:68-74`. Both read `liquidity_flag != "ok"`. With data-informed weights, liquidity weight = 0, so the only
channel liquidity enters the combined score is the downside haircut — so there is effectively NO double-count today
(the opposite of the stated worry). Even under preset weights it is defensible: the haircut answers "can I exit a −60%?"
(realizability of downside) while the component answers "is it tradable at all?" — related but distinct. Hand example
(SME/Industrials/micro cohort): illiquid_frac 0.58 → haircut 0.77 → base 35.2 × 0.77 = 27.1, matches. Keep, but note
the overlap in docs so a future weight change doesn't silently double-weight liquidity.

### M3 — `portfolio_summary` "mean_per_unit_dispersion" is cross-sectional, not a Sharpe — correctly labeled
`analyses.py:25-42`. `mean/std` is computed across NAMES at one horizon (no time series), and the code/docstring say so
("NOT a Sharpe"). MB 1y: mean −1.7%, dispersion 68.0%, ratio −0.03; SME 1y: mean +41.5%, dispersion 241.9%, ratio 0.17.
Reproduces. Honest. One nit: `basket_mean_alpha_%` for SME (+41.5%) alongside `basket_median_alpha_% = −11.5%` and
`beats_donothing = False` (uses median) is internally consistent but a casual reader may anchor on the +41.5% mean of a
massively right-skewed basket; consider leading with the median.

### M4 — `bootstrap_median_ci` is seeded and percentiles are correct
`spine.py:107-120`. seed=0, `np.random.default_rng`, reproducible across calls (verified equal on reruns). For ci=0.90
it returns the 5th/95th percentiles (`a=(1-ci)/2=0.05`), correct. `p_positive` = fraction of bootstrap medians > 0,
correct. Sub-`MIN_N_HINT` guard returns Nones. No bug.

### M5 — `combined_score_backtest` bootstrap is seeded and percentile-clean; verdict matches the numbers
`score_backtest.py:44-70`. seed=0; resamples the index, requires ≥MIN_N_HINT in both top and rest, computes
`median(top) − median(all)`; `lift_p_positive` = fraction > 0. Verdict "ADDS alpha cross-regime" fires only when both
boom and longterm `lift_vs_all_pp > 0` (boom +60.9, long +26.2 → fires). String matches the numbers. Caveat: the edge
itself is in-sample (C2) and partly composition (C3) — the verdict is consistent with the numbers but the numbers are
inflated. Top-quintile fraction verified = exactly 0.20.

### M6 — `bimodal/barbell` flag thresholds (predict.py:81-84) behave as intended
Fires when `>25%` of analog alphas `< −0.3` AND `>25% > +0.5`. Verified on a synthetic 30/30/40 split → fires.
`pick_horizon` (scorecard.py:31-33) correctly gates the WHOLE scorecard to one horizon (3y if maturity-gated N ≥ 10
else 1y); `predict()` recomputes the same gate independently (predict.py:18) — duplicated logic but consistent values.

### M7 — `confidence()` `boom_frac` / `"cohort" in cohort` works as intended
`scorecard.py:131`. `cohort` is a DataFrame; `"cohort" in cohort` tests COLUMN membership (True here), so `boom_frac`
computes. `analog_median_listing_year` and `analog_boom_frac` are disclosure-only (not auto-tuned), matching the
docstring. The `predict.py:100` "analogs are mostly OLD" warning fires when boom_frac < 0.3 — fine. Hand-confirmed.

---

## Recompute summary (for the record)
| quantity | hand value | code/artifact | note |
|---|---|---|---|
| combined-score top-quintile lift (pooled, ALL) | +47.7pp | code 47.7 / artifact 35.9 | artifact STALE (C3/I1) |
| score quintile thresholds | [12.5, 26.5, 37.3, 47.4] | artifact [12.3,26.2,37.1,46.6] | STALE |
| per-cohort lift | boom +60.9pp, long +26.2pp | matches code | both leak via C1/C2 |
| top-quintile cohort mix | 47% boom (field 28%) | — | composition artifact (C3) |
| flip_allotment_ev MB | naive +21.2%, weighted +2.0%, cost 19.2pp | matches | correct (M1) |
| analog-outcome maturity leak | 33.4% of analog 3y outcomes not yet observable | — | C1 |
| derived weights (current data) | rp .355 / mb .327 / ds .319 / liq 0 / qual 0 | artifact has liq .047 | STALE (I1) |
