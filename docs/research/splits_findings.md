# Corp-Action / Split Data — Deep-Dive Prep Findings

> Status: RESEARCH (read-only prep for a later "corp-action deep-dive" build task). NOT a fix, NOT final.
> Every count/example below was reproduced directly against the live repo files on 2026-06-17 and is cited.
> Where a number could not be independently verified it is marked **unverified**.

## Executive summary (5 lines)
1. The corp-action master `data/reference/corp_actions_merged.csv` holds **1,897 records** from 5 sources; **354 are symbol-only yfinance rows with NO ISIN** and **163 are nse:sme rows with a malformed numeric (non-ISIN) code** — together **517 rows (27%) cannot be ISIN-joined**.
2. Fake multibaggers are real and reproduce: ROLEXRINGS gets a 10:1 split counted **3×** (→ ~1000×), NPST/CANTABIL counted **2×** — the bug is that `07_returns_summary.py` dedups corp-actions by exact `(ex_date, ratio)` and the SAME event arrives from NSE + yfinance on **near-but-unequal ex-dates**, so dedup never collapses them.
3. The merge code is structurally lossy: `03l` hardcodes `action_type='split'` and `isin=''` for all 354 yfinance rows, and `03k` only matches NSE↔yfinance within a **10-day window** so the same event reported >10 days apart survives as a duplicate; reverse-splits (`ratio<1`, 45 rows) flow through as divisors-applied-as-multipliers (D-2).
4. A **price-gap arbiter is highly feasible and already partly built**: I confirmed it resolves the disputed cases by hand (PATANJALI gap 3.009≈3.0, ROLEXRINGS 19.96, NPST/CANTABIL show the REAL event at the NSE date and NO gap at the spurious yfinance date). An existing arbiter run lives in `data/master/review/corp_action_corroboration_review.csv` (259 rows; 155 have an observed gap, 104 are arbiter-blind).
5. The arbiter is structurally blind for the 354 ISIN-less yfinance rows (no price file to consult); the reused-symbol hazard is concrete (PATANJALI/Ruchi-Soya, ENGINERSIN, TATASTEEL match yfinance actions that PREDATE the substrate IPO listing). Decision D12 (yfinance = corroboration-only) is the safe default.

---

## 1. Inventory

Source file: `data/reference/corp_actions_merged.csv` — header `isin,symbol,action_type,raw_subject,ratio_factor,ex_date,source`.

| Dimension | Value | How derived |
|---|---|---|
| Total records | **1,897** | csv row count |
| `nse_corp_actions:equities` | 1,341 | source col |
| `yfinance` | **354** | source col |
| `nse_corp_actions:sme` | 163 | source col |
| `manual_thinktank_audit` | 34 | source col |
| `verification_2026-05-31` | 5 | source col |
| action_type `split` | 1,053 | |
| action_type `bonus` | 813 | |
| action_type `bonus+split` | 31 | (D-1-compound — pre-collapsed factor) |
| **Empty-ISIN rows** | **354** | ALL are `yfinance` (one-to-one) |
| **Malformed (non-empty, non-ISIN) codes** | **163** | ALL are `nse_corp_actions:sme` (e.g. AAATECH `376100`, NPST `409536`, USASEEDS `462637`) |
| `ratio_factor < 1` (reverse-split-as-divisor) | **45** | 37 yfinance, 7 nse:equities, 1 manual_thinktank |
| `ratio_factor` in (1.0, 1.5] | 350 (141 exactly 1.5) | small bonuses an absolute gap-floor would wrongly drop (D-1-ratio) |

**Joinability gap:** 354 (empty ISIN) + 163 (malformed code) = **517 / 1,897 (27%)** rows have NO usable ISIN join key; they match only by SYMBOL — the structural origin of the over-count and reused-symbol hazards.

Yahoo-only staging file `data/reference/corp_actions_yahoo_only.csv` (354 rows; cols `symbol,original_symbol,yahoo_date,yahoo_ratio,is_bse_code,status`):
- **225 distinct symbols**; **285 / 354 are `is_bse_code=True`** (numeric BSE codes) → these can NEVER match an NSE-symbol substrate row.
- **37** rows have `yahoo_ratio < 1` (reverse-splits). Examples: `534563` 0.1, `537954` 0.01, `538812` 0.01, BANSAL 0.01, BURNPUR 0.2.

