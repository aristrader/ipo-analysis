# Cluster 2 — Ingestion & Extensibility (CONNECTED design section)

> **STATUS: NOT FINAL.** Design / think-only artifact for the 2026-06-17 night run. Zero code, zero data
> changes, zero pipeline runs. Every number is grounded in the cited ground-truth docs/files (re-verified
> read-only against `docs/sources.md`, `docs/schema.md`, `scrapers/`, the `d1_*` join trail, and Group-B
> `task_14` / `task_15`). This is ONE coherent section spanning three connected concerns: (A) **sourcing per
> field + deterministic fallback order**, (B) the **column registry** (the extensibility core), and (C)
> **identity & matching**. It is written to be woven by a later integrator alongside the other clusters.

## How this cluster connects to the others (read these boundaries first)
- **Cluster 1 OWNS** the missing-data policy and the present-vs-absent / 3-state encoding (`published` /
  `fetch_parse_failed` / `real_zero`), the structural-column set, the end-state schema, and the dataset
  layout. **This cluster REFERENCES that encoding; it does NOT redefine it.** Where this doc says
  "missing-policy", "status", or "provenance state", it means *the encoding Cluster 1 lands on* (the
  extension/replacement of the existing `<field>_src` scheme — `task_03`). The registry's `missing-policy`
  and `as-of` fields are *slots that point at Cluster 1's definitions*, not new semantics.
- **Cluster 3 OWNS** cleaning rules, the overlay/reconciliation campaign, and rule-applicability. This
  cluster defines WHERE data enters and HOW it is keyed/declared; Cluster 3 defines how a dirty value gets
  cleaned/promoted and how overlay corrections layer on top. The registry's `validity-check` slot is the
  *declaration point* a Cluster-3 cleaning rule consumes — the rule logic itself is Cluster 3's.
- **The instrument-type / universe-type seam** (`task_05b` / `task_13`) is shared. This cluster keeps the
  ingestion + identity design open to it (a `dataset-applicability` slot per column + an identity model that
  does not assume "IPO"), but the canonical structural column is Cluster 1's call.

---

## PART A — SOURCING PER FIELD + DETERMINISTIC FALLBACK ORDER

### A.0 Principle: every field has an ORDERED source list + an explicit "absent" outcome
A field is not "scraped from a source"; it is **resolved by walking an ordered list of candidate sources
until one yields a value whose status is `published`**. The walk is deterministic (same inputs → same
winner) and declared once (in the registry, Part B). When the walk exhausts without a published value, the
field is **NULL with a status** (`fetch_parse_failed` if a source was tried and failed to parse, or
`source_never_published` if no source covers that field for that era) — never `0`/`""`. This is the
structural cure for I1 (the `0`-instead-of-missing bug): the fallback fires on *status ≠ published*, not on
a truthy check, so a stored `0` can never block the next source. (Encoding owned by Cluster 1; this is the
fallback mechanism that consumes it.)

### A.1 Source roster (roles only, from `docs/sources.md` + `scrapers/`)
- **Chittorgarh** (SPINE) — identity (ISIN/symbol/bse_code), dates, issue_price, issue_amount, lead_manager,
  market_maker, fresh/OFS, anchor, promoter pre/post, 3yr financials, listing-day OHLC. ISIN authoritative.
- **Sharescart** — boom-cohort (2023–25) enrich: subscription ×, GMP, 3yr financials, promoter %, price
  band, lot size, min investment, listing_open/gain. (The source that MINTS the `0`-subscription bug, task_15.)
- **Screener** — financials/KPIs for 2020–22 where Sharescart absent; weekly price history. No ISIN (bridge via ticker).
- **Exchange lists (NSE/BSE)** — authoritative symbol↔ISIN↔name; the identity cross-check.
- **Bhavcopy (NSE/BSE EOD)** — daily OHLC by ISIN/symbol; the price backbone + listing-day recovery.
- **Yahoo** — daily OHLC for mainboard (poor SME); also the symbol-only corp-action feed (task_14: the 354
  empty-ISIN rows originate here).
- **NSE Public Issues API** — authoritative MB subscription × (2020+). **SME returns 0.00** → not a source for SME.
- **IPOWatch** — GMP series + subscription split incl. SME. Name-slug + listing-date keyed (no ISIN).
- **InvestorGain** — GMP single ₹ value, symbol/bse-code + listing-date keyed (no ISIN).
- **moneycontrol autosuggest** — ISIN↔ticker BRIDGE only (identity helper, not a field source).
- **Corp-action sources** — `nse_corp_actions:equities/sme` (ISIN-carrying, authoritative) + `yfinance`
  (symbol-only, empty ISIN) → reconciled/merged into `corp_actions_merged.csv` (task_14).
