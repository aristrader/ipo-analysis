# Layer 3 — analysis (direction sketch, not yet built)

All three run off the same `returns_summary` + feature table; each builds on the prior. Build order:
**3a descriptive → 3b analog predictor → 3c backtester → (optional) live refresh.** Details settled per-phase later.

## 3a — Descriptive pattern reports (foundation; slow-changing; also validates the data)
Aggregate stats by segment, e.g.: avg/median listing gain (MB vs SME); % opened above/below issue; GMP
accuracy (how often a positive GMP actually opened up; positive-GMP-but-opened-below count); % multibagger /
positive / underwater at 1/3/5/10y; avg subscription by sector/mcap; sector & mcap performance tables.
Output: report + charts + base rates. Re-runs as new IPOs accumulate.

## 3b — Analog predictor / scoring (the centerpiece)
Given a NEW IPO's features (sector, mcap bucket, subscription, GMP, valuation, fresh-vs-OFS, profitability…):
find the most SIMILAR historical IPOs → summarize their outcome distribution (median return, 1y alpha, %
beat-issue, range) → produce an expected-outcome + score + "what to expect / what similar companies did."
- **Approach: analog/base-rate, NOT black-box ML** — transparent (show the comparables), avoids overfitting.
- **Critical discipline (this is where deferred A4 lands):** sample-size guards. Sector×mcap×subscription
  slices shrink fast; show n, widen the slice when sparse (sector-only → all-IPO base rate), never present a
  tiny-n average as a confident prediction.

## 3c — Strategy backtester
Test concrete rules (apply+flip on listing; buy-on-listing hold 1y; buy-after-X%-dip; etc.) across the universe;
report return / alpha vs Nifty50(+smallcap) / hit-rate / drawdown. Honesty requirements:
- **Point-in-time only** (no look-ahead; no post-hoc reclassification).
- **Execution realism** — allotment probability (hot IPOs hard to get), listing-day liquidity (SME realizability),
  rough transaction costs. State assumptions explicitly.
- Report **alpha**, not raw return.

## (optional) Live refresh
A predictor is only useful for new IPOs → a light pipeline to append newly-listed IPOs + re-pull recent prices,
keeping the tool current. Small add-on once the engine exists.

## LOCKED design decisions (2026-05-31, with user)
- **Output: BOTH** a readable report (Part A) AND a query tool (Part B) — built as TWO properly-planned tasks, report first.
- **Score = a SCORECARD of component scores (0-100 each), not one number.** Components, each computed transparently
  from the analog cohort's realized outcomes (and each displayed): **return-potential** (cohort alpha percentile),
  **multibagger-odds** (% of analogs ≥2x/5x), **downside-safety** (inverse of % wiped-out/deep-drawdown/below-issue),
  **liquidity** (realizability), **quality** (profitable/margins/low-debt). User sees the profile.
- **Combined IPO score = weighted blend of components.** Weights set two ways: (1) user-picked PRESETS
  (conservative=weight downside / balanced / aggressive=weight return+multibagger); (2) DATA-INFORMED — backtest
  each component's historical predictive power (lift/hit-rate) and weight the ones that actually worked; transparent
  ("we weight X most because it predicted best") and itself an insight. GUARDRAIL: weights derived from data are
  validated cross-regime (2006-19 vs 2020-25) before trusting; keep it rank-by-lift, not a black-box optimizer.
- **The loop:** each component is a testable signal → backtester measures its lift → sets its weight → and you can
  backtest "buy high combined-score IPOs" vs the do-nothing baseline.
- **Rigor = hypotheses + cross-regime check** (A4 resolved): boom-era findings validated on the 2006-19 cohort; always show N.

## Cross-cutting (decide at Layer-3 design time — deferred A4)
Validation rigor: treat boom-era findings as hypotheses; validate on the 2006-2019 cohort (different regimes)
as out-of-sample; always report sample size + base rate. Survivorship & liquidity handling per Layer-2 decisions.
