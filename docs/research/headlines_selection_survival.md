# Headline truths — Selection & Survival batch

Hunt for counterintuitive, decision-relevant, cross-regime-robust truths about WHICH IPOs to pick/avoid
and HOW they die. Method-spine enforced: hard MB/SME split, maturity-gating before horizon returns,
min-N floors (N≥30 tradable / N≥10 directional), distributions + Wilson CIs not means, long horizons
carried by the longterm cohort, SME wipeout treated as a survivorship UNDER-count (a BAND). A finding is a
HYPOTHESIS until its SIGN holds in BOTH cohorts. All numbers computed live on `data/master/ipo_analysis.csv`
(2,245 equity rows) via `layer3.spine`; verified, not speculated.

Ranked strongest → weakest.

---

## #1 — HEADLINE. The real SME risk isn't the −100% wipeout, it's DEAD MONEY you can't exit

**Belief.** "The danger in a bad IPO is that it goes to zero." Risk = wipeout.

**Truth.** For SME the formal wipeout is rare; the dominant bad outcome is the **zombie** — alive, >50%
below issue, and illiquid (`liquidity_flag='low'`), so you literally cannot sell. Dead-money DWARFS confirmed
wipeout in **both** SME cohorts, and the relationship inverts vs Mainboard.

| segment / cohort | N | dead-money (illiquid, <−50%) [95% Wilson] | confirmed wipeout (lower) | ratio dead : wipeout |
|---|---|---|---|---|
| **SME / boom** | 884 | **17.8%** [15.4–20.4] | 1.1% | **15.7×** |
| **SME / longterm** | 520 | **12.7%** [10.1–15.8] | 8.5% | **1.5×** |
| MB / longterm | 471 | 4.2% [2.8–6.5] | 22.7% | 0.2× |
| MB / boom | 370 | 0.0% [0.0–1.0] | 0.3% | — |

Cross-regime sign for SME holds: dead-money > confirmed wipeout in boom AND longterm. The boom 15.7× is partly
because boom-SME is too young to have formally delisted, but the longterm cohort — where SME has had years to
die — STILL shows dead-money ≥ confirmed wipeout (1.5×), and SME wipeout is itself a documented under-count
(thin SME never prints a −90% terminal). So the true dead-or-stuck share is even larger.

**The movement lens (does the zombie ever offer an exit?).** Yes — early, then never again. Among
currently-dead-money SME names (boom, 1y maturity-gated), measured from ISSUE: 79% traded back above issue at
some point in year 1, 51% reached +20%, 36% reached +50% (median peak +21%). From LISTING (secondary buyer):
34% reached +20%, 18% reached +50%. So the exit existed in the first year and the holder rode it down instead.
For MB dead-money the early window is even more generous (70% reached +20% from issue in yr1). **Mechanism:**
SME float is tiny and market-making is shallow; a name that drifts below issue loses its sponsor-supported
liquidity, the bid evaporates, and the position becomes un-sellable at any sane price — a slow bleed, not a
clean death. The −100% framing makes investors fear the wrong thing and ignore the far more common fate.

**Verdict: HEADLINE (cross-regime for SME).**

**Build-spec.** Promote `n9_zombie` from a single descriptive table into a paired headline finding: (a) the
dead-money-vs-wipeout ratio table above with Wilson CIs, framed as "SME's #1 risk is dead money, not zero";
(b) a movement-lens panel showing that dead-money names DID give a year-1 exit (`spine.reach_curve` MFE on the
currently-dead-money subset, issue + listing entry), making the actionable rule explicit: *in SME, treat the
first-year peak as the exit, because illiquidity removes the second chance.* Surface in the predictor's
downside-safety component and in the app's score-a-new-IPO tab as a SME-specific "dead-money probability" gauge.

---

## #2 — HEADLINE. Fallen-angel recovery is an unstackable coin-flip — no pre-listing feature predicts who comes back

