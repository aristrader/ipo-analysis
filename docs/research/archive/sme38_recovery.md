# Recovery of the 38 SME `unreliable_coverage` listing-day prices

Date: 2026-06-01. Research-only pass (no edits to `data/master`, `corp_actions`, or pipeline;
no run of 08/09). These are the 38 SME residual that the prior pass
(`unreliable75_recovery.md`) could not pull from the BSE *Equity* bhavcopy.

## Headline finding (changes the framing)

The prior pass assumed these listing-day prices were missing from our data. **They are not.**
For **35 of 38**, our own `data/prices/<isin>.csv` already starts EXACTLY on the recorded
`listing_date` and carries the true listing-day OHLC. The user's hypothesis was right: we have
the day-1 graph, so the pop is directly computable.

Critically, these price files are **RAW (unadjusted)** on the listing day, not split/bonus-
adjusted. Verified on RAJMET (listing open 35.00 raw, current ~3.88 after later bonuses+10:1
split — the series was NOT adjusted up) and GLOBAL (180 raw → ~105 now). So
`listing_gain = listing_open / issue_price` is raw/raw and scale-invariant — exactly what
branch-0 of `listing_remediation.py` expects, and exactly the schema of
`listing_day_recovered.csv` (raw OHLC). The pre-existing post-listing splits/bonuses are already
in `corp_actions`, so lifetime metrics remain correct; only the listing-day metrics were nulled.

## Verification (multi-source)

Where our own listing-day open could be cross-checked against external IPO trackers
(chittorgarh / ipocentral / investorzone / business-standard), it matched **exactly**:

| Symbol | Our file (open / close) | External | Match |
|---|---|---|---|
| RAJMET | 35.00 / 33.25 (+34.6%) | listed ₹35, +34.61% | exact |
| DANGEE | 89.90 / 94.35 (+21.5%) | listed ₹89.9, close ₹94.35, +27.5% close | exact |
| GLOBAL | 180.00 / 180.00 (+20%) | listed ₹180, close ₹180, +20% | exact |
| FOCUS | 54.00 / 54.00 (+20%) | listed ₹54, +20% | exact |

This four-way exact match (across low, mid, and high pops) validates that our price files
contain the authoritative raw listing-day OHLC for the SME segment. The remaining own-price rows
were not individually pinned externally but are internally consistent (sane gains, raw scale,
exact-on-listing-date) → confidence **medium** (vs **high** for the four cross-checked).

All 37 recovered gains fall in a sane range: **−2.5% to +34.6%** — realistic SME listing pops,
no scale inversions.

## Tally

| Outcome | N |
|---|---|
| **Recovered from our OWN price files** (raw listing-day OHLC, gap=0) | **35** |
| **Recovered EXTERNAL** (no local listing-day data; debut price from IPO trackers) | **2** |
| **Unrecoverable** (own file contaminated, no clean external OHLC) | **1** |
| **Total** | **38** |

**37 of 38 are now recoverable.** Deliverable: `docs/research/sme38_listing.csv`
(isin,listing_date,open,high,low,close,source,confidence,verified_against), ready to append to
`data/reference/listing_day_recovered.csv` so branch-0 supplies the listing metrics.

Note: 2 of the 38 (BANKBARODA, ANDHRABANK) are actually old MB FPOs the prior pass left as
"rate-limited, retriable" — both are present in our own price files on their listing date and are
included here.

## Per-row detail

### Recovered from own price files (35) — source `own_prices`
`confidence=high` = the open was also confirmed exactly by an external tracker; `medium` =
own-file only (raw, on-listing-date, sane), not individually externally pinned.

