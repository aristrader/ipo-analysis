# Data-Foundation — ARCHITECTURE REFERENCE (what the system IS)
*Consolidated 2026-06-17. Companion to `FOUNDATION_PLAN.md` (the "what & in what order"). This doc = the design
reference: the layers, tables/views, the yaml registries, what sits on top of what, what runs what, and the
cleaning-rule (CR-*) build-spec. Decisions live in the PLAN; this doc describes the target end-state they produce.*

---

## 0. ONE CONNECTED SYSTEM (the idea)
Raw scraped data is **immutable**. On top of it, declared registries (yaml) + authoritative golden reference
files + a corrections overlay are assembled — by a generic pipeline — into **ONE ISIN-keyed spine** (the single
source of truth). Everything else (mainboard/sme/clean/dirty/non-equity/per-pipeline, the schema doc, the rules
index, the lineage diagram) is a **derived view or a generated artifact**. `raw + golden + overlay = substrate`,
recomputed idempotently every run.

---

## 1. THE LAYERS (what's on top of what · what runs what) ← the layer map owner asked for

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ L8  GENERATED ARTIFACTS (never hand-maintained)                                   │
│     schema doc  ← columns.yaml   ·   rules index ← rules.yaml                      │
│     lineage/architecture diagram (P-2) ← registries + golden files                │
├────────────────────────────────────────────────────────────────────────────────┤
│ L7  ANALYSIS (project Layer 2/3) — consumes VIEWS only                            │
│     predictor · backtester · reports · scorecard                                  │
│     rule registry (rules.yaml) gates findings per-IPO; scores trustworthy+relevant │
├────────────────────────────────────────────────────────────────────────────────┤
│ L6  VIEWS (derived, WHERE-filters; materialized where useful)                     │
│     clean · dirty · mainboard · sme · non-equity · cohort · per-pipeline-field    │
├────────────────────────────────────────────────────────────────────────────────┤
│ L5  THE SPINE  (one ISIN-keyed table = single source of truth)                    │
│     all columns + _prov + _asof + 5 structural columns + quality                  │
├────────────────────────────────────────────────────────────────────────────────┤
│ L4  ASSEMBLY PIPELINE (generic; idempotent)                                       │
│     parse → validate(+_prov stamp) → identity-resolve(ISIN-only) →                 │
│     corp-action(golden→arbiter→overlay) → assemble → apply overlay → SPINE        │
├──────────────────────────────┬─────────────────────────────────────────────────┤
│ L3 OVERLAY (corrections)      │ L2 GOLDEN REFERENCE (authoritative)              │
│   one consolidated ledger     │   corp-action events · identity-history ·         │
│   SET/DELETE/ADD/RECOMPUTE    │   Cat-2 do-NOT-correct (67)                        │
│   old_value · conflict policy │   (append-only, overlay-carried)                  │
├──────────────────────────────┴─────────────────────────────────────────────────┤
│ L1  RAW INGESTION (immutable; scrapers fetch raw only, 3-point honesty contract)  │
│     raw source files + fetch-time per value                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ L0  CONTROL PLANE — declarations (yaml) + logic-by-name + validators              │
│     columns.yaml (schema·sources·parsers·validators·as-of·status·_prov)            │
│     rules.yaml (gate·required_fields·properties)   ·   time-partition config       │
│     named-function code registry (parsers/validators/cross-field predicates)       │
│     meta-validators (validate the yaml each run)                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

**What runs what:**
- The **orchestrator** runs L1 scrapers → L4 assembly pipeline → produces L5 spine → derives L6 views → L7 analysis reads views.
- L4 reads its instructions from **L0** (columns.yaml says how to parse/validate/source each column) and pulls from **L2 golden** + **L3 overlay**.
- The **reconciliation campaign** rebuilds L5 from L1+L2+L3 and diffs against the live substrate (every mismatch = a bug).
- The **generators** produce L8 from L0 registries (schema/rules-index/diagram) — so docs never drift.

**Key dependency rule:** nothing in L7 (analysis) runs until the data layer (L0–L6) is complete AND verified (the completion gate).

---

## 2. TARGET SCHEMA (column families; full detail in the registry)
Notation: `[+]` add · `[~]` keep but change model · `[-]` retire. Time-varying fields carry an `_asof` marker.

