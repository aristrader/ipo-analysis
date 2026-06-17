# Data-Foundation Rebuild — MASTER PLAN (single source of truth)
*Consolidated 2026-06-17. THREE surviving docs: this (PLAN) + `FOUNDATION_ARCHITECTURE.md` (design reference) +
`FOUNDATION_BUILD_SPEC.md` (frozen build-spec detail). Everything else from the design run was folded in and deleted
(recoverable from git snapshot 7eda95b). A line-by-line audit caught initial over-compression → the build-spec doc was recovered.*

> **STATUS: DESIGN COMPLETE — decisions made — NOT building yet.** Owner builds only once everything is concrete.
> This is the planning/decisions/sequence doc ("what & in what order"). The companion `FOUNDATION_ARCHITECTURE.md`
> is the design reference ("what the system is"). Corp-action/split research findings (background) → `splits_findings.md`.
>
> **ENTRY POINT (read this first after any context reset):** the project pivoted from whack-a-mole patching to
> rebuilding the DATA FOUNDATION correctly (clean · extensible · correct), with the corp-action (D-1) mess as the
> first real case run through it. All owner decisions are below (§2). The ordered build sequence is §3. Nothing is
> built yet. Do NOT start building without explicit owner "go".

---

## 1. NORTH STAR & NON-NEGOTIABLE PRINCIPLES (banked during the review)
- **Clean · Extensible · Correct.** Correctness over speed. **No cheap fixes** (cheap fixes caused this redesign).
- **Flag rather than guess; flag rather than clamp.** Honest-NULL over a fake value.
- **ONE spine, everything else is a derived view.** No stored duplication, no separate files, no row-moving.
  `clean`/`dirty`/`mainboard`/`sme`/`non-equity`/per-pipeline = all `WHERE`-filter views. Reclassify = change one cell.
- **One place to maintain everything.** No parallel sources, no cross-link tables that drift, no archive dumps.
- **ISIN is the only auto-join key.** Name/symbol matching only FLAGS, never merges.
- **Generated, not hand-maintained.** Schema, rules index, lineage diagram = generated from the registries.
- **Config-driven, not hardcoded.** All date boundaries (cohort/era/train-test) live in one time-partition config.
- **Column-lifecycle:** the registry is the catalog of EVERY column (active / planned / retired); shipped data = active only.
- **Generic rule + on/off gate.** Rules are generic; an applicability gate decides if a rule fires for a given IPO.
  A rule scores only if it passes BOTH the relevance gate AND the trust filter (validated / cross-regime / min-N).
- **DATA-LAYER COMPLETION GATE:** the data layer must be complete AND verified before ANY upper-layer (Layer 2/3) work.

---

## 2. DECISIONS (consolidated by theme; deduped from OD-1..8 + D1..D24 + R1..R6)

### 2.1 Missing-data & provenance (the "I1" root fix)
- **Treat `0`/blank field-by-field, 4 states, value-vs-code split** (OD-1, R2): value=NULL for missing ones (math skips them);
  a separate `_prov` code carries the state — `present`(real 0) / `Missing_data`(source never published, not retryable) /
  `error_out`(fetch/parse fail, retryable) / `N/A`(not applicable). Reject the global `0→NaN` (would corrupt 725 real `ofs_cr=0`).
- **One uniform, registry-driven provenance carrier, on genuinely-ambiguous fields only** (OD-2, D6, R1): +1 `_prov` column per
  ambiguous field (fully populated, never blank); non-ambiguous fields get none. Avoids ~100+ dead columns.
- **Cross-field (multi-column) validity predicates** (OD-2, D24): catch O-3 (Σ tranches vs total: 32 + 218 rows).
- **Validate before stamping a source** (OD-1/I1-stamp): a value earns a `_src`/`_prov=present` only after passing its validity check.
- **OD-3 arithmetic recovery (88 subscription rows):** `sub_total_x = sub_total_cr ÷ issue_size_cr`, stamped `derived`, ONLY when
  `issue_size_cr` is valid; **validate the identity on rows that have both before applying.** Never leave a missing/real-demand mismatch.

### 2.2 As-of semantics (the D-3 leak class)
- **As-of class on ALL time-varying fields** (OD-5, D8): `at_ipo` (predictor-legal) vs `current` (display-only) + `_asof`.
  Only `at_ipo` fields feed the predictor → the leak MECHANISM is killed structurally, no patch.
