# Headline truths — Entry & Exit strategy (Layer-3 research)

Method spine enforced throughout: hard MB/SME split, maturity-gated horizons, min-N floors
(N>=30 tradable, N>=10 directional, suppress below), distributions/medians not just means,
3y/5y carried by the **longterm (2006–19)** cohort (boom 5y is early-survivor-biased),
subscription cuts are **boom-only** (single-regime), and **a finding is a hypothesis until its
SIGN holds in BOTH cohorts.** All exit/entry analysis uses the **secondary buyer** view
(`entry='listing'`, `return_from_listing_*`) unless noted; the allottee additionally pockets the
listing pop. Listing-day cuts exclude `unreliable_coverage`. Note the listing-day tautology:
`mfe_lst>=0`, `mae_lst<=0` mechanically (you bought at the open).

Substrate: `data/master/ipo_analysis.csv`, 2245 equity rows (boom 1254 / longterm 991; SME 1404 / MB 841).

Ranked strongest → weakest.

---

## #1 — HEADLINE: "Sell half" de-risks the median but the right tail still owns the mean (partial-exit paradox)

**Belief.** After the "no take-profit/stop-loss beats buy-and-hold" headline, the natural rescue is
the partial exit: book half at +T, ride the rest. Surely *that* free-lunches the right tail while
cushioning the downside.

**Numbers** (entry=listing; partial = `0.5*T + 0.5*endpoint` if `mfe_lst>=T` else `endpoint`;
HOLD = endpoint). Best-over-T partial vs pure-hold:

| seg/cohort | h | N | HOLD mean | HOLD med | best PARTIAL mean | best PARTIAL med | mean winner | median lifted? |
|---|---|---|---|---|---|---|---|---|
| MB/boom | 1y | 279 | 22.0 | 2.9 | 22.7 | 13.7 | partial(tie) | yes |
| MB/longterm | 1y | 456 | −2.4 | −16.2 | −0.1 | −2.6 | partial | yes |
| SME/boom | 1y | 681 | 61.1 | 0.0 | 46.0 | 14.8 | **HOLD** | yes |
| SME/longterm | 1y | 509 | 42.6 | 0.3 | 33.2 | 5.9 | **HOLD** | yes |
| MB/boom | 3y | 124 | 83.8 | 21.0 | 73.6 | 42.8 | **HOLD** | yes |
| MB/longterm | 3y | 457 | −4.6 | −33.3 | 1.4 | −5.3 | partial | yes |
| SME/boom | 3y | 242 | 279.8 | 51.6 | 192.5 | 105.6 | **HOLD** | yes |
| SME/longterm | 3y | 507 | 104.1 | −2.0 | 79.0 | 22.4 | **HOLD** | yes |

**Cross-regime verdict: HEADLINE (structural, holds in BOTH cohorts).** Two signs are stable
across both regimes and both segments:
1. **Partial exit ALWAYS lifts the median** (8/8 cells): e.g. SME/longterm 3y median goes −2.0% → +22.4%.
   The typical IPO is a slow loser, so locking in a profit on names that *did* run improves the median name.
2. **In any segment with a real right tail, partial exit SACRIFICES the mean** — SME (both cohorts,
   both horizons) and MB-boom-3y all favour pure-hold; selling half of a future 10x-bagger is exactly
   the leak the no-exit headline warned about. SME/longterm 3y: 104% mean → 79%.

The ONLY place partial exit wins the mean is **losing segments with no right tail** (MB/longterm),
where there's nothing to protect — so de-risking is free. That is itself the mechanism.

