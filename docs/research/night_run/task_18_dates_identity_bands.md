# task_18 — dates / identity / price-bands / min-investment / one-offs (Group B re-audit)

> **STATUS: NOT FINAL — design/think proposal for owner review.** Part of the 2026-06-17 data-foundation
> design night run (charter: `night_run_2026-06-17_charter.md`). Group B issue-register + existing-fix re-audit.
>
> **PROVENANCE OF THIS FILE (important, read first):** The upstream author step of workflow `wf_362066cc-8dc`
> did NOT produce this file (the `night_run/` directory held only `_run_continuity.md` + `bash_action_log.tsv`;
> `find docs/research -name 'task_*.md'` returned zero files). A review pass was dispatched against a
> non-existent artifact; the review agents — correctly, per the charter's "verify from ground truth, never
> memory" rule — REFUSED to fabricate a review of imagined content and instead flagged the missing file as a
> precondition failure, AND pre-empted the real, ground-truthed data issues this task must cover. This file was
> authored during the **apply-review-findings** step to capture those verified findings durably ("capture
> everything durably" is a hard charter rule) so the scope is not lost. It is a **first authored skeleton seeded
> from verified review findings**, NOT a fully-worked 8-step task — the DONE CHECKLIST at the bottom marks what
> still has to be completed (options/analysis depth, the full multi-lens review loop). Treat accordingly.
>
> **All counts below were RE-VERIFIED against ground truth** by the apply-findings agent reading
> `data/master/ipo_analysis.csv` (2384 rows) directly via the `csv` module (read-only), not taken on faith from
> the review JSON. Where my re-count differed from the review's number, MY verified number is used and the
> discrepancy is noted.

---

## 1. Scope (the single question)
What is the target end-state, present/absent policy, and declarative validity rules for the **identity** and
**timing/structural metadata** family of columns — specifically: **issue/listing dates**, **identity &
identity-verification columns**, **price bands**, **min-investment / lot**, and the assorted **one-offs**
(O-11, O-13, O-14, O-16 from `alignment_audit_2026-06-16.md`) — such that they are CLEAN, EXTENSIBLE, CORRECT
(minimal structural flags, declarative data-driven validity rules, single source of truth, flag-don't-guess)?

This task does NOT decide the global layout (task_04), the present/absent ENCODING mechanism (task_03 — this
task CONSUMES it), the overlay (task_08), or instrument-type as a structural dimension (task_05b — this task
FEEDS it a correctness finding). Cross-links are noted inline.

## 2. Ground-truth inputs (cited by file path)
- `data/master/ipo_analysis.csv` (2384 rows) — the substrate; all counts below derived here, read-only via `csv`.
  Identity-name columns verified: the substrate has NO bare `name` column; identity names live in `company_name`
  (populated), `name_at_ipo`, `official_isin_name` (both sparsely populated — e.g. the Std Chartered IDR row
  `INE028L21018` has BOTH `name_at_ipo` and `official_isin_name` BLANK). All company names cited below are from
  `company_name`. **name_at_ipo / official_isin_name nullity is itself an identity-coverage gap (see §3).**
- `docs/research/alignment_audit_2026-06-16.md` — the O-series (O-11 dates, O-13 price-bands, O-14 min-inv,
  O-16 = a BUNDLE of THREE one-offs: Wakefit promoter post>pre `INE0E7301029`, Newmalayalam lot_size=1
  `INE0TP801012`, Std Chartered IDR `INE028L21018`). The audit also (lines 573-578) already proposed the
  **systemic checks** that fall in this task's scope: #3 band invariant (`band_low ≤ issue ≤ ~1.05×band_low`)
  and #4 date-ordering invariant (`open ≤ close ≤ listing`, **cross-checked vs first traded day** =
  `data/prices/<isin>.csv` first row). This task ADOPTS those as the prior spec and reconciles them (see §3/§8),
  rather than reinventing weaker versions.
- `docs/schema.md` — column documentation. Drift verified directly against the substrate:
  (a) `price_band_width_pct` (schema line 48) is ABSENT from the substrate; (b) `price_band_high` is absent from
  BOTH the substrate AND `docs/schema.md` (schema documents only `price_band_low`, line 47); (c) `ticker_src`
  (schema line 191, "derived") is ABSENT from the substrate. **Sourcing contradiction to resolve:** `docs/sources.md`
  lines 28-29 attribute price band / lot size / min investment to **sharescart**, while `docs/schema.md` lines 51-53
  attribute `face_value`/`lot_size_shares`/`min_investment_rs` to **chittorgarh**. These are the exact fields this
  task audits; the authoritative source-of-record must be pinned before any backfill plan (§8 owner Q).
- `docs/data_review.md` (note: lives at `docs/data_review.md`, NOT the bare `data_review.md` path) — the review
  register. **Section B (lines 22-26) ALREADY registers the no_ref/identity-cross-check item at 27 rows**
  ("ISIN not in any NSE/BSE exchange list … couldn't be cross-checked … eyeball name+ticker for these 27"). The
  substrate now shows **38** `no_ref` rows (verified) — a **27→38 drift** since data_review was written
  (2026-05-31). The identity-coverage finding in §3 is therefore an UPDATE to a known owner-registered item, not
  a fresh discovery.
- `data/master/review/*.csv` — `name_isin_review.csv`, `ticker_conflicts.csv`, `ticker_validation.csv` are the
  in-scope identity review CSVs (cross-check against the identity findings in §3).
- `rules/index.md` — tested-signal registry. Relevant registered rule: **`x-nonequity`** (non-equity instruments
  FPO/InvIT/REIT handled **SEPARATE** from equity IPOs, per owner decision). This GOVERNS the IDR-misclassification
  hand-off to task_05b — the IDR-as-equity row contaminates equity-only analyses, which is exactly the
  already-settled `x-nonequity` boundary. The hand-off builds on this registered rule (does NOT re-litigate it).

## 3. Reproduce + re-audit (verified against current data, 2384 rows)
Each O-item below was reproduced read-only. **Material finding: the audit's O-items UNDERCOUNT the real
problem** — most of these are COVERAGE gaps (1000s of rows), not one-off value errors.

### O-11 — date-ordering (close_date > listing_date) — REPRODUCES (3 rows), but undercovers
- Verified: **3 rows** have `close_date > listing_date` (a violated `open <= close <= listing` invariant):
  - `INE144J01027` (20 Microns Ltd.) — open 2008-09-08, close 2008-09-11, **listing 2008-09-06** (before close only).
  - `INE918N01018` (Veto Switchgears) — open 2012-12-03, close 2012-12-05, **listing 2012-02-13** (before BOTH).
  - `INE168O01026` (GCM Commodity) — open 2013-08-01, close 2013-08-05, **listing 2013-04-05** (before BOTH).
  - **Which field is corrupt (verified):** for Veto AND GCM the `listing_date` precedes the `open_date` too — so
    `listing_date` is the corrupt field (wrong-year/transposition), NOT `close_date`. For 20 Microns listing
    precedes only `close`. The audit (line 557) frames O-11 as "list BEFORE close"; the prose "almost certainly
    day/month transposition" under-specifies which bound is wrong. The invariant must check `open ≤ close ≤ listing`
    as a whole, route to `quality==dirty`, and **identify which bound is violated** (don't assume close is wrong).
    All currently **UNFLAGGED**.
- **The `open ≤ close` arm is sound but was not stated.** Verified read-only: `open_date > close_date` violations
  = **0**; null `open_date` = **0**; null `close_date` = **0**; all date columns are uniform ISO (no parse
  ambiguity). So the invariant's applicability gate hinges ONLY on `listing_date` presence (open/close are always
  present and well-ordered).
- **Coverage gap the audit misses:** **14 rows have NULL `listing_date`** (old MB/FPO with no price history,
  e.g. Tech Mahindra `INE669C01036`, GMR Infra `INE776C01039`). These ESCAPE the ordering invariant entirely
  (can't evaluate `<= listing` when listing is null). The invariant therefore needs an explicit
  **applicability gate** (`open_date present AND close_date present AND listing_date present AND has_price_history`)
  and must REPORT how many rows it can vs cannot check — coverage of the invariant must itself be auditable.
- **Date-quality issues beyond ordering (verified, audit-uncovered):** (a) **close→listing gap**: `INE590L01019`
  (Vaswani Industries) has close 2011-05-03 → listing 2011-09-20 = a **140-day** gap vs the ~3-6 day SEBI norm — a
  strong wrong-date signal caught by NO ordering rule (15 rows exceed a 30-day close→listing gap; most are 31-39d
  and may be legacy-era normal, so a gap bound needs era calibration). (b) the open→close duration distribution is
  sane but no max-duration plausibility bound is proposed. (c) **No draft/RHP/DRHP/anchor-allocation date exists in
  the dataset at all** — limiting any cross-validation of the date chain (sourcing gap).
- **Audit's date ground-truth anchor (adopted):** the audit (line 558) resolves date one-offs against the **first
  row of `data/prices/<isin>.csv`** (first traded day). This task adopts that as the anchor for resolving the 3
  close>listing rows, rather than guessing the transposition.
- **Scope boundary (O-1):** `alignment_audit` O-1 (Udayshivakumar `INE0N0Y01013` listing_open=0 raw) is a
  listing-DAY value one-off and is **owned by task_19** (returns/listing-day), not here, so task_20's gap-check
  can confirm coverage rather than finding O-1 orphaned.

### O-13 — price bands — the audit's "2 inverted bands" conflates two failure modes; COVERAGE is the real gap
- **Structural gap:** there is NO `price_band_high` column in the substrate — only `price_band_low` (verified:
  `price_band_high` ABSENT). The band is HALF-captured; band-width is not computable.
- **Schema drift (verified):** `docs/schema.md` lists `price_band_width_pct` (line 48), which is ABSENT from the
  substrate; AND `price_band_high` is absent from BOTH the substrate and `docs/schema.md` (band_low is the only
  band column documented). Reconcile both (end-state schema is the single source of truth — feeds task_01).
- **Coverage gap (precise set cardinalities — verified):** `price_band_low` BLANK = **1498**; `min_investment_rs`
  missing (blank+zero) = **1498** — these two ARE the **identical** row-set. But `lot_size_shares` BLANK = **1480**,
  NOT 1498. The 18-row difference is EXACTLY the 18 zero-min_inv SME rows (lot present, band absent). So
  "band/lot/min-inv blank" is NOT one identical set: **1480 rows are missing all three**, and **18 rows are missing
  band_low + min_inv but HAVE lot** (the longterm 2006-19 cohort never got band/lot/min-inv enrichment). O-13
  addressed only the inverted case(s), never the 1498 missing band_low rows.
- **Inversion direction + Enser reconciliation (resolves a contradiction in the audit):** O-13 (audit lines
  563-565) classified BOTH Insolation (band_low 131 > issue 38) and Enser `INE0R9I01021` (band_low 10 < issue 70)
  as "inverted bands" with root cause "price_band_low scraped from wrong field." That framing **conflates two
  distinct failure modes:**
  - `band_low > issue_price` IS a genuine violation. On current data I reproduce **1** such row: `INE0LGX01024`
    (band_low 131 > issue 38.00).
  - `band_low < issue_price` is **NORMAL** (issue priced at/above the floor) — verified **683** substrate rows have
    band_low < issue. It is therefore NOT per se an error, and Enser is NOT caught by an inversion rule.
  - **BUT the audit's conclusion that Enser's band_low IS wrong still holds — via a different rule.** Enser's
    band_low=10 is confirmed wrong by the cross-field check below (lot 2000 × band_low 10 = 20000 vs min_inv 140000,
    a 7× break; and lot × issue_price 70 = 140000 matches min_inv exactly). So Enser is a genuine band_low error,
    detected by the cross-field rule, NOT by `band_low > issue`. **This task explicitly overturns the audit's
    "two inverted bands" classification:** there is ONE inversion (Insolation/`INE0LGX01024`); Enser is a
    band_low-too-low error caught cross-field. (Surfacing this reconciliation rather than silently disagreeing.)
  - **The band-validity rule must be `band_low ≤ issue_price ≤ band_high` (once band_high exists), not just
    `band_low > issue`.** Until band_high is sourced it is UN-IMPLEMENTABLE in full; see §8 proposal 2.

### O-14 — min_investment_rs — the "18 zeros" massively undercounts
- Verified: **1480 BLANK + 18 literal-zero = 1498 / 2384 (63%) missing**; only **886 positive**. (Review JSON
  said the same — confirmed.) The 18 literal-zeros are the I1 "0-instead-of-missing" bug in this field
  (`price_band_low` and `lot_size_shares` have ZERO literal zeros — the 18 are anomalous to THIS field).
- **CORRECTION (the 18 zeros are NOT cheaply recoverable from band_low):** verified read-only against the
  substrate — of the 18 literal-zero min_inv rows, **0 / 18 have `price_band_low`** (all 18 have band_low BLANK;
  all 18 are SME); but **18 / 18 have `lot_size_shares`** AND **18 / 18 have `issue_price`**. Examples:
  `INE0NJ001013` (CFF Fluid Control, lot 400, band_low '', issue 165), `INE18PB01017` (Bhavik Enterprises, lot
  2000, band_low '', issue 140), `INE0SIK01014` (Gujarat Peanut, lot 3200, band_low '', issue 80). So the earlier
  claim "recoverable as lot × band_low" was FALSE — there is no band_low to multiply. The only existing-column
  derivation possible is **lot × issue_price** (which all 18 have). The alignment_audit O-14 itself (line 566) says
  "despite valid lot×price." **Action:** literal-0 → null+flag (I1), then optionally derive min_inv ≈ lot ×
  issue_price (owner decision — that is a *derivation*, not the published min_inv).
- **What distinguishes the 18 zeros from the 1480 blanks** is therefore NOT band availability (neither has
  band_low): it is that the **18 zeros have lot + issue_price (so min_inv is derivable as lot×issue_price)**, while
  the **1480 blanks lack lot too** (not derivable). The 1480 are a **source enrichment gap** (longterm cohort never
  enriched), an owner decision (backfill source vs accept null), not a one-off fix.

### O-16 — a BUNDLE of THREE one-offs (audit lines 568-569) — all three now covered
O-16 in the audit is three distinct one-offs. The earlier skeleton addressed only the IDR; all three are in this
task's named scope and are now re-audited against current data.

**(a) Std Chartered IDR — instrument_type MISCODED + literal-0 issue_amount:**
- Verified: `INE028L21018` (Standard Chartered PLC IDR) has `instrument_type = 'equity'` and — **column-name
  correction** — there is NO `issue_amount` column in the substrate; the actual columns are `issue_amount_cr`
  (value = literal **`0.0`**, NOT blank) and `issue_size_cr` (value = blank). So this is an **I1
  "0-instead-of-missing"** instance (audit line 569 = "issue_amount 0"), to be **nulled + flagged**, consistent
  with this task's own min_inv 0-handling — NOT the already-correct null state. (`name_at_ipo` and
  `official_isin_name` are also both blank on this row.)
- It is an IDR (Indian Depository Receipt), not equity. A mislabelled non-equity row leaks into equity-only
  financial/band analyses (the `x-nonequity` SEPARATE-handling boundary). **Feeds task_05b** (instrument-type
  correctness audit) — building on the registered `x-nonequity` rule, not re-deciding it.
- Current `instrument_type` distribution (verified): `{equity:2329, fpo:38, reit:9, invit:8}` — no `idr`/`ncd`
  value at all, so the IDR is hidden inside `equity`.
- **NORTH-STAR detector (replaces the fragile name-sweep):** the ISIN itself structurally encodes instrument
  family — `isin[7]` is the security-type digit. Verified: `isin[7]=='2'` selects EXACTLY the 18 trust/DR-unit
  instruments (9 REIT + 8 InvIT + the 1 IDR), and the **ONLY** row with `instrument_type=='equity' AND
  isin[7]=='2'` is precisely the misclassified Std Chartered IDR (`INE028L21018`) — **zero false positives, zero
  false negatives, no string matching.** A declarative ISIN-structure validity rule (derive expected family from
  `isin[7]`; FLAG any row where derived family ≠ `instrument_type` → `quality==dirty`) is the PRIMARY cross-check,
  consistent with the repo's "ISIN is the primary key" principle. Keep name patterns (`IDR`/`FPO`/`REIT`/`InvIT`/
  `NCD`) only as a SECONDARY signal — a name sweep alone is locale/spelling-dependent and would silently miss a
  future IDR whose name lacks the keyword. **Hand the ISIN-derived classifier to task_05b/task_07.**