- **IMPORTANT caveat (R3/G14):** the as-of *mechanism* is done, but the at-IPO market-cap *value* is BLOCKED on
  `shares_outstanding` (not in the substrate — BL-1). So until BL-1 lands, the predictor simply has **no trustworthy
  at-IPO market cap** (honestly absent), not a sourced one. "Leak killed" = the predictor can't see the *current* cap;
  it does NOT mean an at-IPO cap exists yet.

### 2.3 Dataset shape (one spine + views)
- **One ISIN-keyed spine = single source of truth** (D1/Option C); masters/cohorts/clean/dirty/non-equity = derived views.
- **5 structural columns** (D2, OD-6, D7): `board` (renamed from overloaded `type`), `instrument_type`
  (equity/reit/invit/idr/fpo — fixes the Std Chartered IDR mislabel), `universe_type` (reserve seam), `quality` (clean/dirty), `cohort`.
- **`cohort` = config-driven view, not stored** (D3): one time-partition config drives cohort + era + train/test/validation splits;
  pull hardcoded dates out of code into it. Materialize views for readability; source of truth = the config.
- **Non-equity** (OD-6): tag with `instrument_type`, exclude from equity analyses via `WHERE` (no if/else), keep in dataset.
- **Two view flavors** (OD-7): coarse `clean`/`dirty` (worklist signal, looks across all columns) + per-pipeline field-scoped views
  (each pipeline keeps rows where ITS required fields are valid → maximizes usable data). Real gating = field-scoped views.

### 2.4 Column registry & lifecycle
- **Declarative YAML registry `columns.yaml` + named-function refs + meta-validator** (D10): metadata=data, logic=code-by-name.
  Add a column reusing existing logic = config-only (non-coder); needing new logic = config + one named function.
- **Column-lifecycle** (D4 + COLUMN-LIFECYCLE POLICY): registry catalogs every column — `active` (materialized) /
  `planned` (backlog stub, not materialized) / `retired` (phantom/old, reason recorded, never re-added).
- **Schema source of truth = the registry;** retire hand-maintained `docs/schema.md` (generate a view from the registry). (D4)
- **`pre_ipo_eps` = retired** (D5); reconsider only if BL-2's EPS work proves it useful.

### 2.5 Identity & matching
- **ISIN-only auto-joins everywhere; names only flag** (O-12). Record matched entity id+name on every join (auditable).
  Then sweep existing data for wrong-entity joins (Bajaj cap 36× too large — "Bajaj isn't the only one").
- **Date-window approximation + curated identity-history golden file** = the data-layer requirement (D14-gate).
  Optional future (does NOT gate): upgrade to a vetted official NSE symbol-change ledger.

### 2.6 Overlay (the locking / reproducibility mechanism)
- **One consolidated fixes-ledger on IMMUTABLE raw → recreatable substrate** (D15): merge the 3 scattered hand-fix files;
  `raw + overlay = substrate`, idempotent, reconciliation-verified. Coherent with the golden catalogs (same store).
- **Ops: SET / DELETE-EVENT / ADD-EVENT / RECOMPUTE** (D16) — SET-only couldn't remove a fake split or add a missing one.
- **Each fix records its OLD VALUE** (D15, R5) → conflict detection. **Conflict policy (D17, Option B):** source still broken → apply;
  source now matches fix → retire fix; source moved to a THIRD value → HOLD for owner review (never silently override).
- **Fetch-time recorded per value** (D15): vintage/provenance + change-detection. Fetch = incremental for speed + PERIODIC FULL
  re-fetch/diff (incremental alone misses upstream corrections to old records).

### 2.7 Network / refetch
- **Honest-NULL default + standing gated refetch mechanism** (OD-4, D11): the `error_out` cells ARE the refetch worklist
  (`Missing_data` excluded — never published). Refetch reuses the same pipeline (no parallel machinery); verified → promote → lock.
  **Network stays default-deny** — the mechanism exists but only runs on owner approval (attended, allowlisted, read-only).
