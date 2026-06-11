# Layer-3 Part B (predictor + scorecard) & Part C (backtester) — adversarial review

Date: 2026-05-31. Reviewer: automated adversarial pass.
Scope: `layer3/predictor/{analogs,scorecard,predict}.py`, `predict_ipo.py`,
`layer3/backtest/engine.py`, `run_backtest.py`, tests. Focus: correctness + whether the
**outputs could mislead**. All `pytest` (11 tests) pass; the bugs below are not caught by tests.

Verified key facts (re-confirmed against the substrate):
- `alpha_*`, `return_from_*` are **fractions (0–1 scale)**: `alpha_1y` median = −0.131 (−13.1%).
- `ofs_pct`, `sub_total_x`, `sub_qib_x`, `gmp_pct`, `pre_ipo_roe_pct`, `pre_ipo_pat_margin_pct`,
  `promoter_post_issue_pct` are **0–100 scale**: `ofs_pct` p50 = 6.1, p90 = 71.7; `roe` p50 = 21.7.
- `pre_ipo_debt_equity` is a ratio (p50 = 0.41). `pre_ipo_pat` is a rupee-crore PAT value (−3942 … 6060).
- CLI `--ofs_pct 60`, `--roe 18` are passed through as `60` / `18` → consistent with the 0–100 data and
  with `robust_ranges` (computed on the same raw columns). **Scale handling in the predictor is correct.**

---

## CRITICAL

### C1. Backtester `secondary_filtered` "edge" is a small-N, regime-specific artifact — the output misleads
`layer3/backtest/engine.py:47-58`, surfaced by `run_backtest.py:16-22`.

The headline table reports, pooled per segment, that `secondary_filtered` **beats do-nothing**:
SME 1y median +12.0% (N=55, `beats_donothing=True`) and SME 3y median +28.0% (N=34, True). A user
reads this as "the profitable+OFS≥25%+investable Tier-1 filter adds alpha." It does not survive a
cohort split (recomputed by hand, alpha_3y − 0.5% cost):

| segment·cohort | filtered N | filtered median α3y | unfiltered median α3y |
|---|---|---|---|
| SME longterm | 24 | **+38.1%** | −40.9% |
| SME boom | 10 | **+2.3%** | +6.8% (filter *hurts*) |
| MB longterm | 85 | −21.4% | −57.2% |
| MB boom | 81 | −21.7% | −23.8% |

The entire SME "beats do-nothing" verdict rests on **24 longterm SME names (2016–2018)** and
**reverses sign in the boom cohort**. This is exactly the Vintage=Regime trap the method spine warns
about (`docs/strategies.md:70`). The binding filter constraint is `ofs_pct >= 25` (only 149 of 1157
SME pass), so the cohort is an OFS-heavy slice, not a clean quality signal.
- **Note (genuinely robust piece):** for **MB**, the filter *does* improve median alpha cross-regime
  (−21% vs −24%/−57%) — i.e. it reliably strips downside — but median alpha stays **negative**, so it
  still does not "beat do-nothing." Report MB as "reduces downside, not a positive-alpha strategy."
- **Fix:** run every strategy **split by cohort** (boom vs longterm) and require the verdict to hold in
  BOTH before any `beats_donothing=True` is shown pooled; print N per cohort; for N<`MIN_N_TRADABLE`
  (30) per cohort, suppress the verdict and tag "insufficient / single-regime." Add a multiple-
  comparisons caveat (5 strategies × 2 segments × 2 horizons = 20 tests).

### C2. Backtester `secondary_filtered` uses a LOOK-AHEAD entry filter (`liquidity_flag`)
`layer3/backtest/engine.py:50` (`liq = g["liquidity_flag"] == "ok"`); provenance
`pipeline/07_returns_summary.py:408-417`.

