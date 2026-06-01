# Layer 2 (price history + returns) — build blueprint

Validated via parallel source research (2026-05-31). All sources tested live. Nothing integrated yet.

## Goal
Daily price history → a one-row-per-IPO **returns-summary** table that the Layer-3 rules run on,
for the full 2006–2025 universe (boom + long-term cohorts), survivorship-correct (incl. delisted).

---

## Feature spec (what we compute — every column maps to a question)

Reference prices: compute returns from BOTH **issue price** (allotment holder) and **listing price** (listing-day buyer).

- **Listing day:** listing gain (open vs issue), day-1 H/L/C, close-vs-open (pop hold/fade).
- **Short-term windows** (1d,1w,1m,3m,6m): return-from-issue, return-from-listing, **max upside (MFE)** &
  **max drawdown (MAE)** within window, closed-below-issue + when.
- **Long-term anniversaries** (1y,2y,3y,5y,10y): return-from-issue, return-from-listing, **CAGR**.
  (5y/10y only populate for the 2006–2015 cohort.)
- **Trajectory/upside-downside:** per-holding-year high & low (+dates), all-time high/low since listing,
  current/last price, **max drawdown ever**, peak return, time-to-peak, time-to-2x, broke-issue & recovery.
- **Relative/alpha:** vs **Nifty 50** and **Nifty Smallcap 250** at each horizon (alpha = stock − index).
- **Outcome/survival:** still-listed? delist date/reason/last-price; terminal return; class = multibagger(>2×)/winner/flat/loser/wipeout.
- **Liquidity/risk (esp. SME):** avg daily volume/turnover (+ first-week), **low-liquidity flag**,
  **circuit-lock flag** (open=high=low), volatility (annualized), beta vs index, drawdown duration.

All derivable from daily (split/bonus-adjusted) OHLCV + the two index series + delisting info.

---

## Validated sources

### Prices — bhavcopy (raw OHLCV backbone)
- **NSE bhavcopy:** 2006→present. Old format (pre 2024-07-08, match by SYMBOL, no ISIN) + UDiFF (≥2024-07-08, has ISIN). Full OHLCV+volume. Covers mainboard + NSE-SME + delisted-while-trading.
- **BSE bhavcopy:** UDiFF 2024→present (ISIN); legacy `EQ_ISINCODE_<DDMMYY>.zip` ~2021-02→2023 (ISIN_CODE); old `EQ{DDMMYY}_CSV.ZIP` back to ~2020 (match by SC_CODE, no ISIN).
- ⚠️ **GAP: BSE-only names before ~2021** — no free official daily source found. (Affects old BSE-exclusive/SME.)
- **Yahoo** = cross-check only for liquid mainboard (adjclose mixes dividends; fails SME/delisted).
- CODE: `scrapers/bhavcopy.py` currently stores **OPEN only** → must extend to full OHLC+volume; add BSE legacy fetchers; fix `scrapers/yahoo.py` to use period1/period2 (range=max downsamples).

### Adjustment — split/bonus (mandatory; bhavcopy is raw)
- **NSE Corporate Actions API** (RECOMMENDED): `/api/corporates-corporateActions?index=equities&from_date=&to_date=`
  (curl_cffi chrome + cookie priming, like scrapers/nse_subscription.py). 2006–2025, **ISIN + symbol** per row,
  parseable ratios (split = faceVal old/new; bonus = `Bonus a:b` → (a+b)/b). **Query index=equities AND index=sme** for SME.
- **BSE DefaultData API** (per scripcode, match bse_script_code): secondary for BSE-only + cross-check.
- Build a split/bonus table → cumulative multiplicative back-adjustment factors (dividends excluded, per decision).

### Indices — Nifty 50 + Nifty Smallcap 250
- **niftyindices.com** (RECOMMENDED, both, back to 2006): POST `Backpage.aspx/getHistoricaldatatabletoString`
  with double-encoded `cinfo` (name + start/end). Plain requests OK. Flaky → quarterly chunks + retry-on-empty + backoff.
- Yahoo `^NSEI` = Nifty 50 cross-check from 2007 only; no Smallcap 250 symbol.

### Delisting / status (3-layer, keyed on ISIN)
- **BSE ListofScripData API** (flag): `/api/ListofScripData/w?segment=Equity&status=Delisted|Suspended|Active`
  (curl_cffi + priming + must pass params). ISIN-keyed, covers SME (Delisted 4606 / Suspended 1240). No date/reason.
- **NSE delisted.csv** (date + reason, but ≤2020, NSE-only, no ISIN): Voluntary/Compulsory/Liquidation.
- **Bhavcopy inference** (universal fallback): last date ISIN/scrip appears = delist/suspend date proxy + last price.
  Only date source for SME/post-2020.

---

## Layer-1 additions (bonus — same screener resolver delivers these)
The fixed screener resolver (below) also extracts, per company: **Sector/Industry** (4-level breadcrumb) and
**Market Cap**. So we get sector + market-cap-class (micro/small/mid/large) for the whole universe from screener.
Market-cap-class anchored at listing (issue price × post-issue shares) is the fixed feature; current cap optional.