**(b) Newmalayalam Steel — lot_size_shares == 1 (verified the ONLY lot==1 row):**
- Verified: `INE0TP801012` (Newmalayalam Steel) is the SINGLE `lot_size_shares == 1` row in the substrate
  (min_inv 90, band_low 85) — a clear ingestion error (no board has a 1-share lot). Recover the true lot from
  sharescart/DRHP or route to `quality==dirty`.
- **A plausibility floor on lot_size is required (the cross-field rule CANNOT catch this).** The min_inv≈lot×band
  rule structurally MISSES Newmalayalam: 90 ≈ 1×85 passes cleanly because all three co-corrupted fields are
  mutually consistent. Mutual-consistency checks are blind to co-corrupted triples. Add an INDEPENDENT plausibility
  floor on `lot_size_shares` (lot==1 / single-digit lots are implausible for any board) so a self-consistent-but-
  wrong triple is still caught.

**(c) Wakefit — promoter post>pre inversion:**
- Verified: `INE0E7301029` (Wakefit) has `promoter_pre_issue_pct = 33.56` and `promoter_post_issue_pct = 37.39`
  (post > pre) — promoter stake should normally FALL after an IPO (dilution). The promoter-pct invariant
  (`promoter_post ≤ promoter_pre`, with documented exceptions like fresh-issue-only structures) belongs to the
  financials/structural task — **hand it to task_16 (financials) and cross-link**, do not re-decide here.

