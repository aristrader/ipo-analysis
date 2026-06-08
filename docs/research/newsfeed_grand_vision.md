# The Grand Vision — from IPO terminal → all-market signal engine (started 2026-06-08)

A staged extension LADDER, not a build plan. Maps the owner's far-stretched north star and what each rung
costs. Ethos that MUST survive every rung: free-data · NO-ML-for-prediction (analog/comparables) ·
cross-regime validated · survivorship-honest · only-ship-what-survives-the-3-layer-test · honest-uncertainty ·
single-owner · git-local · company-laptop. The "honesty moat" is the product — a rung that breaks it is a
downgrade even if it "works".

## The ladder at a glance
```
  RUNG 0  (here)  IPO terminal: rate · apply/avoid · post-listing hold/exit leans · track record · alerts
  RUNG 1          NEWS for hold/exit  — dated ISIN-keyed announcement feed on the cards   ← first rung, pays now
  RUNG 2          NEWS-DRIVEN buy/sell calls for IPO names (catalyst-tagged, tested)
  RUNG 3          UNIVERSE EXPLOSION — extend tool from IPOs-only → ALL listed stocks
  RUNG 4 (north)  FUSION — technicals + fundamentals + news → one honest buy/sell/hold signal
```

---

## RUNG 1 — News for hold/exit  (effort: M · de-risked)
**Unlocks:** every IPO Detail / tracking card gains a dated, ISIN-matched announcement stream — so a "+20% in
3 days" move stops being unexplained. Turns the post-listing hold/exit *leans* (RUNG 0) into *informed* leans:
"persistence-exit lean + a results announcement yesterday" reads differently than the same move with silence.
**New data/infra:** the FREE NSE corporate-announcements API (already scoped VIABLE — `tools/research/
scope_news_feed.py`): HTTP 200, ~18-28 items/active name, carries `sm_isin` (news→stock matching SOLVED for
free), `an_dt`/`dt`, `desc`/`attchmntText`, `smIndustry`. Build: ONE scraper (reuse `scrapers/nse_session.py`)
→ `data/live/` staging keyed on `sm_isin` (NEVER the frozen substrate) → render on cards. No classification
needed for v1 — a raw dated feed is already useful.
**Hard problems:** rate-limiting/session-cookie fragility (NSE blocks); de-duping multi-filing events;
attachment text is messy (PDF subjects). All tractable; none touch a money number.
**What could go wrong:** feed staleness presented as live (mitigate: reuse the existing staleness alarm + mode
labels); scope-creep into classification before the raw feed proves useful.
**Honesty moat:** PRESERVED. It's a data-display surface, not a signal — no score change, nothing to overfit.

