# Target Data-Architecture Design (2026-06-17)

> **STATUS: NOT FINAL — design / think-only.** Per `night_run_2026-06-17_charter.md`. ZERO code, zero
> pipeline changes, zero commits. This document PROPOSES the target data architecture; the **owner decides**.
> It is the synthesized CONVERGENCE of the three cluster design sections —
> `night_run/cluster_1_data_model.md` (schema · structural columns · provenance/missing · as-of · layout ·
> future seams), `night_run/cluster_2_ingestion_extensibility.md` (sourcing+fallback · column registry ·
> identity/matching), `night_run/cluster_3_cleaning_repro_rules.md` (cleaning-rules · overlay · reconciliation
> · applicability · features↔data) — woven into ONE seamless design. Cross-references the clusters left to
> each other are RESOLVED here (the registry's missing-policy/as-of slots point at the §3/§4 definitions; the
> cleaning rules write the §2/§3 partition + provenance; identity is one scheme used by all). Every count is
> inherited from the cited cluster/Group-B task and is read-only-verified there — re-verify before relying.
>
> **North star (charter): CLEAN · EXTENSIBLE · CORRECT** — minimal *structural* (partition) columns, not
> behavioral if/else; single source of truth (no duplication); new columns/stocks/live-data slot in without
> restructuring; correctness over speed; **flag rather than guess, flag rather than clamp**.

---

## 0. DECISIONS NEEDED FROM OWNER (pinned)

Every open owner-question from the three clusters, de-duplicated and grouped by theme. **24 decisions** after
merging recurring items (the three clusters raised ~26 raw; the as-of split, the registry-ownership/missing-
policy-home, and the applicability-register overlaps collapse). Each notes the cluster(s) that raised it and
the recommendation where one exists. **Nothing here is decided.**

### A. Dataset layout & schema (C1)
1. **Physical layout — one spine vs two stored masters.** [C1] Adopt **Option C**: ONE ISIN-keyed spine as
   the single source of truth; `mainboard`/`sme`/`clean`/`dirty`/`longterm`/`shortterm`/`combined` all as
   derived `WHERE`-filter views (the two masters MATERIALIZED for human readability) — vs keep 2 stored
   masters (Option A). *Recommend C; A duplicates the `board` partition between filename + column and splits
   ISIN-uniqueness across two files.* (§5)
2. **`board` vs `type`.** [C1] Retire the overloaded `type` (MB/SME) for an explicit `board` structural
   column, migrating consumers — or keep `type`? (§4, §5)
3. **`cohort` derived vs stored.** [C1] `cohort` is a deterministic function of `listing_date` — keep it
   MATERIALIZED as a convenience column, or compute only in views (avoid a second place that can drift)? (§4)
4. **Schema source of truth.** [C1] Ratify the §3 end-state schema as the single source of truth and
   regenerate `docs/schema.md` from the registry (generated-not-hand-edited, like `MAP.md`), retiring the
   phantom `issue_price_src` / `ticker_src` / `pre_ipo_eps` entries that the doc lists but the substrate
   lacks? (§3.1)
5. **`pre_ipo_eps`.** [C1] ADD it as a real derived field, or RETIRE it from the documented schema (it is
   absent from the substrate today)? (§3.2)

### B. Provenance & missing-data (C1)
6. **Provenance encoding.** [C1] Replace the partial 15-column `*_src` scheme with ONE `<field>_prov` code per
   value-bearing field carrying {present-with-source | absent:source | absent:fetchfail | na:instrument}, vs
   keep `*_src` and bolt on a parallel state flag? *Recommend the unified `_prov` — one column, structurally
   cannot launder a placeholder.* (§6)
7. **`quality` partition.** [C1] Introduce `clean`/`dirty` as the keystone structural column + the shrinking
   quarantine view NOW, so "is this row trustworthy" stops being re-implemented per consumer? *Recommend yes
   — it is what makes the no-branch principle real.* (§4, §5)

### C. As-of semantics (C1 + C3 — same class, merged)
8. **As-of split adoption (the D-3 class).** [C1-Q5 + C3-Q8] Adopt `at_ipo` / `current` + `_asof` as a
   model-wide rule for ALL time-varying fields (not just market-cap), with the registry recording each
   field's as-of class so "only `at_ipo` fields enter the feature set" becomes a checkable invariant — AND
   concretely split `market_cap_cr` into `*_at_ipo_cr` (predictor-bound) + `*_current_cr` (display-only),
   re-binding predictors/migration analysis to `*_at_ipo_cr`? Which fields are in the first wave (market-cap
   decided in task_17 — what else)? (§7)
9. **Source for `market_cap_at_ipo_cr` (boom cohort).** [C3] Chittorgarh KPI (`kpi_market_cap_post_ipo`, after
   value-audit) vs `issue_price × post-issue shares` (the latter BLOCKED on the same missing total-shares-
   outstanding data as EPS-recompute, Q22)? (§7, §8)

### D. Ingestion / column registry (C2)
10. **Registry physical form.** [C2] A declarative config file (`data/registry/columns.yaml`) with named-
    function references vs a typed Python declaration vs a CSV? *Leaning: declarative file so non-coders can
    add a column.* (§9)
11. **Network re-scrape vs permanent NULL for blind residuals.** [C2-Q4] For MB-subscription (NSE cache
    overlaps 0/18 of the MB 0-rows) and the 10 O-4 GMP rows (investorgain cache itself has `gmp_rs=0`):
    approve a network re-scrape, or accept NULL + `source_never_published` as a permanent interim? (Network is
    default-deny.) (§8)

### E. Identity & matching (C2)
12. **Empty-ISIN yfinance corp-action trust.** [C2-Q2] Demote the 354 symbol-only yfinance rows to
    **corroboration-only** (may confirm, never create an adjustment alone), or keep them as primary gap-
    fillers gated by the price-gap arbiter? *The single biggest lever on the over-count class.* (§10)
13. **Date-window slack.** [C2-Q3] How many trading days of pre-`first_trade` slack for a split effective at
    listing? (The 44 bad cases are years off, so a few days is safe — but the exact slack is an owner call.)
    (§10)
14. **Canonical entity-mapping ledger.** [C2-Q5] Eventually adopt an NSE symbol-change ledger (needs a new
    trusted source) to replace the date-window approximation, or is the window-scoped principle the permanent
    design? (§10)

### F. Overlay & reconciliation (C3)
15. **Overlay consolidation.** [C3-Q1] Migrate the three embedded hand-fix catalogs (corp_actions
    `manual_thinktank_audit`+`verification` 39 rows; 88-audit Cat-1 21 splits; `drhp_recovered` 16) INTO one
    unified overlay ledger — vs keep them in separate files with a shared reader? *Recommend consolidate
    (single source of truth).* (§11)
16. **Overlay `op` vocabulary.** [C3-Q2] Confirm the overlay needs `DELETE-EVENT` / `ADD-EVENT` (not just
    `SET`) so a FAKE corp-action can be removed and a MISSING one added — `manual_overrides.csv`'s SET-only
    shape cannot express the ROLEXRINGS triple-split removal. (§11)
17. **Conflict policy when the pipeline value moves.** [C3-Q3] When `v_now ∉ {old,new}` (e.g. a yfinance
    refresh changed a ratio): does the overlay's `new_value` still win automatically (with a reconciliation
    flag), or HOLD the row in dirty-review until the owner re-confirms? *Charter leans "correction wins +
    flag"; confirm.* (§11)
18. **Reconciliation campaign timing & freeze.** [C3-Q4] Run the campaign as the FIRST build action after
    design approval (it STOPS other dev while it runs), accepting the live substrate keeps the 3 fake
    multibaggers (ROLEXRINGS/NPST/CANTABIL) until it completes? (§12)

### G. Cleaning-rules model (C3)
19. **Cleaning-rule default severity.** [C3-Q5] On a validity-rule failure, default to QUARANTINE the whole
    row vs FLAG-ONLY (null the offending cell, keep the row)? *Recommend per-class — cell-local damage →
    FLAG-ONLY; derived-feature contamination → QUARANTINE — but set the DEFAULT for ambiguous cases.* (§13)
20. **Confidence threshold for auto-apply.** [C3-Q6] Auto-apply HIGH + MED and gate only LOW behind owner-Q,
    or auto-apply HIGH only and route ALL MED to the dirty-review worklist for spot-check first? (§13)

### H. Rule-applicability (C2 + C3)
21. **Applicability register home + granularity.** [C3-Q7 + C2-Q6] Formalize the §14 gate AS structured
    fields in `rules/index.md` entries (it is already the de-facto applicability register), or as a separate
    machine-readable table that `rules/index.md` links to? AND is per-column/per-rule applicability keyed on
    `{board, instrument_type, era/cohort, data_quality_tier, min-N}` sufficient, or are finer dimensions
    (exchange, etc.) needed? *Recommend in-place fields (single source of truth).* (§14)

### I. Features ↔ data (C3) and registry capability (C2 + C3)
22. **EPS recompute (A1 vs A2).** [C3-Q9] Will per-year EPS ever feed a feature? If NO → null-and-flag (A2,
    CR-EPS-SHAREBASE) suffices as a pure data fix. If YES → recompute on a constant share base (A1) — BLOCKED
    on total-shares-outstanding data not in the substrate (same gap as Q9). (§15)