### Identity-verification columns (coverage + dead-column findings)
- `ticker_needs_review` is BLANK on **100% (2384/2384)** — a DEAD, never-populated column. North-star: retire
  it or populate it; do not carry a column that is always empty.
- `isin_xchg_check` = `{match:1303, '':1027, unchecked:39, renamed_confirmed:15}`;
  `name_isin_check` = `{match:1304, '':1027, no_ref:38, renamed_confirmed:15}` (verified). **1027 rows blank =
  identity-verification NEVER RUN** (the longterm 2006-19 cohort). Blank ≠ "fine"; it is the present/absent
  trap — must be encoded as an explicit "not-verified" state (task_03), not silently trusted. **This is an UPDATE
  to `docs/data_review.md` Section B** (which registered the no_ref item at 27 rows; now 38 — a 27→38 drift; the
  11 newly-no_ref rows should be reconciled). Also cross-check `data/master/review/name_isin_review.csv`,
  `ticker_conflicts.csv`, `ticker_validation.csv`.
- **CORRECTION — these are NOT "near-duplicate verdicts" (they DISAGREE on 39 rows):** verified joint distribution
  shows `isin_xchg_check` and `name_isin_check` carry DIFFERENT information and disagree on **39 rows**
  (`(unchecked, no_ref)` ×38 + `(unchecked, match)` ×1). They answer different questions — ISIN-vs-exchange-listing
  check vs name-vs-ISIN check. Naive unification would LOSE the distinct signal. **Recommendation (corrected):** if
  unifying, design a COMPOSITE verdict that preserves both dimensions (not a single collapsed status), and attach
  the 39-row disagreement evidence to the **task_07** hand-off (identity vocabulary declared once).

