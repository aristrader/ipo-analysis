# Data-Foundation — BUILD-SPEC DETAIL (frozen; read at build, retire post-build per BL-3)
*Recovered 2026-06-17 from git snapshot 7eda95b after a line-by-line audit found the FOUNDATION_PLAN/ARCHITECTURE
consolidation had compressed away build-critical detail. This is the 3rd survivor doc: the FROZEN BUILD-SPEC we'd
always intended to keep until build (the prior "§4 = frozen build-spec" decision). PLAN = what & in what order;
ARCHITECTURE = what the system is; THIS = the concrete per-issue / per-source / per-hazard detail the build needs.
Counts are draft-grade (re-verify at build). Sourced from the deleted issue-register + design §8 + task_14/17/19.*

---

## PART A — SOURCING ROSTER & DETERMINISTIC FALLBACK ORDERS (recovered from design §8)

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


---

## PART B — THE ISSUE CATALOG + CR-* MAPPING (recovered issue register)

# Consolidated Data Issue Register — 2026-06-17 (Group B rollup)

> ⚠️ **STATUS: NOT FINAL — draft-grade.** This is a CONSOLIDATION of the seven Group-B issue/re-audit task files
> (`task_14`…`task_20` under `docs/research/night_run/`). It re-states their verdicts; it does NOT re-run analysis
> or re-review. **Counts are draft-grade:** the Group-B per-task review loops were stopped early — every owning
> task still has an UNMET review-loop stop rule (none reached the ≥2-consecutive-clean-fresh-round floor), and the
> review log (`night_run_2026-06-17_review_log.md`) was ABSENT on disk as of task_20 (so "quiet" is unverified).
> Treat every count below as the owning task's latest read-only reproduction, not a final number. Each issue cites
> its owning task; resolution approaches and CR-* cleaning-rule pointers are proposals for owner approval.
>
> **Substrate context:** `data/master/ipo_analysis.csv`, 2,384 rows, last rebuilt at commit `26cd1fd`
> (`as_of` 2026-06-06) — which is also the commit that introduced the D-1 corp-action bug, so the live substrate
> reflects the buggy merge.

---

## 1. SUMMARY TABLE

### By severity
| Severity | Count |
|---|---|
| CRITICAL | 4 |
| HIGH | 9 |
| MED | 11 |
| LOW | 5 |
| **TOTAL DISTINCT ISSUES** | **29** |

### By status
| Status | Count | Meaning |
|---|---|---|
| open | 19 | reproduces on current data; no fix ever applied |
| fixed-still-holds | 4 | a prior fix was re-audited and DOES still hold |
| fixed-but-regressed | 2 | a prior fix was applied then CLOBBERED / not-yet-effective on the live substrate |
| handled-before | 4 | a known caveat already registered in `data_review.md` / a contained one-off / a deployed remediation |
| **TOTAL** | **29** | |

### Resolvability
| Resolvable | Count |
|---|---|
| now (read-only / pipeline-design, no new data) | 17 |
| needs-external-data (re-scrape / new source) | 5 |
| needs-owner-decision | 7 |

---

## 2. PINNED — Issues needing an OWNER DECISION

(Distilled from the open-owner-questions blocks of all seven tasks. These block the design, not just the build.)

- **OD-1 — Adopt the I1 reframe ("field-aware validity routing + 3-state present/absent provenance") over the
  charter's original global "0→NaN at load" leaning?** Ground truth shows a global 0→NaN would CORRUPT 725 real
  `ofs_cr=0` (fresh-issue) + debt-free `borrowings=0` rows. (task_19 OQ1; task_15 OQ1.) Leaning: YES.
- **OD-2 — New provenance carrier cost.** Only 2 of ~7 I1 fields (`sub_total_x`, `gmp_pct`) have a `_src` column
  today; the other 5 (`sub_qib/nii/retail_x`, `market_cap_cr`, `min_investment_rs`, `net_sales_yr*`) have NONE.
  Accept adding ONE compact, registry-driven provenance carrier covering all columns uniformly (vs. only the 2
  with `_src`)? (task_19 OQ7.) Also: approve extending the column registry to support CROSS-FIELD predicates
  (needed for O-3 tranche-vs-total, 32+218 rows). (task_19 OQ8.)
- **OD-3 — Recover vs NULL the 88 `_cr`-present subscription rows** (Option D arithmetic recovery from
  `sub_total_cr / issue_size_cr`, status=`derived`, vs lossy NULL). And the `_x`/`_cr` consistency policy when `_x`
  is NULLed but `_cr` is real demand. (task_15 OQ6, OQ8.)
- **OD-4 — Network re-fetch approval** (network is default-deny): NSE re-scrape for the 18 MB subscription rows; a
  fresh (non-investorgain) GMP source for the 10 O-4 rows; backfill of the longterm coverage cliffs (1,498
  band/lot/min-inv, 1,027 unverified-identity, 1,886 face_value, 1,487 anchor). Accept NULL as interim otherwise?
  (task_15 OQ3; task_18 open-Qs; task_16 OQ on coverage.)
- **OD-5 — Source the at-IPO market cap?** Adopt `market_cap_at_ipo_cr` as primary (90 rows today, ALL longterm,
  0% boom) and invest in deriving it for boom (`issue_price × post-issue shares`), or accept the Option-C interim
  (`issue_size_cr` proxy + drop current cap from predictor paths)? AND value-audit `kpi_market_cap_post_ipo` FIRST
  (≥1 gross parse error found: HDFC AMC). AND D-3 binding: should predictor/analogs/weights + `forward_test.py:27`
  bind to the at-IPO field? (task_17 OQ1, OQ1b, OQ2.)
- **OD-6 — Non-equity handling (the standing STATUS.md decision):** exclude REIT/InvIT/IDR/FPO from equity
  financials & analyses, or analyze separately? Governs O-6 (REIT/InvIT sales), O-16(a) (Std Chartered IDR
  mislabel), and the `x-nonequity` rule. (task_16 OQ3; task_18 → task_05b; task_05b owns it.)
- **OD-7 — EPS comparability (A1 vs A2):** will per-year/TTM EPS ever feed a feature (EPS-CAGR/trend)? If no →
  null-and-flag (A2, cheap) suffices; if yes → recompute on a constant share base (A1, BLOCKED on the unsolved
  share-count work). And validity-rule severity: route a financial validity failure to `quality==dirty` (whole row)
  or null only the offending derived field? (task_16 OQ1, OQ5.)
