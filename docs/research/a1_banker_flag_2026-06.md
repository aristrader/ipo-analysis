# A1 — obscure-lead-manager flag: size/quality redefinition + verdict (2026-06-09)

Resolves backlog A1 (seeded by B1 `miss_mining_2026-06.md`). The "obscure lead manager" wipeout
red-flag (one of the 3 N14 validated flags) was **frequency-based and quality-blind** — it fired when
a banker had `< 12` IPOs *in our data window*. B1 proved this false-vetoed reputable but UNDER-SAMPLED
banks (Nuvama, Morgan Stanley, Smart Horizon, Choice, Indorient) and was the **sole blocker on 34 of 52
missed winners** on the recent cohort; 12/34 of those bankers have ≥10 IPOs in the full data (pure
coverage artifact). This task redefines the flag, backtests it cross-regime under the locked
**evolve-only-if-robust** policy, and records the verdict.

Harness: `tools/research/a1_banker_flag.py` (candidate discrimination + false-veto + placebo) and
`tools/research/a1_fold_test.py` (OOS top-quintile lift A/B). No scipy (Wilson CI from `spine`).

## Candidates considered
- **current (freq<12)** — the OLD rule. Quality-blind; the documented artifact.
- **(a) size-aware** — freq<12 but never fire on a large Mainboard issue (`type==MB & issue≥₹50cr`).
- **(b) quality-aware PIT** — *chosen*. Fire iff the banker's PRIOR IPOs (≥ `MIN_PRIOR=5`, listed
  STRICTLY before this IPO) failed at ≥ `BAD_RATE=0.40` (wipeout|dead-money). **ABSTAIN (never fire)
  when the prior record is thin (<5)** — we do NOT fall back to frequency (that re-introduces the
  artifact). So the flag fires only on an EVIDENCED bad track record.
- **(c) hybrid** — freq<12 AND small/SME AND NOT (clean ≥5-prior record). Catches more small issues
  but keeps a frequency leg (partial artifact) and discriminated worst cross-regime.

## (1) Cross-regime bad-outcome discrimination — bad% WITH vs WITHOUT the flag, per N14 panel
`bad = wipeout OR dead-money` (same mask as `risk_assessment`). Wilson95 CI in brackets. lift_pp =
bad%_flagged − bad%_clean (a real risk flag should be POSITIVE).

**current (freq<12)** — fires 430, evaluable 2323:
| panel | N_flag | bad%_flag (CI) | N_clean | bad%_clean (CI) | lift_pp |
|---|---|---|---|---|---|
| MB-boom | 65 | 1.5 [0,8] | 325 | 0.0 [0,1] | +1.5 |
| MB-longterm | 119 | 30.3 [23,39] | 348 | 23.0 [19,28] | +7.3 |
| SME-boom | 185 | 27.6 [22,34] | 763 | 16.1 [14,19] | +11.4 |
| SME-longterm | 61 | 19.7 [12,31] | 457 | 19.5 [16,23] | +0.2 |
→ meaningful (CI-separated, material) in **1/4** panels (SME-boom). MB-boom base rates ~0; SME-longterm null.

**(b) quality-aware PIT** — fires 177, evaluable 1716:
| panel | N_flag | bad%_flag (CI) | N_clean | bad%_clean (CI) | lift_pp |
|---|---|---|---|---|---|
| MB-boom | 11 | 0.0 [0,26] | 329 | 0.3 [0,2] | −0.3 |
| MB-longterm | 56 | 26.8 [17,40] | 192 | 17.2 [13,23] | +9.6 |
| SME-boom | 75 | 38.7 [28,50] | 673 | 14.4 [12,17] | **+24.3** |
| SME-longterm | 35 | 22.9 [12,39] | 345 | 17.7 [14,22] | +5.2 |
→ POSITIVE in **3/4** panels; SME-boom strongly CI-separated (38.7 vs 14.4). MB-boom is the lone
negative but on ~0 base rates (11 flagged, 0 bad vs 0.3% clean — noise, not a real reversal).

(a) size-aware and (c) hybrid both under-perform (b): (a) stops firing on MB entirely so loses the
MB-longterm signal; (c) goes NEGATIVE in SME-longterm. (b) is the cleanest cross-regime discriminator.