- **Manual overlay catalogs** (Cluster 3 owns layering): `manual_overrides.csv` (3 market_maker rows),
  `manual_thinktank_audit` / `verification_2026-05-31` tags inside `corp_actions_merged.csv`, 88-audit
  Cat-1 (21 split overrides), `drhp_recovered.csv` (16 DRHP financials). These are the **highest-priority
  source in the fallback order** (an approved hand-fix wins) but are conflict-flagged, not silent (Cluster 3).
- **Tested & NOT viable** (do not re-add as fallbacks): BSE official IPO API, ipocentral (the O-4 GMP-0
  origin — task_15 §3.3), trendlyne, moneycontrol financials.

### A.2 Fallback order per field GROUP (deterministic; grounded in sources.md + task_14/15)
Ordering principle, in priority: **approved overlay → exchange-authoritative → primary scraper → secondary
scraper → derived/recovered → NULL+status**. Concrete orders:

| Field group | Fallback order (stop at first `published`) | Coverage / notes (ground truth) |
|---|---|---|
| **Identity** (ISIN, nse_symbol, bse_code) | overlay → Exchange lists (NSE/BSE) → Chittorgarh → moneycontrol bridge | ISIN 100% via Chittorgarh; exchange lists are the cross-check (Part C). |
| **Dates / price band / min-inv / issue_price / issue_amount** | overlay → Chittorgarh → Sharescart | Chittorgarh is the spine; Sharescart fills boom band/lot/min-inv. issue_amount '--' from Sharescart → NULL not 0. |
| **Subscription × — MB** | overlay → Sharescart → **NSE Public Issues** → ipowatch | task_15: NSE authoritative but cache overlaps 0/18 of the MB 0-rows → MB residual needs re-scrape, else NULL. |
| **Subscription × — SME** | overlay → Sharescart → **ipowatch** → *derived from `_cr`* (Option D) | task_15 §6: 75/106 SME 0-rows fixable from existing ipowatch cache; +88 recoverable arithmetically (`status=derived`). NSE NOT a SME source (returns 0.00). |
| **Subscription category split (QIB/NII/RII)** | overlay → Sharescart → NSE (MB) / ipowatch (SME) | task_15 O-3: gate completeness check to MB (SME QIB=0 is legitimate). |
| **GMP** | overlay → Sharescart → **investorgain** → ipowatch → gmp_deep_hunter (≤2022) / gmp_patcher (≥2025) | task_15 O-4: the 10 GMP-0 rows came via ipocentral/websearch (no in-repo scraper, NOT viable) → must NULL + queue a fresh source. investorgain cache itself has `gmp_rs=0` for those → genuinely "source never published". |
| **Financials (EPS/sales/PAT/margins)** | overlay (drhp_recovered) → Sharescart (use `pre_ipo_*`) → Screener → Chittorgarh 3yr | Screener covers pre-listing FY for 2020–22; Sharescart post-IPO contamination → use pre_ipo_* fields. |
| **Market cap / sector** | (as-of-tagged) source per task_17 | AS-OF hazard (D-3): current cap ≠ at-IPO cap; the registry's as-of slot (A.3 / Part B) is mandatory here. |
| **Corp actions (split/bonus ratio + ex_date)** | overlay (thinktank/88-audit) → `nse_corp_actions` (ISIN) → yfinance (symbol, corroboration-only per task_14 Q8) | Join + windowing is Part C; yfinance demoted to corroboration is an open owner-question (task_14). |
| **Daily prices (OHLCV)** | Bhavcopy (official, ISIN) → Screener → Yahoo | Bhavcopy authoritative incl. SME; Yahoo poor for SME. |

### A.3 As-of attribute is a SOURCING concern, declared per field (links Cluster 1)
Every TIME-VARYING field carries an **as-of attribute**: `at_ipo_snapshot` vs `current_live`, plus the
recorded as-of date. This is the general cure for the D-3 class (market-cap leak, migration circular-mcap):
a field scraped "as of now" must never be read as "as at IPO". The attribute lives in the registry
(Part B) and is enforced at ingestion (stamp the as-of date when the value is captured). The encoding of
the date column itself is Cluster 1's; this cluster mandates that the *source declaration* names which
as-of class each field belongs to so the fallback walk never mixes an at-IPO source with a live one.