23. **Future-universe seam — reserve now.** [C1-Q8] Reserve `universe_type` + the as-of/frequency registry
    attributes + an `na:universe` absent state NOW (cheap, default-trivial for today's all-IPO data),
    confirming we *reserve* but do NOT *build* non-IPO/live ingestion this run? (§16)
24. **Cross-field predicate support.** [C3-Q10 + C2-Q1 slot] Confirm the column registry's validity-predicate
    facility accepts MULTI-COLUMN predicates (needed for O-3 tranche-vs-total 32+218 rows, CR-EPS-SIGN,
    CR-SF-DENOM, CR-DATE-ORDER) — not just `f(this_cell)`. *Without it those classes fall through.* (§9, §13)

> **Resolved by integration (no longer owner-questions):** C2-Q7 ("where do `missing_policy`/`as_of`
> definitions physically live") — they are OWNED by the data model (§6 provenance, §7 as-of) and the cleaning
> layer (§13 validity), and merely REFERENCED by the registry's slots; this document makes that the single
> source of truth, so it is no longer an open question, only a stated boundary (§9).

---

## 1. WHAT THIS DESIGN IS (one connected system)

The architecture is one object viewed from three angles. The **data model** declares every column, partitions
rows with a tiny structural set, and gives each value a non-lying provenance + as-of class. **Ingestion** is
the generic machine that fills those columns from an ordered, declared source list, keyed by one identity
scheme. **Cleaning + reproducibility** is the pipeline that routes suspect rows, captures hand-fixes in a
replayable overlay, reconciles a fresh rebuild against today's substrate, gates which rule/finding may touch
which row, and traces every feature quirk back to its data root cause.

The connective tissue — the things every angle shares:

```
                         ┌──────────────────────────────────────────────┐
                         │  ONE ISIN-keyed SPINE (single source of truth)│
                         │  + STRUCTURAL PARTITION (board · instrument_  │
                         │    type · universe_type · quality · cohort)   │
                         │  + per-field PROVENANCE code + AS-OF class    │
                         └───────────────┬──────────────────────────────┘
        declares columns ▲               │ filtered into derived VIEWS ▼
   ┌──────────────────┐  │   ┌───────────┴───────────┐   ┌──────────────────────┐
   │ COLUMN REGISTRY  │──┘   │ clean substrate (Layer3)│   │ dirty quarantine     │
   │ (one decl/column)│      │ mainboard/sme/longterm…│   │ (shrinking worklist) │
   └────────┬─────────┘      └───────────────────────┘   └──────────┬───────────┘
            │ fallback walk fills values                            ▲ promote on fix
            ▼                                                       │
   ┌──────────────────┐   ordered/idempotent   ┌──────────────────┐ │
   │ INGESTION + IDENTITY│  overlay replay      │ CLEANING RULES   │─┘
   │ (sources → values)  │◀────────────────────│ + OVERLAY        │
   └──────────────────┘                        │ + RECONCILIATION │
                                               │ + APPLICABILITY  │
                                               └──────────────────┘
```

The same five structural columns drive partitioning (model), source/validity gating (ingestion), cleaning-
rule routing (cleaning), and finding applicability (analysis). The same per-field provenance code that the
model defines is what the fallback walk writes, what the cleaning rule stamps, and what the consumer reads.
There is no parallel scheme anywhere — that is the single-source-of-truth north star made physical.

Order of the design below: **schema drift → end-state schema → structural columns → provenance/missing-policy
→ as-of semantics → dataset layout → sourcing & fallback → column registry → identity & matching →
cleaning-rules model → reproducibility overlay → reconciliation campaign → rule-applicability → features↔data
→ future-universe seams**.

---

## 2. GROUND-TRUTH: THREE SCHEMAS IN PLAY (the drift to resolve)

Before the end-state, the as-found reality (verified read-only against `data/master/ipo_analysis.csv`,
2,384 rows, `as_of` 2026-06-06 per `substrate_meta.json`; counts marked **[B]** are inherited from the
Group-B task files):

- The actual substrate `ipo_analysis.csv` has **220 columns** (header dumped this run).
- `docs/schema.md` documents the `mainboard.csv`/`sme.csv` master shape (~99 cols) — a NARROWER, DIFFERENT
  file. It is the wrong source of truth: it documents `issue_price_src`, `ticker_src`, `pre_ipo_eps` — **all
  absent** from the substrate **[B task_19 §3b-i / task_17]** — and OMITS `cohort`, `instrument_type`, the
  entire market-cap family, the `kpi_*` family, `name_at_ipo`, `official_isin_name`, the ~110-column
  returns/alpha/MFE/MAE matrix, the data-quality columns, and `xcheck_flags` **[B task_17 §2]**.
- The two master files THEMSELVES diverge from the substrate (they lack `cohort`, `instrument_type`,
  `market_cap_*`, the outcome matrix, `data_quality_*`).

So today there are **three schemas with no single declared truth** (two thin masters + the fat substrate).
**Resolution:** the §3 end-state schema, declared in the column registry (§9), becomes the single source of
truth; `docs/schema.md` is regenerated from it, never hand-maintained. (Owner-decision 4.)

---

## 3. TARGET END-STATE SCHEMA

Notation per column: **applicability** = `both` (MB+SME) · `MB` · `SME`; **scope** = `ipo-only` (degrades to
null for future non-IPO rows, §16) vs `universal`. Time-varying fields carry an **as-of** marker (§7).
`[+]` = ADD · `[~]` = present but needs a model change · `[-]` = RETIRE/quarantine · plain = keep.

**A. Identity & classification (universal, partition-bearing — §4)**
| column | appl | scope | note |
|---|---|---|---|
| `isin` | both | universal | PRIMARY KEY (charter non-negotiable) |
| `company_name`, `name_at_ipo`, `official_isin_name` | both | universal | `name_at_ipo` is an at-IPO snapshot (§7); names blank on some rows **[B task_19]** |
| `board` `[+]` | both | universal | STRUCTURAL partition (§4); replaces overloaded `type` |
| `instrument_type` | both | universal | equity:2329 · fpo:38 · reit:9 · invit:8 (verified) — STRUCTURAL (§4) |
| `universe_type` `[+]` | both | universal | ipo / listed-stock seam (§16); default `ipo` today |
| `quality` `[+]` | both | universal | clean / dirty partition (§4) |
| `cohort` | both | universal | boom:1357 · longterm:1027 (verified) — derivable from `listing_date`; §4 |
| `nse_symbol`, `bse_script_code`, `ticker_ns`, `ticker_bo` | both | universal | exchange identity (§10) |
| `type` `[-]` | both | — | overloaded (MB/SME); SUPERSEDED by `board`. Retire after migration |
| `exchange`, `listing_at`, `chittorgarh_id/_slug/_url` | both | universal | provenance/identity housekeeping (§10) |
| `industry`, `sector`, `broad_sector` | both | ipo-only? | sector taxonomy; SME-boom sector gaps (24 rows) |
| `incorporation_year`, `age_at_ipo_years` `[+ if missing]` | both | ipo-only | verify presence (§10) |

**B. IPO offer mechanics (ipo-only; null for non-IPO rows in §16)** — `issue_price`, `issue_price_adj` (§7
adjusted), `price_band_low`, `price_band_width_pct`, `book_built`, `pricing_method`, `face_value`,
`lot_size_shares`, `min_investment_rs`, `issue_amount_cr`, `issue_size_cr`, `fresh_issue_cr`, `ofs_cr`,
`ofs_pct`, `anchor_allocation_cr`, `issue_expenses_cr`. appl `both`.
- `min_investment_rs` `[~]`: 18 zeros are RECOVERABLE = `lot_size_shares × issue_price` **[B task_19 §6]** → a
  derived-recovery rule (§13 CR-MININV-RECOVER), not a raw null.
- For FPO/REIT/InvIT some are semantically N/A (no fresh/OFS split) → provenance state `na:instrument` (§6).

**C. Timetable (ipo-only)** — `open_date`, `close_date`, `listing_date`. appl `both`. `listing_date` anchors
`cohort` and as-of cut-offs (§7).

**D. Demand signals (ipo-only)** — `sub_qib_x`, `sub_nii_x`, `sub_retail_x`, `sub_total_x`, `sub_*_cr` (4),
`gmp_pct`. appl `both`, but:
- `sub_qib_x` `[~]`: SME `==0` is REAL (no QIB tranche) — 314 SME rows; MB `==0` (27 rows) is masked-missing
  **[B task_19 §6]**. The `board` partition (§4) disambiguates — a structural column replacing an if/else.
- `gmp_pct` `[~]`: pre-2023 SME = source-never-published (state a), not zero **[B task_19]**.
- **Cross-field invariant:** `sum(tranches) ≈ sub_total_x` — 32 rows violate (tranches 0, total>0); 218
  partial **[B task_19 §3b-ii]** → a multi-column validity predicate (§6/§13, owner-decision 24).

**E. Ownership (ipo-only)** — `promoter_pre_issue_pct`, `promoter_post_issue_pct`, `promoter_pre_shares`,
`promoter_post_shares`. appl `both`. At-IPO by nature (§7) — keep, mark as at-IPO snapshots.

**F. People / intermediaries (ipo-only)** — `lead_manager`, `market_maker` (appl `SME` — MB IPOs have no
market maker; another board-gated field encoded by partition not branch), `registrar` `[+ if missing]`,
`objects_of_issue`.

**G. Listing-day outcomes (ipo-only, time-anchored)** — `listing_open` (raw, Chittorgarh), `adj_listing_open`,
`adj_listing_close`, `adj_listing_gain_open/close`, `listing_high/low/close`, `listing_metrics_status`.
- `listing_open` `[~]`: raw=0 on INE0N0Y01013 but `adj_listing_open=30` correct; `listing_metrics_status='ok'`
  mislabeled (one-off, count=1) **[B task_19 §3c]**. Keep raw + adjusted both (CLAUDE.md convention).

**H. Financials — 3yr block + normalized pre_ipo_* (ipo-only)** — `net_sales_yr{1,2,3}`,
`operating_profit_yr*`, `pat_yr*`, `eps_yr*`, `shareholder_funds_yr*`, `borrowings_yr*`, `total_assets_yr*`,
`operating_cf_yr*`, `pe_ratio`, `pat_ttm_cr`, `sales_ttm_cr`, `eps_ttm`, `roe_pct`, `roce_pct`, `debt_equity`,
`sales_cagr_3y`, `pat_cagr_3y`, the `pre_ipo_*` normalized family + derived margins. appl `both`, **equity-only
for analysis**.
- The 8 REIT/InvIT `net_sales_yr3==0` rows are state-`na:instrument`, not zeros **[B task_19 §5]** → gated by
  `instrument_type` (§4), not a financial-specific flag.
- `borrowings_*==0` is REAL (debt-free) — must NOT be nulled **[B task_19]**.
- `pre_ipo_eps` `[-]`: documented in schema.md but ABSENT — retire from the doc or ADD as a real derived
  field (owner-decision 5).

**I. Market-cap family (universal-ish; the as-of poster child) [B task_17]**
- `market_cap_at_ipo_cr` `[+]` (at-IPO snapshot; primary src `kpi_market_cap_post_ipo` after value-audit,
  fallback `issue_price × post-issue shares`) — the analog/predictor feature.
- `market_cap_current_cr` `[~]` + `market_cap_current_asof_date` `[+]` (live Screener cap; display only; never
  a predictor input — heals D-3 leak).
- `market_cap_class` `[~]`: single declarative derivation over the row's AUTHORITATIVE cap (at-IPO for
  equity-IPO; current for already-listed), null on null/0 (fixes the O-15 `0→micro` lie, 7 rows).
- `kpi_market_cap_post_ipo` `[~]`: the existing at-IPO source — keep as input, value-audit first (≥1 gross
  parse error, HDFC AMC INE127D01025 = 7.8cr) **[B task_17 §3]**.

**J. Returns / outcomes (ipo-only today; universal once live-prices flow, §16)** — the ~110-column matrix:
`return_from_issue_*`, `return_from_listing_*`, `alpha_*`, `alpha_sc_*` across 10 horizons; `mfe_*`/`mae_*` +
`_lst_` variants; `days_to_mfe/mae/breakeven_*`; `max_gain_pct`, `max_drawdown_*`, `all_time_high/low`,
`current_price`, `current_return_from_issue`, `outcome_class`, `volatility_annual`, `median_daily_turnover_inr`,
`circuit_lock_frac`, `liquidity_flag`, `delisted`, `delist_reason`, `n_days_history`, `price_source`,
`has_price_history`. appl `both`. **Inherently current/live (as-of = current, §7)** — the future seam where
daily-refreshed listed-stock data lands (§16). `current_price`/`current_return` carry an implicit as-of date
to be made explicit.

**K. Structural & provenance (universal; the model's spine)** — `quality`, `board`, `universe_type`,
`instrument_type`, `cohort`, the `*_prov` provenance codes (§6), `data_quality_score`, `data_quality_tier`,
`confidence`, `confidence_reason`, `isin_xchg_check`, `name_isin_check`, `ticker_needs_review`, `xcheck_flags`.
- Today's 15 `*_src` columns **[B task_19 §3b-i]** are SUBSUMED by the unified `*_prov` scheme (§6).

**Net ADD / RETIRE summary:**
- ADD: `board`, `quality`, `universe_type`, `market_cap_at_ipo_cr`, `market_cap_current_cr` + `_asof_date`,
  the unified `*_prov` codes, per-field `_asof` markers on time-varying fields, `registrar`/`age_at_ipo_years`
  if absent.
- RETIRE/replace: `type` (→ `board`), the 15 partial `*_src` (→ `*_prov`), schema.md's phantom
  `issue_price_src`/`ticker_src`/`pre_ipo_eps`.

---

## 4. STRUCTURAL COLUMNS (minimal — partition, not behavior)

The north star forbids behavioral if/else sprawl. The lever is a TINY set of STRUCTURAL columns that
*partition* rows; every downstream consumer then `GROUP BY` / `WHERE` instead of branching. A structural
column answers "**which kind of row is this?**"; a behavioral flag answers "**should the code do X here?**" —
we keep only the former.

**The minimal structural set (5 columns):**

| column | values (verified) | partitions | replaces the branch… |
|---|---|---|---|
| `board` | `MB` (913) / `SME` (1471) | mainboard vs SME analysis & gating | `if is_sme: market_maker…; if MB: no QIB-zero…` |
| `instrument_type` | equity:2329 / fpo:38 / reit:9 / invit:8 | equity vs FPO/REIT/InvIT | `if reit/invit: skip financials` → `WHERE instrument_type='equity'` |
| `universe_type` `[+]` | ipo (all today) / listed-stock (future) | IPO vs non-IPO stock | future `if not ipo: skip offer fields` |
| `quality` `[+]` | clean / dirty | trusted vs quarantined rows | `if row_is_suspect: exclude…` scattered everywhere |
| `cohort` | boom:1357 / longterm:1027 | regime/era for validation | `if listing_date < 2020: ...` |

**Why these and no more:** they are orthogonal facts about the row's identity (`board`/`instrument_type`/
`universe_type` intrinsic; `quality` a curation state; `cohort` a deterministic function of `listing_date`).
They COLLAPSE scattered conditionals into `WHERE`/`GROUP BY`: the SME-vs-MB `sub_qib_x==0` disambiguation (314
SME real vs 27 MB bug **[B task_19]**) → `WHERE board='SME'` vs `'MB'`; "equity-only findings must not run on
NCD/REIT/InvIT" (charter task_10) → `WHERE instrument_type='equity'`; Layer-3 "exclude unreliable rows" →
`WHERE quality='clean'`. **`quality` is the keystone of the no-branch principle** — clean = the analysis
substrate by construction; dirty = the cleanup worklist; promotion (dirty→clean) is the only state
transition, and no consumer re-derives "is this row trustworthy."

**What is NOT structural** (stays a value/provenance column, consumers may filter but it is not the spine):
`outcome_class`, `liquidity_flag`, `data_quality_tier`, `confidence` — graded or behavioral-adjacent;
promoting them to partitions would re-introduce branching. **Present/absent is NOT structural** — it is
per-field provenance (§6); we do NOT add one boolean partition per field.

`board` + `instrument_type` + `universe_type` + `quality` + `cohort` = the entire structural partition.
Everything else is a value or a provenance code.

---

## 5. DATASET LAYOUT (re-derived; the 2-master leaning challenged)

The charter's leaning is **2 stored masters (`mainboard`, `sme`) + derived views**. Steelman, alternative,
recommend.

**Option A — 2 stored masters, shared schema; views derived.** *Steelman:* matches the owner's "2 base files,
others are scripts" mental model; each file small/human-readable; board implicit in the filename. *Cost
(correctness/clean):* `board` is encoded TWICE — structural column AND file split — duplicating the partition
and inviting drift (a row could be in `sme.csv` with `board='MB'`). Every cross-board view UNIONs two files;
every schema change touches two; ISIN uniqueness must be enforced ACROSS two files. It fights §4: if `board`
is a real structural column, the file split is redundant.

**Option B — ONE physical master keyed by ISIN, `board` a column; MB/SME/cohort/clean/dirty all derived.**
*Steelman:* ISIN is THE primary key; uniqueness enforced in ONE place. `board`/`instrument_type`/
`universe_type`/`quality`/`cohort` are columns (§4), so EVERY view is a pure `WHERE`. One schema, one
registry, one place to add a column. The maximal expression of single-source + minimal-flags. *Cost:* the
file is wide (220→~240 cols) and large; "open in a spreadsheet and eyeball SME" is less immediate.

**Option C — internal spine + 2 materialized masters (hybrid).** One ISIN-keyed spine (source of truth for
storage/registry/overlay), with `mainboard.csv`/`sme.csv` MATERIALIZED as derived views for human convenience
(regenerated, never hand-edited). Gets B's single-truth for the pipeline AND A's two-file ergonomics — the
charter's open sub-design (b).

**Recommendation (NOT FINAL): Option C physical, Option B logical.** (Owner-decision 1.)
- **Single source of truth:** ONE ISIN-keyed spine holds every row + full schema + provenance + as-of. ISIN
  uniqueness, the column registry (§9), and the overlay (§11) all bind to this one object.
- **Everything else is a derived VIEW (a filter — no stored duplication):**
  - `clean analysis substrate` = `WHERE quality='clean'` (what Layer-3 / app consume — replaces `ipo_analysis.csv`)
  - `dirty / quarantine worklist` = `WHERE quality='dirty'` (cleanup queue; rows PROMOTE to clean when fixed —
    a shrinking set, the only state transition; hand-fixes live in the overlay, never the file, so they are
    never lost on re-run — §11 owns replay, this section owns the `quality` partition the overlay flips)
  - `mainboard` / `sme` = `WHERE board='MB' | 'SME'` (materialized for readability)
  - `longterm` / `shortterm` = `WHERE cohort='longterm' | 'boom'`
  - `equity-only` = `WHERE instrument_type='equity'` (charter task_10)
  - `combined` = the spine itself (no union)

**Why NOT 2 stored masters:** Option A duplicates the `board` partition between filename + column and splits
ISIN-uniqueness across two files — a direct north-star violation. The owner's readable-two-file goal is
preserved by C's materialized views.

**Testability (architectural):** N/A for a direct predicate — validated by schema cross-check + a walkthrough
against real rows: today's `ipo_analysis.csv` (2,384) ALREADY is effectively "one spine" (it carries
`type`/`cohort`/`instrument_type` as columns), while `mainboard.csv`/`sme.csv` are the thinner split. Option C
describes the system that *already half-exists*; the change is to declare the substrate the spine, regenerate
the two masters as views, and add `quality`. The 2,329 equity / 55 non-equity, 913 MB / 1,471 SME, 1,357 boom
/ 1,027 longterm splits all reduce to single-column filters (those columns verified present + partitioning
cleanly).