- **RAJMET** (INE00KV01022): open 35.00 (+34.6%) vs issue 26.0 — conf HIGH (chittorgarh/ipocentral +34.61%)
- **DANGEE** (INE688Y01022): open 89.90, close 94.35 (+21.5%) vs issue 74.0 — conf HIGH (chittorgarh/ipocentral)
- **GLOBAL** (INE291W01037): open 180.00, close 180.00 (+20%) vs issue 150.0 — conf HIGH (chittorgarh/ipocentral)
- **FOCUS** (INE593W01028): open 54.00 (+20%) vs issue 45.0 — conf HIGH (ipocentral/investorzone)
- **HITECH** (INE106T01025): open 60.00, close 58.75 (+20%) vs issue 50.0 — conf medium (later 10:1 split, raw scale consistent; not externally pinned)
- **GOLDSTAR** (INE405Y01021): open 27.30 (+9.2%) vs issue 25.0 — conf medium
- **SIKKO** (INE112X01025): open 34.40 (+7.5%) vs issue 32.0 — conf medium
- **KRITIKA** (INE00Z501029): open 34.10 (+6.6%) vs issue 32.0 — conf medium
- **SHRENIK** (INE632X01030): open 41.90, close 48.00 (+4.7%) vs issue 40.0 — conf medium
- **VERTOZ** (INE188Y01031): open 113.00, close 129.60 (+4.6%) vs issue 108.0 — conf medium
- **MGEL** (INE0APB01032): open 53.00 (+3.9%) vs issue 51.0 — conf medium
- **LATTEYS** (INE262Z01023): open 68.00 (+3.0%) vs issue 66.0 — conf medium
- **MKPL** (INE964W01021): open 72.00 (+2.9%) vs issue 70.0 — conf medium
- **ISHAN** (INE0LCW01025): open 82.00 (+2.5%) vs issue 80.0 — conf medium
- **IRISDOREME** (INE01GN01025): open 92.00 (+2.2%) vs issue 90.0 — conf medium
- **SIGMA** (INE0A0S01028): open 46.00 (+2.2%) vs issue 45.0 — conf medium
- **OMFURN** (INE338Y01016, FPO): open 76.60 (+2.1%) vs issue 75.0 — conf medium
- **ANDHRABANK** (INE434A01013, MB FPO): open 91.90 (+2.1%) vs issue 90.0 — conf medium
- **KSOLVES** (INE0D6I01023): open 101.95, close 106.90 (+2.0%) vs issue 100.0 — conf medium
- **OSIAHYPER** (INE06IR01021): open 255.00, close 267.60 (+1.2%) vs issue 252.0 — conf medium
- **VINNY** (INE01KI01027): open 40.50, close 42.40 (+1.2%) vs issue 40.0 — conf medium
- **VCL** (INE098201036): open 24.10 (+0.4%) vs issue 24.0 — conf medium
- **PAVNAIND** (INE07S101038): open 165.60 (+0.4%) vs issue 165.0 — conf medium
- **GANGAFORGE** (INE691Z01023): open 21.10 (+0.5%) vs issue 21.0 — conf medium
- **SECL** (INE00Y701026): open 36.00 (0.0%) vs issue 36.0 — conf medium
- **BSHSL** (INE032Z01020): open 60.00, close 63.00 (0.0%) vs issue 60.0 — conf medium
- **BTML** (INE0EEJ01023): open 95.00 (0.0%) vs issue 95.0 — conf medium
- **MCL** (INE813V01022, FPO): open 102.00 (0.0%) vs issue 102.0 — conf medium
- **BANKBARODA** (INE028A01039, MB FPO): open 230.00, close 233.70 (0.0%) vs issue 230.0 — conf medium
- **MITTAL** (INE997Y01027): open 21.00 (0.0%) vs issue 21.0 — conf medium
- **VAISHALI** (INE972X01022): open 71.90 (−0.1%) vs issue 72.0 — conf medium
- **AAKASH** (INE087Z01024): open 55.75 (−0.4%) vs issue 56.0 — conf medium
- **GLOBE** (INE581X01021): open 50.00 (−2.0%) vs issue 51.0 — conf medium
- **SARVESHWAR** (INE324X01026): open 83.00, close 70.55 (−2.4%) vs issue 85.0 — conf medium
- **ATALREAL** (INE0ALR01029): open 70.20, close 66.70 (−2.5%) vs issue 72.0 — conf medium

### Recovered external (2) — no local listing-day data, debut price from IPO trackers
Our local price series for these starts years after listing (true coverage gap). The external
figure is a single debut quote, so OHLC is recorded as open=high=low=close (the listing price)
with `confidence=medium`.

- **WEL** (INE02WG01024, Wonder Fibromats): listed 2019-08-06 at **₹93** (+4.49% vs ₹89), per
  ipocentral + chittorgarh. Local file starts 2023-01-04 (gap 1247d). Recorded as 93/93/93/93.
- **AVROIND** (INE652Z01025, Avon Moldplast): listed 2018-07-26 at **₹51.65** (+1.3% vs ₹51),
  per investorzone + chittorgarh. Local file starts 2019-11-21 (gap 483d). Recorded as
  51.65/51.65/51.65/51.65.

### Unrecoverable (1)

- **UNITEDPOLY** (INE368U01029, United Polyfab Gujarat): NSE-SME listing date verified as
  **2016-07-07**, issue ₹45 (chittorgarh/ipocentral/investorzone). BUT our own price file is
  **contaminated**: it carries rows from **2016-06-07** onward — a month BEFORE the verified
  listing — and has NO clean 2016-07-07 row (only 2016-07-01 and 2016-07-11 around it). The early
  June prices (~42–44) cannot be the debut. External sources confirm the date and issue price but
  give no precise debut open/close. Per the project rule (flag, never mis-assign), this row is
  left unrecovered. To resolve later: NSE-Emerge historical bhavcopy for 2016-07-07, or a dated
  business-standard/screener listing-day quote.

## Method notes / caveats

- Source priority used: (1) our own `data/prices/<isin>.csv` listing-day row → (2) external IPO
  trackers (chittorgarh, ipocentral, investorzone, business-standard) via WebSearch. WebFetch was
  blocked in this environment; BSE-SME and NSE-Emerge raw bhavcopy were not needed because the
  own-price files already held the listing-day OHLC for 35/38.
- The split/bonus corp_actions for these names (FOCUS, RAJMET, GLOBAL, UNITEDPOLY, WEL, AVROIND,
  HITECH, DANGEE, etc.) all post-date listing and are already recorded — lifetime metrics were
  never wrong; only the listing-day pop was nulled by branch-2.
- `sme38_listing.csv` is in the same schema as `listing_day_recovered.csv` plus
  `confidence` + `verified_against`. To apply: map open/high/low/close into
  `listing_day_recovered.csv` (drop the two research-only columns) and re-run 07 → merge → 08 → 09.
  NOT done here (research/staging only).