- **OD-8 — Fix the corp-action join now vs hold for the foundation.** The corrections ARE in the overlay but the
  substrate (rebuilt @26cd1fd) still shows 3 fake multibaggers because the JOIN/dedup is buggy. Fix-and-rebuild
  now, or hold until the overlay + reconciliation campaign (task_08/09) is designed (leaving the fakes live
  interim)? Leaning per charter: hold (foundation-first). (task_20 OQ1; task_14.)

---

## 3. PINNED — Already-"FIXED" items that DON'T still hold (from task_20 re-audit)

The dominant task_20 finding: **almost nothing claimed "fixed" for the DATA is fixed in the SUBSTRATE.** The
substrate WAS rebuilt at `26cd1fd` (same commit that merged the corrections) — so the failure class is
**"applied-but-defeated-by-a-broken-join + lost-on-rebuild,"** NOT "overlay written but never materialised."

- **D-1 corp-action corrections (34 `manual_thinktank_audit` rows) — applied to `corp_actions_merged.csv` but
  DEFEATED by a buggy join/dedup.** 7 of 12 count-conflict symbols still `multibagger`; 3 still absurd
  (ROLEXRINGS +15,272%, NPST +16,127%, CANTABIL +3,968%). The overlay is present and the substrate was rebuilt —
  yet the bug persists because the ISIN-vs-symbol join + duplicate-event dedup is broken (ROLEXRINGS keyed
  INE645S01024 in the substrate vs INE645S01016 in the overlay). (task_20 §3A; task_14.) → status **fixed-but-regressed**.
- **Cat-1 split corrections (21) — 20/21 applied via `corp_actions_merged.csv`; INE399K01017 (Indiabulls Power)
  NEVER written to any overlay.** AND, like D-1, the 20 applied ones are defeated by the same broken join. The
  charter's "NOT yet in `manual_overrides.csv`" framing is half-true/misleading: they were applied via the OTHER
  overlay file (the `07` consumer), not `manual_overrides.csv` (the `09` consumer). (task_20 §3B; task_14 §3.4.)
- **e6053e7 (O-3 category null, 32 cells) — APPLIED then CLOBBERED by the 26cd1fd rebuild.** `git show` confirms
  e6053e7 (2026-06-10) blanked the qib/nii/retail cells for Jupiter/Cyient DLM/ideaForge; the later 26cd1fd
  rebuild (2026-06-14) re-introduced `0` into those exact cells. **Direct first-class evidence the pipeline DROPS
  hand-fixes on a non-idempotent rebuild** — a primary exhibit for task_08 (idempotency / hand-fix preservation).
  (task_20 §3D.) → status **fixed-but-regressed**.
- **T-4 clamp removal — the silent clamp IS gone (genuine), BUT its loud-tripwire + explicit-delisting replacement
  is DESIGN-LOCKED, NOT BUILT** (depends on D-1, still buggy). Correctly pending, not a regression. (task_20 §3C.)
- **WITHDRAWN by task_20's own round-1 review:** the earlier "O-5/O-6/O-8/O-15 are unreproducible" claim was a
  string-`=='0'` predicate bug (zeros stored as `'0.0'`). All four REPRODUCE and match the audit + sibling tasks.
  Recorded here so the withdrawal is not forgotten.

---

## 4. THE ISSUE REGISTER (one row per DISTINCT issue, de-duplicated across files)

> **Cross-file de-dup note:** I1 (0-vs-missing) is the systemic spine that recurs in task_15/16/17/18/19 — it is
> registered ONCE as **I1** below, with the per-field instances cross-referenced. The corp-action family
> (task_14 + task_20) is registered as **D-1/D-2/D-3-family** rows. The market-cap as-of leak (task_17 D-3) is its
> own row. CR-* pointers refer to declarative cleaning rules to be authored in the design doc §13.

### 4.1 SYSTEMIC / CROSS-CUTTING

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **I1** | 0-vs-missing: a blank / parse-fail / source-placeholder stored as `0` (or `''`), indistinguishable from a real zero; fallback guards treat `0` as present so they never fire | CRITICAL | open | TWO layers: (1) the SOURCE emits a placeholder `0` (e.g. sharescart `0x`); the parser (`parse_num`/`pfloat`/`fnum` all return None) does NOT mint it. (2) enrich/backfill steps treat `'0'` as truthy → copy it AND stamp a real `_src` (the provenance layer LIES). Multi-site: `03_enrich.py` for `sub_total_x`; GMP-backfill steps for `gmp_pct` | `sub_total_x` 124, `sub_qib_x` 341 (27 MB implausible / 314 SME real), `sub_nii_x` 156, `sub_retail_x` 157, `gmp_pct` 10, `net_sales_yr3` 13, `pre_ipo_net_sales` 17, `market_cap_cr` 7, `min_investment_rs` 18, `issue_amount_cr` (IDR) 1. NOT I1: `ofs_cr=0` (725 real fresh-issue), `borrowings=0` (real debt-free) | Field-aware validity routing + 3-state (really 4-state, +N/A-for-instrument) present/absent provenance; ONE compact registry-driven carrier (5 of 7 fields have no `_src` today); validity gate BEFORE any `_src` stamp, at every stamp site; distinguish (a)source-never-published / (b)fetch-parse-fail-or-placeholder / (c)real-zero — and (a)/(b) for BLANKS too (all 1129 `sub_total_x` blanks carry empty `_src`, equally ambiguous) | now (design) | task_19 (owner), 15, 16, 17, 18 | CR-I1, CR-prov3 |
| **I1-x** | Cross-field tranche-vs-total inconsistency (the real O-3): all 3 tranches `==0` while `sub_total_x` positive — a per-field predicate cannot express it | HIGH | open | sharescart captured the Total row but not per-category rows, wrote `0` for missing categories | 32 rows all-tranches-0-with-positive-total; 218 rows positive total + ≥1 zero tranche (audit said 3/214 — undercount) | Registry must support MULTI-COLUMN predicates: `Σ(tranches) ≈ total within tolerance, else route tranche cells to state-(b)`; gate SME QIB=0 as legitimate | now (design) | task_19, 15 | CR-O3 |
| **I1-stamp** | Provenance laundering — enrich/backfill steps stamp a real `_src` on a placeholder `0` | HIGH | open | `if o.get(c): r[c]=o[c]` + `r[c+'_src']='sharescart' if o.get(c)` — `'0'` is truthy | all 124 `sub_total_x=0` carry `_src='sharescart'`; 10 `gmp_pct=0` carry `_src∈{ipocentral,websearch}` | Stamping POLICY: a value must pass its validity predicate before earning a source tag, applied at EVERY assemble/stamp site (not a one-file patch) | now (design) | task_19 | CR-stamp |
| **I1-enc** | Inconsistent zero encoding across columns (`'0'` vs `'0.0'`) — any zero-vs-missing predicate must parse numerically, never string-match | MED | open | columns serialized differently (`sub_total_x`/`sub_nii_x`='0'; `net_sales_yr3`/`market_cap_cr`/`gmp_pct`='0.0'; mix for qib/retail) | caused task_20's own string-`=='0'` predicate bug (false "unreproducible" for O-5/6/8/15) | All I1 predicates parse numerically (`float(v)==0`) | now (design) | task_20, 15, 19 | CR-I1 |

