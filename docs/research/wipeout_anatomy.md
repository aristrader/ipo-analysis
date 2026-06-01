# Anatomy of a Wipeout — pre-listing red flags behind IPO death

> **⚠ CORRECTION (post-review, 2026-06-01).** The original draft named **micro market-cap** the #1
> wipeout predictor (+52pp). That is **REVERSE-CAUSATION and has been removed** from the red-flag score
> and any predictor gauge: `market_cap_class` is the company's *current* market cap, so a wiped-out
> name reads "micro" *because it crashed* (median current mcap of a wipeout = ₹9cr vs ₹770–1200cr for
> survivors; 95% of wipeouts read "micro"). It is not prospectus-readable. The VALIDATED pre-listing
> flags are **tiny pre-IPO sales** and **loss-making at IPO** (declining revenue/PAT directional-only).
> The shipped finding (`n14_wipeout_anatomy.py`) reflects this correction; treat the micro-cap rows
> below as a cautionary example only.

**Question.** Do the Indian IPOs that get **wiped out** or turn into **dead money** share PRE-LISTING
patterns we could have read straight off the prospectus? This note tests RHP-only features (no
post-listing price — no look-ahead) against two bad-outcome definitions, finds the patterns that
survive a cross-regime test, and specs a finding module + a predictor "wipeout-risk" gauge.

Engine: `layer3/findings/n14_wipeout_anatomy.py` (registered in `run_layer3_report.py`). All numbers
below are computed on `data/master/ipo_analysis.csv` (equity only, 2,245 rows) via the method spine.

---

## 1. The two bad outcomes (reported together by design)

| outcome | definition | count | where it lives |
|---|---|---|---|
| **WIPEOUT** | `outcome_class == 'wipeout'` (≈−100% / compulsory delist) | 162 | almost entirely **longterm** (107 MB-lt, 44 SME-lt; boom has 1 MB + 10 SME) |
| **DEAD MONEY** | alive & `current_return_from_issue < −0.50` & `liquidity_flag=='low'` (un-exitable zombie) | 243 | mostly **boom-SME** (157), then SME-lt 66, MB-lt 20 |

SURVIVED = `outcome_class ∈ {winner, multibagger, flat}` (1,356 rows).

**Why both.** Formal wipeout needs *years* — the boom (2020–25) cohort is too young, so its true
death rate is a survivorship UNDER-count. Dead money captures the boom cohort's zombies *before*
delisting can register. So the cross-regime test is: **wipeout carried by the longterm cohort,
dead-money carried by the boom cohort** — a flag must point the same way in both to graduate.

Method spine (non-negotiable): hard MB/SME split; min-N floors (N≥30 claim / N≥10 hint, sub-floor
suppressed); proportions with Wilson 95% CIs; financials coverage gaps reported per flag and NEVER
imputed (a null flag never counts as a red flag). Coverage is boom-skewed: MB-longterm has all-3-year
sales for only ~21% of rows, vs ~86–89% in boom.

---

## 2. Per-pattern results — wipeout/dead-money rate WITH vs WITHOUT the flag

Four panels: `MB-lt-W` / `SME-lt-W` = wipeout rate (longterm); `SME-bo-D` / `MB-lt-D` = dead-money
rate. Each cell = **lift in pp (with% vs without%, N on flagged side)**. `N=…` alone = sub-floor,
suppressed. The two high-N validation panels are **SME-lt-W** and **SME-bo-D**.

| red flag (pre-listing) | MB-lt Wipeout | SME-lt Wipeout | SME-boom Dead | MB-lt Dead | verdict |
|---|---|---|---|---|---|
| **micro market-cap** | **+51.9** (54v2, N114) | **+9.1** (9v0, N329) | **+18.3** (18v0, N224) | **+13.5** (14v0, N114) | **HEADLINE** |
| **tiny sales <25cr** | N=7 | **+7.8** (12v4, N181) | **+4.5** (21v17, N217) | N=7 | **VALIDATED** |
| tiny sales <10cr | N=5 | +11.2 (16v5, N91) | +3.0 (21v18, N73) | N=5 | VALIDATED |
| **PAT≤0 latest yr** | +4.8 (31v26, N13) | **+8.5** (15v7, N46) | **+28.5** (45v16, N40) | +7.7 (8v0, N13) | **VALIDATED** |
| loss-making at IPO (`pre_ipo_pat≤0`) | +4.8 (N13) | +8.5 (15v7, N46) | −3.2 (15v18, N27) | +7.7 (N13) | mixed |
| declining revenue (yr3<yr1) | N=5 | −1.6 (7v9, N28) | **+19.4** (36v17, N77) | N=5 | mixed (dead-money only) |
| declining PAT (yr3<yr1) | +4.3 (N13) | −10.3 (0v10, N29) | **+15.6** (33v17, N92) | +7.7 (N13) | mixed (dead-money only) |
| high debt/equity >2 | +18.3 (38v20, N13) | −0.8 (7v8, N58) | −0.3 (17v17, N41) | +7.7 (N13) | **NOT robust** |
| thin PAT margin <3% | −1.3 (25v26, N32) | +2.1 (9v7, N192) | +1.4 (19v18, N180) | +3.1 (N32) | flat |
| micro issue <15cr | N=4 | −0.4 (8v9, N366) | +0.5 (18v18, N259) | N=4 | flat |
| accrual (PAT>0, op-profit≤0) | N=5 | +1.4 (N11) | N=7 | N=5 | too thin |
| expensive vs sector PE | N=0 | N=0 | +12.5 (12v0, N32) | N=0 | too thin |
| **high OFS >50%** | **−26.2** (2v28, N98) | +1.3 (N42) | **−12.8** (5v18, N19) | **−5.4** (0v5, N98) | **REVERSE (protective)** |

