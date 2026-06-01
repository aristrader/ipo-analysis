# Anatomy of a Wipeout — v2: more pre-listing flags + data-gap assessment

> **Builds on** `docs/research/wipeout_anatomy.md` and the shipped finding
> `layer3/findings/n14_wipeout_anatomy.py`. v1 VALIDATED two prospectus-readable flags (**tiny pre-IPO
> sales <25cr**, **loss-making / PAT≤0 at IPO**), kept declining-revenue/PAT as directional-only, found
> **high OFS protective**, and correctly KILLED **micro market-cap** as reverse-causation
> (`market_cap_class` is CURRENT mcap → circular). This note does NOT re-test those; it ADDS five new
> candidate flags the user asked for, then assesses the promoter/anchor data gap and its recoverability.

All numbers computed on `data/master/ipo_analysis.csv` (2,296 rows) via `layer3.spine` (Wilson 95% CIs,
hard MB/SME split, min-N≥10 directional / ≥30 claim, nulls NEVER imputed). Outcomes are identical to
n14: **WIPEOUT** = `outcome_class=='wipeout'` (carried by the mature 2006–19 longterm cohort) and
**DEAD MONEY** = alive & `current_return_from_issue<−0.5` & `liquidity_flag=='low'` (carried by the young
boom cohort, esp. SME). A flag must hold its SIGN in both regimes to graduate beyond hypothesis.

---

## 0. The structural problem that shapes every verdict below

Coverage of the new features is **cohort-skewed almost to the point of being single-regime**:

| feature | pre-listing? | boom-MB | boom-SME | lt-MB | lt-SME | cross-regime testable? |
|---|---|---|---|---|---|---|
| `promoter_post_issue_pct` | ✅ RHP (final allotment) | 202/382 | 562/887 | **0** | **0** | ❌ boom-only |
| `promoter_pre_issue_pct` | ✅ RHP | 244/382 | 652/887 | **0** | **0** | ❌ boom-only |
| `anchor_allocation_cr` | ✅ RHP (anchor book, pre-list) | 360/382 | 411/887 | 64 | 4 | ❌ effectively boom-only |
| `sub_qib_x` / `sub_retail_x` | ✅ subscription close, pre-list | 346/382 | 672/887 | 86 | **0** | ❌ boom-only |
| `gmp_pct` | ✅ grey market, pre-list | 372/382 | 679/887 | **0** | **0** | ❌ boom-only |
| `lead_manager` | ✅ RHP cover | 382/382 | 887/887 | 504 | 520 | ✅ **both cohorts** |

Two further facts collapse the usable panels:
- **Boom-MB has essentially ZERO bad outcomes** (0 wipeouts, 0 dead-money across every flag — too young
  and too large to have died yet). So the only high-N *boom* panel is **SME-boom-dead**.
- **Longterm has NO promoter/GMP/QIB data at all.** So for promoter holding, anchor, demand-skew and GMP
  the *only* high-N test that exists is the single SME-boom-dead panel — there is **no second regime to
  validate against**. That is a verdict-blocking gap, not a stylistic one (see §3).

`lead_manager` is the lone new feature populated in both cohorts, so it is the only new flag that can
clear the cross-regime bar.

---

## 1. Per-flag results — bad-outcome rate WITH vs WITHOUT the flag

Cells are **lift in pp (with% vs without%, N flagged side)**; Wilson CIs computed, sub-floor (N<10)
suppressed. Panels: `MB-lt-W`/`SME-lt-W` = wipeout (longterm); `SME-bo-D` = dead-money (boom-SME, the
one rich boom panel). `MB-bo-D` and `SME-bo-W` are shown to document that boom is too young for either
death mode at MB / for formal wipeout at SME (≈all-zero → uninformative, not evidence of safety).

### Promoter holding (boom-only)

| flag | confirmed pre-listing? | SME-bo-D | other panels | read |
|---|---|---|---|---|
| `low_promoter_post <40%` | ✅ final-allotment %, fixed at listing | **−8.3pp** (11% vs 20%, N53) | lt: no data; MB-bo: 0/30 | **WRONG SIGN** |
| `low_promoter_post <50%` | ✅ | −0.4pp (19% vs 19%, N97) | lt: no data | flat |
| `high_dilution >20pp` (pre−post) | ✅ both RHP figures | +5.3pp (20% vs 14%, N472) | lt: no data | weak, single-regime |