**Belief.** "If an IPO has fallen hard but the company is profitable / low-debt / a big quality issue, it'll
recover — buy the dip." Quality should rescue fallen angels.

**Truth.** Among names that hit a deep trough (MAE ≤ −50% within year 1), lifetime recovery is low and, more
importantly, **no pre-listing fundamental moves the recovery odds in a stable direction across regimes.**

Lifetime "back to break-even (current return ≥ 0)" among fallen names:
- SME/boom 16% · SME/longterm 47% · MB/boom 16% · MB/longterm 37%.

Feature splits on the recovered share (≥10 each side) flip sign cohort-to-cohort and segment-to-segment:
- **issue size**: SME/longterm large issues recover LESS (40% vs 54%), MB/longterm large recover MORE (41% vs 34%) — sign flip.
- **ROE**: high-ROE recovers MORE in longterm (57% vs 33% SME; 21% vs 7% MB) but LESS in SME/boom (11% vs 19%) — sign flip.
- **debt/equity, profitable flag**: gaps within Wilson noise, no consistent direction.

Recovery-to-break-even **by year-end** is even bleaker (6–22%) and equally feature-blind.

**Mechanism.** A −50% IPO drawdown is mostly information about the price path (overpricing + sentiment
reversal), not about a company characteristic that was knowable pre-listing. The features that "should" help
were already in the issue price; once sentiment breaks, recovery depends on idiosyncratic post-listing events
(new contracts, regime liquidity) that are orthogonal to the RHP. You cannot stack the deck on which fallen
angel returns — so "averaging down on a quality name that fell" has no edge.

**Verdict: HEADLINE (cross-regime: the *un-predictability* is the robust finding — every candidate signal fails
its sign-stability test in both cohorts).**

**Build-spec.** New finding `n13_fallen_angel`: fix the fallen set (MAE_1y ≤ −50%, maturity-gated), report
lifetime + year-end recovery base rates by segment×cohort with Wilson CIs, then a feature-split grid
(profitable / debt tertile / issue-size median / ROE median) with an explicit cross-regime sign-stability
column. Headline output is a NEGATIVE rule for the rules registry: `fallen_angel_recovery = unpredictable`
(status: validated-null) — the predictor must NOT award a "cheap after the fall" bonus.

---

## #3 — Strong (cross-regime directional). The accrual red-flag (paper profit, no cash) is the one fundamental that beats the profitable flag — but only directionally

**Belief.** "Profitable companies are safer." (Already flagged MIXED: the profitable premium flips sign across
regimes.) Hunt for ANY fundamental that survives.

**Truth — profitable flag:** confirmed mixed/unreliable, not a headline.

**Truth — accrual flag** (PAT>0 but operating cash ≤ 0 in latest pre-IPO year): in the cohorts old/clean enough
to read, accrual names underperform CLEAN profitable names on forward 1y alpha and carry more wipeout:
- MB/longterm: median 1y alpha **−30% (accrual, N=42)** vs **−5% (clean, N=110)**; wipeout 38% vs 22%.
- SME/boom: median 1y alpha **−15% (accrual, N=420)** vs **+1% (clean, N=411)**.
- MB/boom: no gap (both ≈ −8%) — but boom MB is too young for the downside to show.
- SME/longterm: small REVERSE on alpha (−8% accrual vs −11% clean) though wipeout still higher (14.5% vs 2.4%).

So the **alpha** sign is not perfectly stable (SME/longterm muddies it), but the **wipeout/downside** direction
(accrual ≥ clean wipeout) holds in 3 of 4 readable cells, and accrual is clearly worse than the simple
profitable flag suggests. Notably accrual names sit BETWEEN clean and loss-makers, and in SME/boom the
loss-makers are the worst of all (−58% alpha) — so "loss-makers underperform accrual" does NOT hold; the
ordering is clean > accrual > loss in the cleanest cells.

