# Newsfeed / catalyst — SYNTHESIS DRAFT (2026-06-08)

Unifies the 6 research scouts (sources · taxonomy · mechanics · hypotheses · red-team · grand-vision)
into one opportunity map + a layered task breakdown. RESEARCH, not a build plan. Inherits the ethos:
free-data · no-ML-for-prediction · cross-regime-validated · survivorship-honest · only-ship-what-survives ·
single-owner · company-laptop · git-local. NONE of this is in the score; post-listing = hold/exit FLAGS only.

## 1. Unified opportunity map

### Consolidated source spine (dedup of the source table)
- **TIER A — official, ISIN/symbol-keyed, structured, free (BUILD HERE):** NSE corporate-announcements
  (`sm_isin` in payload — matching SOLVED), board-meetings + event-calendar (forward-dated catalysts),
  SAST reg29 + insider-PIT (promoter buy/sell/pledge). All reuse `nse_session.py`, effort S. Rating actions
  arrive INSIDE these as Reg-30 filings — not a separate scraper. NSE bulk/block-deal archive is the one
  TIER-A source with usable HISTORY (→ backtestable, see H9).
- **TIER B — aggregator, free-text, name-match (the F11 fuzzy swamp):** Google News RSS per-company (the only
  source of real-world/order/sector news beyond filings), ET / LiveMint / Moneycontrol RSS (market-wide),
  screener.in Announcements/Documents tab (fallback + transcripts; HTML, we already scrape it). Live-only →
  forward-collect. Effort M. Adds entity-match + dedup cost; red-team: keep these a SEPARATE harder project.
- **TIER C — NOT VIABLE (one line):** Twitter/X (API paid, ToS), StockTwits (signups closed), Reddit/Telegram/
  Discord (pump-and-dump noise, no SME catalyst value, laptop/ToS risk), Trendlyne/Tickertape/StockEdge (no
  API, scraping forbidden), any paid news API, external-LLM polarity (egress — blocked pending sign-off).