**Mechanism.** IPO returns are barbell-shaped: a near-zero/negative median and a fat right tail
(see #2). The median responds to the body of the distribution → partial exit helps it. The mean
responds to the tail → partial exit hurts it wherever a tail exists. "Sell half" is therefore a
**median-vs-mean trade-off, not a free lunch**: it converts you from a tail-harvester into a
typical-name harvester. It only dominates when the tail is already dead.

**Build-spec.** Add `layer3/findings/f_partial_exit.py` (Tier-1 enhancement). Columns:
`mfe_lst_{1y,3y}`, `return_from_listing_{1y,3y}`. Reuse `spine.segment` (MB/SME × boom/longterm),
maturity-gate implicitly via `mfe_lst.notna() & end.notna()`. Add a sibling to `spine.exit_strategy`
called `spine.partial_exit_strategy(g, entry, horizon, levels, frac=0.5)` returning per-T
`{pct_reached, median_captured, mean_captured}` plus the pure-hold and full-exit columns for
contrast (full-exit logic already in `spine.exit_strategy`). Backtest hook: extend
`layer3/backtest/` with a `partial_half` policy alongside the existing TP/SL policies so the
backtester reports it against do-nothing per segment×cohort.

---

## #2 — HEADLINE: The "buy every IPO" basket is a barbell — the mean is a mirage carried by the top 5%

**Belief.** "IPOs make money on average" / a diversified IPO basket is a sound passive bet.

**Numbers** (entry=listing, `return_from_listing`, whole-segment basket):

| seg/cohort | h | N | mean | **median** | % positive | P90 | top-5% mean | mean EXCLUDING top 5% |
|---|---|---|---|---|---|---|---|---|
| MB/boom | 1y | 279 | 22.0 | **2.9** | 53 | 113 | 229 | 11.9 |
| MB/longterm | 1y | 456 | −2.4 | **−16.2** | 37 | 83 | 209 | −13.1 |
| SME/boom | 1y | 681 | 61.1 | **0.0** | 49 | 193 | 858 | 19.2 |
| SME/longterm | 1y | 509 | 42.6 | **0.3** | 50 | 167 | 605 | 13.5 |
| MB/boom | 3y | 124 | 83.8 | **21.0** | 57 | 257 | 684 | 53.3 |
| MB/longterm | 3y | 457 | −4.6 | **−33.3** | 32 | 103 | 336 | −21.8 |
| SME/boom | 3y | 242 | 279.8 | **51.6** | 68 | 664 | 3102 | 132.6 |
| SME/longterm | 3y | 507 | 104.1 | **−2.0** | 48 | 392 | 1247 | 44.8 |

**Cross-regime verdict: HEADLINE.** In every cell the **median is dramatically below the mean**, and
**% positive sits at or below ~50%** (37% / 32% in MB/longterm). Strip the top 5% and the mean
collapses (SME/longterm 3y: 104% → 45%; SME/boom 3y: 280% → 133%). The sign is identical across both
cohorts: a coin-flip-or-worse chance per name, with the average rescued by a handful of moonshots.

**Mechanism.** IPO returns are right-skewed lognormal-ish: bounded at −100% on the downside, unbounded
on the upside, with a heavy right tail. The mean is dominated by the few survivors that compound; the
**typical (median) IPO drifts sideways or down**. So "buy every IPO" only works if you (a) hold the full
basket — concentration kills you because you'll likely miss the moonshot — and (b) survive the long
losing body. The basket mean is real but **un-bankable at the single-name level** — which is precisely
why entry/exit timing on one name (#1, #4) fights a losing battle against dispersion.

**Build-spec.** Add `layer3/findings/f_basket_dispersion.py`. Columns: `return_from_listing_{1y,3y}`,
`alpha_{1y,3y}`. Reuse `spine.distribution` (gives P10/median/P90/mean/N) + `spine.proportion(end>0)`
for % positive + Wilson CI. Add `spine.basket_dispersion(g, horizon, entry, top_frac=0.05)` returning
`{mean, median, pct_positive(+CI), p90, top_frac_mean, mean_ex_top}`. This is the quantified barbell the
predictor's downside-safety component should cite.

---

## #3 — HEADLINE (boom-only by data, but mechanism is structural): The flip trap — the hotter the IPO, the less of it you can flip

**Belief.** Apply to oversubscribed IPOs, flip the big listing pop, easy money. The pop is the proof.

**Numbers** (BOOM only — subscription is single-regime; allottee flips at open = `adj_listing_gain_open`;
retail allotment odds modelled as `min(1, 1/sub_total_x)`; E[capture per application] = allot × pop):

| seg | sub bucket | N | median pop | median allot odds | **E[capture / application]** | pop>0 |
|---|---|---|---|---|---|---|
| MB | 1–5x | 82 | 0.0% | 43.7% | 0.00% | 43% |
| MB | 5–15x | 34 | 5.9% | 10.5% | 0.56% | 65% |
| MB | 15–50x | 75 | 11.8% | 3.7% | 0.29% | 68% |
| MB | >50x | 128 | 37.1% | 1.1% | 0.35% | 97% |
| SME | 1–5x | 133 | 1.3% | 52.6% | 0.64% | 59% |
| SME | 5–15x | 78 | 3.5% | 12.2% | 0.44% | 65% |
| SME | 15–50x | 89 | 10.0% | 3.1% | 0.30% | 74% |
| SME | >50x | 331 | 55.6% | 0.5% | 0.22% | 92% |

**Cross-regime verdict: SINGLE-REGIME-ONLY (boom; subscription not in longterm cohort) — but the
mechanism is an identity, not a regime effect.** Cannot cross-validate the sign on longterm because
`sub_total_x` is boom-only. Flag as hypothesis-strength on cross-regime, but the arithmetic is robust.

**Mechanism.** The pop and the allotment odds are **mechanically inverse**: demand simultaneously drives
the price up and your allotment down (allotment ≈ 1/oversubscription). The product — what a flipper
actually captures *per rupee applied* — is **flat-to-declining across subscription buckets** (~0.2–0.6%
for the hottest names, and the hottest IPOs actually have the LOWEST expected capture despite a near-100%
pop-positive rate and 37–56% median pops). The visible pop is a **selection illusion**: you see the big
gain but can't size into it. Adverse selection compounds it — the easy-to-get cold IPOs (1–5x) have a
~0% median pop. There is no free flip.

**Build-spec.** Add `layer3/findings/f_flip_trap.py` (mark `cohort_scope: boom_only`). Columns:
`sub_total_x`, `adj_listing_gain_open`, `listing_metrics_status` (exclude `unreliable_coverage`).
Add `spine.allotment_capture(g, alloc_model='inverse_sub')` returning per-sub-bucket
`{n, median_pop, median_allot, expected_capture_per_appln, pct_pop_positive}`. Surface in Part A as a
boom-only "movement-lens" finding and in the predictor's narrative ("a hot IPO's pop is not investable").

---

## #4 — MIXED: Averaging down lowers your average cost but rarely your loss — the dip almost never comes back inside the horizon

**Belief.** A quality IPO that's fallen 30–50% is "on sale" — average down to lower your cost and
recover faster.

**Numbers** (entry=listing; among names whose `mae_lst_{h} <= −D`; HOLD vs ADD-equal-tranche-at-−D,
blended = `(1+end)/(1−D/2)−1`; tranche-2 standalone = `(1+end)/(1−D)−1`):

| seg/cohort | h | D | dippers N | HOLD med | AVG-DOWN med | **% ended above entry** | tranche-2 (buy@−D) med / %pos |
|---|---|---|---|---|---|---|---|
| MB/boom | 1y | 30% | 106 | −31.3 | −19.2 | **4%** | −1.8 / 47% |
| MB/longterm | 1y | 30% | 275 | −42.7 | −32.6 | **13%** | −18.1 / 33% |
| SME/boom | 1y | 30% | 361 | −35.9 | −24.6 | **17%** | −8.5 / 41% |
| SME/longterm | 1y | 30% | 193 | −42.3 | −32.1 | **7%** | −17.6 / 32% |
| MB/longterm | 3y | 30% | 378 | −48.0 | −38.8 | **22%** | −25.6 / 38% |
| SME/longterm | 3y | 30% | 292 | −39.9 | −29.3 | **21%** | −14.1 / 40% |
| SME/boom | 3y | 30% | 136 | −12.0 | +3.6 | **48%** | +25.8 / 56% |

**Cross-regime verdict: MIXED / mostly REJECTED as alpha, but a robust CAVEAT headline.** The
"improvement" from averaging down is **arithmetically guaranteed dilution** (you lowered cost), not a
recovery signal. The decision-relevant numbers are the last two columns:
- **At 1y, in BOTH cohorts and BOTH segments, only 4–17% of −30% dippers end back above the buyer's
  entry, and the tranche-2 *standalone* trade is a median loser (−1.8% to −18%, %pos 32–47%).** The dip
  is information, not a discount.
- **At 3y the longterm cohort still shows the dip persisting (21–22% recovery, tranche-2 median −14 to
  −26%).** SME/boom 3y is the lone winner (48% recover, +26% tranche-2) — but that is the boom
  liquidity tide, not a cross-regime truth (it flips negative in longterm). Sign NOT stable → not a
  headline.

**Mechanism.** A deep early drawdown in an IPO is a momentum/quality signal, not noise: the names that
crater tend to keep cratering (the long left body of the barbell, #2). Averaging down doubles your
exposure to exactly that population. Lowering average cost makes the *reported* blended return less
negative purely by arithmetic, masking that you've put a second, losing trade on top of a losing one.

**Build-spec.** Add `layer3/findings/f_average_down.py`. Columns: `mae_lst_{1y,3y}`,
`return_from_listing_{1y,3y}`. Add `spine.average_down(g, entry, horizon, dips=(0.30,0.50))` returning
per-D `{dipper_n, pct_dipped, hold_med, blended_med, pct_recovered_above_entry, tranche2_med,
tranche2_pct_pos}`. Frame in Part A as a "what NOT to do" caveat; feed `pct_recovered_above_entry` into
the downside-safety scorecard component.

---

## #5 — REJECTED (cross-regime): Contrarian entry — buy the discount/flat lister, skip the big pop

**Belief.** The pop fades (T3), so from the secondary buyer's seat the flat/discount listers should
outperform the big-pop listers over 1y/3y.

**Numbers** (entry=listing; DISC = `adj_listing_gain_open <= 0`; BIGPOP = `>= +20%`; excl.
`unreliable_coverage`):

| seg/cohort | h | DISC N / ret med / pos | BIGPOP N / ret med / pos |
|---|---|---|---|
| MB/boom | 1y | 70 / +0.5% / 50% | 115 / +2.0% / 54% |
| MB/longterm | 1y | 143 / −19.0% / 33% | 127 / −19.1% / 35% |
| SME/boom | 1y | 142 / −13.7% / 37% | 304 / −1.4% / 50% |
| SME/longterm | 1y | 168 / −7.2% / 42% | 85 / −20.8% / 44% |
| MB/boom | 3y | 38 / +8.2% / 55% | 44 / +20.7% / 55% |
| MB/longterm | 3y | 143 / −43.3% / 31% | 128 / −27.2% / 30% |
| SME/boom | 3y | 62 / +55.2% / 68% | 68 / +39.1% / 65% |
| SME/longterm | 3y | 166 / −7.7% / 46% | 85 / −39.6% / 34% |

**Cross-regime verdict: REJECTED — the sign FLIPS by cohort.** SME shows discount > pop in longterm
(−7.7% vs −39.6% at 3y) but pop > discount in boom (−13.7% vs −1.4% at 1y). MB consistently shows
big-pop weakly AHEAD (the opposite of the contrarian thesis). There is **no stable secondary-buyer edge
from listing-gain bucketing** — the listing pop predicts neither outperformance nor underperformance
robustly once you remove the allottee's pop (which the secondary buyer never gets). T3 pop-fade is about
the *allottee's issue-anchored* return decaying, NOT a tradable secondary-buyer signal. Important null:
it tells the secondary buyer **listing-day gain carries no actionable signal** — do not pay up to avoid a
"weak" lister or chase a "hot" one.

**Build-spec.** Keep as a documented NULL in `rules/` (status: rejected, type: entry-signal) rather than
a finding module, with the table above as evidence. If surfaced, it belongs in the validation tab as a
"tested & not robust" entry alongside ofs-skin/profitable. Columns: `adj_listing_gain_open`,
`return_from_listing_{1y,3y}`, `alpha_{1y,3y}`; cut via `spine.segment` + the listing-status filter.

---

## Ranking summary

| # | Headline | Verdict | Decision impact |
|---|---|---|---|
| 1 | Partial exit lifts the median but bleeds the mean wherever a tail exists | **HEADLINE (both cohorts)** | If you want the *expected* IPO return, hold; "sell half" only if you'd rather a reliable typical outcome |
| 2 | Buy-every-IPO basket is a barbell; mean is a top-5% mirage, median ≤ ~0 | **HEADLINE (both cohorts)** | Diversify wide or don't play; never concentrate; size for the body, not the mean |
| 3 | Flip trap: hotter IPO → bigger pop but lower allotment → flat capture | **single-regime (boom) + structural identity** | Stop chasing pops; capture-per-application is flat, the pop is uninvestable |
| 4 | Averaging down dilutes cost but the dip rarely recovers in-horizon | **MIXED / mostly rejected as alpha; robust caveat** | Don't average down an IPO; the drawdown is a signal, tranche-2 is a median loser at 1y both cohorts |
| 5 | Contrarian "buy the discount lister" beats big-pop listers | **REJECTED (sign flips by cohort)** | Listing-day gain is NOT a secondary-buyer entry signal — ignore it |
