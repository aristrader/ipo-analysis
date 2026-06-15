# Newsfeed/catalyst R&D — BUILD-READY specs + evidence tightening (2026-06-09)

Research-only (NO scraping/build/commit). Advances `newsfeed_opportunity_map.md` (authoritative).
Discipline = `hypothesis_protocol.md`; network = `trusted_sources.md` (default-deny; only
`www.nseindia.com`/`www.bseindia.com`/`screener.in`/`sebi.gov.in` + media hosts fetchable; everything
here that needed `archives.nseindia.com` was reached via WebSearch snippets ONLY — the archives host is
OFF the WebFetch allowlist and was correctly NOT fetched). Convention: established-fact vs
[HYPOTHESIS]/[TO-BE-TESTED] tagged throughout; every proposed signal ends with a "beat do-nothing?" line.

Scope of this doc:
1. D2 delivery-volume% — data-availability verdict + 3-layer test design.
2. D1 RUNG-1 explanatory NSE-announcement feed — turnkey BUILD SPEC.
3. Evidence tightening (literature) — sharpened priors with citations.
4. SCOPE-DOWN recommendation — re-ranking the map given (1).

---

## 1. D2 — DELIVERY-VOLUME % : data-availability + test design

### 1a. DATA-AVAILABILITY VERDICT — **FEASIBLE (with a history caveat), but NOT in what we currently pull**

**The data exists, free, security-wise, daily.** NSE publishes a daily consolidated file
`sec_bhavdata_full_<DDMMYYYY>.csv` carrying per-symbol delivery columns. Confirmed columns (established):
`SYMBOL, SERIES, DATE1, PREV_CLOSE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, LAST_PRICE, CLOSE_PRICE,
AVG_PRICE, TTL_TRD_QNTY, TURNOVER_LACS, NO_OF_TRADES, DELIV_QTY, DELIV_PER`.
- `DELIV_QTY` = shares marked for delivery (not intraday-squared-off); `DELIV_PER` = DELIV_QTY / TTL_TRD_QNTY × 100.
- Endpoint pattern (from multiple Python downloaders): `archives.nseindia.com/products/content/sec_bhavdata_full_<DDMMYYYY>.csv`.
  This is the SAME `archives.nseindia.com` host our existing `scrapers/bhavcopy.py` already hits for the
  pre-2024 cm-bhavcopy — i.e. it's a known-good, session-primeable, rate-limited pattern for us.

**CRITICAL GAP — this is a SEPARATE file from what we pull today.** Our `scrapers/bhavcopy.py` +
`bhavcopy_ohlc.py` fetch the plain **cm-bhavcopy** (`cm<DDMMM YYYY>bhav.csv.zip` pre-2024; UDiFF
`BhavCopy_NSE_CM_..._F_0000.csv.zip` post-2024) — these carry OHLC + total volume but **NO delivery
columns**. So delivery% is NOT already in `data/prices/*.csv`; it requires a NEW daily pull
(`sec_bhavdata_full`) + an ISIN/symbol join into the price files. (`grep` confirms "deliv" appears only in
`scrapers/screener_prices.py`, not in the bhavcopy path.) This is a real BUILD cost, not a free add.

**HISTORY DEPTH — the honest caveat that shapes the test:**
- Delivery-position data is materially SHALLOWER than our 2006+ price history. The consolidated
  `sec_bhavdata_full` daily file is reliably retrievable from roughly **FY2016-17 (~2017) onward**
  (multiple downloader projects + NSE "all-reports" archive depth point here); [TO-BE-TESTED: the exact
  first-good date by probing the endpoint — do at build time, do NOT assume].
- Older delivery data existed as a separate legacy **MTO** ("market trade-to-delivery") report, but its
  free archive depth, format stability, and SME coverage are UNCONFIRMED and likely patchy pre-~2011/2014.
  [TO-BE-TESTED]. Do not bank on it.
- **No clean academic/official source pins the precise start date** — treat ~2017 as the working floor and
  *measure* it before building. **Implication: a delivery% study is BOOM-COHORT-ONLY (2017+).** It CANNOT
  clear the project's cross-regime gate (which requires the 2006–19 longterm cohort), because delivery
  history doesn't reach the longterm cohort's listings. This is the linchpin finding (see §4).
- SME/EMERGE coverage: `sec_bhavdata_full` is all-NSE-securities incl. EMERGE (SERIES = "SM"/"ST"); EMERGE
  itself launched 2012 and the SME-index in 2017, so SME delivery history is even shallower + thin-volume
  (delivery% on a 1-trade day is meaningless). [TO-BE-TESTED: per-row TTL_TRD_QNTY floor before computing %].