- **A. Identity & classification (universal, partition-bearing):** `isin` (PRIMARY KEY), `company_name`/`name_at_ipo`/
  `official_isin_name`, **`board`[+]** (replaces `type`[-]), `instrument_type`, **`universe_type`[+]**, **`quality`[+]**,
  `cohort` (config-derived view), `nse_symbol`/`bse_script_code`/`ticker_ns`/`ticker_bo`, `exchange`/`listing_at`/
  `chittorgarh_*`, `industry`/`sector`/`broad_sector`, `incorporation_year`/`age_at_ipo_years`.
- **B. IPO offer mechanics (ipo-only):** `issue_price`(+`_adj`), `price_band_low`/`_width_pct`, `book_built`,
  `pricing_method`, `face_value`, `lot_size_shares`, `min_investment_rs`[~ recover = lot×price], `issue_amount_cr`,
  `issue_size_cr`, `fresh_issue_cr`, `ofs_cr`/`ofs_pct`, `anchor_allocation_cr`, `issue_expenses_cr`.
- **C. Timetable (ipo-only):** `open_date`, `close_date`, `listing_date` (anchors cohort + as-of cutoffs).
- **D. Demand (ipo-only):** `sub_qib/nii/retail/total_x`, `sub_*_cr`, `gmp_pct`. SME `sub_qib_x==0` is REAL; MB==0 is
  masked-missing → `board` partition disambiguates. Cross-field invariant `Σtranches≈sub_total_x` (32+218 violations).
- **E. Ownership (ipo-only, at-IPO):** `promoter_pre/post_issue_pct`, `promoter_pre/post_shares`.
- **F. People (ipo-only):** `lead_manager`, `market_maker` (SME-only — board-gated by partition), `registrar`, `objects_of_issue`.
- **G. Listing-day outcomes (ipo-only, time-anchored):** `listing_open`(raw)+`adj_listing_open/close`,
  `adj_listing_gain_*`, `listing_high/low/close`, `listing_metrics_status`.
- **H. Financials (ipo-only, equity-only for analysis):** `net_sales_yr{1,2,3}`, `operating_profit_yr*`, `pat_yr*`,
  `eps_yr*`, `shareholder_funds_yr*`, `borrowings_yr*`(==0 is REAL debt-free), `total_assets_yr*`, `operating_cf_yr*`,
  `pe_ratio`, `pat_ttm_cr`, `sales_ttm_cr`, `eps_ttm`, `roe_pct`, `roce_pct`, `debt_equity`, `sales_cagr_3y`,
  `pat_cagr_3y`, `pre_ipo_*` family + margins. REIT/InvIT `net_sales==0` = `na:instrument`. `pre_ipo_eps`[-] retired.
- **I. Market-cap family:** `market_cap_at_ipo_cr`[+ planned, BL-1] (predictor input), `market_cap_current_cr`[~]+
  `_asof_date`[+] (display-only — heals D-3 leak), `market_cap_class`[~] (over authoritative cap, null on 0).
- **J. Returns/outcomes (~110-col matrix, inherently current/as-of):** `return_from_issue/listing_*`, `alpha_*`,
  `mfe_*`/`mae_*`(+`_lst_`), `days_to_*`, `max_gain/drawdown`, `all_time_high/low`, `current_price/return`,
  `outcome_class`, `volatility_annual`, `median_daily_turnover_inr`, `circuit_lock_frac`, `liquidity_flag`,
  `delisted`/`delist_reason`, `n_days_history`, `price_source`, `has_price_history`. (The future live-data seam.)
- **K. Structural & provenance (the spine):** the 5 structural columns, the `*_prov` codes (subsume the 15 partial
  `*_src`), `data_quality_score/tier`, `confidence`/`_reason`, `isin_xchg_check`, `name_isin_check`, `xcheck_flags`.

**ADD:** board, quality, universe_type, market_cap_at_ipo_cr(planned), market_cap_current_cr+_asof, unified `*_prov`,
per-field `_asof`. **RETIRE:** `type`→`board`, the 15 `*_src`→`*_prov`, schema.md phantoms (`issue_price_src`/`ticker_src`/`pre_ipo_eps`).

---

