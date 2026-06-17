# task_14 — Corp-actions / splits / bonuses — issue register + existing-fix re-audit

> **STATUS: NOT FINAL.** Design / think-only artifact for the 2026-06-17 night run. Zero code, zero data
> changes, zero pipeline runs. Every number below was re-derived READ-ONLY against the working-tree files on
> 2026-06-17 (substrate = 2384 rows, `corp_actions_merged.csv` = 1897 rows). This is the **authoritative
> per-area re-audit** for the corp-action family (per charter step-3 division of labor; task_20 only
> gap-checks coverage, it does not re-audit from scratch).

---

## STEP 1 — SCOPE (the single question)

**How should split/bonus corporate actions be sourced, reconciled, joined to the price series, and validated,
so that no IPO gets a fabricated return (over-adjustment) and no genuine event is dropped or mis-applied —
expressed as a CLEAN/EXTENSIBLE/CORRECT design with a declarative cleaning rule per failure mode?**

In-scope: the entire **D-1 family** (count-conflict, ratio-conflict, reverse-split, phantom, single-source,
out-of-window/reused-symbol, compound-same-day) + the **fake-returns** symptom (ROLEXRINGS +15,272%, NPST
+16,127%, etc.). Re-audit the existing fixes: the `corp_actions_merged.csv` manual entries
(`manual_thinktank_audit`=34, `verification_2026-05-31`=5), `manual_overrides.csv`, the 88-audit Category-1
(21 missing splits) and Category-2 (67 verified-genuine crashes), and the entire D-1 design trail.

---

## STEP 2 — GROUND-TRUTH INPUTS (read & verified, by file path)

- `data/reference/corp_actions_merged.csv` — **1897 rows**; cols `isin,symbol,action_type,raw_subject,ratio_factor,ex_date,source`.
  Source dist (verified): `nse_corp_actions:equities` 1341, `yfinance` 354, `nse_corp_actions:sme` 163,
  **`manual_thinktank_audit` 34, `verification_2026-05-31` 5**. action_type: split 1053, bonus 813, bonus+split 31.
  354 rows have **empty ISIN** (all `yfinance`); every row has a symbol.
- `data/reference/manual_overrides.csv` — **3 rows, all `market_maker`** (NOT corp-action; INE00D001018,
  INE05FR01029, INE813V01022). Confirms: NO corp-action correction is carried in `manual_overrides.csv`.
- `data/reference/corp_actions_yahoo_only.csv` — **354 rows**; **DIFFERENT schema** from the merged file:
  `symbol, original_symbol, yahoo_date, yahoo_ratio, is_bse_code, status` (NO `isin`, NO `ex_date`, NO
  `ratio_factor` columns). Any overlay/diff against this file must use these real field names. ROLEXRINGS appears
  **twice** here (`yahoo_date` 2025-09-19 + 2025-10-03; `original_symbol='ROLEXRINGS.NS'`, `status='YAHOO_ONLY'`)
  — keyed by `original_symbol`/`yahoo_date`, NOT by isin/ex_date. *(Review-note R1-LOW: the round-1 review claimed
  these two ROLEXRINGS rows carry an EMPTY symbol — ground-truth re-check shows `symbol='ROLEXRINGS'` is populated;
  the symbol-only-join concern is real but the "empty symbol" detail was wrong, so only the schema/key point is carried.)*
- `data/reference/corp_actions.csv` — **1509 rows** (the pre-reconcile NSE+raw input to the 03k/03l chain).
- `data/reference/corp_actions_matches.csv` — **514 rows** (the Yahoo↔NSE cross-source match table 03k emits).
- `data/reference/corp_actions_discrepancies.csv` — **16 rows** (the reconcile-flagged disagreements).
- `data/reference/corp_actions_reconciled.csv` and `data/reference/corp_action_overrides.csv` — **MISSING**
  (the overrides file the D-1 design proposes was never created).
- **DATA-QUALITY ISSUE (register item) — malformed `isin` for nse:sme rows:** **163 `nse_corp_actions:sme` rows
  (+1 equities) store a NON-ISIN numeric code in the `isin` column** (e.g. NPST `409536`, USASEEDS `462637`,
  AAATECH `376100`) instead of a real ISIN. These rows therefore match the substrate only by SYMBOL, never by
  ISIN, and any ISIN-keyed dedup/overlay will mis-key them. This belongs in the issue register, independent of the
  ratio over-count.
- `data/master/review/corp_action_external_evidence.csv` — **53 rows**, web-verified verdicts per stock; cols
  incl. `bucket, price_gap_summary, web_action_summary, recommended_verdict, confidence`. Bucket dist:
  reverse-split 21, ratio-conflict 17, count-conflict 14, ratio-conflict;reverse-split 1. Verdict dist:
  resolve-apply-once 28, resolve-correct-ratio 17, **STAYS-FLAGGED 6**, resolve-reverse-direction 2. **This is
  the de-facto resolution catalog for D-1** (the 6 STAYS-FLAGGED = CMMIPL/COOLCAPS/SILVERTUC/VAISHALI/INDUSFILA/BANSAL).
- `pipeline/07_returns_summary.py` — `load_corp_actions()` (L91-111), `actions_for()` (L114-127),
  `load_prices()` (L206-235), `adj_factor_after()` (L239-246). Adjustment = divide all pre-`ex_date` OHLC by
  the **product of `ratio_factor`** of all later actions; dedup is **only by `(ex_date, ratio_factor)`**.
- `pipeline/03k_reconcile_corporate_actions.py` — within-Yahoo dedup (same symbol+ratio within **7 days**),
  cross-source reconcile (Yahoo→NSE match within **10 days**, ratio within 5%). Non-matches → `yahoo_only`.
- `pipeline/03l_merge_corporate_actions.py` — final merge = NSE-authoritative **concat** yahoo_only; yahoo_only
  rows get `isin=''`, `action_type='split'` (L43-53, verified). **No cross-source de-duplication at merge time.**
  **ACTION_TYPE CORRUPTION (register item):** 03l hardcodes `action_type='split'` for ALL 354 yahoo_only rows
  ("Yahoo calls everything a split", L48) — so `action_type` is UNRELIABLE for every empty-ISIN row (a real
  yfinance bonus/dividend is stamped "split"). Any future detector that keys on `action_type` (e.g. to treat
  bonuses differently from splits) is poisoned for the 354 empty-ISIN rows. The design must preserve/derive the
  original yfinance action_type so `action_type` stays a trustworthy structural field.
- `pipeline/03k_reconcile_corporate_actions.py` — **EXACT-FLOAT ratio equality (L83):** within-Yahoo dedup uses
  `prev_ratio == row['Split_Ratio']` (exact equality). This is the same float-precision fragility that lets
  USASEEDS escape de-dup (`1.428571` ≠ `1.4285714285714286` as floats — see STEP 3.2). The fix-the-source proposal
  must replace exact equality with a numeric tolerance, not just widen the time window.
- `docs/research/unresolved_88_mismatches_audit.md` — Cat-1 (21 missing splits w/ ratios), Cat-2 (67 verified
  genuine crashes, the protective WHITELIST).
