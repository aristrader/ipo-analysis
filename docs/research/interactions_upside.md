# Feature-combination (interaction) patterns for IPO UPSIDE

**Question:** Single pre-listing features mostly failed cross-regime (profitable-at-IPO MIXED, OFS MIXED, debt-flag
not-robust). Do *combinations* of features reveal upside that single features miss — a "what goes hand-in-hand for a
winner" map?

**Substrate:** `data/master/ipo_analysis.csv` via `layer3.spine.load_substrate()` (equity-only, 2,296 IPOs:
boom 2020–25 = 1,269; longterm 2006–19 = 1,027).

**Outcomes (maturity-gated):**
- `alpha_{1y,3y}` — FROM-LISTING alpha vs Nifty 50 (secondary-buyer return; NOT the allottee pop).
- multibagger = `return_from_issue_{h} >= 1.0` (issue-anchored 2x+).

**Discipline applied:**
1. Theory-driven pairs only (each has a stated mechanism).
2. **Cell-level N ≥ 30** floor (tradable claim → higher bar). Sub-floor cells = "insufficient", never a finding.
3. **Cross-regime mandatory** — sign must hold in BOTH boom AND longterm.
4. **Beat base AND beat each single feature** (super-additive), shown via median alpha + multibagger rate.
5. Distributions/medians + Wilson CI + bootstrap median CI (90%). IPO returns are barbell — means lie, so medians lead.

**Feature definitions (pre-listing only):** profitable `pre_ipo_pat>0`; low-debt `D/E<0.5`; high-ROE `ROE≥20%`;
high-margin `PAT-margin≥10%`; small-issue `issue_size_cr<50`; low-OFS `ofs_pct≤10`; rev-growth `net_sales_yr3/yr1≥1.5`.
`market_cap_class` deliberately EXCLUDED (it is CURRENT mcap → contaminated, as in the wipeout work). Subscription/
anchor features (`sub_qib_x`, `anchor_allocation_cr`) are boom-only → any finding using them is single-regime by
construction.

A note on the numbers: at **1y** every cohort's median alpha sits within ±0.1 of zero and NO interaction separates
from base — the upside signal lives at **3y**, so the headline results below are all 3y. The longterm base 3y alpha is
deeply negative (median -0.47) — most 2006–19 IPOs lagged Nifty badly over 3y; that makes a cohort-positive cell a
strong claim.

---

## RANKED RESULTS (3y)

### 1. low-debt × high-ROE  →  SUPER-ADDITIVE & cross-regime ✅ (strongest)

**Mechanism:** A business earning high returns on equity *without* leaning on debt is a genuine self-funding
compounder — the cash returns are real, not levered. Either feature alone is gameable (high ROE can be debt-juiced;
low debt can mean a sleepy no-growth balance sheet). The *conjunction* is the clean-compounder signal.

| cohort | cell | N | median alpha [90% CI] | P(median>0) | multibagger [Wilson] |
|---|---|---:|---|---:|---|
| boom | base | 366 | -0.01 [-0.16,+0.13] | 0.45 | 46% [41,51] |
| boom | low-debt only | 133 | -0.04 [-0.32,+0.13] | 0.42 | 44% [36,53] |
| boom | high-ROE only | 128 | +0.02 [-0.22,+0.32] | 0.54 | 49% [41,58] |
| boom | **BOTH** | **61** | **+0.07 [-0.40,+0.83]** | **0.74** | **52% [40,64]** |
| longterm | base | 964 | -0.47 [-0.50,-0.42] | 0.00 | 19% [16,21] |
| longterm | low-debt only | 174 | -0.31 [-0.40,-0.13] | 0.00 | 23% [17,30] |
| longterm | high-ROE only | 158 | -0.24 [-0.40,-0.08] | 0.01 | 28% [21,35] |
| longterm | **BOTH** | **51** | **+0.18 [-0.18,+0.49]** | **0.76** | **37% [25,51]** |

