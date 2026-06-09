# News × IPO-universe hypotheses (research scoping)

_Generated 2026-06-08. Intersection of a post-listing NEWS/CATALYST feed with our recently-listed
universe. Per hypothesis-protocol: each is an INTERACTION/SEQUENCE/REGIME mechanic with a stated
mechanism (whose money, why) + pre-declared falsifier + data-feasibility verdict. NONE are in the
score yet — post-listing signals are hold/exit FLAGS, never score inputs (locked policy). Most need a
forward-collected news DATE+CATEGORY+DIRECTION (we have prices/path; not news). Read `rules/index.md`
first — F10 (early corp-action tell), F5e (day-90 capitulation), path_ratio_1m persistence already exist._

## Data we HAVE vs a news feed must SUPPLY
- HAVE: daily adj prices, alpha/MFE/MAE by horizon, days_to_peak, path_ratio_1m, day-21/day-90 flags,
  corp_actions (ex-dates: bonus/split/dividend — the ONE backtestable "news" proxy, ISIN/symbol-keyed),
  delisting dates+reasons, fundamentals (yr1–3, so we can detect a results BEAT vs guidance post-hoc only).
- MUST SUPPLY (forward-collect; NSE/BSE corporate-announcements API — scope-probed in `scope_news_feed.py`):
  news DATE + CATEGORY (results / order-win / rating / pledge / block-deal / regulatory) + DIRECTION (+/−).
  Without a dated feed, all H1–H11 below are FORWARD-ONLY except where a backtestable proxy is named.

---

## H1 — Results-day reaction is amplified for recent IPOs (thin float)
- Mechanism: <12mo names have low free float (anchor/lock-in not fully released, retail-heavy). First
  post-listing earnings is the first hard fundamental datapoint → larger repricing per rupee of surprise.
- Predicate: |alpha[event, event+3d]| for first-results event, conditioned on listing-age bucket (<6/6–12/>12mo).
- Data: needs results DATE (forward). Surprise sign approximable post-hoc from yr1 financials we hold.
- Falsifier: |reaction| not monotone-decreasing in listing age, OR no excess vs a non-results-day placebo window.
- Backtestable? Partly — magnitude via known price path around the (forward) date; clean test = forward.
- Regime: boom-only initially (need forward feed); SME float thinness is the live edge.

## H2 — Order-win / big-contract news on SME is a sell-the-spike, not a hold (retail pump-fade)
- Mechanism: SME order-win headlines are retail-driven, thin float → sharp pop then mean-revert (no
  institutional anchor to hold the level). Same family as F10 (early bonus/split = euphoria top).
- Predicate: fwd-3m alpha after an order-win headline, SME vs MB, vs matched no-news controls.
- Data: needs order-win news date+tag (forward). MAE_3m/days_to_peak from path give the fade shape.
- Falsifier: SME post-order-win fwd-3m alpha ≥ controls (no fade) OR no SME>MB gap.
- Backtestable? Forward only. Regime: SME-boom edge; cross-regime gate likely fails (no longterm feed).

## H3 — Credit-rating UPGRADE confirms hold; pledge/encumbrance news flips a hold to exit
- Mechanism: promoter-pledge / share-encumbrance disclosures are a balance-sheet stress tell; for a
  recent IPO (promoter still ~70%+) it signals OFS-pressure/funding stress → downside re-rating. Upgrade
  = the opposite, a quality confirmation. Asymmetric (bad news travels harder on illiquid names).
- Predicate: fwd-1m/3m alpha after pledge-creation vs rating-upgrade, recent-IPO subset.
- Data: pledge & rating dates (forward; NSE/BSE/CARE-CRISIL feeds). promoter_post_issue_pct (HAVE) gates exposure.
- Falsifier: no negative drift post-pledge OR symmetric reaction (no asymmetry).
- Backtestable? Forward. Regime: cross-regime if a historical rating-action archive can be sourced (gated).

## H4 — News confirms the day-21 PERSISTENCE lean (does a catalyst rescue an EXIT_LEAN?)
- Mechanism: path_ratio_1m says month-1 momentum predicts the year. Hypothesis: a POSITIVE catalyst in
  days 22–90 on a PERSIST_EXIT_LEAN name is the only thing that flips its trajectory (information beats
  drift); absent news the exit-lean holds.
