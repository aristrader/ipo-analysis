# Thread A — Paper-portfolio sim + per-stock ₹1L charts — design spec (2026-06-08)

Owner-approved in discussion. The "growth of ₹1L" framing — the intuitive answer to "would
following this tool have beaten the index?" (portfolio) and "what would this IPO have done to my
money?" (per-stock). Pure reader over the calls ledger + substrate + adjusted price series + Nifty.
No new data. Survivorship-honest. Free, on-ethos (descriptive, not a new signal).

## Component 1 — Portfolio sim engine (`layer3/portfolio.py`, pure; `run_portfolio.py` CLI)
**Question:** if you deployed a fixed ₹1L into every APPLY call, what's your equity curve vs ₹1L
into Nifty on the same dates?
- **Universe:** APPLY (and EARLY_APPLY) calls from the ledger. Optional AVOID-as-short is OUT
  (we don't short; AVOID = "didn't buy", shown as opportunity-avoided, not a position).
- **Two entry lenses (both reported, never pooled):**
  - **Secondary buyer (HERO/main lens):** entry = listing close (`adj_listing_close`); the
    realistic view — you can always actually buy on listing day. Lead with this number.
  - **Allottee (comparison):** entry = adjusted issue price; full ₹1L invested (includes the
    listing pop). OWNER DECISION 2026-06-08: NO idle-cash/allotment haircut — assume the full ₹1L
    is invested if allotted (the "if you got allotment" view), apples-to-apples with secondary.
- **Per-position value to "today":** adjusted daily price series (`data/prices/<isin>.csv`) →
  current value; **delisted → terminal (wipeout = ₹0, else last price), and the position STAYS in
  the curve at its dead value** (survivorship honesty, decision A1). Split/bonus already adjusted.
- **Benchmark:** ₹1L into Nifty 50 on each position's entry date, same horizon → an index curve.
- **Aggregation:** equal ₹1L per call; report (a) total deployed, (b) total value now, (c) CAGR,
  (d) vs-Nifty spread, (e) the **equity curve** (sum of position values over calendar time), (f)
  hit-rate + median/mean per-position multiple + P10/P90. **Split every output by `mode`**
  (live/gap_filled = forward truth · backfilled = OOS · historical_sim = rehearsal) — never pooled.
- **Honesty:** headline must state the curve is mostly backfilled/sim until live calls mature.
  Credible-interval band on the win-rate (ties into A.2). MIN_N floors respected.

## Component 2 — Per-stock ₹1L (a function in `layer3/portfolio.py`, rendered on IPO Detail)
`growth_of_1l(isin)` → three aligned series from listing date to today/terminal:
- **at-IPO "if allotted"** (entry = `issue_price_adj`) — labeled "if allotted" (lottery caveat)
- **at-listing** (entry = `adj_listing_close`)
- **Nifty** (₹1L into the index over the same dates)
Returns tidy long-form DF for an Altair multi-line chart. Wipeout → line goes to ₹0 and stays.

## App wiring (render-only; the build-LAST app rework will refine placement)
- **Track Record screen:** the portfolio equity curve as the primary visual (mode-faceted) +
  the summary table. Replaces/augments the current text track-record.
- **IPO Detail screen:** `growth_of_1l` chart as a toggle alongside the §⑥ price-vs-reference
  chart (or its own sub-section). "if allotted" line ON by default but clearly labeled.
- Cached loaders; lazy per-ISIN price reads (reuse `app/ui.py` patterns).

## Tests (`tests/layer3/test_portfolio.py`)
1. ₹1L into a known +50% stock (no splits) → ₹1.5L (allottee math correct).
2. A delisted/wipeout name → position value ₹0 and PRESENT in the aggregate (survivorship).
3. Allotment haircut applied to allottee lens, not to secondary-buyer lens.
4. Mode split never pools live with historical_sim.
5. Nifty benchmark uses each position's own entry date (not a single global start).
6. growth_of_1l returns 3 series, all starting at ₹1L, aligned dates, wipeout→0 monotone tail.

## Assumptions (flag at checkpoint)
A1 ₹1L equal-weight per call (not size-weighted). A2 allottee haircut = the strat-flip-ev ~+2%
real-EV model. A3 horizon = to today (live) / to delisting (dead). A4 AVOID shown as
avoided-loss context, not a short. A5 raw ₹-value charts (the alpha/% view already exists
elsewhere — this is the intuitive money view).
