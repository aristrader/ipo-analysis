# Next-capabilities scan — "what could take this project to the next level"

_Scout report (2026-06-08). Brief: free + feasible + high-leverage things we are NOT yet doing, across
data sources, automation/infra, techniques, and "good-to-have" product capabilities. Each item: what /
enabler / how it plugs in / effort (S/M/L) / payoff / honest blocker. NOT a build order — a menu.
Routes through the standing process (brainstorm → spec → 3-layer test where it's a hypothesis)._

## TOP 8 — highest-leverage, free & feasible (ranked)
1. **Post-listing monitor via daily bhavcopy** — already-owned source; close the live-tracking gap on our own calls. (S, infra we already have.)
2. **Pandera schema gate on the substrate + staging CSVs** — codify the invariants verify.py asserts informally; catch silent data drift. (S)
3. **NSE corporate-announcements feed → ISIN, staged** — the FREE structured news source future_ideas.md flagged as step-1; entity-match is the only hard part. (M)
4. **Wilson / Jeffreys credible intervals on every base rate** — honest small-N framing; drop-in via statsmodels. (S)
5. **GMP-history daily capture (live board)** — we read GMP point-in-time; logging the SERIES makes a new own dataset no free tool keeps well. (S)
6. **NSE/BSE bulk & block-deal capture** — free official endpoint; post-listing smart-money flow per ISIN. (M)
7. **Calibration tracking on the calls ledger** — we log calls; we don't yet score "when we say 70%, is it 70%?" reliability curves. (S)
8. **changedetection.io watch on source pages** — self-healing/scraper-rot early warning + DRHP-filing change-detect, self-hosted, no third party. (S–M)

---

## Bucket A — FREE data sources we're not tapping
- **NSE corporate-announcements** — `nseindia.com/api/corporate-announcements?index=equities[&symbol=]&from_date&to_date`; same curl_cffi/cookie-prime session as our nse_subscription scraper. Plug: new `scrapers/nse_announcements.py` → staged feed → entity-match to ISIN (the F11 fuzzy problem; symbol is in the payload so it's tractable). Effort M. Payoff HIGH (the #1 missing input per future_ideas.md). Blocker: relevance/sentiment classification needs an LLM (company-laptop + cost caveat) — keep raw-tag only first. https://bennythadikaran.github.io/NseIndiaApi/api.html
- **BSE announcements** — `BseIndiaApi` (BennyThadikaran, unofficial, free, JSON) covers SME better than NSE; mirrors our one-file-per-source pattern. Effort M. Payoff MED (redundancy + SME). Blocker: unofficial, maintenance. https://github.com/BennyThadikaran/BseIndiaApi
- **NSE bulk/block deals** — `nseindia.com/api/snapshot-capital-market-largedeal` (official, free, daily). Plug: `scrapers/large_deals.py` → staged, join by SYMBOL→ISIN. Effort M. Payoff MED-HIGH (smart-money post-listing flow; a genuinely new feature input to TEST, not assume). Blocker: name-in-deal ↔ ISIN matching; edge may not survive testing. https://www.nseindia.com/market-data/block-deal-watch
- **NSE event-calendar (results/board meetings)** — `nseindia.com/api/event-calendar`. Plug: powers a "results due" tag for post-listing watch + earnings-window event studies. Effort S–M. Payoff MED. Blocker: SME coverage thin. https://www.nseindia.com/companies-listing/corporate-filings-event-calendar
- **FII/DII daily flows** — NSE `reports/fii-dii` (provisional) + NSDL `fpi.nsdl.co.in` (final). Plug: a market-regime context series. Effort S. Payoff LOW-MED — NOTE: market-regime/sector-heat context was already TESTED & REJECTED (STATUS PARKED); re-use only as display context, not a score input. https://www.nseindia.com/reports/fii-dii
- **Quarterly shareholding pattern / promoter pledge** — NSE `corporate-filings-pledged-data` + BseIndiaApi shareholding methods. Plug: post-listing promoter-pledge-rising flag (a classic wipeout precursor; we have a wipeout finding to extend). Effort M. Payoff MED. Blocker: parsing XBRL/quarterly cadence; matching. https://www.nseindia.com/companies-listing/corporate-filings-pledged-data
- **SEBI DRHP/RHP filings list** — `sebi.gov.in/filings/public-issues.html` (web only, no official API). Plug: earliest-possible upcoming-IPO discovery (before Chittorgarh lists it). Effort M. Payoff MED. Blocker: HTML scrape, no structured API; DRHP-bulk-financials already PARKED (can't get useful columns). https://www.sebi.gov.in/filings/public-issues.html
- **NOT-viable (paid / rule-breaking):** stockinsights.ai tagged-announcements feed (paid AI feed), APIdatafeed, FinEdge, Apify IPO tracker — all paid/subscription → violate free-only. Ticker-plant APIs (~₹3L/yr) → NOT-viable.

## Bucket B — Automation / infra
- **Pandera schemas** on `ipo_analysis.csv` + every staging CSV — in-process, pandas-native, lightweight (Great Expectations is overkill here). Plug: a `pipeline/checks/schema.py`, run inside verify.py / pipeline steps. Effort S. Payoff HIGH (turns "verify.py asserts counts" into typed column/range/null contracts; catches refresh drift). https://aeturrell.com/blog/posts/the-data-validation-landscape-in-2025/
- **changedetection.io (self-hosted, free, OSS)** — watch source pages (Chittorgarh report layout, NSE API shape, SEBI public-issues list) → RSS/webhook → reuse Telegram notifier. Plug: scraper-rot early warning + DRHP-filed alert. Effort S–M. Payoff MED-HIGH (self-healing scrapers = less silent breakage). Blocker: a local Docker/daemon (company-laptop — confirm allowed; the project already avoids Playwright-by-default for the same reason). https://github.com/dgtlmoon/changedetection.io
- **Post-listing monitor loop** — we already pull daily bhavcopy + run launchd thrice-daily; extend the live-board job to refresh prices for in-ledger names and auto-grade maturing calls + fire the day-21/day-90 leans. Effort S (compose existing parts). Payoff HIGH (the PRODUCT.md "live track record is young" gap closes faster). Blocker: none material.
- **Quarto for the descriptive report** (Part A) — render `report/layer3_partA.html` as a versioned, reproducible static doc; keeps Streamlit for interactive only. Effort M. Payoff LOW-MED (nice-to-have; current HTML works). Blocker: adds a toolchain. https://quarto.org/docs/dashboards/
- **Data-quality alerting** — wire Pandera failures + freshness-staleness into the existing Telegram notifier (not just new calls). Effort S. Payoff MED.

## Bucket C — Techniques that fit a no-ML tool
- **Wilson / Jeffreys credible intervals** on every base rate & hit-rate — `statsmodels.stats.proportion.proportion_confint(method='wilson'|'jeffreys')`. Plug: replace/annotate the bare proportions in layer3 findings + scorecard + track record. Effort S. Payoff HIGH (directly serves the "distributions over means, show N, honest about small samples" ethos; better than ad-hoc min-N floors). https://www.statology.org/binomial-confidence-interval-python/
- **Event-study automation** — `easy_es` / eventstudy packages compute AR/CAR around dated events. Plug: once we have the announcements/results feed, measure abnormal alpha around results/orders for our names — turns "does a catalyst tag help a decision?" into a rigorous 3-layer test instead of a guess. Effort M. Payoff MED-HIGH (the validated way to vet the news idea). Blocker: needs the event feed first; right-tail/whipsaw lessons from M1 apply. https://github.com/Darenar/easy-event-study
- **Calibration tracking** — reliability curve / Brier score on the calls ledger (predicted P(up) vs realized). Pure numpy/scipy. Plug: a `layer3/calibration.py` + a Track-Record app panel. Effort S. Payoff HIGH (a serious, honest, ML-free way to measure whether our probabilities mean anything — nobody free does this for IPO calls). Blocker: needs enough matured calls (accruing).
- **Anomaly/outlier flags on incoming data** — robust z-score / IQR on each refresh vs the frozen substrate distribution (e.g. a listing_gain or subscription value far outside historical range = flag, don't ingest). Effort S. Payoff MED (data-integrity; complements Pandera range checks). Blocker: none.
- **Regime detection** — simple rule-based (Nifty drawdown / trailing-vol bands) regime tag. Effort S. Payoff LOW — market-regime context already TESTED & REJECTED as a score input; display-context only. (Listed for completeness; don't re-litigate.)
- **Prospectus text extraction** — local-only (pdfplumber/pymupdf, no LLM) for structured fields. Effort M, Payoff LOW — DRHP recovery already PARKED (useful columns unreliable). LLM-in-the-loop = NOT-viable on company laptop (data + cost). Keep parked.

## Bucket D — "Good-to-have" retail-investor capabilities (free tools do poorly)
- **GMP-history capture (own dataset)** — we read investorgain/ipowatch point-in-time; LOG the daily series into `data/live/` for upcoming IPOs. No free tool keeps a clean historical GMP series. Effort S (extend live_board). Payoff HIGH (own proprietary-ish dataset; feeds the day-1 early-call accuracy work that PRODUCT.md says is "collecting"). Blocker: GMP is unofficial/noisy — label as such.
- **Watchlist + calendar integration** — upcoming-IPO watchlist with open/close/listing dates → iCal export (stdlib `ics`), surfaced in app + Telegram reminders. Effort S–M. Payoff MED. Blocker: none.
- **Peer-comparison panel** — for any IPO, show its analog cohort's realized distribution side-by-side (we already compute analogs for the predictor; surface as a table). Effort S. Payoff MED (presentation of existing logic). Blocker: none.
- **Allotment tracking** — registrar (Linkintime/KFin/Bigshare) allotment-status pages. Effort M. Payoff LOW for THIS tool (personal-allotment, not analysis) + CAPTCHA/anti-bot → leans NOT-worth-it. Blocker: bot-protection, per-PAN, no analytical value.
- **Post-listing dashboard** — combine the monitor loop (B) + leans into a single "my listed names" view. Effort S once B exists. Payoff MED.

## Notes on fit
- Anything that becomes a SCORE input must pass "evolve-only-if-robust" (3-layer / cross-regime) — see rules/index.md before testing. Most Bucket-A/C items enter as display/context first.
- Sources B/D mostly compose tools we ALREADY run (bhavcopy, launchd, Telegram, live_board, analog engine) — that's why they rank high: low new-surface, low maintenance, free, company-laptop-safe.
- Confirm Docker/daemon policy before changedetection.io; everything else is pure-Python over endpoints we already hit similarly.

## Sources
- NSE unofficial API (announcements/deals/calendar): https://bennythadikaran.github.io/NseIndiaApi/api.html · https://github.com/BennyThadikaran/NseIndiaApi
- BSE unofficial API: https://github.com/BennyThadikaran/BseIndiaApi
- NSE bulk/block: https://www.nseindia.com/market-data/block-deal-watch · NSE FII/DII: https://www.nseindia.com/reports/fii-dii · NSDL: https://www.fpi.nsdl.co.in
- NSE event calendar: https://www.nseindia.com/companies-listing/corporate-filings-event-calendar · pledged: https://www.nseindia.com/companies-listing/corporate-filings-pledged-data
- SEBI public issues: https://www.sebi.gov.in/filings/public-issues.html
- Pandera/validation landscape: https://aeturrell.com/blog/posts/the-data-validation-landscape-in-2025/
- changedetection.io: https://github.com/dgtlmoon/changedetection.io
- Wilson/Jeffreys CIs: https://www.statology.org/binomial-confidence-interval-python/ · https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
- Event study: https://github.com/Darenar/easy-event-study · https://pypi.org/project/event-study-toolkit/
- Quarto: https://quarto.org/docs/dashboards/