`liquidity_flag`/`median_daily_turnover_inr` are computed from the IPO's **entire post-listing price
history** (median daily turnover over all available days). Using `liquidity_flag == 'ok'` as a
**point-in-time entry filter** is forward-looking: an investor buying at listing cannot know the
stock's future median turnover. This violates the Part-C "only info known at the decision; no
look-ahead" contract (`engine.py:3-4`, `docs/strategies.md:65`) and inflates `secondary_filtered`
(survivorship — illiquid names that later died are silently excluded from entry). This compounds C1.
- **Fix:** drop `liquidity_flag` from any *entry* rule, or replace with a pre-listing liquidity proxy
  (issue size / lot economics). Liquidity is fine as a *post-hoc reporting* lens (T8), not an entry gate.
  In the predictor (`scorecard.liquidity`) it is acceptable because it *describes* the cohort's realized
  liquidity rather than acting as an investable pre-trade filter — but label it as a realized property.

### C3. `beats_donothing` mixes raw-return and alpha against a single alpha-0 baseline — incoherent for allottee/flip
`layer3/backtest/engine.py:81-95`, `run_backtest.py:13`.

`_metrics` sets `use = "alpha" if kind=="secondary" else "ret"`, then computes
`beats_donothing = median > 0`. For allottee/flip strategies the tested quantity is **raw return**,
but the printed baseline is "do-nothing = index (alpha 0) / break-even" (`engine.py:94`,
`run_backtest.py:13`). A raw-return median > 0 does NOT mean the strategy beat the index — a +5% raw
return in a year the index returned +15% is a **loss vs do-nothing**, yet it prints `beats_donothing=True`
(e.g. `allottee_hold` MB 1y median +5.2% → True; `flip_at_listing` +7.1% → True). The "do-nothing =
break-even" label is only meaningful for the alpha-measured secondary strategies.
- **Fix:** either (a) report allottee/flip `beats_donothing` against an explicit **raw do-nothing**
  (e.g. median index return over matched holding windows, not 0), or (b) drop the `beats_donothing`
  column for `kind=="allottee"` and state plainly "allottee return is not benchmark-adjusted; not
  comparable to the index baseline." Today the column actively misleads for 2 of 5 strategies.

---

## IMPORTANT

### I1. `multibagger_odds` is computed on FROM-ISSUE raw return, but framed/blended as if alpha
`layer3/predictor/scorecard.py:41-47`.

`docs/strategies.md:59` specifies multibagger odds as "% ≥2x/≥5x **alpha**." The code uses
`return_from_issue_{h}` (issue-anchored RAW return; median = 0.0 in data), not alpha and not even
from-listing return. So the component answers "what fraction of the cohort doubled **from the issue
price** (an allottee outcome)", while the headline distribution and `return_potential` answer "from-
**listing alpha** (the secondary buyer)". Two different investors are blended into one score. In the
sample run this produced the eyebrow-raiser: a "multibagger" named-analog (Ujjivan, +49% from issue)
displayed alongside `α3y=−8%` — internally consistent given the columns, but the scorecard never
discloses that multibagger_odds is a *different measure* (allottee, from issue) than the rest.
- **Fix:** decide one frame. If the tool is for the secondary buyer (it is — alpha-from-listing
  everywhere else), compute multibagger odds on `return_from_listing_{h}` (or an alpha multiple) and
  relabel. If you keep from-issue, label the component "2x/5x from ISSUE (allottee)" so it isn't read
  as a listing-buyer outcome.

### I2. Scorecard components silently mix maturity-gated horizons; combined score blends 1y and 3y
`layer3/predictor/scorecard.py:31-47`, `predict.py:18-20`.

`return_potential` and `multibagger_odds` each independently pick `3y` if N≥`MIN_N_HINT` else fall back
to `1y`; `downside_safety` always uses `3y`; the headline `distribution` picks its own horizon. So the
combined score can blend a 3y return_potential with a 1y multibagger_odds with a 3y downside in one
number, and the printed distribution horizon may differ from the components'. Not wrong per se, but the
single "COMBINED 64.8/100" hides that its parts are measured over different windows.
- **Fix:** resolve one horizon for the whole scorecard (the most-mature horizon meeting min-N) and pass
  it to all components; print that horizon next to COMBINED.

### I3. `secondary_avoid_hot` applies a LOOK-AHEAD-free filter but is still survivorship/coverage-skewed, and ties to C1
`layer3/backtest/engine.py:61-69`. The pop≤25% filter itself is point-in-time-OK (listing pop is known
at listing). But it inherits the same pooled-cohort presentation problem as C1 and shows essentially
the same median as `secondary_hold` (MB 1y −16.4% vs −16.8%) — i.e. avoiding froth adds ~nothing. The
output is honest here; the issue is only that, like all rows, it lacks a cohort split to confirm.

