# Adversarial verification report

Independent re-check of the staged fixes. Goal: try to REFUTE each claim using sources OTHER than those
already cited in `verification_corrections.csv` / `recovered_listing_day.csv`. Default to "could-not-confirm"
when sources are silent or disagree. WebFetch was denied in this environment, so all evidence is from
WebSearch result snippets (titles + extracted text) — values quoted below are what those snippets stated.

Date of check: 2026-05-31. No files in `data/master` or `pipeline` were modified.

---

## TASK A — the 9 corrections in `verification_corrections.csv`

| # | ISIN / symbol | Claim | Verdict | Found value | Independent source(s) used |
|---|---|---|---|---|---|
| 1 | INE679V01027 AVL (Aditya Vision) | split 1:10, FV 10→1, rec ~2024-08-27, factor 10.0 | **CONFIRMED** | split 1:10, FV ₹10→Re.1, record date 27 Aug 2024 | Business Standard "Aditya Vision fixes record date for stock split"; ICICIdirect; BusinessToday (ex-date 27 Aug 2024) |
| 2 | INE0LGX01024 INA (Insolation Energy) | split 1:10, FV 10→1, rec ~2025-01-24, true factor 10.0 | **CONFIRMED** | split 1:10, FV ₹10→Re.1, record date 24 Jan 2025 | Business Standard; ICICIdirect; capitalmarket.com — all state record date 24 Jan 2025. (Caveat: a Goodreturns headline says "February 24th"; the majority/authoritative sources say 24 Jan 2025. Date is firmly January.) |
| 3 | INE732I01021 ANGELONE (Angel One) | split 1:10, FV 10→1, rec ~2026-02-26, factor 10.0 | **CONFIRMED** | split 1:10, FV ₹10→Re.1, record date 26 Feb 2026; price adjusted from prev close ₹2,489.90 to open ₹251 on record date | Business Standard "Angel One share price adjusts as 1:10 stock split kicks in on record date" (126022600351); JM Financial; inshorts. The ~2490→251 open = factor ~9.9, corroborating 10.0. Event did happen. |
| 4 | INE071Y01013 TTFL (Trident Texofab) | BONUS 14:10, ex/rec ~2020-08-12, true factor 2.40, NO split (FV stays 10) | **CONFIRMED** | bonus 14:10, record date 12 Aug 2020 (issue 11 Aug 2020); FV = ₹10; no split | MarketsMojo "bonus history of Trident Texofab" (14:10, rec 12 Aug 2020); Equitymaster/torusdigital confirm FV ₹10 and bonus-only (no split). 14:10 bonus → 1+1.4 = factor 2.40. |
| 5 | INE287C01037 MICEL (MIC Electronics) | split 5:1, FV 10→2, true factor ≥5.0 | **CONFIRMED** | split 1:5, FV ₹10→₹2, ex-date 27 Jun 2008 | DynamicLevels "MIC Electronics-Stock Split" (nominal ₹10→₹2, ex 27 Jun 2008); stockanalysis.com (2 splits in history). FV 10→2 ⇒ factor 5.0. (Note: a later 2021 split also exists in history; the 10→2 split alone justifies factor ≥5.0.) |
| 6 | INE728Z01015 (SoftTech Engineers) | NSE SME listing OPEN = ₹88.0 (Chittorgarh ₹72.5 wrong) | **CONFIRMED** | listed on NSE SME 11 May 2018 at **₹88** (open, +10% over ₹80 issue), closed ₹92.40 | SPTulsian IPO analysis / top10stockbroker review: "Listing Price on NSE SME was INR88 per share (up 10% from IPO price)... Closing Price INR92.40". Independent of Chittorgarh. ₹88 matches the bhavcopy claim; Chittorgarh's 72.5 is refuted. |
| 7 | INE813V01022 MCL (Madhav Copper) | market maker = Pantomath Stock Brokers Pvt. Ltd. | **CONFIRMED** | Pantomath Stock Brokers Pvt. Ltd. | ipoplatform.com market-maker page + ipoplatform Madhav Copper IPO page (independent of chittorgarh detail page) |
| 8 | INE05FR01029 (Ashapuri Gold) | market maker = NNM Securities Pvt. Ltd. | **CONFIRMED** | NNM Securities Pvt. Ltd. (both IPO and FPO) | hdfcsec SME IPO page + ipoplatform — both name NNM Securities as market maker |
| 9 | INE00D001018 REXPIPES (Rex Pipes) | market maker = New Berry Capitals Pvt. Ltd. | **CONFIRMED** | New Berry Capitals Pvt. Ltd. | ipoplatform.com merchant-banker page "New Berry Capitals Private Limited" named as Rex Pipes market maker (independent of chittorgarh/ipoplatform detail) |