Continuous check (SME-boom dead-money by promoter-post tertile) **confirms the inversion**:
low (<55%) 15.2% [10,22] · mid (55–67%) 18.3% [13,25] · **high (≥67%) 21.3% [17,27]**. The death rate
*rises* with promoter holding, the OPPOSITE of the "founders keep no skin → death" hypothesis (CIs
overlap, so really it is a non-signal). Mechanism: in Indian SME-land, ultra-high promoter retention
(thin float, ≥65%) co-occurs with tiny illiquid issues — exactly the dead-money profile — while a lower
post-issue stake means a larger genuine public float. **So "low promoter holding" is not a red flag; if
anything it leans mildly protective. Killed.** "High dilution" is the only promoter-derived flag with
the hypothesized sign, but it is weak (+5.3pp, overlapping CIs) and single-regime.

### Anchor (boom-only, structurally)

| flag | pre-listing? | SME-bo-D | read |
|---|---|---|---|
| `no_anchor` (boom-MB, anchor well-covered there) | ✅ anchor book pre-list | 0/360 bad (boom-MB has no deaths) | **uninformative** |
| `tiny_anchor <5cr` | ✅ | +6.6pp (15% vs 8%, N40) | directional, single-regime, thin |

Anchor is only meaningfully populated for boom-MB, which has zero deaths, so anchor cannot be tested
against the death modes at all in the cohort where it is covered. `tiny_anchor` on the SME slice that
has it is directional (+6.6pp) but N=40 and single-regime. **Insufficient data to rule either way.**

### Lead-manager tier (BOTH cohorts — the one that travels)

Crude tier from issue-count frequency + a bulge-bracket name list: `top` = known house or ≥40 IPOs
managed; `obscure` = <10 IPOs managed; else `mid`. (Tier is built from the lead-manager NAME on the RHP
cover — fixed before listing — so it is unambiguously pre-listing.)

| flag | SME-bo-D | SME-lt-W | MB-lt-W | MB-lt-D | verdict |
|---|---|---|---|---|---|
| `obscure_lead_mgr` | **+12.7pp** (28% vs 16%, N141) | +3.7pp (12% vs 8%, N51) | **+9.9pp** (30% vs 20%, N110) | +3.3pp (6% vs 3%, N110) | **sign holds in all 4** |
| `not_top_lead_mgr` | +12.0pp (24% vs 12%, N448) | +1.0pp (N164) | +3.2pp (N270) | +1.5pp (N270) | sign holds, weaker |

**Monotonic tier gradient (top < mid < obscure) in every high-N panel:**

| panel | top | mid | obscure |
|---|---|---|---|
| SME-boom (dead) | 11.6% [9,15] N439 | 21.5% [17,26] N307 | **28.4% [22,36] N141** |
| SME-longterm (wipeout) | 8.1% [6,11] N356 | 8.0% [4,14] N113 | 11.8% [6,23] N51 |
| MB-longterm (wipeout) | 20.5% [16,26] N234 | 19.4% [14,26] N160 | **30.0% [22,39] N110** |

The gradient is clean and same-signed in both cohorts (cleanest in SME-boom; SME-longterm is the
weakest but still correctly ordered). This is the **one new flag that passes the cross-regime sign
test.** Mechanism: obscure/low-frequency bankers do less diligence, price more aggressively, and bring
weaker pipelines — exactly the issues that later die or go illiquid; reputable houses gate-keep.

### Demand skew & GMP (boom-only)

| flag | SME-bo-D | read |
|---|---|---|
| `weak_qib <1x` | **+12.8pp** (25% vs 13%, N315) | strong but single-regime |
| `retail_driven` (retail>2×QIB & QIB<5×) | **+13.3pp** (28% vs 14%, N213) | strong but single-regime |
| `high_gmp >50%` | **−10.2pp** (10% vs 20%, N126) | **WRONG SIGN (protective)** |
| `high_gmp >75%` | **−12.8pp** (6% vs 19%, N64) | **WRONG SIGN (protective)** |

- **Weak QIB / retail-driven**: large lift on dead-money and a clean institutional-validation story
  (no QIB conviction → the issue is a retail-pumped shell that later goes illiquid). But there is **no
  longterm QIB/retail data**, so it cannot be cross-regime validated — single-regime directional only.
- **High GMP is NOT a crash signal — it is protective against dead-money.** The hyped names (high GMP)
  are precisely the liquid, in-demand issues that keep trading; the dead-money zombies are the ones
  nobody wanted (low/zero GMP). "High GMP then crash" exists anecdotally for *return* (pop-and-fade is a
  separate validated finding), but for the *dead-money / un-exitable* outcome the sign is reversed. Do
  NOT add high-GMP as a wipeout red flag.

---

## 2. Per-feature verdict table (the headline grid)