---

## 6. MISSING-DATA POLICY + PRESENT-VS-ABSENT (the I1 root fix)

This is the model's correctness core. Grounded in `task_19_returns_i1.md`.

### 6.1 The problem, precisely
I1 is a **2-layer defect, not a loader bug [B task_19 §3a]**: (1) the SOURCE emits a placeholder `0`
(sharescart prints `0x` subscription when uncaptured) — verified **132 raw source-zeros** in
`data/raw/*_events.csv`; (2) an enrich/backfill step LAUNDERS it (`'0'` is a truthy non-empty string → copied
through AND stamped with a real provenance). Verified: **all 124 `sub_total_x==0` substrate rows carry
`sub_total_x_src='sharescart'`** — the provenance layer actively asserts the fake zero is genuine (same at the
10 `gmp_pct==0` rows, `_src ∈ {ipocentral, websearch}`).

So a value of `0` / `""` / blank today conflates FOUR distinct truths and the consumer cannot tell them apart:

| state | meaning | example (verified [B]) |
|---|---|---|
| **(a) source-never-published** | the source never offered this field for this row/era | pre-2023 SME `gmp_pct`; 1129 `sub_total_x` blanks |
| **(b) fetch/parse-fail OR source-placeholder** | we tried and failed, or the source printed a placeholder | 124 `sub_total_x=0`; 7 `market_cap_cr=0`; 18 `min_investment_rs=0` |
| **(c) real zero** | the value genuinely IS zero | 725 `ofs_cr=0` (fresh-issue-only); debt-free `borrowings=0` |
| **(d) N/A for instrument** | the metric doesn't apply to this instrument type | 8 REIT/InvIT `net_sales_yr3=0` |

A blanket `0→NaN` is WRONG (it destroys the 725 real `ofs_cr=0` rows); a field-blind approach can't separate
(b) from (c). The fix is **field-aware validity routing + a 3(+1)-state present/absent encoding**.

### 6.2 The compact provenance encoding (NOT one boolean per field)
The existing `*_src` scheme is the right *idea* but (i) present on only **15 of 220 columns** (among I1 fields
only `sub_total_x` and `gmp_pct` have it **[B task_19 §3b-i]**) and (ii) it LIES (stamps a real source on
placeholders).

**Proposed: ONE `<field>_prov` code column per value-bearing field, replacing `*_src`** (owner-decision 6) —
a single compact categorical carrying BOTH the present/absent state AND (when present) the winning source:

```
<field>_prov  (one small categorical / packed code per value-bearing field)
   PRESENT states (value trusted):   "<source>"          e.g. chittorgarh | sharescart | screener | derived | overlay
   ABSENT  states (value is null):   "absent:source"     (a) source-never-published
                                     "absent:fetchfail"  (b) we tried/failed OR source placeholder
                                     "na:instrument"     (d) N/A for this instrument_type
                                     "na:universe"  [+]  N/A for this universe_type (future non-IPO — §16)
   REAL-ZERO is NOT an absent state: value=0, prov="<source>"   (c) — a present, trusted zero
```

Key properties:
- **One column per field, not one-boolean-per-state.** A 7-field I1 footprint costs 7 `_prov` columns total,
  not 7×4 booleans. (Impl may bit-pack a global provenance vector per row — a registry impl detail, §9; the
  *model* is "one code per field".)
