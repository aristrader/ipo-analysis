# task_17 — Market-cap: the issue register (O-8, O-12, O-15) + as-of semantics

> **STATUS: NOT FINAL — design/think only.** Per the night-run charter (2026-06-17). No code, no pipeline
> changes. All numbers below were produced read-only against `data/master/ipo_analysis.csv` (2,384 rows) on
> 2026-06-17. Owner owns the design; everything here is a proposal for review.

---

## 1) Scope
Decide how the data architecture should treat the **market-cap field family** and the **as-of-date semantics**
that contaminate it. Concretely, this task owns:
- **O-8** `market_cap_cr < issue_size_cr` (169 rows + zeros).
- **O-12** Bajaj Corp wrong-entity Screener join (`market_cap_cr` ~36× too large).
- **O-15** 7 micro rows with `market_cap_cr == 0` but `market_cap_class == micro`.
- The **as-of class** that ties D-3 (the look-ahead leak): `market_cap_cr` / `market_cap_class` is the
  company's cap **as of the scrape** (current/post-outcome), not at-IPO.
- The proposed **implied-shares cross-check** (O-12's suggested systemic guard) — reproduce and judge it.

The single question: **what is the correct as-of contract, missing/zero policy, and validity check for the
market-cap family, such that the field is CORRECT, the encoding is CLEAN/minimal-flags, and it EXTENDS to
live/listed-stock universes without re-architecting?**

---

## 2) Ground-truth inputs (read, by file path)
- `docs/research/alignment_audit_2026-06-16.md` — O-8 (L541-543), O-12 (L560-562), O-15 (L567), D-3 (L217-237),
  cross-cutting I1 "missing coded as 0" (L507-515), proposed implied-shares check (L575).
- `pipeline/08_build_universe.py` — `mktcap_class()` (L163-173, returns `''` on None — NOT null; see re-audit);
  company_meta attach (L151-192, sets `market_cap_cr` + `market_cap_class` from Screener; the no-meta branch at
  L177-184 sets `market_cap_class=''` (L183) too); 03f `sector_mcap` fill-only recovery (L196-232);
  03g `kpi_market_cap_post_ipo` recovery (L241-...).
- `scrapers/screener.py` — `page_marketcap()` (L98-100): full regex (verified L98) is
  `r'Market Cap\s*</span>\s*<span[^>]*>\s*₹?\s*<span class="number">([\d.,]+)</span>'`;
  this is **current** cap from the live Screener company page. **`search_company()` (L88-94)** = the name→entity
  resolver that produced the Bajaj wrong-entity join (re-exported/used at `scrapers/screener_prices.py:79` and
  `scrapers/screener.py:172`). _(Note: this is the actual symbol; the field is keyed by NAME, not ISIN.)_
- `pipeline/03g_kpi_recovery.py` — scrapes `kpi_market_cap_post_ipo` from the Chittorgarh KPI-table "Market Cap"
  row (L39; cf. `scrapers/chittorgarh.py:228`). **As-of caveat (UNVERIFIED, needs confirming):** this is
  *inferred* to be a post-issue-at-issue-price (at-IPO) cap (the ~3.6× issue ratio is consistent), but the task
  ASSERTS this — it should be spot-checked (kpi cap ≈ issue_price × post-issue shares for a few ISINs) before being
  adopted as the canonical at-IPO field. **Fetch-failure caveat (I1/present-vs-absent):** L43-45 is a broad
  `except Exception as e` that **prints** the error (`print(f"Error fetching {url}: {e}")`) and then returns the
  partial `rec` dict (the key is simply absent on failure) — so it is NOT silent (it logs to stdout) and not
  strictly naked (it binds `as e`), but in the persisted CSV a fetch/parse failure is recorded as a missing key,
  **indistinguishable from "source never published".** So the 90-row coverage may itself be UNDERSTATED by fetch
  failures, and the present/absent provenance (task_03) must be built for this field too (cross-link task_19 I1 /
  task_03). **Structural cohort scope (verified, L48):** the recovery sources ONLY
  `data/raw/chittorgarh/urls_longterm.csv`, so by construction it can NEVER populate boom rows — the 0% boom
  coverage of the at-IPO cap (§3) is a DESIGNED input scope, not a coverage accident. This makes the boom gap
  actionable for task_02 (sourcing/fallback).
- **FULL `market_cap_class` consumer audit (verified via grep — the D-3 binding list, charter feature↔data #9):**
  - **Predictor-path (MUST bind to the at-IPO field — these are the leak surfaces):**
    `layer3/predictor/analogs.py` — hard gate (L104-106), distance ladder rung (L129-131), Gower feature (L141);
    `layer3/predictor/weights.py:20` — in `_QUERY_FEATS` (point-in-time weight derivation);
    **`layer3/forward_test.py:27`** — in `QUERY_FEATURES` (the OUT-OF-SAMPLE harness; an identical look-ahead leak
    path to weights.py — easy to miss, so explicitly added to the D-3 binding list, see §7 Open-Q2);
    `layer3/predictor/predict.py:24,49` — query echo / display of the class.
  - **Findings/report-path (decide leak exposure case-by-case, mirroring n14's deliberate exclusion):**
    `layer3/findings/n14_wipeout_anatomy.py:32,64,189` — **deliberately excludes** `market_cap_class` as
    reverse-causal ("a wiped-out name reads micro *because* it crashed"); `layer3/findings/n11_sc_divergence.py:33`
    (micro/small filter), `layer3/findings/n4_issue_size.py:44-54` (per-class view), `layer3/spine.py:46`
    (segment filter), `layer3/report.py:13` (ID column) — each must be assessed for whether it consumes the
    current (leaky) class; n4/n11/spine/report were NOT yet individually leak-assessed (flagged for §7/task_12).
- **`rules/index.md`** (PRIOR-VERDICT ground truth — charter STAGE-5 lens c) — already carries: (a) micro-mcap as a
  wipeout flag = **REJECTED**, reverse-causal because `market_cap_class` is CURRENT cap (L29, L85); (b) the
  **migration circular-mcap** resolution (L275-281): market_cap_cr IC 0.564 was CIRCULAR (current cap, grew-into-it,
  reverse-causation) → **DISCARDED**, with migrants 16.9× vs trapped 3.3× mcap/issue ratios already measured
  (`migration_predictor_2026-06-11.md`). This task's reverse-causality and wipeout-reclassification claims rest on
  these prior verdicts — they are cited here, not re-derived from scratch.
- **`docs/research/unresolved_88_mismatches_audit.md`** (the 88-audit — PROTECTIVE ground truth, charter Group-B) —
  **Category 1** = 21 decided-but-unapplied missing splits/bonuses (with ratios); **Category 2** = 67 manually
  verified GENUINE crashes/wipeouts with ZERO unrecorded corp action. O-8's "reclassify as real wipeout" claims
  MUST be cross-checked against Cat-2 (and Cat-1) before declaring not-a-bug — see §3 re-audit.
- `data/master/ipo_analysis.csv` — the substrate (counts below all from this file via pandas).

Market-cap columns present in the substrate: `market_cap_cr`, `market_cap_class`, `kpi_market_cap_post_ipo`
(an **at-IPO** cap, sparse), plus the inputs `issue_size_cr`, `issue_price`, `current_price`.
**Schema-drift flag (→ task_01):** NONE of `market_cap_cr` / `market_cap_class` / `kpi_market_cap_post_ipo`
is documented in `docs/schema.md` (verified: grep returns zero entries for the family). The whole market-cap
family is undocumented in the project's nominal schema source of truth — an O-10-class schema/substrate drift. The
new at-IPO/current fields + class rule proposed below MUST be ADDED to schema.md (hand off to task_01).
**Provenance-drift flag (→ task_03):** `market_cap_cr` has **NO `_src` column** while 15 peer fields do
(verified the exact 15: `issue_size_cr_src`, `fresh_issue_cr_src`, `ofs_cr_src`, `gmp_pct_src`, `pat_yr3_src`,
`sub_total_x_src`, … — note `issue_price_src` does NOT exist; the issue-side `_src` that exists is
`issue_size_cr_src`). The proposed
`market_cap_*_asof/_src` design must EXTEND task_03's existing `_src` provenance scheme (source-never-published /
fetch-parse-failed / real-zero), not invent a bespoke per-field as-of attribute (north-star: single source of truth).

---

## 3) Reproduce existing issues + re-audit existing "fixes" against CURRENT data

### Field census (ground truth, 2,384 rows)
- `market_cap_cr`: non-null **1,523**; `== 0` **7**; null **861**.
- `market_cap_class`: `NaN` 861 · `micro` 746 · `small` 317 · `mid` 327 · `large` 133.
- `kpi_market_cap_post_ipo` (the at-IPO cap): non-null **only 90**; `==0` 0. Both at-IPO and current cap present
  on only **67** rows. **COHORT SKEW (critical, verified):** all 90 at-IPO-cap rows are `cohort == longterm`
  (2006-19); **ZERO are boom** (boom = 1,357 rows, 57% of the substrate). **This is STRUCTURAL, not an accident:**
  `pipeline/03g_kpi_recovery.py:48` sources only `data/raw/chittorgarh/urls_longterm.csv`, so the recovery can
  NEVER populate boom rows by construction. Consequence: the field elevated to "primary" below is 0% covered on the
  majority/most-relevant cohort — so on the boom cohort (the de-facto majority) the fallback derivation (Option C /
  issue_price × post-issue shares) IS the de-facto primary, not an afterthought. Any band derived from the at-IPO
  cap is single-regime (longterm-only) until boom at-IPO cap is sourced (see §6/Open-Q + §7 sourcing).
- **Non-equity census (verified, → task_05b/task_10):** of 55 non-equity rows (`instrument_type` ∈ {fpo:38,
  reit:9, invit:8}), **39 carry `market_cap_cr`** and **39 carry `market_cap_class`** (large:14, mid:12, micro:11,
  small:2; 16 NaN). For an FPO/REIT/InvIT an "at-IPO snapshot" cap is semantically meaningless (already-listed
  entity) — only the current cap is a valid reading. The as-of split (at-IPO primary, current display-only) is
  therefore INVERTED for these instruments; see §7 and Open-Q.

### Sub-audit — `kpi_market_cap_post_ipo` VALUE quality (NEW; the proposed PRIMARY field is itself UNVETTED)
The proposal below elevates `kpi_market_cap_post_ipo` to the canonical at-IPO/analog/valuation/predictor anchor —
so its OWN value quality must be audited before adoption, not assumed. It carries **no `_src` column** and **no
validity check** of its own today (same provenance gap the task demands for the current cap). Census of implausible
values (verified, 2,384 rows):
- **23 / 90** non-null rows have `kpi_market_cap_post_ipo < 50 cr`; at least one is a flat-impossible PARSE ERROR:
  **HDFC AMC `INE127D01025`** has `kpi_market_cap_post_ipo = 7.8 cr` against `issue_size_cr = 2,800` and
  `issue_price = 1,100` (HDFC AMC's real at-IPO cap was ~Rs 23,000 cr) — a gross mis-parse (wrong KPI-table cell /
  unit), NOT a "broken row". That is ≥1 gross corruption in a 90-row sample with the other 89 un-audited.
- The single sub-issue-size row flagged in §6 (ratio 0.003, min) IS this HDFC AMC row — it is a value-corruption,
  not merely an as-of ambiguity.
- The §2 as-of caveat only questions at-IPO-vs-current SEMANTICS; it never questioned VALUE correctness. Verdict:
  **before** `kpi_market_cap_post_ipo` is adopted as primary, it needs (a) a parse-quality pass (spot-check
  kpi cap ≈ `issue_price × post-issue shares` across the 90 rows — note the HDFC AMC value makes that check
  un-satisfiable for that row, so the spot-check itself surfaces the corruption), and (b) the same I1 `0→NaN` +
  `_src` provenance + validity rail the task demands for `market_cap_cr`. Until then treat the at-IPO cap as a
  flagged/dirty-routed CANDIDATE, not a trusted feature — and make the Option-B recommendation (§4/§7) CONDITIONAL
  on this audit (cross-link §7 Proposal #1, Open-Q).

### O-15 — `market_cap_cr == 0` but `class == micro` (reproduces EXACTLY: 7 rows)
All 7 are `instrument_type == equity`, all class=`micro`, all tiny SME issues (issue_size 5–15 cr):

| isin | company | market_cap_cr | class | issue_size_cr |
|---|---|---|---|---|
| INE971P01012 | Supreme (India) Impex | 0.0 | micro | 8 |
| INE668X01018 | Bansal Multiflex | 0.0 | micro | 6 |
| INE728W01012 | Pushpanjali Realms & Infratech | 0.0 | micro | 15 |
| INE650Z01011 | Powerful Technologies | 0.0 | micro | 14 |
| INE301Z01011 | Soni Soya Products | 0.0 | micro | 5 |
| INE418Y01016 | CKP Leisure | 0.0 | micro | 12 |
| INE00CO01016 | Artedz Fabs | 0.0 | micro | 8 |

**Re-audit:** O-15 is a textbook I1 instance — a parse/fetch-fail written as `0` instead of NaN. **Exact mechanism
(verified):** `mktcap_class()` (08_build_universe.py:163-173) returns `''` when `fnum(v) is None`, and returns
`micro` ONLY when `fnum` yields a real `0.0`. Verified: `fnum('')=None` (→ `''`), `fnum('0')=0.0` (→ `micro`). So
the "micro" lie fires specifically because the upstream stored the literal string `'0'` (a parse-fail-as-0, I1) —
NOT an empty cell. The class **silently lies** (says "micro" on no data). The fix is therefore **two-layered**:
(a) I1 `0→NaN` at the upstream write so `market_cap_cr` is null (not 0); AND (b) the class guard requires a
non-null, `>0` cap. Note the CURRENT missing sentinel is `''` (empty string), not null: `mktcap_class()` returns
`''` (L165) and the no-meta branch also sets `market_cap_class=''` (L183) — an I1 cousin (`''`-instead-of-missing).
The substrate happens to read these back as NaN, masking that the code emits `''`. Fixing only `0→micro` while
leaving the `''` sentinel re-introduces the same ambiguity — so the O-15/I1 fix must ALSO convert `''→null`
(canonical single null, consistent with task_03's present/absent encoding). **TWO writers, one chokepoint
(verified):** `market_cap_class` is derived in BOTH the company_meta attach branch (08_build_universe.py:163-189)
AND the 03f `sector_mcap` boom-gap fill (08_build_universe.py:224-230, which independently calls `mktcap_class(mc)`
when `market_cap_cr` is empty). The 03f path is the only one that touches boom rows at all (company_meta "covered
longterm well but barely touched boom" per the code comment), so a `'0'` arriving via the boom recovery produces
the SAME `0→micro` lie. 03g KPI recovery is a third potential writer. Therefore the fix must harden
`mktcap_class()` at the **function level** (null-on-0/empty), so ALL callers inherit it — NOT patch one writer.
(Open: confirm whether any of the 7 zero rows entered via 03f vs company_meta — they are all SME, and 03f is the
boom-only fill, so most likely company_meta, but the function-level fix is correct regardless.) The
alignment audit's own "O-8 says 12 zeros / O-15 says 7 zeros" discrepancy is resolved here: **there are 7 zeros
total**; the "12" figure in O-8 is stale (likely a pre-cleanup count). No prior fix exists for either — both OPEN.

### O-8 — `market_cap_cr < issue_size_cr` (reproduces: 169 rows, 0 < mc < issue)
- Total: **169** rows (excluding zeros). Of these, ratio (issue/mc) > 10: **43**; ratio > 50: **3**.
- The 3 extreme (>50×): Tara Jewels (145×), Zylog Systems (61×), Future Supply Chain (54×).
- **Re-audit of the audit's own claim ("only ~3 true 100× errors"):** I checked what the 43 gross (>10×) rows
  ARE. **36 carry `outcome_class == wipeout`, 1 loser, 6 NaN, 0 winners.** `current_price` (terminal/last price per
  the project's A1 convention) is present on 41/43. The *current* cap is genuinely a fraction of the at-IPO issue
  size because the stock collapsed — comparing a CURRENT cap to an AT-IPO issue size is ill-posed. **CAVEAT — the
  `wipeout` LABEL is NOT independent verification (charter Group-B / 88-audit):** `outcome_class == wipeout` is the
  substrate's OWN outcome label; it does NOT prove there is no unrecorded split/bonus. A 145×/61× cap/issue ratio is
  exactly the signature a MISSING split/bonus would ALSO produce, so "wipeout" alone cannot discharge O-8 as
  not-a-bug. **Cross-check done (verified, BOTH categories — applying the whitelist, not just citing it):** I grepped
  the 3 extreme rows by ISIN AND by symbol/name against `unresolved_88_mismatches_audit.md` Category 1
  (genuinely-missing corp actions, L5) and Category 2 (verified-genuine crashes, L32). Result: Zylog `INE225I01026`,
  Tara Jewels `INE799L01016`, Future Supply Chain `INE935Q01015` are in **NEITHER Category 1 NOR Category 2** (grep
  returns zero hits on ISIN or name). **So they are NOT independently corroborated as genuine crashes, AND not on
  the decided-missing-action list either** — they fall outside the protective whitelist entirely. (Same cross-check
  should be extended to all 43 gross >10× rows before any are reclassified — done here only for the 3 extreme.)
  **Corrected verdict:** O-8 is *probably* mostly an as-of-semantics artifact, but each "reclassified" row
  (especially the 43 gross >10× and the 3 extreme >50×) must be cross-checked against Cat-2 (genuine) AND Cat-1
  (missing-action) before being declared not-a-bug. Reclassify-as-real ONLY the rows that are in Cat-2 or
  web-evidenced; route the rest (incl. Zylog/Tara/Future Supply Chain) to **quarantine / owner**, not "stop running
  the check, all real". The protective whitelist (charter task_14/19/20) exists precisely to stop a rebuild from
  mislabeling a missing-corp-action artifact as a genuine crash. No prior fix — OPEN.

### O-12 — Bajaj Corp wrong-entity join (reproduces)
`INE933K01021` Bajaj Corp: `market_cap_cr = 292,355`, class=`large`, `issue_size_cr = 297`, `issue_price = 660`,
`current_price = 552.05`. Implied total shares = 292,355 × 1e7 / 552.05 / 1e7 = **529.6 cr shares** vs Bajaj
Corp's real ~14.75 cr → **35.9×** too large. Confirmed: `search_company` (screener.py:88) matched the wrong
(much larger) entity for the **cap**; `current_price` (552) is plausibly Bajaj's own. So the corruption is on
the **cap field specifically (the CURRENT cap), via the name→entity resolver. No prior fix — OPEN.
**Note (feeds §6/§7):** Bajaj has NO `kpi_market_cap_post_ipo` (verified: at-IPO cap present = False), so the
at-IPO-cap band proposed below STRUCTURALLY CANNOT catch it — see §6 Predicate 3 caveat.**

### Implied-shares cross-check (O-12's proposed systemic guard) — REPRODUCED, and it FAILS
The audit (L575) proposes: flag `market_cap_cr × 1e7 / price` diverging > 5× from the issue-derived share count.
I implemented it exactly: implied total shares = `market_cap_cr / current_price`; issue-derived shares =
`issue_size_cr / issue_price`; ratio = implied / issue-derived. **Exact evaluability predicate (verified):**
`market_cap_cr`, `current_price`, `issue_size_cr`, `issue_price` all non-null AND `current_price != 0` →
**1,479 evaluable** (the denominator is filter-sensitive: a stricter all-four-`> 0` filter gives 1,472; 34 rows
have `current_price == 0` and are excluded by the `!= 0` guard). The headline **716** flag count is robust — it
reproduces identically (716) under BOTH the 1,479 and the 1,472 filter, so the verdict is unaffected by the
denominator choice. 716 / 1,479 = 48.4%.

| threshold | rows flagged |
|---|---|
| ratio > 5× | **716** (48% of evaluable!) |
| ratio > 10× | 375 |
| ratio > 20× | 239 |
| ratio > 50× | 121 |
| ratio > 100× | 56 |

**This check is not viable as specified.** It flags Bajaj (good) but ALSO flags massive legitimate survivors:
Info Edge (123×), Central Bank of India (115×), Time Technoplast (127×), Transformers & Rectifiers (100×),
South Indian Bank FPO, Patel Engineering FPO. Root cause: **IPO shares sold are only ~5–30% of the company, and
companies grow/dilute/split for 10+ years after listing — so `current_cap / issue_size` is SUPPOSED to be large
for any successful old IPO.** The check conflates "wrong-entity join" with "company succeeded since IPO." It is
the SAME as-of-semantics error as O-8, just in the other direction. **Re-audit verdict: the proposed O-12 guard,
if implemented against the current (as-of-now) cap, would have ~700 false positives. Do not build it as written.**

---

## 4) Options (steelmanned; the obvious one challenged)

The obvious move is "add the implied-shares validity check + 0→NaN for the zeros and call it fixed." Step 6 shows
that obvious move is the broken one. So the real decision is about the **as-of contract** for the cap field.

### Option A — Keep ONE `market_cap_cr` (current cap), add a 0→NaN fix + the implied-shares check
- **Steelman:** minimal change; one column; the implied-shares check is already designed; current cap is what
  Screener gives for free.
- **Reject (correctness + clean):** the implied-shares check has a 48% false-positive rate (716 rows) BECAUSE the
  one column is current cap. You cannot validate a current cap against at-IPO inputs. Keeping a single
  as-of-ambiguous column is exactly what causes O-8, the failed check, AND the D-3 leak. Violates "give every
  time-varying field an explicit as-of attribute" (charter §9).

### Option B — Split into TWO explicit as-of'd fields: `market_cap_at_ipo_cr` (at-IPO snapshot) and `market_cap_current_cr` (live, with `_asof_date`)
- **Steelman:** This is the charter's stated class fix (§9: every time-varying field gets an at-IPO vs current
  as-of attribute + as-of date). It heals D-3 at the data layer (predictor/analogs/weights bind to the at-IPO
  field; findings keep excluding the current field). The implied-shares check becomes *well-posed* against the
  at-IPO cap (`at_ipo_cap / issue_size` is tight — measured median **3.55×**, mean 3.65×, max ~10× on the **90
  rows** where the at-IPO kpi cap exists; see step 6 Predicate 3). The current field extends naturally to the
  live/listed-stock universe (charter §10) as just another as-of'd snapshot.
- **Cost:** at-IPO cap is currently sparse (`kpi_market_cap_post_ipo` on only 90 rows, **all longterm — 0% boom**),
  AND its OWN value quality is unvetted (≥1 gross parse error, HDFC AMC — see §3 sub-audit). Need to (a) audit/clean
  the existing 90 values, and (b) source/derive the field for boom (`issue_price × post-issue shares`, where
  post-issue shares can come from issue docs or `issue_size / fresh-issue-price` + OFS). On boom the derivation is
  the de-facto primary (03g is longterm-only). That is real sourcing+vetting work — but it's the CORRECT field, and
  gaps are handled by the same present/absent policy (task_03), so sparsity is honest, not a blocker.
- **This is the recommended direction — CONDITIONAL on the §3 value-quality audit of `kpi_market_cap_post_ipo`**
  (proposal below).

### Option C — Drop `market_cap_cr` entirely; use `issue_size_cr` as the only at-IPO size signal
- **Steelman:** `issue_size_cr` is already a clean at-IPO Gower feature; D-3's own suggested fix mentions it;
  zero new sourcing; instantly kills the leak.
- **Reject (completeness):** issue size ≠ market cap (it's only the slice sold). It loses the size-class signal
  for valuation/liquidity analysis and for the analog "find similar-sized companies" gate. Good as an *interim*
  D-3 patch, too lossy as the *end-state*. Keep as the documented fallback when at-IPO cap is unsourceable.

### Sub-decision — the `market_cap_class` derivation
- Current: `mktcap_class()` buckets whatever `market_cap_cr` holds, including `0 → micro`. **Thresholds (verified,
  08_build_universe.py:167-173):** `< 300 → micro`, `< 2000 → small`, `< 20000 → mid`, else `large` (strict `<`).
  Observed ranges: micro ≤299, small 303-1971, mid 2005-19789, large ≥20599. **Class must be derived from a
  NON-null, validated cap, and return null (not "micro") on missing/0** — the `0 < 300 → micro` branch is the O-15
  bug. Class should also carry the **same as-of attribute** as its source cap.
- **Single declarative derivation, NOT hardwired to at-IPO (north-star: minimal flags / single source of truth).**
  Deriving class ONLY from `market_cap_at_ipo_cr` would silently NULL class for the rows whose only valid cap is
  current — the 39 non-equity rows (FPO/REIT/InvIT, already-listed entities; §3 non-equity census) and any future
  listed-stock universe rows (§7-7), re-creating an absent/ambiguous class field. Instead make class a deterministic
  function of **whichever cap is the row's authoritative as-of reading**, selected by the `instrument_type` /
  `universe_type` seam (task_05b/task_13): at-IPO cap for equity-IPO rows; current cap for already-listed /
  non-IPO rows. **One rule, no per-instrument branch** — the seam column drives it declaratively, so non-equity /
  listed rows are NEVER silently null for class.
- **Threshold-calibration open question (→ Open-Q):** the 300/2000/20000 cut points were calibrated against the
  CURRENT cap. Switching the equity-row class source to the at-IPO cap will re-bucket rows (most companies are
  smaller at IPO than now), so the thresholds may need re-calibrating on an at-IPO basis. Surface as an explicit
  owner question; quantify the churn via §6 Predicate 5 (current-class vs at-IPO-class on the dual-cap rows).

---

## 5) Analysis (step by step)
1. There are really **two different facts** wearing one column name: (a) "how big was this company at IPO" (an
   immutable at-IPO snapshot, the right analog/valuation feature), and (b) "how big is it now" (a live, outcome-
   contaminated quantity). Conflating them is the single root cause of O-8 (current vs at-IPO comparison), the
   failed implied-shares check (current vs at-IPO ratio), AND D-3 (current cap leaking into a predictor that must
   only see at-IPO state). **One root cause, three symptoms — fix the cause (as-of split), not the symptoms.**
2. The zeros (O-15) are a *separate*, orthogonal cause: I1 (parse-fail-as-0). They must be NaN, and class must be
   null when the cap is null — independent of which as-of field we keep.
3. The Bajaj wrong-entity join (O-12) is a *third*, also separate cause: the name→entity resolver
   (`company_search`) picked the wrong company. ISIN is the project's primary key; Screener is keyed by name, not
   ISIN, so this join is inherently risky. The right guard is **at-IPO-cap self-consistency** (`at_ipo_cap /
   issue_size` ∈ a tight band), which is well-posed; the current-cap implied-shares check is not.
4. Therefore the validity check should run against `market_cap_at_ipo_cr`, where my data shows the ratio band is
   tight (median **3.55**, mean 3.65, max **9.996**, on the natural **90-row** at-IPO-cap population — see §6
   Predicate 3 for the exact predicate) → a threshold like `at_ipo_cap / issue_size` outside roughly [1, 20] is a
   strong, low-false-positive flag (exactly 1 row falls outside, the HDFC AMC corruption). The current-cap field gets NO issue-size validity check
   (it's legitimately unbounded for survivors); instead it could be sanity-checked only for internal consistency
   if/when share count is independently sourced.

---

## 6) TEST / validate empirically (numbers + ≥2 ISIN examples)

**Predicate 1 — O-15 zeros (caught/missed/over-caught):** `market_cap_cr == 0`.
- Caught: **7** (all listed in §3). Over-caught (false positives): 0 — all 7 are genuinely missing (tiny SMEs,
  no plausible 0 cap). Missed: separately, **861** rows are null (already correct as missing); the bug is only the
  7 that became 0. Worked examples: **INE971P01012** Supreme Impex (issue 8 cr, cap=0, class wrongly=micro);
  **INE301Z01011** Soni Soya (issue 5 cr, cap=0, class wrongly=micro).

**Predicate 2 — the proposed O-12 implied-shares check against CURRENT cap** (`current_cap/current_price` vs
`issue_size/issue_price`, ratio > 5×):
- Flagged: **716 / 1,479** evaluable (predicate per §3: all four inputs non-null AND `current_price != 0`).
  **Catches Bajaj (good): yes.** Over-caught (false positives): the vast majority — e.g. **INE663F01032** Info Edge
  (ratio 123×, a legitimate 100-bagger), **INE483A01010** Central Bank of India (115×). **This quantifies the check
  as ~700 false positives → REJECTED as specified.**

**Predicate 3 — the WELL-POSED check against AT-IPO cap** (`kpi_market_cap_post_ipo / issue_size_cr`), measured on
the **natural 90-row population** (`kpi_market_cap_post_ipo` non-null AND `issue_size_cr > 0` — this ratio needs
ONLY those two fields; the earlier "67" was the both-caps-present subset, an irrelevant current-cap filter, and the
"at-IPO cap exists on 67 rows" wording was wrong — it exists on **90**):
- Distribution (90-row pop, verified): mean **3.646**, median **3.554**, max **9.996**, min **0.0028** (1 corrupt
  row). The proposed validity check `market_cap_at_ipo_cr / issue_size` will RUN on this 90+ population, so the band
  MUST be derived here, not on the 67-subset.
- Rows outside `[1, 20]×`: exactly **1** — the min-0.0028 row, which is **HDFC AMC `INE127D01025`**
  (kpi cap 7.8 cr vs issue 2,800 cr). Per the §3 sub-audit this is a VALUE corruption (gross mis-parse), not merely
  an "at-IPO < issue_size" curiosity — so the band correctly catches it, but it also proves the PRIMARY field
  itself carries corrupt values and must be parse-audited before adoption.
- Interpretation: an at-IPO band of roughly `[1, 20]×` catches the 1 corrupt row with ~0 false positives on this
  sample. This is the check to build, **but only once `market_cap_at_ipo_cr` is populated** (today: 90 rows,
  longterm-only) **AND its value quality is vetted** (§3 sub-audit).

**Predicate 4 — O-8 reproduction + reclassification** (`0 < current_cap < issue_size`, gross = ratio > 10):
- 169 total; 43 gross. Of the 43 gross: **36 wipeout + 1 loser + 6 NaN, 0 winners**; current_price present on 41.
- Worked examples: **INE799L01016** Tara Jewels (cap 1.23 cr vs issue 179 cr, 145× — a documented delisted scam,
  REAL data); **INE225I01026** Zylog Systems (cap 2.07 cr vs issue 126 cr, 61× — real corporate collapse). →
  confirms O-8 is an as-of artifact, not a data bug; the fix is "don't run this check," not "correct these rows."

**Predicate 5 — current-cap class vs at-IPO-cap class re-bucketing (the D-3 fix's behavioral impact):** on the
67 rows that carry BOTH caps, re-derive `market_cap_class` from each source and count bucket changes. (NOTE:
testability is partial here because the only rows where both classes are derivable today are the 67 dual-cap rows;
the full re-bucketing impact on the boom cohort is unknowable until boom at-IPO cap is sourced — flagged as an
open item, see §7 Open-Q. The 67-row result is the available lower bound on churn.) Switching the class source
from current → at-IPO will re-bucket some rows; quantifying this on the 67 dual-cap rows bounds the change for the
covered cohort. This number should be produced before the D-3 binding is finalized.

**Testability of the architectural proposal (the as-of split):** validated by schema cross-check — the substrate
ALREADY carries `kpi_market_cap_post_ipo` (at-IPO) alongside `market_cap_cr` (current), proving both facts are
storable side-by-side; the 90-row at-IPO population (67-row overlap with current cap) let me empirically derive the
at-IPO validity band above.

---

## 7) NON-FINAL proposal + open owner-questions

### Proposal (NOT FINAL)
1. **Split the cap field by as-of (the class fix, charter §9).** Replace the single ambiguous `market_cap_cr` with
   two explicitly as-of'd fields in the column registry:
   - `market_cap_at_ipo_cr` — at-IPO snapshot. **Primary source:** `kpi_market_cap_post_ipo` (Chittorgarh KPI,
     90 rows today, **all longterm — 03g is longterm-only by input, §3**). **CONDITIONAL on a value-quality audit
     of `kpi_market_cap_post_ipo` FIRST** (§3 sub-audit: ≥1 gross parse error, HDFC AMC `INE127D01025` = 7.8 cr;
     it carries no `_src` and no validity check of its own — adopt only after the parse-quality pass + I1 `0→NaN` +
     `_src` provenance are applied to IT too). **Fallback (the de-facto primary on boom):** derive `issue_price ×
     post-issue shares` (post-issue shares from issue docs, or reconstructed from fresh-issue + OFS split) — make
     this a first-class part of the sourcing plan, not an afterthought, since it covers the 1,357-row boom majority
     where 03g contributes zero. **This is the intended analog/valuation/predictor feature once vetted.**
   - `market_cap_current_cr` (+ `market_cap_current_asof_date`) — the live Screener cap. **For display/current-
     state only; NEVER a predictor/analog/weight input** (heals D-3 at the data layer).
2. **`market_cap_class` is a SINGLE declarative derivation over the row's authoritative cap** (NOT hardwired to
   at-IPO): at-IPO cap for equity-IPO rows, current cap for already-listed / non-IPO rows (FPO/REIT/InvIT + future
   listed-stock universe), selected by the `instrument_type`/`universe_type` seam (task_05b/task_13) — one rule, no
   per-instrument branch, so non-equity/listed rows are never silently null for class. It returns **null on null/0**
   (fixes the O-15 `0 → micro` lie); the `0 < 300 → micro` branch must require a non-null, > 0 cap. **Harden at the
   FUNCTION level** (`mktcap_class()`), so BOTH writers (company_meta 08:163-189 AND the 03f boom-gap fill
   08:224-230) inherit the null-on-0/empty behavior — do not patch one writer.
3. **0 → NaN at load (I1) for the 7 zeros**, AND convert the `''` (empty-string) sentinel `mktcap_class()`/no-meta
   branch emits to canonical null — parse/fetch-fail must never be written as 0 or `''` (task_19/task_03 own the
   systemic version; this is the market-cap instance).
4. **O-12 guard = at-IPO-cap self-consistency, NOT the current-cap implied-shares check.** Validity rule:
   flag when `market_cap_at_ipo_cr / issue_size_cr` is outside ~[1, 20] (band derived empirically on 90 rows,
   step 6 Predicate 3). **APPLICABILITY COVERAGE (critical, verified):** today only **12 / 169** O-8 rows and
   **0 / 1** of the O-12 (Bajaj has no at-IPO cap, §3) carry `kpi_market_cap_post_ipo`, so this guard can validate
   only ~7% of the in-scope O-8 population and CANNOT catch the lone O-12 error today. **The guard's value is
   therefore contingent on the sourcing campaign (Proposal #1 / Open-Q1).** Interim guard for rows lacking an at-IPO
   cap: **quarantine-on-missing** (route to `quality==dirty` rather than silently passing), or a current-cap
   consistency check once share count is independently sourced. Do NOT mark O-8/O-12 "resolved by a check" that runs
   on neither. The originally-proposed current-cap implied-shares check (L575) is **withdrawn** — quantified at ~700
   false positives.
5. **O-8 (169 rows) — PARTIAL reclassification, NOT a blanket "not-a-bug".** For the rows that ARE 88-audit
   Category-2 (verified-genuine) or web-corroborated: reclassify as an as-of-semantics artifact (current-vs-at-IPO
   comparison on a genuinely-crashed company) — not a data bug. For the **43 gross >10× and the 3 extreme >50×
   (Zylog `INE225I01026`, Tara `INE799L01016`, Future Supply `INE935Q01015` — verified in NEITHER Cat-1 NOR Cat-2,
   §3)**: route to **quarantine / owner pending Cat-1/Cat-2 cross-check**, NOT marked not-a-bug. The rollup must not
   overstate: a 145×/61× cap/issue signature is exactly what a missing split also produces, and labeling
   un-corroborated rows "resolved" is the charter-warned failure mode. Bajaj remains the lone genuine wrong-entity
   error → quarantine (`quality==dirty`) until the cap is corrected/re-sourced by ISIN.
6. **Identity hardening (feeds task_07):** the Bajaj join failed because Screener is name-keyed. Record the
   Screener-matched entity id + name with the scraped cap so wrong-entity matches are auditable/reversible, and
   prefer ISIN-anchored resolution where possible.
7. **Extensibility (charter §10):** `market_cap_current_cr` + `_asof_date` is exactly the live/listed-stock seam —
   a non-IPO row simply has no `market_cap_at_ipo_cr` (present/absent handles it) and a populated current snapshot.
8. **Sourcing / fallback table (charter §2 — both cap fields, incl. the dominant gaps):**

   | field | primary | fallback order | gap today | interim policy |
   |---|---|---|---|---|
   | `market_cap_at_ipo_cr` | `kpi_market_cap_post_ipo` (03g, longterm-only) — AFTER value audit | `issue_price × post-issue shares` (issue docs / fresh-issue+OFS) → Option C `issue_size_cr` proxy | 0/1357 boom; 90/90 longterm; 861 rows null overall (36%) | null + `_src=source-never-published`/`fetch-parse-failed` (task_03); boom derivation is de-facto primary |
   | `market_cap_current_cr` | live Screener `page_marketcap` (name-keyed) | none (display-only) | wrong-entity joins (O-12); 861 null; 34 `current_price==0` | record matched entity id+name (§7-6); quarantine wrong-entity; no issue-size validity check |

   The **861 null `market_cap_cr` rows (36%)** get no special-case — the same present/absent missing-policy
   (task_03) applies; class is null for them (correct). This is honest sparsity, not a blocker.
9. **Current-cap parse/wrong-entity sweep (NOT done this run — flagged):** O-12 (Bajaj) is almost certainly NOT the
   only name-keyed mis-join. A systemic sweep should flag every row whose Screener-matched entity name differs
   materially from `company_name` (not just Bajaj), plus any negative/absurd current-cap values — the
   implied-shares check is NOT a substitute (700 false positives). This is a completeness gap to close in task_07
   (identity) / task_03 (provenance), not resolvable by the at-IPO band.

### Open owner-questions
1. **Source the at-IPO cap?** Adopt `market_cap_at_ipo_cr` as primary and invest in sourcing/deriving it (90 rows
   today, **all longterm — 0% boom; 03g is longterm-only by input**), or accept Option C interim (use
   `issue_size_cr` as the at-IPO size proxy and drop the current cap from all predictor paths)? Note the boom
   derivation (`issue_price × post-issue shares`) is the de-facto primary for 57% of the substrate, not an
   afterthought.
1b. **Value-audit the at-IPO cap FIRST?** Confirm `kpi_market_cap_post_ipo` gets a parse-quality pass (≥1 gross
   corruption found: HDFC AMC `INE127D01025` = 7.8 cr) + I1 `0→NaN` + `_src` provenance BEFORE it is bound as the
   predictor anchor — the field is currently unvetted and carries no `_src`.
2. **D-3 binding:** confirm the predictor/analog/weights **AND `layer3/forward_test.py:27` (the OOS harness)**
   should bind to `market_cap_at_ipo_cr` (heal at data layer) vs the lighter "just drop `market_cap_class` from the
   gate + `_QUERY_FEATS` + `QUERY_FEATURES`" patch in D-3's note? (forward_test must not be left consuming the leaky
   class.) Also: should n4/n11/spine/report be leak-assessed or left as-is like n14?
3. **Keep the current cap at all?** Is `market_cap_current_cr` worth storing (display value / future live
   universe), or should we drop the current-cap scrape entirely until the live-universe work begins?
4. **At-IPO validity band:** is `[1, 20]×` issue_size acceptable (derived on the **90-row longterm-only**
   population), or should the band be re-derived once the at-IPO cap is populated on boom at scale? **Do NOT confuse
   this AT-IPO band with `rules/index.md`'s CURRENT-cap migration ratios (migrants 16.9× vs trapped 3.3× mcap/issue)
   — those are a different as-of measure (current cap) and must not be cross-applied;** the band here is
   single-regime (longterm) pending boom at-IPO sourcing.
4b. **Class-threshold calibration basis:** keep the 300/2000/20000 cut points (current-cap-calibrated), or
   re-calibrate them on an at-IPO basis given the class source switches to the at-IPO cap for equity rows?
   (Quantify churn via §6 Predicate 5.)
5. **Bajaj + any future wrong-entity rows:** quarantine to `dirty` and leave null, or attempt an ISIN-anchored
   re-scrape now (network is default-deny this run)? (See also the systemic wrong-entity sweep, §7-9.)
6. **O-8's "169 rows" status in the register:** mark as **PARTIAL reclassification** — as-of artifact ONLY for the
   Cat-2/web-corroborated rows; the 43 gross / 3 extreme (Zylog/Tara/Future Supply, in NEITHER category) go to
   quarantine pending Cat-1/Cat-2 cross-check, NOT marked not-a-bug — confirm?

---

### DONE CHECKLIST
- [x] all 8 steps present and non-empty (scope·ground-truth·reproduce/re-audit·options·analysis·test·review-note·proposal)
- [x] ground-truth inputs cited by FILE PATH
- [x] step-6 numbers present (caught/missed/over-caught for 4 predicates + ≥2 ISIN examples each)
- [ ] review-loop stop rule — **PENDING** (**Round 1 applied:** an independent multi-lens review pass — correctness
      · completeness · context-pickup · north-star · adversarial — was run; its findings have been APPLIED above
      (key fixes: at-IPO band re-derived on the correct 90-row population not 67; HDFC AMC `INE127D01025` flagged as
      a gross parse error + a new §3 value-quality sub-audit of `kpi_market_cap_post_ipo`; O-8 reclassification
      downgraded to PARTIAL with the 43 gross / 3 extreme routed to quarantine; the 12/169 O-8 applicability-coverage
      gap surfaced; the full 6-file `market_cap_class` consumer audit incl. `forward_test.py:27`; the 03f second
      writer + function-level harden; the 03g longterm-only structural cause; `issue_price_src`→`issue_size_cr_src`
      correction; 03g except-block re-described as prints-not-silent). **Still needs ≥2 consecutive INDEPENDENT
      fresh-agent rounds with zero new ≥LOW findings, each logged in `night_run_2026-06-17_review_log.md`, author ≠
      reviewer per charter step 7.**)
- [x] NOT-FINAL marker + open-owner-questions block present

> _Round-1 multi-lens review findings have been applied (see above). The stop rule (≥2 quiet independent rounds,
> each logged, author ≠ reviewer) is NOT yet satisfied — the task is NOT closeable until those rounds run. Flagged,
> not skipped._
