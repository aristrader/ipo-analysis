# Newsfeed mechanics — how news becomes a tradeable (or untradeable) signal

Research slice: the MECHANICS of news→signal. UI-agnostic. Not financial advice.
What's IN scope for us = daily EOD OHLCV + a **news-date stamp**. What's OUT = anything needing
intraday/tick (we have no intraday). The keystone result: prices **drift after news, reverse after
no-news** (Chan 2003) — so the news *stamp itself* is the conditioning variable that separates a
real catalyst from a pop.

## The core look-ahead trap (applies to every mechanic below)
You only know a news item AFTER it is public. So any signal forms on news_date and is tradeable from
**next open (D+1)** at the earliest. Never measure the move from a price BEFORE the stamp. The
news-date stamp is the only new column; everything else we already have. Watch: (a) stale/backfilled
timestamps (use the FIRST public timestamp, not the article's edited date); (b) leakage — pre-event
drift means "the move" partly happened before D0 (buy-the-rumor); measure forward from D+1 only.

## Mechanic 1 — Post-news DRIFT vs no-news REVERSAL (the keystone)
- **Hypothesis:** moves accompanied by genuine news CONTINUE (underreaction → drift); moves with NO
  identifiable news REVERSE (liquidity/attention pop). The stamp is the discriminator.
- **Evidence (strong, direction clear):** Chan (2003), "Drift and Reversal after Headlines" —
  post-headline drift (esp. after bad news), reversal after extreme moves WITHOUT news. Confirmed by
  the jump literature (no-news jumps relax/reverse; news jumps persist). PEAD (Bernard-Thomas):
  ~2% drift over ~60 trading days in the surprise direction, most in the first weeks.
- **Testable with daily?** YES. Tag each row: did a +X% / large-volume day have a news stamp within
  ±1 day? Compare forward 1/5/20d alpha for news-tagged vs no-news moves of the same size. Falsifier:
  no-news moves drift as much as news moves → mechanic dead (placebo = match on move size + volume).

## Mechanic 2 — FAKE move vs real catalyst (volume + follow-through)
- **Hypothesis:** a real catalyst comes with abnormal VOLUME and D+1 follow-through (gap-and-go); a
  fake pop is low rel-volume and fades. Volume confirms information.
- **Evidence (moderate):** practitioner gap-and-go uses ≥2–3× rel-volume + catalyst as the filter;
  no-news/low-volume gaps fill. Barber-Odean: attention/extreme-return/high-volume stocks draw retail
  buying then UNDERPERFORM — so high volume alone (without news) can mark the *top*, not continuation.
  The two reconcile via the stamp: volume + news = drift; volume + no news = reversal.
- **Testable with daily?** YES (proxy intraday with EOD): rel-volume = day volume / trailing-20d median;
  follow-through = sign(D+1 close vs D0 close). Bucket forward returns by {news?} × {rel-vol hi/lo} ×
  {D+1 confirms?}. Falsifier: volume adds nothing once you condition on the news stamp.

## Mechanic 3 — ENTER NOW vs WAIT for the pullback
- **Hypothesis:** under genuine drift, entering immediately (D+1 open) beats waiting (you forfeit drift);
  under a fakeout-prone pop, waiting for a pullback/retest filters false signals and improves expectancy.
- **Evidence (mixed/conditional):** breakout-vs-pullback lit says neither dominates — immediate entry
  captures the first impulse but eats fakeouts; pullback entry filters fakeouts but arrives late and
  misses fast movers. Conditioner: trend strength (drift regime → don't wait; range → fade-prone).
- **Testable with daily?** PARTIALLY. We can test "enter D+1 open" vs "enter only if price holds/retests
  over D+1..D+3" forward expectancy. We CANNOT test same-day timing (no intraday) — flag as out of scope.
  Report the WHOLE grid (entry rule × horizon), pre-declared; failure cells included.

## Mechanic 4 — SELL-THE-NEWS / buy-the-rumor (anticipated events)
- **Hypothesis:** for ANTICIPATED events (scheduled results, lock-in expiry, index inclusion), price
  runs UP into the event and FALLS after even on a good outcome — the news was already priced.
- **Evidence (moderate):** classic BRSN; rule-of-thumb that pre-event run-up ≈ post-event give-back;
  India buyback studies show pre-announcement abnormal returns (leakage/anticipation) and muted/negative
  post-event continuation. "Good news, stock falls" is systematic for events the market expected.
- **Testable with daily?** YES for anticipatable, dated events (the stamp + an "anticipated?" flag).
  Measure pre-event run-up (D−10..D−1 alpha) vs post-event (D+1..D+20). For IPOs the natural anticipated
  events are lock-in/anchor-expiry and first results — high-value because they're DATED in advance.

## Mechanic 5 — Is news INCREMENTAL to price/our score, or already priced?
- **Hypothesis:** much of "news" is already in the move (efficient/leaked); the residual edge is only in
  the drift component. The honest test is whether a news signal adds OOS top-quintile lift OVER price
  momentum + our existing scorecard.
- **Evidence (cautionary):** PEAD magnitude has DECAYED as it became known (esp. large/liquid names);
  retail-attention buying loses money. BUT drift survives where arbitrage is costly — small/illiquid/
  low-analyst stocks (PEAD 1.6–2.4%/mo illiquid vs ~0.1% liquid). **That is exactly our SME/microcap IPO
  universe** → highest a-priori chance news drift is real and not arbitraged away.
- **Testable with daily?** YES, and REQUIRED by our score policy: news enters the weighted score only if
  it beats the price-momentum + scorecard baseline OOS across folds; else display-only. Subgroup by
  liquidity tier (expect effect concentrated in illiquid).

## Sentiment direction & magnitude (cross-cutting note)
Direction matters asymmetrically: literature finds **continuation after negative shocks, reversal after
positive shocks** (positive extremes over-attended by retail). Magnitude (surprise size) scales drift in
PEAD. With daily data we proxy surprise by gap+rel-volume; true surprise (vs expectation) needs an
estimate we mostly lack — flag as a measurement limit, not a hard blocker.

## In scope vs out of scope (summary)
- IN (daily EOD + stamp): drift/reversal split by news-vs-no-news, rel-volume confirmation, D+1
  follow-through, enter-D+1 vs wait-for-retest, pre/post anticipated-event run-up, incrementality vs
  baseline, liquidity-tier subgroups.
- OUT (needs intraday/tick): same-day entry timing, opening-auction fade, first-N-minutes follow-through,
  exact gap-fill timing. State these as "needs intraday" wherever they appear.
- DATA REALITY: an IPO-specific, time-stamped news feed (free) is the binding constraint — coverage,
  dedup, and FIRST-public-timestamp accuracy decide whether any of this is testable at all.

## Sources
- Chan, "Stock Price Reaction to News and No-news: Drift and Reversal after Headlines," JFE 2003 —
  https://www.sciencedirect.com/science/article/abs/pii/S0304405X03001466
- Bernard & Thomas / PEAD review — https://www.sciencedirect.com/science/article/pii/S2214635020303750 ;
  Wikipedia PEAD — https://en.wikipedia.org/wiki/Post%E2%80%93earnings-announcement_drift
- PEAD & limits-to-arbitrage / illiquidity — https://acfr.aut.ac.nz/__data/assets/pdf_file/0019/105544/ME0008Tais-Supervisor-PEAD-and-Expected-growth-risk.pdf
- Barber & Odean, "All That Glitters" (attention-driven buying underperforms) —
  https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/allthatglitters_rfs_2008.pdf ;
  "Retail trades positively predict returns but are not profitable" — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3783492
- Information shocks / short-term under- vs over-reaction (asymmetry) —
  https://www.sciencedirect.com/science/article/abs/pii/S0304405X16302409 ; reaction after extreme moves — https://arxiv.org/pdf/cond-mat/0406696
- Jumps: news vs no-news persistence/relaxation — https://arxiv.org/pdf/0803.1769
- Buy-the-rumor/sell-the-news (Peterson, behavioral) — http://www.richard.peterson.net/buyontherumor10.html
- India event studies (buyback pre-announcement abnormal returns / leakage) —
  https://www.sciencedirect.com/science/article/abs/pii/S1544612325018483 ; corporate announcements (India) — https://emerald.com/insight/content/doi/10.1108/ajar-06-2021-0097/full/html
- Gap-and-go vs gap-fade (volume/follow-through filters, practitioner) — https://www.quantifiedstrategies.com/gaps/
- Breakout vs pullback entry timing — https://www.heygotrade.com/en/blog/choosing-pullback-vs-breakout-trading/
