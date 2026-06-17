# Cluster 1 — THE DATA MODEL (connected design)

> **STATUS: NOT FINAL — design / think only.** Per `night_run_2026-06-17_charter.md`. No code, no pipeline
> changes; this doc proposes, the owner decides. All counts below were verified read-only against
> `data/master/ipo_analysis.csv` (2,384 rows, `as_of` 2026-06-06 per `substrate_meta.json`) on 2026-06-17, or
> are inherited (cited) from the Group-B task files (`task_17_market_cap.md`, `task_19_returns_i1.md`,
> `task_15..task_18`). Where a number is inherited rather than re-run, it is marked **[B]**.

This is **one coherent data-model design**, not six fragments. It is organized as a single chain:
**schema → structural partition columns → present/absent provenance → as-of semantics → dataset layout →
future-universe seams.** Each section is the natural consequence of the one before it. Where a topic belongs to a
sibling cluster, this doc states the *seam* and defers the content (so a later integrator can weave them):

- **Cluster 2 = sourcing / source-registry / identity-matching.** This doc names which fields are time-varying and
  need an as-of attribute, and which structural columns exist; it does **not** decide the per-field source fallback
  order or the ISIN/symbol collision logic. (Seams flagged inline as `→ C2`.)
- **Cluster 3 = cleaning / overlay / declarative rules.** This doc defines the *encoding* a cleaning rule reads and
  writes (the provenance states, the quality partition, the validity-routing contract); it does **not** author the
  per-issue cleaning rules or the overlay replay machinery. (Seams flagged as `→ C3`.)

The north star (charter): **CLEAN · EXTENSIBLE · CORRECT** — minimal *structural* (partition) columns, not
behavioral if/else; single source of truth; new columns/stocks/live-data slot in without restructuring; flag rather
than guess.

---

## 0) DECISIONS NEEDED FROM OWNER (pinned)

These are the cross-cutting model decisions; per-section open questions are restated at the end.

1. **One internal spine vs two stored masters?** The candidate layout is 2 stored masters (`mainboard`/`sme`).
   §5 argues the cleaner end-state is **ONE physical master keyed by ISIN with a `board` column**, masters/cohorts
   as derived views. Owner picks the physical layout.
2. **Compact provenance encoding** (§3): adopt the **one `*_prov` code per value-bearing field** (3-state +
   instrument-N/A), replacing the partial `*_src` scheme — vs keep `*_src` and bolt a parallel flag. (Recommend the
   unified `*_prov`.)
3. **As-of split for time-varying fields** (§4): adopt the `<field>_at_ipo` / `<field>_current` + `_asof` pattern
   as a **class rule** (not just for market-cap)? Which fields are in the first wave.
4. **Schema drift** (§1): ratify the END-STATE schema as the new single source of truth, **superseding
   `docs/schema.md`** (which is stale: it omits ~120 live columns and documents `issue_price_src`/`ticker_src`/
   `pre_ipo_eps` that are **absent** from the substrate **[B]**).
5. **Future-universe seam now or later** (§6): reserve `universe_type` + the as-of/frequency abstraction in the
   schema **now** (cheap, design-open), build non-IPO/live ingestion later — confirm we reserve, not build.

---

## 1) TARGET END-STATE SCHEMA

### 1.1 Ground truth — what exists vs what is documented (drift)

- The actual substrate `data/master/ipo_analysis.csv` has **220 columns** (verified; header dumped this run).
- `docs/schema.md` documents the **`mainboard.csv`/`sme.csv`** master shape (~99 cols, verified header) — a
  DIFFERENT, narrower file than the analysis substrate. It is the **wrong source of truth** for the end-state:
  - It documents `issue_price_src`, `ticker_src`, `pre_ipo_eps` — **all absent** from the substrate **[B from
    task_19 §3b-i / task_17]**.
  - It does **not** document `cohort`, `instrument_type`, the entire **market-cap family** (`market_cap_cr`,
    `market_cap_class`, `kpi_market_cap_post_ipo`) **[B task_17 §2]**, the `kpi_*` family, `name_at_ipo`,
    `official_isin_name`, the full returns/alpha/MFE/MAE/days-to-* matrices (~110 outcome columns), the
    data-quality columns, or `xcheck_flags`.
- **The two master files themselves diverge** structurally from the substrate: `mainboard.csv`/`sme.csv` lack
  `cohort`, `instrument_type`, `market_cap_*`, the outcome matrix, `data_quality_*`. So today there are
  effectively **three schemas in play** (the two thin masters + the fat substrate) with no single declared truth.

**Resolution (charter task_01):** the END-STATE SCHEMA below — declared in a **column registry** (Cluster-2/§6
seam) — becomes the single source of truth; `docs/schema.md` is regenerated from it (never hand-maintained), the
same generated-not-hand-edited discipline `MAP.md` already follows.

