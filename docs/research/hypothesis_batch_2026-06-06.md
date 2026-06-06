# Hypothesis Batch — 48 agent-generated hypotheses, tested (2026-06-06)

4 subagents (lenses: issue structure/pricing, demand/allocation, post-listing path,
fundamentals/governance) generated 48 hypotheses; deduped to ~34 testable features;
each tested: rank-IC + tercile alpha_1y spread across the 4 regime cells
(MB/SME × boom/longterm). Bar: same sign in all available cells, mean |IC| ≥ 0.08.
Full table: tools/research/hypothesis_batch.py output (re-runnable).

## The honest headline
**No new PRE-IPO signal cleared the robustness bar.** Every structural/demand/
fundamental idea (banker track record, pricing-in-band, anchor conviction, QIB-vs-
retail, GMP-vs-subscription disagreement, sales window-dressing, accruals, leverage
ramp, dilution, objects-of-issue, …) came out MIXED (sign flips across cells) or
THIN (insufficient cells). The existing score + crowded_window already capture the
predictable part; 30+ ideas now sit in the REJECTED registry so they are never
re-litigated without new evidence.

## Nuanced sub-verdicts (recorded, not folded)
- **pe_vs_sector** — MB-only LEAN-NEGATIVE (IC −0.10/−0.21, −43pp tercile spread in the
  2 cells where PE exists; SME has no PE data). Watchlist: re-test if SME PE ever lands.
- **qib_retail_ratio** — LEAN-POSITIVE (+0.05/+0.07/+0.08 in 3 cells): institutions-over-
  retail demand mildly good. Display-only candidate at best; not folded.
- **banker_prior_wipeout (point-in-time)** — directionally negative but weak (−0.0…−0.10);
  the binary obscure-banker flag already in-score captures most of it.

## Path/conditioning verdicts (POST-listing info — hold/exit decisions, never the pre-IPO score)
- **path_ratio_1m (ROBUST conditioning)** — month-1 up/down asymmetry (mfe/|mae| from
  listing) predicts the full year in all 4 cells (IC +0.23…+0.49, ~51pp tercile spread).
  This is the PERSISTENCE rule made tradable: a strong, shallow first month → hold;
  a weak, deep one → the year rarely recovers. (Overlap caveat: month 1 is inside the
  1y window; the effect size far exceeds the mechanical share.)
- days_to_peak_1y (IC 0.66-0.77) — MECHANICAL/descriptive (late peak ≈ kept rising);
  not an ex-ante signal. Confirms "winners peak late" persistence; rejected as a signal.
- turnover_to_size (IC 0.37-0.65) — LIFETIME turnover = look-ahead (winners stay liquid);
  descriptive only; rejected as a signal.
- lday_giveback / volatility / circuit_lock — mixed signs across cells; rejected.

## Where this leaves the system
- Score: 8 components; data_informed = downside 0.264 + **crowded_window 0.254** +
  multibagger 0.197 + return 0.185 + wipeout 0.099 (in-sample top-quintile +39.5pp).
- New conditioning guidance (display/report layer): month-1 path asymmetry.
- Registry: +~30 rejected entries — the "failed hypothesis list" the project wanted.