## Screener resolver FIX (fixes SME financials gap + delivers sector/mcap) — VALIDATED 15/15
Root cause of the ~834 SME rejections: verifying by on-page `NSE:/BSE:` codes, which **BSE-SME pages don't show**.
Fix: verify by **company-NAME match** (page `<h1>` vs our name, normalized) instead. Logic:
1. Try `/company/<bse_script_code>/` then `/company/<nse_symbol>/`; verify by normalized name (exact, or token-set
   containment ≥0.8 + Jaccard ≥0.5). Direct path may use a digit-stripped fallback (code already corroborates).
2. On 404 → `/api/company/search/?q=<normalized name>` → best name match → fetch its url (handles `/company/id/<id>/`
   for **delisted**) → re-verify by name.
3. Extract financials (existing parse_financials), Market Cap, Sector breadcrumb.
Projected recovery ≈ 85–95% of the 272 missing SME. Estimated cost ~2–4 requests/company; keep 1 worker + ~1.5s + circuit-breaker.

---

## Output shape
- `data/prices/<isin>.csv` — daily adjusted OHLCV per stock (raw kept too, or adjust on read).
- `data/master/returns_summary.csv` — one row per IPO with the feature spec above; joined to masters by ISIN.
- Index series cached under `data/reference/indices/`.

## Build order (proposed)
1. **Screener resolver fix** → recover SME financials + add sector + market-cap to all rows (completes Layer 1).
2. **Prices:** extend bhavcopy.py (full OHLCV) + pull NSE/BSE daily for the universe (2006–2025).
3. **Corporate actions** → adjustment factors → adjusted series.
4. **Indices** (niftyindices) + **delisting** (3-layer).
5. **Compute returns_summary** (the Layer-3 substrate).

Open gap to accept/track: BSE-only daily prices pre-~2021 — NOW SOLVED via screener chart API (below).

---

## DECISIONS (locked 2026-05-31)

**A1 Delisting return:** terminal value = last traded price, EXCEPT compulsory-delist / liquidation → −100%.
Flag reason-unknown. Always report results both WITH and WITHOUT delisted (survivorship transparency).
Priority for delisted = correct returns + delisting outcome (did investors get paid vs wiped out), not financials.
**A2 Liquidity:** compute volume/turnover + circuit-lock flag + liquidity score per stock in Layer 2;
report patterns on all vs liquid-only in Layer 3.
**A3 Non-equity:** tag `instrument_type` (equity/invit/reit/fpo); exclude from core IPO analysis (TODO list).
**A4 Validation rigor:** DEFERRED to Layer-3 design (capture sample sizes + cross-regime cohort meanwhile).
**A5 Adjustment correctness:** cross-check our split/bonus-adjusted series vs Yahoo adjusted-close for ALL
Yahoo-covered mainboard (~859); flag/fix divergences before trusting long-term returns.

**B1 Old BSE-SME prices:** SOLVED — **screener chart API** `/api/company/<id>/chart/?q=Price-Volume&days=10000`
(weekly, split/bonus-ADJUSTED, +volume, back to listing year, ~87% of 157 old BSE-only-SME). id via resolve()→
`data-company-id`. Daily bhavcopy still primary for NSE + post-2021 BSE. Weekly is fine for long-term returns.
**B2 Subscription:** accept the gap (2017+ only; pre-2017 split unavailable).
**B3 GMP (~252, all 2020-25):** chase via extra trackers (agent running), validate, then integrate.
**B4a Financials survivorship:** accept (delisted/old blank) — returns+outcome matter, not their P&L.
**B4b Promoter %:** chase via screener shareholding table (extend extractor; post-IPO promoter % feature).
**B5 Symbol-reuse / ISIN in old NSE prices:** STRICT logic — flag over mis-assign. Use ISIN directly wherever
present (BSE old, NSE 2024+). For NSE pre-2024 (symbol-only): attach a price segment to a stock ONLY when the
symbol↔ISIN mapping is confidently valid for that window — bound to [listing_date → delist_date/today] (via
delisting.csv) AND the symbol's ISIN in an ISIN-bearing era (NSE 2024+/BSE) matches ours AND the series is
continuous. ANY ambiguity (internal gap, symbol→multiple ISINs, delist-then-reuse) → DROP/flag that segment as
uncertain, never guess. A flagged-missing price beats a wrong-company price.

**C1 Quality score:** YES — per-row data_quality + field provenance (also surfaces gaps/bugs).
**C2 Cross-source validation:** YES — compare multi-source fields (issue price, listing price, financials);
agreements→confidence, disagreements→review register; feeds C1.
**C3 Richer L3 features:** DEFERRED to Layer 3.
**C4 Spine completeness:** YES — sanity-check 2006-2019 per-year counts vs known totals.
**C5 Schema unification:** YES — one shared schema for both cohorts (+ cohort + instrument_type), at returns_summary build.

**Index sources (niftyindices POST unreachable here):** Nifty 50 = Yahoo `^NSEI` daily (2007→now);
Nifty Smallcap 250 = investing.com id 1141645 via cloudscraper (2019→now). Pre-2019 smallcap & 2006-07 Nifty50
alpha unavailable → use Nifty 50 as the universal benchmark, smallcap where available.