- **First refetch targets when run:** the **18 MB-subscription + 10 GMP** rows (small, high-value, trusted source). The big
  long-term backfills (**1,498** band/lot · **1,027** identity · **1,886** face_value · **1,487** anchor) are a SEPARATE
  later decision — many are likely `Missing_data` (never published 2006–19), so honest-NULL for now. (Concrete per-field
  fallback orders + coverage facts: `FOUNDATION_BUILD_SPEC.md` Part A.)

### 2.8 Cleaning-rules & rule registry
- **Declarative cleaning rules (CR-*)** from the issue catalog; **severity per-class** (D19): field-level null default, escalate to
  whole-row `dirty` only when the error poisons the row.
- **Auto-apply HIGH only** (D20): MED + LOW → dirty-review worklist; a MED rule promotes to HIGH once proven reliable.
- **Rule registry `rules.yaml` + meta-validator** (D21), generated rules index (retire hand-maintained `rules/index.md`).
  A rule entry = **GATE** (`board` + `instrument_type` only) + **`required_fields`** (data-quality via OD-7 views) +
  **PROPERTIES** (`cross_regime_validated`, `min_n`, status, lift). **Firing policy:** scores only if relevance-gate AND
  trust-filter pass; relevant-but-untrusted = display-only (the "evolve-only-if-robust" policy).

### 2.9 Corp-action fix (D-1) — the first real cleanup through the foundation
- **Fix properly through the foundation, not a join patch** (OD-8): price-gap arbiter (source-agnostic) + source-reconcile dedup +
  golden-catalog override + reconciliation campaign. It corrupts returns themselves → a prioritized EARLY build task, not backlog.
- **ISIN-less (symbol-only) yfinance = corroboration-only** (D12): never adjusts alone; honored only if the price-gap arbiter or an
  ISIN source confirms; else flag for manual verify. The single biggest lever on the fake-multibagger over-count class.
- **D12/D13 = a dedicated deep-dive** (enumerate ALL failure modes; calibrate the date-window slack from real ex-date↔first-trade gaps).
  Informed by `splits_findings.md`.
- **Three golden reference files (P-1):** (1) corp-action events (verified ratios/dates; fill the 4-stock gap), (2) identity-history,
  (3) Cat-2 "do-NOT-correct" protected list (67 verified-genuine crashes). Authoritative, append-only, overlay-carried.
  Fallback order: golden catalog → price-gap arbiter → source-reconcile → flag (never guess).

### 2.10 Reconciliation campaign (the verify gate)
- **Migrate EVERY hand-fix into the overlay** (incl. the orphaned Indiabulls Power fix) + reconstruct `old_value` baselines (R5).
- **Rebuild → diff vs current → every mismatch is a bug → resolve** (D18); runs as the first build action, fakes stay until it completes.
- **Must-pass §3 verification targets** (proof the foundation works): ROLEXRINGS / NPST / CANTABIL fakes gone; e6053e7 O-3 nulls hold;
  Indiabulls Power fix lands. Verified twice — during the build (reconciliation) AND before moving to upper layers.

---

## 3. EXECUTION PLAN — topo-sorted phases (dependencies respected)
> "First cleanup" (corp-action, OD-8) means first real cleanup CASE run through the foundation — so the foundation
> framework (registry, provenance, identity, overlay) is built first, then corp-action is the first thing run through it.

### PHASE 0 — Pre-build foundation framework
- **T0.1 Scraper review & fix** (3-point contract: never mint a placeholder · distinguish no-value vs fetch-fail · surface the signal).
  *Gates the I1 provenance build.* [OD-1 pre-task]
- **T0.2 Column-registry framework** `columns.yaml` + meta-validator + named-function code registry. *Foundational — everything declares here.* [D10, D4]
- **T0.3 Time-partition config** (cohort/era/train-test boundaries) + pull hardcoded dates out of code. [D3]

