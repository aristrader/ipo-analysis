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

---

## FLOW FAMILIES — F2a-f, F7, F8  *(agent specs; status: READY)*

**Shared cluster builder:** cluster = connected component over IPOs (same type) whose [open,close]
windows overlap AND open_dates within W days. Baseline W=5; MANDATORY sweep W∈{2,3,5,7,10} — an
effect surviving only one W = curve-fit = rejected. Singletons = placebo group. Precompute:
cluster_id/size/listing_order/open_order. One parameterized builder feeds F2a-f, F7, F8.
All forward outcomes = listing-anchored (secondary buyer); exclude unreliable_coverage rows.
Cross-regime gate: headline cell must hold in boom AND longterm (N≥30) else "boom-only/MIXED".

### F2a — Within-cluster GMP rank (the owner's pattern)
L1: alpha_1m ~ gmp_rank_norm + cluster_FE; FALSIFIER: rank coef ≤0/insig. PLACEBOS: pseudo-clusters
from singletons by month + 1000× GMP-rank shuffles (must exit 90% band).
L2 table: [cohort,type,rank bucket{top/mid/bottom}] × {n, median pop, alpha_1w/1m, P10/P90, %pos};
"pop-then-bleed" contrast = alpha_1m − alpha_1w.
L3 grid: R1 buy bottom-rank member at listing; R2 buy bottom-2 (size≥3) × horizons {1w,1m,3m};
BH = equal-weight whole cluster. Failure: whole-cluster-junk (median gmp<0) — neglected≠cheap there.
N: MB-boom clusters ≈150-250; SME-longterm THIN.

### F2b — Listing-order tone-setting
L1: later-member open-gain ~ first_lister_day1_gain + own gmp + own sub (cluster SE); listings ≤5td
apart. PLACEBO: calendar-adjacent non-cluster lister. L2: spill by first-lister bucket {pop>10 /
flat / dud<−5} + decay by position 2 vs 3+. L3: R1 chase-tone when first popped; R2 value-of-skipping
when first was a dud × {1d,1w,1m}. Failure: chase when later member's sub<2x. N≈80-140 MB-boom.

### F2c — Ordinal fatigue in streaks
Streak = same-type opens each ≤G td apart (G sweep {2,3,5}); ordinal = position. L1: outcomes ~
ordinal + year_FE + log(size); fatigue must hit RETAIL sub harder than QIB (mechanism signature).
L2: ordinal buckets {1, 2-3, 4+} monotonicity. L3: R1 buy leader vs R2 buy fatigued tail × {flip,1w,1m}.
Failure: leader-chase under gmp>40 frenzy. MB ordinal-4+ THIN.

### F2d — Retail congestion tax
congestion_load = Σ issue_size of other overlapping books (same-type + all-type variants). L1: retail
sub ~ congestion (expect −) while QIB ~ congestion ≈ 0 (category placebo; if QIB falls equally →
macro, reject). L2: quartile dose-response retail vs QIB divergence + hidden-quality table (high
congestion × high quality tercile → fwd alpha). L3: R1 congestion-hidden quality (top-congestion ×
top-quality × sub<cluster-median) vs R2 same quality, low congestion × {1m,3m,6m}. R1 N≈40-70 (THIN).

### F2e — QIB rotation to later-closing book
MB clusters with staggered closes: sub_qib ~ close_order_norm + gmp + size + cluster_FE (expect +);
retail placebo must NOT tilt. L2 adds anchor_pct compounding. L3: buy later- vs earlier-closing
member × {flip,1m,3m}. Staggered-close size≥3 clusters RARE → bucket THIN everywhere.

### F2f — Mega-IPO shadow + drought rebound
is_mega = size ≥ p95 (per cohort+type); shadow = opening ≤S td after a mega's close (S sweep
{5,10,15}); drought = first open after ≥D td gap (D sweep {10,15,21}). L1: shadow → lower retail
sub/pop (controls: own gmp/sub); drought → higher. PLACEBO: pseudo-mega (random non-top-5%).
L2: days-since-mega recovery curve {0-3,4-10,11-20}; drought dose {15-25,26-45,46+}.
L3: R1 buy post-drought first-lister; R2 avoidance value of shadow × {flip,1w,1m}.
Failure: drought-rebound on junk (gmp<0). Boom droughts THIN (~15-30); SME droughts ≈ none.

