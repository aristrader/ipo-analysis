# Recovery of the 75 `unreliable_coverage` (scale-inversion) rows

Date: 2026-06-01. Research-only pass (no edits to `data/master`, `corp_actions`, or pipeline).
Sources: BSE bhavcopy archives (`download/BhavCopy/Equity/`, old `EQ_ISINCODE_DDMMYY.zip` +
new `BhavCopy_BSE_CM_..._F_0000.CSV`), matched by **BSE SC_CODE** (and by ISIN where the
listing-era bhavcopy carried the current ISIN); screener.in / trendlyne / business-standard /
NSE for split, face-value and listing-date confirmation.

## Root-cause finding (important — changes the framing of the task)

The task brief assumed these are "mostly stocks with face-value splits NOT in our corp-actions
feed." **That is not what the data shows.** I cross-checked all 75 symbols against
`data/reference/corp_actions.csv`:

- **59 of 75 already have their split/bonus recorded** in corp_actions (matched by SYMBOL — the
  feed key — even though the listing-era ISIN differs from the current ISIN). Their
  `issue_price_adj` in `ipo_analysis.csv` is ALREADY reduced by the correct factor
  (e.g. Astral ip 115 → ip_adj 5.18 via the recorded 2.0×2.5×2.0 splits + 1.25×1.333×1.333
  bonuses; IEX 1650 → 55.0 via the recorded 10:1 split + 2:1 bonus).
- The remaining 16 with **no** corp action are: 7 REIT/InvIT trusts (par value, never split),
  6 FPOs / very-old mainboard names that genuinely never split (Patel Eng FPO, Andhra Bank FPO,
  DSKulkarni FPO, Visa Steel, Malu Paper, Adhunik, Vodafone Idea FPO), Gallantt Metal (0 splits,
  confirmed by trendlyne/screener), and Wonderla (no split — see below).

**So the real cause of the `unreliable_coverage` flag is almost entirely the PRICE-SERIES
COVERAGE GAP, not a missing split.** Every local `data/prices/<isin>.csv` for these names starts
around 2024-12-20 (a recent snapshot), i.e. years/decades after the actual listing. The pipeline's
computed `listing_open` is therefore the first *adjusted* price in that late-starting series
(tiny, post-split scale), while the Chittorgarh raw quote and `issue_price` are on the original
scale → `implied_factor` blows past 12 (or inverts), tripping branch-2 (`unreliable_coverage`).

**The correct remediation is branch-0 of `listing_remediation.py`: supply the authoritative
listing-day OHLC** (raw, at-listing scale) via `listing_day_recovered.csv`. Then
`listing_gain = recovered_open / issue_price` (raw/raw) is scale-invariant and correct, and the
already-correct `issue_price_adj` keeps the lifetime/multibagger metrics right. **No new
corp_actions rows are needed** — hence `unreliable75_corp_actions.csv` is intentionally empty
(header only). The deliverable that matters is `unreliable75_listing.csv` (36 recovered rows).

## Tally

| Outcome | N |
|---|---|
| **Recovered listing-day OHLC from BSE bhavcopy** (→ `unreliable75_listing.csv`) | **36** |
| Recovered a price but it is NOT the debut → identity/listing_date fix instead (Wonderla) | 1 |
| Could-not-recover: BSE-SME segment (have SC_CODE, not in BSE *Equity* bhavcopy) | 14 |
| Could-not-recover: NSE-Emerge SME (no BSE code at all) | 24 |
| **New splits/bonuses found missing from corp_actions** | **0** (all already recorded) |

Recovery rate for the recoverable universe: every mainboard / BSE-main + REIT/InvIT name
resolved. The 38 unrecovered are SME (BSE-SME or NSE-Emerge), whose listing pops are small and
whose splits are already in the feed — low value, low risk; leave their listing metrics nulled.

## Recovered listing-day quotes (the 36 in `unreliable75_listing.csv`)

`listing_gain_open = open/issue_price − 1`. has_CA = split/bonus already in corp_actions.