**Verdict:** Delivery% is **data-feasible for the 2017+ boom cohort only**, via a new `sec_bhavdata_full`
daily pull (separate from current bhavcopy). It is **NOT** feasible cross-regime. That single fact demotes it
from the map's "DO FIRST / could clear the bar" framing — see the scope-down (§4).

### 1b. THREE-LAYER TEST DESIGN — "high post-listing delivery% = real conviction → predicts drift"

Mechanism (the [HYPOTHESIS]): in thin-float SME/microcap recent IPOs, a high delivery% (shares actually
taken into demat, not flipped intraday) marks genuine accumulation by holders who intend to stay → less
float churn → positive drift; conversely low delivery% + high volume = pure intraday churn / operator
rotation → no support → fade. The conviction is in the *delivery ratio*, not raw volume.

**Feature construction (point-in-time, look-ahead-safe — non-negotiable):**
- `deliv_pct_w1` = mean DELIV_PER over trading days **t+1 … t+5** post-listing (the first full week AFTER
  listing day; listing day excluded — its delivery% is a primary-allotment artifact, not secondary conviction).
- Variants to pre-declare (one grid, fixed before looking): w1 (d1–5), w2 (d1–10), and a 20d.
- Normalize within segment×listing-vintage (delivery% has a structural level that drifts with market
  regime and segment) → use the within-cohort PERCENTILE/tertile, never the raw level across eras.
- GUARD: drop rows where median TTL_TRD_QNTY in the window < a liquidity floor (delivery% is noise on
  near-zero volume — exactly the SME zombie names). Report how many rows the floor removes.

**Entry / horizon:** signal forms at end of day d+5 (or d+10) → tradeable from **d+6 open** (the secondary
buyer). Forward outcome = alpha vs Nifty (+ Smallcap-250 where available, per project convention) over
**+1m / +3m / +6m / +1y** measured FROM d+6 (never from listing — that would re-use the pre-signal path).
Use `mfe_*`/`mae_*` from the matching entry for the movement view.

**Controls (the signal must beat these, not just exist):**
1. Raw post-listing volume / turnover (the cheap confound — does delivery% add anything over volume?).
2. Month-1 path direction (`path_ratio_1m`, already VALIDATED cross-regime as a persistence signal) — does
   delivery% add lift OVER the momentum we already ship? (This is the score-policy bar: incremental OOS lift.)
3. The existing scorecard rank. If delivery% doesn't beat #2 and #3 it is display-only at best.

**Placebo (pre-declared kill condition):** shuffle the delivery% labels within segment×vintage 1,000× and
recompute the tertile-spread / rank-IC. If the real spread sits inside the shuffled distribution (p>0.05),
the signal is DEAD (this is the same falsifier discipline that killed F5a/pe-vs-sector survived). Second
placebo: substitute *raw volume percentile* for delivery% — if volume alone reproduces the effect, delivery%
adds nothing (the "incremental to volume" test).

**Min-N / reporting:** project floors — <12 suppress, 12–29 "thin", ≥30 report; print N every cell;
distributions (median + P10/P90) not means; report the WHOLE entry×horizon grid incl. failure cells.

**Look-ahead / survivorship flags specific to this test:**
- Look-ahead: never include listing day; never normalize using a cross-section that includes future
  listings; the liquidity floor must use only in-window (d1–d5) volume, not lifetime turnover.
- Survivorship: delisted names that died early may have NO d1–d5 window or get nulled by the volume floor →
  they must stay in the denominator as "unclassifiable", not silently dropped (the bias the project fought).
- Regime: 2017+ only → the result is BOOM-ONLY and can never be cross-regime-validated → caps it at
  display-only under the locked score policy regardless of how strong it looks.

**→ Could this beat do-nothing, and how would we know?** Do-nothing = our existing top-quintile scorecard
rank (3y OOS-validated). Delivery% beats do-nothing ONLY if, on a pre-declared fold harness
(`heat_fold_test.py` pattern), adding the delivery%-tertile improves the OOS top-quintile lift over the
current 8-component score AND survives both placebos — AND even then it's display-only (boom-only fails
cross-regime). Honest prior: **likely display-only-or-rejected**; the practitioner "high delivery = conviction"
claim has NO peer-reviewed support (only blogs/screeners — see §3e), and it overlaps the volume/momentum we
already ship. Worth ONE disciplined test precisely to settle it, not to expect a win.

