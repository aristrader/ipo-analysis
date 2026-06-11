# Validation-layer ideas — what to BUILD next (prioritized)

Goal: only checks that genuinely raise trust in the 16 findings + the predictor/backtest. Already built and NOT
re-proposed here: cross-regime SIGN check (`layer3/validate.py`), Wilson CIs on proportions (`spine.proportion`),
unbypassable min-N floors (`spine.guarded` + `config.n_tier`), competing-risks wipeout BAND (`spine.wipeout_band`),
the data-quality bias audit (T7, `findings/t7_benchmark`), point-in-time analog-set freeze + cross-regime-gated
predictor weights (`predictor/weights.py`) and the combined-score backtest (`backtest/score_backtest`).

The single biggest residual risk this catalog targets: **the catalog's own trap #1 — vintage = regime = market-level
collinearity.** The current cross-regime check only proves a sign holds in *two pooled buckets* (2020–25 vs 2006–19).
Two buckets is two data points; a sign can hold in both yet be driven entirely by one or two big bull/bear years
inside each. That is the gap to close first.

## Top BUILD picks (do these)

1. **Within-vintage validation** — for each directional claim, recompute the signal *within each listing year* (the
   `year` column), then count in how many vintages it holds the expected sign (sign-test / fraction-positive with a
   Wilson CI on that fraction). A claim that holds in 14/17 years is robust; one that holds "in both regimes" but only
   in 3/17 years is a regime/vintage artifact wearing a disguise. This directly kills the #1 trap the catalog warns
   about and the cross-regime check cannot catch. Computable now (`year` present, 2006–2025). The promotion gate should
   become: cross-regime sign AND within-vintage majority.

2. **Fragility / N-to-flip score per finding** — for each headline directional finding, report the smallest number of
   observations that, if moved to the opposite side (or dropped), would flip the sign of the median-gap / lift. A finding
   resting on `pred-profitable-ipo` (MB N=16/11) or `pred-ofs-skin` (boom N=14) is one or two IPOs from reversing; this
   makes that fragility a printed number instead of a footnote. Cheap (re-rank + recount on existing series), and it gives
   each finding a single honest "how load-bearing is this?" tag.

3. **Bootstrap CIs on medians & lifts** — Wilson covers proportions (wipeout rates), but the *headline numbers* are
   median alphas and median-gaps/lifts (T1, T3, T5, T9, the score backtest spread), which currently have N but no
   interval. A simple percentile bootstrap (resample within each segment×cohort cell, 2–5k draws) gives a CI on every
   median/gap and, as a free byproduct, the share of resamples where the sign holds — i.e. an empirical p-value for the
   directional claim. Turns "boom +52% vs −4%" into "+52% [CI…] vs −4% [CI…], sign held in 97% of resamples." Moderate
   effort, high payoff, no new data.

4. **Multiple-comparisons / false-discovery note** — 16 findings × {MB,SME} × {boom,longterm} × several
   horizons/tertile slices is easily 100+ tested directional contrasts. With that many slices, several "signals" at
   p<0.05 are expected by chance. This need not be a heavy FDR machine: tag each finding **confirmatory** (pre-registered
   Tier-1: T1,T2,T6,T3,T5,T9 per §0) vs **exploratory** (everything tertile-mined: n3/n5/n6/n7/n8 sub-slices), apply a
   stricter bar to exploratory ones, and print one honest paragraph stating how many contrasts were tested. Low effort
   (mostly a tagging pass + a count), and it reframes the weakest findings honestly. Pairs naturally with #3's p-values.

5. **Placebo / random-signal test** — replace a real predicate (e.g. OFS tertile, a fundamental tertile) with a randomly
   assigned label and rerun the exact finding/backtest harness; a trustworthy pipeline should show ≈0 lift and the
   cross-regime check should NOT promote it. Run it a few hundred times to get the null distribution of "lift" the
   machinery manufactures from noise — then a real finding is only credible if it beats that null. This validates the
   *harness itself* (catches a coding/leakage bug that inflates every lift) and gives the backtest spread a baseline.
   Cheap to bolt onto the existing backtest/finding runners.