| Symbol | Listing date | Issue | Rec. open | Listing gain | has_CA | Note |
|---|---|---|---|---|---|---|
| ASTRAL | 2007-03-20 | 115 | 115.00 | +0.0% | yes | flat debut; multibagger came later via splits/bonuses (already adj) |
| IEX | 2017-10-23 | 1650 | 1500.00 | −9.1% | yes | weak debut (matches public record); 10:1 split+2:1 bonus already adj |
| EASEMYTRIP | 2021-03-19 | 187 | 206.00 | +10.2% | yes | |
| NBCC | 2012-04-12 | 106 | 100.00 | −5.7% | yes | |
| MINDSPACE | 2020-08-07 | 275 | 304.00 | +10.5% | REIT | matched by ISIN in bhavcopy |
| BIRET | 2021-02-16 | 275 | 275.05 | +0.0% | REIT | |
| PGINVIT | 2021-05-14 | 100 | 104.00 | +4.0% | InvIT | |
| NXST | 2023-05-19 | 100 | 102.27 | +2.3% | REIT | |
| BHINVIT | 2024-03-12 | 100 | 101.00 | +1.0% | InvIT | |
| CAPINVIT | 2025-01-17 | 99 | 99.00 | +0.0% | InvIT | |
| ANANTAM | 2025-10-17 | 100 | 105.00 | +5.0% | InvIT | |
| SALASAR | 2017-07-25 | 108 | 259.15 | +140.0% | yes | strong debut; matches our raw listing_open 259.15 |
| SAKUMA | 2006-03-08 | 50 | 65.00 | +30.0% | yes | later 10:1 split already adj |
| VBL | 2016-11-08 | 445 | 430.00 | −3.4% | yes | |
| VKSPL | 2012-07-18 | 55 | 55.80 | +1.5% | yes | |
| PATELENG (FPO) | 2006-05-24 | 440 | 419.75 | −4.6% | no | |
| VISASTEEL | 2006-03-17 | 57 | 58.90 | +3.3% | no | |
| GALLANTT | 2006-04-04 | 10 | 11.05 | +10.5% | no | 0 splits (trendlyne/screener); genuine ~67× lifetime |
| SUNILHITEC | 2006-03-02 | 100 | 125.00 | +25.0% | yes | |
| MOTILALOFS | 2007-09-11 | 825 | 999.00 | +21.1% | yes | |
| BLKASHYAP | 2006-03-17 | 685 | 749.90 | +9.5% | yes | |
| MALUPAPER | 2006-04-05 | 30 | 31.90 | +6.3% | no | no split (par×3 issue) |
| ADHUNIK | 2006-04-05 | 37 | 37.00 | +0.0% | no | |
| INFIBEAM | 2016-04-04 | 432 | 458.00 | +6.0% | yes | |
| NITINFIRE | 2007-06-05 | 190 | 332.50 | +75.0% | yes | strong debut; matches raw 332.5 |
| TIMETECHNO | 2007-06-13 | 315 | 415.55 | +31.9% | yes | |
| YESBANK (FPO) | 2020-07-27 | 12 | 12.30 | +2.5% | yes | |
| SHREEASHTA | 2007-01-10 | 160 | 189.90 | +18.7% | yes | |
| PATANJALI | 2022-04-08 | 650 | 850.00 | +30.8% | yes | strong debut |
| NAUKRI (Info Edge) | 2006-11-21 | 320 | 480.00 | +50.0% | yes | strong debut |
| JYOTHYLAB | 2007-12-19 | 690 | 799.00 | +15.8% | yes | |
| IDEA (Voda FPO) | 2024-04-25 | 11 | 12.00 | +9.1% | no | |
| SOUTHBANK (FPO) | 2006-03-07 | 66 | 65.75 | −0.4% | yes | |
| PCJEWELLER | 2012-12-27 | 135 | 135.50 | +0.4% | yes | |
| DSKULKARNI (FPO) | 2006-05-19 | 275 | 327.60 | +19.1% | no | O=H=L=C, vol 3922 — thin print; medium confidence |
| VGUARD | 2008-03-13→14 | 82 | 73.90 | −9.9% | yes | bhavcopy on 03-14 (03-13 no data) |