- **It cannot lie.** A value that fails its validity predicate is routed to `absent:fetchfail` and gets NO
  source tag — laundering is structurally impossible because earning a source tag REQUIRES passing validity.
  This is the "validity gate before stamping, at every stamp site" rule **[B task_19 proposal #4]**, expressed
  in the data model rather than per-script.
- **Real zero is first-class** ((c) = `value=0` WITH a present source tag). **Blanks are disambiguated too**:
  today a blank + empty `_src` conflates (a) and (b) **[B task_19 §5]**; `_prov` records `absent:source` vs
  `absent:fetchfail` for blanks, not only for zeros.

### 6.3 Validity routing — the contract (the rules themselves are §13)
The encoding here is CONSUMED by per-field validity predicates that decide (b) vs (c). The *predicates
themselves are the cleaning-rule content of §13* (this resolves the cross-reference the clusters left: C1
defined the contract, C2's registry `validity_check` slot is the declaration point, C3 authors the logic).
Each value-bearing field declares a validity predicate in the registry (§9); at assemble time a value failing
it is routed to `absent:fetchfail` (null + `_prov`), never silently kept as 0. Seeds, verified with **0
over-catch [B task_19 §6]**:
- `sub_total_x==0` on a LISTED row → (b) — 124 rows (a listed IPO cannot have 0× subscription).
- `sub_qib_x==0`: `board='SME'` → (c) real (314); `board='MB'` → (b) (27) — **board partition drives it (§4)**.
- `min_investment_rs==0 ∧ lot×price>0` → recover (derived), not null — 18 rows.
- `market_cap_cr==0` on a listed row → (b) — 7 rows; class→null.
- `net_sales_yr3==0`: `instrument_type∈{reit,invit}` → (d) (8); else equity → (b) (5, two need a per-row check).
- `ofs_cr==0`, `borrowings_*==0` → ALWAYS (c) — never touch.
- **Cross-field:** `sum(tranches)≉sub_total_x` → route tranche cells to (b) (32+218 rows) — the registry must
  support multi-column predicates **[B task_19 §3b-ii]** (owner-decision 24).

This is the SINGLE root fix for I1: it dissolves the 0-vs-missing ambiguity into an explicit, compact,
non-lying per-field code, applied uniformly via the registry — no per-consumer "is this 0 fake?" re-implementation.

---

## 7. AS-OF SEMANTICS (a CLASS, not one instance)

The D-3 market-cap leak is ONE instance of a general class **[B task_17 §1,§9; charter §9]**: any field
scraped "as of now" silently leaks future/post-outcome state into an at-IPO predictor. The migration
analysis's circular rank-IC 0.564 (current cap, grew-into-it, reverse-causation) is a second instance
**[B task_17 §2]**.

**The model rule:** every TIME-VARYING field carries an explicit **as-of attribute** declaring whether it is
an **at-IPO snapshot** or a **current/live reading**, plus an `_asof` date for live readings.

### 7.1 The two as-of classes
- **`at_ipo` (immutable snapshot):** the value as at/around the IPO — the legitimate analog/predictor feature.
  Examples: `market_cap_at_ipo_cr`, `issue_price`, `promoter_*_pct`, the `pre_ipo_*` financials, `name_at_ipo`,
  all offer mechanics. FROZEN once captured; a re-run must reproduce them exactly.
- **`current` (live, dated):** the value as of a scrape date. Display/current-state only; **FORBIDDEN** as a
  predictor/analog/weight input. Examples: `market_cap_current_cr`, `current_price`,
  `current_return_from_issue`, `all_time_high/low`, every `outcome`/`alpha`/`return_*` column. Each carries an
  `_asof` date (e.g. `market_cap_current_asof_date`).

### 7.2 Encoding (cheap, registry-driven)
Two equivalent encodings — pick one (owner-decision 8):
1. **Name convention** (`<field>_at_ipo` / `<field>_current` + `<field>_current_asof`) — explicit,
   self-documenting; already used for `market_cap_*` and `adj_*` listing fields. Recommended for high-risk fields.
2. **Registry attribute** (`as_of: at_ipo | current`) declared once per column, with one global `data_asof`
   date for all `current` fields — compact, no name churn, less self-documenting in the CSV.

**Recommendation:** name-convention for leak-prone fields (market-cap, any future fundamental with both a
TTM-at-IPO and a live value); registry-attribute + global `data_asof` for the uniformly-"current" outcome
matrix. Either way the **registry records the as-of class for every time-varying field** so a predictor build
can mechanically assert "only `at_ipo` fields entered the feature set" — turning D-3 from a latent leak into a
checkable invariant.

### 7.3 Why a class fix, not a market-cap patch
Binding the predictor to `market_cap_at_ipo_cr` fixes D-3 **[B task_17 §7]**, but the SAME discipline must
cover `layer3/forward_test.py` (the OOS harness, an identical leak path **[B task_17 Open-Q2]**) and any
future field with a live reading. Encoding as-of in the model — not remembering it per feature — makes the
leak STRUCTURALLY unable to recur when a new fundamental column is added (§16): a `current` field simply
cannot be selected into an at-IPO feature set. (Concretely for market-cap: split `market_cap_cr` into
`*_at_ipo_cr` (predictor-bound; source per owner-decision 9) + `*_current_cr` (display-only); re-bind
predictors/migration analysis to `*_at_ipo_cr` — this is the data fix for BOTH the D-3 leak and the circular
migration IC, one class, two instances. The per-feature binding list is in §15.)

---

## 8. SOURCING PER FIELD + DETERMINISTIC FALLBACK ORDER

### 8.1 Principle: every field has an ORDERED source list + an explicit "absent" outcome
A field is **resolved by walking an ordered list of candidate sources until one yields a value whose
provenance state is PRESENT** (§6). The walk is deterministic (same inputs → same winner) and declared once in
the registry (§9). When it exhausts without a present value, the field is **NULL with a `_prov` state**
(`absent:fetchfail` if a source was tried and failed/placeholder; `absent:source` if no source covers that
field for that era) — never `0`/`""`. This is the structural cure for I1: the fallback fires on *state ≠
present*, not on a truthy check, so a stored `0` can never block the next source. (The encoding is §6's; this
is the mechanism that consumes it — resolving the C2→C1 cross-reference.)

### 8.2 Source roster (roles only, from `docs/sources.md` + `scrapers/`)
- **Chittorgarh** (SPINE) — identity (ISIN/symbol/bse_code), dates, issue_price, issue_amount, lead_manager,
  market_maker, fresh/OFS, anchor, promoter pre/post, 3yr financials, listing-day OHLC. ISIN authoritative.
- **Sharescart** — boom (2023–25) enrich: subscription ×, GMP, 3yr financials, promoter %, band, lot, min
  inv, listing_open/gain. (Mints the `0`-subscription bug, task_15.)
- **Screener** — financials/KPIs for 2020–22 where Sharescart absent; weekly prices. No ISIN (bridge via ticker).
- **Exchange lists (NSE/BSE)** — authoritative symbol↔ISIN↔name; the identity cross-check.
- **Bhavcopy (NSE/BSE EOD)** — daily OHLC by ISIN/symbol; price backbone + listing-day recovery.
- **Yahoo** — daily OHLC for mainboard (poor SME); symbol-only corp-action feed (the 354 empty-ISIN rows).
- **NSE Public Issues API** — authoritative MB subscription × (2020+). **SME returns 0.00** → NOT a SME source.
- **IPOWatch** — GMP + subscription split incl. SME. Name-slug + listing-date keyed (no ISIN).
- **InvestorGain** — GMP single ₹, symbol/bse-code + listing-date keyed (no ISIN).
- **moneycontrol autosuggest** — ISIN↔ticker BRIDGE only (identity helper, not a field source).
- **Corp-action sources** — `nse_corp_actions:equities/sme` (ISIN-carrying, authoritative) + `yfinance`
  (symbol-only, empty ISIN) → reconciled into `corp_actions_merged.csv` (task_14).
- **Manual overlay catalogs** (the §11 ledger): `manual_overrides.csv` (3 market_maker rows),
  `manual_thinktank_audit`/`verification_2026-05-31` tags in `corp_actions_merged.csv`, 88-audit Cat-1 (21
  split overrides), `drhp_recovered.csv` (16 DRHP financials). **Highest-priority source in the fallback
  order** (an approved hand-fix wins) but conflict-flagged, not silent (§11).
- **Tested & NOT viable** (do not re-add): BSE official IPO API, ipocentral (the O-4 GMP-0 origin), trendlyne,
  moneycontrol financials.

### 8.3 Fallback order per field GROUP (deterministic; grounded in sources.md + task_14/15)
Priority: **approved overlay → exchange-authoritative → primary scraper → secondary scraper →
derived/recovered → NULL+state.** Concrete orders:

| Field group | Fallback order (stop at first PRESENT) | Coverage / notes |
|---|---|---|
| **Identity** (ISIN, nse_symbol, bse_code) | overlay → Exchange lists → Chittorgarh → moneycontrol bridge | ISIN 100% via Chittorgarh; exchange lists cross-check (§10). |
| **Dates / band / min-inv / issue_price / issue_amount** | overlay → Chittorgarh → Sharescart | Chittorgarh spine; Sharescart fills boom band/lot/min-inv. issue_amount '--' from Sharescart → NULL not 0. |
| **Subscription × — MB** | overlay → Sharescart → **NSE Public Issues** → ipowatch | NSE authoritative but cache overlaps 0/18 of MB 0-rows → residual needs re-scrape, else NULL (owner-decision 11). |
| **Subscription × — SME** | overlay → Sharescart → **ipowatch** → *derived from `_cr`* (Option D) | 75/106 SME 0-rows fixable from ipowatch cache; +88 recoverable arithmetically (`prov=derived`). NSE NOT a SME source. |
| **Subscription category split (QIB/NII/RII)** | overlay → Sharescart → NSE (MB) / ipowatch (SME) | gate completeness check to MB (SME QIB=0 legitimate). |
| **GMP** | overlay → Sharescart → **investorgain** → ipowatch → gmp_deep_hunter (≤2022)/gmp_patcher (≥2025) | the 10 GMP-0 rows came via ipocentral/websearch (no in-repo scraper, NOT viable) → NULL + queue a fresh source; investorgain cache itself has `gmp_rs=0` → genuinely (a). |
| **Financials (EPS/sales/PAT/margins)** | overlay (drhp_recovered) → Sharescart (`pre_ipo_*`) → Screener → Chittorgarh 3yr | Screener covers pre-listing FY 2020–22; use `pre_ipo_*` to avoid post-IPO contamination. |
| **Market cap / sector** | (as-of-tagged) source per task_17 | AS-OF hazard (D-3): current cap ≠ at-IPO cap; the registry's as-of slot (§7/§9) is mandatory here. |
| **Corp actions (split/bonus ratio + ex_date)** | overlay → `nse_corp_actions` (ISIN) → yfinance (symbol, corroboration-only — owner-decision 12) | Join + windowing is §10. |
| **Daily prices (OHLCV)** | Bhavcopy (official, ISIN) → Screener → Yahoo | Bhavcopy authoritative incl. SME; Yahoo poor for SME. |

### 8.4 As-of is a SOURCING concern too
Every time-varying field's source declaration names its as-of class (§7), so the fallback walk never mixes an
at-IPO source with a live one. The attribute lives in the registry (§9) and is stamped at ingestion.

---

## 9. THE COLUMN REGISTRY (the extensibility core)

### 9.1 Goal
Today, adding a column means a bespoke `pipeline/03x_*` step with its own scraper call, its own skip-guard
(the I1 bug, replicated in `03c/03d/03e` — task_15 §3.4), and its own ad-hoc parse. **Target: adding a column
= ONE registry entry, no new script.** The pipeline reads the registry and generically (1) resolves the value
by walking the declared sources (§8), (2) parses with the declared parser, (3) applies the declared
missing-policy (§6's 3-state), (4) runs the declared validity-check (routing failures to dirty per §13),
(5) stamps the as-of attribute (§7), (6) restricts the column to the declared datasets. New-column gaps are
then auto-handled by the SAME missing-policy — no special-casing.

### 9.2 Registry SCHEMA (one declaration per column)
Each column is one record (`data/registry/columns.yaml` or a typed table — physical form is owner-decision 10):

| Slot | Meaning | Example |
|---|---|---|
| `name` | canonical column name | `sub_total_x` |
| `dtype` | logical type | `float` |
| `sources` | ORDERED `{source, locator, parser_args}` = the §8 fallback order | `[{sharescart, cell[3]}, {nse_public_issues}, {ipowatch}, {derived: sub_total_cr/issue_size_cr}]` |
| `parser` | named parser (§9.3) applied to each source's raw cell | `parse_num_x` |
| `missing_policy` | a REFERENCE to §6's 3-state policy + the absent outcome | `three_state` (→ null + `_prov`, never 0) |
| `validity_check` | named predicate(s) the value must pass; failure → dirty (§13 acts) — **must accept MULTI-COLUMN predicates** (owner-decision 24) | `in_range(0,5000)`, `cross: x ≈ cr/issue_size` |
| `dataset_applicability` | which datasets/instrument-types/eras apply | `{board:[MB,SME], instrument_type:[equity], era:2020+}` |
| `as_of` | as-of class + date-source (§7) | `at_ipo_snapshot` |
| `provenance_col` | the `_prov` companion (§6 owns the encoding) | `sub_total_x_prov` |
| `key` | which identity key joins this field's source rows (§10) | `isin` / `nse_symbol+listing_date` |

**Boundary (resolves the C2→C1/C3 cross-reference):** the registry's `missing_policy`, `as_of`, and
`provenance_col` slots are *slots that point at the §6/§7 definitions*; `validity_check` is the *declaration
point* a §13 cleaning rule consumes. The registry declares WHERE/HOW; the model owns the encoding; the
cleaning layer owns the logic. There is ONE definition of each, not a parallel one (C2-Q7 thereby resolved —
not an owner question, a stated boundary).

The pipeline has ONE generic resolver consuming this record for every column. The scattered `03c/03d/03e`
skip-guards collapse into the single `missing_policy` slot (kills the 3 duplicated I1 guards — task_15 §7.2).
The existing `<field>_src` columns are the seed of `provenance_col`.

### 9.3 Named parsers (reusable, not per-column)
A small library the registry references by name: `parse_num` (digits→float, `--`/blank → NULL, **never 0** —
fixing the `'0.00x'`→0 mint, task_15 §3.1), `parse_ratio` (split/bonus `X:Y` → factor, **numeric-tolerance**
not exact-float, task_14 USASEEDS), `parse_date`, `parse_pct`, `parse_currency_cr`, `parse_derived(expr)`
(e.g. `sub_total_cr/issue_size_cr`, `prov=derived`). A parser bug is fixed once for every column using it.

### 9.4 WORKED EXAMPLE — "add a new column" (`anchor_lockin_pct`)
The ENTIRE change is one registry record — no new script:

```yaml
- name: anchor_lockin_pct
  dtype: float
  sources:
    - {source: chittorgarh, locator: "detail.anchor_lockin"}   # primary
    - {source: sharescart,  locator: "cells.lockin"}           # fallback
  parser: parse_pct
  missing_policy: three_state           # → NULL + _prov (§6); never 0/""
  validity_check: [ "in_range(0,100)" ]
  dataset_applicability: {board: [MB,SME], instrument_type: [equity], era: 2021+}
  as_of: at_ipo_snapshot
  provenance_col: anchor_lockin_pct_prov
  key: isin
```

On the next run the generic resolver walks chittorgarh→sharescart, parses with `parse_pct`, writes NULL +
`absent:source` for pre-2021/non-equity rows (auto-handled — no special-casing), validity-checks 0–100
(out-of-range → dirty, §13 promotes on fix), stamps `as_of=at_ipo_snapshot`, records the winning source in
`anchor_lockin_pct_prov`. The column appears in the spine; derived views (§5) inherit it for free. **No
bespoke `pipeline/03x` step.**

### 9.5 Testability
N/A as a runnable predicate (architectural). Validated by schema cross-check: the registry SUPERSETS the
existing `<field>_src`/`_prov` columns already in the substrate, and a walkthrough of `sub_total_x` (the I1
column) shows its bespoke `03c/03d/03e` guards reduce to the single `missing_policy=three_state` slot — the
registry expresses the existing pipeline declaratively, then extends it.

---

## 10. IDENTITY & MATCHING (D-1 learnings → a STANDING principle)

### 10.1 ISIN is the primary key; symbol bridges face-value splits; everything is date-scoped
From `d1_join_strategy_2026-06-17.md` + task_14:
- **ISIN is the ONLY automatic join key** for substrate fields. Name-matching never merges — it only flags
  (§10.4). Substrate masters + price files are keyed by the substrate (post-split) ISIN.
- **Corp actions are the documented EXCEPTION** (a face-value split mints a NEW ISIN, so the action sits under
  the OLD ISIN or — for yfinance — under no ISIN). They match by **symbol ∪ substrate-ISIN**. Load-bearing:
  **301 of 449** action-receiving substrate rows reach their actions via SYMBOL ONLY; only 26 via ISIN-only
  (d1 §2). Dropping the symbol bridge loses almost all adjustments — ISIN-only is not viable.

### 10.2 THE STANDING MATCHING PRINCIPLE (promoted from D-1)
> **Corp-action ↔ substrate matching = (symbol ∪ substrate-ISIN), SCOPED by the stock's trading-date window,
> with collisions FLAGGED not guessed.** For each substrate ISIN with a price file:
> 1. Candidate set = `by_isin[isin] ∪ by_symbol[SYMBOL]`, deduped by `(ex_date, ratio_factor)` using a
>    **numeric ratio tolerance** (not exact float — task_14 USASEEDS `1.428571` vs `1.4285714285714286`).
> 2. **Date-window guard (primary collision cure):** admit an action only if its `ex_date` ∈
>    `[first_trade − small_slack, last_trade]`. Out-of-window → DROP from adjustment + flag
>    `corp_action_out_of_window` (never silently apply). Catches **44** wrong-era attachments (37 yfinance, 25
>    rf<1) while keeping all 458 legitimate symbol matches (d1 §2). (KAUSHALYA 0.01 reverse-split would attach
>    to the 2007 infra company via a freed-then-reused symbol — the window guard is what makes the symbol join
>    safe. Slack = owner-decision 13.)
> 3. **ISIN-family preference (secondary, confidence not rejection):** prefer a candidate whose issuer family
>    (`INE`+5-char) matches; an empty-ISIN (yfinance) action is admitted only on date-window strength → set
>    `corp_action_match = isin_family | symbol_in_window`.
> 4. **Window scoped to the symbol-added subset only** (D1-F1): the gate must NOT touch ISIN-matched actions,
>    or it drops ~26 legit pre-coverage splits (ATLANTAA winner→loser; TARIL +1434×).
> 5. **Coverage-END branch** (D1-F2/R11-B2): `ex_date > last_trade` ⇒ gap NOT measurable ⇒ DEFER to override,
>    NOT auto-phantom-drop (else nulls real multibaggers, E2E +74.7×, FORGE). A separate branch from
>    "out of window before listing".
> 6. **Undisambiguable collision** (two in-window candidates with contradictory ratios; or ≥2 issuer families
>    in-window) ⇒ do NOT pick — null the affected metric + raise to the flagged/unresolved set. The standing
>    failure mode for EVERY key, not just corp actions.

This approximates the long-term ideal — a canonical entity-mapping table (ISIN-family ↔ symbol ↔ substrate
row) — from on-disk data (the price coverage window IS the per-entity trading life). The full table needs an
NSE symbol-change ledger the repo lacks (network default-deny) → the eventual target (owner-decision 14); the
window-scoped principle is the buildable design now.

### 10.3 Generalise to ALL multi-source ingestion (the registry `key` slot)
- **ISIN-keyed sources** (Chittorgarh detail, NSE UDiFF bhavcopy, exchange lists) → direct ISIN join.
- **Symbol+date-keyed** (NSE Public Issues, investorgain `nse_sym/bse_code + listing_date`) → bridge
  symbol→ISIN via exchange lists, then confirm with the listing-date window (same date-scoping; a freed/reused
  symbol is rejected if its event date doesn't fall in the row's window).
- **Name+date-keyed** (ipowatch slug + listing-date window) → **flag-for-manual, never auto-merge** (§10.4).
  The window narrows the candidate set; ambiguity → dirty.
- **No-ISIN bridge sources** (screener via ticker, moneycontrol autosuggest) → resolve ISIN↔ticker via the
  bridge, carry ISIN as the key; a failed bridge → `absent:fetchfail`, not a wrong join.

### 10.4 Malformed-key hazards to handle structurally (task_14 ground truth)
- **163 `nse_corp_actions:sme` rows (+1 equities) store a NON-ISIN numeric code in the `isin` column** (NPST
  `409536`, USASEEDS `462637`). They match the substrate by SYMBOL only; any ISIN-keyed dedup/overlay would
  mis-key them. The matcher must detect "isin not in `INE…` form" → treat as symbol-only.
- **354 yfinance rows carry empty ISIN**; **52 match a substrate IPO symbol** — the structural origin of the
  over-counts (ROLEXRINGS ×1000, NPST ×9). Demote-to-corroboration vs keep-as-primary = owner-decision 12.
- **`action_type` corrupted for all 354 yfinance rows** (03l hardcodes `'split'`) — the matcher/registry must
  not key behaviour on `action_type` for empty-ISIN rows.

### 10.5 Identity kept open to the future universe
The identity layer must not assume "IPO". `instrument_type` ({equity, fpo, reit, invit, …}) and a future
`universe_type` (ipo / listed-stock) ride the SAME ISIN key; IPO-only fields degrade to NULL for non-IPO rows
via the registry's `dataset_applicability` + the §6 missing-policy (no special-casing). Live/daily price
ingestion slots in as another ISIN-keyed source with a `frequency` attribute — the matching principle (ISIN
primary, date-scoped) is unchanged (§16).

---

## 11. REPRODUCIBILITY OVERLAY (`pipeline output + ordered overlay = substrate`)

### 11.1 What already exists (the seeds — verified read-only)
- **`data/reference/manual_overrides.csv`** — shape `isin,column,value,reason,date`; **3 rows, all
  market_maker**. Read by `pipeline/09_assemble.py` (L98-112), applied at the END of assemble so a re-run
  reproduces hand-facts (the 2026-06-04 showdown finding: they used to live only in output files and silently
  vanished on re-run). The canonical "cell-override-by-ISIN" overlay and the model for the general design.
- **`data/reference/corp_actions_merged.csv`** — shape `isin,symbol,action_type,raw_subject,ratio_factor,
  ex_date,source`; **1897 rows** (nse:equities 1341, yfinance 354, nse:sme 163, **manual_thinktank_audit 34,
  verification_2026-05-31 5**). Read by `pipeline/07_returns_summary.py` `load_corp_actions()` → keyed by ISIN
  AND symbol, deduped only by `(ex_date, ratio_factor)`. The 34+5 manual tags are an *embedded* overlay inside
  a mostly-scraped file.

Plus the un-formalized catalogs: `unresolved_88_mismatches_audit.md` Category-1 (21 decided-but-unapplied
split overrides WITH ratios), `docs/research/data/drhp_recovered.csv` (16 SEBI-DRHP financials with
`pat_suspect` flags), the DRHP staging. **task_20 proved these are NOT a solved problem:** the Cat-1
corrections ARE in `corp_actions_merged.csv` yet the fake multibaggers persist (the JOIN that consumes them is
buggy), AND commit `e6053e7`'s hand-null of O-3 cells was CLOBBERED by the later `26cd1fd` rebuild (a
non-idempotent rebuild dropped a hand-fix). Today's overlay mechanism fails 4 of the 5 hard parts.

### 11.2 The unified overlay design (built ON the seeds)
**One overlay store, one shape, multiple read-points by phase.** The corp-action manual tags and Cat-1/DRHP
catalogs migrate INTO it (single source of truth — owner-decision 15):

```
OVERLAY ENTRY (one row, append-only ledger):
  key        : { isin (primary) , symbol , ex_date }   ← §10 identity; ex_date for event-overlays
  target     : column  (or action_type for a corp-action event)
  old_value  : the pipeline value this entry overrode at capture (for conflict-detection, §11.3-4)
  new_value  : the corrected value
  op         : SET | DELETE-EVENT | ADD-EVENT | RECOMPUTE   ← so a fake corp-action can be removed, owner-decision 16
  reason     : provenance string (WHY)
  source     : manual_thinktank | drhp_recovered | cat1_88audit | verification_<date> | ...
  confidence : HIGH|MED|LOW   (mirrors the cleaning-rule confidence, §13)
  seq        : monotonic ordering key (§11.3-2)
  date       : capture date
  retired    : bool + retire-reason  (§11.3-5)
```

This single shape subsumes BOTH seeds: a `market_maker` cell-fix = `op=SET`; a fake ROLEXRINGS split =
`op=DELETE-EVENT key=(ROLEXRINGS, ex_date)`; a missing Indiabulls bonus = `op=ADD-EVENT`. The substrate
identity `= pipeline_output ⊕ apply(overlay, ordered)`.

### 11.3 The five hard parts (each solved)
**1) CAPTURE** — every post-pipeline hand-fix becomes an overlay entry (never a direct CSV edit). The cleaning
rules (§13) are the producer: a rule whose action is FIX-VALUE/FLAG-ONLY/QUARANTINE with `owner-decision`
answered emits an entry with its `reason`+`confidence`. The three embedded catalogs migrate IN: the 34
`manual_thinktank_audit` → 34 `ADD/SET`; the 21 Cat-1 splits → 21 `ADD-EVENT` (the one missing — INE399K01017
— stays an OPEN owner-Q, not a silent gap); the 16 `drhp_recovered` → financial `SET` with `pat_suspect`
preserved as `confidence=LOW`. **Nothing hand-fixed lives only in an output file.**

**2) ORDER / SEQUENCING** — entries replay in a deterministic order by `(seq, date, id)`, NOT an unordered
bag (a corp-action `ADD-EVENT` must apply before a returns-recompute consuming it; two entries on one cell →
last-writer-by-seq). Applied at **phase-appropriate read-points** mirroring today's split: corp-action
event-overlays at the `07_returns_summary` phase; cell-value overlays at the `09_assemble` END phase. `seq` is
assigned at capture and stable → reproducible across runs and machines.