### Trading-identity (ticker) columns — entire family added to scope
- The substrate carries FOUR overlapping trading-identity columns (a single-source-of-truth smell): blank counts
  verified — `nse_symbol` **699 blank**, `bse_script_code` **680 blank**, `ticker_ns` **1443 blank**, `ticker_bo`
  **1540 blank**. (`ticker_src` is in `docs/schema.md` line 191 but ABSENT from the substrate — schema drift.)
- **283 rows have NO usable trading ticker at all** (no `nse_symbol` AND no `ticker_ns` AND no `ticker_bo`) — a
  coverage/owner-decision item. Four parallel ticker columns violate single-source-of-truth. **Design a single
  canonical trading-symbol resolution** (which column wins, fallback order) rather than four parallel columns →
  **feeds task_07**.

### face_value — added to scope (identity + split-detection role)
- Verified: `face_value` is BLANK on **1886 / 2384 (79%)**; populated dist `{10:483, 5:8, 2:4, 1:3}` — all within
  the plausible set `{1,2,5,10}` (no out-of-set values currently). `docs/schema.md` line 51 documents it
  (chittorgarh).
- **Correctness role:** face_value governs **face-value splits**, which the project's corp-action/identity rule
  hinges on ("a face-value split changes the ISIN", per CLAUDE.md). A missing/incorrect face_value directly affects
  split detection and the symbol-keyed corp-action join. **Cross-link task_14** (corp-actions). Validity rule: flag
  any face_value outside `{1,2,5,10}` (none today). The 79% coverage gap is an owner backfill decision.