### 4.2 CORP-ACTIONS / SPLITS / BONUSES (D-family — task_14, cross-checked task_20)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **D-1** | Over-count / fake returns — one corp-action event counted ≥2× → fabricated multibaggers | CRITICAL | open (overlay applied but defeated — see §3) | 3 root causes: (a) 03k/03l can't collapse one event reported by ≥2 sources on near-but-not-equal dates (7d/10d windows too tight; exact-float ratio equality at 03k L83; `action_type='split'` hardcoded at 03l L48); (b) 07 dedups only on exact `(ex_date,ratio)`; (c) `09_assemble.py:88-89` DISABLES the cross-source listing-price tripwire for any stock with a corp action | ROLEXRINGS +15,272% (10:1 counted 3×→×1000), NPST +16,127% (3:1 counted 2×→×9), CANTABIL +3,968%, GICL +948%, GNA +639%, PAVNAIND +297%; cluster predicate (rounded ratio, ≤90d, diff source) = 12 stocks; symbol-only-yf dup (predicate 3) = 13 symbols (ENGINERSIN, OPTOCIRCUI missed by 90d window) | Option A (price-gap detector, the source-agnostic arbiter) + Option B (source-reconcile de-dup, upstream complement) + Option C (override catalog, narrow fallback). Numeric-tolerance ratio compare at cluster step AND 03k L83. Re-enable the 09 cross-source tripwire for corp-action stocks. Resolution must be representable in the substrate (defer column set to task_03/05) | now (design); build needs the join fix | task_14, 20 | CR-D1, CR-gap |
| **D-1-fp** | Naive cluster detector over-catches (ANGELONE false positive) | MED | open | ANGELONE's two 10.0 legs share the SAME ex_date 2026-02-26 → `actions_for` `(ex_date,ratio)` dedup already collapses them (adj 30.6 correct); cluster predicate still flags it | FP rate ≥1/12 (~8%), not 0 as round-1 claimed | Gate: same-ratio cluster is a bug ONLY when legs have DISTINCT ex_dates AND survive the dedup; disambiguate genuine repeats via price gap | now (design) | task_14 | CR-D1 |
| **D-1-prec** | Float-precision miss (USASEEDS) — exact-equality ratio compare drops a real over-adjustment | MED | open | nse `1.428571` vs yfinance `1.4285714285714286` are different floats; exact equality (03k L83) misses the cluster | USASEEDS issue 120 → adj 58.8 (≈2.04× applied, should be ≈84) | Numeric tolerance (`abs(a−b)/b < 1e-3`) at the cluster step AND at 03k L83 | now (design) | task_14 | CR-D1 |
| **D-2** | Reverse-split-as-divisor — Yahoo `ratio_factor<1` multiplies instead of divides (0.01 → ×100) | CRITICAL | open (folded into D-1) | NSE parser only emits factors ≥1; all sub-1 factors are yfinance, applied as divisors | 45 merged rows have `ratio_factor<1`; PATANJALI INE619A01035 compounds D-2 (0.01) WITH D-1 (5.0 + 3.0 legs) | Direction-normalized price-gap test (gap sign → split vs reverse-split; gap magnitude → ratio) | now (design) | task_14 | CR-D1 |
| **D-1-cov** | Arbiter-blind rows — price-gap arbiter cannot fire (no observable gap) | HIGH | open | (i) 354 empty-ISIN yfinance rows; (ii) bhavcopy coverage starts years after ex_date (ATLANTAA ex-2010, coverage ~2017); (iii) R11-B2 coverage-END (`ex_date > last_trade`) | 6 ISIN-matched coverage-END events are REAL MULTIBAGGERS: E2E INE255Z01019 (+74.7×), LEMERITE INE0G1L01017, FORGE INE319Y01016 (ex 3.5yr after coverage) | Explicit FALLBACK ORDER when arbiter blind (source-priority → override catalog → flag-unresolved); a dedicated `ex_date > last_trade` → defer-to-override branch (NOT auto-phantom-drop, which would null genuine multibaggers) | now (design) | task_14 | CR-D1 |
| **D-1-win** | Window gate must be scoped to symbol-added only (D1-F1) | HIGH | open | a date-window gate applied to the whole union would drop ~26 legit ISIN-matched post-listing splits | ATLANTAA INE285H01022 (adj 30, +36% winner) + TARIL INE763I01026 (+1,434×) would both break | Scope the window guard to the symbol-added subset; ISIN-matched actions always apply | now (design) | task_14 | CR-D1 |
| **D-1-ratio** | Gap detector must be ratio-aware (R11-B1) — an absolute floor drops genuine small bonuses | HIGH | open | a 1.5× absolute floor calls a 5:4 bonus (gaps ~1.25×) a phantom | 350/1897 rows have ratio in (1.0,1.5] (141 are exactly 1.5) | Test "observed gap ≈ claimed ratio within tolerance, direction-normalized" — not "gap > X" | now (design) | task_14 | CR-D1 |
| **D-1-compound** | `bonus+split` same-day compound rows are fragile to future split-out | MED | fixed-still-holds (today) | 31 `action_type='bonus+split'` rows carry a single pre-collapsed factor; correct now (0 live double-counts) but a future yfinance re-report of the separate legs would survive `(ex_date,ratio)` dedup and double-apply | 31 rows (e.g. ASHOKA 3.0, BAJFINANCE 10.0) | Cluster/arbiter must treat a `bonus+split` row + its constituent legs as ONE event | now (design) | task_14 | CR-D1 |
| **D-1-sme-isin** | Malformed ISIN on nse:sme corp-action rows — a non-ISIN numeric code stored in the `isin` column | MED | open | 163 `nse_corp_actions:sme` rows (+1 equities) store e.g. NPST `409536`, USASEEDS `462637` instead of a real ISIN → match only by SYMBOL; ISIN-keyed dedup/overlay mis-keys them | 164 rows | Treat as symbol-only; feed to task_07 identity/matching; do not use as an ISIN join key | now (design) | task_14 | CR-id |
| **D-1-action** | `action_type` corrupted for all 354 yfinance rows | MED | open | 03l L48 hardcodes `action_type='split'` for every yahoo_only row ("Yahoo calls everything a split") — a real yfinance bonus/dividend is stamped "split" | 354 empty-ISIN rows | Preserve/derive the original yfinance action_type so `action_type` stays trustworthy | now (design) | task_14 | CR-D1 |
| **D-1-yftrust** | Empty-ISIN yfinance rows match purely by symbol — structural origin of the over-counts + reused-symbol hazard | HIGH | open (owner decision) | 354 yfinance rows carry NO ISIN; 52 match a substrate IPO symbol | 354 rows / 52 matching substrate symbols | OWNER CHOICE: demote empty-ISIN yfinance to CORROBORATION-ONLY (confirm but never CREATE an adjustment) vs keep as primary gap-fillers under the price-gap arbiter. NSE/ISIN-authoritative-only would kill most over-counts at source | needs-owner-decision | task_14 | CR-D1 |
| **D-cov-gap** | Resolution-catalog coverage gap — over-adjusted/dup stocks missing from the 53-row evidence file | MED | open | SIKKO, RAJMET, MKPL (issue_adj<1, over-adjusted) + GICL (dup-split +948%) are NOT in `corp_action_external_evidence.csv` (53 rows) | 4 uncovered stocks | Materialize the missing override catalog from the evidence file; resolve the 4 uncovered cases | now (design) | task_14 | CR-D1 |

