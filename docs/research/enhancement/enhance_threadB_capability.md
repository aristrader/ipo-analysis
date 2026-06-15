# Thread B capability expansion — pipeline-hardening & data-capture (scan)

_Lens: make Thread B's schema-gate + GMP-history MVPs genuinely STRONGER, within free-data +
no-heavy-deps + company-laptop constraints. Each: what · free feasibility · effort · blocker.
Ranked by value-per-effort. NON-rec = gold-plating for a single-user local tool. (2026-06-08)_

Baseline today: `tools/checks/schema_gate.py` pins typed/range/null contracts on `ipo_analysis.csv`
+ `calls_ledger.csv` but runs STANDALONE (not in the per-turn hook). `live_board.py` accumulates
`daywise_sub.csv` + `gmp_history.csv`. Gaps below build on exactly those two.

## Tier 1 — high value-per-effort (do first)
1. **Cross-field invariants in the schema gate** (S). The gate checks columns in isolation; the real
   refresh bugs are CROSS-field. Cheap, pure-pandas row predicates to add: (a) `adj_listing_gain_open`
   ≈ `(adj_listing_open/issue_price_adj − 1)` within tol — catches the scale-inversion class directly;
   (b) `alpha_1d` ≈ `return_from_listing_1d − nifty_ret` sanity (alpha ≤ raw when index up); (c) monotonic
   dates `open_date ≤ close_date ≤ listing_date`; (d) per-horizon return bands (e.g. no `return_*_1d`
   < −1.0 or > +5.0; alpha within sane window) flag-not-drop. Source: substrate already has all cols.
   Blocker: pick tolerances from the frozen substrate, not guesses, or false alarms.
2. **Wire the gate into the per-turn `verify.py --quiet` hook** (S). Today the gate only fires when run
   by hand; drift between refreshes goes unseen until someone remembers. Call `schema_gate.check_all()`
   inside verify's quiet path; any violation prints → injected into context like map-drift already is.
   Blocker: keep it <~0.3s (it reads 2 CSVs already; fine) and exit-0 in quiet mode (warn, don't fail turn).
3. **Referential integrity: ledger ISINs ⊆ substrate ISINs** (S). Every `calls_ledger.isin` (and live-board
   isin, once it has one) should resolve to an `ipo_analysis.isin`, else the call grades against nothing.
   One set-difference check in the gate. Free, instant. Blocker: live/upcoming names legitimately not yet
   in substrate — scope the check to ledger rows with a non-null grade only.
4. **`fetched_at` freshness check on the live board** (S). `board.json` carries `fetched_at`; nothing
   asserts it isn't stale. Gate/verify: warn if `now − fetched_at > N days` during an IPO window. Pure
   stdlib. Blocker: N must be window-aware (weekends/no-open-IPO periods shouldn't alarm).

## Tier 2 — worth it, slightly more surface
5. **Delivery % daily capture** (M). NSE sec-wise delivery (`/api/snapshot-capital-market-largedeal`
   sibling; bhavcopy-adjacent `sec_delivery` MTO file is FREE + official). A genuinely new post-listing
   conviction series no free IPO tool keeps per-ISIN. Plug: extend the bhavcopy job, join by SYMBOL→ISIN.
   Blocker: MTO file is symbol-keyed + format-fiddly; must pass "evolve-only-if-robust" before it scores.
6. **Coverage / drift report over time** (S–M). A tiny `data/live/coverage_log.csv`: per refresh, append
   {date, n_open, n_upcoming, n_gmp_nonnull, n_sub_nonnull}. Plotting null-rate creep = scraper-rot alarm
   that's cheaper than changedetection.io and needs no daemon. Blocker: none; just append + a sparkline.
7. **Richer day-wise board snapshot** (S). We already append `daywise_sub.csv` once/day per open issue;
   capture is currently last-write-per-day. Add the intra-day MAX subscription seen (the close-evening
   surge is the signal) by keeping the row with highest `sub_total_x` per (date,name) instead of first.
   Blocker: needs ≥2 fetches/day to matter — launchd already runs thrice daily, so free.
8. **Anomaly flag on incoming refresh** (S). Robust z-score / IQR of each new listing_gain & subscription
   vs frozen substrate distribution; flag (don't ingest) outliers. Complements #1's hard bands with a
   soft "this is historically weird" tag. Blocker: none; pure numpy.

## Tier 3 — defer / NON-rec for a single-user local tool
- **Bulk/block-deal capture** (M) — listed in next_capabilities_scan; real but a NEW feature input that
  must survive testing, not pipeline-hardening. Defer to a hypothesis thread, not Thread B.
- **changedetection.io daemon** — NON-rec here: #6's coverage_log gets 80% of the rot-alarm value with
  zero Docker/daemon (company-laptop policy unconfirmed). Revisit only if source layouts actually break.
- **Pandera / Great Expectations** — NON-rec: the pure-dict gate is the project's chosen style; adding a
  framework is the gold-plating the gate was written to avoid.
- **Full schema census (every column typed)** — NON-rec: contract the cols we DEPEND on (current design),
  not all ~120; a full census is maintenance burden with no single-user payoff.
- **Block/allotment per-PAN, registrar scrapes** — NON-rec (CAPTCHA, no analytical value; already judged).

## Fit notes
- Tier 1 is all pure-pandas/stdlib over files/JSON we already produce — no new deps, no new sources,
  company-laptop-safe. That's why it ranks above every new-source idea.
- Anything that becomes a SCORE input (#5 delivery%, deals) still routes through evolve-only-if-robust;
  capture-now / test-later is the right posture for those.