### 1.2 The end-state column set, grouped by domain

Notation per column: **applicability** = `both` (MB+SME) · `MB` · `SME` · and **scope** = `ipo-only` (degrades to
null for future non-IPO rows, §6) vs `universal` (meaningful for any listed stock). Time-varying fields carry an
**as-of** marker (§4). `[+]` = ADD (not present today). `[~]` = present but needs a model change (split/rename/
re-typed). `[-]` = RETIRE/quarantine. Plain = keep.

**A. Identity & classification (universal, partition-bearing — see §2)**
| column | appl | scope | note |
|---|---|---|---|
| `isin` | both | universal | PRIMARY KEY (charter non-negotiable) |
| `company_name`, `name_at_ipo`, `official_isin_name` | both | universal | `name_at_ipo` is an at-IPO snapshot (§4); names blank on some rows **[B task_19]** |
| `board` `[+]` | both | universal | STRUCTURAL partition (§2); replaces overloaded `type` |
| `instrument_type` | both | universal | equity:2329 · fpo:38 · reit:9 · invit:8 (verified) — STRUCTURAL (§2) |
| `universe_type` `[+]` | both | universal | ipo / listed-stock seam (§6); default `ipo` today |
| `quality` `[+]` | both | universal | clean / dirty partition (§2) |
| `cohort` | both | universal | boom:1357 · longterm:1027 (verified) — derivable from `listing_date`; see §2 |
| `nse_symbol`, `bse_script_code`, `ticker_ns`, `ticker_bo` | both | universal | exchange identity → C2 |
| `type` `[-]` | both | — | overloaded (MB/SME); SUPERSEDED by `board`. Retire after migration |
| `exchange`, `listing_at`, `chittorgarh_id/_slug/_url` | both | universal | provenance/identity housekeeping → C2 |
| `industry`, `sector`, `broad_sector` | both | ipo-only? | sector taxonomy; SME-boom sector gaps (24 rows) noted in CLAUDE.md |
| `incorporation_year`, `age_at_ipo_years` `[+ if missing]` | both | ipo-only | doc'd in schema.md, verify presence → C2 |

**B. IPO offer mechanics (ipo-only; null for non-IPO rows in §6)**
`issue_price`, `issue_price_adj` (§4 adjusted), `price_band_low`, `price_band_width_pct`, `book_built`,
`pricing_method`, `face_value`, `lot_size_shares`, `min_investment_rs`, `issue_amount_cr`, `issue_size_cr`,
`fresh_issue_cr`, `ofs_cr`, `ofs_pct`, `anchor_allocation_cr`, `issue_expenses_cr`. — appl `both`.
- `min_investment_rs` `[~]`: 18 zeros are **recoverable** = `lot_size_shares × issue_price` **[B task_19 §6]** →
  derived-recovery rule (C3), not a raw null.
- For FPO/REIT/InvIT some of these are semantically N/A (no fresh/OFS split) → provenance state (d) (§3).

**C. Timetable (ipo-only)** — `open_date`, `close_date`, `listing_date`. appl `both`. `listing_date` is the anchor
for `cohort` and as-of cut-offs (§4).

**D. Demand signals (ipo-only)**
`sub_qib_x`, `sub_nii_x`, `sub_retail_x`, `sub_total_x`, `sub_*_cr` (4), `gmp_pct`. appl `both`, but:
- `sub_qib_x` `[~]`: SME `==0` is REAL (no QIB tranche) — 314 SME rows; MB `==0` (27 rows) is masked-missing
  **[B task_19 §6]**. The board partition (§2) is what disambiguates — a structural column replacing an if/else.
- `gmp_pct` `[~]`: pre-2023 SME = source-never-published (state a), not zero **[B task_19]**.
- **Cross-field invariant:** `sum(tranches) ≈ sub_total_x` — 32 rows violate (all tranches 0, total>0); 218 rows
  partial **[B task_19 §3b-ii]**. Needs a cross-field validity predicate (§3, C3).

**E. Ownership (ipo-only)** — `promoter_pre_issue_pct`, `promoter_post_issue_pct`, `promoter_pre_shares`,
`promoter_post_shares`. appl `both`. These are at-IPO by nature (§4) — fine as-is, but mark as at-IPO snapshots.

**F. People / intermediaries (ipo-only)** — `lead_manager`, `market_maker` (SME-centric), `registrar` `[+ if
missing]`, `objects_of_issue`. `market_maker` appl `SME` (MB IPOs have no market maker) — another natural
board-gated field, encoded by partition not branch.