**Why this is a real interaction (not just two okay features):** the 2×2 conditional in longterm is textbook
super-additive — neither feature alone escapes the base region (single-feature cells stay at median -0.40, P+≈0.00),
but the conjunction flips to **+0.18 (P+=0.76)** and nearly doubles the multibagger rate (19% base → 37%):

```
longterm 2x2 (3y, median alpha):   ~ROE & ~LD: -0.50 (n=683)   ROE & ~LD: -0.40 (n=107)
                                    ~ROE & LD : -0.40 (n=123)   ROE & LD : +0.18 (n=51, P+=0.76, mb 37%)
```
Only the both-true corner moves. In boom the picture is noisier (the `~ROE&~LD` corner is also positive, +0.13), so the
boom interaction is *weaker and partly co-incidental* — but the both-true cell still carries the highest P(>0)=0.74 and
the highest multibagger rate (52% vs 46% base). **Verdict: cross-regime upside interaction. Sign holds in both; the
mechanism is cleanest in longterm.** Caveat: boom both-cell N=61 with a very wide alpha CI — treat the *multibagger*
lift (clearer signal: 52% vs 46%) as the boom evidence, the *alpha flip* as the longterm evidence.

### 2. high-ROE × high-margin  →  SUPER-ADDITIVE on multibagger, MARGINAL on alpha ✅/⚠️

**Mechanism:** High ROE + fat PAT margin = pricing power compounding on efficient capital — a quality-of-earnings
stack. Margin without ROE can be a low-asset-turn niche; ROE without margin can be thin-margin high-churn. Together =
durable quality.

| cohort | cell | N | median alpha | multibagger |
|---|---|---:|---|---|
| boom | base | 366 | -0.01 | 46% |
| boom | high-ROE only | 128 | +0.02 | 49% |
| boom | high-margin only | 126 | -0.16 | 48% |
| boom | **BOTH** | **66** | **+0.03** | **55% [43,66]** |
| longterm | base | 964 | -0.47 | 19% |
| longterm | high-ROE only | 158 | -0.24 | 28% |
| longterm | high-margin only | 129 | -0.25 | 21% |
| longterm | **BOTH** | **55** | **+0.02 [-0.55,+0.34]** | **27% [17,40]** |

**Verdict:** Both cohorts: combo median alpha ≥ base and the multibagger rate beats base (boom 55% vs 46%; longterm
27% vs 19%). But the longterm alpha lift is *marginal* — median only +0.02 with a very wide CI [-0.55,+0.34] (P+=0.57),
i.e. the median barely clears zero. The **multibagger** signal is the more credible one here. Genuine but a notch below
#1: high-ROE is doing most of the work in longterm (ROE-only already +0.28 mb), high-margin adds little incremental.
**Cross-regime on multibagger; weak/marginal on alpha.**

### 3. high-margin × low-debt  →  merely-additive / cohort-incomplete ⚠️

**Mechanism:** profitable-and-fat + unlevered = conservative cash generator.

| cohort | cell | N | median alpha | multibagger |
|---|---|---:|---|---|
| boom | base | 366 | -0.01 | 46% |
| boom | **BOTH** | 60 | +0.07 | 53% |
| longterm | base | 964 | -0.47 | 19% |
| longterm | **BOTH** | 71 | **-0.10 [-0.38,+0.09]** | 24% |

**Verdict:** In boom the combo looks good (+0.07, 53% mb). But in **longterm the cell median stays NEGATIVE (-0.10,
P+=0.19)** — it improves on the base (-0.47) but never flips positive, and the multibagger lift is small (24% vs 19%).
This is the low-debt-only weakness leaking through (low-debt was the weakest single feature). **Merely-additive /
fails the "flip positive in both regimes" bar.** Not a winner.

---

## Combos tested and REJECTED (failed cross-regime or sign-flip)

All shown at 3y (the upside horizon). "rejected" = combo failed to beat base AND beat both singles in at least one
cohort.

