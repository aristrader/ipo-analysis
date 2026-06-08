# Future ideas — owner's "someday" backlog (started 2026-06-08)

Big ideas we want eventually but aren't building now. Each: the idea, why it matters, what it
needs, the honest blocker. Pick one up when ready. (Small/tactical items live in STATUS backlog.)

## 1. Swing-trade buy/sell calls (post-listing entry → take-profit exit)
**Owner's idea (2026-06-07/08):** beyond the IPO-time APPLY/AVOID, give *trade* calls on already-
listed names — "buy when X happens, then sell the day it's up ~20%" — pushed via the bot.
**Why it matters:** turns the tool from an IPO-decision aid into an ongoing trade companion.
**Status of the EXIT side:** heavily tested. A fixed take-profit (+15/+25/+40%) LOSES to buy-and-
hold cross-regime — it caps the rare big winners that carry IPO returns (the "timing tax":
P(ever 2x) ≫ P(end 2x)). See M1 exit-discipline finding + rules/index. So a blanket "sell at +20%"
is not validated. (A fresh test of a CONDITIONAL version is logged in tier1_wave1_verdicts —
2026-06-08 swing-trade test.)
**Status of the ENTRY side:** weak. "Buy after a fall" rejected; breakout-buys falsified; issue-
magnet was placebo. Only survivors post-listing: month-1 persistence lean (already a call) + the
coarse tape regime. **What would change the verdict:** a genuinely new entry signal that survives
the 3-layer protocol, OR the news/catalyst feed below (idea #2) giving an event-driven entry.
**Decision:** keep as research, not a product feature, until an entry signal earns its keep.

## 2. Stock-news / catalyst feed to sharpen buy-sell calls
**Owner's idea (2026-06-08):** track news on our stocks (results, orders, management changes,
regulatory, sector events). Real catalysts move prices and SHOULD change a buy/sell decision —
our price-only model is blind to them.
**Why it matters:** the single biggest missing input. A "+20% in 3 days" move means opposite
things if it's (a) a real earnings beat vs (b) an unexplained pump. News tells them apart.
**What it needs (a real sub-project, not a quick add):**
- A news source per stock. Options to scope: free RSS (Google News / company filings via BSE/NSE
  announcements API — these are FREE and structured), Screener's "Documents/Announcements" tab,
  moneycontrol/ET RSS. Paid APIs exist but violate the free-data rule.
- A scraper per source (like our existing one-file-per-source pattern) → staged, never into the
  frozen substrate (same discipline as the live board).
- Entity-matching news → ISIN (the hard part — same fuzzy-matching problem that parked F11).
- Then: does a catalyst tag actually improve a trade decision? = another 3-layer hypothesis test,
  NOT an assumption. (News-reaction edges are famously arbitraged away fast.)
**SCOPE DONE (2026-06-08, tools/research/scope_news_feed.py): VIABLE.** The FREE NSE
corporate-announcements API returns HTTP 200, ~18-28 announcements per active listed name (5/8
sampled; the 0s were very-recent/illiquid symbols), with fields `an_dt`/`dt` (date), `desc`/
`attchmntText` (subject), `attchmntFile` (attachment), `smIndustry`, and crucially **`sm_isin`** —
**the ISIN is IN the payload, so news→stock matching is SOLVED for free** (the blocker that parked
this is gone). Remaining hard part is ONLY "good vs bad classification" (the LLM/ethos/laptop
tension) — but a raw dated-announcement feed per held stock is useful even WITHOUT classification.
**Upgraded: Large build → Medium, data de-risked.** Next when picked up: build a one-file scraper
(reuse scrapers/nse_session.py) → data/live staging keyed on sm_isin → show on IPO Detail /
tracking cards; THEN (optional) a classification + 3-layer test of whether catalysts improve calls.

## How to pick one up
Both route through the standing process: brainstorm → spec → 3-layer test where it's a
hypothesis (docs/research/hypothesis_protocol.md) → only ship what survives. News feed = build +
test; swing-trade = mostly a test that's already leaning "no" on current signals.

## Owner discussion parking-lot
- **Discuss Fujiyama and Park Hospital** (owner note 2026-06-08) — context to be supplied when we pick this up.

## Thread C data-gated hypotheses (2026-06-08 — pursue when the data exists)
- **Pre-IPO accruals (earnings-quality red flag):** needs RECEIVABLES + CASH-FLOW-FROM-OPS per IPO
  (re-scrape screener); then Modified-Jones discretionary-accruals test upgrades the n8 flag.
- **SME→Mainboard migration:** needs a migration-date source (Chittorgarh report 123 / BSE / NSE).
  Then: migration as an outcome class + a predictive feature (the SME escape from the dead-money trap).
