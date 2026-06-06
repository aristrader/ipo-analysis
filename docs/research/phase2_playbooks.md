# Phase-2 Playbook Specs — implementation-ready 3-layer tests

Built from `deep_hypotheses_2026-06.md` (the curated families). Every spec follows the 3-layer
protocol: L1 existence (+falsifier/placebo) → L2 magnitude & shape → L3 PLAYBOOK (pre-declared
entry grid, payoff distribution vs buy-and-hold, failure cells; full grid reported; cross-regime +
2026-holdout validation where horizons permit). F1 spec written by the main session; F2–F8 + T2
specs consolidated from the playbook agents (appended below as they land).

---

## F1 — Anchor-unlock supply waves  *(spec status: READY)*

**Mechanism.** SEBI: anchor shares lock 50% to day-30, 50% to day-90, for issues OPENING ≥ 2022-04-01
(single 30-day cliff before — the built-in placebo). Unlock day ≈ allotment+30/90; we proxy
allotment ≈ listing−3 trading days (T+3 era) / listing−6 (pre-Dec-2023); robustness: ±3-day window
absorbs the proxy error.

**L1 EXISTENCE.**
- Event study, MB with anchor_allocation_cr>0, listed ≥2022-04-01: mean/median ALPHA (vs Nifty,
  from daily prices) over windows W30=[d27,d36] and W90=[d87,d96] vs baseline B=[d45,d80].
- FALSIFIER: W90 alpha not below baseline (one-sided), or no dose-response (below).
- PLACEBO 1: same windows for 2010–2021 listings (no 90-day tranche existed) — the W90 dip must be
  ABSENT/weaker. PLACEBO 2: random non-event windows (d60, d120) must show no dip.

**L2 MAGNITUDE & SHAPE.** Tables (rows = anchor-share terciles × run-up terciles; MB only; boom era):
`{n, pct_with_negative_W90_alpha, median_W90_alpha_%, P10, worst, median_dip_duration_days,
median_recovery_days (alpha back to pre-window level), volume_ratio_W90_vs_baseline}`.
Dose-response check: Spearman(anchor_share, W90 alpha) < 0. Interaction cells: × subscription
tercile (thin-demand bites harder) × momentum sign into d85. Unlock-COLLISION column: count of other
IPOs with a d90 in the same ±5 days; split low/high collision density.

**L3 PLAYBOOK — "buy the unlock dip".** Pre-declared grid (fixed BEFORE looking):
- Entry rules (rows): E1 = buy at close of day-2-of-decline inside W90 (first 2 consecutive negative
  alpha days); E2 = buy at d93 unconditionally if W90 alpha ≤ −3%.
- Horizons (cols): +2w, +1m, +3m (alpha).
- Report per cell: n, win_rate, median, P10, P90, and Δ vs buy-and-hold-from-d85.
- FAILURE CELLS (pre-declared): sub_total_x < 2 (no organic bid); bear regime during window
  (Nifty 60d return < 0); anchor_share top-tercile × run-up bottom-tercile (anchors dumping a loser).
  Expectation: the dip-buy works EXCEPT in these cells — report them separately.
- Counterfactual honesty: compare against simply holding through the dip (the existing truth says
  holding wins unconditionally — the playbook only matters if entry timing adds alpha for NEW money).

**Features.** unlock30/90 = listing_date + offset (trading days via the Nifty calendar);
anchor_share = anchor_allocation_cr/issue_size_cr; run-up = alpha from listing to d85; daily alpha
series from data/prices joined to nifty50.csv. Expected N: ~350–450 post-2022 MB with anchors;
collision/interaction cells will run THIN (flag <30).

---

*(F2, F7, F8 — flow families; F3, F4 + T2 regime families; F5, F6 + T2 path families: agent specs
appended below on arrival.)*

---

## REGIME FAMILIES — F3, F4, T2b-T2f  *(agent specs; status: READY)*