### Taxonomy → move-type → which hypotheses it feeds (folded in)
- **Cleanly tradeable (real drift):** earnings/PEAD (→H1), regulatory firm-specific (→H8), promoter
  pledge/invocation (→H3), M&A target (open-offer floor), abrupt mgmt exit. Drift is LARGEST in illiquid/
  under-covered names = exactly our SME/microcap IPO universe (mechanics #5).
- **Noise / fade (sell-the-spike):** order-wins (→H2), block/bulk deals (→H9 caveat), analyst initiations,
  bonus/split cosmetic (→H7 as a euphoria TOP, not a buy), capex.
- **Already-priced (don't react):** credit-rating (moves PRE-event), index inclusion (front-run then fades),
  insider-trading enforcement (≈no reaction). Anything that ran up INTO a dated event (→H6 sell-the-news).
- **Microstructure tax on ALL of it:** circuit limits censor the true move; retail/F&O frenzy exaggerates
  pops that fade; SAST/block filings hit AFTER the move; calendar events get front-run.

### The mechanics layer (how a stamp becomes a signal — UI-agnostic, daily-EOD only)
The keystone (Chan 2003): **news-tagged moves DRIFT, no-news moves REVERSE** — the date-stamp is the
discriminator. IN-scope with daily data: drift-vs-reversal split, rel-volume confirmation, D+1 follow-through,
enter-D+1-vs-wait-for-retest, pre/post anticipated-event run-up, incrementality-vs-baseline, liquidity-tier
subgroups. OUT (needs intraday): same-day timing, opening-auction fade, gap-fill timing. Hard rule everywhere:
a catalyst is actionable only at NEXT session open after dissemination (look-ahead trap).

### The grand-vision ladder (cost-tapered)
RUNG 0 (here) IPO terminal → **RUNG 1 news for hold/exit (M, pays now)** → RUNG 2 news-driven IPO buy/sell
(L, must clear 3-layer) → RUNG 3 universe explosion to all stocks (XL, fundamentals pull is the wall) →
RUNG 4 NORTH STAR TA+FA+news fusion as a weighted scorecard of individually-validated components (XL).

## 2. Reconciling the tension — what SURVIVES the red-team

The red-team's two KILLS-IT bullets are correct and decisive for the *broad* pitch: (1) news-REACTION alpha
decays in minutes; a daily, free, thrice-daily-refresh retail tool is structurally too slow to ever be early;
(2) backfill is impossible → forward-only → years to prove on a tiny rare-event sample. So **"react to news"
is dead.** But two reframings survive intact, and they are exactly where mechanics+hypotheses pointed:

- **SURVIVES — EXPLANATORY (not predictive).** Labelling a move we already see ("the +20% had a results
  filing behind it" vs "unexplained pump") needs no speed, no polarity model, no validation bar — it's a
  data-display surface. This is the red-team's own "ONE slice worth doing" AND grand-vision RUNG 1. **Real.**
- **SURVIVES — SLOW-DRIFT in ILLIQUID names.** PEAD is 1.6–2.4%/mo in illiquid vs ~0.1% liquid (mechanics #5);
  our SME/microcap IPO cohort is the highest-a-priori place drift isn't arbitraged. Plays out over WEEKS →
  daily cadence is fine. Still forward-only to PROVE, but the mechanism is sound, not theater.
- **SURVIVES — H7 (corp-action euphoria top), BACKTESTABLE NOW.** corp_actions.csv is in hand, 2006+, ISIN/
  symbol-keyed → no feed, no look-ahead-from-news, cross-regime possible. It widens the shipped F10 flag
  (n=31). This is the ONE hypothesis that can be tested today against the cross-regime bar. **Not theater.**
- **PARTIALLY SURVIVES — H9 (block-deal, not lock-in DATE, moves price):** NSE bulk/block-deal archive is
  historically downloadable → possibly backtestable, correctly re-opens the rejected F1. But block deals are
  post-trade/opaque-intent (taxonomy: low S/N, often reverse) — expect a weak/null result; worth testing,
  low prior.
- **THEATER / forward-only-and-likely-to-fail:** H1/H2/H4/H6/H10/H11 all need a forward-collected dated+typed+
  directional feed AND must then clear OOS cross-regime lift on a sample the red-team shows will be nuked by
  min-N floors. They are honest *display-only context* candidates at best, not validated signals — and
  recruiting them to rescue an entry/exit layer that already failed validation is how you manufacture overfit.
- **H3/H8 (pledge / regulatory as EXIT flags):** mechanistically the strongest of the forward set (asymmetric,
  distress-driven, gated by promoter_post_issue_pct / N14 we already hold) — but still forward-only to prove.
  H8 has a partial backtest via delisting-reason proxy.

**Bottom line:** the honest near-term product is RUNG 1 *explanatory context* + the H7 backtest. Everything
predictive is parked behind forward-collection and the 3-layer gate.

## 3. Expansion — dimensions the 6 under-covered

- **F&O / options activity as a news-PROXY (NEW).** 91% of F&O retail lose money, but option OI/IV spikes
  often LEAD a cash move (informed flow positions ahead of catalysts). NSE publishes EOD F&O bhavcopy + OI
  free. Most of our SME/microcap universe has NO F&O (only ~220 names are in derivatives) → this is a
  LARGE-IPO-only lens, and a measurement of *attention/positioning*, not direction. Worth a scoping probe;
  honest-blocker: coverage excludes the exact illiquid names where drift is real.
- **"Explanatory not predictive" as the locked product framing (NEW emphasis).** Make it a first-class chip
  ("CONTEXT, not a signal — unvalidated") rather than a stepping-stone. It may be the *terminal* honest form
  for most catalyst types — i.e. RUNG 2 may correctly never ship.
- **Forward-collection timeline (quantified, NEW).** Rare-event math: ~1,269 boom IPOs, but clean/dated/typed/
  in-window catalysts per name are sparse. At ~current SME+MB listing pace, expect on the order of ~150–250
  classifiable first-results events/yr and far fewer pledge/regulatory. To clear a min-N=12 floor PER cell
  (type × segment × liquidity × regime), realistic horizon to a cross-regime verdict on any forward hypothesis
  is **2–4 years of daily staging** — must start the staging pull NOW or the clock never starts.
- **Maintenance cost of N scrapers (NEW, decisive for single-owner).** Each free source breaks independently
  (session cookies, anti-bot, param drift — BSE already returned no-records, Business Standard 403). TIER-A is
  1 session pattern (low). Every TIER-B source added = a recurring weekly-breakage tax on one owner. Budget:
  ship 1 scraper (NSE announcements), resist the rest until the first earns trust.
- **How news combines with the score WITHOUT overfitting (NEW concreteness).** It does NOT enter the weighted
  score under the locked "evolve-only-if-robust" policy unless it improves OOS top-quintile lift across splits.
  Given red-team's sample-size reality, the realistic outcome is **display-only forever** for most signals —
  same status as `tradeable_upside` (weight 0). News should be modelled as a *hold/exit FLAG overlay* and a
  *context column*, never a 6th-weighted-component, until a forward test genuinely clears the bar.
- **Survivorship in news (NEW guard):** dead names stop filing; "no news found" ≠ "no event." Failed names
  stay in the denominator of any event study — the same bias the project fought to remove.

## 4. LAYERED TASK BREAKDOWN  (effort · payoff · honest-blocker)

**NO-BRAINER (do without ceremony):**
- Start the daily NSE-announcements staging pull to `data/live/` keyed on `sm_isin`. S · starts the
  forward-collection clock (the binding constraint on everything predictive) · blocker: none.

**LOW-EFFORT:**
- RUNG 1 v1: render the raw dated announcement stream on each IPO Detail / tracking card, category-only via a
  LOCAL keyword/regex taxonomy, "context not signal" chip + next-session-open actionability note. S–M · turns
  "+20%, cause unknown" into explanation; touches no money number · blocker: dedup multi-filing events.
- H5 filing-COUNT spike as a volatility (not direction) flag. S · cheapest real signal, no classification ·
  blocker: forward-only (needs the staged timestamps the no-brainer accrues).

**MEDIUM:**
- **H7 corp-action euphoria-top backtest (THE do-it-now analysis).** M · widens shipped F10 to graduation,
  cross-regime POSSIBLE · blocker: none — corp_actions.csv in hand. (See headline.)
- H9 block-deal vs lock-in-DATE test on the NSE bulk/block archive. M · correctly re-opens rejected F1 ·
  blocker: low prior (block deals are opaque/post-trade), archive completeness unverified.
- F&O OI/IV proxy scoping probe (large-IPO subset). M · novel attention/positioning lens · blocker: no
  coverage on the illiquid names where drift is real.

**BIG-BET:**
- RUNG 2 catalyst-tagged buy/sell calls (type + good/bad). L · the first genuinely event-driven call ·
  blocker: polarity needs an LLM (egress-blocked) or fails on keywords; must clear 3-layer OOS cross-regime —
  red-team says it likely won't on this sample. Park behind RUNG 1 earning trust.

**DATA-GATED (real mechanism, blocked only by forward collection):**
- H1 amplified results-reaction · H2 SME order-win sell-the-spike · H3 pledge flips hold→exit · H4 catalyst
  overrides day-21 exit-lean · H6 sell-the-news on hot IPOs · H8 regulatory wipeout-accelerant · H10 news-vs-
  silence at day-90 capitulation · H11 sector contagion. All: forward-only, 2–4yr horizon, min-N risk; ship as
  display-only context at most until a clean cross-regime test exists.

**NOT-VIABLE (permanent):**
- Twitter/StockTwits/Reddit/Telegram sentiment · Trendlyne/Tickertape scraping · paid news APIs · external-LLM
  polarity on scraped content · the all-stocks TA×FA×news fusion as a near-term goal (combinatorial false-
  discovery + N-scraper maintenance collapse on a single-owner laptop). · "react to news" reaction-trading
  (structurally too slow).

**NORTH-STAR (years of optionality, not a sprint):**
- RUNG 4 fusion = a weighted SCORECARD of individually-validated TA + FA + news components (NOT a learned
  combiner), each gated by evolve-only-if-robust, regime-overlay-aware. Honesty moat survives only because
  fusion ≠ ML. Preconditions: RUNG 1→2→3 in order; the honest answer for most names ("no edge, hold") is the
  product.