---

## 2. D1 — RUNG-1 EXPLANATORY NSE-ANNOUNCEMENT FEED : BUILD SPEC

A turnkey spec for an ISIN-keyed, dated, locally-category-tagged announcement CONTEXT feed on the IPO Detail
card. **NO LLM, NO egress, NO polarity, NO trade call.** It turns "+20%, cause unknown" into "+20% on a
results filing." Display-only "context, NOT a signal" — structurally cannot breach the honesty moat
(red-team's "ONE slice worth doing"). This is a SPEC; the actual pull waits for network + babysitting.

### 2a. Source endpoint + fields (confirmed)
- **NSE corporate-announcements API** — already probed in `tools/research/scope_news_feed.py` (map + sources
  doc). `/api/corporate-announcements?index=equities&symbol=<SYM>`, JSON, session-primed via the existing
  `nse_session.py` pattern, rate-limited like our other NSE pulls. Host = `www.nseindia.com` (ON the
  WebFetch allowlist; but the production pull is via the python scraper, not WebFetch).
- **`sm_isin` IS in the payload** — confirmed by the prior probe (5/8 symbols returned 18–28 announcements
  with full fields). This SOLVES ISIN matching for the structured NSE case (no fuzzy name-match → stays out
  of the F11 swamp). Fields to keep: `sm_isin` (join key), `symbol`, `desc`/subject, `attchmntText`/headline,
  `an_dt` (announcement datetime — the look-ahead-critical field), `attchmntFile` (PDF link, store URL only —
  do NOT download, per zero-download rule), `smIndustry`.
- Companion forward-catalyst endpoints (same session, optional v2): `/api/corporate-board-meetings`
  (`bm_date`/`bm_purpose`) and `/api/event-calendar` (`date`/`purpose`) for *scheduled* results/dividend/AGM
  dates. Display-only "upcoming catalyst" chip. SAST-reg29 / PIT optional later.
- **Scope discipline:** structured NSE/BSE ONLY. Do NOT add Google-News/RSS/social — they reintroduce
  fuzzy name→ISIN matching (F11) and are explicitly killed in the red-team. BSE (`api.bseindia.com`) is a
  redundant fallback for NSE-listed; only worth it for BSE-only SME names [TO-BE-TESTED param fix].

### 2b. Local category taxonomy (rule-based, 100% local, coarse-but-honest)
Keyword/regex over `desc` + `attchmntText` + structured fields. Multi-label allowed; default `other`.
Category is honest; **POLARITY (good/bad) is deliberately NOT computed** (red-team: keywords botch the
hard 20% — "resignation"/"results" are context-dependent; a local small-model is the only ethos-fit polarity
path and is blocked pending egress sign-off). Categories:
| category | example trigger keywords (illustrative — finalize at build) |
|---|---|
| earnings | "financial results", "quarterly", "audited", "un-audited", "Q1/Q2/Q3/Q4 results" |
| sebi-regulatory | "SEBI", "show cause", "adjudication", "penalty", "order", "settlement", "circular" |
| pledge-encumbrance | "pledge", "encumbrance", "invocation", "creation of charge", "reg 31" |
| m&a-openoffer | "acquisition", "amalgamation", "scheme of arrangement", "open offer", "SAST", "merger" |
| management | "resignation", "appointment", "cessation", "auditor", "KMP", "director", "CFO/CEO" |
| index-inclusion | "index", "inclusion", "F&O", "exclusion", "reconstitution" |
| order-win | "order", "contract", "LOI", "work order", "bagged", "awarded", "tender" |
| corp-action | "bonus", "split", "sub-division", "dividend", "rights", "buyback" (cross-link to corp_actions.csv) |
| capital-raise | "preferential", "QIP", "fund raising", "warrants", "rights issue" |
| ratings | "rating", "CRISIL", "ICRA", "CARE", "reaffirmed", "downgrade", "upgrade" (arrive as Reg-30 here) |
| litigation | "litigation", "NCLT", "insolvency", "winding up", "arbitration" |
| other | fallback |
Keep the keyword map in a versioned local file (e.g. `layer3/news/taxonomy.py`); precision over recall
(better `other` than a wrong tag driving a glance-judgment). Tag = display label only.

### 2c. Look-ahead-safe timestamp rule (the spine rule, baked in)
- Use `an_dt` as the FIRST-public timestamp (not any edited/attachment date).
- **Actionability rule:** an announcement disseminated at/after **15:30 IST** (market close) is actionable
  only from the **next session open** → effectively **D+2** for a same-day-staged-then-thrice-daily tool.
  Pre-15:30 → D+1 at the earliest. Store both `an_dt` and a derived `actionable_from` date.
- This is *display* (a chip says "filed after hours — markets had not traded on this yet when the move you're
  looking at happened"); but it is ALSO the hard rule any future predictive test (RUNG-2) must inherit, so
  encode it now. A backtest that joins news to the same-day close leaks the future (red-team [KILLS-IT]).

### 2d. Staging, NOT substrate (data discipline)
- Land raw rows in `data/live/news/<sm_isin>.csv` (or a single dated `announcements_staging.csv`), keyed on
  `sm_isin` + `an_dt`. **NEVER write into the frozen substrate** (`ipo_analysis.csv`) — same rule as the live
  board (`newsfeed_sources.md` discipline). The substrate stays the survivorship-clean, point-in-time
  research base; the feed is a mutable display overlay joined at render time.
- Idempotent upsert on (`sm_isin`,`an_dt`,`desc`+`attchmntText`-hash); store `attchmntFile` URL only
  (zero downloads). [AMENDED 2026-06-10 at build: the key includes `attchmntText`, not `desc` alone —
  NSE often files several DISTINCT attachments in the same minute under an identical subject `desc`
  ("Outcome of Board Meeting"); hashing `desc` alone collapsed them and silently dropped a real filing.
  Caught by the build's independent review.]
- Forward-collect: the API skews recent + 0-coverage on old/illiquid names (prior probe) → start the daily
  pull NOW to accrue history; "no news found" ≠ "no event" (survivorship caveat shown in UI).

### 2e. Display rules (IPO Detail card)
- A reverse-chronological dated list under the price chart: `[date] [category chip] headline (source: NSE)`.
- Mandatory persistent chip: **"Context, not a signal — unvalidated."** No good/bad coloring, no buy/sell.
- Optionally annotate the price chart with category markers so a visible move lines up with a filing
  ("the +20% had an earnings filing behind it"). Markers respect `actionable_from` (drawn on the actionable
  day, with a tooltip noting after-hours filings).
- "Upcoming catalyst" sub-block from board-meetings/event-calendar (scheduled results/dividend) — labelled
  "scheduled, not predictive".
- Empty state: "No NSE filings captured for this name (coverage starts <staging-start-date>; absence ≠ no event)."

**→ Could this beat do-nothing, and how would we know?** This feed makes NO trade claim, so "beat do-nothing"
does not apply — its job is *explanation*, and success = the user can attribute an observed move to a filing
instead of guessing. It is intentionally OUTSIDE the score (display-only, cannot move a decision). The moment
anyone wants it to drive a hold/exit call (RUNG-2), it must clear the full 3-layer/cross-regime/OOS bar with a
forward-collected DATE+CATEGORY+DIRECTION — and the red-team's verdict is that, for a daily/free/slow tool on a
tiny rare-event sample, it is unlikely to ever clear that bar. So: ship as context; do not let it creep into a signal.

---

## 3. EVIDENCE TIGHTENING (literature → sharpened priors)

Decision-relevant only. Each prior tagged with what it does to our hypotheses.

### 3a. PEAD is real in India AND concentrated in illiquid/small-caps (sharpens the WHOLE drift thesis — supportive)
A test of PEAD on the Indian market (2002–2017) found **statistically significant drift that persists after
controlling for beta, market-cap, P/B, illiquidity and idiosyncratic vol** — i.e. not subsumed by known
factors. ([SCIRP, *PEAD Anomaly in India: A Test of Market Efficiency*](https://file.scirp.org/Html/20-1501629_88060.htm)).
Cross-market, drift is **~1.6–2.4%/month in illiquid stocks vs ~0.04–0.14% in liquid** ones — the effect
lives where arbitrage is costly ([PEAD review, ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214635020303750)).
**Prior:** our SME/microcap recent-IPO cohort is the highest-a-priori place for drift to survive — supports
RUNG-1's earnings category and any future earnings-drift test. BUT it's an *earnings-event* drift, which
RUNG-1 (context-only) does not trade and which needs a forward-collected results-date feed to test → keeps
the predictive version DATA-GATED, not killed. [HYPOTHESIS for our cohort — not yet our-data-tested.]

### 3b. Index-inclusion = front-runnable price-pressure, then reversal (sharpens index-inclusion category — supportive but two-sided)
NSE/CNX inclusions: prices jump **>3% on announcement then nearly fully reverse within ~2 weeks**; likely
additions **rise 5–10% in the week before** the change as sophisticated players front-run; the pattern is
**price-pressure, not information** ([Macrothink, *Price and Volume Effects Associated with Index Additions*](https://www.macrothink.org/journal/index.php/ajfa/article/download/469/815)).
Caveat: the global "index effect" has been **decaying** as it became widely known ([Greenwood & Sammon, *The
Disappearing Index Effect*, HBS WP 23-025](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf)).
**Prior:** an index-inclusion chip is useful *context* (explains a run-up + warns of post-event give-back),
and the run-up is anticipatable (forward-dated) — but as a TRADE it's a fast, decaying, large-cap effect that
our recent SME/microcap IPOs rarely qualify for (they're not index candidates early). **Keep as a context
category; do NOT elevate to a signal for our universe.** [TO-BE-TESTED if ever: which of our names actually got
included, and N is likely tiny.]

### 3c. Corp-action (bonus/split) announcement effect is SMALL on average but a liquidity/retail event (sharpens H7 — nuance, mild caution)
Indian event studies: average announcement abnormal returns are modest — **~1.8% for bonus, ~0.8% for splits**
— with mixed evidence on whether the return clusters at announcement vs ex-date, and the stated corporate
motive is **liquidity / retail participation** ([ResearchGate, *Stock Split Announcement Effect on Stock
Returns: Evidence from Select Indian Companies*](https://www.researchgate.net/publication/322423133_Stock_Split_Announcement_Effect_on_Stock_Returns_Evidences_from_select_Indian_Companies)).
**Prior:** the *average* effect is small — so our F10/H7 "euphoria-top" thesis is NOT the generic
announcement-return literature; it's the narrower, behaviorally-distinct claim that a corp action *timed after
a big run in a recent IPO* marks a retail-demand top (F10: n=31, fwd-3m −22% vs +2% controls). The literature
neither confirms nor refutes that specific conditioning — it just reminds us the unconditional effect is tiny,
so H7's edge (if real) is entirely in the *post-run-up, recent-IPO* conditioning, which we CAN backtest now
from `corp_actions.csv` (2006+, cross-regime-capable). **Supports running H7; cautions against expecting a
generic effect — the conditioning is the whole hypothesis.**

### 3d. Indian IPO long-run UNDERPERFORMANCE confirms the base rate (sharpens the whole tool — supportive)
Indian evidence: IPOs **underperform by ~29% over 3 years post-listing**, influenced by market-cap, issue
premium, face value, issue price, oversubscription ([IBIMA, *Post Listing IPO Returns and Performance in
India*](https://ibimapublishing.com/articles/JFSR/2021/418441/)); the long-run underperformance puzzle is
tied to the **idiosyncratic-risk / limits-to-arbitrage** puzzle ([ScienceDirect, *IPO underperformance and
the idiosyncratic risk puzzle*](https://www.sciencedirect.com/science/article/abs/pii/S0378426621001497)).
**Prior:** independently corroborates our VALIDATED `desc-lasting-wealth` finding (MB underperforms in both
regimes) — any news/drift signal sits on top of a structurally negative base, so the bar for a *positive*
catalyst signal to beat do-nothing is high.

### 3e. "High delivery% = conviction → returns" has NO academic support — practitioner heuristic only (sharpens D2 — cautionary)
Despite wide practitioner use (brokers/screeners frame high delivery% as "genuine accumulation"/"conviction"
— [Tradejini](https://www.tradejini.com/blogs/delivery-volume-in-the-cash-market-a-key-indicator-for-investors)),
search surfaced **no peer-reviewed evidence** that delivery% *predicts forward returns* (only descriptive
screeners and blogs). Contrast: the attention/volume literature finds high-attention/high-volume names often
**underperform** ([Barber & Odean, *All That Glitters*](https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/allthatglitters_rfs_2008.pdf)),
so "high activity = good" is not safe a priori. **Prior:** treat D2 as a folk signal with a weak prior, worth
exactly ONE disciplined falsifiable test (the placebo/incremental-to-volume design in §1b), expecting
display-only-or-rejected — NOT a likely score addition.

---

## 4. SCOPE-DOWN RECOMMENDATION (updates the map's ranking)

The map ranked the 3 "worth doing" as: (1) delivery-% [DO FIRST], (2) H7 corp-action backtest, (3) RUNG-1
feed. **This R&D changes the order**, driven by the delivery-% history finding (the linchpin).

**Re-ranked:**

1. **H7 corp-action euphoria backtest — PROMOTE to DO-FIRST.** It's the only one that is (a) backtestable
   TODAY with data in hand (`corp_actions.csv`, 2006+, ISIN/symbol-keyed), (b) **cross-regime-capable** (so it
   can actually clear the project's validation gate, unlike delivery-%), (c) zero new fragility / no new pull,
   (d) extends a thin shipped flag (F10, n=31) toward graduation. Lowest cost, highest gate-clearing odds.
   Watch the F10 double-count + the §3c caution (the edge is the post-run-up/recent-IPO conditioning, not the
   generic small announcement return). **Beat do-nothing?** Yes-or-no is decidable now: does a fwd-3m short/avoid
   on post-run-up corp-action names beat holding, cross-regime, after the matched-control + placebo? Run it to kill-or-keep.

2. **RUNG-1 explanatory feed — KEEP at MEDIUM, but it's the best near-term PRODUCT.** Spec is turnkey (§2),
   moat-safe (display-only), reuses `nse_session.py`, no LLM/egress. Pair with starting the announcement
   staging clock NOW (the only way to make any RUNG-2 predictive test possible in 18–36mo). Not a signal, so
   no "beat do-nothing" — ships as honest context. Gated only on a network+babysitting session.

3. **Delivery-% (D2) — DEMOTE from "DO FIRST" to "ONE disciplined test, expect display-only."** The map hoped
   it could "clear our bar" and become a score candidate. The history finding (§1a) **caps it at boom-only
   (2017+) → it can never be cross-regime-validated → can never enter the weighted score** under the locked
   policy, no matter how strong. Add the weak academic prior (§3e) and the volume/momentum overlap, and the
   realistic ceiling is **display-only**. It also costs a NEW daily `sec_bhavdata_full` pull (separate from our
   bhavcopy) — real build + maintenance. So: still worth ONE falsifiable test (it's cheap to settle and the
   map made it the linchpin), but reframe expectations — it is NOT the "surprise winner that could carry the
   catalyst direction." If H7 and the feed are the budget, delivery-% is optional. **Beat do-nothing?** Only if
   it adds OOS top-quintile lift over the 8-component score AND survives both placebos — and even then it's
   display-only (boom-only). Prior: unlikely.

**Unchanged from the map:** KILL social / hosted-LLM polarity / RSS fuzzy-match / all-stocks TA+FA+news
fusion. PARK the forward-only H1–H6/H8/H10/H11 (collect the staged feed quietly; 18–36mo clock).

**One-line scope-down:** *Do H7 first (only cross-regime-capable, data-in-hand), ship RUNG-1 as honest
context + start the staging clock, and run delivery-% as a single falsifiable display-only experiment — not as
the linchpin the map hoped for, because its history doesn't reach the longterm cohort.*

---

### Sources (key)
- NSE security-wise / sec_bhavdata_full file + columns: [NSE Security-wise Archives](https://www.nseindia.com/report-detail/eq_security) · [NSE All Reports](https://www.nseindia.com/all-reports) · column list & endpoint via downloader writeups ([GamesOfTrading](https://gamesoftrading.in/algo/how-to-fetch-historical-data-from-nse-daily-bhavdata-csv-file-through-python-save-it-in-database-table), [MicroStocks](https://www.microstocks.in/blog/how-to-read-nse-bhavcopy-data)).
- PEAD India: [SCIRP](https://file.scirp.org/Html/20-1501629_88060.htm) · PEAD/illiquidity review: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214635020303750).
- Index inclusion: [Macrothink](https://www.macrothink.org/journal/index.php/ajfa/article/download/469/815) · [Greenwood & Sammon (HBS)](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf).
- Corp-action effect (India): [ResearchGate split study](https://www.researchgate.net/publication/322423133_Stock_Split_Announcement_Effect_on_Stock_Returns_Evidences_from_select_Indian_Companies).
- Indian IPO long-run underperformance: [IBIMA](https://ibimapublishing.com/articles/JFSR/2021/418441/) · [ScienceDirect idiosyncratic-risk](https://www.sciencedirect.com/science/article/abs/pii/S0378426621001497).
- Attention/volume caution: [Barber & Odean](https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/allthatglitters_rfs_2008.pdf) · delivery practitioner framing: [Tradejini](https://www.tradejini.com/blogs/delivery-volume-in-the-cash-market-a-key-indicator-for-investors).