## (2) False-veto reduction
**Named reputable banks tagged (full-window IPO count → # flagged):**
| banker | full-window IPOs | current | (a) | **(b) chosen** | (c) |
|---|---|---|---|---|---|
| Nuvama | 11 | **11** | 0 | **0** | 0 |
| Morgan Stanley | 8 | **8** | 0 | **0** | 0 |
| Smart Horizon | 25 | 0 | 0 | **0** | 0 |
| Choice | 13 | 0 | 0 | **0** | 0 |
| Indorient | 13 | 0 | 0 | **0** | 0 |
| Arihant | 11 | **11** | 7 | **0** | 4 |
| Anand Rathi | 24 | 0 | 0 | 12 | 0 |
→ (b) exonerates ALL the B1-named reputable banks (0 flags). It DOES flag 12 Anand-Rathi IPOs and 1
Motilal — but only where their *PIT prior record* actually failed ≥40%, which is the intended behaviour
(evidence-driven, not name-driven), and those are MB-longterm-era rows, not the recent missed winners.

**B1 missed-winner un-veto (independently recomputed from `miss_mining_grades.csv`):** of the **34
obscure-banker-ONLY false-negatives**, the NEW definition un-vetoes **33** (only Vegorama / Corporate
Makers still fires). Every B1-cited recoverable winner — Park Medi, Sambhv Steel, KSH, Samay,
BharatRohan, LG Electronics India, Influx Healthtech, Sai Parenteral — is cleared. This is the
single decisive false-veto win.

**Of all 430 IPOs the OLD rule flagged, (b) un-flags 407** (bad-rate of the un-flagged = 22.9%) and
keeps 23 flagged (bad-rate 30.4%) — i.e. the IPOs it KEEPS flagged are genuinely worse, and the bulk
it drops were the frequency artifact. (The 22.9% bad-rate among un-flagged is segment-mix driven —
mostly SME — not a sign the dropped flag was discriminating; see caveats.)

## (3) Placebo (shuffle banker labels, 100 shuffles, pooled lift)
| candidate | real lift | null mean±sd | p(null≥real) |
|---|---|---|---|
| current | 7.8pp | −0.04 ± 2.05 | 0.00 |
| (a) | 10.5pp | 2.23 ± 2.52 | 0.00 |
| **(b)** | **16.9pp** | 5.82 ± 3.64 | **0.00** |
| (c) | 9.5pp | 2.24 ± 2.68 | 0.01 |
→ (b)'s real lift sits firmly in the right tail of the shuffled null → discrimination is NOT mechanical.
**Honesty note:** the null MEAN is positive (~5.8pp), so part of (b)'s lift is mechanical — banker
prior-bad-rate correlates with segment composition (SME-heavy bankers carry higher base risk). The
"clean" excess over the null is ~11pp, not the full 16.9pp. Still clearly significant.

## (4) Evolve-only-if-robust: OOS top-quintile lift A/B (`a1_fold_test.py`)
Does folding the NEW def into the live `wipeout_safety` score component DEGRADE OOS lift? (The locked
bar: a new signal stays in the weighted score only if it doesn't degrade OOS top-quintile lift robustly.)

**1y horizon** (high-N test folds):
| cutoff | n_test | CUR_lift | NEW_lift | delta |
|---|---|---|---|---|
| 2021 | 811 | 21.3 | 21.9 | +0.6 |
| 2022 | 664 | 22.6 | 24.1 | +1.5 |
| 2023 | 426 | 7.1 | 7.1 | 0.0 |
→ **better 2, same 1, worse 0** — NEW never degrades, marginally improves.

**3y horizon** (thin test folds):
| cutoff | n_test | CUR_lift | NEW_lift | delta |
|---|---|---|---|---|
| 2021 | 211 | 52.9 | 39.9 | −13.0 |
| 2022 | 65 | 0.0 | 54.6 | +54.6 |
→ **better 1, worse 1** — MIXED, but on tiny folds (65–211 test rows) → high variance, not decisive
either way. The `wipeout_safety` weight is small (≤0.09) in every fold, so the score impact is minor.

## VERDICT — **LIVE** (wired into `wipeout_flags` / `_query_flag_series` / `risk_assessment`)
The NEW quality-aware PIT definition (`OBSCURE_BANKER_NEW = True`) is kept LIVE because it:
1. **Improves cross-regime bad-outcome discrimination** — 3/4 panels positive (vs the old rule's 1/4
   meaningful), SME-boom CI-separated at +24pp;
2. **Eliminates the documented false-veto** — un-vetoes 33/34 B1 missed winners; exonerates every named
   reputable bank; fires only on EVIDENCED bad track records;
3. **Does not degrade OOS lift** at the high-N 1y horizon (better 2 / same 1 / worse 0), and is placebo-clean.

The 3y fold ambiguity is on too-thin folds to override the consistent 1y result + the discrimination +
the false-veto win. This is the conservative call: NEW dominates OLD on the flag's stated purpose (catch
bad outcomes) *and* fixes the documented harm, with no OOS degradation where N supports a read. The OLD
frequency rule is retained behind `OBSCURE_BANKER_NEW=False` purely for the A/B harness.

Parameters (in `scorecard.py`): `OBSCURE_MIN_PRIOR=5`, `OBSCURE_BAD_RATE=0.40`. Chosen as round, defensible
defaults (5 = a minimal track record; 40% bad ≈ ~2× the SME segment base) — NOT tuned to maximize the fold
lift (that would overfit). Sensitivity not swept; see caveats.

## Caveats for the adversarial reviewer to scrutinize
- **Abstention shrinks coverage.** NEW is evaluable on 1716 rows vs the old rule's 2323 — it is SILENT on
  607 thin-record bankers. Honest (no false fire) but it means genuinely-tiny brand-new shops with NO
  prior record are NOT flagged by this signal. The tiny-sales / loss-making flags still cover many of those;
  whether the abstention leaves a real gap on first-time-banker SME wipeouts is untested here.
- **MB-boom panel is uninformative** (~0 base rates both sides) — the −0.3pp there is noise, not a reversal,
  but I cannot *prove* the flag helps in MB-boom. The cross-regime claim rests on MB-longterm + SME-boom.
- **Placebo null mean is positive (~5.8pp)** → ~1/3 of the headline lift is mechanical (segment composition).
  Real clears it (p=0.00) but the "true" banker-quality signal is ~11pp, not 16.9pp. Don't over-cite 16.9.
- **3y fold is mixed and thin** (65–211 test rows). The favourable verdict leans on the 1y folds. If the
  adversarial reviewer weights 3y more, the verdict is "no-degrade / neutral", not "improves" — it would
  still pass the conservative evolve-only-if-robust bar (don't degrade) but the upside claim weakens.
- **Parameters un-swept.** `MIN_PRIOR=5`, `BAD_RATE=0.40` are reasoned defaults, not optimized. A reviewer
  should confirm the discrimination + un-veto results are not knife-edge at these thresholds.
- **The 33/34 un-veto is a counterfactual** (flag removed, nothing else re-derived) — same caveat B1 flagged;
  it is an upper-ish bound on clean recoverable regret, not a guaranteed gain.
- **PIT in the live (asof=None) path uses the banker's FULL history**, which is correct for a not-yet-listed
  query (every substrate IPO is prior to it) but means a *backtest* must always pass `listing_date` to avoid
  look-ahead. `_obscure_banker_series` does this per row; verified by `test_point_in_time_prior_only`.

## Reproduce
```
PYTHONPATH=. .venv/bin/python tools/research/a1_banker_flag.py     # discrimination + false-veto + placebo
PYTHONPATH=. .venv/bin/python tools/research/a1_fold_test.py 1y    # OOS lift A/B (1y; pass 3y for 3y)
PYTHONPATH=. .venv/bin/python -m pytest tests/layer3/test_banker_flag.py -q
```

## ADVERSARIAL REVIEW VERDICT (2026-06-10): DOWNGRADE TO DISPLAY-ONLY — NOT LIVE
Independent skeptic reproduced all numbers. The NEW def is genuine + look-ahead-clean BUT does not clear the live bar:
- BIGGEST: abstention HALVES bad-outcome recall (25.4%→13.2%); 78 real small-shop SME wipeouts the old rule caught
  are now missed (none are the reputable-artifact type the fix targets) — trades a false-veto for a worse false-negative.
- "3/4 panels" is really 1 CI-separated (SME-boom) + 1 directional-overlap + 2 noise. "Improves OOS" overstated:
  higher-N 3y fold (n=211) DEGRADES. Placebo survives (~11pp clean). Params SME-boom-robust but headline knife-edge.
ACTION TAKEN: `OBSCURE_BANKER_NEW=False` (reverted live flag to legacy freq<12 baseline). NEW code retained behind the
toggle for the A1b hybrid. Re-promotion bar: recall must NOT regress.