---

## PART B — THE COLUMN REGISTRY (the extensibility core)

### B.0 The goal (north-star: clean / extensible / single-source-of-truth)
Today, adding a column means writing a bespoke `pipeline/03x_*` step with its own scraper call, its own
skip-guard (the I1 bug, replicated three times in `03c/03d/03e` — task_15 §3.4), and its own ad-hoc parse.
**Target: adding a column = ONE registry entry. No new script.** The pipeline reads the registry and
generically (1) resolves the value by walking the declared sources, (2) parses with the declared parser,
(3) applies the declared missing-policy (Cluster 1's 3-state), (4) runs the declared validity-check
(routing failures to dirty per Cluster 3), (5) stamps the as-of attribute, and (6) restricts the column to
the declared datasets. New-column gaps are then auto-handled by the SAME missing-policy — no special-casing.

### B.1 Registry SCHEMA (one declaration per column)
Each column is one record (proposed as `data/registry/columns.yaml` or a typed table — physical form is a
Cluster-1/owner call). Fields:

| Slot | Meaning | Example value |
|---|---|---|
| `name` | canonical column name | `sub_total_x` |
| `dtype` | logical type | `float` |
| `sources` | ORDERED list of `{source, locator, parser_args}` = the Part-A fallback order | `[{sharescart, cell[3]}, {nse_public_issues}, {ipowatch}, {derived: sub_total_cr/issue_size_cr}]` |
| `parser` | named parser (Part B.2) applied to each source's raw cell | `parse_num_x` |
| `missing_policy` | a REFERENCE to Cluster 1's 3-state policy + the "absent outcome" | `three_state` (→ null + status, never 0) |
| `validity_check` | named predicate(s) the value must pass; failure → dirty (Cluster 3 acts) | `in_range(0, 5000)`, `cross: x ≈ cr/issue_size` |
| `dataset_applicability` | which datasets/instrument-types/eras this column applies to | `{board: [MB,SME], instrument_type: [equity], era: 2020+}` |
| `as_of` | as-of class + date-source (Part A.3) | `at_ipo_snapshot` |
| `provenance_col` | the `_src`/status companion (Cluster 1 owns the encoding) | `sub_total_x_src` |
| `key` | which identity key joins this field's source rows to the substrate (Part C) | `isin` / `nse_symbol+listing_date` |

The pipeline has ONE generic resolver that consumes this record for every column. The existing scattered
`03c/03d/03e` skip-guards collapse into the single declarative `missing_policy` slot (kills the 3 duplicated
I1 guards — task_15 §7.2). The existing `<field>_src` columns (`issue_price_src`, `sub_total_x_src`,
`gmp_pct_src`, `pat_yr3_src`, …, verified in `docs/schema.md` L184-194) are the seed of `provenance_col`.

### B.2 Named parsers (reusable, not per-column)
A small library of named parsers the registry references by name — e.g. `parse_num` (digits→float, `--`/blank
→ NULL, **never 0** — fixing the `'0.00x'`→0 mint at the source, task_15 §3.1), `parse_ratio` (split/bonus
`X:Y` → factor, **numeric-tolerance** comparison not exact-float, task_14 USASEEDS), `parse_date`,
`parse_pct`, `parse_currency_cr`, `parse_derived(expr)` (e.g. `sub_total_cr/issue_size_cr` for Option-D
recovery, status=`derived`). Reuse means a parser bug is fixed once for every column that uses it.

### B.3 WORKED EXAMPLE — "add a new column" (e.g. `anchor_lockin_pct`)
To add anchor-lock-in % (hypothetically newly desired), the ENTIRE change is one registry record — no new script:

```yaml
- name: anchor_lockin_pct
  dtype: float
  sources:
    - {source: chittorgarh, locator: "detail.anchor_lockin"}   # primary
    - {source: sharescart,  locator: "cells.lockin"}           # fallback
  parser: parse_pct
  missing_policy: three_state           # → NULL + status (Cluster 1); never 0/""
  validity_check: [ "in_range(0,100)" ]
  dataset_applicability: {board: [MB,SME], instrument_type: [equity], era: 2021+}
  as_of: at_ipo_snapshot
  provenance_col: anchor_lockin_pct_src
  key: isin
```
On the next run the generic resolver: walks chittorgarh→sharescart, parses with `parse_pct`, writes NULL +
`status=source_never_published` for pre-2021 / non-equity rows (auto-handled by missing_policy — no
special-casing), validity-checks 0–100 (out-of-range → dirty, Cluster 3 promotes on fix), stamps
`as_of=at_ipo_snapshot`, and records the winning source in `anchor_lockin_pct_src`. The column appears in
the masters; derived views (Cluster 1) inherit it for free. **No bespoke `pipeline/03x` step is written.**

### B.4 Testability
N/A as a runnable predicate (architectural). Validated by schema cross-check: the registry SUPERSETS the
existing `<field>_src` columns already in the substrate (L184-194), and a walkthrough of `sub_total_x`
(the I1 column) shows its bespoke `03c/03d/03e` guards reduce to the single `missing_policy=three_state`
slot — i.e. the registry expresses the existing pipeline declaratively, then extends it.

---

## PART C — IDENTITY & MATCHING (promote D-1 learnings to a STANDING principle)

### C.0 ISIN is the primary key; symbol bridges face-value splits; everything is date-scoped
Confirmed from `d1_join_strategy_2026-06-17.md` + task_14:
- **ISIN is the ONLY automatic join key** for substrate fields. Name-matching never merges — it only flags
  (Part C.4). Substrate masters + price files are keyed by the substrate (post-split) ISIN.
- **Corp actions are the documented EXCEPTION** (a face-value split mints a NEW ISIN, so the action sits
  under the OLD ISIN or — for yfinance — under no ISIN). They match by **symbol ∪ substrate-ISIN**. This is
  load-bearing: **301 of 449** action-receiving substrate rows reach their actions via SYMBOL ONLY; only 26
  reach via ISIN-only (d1 §2). Dropping the symbol bridge loses almost all adjustments. ISIN-only is not viable.

### C.1 THE STANDING MATCHING PRINCIPLE (promoted from D-1)
> **Corp-action ↔ substrate matching = (symbol ∪ substrate-ISIN), SCOPED by the stock's trading-date
> window, with collisions flagged not guessed.** Concretely, for each substrate ISIN with a price file:
> 1. Build the candidate set = `by_isin[isin] ∪ by_symbol[SYMBOL]`, dedup by `(ex_date, ratio_factor)`
>    using a **numeric ratio tolerance** (not exact float — task_14 USASEEDS `1.428571` vs
>    `1.4285714285714286`).
> 2. **Date-window guard (primary collision cure):** admit an action only if its `ex_date` ∈
>    `[first_trade − small_slack, last_trade]` (price coverage window). Out-of-window → **drop from
>    adjustment + flag** `corp_action_out_of_window` (never silently apply). This neutralises symbol-reuse:
>    catches **44** wrong-era attachments today (37 yfinance, 25 with rf<1) while keeping all 458 legitimate
>    symbol matches (d1 §2). Example: KAUSHALYA 0.01 reverse-split would attach to the 2007 infra company via
>    the freed-then-reused symbol — the window guard is what makes the symbol join safe.
> 3. **ISIN-family preference (secondary, confidence not rejection):** when a candidate carries a non-empty
>    ISIN, prefer the one whose issuer family (`INE`+5-char) matches; an empty-ISIN (yfinance) action is
>    admitted only on the date-window strength → set `corp_action_match = isin_family | symbol_in_window`.
> 4. **Window scoped to the symbol-added subset only** (D1-F1): the gate must NOT touch ISIN-matched
>    actions, or it drops ~26 legit pre-coverage splits (ATLANTAA winner→loser; TARIL +1434×).
> 5. **Coverage-END branch** (D1-F2/R11-B2): `ex_date > last_trade` ⇒ gap NOT measurable ⇒ **defer to
>    override, NOT auto-phantom-drop** (else nulls real multibaggers E2E +74.7×, FORGE). A separate branch
>    from "out of window before listing".
> 6. **Collision that can't be disambiguated** (two in-window candidates, contradictory ratios; or ≥2
>    issuer families with in-window events) ⇒ **do NOT pick — null the affected metric + raise to the
>    flagged/unresolved set** (flag-don't-guess). This is the standing failure mode for every key, not just
>    corp actions.

This is the behaviour of the long-term ideal — a canonical entity-mapping table (ISIN-family ↔ symbol ↔
substrate row, d1 option (e)) — approximated from on-disk data (the price coverage window IS the per-entity
trading life). The full mapping table needs an NSE symbol-change ledger the repo lacks (network default-deny)
→ keep as the eventual target; option (d) above is the buildable standing principle now.

### C.2 Generalise to ALL multi-source ingestion (not just corp actions)
The registry's per-column `key` slot (Part B.1) carries the same discipline:
- **ISIN-keyed sources** (Chittorgarh detail, NSE UDiFF bhavcopy, exchange lists) → direct ISIN join.
- **Symbol+date-keyed sources** (NSE Public Issues, investorgain `nse_sym/bse_code + listing_date`) →
  bridge symbol→ISIN via exchange lists, then **confirm with the listing-date window** (same date-scoping
  principle — a freed/reused symbol is rejected if its event date doesn't fall in the row's window).
- **Name+date-keyed sources** (ipowatch slug + listing-date window) → **flag-for-manual, never
  auto-merge** (name-matching only flags — C.0). The window narrows the candidate set; ambiguity → dirty.
- **No-ISIN bridge sources** (screener via ticker, moneycontrol autosuggest) → resolve ISIN↔ticker via the
  bridge, then carry ISIN as the key; a failed bridge → `fetch_parse_failed`, not a wrong join.

### C.3 Malformed-key hazards to handle structurally (task_14 ground truth)
- **163 `nse_corp_actions:sme` rows (+1 equities) store a NON-ISIN numeric code in the `isin` column**
  (NPST `409536`, USASEEDS `462637`). These match the substrate by SYMBOL only; any ISIN-keyed dedup/overlay
  will mis-key them. The matcher must detect "isin not in `INE…` form" → treat as symbol-only, not as a real ISIN.
- **354 yfinance rows carry empty ISIN**; **52 match a substrate IPO symbol** — the structural origin of the
  over-counts (ROLEXRINGS ×1000, NPST ×9). Owner-question (task_14 Q8): demote empty-ISIN yfinance to
  **corroboration-only** (may confirm, never CREATE an adjustment alone) vs keep as primary gap-fillers.
- **`action_type` is corrupted for all 354 yfinance rows** (03l hardcodes `'split'`) — the matcher/registry
  must not key behaviour on `action_type` for empty-ISIN rows; preserve the original yfinance type if needed.

### C.4 Identity model kept open to the future universe (Cluster 1 / task_05b/13 seam)
The identity layer must not assume "IPO". An `instrument_type` ({equity, fpo, reit, invit, …} — already
exists per the charter) and a future `universe_type` (ipo / listed-stock) ride the SAME ISIN key; IPO-only
fields degrade to NULL for non-IPO rows via the registry's `dataset_applicability` + the 3-state
missing-policy (no special-casing). Live/daily price ingestion slots in as another ISIN-keyed source with a
`frequency` attribute — the matching principle (ISIN primary, date-scoped) is unchanged. This cluster only
keeps the seam open; the canonical structural column is Cluster 1's decision.

---

## OPEN OWNER-QUESTIONS
1. **Registry physical form** — YAML/TOML config file (`data/registry/columns.yaml`) vs a typed Python
   declaration vs a CSV the pipeline reads? (Affects how `validity_check`/`parser` are referenced; leaning: a
   declarative file with named-function references, so non-coders can add a column.)
2. **Empty-ISIN yfinance corp-action trust** (task_14 Q8) — demote the 354 symbol-only rows to
   corroboration-only (never create an adjustment alone), or keep them as primary gap-fillers gated by the
   price-gap arbiter? This is the single biggest lever on the over-count class.
3. **Date-window slack** — how many trading days of pre-`first_trade` slack for a split effective at listing?
   (d1 confirms the 44 bad cases are years off, so a few days is safe — but the exact slack is an owner call.)
4. **Fallback for arbiter-blind / cache-empty residuals** — for MB-subscription (NSE cache overlaps 0/18) and
   the 10 O-4 GMP rows (investorgain itself has `gmp_rs=0`): approve a network re-scrape, or accept NULL +
   `source_never_published` as a permanent interim? (Network is default-deny.)
5. **Canonical entity-mapping table (d1 option e)** — do we eventually want an NSE symbol-change ledger (needs
   a new trusted source) to replace the date-window approximation, or is the window-scoped principle the
   permanent design?
6. **`dataset_applicability` granularity** — is per-column applicability keyed on `{board, instrument_type,
   era}` sufficient, or do we need finer dimensions (e.g. exchange, cohort)? (Depends on Cluster 1's
   structural-column set + task_05b's instrument-type decision.)
7. **Where the registry's `missing_policy` / `as_of` definitions physically live** — confirm they are
   OWNED by Cluster 1 and merely REFERENCED here, so there is one source of truth (no parallel encoding).
```
