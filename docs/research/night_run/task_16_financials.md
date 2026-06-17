# task_16 — Financials (EPS / net_sales / margins / debt-equity-vs-ROE) — issue register

> **STATUS: NOT FINAL.** Design/think-only output for owner review. No code, no pipeline changes.
> Part of the 2026-06-17 overnight data-architecture run (Group B — issue register + existing-fix re-audit).
> Author: task_16 agent. All numbers re-derived read-only against `data/master/ipo_analysis.csv` (2,384 rows) on 2026-06-17.

---

## 1. SCOPE (the single question)
For the **financial fields** in the substrate — per-year EPS (`eps_yr1/2/3`, `eps_ttm`), net sales (`net_sales_yr1/2/3`,
`pre_ipo_net_sales`), profitability (`pat_yr*`, `pat_ttm_cr`, `pre_ipo_pat`, `pre_ipo_pat_margin_pct`), operating profit
(`operating_profit_yr*`), cash flow (`operating_cf_yr*`), the balance-sheet inputs/ratios (`shareholder_funds_yr*`,
`borrowings_yr*`, `total_assets_yr*`, `pre_ipo_debt_equity`, `pre_ipo_roe_pct`), valuation (`pe_ratio`, `kpi_pe_pre_ipo`/
`kpi_roe_pre_ipo`), and `sales_ttm_cr` — **reproduce the known issues (O-5, O-6, O-7, O-9, O-10) against current data,
re-audit any existing handling, identify the true root cause vs false-positive audit claims, audit the validity AND the
coverage of every financial column, and propose (NOT final) how the target architecture should source / validate / encode
these fields** — including the NCD/REIT/InvIT non-equity contamination that poisons the equity financials table.

SCOPE NOTE (completeness): the original draft addressed only the O-series-named columns. This version expands to ALL
financial columns (operating_profit, total_assets, pe_ratio, pat_ttm_cr, shareholder_funds/borrowings — the actual O-9
denominators — and the per-cohort COVERAGE gap), per the completeness lens. Validity AND coverage are both in-scope: a
financials register that records only mis-valued cells but not the missing-data cliff is incomplete.

This task does NOT decide the equity-vs-non-equity table split (that is task_05b) — but it supplies the financial-corruption
evidence that the split must resolve, and explicitly hands the non-equity contamination there.

---