- Predicate: among day-21 EXIT_LEAN names, fwd-90d alpha WITH a positive catalyst vs WITHOUT.
- Data: catalyst dates (forward). day-21 lean + path already computed (HAVE).
- Falsifier: catalyst presence does not lift exit-lean fwd alpha (drift dominates information).
- Backtestable? Forward. High product value: this is the "should I override the exit lean?" question.
- Regime: forward/boom; ties directly to a shipped flag.

## H5 — News VOLUME (filing count) spike on a recent IPO = volatility, not direction
- Mechanism: a burst of exchange filings (many announcements in a short window) marks contested
  information / corporate churn → widens the MFE–MAE band without a directional edge. A risk flag, not a call.
- Predicate: announcement-count z-score (30d) vs forward realized vol (volatility_annual proxy) and |alpha|.
- Data: filing COUNT only (cheap — no NLP/direction needed); a near-term feasible feed. Vol we HAVE.
- Falsifier: filing-count spike uncorrelated with forward dispersion.
- Backtestable? Forward (need filing timestamps). Cheapest feed to start with (count, no classification).

## H6 — "Sell-the-news" on HOT IPOs: post-listing positive news under-delivers when GMP was already high
- Mechanism: a hot IPO (high GMP/sub) has already priced in optimism; the first good news is the
  liquidity event longs were waiting for → distribution. Interaction: news_direction × pre-listing heat.
- Predicate: fwd-5d/1m alpha after first positive catalyst, split by gmp_pct / sub_total_x tertile.
- Data: catalyst date+direction (forward). gmp_pct, sub_total_x (HAVE).
- Falsifier: positive-news reaction not weaker for high-GMP tertile (no priced-in effect).
- Backtestable? Forward. Regime: boom (GMP coverage); echoes the rejected "sell-the-news" intuition — needs the date.

## H7 — Corporate-action (bonus/split) news is a EUPHORIA TOP — EXTEND F10 with a dated feed (BACKTESTABLE)
- Mechanism: management times bonus/split after a big run to feed retail demand → marks the top (F10:
  n=31, fwd-3m −22% vs +2% controls). The catalyst feed lets us widen N + add dividend-hike/rights events.
- Predicate: fwd-3m alpha after first corp-action event within yr1, vs matched controls; by run-up bucket.
- Data: corp_actions.csv (HAVE — ex_date, action_type, ratio). DIRECTLY backtestable NOW; no new feed.
- Falsifier: with larger N the −22% fwd-3m collapses to control levels (F10 was thin-N noise).
- Backtestable? YES — already have it. Cross-regime POSSIBLE (corp_actions spans 2006+). Highest feasibility.
- **PRIOR (2026-06-09 lit review, `newsfeed_rnd_2026-06-09.md` §3c):** the UNCONDITIONAL Indian corp-action
  announcement effect is SMALL (~1.8% bonus / ~0.8% split) with the stated motive = liquidity/retail
  participation. So H7's edge is NOT the generic announcement-return literature — it is the narrow
  behavioral conditioning "corp action timed AFTER a big run in a RECENT IPO marks a retail-demand top."
  Run H7, but expect the edge (if any) to live entirely in that conditioning; a flat result on
  unconditioned corp actions does NOT falsify it. **RECOMMENDED DO-FIRST** of the 3 catalyst items
  (only one that is data-in-hand AND cross-regime-capable — see scope-down §4).

## H8 — Regulatory/SEBI action or audit-qualification = the wipeout accelerant on flagged names
- Mechanism: a regulatory red flag landing on a name that ALREADY carries N14 wipeout flags (tiny sales/
  loss-making) is the trigger that converts dead-money into a −100% path. Interaction: news × pre-flag load.
- Predicate: P(wipeout / delist within 1y) after regulatory news, split by wipeout_flag count.
- Data: regulatory news date (forward; rare events → thin N). delist dates + N14 flags (HAVE).
- Falsifier: regulatory news adds no wipeout hazard beyond the flag load already predicts.
- Backtestable? Partly (delisting reasons we HAVE may encode some regulatory exits — proxy test possible).
- Regime: cross-regime via delist-reason proxy; clean test forward. Rare-event N risk.

