# News/catalyst direction — RED-TEAM (skeptic's brief, 2026-06-08)

_Adversarial review of the news-feed direction (future_ideas #2) + the far-future TA+FA+news fusion,
BEFORE we invest build time. Scored: KILLS-IT / IMPORTANT / NIT. Not a plan — a stress test._

## The core thesis being attacked
"Track news per stock → tag good/bad/category → improve buy/sell decisions." The scope probe proved
the FREE NSE announcements API exists and carries `sm_isin` (matching solved). That de-risks PLUMBING.
It does NOT de-risk the only thing that matters: **does a news tag change a decision profitably, for a
slow daily-data retail tool?** Everything below attacks that.

## EDGE REALITY (the make-or-break)
- **[KILLS-IT] The edge is timing, and we are structurally slow.** News-reaction alpha decays in
  minutes-to-hours. We are a DAILY-DATA tool refreshed at "last refresh," reading a free feed retail
  also reads. By the time an announcement is in our staged data and we alert thrice-daily, the move is
  priced. We can NEVER be early on the reaction. → If the pitch is "react to news," it's fantasy.
  Honest mitigation: do NOT frame this as reaction-trading. The only defensible framings are
  (a) *explanatory* (label a move we already see: "the +20% had an earnings filing behind it" vs
  "unexplained pump") and (b) *slow-drift* (post-earnings-announcement-drift, guidance, large orders —
  effects that play out over WEEKS, where daily cadence is fine). Anything faster = don't.
- **[KILLS-IT for the broad version] Our own evidence already says the tradeable layer is weak.** Entry
  signals are a graveyard (buy-after-fall rejected, breakout falsified, issue-magnet placebo); exits
  lose to buy-and-hold (timing tax). News is being recruited to rescue a layer that has repeatedly
  failed validation. Recruiting a noisy new input to fix a weak base is how you manufacture overfit.
  Mitigation: news must clear the SAME 3-layer/cross-regime bar (top-quintile OOS lift, robust across
  boom vs longterm) as everything else — and it almost certainly won't on a small IPO sample.
- **[IMPORTANT] Sample is tiny for event studies.** Real catalysts (earnings beats, big orders) are
  rare per name; across 2,384 IPOs the count of *clean, classified, dated, in-our-window* catalyst
  events is small once you require no-look-ahead. Min-N floors (suppress <12) will nuke most cells.
  Mitigation: accept this is descriptive/illustrative, not a validated signal, unless N genuinely clears.

## CLASSIFICATION TENSION (good/bad/category without an LLM)
- **[IMPORTANT] Reliable good/bad needs an LLM; that's cost + a company-laptop egress question.**
  Sending Indian micro-cap headlines to an external LLM = data leaving the laptop (the very thing
  NEXT.md already flags as off-moat). Mitigation / how far rules get you WITHOUT an LLM:
  - **Structured fields get you ~category for free.** NSE payload has `desc`/subject + `smIndustry` +
    attachment type. A keyword/regex taxonomy (Results, Dividend, Bonus/Split, Order Win, Resignation,
    Pledge, Open Offer, Rating, Litigation, Allotment) is honest and 100% local. Coarse but real.
  - **Polarity (good vs bad) is the hard 20%** keywords botch: "results" is neither; "resignation of
    CFO" reads bad but is context-dependent; sarcasm/spin in PR-style filings. Keyword polarity will be
    wrong often enough to be dangerous if it drives a call.
  - Verdict: ship **category-only, rule-based, local** (useful as context). Do NOT ship rule-based
    good/bad as a decision driver. If polarity is ever wanted, a LOCAL small model is the only
    ethos-fit path, and only after egress sign-off — treat as blocked until then.

## DATA TRAPS (every one of these silently produces a wrong number)
- **[KILLS-IT if ignored] Look-ahead via timestamps.** An announcement's *filing* time ≠ when it was
  retail-actionable (post-market filings, attachment-vs-headline lag, exchange dissemination delay). A
  backtest that joins news to the same-day close will leak the future and look brilliant. Mitigation:
  hard rule — a catalyst is only actionable at NEXT session open after dissemination; bake into the
  spine like the existing no-look-ahead rule. Assume any too-good result is leakage until proven.
- **[KILLS-IT for proof speed] Backfill is impossible → forward-only → years to prove.** Most free
  news/announcement history is not reliably archived (NSE API skews recent; the probe's 0-coverage
  names were old/illiquid). You cannot run a clean historical event study, so the signal can only be
  proven by FORWARD collection — same multi-month/years problem as the live track record, but worse
  (rarer events). The tool would carry an unproven feature for a long time.
- **[IMPORTANT] ISIN matching is "solved" only for NSE-natively-filed announcements.** `sm_isin` covers
  NSE corporate filings. The moment you add Google News / ET / moneycontrol RSS (free-text, no ISIN),
  you are back in the F11 fuzzy-matching swamp (name collisions, renamed/merged entities, SME ticker
  reuse). Mitigation: stay NSE/BSE-structured-only. Treat any RSS/social add as a separate, harder
  project — don't let "we solved matching" leak from the structured case to the free-text case.
- **[IMPORTANT] Survivorship in news coverage.** Delisted/dead names stop filing; their pre-death
  news is gone. An event study that only sees survivors' news re-introduces the survivorship bias the
  whole project fought to remove. Mitigation: failed names must stay in the denominator; "no news
  found" ≠ "no event happened."

## SOCIAL SOURCES
- **[KILLS-IT — just don't] Twitter/Telegram/forum "sentiment."** Indian micro/SME-cap social is a
  pump-and-dump arena; scraping it ingests adversarial, manipulated signal that actively inverts
  (loudest buzz = the exit liquidity trap). Plus ToS/scraping-on-a-company-laptop exposure. Mitigation:
  out of scope, permanently, for this tool. Not "later" — no.

## SCOPE CREEP — "extend to all stocks + TA+FA+news fusion"
- **[KILLS-IT for the grand version] Combinatorial collapse.** All-stocks ×(TA × FA × news) explodes
  the signal-test space → guaranteed false discoveries under any sane multiple-testing discipline, and
  N fragile scrapers to maintain on a company laptop (each a breakage + ToS surface). It abandons the
  one thing that makes THIS tool honest: a bounded, survivorship-clean IPO universe with cross-regime
  validation. Maintenance load alone (feeds break weekly) sinks a personal project.
  Mitigation: refuse the all-stocks fusion. Keep the universe = our IPO cohort. News is at most one
  *context* column on names we already track, not a new asset class.

## LEGAL / ToS / SECURITY (company laptop)
- **[IMPORTANT]** NSE/BSE public APIs: tolerable IF rate-limited + cached like existing scrapers and
  used for personal research (consistent with current chittorgarh/screener practice). Social scraping
  and any paid-API key on the work machine: don't. External-LLM egress of scraped content: blocked
  pending explicit sign-off. Keep everything localhost/local-file, same as current posture.

## VERDICTS
- **#1 reason this is a low-ROI rabbit hole:** the durable edge requires SPEED we structurally cannot
  have (daily, free, public, thrice-daily alerts), AND the only honest proof path is forward-only over
  years on a tiny rare-event sample — so we'd sink real build + maintenance effort into a feature that
  is unlikely to ever clear our own validation bar, while expanding the fragile-scraper surface on a
  company laptop. High effort, slow/uncertain payoff, ethos risk (egress).
- **The ONE slice worth doing:** a **local, rule-based, category-tagged NSE-announcements CONTEXT feed
  on names we already track** — dated filings (results/dividend/order/resignation/pledge/open-offer)
  keyed on `sm_isin`, shown on the IPO Detail / tracking card as *explanation*, with a hard
  next-session-open actionability rule and an explicit "context, NOT a signal — unvalidated" chip. It
  turns "+20%, cause unknown" into "+20% on a results filing," which is genuinely useful and honest,
  costs no LLM, no egress, no new fragile source, and reuses `nse_session.py`. Everything beyond that
  (good/bad polarity, RSS/social, all-stocks fusion, news-driven trade calls) stays parked until this
  slice earns trust and an entry signal independently clears the 3-layer protocol.
