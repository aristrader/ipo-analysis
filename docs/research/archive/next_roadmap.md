# Next roadmap — ranked "what to build next" (2026-06-08)

> Owner-only research tool. Ethos: only-what-works (3-layer validated) · free data · no ML · analog-based.
> Grounded in: PRODUCT.md, STATUS.md, future_ideas.md, rules/index.md, microcap_extension_thinking.md.
> **Reality check first:** the four seed directions are NOT all greenfield. The track-record machinery (3)
> mostly EXISTS (calls_ledger ~5,170, forward test, monthly OOS, Telegram alerts, sim APPLY vs AVOID +34pp).
> The predictor (2) already shows closest analogs, confidence label, analog count + recency/boom-fraction.
> So the high payoff is in *closing the loop* (prove-it-forward) and *the one genuinely missing input* (news),
> not in re-building what's there. Effort S/M/L · payoff low/med/high.

## Candidates (assessed)

### A. Paper-portfolio sim of following the LIVE calls (seed 3, the missing piece)
One-line: a virtual ₹-sized book that applies/holds/exits per the bot's own live calls and tracks equity vs Nifty.
Who/how: gives the owner the one number he actually trusts — "if I'd done exactly what it said, where would I be."
Closes the loop between calls_ledger and a believable P&L. · Effort S (ledger + prices already exist; this is an
accounting layer + an app panel) · Payoff HIGH · Risk: allotment realism (flip EV is ~+2% after adverse selection —
must model the 3.5% median allotment prob, NOT assume fills) · Fits ethos YES (no new data, no ML) · Deps: calls_ledger,
data/prices, strat-flip-ev model.

### B. Monthly "were-we-right" scorecard as a first-class, dated artifact (seed 3)
One-line: freeze a monthly snapshot of every open/graded call + hit-rate by call type, kept as an append-only series.
Who/how: forward test already runs ~monthly; this makes it a *durable, comparable* record the owner can flip through,
and is what hardens the young OOS verdict. · Effort S · Payoff MED-HIGH (it IS the product's credibility) · Risk:
mostly cosmetic over run_forward_test; don't let it imply more certainty than the young sample supports · Fits YES ·
Deps: run_forward_test, calls_ledger.

### C. News/catalyst feed — SCOPE ONLY, free BSE/NSE announcements (seed 1)
One-line: pull the free structured BSE/NSE corporate-announcements feed for our ISINs; tag, don't yet trade on it.
Who/how: the single biggest *missing input* — price-only model can't tell an earnings beat from a pump. But it's a
real sub-project with three honest blockers (news→ISIN matching, good/bad classification without an LLM, edge may not
survive testing). · Effort: scope S, build+test L · Payoff: potentially HIGH, unproven · Risk HIGH (per future_ideas:
news edges arbitrage away fast; classification wants an LLM = cost + company-laptop data question = ethos tension) ·
Fits PARTIALLY (free data yes; "only what works" demands it pass the 3-layer test, which it may fail) · Deps: new
scraper, entity-matching (same infra F11 is gated on).

### D. Sharpen predictor — CONDITIONED scoring + confidence BANDS (seed 2)
One-line: show the score's analog-distribution as a band (P10–P90 already computed) and let scoring condition on a
second axis (e.g. sector × size) when N allows.
Who/how: closest-analogs + confidence label already ship; the incremental win is making the *uncertainty visible* (band)
and conditioning where min-N permits. · Effort M · Payoff MED (polish on an already-good surface; thin-cohort risk) ·
Risk: conditioning shreds N fast → "insufficient analogs" most of the time; must respect min-N floors · Fits YES ·
Deps: scorecard distribution (exists), MIN_N_HINT discipline.

### E. Microcap / wider-universe RISK screener (seed 4)
One-line: extend the survivorship/dead-money/wipeout/clean-compounder lens to seasoned NSE-Emerge+BSE-SME microcaps as a
RISK screener (never a return predictor). · Who/how: broadens the tool beyond the IPO event to where the same retail/thin
forces persist; bhavcopy + screener plumbing already exist. · Effort L (delisting spine + corp-actions + screener pulls
must widen to ~3–4k names; screener blocks hard) · Payoff MED (off the IPO-decision workflow the owner mainly uses) ·
Risk: scope creep; reverse-causation if universe defined by spot mcap (doc already solves this via turnover) · Fits YES
(explicitly framed risk-only, on-moat) · Deps: bhavcopy keep-all, delisting.csv widen, corp_actions widen.

### F. Day-1 EARLY-call accuracy harvest (own-add, tiny)
One-line: the EARLY_APPLY/AVOID day-1 reads are forward-only and "accuracy being measured" — just make sure each is
logged and auto-graded so the verdict actually lands. · Who/how: turns an open question into an answered one with near-zero
build. · Effort S · Payoff MED · Risk: only as good as the cadence of fresh IPOs · Fits YES · Deps: calls_ledger, notifier.

### G. Per-IPO "watch-after-listing" digest pushed at day 21 / 90 (own-add)
One-line: bundle the already-validated post-listing flags (persistence lean d21, capitulation F5e d90, corp-action top F10)
into one scheduled per-name nudge. · Who/how: the leans exist but are passive; this delivers them at the moment they matter. ·
Effort S-M · Payoff MED · Risk: alert fatigue (keep it strictly per-name, event-triggered) · Fits YES · Deps: notifier, F5e/F10/persistence.

## TOP 3 (with sequencing)

1. **A — Paper-portfolio sim of the live calls.** Highest payoff for the least build: it converts an already-rich
   calls_ledger into the one number the owner cares about (a believable equity curve), and it forces the honest
   allotment/adverse-selection model that prevents self-deception. Do first.
2. **B — Durable monthly were-we-right scorecard.** Small add on top of the existing forward test; it is the
   credibility spine and it *feeds* A (the sim needs the same graded outcomes). Sequence right after A so they share plumbing.
3. **C — News/catalyst feed, SCOPE STEP ONLY.** The biggest missing input and the owner's stated #1 gap, but it is an
   L build with real blockers, so commit only to the cheap scope-the-free-BSE/NSE-source step now; greenlight the build
   solely if coverage is good AND a catalyst tag survives the 3-layer test. Do third, time-boxed.

Reasoning: 1→2 close the prove-it-forward loop (seed 3) with mostly-existing parts and harden the young OOS story before
adding anything new; 3 then tackles the one input the model is genuinely blind to, but gated behind a scope check so we
don't sink L-effort into an edge that may arbitrage away.

## Anti-recommendations (shiny but low-value or against the ethos)
- **Swing-trade buy/sell (take-profit) calls — DO NOT BUILD.** Definitively rejected (2026-06-08): take-profit lifts
  win-rate but decapitates the right tail that carries returns (negative Δmean in all 4 regime cells). Re-litigating
  violates "only what works."
- **ML price targets / "predict the return."** Against the no-ML, analog-only design; small data; opacity. Seed-2 framed
  as "conditioned scoring" is fine ONLY as analog conditioning with min-N floors — not a model.
- **Intraday / daily buy-sell signals.** Daily prices only; stop-loss/exit rules lose to hold cross-regime (M1). No edge.
- **Over-building the predictor (seed 2 beyond bands/conditioning).** Closest-analogs + confidence already ship; more
  knobs here is polish, not payoff. Cap it at the visible-uncertainty band.
- **Microcap as a RETURN predictor.** Efficient-market turf, no edge — only the risk/dead-money/wipeout screener framing
  is on-moat. Don't let scope drift into "what return will this microcap give."
- **Paid news/data APIs for the catalyst feed.** Violates the free-data rule outright. Free BSE/NSE/RSS only.