---

## 2. Failure modes (each with concrete, reproduced examples)

### 2a. Over-counting — one event counted 2–3× → fabricated multibaggers (D-1, CRITICAL)
Root cause is in the join, not the data. `07_returns_summary.py` `actions_for()` (L114–127) builds the union of ISIN-matched + symbol-matched actions and **dedups on the exact tuple `(ex_date, ratio_factor)`**. When NSE and yfinance report the same split on different ex-dates, the tuples differ → both apply.

Reproduced from `corp_actions_merged.csv` (symbol → records) + my price-gap probe on `data/prices/<isin>.csv`:

- **ROLEXRINGS** (substrate ISIN `INE645S01024`) — three 10.0 records: nse `2025-10-17`, yfinance `2025-10-03`, yfinance `2025-09-19`. Three distinct dates → applied 3× ≈ ×1000. The REAL price gap across all three dates is the **same 19.96×** (`before=2516.95 → after=126.1`), i.e. one event, not three. (Note: the overlay keys ROLEXRINGS as `INE645S01016` which has **no price file** — the ISIN-vs-symbol key mismatch flagged in the register.)
- **NPST** (`INE0FFK01017`) — nse `bonus 3.0 @2024-02-02` + yfinance `split 3.0 @2024-01-22`. Price gap at the **NSE date = 2.857 ≈ 3.0** (real event); at the **yfinance date = 0.969 (NO gap)** → the yfinance leg is a phantom duplicate that double-applies to ×9.
- **CANTABIL** (`INE068L01024`) — nse `split 5.0 @2023-11-02` (gap **5.195**) + yfinance `split 5.0 @2023-10-20` (gap **0.986, none**). Same pattern.
- Register also lists GICL +948%, GNA +639%, PAVNAIND +297% in the same family (unverified by my own probe but consistent).

### 2b. Reverse-split-as-divisor (D-2, CRITICAL)
NSE's parser only emits factors ≥1; **all sub-1 factors come from yfinance** and are applied as if they were ordinary split divisors (0.01 → ×100 inflation). 45 merged rows have `ratio_factor<1`. Compound case: **PATANJALI `INE619A01035`** carries yfinance `split 0.01 @2019-11-14` AND `split 5.0 @2007-10-29` AND nse `bonus 3.0 @2025-09-11` — a D-2 reverse-split stacked on D-1 over-count. (`03k` L142 only skips ratios in [0.99, 1.01], so 0.01 passes through.)

### 2c. Float-precision ratio mismatch (D-1-prec, MED)
`03k` L162-164 compares ratios with a 5% relative tolerance, but the downstream `07` dedup uses **exact tuple equality**. **USASEEDS** has nse `bonus 1.428571 @2025-10-10` vs yfinance `split 1.4285714285714286 @2025-09-26` — different floats AND different dates → never collapses.

### 2d. Near-but-unequal ex-dates (the window problem)
`03k` matches NSE↔yfinance only when `date_diff ≤ 10` days (L155). The legitimate NSE-vs-yfinance ex-date reporting offset I measured on the 16 same-ratio matched pairs is **11–28 days** (median 20) — i.e. the real reporting jitter EXCEEDS the 10-day window, so genuine same-events fall out of the match and survive into `yahoo_only`, then get appended as duplicates by `03l`.

