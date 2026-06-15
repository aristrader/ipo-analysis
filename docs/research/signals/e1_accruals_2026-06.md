# E1 — Pre-IPO accruals (earnings-quality) signal (2026-06-09)

Harness: `tools/research/e1_accruals.py` · review CSVs: `data/master/review/e1_accruals_review.csv`,
`e1_accruals_summary.csv` · cohort/segment, point-in-time, survivorship-honest, no scipy.

## 0. Data question resolved FIRST (don't re-run the gated thing)
Prior verdict (Thread-C, 2026-06-08): **"accruals (Modified-Jones DCA): DATA-GATED — needs receivables + CFO."**
That stands — confirmed there is **NO receivables / debtors column** in the substrate (only `pat_yr*`,
`operating_cf_yr*`, `total_assets_yr*`, `net_sales_yr*`, `operating_profit_yr*`). So full Modified-Jones
discretionary accruals remains uncomputable.

**What IS computable — and what E1 actually tested — is the TOTAL-ACCRUALS proxy:**

    TA = (PAT − operating CFO) / average total assets        (latest pre-IPO FY)

High TA = a large share of reported profit is NOT backed by operating cash = lower earnings quality.
This is the **graded** version of the proven binary **n8 flag** ("PAT>0 but CFO≤0"). E1's purpose: does the
graded measure add anything robust over the binary flag + existing N14 flags?

**Year semantics:** `yr3` is the LATEST pre-IPO FY (`pre_ipo_pat` matches `pat_yr3` in 1590/1920 rows) and has
the best coverage. Avg assets = (`total_assets_yr2`+`total_assets_yr3`)/2, fallback ending `yr3`; guarded against
≤0 (negative-equity / div-by-zero).

**Coverage (the honest limit):** TA proxy valid on **72.2% overall**, but very uneven by cell — MB-longterm only
**141/459 = 31%**, SME-longterm 318/518 = 61%. The longterm cells (the ones that matter for the cross-regime gate)
are the thinnest. No look-ahead: TA is pre-IPO financials only; forward alpha is maturity-gated; placebo shuffles
labels within cell.

## 1. Method
Within each cohort×segment cell, tertile TA (Q1 = lowest accruals / highest quality → Q3 = highest accruals).
Per tertile: forward **alpha vs Nifty** (1y/3y, maturity-gated) + **bad-outcome rate** = confirmed-wipeout-class OR
dead-money (alive, ≤−50% from issue, illiquid — the n9-zombie definition), with Wilson CI. Spread = Q3 − Q1.
Thesis-consistent = alpha-spread **< 0**, bad-rate-spread **> 0**. Placebo = 1000× within-cell label shuffle on the
bad-rate spread. Incremental test: within n8-CLEAN names, does the top accrual tertile still show worse outcomes?

## 2. Results (Q3 high-accrual − Q1 low-accrual)

| cell | N_valid | med_α1y Q1→Q3 | spread_α3y | bad-rate Q1→Q3 | spread_bad | placebo p | rank-IC(acc,α3y) | incr vs n8-clean |
|---|---|---|---|---|---|---|---|---|
| MB-boom | 362 | −10.3%→−11.2% | **−0.579** | 0.0%→0.0% | **0.000** | 1.00 | −0.146 | 0.000 |
| SME-boom | 850 | −14.7%→−6.3% | −0.118 | 11.6%→9.5% | **−0.021** (wrong sign) | 0.44 | +0.016 | −0.021 |
| MB-longterm | 141 | −5.1%→−18.1% | −0.259 | 12.8%→29.8% | **+0.170** | 0.045 | −0.100 | +0.111 |
| SME-longterm | 318 | −8.9%→−9.6% | −0.045 | 14.2%→26.4% | **+0.123** | 0.029 | −0.008 | +0.079 |

(Per-tertile N, Wilson CIs and k/n in the review CSV.)

## 3. Reading it
- **Bad-outcome (the headline use, validated definition):** the signal works in the **longterm cohort only**
  (MB +17pp, SME +12pp, both placebo-clean p≈0.03–0.05) and is **NULL or INVERTED in boom** (MB-boom has literally
  zero bad outcomes so it can't discriminate; SME-boom high-accrual was slightly *safer*, placebo p=0.44 = noise).
  That is a textbook **regime-dependent, not cross-regime-robust** signal → fails the cross-regime gate.
- **3y alpha spread** is negative in 3/4 cells (directionally thesis-consistent), but the dramatic MB-boom −58pp is
  one volatile high-accrual tertile, and rank-IC is essentially zero in 3/4 cells (only MB-boom −0.15). No
  monotone, sign-stable alpha gradient.
- **Incremental over n8:** within n8-clean names, the graded measure adds discrimination only in longterm
  (MB +11pp, SME +8pp); **nothing in boom**. So it does not *robustly* upgrade the binary flag — same regime story.
- **Placebo:** the two longterm bad-rate effects survive their shuffle (p=0.029 / 0.045, null mean ≈0). The boom
  effects do not exist / are noise. The placebo is doing its job — it confirms the longterm effect is real and the
  boom non-effect is genuinely absent (not just hidden).

## 4. Verdict — **DISPLAY-ONLY (longterm-leaning, not cross-regime)**

Upgraded from the prior **DATA-GATED** parking: the *total-accruals proxy* is computable and IS a real
earnings-quality red flag — **but only in the long-term (2006–19) cohort**, and it vanishes/inverts in the boom.
It therefore **fails the cross-regime gate** and the "evolve-only-if-robust" score policy (would not survive an OOS
fold either — boom is null). It does not robustly improve over the already-proven binary n8 flag.

**NOT in score.** Keep as a **display-only earnings-quality read**, complementary to the binary n8 flag: "in the
longer-horizon regime, high pre-IPO accruals (profit not backed by cash) carried ~+12–17pp more wipeout/dead-money;
absent in the boom." Modified-Jones DCA stays formally data-gated (needs receivables). Caveat the thin MB-longterm
coverage (31%) on any display.

Numbers I'm least sure of: MB-longterm rests on 141 TA-valid rows (47/tertile) — the +17pp bad-rate spread is real
but thin (Wilson CIs overlap somewhat: Q1 [6,25]% vs Q3 [19,44]%). The MB-boom −58pp 3y alpha spread is one
fragile tertile, not a stable gradient — do not quote it as a "high accruals lose 58%" headline.