**Regime standardization (all specs, point-in-time at listing):**
DIR = Nifty trailing-60d return sign/terciles · VOL = 20d realized vol terciles ·
PHASE = distance from trailing 252d high (at-high ≥−3% / mid / correction <−12%).
Cohort-separate tercile cuts (no leakage). RUN T2f FIRST — it decides whether every other
test gates on regime or calendar-year.

### F3 — Regime-gated junk bounce + take-profit
L1: {score bottom-tercile × DIR-bull} median mfe_lst_1m vs {junk × non-bull}; Mann-Whitney.
FALSIFIER: junk×bull MFE ≤ junk×bear or ≤ all-IPO. PLACEBO: 1000× shuffled regime labels, must beat p95.
L2: 3×3 {score tercile × DIR} table: N, median mfe_lst_1m, P10/P90, days_to_peak, terminal 1m alpha
(timing-tax gap); SME-vs-MB elasticity split.
L3 grid: entry = listing close iff junk×bull; TP {+15/+25/+40%} × hold-cap {21d/42d} → win-rate,
median, P10/P90 vs B&H-1m. Failure cells: tight TP in non-bull. N: junk×bull ≈250-300 (SME ≈120 thin).

### F4 — Regime-conditional stop-loss
L1: in IPOs whose 3m window overlaps a >−10% Nifty drawdown (labs: 2008-09/2011/2020Q1/2022), does a
fixed SL beat B&H median 3m? FALSIFIER: SL ≤ B&H in every lab. PLACEBO: same SL in calm windows.
L2: per-lab N, B&H vs SL medians, whipsaw rate, median mae_lst_3m, SL-benefit vs drawdown depth.
L3 grid: SL {−12%/−20%} × {hard/trailing} in bear-DUR cohort → win-rate/median/P10/P90/whipsaw%.
Failure: trailing-SL in choppy bears. N thin in 2008 (≈25-40) — corroboration not proof.

### T2b — First-week tape × regime (hold-horizon)
L1: {wk1_ret top-tercile × DIR}: fwd 1m/3m alpha; FALSIFIER: strong-wk1-in-bear ≥ in-bull.
L2: 9-cell table + give-back rate (>50% of wk1 gain returned by 3m) + mae_lst_3m.
L3 grid: {hold-3m / sell-at-wk1 / sell-first-down-week} × {bull/bear gate}. N: ×bear ≈200.

### T2c — Regime-transition fragility (defensive overlay)
L1: bull-listed month-1-strong, transition = Nifty 90d-forward < −8%: fwd 6m alpha vs bull-persists.
L2: give-back pp (mfe_lst_6m − terminal), recovery-by-1y. L3 (TRADEABLE exit trigger, point-in-time):
exit/trail/hold when Nifty crosses {20d-MA / −5% / −8%} below listing-date level. N≈60-90 transition (thin).

### T2d — Crowded-window × regime (scorecard refinement)
L1: crowd-tercile × DIR interaction on 1y alpha; FALSIFIER: flat interaction → no conditioning needed.
L3: weight-variant grid {only-in-bull/always/never} × {0.5×/1×} judged by OOS top-quintile lift under
the locked SCORE POLICY. Longterm bull-crowd labs: 2007, 2017.

### T2e — Recovery odds by listing PHASE
L1: among mae_lst_3m < −20%: recovery-to-breakeven by 6m/1y rate, at-high vs correction listings.
FALSIFIER: at-high recovery ≥ correction recovery. L3: cut-vs-hold conditioned on {PHASE=at-high ×
dd > −20/−30%} → 1y payoff vs B&H. Failure: cutting shallow dips of correction-phase listings.

### T2f — Rolling-regime vs calendar-year vintage  **(RUN FIRST)**
Nested regressions: alpha_1y ~ year-dummies vs + {dir60, vol20, phase}; both nest directions;
ΔR² + collinearity (VIF); repeat for 1m alpha, multibagger, wipeout. Winner declared only at ≥5/6
cells; outcome governs the gating variable for ALL other Phase-2 tests.
