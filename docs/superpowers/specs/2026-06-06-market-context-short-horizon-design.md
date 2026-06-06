# Market-Context Signals + Short-Horizon Lens + Play/Skip Classifier — Design Spec

**Date:** 2026-06-06 · **Approved:** yes (auto-mode; user away — run in background, report on return)

## A. Market-context signals (point-in-time, pre-listing info ONLY)
Features per IPO, computed from data already on disk:
- `ctx_nifty_mom_3m` — trailing 3-month Nifty return ending at listing date (nifty50.csv).
- `ctx_ipo_heat_90d` — number of IPOs (same segment) listed in the prior 90 days + the median
  listing pop of those prior IPOs (`ctx_heat_pop_90d`). Both from our own substrate, point-in-time.
- `ctx_sector_heat_180d` — median listing pop of same-broad-sector IPOs in the prior 180 days.
Testing: rank-IC + bucket lift vs 1y alpha, cross-regime (boom AND longterm), same machinery
style as weights/component_lift; OOS sanity on the 2026 holdout. Verdict per signal recorded in
rules/index.md (in-score ONLY if robust per the locked policy; else display-only; else rejected).
EXCLUDED by decision: gold/silver/crude/rupee (weak general link, new source maintenance).

## B. Short-horizon movement (1m/3m/6m MFE/MAE + timing)
Extend the existing MFE/MAE block in pipeline/07 + the merge to also emit
mfe/mae/mfe_lst/mae_lst/days_to_* for 1m, 3m, 6m (same math, more labels).
Substrate rebuild via the refresh rails: snapshot -> chain B -> goldens re-derive -> full suite.
Envelope invariant tests extended to the new horizons. No new pipeline; same two files.

## C. Hot-pop fade + SHORT score + play/skip categorization
- Analysis (new finding `m2_short_horizon`): listing-pop / 1m-move buckets -> subsequent path
  (1m->3m->6m->1y), incl. P(peak in first month), post-peak drift — quantifies "hot IPOs run
  20-30% in month 1 then fade" with maturity-gated cohorts.
- SHORT score: P(strong early move) proxy built from pre-listing features (GMP, subscription,
  heat, size, segment) trained point-in-time on listings ≤2025; LONG score = existing combined.
- Categorizer: quadrant of (SHORT, LONG) -> play-short / play-long / hold-patient / skip, with
  confidence from analog N + score spread. DISPLAY-ONLY (advisory) until OOS-robust per policy.
- Validation: trained ≤2025, validated on the 82-IPO 2026 holdout (the forward-test pattern);
  every short-horizon figure labeled EARLY READ where the cohort is young.

## Honesty rails
Point-in-time everywhere (no post-listing info in features); min-N floors; cross-regime checks;
the known truth stands unless beaten: exit-timing rules don't beat buy-and-hold at 1y+ — the new
question is ENTRY selection at short horizons, which is allowed to fail honestly.

## Success criteria
A: verdict (with numbers) for each context signal, registered. B: substrate carries the new
movement columns; suites green. C: the fade pattern quantified; per-IPO category + confidence
shown in the predictor output (display-only); holdout validation table delivered.