### anchor_allocation_cr — added to scope (structural IPO-metadata coverage)
- Verified: `anchor_allocation_cr` is BLANK on **1487 / 2384**; `docs/schema.md` line 59 documents it
  (chittorgarh). It is a present/absent coverage case directly analogous to the band/lot gaps, and anchor
  presence/size is a known IPO-quality signal. Add to the coverage table (present/absent classification);
  the gap is an owner backfill decision.

### listing_at — un-normalized free text
- Verified distribution: `BSE, NSE` 848 · `BSE SME` 741 · `NSE SME` 730 · `BSE` 61 · `NSE` 2 · `NSE, BSE` 1 ·
  `BSE, NSE, MCX-SX` 1. Order-inconsistent (`BSE, NSE` vs `NSE, BSE`) and legacy `MCX-SX` — cannot be reliably
  parsed for exchange identity. Needs normalization to a canonical exchange-set token.

### Cross-field consistency — the rule must compare against lot × ISSUE_PRICE, not lot × band_low
**CORRECTION (the band_low formulation produces ~80% false positives):** the earlier `min_inv ≈ lot × band_low
(>15%)` rule flags 5/886, but verified row-by-row, **4 of the 5 are NOT errors** — they are explained by the
NORMAL "issue priced above the floor" convention (band_low < issue; 683 substrate rows do this), and for those 4
`min_inv = lot × issue_price` EXACTLY:
- `INE0LWY01029` (Tridhya) — min_inv 126000 = lot 3000 × issue 42 (band_low 35 is just the floor). NOT an error.
- `INE0N1401016` (Neelam) — min_inv 144000 = lot 6000 × issue 24 (band_low 20). NOT an error.
- `INE130701019` (Valencia) — min_inv 132000 = lot 1200 × issue 110 (band_low 95). NOT an error.
- `INE0SLP01017` (NSB BPO) — min_inv 280000 BUT lot 2000 × issue 121 = 242000 (band_low 121 = issue). Here min_inv
  ≠ lot×issue either → a genuine **min_inv** anomaly (not a band_low error).
- `INE0R9I01021` (Enser) — min_inv 140000 = lot 2000 × issue 70 (matches), but lot × band_low = 2000×10 = 20000 (a
  7× break) → a genuine **band_low** error (band_low=10 is wrong; this is the audit's "inverted" Enser, caught here
  rather than by `band_low > issue`).
- **So of the 5 band_low breaks, only 2 are real (Enser band_low error + NSB min_inv anomaly); the other ~3-4 are
  the priced-above-floor convention.** The correct cross-field validity rule compares **min_inv against lot ×
  issue_price** (or lot × band_high once it exists), NOT lot × band_low. Against `lot × issue_price` the rule
  cleanly isolates the genuine min_inv anomalies (e.g. NSB) and is not fooled by the floor convention; band_low
  errors (Enser) surface as `lot×band_low` ≠ `lot×issue_price` ≠ min_inv. No current check catches any of these.
- **Threshold sensitivity (verified sweep, completing the earlier TODO):** breaks under `|min_inv −
  lot×band_low|/(lot×band_low)` = **13 at 10% · 5 at 15% · 1 at 25%**. The 15% choice was arbitrary and most of its
  hits are the floor convention; switching the basis to `lot × issue_price` makes the threshold far more
  defensible. Consider board-specific tolerances (SME vs MB lot conventions differ); list marginal ISINs at each
  threshold for owner calibration.