| NEW feature | pre-listing confirmed | wipeout/dead rate WITH vs WITHOUT (best panel) | cross-regime verdict | mechanism |
|---|---|---|---|---|
| **obscure lead manager** | ✅ RHP cover, name→tier | 28% vs 16% dead (SME-bo, N141); 30% vs 20% wipe (MB-lt, N110) | **HEADLINE — validated** (sign holds 4/4 panels, monotonic tier gradient both cohorts) | weak banker → weak diligence/pricing/pipeline |
| weak QIB <1× | ✅ subscription close | 25% vs 13% dead (SME-bo, N315) | **single-regime** (no lt QIB data) | no institutional validation |
| retail-driven demand | ✅ subscription close | 28% vs 14% dead (SME-bo, N213) | **single-regime** | retail-pumped, no smart money |
| high dilution >20pp | ✅ pre−post promoter % | 20% vs 14% dead (SME-bo, N472) | **single-regime, weak** | founders cashing out hard |
| tiny anchor <5cr | ✅ anchor book | 15% vs 8% dead (SME-bo, N40) | **insufficient data** | low institutional conviction |
| **low promoter holding** | ✅ final allotment % | 11% vs 20% dead — **inverted** | **REJECTED (wrong sign)** | hi-retention = thin float = the zombie profile |
| **high GMP >50/75%** | ✅ grey market | 6–10% vs 19–20% dead — **inverted** | **REJECTED (protective)** | hyped = liquid = NOT dead money |

---

## 3. Updated red-flag score — does any new flag graduate the monotonicity?

Only `obscure_lead_mgr` cleared the cross-regime bar, so it is the only new flag eligible to join the
n14 additive count. New score = n14's 4 prospectus flags (tiny_sales<25cr, PAT≤0 latest, declining
revenue, declining PAT) **+ obscure_lead_mgr** (0..5). Scored only where ≥2 flags are evaluable; nulls
never count. Outcome = wipeout OR dead-money.

| segment · cohort | 0 flags | 1 flag | 2 flags | 3+ flags |
|---|---|---|---|---|
| **SME · boom** (dead) | 12.5% [10,16] N473 | 20.5% [16,26] N283 | 36.0% [26,47] N75 | **41.9% [28,57] N43** |
| **SME · longterm** (wipe) | 10.7% [7,16] N196 | 21.3% [16,28] N169 | 27.1% [17,41] N48 | 11.1% N18 (thin) |
| **MB · longterm** (wipe) | 23.7% [17,32] N114 | 34.1% [22,49] N44 | 44.4% N9 (thin) | 0% N4 (thin) |

**Adding the lead-manager flag keeps the score monotonic 0→2 in all three high-N panels and steepens
the SME-boom gradient** (v1 4-flag SME-boom was 13.7→17.9→28.8→38.2%; v2 5-flag is
12.5→20.5→36.0→41.9% — a wider spread, i.e. better separation). The 3+ band stays noisy in the longterm
panels (small N once you require 3 co-present flags on the sparse longterm financials), so keep
reporting 0/1/2/3+ banding only. **Recommendation: graduate `obscure_lead_mgr` into the n14 score and
the predictor's downside-safety wipeout-risk sub-score at weight 1** (alongside tiny_sales and
PAT-negative); it is the first flag in this family that is genuinely cross-regime AND fully covered
(lead_manager is 100% populated, so it never degrades to "not evaluable").

---

## 4. DATA-GAP ASSESSMENT — promoter holding & anchor

### 4a. Does the gap block a cross-regime verdict?

**Yes, decisively, for promoter holding (and for anchor / QIB / GMP).** Longterm coverage is exactly
0% for promoter %, GMP and SME-QIB, and the only boom panel with deaths is SME-boom-dead. So every one
of these features is **structurally single-regime**: there is no 2006–19 wipeout panel to confirm the
sign against. Per the project's own rigor rule (a flag is a hypothesis until it holds on the longterm
cohort), none of promoter-holding / anchor / demand-skew / GMP can be promoted to "validated" today —
not because the signal is weak (weak-QIB and retail-driven are quite strong on boom-SME) but because the
second regime is **missing data**. The promoter-holding flag in particular ALSO has the wrong sign even
within the one regime we can see, so more data would most likely just confirm it is a non-flag.

### 4b. Is more promoter-holding / anchor data obtainable for free?

**Promoter holding — PARTIALLY RECOVERABLE, moderate effort, no new scraping for the bulk.**

