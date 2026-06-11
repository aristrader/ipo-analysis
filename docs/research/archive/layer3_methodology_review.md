# Layer 3 Part A — Adversarial Methodology Review

**Reviewer stance:** the analysis is guilty of lying until proven robust. Scope: the plan in
`docs/superpowers/plans/2026-05-31-layer3-partA-descriptive.md` (method spine `layer3/spine.py` + 8 Tier-1 findings T1,T2,T3,T5,T6,T7,T8,T9 + report assembler), checked against the actual substrate `data/master/ipo_analysis.csv` (2,296 rows; 2,245 equity) and the coverage map in `TODO.md`.

**What I verified against the real file (2026-05-31):**
- equity cohort×segment counts: boom-MB **370**, boom-SME **884**, long-MB **471**, long-SME **520**.
- alpha non-null by cohort: 1y boom 947 / long 743; **3y boom 353 / long 738; 5y boom 69 / long 725; 10y boom 11 / long 365.**
- `broad_sector` non-null: **boom-MB 3%**, boom-SME 29%, long-MB 64%, long-SME 80%.
- `market_cap_class`: **1,233 of 2,245 (55%) are NaN.** micro 650 / small 189 / mid 116 / large 57.
- `listing_metrics_status`: ok 2,019 / unreliable_coverage **124** / inferred_split **83** / NaN 19. (Plan text says 142/85; file says 124/83 — minor, but the **NaN 19 and inferred_split 83 are not addressed by the plan's exclusion list**, see §3.)
- `delist_reason`: only **40 non-null** (Liquidation 20, Compulsory 14, Voluntary 6); `delisted==True` = **195**. So **155 delisted rows have NO reason.**
- `outcome_class`: multibagger 685, winner 346, flat 308, loser 700, wipeout 141, **NaN 65.** Plan/spine assume ~97% non-null and never specify NaN handling.
- **`outcome_class` is defined on RAW `current_return_from_issue`, not alpha** (multibagger median raw ret = 3.36x; wipeout = −0.97). This is a benchmark mismatch with the "returns = alpha" headline (§5/§1-trap-3-adjacent).
- **No `age_days`/`age_years` column** — T2 must derive age from `listing_date`; plan assumes it exists.
- **No `alpha_sc_*` / Smallcap-250 columns at all** — confirmed; the report header still claims nothing false, but T7's "raw vs alpha for small/micro" must use `return_from_issue_*` (raw, mixed-age) vs `alpha_*`.
- **`return_from_listing_*` exists but is RAW return, not alpha-from-listing.** There is **no from-listing alpha column.** This is the central T3 trap (§3).
- `data_quality_tier`: high 1558 / med 491 / **low 196** (not 213). `liquidity_flag`: ok 1415 / low 811 / **NaN 19** — the `investable()` filter `== 'ok'` silently drops the 19 NaN; fine, but should be conscious.

The plan is solid in spirit (the spine encodes maturity-gating, competing-risks, MB/SME split, min-N, distributions). The danger is in the **findings layer and presentation**, where the spine's guards are easy to bypass. Below: every place a trap can bite, with a concrete fix (a spine function, a guard, or a presentation rule).

---

## 1. The 5 traps — where each bites and the exact guardrail

### Trap 1 — Vintage = Regime collinearity (SEVERITY: HIGH)
Only ~2–3 macro regimes exist in 19 years. Any finding that shows boom vs longterm and reads the difference as a *structural* effect is really reading the 2020–25 bull regime vs the mixed 2006–19 regime.

**Where it bites:**
- **T1 (HIGH):** "boom median 1y alpha > longterm median 1y alpha" will look like a segment truth but is a regime artifact (boom = a historic bull run for small-caps). The plan shows both cohorts side-by-side (good) but provides **no within-vintage control** — the spine has no listing-year axis.
- **T9 (HIGH):** "profitable-at-IPO premium widens with horizon" — if profitable names cluster in a different vintage than loss-makers, the horizon-widening is a vintage drift, not a quality effect. Coverage map confirms `pre_ipo_pat` is 90–99% boom but 27–34% long-MB → **profitable-flagged rows are disproportionately boom**, loss/unknown disproportionately longterm. The comparison is **confounded by cohort by construction.**
- **T5 (MED):** OFS gradient — PE-exit-heavy high-OFS issues cluster in specific windows.

**Fix:**
1. Add `spine.by_listing_year(df, col)` returning the metric **within each listing-year band** (e.g. 2006–09, 2010–13, 2014–16, 2017–19, 2020–22, 2023–25), so the cross-regime claim is "sign holds *within* a vintage," per method spine §8. Make it a required panel for T1, T5, T9.
2. **T9 guard:** compute the profitable-vs-loss alpha gap **stratified by cohort** (and within-vintage) and render BOTH cohorts' gaps. Add caveat: "profitable-flag coverage is boom-skewed (90%+ boom vs 27–34% long-MB); a horizon-widening gap that appears only when cohorts are pooled is a vintage artifact, not validated." Refuse to state "gap widens with horizon" as confirmatory unless the *sign* holds within at least two vintages.
3. Presentation rule: any boom-vs-longterm delta narrative must carry the standing caveat "cohort difference conflates segment effect with market regime; treat as hypothesis unless the sign also holds within a single vintage."

### Trap 2 — Conditioning collapse / tiny-N cells (SEVERITY: HIGH)
2,245 equity rows shatter fast: MB/SME × cohort × mcap(5 incl. unknown) × horizon. T1 alone is 2×2×5×3 = 60 cells, many < 10.

**Where it bites:**
- **T1 (HIGH):** mcap × cohort × horizon. With mcap NaN 55% and 5y boom alpha N=69 total, a cell like "boom-MB-large-5y" is **N≈0–3**. The plan's min-N floor (render "insufficient (N=k)" for N<10) is specified for findings but the **floor logic lives only in the per-finding `compute` (easy to forget); the spine `distribution()` returns a tier but does not blank the percentiles.** A finding that prints `d["median"]` directly bypasses the floor.
- **T6 (HIGH):** sector × MB/SME × cohort with boom-MB sector at 3% (≈11 rows) — see §2.
- **T8 (MED):** "eventual winners" further split by MB/SME × mcap — multibagger SME in a given mcap can be < 10.

**Fix:**
1. Make the floor **unbypassable in the spine.** Add `spine.safe_metric(value, n)` and have `distribution()` return a `display` dict whose percentile fields are the **string `"insufficient (N=k)"` when `tier=='insufficient'`**, with the raw floats kept under separate keys for charting. Findings must render `display`, never raw floats. Add a test (`test_distribution_blanks_subfloor`) asserting sub-10 percentiles render as the string.
2. Add `spine.guard_cells(table, n_col="N")` that the report assembler applies to **every** table: any row with N<10 has its numeric metric columns replaced by the insufficient-string, and the row is added to a "suppressed for low N" caveat list automatically. This makes the floor a property of the assembler, not finding discipline.
3. Charts must not plot sub-floor cells (a bar at N=3 looks identical to N=300). `charts.bar_png` should accept an `n_map` and grey-out / annotate bars with N<10, or the finding must drop them before charting.

### Trap 3 — Dirty inputs as ground truth (SEVERITY: MED for Part A; HIGH for the inputs it does use)
Part A wisely uses no GMP in any Tier-1 finding (GMP is Part B / quarantined). But two dirty-input variants survive into Part A:

**Where it bites:**
- **T9 (MED-HIGH):** `pre_ipo_pat` is **RHP-sourced pre-IPO financials** — the dirtiest non-GMP input (restatement, consolidated-vs-standalone noise, provenance = prospectus). The plan caveats provenance, but the **profitable/loss split is treated as ground truth** in the headline. Also the fallback `pat_ttm_cr` is a *different vintage* of profitability than `pre_ipo_pat` — mixing them changes the definition mid-population.
- **T1/T6 "% multibagger" (MED):** `outcome_class` is computed on **raw `current_return_from_issue`**, not alpha. So a finding headlined "alpha base rates" silently mixes a **raw-return-defined** multibagger rate with **alpha-defined** distribution stats. A 2021 micro-cap that 3x'd while smallcaps 2.5x'd is a "multibagger" with thin alpha. This is a quiet benchmark-inconsistency, not a data-cleanliness issue, but it lies the same way.

**Fix:**
1. **T9:** Pick ONE profitability definition and stick to it; **do not silently fall back** from `pre_ipo_pat` to `pat_ttm_cr`. If falling back, add a `profit_flag_source` column and report the two sources as **separate sub-cohorts**, never merged. Mark the entire T9 finding `reliability: RHP-sourced — directional` in its caveats and in the report header chip.
2. **T1/T6:** State explicitly in every "% multibagger" cell that **multibagger is a raw-return classification** (≥~2x from issue), distinct from the alpha distribution in the same table. Better: add `spine.pct_multibagger_alpha(df, horizon)` computing ≥2x on an **alpha-or-raise basis** and show it next to the raw-return multibagger rate so the wedge is visible. At minimum, a per-table footnote: "multibagger = raw return ≥2x from issue; alpha columns are vs Nifty 50 — the two can disagree."
3. Add a **reliability chip** to the `Finding` dataclass (`reliability: str` ∈ {official, mixed, rhp-sourced}) rendered as a colored badge, so the reader sees provenance without reading caveats. (Method spine §7.)

### Trap 4 — Survivorship + right-censoring asymmetry (SEVERITY: HIGH)
Two distinct asymmetries: (a) delisted winners (buyout/payout) vs delisted losers (wipeout) must not be lumped; (b) young IPOs are right-censored — absence of a 5y outcome is not a 5y outcome.

**Where it bites:**
- **T2 (HIGH):** competing-risks. The spine's `terminal_state` maps the **155 delisted-without-reason** rows to `alive_delisted_unknown` *unless* `outcome_class=='wipeout'`. But `outcome_class` is NaN for 65 rows, and a delisted-unknown row that is `loser` (−54% median) is **neither alive nor wiped out** — calling it "alive" understates death risk; calling it wipeout overstates it. T2's cumulative wipeout curve depends entirely on how these 155 are bucketed, and the plan leaves them in a third bucket that **the wipeout curve presumably ignores** → systematic **under-counting of wipeout**. Also the plan's T2 test asserts wipeout-rate is "monotonic-ish nondecreasing in year" — but with **maturity-gating, the denominator changes each year** (only IPOs old enough to reach year Y), so a naive cumulative rate can be **non-monotone** purely from cohort composition, and the test will either fail spuriously or force a wrong implementation.
- **T1 "% below issue" (HIGH):** uses `current_return_from_issue` which is a **lifetime return as of today, mixing a 2006 IPO (19y) with a 2024 IPO (1y)** — see §3 look-ahead. A young IPO that is −10% today is right-censored, not a final loss.
- **T8 (MED):** "eventual winners" is defined on terminal `outcome_class`, which for young boom IPOs is a 1y verdict, not a mature one — survivorship of the *label*.

**Fix:**
1. **`terminal_state` must surface the unknowns as a first-class category, and T2 must report a band, not a point.** For the cumulative wipeout curve, compute **two bounds**: a *lower* wipeout estimate (unknown-reason delisted = not wipeout) and an *upper* estimate (delisted-unknown that are loser/wipeout-class = wipeout). Render T2 as a **shaded band between lower/upper**, with the count of unknown-reason delisted shown per year. Never a single line.
2. **Competing-risks denominators:** wipeout/payout rates at year Y must use **only IPOs that have ≥Y years of listed history** (maturity-gating the risk-set), with the **survivor/at-risk count printed at each year** (already in the plan — enforce it). Replace the "monotonic nondecreasing" test with a **per-fixed-cohort monotonicity** test (within a single listing-year band the cumulative count of wipeouts is nondecreasing) — the *pooled* rate need not be monotone and the test must not require it.
3. **T1 "% below issue":** do NOT use `current_return_from_issue` (mixed-age). Replace with a **maturity-gated, horizon-specific** "% with negative alpha at 1y / 3y / 5y" using `maturity_gated(df, h)`. Keep a clearly-labeled separate "lifetime current return (as-of today, ages mixed)" column only as color, flagged "ages mixed — not a base rate."

### Trap 5 — SME ≠ Mainboard pooling (SEVERITY: HIGH)
SME is 884/1254 of the boom equity count → any pooled boom stat is secretly an SME stat. SME is illiquid/manipulated/often un-investable.

**Where it bites:**
- **Report header & every chart (HIGH):** the plan's `assemble()` header says "MB and SME never pooled," and findings run them separately — good. But the **overall/headline rows in T1** ("overall" before mcap split) and any chart that aggregates can still pool. The `run_layer3_report.py` subtitle "N=2245 equity IPOs" is itself a **pooled count** that anchors the reader.
- **T3 (HIGH):** SME listing microstructure is manipulated (circuit games). The plan marks SME buckets "exploratory" — keep, but the from-listing forward-return for SME is **doubly unreliable** (manipulated listing price × thin liquidity).
- **T8 (MED):** SME drawdowns are liquidity artifacts (circuit-locked prints), not real tradeable drawdowns.

**Fix:**
1. **No pooled headline metric anywhere.** Add a spine assertion `spine.assert_segmented(table)` that fails if a results table lacks a `segment` (MB/SME) column or an explicit per-segment breakdown. The assembler refuses to render an un-segmented metric table (counts-only tables exempt).
2. **Liquidity-gate SME upside, keep SME downside.** Method spine §5: for T1/T3/T8, show SME metrics **both** raw and `investable()`-filtered (liquidity_flag=='ok'), so the reader sees how much SME "outperformance" evaporates when restricted to tradeable names. Make `investable` a standard second panel for any SME upside claim.
3. **Mark every SME upside number "microstructure-suspect"** via the reliability chip; SME survival/wipeout (downside) can stay normal-reliability.

---

## 2. Coverage-driven bias — where a data gap masquerades as a finding

This is the highest-yield attack surface. **The boom cohort cannot supply long-horizon or sector data; the longterm cohort cannot supply GMP/PE/subscription/anchor.** Any finding that reads across this asymmetry will manufacture a "trend."

| # | Where | The lie it can tell | Severity | Fix |
|---|---|---|---|---|
| C1 | **T1 / T9 horizon panels** | Shows boom 1y alpha next to longterm 5y alpha and the eye reads a "fade with horizon" or "boom does better." **Boom 5y N=69, 10y N=11** — essentially nonexistent. A horizon curve drawn across cohorts is a **cohort swap**, not a time effect. | HIGH | Long-horizon (3y/5y/10y) panels must be **longterm-cohort-only by default**, with boom long-horizon cells either suppressed (N<30) or explicitly tagged "boom, N=k, not mature — illustrative only." Add `config.LONG_HORIZON_COHORT = "longterm"` and a spine helper `maturity_gated` already gates rows, but add a finding-level rule: **never draw a single horizon line that switches cohorts between points.** |
| C2 | **T6 sector matrix, boom** | boom-MB sector = **3% (~11 rows total, before MB and before per-sector split)**. A "boom mainboard sector matrix" is N=1–3 per sector — pure noise that will print as a ranked table. | HIGH | T6 must **compute boom-MB sector only if total boom-MB-with-sector ≥ MIN_N_TRADABLE (30)** — it is not (≈11), so **boom-MB sector is suppressed entirely** with a one-line coverage note: "boom mainboard sector coverage 3% — sector matrix not computable for this cell; recover via TODO boom-sector re-pull." Sector findings are **longterm-carried**; state this. Add an explicit assertion in the T6 test that boom-MB sector cells are suppressed. |
| C3 | **T6 / T1 mcap** | mcap NaN = **55%**. A mcap table that silently uses the 45% with mcap will report "large-cap IPOs do X" off the survivor-biased subset (mcap is present mostly for longterm survivors + boom that screener resolved). | HIGH | Treat **unknown-mcap as its own bucket and always show its N and its metrics** (plan says this — enforce via assembler: a mcap table missing the "unknown" row fails a test). Never normalize "% by mcap" over only-known rows. Add caveat: "mcap known for 45% of equity; unknown skews to early-longterm and unresolved boom — unknown bucket shown explicitly, never imputed." |
| C4 | **T5 OFS by promoter %** | `promoter_post_issue_pct` coverage 54%/63% boom, **0% longterm** → any promoter-holding gradient is **boom-only** and cannot be cross-regime validated; presented next to a cross-regime OFS gradient it borrows false credibility. | MED | Promoter-% sub-analysis flagged **single-regime (boom-only)** explicitly; it must not appear in any cross-regime panel. OFS itself is 100% covered — keep OFS cross-regime, isolate the promoter sub-panel. |
| C5 | **T7 / any subscription mention** | subscription is 93% boom-MB but **18% long-MB, 0% long-SME** → if any Tier-1 finding slices by subscription (T7 lists denominators only — OK), it is boom-only. | LOW (Part A doesn't slice on it) | Keep subscription out of Tier-1 base rates (it is); if T7's coverage table includes it, label boom-only. |
| C6 | **T9 profitable flag** | `pre_ipo_pat` 90%+ boom vs 27–34% long-MB → "profitable" rows ≈ boom, "loss/unknown" ≈ longterm → profitable-vs-loss is **cohort-vs-cohort in disguise** (also Trap 1). | HIGH | Same as Trap-1 fix: stratify by cohort; report the gap **within each cohort**; show the **unknown-profitability** rate per cohort (a 70%-unknown long-MB makes any long-MB profitable-premium claim unsupportable). |
| C7 | **Report subtitle / headline N** | "N=2245" pooled across MB/SME/cohort anchors the reader to a number that no single finding actually uses. | LOW | Subtitle should read the **segmented** counts ("MB 841 / SME 1404; boom 1254 / longterm 991") not a single pooled N. |

**Standing rule (add to the assembler):** every table renders a **coverage line** = "% of the relevant segment population this table is computed on" (non-null share of the keying feature). A sector table on 3% coverage must SAY 3% on its face. Add `spine.coverage_note(df_segment, feature)` and require it on T5/T6/T9.

---

## 3. Selection / look-ahead in descriptive stats

Descriptive ≠ immune to look-ahead. Specific leaks:

1. **`outcome_class` thresholds (MED).** outcome_class is a **terminal/as-of-today label on raw return**. Using it as a *grouping* variable (T8 "eventual winners", T1/T6 "% multibagger") imports look-ahead into a base rate: you are selecting on the outcome to describe the outcome. This is **fine for descriptive "what did winners endure"** (T8) but **must be labeled "conditioned on the realized terminal outcome — not knowable at IPO."** Add a caveat chip "outcome-conditioned (hindsight)" on T8 and on any % multibagger. Also **65 NaN outcome_class rows** — specify: excluded from outcome-class groupings, counted in the denominator's "unknown."

2. **`current_return_from_issue` mixes ages (HIGH).** Confirmed no `age_years` column; this field is lifetime-to-today. A "% below issue" or "median current return" off it pools a 19-year compounding with a 1-year one. **Banned from any base rate.** Replace with maturity-gated horizon alpha (see Trap-4 fix). Allowed only as an explicitly-labeled "as-of-today, ages mixed" color column.

3. **`listing_metrics_status` inclusion (MED).** Plan excludes `unreliable_coverage` (124) for T3 — correct. But it is **silent on `inferred_split` (83) and NaN (19)** for listing metrics. `inferred_split` means the split was inferred, so `adj_listing_gain_*` is model-derived, not observed → T3 buckets built on inferred splits carry extra error. **Fix:** T3 should (a) exclude `unreliable_coverage` AND `NaN` status, and (b) flag `inferred_split` rows as a lower-confidence sub-bucket (show T3 with and without inferred_split, or mark those rows). Add `config.EXCLUDE_LISTING_STATUS = ["unreliable_coverage", None]` handling and an `inferred_split` flag column passthrough.

4. **T3 from-listing basis is missing alpha (HIGH).** Verified: `return_from_listing_*` exist but are **raw returns**; `alpha_*` are **issue-anchored**. T3 wants "forward alpha *from listing*" — **neither column provides it.** The plan's "approximate from `alpha_*` (issue-anchored)" is wrong: issue-anchored alpha includes the listing pop itself, so bucketing by listing-pop and then measuring issue-anchored alpha **double-counts the pop** (mechanical correlation → fake "big pops fade" or "big pops persist" depending on sign). **Fix:** either (a) compute a true from-listing alpha = `return_from_listing_h − benchmark_return_over_same_window` (needs the benchmark path — may not be feasible in Part A), or (b) **use raw `return_from_listing_*` and drop the word "alpha" from T3**, labeling it "forward RAW return from listing (benchmark not subtracted; secondary buyer's gross experience)." Do NOT bucket on listing pop and report issue-anchored alpha. Add a test that T3 never reads an `alpha_*` column.

5. **Delisted-without-reason in competing risks (HIGH).** The 155 reason-less delisted rows are a selection hole; see Trap-4 fix (band, not point). Additionally: **`delisted==True` (195) vs `delist_reason` (40)** means 80% of delistings are unexplained — T2's headline must lead with this coverage fact, not bury it.

6. **`liquidity_flag` NaN (19) (LOW).** `investable()` `== 'ok'` drops NaN silently. Decide: NaN liquidity → excluded from investable view, counted in the un-filtered view. Document.

---

## 4. Multiple comparisons — 8 findings × many slices → false positives

8 findings, each MB/SME × cohort × (mcap or sector or bucket) × multiple horizons = **easily 200+ reported cells.** At that volume, several "patterns" are noise. The plan has min-N floors but **no multiple-comparisons discipline and no confirmatory/exploratory tagging.**

**Fix — pre-registration discipline:**
1. Add a top-of-report **"Pre-registered confirmatory claims"** box listing the handful of Tier-1 hypotheses that are *the point of the tool*, and treat everything else as **exploratory** (rendered, but tagged). Confirmatory set (proposed, from `docs/strategies.md` Tier-1 intent):
   - **CONF-1 (T1):** survivorship-honest median 1y alpha is positive for MB and negative-or-lower for SME (the anchor truth).
   - **CONF-2 (T2):** SME cumulative wipeout-rate exceeds MB at every matured year.
   - **CONF-3 (T9):** profitable-at-IPO names have **lower wipeout rate** than loss-making (sign), **validated within at least one single cohort** (not pooled).
   - **CONF-4 (T5):** high-OFS (75–100%) has **lower long-term median alpha and/or higher wipeout** than low-OFS, dose-response sign.
   - **CONF-5 (T3):** the top listing-pop bucket has **lower forward from-listing return** than the bottom bucket (mean-reversion sign).
   A confirmatory claim is "supported" only if **the sign holds in BOTH cohorts (or within ≥2 vintages) at N≥30 per side.** Otherwise it is downgraded to "exploratory — not confirmed."
2. **Everything else (T6 sector rankings, T8 drawdown-by-mcap, all mcap cells, all bucket×segment×cohort cells) is EXPLORATORY** and rendered with an "exploratory — multiple comparisons not controlled; hypothesis-generating" chip. Add `Finding.claim_type` ∈ {confirmatory, exploratory} and a per-cell `exploratory` flag for sub-slices beyond the pre-registered axis.
3. **Sector matrix (T6) is inherently many comparisons** (10+ sectors × 2 segments × metrics). Rank-and-highlight invites cherry-picking the top sector. Fix: present T6 as a **full ranked table with a "do not read individual sectors as signals; N per cell shown" banner**, and **do not** narrate "Sector X is best." Report only the *aggregate dispersion* ("sector explains a wide alpha range, N-gated") as the finding.
4. Practical, no-ML-needed CI: where a confirmatory claim hinges on a **rate** (wipeout %, % multibagger, % profitable-premium), show a **Wilson 95% CI** (closed-form, no libraries) so a 60%-vs-55% "difference" on N=40 is visibly not significant. See §6.

---

## 5. Benchmark-versioning — Nifty 50 vs Smallcap 250

**Verified:** there are **no `alpha_sc_*` columns** — Smallcap-250 alpha does not exist in the substrate. So the "fake alpha break at 2017" risk is **not live in Part A** (only Nifty-50 alpha is used). The real benchmark issues are different:

1. **Nifty-50 is the WRONG benchmark for micro/SME (HIGH for interpretation).** Benchmarking a microcap IPO against large-cap Nifty 50 **inflates alpha during small-cap bull runs** (most of the boom). This is exactly T7's point — but until Smallcap-250 alpha exists, **every micro/small/SME alpha number is benchmark-mismatched and likely overstated.** Fix: T7 must lead with a prominent caveat: "**all alpha is vs Nifty 50; for micro/small/SME this overstates alpha in small-cap bull regimes (most of 2020–25). Smallcap-250 alpha is pending (TODO). Treat micro/small/SME alpha as an upper bound.**" Add a per-finding benchmark chip on T1/T6/T8 for the micro/small/SME rows.
2. **Raw-vs-alpha side-by-side (T7).** Plan uses raw vs alpha for small/micro — good, but the only raw available is `return_from_issue_*` (also mixed-age if you use lifetime). Use the **maturity-gated horizon raw return** vs **horizon alpha**, same row set, so the comparison is apples-to-apples.
3. **Pre-Sep-2007 IPOs (LOW but verify).** Coverage map notes ~148 pre-Sep-2007 IPOs originally lacked Nifty-50 alpha (index history). Plan says "post-fix … note if substrate not yet refreshed." **Action:** T7 must print the count of rows with **null alpha but non-null return** per horizon; if pre-2007 alpha is still null, those longterm-MB rows silently drop from every alpha base rate → a **survivorship-flavored hole in the oldest cohort**. Verify and state.
4. **Benchmark policy statement (presentation).** The report header already says "alpha vs Nifty 50." Strengthen to: "alpha = vs **Nifty 50 only** (Smallcap-250 pending). No benchmark switching occurs, so there is no version break — but small/SME alpha is benchmark-mismatched (overstated)." This pre-empts the reader assuming alpha is small-cap-appropriate.
5. **Which segment should use which benchmark (forward note for Part B/integration):** MB-large/mid → Nifty 50 fine; MB-small/micro + all SME → should be Smallcap-250 (or a microcap index) once built. Record this as the benchmark-assignment rule so the integration pass wires it; Part A must not pretend it's already done.

---

## 6. Distribution / min-N reporting — is P10/median/P90 + N enough?

Mostly yes for shape, but **insufficient where the distribution is bimodal or the claim is a rate.**

1. **Fat-tailed / bimodal multibagger distributions (HIGH).** IPO alpha is not unimodal — it's a mass of mediocrity + a fat right tail (multibaggers) + a wipeout spike at −100%. P10/median/P90 **hides bimodality**: a segment with median ≈0 could be "everyone flat" OR "half wipeouts + half 5-baggers" — opposite decisions, same median. **Fix:** add `spine.distribution()` fields for **% ≥2x, % ≥5x, % ≤ −50%, % wipeout** alongside percentiles (the tails are the decision drivers, per the scorecard design). Add a **bimodality flag**: if (% in tails) > (mass near median), set `d["bimodal"]=True` and the finding renders "bimodal — median is misleading; see tail rates." A simple rule (e.g. P90−median ≫ median−P10, or dip in a coarse histogram) suffices, no libraries.
2. **Rates need CIs (HIGH for confirmatory claims).** wipeout %, % multibagger, % profitable-premium on N=20–60 cells have wide error. **Fix:** add `spine.wilson_ci(k, n)` (closed-form, no scipy) and render every **rate** as "p% [lo–hi], N=n." A confirmatory claim (§4) requires **non-overlapping CIs** (or a stated effect size), not just different point rates.
3. **Distribution percentiles need N gating in the chart too (MED).** A median bar at N=8 looks like one at N=800. Charts must annotate N on/under each bar and grey sub-floor bars (§Trap-2 fix).
4. **Show the histogram, not just percentiles, for the headline T1 alpha (MED).** The scorecard design (`layer3.md`) explicitly wants "render the histogram." Part A should embed an actual alpha histogram per segment (boom/longterm, MB/SME) so bimodality is visible to the eye, not just a flag.
5. **Mean is misleading and partly present (LOW).** `distribution()` returns `mean`; with −100% wipeouts and 10x tails the mean is dominated by tails. Keep mean only as a labeled secondary; lead with median + tail rates. Do not put mean in any chart.

---

## Prioritized "must-fix before trusting Part A"

**P0 — the analysis will actively lie without these:**
1. **T3 from-listing alpha does not exist** — do NOT bucket on listing pop and report issue-anchored alpha (mechanical double-count). Use raw `return_from_listing_*`, drop the word "alpha," label as gross secondary-buyer return. (§3.4, §1-trap-3)
2. **Long-horizon cohort-swap (C1)** — never draw a horizon curve that switches cohorts between points; 3y/5y/10y panels are longterm-only by default; boom long-horizon (5y N=69, 10y N=11) suppressed or tagged illustrative. (§2-C1, §1-trap-1)
3. **Boom-MB sector matrix (C2)** — boom-MB sector is 3% (~11 rows); T6 must suppress it entirely with a coverage note, not print an N=1–3 ranking. (§2-C2)
4. **Competing-risks unknowns (Trap-4)** — 155 of 195 delisted have no reason; T2 must render wipeout as a **lower/upper band** (unknown=not-wipeout vs unknown-loser=wipeout), with at-risk counts per matured year, and drop the naive "monotonic" test. (§1-trap-4, §3.5)
5. **Ban `current_return_from_issue` from base rates (age-mixing look-ahead)** — replace "% below issue / median current return" with maturity-gated horizon alpha. (§3.2, §1-trap-4)

**P1 — strongly biases interpretation:**
6. **Unbypassable min-N floor + auto-suppression in the assembler** (`guard_cells`), plus N-annotated, sub-floor-greyed charts — so no finding can print an N<10 number or bar. (§1-trap-2, §6.3)

**P2 — required for honest reading (do alongside):**
7. Within-vintage control (`by_listing_year`) for T1/T5/T9, and **T9 profitable-vs-loss stratified by cohort** (the profitable flag is boom-skewed → currently a vintage confound). (§1-trap-1, §2-C4/C6)
8. Tail rates + bimodality flag + Wilson CIs on all rates; confirmatory-vs-exploratory tagging with a pre-registered confirmatory box. (§4, §6.1–6.2)
9. Mcap "unknown" bucket always shown (never normalize over known-only); coverage line on every T5/T6/T9 table; reliability chip (RHP/official) on T9 and on SME upside. (§2-C3, §1-trap-3/5)
10. Benchmark caveat: all alpha vs Nifty 50; micro/small/SME alpha is overstated upper-bound until Smallcap-250 exists. (§5)