**G. Listing-day outcomes (ipo-only, time-anchored)** — `listing_open` (raw, Chittorgarh), `adj_listing_open`,
`adj_listing_close`, `adj_listing_gain_open/close`, `listing_high/low/close`, `listing_metrics_status`.
- `listing_open` `[~]`: raw=0 on INE0N0Y01013 but `adj_listing_open=30` correct; `listing_metrics_status='ok'`
  mislabeled (one-off, count=1) **[B task_19 §3c]**. Keep raw + adjusted both (CLAUDE.md convention).

**H. Financials — 3yr block + normalized pre_ipo_* (ipo-only)** — `net_sales_yr{1,2,3}`,
`operating_profit_yr*`, `pat_yr*`, `eps_yr*`, `shareholder_funds_yr*`, `borrowings_yr*`, `total_assets_yr*`,
`operating_cf_yr*`, `pe_ratio`, `pat_ttm_cr`, `sales_ttm_cr`, `eps_ttm`, `roe_pct`, `roce_pct`, `debt_equity`,
`sales_cagr_3y`, `pat_cagr_3y`, and the `pre_ipo_*` normalized family + derived margins.
- appl `both`; **equity-only for analysis** — REIT/InvIT/FPO financials are N/A or non-comparable. The 8
  REIT/InvIT `net_sales_yr3==0` rows are state-(d) N/A, not zeros **[B task_19 §5]**. → gated by `instrument_type`
  (§2), not by a financial-specific flag.
- `borrowings_*==0` is REAL (debt-free) — must NOT be nulled **[B task_19]**.
- `pre_ipo_eps` `[-]`: documented in schema.md but **absent** from substrate — retire from the doc or ADD as a
  real derived field; owner picks.

**I. Market-cap family (universal-ish; the as-of poster child)** **[B task_17]**
- `market_cap_at_ipo_cr` `[+]` (at-IPO snapshot; primary src `kpi_market_cap_post_ipo` after value-audit, fallback
  `issue_price × post-issue shares`) — ipo-only-ish, the analog/predictor feature.
- `market_cap_current_cr` `[~]` + `market_cap_current_asof_date` `[+]` (live Screener cap; display only; never a
  predictor input — heals D-3 leak).
- `market_cap_class` `[~]`: single declarative derivation over the row's **authoritative** cap (at-IPO for
  equity-IPO; current for already-listed), null on null/0 (fixes the O-15 `0→micro` lie, 7 rows).
- `kpi_market_cap_post_ipo` `[~]`: the existing at-IPO source — keep as input, value-audit first (≥1 gross parse
  error, HDFC AMC INE127D01025 = 7.8cr) **[B task_17 §3]**.

**J. Returns / outcomes (ipo-only today; universal once live-prices flow, §6)** — the ~110-column matrix:
`return_from_issue_*`, `return_from_listing_*`, `alpha_*`, `alpha_sc_*` across 10 horizons; `mfe_*`/`mae_*` +
`_lst_` variants; `days_to_mfe/mae/breakeven_*`; `max_gain_pct`, `max_drawdown_*`, `all_time_high/low`,
`current_price`, `current_return_from_issue`, `outcome_class`, `volatility_annual`, `median_daily_turnover_inr`,
`circuit_lock_frac`, `liquidity_flag`, `delisted`, `delist_reason`, `n_days_history`, `price_source`,
`has_price_history`. — appl `both`. **These are inherently current/live (as-of = current, §4)** and are the future
seam where daily-refreshed listed-stock data lands (§6). `current_price`/`current_return` carry an implicit as-of
date that should be made explicit.