## The full table

| # | check | failure mode it catches | computable? | effort | recommendation |
|---|---|---|---|---|---|
| 1 | **Within-vintage validation** (sign-fraction across listing years) | vintage=regime confound (#1 trap): a sign that "holds in both regimes" but lives in 2–3 years | yes (`year`, 2006–25) | M | **BUILD** — closes the #1 trap the cross-regime check can't; becomes part of the promotion gate |
| 2 | **Fragility / N-to-flip per finding** | findings resting on 1–2 IPOs (profitable-ipo 16/11, ofs 14) that read as "validated" | yes | low | **BUILD** — turns fragility into a printed number; trivial on existing series |
| 3 | **Bootstrap CIs on medians/lifts** + sign-stability share | the headline median-gaps/lifts have N but no interval; can't tell signal from sampling noise | yes | M | **BUILD** — gives every non-proportion an interval + empirical sign p-value; no new data |
| 4 | **Multiple-comparisons / FDR note + confirmatory-vs-exploratory tags** | ~100+ slices → false positives expected; mined tertile findings dressed as discoveries | yes | low | **BUILD** — mostly a tagging pass + a count; honest reframing of weakest findings |
| 5 | **Placebo / random-signal test** | a harness/leakage bug that manufactures lift from noise; backtest spread has no null baseline | yes | low–M | **BUILD** — validates the machinery itself + baselines the score-backtest spread |
| 6 | **Sub-period stability (split each cohort in half)** | a cohort whose signal lives in one half (e.g. 2021 froth) only | yes | low | **MAYBE** — cheap, but #1 (within-vintage) strictly dominates it; build only if #1 is too granular for headline display |
| 7 | **Sensitivity to min-N floor + tertile/bucket cutoffs** | conclusions that exist only at the chosen 30/10 floor or the specific tertile edges | yes | M | **MAYBE** — real concern for tertile findings (n5/n6/n7); do it for the tertile-based ones, skip for the base-rate findings where cutoffs aren't load-bearing |
| 8 | **Recompute-on-resample stability** (rank stability of the score) | predictor rank order that's unstable to resampling | yes | M | **MAYBE** — largely redundant with #3's bootstrap applied to the rank-IC; fold into #3 rather than build separately |
| 9 | **Explicit look-ahead audit** of every finding/feature | a finding silently using post-listing info (e.g. final outcome leaking into a "pre-listing" filter) | partly (manual) | low | **MAYBE** — the predictor weights already freeze the analog set point-in-time and `strat-buy-filtered` was already corrected for a look-ahead artifact; do a one-time manual feature-provenance pass (is each feature known at listing?), don't build standing code |
| 10 | Separate confirmatory/exploratory *promotion gates* in `rules/index.md` | exploratory findings promoted to `validated` on the same evidence as Tier-1 | yes | low | **MAYBE** — this is the policy half of #4; adopt as a convention rather than new code |

## Cut (statistical theater here)

- **A heavyweight FDR engine (Benjamini–Hochberg across all contrasts).** With sign-based (not p-value-based)
  validation and small heterogeneous cells, a formal q-value table implies a precision the data doesn't support. The
  honest note + confirmatory/exploratory split (#4) delivers the real benefit without the false rigor.
- **Standalone recompute-on-resample module (#8).** Duplicates the bootstrap (#3) once it's applied to the rank-IC; a
  second resampling harness is maintenance cost for no new signal.
- **Sub-period halving as its own promotion gate (#6).** Within-vintage (#1) is the same idea at the right granularity;
  two overlapping time-stability gates is padding.

---
**Build order:** #1 within-vintage (extend `validate.py`'s gate) → #2 fragility (cheap, attaches to every finding) →
#3 bootstrap (feeds #4's p-values) → #4 MC note + confirmatory/exploratory tags → #5 placebo (validates the harness).