**Task A bottom line:** all 9 CONFIRMED. One minor caveat on #2 (Insolation): a Goodreturns headline said "February 24th",
but Business Standard, ICICIdirect and CapitalMarket all give **24 January 2025** — the January date is the authoritative one.

---

## TASK B — the 7 recovered listing-day rows lacking a Chittorgarh cross-check

| ISIN | Company | Claim (list date / open / issue) | Verdict | Independent finding | Source |
|---|---|---|---|---|---|
| INE05FR01029 | Ashapuri Gold Ornament FPO | 2021-03-17 / open 75.0 / issue 81.0 | **CONFIRMED** | listed BSE SME 17 Mar 2021 at ₹75.00 vs issue ₹81.00 (listing loss −7.41%) | chittorgarh FPO review snippet + investorgain — open 75.0, issue 81.0, date all match exactly |
| INE211P01021 | VKJ Infradevelopers | 2013-08-30 / open 23.8 / issue 25.0 | **PARTIAL — date+issue CONFIRMED, open COULD-NOT-CONFIRM** | issue ₹25, listed BSE SME 30 Aug 2013, BSE code 536128 confirmed; listing-day OPEN ₹23.8 not surfaced independently | chittorgarh/ipoplatform/business-standard (date+issue+code); open price not found in free sources |
| INE388G01026 | Tantia Constructions FPO | 2006-04-28 / open 180.0 / **issue_price=5000 suspected error** | **DATE CONFIRMED; issue_price=5000 REFUTED (true ≈ ₹50); open COULD-NOT-CONFIRM** | BSE listing effective 28 Apr 2006 confirmed. Correct FPO issue price = **₹50** (₹10 FV + ₹40 premium), 1,12,50,000 shares, ~₹56.25 Cr. The 5000 value is a data error. Open ₹180 not independently surfaced. | chittorgarh FPO news + 5paisa (issue ₹50, premium ₹40); date confirmed via valueresearch/businesstoday |
| INE474O01010 | India Finsec | 2013-06-11 / open 10.0 / issue 10.0 | **CONFIRMED** | listed BSE SME 11 Jun 2013, issue ₹10, "listed at ₹10.50 against offer ₹10.00" (matches row's open 10.0 / close 10.50) | chittorgarh/ipoplatform/business-standard |
| INE684H01018 | Spice Communications | 2007-07-19 / open 55.75 / issue 46.0 | **CONFIRMED** | "Spice Communications Limited lists at Rs.55.75 in BSE"; close ₹60.65 on 19 Jul 2007; issue ₹46 | equitybulls headline (open 55.75) + Business Standard (close 60.65, 19 Jul 2007) — both match the row exactly |
| INE700H01012 | KEW Industries | 2006-09-25 / open 35.5 / issue 30.0 | **PARTIAL — date+issue CONFIRMED, open COULD-NOT-CONFIRM** | issue ₹30, listed 25 Sep 2006 confirmed; listing-day OPEN ₹35.5 not surfaced. (Note: sources say listed on NSE; row is BSE bhavcopy — both exchanges listed it same day, not a conflict.) | chittorgarh/valueresearch (date+issue); open not found |
| INE224B01024 | Birla Power Solutions FPO | 2006-04-26 / open 37.05 / issue 42.0 | **PARTIAL — date+issue+code CONFIRMED, open COULD-NOT-CONFIRM** | issue ₹42, listed BSE 26 Apr 2006, BSE code 517001 all confirmed; listing-day OPEN ₹37.05 not surfaced independently | chittorgarh FPO page + business-standard |

**Task B bottom line:** 3 fully CONFIRMED (Ashapuri, India Finsec, Spice — open prices independently matched).
3 PARTIAL (VKJ, KEW, Birla — listing dates + issue prices independently confirmed and BSE-code match already verified,
but the exact intraday OPEN price for old 2006/2013 SME listings is not retrievable from free public snippets; these
rest on the BSE bhavcopy, which is the authoritative price source per project convention). 1 important finding:
**Tantia Constructions FPO issue_price = 5000 is a confirmed data error — true issue price ≈ ₹50**; the listing date
(2006-04-28) is correct.

---

## TASK C — pre-2007 Nifty 50 prepend scale/series check

File values read from `data/reference/indices/nifty50.csv`:

| Date | File close | Independent corroboration | Verdict |
|---|---|---|---|
| 2000-01-03 | **1592.2** | Nifty was near its dot-com peak (~1500–1818) in early 2000; 1592 sits squarely in that band | CONFIRMED scale/plausible |
| 2004-05-14 → 2004-05-17 | 1582.4 → **1388.75** | Documented as Nifty's worst-ever single-day fall on 17 May 2004; sources state "Nifty fell ~12%". File move = −12.24% exactly. Big drop present on the right day. | CONFIRMED (magnitude + date match) |
| 2006-05-17 → 2006-05-18 | 3635.1 → **3388.9** | 18 May 2006 Sensex fell 826 pts to 11,391 (start of the 2006 crash). Sensex/Nifty ≈ 3.36 → implied Nifty ≈ 3389, matching 3388.9. | CONFIRMED (cross-index ratio consistent) |

Sources: Wikipedia "Stock market crashes in India"; Business Standard / Angel One (12% Nifty fall on 17 May 2004);
macroscan.org + groww (18 May 2006 Sensex −826 to 11,391); Wikipedia NIFTY 50 (dot-com peak ~1818).

**Task C bottom line:** The prepend is the genuine Nifty 50 series at the correct scale (hundreds→thousands of points,
not normalized or a different index). The two crash days land on the correct dates with the correct magnitude, and the
2006 value reconciles with the contemporaneous Sensex via the ~3.36 ratio. No wrong-scale or wrong-series problem found.

---

## OVERALL BOTTOM LINE

**SAFE TO APPLY (independently confirmed):**
- All 9 Task-A corrections (AVL split, INA split, ANGELONE split, TTFL bonus 14:10 / no split, MICEL split 10→2,
  SoftTech listing open ₹88, and all 3 market makers: Pantomath / NNM Securities / New Berry Capitals).
- Task-B rows: Ashapuri Gold FPO, India Finsec, Spice Communications (open prices independently matched).
- Task-C Nifty 50 pre-2007 prepend (correct series and scale).

**NEEDS A HUMAN EYEBALL (not refuted, but the specific OPEN price wasn't independently confirmable from free sources —
relies on the BSE bhavcopy, which is the project's authoritative price source, so likely fine):**
- VKJ Infradevelopers listing open 23.8 (date/issue/BSE-code confirmed).
- KEW Industries listing open 35.5 (date/issue confirmed).
- Birla Power Solutions FPO listing open 37.05 (date/issue/BSE-code confirmed).

**DATA ERROR FLAGGED (fix recommended):**
- Tantia Constructions FPO (INE388G01026): stored issue_price = 5000 is WRONG; true issue price ≈ ₹50
  (₹10 FV + ₹40 premium). Listing date 2006-04-28 is correct. Recompute any issue-anchored metric.

**MINOR CAVEAT:**
- Insolation Energy (INA) split record date is **24 January 2025** (majority/authoritative sources); ignore the one
  Goodreturns "February 24th" headline. Ratio/FV/factor are correct.

No source actively REFUTED any staged value except Chittorgarh's SoftTech ₹72.5 (correctly overridden to ₹88) and the
Tantia issue_price=5000 (a pre-existing data error the recovery already flagged).
