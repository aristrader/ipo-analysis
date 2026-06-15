# A1c — banker-quality measure: build + verdict (2026-06-11)

Spec: `docs/superpowers/specs/2026-06-11-a1c-banker-quality-design.md`. Built TDD + 3-lens diverge +
independent adversarial review. Module `layer3/predictor/banker_quality.py` (transparent, PIT, NO ML);
harness `tools/research/a1c_banker_quality.py`; tests `tests/layer3/test_banker_quality.py` (8). The
construction: size+recency-weighted (H=3y), segment-specific, horizon-tapered with strict maturity-gating,
confidence-shrinkage toward the PIT segment base (k=5) — the principled "don't judge on count" replacement
for A1b's MIN_PRIOR/freq cliff.

## Verdict — **NO live-score change. coverage_guard (A1b) stays.** Two real findings, both display-only/dead.

### 1. RETURN arm (banker quality → sustained alpha): DEAD — confirms n12, across ALL horizons
Tested per-cell rank-IC of the banker-alpha-track vs `alpha_1m/3m/1y` + listing pop, shuffle placebo:
- `alpha_1y`: pooled IC −0.001, p=0.95, sign-flips across cells. `alpha_3m`: +0.024, p=0.19. `alpha_1m`:
  +0.04, p=0.10. None same-sign cross-regime; all inside the null. The standing n12 "no clean banker→alpha
  signal" holds at every horizon. Independent review reproduced the placebo (200×) and confirmed DEAD.

### 2. DOWNSIDE arm (banker quality → wipeout/dead-money): competitive but NOT robustly better → KEEP coverage_guard
- At a 0.40 threshold the shrunk score's recall collapses to 9.9% (miscalibrated cutoff). As a RANKER at
  matched fire-count (top-365) recall = 27.4% vs coverage_guard 24.6% — marginally better, and strict-PIT
  (no look-ahead) with a cleaner mechanism (no count-cliff). Per-cell IC modest (+0.12 MB-lt, +0.15 SME-boom,
  ~0 elsewhere). Independent review: competitive + cleaner + look-ahead-honest, but NOT a robust OOS
  improvement; replacing the incumbent adds churn/re-validation for no measured gain. **Shelved at parity**
  as the reference/cleaner mechanism — revisit if a regime shift widens its edge (NOT rejected on quality).

### 3. PRICING-DISCIPLINE → listing POP: REAL + cross-regime + placebo-clean, but caps DISPLAY-ONLY
The owner's horizon-split insight (short horizon = the allottee pop; long = company performance) surfaced this —
the 1y/3y-only test had missed it. A banker's prior **listing-pop** track predicts the new IPO's listing pop:
- per-cell IC MB-boom +0.05, MB-lt +0.10, **SME-boom +0.35**, SME-lt +0.15 → **positive in ALL 4 cells**,
  pooled +0.163, placebo **p=0.0**, **same-sign cross-regime**. The first banker signal to clear that gate.
- It predicts ONLY the pop: vs `alpha_1m` pooled +0.009 (p=0.94) — the pop does NOT carry into sustained alpha.
- **Incrementality (the deciding test):** partial rank-IC controlling for GMP / subscription —
  SME-boom holds (raw +0.35 → +0.146 | GMP, +0.124 | sub); MB-boom absorbed (→ ~0); **longterm cells
  UNTESTABLE — GMP/subscription coverage is 0 pre-2020** (the same wall that capped pe_vs_sector & H-MVP).
- **Why display-only:** (a) predicts the pop (allottee day-1), not from-listing alpha — it's APPLY-side
  CONTEXT, not a from-listing signal; (b) largely overlaps GMP, which the tool already uses; (c) incrementality
  is only boom-verifiable → cannot clear the cross-regime *incremental* bar for the live score. Real, honest,
  and useful as context — but not a scored signal under evolve-only-if-robust.

## Net
The owner's "don't judge on count" complaint was addressed (the shrinkage mechanism was built + tested and is
the cleaner reference); the "test different timeframes" nudge directly surfaced the pricing-discipline→pop
finding the long-horizon test had missed. Honest outcome: **zero live-score change**; A1b/coverage_guard remains
the live banker mechanism; the pop finding is logged display-only (a candidate APPLY-side context chip later).
Reproduce: `PYTHONPATH=. python tools/research/a1c_banker_quality.py`.