### PHASE 1 — Provenance & missing-data (the I1 fix) — depends: T0.1, T0.2
- **T1.1** `_prov` encoding (value-vs-code split, validate-before-stamp, ambiguous fields only). Canonical codes:
  `present` / `derived` / `Missing_data` / `error_out` / `N/A` (the 4 "missing-data states" = the last-but-`derived` set). [OD-1, OD-2, D6, R1, R2]
  - **Refetch-bucket rule (R2/G2):** only `error_out` = OUR-side fetch/parse failure is retryable (the refetch worklist).
    A **source-emitted placeholder** (source returned junk, e.g. `0.00x`) is NON-retryable → classify `Missing_data`
    (re-scraping the same source won't cure it). Keeps the refetch worklist from chasing un-curable cells.
- **T1.2** Cross-field validity predicates (O-3 Σtranches vs total). [OD-2, D24]
- **T1.3** Arithmetic recoveries (validate-the-identity-first, stamp `derived`): OD-3 subscription (88 rows,
  `sub_total_x=sub_total_cr/issue_size_cr`) **AND** `min_investment_rs` (18 rows, `lot_size×issue_price`, CR-MININV). [OD-3, O-14]
- **T1.4** Gated refetch mechanism (OD-4/D11): the `error_out` cells ARE the worklist; reuse the normal pipeline; verified→promote→lock.
  Network stays default-deny — wired but runs only on owner approval. [OD-4, D11]

### PHASE 2 — Structural columns, spine & views — depends: T0.2, T0.3, T1.1
- **T2.1** Structural columns: `board` (rename `type`), `instrument_type` (incl. IDR fix), `universe_type` (seam), `quality`, `cohort`-view.
  Also **retire `pre_ipo_eps`** (registry status `retired`, D5) — explicit action here. [D2, OD-6, D7, D5]
- **T2.2** One spine + derived views (clean/dirty/mainboard/sme/non-equity). [D1, OD-6, OD-7]
- **T2.3** As-of semantics (`at_ipo`/`current`/`_asof`). [D8, OD-5]
- **T2.4** Per-pipeline field-scoped views (`required_fields` → validity filter). [OD-7]

### PHASE 3 — Identity & matching — depends: T0.2
- **T3.1** Enforce ISIN-only joins everywhere; names only flag; record matched entity id+name. [O-12]
- **T3.2** Curated identity-history golden file. [P-1, D14-gate]
- **T3.3** Sweep existing data for wrong-entity joins (Bajaj + siblings). [O-12]

### PHASE 4 — Overlay (locking mechanism) — depends: T0.2
- **T4.1** Consolidated overlay ledger (merge 3 hand-fix files); immutable raw + overlay = substrate; idempotent. [D15]
- **T4.2** Overlay ops (SET/DELETE-EVENT/ADD-EVENT/RECOMPUTE); old_value capture; fetch-time per value. [D16, D15]
- **T4.3** Conflict policy (Option B: hold-for-review on 3-way move). [D17]

### PHASE 5 — Corp-action cleanup (D-1) [GATE item — first cleanup through the foundation] — depends: P1, **P2** (board/instrument_type/quality + as-of), P3, P4
- **T5.1** Golden files: corp-action events (fill 4-stock gap) + Cat-2 do-NOT-correct list. [P-1]
- **T5.2** Price-gap arbiter (source-agnostic). [OD-8]
- **T5.3** D12/D13 dedicated deep-dive: ISIN-less corroboration-only + all failure modes + slack calibration. [D12, D13]
  *Concrete inputs already found (`splits_findings.md`):* root cause = `07_returns_summary.py:114-127` exact-`(ex_date,ratio)`
  dedup + `03k` 10-day window vs real 11–28-day jitter (median 20) → use **~30-day collapse slack** + relative-tolerance
  ratio compare + direction-normalized gap test; **pre-listing-date filter** kills reused-symbol hazards (PATANJALI/Ruchi
  Soya etc.); 517/1897 rows have no usable ISIN (354 yfinance empty + 163 nse:sme malformed numeric codes); arbiter input
  already exists (`corp_action_corroboration_review.csv` 259 rows / `corp_action_external_evidence.csv` 53). Re-enable the
  `09_assemble.py:88-89` cross-source tripwire for corp-action stocks. Open: ROLEXRINGS ratio 19.96-vs-10.0 + overlay re-keying.
- **T5.4** Source-reconcile dedup + fallback order; apply the fix through the foundation. [OD-8, P-1]

### PHASE 6 — Cleaning-rules & rule registry — depends: T0.2, P1, **P2** (rule gate uses board/instrument_type; CR-* write `quality`)
- **T6.1** Declarative cleaning-rules model (CR-* from the issue catalog); per-class severity; auto-apply HIGH only. [D19, D20, OD-7]
- **T6.2** Rule registry `rules.yaml` (gate + required_fields + properties) + meta-validator. [D21]

### PHASE 7 — Reconciliation campaign [VERIFY GATE] — depends: P4, P5
- **T7.1** Migrate ALL hand-fixes into the overlay (incl. orphaned Indiabulls Power) + reconstruct old_value baselines. [§3, R5]
- **T7.2** Rebuild → diff vs current → resolve every mismatch. [§12, D18]
- **T7.3** Verify the §3 must-pass targets (ROLEXRINGS/NPST/CANTABIL/e6053e7/Indiabulls). [§3]

### PHASE 8 — Generation & pre-coding finalization — depends: T0.2, P6
- **T8.1** Generate schema view from `columns.yaml`; retire `docs/schema.md`. [D4]
- **T8.2** Generate rules index from `rules.yaml`; retire hand-maintained `rules/index.md`. [D21]
- **T8.3** P-2 lineage/architecture diagram (from registry + golden files; what links to what). [P-2]
- **T8.4** P-3 data-change rulebook (wired into project_map CONTEXTS). [P-3]

### ▶ DATA-LAYER COMPLETION GATE — data layer complete AND verified → only now move up.

### PHASE 9 — Upper layers (out of this design's scope) — re-point Layer 2/3 onto the new substrate; re-point genuinely-sound findings; rebuild anything that stood on a data hack.

---

## 4. BACKLOG (genuinely deferred — does NOT gate upper layers; separate efforts, with concrete data)
- **BL-1 — At-IPO market cap (proper D-3 cure).** No proxy/cheap fix. Steps on pickup: value-audit Chittorgarh `kpi_market_cap_post_ipo`
  (HDFC AMC ₹7.8cr error known) → source **shares outstanding** (R3, the shared blocker with EPS) → derive `market_cap_at_ipo_cr =
  issue_price × post-issue shares`. `market_cap_at_ipo_cr` + `shares_outstanding` = registry status `planned` (not shipped); 90 existing
  longterm values preserved in source.
- **BL-2 — EPS comparability (A1 vs A2) + usage check.** A1 (constant-share-base recompute) blocked on the same shares-outstanding (R3).
  Now: no EPS-trend/CAGR feature shipped; per-year EPS values kept. On pickup: check if EPS feeds a feature → A2 null-and-flag if no, A1 if yes.
- **BL-3 — POST-DEV cleanup** (only after the new foundation is proven): retire the old data + old data docs + hand-maintained
  `docs/schema.md`/`rules/index.md` (now generated). Prefer git history over a dump; one source of truth, no stale parallel copies.
- **D14-optional** — official NSE symbol-change ledger upgrade (gated on a vetted trusted source).
- **P-4 — Live / upcoming data** — its own project; each source refreshes differently. Design the seam now (`upcoming` status,
  `announcements` feed), build later.

---

## 5. CROSS-CUTTING TODOs (P-2/P-3 — these ARE the Phase-8 tasks T8.3/T8.4, listed here for visibility, not duplicated)
- **P-2 — Lineage/architecture diagram.** The **pre-coding human-readable picture already exists** = `FOUNDATION_ARCHITECTURE.md` §1
  (hand-authored layer map). The **generated** diagram (P-2, from the populated registry) is **T8.3** — it can only be auto-generated
  *after* the registry exists, so it confirms/supersedes the hand-authored one. (Resolves the "generated vs pre-coding" tension.)
- **P-3 — Data-change protocol rulebook** (declare in registry → validity check → design → implement → update pipeline → regenerate → verify).
  Process doc, no registry dependency → may be authored any time; scheduled as **T8.4**. Architectural home noted in `FOUNDATION_ARCHITECTURE.md`.

---

## 6. INPUTS / SUPPORTING ARTIFACTS (the surviving docs)
- `FOUNDATION_ARCHITECTURE.md` — the design reference (layers, tables, yaml, what-runs-what).
- **`FOUNDATION_BUILD_SPEC.md`** — the FROZEN build-spec detail (sourcing roster + fallback orders · the full issue catalog +
  CR-* mapping · task-file build hazards). Read at build; retire post-build (BL-3). *(Recovered from git after a line-by-line
  audit caught over-compression — see that doc's header.)*
- `splits_findings.md` — background corp-action/split research (feeds the Phase-5 deep-dive).
- `foundation_run_log.tsv` — audit log of every action taken during this consolidation run.