### 4.3 SUBSCRIPTION + GMP (task_15)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **O-2** | `sub_total_x = 0` — subscription bid-multiple parsed as 0 | HIGH | open | TWO mechanisms: (1) partial parse (88 rows, mostly SME) — `_cr` (shares) parsed fine, only the bid-multiple cell `cells[3]` came through 0 (`parse_num('0.00x')→'0.00'`); (2) genuinely-empty table (36 rows, mostly the 18 MB) | 124 rows (SME 106 / MB 18); 88 carry ≥1 non-zero `_cr` (RECOVERABLE), 36 truly missing; 33/124 had listing pop ≥+20% | I1 3-state encoding + Option D arithmetic recovery (`sub_total_cr / issue_size_cr`, status=`derived`) for the 88; NULL the 36 residual; flip the `03d` guard → repairs 75/106 SME from existing ipowatch cache (network-free) | now (75 SME + 88 derived); MB 18 needs re-scrape | task_15, 19 | CR-I1, CR-O2recover |
| **O-3** | Category split (`sub_qib/nii/retail_x`) all-0 while total real | MED | open (e6053e7 partial+REVERTED) | sharescart got the Total row but not per-category rows | strict MB predicate = 3 (Jupiter INE682M01012, Cyient DLM INE055S01018, ideaForge INE349Y01013); broadened = 41 (SME 22 / MB 19); e6053e7 nulled 32 cells then 26cd1fd re-introduced 0 | Cross-field rule (= I1-x); gate to MB or "Σcategories ≠ total" so legitimate SME QIB=0 is not flagged | now (design) | task_15, 19, 20 | CR-O3 |
| **O-4** | `gmp_pct = 0` on premium-listing rows | LOW | open | entered via `src=ipocentral`(8)/`websearch`(2) — NEITHER source has a scraper in-repo (external/one-off ingestion); sharescart already NULLs `--` so it is NOT the source | 10 rows; 5 had pop ≥+20% (Vivo +333% INE0IA701014, KN Agri +105% INE0KNW01016, Krishna Defence INE0J5601015, Timescan INE0IJY01014); 9/10 in `gmp_deep_hunter`'s year≤2022 window but its `.isna()` filter skips literal-0 | 0→NULL first (PREREQUISITE for the hunters to pick them up), then backfill from a non-investorgain GMP source (investorgain itself has `gmp_rs=0` for all matched) | needs-external-data (new GMP source) | task_15 | CR-I1 |