### I4. CLI `--profitable` collapses real PAT to ±1; quality() then can't use magnitude — and substrate `pre_ipo_pat` is a value, not a flag
`predict_ipo.py:25-26`, `scorecard.py:82-84`. `quality()` only checks `pat > 0`, so the ±1 encoding is
fine for the predictor. BUT the same column name `pre_ipo_pat` means a rupee-crore VALUE in the
substrate (used correctly as `>0` in the backtest filter) and a ±1 FLAG in a CLI query. This dual
meaning is a latent footgun if anyone ever uses query magnitude. Minor today; document it.

---

## MINOR

- **M1. Proportions printed with a signed `+` look like returns.** `predict.py:33-34` `_pct` prefixes
  `+`; applied to `pct_below_issue`, `pct_2x`, `maturity_coverage_3y`, wipeout rates. Output reads
  "below-issue +37%", "3y-maturity-cov +60%" — these are *shares of the cohort*, not gains. Use a
  non-signed `%` formatter for proportions. (`scorecard.py:90`, `predict.py:64-66,77,88,90`.)
- **M2. Alpha < −100% displayed as "−107%".** `predict.py` named-analog line (Spandana α3y=−107%).
  Mathematically valid (alpha = return − benchmark can exceed −100%), but jarring; add a one-line note
  that alpha is excess-vs-index and can exceed ±100%.
- **M3. `downside_safety` deep-drawdown term is near-saturated.** `scorecard.py:55-56`: `max_drawdown_pct
  <= -0.50` is true for the vast majority (substrate p50 = −0.73), so this 0.2-weight term barely
  discriminates between cohorts. Consider a steeper threshold or a continuous map.
- **M4. GMP is in the analog DISTANCE (weight 0.4) though the policy quarantines it from the SCORE.**
  `analogs.py:27`. `docs/strategies.md:45` says quarantine GMP from the *score*; it's not in the
  scorecard (good), but it does influence *which* analogs are picked, which indirectly feeds the score.
  Defensible (down-weighted, matching-only) but worth an explicit note in `docs/layer3.md`.
- **M5. Self-match relies on the caller passing `isin`.** `predict.py:13` excludes `query.get("isin")`;
  CLI queries are synthetic (no isin) so safe, but a programmatic caller scoring an IPO already in the
  substrate without passing isin would self-match. Consider also excluding on exact name match as a
  backstop, or document the requirement.
- **M6. `flip_at_listing` is horizon-independent (held ~0 days) so N is identical for 1y/3y (805/805).**
  Correct by design, but it appears in both horizon tables with the same numbers, which can read as a
  duplicated row. Print it once, outside the horizon loop.

---

## What is correct / robust (do not "fix")
- Predictor scale handling: 0–100 features normalized by P10–P90 ranges on the *same* raw columns;
  `log_issue_size` derived once; missing features dropped + weights renormalized (`gower`,
  `robust_ranges`). No double-counting found; ofs is not double-counted.
- Widening ladder relaxes only when `len(gated) < target_n`, prefers sector-preserving rungs first,
  keeps delisted analogs, degrades the confidence label, and never self-matches (with isin passed).
- Component scores are all clipped to [0,100], correctly signed (downside_safety falls as
  wipeout/below-issue/drawdown rise), min-N floor returns `None` (not a fake score), and the combined
  score renormalizes over only the available components (`scorecard.py:126-129`). Confidence label keys
  off N + rung + maturity coverage sensibly.
- The predictor **never forecasts the query's own number** — it only reports "what N similar past IPOs
  did" + the query's own fundamentals for the quality component. Honesty footer present.
- Backtester: maturity-gating correct (3y N ≤ 1y N, verified SME); costs applied exactly once per
  strategy (verified `gross − net ≈ 0.005`); SME/MB never pooled; flip access-realism caveat honest and
  present. Manual recompute of `secondary_filtered` SME-3y median (+28.0%) matched the engine exactly.
- The `flip_at_listing` raw gains being unrealistic (adverse selection) is explicitly caveated.