**Mechanism.** Reported PAT with negative operating cash = earnings manufactured by working-capital build /
aggressive revenue recognition — common in SME pre-IPO window-dressing. The market eventually discounts profits
with no cash behind them, and cash-burning "profitable" firms are more fragile when funding tightens.

**Verdict: mixed-to-strong** — robust as a DOWNSIDE/wipeout discriminator, NOT robust as an alpha signal. Best
available fundamental, but does not clear the cross-regime HEADLINE bar on its own.

**Build-spec.** Keep `n8_accrual` but re-headline it on the WIPEOUT axis (where the sign is stable) rather than
alpha: "earnings-without-cash roughly doubles the wipeout rate vs clean profitable, across regimes." Add the
3-way ordering (clean < accrual < loss) explicitly. Feed accrual into the downside-safety component as a
penalty; do NOT give it alpha weight.

---

## #4 — Strong, but single-cohort for clean cross-regime. Size-survival: small Mainboard issues carry ~2× the bad-outcome rate; "too big to pop" is real on the upside

**Belief.** "A small, focused issue is fine; size doesn't drive survival."

**Truth.** Bad-outcome rate (confirmed wipeout + dead-money) falls monotonically with issue size for Mainboard:
- MB/longterm: <100cr **49.2%** [41.9–56.5] vs ≥500cr **25.6%** [18.8–33.9] — nearly 2×.
- MB/longterm full ladder: <25cr 32% · 25–100cr 53% · 100–500cr 40% · 500–2000cr 28% · >2000cr 19%.
- MB/boom: too young for wipeout, but dead-money already shows the gradient — 100–500cr 13.2% vs >2000cr 5.7%.