## RUNG 2 — News-driven BUY/SELL calls for IPOs  (effort: L)
**Unlocks:** the first genuinely *event-driven* call. RUNG 0's entry side is weak (buy-after-fall rejected,
breakout falsified, issue-magnet placebo); a real catalyst (earnings beat, large order, regulatory clear) is
the one new entry signal that *could* earn its keep. Exit side gains a catalyst overlay (sell-on-bad-news).
**New data/infra:** a classification layer over RUNG 1's feed — catalyst type + good/bad/neutral. Two honest
routes: (a) keyword/rule taxonomy (transparent, no-ML, laptop-safe) over `desc`; (b) a bounded LLM tag of the
subject line (tension with no-ML + laptop + cost — keep it as a *labeller*, never a predictor). Then the
HARD requirement: a 3-layer hypothesis test (`hypothesis_protocol.md`) that catalyst-tagged entries/exits
*actually* beat the do-nothing baseline, cross-regime. Register the verdict; kill honestly.
**Hard problems:** news-reaction edges are famously arbitraged away fast (the move is often gone by the time a
free daily feed sees it — we have DAILY prices, not intraday); good/bad classification is genuinely hard and
the most ethos-risky step; survivorship + look-ahead traps in any event-study (don't tag with hindsight).
**What could go wrong:** shipping a catalyst call that's really a placebo (mitigate: falsifier discipline,
this is exactly what the 3-layer protocol is for); LLM-labeller drift; the edge being real but un-tradeable on
daily bars (then it's display-only, like `tradeable_upside`).
**Honesty moat:** AT RISK but DEFENSIBLE if the protocol is obeyed — a catalyst call ships ONLY if it survives
OOS cross-regime lift, else it's display-only. The moat is the gate; respect it and the moat holds.

## RUNG 3 — Universe explosion: IPOs-only → ALL listed stocks  (effort: XL)
**Unlocks:** the tool stops being IPO-shaped and becomes a whole-market terminal — rate/track/alert ANY of
~2,000+ listed names, not just recent IPOs. This is the precondition for the north star (fusion needs a full
universe to be interesting). Also unlocks a portfolio/watchlist tracker over real holdings (see tangents).
**New data/infra:** (a) a full-universe identity table (NSE/BSE equity lists — we already have
`exchange_lists.py`); (b) daily OHLCV for thousands of names not just 2,383 IPOs — bhavcopy is per-DAY
all-market (we already pull it for IPOs), so the marginal cost is *storage + a daily merge*, not new sources —
this is the cheap part; (c) the EXPENSIVE part: ongoing quarterly FUNDAMENTALS for thousands of names
(screener blocks aggressively, 1-worker + cooldowns — a full-universe quarterly pull is a multi-day,
fragile, rate-limited grind). (d) daily pipeline SCALE: run order, incremental updates, resume-safety at
2000× the row count.
**Hard problems:** the IPO analog method ("show similar past IPOs") doesn't transfer cleanly — a 15-year-old
listed name has no "IPO cohort"; need a new comparables frame (sector × size × regime). The boom/longterm
cross-regime split was IPO-cohort-shaped; a whole-market history needs its own regime taxonomy. Fundamentals
freshness becomes a per-name SLA problem. Survivorship honesty gets harder (delistings across 20 years of the
whole market, not just IPOs).
**What could go wrong:** the daily pull becomes a maintenance burden that eats the single owner's time; data
quality dilutes (per-row tiers across 2000 names); the analog moat doesn't generalize and tempts a slide
toward ML to "scale". 
**Honesty moat:** STRAINED. The discipline (min-N, distributions, cross-regime, flag-don't-assign) all still
apply but at 2000× the surface area — honesty becomes an *operational* cost, not just a design choice.

## RUNG 4 — NORTH STAR: technicals + fundamentals + news fused into ONE signal  (effort: XL)
**Unlocks:** a personal "signal terminal" — for any name, one honest buy/sell/hold read that fuses tape
(TA), value/quality (FA), and catalysts (news), each component validated, each shown with its evidence.
**New data/infra:** mostly assembled by RUNGs 1-3. (a) TA: we ALREADY have daily OHLCV — the honest subset is
trend/momentum/volatility/liquidity indicators that survive cross-regime (MA-cross, ATR, volume regime);
the curve-fit trap is oscillator-zoo parameter-tuning (RSI thresholds, MACD periods) — TEST each, ship only
survivors, exactly like signals today. (b) FA: from RUNG 3's quarterly pull — growth, margins, leverage,
accruals (the parked accruals red-flag, `future_ideas` Thread-C). (c) News: RUNG 2's catalyst tags.
**Fusion WITHOUT ML/overfitting:** keep the SCORECARD method we already use — independent validated components,
each with a data-informed (backtested-lift, rank-IC, cross-regime) weight; a component enters the fused score
ONLY under the locked "evolve-only-if-robust" policy (improves OOS top-quintile lift across splits, else
display-only). Fusion = a weighted scorecard of *already-individually-validated* signals, NOT a learned
combiner. The registry (`rules/index.md`) governs what's in-score vs display-only vs rejected.
**Hard problems:** the combinatorial test space explodes (TA×FA×news × MB/SME × boom/longterm = many cells,
each needs min-N) — multiple-testing / p-hacking risk is the dominant threat; component correlation
(TA-momentum and news-catalyst aren't independent); regime-dependence of weights (what works in a boom fails
in a drawdown — needs the regime overlay tangent).
**What could go wrong:** the honest answer for most names is "hold / insufficient edge" — a fused signal that
mostly says "no clear call" is *correct* but feels underwhelming; pressure to over-fit weights to look
decisive. The right posture: a confident "no edge here" IS the product.
**Honesty moat:** PRESERVED IF the scorecard discipline holds — this is the SAME method as today, just more
components. The moat survives precisely because fusion ≠ ML; it's transparent weighted validated parts.

---

## Adjacent tangents the owner didn't name (natural fallout of the rungs)
- **Watchlist / portfolio tracker (S-M, unlocks at RUNG 3):** track real holdings across all names, P&L vs
  Nifty (our alpha frame already), per-holding hold/exit lean + news. Likely the *most-used* personal feature.
- **Alerting beyond IPOs (S, extends RUNG 1 bot):** the Telegram bot already exists — extend it to fire on a
  watchlist name's catalyst or signal flip. Cheap, high daily value.
- **Personal "signal terminal" home (M, RUNG 4 surface):** one board — holdings · watchlist · today's
  catalysts · today's signal flips · regime banner.
- **Market-wide REGIME OVERLAY (M, enables honest RUNG 4):** today's cross-regime split is a *validation*
  device; promote it to a *live* market-regime banner (breadth, index trend, volatility) so the fused signal
  and weights adapt to boom-vs-drawdown — directly answers RUNG 4's regime-dependence problem.
- **Event-study lab (M, byproduct of RUNG 2):** a reusable harness to test "does catalyst X move price?" —
  pure research, feeds the registry, no product surface.

## The honest framing
This is YEARS of optionality, not a sprint. The natural sequence is the ladder as numbered — each rung is a
precondition for the next (news feed → catalyst calls → universe → fusion), and effort climbs S→M→L→XL→XL.
**The first rung that pays for itself is RUNG 1 (news for hold/exit):** the data is already scoped VIABLE and
FREE (ISIN is in the NSE payload), it's a Medium build reusing existing infra, it touches NO money number so
it can't break the honesty moat, and it immediately makes EVERY existing post-listing lean more informative.
It also de-risks RUNG 2 (the feed is the precondition for catalyst calls) — so climbing it buys down the
biggest input gap the tool admits to (`PRODUCT.md`: "news/catalyst awareness" is the headline non-feature).
Climb RUNG 1, live with it, and let real usage decide whether RUNG 2's catalyst calls are worth the L effort.