### 4.4 FINANCIALS (task_16)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **O-5/O-7** | Per-year & TTM EPS ~1000×-magnitude values | MED | handled-before (caveat in `data_review.md:46-47`) | NOT a parse/÷1000 bug — a REAL share-base discontinuity faithfully copied from Screener (tiny pre-IPO share count → huge EPS). `|eps_yr1/eps_yr3|∈[990,1010]` returns 0 rows (kills the ÷1000 fix) | `\|eps_yr1\|>1000`=51, `\|eps_yr2\|>1000`=57, yr3=25, `eps_ttm`>2000=3; cross-year share-base break=95 rows (yr3 clean in 90/95). Honasa INE0J5401028 max magnitude 1,306,098. `eps_ttm` IS consumed (issue-time P/E via h2/hmvp) | A2 (floor): null a per-year EPS whose implied share-base differs >~50× from latest year, code "published-but-not-comparable". A1 (recompute on constant post-issue share base) BLOCKED on the unsolved share-count work (shared with O-12). NOT ÷1000 | now (A2); A1 blocked | task_16 | CR-EPS |
| **O-5b** | EPS↔PAT sign-consistency break (new validity class) | MED | open | wrong-entity join / stale year / unit-parse — eps and pat must share sign | `sign(eps_ttm)≠sign(pre_ipo_pat)` = 34 rows (per-year analog applies too) | Validity rule → `quality==dirty` | now (design) | task_16 | CR-EPS |
| **O-6** | `net_sales_yr3 = 0` + non-equity contamination of the equity financials table | MED | fixed-still-holds (margin half) + open (contamination) | the "poisons margins" half is FALSE — `if sales and pat` guard skips zero-sales (0 rows poisoned, holds). The real contamination = REIT/InvIT in the equity sales column | `net_sales_yr3==0`=13 (equity 5 / reit 4 / invit 4); the 5 BIG offenders are ALL REIT/InvIT (Mindspace INE0CCU25019, Bharat Highways INE0NHL23019, IRB INE183W23014, Embassy INE041025011, Citius INE2Q7823014); per-year broader: `net_sales_yr1=0`=32, yr2=20; `pat_yr*=0`=184/102/61 | Keep the zero-guard (holds); I1 3-state for the 17 literal-`pre_ipo_net_sales=0`; gate equity table by `instrument_type==equity` → hand to task_05b. task_12: n14 `declining_pat` lacks the `p1>0` guard `declining_revenue` has → false flags | now (design) | task_16, 05b, 19 | CR-I1, CR-nonequity |
| **O-6b** | Other never-audited financial columns carry the same 0/invalid classes | MED | open | I1 + invalid-value classes never inventoried for these columns | `operating_profit_yr1/2/3=0`: 77/51/29 (yr3 read live by n14); `pe_ratio`: 46 NEGATIVE + 2 >500 (negative P/E should be NULL, is a Gower feature in analogs.py:22); `pat_ttm_cr=0`: 19 | Same I1 missing-policy; validity rule: loss-maker P/E → null (not negative) | now (design) | task_16 | CR-I1, CR-pe |
| **O-9** | `pre_ipo_debt_equity` / `pre_ipo_roe_pct` detonation via near-zero/negative shareholder-funds denominator | HIGH | open (CONFIRMS the audit's 9-row scope; NOT the naive 54-row sign test) | `sf=equity_capital+reserves`; `roe=pat/sf`, `de=brw/sf`; a near-zero/negative `sf` denominator detonates the ratio. The `if sf` guard catches exactly-0 but NOT negative/tiny-positive (negative is truthy) | naive `sign(D/E)≠sign(ROE)` flags 54 (~45 are VALID positive-equity loss-makers — Paytm/Zomato/Swiggy/Delhivery/Nykaa); the real bug = 9 with `de<0`. On `sf` directly: 19 rows `sf<=0` (17 carry a non-null derived ROE/DE = the quarantine set), 25 rows `|sf|<1`. Indiqube INE06ST01018 ROE 1400% / D/E −409.5 | DROP the naive sign test; `shareholder_funds`-denominator-validity rule (`sf<=0` OR tiny-`sf` → quarantine ROE/DE); keep loss-maker `+D/E/−ROE` as valid | now (design) | task_16 | CR-sf |
| **O-10** | `pre_ipo_pat_margin_pct` extreme one-offs from tiny-but-nonzero sales denominator | HIGH (raised from MED — corrupts a VALIDATED in-score flag) | open | wrong-but-nonzero sales passes the `if sales` guard. Ujjivan INE334L01012 `sales=18` is the RAW screener value verbatim (NBFC "sales"≠topline / wrong-FY) — NO pipeline truncation | `\|margin\|>80`=11 rows (Ujjivan 983%, Manas 250%, Transpact −231%); `<25 sales & \|margin\|>80`=11 (the set feeding the VALIDATED `tiny_sales_lt25cr` flag — false-positive on Ujjivan, a multibagger bank). `pre_ipo_net_sales` is an IC-0.20 predictor | Latest-year-sales denominator-validity rule (implausible-vs-PAT signature → `quality==dirty`); cross-source corroborate vs `screener_financials_review.csv` (21 rows). NO clamping (T-4 lesson; note `scorecard.py` `np.clip` already masks Indiqube D/E−409.5→debt-score 100 — quarantine must be UPSTREAM) | now (design) | task_16 | CR-margin |
| **O-fin-asof** | Financials carry no as-of attribute; sharescart has post-IPO contamination | MED | open | financials are TIME-VARYING; `sources.md:32` warns sharescart 3yr financials may be as-of POST-listing | all financial fields | As-of attribute per field (at-IPO RHP snapshot vs current); fallback order DRHP-recovered (`drhp_recovered.csv`, 16 rows) → screener pre-listing FY → sharescart | now (design) | task_16, 02 | CR-asof |
| **O-fin-cov** | Financials coverage cliff by cohort | MED | open | longterm cohort under-sourced | `pre_ipo_pat` nonnull: boom 1318/1357 (97%) vs longterm 602/1027 (59%) | Record per-cohort fill rate; close with DRHP-recovered + screener longterm; biases t9/n7/n13 | needs-external-data | task_16, 02, 19 | CR-cov |

### 4.5 MARKET CAP (task_17)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **D-3** | Market-cap as-of LEAK — `market_cap_cr`/`market_cap_class` is CURRENT (post-outcome) cap, not at-IPO, leaking future state into the predictor | CRITICAL | open | one ambiguous column conflates "size at IPO" (the right analog feature) with "size now" (outcome-contaminated). Single root of O-8 + the failed implied-shares check + the D-3 leak + the circular migration rank-IC 0.564 | `market_cap_class` consumed by analogs.py (gate L104, ladder L129, Gower L141), weights.py:20, forward_test.py:27, predict.py — all leak surfaces. `market_cap_cr` non-null 1523 / null 861 | Split into `market_cap_at_ipo_cr` (at-IPO, predictor/analog/weight input) + `market_cap_current_cr` (+`_asof_date`, display-only, NEVER a predictor input). Bind predictor/analogs/weights/forward_test to the at-IPO field | now (design); at-IPO sourcing needed | task_17, 02 | CR-asof, CR-mcap |
| **O-8** | `market_cap_cr < issue_size_cr` | MED | open (PARTIAL reclassification) | comparing a CURRENT cap to an AT-IPO issue size is ill-posed for crashed stocks | 169 rows (0<mc<issue); 43 gross (>10×) = 36 wipeout/1 loser/6 NaN/0 winners; 3 extreme >50× (Tara INE799L01016 145×, Zylog INE225I01026 61×, Future Supply INE935Q01015 54×) are in NEITHER 88-audit Category | Reclassify as as-of artifact ONLY for Cat-2/web-corroborated rows; route the 43 gross / 3 extreme to quarantine pending Cat-1/Cat-2 cross-check (a 145× ratio is also a missing-split signature). NOT a blanket "not-a-bug" | now (design) | task_17, 14/20 | CR-mcap |
| **O-12** | Bajaj Corp wrong-entity Screener join — `market_cap_cr` ~36× too large | HIGH | open | `search_company` (screener.py:88) is NAME-keyed (not ISIN) → matched the wrong (larger) entity for the cap | Bajaj INE933K01021 `market_cap_cr=292,355` (implied 529.6 cr shares vs real ~14.75 cr) | The proposed implied-shares guard (current-cap basis) is WITHDRAWN — it had ~700 FPs (716/1479, 48%; flags Info Edge 123×, Central Bank 115×). Use the WELL-POSED at-IPO-cap band `[1,20]×` (1 FP on 90 rows). Record matched entity id+name (task_07). Systemic wrong-entity sweep needed (Bajaj is not the only one) | now (design); at-IPO sourcing needed | task_17, 07 | CR-id, CR-mcap |
| **O-15** | `market_cap_cr == 0` but `market_cap_class == micro` (class silently lies) | MED | open | I1 instance: `mktcap_class()` returns `micro` on a real `0.0`, `''` on None — and the upstream stored literal `'0'`. TWO writers (company_meta 08:163-189 + 03f boom-fill 08:224-230) | 7 rows (Supreme INE971P01012, Bansal INE668X01018, Pushpanjali INE728W01012, Powerful INE650Z01011, Soni Soya INE301Z01011, CKP INE418Y01016, Artedz INE00CO01016) | Harden `mktcap_class()` at the FUNCTION level: require non-null `>0` cap → null; ALSO convert the `''` sentinel → canonical null; I1 0→NaN upstream. Resolves the audit's "12 vs 7" → 7 actual zeros | now (design) | task_17, 19 | CR-I1, CR-mcap |
| **O-mcap-val** | `kpi_market_cap_post_ipo` (the proposed at-IPO PRIMARY field) is itself UNVETTED | HIGH | open | no `_src`, no validity check; ≥1 gross parse error | HDFC AMC INE127D01025 = 7.8 cr vs issue 2,800 (real ~23,000 cr); 23/90 nonnull rows <50cr. Present on only 90 rows, ALL longterm, 0% boom (03g sources only `urls_longterm.csv`) | Parse-quality pass (kpi cap ≈ `issue_price × post-issue shares`) + I1 0→NaN + `_src` provenance BEFORE adopting as primary; boom derivation is the de-facto primary | now (design) | task_17 | CR-mcap, CR-prov3 |

### 4.6 DATES / IDENTITY / BANDS / ONE-OFFS (task_18)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **O-11** | Date-ordering violation (`close_date > listing_date`) | LOW | open | wrong-year/transposition in `listing_date` (for Veto + GCM listing precedes OPEN too → listing is the corrupt field) | 3 rows: 20 Microns INE144J01027, Veto INE918N01018, GCM INE168O01026. Plus 14 NULL listing_date escape the rule; 15 rows exceed a 30d close→listing gap (Vaswani INE590L01019 = 140d) | Whole-chain `open ≤ close ≤ listing` validity rule with an applicability gate (all-three-present + has_price_history), identifying WHICH bound is violated; resolve against first row of `data/prices/<isin>.csv`; era-calibrated close→listing gap bound | now (design) | task_18 | CR-date |
| **O-13** | Price bands — only `price_band_low` exists; band validity un-implementable; 1 inversion | MED | open | NO `price_band_high` column (band half-captured); `band_low<issue` is NORMAL (683 rows), not an error | 1 true inversion `band_low>issue` (Insolation INE0LGX01024 131>38); Enser INE0R9I01021 band_low=10 wrong but caught CROSS-FIELD (overturns the audit's "2 inverted bands"); `price_band_low` BLANK = 1498 | Add `price_band_high` (sharescart cap) → derive width; rule `band_low ≤ issue ≤ band_high` (band_high is a PREREQUISITE). Audit's `≤1.05×band_low` proxy REJECTED (over-catches 581/886). Until then ship `band_low ≤ issue` only | now (`band_low≤issue`); full rule needs band_high source | task_18, 01 | CR-band |
| **O-14** | `min_investment_rs` zeros + massive coverage gap | LOW | open | I1 zero on 18 SME rows; longterm cohort never enriched | 18 literal-zero + 1480 blank = 1498/2384 (63%) missing; only 886 positive. The 18 zeros have lot + issue_price (NOT band_low — all 18 blank) | I1 0→NULL+flag; optionally DERIVE `min_inv ≈ lot × issue_price` (status=derived; CFF INE0NJ001013 400×165=66,000). The 1480 blanks = source-enrichment gap (owner backfill) | now (18 derivable); 1480 needs backfill | task_18, 19 | CR-I1, CR-mininv |
| **O-16a** | Std Chartered IDR mislabeled `instrument_type=equity` + literal-0 issue_amount | MED | open | a non-equity (IDR) row hidden inside `equity` leaks into equity-only analyses; `issue_amount_cr=0.0` is an I1 instance | INE028L21018; `instrument_type` dist {equity:2329, fpo:38, reit:9, invit:8} (no idr/ncd value) | DECLARATIVE ISIN-structure rule: `isin[7]` security-type digit derives family — `isin[7]=='2'` selects exactly the 18 trust/DR units, and the ONLY `equity` row among them is the IDR (zero FP/FN, no string matching). Name patterns SECONDARY. Hand to task_05b/07. I1 0→null for `issue_amount_cr` | now (design) | task_18, 05b, 07, 19 | CR-instr, CR-I1 |
| **O-16b** | Newmalayalam Steel `lot_size_shares == 1` | LOW | open | ingestion error (no board has a 1-share lot); the cross-field rule MISSES it (90≈1×85 is a self-consistent co-corrupted triple) | INE0TP801012 (the only lot==1 row) | INDEPENDENT lot_size plausibility floor (lot==1 / single-digit implausible) — independent of mutual-consistency checks | now (design) | task_18 | CR-lot |
| **O-16c** | Wakefit promoter post>pre inversion | MED | open | promoter stake should fall after IPO (dilution) | Wakefit INE0E7301029 pre 33.56 / post 37.39 | `promoter_post ≤ promoter_pre` invariant (with fresh-issue-only exceptions) → hand to task_16 (financials/structural) | now (design) | task_18 → task_16 | CR-promoter |
| **ID-verify** | Identity-verification columns: a dead column + 1027 never-verified + a 39-row disagreement | MED | handled-before (registered in `data_review.md` §B at 27 → now 38) | longterm cohort never identity-checked; `isin_xchg_check` and `name_isin_check` answer different questions | `ticker_needs_review` blank 100% (DEAD); blank `isin_xchg_check`/`name_isin_check`=1027 (never verified); they DISAGREE on 39 rows (`no_ref` now 38, was 27); 283 rows have NO usable trading ticker; 4 overlapping ticker columns | Encode "not-verified" as an explicit present/absent state (NOT silent trust); COMPOSITE verdict preserving both dimensions (not a collapse); single canonical resolved trading-symbol with fallback order; retire or populate `ticker_needs_review`. Reconcile 27→38 drift | now (design); backfill needs data | task_18, 07 | CR-id |
| **face-value** | `face_value` 79% blank (split-detection role) | LOW | open | longterm cohort un-enriched | blank 1886/2384; populated dist all in {1,2,5,10} (0 out-of-set today) | Validity rule (flag outside {1,2,5,10}); cross-link task_14 (face-value split changes ISIN); 79% gap = owner backfill | now (rule); backfill needs data | task_18, 14 | CR-face |
| **anchor-cov** | `anchor_allocation_cr` coverage gap | LOW | open | un-enriched | blank 1487/2384 | Present/absent classification; owner backfill decision | needs-external-data | task_18 | CR-cov |
| **listing_at** | `listing_at` un-normalized free text | LOW | open | inconsistent order + legacy token | `BSE, NSE` vs `NSE, BSE`; legacy `MCX-SX` | Normalize to a canonical exchange-set token | now (design) | task_18 | CR-norm |

### 4.7 RETURNS / OUTCOMES (task_19) + ENVELOPE (task_19/20)

| ID | Title | Sev | Status | Root cause | Affected fields / counts | Resolution approach | Resolvable | Task(s) | CR-* |
|---|---|---|---|---|---|---|---|---|---|
| **O-1** | `listing_open = 0` raw + mislabeled `listing_metrics_status='ok'` | LOW | handled-before (contained one-off) | source-origin zero — raw chittorgarh `details.csv` itself has `listing_open='0.00'`. Layer-3 uses the correct `adj_listing_open=30.0`, so contained | Udayshivakumar INE0N0Y01013. Predicate `raw∈{0,blank} AND adj>0 AND status='ok'` = 1 row (a one-off, NOT a class) | Repair raw from the adjusted value OR downgrade `listing_metrics_status` from `ok` (it relied on the adjusted-column rescue). No general rule warranted (count=1) | now (design) | task_19 | CR-status |
| **T-2** | Envelope violation (`trough ≤ endpoint ≤ peak`) — but these are REAL paths, must NOT be clamped | MED | fixed-still-holds (clamp REMOVED; construction sound) | the MFE/MAE clamp was removed; envelope now relies on corp-actions being perfect, which D-1 shows they are not | 43 violations / 32 stocks (predicate NOT pinned to a column/horizon → not independently reproducible; task_19 to re-state). Offender set dominated by 88-audit Category-2 verified-genuine crashes. Inox INE312H01016 is the single offender that is REAL data (+604% multibagger via PVR merger at current; genuine drawdown at 3y) | Do NOT clamp; the cleaning model must carry the Cat-2 whitelist (67 ISINs) and whitelist the RIGHT horizon's path. Envelope correctness depends on the D-1 fix (task_14) | now (design); depends on D-1 | task_19, 14, 20 | CR-envelope |

---

## 5. THE Category-2 PROTECTIVE WHITELIST (carry into the cleaning model)

The 67 ISINs in `unresolved_88_mismatches_audit.md` Category-2 are **verified-genuine crashes with ZERO unrecorded
corp action** — the rebuild must NOT manufacture a split/bonus "correction" for any of them. Canonical examples:
Aster Silicates INE900K01012 (−100% Compulsory Delisting, NOT "−91.6%"), Future Capital INE688I01017, Maytas
INE369I01014, **Inox INE312H01016** (the single T-2 envelope offender that is REAL data — a +604% multibagger via
PVR merger, NOT a wipeout). **Key correction (task_14/17/20):** the "−91.6%"/"−39.8%" figures the charter attached
to Aster/Inox are the 88-audit COVERAGE-DIFF %, NOT returns — cite real substrate values
(`current_return_from_issue`, delisting terminal), never the coverage-diff %. The whitelist concept must
distinguish "genuine extreme path (any direction)" from "genuine wipeout."

---

## 6. NOTES ON COMPLETENESS / DE-DUPLICATION

- **I1 is registered once (4.1)** with every per-field instance cross-referenced into its area row (O-2, O-4, O-6,
  O-15, O-16a, O-14, O-6b). Counts for the per-field instances live in those rows.
- **The corp-action over-count** appears in task_14 (authoritative re-audit), task_19 (envelope cross-link), and
  task_20 (substrate cross-check) — registered once as D-1 + its sub-issues (D-1-fp, D-1-prec, etc.).
- **The market-cap as-of leak** is D-3 (task_17) — distinct from O-8 (the symptom) and O-15 (the zeros), all in 4.5.
- **DOC/STRUCT items** (DOC-2/3/4/7, STRUCT-1, C-2) are NON-DATA and are intentionally EXCLUDED from this data
  register; task_20 logged them separately as genuinely-landed structural/doc fixes.
- **One overlay gap not a data-cell issue:** INE399K01017 (Indiabulls Power) Cat-1 bonus was never written to any
  overlay (ratio unknown) — pinned in §3.

---

## 7. PROVENANCE / CONFIDENCE

Every count and example above is the OWNING TASK's read-only reproduction against `data/master/ipo_analysis.csv`
(2,384 rows) on 2026-06-17. **None of the owning tasks satisfied its review-loop stop rule** (≥2 consecutive
independent clean fresh-agent rounds); task_15/16/17/18/19/20 all mark the stop rule UNMET, and
`night_run_2026-06-17_review_log.md` was ABSENT on disk (task_20 §2/OQ6). **Therefore: NOT FINAL, counts
draft-grade.** This register is a consolidation for the owner's morning review, not an approved artifact.


---

## PART C — TASK-FILE-ONLY BUILD HAZARDS (recovered from task_14 / task_17 / task_19 — these existed in NEITHER the register NOR the consolidated docs)

### C.0 Tested & NOT viable sources (DO NOT re-add) — from design §8.3
BSE official IPO API · ipocentral (the O-4 GMP-0 origin) · trendlyne · moneycontrol financials. Re-adding any wastes effort / re-introduces known-bad data.

### C.1 Corp-actions (task_14) — the highest-impact build inputs
- **`issue_price_adj < Rs 1` over-adjustment detector (cleanest zero-FP signal):** exactly 8 rows, all genuine over-adjustments —
  HARDWYN 0.357, SBC 0.489, SIKKO 0.533, RAJMET 0.578, LAL 0.647, FCL 0.700, MKPL 0.778, ROLEXRINGS 0.900. Use as a second detector alongside the price-gap arbiter.
- **Two DEPLOYED + re-audited remediations that HOLD** (must not be undone): (a) symbol+ISIN feed-matching fix (116→383 stocks fixed; IRCTC +59%→+697%);
  (b) `pipeline/listing_remediation.py` inferred_split remediation. `listing_metrics_status` distribution: ok 1935 / unreliable_coverage 223 / recovered_bhavcopy 153 / inferred_split 57 / '' 16.
- **INTERACTION HAZARD — the still-active MFE/MAE scale-inversion clamp (~75 rows, flag `mfe_mae_clamped`):** any corp-action redesign that changes applied
  factors MUST re-derive both the inferred_split set AND the scale-inversion clamp, or it silently shifts which rows are clamped.
- **53-row evidence catalog taxonomy:** buckets count-conflict 14 / ratio-conflict 17 / reverse-split 21; verdicts resolve-apply-once 28 / resolve-correct-ratio 17 /
  **STAYS-FLAGGED 6** / resolve-reverse 2. The 6 still-unresolved: CMMIPL, COOLCAPS, SILVERTUC, VAISHALI, INDUSFILA, BANSAL. Worked: KAUSHALYA (1:100→adj 6000), ISHAN (10:1+2:1→30→adj 2.667).
- **Ratio-interpretation ambiguity (OPEN risk class):** Darshan INE671T01028 "Bonus 11:10" → 1.1 vs 2.1 — any `X:Y` bonus with ambiguous wording needs gap re-confirmation (the manual ratio itself may be wrong, not just defeated by the join).
- **`corp_actions_yahoo_only.csv` schema (NO isin/ex_date/ratio_factor):** columns `symbol, original_symbol, yahoo_date, yahoo_ratio, is_bse_code, status`. Any overlay/diff against it
  must key by `original_symbol/yahoo_date`, NOT isin/ex_date. 285/354 are numeric BSE codes that can never match the NSE-symbol substrate.
- **`manual_overrides.csv` = 3 market_maker rows ONLY** (INE00D001018, INE05FR01029, INE813V01022) — ZERO corp-action fixes there (corrects the charter's framing; Cat-1 fixes lived in the OTHER overlay file, the `07` consumer).
- **Companion file counts:** `corp_actions.csv` 1509 · `corp_actions_matches.csv` 514 · `corp_actions_discrepancies.csv` 16 · 44 symbol-added-out-of-window · 37 suspect-reverse-split (WAAREEINDO/SWANDEF/SHEKHAWATI/SEJALLTD) · `verification_2026-05-31` 5-row overlay (AVL/INA/MICEL/TTFL, HOLDS).
- D-1-ratio sub-breakdown: of the 350 rows in (1.0,1.5], 141 are exactly 1.5, 40 are 1.2, 32 are 1.1 (calibrates the ratio-tolerance band).

### C.2 Market-cap (task_17) — bears on BL-1 sizing
- **The 90-row at-IPO-cap coverage may be UNDERSTATED:** 03g's `except` (L43-45) prints but returns a partial dict → a fetch/parse failure persists as a missing key,
  indistinguishable from "source never published". So the real at-IPO-cap gap may be larger than 90 (relevant to BL-1 sizing) — and is itself an I1 instance to fix.
- **`market_cap_class` re-bucketing churn (Open-Q 4b):** switching the class to the at-IPO cap re-buckets rows; measure churn on the 67 dual-cap rows BEFORE finalizing the D-3 binding,
  and decide whether to re-calibrate the class cut-points (300 / 2000 / 20000) on an at-IPO basis.
- **At-IPO band `[1,20]×` empirical basis:** the 90-row implied-shares distribution = mean 3.646 / median 3.554 / max 9.996 / min 0.0028 → `[1,20]×` gives 1 FP on 90. (90, not 67, is the right denominator.)
- More wrong-entity FPs to sweep: Time Technoplast 127×, Transformers & Rectifiers 100×, South Indian Bank FPO, Patel Engineering FPO. Parser sites: `screener.py:88/172`, `screener_prices.py:79`, `03g…py:39`, `chittorgarh.py:228`, `page_marketcap` L98-100.

### C.3 Financials zeros (task_19) — for the task_16 hand-off
- Financial-zero hand-off counts (all four, so the MIXED class is quantified): `pat_yr3==0` 61 · `operating_profit_yr3==0` 29 · **`eps_yr3==0` 15** · **`operating_cf_yr3==0` 90**.
- **5 equity `net_sales_yr3=0` ISINs** (the recovery rule must not fabricate a sales figure here; substrate names blank → ISINs are the only handle); two of them (INE320H01019, INE009Q01019) also have `net_sales_yr2==0` and need a per-row check (may be genuinely unavailable, not a parse-fail).

### C.4 Subscription / GMP recoveries the targets under-state
- **O-2 network-free SME recovery:** flip the `03d` guard → repairs 75/106 SME 0-rows from the existing ipowatch cache (no network). Distinct from the 88-row arithmetic derivation + 18-row min_inv.
- **O-4 (GMP=0) — has NO CR home; the 2-step fix:** (1) `0 → NULL` FIRST (prerequisite — so `gmp_deep_hunter`'s `.isna()` filter will pick it up), THEN (2) backfill from a NON-investorgain source
  (investorgain itself has `gmp_rs=0` for all matched, so it can't self-cure). Named offenders: Vivo +333% (INE0IA701014), KN Agri +105%, Krishna Defence, Timescan. Needs a CR-GMP rule + network (OD-4 gated).