- D-1 design trail: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`,
  `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`,
  `docs/research/d1_join_strategy_2026-06-17.md`, `docs/research/d1_final_correctness_2026-06-17.md`
  (+ d1_plan_review / _rereview / _plan_final_verify / _adversarial / _adversarial2). **Verified: this design
  is PURELY PAPER — halted at Review Round 11 "EDGE-CASE-FOUND → NOT BUILD-READY". NONE of it is in code**
  (07 has no `detect_gap`, no `out_of_window`, no window gate, no override loader — grep-confirmed).

---

## STEP 3 — REPRODUCE every issue + RE-AUDIT every existing fix (on current data)

### 3.1 The fake-returns symptom — REPRODUCED

| symbol | ISIN | issue | **issue_price_adj** | cur_ret | root cause |
|---|---|---|---|---|---|
| ROLEXRINGS | INE645S01024 | 900 | **0.90** | **+15,272%** | one 10:1 split counted **3×** → ×1000 |
| NPST | INE0FFK01017 | 80 | **8.89** | **+16,127%** | one 3:1 event counted **2×** (bonus + yfinance "split") → ×9 (should be ×3) |

**ROLEXRINGS mechanism (fully traced):** the single real 10:1 split appears 3 times in
`corp_actions_merged.csv` — yfinance `2025-09-19` (`isin=''`), yfinance `2025-10-03` (`isin=''`), nse `2025-10-17`
(`isin='INE645S01016'`), **all ratio 10.0**. **ISIN/symbol caveat (verified):** the nse leg carries ISIN
**INE645S01016**, while the substrate row (the `issue_price_adj=0.90` over-adjustment) is keyed
**INE645S01024** — a *different* ISIN (a face-value split changes the ISIN). The two yfinance legs carry EMPTY
ISIN. So all three legs attach to the substrate row via the **SYMBOL union** in `actions_for`, NOT via ISIN — the
over-count is fundamentally a **symbol-join phenomenon across two ISIN versions of the same company plus two
empty-ISIN legs**, not a clean single-key event. (Feed this into task_07's ISIN-versioning / symbol-join collision
handling — do NOT present ROLEXRINGS as a single-ISIN example.) `actions_for()` dedups by `(ex_date, ratio_factor)`
— but the dates differ, so all 3 survive → `load_prices` divides pre-event prices by 10×10×10 = **1000** →
`issue_price_adj = 900/1000 = 0.90` → `138.35 / 0.90 ≈ 153×`. **Why the upstream reconcile missed it:** 03k's
within-Yahoo dedup window is 7 days (09-19→10-03 is 14d, survives); 03k's Yahoo→NSE match window is 10 days
(09-19→10-17 is 28d, 10-03→10-17 is 14d — both miss) → both yfinance rows land in `yahoo_only` and 03l blindly
concats them. Confirmed: `corp_actions_yahoo_only.csv` contains ROLEXRINGS **twice** (09-19, 10-03).

**NPST mechanism:** real bonus 3:1 (nse:sme `2024-02-02`, `isin='409536'` — a NON-ISIN code, so it matches by
SYMBOL only) + yfinance mis-labels the same event as "split" 3.0 (`2024-01-22`, `isin=''`, 11d apart).
`(ex_date,ratio)` differs → both kept → ×9 instead of ×3. Both legs attach by symbol (one has a malformed isin,
the other empty) — another symbol-join artifact, not an ISIN-keyed one.

### 3.2 The full count-conflict / over-count BLAST RADIUS — REPRODUCED

Predicate (stated **exactly as run**): same symbol, **same ratio (rounded to 3 dp)**, two ex_dates ≤90d apart,
**different sources** → likely one event double-counted. Grouping by `(symbol, ratio)`.

> ⚠️ **PRECISION & MEMBERSHIP — corrected (was internally inconsistent in the round-1 draft).** Re-reproduced
> read-only on 2026-06-17:
> - **RAW exact-string ratio comparison** → **11 clusters / 11 stocks**: ANGELONE, CANTABIL, DIGIKORE, GICL,
>   GNA, MOS, NPST, PAVNAIND, ROLEXRINGS, RPEL, VISHWARAJ. (USASEEDS is EXCLUDED — its two legs store the same
>   ratio at different precision: nse `1.428571` vs yfinance `1.4285714285714286`, which are different floats and
>   do not match under exact equality.)
> - **ROUNDED-to-3dp ratio comparison** → **13 clusters / 12 stocks**: the 11 above **plus USASEEDS** (the
>   rounding makes its two legs match). *(Cluster count vs stock count: ROLEXRINGS contributes two near-date
>   diff-source pairs → it can be counted as 2 clusters under a pairwise convention, hence 13 clusters / 12
>   stocks; under a strict one-cluster-per-`(symbol,ratio)` grouping it is 12 clusters / 12 stocks. The 12-STOCK
>   list is the reproducible, convention-independent figure — counts below use 12 stocks.)*
> - The round-1 draft's "12 clusters / 11 stocks incl. USASEEDS, excl. ANGELONE" matched NEITHER run (it
>   silently used rounded ratios to include USASEEDS *and* hand-dropped ANGELONE). Corrected here.

**Caught (rounded predicate, 12 stocks):** ANGELONE (10.0, same-date), CANTABIL (5.0, 13d), DIGIKORE (2.0, 14d),
GICL (2.0, 54d), GNA (2.0, 21d), MOS (2.0, 18d), NPST (3.0, 11d), PAVNAIND (2.0, 19d), ROLEXRINGS (10.0),
RPEL (2.0, 15d), USASEEDS (1.43, 14d), VISHWARAJ (5.0, 43d).

**⚠️ ANGELONE is a TRUE-POSITIVE of the predicate but a NON-bug at the substrate — i.e. a real OVER-CATCH.**
ANGELONE's two 10.0 legs share the SAME ex_date 2026-02-26 (ISIN INE732I01021 from `verification_2026-05-31`
vs INE732I01013 from nse). Because `actions_for()` dedups by `(ex_date, ratio)` and both legs share the ex_date,
they collapse to ONE factor → issue 306 → adj 30.6 = exactly one 10:1 applied (correct). So the cluster
predicate flags ANGELONE, but the substrate is already correct. This is a worked **false-positive** of the naive
cluster detector and directly contradicts the round-1 "0 confirmed over-catch" claim (see STEP 6 + STEP 7
correction). FP rate of the raw cluster predicate is therefore **≥1/12**, not 0; the gating must be "distinct
ex_dates AND survives `actions_for`'s `(ex_date,ratio)` dedup."

**USASEEDS evidence:** any same-ratio cluster/dedup rule MUST normalize ratio precision (numeric tolerance, e.g.
`abs(a−b)/b < 1e-3`) — the raw file stores the same ratio at two precisions, so exact-equality silently MISSES a
real over-adjustment (USASEEDS issue 120 → adj 58.8 ≈ applied 2.04× = 1.4286², should be ≈84). Same fragility
exists upstream in 03k L83 (`prev_ratio == row['Split_Ratio']`).

Verified inflated returns these produce (current substrate): CANTABIL +3,968%, GICL +948%, GNA +639%,
VISHWARAJ +136%, PAVNAIND +297% (3y +1,294%), NPST/ROLEXRINGS as above. (DIGIKORE/MOS/USASEEDS/RPEL are
smaller-ratio so the inflation is milder but still wrong; ANGELONE produces NO inflation — same-date collapse.)

**Third detector predicate (symbol-only-yfinance duplicate, any date distance):** "the same symbol has BOTH an
ISIN-carrying action AND an empty-ISIN (yfinance) action with the same ratio (numeric tolerance)." This catches
the over-count vector that predicates 1+2 partly miss (predicate-2's 90-day window and predicate-1's <Rs1 floor
do not guarantee catching all of them). Reproduced read-only → **13 symbols**: CANTABIL, DIGIKORE, ENGINERSIN,
GICL, GNA, MOS, NPST, OPTOCIRCUI, PAVNAIND, ROLEXRINGS, RPEL, USASEEDS, VISHWARAJ. ENGINERSIN and OPTOCIRCUI are
NOT in predicate-2's list → genuine residual false-negatives of the 90-day cluster test. *(Review-note: a round-1
reviewer cited "15 symbols / 69 substrate-symbol matches"; my read-only reproduction yields 13 symbols and 52
empty-ISIN yfinance rows that match a substrate symbol. The directional point — predicate-2 has residual misses —
holds; the exact figures I carry are MY reproduced counts (13 / 52), not the unverified 15 / 69.)*

**A second detector** — `issue_price_adj < Rs 1` (structurally impossible: Indian face value floor is Rs 1 and
issue price ≥ face value). Result = **exactly 8 rows**, every one a genuine over-adjustment:
HARDWYN 0.357, SBC 0.489, **SIKKO 0.533, RAJMET 0.578**, LAL 0.647, FCL 0.700, **MKPL 0.778**, ROLEXRINGS 0.900.

**But the Rs-1 floor is a COARSE LOWER BOUND, not the full over-adjustment net.** Over-adjustment also corrupts
rows where the over-count is milder yet `issue_price_adj` stays > Rs 1 (NPST at 8.89 is the acknowledged example;
also USASEEDS at 58.8 vs correct ~84). A structurally tighter candidate test uses the **known `face_value`
column** (verified present in the substrate): `issue_price_adj < face_value` (issue price is almost always priced
well above face value, so the adjusted issue should rarely fall below it). Reproduced read-only → **68 rows** in
the band `[1, face_value)`. **CAVEAT (not all are bugs):** a genuinely bonus-heavy stock legitimately has
`adj < face_value` (e.g. Astral `issue_price_adj=5.18` with face_value 10 is a REAL bonus chain, +292× winner —
NOT an over-adjustment). So `< face_value` is a *candidate-set* enricher (catches the band predicate-1 misses),
NOT a clean over-adjustment classifier on its own — it must be confirmed by the price-gap arbiter. State
explicitly: predicate-1 (`<Rs1`) = 8, FP 0; `< face_value` = 68 candidates, requires gap confirmation.

### 3.3 The other D-1 buckets — REPRODUCED via the evidence catalog (53 rows)

- **reverse-split (21):** ratio<1 consolidations whose price gaps UP by 1/rf. KAUSHALYA `INE234I01028`
  (1:100 → `issue_price_adj = 6000 = 60×100`, correctly applied up; cur_ret −85% genuine). 45 rows total have
  ratio<1 in the file (37 yfinance, 7 nse, 1 manual). The verdicts: 18 apply-once, 2 reverse-direction,
  1 STAYS-FLAGGED (INDUSFILA, BANSAL).
- **ratio-conflict (17):** NSE vs Yahoo disagree on the magnitude. ISHAN `INE0LCW01025` = compound 10:1 split +
  2:1 bonus → product 30 (`issue_price_adj = 80/30 = 2.667`, correct vs measured gap 28.56×). Verdicts: 14
  resolve-correct-ratio, 3 STAYS-FLAGGED (COOLCAPS, SILVERTUC, VAISHALI).
- **phantom:** claimed action, price never gapped (e.g. a CANTABIL yfinance leg) → must be dropped.
- **single-source:** a yfinance-only event with no NSE corroboration and no ISIN — the structural origin of the
  354 empty-ISIN rows (03l L47). Some are genuine gap-fills, some are the duplicate legs above.
- **out-of-window / reused-symbol:** a freed NSE symbol reassigned to a later listing → the OLD company's
  action attaches via the symbol join. The join_strategy doc counts **44 symbol-added out-of-window rows
  (37 suspect reverse-splits)**; PATANJALI/WAAREEINDO/SWANDEF/SHEKHAWATI/SEJALLTD are examples.

#### 3.3a — D-2 reverse-split-as-divisor (explicitly re-audited; `alignment_audit_2026-06-16.md` L70, L161-178)

The alignment audit classifies **D-2 as CRITICAL, "FOLDED INTO D-1"**: reverse splits (`ratio_factor < 1`) from
Yahoo applied as DIVISORS multiply pre-event prices instead of dividing (a 0.01 factor multiplies by 100).
Re-verified read-only: **45 merged rows have `ratio_factor < 1`** (matches the audit's count; e.g. PATANJALI
0.01, SELMC 0.001, BURNPUR 0.2; the NSE-native parser only ever emits factors ≥ 1, so all sub-1 factors are
yfinance). **PATANJALI compounding (audit L171, verified):** PATANJALI (`INE619A01035`) carries THREE legs —
`0.01` (yfinance 2019-11-14), `5.0` (yfinance 2007-10-29), and `3.0` (nse 2025-09-11) — i.e. it compounds the
D-2 reverse-split-divisor bug WITH a D-1 over-count. A direction-normalized price-gap test (gap sign decides
split vs reverse-split; gap magnitude decides ratio) must resolve BOTH; treating reverse-splits as merely "one of
several buckets" without the direction-normalization is insufficient.

- **bonus+split compound same-day (31 rows):** 31 rows are `action_type='bonus+split'` carrying a single
  PRE-COLLAPSED `ratio_factor` (e.g. ASHOKA 3.0 = 1:2 bonus + FV-split 10→5; BAJFINANCE 10.0). This collapsed
  representation is **correct today (0 live double-counts** where a bonus+split co-occurs with a separate
  yfinance bonus/split leg within 30d), but the design is FRAGILE: a future yfinance refresh that reports the
  split-leg and the bonus-leg of the SAME event SEPARATELY would survive the `(ex_date,ratio)` dedup and multiply
  on top of the collapsed `bonus+split` row. The clustering/arbiter MUST treat a `bonus+split` row and its
  constituent legs as ONE event so a future split-out re-report cannot double-apply. (See issue register.)

- **empty-ISIN yfinance trust (owner decision — flagged, see STEP 8 / Q8):** **354 yfinance rows carry NO ISIN**
  and match purely by symbol; **52 of them match a substrate IPO symbol** (read-only reproduction). These
  symbol-only rows are the STRUCTURAL ORIGIN of the over-counts (ROLEXRINGS, NPST) and the reused-symbol /
  out-of-window hazard. A cleaner upstream policy choice exists than any detector: **demote empty-ISIN yfinance
  rows to CORROBORATION-ONLY** (they may confirm but never CREATE an adjustment by themselves) vs keep them as
  primary gap-fillers under the price-gap arbiter. An NSE/ISIN-authoritative-only policy would eliminate most
  over-counts at the source. Raised as an explicit owner-question (Q8).

### 3.4 RE-AUDIT of existing fixes — does each hold on current data?

| Fix / catalog | Claimed | Re-audit verdict (2026-06-17) |
|---|---|---|
| **`manual_thinktank_audit` (34 rows)** — the Cat-1 corrections | 21 missing-split stocks fixed | **PRESENCE HOLDS (20/21), but RATIO-INTERPRETATION NOT re-audited → 1 ambiguous entry flagged OPEN.** 20 of 21 Cat-1 ISINs ARE present (e.g. Aishwarya INE778I01024 2:1, Darshan INE671T01028 5:1+11:10, 7NR INE413X01035 1:10-rev+10:1+1:5). **INE399K01017 (Indiabulls Power) is ABSENT entirely** — Cat-1 says "Bonus issue reported" (no ratio) → never encodable, still unfixed. Spot-check: Aishwarya now `issue_price_adj`/return on-scale. Charter's "Cat-1 NOT yet in manual_overrides.csv" is technically true but **misleading** — they were applied via `corp_actions_merged.csv` (a different overlay file), NOT `manual_overrides.csv`. ⚠️ **DO NOT stamp "HOLDS" on mere PRESENCE — the ratios are hand-entered ground truth and the interpretation is the very error class that produced fake returns. Darshan (INE671T01028) `raw_subject='Bonus 11:10'` is encoded as `ratio_factor=2.1` (combined 10.5 = 5.0× split × 2.1, adj 5.714). "Bonus 11:10" is AMBIGUOUS: if it means 11 total shares per 10 held, factor=1.1 → combined 5.5 (adj 10.9), NOT 10.5. The manual entry assumed "11 bonus per 10 held" (factor 2.1). This must be confirmed by the price-gap arbiter (which factor the close actually gapped by), not trusted on presence → flagged OPEN. Any `X:Y` bonus whose wording is interpretation-ambiguous needs the same gap re-confirmation.** |
| **`verification_2026-05-31` (5 rows)** | ANGELONE/AVL/INA/MICEL/TTFL ratios verified | **HOLDS.** All 5 present with sane ratios; these are confirmations, not new risk. |
| **`manual_overrides.csv` (3 rows)** | corp-action corrections | **N/A** — all 3 are `market_maker`, zero corp-action. The overlay for corp actions is `corp_actions_merged.csv`, not this file. |
| **Cat-2 whitelist (67 genuine crashes)** | no unrecorded corp action | **HOLDS as protective input, but TWO examples in the round-1 draft were factually wrong — corrected below against the substrate.** The rebuild must NOT manufacture a split for any Cat-2 ISIN. ⚠️ **Inox INE312H01016 is NOT a crash** (see correction box). |
| **D-1 design (plan+spec+4 reviews)** | full architecture designed | **NOT IMPLEMENTED** (paper only; halted R11 NOT-BUILD-READY). Open findings D1-F1 (HIGH), D1-F2 (MED), D1-M1 (MED), R11-B1 (HIGH) all still live. |
| **`corp_action_external_evidence.csv` (53)** | web-verified verdicts | **HOLDS as the resolution catalog**, BUT coverage GAP found: **SIKKO, RAJMET, MKPL** (all issue_adj<1, over-adjusted) and **GICL** (dup-split, +948%) are **NOT in the 53 rows** → uncovered, unresolved. |

**D-1 design open findings — re-verified against current data (all still TRUE):**
- **D1-F1 (HIGH):** a date-window gate applied to the *whole* union would drop ~26 legit ISIN-matched
  post-listing pre-coverage splits. Confirmed live: ATLANTAA `INE285H01022` `issue_price_adj=30` (=150/5,
  correct, +36% winner) and TARIL `INE763I01026` `adj=20.93` (+1,434% multibagger) would BOTH break if the
  gate touched ISIN-matched actions. The gate must be scoped to the **symbol-added subset only**.
- **R11-B1 (HIGH):** a price-gap detector with an *absolute* 1.5× floor would wrongly drop genuine small
  bonuses. Confirmed live: **350 of 1897** corp-action rows have ratio in (1.0, 1.5] (141 are exactly 1.5,
  40 are 1.2, 32 are 1.1) — a detector must be **ratio-aware**, not magnitude-floored.
- **R11-B2 (MEDIUM — was DROPPED in round 1; carried now):** `docs/research/d1_adversarial2_2026-06-17.md`
  (L131-175, L212) records a SECOND, distinct break alongside B1 — the **coverage-END boundary**: actions whose
  `ex_date > last_trade` (past the last available close) cannot be tested by the price gap (the gap is NOT
  MEASURABLE, distinct from B1's "wrong ratio" and from R10's "gap present but wrong"). **6 ISIN-matched events**
  hit this, and they are REAL MULTIBAGGERS: **E2E `INE255Z01019`** (ex 2026-06-05 vs last close 2026-06-04, rf
  10.0, **+74.7×**), **LEMERITE `INE0G1L01017`** (rf 5.0), **FORGE `INE319Y01016`** (rf 5.0 +1.75, ex-date **3.5
  years** after the prior coverage — the starkest case). If read as "phantom → drop", E2E stays a multibagger;
  if read as "coverage-hole → defer-to-override → no override → flag-unresolved", E2E is NULLED and loses its
  multibagger label. The ratio-aware redesign (folded for B1) does NOT resolve B2 — the design needs an explicit
  **`ex_date > last_trade` branch: coverage-hole → defer to override, NOT auto-phantom-drop**, so it does not null
  genuine multibaggers. (Pin E2E + FORGE as tests.)
- **D1-F2 (MED) / D1-M1 (MED):** confirmed still live in the D-1 trail (carried from `d1_final_correctness` /
  `d1_adversarial`); folded into the Option-A redesign requirements (ratio-aware gap + scoped window). No new
  data contradiction found.

> ### ⚠️ CORRECTION BOX — Inox & Aster mischaracterized in round 1 (verified against the substrate 2026-06-17)
> The round-1 draft (and the charter's framing) listed **Inox INE312H01016** and **Aster Silicates INE900K01012**
> with figures that are NEITHER the correct metric NOR the correct value. Re-checked against
> `data/master/ipo_analysis.csv`:
> - **Inox Leisure INE312H01016 — NOT a crash; it is a +604% MULTIBAGGER.** `current_return_from_issue = +6.04`
>   (issue 120, `issue_price_adj = 72.29`, `data_quality_tier=high`, `listing_metrics_status=inferred_split`). It
>   became INOXLEISUR → PVR-Inox via merger (a real corporate event), consistent with the strong positive return.
>   The "−39.8%" the charter attaches to Inox is the **88-audit Chittorgarh-open-vs-Bhavcopy-open COVERAGE-DIFF %**
>   (`unresolved_88_mismatches_audit.md` L89), NOT a return. Inox IS the single **T-2 envelope offender** and IS a
>   Cat-2 do-not-clamp row — but it is a genuine **EXTREME-UPSIDE / merger path**, not a wipeout. ⚠️ ALSO: there
>   IS an ~1.66× adjustment on it (`issue_price_adj=72.29`, not 120) carried via `inferred_split` listing
>   remediation — verify what that factor is and whether it is correct before citing Inox as a "no corp action"
>   protect example. The protective whitelist concept must distinguish **"genuine extreme path (any direction)"**
>   from **"genuine wipeout"** so the protection rule is correct.
> - **Aster Silicates INE900K01012 = −100% (`current_return_from_issue = -1.0`), NOT "−91.6%".** It is a
>   **Compulsory Delisting** (`data/master/delisting.csv`: status=delisted, reason='Compulsory Delisting',
>   delist_date 2018-05-30) → decision A1 sets terminal = −100%. The "−91.6%" is again the 88-audit coverage-diff %
>   (`unresolved_88_mismatches_audit.md` L37), the wrong metric AND the wrong value. The point that Aster has no
>   *unrecorded* split still holds — BUT note it DOES carry `listing_metrics_status=inferred_split` and
>   `issue_price_adj=9.89`, so "no split at all" is too strong; the substrate fact to cite is the −100%
>   compulsory-delisting terminal, not a coverage-diff %.
>
> Lesson: cite REAL substrate values (`current_return_from_issue`, `issue_price_adj`, delisting terminal), never
> the 88-audit's coverage-diff % as if it were a return.

#### 3.4a — DEPLOYED corp-action remediations the round-1 draft OMITTED (charter step-3 requires re-auditing EVERY existing fix)

The round-1 draft re-audited only paper/manual catalogs. **Two corp-action fixes are actually SHIPPED in the live
pipeline and were NOT re-audited** (`docs/data_review.md` L69-73, `rules/index.md` L122-126,
`pipeline/listing_remediation.py`):

| Deployed fix | Where | Re-audit verdict (2026-06-17) |
|---|---|---|
| **Symbol+ISIN feed-matching remediation** (`116→383` stocks fixed; "IRCTC +59%→+697%, Astral bonus chain applied") | `docs/data_review.md` L69-70 | **HOLDS (spot-checked).** Astral Poly Technik `issue_price_adj=5.18`, `current_return_from_issue=+292.5` — on-scale, the real bonus chain IS applied. (IRCTC not located by name in this read; re-confirm IRCTC ISIN at build.) The `116→383` population should be re-quantified against current data during the campaign. |
| **Inferred-split listing remediation** (Chittorgarh-raw vs screener-adjusted; e.g. Aditya Vision 10:1) | `pipeline/listing_remediation.py` (verified exists, 8226 B) → substrate `listing_metrics_status=inferred_split` | **HOLDS structurally; count re-derived = 57 rows** (`listing_metrics_status` dist verified: ok 1935 / unreliable_coverage 223 / recovered_bhavcopy 153 / inferred_split 57 / '' 16). `rules/index.md` L122-126 ties this to the **still-active MFE/MAE invariant clamp on the ~75 split-remediated "scale-inversion" rows** (flag `mfe_mae_clamped`) — that clamp conservatively understates upside and INTERACTS with this proposal: any corp-action redesign that changes applied factors must re-derive the inferred_split set AND the scale-inversion clamp, or it will silently shift which rows are clamped. (Note Inox & Aster both carry `inferred_split` — see correction box.) |

#### 3.4b — THIRD root cause OMITTED in round 1: the `09_assemble` cross-source check is DISABLED for corp-action stocks

`docs/research/alignment_audit_2026-06-16.md` (L109, L152) ties a THIRD structural contributor to D-1 that the
round-1 draft never named. Verified in code — `pipeline/09_assemble.py:88-89`:

```python
has_action = (isin in action_isins) or (u_sym and u_sym in action_symbols)
if u_open and r_open and not has_action:        # ← the cross-source listing-price check
```

The one cross-source tripwire that could catch over-adjustment (bhavcopy listing_open vs Chittorgarh
listing_open, >20% rel-diff → `listing_price_mismatch`) is **deliberately SKIPPED for any stock with a corp
action** — i.e. precisely the stocks most at risk of over-adjustment have NO cross-source over-adjustment
tripwire. This is a named third root cause (alongside 03k/03l upstream + 07 exact-key dedup). The STEP-8 proposal
must redesign this gate (e.g. compare to the price-gap-validated factor rather than skipping outright) so
corp-action stocks regain a cross-source check.

---

## STEP 4 — OPTIONS (≥3, steelmanned; leaning challenged)

The charter's STARTING LEANING for the whole run is "overlay file + declarative cleaning rules". For
corp-actions specifically, the in-flight D-1 leaning is "price-gap detector + symbol∪ISIN window join +
override file". I name it, then argue a non-leaning alternative on merits.

### Option A (LEANING) — Source-reconcile + price-gap DETECTOR + scoped window join + override catalog
**Steelman:** This is the only option that is *self-validating* — the price series itself is the arbiter
("price disposes"), so it catches over-counts, phantoms, and wrong ratios regardless of which source erred,
and it degrades gracefully (flag+null when the gap is ambiguous). It already has a 4-round-reviewed design and
a 53-row evidence catalog. It directly fixes all 12 count-conflicts + 8 issue_adj<1 cases.
**Cost / why not slam-dunk:** the detector is subtle (R11-B1 small-bonus, compound same-day, suspension gaps,
coverage holes) and was halted as not-build-ready; it needs a ratio-aware gap test before it is safe.

### Option B — De-duplicate at the MERGE step (03k/03l), no price detector
**Steelman:** The root cause of the fake returns is *upstream*: 03k/03l fail to collapse the same event across
sources because the windows (7d/10d) are too tight and the merge does a naive concat. Widen the cross-source
event-clustering window (e.g. cluster same-symbol same-ratio events within ~45 trading days into ONE), prefer
the NSE/ISIN-carrying row, and the over-count vanishes before it ever reaches 07. Simpler, no per-action price
math, fixes the count-conflicts at the source (12 stocks under the rounded predicate; minus ANGELONE which is
already correct via same-date dedup — see §3.2).
**Why rejected as the SOLE fix (tied to north-star CORRECT):** clustering by date+ratio cannot tell a genuine
*repeated* event (two real 2:1 bonuses 6 weeks apart) from a double-count, and it does nothing for
ratio-conflicts, phantoms, or out-of-window symbol reuse. It also can't validate the *manual* entries. It is a
necessary **complement** to A (fix the source AND validate at the join), not a replacement. → fold into A as
the "reconcile" half.

### Option C — Manual override-only (extend the existing `corp_actions_merged.csv` manual tags)
**Steelman:** We already have a 53-row evidence catalog with high-confidence verdicts and 34 manual_thinktank
entries that demonstrably work. Just hand-encode the resolution for every flagged stock; zero detector
complexity, fully auditable.
**Why rejected as the sole fix (north-star EXTENSIBLE):** it does not scale to live data — every new IPO split
would re-introduce the over-count until someone hand-fixes it, re-accreting the exact hand-fix backlog the
charter's overlay design exists to kill. Manual overrides should be the **fallback for the ~6-8 genuinely
ambiguous STAYS-FLAGGED / uncovered cases only**, not the mechanism.

**Convergence:** **A (detector + scoped window join) as the engine, B (source-reconcile de-dup) as the
upstream complement, C (override catalog) as the narrow fallback for ambiguous residue.** This is the D-1
design's own shape — but the re-audit adds: (i) fix R11-B1 (ratio-aware gap) **AND R11-B2 (coverage-END
`ex_date>last_trade` branch → defer, not auto-drop)**, (ii) scope the window to symbol-added only (D1-F1),
(iii) **numeric-tolerance ratio comparison** at both the cluster step and 03k L83 (USASEEDS), (iv) materialize
the missing `corp_action_overrides.csv` from the 53-row evidence catalog, (v) close the SIKKO/RAJMET/MKPL/GICL
coverage gap, (vi) re-enable a cross-source over-adjustment tripwire for corp-action stocks (the
`09_assemble.py:88-89` hole, §3.4b), (vii) require corp-action resolution to be representable in the substrate —
but **defer the actual provenance columns to task_03/task_05** (do NOT prescribe a bespoke status enum here).

---

## STEP 5 — ANALYSIS (step by step)

1. **THREE root causes feed one symptom** (round 1 named only two). (a) Upstream: 03k/03l can't collapse one
   event reported by ≥2 sources on near-but-not-equal dates (made worse by exact-float ratio equality at 03k L83
   and `action_type='split'` hardcoding at 03l L48). (b) Downstream: 07 dedups only on exact `(ex_date, ratio)`,
   so it can't undo (a). (c) **`09_assemble.py:88-89` disables the cross-source listing-price tripwire for any
   stock with a corp action** (§3.4b) — the over-adjusted stocks are exactly the ones with no cross-source check.
   No single layer is sufficient; the design must touch all three — but the *single trustworthy arbiter* is the
   **price gap**, which is source-agnostic.
2. **The price gap is the ground truth that scales — WHERE IT IS OBSERVABLE.** A real 10:1 split gaps the close
   ~10× on ONE trading day; three phantom copies still correspond to ONE gap. So "collapse all same-ratio events
   that map to the same price gap" is correct AND extensible. This is the heart of Option A and *why* B-alone
   fails. ⚠️ **BUT the arbiter is BLIND for a non-trivial slice** and the design must name an explicit fallback
   when it cannot fire: (i) the **354 empty-ISIN yfinance rows** (no testable own gap unless the symbol's series
   exists), (ii) stocks whose **daily bhavcopy coverage starts years after the ex_date** (ATLANTAA: ex 2010 but
   coverage from ~2017 → no observable gap), and (iii) the **R11-B2 coverage-END** case (`ex_date > last_trade`,
   gap not measurable — E2E/FORGE). For all "arbiter-blind" rows the cleaning rule must define an explicit
   FALLBACK ORDERING (source-priority → override catalog → flag-unresolved), not imply the gap test always
   adjudicates. "Arbiter unavailable" is a first-class branch of the declarative rule. (The no-observable-gap
   population must be quantified during the campaign.)
3. **But the gap test must be ratio-aware (R11-B1).** A 5:4 bonus gaps ~1.25×; an absolute 1.5× floor calls it
   a phantom and drops a real event. 350/1897 rows live in (1.0,1.5]. The test must be "does the observed gap
   ≈ the claimed ratio (within tolerance), direction-normalized" — not "is the gap > X".
4. **The join must distinguish ISIN-matched (own event, always apply) from symbol-added (gate by trading-date
   window).** D1-F1 proves over-reach corrupts 26 legit old stocks (ATLANTAA flips winner→loser). The window
   is a *symbol-reuse guard*, not a universal filter.
5. **Genuine REAL paths are sacred (Cat-2) — and "real" ≠ "crash".** The detector must never invent a split to
   "explain" a real outcome. The Cat-2 whitelist (67 ISINs) is a hard do-not-touch input. ⚠️ Inox INE312H01016 is
   real data but is an **EXTREME-UPSIDE / merger path (+604%)**, NOT a wipeout (see correction box §3.4); Aster
   INE900K01012 is a real **−100% compulsory delisting**. The whitelist concept must distinguish "genuine extreme
   path (any direction)" from "genuine wipeout" so the protection logic is correct — protect both, but don't
   conflate them.
6. **Provenance must become structural — but this task does NOT own the column set (deferred to task_03/task_05).**
   The substrate carries ZERO corp-action columns today, which is wrong; the resolution of every action MUST be
   representable in the substrate. ⚠️ **Round 1 unilaterally prescribed two new columns (`corp_action_factor` +
   a 5-state `corp_action_status` enum {ok, over_count_collapsed, out_of_window_dropped, phantom_dropped,
   unresolved_flagged}). That is a Group-A design decision that task_14 (a Group-B re-audit) must NOT pre-empt** —
   a 5-state status enum that downstream code branches on is exactly the flag-sprawl risk task_05 (structural
   columns / minimal flags) is chartered to adjudicate, and it duplicates the generic provenance mechanism task_03
   owns (the `_src` / 3-state present-absent scheme — single source of truth). **So this task contributes the
   REQUIREMENT, not the columns:** "corp-action resolution (the applied cumulative factor + a resolution state
   incl. unresolved→null-returns) must be representable in whatever generic provenance/structural scheme
   task_03/task_05 lands on; if a corp-action-specific status is needed, justify why it cannot ride the generic
   `_src`/3-state encoding rather than spawning a parallel mechanism." Final column set = task_03 + task_05.
7. **Idempotency / overlay (links to task_08/09).** The resolution catalog (53 evidence rows + the 6
   STAYS-FLAGGED + the manual_thinktank 34) is exactly the kind of ordered, provenance-carrying overlay
   task_08 must absorb; task_09's reconciliation diff is what would have *caught* the 4 uncovered cases.

---

## STEP 6 — TEST / VALIDATE (numbers + worked examples, read-only)

**Detector predicate 1 (over-adjustment):** `issue_price_adj < 1.0`.
- **Caught: 8** (HARDWYN, SBC, SIKKO, RAJMET, LAL, FCL, MKPL, ROLEXRINGS). All 8 manually confirmed genuine
  over-adjustments (issue price < Rs 1 is structurally impossible).
- **False positives: 0** — no legitimate IPO has issue price below Rs 1.
- **Missed (false negatives): yes** — NPST (`issue_adj=8.89`, real ×3 over-counted to ×9) passes this test
  because 80/9 ≈ 8.89 > 1. So predicate-1 alone is necessary-not-sufficient.

**Detector predicate 2 (count-conflict cluster):** same symbol + **same ratio (numeric tolerance / rounded 3dp)**
+ two ex_dates ≤90d apart + diff source. *(Comparison MUST be tolerance-based, not exact-string — exact equality
silently misses USASEEDS; see STEP 3.2.)*
- **Caught: 12 STOCKS** (rounded predicate): ANGELONE, CANTABIL, DIGIKORE, GICL, GNA, MOS, NPST, PAVNAIND,
  ROLEXRINGS, RPEL, USASEEDS, VISHWARAJ. (Exact-string predicate → 11 stocks, dropping USASEEDS.) Catches NPST
  (predicate-1 missed) → the two predicates are complementary.
- **Over-caught (false positives) — ≥1/12, NOT 0 (round-1 correction).** ⚠️ **ANGELONE is a worked false
  positive**: its two 10.0 legs share the SAME ex_date 2026-02-26 (INE732I01021 vs INE732I01013), so
  `actions_for`'s `(ex_date,ratio)` dedup already collapses them → adj 30.6 = one 10:1 (correct). The cluster
  predicate flags it, but the substrate is fine → a TRUE over-catch. So the FP rate of the raw predicate is
  **≥1/12 ≈ 8%**, not 0 (round 1 wrongly claimed "0 confirmed over-catch"). The gating fix: only treat a
  same-ratio cluster as a bug when the legs have **DISTINCT ex_dates AND survive the `(ex_date,ratio)` dedup**.
  A genuinely *repeated* same-ratio event (two real bonuses within 90d) would also trip it — disambiguated by the
  price-gap arbiter (one gap vs two). Live ambiguous-repeats among the rest: 0 confirmed.
- **Missed (false negatives):** the 90-day window + the <Rs1 floor do NOT catch every symbol-only-yfinance
  duplicate. **Predicate 3 (symbol-only-yf dup, any date distance)** catches **13 symbols** (STEP 3.2), of which
  **ENGINERSIN and OPTOCIRCUI are NOT caught by predicate-2** → genuine residual false-negatives. Treat the
  symbol-only yfinance row that duplicates an ISIN-row as the PRIMARY over-count vector, independent of the 90d
  window.

**Coverage cross-check (re-audit of the evidence catalog):** of the 8 issue_adj<1 + 12 dup-cluster stocks,
**SIKKO, RAJMET, MKPL, GICL are NOT in the 53-row `corp_action_external_evidence.csv`** → 4 uncovered open
items the campaign must resolve.

**Worked examples by ISIN:**
- **ROLEXRINGS — spans TWO ISINs** (substrate row INE645S01024; corp-action nse leg INE645S01016; two yfinance
  legs empty-ISIN) → the over-count is a **SYMBOL-join artifact across ISIN versions**, not a single-key event
  (do NOT present one ISIN as the clean key). Raw actions {10.0@2025-09-19(yf), 10.0@2025-10-03(yf),
  10.0@2025-10-17(nse)}; `actions_for` keeps all 3 (distinct ex_dates) → ×1000 → `issue_price_adj=0.90` →
  +15,272%. Evidence catalog: bucket=count-conflict, gap 2025-10-17 ≈19.96×, verdict=resolve-apply-once
  (factor 10). FIX = collapse to one. Feed the ISIN-duality into task_07.
- **INE0FFK01017 NPST** — bonus 3.0@2024-02-02(nse:sme, isin=`409536` non-ISIN code → symbol-join) + "split" 3.0
  @2024-01-22(yf, empty isin, mislabeled — see 03l action_type hardcode) → ×9 → `issue_price_adj=8.89` (should be
  80/3=26.67) → +16,127%. Verdict=resolve-apply-once (factor 3).
- **INE732I01021 ANGELONE (worked FALSE POSITIVE of predicate-2)** — two 10.0 legs, SAME ex_date 2026-02-26
  (INE732I01021 verification_2026-05-31 vs INE732I01013 nse). `actions_for` `(ex_date,ratio)` dedup collapses
  them → adj 30.6 = exactly one 10:1 (issue 306). Substrate is CORRECT; the cluster predicate over-catches it.
  Canonical over-catch example → FP rate ≥1/12.
- **INE0CBM01019 USASEEDS (worked FLOAT-PRECISION miss)** — two legs store the SAME 10:7 ratio at different
  precision: nse `1.428571` (isin=`462637`, a non-ISIN code) vs yfinance `1.4285714285714286` (empty isin), ex
  2025-10-10 / 2025-09-26. Exact-string comparison MISSES the cluster; rounded/tolerance comparison catches it.
  Real over-adjustment: issue 120 → adj 58.8 ≈ applied 2.04× (=1.4286²), should be ≈84. Proves the comparison
  must be numeric-tolerance (and 03k L83's exact-float equality must be fixed too).
- **INE285H01022 ATLANTAA** (counter-example for D1-F1) — ISIN-matched 5:1 split ex 2010-11-08, listed
  2006-09-25, daily bhavcopy coverage starts ~2017 → `ex_date < first_trade`. A naive window gate would DROP
  it, un-dividing issue → winner (+36%) flips to loser. Proves the gate must exclude ISIN-matched actions.
- **INE234I01028 KAUSHALYA** (reverse-split correctness) — 1:100 consolidation, `issue_price_adj=6000`
  (=60×100), cur_ret −85% genuine. Confirms reverse direction handled correctly today.

**Testability note:** the *architectural* parts (provenance columns, overlay materialization) are design-time;
validated by schema cross-check (0 corp-action columns exist today) and walkthrough against the 4 worked rows.

---

## STEP 7 — MULTI-LENS REVIEW (loop-until-quiet; every round logged)

> Author = task_14 agent. Reviews are self-administered fresh-lens passes (the night run is single-agent;
> full independent agents run in STAGE 5 of the macro sequence). Each round states findings or "NONE + what
> was checked". Stop rule: ≥2 consecutive rounds with zero new ≥LOW findings (hard floor 2).

**Round 1 — correctness + completeness.**
- F1 (MED, fixed): initial draft asserted "Cat-1 not applied" per the charter; ground-truth check showed 20/21
  ARE applied via `corp_actions_merged.csv`. Corrected in step 3.4 with the INE399K01017 exception.
- F2 (LOW, fixed): missed that NPST passes the issue_adj<1 test; added predicate-2 complementarity note.
- F3 (MED, fixed): had not checked whether the evidence catalog covers ALL over-adj cases; found SIKKO/RAJMET/
  MKPL/GICL gap. Added.

**Round 2 — context-pickup + north-star + adversarial.**
- F4 (MED, fixed): had not confirmed the D-1 design is unimplemented; grep-verified 07 has none of
  detect_gap/out_of_window/window-gate; added explicit "paper only, halted R11" finding.
- F5 (adversarial, LOW, fixed): "could the window gate be safe if applied to all?" → disproved live with
  ATLANTAA (winner→loser) and TARIL (multibagger). Documented as D1-F1 confirmation.
- F6 (adversarial, LOW, noted): "does predicate-2 over-catch real repeated events?" → none found among the 12
  live, but flagged as a residual risk to be settled by the price-gap arbiter (open question Q4).

**Round 3 — fresh adversarial sweep.** ⚠️ *SUPERSEDED in part by independent Round 5 — its "ZERO findings" /
"0 over-catch" conclusions were WRONG (ANGELONE FP, USASEEDS precision miss, etc.); retained for audit trail.*
- Checked: are there over-adjustments NOT caught by EITHER predicate? Predicate-2 is ratio-agnostic and catches
  the dup-clusters incl. the mild ones; residual risk is a single-source phantom only the price-gap detector
  catches. *(Round 5: predicate-2 also MISSES symbol-only-yf dups out-of-window — ENGINERSIN/OPTOCIRCUI — so this
  was not fully correct; added predicate 3.)*
- Checked: does any Cat-2 whitelist stock appear in the dup-clusters? No overlap (recent SME splits vs old
  crashes).
- **Round-3 claimed "ZERO new ≥LOW findings" — DISPROVED by Round 5.**

**Round 4 — fresh correctness re-read.** ⚠️ *SUPERSEDED — claimed every count "stated consistently"; Round 5
showed the 12/11 cluster count was internally inconsistent and ANGELONE/USASEEDS membership was wrong.*
- Re-verified counts (1897, 53, 8, 34, 5, 3, 350, 26, 45). Re-verified worked ISINs. *(The cluster count was NOT
  in fact consistent — see Round 5.)*

**Round 5 — INDEPENDENT fresh-agent review (2026-06-17, a DIFFERENT agent than the author).** The charter STOP
RULE requires the reviewer be a different agent and ≥2 consecutive independent zero-finding rounds; round 1-4 were
self-administered, so the stop rule was NOT actually met. This independent pass found **multiple ≥LOW findings** —
the loop is NOT dry. Applied this round:
- **(HIGH) Cluster count was internally inconsistent** — "12/11 incl. USASEEDS, excl. ANGELONE" matched neither
  the raw (11 stocks, incl. ANGELONE) nor the rounded (12 stocks, incl. both) reproduction. Corrected §3.2 + §6.
- **(HIGH) ANGELONE is a worked FALSE POSITIVE** of predicate-2 (same-date dedup collapses it) → FP rate ≥1/12,
  contradicting the round-3/4 "0 over-catch" claim. Corrected §3.2 + §6 + §7.
- **(HIGH) USASEEDS float-precision miss** — exact-string ratio comparison drops it; comparison must be numeric
  tolerance; 03k L83 has the same exact-float bug. Added §3.2 + §6 + 03l/03k notes in §2.
- **(HIGH) Inox & Aster mischaracterized** — Inox is +604% multibagger (not a crash), Aster is −100% compulsory
  delisting (not "−91.6%"); both round-1 figures were the 88-audit coverage-diff %, the wrong metric. Correction
  box added §3.4; §5 point 5 reframed.
- **(HIGH) Three dropped context items carried in:** R11-B2 coverage-END boundary (E2E/FORGE multibaggers);
  the `09_assemble.py:88-89` cross-source-check-disabled-on-has_action third root cause; the DEPLOYED symbol+ISIN
  (116→383, IRCTC/Astral) + inferred_split/listing_remediation fixes (none re-audited in round 1). Added §3.4a/b.
- **(MED) D-2 reverse-split-divisor + PATANJALI 0.01+5.0+3.0 compounding** explicitly re-audited (45 rows). §3.3a.
- **(MED) Column-proposal over-reach** — round-1 prescribed a 2-column/5-state status enum; demoted to a
  REQUIREMENT for task_03/task_05 (avoid parallel provenance + flag sprawl). §5 point 6 + §8 item 5.
- **(MED) Darshan ratio-interpretation ambiguity** (Bonus 11:10 → 1.1 vs 2.1) — manual entries re-flagged OPEN
  pending price-gap confirmation; "HOLDS on presence" rejected. §3.4.
- **(LOW) Predicate-1 generalized** to a `< face_value` candidate band (68 rows, gap-confirmation required);
  3rd predicate (symbol-only-yf dup, 13 symbols) added for FN coverage; arbiter-blind population named (§5 pt 2);
  yahoo_only schema, malformed-isin (163 nse:sme), action_type hardcode, companion files (corp_actions.csv 1509 /
  matches 514 / discrepancies 16) all added to §2. New owner-questions Q8-Q10 added.

**STOP RULE — PROVISIONAL (NOT satisfied).** Round 5 (this independent pass) produced numerous ≥LOW findings, so
the loop is demonstrably NOT dry. The round-3/4 "stop" was author-self-administered and the charter disallows
closure on the author's own passes. **The STEP-7 stop-rule checkbox is marked PROVISIONAL** — closure requires
≥2 consecutive INDEPENDENT fresh-agent rounds with zero new ≥LOW findings (one of which this round is, and it was
not clean). Deferred to STAGE 5.

---

## STEP 8 — NON-FINAL PROPOSAL + OPEN OWNER-QUESTIONS

> **NOT FINAL — proposal for owner approval. No code. Aligns with the D-1 design trail + this re-audit.**

**Proposed corp-action architecture (declarative, fits the charter overlay + column-registry):**

1. **Source-reconcile (upstream, 03k/03l redesign).** Cluster same-symbol same-ratio events that map to ONE
   price gap into ONE event (prefer ISIN-carrying/NSE row); widen the cross-source clustering to trading-day
   windows; stop the naive concat. Eliminates the 12 count-conflicts at the source.
2. **Price-gap DETECTOR at the 07 join (the arbiter), with an explicit ARBITER-BLIND fallback.** For each
   candidate action, compare the observed close gap to the claimed ratio, **ratio-aware + direction-normalized**
   (fixes R11-B1; handles reverse-splits and small bonuses), over a **trading-day-indexed** window (handles
   suspensions). Outcomes: apply-once / collapse-duplicate / drop-phantom / flag-unresolved. **Comparison MUST be
   numeric-tolerance, not exact-float** (fixes USASEEDS; also fix 03k L83). **`ex_date > last_trade` BRANCH
   (R11-B2):** when the gap is NOT measurable (ex past coverage END, or coverage starts after ex_date, or
   empty-ISIN symbol-only with no own series) → **defer to override, NOT auto-phantom-drop** (else E2E/FORGE/
   LEMERITE multibaggers get nulled). Define the explicit fallback ordering for arbiter-blind rows:
   source-priority → override catalog → flag-unresolved.
3. **Scoped window join (fixes D1-F1).** ISIN-matched actions ALWAYS apply; **only symbol-added** actions are
   gated by `[first_trade,last_trade]` to catch symbol reuse. Out-of-window symbol matches dropped + flagged.
   (Note: `bonus+split` compound rows and their constituent legs must be treated as ONE event so a future
   split-out yfinance re-report cannot double-apply on top of the collapsed factor — §3.3.)
4. **Override catalog (materialize the missing file).** Build `corp_action_overrides.csv` from the 53-row
   `corp_action_external_evidence.csv` (high/medium verdicts) + the 6 STAYS-FLAGGED + manual_thinktank 34,
   carried in the task_08 ordered/idempotent overlay. Honor an override only when the gap is ambiguous OR the
   override cites a price-vs-web conflict (contradiction guard); else hard-fail.
5. **Structural provenance into the substrate (today: ZERO columns) — column set DEFERRED to task_03/task_05.**
   Corp-action resolution MUST be representable: the applied cumulative factor + a resolution state (incl.
   `unresolved → null the returns`, never guess — Confidence Invariant). ⚠️ **This task does NOT prescribe the
   columns** (round-1's 2-column / 5-state enum is withdrawn as a Group-A pre-emption). The REQUIREMENT goes to
   **task_03** (generic provenance / `_src` 3-state encoding — reuse it, don't spawn a parallel mechanism) and
   **task_05** (structural-column / minimal-flag adjudication). If a corp-action-specific status is truly needed,
   justify why it cannot ride the generic encoding.
6. **Protect genuine REAL paths (Cat-2) — distinguish extreme-upside from wipeout.** Hard do-not-touch whitelist
   (67 ISINs); the detector must never synthesize a split to "explain" a real outcome. ⚠️ Inox INE312H01016 is a
   genuine **+604% merger multibagger** (NOT a crash); Aster INE900K01012 is a genuine **−100% compulsory
   delisting** — protect BOTH, but the whitelist must separate "genuine extreme path (any direction)" from
   "genuine wipeout" so the protection logic is correct (§3.4 correction box).
7. **Close the 4 coverage gaps:** resolve SIKKO, RAJMET, MKPL (issue_adj<1) + GICL (+948% dup) — none are in
   the evidence catalog today.
8. **Encode INE399K01017 (Indiabulls Power)** once its bonus ratio is sourced (Cat-1 lists "Bonus issue
   reported" with no ratio → currently unencodable).

**OPEN OWNER-QUESTIONS:**

- **Q1.** Source-of-truth for corp-action *resolution*: adopt `corp_action_external_evidence.csv` (53 web-
  verified verdicts) as the canonical overlay seed, or re-verify each independently before trusting?
- **Q2.** For the 6 STAYS-FLAGGED + 4 uncovered (SIKKO/RAJMET/MKPL/GICL): **flag+null the returns** (lose the
  rows from return analysis) or commission a web-evidence pass (STAGE 6) to resolve them first?
- **Q3.** Ratio-aware gap tolerance: what band counts as "gap ≈ claimed ratio" (e.g. ±15% log-magnitude)?
  Tighter = more flagged-unresolved; looser = risk of accepting a wrong ratio. Owner's risk preference?
- **Q4.** Repeated genuine events: if a stock truly had two same-ratio bonuses within 90d, the cluster detector
  would wrongly collapse them. Accept "one price gap ⇒ one event" as the disambiguator, or require manual
  confirmation for every collapse?
- **Q5.** Indiabulls Power INE399K01017: source the missing bonus ratio (web/DRHP) now, or leave the row's
  pre-bonus returns flagged-unreliable until then?
- **Q6.** Provenance columns: the round-1 2-column / 5-state proposal is WITHDRAWN as a Group-A pre-emption.
  Confirm corp-action resolution rides the GENERIC provenance scheme (task_03 `_src`/3-state) + structural-column
  adjudication (task_05), rather than a bespoke corp-action status enum — or, if a dedicated status IS wanted,
  what footprint (minimal factor-only vs full per-action audit ex_date/ratio/source/verdict)?
- **Q7.** Build sequencing: the charter says "base first, then fix D-1 through the solid base." Confirm D-1 is
  no longer the immediate boulder — i.e. this design is captured now but BUILT only after task_04/06/08 land.
- **Q8 (NEW).** **Trust of empty-ISIN yfinance rows.** 354 yfinance rows carry no ISIN (52 match a substrate IPO
  symbol) and are the structural origin of the over-counts + reused-symbol hazard. **Demote them to
  CORROBORATION-ONLY** (may confirm but never CREATE an adjustment alone — NSE/ISIN-authoritative) vs keep them as
  gap-fillers under the price-gap arbiter? Quantify what each policy keeps/drops (how many genuine NSE-uncovered
  events rely SOLELY on a symbol-only yfinance row) before deciding.
- **Q9 (NEW).** **Reproducibility / timebomb of the corp-action INPUT** (cross-link task_08/task_09; charter §D).
  `corp_actions_merged.csv` is built from 03k/03l over LIVE yfinance + NSE scrapes; re-running the scrapers
  OVERWRITES the cache and a yfinance refresh silently changes ratios/dates (the exact mechanism behind the
  ROLEXRINGS triple-report). Must the corp-action raw inputs (yfinance + NSE pulls) be captured as **pinned
  snapshots** feeding the overlay so the detector is deterministic — and must a yfinance refresh surface as a
  task_09 reconciliation DIFF rather than silently re-corrupting? (Confirm yes.)
- **Q10 (NEW).** **Malformed-ISIN nse:sme rows.** 163 `nse_corp_actions:sme` rows store a non-ISIN numeric code
  in the `isin` column (NPST `409536`, USASEEDS `462637`, …). Fix at the scraper/parser (map code→real ISIN) so
  ISIN-keyed dedup/overlay works, or accept symbol-only matching for SME corp actions as policy?

---

### DONE CHECKLIST
- [x] all 8 steps present and non-empty
- [x] ground-truth inputs cited by FILE PATH
- [x] step-6 numbers present (pred-1 caught 8 / FP 0 ; pred-2 caught 12 stocks rounded [11 exact] / **FP ≥1/12 = ANGELONE** ; pred-3 symbol-only-yf dup 13 ; missed NPST-on-pred1 + ENGINERSIN/OPTOCIRCUI-on-pred2 ; ≥2 ISIN examples: ROLEXRINGS, NPST, ANGELONE, USASEEDS, ATLANTAA, KAUSHALYA)
- [~] **PROVISIONAL — review-loop stop rule NOT yet satisfied.** Rounds 1-4 were self-administered; the independent Round 5 found numerous ≥LOW findings (loop NOT dry). Closure requires ≥2 consecutive INDEPENDENT zero-finding rounds (STAGE 5).
- [x] NOT-FINAL marker + open-owner-questions block present
