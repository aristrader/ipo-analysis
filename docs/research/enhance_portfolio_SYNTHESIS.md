# Portfolio/scorecard enhancement — CONVERGED plan (2026-06-08)

Synthesis of 3 divergent lenses (enhance_portfolio_{investor,analytics,redteam}.md). The lenses
strongly agreed; the red-team found the CURRENT shipped numbers MISLEAD on 4 axes (all upward).
Trust-fixes are non-negotiable (this project's whole point is not misleading); enhancements are
ranked value-per-effort and pruned with YAGNI.

## PHASE 1 — TRUST FIXES (must; these correct misleading live numbers)
T1. **Median prominence + outlier decomposition.** The headline mean 2.09x hides: median position
    only 1.18x, win 59%, one 25.8x name carries it (drop-top-1 → 1.96x, drop-top-3 → 1.81x).
    Show median + P10/P90 + top-3 share NEXT TO the mean, equal prominence. (redteam#2, analytics#1)
T2. **Relabel "vs Nifty".** It is the average of per-call ₹1L-vs-index outcomes, NOT a single
    shared-capital portfolio curve. Rename to "avg per-call vs Nifty (same-window)" + caption.
    (redteam#3)
T3. **Simulation honesty above the table.** ~94% of the APPLY basket is historical_sim/backfilled,
    1 live. Move the "no live calls matured yet — this is mostly rehearsal/OOS, not a followed
    record" banner ABOVE the table; show the mode mix inline. (redteam#1)
T4. **Per-stock chart start points.** "at-IPO (if allotted)" starts at ~₹129k (pop baked in) while
    the others start at ₹100k → looks like same-start outperformance. Annotate the start gap +
    keep the "if allotted (lottery ~3.5%)" caveat visible. (redteam#4, investor trap)
T5. **Scorecard win-rule honesty.** Grading APPLY/AVOID on from-listing alpha excludes the pop →
    APPLY understated, AVOID overstated. Grade APPLY on the ALLOTTEE return (from issue) where we
    have it; keep AVOID from-listing; caption the asymmetry plainly (not "slightly"). (redteam#5)

## PHASE 2 — DEPTH (high value, all Small, ≥2 lenses endorsed)
D1. **"Beat buying EVERY IPO" baseline / lift.** Judge each hit-rate vs the unconditional
    segment×horizon rate (the field median is in the substrate). The cut that proves the calls add
    value over indiscriminate IPO-buying. (investor#1, analytics#2)
D2. **Best/worst position attribution.** Rank APPLY picks by ₹ P&L — surface the winners that carry
    returns + the wipeouts. Nearly free off simulate()'s per-position frame. (investor#2)
D3. **Bootstrap CI on the portfolio multiple.** Pure-Python random.choices resample (B=2000, fixed
    seed, 5th/95th pct). Stops 2.09x being read as precise. (analytics#3)
D4. **Edge decay over horizon.** Pivot the existing 1m/3m/1y scorecard side-by-side — build vs fade.
    Zero new data. (analytics#4)

## PHASE 3 — DEFER (M effort or 2nd-wave; not this pass unless quick)
real equity CURVE + max drawdown (investor#4, M) · counterfactual toggles skip-AVOID/top-decile
(investor#3) · scorecard cuts by sector/size (investor#5) · Smallcap250 benchmark for 2017+
(analytics#5). All good; queue after Phase 1+2 land.

## DO NOT BUILD (flagged as theatre/traps by the lenses)
Portfolio Sharpe/annualised-vol (no clean periodic returns; analytics) · parametric t-tests on
tiny skewed samples (analytics) · lump-sum-day-0 equity curve (fakes compounding; investor) ·
any curve/stat that drops delisted/wipeout members (survivorship; all three).

## ALSO: fix the misleading headline I already propagated
STATUS.md / DONE.md / commit messages headlined "2.09x vs Nifty 1.27x" without the median/
simulation caveats. Correct the STATUS/DONE wording to lead with "median followed call ~+18%,
mostly simulated" honesty (the mean is real but not the honest headline).

## Build order: Phase 1 (TDD) → review agent → Phase 2 (TDD) → review → test → fix STATUS/DONE.