**3) IDEMPOTENCY** — applying twice == once. This is the part TODAY FAILS (task_20 §3D: `e6053e7` clobbered by
`26cd1fd`). Fix: overlay application is a **pure function of (fresh pipeline output, overlay ledger)** with no
in-place accumulation — the substrate is always rebuilt from scratch + overlay, never edited and re-saved.
Because each entry carries `old_value`, re-applying is a no-op when the cell already equals `new_value` and can
detect when the pipeline value moved (§11.3-4). A `DELETE-EVENT` is idempotent (deleting an absent event = a
no-op + a conflict flag). The non-idempotent in-place rebuild that re-introduced `0` into O-3 cells is
structurally eliminated.

**4) CONFLICT-DETECTION** — before applying entry E, compare the current fresh value `v_now` vs `E.old_value`:
- `v_now == E.old_value` → normal: apply `new_value` silently.
- `v_now == E.new_value` → the pipeline now emits the right value natively → a **retire-candidate** (§11.3-5):
  apply is a no-op, flag for retirement.
- `v_now ∉ {old,new}` → the underlying pipeline value CHANGED (e.g. a yfinance refresh changed a ratio — the
  ROLEXRINGS mechanism). The correction usually still wins, BUT this is surfaced as a **reconciliation diff**
  (§12) so an obsolete fix gets re-reviewed rather than silently masking newly-correct data — vs HOLD the row
  in dirty-review (owner-decision 17). This is the charter's hard requirement #4, made concrete via `old_value`.