## Identity / listing_date corrections (do NOT use a recovered price)

- **Wonderla Holidays (INE066O01014, WONDERLA)** — IDENTITY/DATE FIX, not a price/split fix.
  Recorded `listing_date` = 2014-09-05 is **wrong** (digits transposed). The real debut was
  **2014-05-09**, opening **₹164.75 on BSE, +31.8%** vs the ₹125 issue
  (business-standard / franchiseindia / BSE listing-ceremony record, 9-May-2014). The BSE bhavcopy
  row I pulled for the *recorded* 2014-09-05 (open 308) is a normal mid-life trading day, NOT the
  debut — discarded. **Our existing `listing_open` of 164.75 is already the correct debut price.**
  Recommended fix: set `listing_date = 2014-05-09`; keep listing_open 164.75. Wonderla has **no
  split** (issue_price_adj = 125). EXCLUDED from `unreliable75_listing.csv`.

## Could-not-recover (38) — leave listing metrics nulled

All 38 are SME. Their splits/bonuses are ALREADY in corp_actions (so lifetime metrics are fine);
only the listing-day quote is unavailable from the standard BSE *Equity* bhavcopy.

- **BSE-SME segment, have SC_CODE but absent from Equity bhavcopy (14):** VINNY, WEL, PAVNAIND,
  SIGMA, ATALREAL, MGEL, KSOLVES, BTML, HITECH, SARVESHWAR, AVROIND, MKPL, plus two old mainboard
  Feb-2006 names blocked by BSE rate-limiting mid-run (BANKBARODA 532134, ANDHRABANK 532418 — the
  archive 200-returned an HTML error page after the heavy batch; retriable later, both never split
  so listing_gain is the only missing metric). BSE-SME has a separate bhavcopy file/segment not
  fetched here.
- **NSE-Emerge SME, no BSE code at all (24):** RAJMET, SECL, KRITIKA, IRISDOREME, BSHSL, OSIAHYPER,
  AAKASH, VCL, ISHAN, SIKKO, VERTOZ, LATTEYS, GLOBAL, OMFURN, UNITEDPOLY, GOLDSTAR, GLOBE, FOCUS,
  SHRENIK, DANGEE, GANGAFORGE, MCL, VAISHALI, MITTAL. These never traded on BSE; would need the
  NSE-Emerge historical bhavcopy (not currently a project source).

For all 38: lifetime `current_return_from_issue` against `issue_price_adj` is already correct
(splits recorded). Only the listing-day pop is missing, which for SME is typically small.

## Biggest corrections (listing-pop now recoverable, previously nulled)

These were `unreliable_coverage` (listing metrics nulled) and now get a real, scale-correct
listing gain:

- **Salasar Techno Engineering (+140%)** — issue 108 → open 259.15.
- **Nitin Fire Protection (+75%)** — issue 190 → open 332.50.
- **Info Edge / Naukri (+50%)** — issue 320 → open 480.
- **Time Technoplast (+31.9%)**, **Patanjali Foods (+30.8%)**, **Sakuma (+30%)**,
  **Sunil Hitech (+25%)**, **Motilal Oswal (+21.1%)**, **DSKulkarni FPO (+19.1%)**,
  **Shree Ashtavinayak (+18.7%)**, **Jyothy Labs (+15.8%)**.
- **Wonderla**: not in the listing CSV, but the date fix (2014-05-09) un-nulls its already-correct
  **+31.8%** debut.

Note: these are LISTING-DAY pops becoming visible again — they are not "hidden multibaggers"
flipping sign. The lifetime multibagger returns (e.g. Astral 304×, KSolves 44×, Gallantt ~67×,
V-Guard 51×, Info Edge 61×) were already correctly captured via the recorded splits/bonuses; the
flag had only nulled the *listing-day* metrics.