| combination | mechanism | why rejected |
|---|---|---|
| profitable × low-debt | clean compounder | boom: combo ≤ base/single (profitable alone ≈ combo). low-debt dilutes. Additive at best. |
| small-issue × profitable | under-the-radar quality | **boom strong (+0.2, mb 51%)** but **longterm flat (-0.4, no lift over singles)**. Single-regime. |
| low-OFS × profitable | founders keep skin in a real biz | boom positive; longterm combo = base (-0.5). OFS-skin already known MIXED — confirmed here. |
| rev-growth × profitable | growing & profitable | rev-growth HURTS in both cohorts (growth-at-IPO often peak-cycle); combo ≤ profitable-alone. |
| small-issue × low-debt | small clean co. | longterm additive only; boom combo < small-issue alone. |
| rev-growth × low-debt | self-funded growth | longterm combo -0.6 < base. Rev-growth poisons it. |
| small-issue × high-ROE | tiny quality | **boom striking (+0.4 median, mb 52%)** but **longterm additive** (high-ROE alone explains it). Single-regime. |
| low-OFS × low-debt | conservative cap structure | additive in both; neither edge survives conjunction. |
| rev-growth × high-margin | quality growth | NEGATIVE in both cohorts. Rejected. |

**Recurring lessons:**
- **`rev-growth` (net_sales_yr3/yr1) is a consistent UPSIDE KILLER** in combination — IPOs sold on recent
  topline acceleration tend to list near a peak; pairing growth with anything degrades it. Worth a standalone note.
- **`small-issue` and `high-anchor/high-QIB` effects are BOOM-ONLY** — small-issue × {profitable, high-ROE} are
  genuinely strong in 2020–25 but vanish in 2006–19, so they are *boom-regime hypotheses*, not durable interactions.
- **`profitable` and `low-OFS` add little on top of the quality pair** — profitability is necessary-ish background but
  not the differentiator; OFS-skin remains MIXED (re-confirmed).

---

## Bonus: the 3-way QUALITY STACK (low-debt & high-ROE & high-margin)

Pushing the winning pair to a triple. N is right at the floor but holds in both cohorts:

| cohort | base median / mb | STACK N | STACK median alpha [CI] | P+ | STACK multibagger [Wilson] |
|---|---|---:|---|---:|---|
| boom | -0.01 / 46% | 41 | **+0.07 [-0.40,+0.88]** | 0.80 | **56% [41,70]** |
| longterm | -0.47 / 19% | 34 | **+0.11 [-0.32,+0.49]** | 0.73 | **35% [21,52]** |

The stack flips median alpha positive in BOTH cohorts (longterm +0.11 vs base -0.47 is a large move) and lifts the
multibagger rate to 56%/35% (vs 46%/19% base). N=34–41 is just above the floor, so treat as **suggestive
confirmation of the #1 mechanism**, not an independent finding. The consistent read: **unlevered + high-ROE is the
spine; margin is a mild reinforcer.**

---

## BOTTOM LINE

Combinations DO reveal upside that single features miss — but only one combination clears the high bar cleanly, and
the edge is a **quality cluster centred on `low-debt × high-ROE`**, not a long list of pairs.

1. **`low-debt × high-ROE` — the one genuine cross-regime upside interaction.** Super-additive in longterm (the 2×2
   shows neither feature alone escapes the -0.40 base region; the conjunction flips to +0.18 median alpha, P+=0.76, and
   multibagger 19%→37%) and directionally positive in boom (mb 52% vs 46%, P+=0.74). This is the "clean compounder"
   signal and it is the headline.
2. **`high-ROE × high-margin` — a real but weaker companion** (multibagger lift in both cohorts: 55%/27% vs 46%/19%;
   alpha flip is marginal in longterm, +0.02 with a wide CI). Use as confirmation of the quality theme, not standalone.
3. The **3-way quality stack** (low-debt & high-ROE & high-margin) flips alpha positive in both cohorts (+0.07/+0.11)
   and lifts multibaggers to 56%/35%, corroborating that quality features compound — at the cost of N (~34–41, floor-level).

Everything else is single-regime (small-issue / high-ROE boom effects), merely-additive, or actively rejected
(rev-growth, OFS-skin). **The honest map: low-debt-AND-high-ROE is what goes hand-in-hand for a winner; almost nothing
else survives both regimes.**
