# Extension roadmap — beyond IPOs (captured 2026-06-01, so the thinking isn't lost)

> Status: STRATEGY NOTE, not committed work. The IPO tool is finished first. This records the
> reasoning from the user discussion about extending the framework to the broader market.

## The question
Should we extend this analysis framework (risk analysis, long-term hold, financial patterns, sector
analysis, movement/exit lens) from IPOs to ALL listed stocks (Mainboard + SME)?

## The verdict: not big-bang — STEPWISE, edge-targeted, framed as RISK not RETURN

### Why not the full "predict all stocks" version
- **The IPO event is the moat.** An IPO is information-poor, hype-prone, retail-dominated, and full of
  exploitable structure (issue price, listing pop, OFS, subscription, GMP, allottee-vs-secondary,
  pop-fade). Our edge (+55pp 3y ranking, wipeout/dead-money anatomy) comes from that inefficiency.
- **Remove the event → general stock-picking**, the most studied/competitive/efficient problem in
  finance. The analog *predictor* doesn't transfer; any edge there is a known, arbitraged factor.
- **Scope reality:** ~5,000+ names × decades × full feature set = a different project, huge compute,
  and every survivorship-honest / cross-regime guarantee needs re-validation. Risks diluting the
  near-complete IPO tool.

### What DOES transfer (our differentiators)
Survivorship-honesty + the movement lens (reach/exit, no-stop-beats-hold, the barbell) + the
dead-money trap + the wipeout anatomy. These are truths about **illiquid, retail-dominated small/micro
caps** — exactly where retail loses money and where we have an edge.

## The stepwise plan (each step = a separate module, reuses the spine, can't destabilize the IPO tool)
**Criterion for picking a slice:** go where our edge transfers (illiquid/inefficient/retail), not where
it doesn't (efficient large/mid caps).

1. **STEP 1 — Microcap / SME-seasoned small-cap RISK & MOVEMENT screener.** Best first slice: it's the
   ring directly outward from our SME IPOs (which season into microcaps), the data exists (bhavcopy +
   screener), and our edge transfers strongest. **Build a SCREENER, not a return predictor:**
   - risk screen: dead-money / wipeout / illiquidity flags (already validated on IPOs),
   - movement/exit patterns (reach, no-stop truth, barbell),
   - quality screen (the clean-compounder = low-debt × high-ROE).
   Frame = "where does retail lose money in small caps, and how to avoid the trap" — on-moat, off the
   crowded return-prediction turf.
2. **STEP 2+ — only after Step 1 proves value.** Other slices by the same edge-transfer criterion.
3. **Sectors = a LENS/dimension within a universe** (a cut, like we already do), NOT a unit of
   extension — unless a sector behaves so distinctively it earns its own module.
4. **Large/mid caps, general return prediction, "all stocks"** = explicitly NOT early steps (efficient,
   huge, low edge). Deliberate later decision if ever.

## Near-free adjacency (stays entirely in our lane)
Track our EXISTING IPO cohort as it **seasons** into regular stocks (longer horizons, post-lock-in
behavior). Cheap, coherent, no new universe.

## Design discipline for any extension
- Separate module; reuse `layer3/spine.py` + method spine; never destabilize the IPO predictor.
- Define the universe + the HONEST question it answers (risk/movement, not return) up front.
- Same rigor: survivorship-honest, cross-regime, min-N floors, distributions over means.
- Prove value on the slice before funding the next.

## Sequencing vs the IPO tool
Finish + polish the IPO tool FIRST (eval report / interaction layer / DRHP financials in flight). The
microcap step is queued AFTER, as a deliberate, scoped decision.