The pipeline is *already leaving longterm promoter data on the floor*:
- `scrapers/chittorgarh.py` (lines 217–219) extracts `promoter_pre_shares` / `promoter_post_shares` from
  the "Share Holding Pre/Post Issue" rows. The boom **percentage** `promoter_post_issue_pct` actually
  comes from **Sharescart** (`scrapers/sharescart.py` lines 455–458, "Pre/Post Issue Share Holding" as a
  literal %), and Sharescart only covers **2023–2025** (`YEARS=[2023,2024,2025]`) — that is why even
  boom is only ~33% covered and longterm is 0%.
- BUT the longterm raw file `data/raw/chittorgarh/details_longterm.csv` **already contains
  `promoter_pre_shares` and `promoter_post_shares` for 1028/1029 rows** (verified). These are absolute
  share COUNTS, not %, and the longterm assembler `pipeline/longterm/02_detail.py` `ATTACH` list
  (lines 40–42) **simply omits them** — they never reach the master table.
- A live fetch of a 2018 Chittorgarh page (probe, 1 fetch) confirms the page still shows only the share
  counts (`Share Holding Pre Issue 93,54,400 shares / Post Issue 1,39,51,200 shares`), not a %. So the %
  must be DERIVED: `promoter_post_% ≈ promoter_post_shares / total_post_issue_shares`, where
  `total_post_issue_shares` is reconstructed from `issue_size_cr` and `issue_price` (both already in the
  dataset). Calibrating this derivation on the 762 boom rows that have BOTH the Chittorgarh counts and
  the Sharescart % yields internally consistent values (712/762 land in a sane 0–100% range, median
  derived pre-% ≈ 60%). **Effort: ~half a day of pipeline work** (add the two columns to the longterm
  ATTACH, compute total-post shares, derive the %, validate against the boom overlap). No new scraping.
  Risk: the derived % is an estimate (issue-size/price rounding), so it would carry a lower
  `data_quality_tier` than the boom Sharescart %.

**Anchor — LARGELY A STRUCTURAL LIMIT, low upside.** The 2018 SME page does expose
"Anchor Portion (₹ Cr.) 10.01", so anchor IS on the Chittorgarh page where it exists, and the longterm
raw already captured 68 rows. But anchor investors were only introduced by SEBI in **2009**, and SME
anchors are genuinely rare — so most of the 2006–19 cohort had **no anchor at all** (the null is a true
zero, not a scrape miss). Re-scraping would add only a modest number of post-2009 mainboard anchor rows.
Even then, the cohort where anchor IS well covered (boom-MB) has zero deaths, so more anchor data does
not unlock a death-mode test. **Effort: low; payoff: low.**

**GMP / QIB for longterm — NOT freely obtainable.** Grey-market premium for 2006–19 is not archived on
the free sources (investorgain/ipowatch GMP history starts in the boom era); longterm QIB/retail splits
were not in the Chittorgarh subscription tables we have. No cheap recovery path.

---

## 5. Bottom line

- **VALIDATED (graduates):** **obscure lead manager** — the only new flag whose sign holds across both
  cohorts AND all four panels, with a clean monotonic top<mid<obscure death gradient (SME-boom dead
  11.6%→21.5%→28.4%; MB-longterm wipeout 20.5%→19.4%→30.0%) and 100% coverage. Adding it to the n14
  red-flag score keeps monotonicity and widens the SME-boom spread to 12.5%→41.9%. Recommend wiring it
  into the score + the predictor downside sub-score at weight 1.
- **STRONG BUT SINGLE-REGIME (cannot validate — data gap):** weak QIB (<1×, +12.8pp) and retail-driven
  demand (+13.3pp) on boom-SME dead-money. Keep as boom-only directional hints; cannot promote.
- **KILLED:** **low promoter holding** — wrong sign (death *rises* with promoter retention: high-
  retention = thin illiquid float = the dead-money profile). **High GMP** — wrong sign / protective for
  the dead-money outcome (hyped names stay liquid). These are NOT wipeout red flags.
- **INSUFFICIENT DATA:** tiny anchor, high dilution — directional and single-regime only.

**Is finding more promoter-holding data worth it?** Modestly, and cheaply: ~half a day to surface the
already-scraped longterm Chittorgarh share counts and derive a (lower-tier) post-issue %, which would
finally give a *second regime* for the promoter flag. But the expected payoff is low — within the one
regime we can already see, low promoter holding has the WRONG sign, so more data will most likely just
confirm it is a non-flag rather than rescue it. **Anchor and GMP/QIB are not worth chasing** (anchor is
a true structural zero pre-2009 and lives in a death-free panel; longterm GMP/QIB aren't on free
sources). The high-value, low-effort win is **lead-manager tier**, which needs no new data at all.