**5) PROVENANCE + RETIRE-ABILITY** — every entry records WHY (`reason`,`source`,`confidence`). When
conflict-detection finds `v_now == new_value`, the entry flips `retired=true` ("pipeline emits natively as of
<run>"). Retired entries stay in the ledger (audit trail / git history is the drift-free record) but no longer
apply — the overlay SHRINKS as the pipeline improves, the same shrink-to-zero discipline as the dirty
quarantine (§13).

### 11.4 Testability
Architectural; validated by walkthrough: (i) the 3 `manual_overrides` rows replay as 3 `SET` entries at the 09
phase, bit-identical to today; (ii) the ROLEXRINGS fake-split is expressible as `op=DELETE-EVENT
key=(ROLEXRINGS, 2025-09-19 & 2025-10-03)` — which today's `(ex_date,ratio_factor)`-only dedup CANNOT express
(it keeps distinct ex_dates), proving the new `op` vocabulary is necessary; (iii) the e6053e7 clobber is
impossible under pure-rebuild because the O-3 null is an overlay entry re-applied on every run, not an in-place
CSV edit.

---

## 12. RECONCILIATION CAMPAIGN (the one-time trust build)

### 12.1 The campaign (charter §B, made concrete)
```
  1. BUILD the overlay   — migrate all hand-fix catalogs into the unified ledger (§11.2):
                           manual_overrides (3) + corp_actions manual (34+5) + Cat-1 (21) + drhp (16).
  2. REGENERATE fresh    — run the full pipeline from CACHED RAW (no live calls — §12.3) → fresh output;
                           apply the overlay (ordered, idempotent) → candidate substrate.
  3. DIFF vs current     — cell-by-cell + row-MEMBERSHIP diff candidate vs today's ipo_analysis.csv.
  4. EVERY mismatch is a BUG — classify each diff:
                           • new-data error  (the fresh pipeline regressed / a buggy join — e.g. D-1)
                           • stale hand-fix  (an overlay entry the pipeline now supersedes → retire, §11.3-5)
                           • silent-drop     (a row that VANISHED — §12.2)
                           • genuine improvement (a real bug the rebuild fixes — expected, must be confirmed)
  5. REVIEW + RESOLVE    — fix the join / retire the entry / restore the dropped row; re-run, re-diff,
                           until the only diffs are intended improvements.
  6. TRUST → LIVE        — only when all diffs resolved + owner-trusted do we declare
                           `pipeline + overlay = substrate` LIVE. Doubles as a full integrity sweep.
```
This STOPS other dev while it runs (charter §B; owner-decision 18). task_20 is the evidence it is needed: the
substrate was rebuilt at `26cd1fd` WITH the corrections present, yet 7 fake multibaggers persist (broken join)
and an O-3 hand-null was reverted (non-idempotent rebuild) — exactly the diff class step 4 surfaces.

### 12.2 Silent-drop is a first-class diff CLASS
Naked `try/except` row-drops (backlog TD-7) make rows vanish non-deterministically — breaking BOTH
reproducibility and completeness. The diff therefore compares **row membership (by ISIN set)**, not just cell
values. A row present today but absent from the fresh rebuild (or vice-versa) is a `silent-drop` diff — it
must surface and be explained, never disappear quietly. (Also why the row-count is "movable" and must be read
from `substrate_meta.json`.)

### 12.3 Fencing the reproducibility breakers (so the rebuild is deterministic)
| breaker | where | fence |
|---|---|---|
| **Live Yahoo calls** | `06_validate_tickers.py` L38 `fetch_chart(ticker,'1mo')` (from `scrapers.yahoo`) | replay from a **pinned snapshot** of the validation pull; the rebuild must NOT hit the network. A yfinance refresh becomes an explicit dated snapshot bump surfacing as a §12 diff, not silent drift. |
| **Scrapers overwrite raw cache** | re-running any scraper clobbers `data/raw/<source>/` | separate **immutable pinned raw snapshots** (the rebuild input) from the live scrape area; the rebuild reads the pinned snapshot. A new scrape is a deliberate, versioned snapshot, diffed via §12. (Directly fixes the ROLEXRINGS mechanism.) |
| **Date/year timebombs** (TD-1) | `01_build_base` `hi=2026` fallback (breaks 2027), chittorgarh `YEARS`, `'2026-27'` FY, `page<=300` | replace hardcoded year/page constants with derived/config values so the SAME inputs produce the SAME output across calendar years — a determinism prerequisite, flagged to the build phase. |
| **Silent try/except drops** (TD-7) | naked `except` in pipeline steps | surfaced via the §12.2 silent-drop diff class as the minimum; ideally narrowed in the build phase so drops are explicit + logged. |

### 12.4 Testability
The campaign IS the test. Acceptance (concrete, falsifiable): after resolution, a fresh
`pipeline-from-pinned-raw + overlay` reproduces the trusted substrate **bit-for-bit on a second run** (proves
idempotency + determinism); the ROLEXRINGS/NPST/CANTABIL returns are corrected (proves the D-1 join fix
landed); the O-3 cells stay nulled across two rebuilds (proves the e6053e7 clobber class is gone).

---

## 13. CLEANING-RULES MODEL (declarative)

### 13.1 The single rule shape (one shape for ALL issue classes)
Every cleaning rule is ONE declarative record with the same slots; issue classes differ only by what they
fill in, never by bespoke code.

```
RULE
  id            : stable identifier (e.g. CR-SUB-ZERO)
  target        : { columns:[...], scope-predicate }
  condition     : a boolean predicate over the row (may be CROSS-FIELD — §13.4)
  action        : ONE of  FIX-VALUE (deterministic recompute) | FLAG-ONLY (null/keep, set provenance, quality
                   unchanged) | QUARANTINE (route row → quality=dirty until resolved)
  confidence    : HIGH | MED | LOW   (drives auto-apply vs propose-only)
  provenance-tag: the §6 state to stamp — (a)/(b)/(c)/(d) + a reason string
  owner-decision: NULL | a pending owner-Q id (rule is PROPOSED until answered)
  applicability : the §14 gate (era / cohort / instrument_type / data_quality_tier / board / min-N)
```

Invariants:
- **Action is the routing verb.** FIX-VALUE → row stays clean, cell replaced + prov=`derived`. FLAG-ONLY → row
  stays clean, cell nulled + prov=(b). QUARANTINE → row leaves clean (`quality=dirty`) + joins the worklist.
  *Clean vs dirty is decided entirely by which action fires.*
- **Confidence governs automation, not truth** (owner-decision 20). HIGH → auto-apply every run. MED →
  auto-apply but list for owner spot-check. LOW or `owner-decision != NULL` → PROPOSED-only (computes the
  verdict, does NOT mutate until the owner answers).
- **Provenance-tag is mandatory §6 vocabulary** — a rule may NEVER invent a new boolean column (the flag-sprawl
  the north-star forbids).
- **No clamping.** A rule may null, recover, or quarantine — NEVER silently winsorize into a plausible band
  (the condemned `np.clip` anti-pattern; task_16 §4 found the scorecard's own `np.clip` masks Indiqube D/E
  −409.5 → debt-score 100, so quarantine must happen UPSTREAM of any consumer's clip — §15).

### 13.2 How a rule routes a row CLEAN vs DIRTY — cell-level vs row-level damage
- A *single bad cell* on an otherwise-good row → `FLAG-ONLY` (null the cell, keep the row clean; usable for
  every feature that doesn't read that cell). E.g. `gmp_pct=0` masked-missing → null `gmp_pct`, prov=(b); the
  row's returns/subscription are fine.
- A *value that contaminates derived features and can't be locally repaired* → `QUARANTINE` until a
  human/overlay supplies the fix. E.g. Ujjivan `pre_ipo_net_sales=18` poisons margin + the validated
  `tiny_sales_lt25cr` flag + analog distance → the whole row is untrustworthy for the quality component, so
  `quality=dirty` until corrected. A quarantined row is PROMOTED back to clean the instant the overlay (§11)
  supplies a value that makes the condition false — the worklist shrinks. (Default for ambiguous cases =
  owner-decision 19.) **`quality` is set by §4; the cleaning rules are the ONLY thing that writes it, and only
  via QUARANTINE.**

### 13.3 Issue-class → rule-shape map (built DIRECTLY on Group B)
Counts are the owning task's reproduced figures (re-verify there).

| id | issue class (Group B) | condition | action | conf | prov | owner-Q? |
|---|---|---|---|---|---|---|
| **CR-SUB-ZERO** | O-2 subscription masked-zero (124 rows) | LISTED AND `sub_total_x==0` | FLAG-ONLY (null) | HIGH | (b) | — |
| **CR-SUB-TRANCHE** | O-3 tranche masked-missing (cross-field) | `sum(qib,nii,retail)≈0` AND `sub_total_x>0` → null tranche CELLS, keep total | FLAG-ONLY | HIGH | (b) | — |
| **CR-QIB-BOARD** | O-3 MB-vs-SME QIB zero (27 MB bug / 314 SME real) | `sub_qib_x==0 ∧ board==MB ∧ listed` | FLAG-ONLY | HIGH | (b) | — |
| | (same column, SME) | `sub_qib_x==0 ∧ board==SME` | NO-OP (real: no QIB tranche) | HIGH | (c) | — |
| **CR-GMP-ZERO** | O-4 GMP masked-zero (10 rows) | listed AND `gmp_pct==0` AND NOT (pre-2023 SME) | FLAG-ONLY | HIGH | (b) | Q-backfill |
| | (pre-2023 SME) | `gmp_pct==0 ∧ era=pre-2023 ∧ board=SME` | FLAG-ONLY | HIGH | (a) | — |
| **CR-MININV-RECOVER** | O-14 min_investment masked-zero (18 rows) | `min_investment_rs==0 ∧ lot>0 ∧ issue_price>0` | **FIX-VALUE** = `lot × issue_price` | HIGH | derived | — |
| **CR-MCAP-ZERO** | O-15 market_cap zero (7 rows) | listed AND `market_cap_cr==0` | FLAG-ONLY (null) + null `market_cap_class` | HIGH | (b) | — |
| **CR-MCAP-ASOF** | D-3 / O-8 as-of leak | `market_cap_cr` is CURRENT cap on an at-IPO-consumed row | split into `*_at_ipo_cr`/`*_current_cr` (§7) | MED | as-of attr | Q-asof |
| **CR-MCAP-ENTITY** | O-12 wrong-entity join (1 row, Bajaj) | `market_cap_at_ipo_cr / issue_size_cr ∉ [1,20]` | QUARANTINE | MED | (b) | — |
| **CR-EPS-SHAREBASE** | O-5/O-7 EPS share-base discontinuity (51/57/95 rows) | implied share-base differs >~50× | FLAG-ONLY (null the non-comparable year) | MED | (a) published-not-comparable | Q-eps |
| **CR-EPS-SIGN** | EPS↔PAT sign break (34 rows) | `sign(eps_*)≠sign(pat_*)` | QUARANTINE | MED | (b) | — |
| **CR-SALES-IMPLAUS** | O-10 tiny-denominator margin (11 rows) | `pre_ipo_net_sales<25 ∧ |implied margin|>80%` | QUARANTINE | MED | (b) | Q-repair |
| **CR-SF-DENOM** | O-9 negative/near-zero equity (19 rows `sf≤0`) | `shareholder_funds_yr3≤0` OR `|sf|` tiny vs pat/borrow | QUARANTINE (the ratio cells) | MED | (b) | — |
| **CR-PE-NEG** | negative P/E (46 rows) | `pe_ratio<0` (loss-maker) | FLAG-ONLY (null) | HIGH | (b) | — |
| **CR-NONEQ-FIN** | O-6 REIT/InvIT in equity table (8 rows) | `net_sales_yr3==0 ∧ instrument_type∈{reit,invit}` | FLAG-ONLY (defer to the §14 instrument gate) | HIGH | (d) | Q-noneq |
| **CR-DATE-ORDER** | O-11 date transposition (3 rows) | NOT (`open≤close≤listing`) where all present | QUARANTINE | HIGH | (b) | — |
| **CR-BAND-INVERT** | O-13 band inversion (1 true) | `price_band_low > issue_price` | QUARANTINE | HIGH | (b) | — |
| **CR-CORP-OVERCOUNT** | D-1 over-adjustment (8 `<Rs1`, 12 dup-clusters) | price-gap arbiter disagrees with applied cumulative factor | FIX-VALUE (collapse) / QUARANTINE if arbiter blind | MED | (b) | Q-corp |
| **CR-CORP-PROTECT** | Cat-2 genuine path (67 ISIN whitelist) | ISIN ∈ Cat-2 whitelist | NO-OP (never synthesize a split) | HIGH | — | — |

Notes that keep this honest:
- **CR-CORP-OVERCOUNT is the hardest** — NOT a single predicate; it delegates arbitration to the price-gap
  detector (task_14 Option A) + §10's symbol∪ISIN window join. When the arbiter is BLIND (empty-ISIN yfinance
  with no own series; coverage starts after ex_date; `ex_date>last_trade`, e.g. E2E/FORGE multibaggers) the
  action is QUARANTINE/defer-to-override — NEVER auto-drop (task_14 R11-B2). CR-CORP-PROTECT (Cat-2 whitelist)
  runs FIRST and vetoes any synthesis on a verified-genuine outcome.
- **Cross-field conditions are first-class** (CR-SUB-TRANCHE, CR-EPS-SIGN, CR-SF-DENOM, CR-DATE-ORDER,
  CR-CORP-OVERCOUNT) — §13.4.
- **No global "0→NaN" rule exists** — task_19 proved it would destroy 725 legitimate `ofs_cr=0` + debt-free
  `borrowings=0`. Every zero rule is field-aware (the (c) real-zero set in task_19 §3b is the do-not-touch set,
  encoded as NO-OP rules).

### 13.4 Cross-field predicates (a registry requirement)
task_19 §3b-ii proved a per-field predicate cannot express O-3 ("tranches sum to ~0 but total is positive", 32
rows; partial-tranche-missing, 218 rows). So the `condition` slot must support **multi-column predicates** —
a constraint Cluster 3 imposes on the §9 registry: the registry's validity-predicate facility must accept
N-column predicates, not just `f(this_cell)` (owner-decision 24).

### 13.5 Worked routing examples (clean vs dirty)
- **INE0QTF01015 Vibhor Steel** — `sub_total_x=0`, listed +181%. CR-SUB-ZERO → null `sub_total_x`, prov=(b).
  Row STAYS CLEAN (cell-level damage → FLAG-ONLY).
- **INE334L01012 Ujjivan** — `pre_ipo_net_sales=18`, margin 983%, fires `tiny_sales_lt25cr` on a multibagger
  bank. CR-SALES-IMPLAUS → QUARANTINE. Promoted back when the overlay supplies the DRHP ~₹1,800cr value.
- **INE0NJ001013 CFF Fluid** — `min_investment_rs=0`, lot 400 × ₹165. CR-MININV-RECOVER → FIX-VALUE 66,000,
  prov=derived. Row STAYS CLEAN (no overlay needed).
- **INE933K01021 Bajaj Corp** — `market_cap_cr=292355` (wrong entity, ~36× too large). CR-MCAP-ENTITY →
  QUARANTINE until the join is fixed/overlaid.

---

## 14. RULE / HYPOTHESIS APPLICABILITY (the data ↔ rule mapping, declarative)

### 14.1 The problem
Two populations must be gated to the right rows: **cleaning rules** (§13 — must not fire where the condition
is genuinely valid) and **downstream hypotheses/findings/score-components** (`rules/index.md` — must not run on
data they were never validated on). A naive "run everything on every row" re-introduces every false-positive
the re-audits found (the global-0→NaN that nukes `ofs=0`; an equity-only finding on a REIT). Applicability is
the gate — and it must be **declarative data**, not scattered `if instrument_type=='reit'` branches.

### 14.2 The applicability vector (attached to every rule AND every hypothesis)
Each rule/hypothesis declares a gate over five structural dimensions — all already columns (or §4-owned), so
the gate is pure data:

| dimension | values | owner | example gate |
|---|---|---|---|
| **instrument_type** | equity / fpo / reit / invit / idr / ncd | §4 / task_05b | equity-only financials & N14 wipeout flags |
| **board** | MB / SME | substrate `board` | QIB-zero rule (SME real, MB bug); anchor finding (MB-only) |
| **era / cohort** | boom (2020-26) / longterm (2006-19) | listing date | subscription/GMP findings (boom-only); pe_vs_sector (no longterm P/E) |
| **data_quality_tier** | high / medium / low | substrate | exclude `low` from optimistic base rates (t7: low-tier wipeout 21-33% vs 6-9%); exclude `unreliable_coverage` from listing-pop |
| **min-N floor** | integer | per-finding | suppress a sector/segment cell below ~30 (n15 floor; T-2c "thin") |

### 14.3 Declarative mapping (built on `rules/index.md`)
`rules/index.md` ALREADY records the applicability verdict for every signal — the de-facto register; this
formalizes it as a machine-readable gate so consumers stop re-deriving it (home/granularity = owner-decision
21). Representative gates:

| logic | applicability gate | source in rules/index.md |
|---|---|---|
| n2-subscription, n3-demand-skew, n6-valuation, pe_vs_sector | `era == boom` | "boom-only"/"single-regime" |
| n5-anchor | `era == boom AND board == MB` | "boom-MB primary (SME anchor thin)" |
| x-nonequity | `instrument_type ∈ {fpo,reit,invit}` — analyzed SEPARATELY, never pooled | "SEPARATE from equity (user decision)" |
| n14 wipeout flags, all financial findings (n7/n8/n13/n15/t9) | `instrument_type == equity` | NCD/REIT contaminate financials (O-6) |
| t7 base rates / optimistic stats | EXCLUDE `data_quality_tier == low` | "excluding them biases optimistic" |
| listing-pop analyses | EXCLUDE `listing_metrics_status == unreliable_coverage` | CLAUDE.md Layer-2 note |
| strat-combined-score | `horizon == 3y` (OOS-validated); 1y display-only | "3-YEAR ranking tool ... NOT a 1-year signal" |
| any cross-regime claim | sign-stable in BOTH `era` cells | validate.py VALIDATED set |

### 14.4 The gate runs in TWO places (and they must agree)
- **At clean time** — a cleaning rule's `applicability` decides whether its condition is even evaluated
  (CR-QIB-BOARD only on MB; CR-NONEQ-FIN only on reit/invit). Mis-gating = the false-positives the re-audits killed.
- **At analysis time** — a finding/score-component's `applicability` decides which substrate rows feed it
  (equity-only findings MUST NOT run on the 8 REIT/InvIT `net_sales=0` rows — gated via `instrument_type`).
**Single source of truth:** the gate is declared ONCE per logic item and read by both cleaner and analyzer —
never re-implemented per consumer.

### 14.5 Testability
`rules/index.md` is the cross-check: every "boom-only/MB-only/separate/not-cross-regime" marker maps to
exactly one gate above (1:1 coverage). Over-catch test: the equity-financials gate drops the 5 big O-6
REIT/InvIT offenders from the equity table — 0 legitimate equity rows lost (the 5 equity shells route to I1,
not the gate).

---

## 15. FEATURES ↔ DATA reverse-map (is each quirk a DATA bug fixable here?)
For every built artifact (predictor / analog engine / scorecard / backtester / findings / weights): is a known
quirk a DATA bug fixable by a §13 rule + §11 overlay — or a genuine modelling limitation no data fix removes?
Grounded in `rules/index.md` + task_16/17/19.

| feature / consumer | known quirk | DATA root cause | fixable here? | fix |
|---|---|---|---|---|
| **predictor analog distance** (`analogs.py` Gower: pe, roe, d/e, margin) | analogs distorted by corrupt fundamentals | O-9 neg-equity ROE/DE (Indiqube 1400% / −409.5), O-10 Ujjivan margin 983%, neg P/E (46) | **YES — data** | CR-SF-DENOM, CR-SALES-IMPLAUS, CR-PE-NEG quarantine/null BEFORE analogs reads them |
| **data-informed weights** (`weights.py` rank-IC) | learned weights polluted by the same fundamentals | same O-9/O-10 cells feed the point-in-time rank-IC | **YES — data** | same rules; corrupt rows quarantined out of the panel |
| **quality scorecard** (`scorecard.py` profitable/ROE/D-E/margin) | `np.clip` MASKS corruption (Indiqube D/E −409.5 → debt-score 100) | O-9 neg-equity reaches `scorecard.quality()` un-quarantined | **YES — data** | CR-SF-DENOM quarantines UPSTREAM of the clip |
| **wipeout-safety (IN-SCORE)** + `tiny_sales_lt25cr` | false-fires on a multibagger bank (Ujjivan) | O-10 implausible `pre_ipo_net_sales=18` (NBFC sales-definition mismatch) | **YES — data** | CR-SALES-IMPLAUS quarantine + overlay DRHP ~₹1,800cr; re-derive the flag |
| **`pre_ipo_net_sales` IC-0.20 at-IPO predictor** | poisoned feature value | same O-10 implausible sales | **YES — data** | same; corrected via overlay |
| **D-3 mcap leak / migration_predictor circular IC 0.564** | predictor fed CURRENT cap → look-ahead | `market_cap_cr` is current cap, NO as-of attribute; same class poisons SME→MB migration | **YES — data (the named as-of class)** | CR-MCAP-ASOF: split `*_at_ipo_cr`/`*_current_cr`; bind predictors to `*_at_ipo_cr` only (§7) |
| **subscription-as-feature** (n2/n3 + low-sub veto candidate) | breaks on the 0-bug | O-2 124 `sub_total_x=0` masked-missing + the `_src` laundering | **YES — data** | CR-SUB-ZERO null + (b); STOP the enrich step stamping a source on a placeholder (§6, multi-site policy) |
| **n14 `declining_pat` flag** | false-fires (no `p1>0` guard, unlike `declining_revenue`) | per-year PAT zeros (pat_yr1 184) read as a real value | **PARTLY** | CR (per-year pat zero → (b)) fixes the DATA half; the missing `p1>0` guard is a FEATURE-code bug for the feature owner — NOT a pure data fix |
| **corp-action fake returns** (ROLEXRINGS +15,272%, NPST +16,127%) | absurd multibaggers in every return-based finding/backtest | D-1 over-count: 3× duplicate split events surviving `(ex_date,ratio)` dedup; pre/post-split ISIN drift | **YES — data** | CR-CORP-OVERCOUNT (price-gap arbiter, `DELETE-EVENT` overlay) + §10 join fix + §12 campaign |
| **EPS-CAGR / EPS-trajectory** (NOT a feature today; `eps_yr*` unread) | share-base discontinuity would corrupt it IF built | O-5 EPS on changing share base (51/57 rows; NOT a ÷1000 parse bug) | **PARTLY** | null-and-flag (CR-EPS-SHAREBASE) is a data fix; a *recompute* on constant share base is BLOCKED on missing total-shares data (same gap as O-12) — owner-decision 22 |
| **liquidity / quality score components** | weight 0 (no signal) | NOT a data bug — IC genuinely flips sign | **NO — genuine** | none; leave display-only |
| **take-profit / stop-loss never beats hold** | a "limitation" | NOT a data bug — the right tail genuinely carries returns | **NO — genuine** | none |
| **strat-combined-score 1y weak / 3y strong** | horizon-specific | NOT a data bug — real OOS result | **NO — genuine** | §14 applicability gate restricts to 3y |

**Verdict:** the corruption leaking into SCORED features (analog distance, learned weights, in-score
wipeout-safety + quality, the IC-0.20 sales predictor, D-3 mcap leak, corp-action fake returns) is
**overwhelmingly DATA bugs** fixable here via §13 + §11 + §12 — task_16's central correction was "scored-feature
corruption, NOT display-only." The non-data residue is small and honest (liquidity/quality have no signal,
no-exit-rule-beats-hold, horizon-specificity) — genuine empirical results no data fix changes (and must not be
"fixed" away). Two are PARTLY data: the `declining_pat` missing guard (feature-code half → feature owner) and
EPS-recompute (blocked on missing total-shares data).

---

## 16. FUTURE-UNIVERSE SEAMS (design-open, NOT built)
The model must let (a) non-IPO listed stocks and (b) live/daily price data slot in LATER without restructuring
(charter §10). Seams reserved now, built later (owner-decision 23):

### 16.1 `universe_type` seam (non-IPO stocks)
- Add `universe_type ∈ {ipo, listed-stock}` as a structural column (§4), default `ipo` for all 2,384 rows today.
- IPO-only fields degrade to null via the SAME present/absent policy (§6): a non-IPO row has no
  `issue_price`/`sub_*`/`ofs_*`/listing-day fields → those carry `na:universe` (the 5th sibling of the (d)
  instrument-N/A state). No new branching: consumers already `WHERE` on structure and treat absent as absent.
- Identity still ISIN-keyed (§10). **REIT/InvIT/FPO are the dress rehearsal** — they already exercise
  "instrument where IPO-offer fields are partly N/A" (39 of 55 carry a market cap, financials N/A **[B task_17
  §3]**), proving the present/absent + instrument-gate machinery handles non-equity/non-pure-IPO rows today.

### 16.2 as-of / frequency abstraction (live/daily data)
- The **as-of class (§7) is the live-data seam.** A daily price refresh writes `current`-class fields with a
  moving `_asof` date; the at-IPO snapshot is frozen and untouched. The outcome matrix (group J) is already
  entirely `current` — literally the table a daily feed updates.
- Reserve a **`frequency`/`source` abstraction in the registry** (§9): each `current` field declares its
  refresh cadence (one-shot at-IPO vs daily/weekly) and source, so a live feed registers like any column rather
  than needing a bespoke ingestion path. The predictor's "only `at_ipo` fields" invariant (§7.3) guarantees
  live data can flow into `current` fields without ever leaking into a feature.

### 16.3 New-column extensibility (the §9 registry, which the model relies on)
Adding a column later = a REGISTRATION, not a bespoke script (charter §8): declare `name · domain ·
applicability(board/instrument/universe) · scope(ipo-only/universal) · source(s)+fallback (§8) · parser (§9) ·
as-of class (§7) · validity predicate (§13) · missing-policy (§6)`. The model guarantees a newly-registered
column with gaps is handled by the SAME present/absent policy automatically — no special-casing.

**Design-open, not built:** we reserve `universe_type`, the as-of/frequency registry attributes, and the
`na:universe` absent state NOW (zero cost — they default trivially for today's all-IPO substrate), and defer
non-IPO/live ingestion to a later session.

---

## 17. HOW THE PIECES CONNECT (one-paragraph synthesis)
The **schema (§3)** declares every column; a **tiny structural partition (§4)** — `board`, `instrument_type`,
`universe_type`, `quality`, `cohort` — lets every consumer `WHERE`/`GROUP BY` instead of branching; each
value-bearing column carries a compact **`_prov` code (§6)** distinguishing source-never-published /
fetch-fail / real-zero / N/A and structurally cannot launder a placeholder; each time-varying column carries
an **as-of class (§7)** so live readings never leak into at-IPO features; values are filled by a **generic
resolver walking the registry's ordered source list (§8–§9)**, joined by **one ISIN-primary, date-scoped
identity scheme (§10)**; the whole thing lives as **ONE ISIN-keyed spine with all masters/cohorts/clean-dirty
as derived views (§5)**. **Declarative cleaning rules (§13)** read the `_prov` states and flip the `quality`
partition; the **ordered/idempotent overlay (§11)** makes hand-fixes survive re-runs; the **one-time
reconciliation campaign (§12)** makes `pipeline + overlay = substrate` trustworthy; the **applicability gate
(§14)** keeps each rule and finding on the rows it was validated for; and the **features↔data reverse-map
(§15)** confirms the corruption poisoning scored features is overwhelmingly fixable at this layer. Finally,
`universe_type` + the as-of/frequency registry attributes **(§16)** reserve room for non-IPO stocks and live
data without restructuring.

---

## 18. IN-THREAD REVIEW FINDINGS (single bounded pass, 2026-06-17)
One review pass by the main thread (per the corrected lean rule: design needs 1–2 bounded reviews, not loop-until-dry).
The design is sound and ready for owner decision; these are REAL gaps to fold in, not blockers. Each is also an
input to the owner decisions in §0.

- **R1 [HIGH · §6] Provenance column explosion vs the "compact" claim.** "One `<field>_prov` per value-bearing field"
  is ~100+ new columns on a 220-col substrate (could ~double width) — in tension with the readability the owner wants.
  §6.2 hand-waves "impl may bit-pack." RESOLVE concretely (e.g. a single packed per-row provenance struct, OR `_prov`
  only on fields that can actually be ambiguous, not real-zero-only ones) — make it an explicit choice under owner-decision 6.
- **R2 [HIGH · §6 vs §0-Q11] State (b) conflates two causes the design itself needs separated.** §6.1 bundles
  "fetch/parse-fail" AND "source-placeholder" into one code `absent:fetchfail` — but owner-decision 11 (network re-scrape
  vs permanent NULL) DEPENDS on that distinction (a re-scrape can cure a fetch-fail, never a source-never-published).
  Either split (b) into `fetchfail` vs `source-placeholder`, or accept Q11 can't be decided per-row. Internal inconsistency.
- **R3 [HIGH · §7/§0-Q9 + §15/Q22] The flagship as-of cure AND EPS-recompute are both BLOCKED on a missing source.**
  `market_cap_at_ipo_cr` fallback (`issue_price × post-issue shares`) and the EPS constant-share-base recompute BOTH need
  **total-shares-outstanding**, which is not in the substrate and not on any sourcing plan; the alternative KPI source has
  gross parse errors (HDFC AMC 7.8cr). So the D-3 leak fix is only PARTIAL until shares-outstanding is sourced. Add it as
  an explicit registry column + sourcing task, or scope the as-of cure to what KPI (post-audit) can populate.
- **R4 [MED · §4/§13] Whole-row QUARANTINE may be too coarse.** 6 CR-* rules quarantine the ENTIRE row for one bad metric
  (Bajaj mcap, Ujjivan sales, EPS-sign, SF-denom, date-order, band-invert) — dropping that row's OTHER good fields
  (returns, subscription, etc.) from the clean substrate. Before committing to binary clean/dirty: quantify how many rows
  each QUARANTINE rule removes, and consider feature-group-scoped quarantine (a row can stay usable for analyses that
  don't touch the bad cell). Ties to owner-decision 19.
- **R5 [MED · §11.3-4] Conflict-detection needs `old_value`, which migrated entries may lack.** The 34+21+16 migrated
  hand-fixes may have no recorded pipeline-value-at-capture → conflict-detection is inert for them until baselines are
  reconstructed (re-derive each entry's `old_value` from the pre-fix pipeline output during the §12 campaign). Add a
  baseline-backfill step to §12 step 1.
- **R6 [LOW · caveat] Counts are draft-grade.** Figures inherited `[B task_*]` rest on Group B drafts whose review loops
  were deliberately stopped (budget) — not fully hardened. "Re-verify before relying" (already stated) should be read as
  "treat counts as draft-grade pending a confirm pass," not as signed-off.

**Net:** no finding overturns the architecture; R1–R3 should be folded into owner-decisions 6/11/9-22 before build,
R4–R5 are build-time refinements. One pass, stopping here (not looping).

---

> **NOT FINAL — proposal for owner approval.** No code, no data, no commits. Counts are the cited cluster /
> Group-B tasks' reproduced figures; re-verify in the owning task before relying. **One bounded in-thread review pass
> is done (§18)** — the loop-until-dry cycle is deliberately NOT run (it's for dirty-data hunting, not design).
> **Consolidated owner-decisions: 24** (§0) + 6 review findings (§18).