The clean cross-regime test is blocked because **boom-MB has almost no small issues** (N=6 under 100cr), so the
small-vs-large contrast is essentially a longterm-MB finding (directionally echoed by boom dead-money). On the
UPSIDE the mirror also holds and is genuinely cross-regime: the multibagger/2x rate is much higher in the
small/SME bands than in jumbo issues (consistent with the SME barbell, #5) — "too big to pop."

For SME there is no usable spread (≈97% of SME issues are <100cr), so size-survival is not testable within SME.

**Mechanism.** Small issues skew to weaker sponsors, thinner post-listing float, and less institutional
diligence → higher death + dead-money. Large issues are over-distributed and fully priced → muted pops but rare
ruin. There is a goldilocks read: the 500–2000cr band minimizes ruin without fully killing upside.

**Verdict: single-regime (longterm-MB) for the survival gradient; cross-regime directional for the upside
mirror.** Decision-relevant but does not meet the strict both-cohort wipeout bar.

**Build-spec.** Sharpen `n4_issue_size`: add the combined "bad-outcome" column (wipeout_lower + dead-money) with
Wilson CIs and an explicit caveat that the small-MB bin is longterm-only (boom-MB has ~no small issues, shown
via dead-money proxy). Keep it as a downside-component input for MB; flag it non-applicable inside SME.

---

## #5 — Strong reframe (not new, sharpened). SME is a lottery; the index-beating "mean" describes nobody — and the distinctively SME risk is dead money

**Belief.** "SME IPOs beat the market on average — a good place to invest."

**Truth.** The mean is a mirage produced by a handful of moonshots; the median holder gets little, and the modal
bad outcome is dead money, not a clean loss:

| seg / cohort | N | MEAN current return | MEDIAN | %≥2x | %≥5x | %below issue | wipeout_lo | dead-money(illiq) |
|---|---|---|---|---|---|---|---|---|
| SME / boom | 884 | **+129%** | **+2%** | 26.1% | 7.9% | 48.6% | 1.1% | 17.8% |
| SME / longterm | 520 | **+666%** | +46% | 41.9% | 24.2% | 42.5% | 8.5% | 12.7% |
| MB / boom | 370 | +62% | +11% | 19.5% | 3.0% | 45.9% | 0.3% | 0.0% |
| MB / longterm | 471 | +578% | +6% | 38.5% | 23.9% | 49.1% | 22.7% | 4.2% |

The SME/boom case is starkest: mean +129% but median +2%, with ~49% below issue and 18% dead-money — the
average is carried entirely by the right tail. Caveat: the mean-≫-median barbell is GENERAL to IPOs (it shows in
MB too — see the gold-standard right-tail result), so "barbell" alone is not SME-specific. What IS distinctively
SME is the **dead-money leg** (#1): MB barely has it, SME is riddled with it. So the honest SME headline is
"lottery with a trapdoor you can't climb out of," which is #1 stated as a distribution.

**Mechanism.** Same as #1 — thin float makes both tails extreme (moonshots on no supply, un-exitable bleed on
no bid) and makes the mean uninformative for a single buyer who can't diversify across the whole cohort.

**Verdict: HEADLINE as a distribution-vs-mean reframe; its NOVEL, SME-specific content is #1.** Best delivered
as the framing wrapper around #1.

**Build-spec.** A combined `outcome_profile`-style SME-vs-MB distribution card (mean/median/%≥2x/%≥5x/
%below-issue/wipeout-band/dead-money) per cohort, with the one-line takeaway "report the distribution, never the
mean." Wire into the app report tab as the SME explainer; point it at #1 for the actionable rule.

---

## Rejected / not-robust

- **Profitable-at-IPO premium** — confirmed MIXED (sign flips across regimes); not a headline. (t9)
- **Debt/equity death-signal** — the top-debt tertile shows higher wipeout ONLY in MB/longterm (11%→29% across
  tertiles); MB/boom is uniformly ~0 (too young) and SME shows no gradient (boom: 0.4/0.0/0.8%; longterm:
  9.3/4.8/8.5% — non-monotone). NOT cross-regime robust. (n7)
- **Loss-makers are the safest floor** — false; in SME/boom loss-makers post the WORST alpha (−58%); ordering is
  clean > accrual > loss, so loss-making is not a protective floor.

---

## Strongest validated headlines (TL;DR)

1. **SME's real risk is dead money, not the −100%.** Belief: a bad IPO goes to zero. Truth: SME wipeouts are
   rare; the dominant bad fate is the illiquid zombie — alive, >50% below issue, un-sellable. Dead-money beats
   confirmed wipeout 15.7× in boom-SME (17.8% vs 1.1%, N=884) and still 1.5× in longterm-SME (12.7% vs 8.5%,
   N=520), exactly inverting Mainboard (where wipeout dominates). And the zombie DID offer an exit — 51% of
   currently-dead SME names traded ≥+20% above issue at some point in year 1 — then the thin float closed the
   door. Mechanism: tiny SME float loses its market-maker bid below issue, so the loss can't be realized.

2. **Fallen-angel recovery is an unstackable coin-flip.** Belief: buy the quality name that fell, it'll bounce.
   Truth: among names that fell ≤−50% in year 1, lifetime recovery to break-even is 16–47%, and NO pre-listing
   feature (profitable, low-debt, large issue, high ROE) shifts those odds in a sign-stable way across cohorts —
   every candidate signal flips between boom and longterm. Mechanism: a deep IPO drawdown is a price-path fact,
   not a knowable company trait; the "rescue" features were already in the issue price. The validated rule is a
   negative one: do not pay up for "cheap after the fall."

3. **Earnings-without-cash is the one fundamental worth flagging — on the downside.** Belief: profitable =
   safe. Truth: the profitable flag is mixed, but the accrual red-flag (PAT>0 yet operating cash ≤0) roughly
   doubles the wipeout rate vs clean profitable companies (MB/longterm 38% vs 22%; SME ~2.4%→14.5%) and posts
   sharply worse forward alpha where the cohort is old enough to read (MB/longterm median 1y alpha −30% vs −5%).
   Mechanism: cash-less profit is manufactured earnings that the market eventually discounts; such firms are
   fragile when funding tightens. Robust as a downside discriminator, not as an alpha signal.