Reading notes:
- **micro market-cap** is the single dominant death signal and the only one positive in **all four**
  panels — including the huge MB-longterm wipeout jump (2% → 54%).
- **tiny sales** and **PAT≤0 latest** hold their sign in both the SME-lt-wipeout and SME-boom-dead
  high-N panels → validated.
- **declining revenue / declining PAT** are strong on **dead money** (SME-boom +19.4 / +15.6pp) but
  **flip negative** on SME-longterm wipeout (small-N flagged side: 28/29). So they are *directional
  dead-money* signals, not confirmed wipeout signals — kept in the score with that caveat.
- **high debt/equity** only shows up in the tiny MB-longterm flagged cell (N=13); flat/negative on
  the high-N SME panels → **NOT robust** despite the "leverage kills" prior.
- **high OFS is PROTECTIVE**, not a red flag: OFS-heavy issues are *established* companies (founders
  cashing out a real business), so OFS must never enter a wipeout gauge with a positive sign.
- **Sector** over-indexing is inconsistent across cohorts (Healthcare/Consumer-Discretionary top in
  SME-boom; FMCG/Consumer-Disc top in MB-longterm; Financial Services lowest in both) → too noisy
  for a standalone flag; subsumed by scale/profitability.

---

## 3. The additive RED-FLAG SCORE (transparent count, NO ML)

Score = count (0..5) of: **micro market-cap · tiny sales <25cr · PAT≤0 latest · declining revenue
· declining PAT**. Scored only where ≥3 of the 5 flags are *evaluable*; a null flag never counts.
Outcome = **bad outcome (wipeout OR dead money)**.

| segment · cohort | 0 flags | 1 flag | 2 flags | 3+ flags |
|---|---|---|---|---|
| **SME · boom** (dead-money regime) | 13.7% [11,17] N402 | 17.9% [13,23] N224 | 28.8% [21,38] N118 | **38.2% [27,51] N55** |
| **SME · longterm** | 2.6% [1,9] N78 | 16.7% [12,23] N156 | 21.6% [16,29] N134 | **25.6% [15,41] N39** |
| **MB · longterm** (micro_mcap-driven) | 8.5% [4,17] N71 | 60.0% [45,74] N40 | 50.0% N6 | 40.0% N5 |

**More flags ⇒ more death, monotonically up to 3, in every segment.** SME (both cohorts) shows a
clean 0→1→2→3+ gradient. MB-longterm is dominated by the single micro_mcap flag (one flag already
takes the rate from 8.5% to 60%), so its higher bands are thin. The 4–5 flag buckets are too small
(N≤11) and noisy — report 0/1/2/3+ banding only.

---

## 4. BUILD-SPEC

**(1) Finding module — `layer3/findings/n14_wipeout_anatomy.py`** (built, registered).
`build_flags(df)` → 13 RHP-only float flags (NaN = not evaluable, never imputed). `bad_outcomes(df)`
→ the wipeout + dead-money masks. `compute(df)` returns a `Finding` with: (a) the per-flag lift table
across the 4 MB/SME×cohort×outcome panels with Wilson CIs and N-available; (b) the additive
red-flag-score table (0/1/2/3+ → bad-outcome rate per segment); (c) a bar chart of the SME-boom
monotonic gradient. Sign-must-hold-across-cohorts is enforced in the caveats; sub-floor cells show N
only. Wire into `FINDINGS` after n13 (done) and add a `tests/layer3/test_n14.py` asserting: micro_mcap
lift > 0 in all four panels, the SME score gradient is monotonic 0→3+, and OFS lift < 0 (reverse).

**(2) Predictor "wipeout-risk" gauge — downside-safety component.** Add a transparent additive
`wipeout_risk` sub-score to `layer3/predictor/` (downside-safety component), using **only the
cross-regime-validated flags** with these point-in-time-safe weights: micro_mcap **= 2** (dominant,
positive in all 4 panels), tiny_sales_lt25cr **= 1**, pat_negative_latest **= 1**. Declining-revenue
and declining-PAT enter at **weight 0.5 each** and flagged *dead-money-directional only* (not used for
formal-wipeout claims). Debt/equity, thin-margin, OFS, sector, valuation → **weight 0**
(not-robust / reverse). Map the weighted count to a downside band (e.g. ≤1 = low, 2–3 = elevated,
>3 = high wipeout-risk), and surface the analog comps' realized bad-outcome rate at that score. Gauge
must be MB/SME-aware (use the SME gradient for SME, the micro_mcap-led one for MB) and degrade
gracefully when financials are missing (report `flags_evaluable`, never impute).

---

## 5. Headline verdicts

- **VALIDATED (sign holds across regimes & outcomes):** micro market-cap (strongest), tiny pre-IPO
  sales (<25cr / <10cr), loss-making at IPO (PAT≤0 latest year).
- **Directional only (dead-money, not confirmed on wipeout):** declining revenue, declining PAT.
- **NOT robust:** high debt/equity (only the tiny MB-longterm cell), thin margin, micro issue size,
  accrual, expensive-vs-sector, sector identity.
- **REVERSE (protective — do not use as a red flag):** high OFS (>50%).
