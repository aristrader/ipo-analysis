# Tier-1 Wave-1a Verdicts (2026-06-06) — T2f, F3, F1

All three FALSIFIED — by their own pre-declared falsifiers/placebos. Scripts:
tools/research/tier1_t2f_f3.py · tier1_f1_anchor.py (re-runnable).

## T2f — vintage: calendar-year vs rolling regime → **YEAR WINS 4/4**
Nested adj-R² on alpha_1y & alpha_1m × boom/longterm: year adds +1.5–6.3pp beyond regime;
regime adds only +0.07–0.6pp beyond year. The Nifty regime (dir/vol/phase) does NOT subsume
vintage. CONSEQUENCE: year remains the gating variable for all Phase-2 conditioning; regime
features are weak controls, not replacements.

## F3 — regime-gated junk bounce → **FALSIFIED (on the demand-quality proxy)**
junk×bull did NOT out-peak junk×non-bull (MB: 9.7% vs 13.3% median month-1 MFE — opposite
direction; SME: flat). Placebo (200× shuffled regime labels): real gap fails p95 in both
segments. TP grid deltas ≈ 0–0.7pp. CAVEAT (declared): "junk" proxied by below-median GMP+sub
(no persisted per-row score); a point-in-time-score re-test is allowed ONCE, later. Junk×bull
cells thin (MB n=22).

## F1 — anchor-unlock supply waves → **FALSIFIED (placebo inverted)**
Post-2022 (treatment, 50% unlocks day-90, n=279): W90 median CAR **+0.10%**, P(neg)=48%,
dose-response Spearman **+0.058** (wrong sign), run-up interaction ≈ 0.
Placebo pre-2022 (NO day-90 tranche, n=144): W90 **−1.16%** — more negative than treatment;
the pattern fails the natural experiment completely. L3 buy-the-dip (E2, n=97): win 38%,
median −2.9%, P10 −19.7% — day-90 dips are losers losing, not supply air-pockets.
The Field&Hanka US lockup effect does NOT replicate for Indian anchor unlocks at day 90.
(Day-30: also null post-2022, +0.23%.) Event-calendar app feature stays useful as INFORMATION
(dates are real) but carries NO validated trading edge — chip it accordingly.

## Standing after wave-1a
The 8-component score remains unbeaten. Graveyard +3 families. NEXT in queue: F2a
(wallet-competition clusters — the owner's pattern; needs the cluster builder), F5b (LDH
trapped-supply), F6a (GMP surprise), F7 (disposition contagion).

---
# Wave-1b (2026-06-07) — F2a-f, F7, F8, F6a-d, F5b
Scripts: tools/research/wave1_flows.py · wave1_gmp_path.py (re-runnable).

## FALSIFIED / REJECTED
- **F2a within-cluster neglected-member (the owner's pattern):** hot members pop more (−0.49,
  mechanical) but NEGLECTED MEMBERS SHOW ZERO FORWARD CATCH-UP — IC(rank, fwd alpha_1m | cluster)
  = +0.005/−0.003/−0.002 at W=3/5/7. Robust null across the sweep. Falsified.
- F2b tone-setting: raw spill +0.248 → +0.048 after controlling own GMP (shared hype, not contagion).
- F2c ordinal fatigue: demand-side signature real on SME (retail −0.226 vs QIB −0.137 — the wallet
  mechanism shows) but no consistent price edge; MB weak. Mechanism-only, no trade.
- F8 unfilled-demand: inverted — undersubscribed are simply worse (fwd −6.5% vs −2.6%); junk
  signal dominates clean-float mechanics. n=140 (boom-MB 27, as predicted thin).
- F6b GMP×retail-share: NO interaction (IC 0.643 vs 0.670) — GMP transmits regardless of buyer mix.
- F6c GMP-by-regime: no sign flip (hot +0.06, cold −0.01; both ≈0).
- F6d T+3 experiment: transmission got LOOSER post-T+3 (IC 0.626→0.604; |error| 11.1→14.8pp) —
  opposite of hypothesis; 2024-25 frenzy confound noted. Falsified as stated.
- F5b LDH breakout: confirmed breakouts show NO acceleration (fwd-20d −1.1%, win 47%).
  ⚠ METHOD TRAP CAUGHT: the touch-and-FAIL cohort (−39.6%, win 3%) is LOOK-AHEAD-classified
  (knowing it "never confirms" uses the future) — descriptive only, never tradable. Recorded.

## SURVIVORS (the wave's harvest)
- **F7 DISPOSITION CONTAGION — the strongest result of the wave:**
  demand chase confirmed: IC(trailing-60d pops, retail sub) = **+0.454**;
  the tax confirmed: IC(trailing pops, fwd alpha_3m | Nifty-controlled) = **−0.088**;
  L3: cold-streak listers fwd 3m median **−0.9% (n=524)** vs hot-chase **−8.5% (n=555)** = **+7.6pp**.
  STATUS: VALIDATED-DIRECTIONAL → next: cross-regime cell check + OOS fold test (could refine or
  replace count-based crowded_window with outcome-based climate — the owner's tangent F12 idea).
- F2d congestion tax mechanism: retail −0.197 vs QIB +0.056 — the predicted asymmetry confirmed
  (mechanism supporting crowded_window; hidden-quality trade leg still untested).
- F6a GMP-surprise: weak lean (+0.048 after pop control; Q1 −7.9% vs Q5 −2.7%) — display-watch only.

## NEW FAMILIES from the owner (registered, queued)
- **F9 sector copycat decay** — Nth same-sector IPO in 12m progressively worse (testable now).
- **F10 early corp-action tells** — bonus/split within year 1: SME pump vs MB confidence
  (corp_actions.csv on hand; testable now).
- **F11 serial-promoter fingerprints** — same promoter group across listings (needs entity matching; gated).
- **F12 retail cumulative IPO P&L index** — outcome-based climate gauge to refine/replace count-based
  heat (directly supported by F7's result; high priority).

## QUEUE (wave-2 ready, specs in phase2_playbooks.md)
F4 bear-window stop-loss · F5a/c/d/e/f reference-point variants · T2a/b/c/e/g/h/i/j ·
F9/F10/F12 (new) · F3 one PIT-score re-test · F7 cross-regime+OOS confirmation (FIRST).