### F7 — Disposition contagion / cold-streak survivors
trailing_cohort_gain = median return_from_listing_1m (and pop variant) of listers in prior T days
(T sweep {45,60,90}; same-type + all-type; null if <5 priors). L1: (i) retail sub ~ trailing gain
(expect +, the contagion); (ii) fwd alpha_3m ~ trailing gain (expect −, the tax); MUST survive
controlling trailing NIFTY (else it's generic momentum). L2: the SCISSORS chart — demand rises while
forward alpha falls across sentiment quartiles. L3: R1 buy cold-tape listers (bottom quartile) vs
R2 hot-chase (top) × {1m,3m,6m}. Failure: cold-tape × cold-Nifty (regime collapse, knife).
Holdout: 1m/3m only (6m too young).

### F8 — Unfilled-demand day-1 (undersubscription kink)
unfilled = max(0, 1−sub_total_x); day1_strength = gain_close − gain_open. L1: day1_strength ~
unfilled + sub_total + gmp (+FE) — unfilled must be INCREMENTAL; placebo kink at 2.0 must lose to
the real kink at 1.0 (RD flavor). L2: fine bins around sub=1.0 in [0.5,1.5]; opposing-force check
(deep undersub = junk signal vs clean-float mechanics — which dominates). L3: R1 mild-undersub band
buy at open {day-close exit, 1w, 1m}; R2 deepest-undersub quartile = the DECLARED knife cell
(report prominently). MB-boom undersub N<15 → primarily a LONGTERM + SME test (declared).

---

## PATH & GMP FAMILIES — F5a-f, F6a-d, T2g/T2i/T2j  *(agent specs; status: READY)*
Conventions: t=0 = listing day; alpha vs Nifty; exclude unreliable_coverage; min-N 30 (12-29 = "thin",
<12 suppressed); holdout = train 2006-2021 rules locked, test 2022-2026.

### F5a — Issue-price magnet
Approach episode: close enters [0.97,1.00)×issue having been <0.95×issue in prior 10d. Outcome 10d:
clear (>1.02×issue) vs reject (<0.97). FALSIFIER: P(clear) ≥ P(reject) or ≈placebo. PLACEBOS: 20d-MA
level + random level at equal distance. L2: by approach depth {−5/−10/−20%}: stall≥3d rate, clear
rate, dwell, conditional fwd-10d drift. L3 grid: {buy-on-touch vs buy-on-confirmed-clear} × depth;
failure: touch-buys on shallow approaches (dead money). N: 800-1200 episodes.

### F5b — Listing-day-high trapped-supply ceiling
Confirmed breakout: close>1.02×LDH held 3d; touch-and-fail: high≥0.99×LDH but never holds. Fwd-20d
alpha post-confirm vs post-fail. PLACEBO level: listing-day CLOSE (no overhang). L2: by days-to-first-
touch {≤10/11-30/31-60}: confirm rate, alphas, breakout volume ratio. L3: {confirmed-only vs naked-
touch} × touch-timing; failure: naked touches ≤10d (supply unabsorbed). N: 700-1000 breakouts.

### F5c — Volume-confirmed crossings
Confirmed = crossing-day volume ≥1.5× trailing-20d median (sensitivity 1.25/1.5/2.0×). Hold-rate(5d)
+ fwd-10d alpha confirmed vs naked; PLACEBO: shuffled volume labels. L3: {confirmed-only vs all} ×
{issue-clear, LDH-breakout, both}; failure: naked LDH (whipsaw). SME thin at 2.0×.

### F5d — Double-reference ordering
Both refs live (traded below issue + below LDH): P(clear LDH ≤60d | reclaimed issue first) vs not.
PLACEBO: arbitrary A→B level pairs. L2: 3-state transition matrix {below-issue / between / above-LDH}
at 20d/60d + dwell times. L3: {enter on issue-reclaim targeting LDH vs after LDH clear} × dwell
buckets; failure: reclaim-entry with dwell>30d (grind). N: 400-700.

### F5e — Capitulation flag (never reclaimed issue by 90d)
P(wipeout | flag) with the INCREMENTAL test vs existing N14 flags (must add lift beyond tiny-sales/
loss-making/obscure-banker). PLACEBO: never-reclaimed-listing-close (weaker ref). L3 = red-flag
screen {flag ×existing-flag-count 0/1/2+} → avoided-loss; report the screen's miss rate. SCORE
POLICY: display-only unless OOS-incremental. Wipeout-conditional cells thin.

### F5f — Round-number magnets
Tiers: A=×100/×50, B=×10, C=ugly. Stall-rate gradient A>C at equal distance, stratified by price level.
PLACEBO: round levels that are NOT the issue price (generic round-number psych vs issue-anchor —
both real, distinct claims). L3 2×2: {tier A vs C} × {touch vs clear}; failure: touch-buy tier A.

### F6a — GMP-surprise residual
surprise = adj_listing_gain − GMP/issue_price. Quintile → 1w/1m drift (must add beyond raw pop —
partial out). PLACEBO: stale 5d-before GMP must predict weaker. L3: {long Q5, avoid/short Q1} ×
{1w,1m,3m}; failure: Q5 at 3m (drift decayed). GMP pre-2019 sparse → boom-weighted, declared.

### F6b — GMP × retail-share (self-fulfilling)
Interaction GMP×retail_share on pop + 1w drift; PLACEBO: GMP×QIB-share must be ≪. L2: 3×3 GMP-tercile
× retail-share-tercile surface. L3: {apply only high-retail vs regardless} × GMP tercile; failure:
high-GMP×QIB-dominated. Corner cells structurally thin.

### F6c — GMP meaning flips by regime
GMP→1m-drift slope sign by regime {hot/neutral/cold} (interaction test; PLACEBO: shuffled regimes).
L3: regime-conditional GMP strategy (long cold-high-GMP, fade hot-high-GMP) vs regime-blind; failure:
regime-blind in hot. KEY THIN CELL: cold×high-GMP (cold suppresses GMP) — flag prominently.

### F6d — T+3 natural experiment
Clean-pre (≤Aug-2023) vs clean-post (≥Dec-2023), DROP Sep-Nov-2023 transition; GMP→pop slope/R²/
residual-SD comparison + fake-date placebo (Dec-2022). Confound: 2024-25 frenzy — partial out
IPO-market temperature. L3 = GMP trustworthiness for pop-sizing by era.

### T2g — Same-banker collision
Canonicalize lead_manager FIRST. Collision = same lead, windows ≤10td apart. Underperformance must
survive regime control; PLACEBO: different-banker same-window (calendar congestion vs banker effect).
L2: window tightness {same-week/≤10d/11-20d} + does the LATER one suffer more. N 150-400 pairs.

### T2i — Day-1 flipping proxy
flip = day1_volume/shares_offered; + day1→5 reversal. Top-quintile → lower 6m/1y alpha (partial out
pop). PLACEBO: day-20 turnover must NOT predict. MB only reliable (SME circuit distorts day-1 volume).
L3: {avoid high-flip, fade high-flip+reversed} × {1m,6m,1y}; failure: acting at 1m (unresolved churn).

### T2j — SME circuit-cage path signature
Matched |move| buckets: SME (5% bands) vs MB (20%) — monotone run length, days-to-MFE/MAE, fraction
of limit days, give-back. PLACEBO: large-MB that never hits bands. L3 entry-timing: {day-1 vs first
non-limit consolidation day} × trend-so-far; FAILURE (the practical warning): day-1 entry into a
down-trending caged SME — locked in while it steps down 5%/day, can't exit at limit-down.
Boom/2013+ finding by construction (SME barely existed before).