## H9 — Lock-in expiry NEWS (not calendar) — only the announced/large unlocks move price
- Mechanism: F1 found NO calendar lock-in-expiry effect. Refinement: the move happens only when an
  unlock is paired with a BLOCK-DEAL / promoter-sale headline (actual supply hitting), not the date itself.
- Predicate: fwd-5d alpha around block-deal headlines in the 90d post-lock-in window vs calendar-only.
- Data: block-deal feed (forward; NSE bulk/block-deals IS a free archive — potentially BACKTESTABLE).
- Falsifier: block-deal headlines in-window show no excess negative drift over the (dead) calendar effect.
- Backtestable? POSSIBLY — NSE bulk/block-deal data is historically downloadable. Re-opens a rejected idea CORRECTLY.

## H10 — News-confirmed day-90 capitulation: silence + below-issue = exit; news = wait one quarter
- Mechanism: F5e (never closed above issue in 90d → 55% bad outcome) is the silent-decline flag. Add news:
  a capitulation name WITH a pending positive catalyst (results due, order pipeline) may be early, not dead.
- Predicate: among F5e-flagged names, fwd-6m recovery rate WITH vs WITHOUT a positive catalyst in days 90–180.
- Data: catalyst dates (forward). F5e flag + fwd path (HAVE).
- Falsifier: catalyst presence doesn't lift F5e recovery (the silent decline is terminal regardless).
- Backtestable? Forward. Product value: refines a shipped exit flag — "dead vs just early".

## H11 — Sector-wide news contagion: a peer's bad news drags co-listed recent IPOs (shared float buyers)
- Mechanism: recent IPOs in one sector share the same retail/HNI buyer pool; bad news on the sector
  bellwether → forced de-risking across the thin-float cohort (correlated, not idiosyncratic).
- Predicate: fwd-5d alpha of recent same-sector IPOs around a peer's negative catalyst, vs non-event days.
- Data: sector (HAVE) + dated sector-peer news (forward). Cross-IPO mechanic (protocol exemplar shape).
- Falsifier: no excess co-movement beyond normal sector beta on peer-news days.
- Backtestable? Forward. Regime: boom. Novel cross-IPO angle, but feed-heavy + confound-prone (sector beta).

---

## RANKED TOP 5 (mechanism × feasibility × not-already-tested)
1. **H7 — Corp-action euphoria top (dated, widened F10).** BACKTESTABLE NOW (corp_actions in hand, 2006+,
   cross-regime possible); extends a thin survivor to graduation. Mechanism: management times bonus/split
   after a run to dump into retail demand → marks the top. Highest feasibility, real exit-flag value.
2. **H4 — News overrides the day-21 exit lean.** Directly answers "should I hold through the exit-lean if a
   catalyst lands?" Mechanism: information beats drift — a positive catalyst is the only thing that flips a
   momentum-driven exit lean. Forward-only but ties to a SHIPPED flag = immediate product use.
3. **H3 — Pledge/encumbrance flips hold→exit (asymmetric).** Mechanism: on a still-promoter-heavy recent IPO,
   share-pledge disclosure signals funding stress / impending OFS supply → downside re-rate; upgrade confirms.
   Clean asymmetry test, gateable by promoter_post_issue_pct we already hold.
4. **H9 — Block-deal headline, not the lock-in DATE, moves price.** Mechanism: actual supply (promoter/PE
   sale) hitting the tape, not the calendar — correctly re-opens the rejected F1 lock-in effect. Possibly
   BACKTESTABLE via NSE bulk/block-deal archive (free), so it can clear the cross-regime gate.
5. **H2 — SME order-win = sell-the-spike (retail pump-fade).** Mechanism: thin-float SME order-win headlines
   are retail-pumped with no institutional anchor → sharp pop then revert; treat first-year peak as the exit.
   Forward-only/boom, but the strongest "news flips the hold-vs-exit decision" edge for our riskiest segment.
