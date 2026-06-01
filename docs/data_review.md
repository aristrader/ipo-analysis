# Data Review Register

Every known doubtful / needs-checking / partial item in the dataset, with where it lives and what to
verify. This is the "come back and fix later" list. Update as items are resolved.
(Resolved items kept at the bottom for history.)

Last updated: 2026-05-31.

---

## A. Values that disagree between sources (verify which is right)

- **`data/master/screener_financials_review.csv` (21 rows)** — screener vs old Sharescart `pre_ipo_*`
  disagree >5%. Screener (correctly-dated) was used; some are big (Anand Rathi Wealth FY21 net_sales
  846 vs 273; Concord Enviro FY24 PAT 96 vs 41). **Check:** standalone-vs-consolidated or Sharescart
  contamination? Spot-check ~5 against the DRHP/annual report; confirm screener is right.

- **`data/master/reconciliation_report.csv` — 62 SOFT rows** — issue_price / listing_open / sub_total
  differ >5% between new and old (mostly the old decimal-bug fixes). **Check:** glance for any where the
  NEW value looks wrong (most are corrections, but confirm none regressed).

## B. Identity not cross-verifiable (small)

- **27 `no_ref` rows** (`name_isin_check=='no_ref'` in the masters) — ISIN not in any NSE/BSE exchange
  list, so company name/ticker couldn't be cross-checked against an authoritative source. **Check:**
  eyeball name+ticker for these 27 (likely fine, but unverified).

## C. Coverage gaps (partial fields — source limitation, not error)

- **SME financials — 272/887 missing; only 34 SME screener-verified.** Screener rejected **834 rows**
  (mostly BSE-SME) because its numeric-BSE-code slug resolves to the wrong/absent company → concrete
  check correctly rejected them. **Fix option:** add screener **name-search** resolution (search by
  company name → correct slug → verify exchange code) to recover many SME. ~1 build.
- **Mainboard financials — 18 missing.** Minor; no screener match + no Sharescart.
- **Subscription gaps** — MB 29, SME 147 (no source covers these). Diminishing returns.
- **GMP gaps** — ~252 rows have no GMP at ipowatch or investorgain (often genuine ₹0/weak IPOs; some may
  be true source gaps). Low priority — GMP is inherently sparse.
- **promoter_pre/post_issue_pct** — partial (MB 244/202, SME 652/562). **No clean source:** Chittorgarh
  has promoter *shares* not %, and converting needs total share count. Parked.
- **G4 — 8 SME missing `market_maker`** — re-check Chittorgarh detail for those 8 ISINs.
- **G6 — 39 `price_source=none`** (`data/master/price_source_review.csv`) — recent SME not on Yahoo or in
  the bhavcopy cache yet. **Expected to resolve automatically with the full Layer-2 bhavcopy pull.**

## D. Methodology caveats (note when analyzing)

- **Pre-IPO EPS may be on a pre-split share base** (screener reports historical EPS before IPO-era share
  count). Absolute ₹-cr financials (sales/PAT/assets) are comparable; **EPS across the IPO boundary is not.**
- **Financials are consolidated where available** (else standalone) — restated vs DRHP in some cases.
- For long-term return work: use **total return** (splits/bonus/dividends) and **benchmark vs Nifty**
  (alpha, not raw return); treat delisting as a real outcome, not a dropped row.

---

## E. Long-term cohort (2006–2019, longterm_*.csv) — coverage limits (inherent)

- **Subscription pre-2017 unavailable.** NSE's per-symbol subscription endpoint only returns data for
  ~2017+ IPOs (verified: DMART/HDFCLIFE 2017, BANDHANBNK 2018, IRCTC 2019 work; Coal India 2010,
  POWERGRID 2007, Muthoot 2011 return empty). So long-term subscription = 89 MB rows (2017–19 only).
  No free per-symbol source found for pre-2017 split. SME old subscription not pursued.
- **Financials survivor + recency limited.** Screener keeps ~10–12 yrs, so the pre-listing FY only exists
  for newer-listing (~2015+) *survivors*; pre-2015 and delisted IPOs can't be derived → blank (expected,
  and the delisted blanks are themselves a survivorship signal). Applied so far: 51 MB + 2 SME.
  **~588 ISINs (68 MB + 520 SME) remain for a screener grinder pass** — most SME will resolve to
  "not on screener". Resume: `pipeline/longterm/04_financials.py --fetch --delay 1.5` (resume-safe).
- **No GMP** in the long-term cohort by design (doesn't exist pre-2020).
- Detail (Chittorgarh) is near-full (MB ~500, SME ~520); market_maker=0 on MB is correct (SME-only).

## F. Layer-2 returns (price-derived) — known residuals
- **Splits/bonus MISSING from the NSE corp-actions feed.** Adjustment now matches by symbol+ISIN (116→383
  stocks fixed; IRCTC +59%→+697%, Astral bonus chain applied). BUT some old/SME splits aren't in the feed at all
  (e.g. **Aditya Vision** 10:1 FV split absent) → those stocks' issue-anchored returns are still understated and
  `listing_gain` distorted (Aditya listing_gain shows −90%). FIX OPTION (screener_weekly rows): infer the cumulative
  split factor from Chittorgarh raw listing ÷ screener adjusted listing, and adjust issue_price by it. ~the 16
  remaining `xcheck_review.csv` mismatches + some screener_weekly stocks are affected. Quantify in review.
- **Listing metrics for old BSE-SME** come from screener WEEKLY (price_source='screener_weekly') — first weekly
  point ≈ listing, not exact day-open; fine for long-term, coarse for listing-day event studies.
- 8 stocks (`none_listing_era`) screener couldn't resolve → listing-anchored columns NULLed (no wrong values).

## Resolved (history)
- ticker_conflicts.csv → 0 (4 renames confirmed via name_overrides.csv).
- name_isin_review.csv → 0 (12 renames confirmed; Meson→Quest Flow, Ambey→Dhansa, etc.).
- 13 "missing" old-ISIN rows → all present under corrected ISINs.
- Sharescart yr2/yr3 post-IPO contamination → re-sourced from screener (mainboard).
- **xcheck_review.csv (14 listing-price mismatches) → REVIEWED 2026-06-01, no fix needed.** The analysis uses the
  bhavcopy-derived `adj_listing_*` (the official exchange price); Chittorgarh's raw `listing_open` is kept separately
  and is NOT used for gains. Checked all 14 against issue_price: the bhavcopy value is the plausible one in ~12
  (e.g. Prime Customer 60≈issue 60 vs Chittorgarh 169; Inox 172 vs 285; SoftTech 88 — independently confirmed).
  Veranda = NSE(125, ours) vs BSE(157, Chittorgarh) — both correct, different exchanges. Puravankara genuinely
  ambiguous (public records cite ₹361.75, matching neither) — left flagged. Net: our computed values are sound.
- **210→12 low data_quality (era-aware fix) + the 12 residual low rows → ACCEPTED 2026-06-01 as legitimately sparse.**
  The 210 were mostly old IPOs unfairly penalised for era-impossible GMP/subscription (fixed: `09_assemble`
  era-aware quality). The 12 remaining are genuinely irrecoverable (no screener page / delisted / BSE code
  reassigned to a different company → unsafe to fill) per the enrichment agent. Kept flagged, not filled.
- **24 boom 'SME' sector no-matches → RECOVERED 2026-06-01.** They were RENAMED companies (Zomato→Eternal,
  Burger King→RBA, Angel Broking→Angel One, …) matched safely by permanent BSE/NSE code → in `sector_mcap.csv`.
