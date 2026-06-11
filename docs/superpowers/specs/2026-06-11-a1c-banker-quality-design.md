# A1c — richer banker-quality measure: design spec (2026-06-11)

**Goal:** replace A1b's two coarse, count-based banker-flag legs (the thin-record `freq<12 & SME` leg and the
single lifetime good/bad quality flag) with a transparent, point-in-time banker-quality measure that judges a
banker on the **quality + scale + trajectory** of their book — and test, honestly, whether it earns a live slot.

**Path:** FULL (score-touching). Built TDD → independent adversarial review → evolve-only-if-robust gate.
**Authority:** `hypothesis_protocol.md` for test mechanics. NO ML (transparent formulas). Strictly point-in-time.

## Converged from the 3-lens diverge (test-design `a5bf7d6` · red-team `a1b0b36` · expand-space `aff1a6f`)
The lenses agreed strongly. The headline reframes:
1. **The DOWNSIDE use is largely already solved** (coverage_guard is live). A1c's value on the downside is a
   *cleaner mechanism* (shrinkage replaces the MIN_PRIOR/freq cliff; strict maturity fixes A1b's disclosed
   look-ahead) — it must NOT regress recall, but won't add much raw lift there.
2. **The RETURN (two-sided) use re-litigates n12** (which found NO clean banker→alpha signal). It starts
   **PRESUMED DEAD** and faces a higher bar. Highest false-positive risk = segment-composition leakage +
   SME-boom-only artifact + multiple-comparisons.
3. **Multiple comparisons is the dominant trap.** ~600 effective cells if we test everything naively → ~30
   spurious "winners." Must pre-register, keep the *promotion* bench tiny, one primary endpoint per arm.

## IN (the promotion bench — what can win a live slot)
**1. The unified banker-track score** — one construction, two targets:
- For banker `b` scoring an IPO at date `t`, segment `s`: take `b`'s prior IPOs in segment `s` that **listed
  before `t`**. Each prior `i` contributes weight `w_i = log1p(issue_size_cr_i) · 0.5^(age_years_i / H)`
  (size-damped × recency, half-life `H=3y`).
- **DOWNSIDE arm** target = bad-outcome indicator (wipeout|dead-money, `_bad_outcome_mask`).
- **RETURN arm** target = horizon-tapered alpha `a_i = Σ_h τ_h·α_h(i)` with taper `τ = {3m:0.45, 6m:0.30,
  1y:0.20, 3y:0.05}`, **each horizon dropped+renormalized if not matured by `t`** (maturity rule below).
- **Confidence-shrinkage (the principled "don't judge on count" fix):** `Q = (W·raw + k·μ_seg)/(W + k)`,
  `W = Σw_i`, `μ_seg` = the **PIT** segment-cohort base (over priors matured by `t`), pseudocount `k=5`.
  Count/evidence-mass sets *trust*, never the verdict. A 2-prior banker ≈ segment base; a 30-prior banker
  ≈ its own record. This dissolves A1b's MIN_PRIOR/freq cliff.

**2. Deterioration-trend** (the one orthogonal NEW dimension, expand-space top pick): is the banker's *recent*
book worse than its lifetime? PIT slope of bad-rate / recent-minus-prior alpha, floor ≥8 priors, else abstain.
Tested as a downside-risk modifier only.

## CUT (compute as descriptive/secondary only — NOT separate scored legs, to bound the test count)
C pricing-discipline (listing-pop track) · D consistency/hit-rate · #3 velocity (kept only as a *mechanism*
read paired with deterioration) · demand-generation · market-share/tier (≈ the size-weighting already in #1) ·
**# BRLMs (INFEASIBLE — `lead_manager` is a single name per row, verified)** · score×banker interaction (defer
until a banker signal earns its place). Rationale: all are redundant with #1's distribution or confounded, and
each standalone leg multiplies the test count → p-hacking. They appear in the harness as descriptive context only.

## The harness + the PRE-REGISTERED decision rule (lock before computing)
- **Two primary endpoints, one per arm:** (a) DOWNSIDE = pooled bad-outcome recall (the A1b bar: must NOT
  regress vs live coverage_guard 24.6%) + 4-cell discrimination (Wilson CI) + false-veto on the named-reputable
  list; (b) RETURN = incremental OOS top-quintile alpha lift of (live score + banker-Q) **over the live score**
  (not vs do-nothing), via the `a1_fold_test.py` fold harness. Everything else is secondary/descriptive.
- **Pre-registered params:** `H=3y, k=5, τ=0.45/0.30/0.20/0.05, BAD_RATE=0.40`; min-N floors (suppress<12).
  The headline uses these; a **sensitivity sweep** (H, k, τ) is a separate appendix — promote only if the
  verdict is a plateau, not a knife-edge.
- **Maturity rule (load-bearing):** a prior's horizon-`h` value is usable for scoring `t` ONLY if
  `prior.listing_date + h ≤ t`. Gate BOTH the alpha legs AND the bad-outcome target on maturity (this is the
  honest fix to A1b caveat #76; it will *lower* recall vs the peeking baseline — report that delta, don't hide it).
  `μ_seg` must also be PIT (priors matured by `t`), never the full-panel mean (that's leakage).
- **Placebo:** shuffle banker labels ≥100×, re-run the whole pipeline; report **clean excess over the null
  mean** (the null mean is ~+5pp mechanical segment-composition — cite clean excess, not raw lift).
- **Cross-regime gate (4-cell):** directionally positive in ≥3/4 cells AND CI-separated in ≥1. **SME-boom-alone
  = boom-only / NOT live** (every prior banker result lived only there).
- **n12 prior:** the RETURN arm is presumed dead; only a cross-regime, placebo-clean, *incremental* result
  overturns it. Downside and return arms sit on different evidentiary bars.
- **Promotion:** at most ONE leg enters the score; the rest are display-only and logged in `rules/index.md`
  with WHY. Any promotion → independent adversarial review → re-derive weights → review again. Default = nothing.

## Files
- Create `layer3/predictor/banker_quality.py` — pure, PIT, transparent construction (importable by `scorecard`
  only if promoted). Create `tools/research/a1c_banker_quality.py` — the harness (discrimination/recall/placebo/
  cross-regime + the fold A/B + the sensitivity appendix). Tests `tests/layer3/test_banker_quality.py`
  (synthetic frames: maturity gating, shrinkage toward base, size/recency weighting, segment split, abstain).
- Touch `scorecard.py` ONLY if a leg is promoted (add an `OBSCURE_BANKER_MODE`/component path).

## Honest expected outcome
Per all three lenses: the downside arm likely **matches** coverage_guard at similar recall with a cleaner,
look-ahead-honest mechanism (a mechanism win, possibly worth adopting); the return arm most likely lands
**display-only / rejected** (n12 holds). A "nothing beats A1b" result is a valid, honest success here.

## Success criteria
A robust, review-approved banker-quality signal that ≥ matches A1b on the downside bar (cleaner mechanism) and/or
a cross-regime incremental return signal — OR an honest, logged "nothing beats A1b" verdict. Suite + verify green.
