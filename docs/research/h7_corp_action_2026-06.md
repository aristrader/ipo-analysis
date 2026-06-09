# H7 — Corp-action euphoria-top backtest (widened F10)

_2026-06-09. Script: `tools/research/h7_corp_action.py`. Events: `data/master/review/h7_corp_action_events.csv`._

## HONEST CAVEATS FIRST (read before any number)
- **Min-N is the binding constraint.** Only **n=31** IPOs ever had a bonus/split with an ex-date inside
  their first year of listing (the "recent IPO" gate), across 20 years. Per the protocol floor that is
  "thin" (12–29) to barely-reportable (≥30); **per-cohort it is BELOW the floor** — boom n=13, longterm
  n=18; MB n=18, SME n=13. Every sub-cell is small. Treat the magnitudes as indicative, not precise.
- **No new data vs F10.** corp_actions.csv contains ONLY bonus/split/bonus+split ex-dates. There are
  **NO standalone dividend ex-dates**, so the hypothesis' "dividend" leg is **not testable** here. H7 is
  the SAME universe as F10 (n moved 31→31 after folding in the 1 `bonus+split` match F10's filter missed).
  The widening is in METHOD (4 horizons, explicit run-up conditioning + dose, cross-regime split, a proper
  same-name random-date PLACEBO, Wilson/bootstrap CIs), not in sample size. So H7 does NOT "graduate F10
  on N" — it stress-tests it.
- **Look-ahead controlled:** forward alpha measured from the trading day AFTER ex_date; run-up uses only
  alpha accumulated UP TO ex_date. Returns = alpha vs Nifty 50. `unreliable_coverage` excluded.

## Method
Match corp_actions (bonus/split/bonus+split) to substrate IPOs by ISIN, else by `nse_symbol` (a face-value
split changes the ISIN — project rule). Keep the EARLIEST action with ex_date 30–365 cal-days after listing.
Trading-day index `tdx = cal_days*0.69`. Run-up = Σ daily alpha to `tdx`. Forward = cumulative alpha over
`[tdx+1, tdx+H]` for H ∈ {21,63,126,252} td (~1m/3m/6m/1y). Three comparators:
- **CONTROL** — matched pseudo-events: same type, run-up within ±25pp, NO corp action, same tdx offset.
- **PLACEBO** — random fake ex-dates (30–365d, ≥10td from the real one) on the SAME treated names. If the
  drop reproduces at random dates, it is mechanical post-IPO drift, not the action.

## Test table (median fwd alpha · win-rate [Wilson95] · n)

| Horizon | Treated (all) | boom | longterm | HIGH run-up | LOW run-up | CONTROL | PLACEBO |
|---|---|---|---|---|---|---|---|
| **1m** | −27.1% · 13% · 31 | −17.3% · n13 | −43.4% · n18 | **−80.7% · 0% · n16** | −6.5% · 27% · n15 | −2.7% · 34% · n44 | **+0.0% · 50% · n82** |
| **3m** | −22.2% · 16% · 31 | −10.4% · n13 | −68.8% · n18 | **−88.8% · 6% · n16** | −10.4% · 27% · n15 | −0.6% · 50% · n44 | −7.9% · 40% · n82 |
| **6m** | −54.2% · 26% · 31 | −11.2% · n13 | −70.5% · n18 | −101.3% · 6% · n16 | −2.8% · 47% · n15 | −6.9% · 41% · n44 | −31.3% · 23% · n82 |
| **1y** | −45.3% · 17% · 30 | −38.5% · n12 | −74.2% · n18 | −112.5% · 12% · n16 | −27.7% · 21% · n14 | −2.1% · 50% · n44 | −59.4% · 21% · n82 |

Dose (Spearman run-up vs forward): 1m **−0.74**, 3m −0.61, 6m −0.68, 1y −0.62. Days-to-action: ~0 (no timing edge).
Median run-up TO ex-date = **+183.7%** (P90 +1351%) — these are names that already ripped.

## What survives, what doesn't
- **The SHORT-window effect (1m, 3m) is REAL and action-specific.** At 1m treated −27% beats CONTROL −2.7%
  AND PLACEBO +0.0% (placebo win 50% = a coin flip); at 3m treated −22% vs control −0.6% vs placebo −7.9%.
  The random-date placebo does NOT reproduce the immediate post-action drop → the timing of the action carries
  information, not just "these names drift down."
- **The mechanism is the RUN-UP, not the action per se.** The dose −0.74 and the HIGH-vs-LOW split are the
  headline: HIGH-run-up names are −81% (win **0%**) at 1m and −89% (win 6%) at 3m; LOW-run-up names sit at
  control levels (−6.5% / −10%). Edge lives ENTIRELY in "action AFTER a big run," exactly the lit-review prior.
- **The LONG-window effect (6m, 1y) is NOT action-specific — it largely collapses into the PLACEBO.** At 1y
  treated −45% but PLACEBO −59%; at 6m treated −54% vs placebo −31%. At long horizons these names mean-revert
  from extreme run-ups regardless of WHEN you'd have measured — that's general euphoria fade, double-counted
  by F5e/path persistence, NOT a corp-action tell. **Do not claim a 6m/1y corp-action edge.**
- **Cross-regime:** the sign holds in BOTH cohorts at 1m/3m (boom 3m −10% win 31%; longterm 3m −69% win 6%),
  but boom is weaker and n=13. Longterm carries the effect. Call it **cross-regime-PRESENT but boom-thin**.

## Placebo verdict
PASS at 1m/3m (random-date placebo ≈ flat / mild, far above treated), FAIL at 6m/1y (placebo ≈ treated).
The honest read: the corp-action-SPECIFIC, tradeable signal is the **1–3 month** post-ex-date window on
**high-run-up** names. Beyond a quarter you're just measuring euphoria mean-reversion that other flags catch.

## Falsifier (pre-declared) — outcome
"With the same-name random-date placebo, the post-action drop reproduces at random dates" → would kill it as
mechanical. **Result: did NOT reproduce at 1m/3m (placebo flat), DID reproduce at 6m/1y.** So: 1m/3m survive,
6m/1y falsified as action-specific.

## F10 double-count check
- H7 IS F10 re-run with more rigor on the SAME n≈31 — it is NOT an independent confirmation. The 3m −22%
  headline reproduces F10 exactly (F10: −22.2% win 16% vs control +2.2% win 55%). H7 adds: the placebo
  (new), the explicit run-up dose (the real driver), and the finding that 6m/1y are NOT incremental.
- **Versus F5e / path-persistence:** the 6m/1y leg overlaps the existing euphoria-fade flags (the placebo
  proves the long-horizon drop is generic to high-run-up recent IPOs). DO NOT credit H7 for the 6m/1y move.
  Only the 1–3m action-timed drop is incremental to what's already shipped.
- **Endpoint sanity:** treated names' from-LISTING alpha_1y is +12.8% (vs all-IPO −12.8%) — they are NOT bad
  companies. The action marks a LOCAL top for someone holding INTO it, not a doomed business. Consistent with F10.

## VERDICT: **DISPLAY-ONLY EXIT FLAG (confirms & narrows F10); NOT a score input.**
- Robust enough to KEEP as a display-only EXIT/timing flag, NARROWED to: "bonus/split ex-date in yr 1 AFTER a
  large run-up → expect negative 1–3m alpha (sell-into-strength), worst when run-up is biggest." This is a
  post-listing signal → per the locked policy it can NEVER be a score input regardless of robustness.
- NOT promoted to "validated/graduated": per-cohort N is below floor and it shares its sample with F10 (no
  independent N). The contribution is (a) a placebo that legitimizes the SHORT-window claim, (b) the run-up
  dose as the true driver, (c) an explicit "no 6m/1y incremental edge — don't double-count euphoria fade."
- Numbers I'm unsure about: every per-cohort/per-type cell (n 12–18, wide bootstrap bands); the cal→td 0.69
  factor (approximate); the 6m/1y treated medians (confounded by survivorship of names with ≥126/252 td paths).