### 2e. Naive cluster detector over-catches (D-1-fp, MED)
A simple "same rounded ratio on ≥2 distinct dates >10 days apart" predicate flags **152 symbols** — but most are legitimate repeated actions years apart (MOTHERSON 1.5 spanning 6,532 days = several genuine bonuses; INFY 2.0; BPCL 2.0; ANGELONE's two 10.0 legs share an ex-date and are already collapsed). Any cluster rule must be gated (distinct ex-dates AND survives dedup AND arbiter-confirmed) or it will null real events.

### 2f. ISIN-vs-symbol key mismatch (D-1-sme-isin / overlay mis-key)
The overlay corrections (`manual_thinktank_audit`, 34 rows) key ROLEXRINGS as `INE645S01016` while the substrate carries `INE645S01024` (a face-value split changes the ISIN) → the correction never lands. The 163 nse:sme rows store a numeric code (NPST `409536`, USASEEDS `462637`) in the ISIN column → ISIN-keyed dedup/overlay mis-keys them.

### 2g. bonus+split compound (D-1-compound, currently OK but fragile)
31 rows carry a single pre-collapsed factor (e.g. ASHOKA 3.0, BAJFINANCE 10.0) — correct today (0 live double-counts) but a future yfinance re-report of the separate legs would survive `(ex_date,ratio)` dedup and double-apply.

### 2h. action_type corruption (D-1-action, MED)
`03l` L48 hardcodes `action_type='split'` for ALL 354 yfinance rows ("Yahoo calls everything a split") and L46 hardcodes `isin=''`. A real yfinance bonus/dividend is therefore stamped "split", and the original action type is unrecoverable from the merged file.

---

## 3. The ISIN-less yfinance case (Decision D12 = corroboration-only)

For the 354 symbol-only yfinance rows (`corp_actions_yahoo_only.csv`):
- **225 distinct symbols**; **285 are numeric BSE codes** (`is_bse_code=True`) → cannot match the NSE-symbol-keyed substrate at all; only **~69 alpha symbols match a substrate `nse_symbol`** (my count of yahoo_only rows whose symbol/original_symbol hits a substrate symbol = **69**; the register's "52 matching substrate symbols" is a different denominator — **unverified which is canonical**; both agree the matchable subset is small).
- **Arbiter-blind by construction:** with no ISIN, there is no `data/prices/<isin>.csv` to consult, so a price-gap arbiter cannot independently confirm a symbol-only record unless it is first mapped to a substrate ISIN. 2,383 price files exist (`data/prices/`).
- **Reused-symbol hazard (concrete, reproduced):** NSE recycles tickers. A yfinance action whose `yahoo_date` PREDATES the matching substrate IPO's `listing_date` almost certainly belongs to a different, older company that once held the ticker:
  - **PATANJALI** — substrate Patanjali Foods listed `2022-04-08`, but yfinance actions dated `2007-10-29` (5.0) and `2019-11-14` (0.01) belong to the predecessor **Ruchi Soya** that held the ticker → mis-applied (this is the same PATANJALI compound D-2 case in §2b).
  - **ENGINERSIN** — substrate listing `2010-08-12`, yfinance actions `1999-11-22` (3.0) and `2010-05-06` (2.0) predate it.
  - **TATASTEEL** — substrate listing `2011-02-02`, yfinance action `2004-08-11` (1.5) predates it.
  - Total yahoo_only rows whose `yahoo_date < matching substrate listing_date` = **5** (the three symbols above). This is a clean, cheap pre-listing filter the deep-dive should apply.
- **Verdict for the build:** D12 (corroboration-only) is correct — a symbol-only yfinance row should be allowed to CONFIRM an ISIN/NSE event via the price gap but never to CREATE an adjustment. NSE/ISIN-authoritative-only at source would kill most over-counts.

---

## 4. Price-gap arbiter feasibility

**Feasible and partly already built.** An arbiter already ran: `data/master/review/corp_action_corroboration_review.csv` (259 rows; cols `isin,symbol,ex_date,observed_gap,gap_dir,yahoo_count,yahoo_ratio,nse_count,nse_ratio,cumulative_applied_factor,bucket,current_return_from_issue,outcome_class,note`):
- **155 rows carry an observed_gap** (arbiter CAN decide); **104 have an empty observed_gap (arbiter-blind)**.
- `gap_dir`: down 134, edge 101, up 21, no-data 2.
- `bucket`: phantom 101, single-source 78, ratio-conflict 35, reverse-split 27, count-conflict 14, agree-all 3.
- `outcome_class` (where set): multibagger 76, wipeout 27, loser 29, winner 23, flat 10.

Human/web evidence layer: `data/master/review/corp_action_external_evidence.csv` (53 rows):
- `recommended_verdict`: resolve-apply-once 28, resolve-correct-ratio 17, STAYS-FLAGGED 6, resolve-reverse-direction 2.
- `agrees_with_price`: Y 26, partial 21, N 6. `confidence`: high 26, medium 21, low 6.
- `bucket`: reverse-split 21, ratio-conflict 17, count-conflict 14.

**My own hand-probes (close just before vs just after ex-date, on the substrate ISIN price file) — the arbiter works:**

| Symbol | ISIN | ex-date | claimed ratio | observed gap | verdict |
|---|---|---|---|---|---|
| PATANJALI | INE619A01035 | 2025-09-11 | 3.0 (nse bonus) | **3.009** | confirms real event |
| ROLEXRINGS | INE645S01024 | all 3 dates | 10.0 ×3 | **19.96** at each | one real event, not 3 (×1000 is fake) |
| NPST | INE0FFK01017 | 2024-02-02 (nse) | 3.0 | **2.857** | real |
| NPST | INE0FFK01017 | 2024-01-22 (yf) | 3.0 | **0.969** | NO gap → phantom duplicate |
| CANTABIL | INE068L01024 | 2023-11-02 (nse) | 5.0 | **5.195** | real |
| CANTABIL | INE068L01024 | 2023-10-20 (yf) | 5.0 | **0.986** | NO gap → phantom duplicate |

**Where the arbiter CAN decide:** ISIN-matched events with bhavcopy coverage spanning the ex-date — it distinguishes the real event (gap ≈ claimed ratio, direction-normalized) from a phantom duplicate (gap ≈ 1.0), and detects reverse-splits (gap direction flips).

**Where the arbiter CANNOT decide (arbiter-blind — needs a fallback):**
- (i) The 354 ISIN-less yfinance rows (no price file).
- (ii) Coverage-START gaps — bhavcopy starts years after the ex-date (register: ATLANTAA ex-2010, coverage ~2017).
- (iii) Coverage-END gaps — `ex_date > last_trade` (register lists 6 ISIN-matched coverage-END events that are REAL multibaggers: E2E `INE255Z01019` +74.7×, LEMERITE `INE0G1L01017`, FORGE `INE319Y01016`). These must NOT be auto-dropped as phantoms.
- ROLEXRINGS observed gap 19.96 vs claimed 10.0 shows the arbiter can also flag where the gap and the claimed ratio DISAGREE (here, an additional unrecorded factor or a wrong claimed ratio) — needs human/web adjudication, not auto-apply.

---

## 5. Recommendations for the deep-dive

**Handling per failure mode:**
- D-1 over-count: replace the exact `(ex_date, ratio)` dedup in `07` with a **cluster-collapse keyed on (rounded ratio, ex-date within slack)**, then run the price-gap arbiter to keep exactly one leg. Re-enable the `09` cross-source listing-price tripwire for corp-action stocks (currently disabled at L88-89 via `has_action`).
- D-1-prec (float precision): compare ratios with relative tolerance (`abs(a-b)/b < 1e-3`) at BOTH `03k` L162 AND the `07` dedup — not exact equality.
- D-2 reverse-split: direction-normalize the price-gap test (gap<1 ⇒ reverse-split; gap>1 ⇒ split); never apply a yfinance sub-1 factor as a plain divisor without arbiter confirmation.
- D-1-ratio (small bonus): test "observed gap ≈ claimed ratio within tolerance," NOT "gap > absolute floor" (350 rows in (1.0,1.5] would be wrongly dropped by a 1.5× floor).
- D-1-action / D-1-yftrust: preserve the original yfinance action_type; demote ISIN-less yfinance to corroboration-only (D12); apply the **pre-listing filter** (drop/flag any symbol-only action whose date predates the matched IPO listing — caught PATANJALI/ENGINERSIN/TATASTEEL).
- D-1-sme-isin: treat the 163 nse:sme numeric codes as symbol-only; route to identity/matching; never use as an ISIN join key.
- Overlay key mismatch: re-key the 34 manual_thinktank corrections through a symbol→current-ISIN map (face-value splits change the ISIN; ROLEXRINGS `…01016`→`…01024`).

**Suggested fallback order when applying an adjustment:**
1. ISIN-matched NSE event (authoritative) → apply.
2. Price-gap arbiter confirms (gap ≈ ratio, direction-normalized) → apply once; if multiple legs cluster on the same gap, collapse to one.
3. Arbiter disagrees with claimed ratio (e.g. ROLEXRINGS 19.96 vs 10) → STAYS-FLAGGED → override catalog (`corp_action_external_evidence.csv` web verdicts) → else leave unresolved + flag.
4. Arbiter-blind + `ex_date > last_trade` (coverage-end) → **defer to override catalog, do NOT auto-drop** (these are real multibaggers).
5. Symbol-only yfinance with no ISIN map or a pre-listing date → corroboration-only / discard, never create.

**Suggested date-window slack (D13):** based on the measured NSE↔yfinance same-ratio matched-pair ex-date gap (16 pairs: min 11, median 20, most ≤28 days; a handful >90 days that are genuinely DIFFERENT events) — set the **same-event collapse slack to ~30 days** (covers the real reporting jitter, excludes the genuine-repeat outliers), and require ratio-match (rel tol 1e-3) AND, where price coverage exists, a SINGLE observed gap shared across the candidate legs. Do NOT widen the window beyond ~30d without the arbiter, or genuine repeats (e.g. two real same-ratio bonuses ~57–70 days apart, seen on BSE codes 540455/540786) will be wrongly merged.

**Re-use what exists:** the corroboration arbiter (`corp_action_corroboration_review.csv`, 259 rows) and the web-evidence catalog (`corp_action_external_evidence.csv`, 53 rows) are already-built inputs — the deep-dive should consume/extend them, not rebuild from scratch. Also carry the Category-2 protective whitelist (67 ISINs, §5 of the issue register) so the rebuild never manufactures a correction for a verified-genuine crash.

---

## 6. Open questions / data gaps blocking a clean fix

1. **Matchable-yfinance denominator conflict:** my count of yahoo_only symbols matching a substrate `nse_symbol` = **69**; the issue register says **52**. Different match logic (alpha vs BSE-code, original_symbol handling). Need one canonical matcher. (unverified which is right.)
2. **ROLEXRINGS true ratio:** observed gap 19.96 but claimed 10.0 — is there an unrecorded second factor (e.g. face-value change) or is the bhavcopy gap itself distorted? Needs web/RHP adjudication before applying.
3. **Overlay ISIN re-keying** needs a reliable symbol→current-ISIN map for face-value-split renames; no such canonical map verified in-repo.
4. **Coverage-start gaps** (ex-date before bhavcopy coverage, e.g. ATLANTAA) leave the arbiter blind for old (2006–13) events — no free backfill source identified; these rely on the override catalog.
5. **D-cov-gap:** SIKKO, RAJMET, MKPL (over-adjusted, issue_adj<1) and GICL (dup +948%) are NOT in the 53-row evidence file — the override catalog is incomplete.
6. **Indiabulls Power `INE399K01017`** Cat-1 bonus was never written to any overlay (ratio unknown).
7. **Substrate reflects the buggy merge:** `ipo_analysis.csv` was last rebuilt at commit `26cd1fd` (the same commit that introduced the D-1 bug), so any validation must rebuild after the fix; the rebuild is non-idempotent and has dropped hand-fixes before (register §3).

---

### Provenance
All counts/examples reproduced read-only on 2026-06-17 from: `data/reference/corp_actions_merged.csv`, `corp_actions_yahoo_only.csv`, `data/master/ipo_analysis.csv`, `data/prices/<isin>.csv`, `data/master/review/corp_action_corroboration_review.csv` + `corp_action_external_evidence.csv`, `data/master/delisting.csv` (2,296 rows: active 2,039 / delisted 145 / suspended 75 / unknown 37 — a price-pipeline INPUT read by step 07), and pipeline `03k_reconcile_corporate_actions.py`, `03l_merge_corporate_actions.py`, `07_returns_summary.py`, `09_assemble.py`. Cross-referenced against `docs/research/data_issue_register_2026-06-17.md` §4.2 + §5.
</content>
</invoke>