**K. Structural & provenance (universal; the model's spine)** — `quality`, `board`, `universe_type`,
`instrument_type`, `cohort`, the `*_prov` provenance codes (§3), `data_quality_score`, `data_quality_tier`,
`confidence`, `confidence_reason`, `isin_xchg_check`, `name_isin_check`, `ticker_needs_review`, `xcheck_flags`.
- Today's `*_src` columns (15 of them **[B task_19 §3b-i]**) are SUBSUMED by the unified `*_prov` scheme (§3).

**Net ADD / RETIRE summary (end-state):**
- ADD: `board`, `quality`, `universe_type`, `market_cap_at_ipo_cr`, `market_cap_current_cr` +
  `_asof_date`, the unified `*_prov` codes, per-field `_asof` markers on time-varying fields, `registrar`/
  `age_at_ipo_years` if absent.
- RETIRE/replace: `type` (→ `board`), the 15 partial `*_src` (→ `*_prov`), schema.md's phantom
  `issue_price_src`/`ticker_src`/`pre_ipo_eps`.

---

## 2) STRUCTURAL COLUMNS (minimal, partition not behavior)

The north star forbids behavioral if/else sprawl. The lever is a **tiny set of STRUCTURAL columns** that
*partition* the rows; every downstream consumer then `GROUP BY` / `WHERE` on a column instead of branching on a
condition. A structural column answers "**which kind of row is this?**"; a behavioral flag answers "**should the
code do X here?**" — we keep only the former.

**The minimal structural set (5 columns):**

| column | values (verified) | partitions | replaces the branch… |
|---|---|---|---|
| `board` | `MB` (913) / `SME` (1471) | mainboard vs SME analysis & gating | `if is_sme: market_maker… ; if MB: no QIB-zero…` |
| `instrument_type` | equity:2329 / fpo:38 / reit:9 / invit:8 | equity vs FPO/REIT/InvIT | `if reit/invit: skip financials` → becomes `WHERE instrument_type='equity'` |
| `universe_type` `[+]` | ipo (all today) / listed-stock (future) | IPO vs non-IPO stock | future `if not ipo: skip offer fields` |
| `quality` `[+]` | clean / dirty | trusted vs quarantined rows | `if row_is_suspect: exclude…` scattered everywhere |
| `cohort` | boom:1357 / longterm:1027 | regime/era for validation | `if listing_date < 2020: ...` |

**Why these and not more:**
- They are **orthogonal facts about the row's identity**, each independently true and stable, not derived from a
  rule's needs. `board`, `instrument_type`, `universe_type` are intrinsic; `quality` is a curation state;
  `cohort` is a deterministic function of `listing_date` (so it could be a *derived view* column, §5 — kept as a
  materialized convenience, but it is NOT a new source of truth).
- They **collapse the existing scattered conditionals** into `WHERE`/`GROUP BY`. Concrete instances from ground
  truth: the SME-vs-MB `sub_qib_x==0` disambiguation (314 SME real vs 27 MB bug **[B task_19]**) becomes
  `WHERE board='SME'` vs `board='MB'`; the "equity-only findings must not run on NCD/REIT/InvIT" rule (charter
  task_10) becomes `WHERE instrument_type='equity'`; the Layer-3 "exclude unreliable rows" becomes
  `WHERE quality='clean'`.
- **`quality` is the keystone of the no-branch principle.** Today, suspicion is expressed as ad-hoc exclusions and
  `data_quality_tier` filters re-implemented per consumer. A single `quality` partition + the dirty quarantine
  (§5) means: clean = the analysis substrate by construction; dirty = the cleanup worklist; promotion (dirty→clean)
  is the only state transition. No consumer re-derives "is this row trustworthy."

**What is NOT structural (stays a value/provenance column, not a partition):** `outcome_class`, `liquidity_flag`,
`data_quality_tier`, `confidence`. These are *graded* or *behavioral-adjacent*; promoting them to partitions would
re-introduce branching. They live as ordinary columns; consumers may filter on them but they are not the spine.

**Present/absent is NOT a structural column** — it is per-field provenance (§3). Crucially we do **not** add one
boolean partition per field (that is the explosion the charter forbids); provenance is a compact per-field code,
covered next.

`board` + `instrument_type` + `universe_type` + `quality` + `cohort` = the entire structural partition. Everything
else is a value or a provenance code. That is the minimal-flags design.

---

## 3) MISSING-DATA POLICY + PRESENT-VS-ABSENT (the I1 root fix)

This is the model's correctness core and the root fix for the **I1 "0-instead-of-missing" bug**. Grounded in
`task_19_returns_i1.md`.

### 3.1 The problem, precisely (from task_19 ground truth)

I1 is a **2-layer defect, not a loader bug [B task_19 §3a]**:
1. The **source emits a placeholder `0`** (sharescart prints `0x` subscription when uncaptured) — verified **132
   raw source-zeros** in `data/raw/*_events.csv`.
2. An **enrich/backfill step launders it**: `'0'` is a truthy non-empty string → copied through AND stamped with a
   real provenance. Verified: **all 124 `sub_total_x==0` substrate rows carry `sub_total_x_src='sharescart'`** —
   the provenance layer actively *asserts the fake zero is genuine*. The same pattern recurs at other stamp sites
   (the 10 `gmp_pct==0` rows carry `_src ∈ {ipocentral, websearch}`).

So a value of `0` (or `""`, or blank) today conflates **four distinct truths**, and the consumer cannot tell them
apart:

| state | meaning | example (verified [B]) |
|---|---|---|
| **(a) source-never-published** | the source never offered this field for this row/era | pre-2023 SME `gmp_pct`; 1129 `sub_total_x` blanks |
| **(b) fetch/parse-fail OR source-placeholder** | we tried and failed, or the source printed a placeholder | 124 `sub_total_x=0`; 7 `market_cap_cr=0`; 18 `min_investment_rs=0` |
| **(c) real zero** | the value genuinely IS zero | 725 `ofs_cr=0` (fresh-issue-only); debt-free `borrowings=0` |
| **(d) N/A for instrument** | the metric doesn't apply to this instrument type | 8 REIT/InvIT `net_sales_yr3=0` |

A blanket `0→NaN` is WRONG: it would destroy the 725 real `ofs_cr=0` rows. A field-blind approach can't separate
(b) from (c). **The fix is field-aware validity routing + a 3(+1)-state present/absent encoding.**

### 3.2 The compact provenance encoding (NOT one boolean per field)

The charter forbids a per-field boolean explosion. The existing `*_src` scheme is the right *idea* but is (i)
present on only **15 of 220 columns**, and among I1 fields only `sub_total_x` and `gmp_pct` have it **[B task_19
§3b-i]**, and (ii) it lies (stamps a real source on placeholders).

**Proposed: ONE `<field>_prov` code column per value-bearing field, replacing `*_src`.** It is a single compact
categorical that carries BOTH the present/absent state AND (when present) the winning source — folding two concerns
into one column instead of `_src` + a new boolean:

```
<field>_prov  (one small categorical / packed code per value-bearing field)
   PRESENT  states (value is trusted):   "<source>"            e.g. chittorgarh | sharescart | screener | derived | overlay
   ABSENT   states (value is null):      "absent:source"       (a) source-never-published
                                         "absent:fetchfail"    (b) we tried, failed / source placeholder
                                         "na:instrument"        (d) N/A for this instrument_type
   REAL-ZERO is NOT an absent state:     value=0, prov="<source>"   (c) — a present, trusted zero
```

Key properties:
- **One column per field, not one-boolean-per-state.** The state space (present-with-source | absent:source |
  absent:fetchfail | na:instrument) is a single enum, so a 7-field I1 footprint costs 7 `_prov` columns total, not
  7×4 booleans. (Implementation may bit-pack a global provenance vector per row — an impl detail for the registry,
  Cluster-2/§6; the *model* is "one code per field".)
- **It cannot lie.** A value that fails its validity predicate is routed to `absent:fetchfail` and gets NO source
  tag — the laundering bug is structurally impossible because earning a source tag REQUIRES passing validity. This
  is the "validity gate before stamping, at every stamp site" rule **[B task_19 proposal #4]**, expressed in the
  data model rather than per-script.
- **Real zero is first-class:** `(c)` is `value=0` WITH a present source tag — distinct from `absent:fetchfail`.
- **Blanks are disambiguated too:** today a blank + empty `_src` conflates (a) and (b) **[B task_19 §5]**. The
  `_prov` code records `absent:source` vs `absent:fetchfail` for blanks, not only for zeros.

### 3.3 Validity routing (the rule the encoding serves) — defer authoring to C3

The *encoding* (this doc) is consumed by **per-field validity predicates** that decide (b) vs (c). The *predicates
themselves* are Cluster-3 cleaning-rule content; this doc only fixes the contract: each value-bearing field
declares a validity predicate in the registry (§6); at assemble time a value failing it is routed to
`absent:fetchfail` (null + `_prov`), never silently kept as 0. Seeds, verified with **0 over-catch [B task_19 §6]**:
- `sub_total_x==0` on a LISTED row → (b) — 124 rows (a listed IPO cannot have 0× subscription).
- `sub_qib_x==0`: `board='SME'` → (c) real (314); `board='MB'` → (b) (27) — **board partition drives it (§2)**.
- `min_investment_rs==0 ∧ lot×price>0` → recover (derived), not null — 18 rows.
- `market_cap_cr==0` on a listed row → (b) — 7 rows; class→null.
- `net_sales_yr3==0`: `instrument_type∈{reit,invit}` → (d) (8); else equity → (b) (5, two need per-row check).
- `ofs_cr==0`, `borrowings_*==0` → ALWAYS (c) — never touch.
- **Cross-field:** `sum(tranches)≉sub_total_x` → route tranche cells to (b) (32+218 rows) — registry must support
  multi-column predicates `[B task_19 §3b-ii]` (→ C3 / Cluster-2 registry).

**This is the single root fix for I1**: it dissolves the 0-vs-missing ambiguity into an explicit, compact,
non-lying per-field code, applied uniformly via the registry — no per-consumer "is this 0 fake?" re-implementation.

---

## 4) AS-OF SEMANTICS (a CLASS, not one instance)

The D-3 market-cap leak is **one instance of a general class** **[B task_17 §1, §9; charter §9]**: any field
scraped "as of now" silently leaks future/post-outcome state into an at-IPO predictor. The migration analysis's
circular rank-IC 0.564 is a second instance (current cap, grew-into-it, reverse-causation) **[B task_17 §2]**.

**The model rule:** every **TIME-VARYING** field carries an explicit **as-of attribute** declaring whether it is an
**at-IPO snapshot** or a **current/live reading**, plus an `_asof` date for live readings.

### 4.1 The two as-of classes

- **`at_ipo` (immutable snapshot):** the value as it was at/around the IPO. The legitimate analog/predictor
  feature. Examples: `market_cap_at_ipo_cr`, `issue_price`, `promoter_*_pct`, the `pre_ipo_*` financials,
  `name_at_ipo`, all offer mechanics. These are **frozen** once captured; a re-run must reproduce them exactly.
- **`current` (live, dated):** the value as of a scrape date. Display/current-state only; **forbidden** as a
  predictor/analog/weight input. Examples: `market_cap_current_cr`, `current_price`, `current_return_from_issue`,
  `all_time_high/low`, every `outcome`/`alpha`/`return_*` column (these are by definition post-listing). Each
  carries an `_asof` date (e.g. `market_cap_current_asof_date`).

### 4.2 Encoding (cheap, registry-driven)

Two equivalent encodings — pick one in C2/§6:
1. **Name convention** (`<field>_at_ipo` / `<field>_current` + `<field>_current_asof`) — explicit, self-documenting,
   already used for `market_cap_*` and `adj_*` listing fields. Recommended for the high-risk fields.
2. **Registry attribute** (`as_of: at_ipo | current`) declared once per column, with a single global `data_asof`
   date for all `current` fields — compact, no name churn, but less self-documenting in the CSV.

**Recommendation:** name-convention for the *leak-prone* fields (market-cap, any future fundamental that has both a
TTM-at-IPO and a live value); registry-attribute + global `data_asof` for the outcome matrix (already uniformly
"current"). Either way the **registry records the as-of class for every time-varying field** so a predictor build
can mechanically assert "only `at_ipo` fields entered the feature set" — turning D-3 from a latent leak into a
checkable invariant.

### 4.3 Why this is a class fix, not a market-cap patch

Binding the predictor to `market_cap_at_ipo_cr` fixes D-3 **[B task_17 §7]**, but the *same* discipline must cover
`layer3/forward_test.py` (the OOS harness, an identical leak path **[B task_17 §2/Open-Q2]**) and any future field
with a live reading. Encoding as-of in the model — rather than remembering it per feature — is what makes the leak
**structurally unable to recur** when a new fundamental column is added later (§6 extensibility): a `current` field
simply cannot be selected into an at-IPO feature set. (Cross-ref Cluster-3 features↔data reverse-map for the
per-feature binding list.)

---

## 5) DATASET LAYOUT (re-derived; the 2-master leaning challenged)

The charter's leaning is **2 stored masters (`mainboard`, `sme`) + derived views**. I steelman it, then argue a
credible alternative, and recommend.

### 5.1 Option A — 2 stored masters (`mainboard.csv` + `sme.csv`), shared schema; views derived
- **Steelman:** matches the owner's "2 base files, others are scripts" mental model; each file is human-readable and
  small enough to open; board is implicit in the filename so a casual reader never confuses MB and SME.
- **Cost (correctness/clean):** `board` is then encoded **twice** — as a structural column AND as the file split —
  which duplicates the partition and invites drift (a row could be in `sme.csv` with `board='MB'`). Every
  cross-board view (`combined`) must UNION two files; every schema change touches two files; ISIN uniqueness must be
  enforced ACROSS two files, not within one. It also fights §2: if `board` is a real structural column, the file
  split is redundant with it.

### 5.2 Option B — ONE physical master keyed by ISIN, `board` as a column; MB/SME/cohort/clean/dirty all derived
- **Steelman:** ISIN is THE primary key (charter non-negotiable) and uniqueness is enforced in ONE place. `board`,
  `instrument_type`, `universe_type`, `quality`, `cohort` are *columns* (§2), so EVERY view —
  `mainboard`, `sme`, `clean substrate`, `dirty worklist`, `longterm`, `shortterm`, `combined` — is a pure
  `WHERE` filter over the one master. One schema, one registry, one place to add a column. No duplication of the
  board partition. This is the *maximal* expression of single-source-of-truth + minimal-flags.
- **Cost:** the single file is wide (220→~240 cols) and large; "open it in a spreadsheet and eyeball SME" is less
  immediate (mitigated: the derived `sme` view is one filter away and can be materialized on demand).

### 5.3 Option C — internal spine + 2 materialized masters (hybrid)
- One internal ISIN-keyed spine (source of truth for storage/registry), with `mainboard.csv`/`sme.csv`
  **materialized as derived views** for human convenience (regenerated, never hand-edited). Gets B's single-truth
  for the pipeline AND A's readable two-file ergonomics. This is essentially the charter's open sub-design (b)
  ("2 masters stored directly vs materialized from one internal spine").

### 5.4 Recommendation (NOT FINAL)

**Option C as the physical layout, with Option B as the logical model.** Rationale tied to the north star:
- **Single source of truth (CORRECT/CLEAN):** ONE ISIN-keyed spine holds every row + the full schema + provenance +
  as-of. ISIN uniqueness, the column registry, and the overlay (Cluster-3) all bind to this one object.
- **Everything else is a derived VIEW (EXTENSIBLE), each a filter — no stored duplication:**
  - `clean analysis substrate` = `WHERE quality='clean'` (what Layer-3 / app consume — replaces `ipo_analysis.csv`)
  - `dirty / quarantine worklist` = `WHERE quality='dirty'` (the cleanup queue; rows PROMOTE to clean when fixed —
    a shrinking set, not a permanent store; the only state transition in the model)
  - `mainboard` / `sme` = `WHERE board='MB' | 'SME'` (materialized for human readability if desired)
  - `longterm` / `shortterm` = `WHERE cohort='longterm' | 'boom'`
  - `equity-only` = `WHERE instrument_type='equity'` (for equity-only findings, charter task_10)
  - `combined` = the spine itself (no union needed)
- **clean/dirty quarantine is the curation mechanism:** a row enters `dirty` when any field fails validity (§3) or a
  cross-source check trips; it is PROMOTED to `clean` when the overlay (Cluster-3) supplies a vetted fix. Hand-fixes
  are never lost on re-run because they live in the overlay, not in the file (Cluster-3 owns the replay; this doc
  owns the `quality` partition the overlay flips).

**Why NOT 2 stored masters (rejected):** Option A duplicates the `board` partition between filename and column,
splitting the single source of truth and the ISIN-uniqueness guarantee across two files — a direct north-star
violation. The owner's readable-two-file goal is preserved by C's materialized views without paying A's duplication
cost.

**Testability (architectural, per charter step 6):** N/A for direct predicate — validated by schema cross-check
and a walkthrough against real rows: today's `ipo_analysis.csv` (2,384 rows) ALREADY is effectively "one spine"
(it carries `board`-equivalent `type`, `cohort`, `instrument_type` as columns), while `mainboard.csv`/`sme.csv`
are the thinner split. So Option C describes the system that *already half-exists*; the change is to make the
substrate the declared spine, regenerate the two masters as views, and add `quality`. The 2,329 equity /
55 non-equity and 913 MB / 1,471 SME / 1,357 boom / 1,027 longterm splits all reduce to single-column filters on
the spine — verified those columns exist and partition cleanly.

---

## 6) FUTURE-UNIVERSE SEAMS (design-open, NOT built)

The model must let (a) **non-IPO listed stocks** and (b) **live/daily price data** slot in LATER without
restructuring (charter §10). The seams, reserved now, built later:

### 6.1 `universe_type` seam (non-IPO stocks)
- Add `universe_type ∈ {ipo, listed-stock}` as a structural column (§2), default `ipo` for all 2,384 rows today.
- **IPO-only fields degrade to null via the SAME present/absent policy (§3):** a non-IPO row has no
  `issue_price`/`sub_*`/`ofs_*`/listing-day fields → those carry `_prov='na:instrument'`-style absent codes
  (a 5th sibling of the (d) instrument-N/A state, e.g. `na:universe`). No new branching: consumers already
  `WHERE` on structure and treat absent as absent.
- Identity still ISIN-keyed (→ Cluster-2). REIT/InvIT/FPO are the *dress rehearsal*: they already exercise
  "instrument where IPO-offer fields are partly N/A" (39 of 55 carry a market cap, financials N/A **[B task_17
  §3]**), proving the present/absent + instrument-gate machinery handles non-equity/non-pure-IPO rows today.

### 6.2 as-of / frequency abstraction (live/daily data)
- The **as-of class (§4) is the live-data seam.** A daily price refresh writes `current`-class fields with a moving
  `_asof` date; the at-IPO snapshot is frozen and untouched. The outcome matrix (group J) is already entirely
  `current` — it is literally the table that a daily feed updates.
- Reserve a **`frequency`/`source` abstraction in the registry** (→ Cluster-2): each `current` field declares its
  refresh cadence (one-shot at-IPO vs daily/weekly) and source, so a live feed registers like any column (§6.3)
  rather than needing a bespoke ingestion path. The predictor's "only `at_ipo` fields" invariant (§4.3) guarantees
  live data can flow into `current` fields without ever leaking into a feature.

### 6.3 New-column extensibility (the registry — Cluster-2 owns, model relies on)
Adding a column later must be a **registration**, not a bespoke script (charter §8): declare `name · domain ·
applicability(board/instrument/universe) · scope(ipo-only/universal) · source(s)+fallback (→C2) · parser (→C2) ·
as-of class (§4) · validity predicate (→C3) · missing-policy (§3)`. The model guarantees that a newly-registered
column with gaps is handled by the SAME present/absent policy automatically — no special-casing. (The registry
mechanism itself is Cluster-2/charter task_06; this doc specifies the *attributes a column must declare* so the
model's invariants — partition, provenance, as-of — apply to it for free.)

**Design-open, not built:** we reserve `universe_type`, the as-of/frequency registry attributes, and the
`na:universe` absent state NOW (zero cost — they default trivially for today's all-IPO substrate), and defer
non-IPO/live ingestion to a later session.

---

## 7) HOW THE PIECES CONNECT (one-paragraph synthesis)

The **schema (§1)** declares every column; a **tiny structural partition (§2)** — `board`, `instrument_type`,
`universe_type`, `quality`, `cohort` — lets every consumer `WHERE`/`GROUP BY` instead of branching; each
value-bearing column carries a compact **`_prov` code (§3)** that distinguishes source-never-published /
fetch-fail / real-zero / N/A and structurally cannot launder a placeholder; each **time-varying column carries an
as-of class (§4)** so live readings can never leak into at-IPO features; the whole thing lives as **ONE ISIN-keyed
spine with all masters/cohorts/clean-dirty as derived views (§5)**; and `universe_type` + the as-of/frequency
registry attributes **(§6)** reserve room for non-IPO stocks and live data without restructuring. The cleaning
rules that *read* the `_prov` states and *flip* the `quality` partition, and the overlay that makes fixes survive
re-runs, are **Cluster 3**; the per-field source fallback order, the parser/registry mechanism, and ISIN/symbol
identity matching are **Cluster 2**.

---

## OPEN OWNER-QUESTIONS

1. **Physical layout:** adopt Option C (one ISIN-keyed spine as the source of truth; `mainboard`/`sme`/`clean`/
   `dirty`/`longterm`/`shortterm` as derived views, the two masters materialized for readability) — or keep 2
   stored masters (Option A)? (Recommend C; A duplicates the `board` partition + splits ISIN-uniqueness.)
2. **Provenance encoding:** replace the partial 15-column `*_src` scheme with ONE `<field>_prov` code per
   value-bearing field carrying {present-with-source | absent:source | absent:fetchfail | na:instrument}, vs keep
   `*_src` and add a parallel state flag? (Recommend the unified `_prov` — single column, can't launder.)
3. **`quality` partition:** introduce `clean`/`dirty` as the keystone structural column + quarantine view now, so
   suspicion stops being re-implemented per consumer? (Recommend yes — it is what makes the no-branch principle
   real.)
4. **`board` vs `type`:** retire the overloaded `type` (MB/SME) in favor of an explicit `board` structural column,
   migrating consumers — or keep `type`?
5. **As-of class rule:** adopt `at_ipo`/`current` + `_asof` as a model-wide rule for ALL time-varying fields (not
   just market-cap), with the registry recording each field's as-of so "only at_ipo fields enter features" becomes a
   checkable invariant? Which fields in the first wave (market-cap is decided in task_17; what else)?
6. **Schema source of truth:** ratify the §1 end-state schema as the single source of truth and regenerate
   `docs/schema.md` from the registry, retiring the phantom `issue_price_src`/`ticker_src`/`pre_ipo_eps` entries?
7. **`pre_ipo_eps`:** ADD it as a real derived field, or RETIRE it from the documented schema (it is absent today)?
8. **Future-universe seam:** reserve `universe_type` + the as-of/frequency registry attributes + an
   `na:universe` absent state NOW (cheap, default-trivial for today's all-IPO data), confirming we *reserve* but do
   NOT *build* non-IPO/live ingestion this run?
9. **`cohort` as derived vs stored:** `cohort` is a deterministic function of `listing_date` — keep it materialized
   as a convenience column, or compute it only in views (avoid a second place that could drift)?

---

### DONE / SCOPE NOTE
This is a Cluster-1 **design section** (data model), not a per-task `task_x.md`, so the 8-step task checklist does
not apply verbatim; however: ground-truth inputs are cited by file path (§1–§6), counts are verified-this-run or
marked **[B]** with their source task, and seams to Cluster 2 (sourcing/registry/identity) and Cluster 3
(cleaning/overlay/rules) are flagged inline so a later integrator can weave the three clusters without overlap.
**NOT FINAL — owner owns the design.**
