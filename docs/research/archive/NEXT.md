> ⚠️ **SUPERSEDED AS THE LIVE MENU (2026-06-09):** the current, deduped, status-tagged backlog is
> `improvement_backlog.md`. This doc remains as the deeper Thread A/B/C *reasoning* (a feeder); pick work from the backlog.

# What's next — synthesis & recommendation (2026-06-08)

Synthesizes three scouting passes (all in docs/research/):
- `next_roadmap.md` — product/roadmap thinker (internal)
- `next_factor_research.md` — new IPO-signal hypotheses (web + literature)
- `next_capabilities_scan.md` — infra/tooling/automation we could add (web)

## The big picture
The repo is more built-out than it feels — the predictor, ledger, forward test, alerts, sim are
all live. So the highest-leverage work splits into THREE threads, not one:

### Thread A — CLOSE THE LOOP (make what exists credible & tangible)  ← best boost-per-effort
All Small effort, free data, pure-ethos fit, no new scraping:
1. **Paper-portfolio sim of the live calls** — an equity curve "what if I'd followed every APPLY,
   with an honest allotment/adverse-selection fill model (~+2% real, not naive)" vs Nifty. The one
   number the owner will actually trust. (roadmap #1)
2. **Monthly "were-we-right" scorecard** — small add over the existing forward test; the credibility
   spine; shares plumbing with #1. (roadmap #2)
3. **Calibration tracking on the ledger** — reliability curve / Brier: do our stated odds mean
   anything? (capabilities #7)
4. **Wilson/Jeffreys credible intervals on every base rate** — honest small-N framing. (capabilities #4)

### Thread B — CHEAP PIPELINE HARDENING (start accumulating data we'll want)
5. **GMP-history daily capture** — log the GMP *series*, not just point-in-time; an own dataset no
   free tool keeps. (capabilities #5)
6. **Post-listing monitor via daily bhavcopy** — auto-grade maturing calls + fire day-21/90 leans
   from data we already pull. (capabilities #1)
7. **Pandera schema gate** on substrate + staging CSVs — typed contracts; catches refresh drift
   verify.py only checks loosely. (capabilities #2)

### Thread C — EXTEND THE ANALYSIS (the original mission; each = a 3-layer test)
8. **Pre-IPO discretionary accruals (Modified-Jones)** — best evidence-to-effort new signal;
   upgrades the proven binary n8 accrual flag; inputs already in screener data. (factor #1)
9. **Unblock P/E-vs-sector for SME + EV/Sales for loss-makers** — graduate the watchlisted
   `pe_vs_sector` (already leans −43pp MB) by computing issue-time multiples ourselves. (factor #2)
10. **SME→Mainboard migration** as an outcome class + feature — the big unmodeled SME escape from
    the dead-money trap; free dated source. (factor #3)

### The one everyone names but nobody should rush: NEWS/CATALYST FEED
Owner's stated #1 missing input, but a Large build with real blockers (ISIN matching, good/bad
classification wants an LLM = ethos/company-laptop tension, edge may not survive testing).
**Commit only to the cheap SCOPE step now:** probe the free NSE/BSE corporate-announcements API for
coverage of our ISINs (capabilities #3). Gate the build on coverage + a passing 3-layer test.

## RECOMMENDATION (sequencing)
1. **Start with Thread A (paper-portfolio sim first).** Biggest boost: it turns ~5,170 logged calls
   into a believable track record the owner trusts — and it's a few days, free, on-ethos.
2. **Fold in Thread B #5–#6 cheaply alongside** (they start data accruing for everything later).
3. **Pick ONE Thread C hypothesis** (accruals) to keep the research engine alive.
4. **Do the news SCOPE pass** — decide build/no-build from real coverage data, not a guess.

## Anti-recommendations (don't build — tested/ethos)
Swing-trade take-profit calls (rejected 2026-06-08), ML price targets, intraday/daily buy-sell,
over-building the predictor past a confidence band, microcap as a *return* predictor (only the
risk-screener framing is on-moat), any PAID API, LLM news-classification on the company laptop.