## 2. GROUND-TRUTH INPUTS (read, by path)
- **`data/master/ipo_analysis.csv`** — THE substrate. 220 columns, 2,384 rows (counted via `csv`, not `wc -l`).
- **`docs/research/alignment_audit_2026-06-16.md`** — the O-series source (O-5…O-10 under "Financials"; the I1 "0-vs-NaN"
  cross-cutting root cause; proposed systemic check #5 "EPS reconciliation"). NOTE: the audit's O-9 entry (line 544) scopes
  the ROE/DE inconsistency to **9 rows** and names INE06ST01018 (Indiqube, ROE 1400%) as "clearly broken" — see §3 O-9.
- **`docs/data_review.md`** (lines 13–16 + 46–47) — the canonical data-review register. **Line 46-47 already documents the
  EPS share-base resolution verbatim** ("Pre-IPO EPS may be on a pre-split share base … Absolute ₹-cr financials … are
  comparable; EPS across the IPO boundary is not"). Lines 13-16 document the 21 sharescart-vs-screener >5%-divergence rows
  already flagged for owner spot-check (Anand Rathi Wealth net_sales 846 vs 273; Concord Enviro PAT 96 vs 41). This is the
  PRIOR resolution / prior flag set — §3 O-5/O-7/O-10 build on it, they do not re-discover it. (Required STAGE-0 read.)
- **`docs/schema.md`** (lines 123–175) — declares the financial columns + their stated source (`sharescart` / `derived`).
- **`docs/sources.md`** (line 32 + G1b) — sources.md:32 warns sharescart has **"post-IPO financial contamination"** (its
  3yr financials may be as-of POST-listing, not at-RHP); G1b names **screener** as the financials source. As-of relevance: financials are time-varying — see §4 Problem A note + §7 open-Q.
- **`data/master/review/screener_financials_review.csv`** (21 rows; cols `isin/company/field/sharescart/screener/fy`) — the
  sharescart-vs-screener >5%-divergence flag file (the existing cross-check output; data_review.md:13-16 documents it).
- **`docs/research/data/drhp_recovered.csv`** (16 SEBI-DRHP-recovered financials, incl. `pat_suspect`/review-needed flags) —
  the charter-designated financial overlay/fallback source for missing/wrong pre-IPO financials (Coal India FY10 sales, DLF…).
- **`pipeline/08_build_universe.py`** (lines 97–145) — where `pre_ipo_*` are DERIVED and per-year `*_yr{1,2,3}` are
  overwritten from screener's pre-listing trajectory. (`sf = equity_capital + reserves` at line 139; `roe = pat/sf`,
  `de = brw/sf` at 140-142 — the shareholder-funds denominator behind O-9.)
- **`pipeline/03b_fill_financials_screener.py`** (lines 39–98) — the screener fill + the sharescart-vs-screener guard +
  the `data/master/review/screener_financials_review.csv` writer.
- **`pipeline/longterm/04_financials.py`** (lines 37–183) — the 2006–19 cohort financials (same `YR_METRICS` map; same
  `if sales and pat` margin guard).
- **`pipeline/03_enrich.py`** (lines 11–17) — sharescart financial columns (the original per-year values).
- **`data/raw/screener/financials.csv`** — raw long-format `(isin, fy, metric, value)` source for per-year financials.
- **`rules/index.md`** (line 34 wipeout-safety IN-SCORE; line 277 `pre_ipo_net_sales` rank-IC 0.20) — financial fields are
  not display-only: `pre_ipo_net_sales`+`pre_ipo_pat` feed the IN-SCORE wipeout-safety component; ROE/DE/margin feed the
  quality component; pre_ipo_net_sales is itself an IC-0.20 at-IPO predictor.
- **LIVE DOWNSTREAM CONSUMERS (verified by `grep -rn --include="*.py" … layer3/`) — NOT just n14:**
  - `layer3/findings/n14_wipeout_anatomy.py:50-54` — `pat_yr1/yr3`, `net_sales_yr1/yr3`, `operating_profit_yr3`,
    `pre_ipo_net_sales` (the VALIDATED cross-regime `tiny_sales_lt25cr` flag), `pre_ipo_debt_equity`,
    `pre_ipo_pat_margin_pct`, `pre_ipo_pat`, `pe_ratio` — n14 itself uses the DERIVED `pre_ipo_*` ratios, contradicting any
    "n14 only reads `net_sales_yr/pat_yr`" claim.
  - `layer3/findings/n7_fundamentals.py:12-14` — a PUBLISHED finding that tertiles `pre_ipo_roe_pct` / `pre_ipo_pat_margin_pct` / `pre_ipo_debt_equity` ("death signal") → outcomes.
  - `layer3/findings/n13_fallen_angel.py:13-16` — `pre_ipo_pat`, `pre_ipo_debt_equity`, `pre_ipo_roe_pct`.
  - `layer3/findings/n15_clean_compounder.py:40-41` — `pre_ipo_debt_equity`, `pre_ipo_roe_pct`.
  - `layer3/findings/n8_accrual.py:14-15` — `operating_cf_yr3`, `pat_yr3`.
  - `layer3/findings/n6_valuation.py:14` — `pe_ratio`.
  - `layer3/findings/t9_profitable.py:14` + `backtest/engine.py:52` + `validate.py:37` — `pre_ipo_pat`.
  - **THE SCORED PREDICTOR:** `predictor/analogs.py:22-25` — `pe_ratio`/`pre_ipo_roe_pct`/`pre_ipo_debt_equity`/
    `pre_ipo_pat_margin_pct` are GOWER DISTANCE FEATURES (the corruption distorts who counts as an "analog");
    `predictor/weights.py:21-23` — the same fields are QUERY FEATURES fed row-by-row into the point-in-time rank-IC that
    DERIVES the data-informed weights; `predictor/scorecard.py:436-453` — `pre_ipo_pat`/`pat_yr3` fallback,
    `pre_ipo_roe_pct`, `pre_ipo_debt_equity`, `pre_ipo_pat_margin_pct` feed the quality component; `forward_test.py:28-30`.
  - **Conclusion:** O-9/O-10 corruption (Indiqube ROE 1400 / D/E −409.5, Ujjivan margin 983) leaks into the analog Gower
    distance, the data-informed weight derivation, AND the in-score wipeout-safety + quality components — **scored-feature
    corruption, NOT display-only.** EPS is the only family with no live numeric consumer today (`eps_yr*` unread; `eps_ttm`
    is consumed by research tools h2/hmvp via issue-time P/E — see §3 O-7).

Schema-drift note (feeds task_01): the following financial columns are declared in `docs/schema.md` but **do NOT exist** in
the substrate (all verified `False` against the CSV header): `pre_ipo_eps`; plain `roe_pct` (schema.md:32, attributed to
sharescart) and plain `debt_equity` (schema.md:34, sharescart); plus the derived-doc drifts `roce_pct`, `pre_ipo_roce_pct`,
`pre_ipo_ebitda_margin_pct`, `sales_cagr_3y`, `pat_cagr_3y`, `pre_ipo_net_sales_growth_pct`, `pre_ipo_pat_growth_pct`,
`pre_ipo_shareholder_funds`, `pre_ipo_borrowings`. Actual columns are `eps_yr*`/`eps_ttm`, `pre_ipo_roe_pct`,
`pre_ipo_debt_equity`, and the per-year `shareholder_funds_yr*`/`borrowings_yr*`. **Source-attribution contradiction:**
schema.md attributes per-year financials to `sharescart`, but `08_build_universe` OVERWRITES them from screener, and
sources.md G1b names screener — hand the source-attribution reconciliation to task_01/task_02 (full list in §7 item 6).

---

## 3. REPRODUCE + RE-AUDIT (against current data)

### O-5 — per-year EPS ~1000× inflation — **REPRODUCES; ROOT CAUSE already documented in data_review.md (NOT a fresh discovery, NOT a parse error)**
> **Context-pickup correction:** the share-base-discontinuity resolution below is **NOT a novel re-audit finding** — it is
> already documented verbatim in the canonical register `docs/data_review.md:46-47` ("Pre-IPO EPS may be on a pre-split
> share base … EPS across the IPO boundary is not [comparable]"). This task **confirms and operationalizes** that existing
> owner-known caveat (data_review treats it as a methodology caveat; here we propose the validity-rule operationalization,
> A2/A1). It does not "discover" it.

Counts (read-only):
- `eps_yr1`: 51 rows with |value| > 1000 (**max magnitude 1,306,098** — Honasa INE0J5401028, the same row used as the worked
  example below; 151,200 is the 2nd-largest). `eps_yr2`: 57 rows (max magnitude 204,000). `eps_yr3`: 25 (max 42,481).
  `eps_ttm`: 3 (max 13,927). Confirms the audit's "yr1/yr2 worst, yr3/ttm cleaner."
- A **cross-year consistency check** (eps_yrN / pat_yrN should be ~constant within a row, since shares are ~constant) flags
  **95 rows** where one year's implied share-base differs >100× from another. In **90 / 95** the LATEST pre-IPO year (yr3)
  is the clean one; yr1/yr2 carry the inflation.

**Re-audit — what the inflation actually IS (verified against raw `screener/financials.csv`):** it is **NOT** a 1000×
unit/parse bug. It is a **real share-base discontinuity faithfully copied from Screener.** Pre-IPO years have a tiny
private/pre-bonus share count, so EPS = PAT / (very few shares) is genuinely enormous; after the IPO+bonus the share count
explodes and EPS normalizes. Worked raw examples:
- **Honasa (INE0J5401028):** raw EPS FY2021 = **−1,306,098** on PAT −1,332 cr (⇒ ~10k shares); FY2023 EPS −10.47 on PAT
  −151 cr (⇒ ~1.4 cr shares). The denominator changed ~3 orders of magnitude — both numbers are "correct" per Screener.
- **Syrma (INE0DYJ01015):** raw EPS FY2020 = **1,281.97** on PAT 92 cr; FY2022 EPS 5.59 on PAT 79 cr. Same pattern.
- **Delhivery (INE148O01028):** raw EPS FY2019 = **−18,607** on PAT −1,783 cr; FY2022 EPS −15.75.

⇒ The audit's proposed fix "divide the inflated year by 1000" (systemic check #5) is **wrong** — the ratio is not a clean
1000×; it is whatever the pre-IPO share count happened to be. The correct frame is **comparability/normalization**, not
de-corruption. **Direct rebuttal of the audit's "ratio peaks at exactly 1000.0" claim (alignment_audit:533):** a per-row
test `|eps_yr1/eps_yr3| ∈ [990,1010]` returns **0 rows** — NO row exhibits a clean ~1000× cross-year EPS ratio. So
"peaks at exactly 1000.0" does not hold as a per-row unit factor; this empirically kills the ÷1000 fix (the 1000 the audit
saw is a population-level artifact, not a per-row scale factor).

### O-7 — `eps_ttm` absurd values — **REPRODUCES (3 rows), same root cause**
`eps_ttm` with |value| > 2000: **INE1I1301016** Workmates 13,927 (PAT_ttm 14 cr), **INE1EUB01016** Shlokka Dyes 3,696,
**INE14VP01014** JD Cables 4,405 — all **SME**, all tiny pre-listing share base. Same share-base mechanism as O-5.
NOTE (blast radius): unlike `eps_yr*`, `eps_ttm` is NOT purely display-only — the research tools h2/hmvp derive issue-time
P/E from it (and it relates to `pe_ratio`), so a corrupted `eps_ttm` can distort a derived issue-time P/E. The A2 floor still
applies; the "no live consumer of EPS" framing in the earlier draft was over-stated for `eps_ttm`.

### EPS↔PAT sign-consistency — **NEW validity class (the original draft missed it)**
EPS and PAT must share sign for a single entity. `sign(eps_ttm) ≠ sign(pre_ipo_pat)` flags **34 rows** — genuine
consistency breaks (wrong-entity join, stale year, or unit/parse), a class distinct from the magnitude inflation above. The
analogous per-year check `sign(eps_yrN) ≠ sign(pat_yrN)` should run too. This is the reconciliation the audit's "systemic
check #5" was reaching for; route mismatches to `quality==dirty`. (See §4 Problem A + §6.)

### O-6 — `net_sales_yr3 = 0` poisoning margins — **PARTIALLY OBSOLETE; the "poisons margins" half does NOT reproduce**
- `net_sales_yr3 == 0`: **13 rows** today (audit said "13 large cos" — count matches). By instrument_type: **equity 5,
  reit 4, invit 4.**
- The 5 BIG offenders (yr2 sales > ₹100 cr) are **ALL REIT/InvIT**: Mindspace REIT (INE0CCU25019), Bharat Highways InvIT
  (INE0NHL23019), Citius InvIT (INE2Q7823014), IRB InvIT (INE183W23014), Embassy REIT (INE041025011). Note the ISIN series
  `...25...` / `...23...` (REIT/InvIT/debt), **not** equity `...01...`. → This is **non-equity contamination of the equity
  financials table** (hand to task_05b).
- The 5 *equity* `net_sales_yr3==0` rows are tiny shells (Saamya Biotech, Broadcast Initiatives, Shri Krishna Prasadam,
  Vanta Bioscience, Advitiya Trade) — genuine ~zero / unfetched, not "large cos."
- **PER-YEAR ZEROS ARE BROADER THAN yr3 (completeness — the draft under-scoped to one year):** `net_sales_yr1==0` = **32
  rows**, `net_sales_yr2==0` = **20 rows**, `net_sales_yr3==0` = 13. And per-year PAT zeros: `pat_yr1==0` = **184**,
  `pat_yr2==0` = **102**, `pat_yr3==0` = **61**. These feed n14's `declining_revenue` (`s3<s1`) and `declining_pat`
  (`p3<p1`) flags. **n14 asymmetry (feature↔data finding for task_12):** `declining_revenue` is guarded by `s1>0`
  (n14:...`& (s1 > 0)`) but `declining_pat` has **NO `p1>0` guard** — so a per-year PAT zero/sign-flip silently produces a
  false `declining_pat`. Hand the full per-year 0-vs-missing set (sales AND pat, all three years) to I1/task_19, and the
  `declining_pat` missing-guard to task_12 as a feature-correctness bug.
- **CRITICAL RE-AUDIT RESULT — the "0 poisons margins" claim is FALSE on current data.** Predicate
  `pre_ipo_net_sales==0 AND pre_ipo_pat_margin_pct is not null` returns **0 rows**. The derivation in
  `08_build_universe.py:137` is `if sales and pat is not None:` — `sales==0` is falsy → the margin is **skipped**, not
  divided-by-zero. So zeros do **not** reach the margin. The poisoning the audit feared comes from **wrong-but-nonzero**
  sales (see O-10), not from zeros. **The zero-guard is an existing, viable fix; it holds.** (Caveat: a zero still leaks
  into `pre_ipo_net_sales` itself as a value — that is the I1 "0-vs-NaN" problem. **Full I1 count: `pre_ipo_net_sales==0`
  is stored as literal `0.0` in 17 rows substrate-wide** — the 5 equity `net_sales_yr3==0` shells are a strict subset
  surfaced via the yr3 lens. Hand the full 17 to task_19 so it doesn't under-scope; not a margin bug.)

### O-6b — operating_profit / total_assets / pe_ratio / pat_ttm zeros + invalid values — **NEW (these columns were never audited)**
The draft audited only the O-series-named columns. The other financial columns carry the same 0-vs-missing and
invalid-value classes:
- `operating_profit_yr1` nonnull 1499, **77 zeros**; `operating_profit_yr2` 1708, **51 zeros**; `operating_profit_yr3`
  1880, **29 zeros**. `operating_profit_yr3` is read LIVE by n14 — same I1 0-vs-NaN ambiguity as sales/pat. Route to task_19.
- `pe_ratio`: 883 nonnull, **46 NEGATIVE values** + **2 > 500**. A negative P/E is meaningless (it's a loss-maker — P/E
  should be NULL, not a negative number); `pe_ratio` is read live by n6/n14 and is a Gower distance feature in
  `analogs.py:22`. Validity rule: loss-maker P/E → null, not negative. (Cross-ref O-9 — same "ratio with a sign-flipped or
  invalid denominator" class.)
- `pat_ttm_cr`: **19 zeros** (likely the I1 0-vs-missing class). `total_assets_yr*`, `sales_ttm_cr`,
  `kpi_pe_pre_ipo`(38)/`kpi_roe_pre_ipo`(2): inventory + apply the same missing-policy; not separately corrupted in spot
  checks but must be registered, not silently dropped.

### O-10 — `pre_ipo_pat_margin_pct` extreme one-offs — **REPRODUCES, broader than the audit's single example**
- `|pre_ipo_pat_margin_pct| > 80`: **11 rows** (audit named only INE334L01012). Worst: **INE334L01012 Ujjivan Financial
  983.3%** (pat 177 / sales **18**). Others: Manas Properties 250%, Transpact −230.8%, Suyog Funicular −200%, Valencia
  −150.7%, Shreeshay 144%, HPC Bio 105%, Fino 100%, B-Right 100%, Sodhani 100%, Esteem 96.7%.
- **Root cause (corrected — the "truncation, should be ~₹1,800" was a guess stated as fact):** the substrate value
  `pre_ipo_net_sales=18` for Ujjivan (FY `Mar 2016`) is the **raw screener value verbatim** — verified in
  `data/raw/screener/financials.csv`: `INE334L01012,2016,sales,18.0` (also FY2017=24, FY2018=8). **There is NO pipeline
  truncation of 1800→18.** The implausibility is an **upstream source quirk**: for a microfinance/NBFC, screener's "sales"
  is not topline revenue (NBFC revenue ≈ interest income, not booked as "sales"), and/or the FY label is wrong. So the
  margin is "wrong-but-nonzero" not because the pipeline dropped a digit but because the **source value itself is
  implausible for a finance company** (NBFC sales-definition mismatch). The corrected value (~₹1,800 cr) is a hypothesis to
  confirm against DRHP, not an established fact.
- The wrong-but-nonzero cell DOES pass the `if sales` guard and so propagates into the margin. 14 rows have
  `pre_ipo_net_sales < ₹5 cr` AND `|margin| > 50%`; **11 rows have `pre_ipo_net_sales < 25 AND |margin| > 80`** — these are
  the tiny-denominator margin blow-ups. Distinct from O-6 (zeros are caught; tiny-nonzeros are not).
- **O-10 is NOT cosmetic — it corrupts a VALIDATED in-score flag (the draft missed this):** the same truncated/implausible
  `pre_ipo_net_sales=18` (<25) directly fires the **VALIDATED cross-regime n14 wipeout red-flag `tiny_sales_lt25cr`** on
  Ujjivan — a *successful bank* (`outcome_class=multibagger`) — a false-positive in a live, partially-scored, owner-approved
  signal. And `pre_ipo_net_sales` is itself an IC-0.20 at-IPO predictor (`rules/index.md:277`), so a wrong sales value is
  not display-only. **The 11 `<25 & |margin|>80` rows are the truncation-suspect set currently feeding the validated
  `tiny_sales_lt25cr` flag.** This raises O-10 from "MED cosmetic" to a feature-corrupting bug (derived margin + the
  validated tiny-sales flag + the IC-0.20 raw feature).
- **Cross-reference the existing flag file:** `data/master/review/screener_financials_review.csv` (21 rows;
  isin/company/field/sharescart/screener/fy) already lists sharescart-vs-screener >5%-divergence financials (data_review.md:13-16
  — Anand Rathi Wealth net_sales 846 vs 273; Concord Enviro PAT 96 vs 41). It should be cross-referenced against the 11
  truncation-suspect rows to state whether the existing 21 flags already COVER the O-10 truncations or are disjoint — the
  step-6 over-catch/miss the charter requires. (Spot check: the 21-row file flags >5% divergences; the Ujjivan-class
  truncations are a distinct "implausible-vs-PAT" signature and are likely NOT all in the 21 — disjoint, to confirm row-by-row.)

### O-9 — `pre_ipo_debt_equity` sign vs `pre_ipo_roe_pct` sign — **CONFIRMS & SHARPENS the audit (a naive sign test is NOT what the audit used)**
> **Context-pickup correction (the earlier "audit premise is WRONG / 54 false positives" framing was a strawman):** the
> alignment_audit O-9 entry (alignment_audit:544) scopes the inconsistency to **"9 rows"**, NOT 54, and explicitly names
> INE06ST01018 (Indiqube, ROE 1400%) as "clearly broken." **Ground-truth reconciliation:** there are **14** negative-equity
> rows (`de<0`); of the **54** naive sign-mismatches, only **9** also have `de<0`. So the audit's "9 rows" almost certainly
> = the negative-equity detonation class (i.e. the genuine bug), the SAME class this task identifies. The audit was right
> and narrowly scoped; the 54-row "flood of false positives" is an artifact of a **naive predicate the audit never used.**
> This task therefore **CONFIRMS and sharpens** O-9 (negative/near-zero shareholder-funds denominator), it does not overturn it.
- Why a *naive* "sign(D/E) ≠ sign(ROE)" predicate over-flags (and why it's the wrong test, not the audit's): in
  `08_build_universe.py:140-142`, `roe = pat/sf` and `de = brw/sf` share only the *denominator* `sf` (shareholder funds);
  ROE's sign is driven by **PAT**, D/E's by **borrowings** (≥0). So a **loss-making company with positive equity** correctly
  shows **+D/E and −ROE** — economically valid. The naive test flags 54; ~45 of those are valid positive-equity loss-makers
  (Paytm/One 97, Eternal/Zomato, Swiggy, Delhivery, Nykaa-era, Ola Electric, PB Fintech, Star Health, Meesho,
  PhysicsWallah). **The 9 with `de<0` are the real detonation set** (the audit's 9).
- Worked genuine row: **INE06ST01018 Indiqube Spaces — ROE 1400%** (D/E −409.5). Negative D/E ⇒ **negative equity**
  (`sf < 0`); with `sf < 0` both `pat/sf` and `brw/sf` flip, and a near-zero negative `sf` denominator detonates the ratio.
  The real bug class is **near-zero / negative shareholder-funds denominator**, not "sign disagreement."
- `|ROE| > 200%`: **11 rows** — Krsnaa −1682, Indiqube +1400, Matrimony 2300, InterGlobe 312, Ortel −233, Meesho −272,
  etc. = small/negative-equity-denominator detonations (the real O-9 problem) + a couple of genuine high-ROE asset-light names.
- **Audit the UPSTREAM denominator directly (the draft only audited the derived ratios):** `sf = equity_capital + reserves`
  (`08_build_universe.py:139`). The actual quarantine target is `shareholder_funds_yr3` (present in the substrate). The
  proposed denominator-validity rule (D1) must be measured on `sf` itself: count rows with `sf<=0` and tiny-positive `sf`,
  give ISINs, and check how many have a non-null derived ROE/DE (= the actual quarantine set). Also check whether `sf` goes
  wrong because `reserves`/`equity_capital` is blank-treated-as-0 (ties to I1). The D1 over-catch/miss numbers in §6 must
  be on `sf`, not on the rejected sign test.

### Existing fixes re-audited (viability)
| Existing handling | Where | Holds today? |
|---|---|---|
| `if sales and pat` margin guard (zero sales → skip margin) | `08:137`, `03b:85`, `longterm/04:173` | **YES** — 0 rows poisoned by zero sales. Viable. |
| `if sf and ...` ROE/DE guard (zero shareholder-funds → skip) | `08:139-142` | **PARTIAL** — catches exactly-zero `sf` but NOT negative or tiny-positive `sf`. Ground truth: **19 rows have `sf<=0`** (17 carry a non-null derived ROE/DE — Indiqube, Krsnaa −1682, etc.) and **25 have `|sf|<1`** — all pass the truthiness guard (negative is truthy) and detonate. Weak. |
| sharescart-vs-screener cross-check → `screener_financials_review.csv` | `03b:58-63` | flags fy3 sales/PAT divergence only; does **not** check EPS unit-breaks or near-zero denominators. Partial coverage. |
| trust-existing-then-screener-fill order (`if pre_ipo_pat != '': continue`) | `08:105` | structurally fine; but no validity gate before accepting either source. |

---

## 4. OPTIONS (≥2–3 per problem; leanings named + a non-leaning steelmanned)

### Problem A — per-year EPS share-base discontinuity (O-5/O-7)
- **A1 (leaning) — recompute per-year EPS on a CONSTANT (post-issue) share base, store the raw source EPS in a `_src_raw`
  shadow only.** EPS_yrN = PAT_yrN × 1e7 / post_issue_shares. Steelman: makes the EPS *trajectory* economically comparable
  (the whole point of per-year EPS is CAGR/trend); kills the inflation at the root. **Cost / dependency (corrected — the
  draft overstated this as a cheap recompute):** post-issue *total shares outstanding* is **NOT currently in the substrate.**
  Verified columns: only `lot_size_shares` (904 nonnull) and `shareholder_funds_yr*` — there is NO total-shares-outstanding /
  float column. `issue_size_cr / issue_price` yields only the NEW shares issued, not total post-issue shares (the latter
  needs the pre-issue share count — precisely the unsolved O-12/market-cap share-count problem). **So A1 is BLOCKED on the
  same share-count work as task_17/O-12; it is NOT a low-cost recompute riding existing data.** Cross-link task_17. (The
  A2-floor conclusion below is unaffected and remains the right primary.)
- **A2 — null the per-year EPS for any year whose implied share-base differs >X× from the latest year; keep latest-year EPS.**
  Steelman: cheap, no new dependency, preserves the one EPS value that's already clean (yr3 is clean in 90/95 cases) and
  honest about the unavailable comparison. Rejected-as-primary (not rejected outright): it throws away usable info that A1
  could *recover*; but it is the correct FALLBACK when share count is unavailable.
- **A3 — leave EPS as-is, add a `eps_yr_comparable` flag + an as-of/share-base note.** Steelman: zero data change, fully
  honest. Rejected as primary: violates north-star "correctness over speed / don't ship a known-misleading number as a
  first-class field"; a downstream EPS-CAGR feature would silently consume garbage.
- **Non-leaning argued on merits:** A2 is genuinely competitive with A1 because **no live numeric feature reads `eps_yr*`**
  (verified — `eps_yr*` is unread by layer3; `eps_ttm` IS consumed indirectly by research tools h2/hmvp via issue-time P/E,
  so it is NOT purely display-only — see O-7). For the per-year series specifically, A2's "null-and-flag" is *sufficient and
  cleaner* than computing a synthetic series nobody reads. A1 is additionally penalized by being **blocked on the O-12
  share-count work** (above). **Leaning resolves to: A2 as the floor (always), A1 only IF an EPS-trajectory feature is ever
  promoted AND the share count is solved** — registered as a validity rule + an optional recompute, so it's a config choice,
  not a rewrite. NOTE: even under A2, the EPS↔PAT sign-consistency rule (34 rows) applies to `eps_ttm` and per-year, since
  `eps_ttm` IS consumed.

### Problem B — net_sales_yr3==0 + non-equity contamination (O-6)
- **B1 (leaning) — 3-state present/absent at load (I1) so a blank/parse-fail becomes NaN, never 0; AND gate the equity
  financials table by `instrument_type==equity` so REIT/InvIT never land in the equity sales column.** Steelman: fixes both
  halves at the structural layer (single source of truth: the missing-policy + the instrument-type dimension). The 5 big
  O-6 offenders vanish from the equity view automatically; the 5 equity shells become NaN-or-real-zero, distinguished.
  Hand the instrument-type half to **task_05b** (which owns the seam) — this task just supplies the evidence.
- **B2 — keep one table, add an `is_nonequity` boolean and special-case the readers.** Rejected: behavioral flag +
  per-reader branching = exactly the if/else sprawl the north-star forbids; doesn't generalize to InvIT/IDR/NCD.
- **B3 — drop REIT/InvIT rows entirely.** Rejected: violates "flag, never silently drop" and the future-universe goal
  (task_13 wants them analyzable separately). Quarantine/derive-view, not delete.

### Problem C — tiny-nonzero-sales margin blow-ups (O-10)
- **C1 (leaning) — a declarative VALIDITY RULE on the latest-year sales cell before it feeds the margin** (e.g. flag/quarantine
  when `pre_ipo_pat / pre_ipo_net_sales` implies |margin| > a sane band AND sales is implausibly small vs PAT — the
  Ujjivan 177/18 signature). Route the row to `quality==dirty`; the margin is computed only on a sane denominator.
  Steelman: catches truncation that the zero-guard misses; declarative (one rule, registry-driven), not per-row patching.
- **C2 — cross-source corroborate the latest-year sales (sharescart vs screener) and quarantine on >X× divergence.**
  Steelman: catches the truncation at the source-disagreement layer (the `03b` cross-check already exists — extend it from
  "review CSV" to "route-to-dirty"). Complementary to C1, not exclusive.
- **C3 — clamp/winsorize margin to ±100%.** Rejected hard: this is exactly the "silent clamp hides bad data" anti-pattern
  the T-4 post-mortem condemned. Flag, don't clamp.

### Problem D — ROE/DE near-zero/negative-equity denominator (O-9)
- **D1 (leaning) — DROP the naive sign test; replace with a `shareholder_funds`-denominator-validity rule:** flag when
  `sf<=0` OR `|sf|` is tiny relative to PAT/borrowings (the detonation condition) → quarantine ROE/DE for that row; keep
  loss-maker `+D/E / −ROE` as VALID (it is). Measured on `sf` directly (`shareholder_funds_yr3`): **19 rows `sf<=0`** (17
  with a non-null derived ROE/DE = the quarantine set), **25 rows `|sf|<1`**. Steelman: targets the real bug (Indiqube /
  Krsnaa class), encodes economic truth, and operates on the upstream denominator not the corrupted derived ratio.
- **D2 — keep the sign test but whitelist loss-makers (PAT<0).** Rejected: a whitelist is a patch over a wrong predicate;
  the predicate itself is the bug. Cleaner to fix the rule (D1).

### Problem E — sourcing / as-of semantics for the financial fields (NEW — completeness, charter §2/§9)
- The draft never reconciled financial sourcing with two documented realities. (1) **As-of leak class (charter §9):**
  financials are TIME-VARYING, and `docs/sources.md:32` warns sharescart carries **"post-IPO financial contamination"** —
  sharescart's 3yr financials may be as-of POST-listing, not at-RHP. Every financial field therefore needs an explicit
  **as-of attribute** (at-IPO RHP snapshot vs current/live), exactly the D-3 mcap-leak class generalized. (2) **Fallback
  source:** `docs/research/data/drhp_recovered.csv` (16 SEBI-DRHP-recovered financials, with `pat_suspect`/review flags) is
  the charter-designated financial overlay/fallback and is the named repair source for O-10 truncations / missing
  `pre_ipo_pat`. **Proposed fallback order (hand to task_02/task_08):** RHP/DRHP-recovered → screener pre-listing FY (G1b) →
  sharescart (last, because of the post-IPO contamination risk; flag, don't silently trust).
- **Coverage (NEW — financials are a COVERAGE issue, not only a corruption issue):** `pre_ipo_pat` coverage is **1318/1357
  (97%) boom vs 602/1027 (59%) longterm** — a stark cohort cliff that biases every financial finding (t9/n7/n13 already
  carry "boom-heavy coverage" caveats). The register must record the per-cohort fill rate + the longterm sourcing gap +
  the fallback (drhp_recovered, screener longterm) intended to close it. Hand to task_02/task_19.

---

## 5. ANALYSIS (step by step)
1. **Two genuinely different failure modes hide under "financials are corrupt":** (a) **EPS share-base discontinuity**
   (O-5/O-7) — *correct source data, wrong for comparison*; (b) **wrong/missing cells** (O-6 zeros, O-10 truncations,
   O-9 negative-equity) — *actually wrong data*. They need different treatments; conflating them (the audit's "÷1000")
   would corrupt good data.
2. **The existing zero-guard already neutralizes the scary half of O-6.** The real residual margin bug is O-10's
   tiny-nonzero denominators — a smaller, sharper target. This is a re-audit WIN: don't rebuild the margin path, just add a
   denominator-validity rule.
3. **O-9: a NAIVE sign test is a phantom, but the audit itself was NOT wrong.** A naive "sign(D/E)≠sign(ROE)" predicate
   flags 54, ~45 of which are valid positive-equity loss-makers. But the alignment_audit scoped O-9 to **9 rows** (the
   negative-equity class) and named Indiqube — so this task **confirms and sharpens** the audit, not overturns it. The real
   bug is the negative/near-zero `sf` denominator: **19 rows `sf<=0`** (17 with a non-null derived ROE/DE). The re-audit
   correction is "use a `sf`-denominator-validity rule, not a sign test" — not "the audit was wrong."
4. **Downstream blast radius is LARGE — NOT "small and known" (the draft's central error, corrected via `grep layer3/`).**
   The corrupted financial fields feed FAR more than n14: (a) `pre_ipo_roe_pct`/`pre_ipo_debt_equity`/`pre_ipo_pat_margin_pct`
   are **Gower distance features in the analog predictor** (`analogs.py:22-25`) AND **query features in data-informed weight
   derivation** (`weights.py:21-23` → `scorecard.quality(q)` → point-in-time rank-IC); (b) the same three feed the **quality
   scorecard component** shown to users (`scorecard.py:445-453`); (c) `pre_ipo_net_sales`+`pre_ipo_pat` feed the **IN-SCORE
   wipeout-safety component** (`rules/index.md:34`, weight ~0.10-0.13) and `pre_ipo_net_sales` is an **IC-0.20 predictor**
   (`rules/index.md:277`); (d) published findings n7 (debt death-signal)/n13/n15/t9/n6/n8 all consume these; (e) n14 itself
   reads the derived `pre_ipo_*` ratios + the VALIDATED `tiny_sales_lt25cr` flag. **So O-9 (Indiqube ROE 1400 / D/E −409.5)
   and O-10 (Ujjivan margin 983 + spurious tiny-sales flag) are SCORED-FEATURE corruption (analog distance + learned
   weights + in-score wipeout-safety/quality), NOT "display-correctness."** EPS is the only family with no live numeric
   consumer of `eps_yr*` (but `eps_ttm` IS consumed via issue-time P/E). The features↔data reverse-map (task_12) must list
   every one of these edges.
   - **The scorecard's `np.clip` MASKS the corruption (a live correctness consequence the draft missed):** for Indiqube
     `scorecard.py:449` computes `np.clip(100 - (-409.5)*40, 0, 100) = 100` — a company with NEGATIVE shareholder funds gets
     the **MAXIMUM "good-debt" score**; ROE 1400% and margin 983% likewise clip to band extremes. This is exactly the
     "silent clamp hides bad data" anti-pattern condemned in C3/T-4, already live in scoring. **The D1 denominator-validity
     rule must quarantine BEFORE the value reaches `scorecard.quality()`** — the clip must not be relied on.
5. **Everything routes to two architectural seams the run already owns:** the **missing-policy / 3-state present-absent**
   (task_03 / I1) and the **instrument-type dimension** (task_05b). Financials should not invent its own machinery — it
   should *register validity rules* (column registry, task_06) and let the spine route bad rows to `quality==dirty` **before
   the corrupted value reaches any scored feature** (per point 4 — quarantine upstream of `scorecard.quality()`/`analogs`/`weights`).

---

## 6. TEST / VALIDATE (numbers + ≥2 ISIN examples per claim)

| Claim | Predicate (read-only) | Result | False-pos / over-catch check |
|---|---|---|---|
| O-5 reproduces | `\|eps_yr1\|>1000` ; `\|eps_yr2\|>1000` | 51 ; 57 | yr3=25, ttm=3 (audit's "yr3/ttm cleaner" holds) |
| O-5 root = share-base, not ÷1000 | cross-year `eps/pat` ratio >100× break | **95 rows**; latest year clean in **90/95** | raw `screener/financials.csv` confirms tiny pre-IPO share base (Honasa, Syrma, Delhivery) |
| O-7 reproduces | `\|eps_ttm\|>2000` | 3 (all SME) | INE1I1301016 / INE1EUB01016 / INE14VP01014 |
| O-6 count | `net_sales_yr3==0` | 13 (equity 5 / reit 4 / invit 4) | big-yr2 offenders ALL non-equity (5/5) |
| **O-6 "poisons margins" — DOES NOT hold** | `pre_ipo_net_sales==0 AND margin not null` | **0 rows** | zero-guard `if sales` works; over-fear caught |
| O-10 reproduces (broader) | `\|pre_ipo_pat_margin_pct\|>80` | 11 rows | tiny-sales (<₹5cr) & \|margin\|>50: 14 rows; `<25 & \|margin\|>80`: 11 (feed validated tiny_sales flag) |
| **O-9: naive sign test over-flags; audit's "9 rows" = the real bug** | `sign(D/E)≠sign(ROE)` vs `de<0` | 54 sign-mismatch; **14** `de<0`; **9** are BOTH (≈ audit's 9) | ~45 sign-mismatches are valid +equity loss-makers; the audit's 9-row scope = the `de<0` detonation class |
| **D1 quarantine set (the proposal, on `sf` itself)** | `shareholder_funds_yr3 <= 0` ; `\|sf\|<1` | **19** ; **25** | 17 of the `sf<=0` carry a non-null derived ROE/DE (= rows to quarantine); loss-makers with `sf>0` NOT caught (correct) |
| ÷1000 fix empirically dead | `\|eps_yr1/eps_yr3\| ∈ [990,1010]` | **0 rows** | no per-row clean 1000× ratio → audit's "peaks at 1000.0" is a population artifact |
| EPS↔PAT sign-consistency (NEW class) | `sign(eps_ttm)≠sign(pre_ipo_pat)` | **34 rows** | distinct from magnitude inflation; route to dirty (per-year analog applies too) |
| per-year zeros broader than yr3 | `net_sales_yr1==0` / `yr2==0` ; `pat_yr1/2/3==0` | 32 / 20 ; 184 / 102 / 61 | feeds n14 declining flags; `declining_pat` lacks the `p1>0` guard → false flags |
| O-6b other-column zeros/invalids | `operating_profit_yr1/2/3==0` ; `pe_ratio<0` ; `pe_ratio>500` ; `pat_ttm_cr==0` | 77/51/29 ; 46 ; 2 ; 19 | operating_profit_yr3 read live by n14; negative P/E should be null |
| coverage cliff | `pre_ipo_pat` nonnull by cohort | boom 1318/1357 (97%) ; longterm 602/1027 (59%) | longterm sourcing gap biases every financial finding |

**Worked ISIN examples:**
- **INE0J5401028 (Honasa):** substrate `eps_yr1` = −1,306,098 (the substrate-wide max EPS magnitude); raw Screener EPS
  FY2021 = −1,306,098 on PAT −1,332 cr (⇒ ~10k shares) vs FY2023 EPS −10.47 on PAT −151 cr. ⇒ O-5 = real share-base
  discontinuity, NOT a parse bug. **Year-alignment note (prevents a false "numbers don't tie" flag):** `eps_yr1` is the
  EARLIEST pre-IPO year (FY2021, PAT −1,332) while the substrate's `pre_ipo_pat = −151` is the LATEST year (FY2023) — they
  are DIFFERENT fiscal years (that is the whole point of the share-base discontinuity), so the −1.3M `eps_yr1` pairs with the
  FY2021 PAT, not with `pre_ipo_pat`.
- **INE334L01012 (Ujjivan Financial):** `pre_ipo_pat_margin_pct = 983.3%`, from `pre_ipo_pat=177 / pre_ipo_net_sales=18`
  (FY `Mar 2016`). **Verified: `18` is the raw screener value verbatim** (`data/raw/screener/financials.csv`:
  `INE334L01012,2016,sales,18.0`; FY2017=24, FY2018=8) — there is NO pipeline truncation of 1800→18. Root cause = an
  **implausible SOURCE value for a finance company** (NBFC "sales" ≠ topline revenue / possible wrong-FY), passing the
  zero-guard. ⇒ O-10 = wrong-but-nonzero denominator; ALSO spuriously fires the validated `tiny_sales_lt25cr` flag on a
  multibagger bank. (A corrected ~₹1,800 cr is a DRHP-confirmable hypothesis, not an established fact.)
- **INE06ST01018 (Indiqube Spaces):** `pre_ipo_roe_pct = 1400%`, `pre_ipo_debt_equity = −409.5` → negative shareholder-funds
  denominator detonation. ⇒ the GENUINE O-9 row (one of the audit's 9 `de<0` rows / 19 `sf<=0`), not the naive 54-row sign
  phantom. The corrupted D/E −409.5 ALSO clips to the MAX debt-score (100) in `scorecard.quality()` — a live scoring error.
- **INE0CCU25019 (Mindspace REIT):** `net_sales_yr3=0`, `net_sales_yr2=1432`, instrument_type=`reit`. ⇒ O-6 = non-equity
  contamination, hand to task_05b.

---

## 7. NON-FINAL PROPOSAL + OPEN OWNER-QUESTIONS

### Proposed handling (NOT FINAL — for owner approval)
1. **Reclassify O-5/O-7 from "corruption" to "comparability" (operationalizing data_review.md:46-47, not a new finding).**
   The per-year/TTM EPS is *correct source data on a changing share base*. **Floor fix (A2):** register a validity rule that
   NULLs a per-year EPS whose implied share-base differs >~50× from the latest pre-IPO year, and add a present/absent code
   ("source-published-but-not-comparable"). **Plus the EPS↔PAT sign-consistency rule** (34 rows; per-year analog) → dirty.
   **Optional upgrade (A1):** recompute EPS on a constant post-issue share base — but ONLY if an EPS-trajectory feature is
   promoted AND the O-12 share count is solved (A1 is blocked on it). Note `eps_ttm` IS consumed (issue-time P/E via h2/hmvp),
   so it is not purely display-only. Do **NOT** apply the audit's "÷1000" (0 rows show a clean per-row 1000× ratio).
2. **O-6: keep the existing zero-guard (it holds — 0 rows poisoned),** add the I1 3-state encoding so `0` for sales becomes
   "absent" not a real zero (**17 rows** carry literal `0.0` in `pre_ipo_net_sales`; plus per-year `net_sales_yr1/2==0`
   32/20 and `pat_yr*==0` 184/102/61, and `operating_profit_yr*==0` 77/51/29 — all to task_19), and **hand the REIT/InvIT
   contamination to task_05b** (gate the equity financials table by `instrument_type==equity`). The 5 big offenders are
   non-equity; the 5 equity shells become NaN/real-zero distinguishable. **task_12 handoff:** n14's `declining_pat` lacks
   the `p1>0` guard that `declining_revenue` has → fix the feature.
3. **O-10: add a latest-year-sales denominator-validity rule** (flag the implausible-vs-PAT signature — Ujjivan 177/18 —
   or sharescart-vs-screener divergence) and route the row to `quality==dirty`; margin computed only on a sane denominator.
   **This is feature-corrupting, not cosmetic** — it poisons the derived margin, the analog distance, the data-informed
   weights, AND spuriously fires the validated `tiny_sales_lt25cr` flag on the 11 `<25 & |margin|>80` rows (Ujjivan = a
   multibagger bank), and corrupts the IC-0.20 `pre_ipo_net_sales` feature. Cross-reference the existing 21-row
   `data/master/review/screener_financials_review.csv` for overlap. **No clamping** (T-4 lesson) — and note the scorecard's
   own `np.clip` already silently masks these (Indiqube D/E −409.5 → debt-score 100), so quarantine must happen UPSTREAM.
4. **O-9: replace the naive sign test with a `shareholder_funds`-denominator-validity rule (CONFIRMS the audit's 9-row
   scope, does not overturn it).** The naive sign test over-flags 54 (~45 valid +equity loss-makers); the audit already
   scoped O-9 to 9 rows (the `de<0` class) and named Indiqube. Quarantine ROE/DE where `sf<=0` (**19 rows**, 17 with a
   non-null derived ratio) or `|sf|` is tiny vs PAT/borrowings; keep loss-maker `+D/E / −ROE` as valid. Audit `sf` directly,
   not the derived ratio.
5. **All become declarative VALIDITY RULES in the column registry (task_06), routing bad rows to the `quality==dirty`
   quarantine (task_04/task_11) BEFORE the value reaches any scored feature** (`scorecard.quality()`/`analogs`/`weights`) —
   no per-field bespoke scripts, no behavioral flags. Financials fixes ride the same missing-policy + instrument-type seams
   as everything else (north-star: single source of truth, minimal flags).
6. **Sourcing/as-of + fallback (task_02/task_08):** give every financial field an **as-of attribute** (at-IPO RHP snapshot
   vs current) — sources.md:32 warns sharescart carries post-IPO contamination. Named fallback order: **DRHP-recovered
   (`docs/research/data/drhp_recovered.csv`, 16 rows) → screener pre-listing FY (G1b) → sharescart**. Record the per-cohort
   coverage cliff (`pre_ipo_pat` 97% boom / 59% longterm) + its longterm sourcing gap.
7. **Schema-drift handoff to task_01 (COMPLETE list — the draft named only 3):** absent from substrate but in `docs/schema.md`:
   `pre_ipo_eps`; plain `roe_pct` (schema.md:32, sharescart-attributed) and plain `debt_equity` (schema.md:34); plus
   `roce_pct`, `pre_ipo_roce_pct`, `pre_ipo_ebitda_margin_pct`, `sales_cagr_3y`, `pat_cagr_3y`,
   `pre_ipo_net_sales_growth_pct`, `pre_ipo_pat_growth_pct`, `pre_ipo_shareholder_funds`, `pre_ipo_borrowings`. For each,
   task_01 decides: target field to source (end-state) vs doc artifact to delete. Also surface the **source-attribution
   contradiction** (schema says sharescart; `08_build_universe` overwrites per-year from screener; sources.md G1b names
   screener) to task_01/task_02.

### Open owner-questions
1. **EPS comparability (A1 vs A2):** is the per-year/TTM EPS ever going to feed a feature (EPS-CAGR/trend)? If **no** →
   null-and-flag (A2) is enough. If **yes** → recompute on a constant share base (A1). Which?
2. **Truncated-cell repair (O-10):** when the latest-year sales cell is implausible (Ujjivan 18 vs ~1,800), do we (a) only
   quarantine + null the derived margin/ROE, or (b) attempt a corrected value from a second source (sharescart / DRHP)
   under the overlay (task_08)?
3. **Non-equity financials (O-6 REIT/InvIT):** confirm these go to task_05b's equity-table gate (exclude from equity
   financials) vs analyzed-separately — the standing STATUS.md "non-equity handling" decision. (Cross-ref task_05b.)
4. **O-9 rule:** confirm we use the `shareholder_funds`-denominator-validity rule (`sf<=0` / tiny-`sf`, 19 rows) instead of
   a naive sign test. NOTE: this CONFIRMS the alignment_audit's 9-row scope (the `de<0` class), it does not supersede the
   audit — the naive 54-row sign test is a predicate the audit never used. Agree?
5. **Validity-rule severity:** for a financial validity failure, default to `quality==dirty` (row quarantined from the clean
   substrate) or `null the offending derived field but keep the row clean`? (Affects how aggressively margins/ROE are
   suppressed.)

---

## DONE CHECKLIST
- [x] all 8 steps present and non-empty (scope · ground-truth · reproduce/re-audit · options · analysis · test · proposal · open-Qs)
- [x] ground-truth inputs cited by FILE PATH
- [x] step-6 numbers present (caught/missed/over-caught counts + ≥2 ISIN examples: INE0J5401028, INE334L01012, INE06ST01018, INE0CCU25019)
- [ ] review-loop stop rule — **IN PROGRESS** (Round 1 multi-lens review applied 2026-06-17, see below; the stop rule
  requires ≥2 consecutive INDEPENDENT fresh-agent rounds with zero new findings ≥LOW — NOT yet satisfied. Log each round in
  `night_run_2026-06-17_review_log.md`.)
- [x] NOT-FINAL marker + open-owner-questions block present

> **Review status: ROUND 1 of multi-lens review (correctness · completeness · context-pickup · north-star · adversarial)
> has been APPLIED to this draft** — the major round-1 corrections folded in: (1) the blast-radius rewrite (n14 is NOT the
> only consumer; O-9/O-10 corrupt the analog Gower distance, the data-informed weights, and the in-score wipeout-safety +
> quality components — `grep layer3/` verified); (2) O-9 reframed to CONFIRM the audit's 9-row scope (not "audit wrong");
> (3) O-10 Ujjivan root-cause corrected to "implausible source value, not pipeline truncation" (raw screener sales=18
> verbatim); (4) eps_yr1 max corrected to 1,306,098; ÷1000 empirically killed (0 rows); (5) scope expanded to all financial
> columns + coverage cliff; (6) `sf` denominator audited directly (19 rows sf<=0); (7) sourcing/as-of + DRHP fallback added;
> (8) schema-drift list completed; (9) EPS↔PAT sign-consistency (34) added; (10) scorecard `np.clip`-masks-corruption noted;
> (11) data_review.md:46-47 cited as the prior EPS resolution. **Still REQUIRED before COMPLETE:** ≥2 consecutive clean
> independent fresh-agent rounds, each logged. This remains an author-incorporated draft, NOT final.**