## 4. Options (≥2-3, steelmanned) — TODO: deepen
For each problem family, the candidate end-states (to be steelmanned + a non-leaning alternative argued):
1. **Date-ordering & band validity:** (a) declarative validity-rule registry entries routing violators to
   `quality==dirty` (LEANING — declarative, data-driven, north-star aligned); vs (b) hardcoded per-rule branches
   in the pipeline (rejected — behavioral-flag sprawl, violates minimal-flags); vs (c) leave unflagged + handle
   downstream (rejected — silently keeps known-bad rows, violates flag-don't-guess).
2. **Coverage gaps (1498 band/lot/min-inv; 1027 identity-checks):** (a) treat as present/absent
   "source-never-published" state + surface owner backfill decision (LEANING); vs (b) attempt cross-column
   derivation (only works for the 18 zeros, not the 1480 blanks); vs (c) drop the longterm cohort from band/
   affordability analyses via rule-applicability gating (task_10) — credible alternative, argue on merits.
3. **price_band_high / band-width:** (a) add `price_band_high` (source: sharescart cap price) + derive
   `price_band_width_pct` in end-state schema (LEANING — completes the band, fixes schema drift); vs (b) keep
   band_low-only + retire the stale schema entry (cheaper, but loses band-width signal — argue); vs (c) the
   CHEAPER completion the audit/schema actually specced — `band_low + price_band_width_pct` (schema line 48), from
   which band_high derives — argue this is less sourcing work than a new band_high column. **Reconcile with the
   audit's `band_low ≤ issue ≤ ~1.05×band_low` proxy** (audit line 576): verified it over-catches **581/886**
   (most issues price ABOVE 1.05× the floor), so the proxy is unusable; until band_high (or width_pct) is sourced,
   the only sound band rule is `band_low ≤ issue_price` (catches the 1 inversion). **band_high is a prerequisite —
   the full band rule is UN-IMPLEMENTABLE today.**
4. **ticker_needs_review (dead column):** (a) retire; vs (b) populate from the validity rules. Argue both.
5. **isin_xchg_check vs name_isin_check (they DISAGREE on 39 rows, not duplicates):** (a) a COMPOSITE verdict
   preserving both dimensions (LEANING — keeps the distinct ISIN-vs-exchange and name-vs-ISIN signals); vs (b)
   keep two columns, justify distinct semantics; vs (c) collapse to one status (REJECTED — loses the 39-row signal).
6. **Trading-symbol identity (4 overlapping ticker columns):** (a) a single canonical resolved trading-symbol with
   declared fallback order (nse_symbol → bse_script_code → ticker_ns → ticker_bo) + 283 no-ticker rows surfaced as
   an owner item (LEANING — single source of truth); vs (b) keep four parallel columns (REJECTED — SSOT smell).
7. **instrument-type mislabel detector:** (a) declarative ISIN-structure rule (`isin[7]` family vs
   `instrument_type`) as PRIMARY, name-patterns SECONDARY (LEANING — zero-FP/FN, no string matching, "ISIN is
   primary key"); vs (b) name-pattern sweep alone (REJECTED — locale/spelling-fragile, misses keyword-less names).
8. **lot_size plausibility:** add an independent floor (lot==1 / single-digit implausible) BECAUSE the
   mutual-consistency cross-field rule is blind to co-corrupted triples (Newmalayalam 90≈1×85).

## 5. Analysis — TODO: deepen step-by-step per option; preliminary converged leaning below.
Preliminary leaning: a **declarative validity-rule set** routing violators to `quality==dirty`:
- date-ordering with an applicability gate (whole-chain `open ≤ close ≤ listing`, identifying the violated bound;
  resolve against `data/prices/<isin>.csv` first traded day) + a close→listing gap bound;
- band validity `band_low ≤ issue_price` now (the full `≤ band_high` is a PREREQUISITE-blocked extension; the
  audit's 1.05× proxy is rejected — over-catches 581/886);
- cross-field `min_inv ≈ lot × ISSUE_price` (the band_low basis over-caught 4/5);
- an INDEPENDENT lot_size plausibility floor (mutual-consistency rules miss co-corrupted triples);
- a declarative ISIN-structure instrument-family rule (PRIMARY) over a name sweep (SECONDARY);
PLUS explicit present/absent encoding for the coverage gaps (consumed from task_03), PLUS feeding the IDR
misclassification to task_05b (on the `x-nonequity` rule), Wakefit promoter to task_16, and the identity vocabulary
(composite verdict + single canonical trading-symbol) to task_07. All NON-FINAL.

## 6. TEST / validate (numbers, verified read-only against data/master/ipo_analysis.csv, 2384 rows)
| Check / predicate | Caught (true issues) | Over-caught / coverage / not-checkable | Worked ISIN examples |
|---|---|---|---|
| `open ≤ close ≤ listing` (whole) | 3 (close>listing); 0 open>close | 14 null listing_date (gated out); open/close never null/well-ordered | INE144J01027, INE918N01018 (listing<open → listing is corrupt), INE168O01026 |
| close→listing gap > 30d | 15 (mostly 31-39d, era-calibrate) | 1 extreme: 140d | INE590L01019 (140d) |
| `band_low > issue_price` (inversion) | 1 | 683 rows band_low<issue are NORMAL (NOT violations); 1498 band_low blank | INE0LGX01024 (131 > 38) |
| `min_inv ∈ {blank, 0}` (I1) | 1498 (1480 blank + 18 zero); 18 zeros derivable as lot×ISSUE (not band_low) | n/a | INE028L21018 (IDR issue_amount_cr=0.0 also I1), INE0NJ001013 (zero min_inv, lot 400, issue 165) |
| `min_inv ≉ lot × ISSUE_price` (corrected basis) | 1 genuine min_inv anomaly | band_low basis over-caught 4/5 (floor convention) | INE0SLP01017 (min_inv 280000 vs lot×issue 242000) |
| `band_low ≠ lot-implied` (Enser-type band error) | 1 | — | INE0R9I01021 (band_low 10 vs issue 70; lot×band 20000 vs min_inv 140000) |
| ISIN-structure: `isin[7]=='2' AND instrument_type=='equity'` | 1 (zero FP, zero FN) | isin[7]=='2' = exactly 18 trust/DR units | INE028L21018 (IDR mislabelled equity) |
| `lot_size_shares == 1` (plausibility floor) | 1 (only lot==1 row) | cross-field rule MISSES it (90≈1×85 self-consistent) | INE0TP801012 (Newmalayalam) |
| promoter_post > promoter_pre | 1 (→ task_16) | — | INE0E7301029 (Wakefit: 37.39 > 33.56) |
| `ticker_needs_review` blank | 2384/2384 (dead column) | n/a | (all rows) |
| no usable trading ticker | 283 | n/a | (nse_symbol+ticker_ns+ticker_bo all blank) |
| `isin_xchg_check` vs `name_isin_check` disagree | 39 rows (NOT duplicates) | n/a | 38× (unchecked,no_ref) + 1× (unchecked,match) |
| `face_value` blank / out-of-set | 1886 blank; 0 out-of-{1,2,5,10} | n/a | (longterm cohort) |

False-positive notes: (a) `band_low < issue_price` is NORMAL (683 rows) — NOT a violation. (b) The earlier
`min_inv ≈ lot × band_low` rule over-caught 4/5 of its hits (the floor convention); the corrected basis is `lot ×
issue_price`. (c) min_inv≈lot×band tolerance sweep: 13/5/1 breaks at 10/15/25%.

## 7. Multi-lens review (loop-until-quiet) — NOT YET RUN on this authored content
- Round 0 (the round that produced THIS file): correctness/completeness/context-pickup/north-star/adversarial
  agents reviewed the (then non-existent) artifact and returned the precondition-failure + ground-truthed
  findings now folded in above. That round reviewed an ABSENT file, so it does NOT satisfy the stop rule.
- **STOP RULE NOT YET MET.** Required: ≥2 consecutive independent fresh-agent rounds with zero new findings
  (≥LOW), hard floor ≥2 rounds, each logged in `night_run_2026-06-17_review_log.md`, reviewer ≠ author.
  **TODO:** run the review loop on this authored content.

## 8. Non-final proposal + open owner questions (NOT FINAL)
**Proposed (for approval, all NON-FINAL):**
1. Add declarative validity rules with explicit applicability gates, all routing violators → `quality==dirty`
   (never silently kept or guessed), all adopting the audit's spec where it exists:
   - **date-ordering** `open ≤ close ≤ listing` (whole-chain, identifying WHICH bound is violated — not assuming
     close is wrong), gated on all-three-present; resolve the 3 close>listing rows against the **first traded day
     in `data/prices/<isin>.csv`** (the audit's anchor). Add a **close→listing gap bound** (era-calibrated;
     INE590L01019 = 140d) and an open→close max-duration plausibility bound.
   - **band validity** `band_low ≤ issue_price ≤ band_high` — band_high is a PREREQUISITE (un-implementable
     today); until sourced, ship only `band_low ≤ issue_price` (catches the 1 inversion). Do NOT use the audit's
     `≤1.05×band_low` proxy (over-catches 581/886).
   - **cross-field** compare `min_inv` against **lot × issue_price** (NOT lot × band_low — that over-caught 4/5);
     surface band_low errors as lot×band_low ≠ lot×issue_price.
   - **lot_size plausibility floor** (lot==1 / single-digit implausible) — INDEPENDENT of the cross-field rule
     (which is blind to co-corrupted triples like Newmalayalam).
   - **ISIN-structure instrument-family** rule (`isin[7]` derived family ≠ `instrument_type`) as the PRIMARY
     non-equity-mislabel detector; name patterns SECONDARY.
   - **face_value** validity (flag outside `{1,2,5,10}`; none today) — cross-link task_14 (split detection).
2. Add `price_band_high` to the end-state schema (source: sharescart cap price) and derive `price_band_width_pct`;
   reconcile the `docs/schema.md` drift — schema documents `price_band_width_pct` (absent) and omits
   `price_band_high` entirely, and lists `ticker_src` (absent). Schema is the single source of truth (task_01).
   Also resolve the `docs/sources.md` (sharescart) vs `docs/schema.md` (chittorgarh) sourcing contradiction for
   band/lot/min-inv before any backfill plan.
3. Encode the coverage gaps via the task_03 present/absent 3-state policy ("source-never-published" /
   "fetch-parse-failed" / "real-zero"): band_low blank 1498 (= min_inv missing 1498, identical set); lot blank
   1480 (the 18-row gap = the 18 zero-min_inv SME rows with lot but no band); identity-checks blank 1027; 14 null
   listing_date; face_value blank 1886; anchor_allocation_cr blank 1487. **I1 zero-instead-of-missing → null+flag**
   for: the 18 literal-zero min_inv AND the Std Chartered IDR `issue_amount_cr = 0.0` (cross-link task_19/I1, fixed
   once at the load layer). The 18 zero-min_inv rows are derivable as **lot × issue_price** (NOT lot × band_low,
   which is blank on all 18) — a derivation, owner-decision.
4. Normalize `listing_at` to a canonical exchange-set token (note legacy `MCX-SX`).
5. Fix the Std Chartered IDR misclassification via the ISIN-structure rule → hand to task_05b (building on the
   registered `x-nonequity` SEPARATE-handling rule, not re-deciding it). Newmalayalam lot==1 → recover or dirty.
   Wakefit promoter post>pre → hand to task_16 (financials).
6. Decide `ticker_needs_review` (retire vs populate); design a single canonical trading-symbol with fallback order
   (surface the 283 no-ticker rows); preserve the `isin_xchg_check`/`name_isin_check` distinction as a COMPOSITE
   verdict (they disagree on 39 rows) → hand identity vocabulary to task_07.

**Open owner questions:**
- Backfill the 1498 band_low / 1480 lot / 1498 min-inv rows from an external source, or accept null on the
  longterm cohort? — **and first resolve which source is authoritative** (sources.md says sharescart; schema.md
  says chittorgarh) and its longterm coverage.
- Backfill the 1027 unverified-identity longterm rows, or accept "not-verified" as a terminal state? (Reconcile
  the 27→38 no_ref drift vs `docs/data_review.md` Section B — what 11 rows newly became no_ref?)
- Backfill `face_value` (1886 blank) and `anchor_allocation_cr` (1487 blank), or accept null on the longterm cohort?
- Tolerance for the min_inv ≈ lot×issue_price rule (and do SME vs MB lot conventions need different tolerances)?
  (sweep: 13/5/1 breaks at 10/15/25% on the old band_low basis.)
- For the 14 null-listing_date rows: skip-with-flag, or backfill listing_date from first traded day?
- Retire `ticker_needs_review`, or populate it from the validity rules?
- Collapse the four ticker columns to one canonical resolved trading-symbol, and how to treat the 283 no-ticker rows?

---

## Review notes — round-2 findings application (all re-verified read-only against the substrate)
This file was a verified-findings skeleton; round-2 review (the JSON below) surfaced correctness/completeness/
context-pickup/north-star findings. Each was re-verified against `data/master/ipo_analysis.csv` before applying;
NONE were judged invalid or out-of-scope. Summary of what changed:

**Correctness fixes (all verified):**
- **18 zero-min_inv rows are recoverable as lot × ISSUE_PRICE, NOT lot × band_low** (verified 0/18 have band_low,
  18/18 have lot AND issue_price; all SME). The prior "lot × band_low" claim was factually false. §3 O-14 corrected;
  the distinguisher between the 18 zeros and 1480 blanks is now lot+issue_price presence, not band availability.
- **Cross-field rule basis changed band_low → issue_price.** Verified 4/5 of the old band_low hits are the NORMAL
  priced-above-floor convention (683 rows have band_low<issue); only Enser (band_low error) + NSB (min_inv anomaly)
  are real. §3 cross-field + §6 table corrected; the O-13/cross-field Enser contradiction resolved (Enser is NOT
  an inversion — caught cross-field; the audit's "two inverted bands" is overturned, conclusion preserved).
- **`issue_amount` → `issue_amount_cr`, value literal `0.0` (not blank)** for the Std Chartered IDR — re-classed as
  an I1 zero-instead-of-missing case. §3 O-16 + §6 + §8 corrected.
- **Set cardinalities made precise:** band_low blank 1498 = min_inv missing 1498 (identical); lot blank 1480; the
  18-row gap is the zero-min_inv SME rows. §3 O-13/O-14 corrected.
- **Date one-offs:** for Veto + GCM, listing precedes open → `listing_date` is the corrupt field (not close);
  invariant now whole-chain. Added open>close=0 / null-open=0 / null-close=0 verification. §3 O-11.
- **Schema drift:** noted `price_band_high` absent from BOTH substrate and schema.md, and `ticker_src` absent from
  substrate. §2/§3/§8.
- **Std Chartered name claim:** cited names are from `company_name`; `name_at_ipo`/`official_isin_name` are sparse
  (blank on the IDR row) — flagged as an adjacent identity-coverage gap. §2/§3.

**Completeness additions (all verified, were omitted):** Newmalayalam lot==1 (only lot==1 row) + lot plausibility
floor (cross-field rule is blind to the co-corrupted 90≈1×85 triple); Wakefit promoter post>pre → task_16; ticker
family (nse_symbol 699 / bse_script_code 680 / ticker_ns 1443 / ticker_bo 1540 blank; 283 no-ticker rows);
isin_xchg_check vs name_isin_check DISAGREE on 39 rows (not duplicates → composite verdict); face_value (1886 blank,
split-detection role → task_14); anchor_allocation_cr (1487 blank); close→listing gap bound (INE590L01019 = 140d);
ISIN-structure instrument-family detector (isin[7]=='2', zero FP/FN) replacing the fragile name-sweep; band rule
un-implementability + the 1.05× proxy over-catch (581/886) + the width_pct cheaper-completion; min_inv≈lot×band
threshold sweep (13/5/1 at 10/15/25%); O-1 scope boundary (→ task_19).

**Context-pickup fixes (verified):** `docs/data_review.md` (correct path) Section B already registered the no_ref
item at 27 rows — now 38 (27→38 drift) → framed as an UPDATE; adopted the audit's already-specified systemic checks
#3 (band) / #4 (date-ordering vs `data/prices/<isin>.csv` first traded day); cited the registered `x-nonequity`
owner rule governing the IDR hand-off; cross-linked the identity review CSVs.

**No findings invalid/out-of-scope.** task_05b (instrument-type), task_07 (identity vocabulary), task_14 (face_value/
splits), task_16 (promoter), task_19 (I1 / O-1) items are kept as CORRECTNESS findings but explicitly handed off,
not re-decided here — respecting the charter's task-ownership boundaries.

## DONE CHECKLIST
- ☑ all 8 steps present; steps 4 (options, now 8 steelmanned) + 5 (analysis, converged leaning) deepened in
  round-2; step 7 (review loop) still has an unmet stop rule (see below).
- ☑ ground-truth inputs cited by FILE PATH.
- ☑ step-6 numbers present (caught / over-caught / coverage + ≥2 ISIN examples per check) — all re-verified read-only.
- ☐ review-loop stop rule satisfied (NOT MET — round-2 findings APPLIED here, but the ≥2-consecutive-clean-fresh-
  agent-rounds stop rule is not yet reached; each round must still be logged in `night_run_2026-06-17_review_log.md`).
- ☑ NOT-FINAL marker + open-owner-questions block present.

**→ TASK still INCOMPLETE on the review loop only.** Steps 1-6 + 8 are now substantively worked and ground-truth
verified (round-2 findings folded in). Remaining: continue the multi-lens review loop (step 7) to the stop rule
(≥2 consecutive independent fresh-agent rounds with zero ≥LOW findings, hard floor ≥2 rounds), logging each round.