## 3. STRUCTURAL COLUMNS (5 — partition, not behavior)
| column | values | partitions | replaces the branch |
|---|---|---|---|
| `board` | MB(913) / SME(1471) | mainboard vs SME | `if is_sme … / if MB …` |
| `instrument_type` | equity(2329)/fpo(38)/reit(9)/invit(8) | equity vs non-equity | `if reit/invit: skip financials` → `WHERE instrument_type='equity'` |
| `universe_type`[+] | ipo (all today) / listed-stock (future) | IPO vs non-IPO | future seam |
| `quality`[+] | clean / dirty | trusted vs quarantined | scattered `if row_is_suspect` |
| `cohort` | boom(1357)/longterm(1027) | era for validation | `if listing_date<2020` |

`quality` is the keystone of the no-branch principle: clean = the analysis substrate by construction; dirty = the
cleanup worklist; promotion (dirty→clean) is the only state transition. **Present/absent is NOT structural** — it's
per-field `_prov` (no boolean partition per field).

---

## 4. PROVENANCE (`_prov`) & MISSING-DATA STATES (the I1 fix)
Each genuinely-ambiguous field has a companion `_prov` column (fully populated; +1 col, only where ambiguity is real).
**5 canonical codes** (the "4 missing-data states" of OD-1 = the rows below minus `derived`):
| state | `_prov` code | numeric cell | retryable |
|---|---|---|---|
| real zero | `present` | `0` | n/a |
| computed | `derived` | value | n/a |
| source never published / source-emitted placeholder | `Missing_data` | NULL | **no** |
| OUR-side fetch/parse failed | `error_out` | NULL | **yes** (refetch worklist) |
| not applicable | `N/A` (`na:instrument`/`na:universe`) | NULL | n/a |
Rules: validate BEFORE stamping `present`; cross-field predicates allowed (Σtranches vs total).
**Refetch-bucket rule (R2):** only `error_out` (our fetch/parse broke) is retryable. A **source-emitted placeholder**
(source returned junk like `0.00x`) is NON-retryable → `Missing_data` (re-scraping the same source can't cure it). This
keeps the refetch worklist from chasing un-curable cells — the distinction owner-decision-11/refetch depends on.

## 5. AS-OF SEMANTICS
Every time-varying field carries `_asof` and a class: **`at_ipo`** (snapshot, predictor-legal) vs **`current`**
(live, display-only). Invariant: only `at_ipo` fields feed the predictor → kills the D-3 market-cap leak class structurally.
**Caveat (R3/G14 — do not overstate):** the as-of *mechanism* is what's done; the at-IPO market-cap *value* is BLOCKED on
`shares_outstanding` (not in the substrate — BL-1). So "leak killed" means the predictor can't see the *current* cap — it does
NOT mean a trustworthy at-IPO cap exists. Until BL-1, the predictor has **no at-IPO market cap** (honestly absent).

## 6. DATASET LAYOUT (one spine + views)
ONE ISIN-keyed spine (L5) = source of truth. `mainboard`/`sme`/`clean`/`dirty`/`non-equity`/`cohort`/per-pipeline =
derived `WHERE`-filter views (L6), materialized where readability helps. Reclassify = change one cell → all views update.
No separate source files, no row-moving.

## 7. COLUMN REGISTRY (`columns.yaml`) + LIFECYCLE
Declarative YAML: per column = name, dtype, ordered sources, parser/validator BY NAME, as-of class, applicability,
`_prov` carrier, status. Logic lives in a named code registry. Meta-validator checks the file each run. **Lifecycle:**
`active` (materialized) / `planned` (stub → backlog, not materialized) / `retired` (reason recorded, never re-added).
The registry IS the schema (generate the schema doc from it).
**Named-parser roster (load-bearing bug-fixes that must survive):** `parse_num` NEVER mints `0` (no value → null, not 0);
`parse_ratio` uses **numeric tolerance** not exact-float equality (USASEEDS `1.428571` vs `1.4285714…`); `parse_derived`
stamps `derived`. These names are referenced from `columns.yaml`.

## 8. IDENTITY & MATCHING
**ISIN = the only auto-join key; names only flag.** Record matched entity id+name on every join (auditable). Symbol/ISIN
changes over time → the **identity-history golden file** (date-windowed; optional future upgrade to an official NSE ledger).
Bajaj-type wrong-entity joins (name-keyed, 36× cap error) → swept out by enforcing ISIN-only joins.
**Malformed-key hazards (carry as build rules — splits_findings.md):** an `isin` not in valid INE… form is NOT a join key →
treat as symbol-only (163 nse:sme rows store numeric codes e.g. NPST `409536`; 354 yfinance rows are empty-ISIN). Do NOT trust
`action_type` for empty-ISIN yfinance rows (`03l` hardcodes `'split'`). Apply a **pre-listing-date filter** to symbol-only
corp-actions (kills reused-symbol hazards: PATANJALI/Ruchi-Soya 2007, ENGINERSIN 1999).

## 9. OVERLAY (corrections) + GOLDEN FILES + CONFLICT
**Overlay:** one consolidated ledger on immutable raw; ops SET / DELETE-EVENT / ADD-EVENT / RECOMPUTE; each fix records
`old_value` + fetch-time. **Conflict (source moved):** still-broken → apply; now-matches → retire fix; moved to a THIRD
value → HOLD for review. **Golden reference files (3, authoritative, append-only, overlay-carried):**
1. **corp-action events** (ISIN, ex-date, ratio, verified) → price adjustment; fill the 4-stock gap.
2. **identity-history** (symbol/ISIN changes) → matching.
3. **Cat-2 do-NOT-correct** (67 verified-genuine crashes) → the corp-action fix never fabricates a split for these.
**Corp-action fallback order:** golden catalog → price-gap arbiter → source-reconcile dedup → flag (never guess).
ISIN-less yfinance = corroboration-only (honored only if arbiter/ISIN-source confirms).

## 10. CLEANING-RULES MODEL + VALIDITY VIEWS
Declarative CR-* rules (see §15) read `_prov`/values and set `quality`/null cells. **Severity per-class:** field-level null
default; whole-row `dirty` only when the error poisons the row. **Auto-apply HIGH only;** MED+LOW → dirty-review worklist
(MED promotes to HIGH once proven). **Validity views:** each pipeline declares `required_fields`; its view keeps rows where
those are valid (data-quality handled here, not as a gate key). **This IS the resolution of R4 (whole-row quarantine too
coarse):** a row bad for one metric is still usable by pipelines that don't need that metric — the coarse `quality=dirty`
flag is only a worklist signal, the field-scoped view does the real gating, so no row is over-discarded. (At build, quantify
how many rows each whole-row QUARANTINE rule removes before committing it.)

## 11. RULE REGISTRY (`rules.yaml`) + APPLICABILITY + SCORING
A rule entry = **GATE** (`board` + `instrument_type` only) + **`required_fields`** + **PROPERTIES**
(`cross_regime_validated`, `min_n`, status, lift). **Firing:** a rule scores only if relevance-gate AND trust-filter pass;
relevant-but-untrusted = display-only ("evolve-only-if-robust"). Generated rules index (retire hand-maintained `rules/index.md`).

## 12. RECONCILIATION CAMPAIGN (verify gate)
Migrate every hand-fix into the overlay (incl. orphaned Indiabulls Power) + reconstruct `old_value` baselines → rebuild
from raw+golden+overlay → diff vs current → every mismatch is a bug → resolve. Must-pass targets: ROLEXRINGS/NPST/CANTABIL
fakes gone, e6053e7 O-3 nulls hold, Indiabulls fix lands.
**Baseline caveat (R5):** the migrated hand-fixes (34+21+16) lack a recorded `old_value`, so conflict-detection is INERT for
exactly those legacy fixes until baselines are backfilled — backfill is step 1 of the campaign, not optional.
**Determinism fences (required for a reproducible rebuild — design §12.3):** pin raw snapshots; NO live network calls during
rebuild (e.g. `06_validate_tickers.py` Yahoo); scrapers must NOT overwrite the raw cache (the ROLEXRINGS mechanism); no
date/year timebombs (hardcoded `hi=2026`); no silent `try/except` drops. **Row-membership diff** (by ISIN set) is a first-class
diff class — protects the movable row count / catches silent drops.

## 13. TIME-PARTITION CONFIG
One config holds all date boundaries: cohort (boom/longterm), era buckets, train/test/validation splits. Hardcoded dates
pulled out of pipeline/predictor/validation code into here. `cohort` etc. are views derived from it.

## 14. FUTURE SEAMS (designed now, NOT built)
`universe_type` (ipo / listed-stock) + the as-of/frequency registry attributes + an `na:universe` state reserve room for
non-IPO stocks and live data. The golden-file `upcoming`/`announced` status + the `announcements` feed seed live corp-actions.
Build = a separate live-data effort (P-4) — each source refreshes differently.

## 14.5 STANDING GUARDS (do not "fix" these; they are correct as-is)
- **Features↔Data guard (design §15):** some empirical results are GENUINE NULLS, not data bugs — do NOT "fix them away."
  Specifically: **liquidity & quality have no predictive signal → weight 0** (validated); **no take-profit/stop-loss rule beats
  buy-and-hold cross-regime** (the right tail carries returns; tight stops hurt the secondary buyer). A future agent must not
  treat these as corruption to repair. Before "fixing" any feature, confirm it's a DATA root cause (reverse-map), not a real result.
- **P-3 data-change protocol** (the rulebook): every future data/column change MUST go declare-in-registry → validity-check →
  design → implement → update-pipeline → regenerate (schema/rules/diagram) → verify. This is the generated-artifact discipline
  that keeps L0→L8 coherent. (Authored as PLAN T8.4; wired into project_map CONTEXTS so it auto-surfaces.)

---

## 15. CLEANING-RULE (CR-*) BUILD-SPEC — distilled from the issue catalog
*This is the COMPRESSED index. The FULL per-issue detail + fix mechanics + task-file build hazards live in
**`FOUNDATION_BUILD_SPEC.md`** (the frozen build-spec — read it at build). Counts are draft-grade (re-verify at build).*

| CR family | issues | what the rule does |
|---|---|---|
| **CR-I1 / CR-prov / CR-stamp** | I1, I1-x, I1-stamp, I1-enc, O-15 | 4-state `_prov`; numeric-parse zeros; validate-before-stamp; harden `mktcap_class` (0→null) |
| **CR-O3 (cross-field)** | O-3, I1-x | `Σtranches ≈ total` else route tranche cells to missing (32+218 rows) |
| **CR-O2recover / CR-MININV** | O-2, O-14 | derive `sub_total_x=sub_total_cr/issue_size_cr` (88) + `min_inv=lot×price` (18), status `derived`, validated; ALSO O-2 75/106 SME network-free recovery via `03d`-guard flip from ipowatch cache |
| **CR-GMP** | O-4 | `gmp_pct=0` → NULL FIRST (so `gmp_deep_hunter` `.isna()` picks it up) → backfill from a NON-investorgain source (gated, OD-4). Offenders: Vivo/KN Agri/Krishna Defence/Timescan |
| **CR-D1 family** | D-1 + 11 sub-issues, D-2, D-cov-gap | price-gap arbiter, numeric-tolerance ratio, reverse-split sign, window-scope, ISIN-less corroboration-only, golden override |
| **CR-EPS** | O-5/7, O-5b | EPS share-base: A2 null-and-flag non-comparable; sign-consistency (eps↔pat) validity (deferred recompute = BL-2) |
| **CR-SF / CR-margin / CR-pe** | O-9, O-10, O-6b | shareholder-funds denominator validity (sf≤0/tiny → quarantine ROE/DE); tiny-sales margin; loss-maker P/E → null |
| **CR-nonequity / CR-instr** | O-6, O-16a | gate equity table by `instrument_type=='equity'`; ISIN security-type digit → instrument family (Std Chartered IDR) |
| **CR-asof** | D-3, O-fin-asof | at-IPO vs current split; financials as-of attribute (RHP snapshot vs current) |
| **CR-mcap** | D-3, O-8, O-12, O-mcap-val | market_cap_at_ipo (BL-1); well-posed [1,20]× band; value-audit KPI; ISIN-only entity join |
| **CR-date / CR-band / CR-lot / CR-promoter** | O-11, O-13, O-16b, O-16c | `open≤close≤listing`; `band_low≤issue≤band_high` (needs band_high); lot plausibility floor; `promoter_post≤pre` |
| **CR-id / CR-norm / CR-face / CR-cov** | ID-verify, listing_at, face-value, O-fin-cov, anchor-cov | explicit not-verified state; canonical exchange token; face-value set check; per-cohort fill-rate |
| **CR-envelope / CR-status** | T-2, O-1 | carry Cat-2 whitelist (no clamp); repair raw listing_open / downgrade status (one-off) |

**Protected (do-NOT-correct):** the 67 Cat-2 ISINs — verified-genuine crashes (e.g. Aster Silicates −100% real delisting,
Inox +604% real) — the corp-action fix must never invent a split for these.
