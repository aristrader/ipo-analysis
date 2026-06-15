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

---
# Wave-2 part 1 (2026-06-07) — substrate tests (tools/research/wave2_substrate.py)

## ⭐ F7 GRADUATES: VALIDATED CROSS-REGIME (4/4 cells)
Cold-tape minus hot-tape fwd-3m edge: boom/MB +3.1pp · boom/SME +10.1pp · longterm/MB +18.2pp ·
longterm/SME +2.6pp. OOS (thresholds trained ≤2021, tested ≥2022): cold −2.6% vs hot −5.8%
(+3.2pp, right direction; cold n=57 — post-2022 was mostly hot tape).
STATUS: VALIDATED. NEXT: OOS fold test as a climate component (median-pop-based trailing climate)
— candidate to upgrade/augment count-based crowded_window in the score.

## Everything else in this batch: REJECTED (honest nulls)
- F12 size-weighted retail-P&L index: WORSE than simple median-pop climate (IC −0.02/−0.03 vs
  −0.09); median-pop (= F7's basis) is the best climate gauge. Size-weighting rejected.
- F9 sector copycat decay: IC −0.012; pioneers −13.1% vs 4th+ −10.8% — no decay (slightly opposite).
- F4 bear-window stop-loss: stops LOSE even in bear windows (SL12 −12.0% / SL20 −9.1% vs B&H −5.8%).
  The no-stop-loss truth is now unconditional AND conditional.
- T2b first-week×regime: bull −8.5% vs bear −10.0% — no gate.
- T2c transition fragility: +6.5% vs +6.9% (transition n=22 thin) — none detected.
- T2e recovery by phase: 20%/16%/21% — no phase effect on recovery odds.
- T2g same-banker collision: −4.5% vs −5.2% — null (also under congestion control).
- T2h ASBA refund echo: IC **−0.179** — OPPOSITE of pump: concurrent unblocking = congestion drag.
  Reject echo; consistent with the F2d retail-congestion-tax mechanism.
- T2j SME circuit-cage: inconsistent (SME peaks later on small moves 11v8d, EARLIER on big 40v52d).

## Remaining queue (price-path scan, post-compaction): F5a/c/d/e/f, F10 (early corp-action tells),
T2i (flipping), T2a (day-180 unlock). Gated: F11 serial promoters, F3 PIT re-test.

---
# Wave-2 part 2 (2026-06-07) — price-path scan + unlock/corp-action + fold tests
(tools/research/wave2_pricepath.py, wave2_unlock_corp.py, climate_fold_test.py)

## ⭐ F5e GRADUATES: CAPITULATION FLAG — VALIDATED CROSS-REGIME, NO LOOK-AHEAD
Flag = never closed above (adjusted) issue price in trading days 1–90 (knowable at day 90).
Flag-rate 12% (n=261/2174). Bad-outcome (wipeout/dead-money) rate 55% vs 13% without.
INCREMENTAL to the N14 prospectus flags at EVERY flag count: lift +39pp (0 flags) / +44pp (1) /
+45pp (2+). NO-LOOK-AHEAD test — forward 1y alpha measured from d91 (after flag knowable):
capit −35.3% (win 19%) vs clean −18.1% (win 37%); negative gap in all 4 cells
(boom/MB −7.5pp · boom/SME −24.0pp · longterm/MB −14.8pp · longterm/SME −32.7pp; boom/MB
bad-outcome cell immature — too young to die). STATUS: VALIDATED, display-only red flag per the
score policy (post-listing monitoring flag, not a pre-listing score input). USE: day-90 portfolio
checkpoint — "still below issue after 90 days = exit review", alongside the N14 badge.

## ⭐ F10 SURVIVOR (THIN n=31): EARLY CORP-ACTION = EUPHORIA TELL
Bonus/split with ex-date 30–365d after listing (18 bonus + 14 split matched). These follow huge
run-ups (median +184%) and then CRASH: fwd-3m alpha after ex-date −22.2%, win 16% — vs matched
(same type, run-up ±25pp) pseudo-event controls +2.2%, win 55%. NOT run-up mean-reversion.
MB worse (−78.5%, n=18). Timing-dose null (occurrence matters, not when). Endpoint alpha_1y still
+12.8% vs all-IPO −12.8% (they were winners overall — the action marks the TOP, not a bad company).
STATUS: validated-thin, display-only EXIT flag ("early bonus/split after a big run-up = sell
signal"). N too thin for score entry; revisit as sample grows.

## F7 FOLD TEST: does NOT enter the score
Trailing median-pop climate component (cold→high), folds 2021/2022/2023 × 1y/3y: improved OOS
top-quintile lift in 1/5 splits (max +0.1). F7 is a SHORT-HORIZON (3m) timing signal; the score's
1y/3y selection horizons don't capture it (crowded_window already covers long-horizon climate).
STATUS: stays VALIDATED as a finding + display-only regime read ("hot tape = wait, cold tape =
engage"); not a score component. Score remains 8 components.

## F3 PIT RE-TEST (gated item, now closed): REJECTED
Junk = bottom-tercile point-in-time score. The bull-gate FLIPS across cohorts: boom junk×BULL
mfe_lst_1m +10.5% (P≥15%: 45%) vs junk×BEAR +6.9% (27%) — but longterm junk×BEAR +18.2% (60%)
BEATS junk×BULL +13.4% (44%). Not cross-regime; terminal alpha_1m negative everywhere (−5..−10%).
Original rejection CONFIRMED with the proper PIT junk definition. F3 closed.

## Everything else: REJECTED (honest nulls/inversions)
- F5a issue-price magnet: FALSIFIED BY PLACEBO. 4472 episodes: issue level clear 33%/reject 65%,
  placebo 0.90× level 37%/62% — identical. No breakeven-anchor magnet; any overhead level rejects
  weak stocks. Dose runs OPPOSITE the anchor story (deep approaches clear MORE, 41% vs 29% —
  momentum). Touch-buy = dead money everywhere (median fwd-10d −2.1%, win 40%).
- F5f round-number tiers: NULL. Stall/clear/reject flat across A/B/C tiers (36/35/32% clear).
- F5c volume-confirmed reclaim: INVERTED as a buy signal. Confirmed crossings hold better 5d
  (58% vs 48%) but fwd-10d alpha is WORSE (−3.0% vs −1.4%) — reclaim-day volume spike =
  distribution, not accumulation. Reject.
- F5d double-reference ordering: MECHANICAL/CONFOUNDED. Reclaimed-issue-by-d60 → 57% clear LDH by
  d120 vs 15% never-reclaimed — but that's mostly "weak stocks stay weak" + the path constraint
  (must pass issue to reach LDH). Descriptive only; F5a's placebo says levels per se carry nothing.
- T2i day-1 flipping: INVERTED. High day-1 turnover → BETTER alpha (IC +0.103 on 1y,
  pop-controlled; Q5 −14.5% vs Q1 −30.2%; placebo day-20 turnover clean at −0.009). Day-1 volume
  is a DEMAND signal, not flipping churn. Hypothesis rejected; inversion noted as display-context.
- T2a day-180 unlock: WEAK/NOT TRADEABLE. Crossed design half-works: pre-Aug-2021 cohort dips at
  its 1y unlock (W365 −1.94%, 60% neg) and is clean at the placebo W180 (+0.54%) — but the
  post-2021 cohort dips at BOTH windows (−0.82%/−1.02%), so attribution is unclean; magnitude
  ~1–2% over 12 trading days ≈ costs. Reject as a trade; consistent-with-mechanism noted.

## PHASE-2 RESEARCH PROGRAM: COMPLETE (except F11, gated on entity-matching infra)
Final tally across all waves: ~33 tests run · 3 graduates (crowded_window IN-SCORE 0.254;
F7 disposition contagion VALIDATED display; F5e capitulation flag VALIDATED display) ·
1 thin survivor (F10 exit tell) · 2 mechanism confirmations (F2d congestion tax, F2c SME fatigue) ·
1 display-watch (F6a GMP-surprise) · everything else honestly killed.

---
# Swing-trade take-profit test (2026-06-08, owner idea — tools/research/swing_tp_test.py)
ENTRY = listing close; SELL first day closing >= +X%, else hold to 1y; vs buy-and-hold to 1y.
VERDICT: REJECTED as a strategy, CONFIRMS the no-take-profit truth — and shows WHY, with numbers.

The median/mean SCISSORS (n=2279, all listed):
- buy&hold 1y: median −6.7% · MEAN +40.7% · P90 +140% · win 46%
- take-profit +20%: median +21.2% · MEAN +1.0% · P90 +28% · win 67%
Take-profit makes you WIN MORE OFTEN (67% vs 46%) and lifts the median hugely — it FEELS great —
but it guts the MEAN (+1% vs +40.7%) and decapitates the P90 (+28% vs +140%). IPO total return is
carried by a few multibaggers; selling them at +20% throws that away.
CROSS-REGIME (Δmean TP20 − hold, negative = hurts): boom/MB −9.7pp · boom/SME −47.2pp ·
longterm/MB −36.9pp · longterm/SME −51.1pp. Negative in ALL 4 cells. (Δmedian positive in all 4 —
the trap: hit-rate up, wealth down.)
CONDITIONAL ENTRY (month-1 strong, the validated persistence lean, n=769): hold MEAN +103.7%,
P90 +222% vs take-profit +20% mean +19%. The BETTER the entry, the MORE take-profit costs — you're
capping your best names. So a good entry signal makes HOLDING more valuable, never take-profit.
USE: this is the definitive teaching example of the right-tail truth. Logged in future_ideas.md;
the bot will NOT emit "sell at +X%" calls. A descriptive "touched +X% today" info-ping is the only
honest version (no action implied).

---
# Thread C — new-signal hypotheses (2026-06-08; scope-first per protocol)
2 of 3 were DATA-GATED on scoping (the discipline working as intended); 1 testable.

## H2 pe-vs-sector — REPLICATES both segments (boom), → DISPLAY-ONLY (not score)
tools/research/h2_pe_vs_sector_sme.py. Rich issue-time P/E vs sector median → underperformance.
- SME: IC(rel_PE, alpha_1y) −0.245, rich +4.0% vs cheap +52.9% = −48.9pp (n=68). STRONG.
- MB: IC −0.066, −13.1pp (n=161) — same direction, confirms the prior MB-only finding.
- CROSS-REGIME GATE FAILS: SME is boom-only (longterm SME has ~0 P/E data) — cannot validate on
  2006-19. Per "boom findings are hypotheses until they hold longterm" + evolve-only-if-robust,
  it CANNOT enter the score. PLACEBO/FALSIFIER (added 2026-06-08 to meet the 3-layer bar):
  1000x shuffle null mean ~0.00, real IC −0.245 at p=0.019 (SURVIVES); random-feature placebo at
  noise (~1 SD for n=68). VERDICT: graduate watchlist/blocked → DISPLAY-ONLY (both segments, boom);
  placebo-confirmed real, but n=68 + SME-not-cross-regime-testable keep it out of the score.

## H1 accruals (Modified-Jones DCA) — DATA-GATED (parked)
Substrate has sales/PAT/total_assets by year but NO receivables and NO cash-flow-from-ops —
Modified-Jones needs ΔReceivables + CFO to separate discretionary accruals. Not computable from
current data. To pursue: re-scrape screener for receivables + CFO (a data project), THEN test.

## H3 SME→Mainboard migration — DATA-GATED (parked)
No migration flag/date in the substrate; needs a new free source (Chittorgarh report 123 / BSE /
NSE migration list). Scope-the-source-first before any test. Descriptive-finding candidate.

---
# Thread C round 2 — expanded hypothesis space (2026-06-08; divergence agent generated, all tested)
The "diverge before testing" step I'd skipped, done properly. 3 genuinely-new second-order
hypotheses (cross-checked not-already-tested), tested with placebo/falsifier. ALL REJECTED — honest.
tools/research/threadC_new_hypotheses.py.
- **H-C1 margin-expansion vs sales-only growth: REJECTED (opposite + sign-flip).** Among growers,
  margin-EXPANDERS underperformed eroders (1y −2.6pp, 3y −17.1pp; IC ~0) and the sign flipped across
  regimes (boom +5.6pp, longterm −6.7pp). Not the predicted "quality growth wins."
- **H-C2 sales-accel × demand divergence: REJECTED (fails placebo).** The predicted asymmetry showed
  (high-sub accel beat decel +7.1pp; low-sub ~flat −2.7pp), passing the directional falsifier — BUT
  the 1000× shuffle placebo put it WITHIN NOISE (p=0.156), and longterm is thin (n=19, no
  cross-regime). Suggestive, not distinguishable from noise → not a signal.
- **H-C3 same-banker pipeline congestion: REJECTED (null).** Congested (LM ≥1 IPO in prior 30d)
  −12.5% vs solo −12.7% = +0.2pp. No effect (consistent with the earlier T2g banker-collision null).
NET: 0 new validated signals; the placebo caught H-C2 (which the falsifier alone would have passed).

## B1 — two-sided miss-mining of recent-cohort calls (2026-06-09; EARLY READ, data as-of 2026-06-06)
Per-IPO point-in-time grade of all 364 IPOs listed in the last ~12mo (analog pool = prior-only; weights
per-month prior-only; calls.py verdict logic). Full writeup: `docs/research/miss_mining_2026-06.md`;
grades: `data/master/review/miss_mining_grades.csv`.
- **Confusion matrix:** TRUE_POS 68 · FALSE_POS 59 · FALSE_NEG 52 · TRUE_NEG 158 (+27 flat/not-applied).
  APPLY hit-rate 68/154 = 44.2% (Wilson95 36.5–52.0). APPLY allottee median +7.0% / mean +28.6% / 0 wipeouts
  vs whole-cohort median −5.1% — the ranking adds value even this young.
- **FALSE-POS (capital loss, n=59, ≈−₹2.18M/₹1L):** a pure flag BLIND SPOT (0 flags on all 59); the tell was
  WEAK DEMAND — sub_total_x median 2.2× vs 6.6× for winners, 32/58 <3× subscribed; SME/small-issue took the
  worst hit (−48% median). GMP did NOT separate. → seeds a low-subscription guard (display-first, must pass 3-layer).
- **FALSE-NEG (missed winners, n=52, ≈₹3.82M/₹1L, allottee median +50%):** obscure-banker flag is the SOLE
  blocker on 34/52; 17 are top-quintile (would flip APPLY, ~₹0.93M recoverable); 12/34 bankers have ≥10 IPOs
  in full data (artifact). **Obscure-banker false-negative hypothesis CONFIRMED.** → seeds A1 (banker-flag fix).
NET: 2 backlog seeds (A1 banker-flag fix = do-first; new low-sub FALSE-POS guard = downside-first). EARLY READ —
re-run as the cohort matures; labels are realized-to-date, not 1y/3y verdicts.
