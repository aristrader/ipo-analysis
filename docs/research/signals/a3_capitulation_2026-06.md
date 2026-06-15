# A3 — Does the 90-day capitulation EXIT beat holding? (re-validation of F5e as an act-on sell)

**Verdict: NO. The 90-day capitulation rule must stay a LEAN/FLAG only — NOT an act-on-it sell.**
Acting on it (selling at day 90) does not beat do-nothing cross-regime, and in the boom cohort
it provably **destroys value**. F5e remains a valid display-only red flag (predicts bad *outcomes*),
but it is *not* a profitable exit trigger. Score policy is unchanged: post-listing signal, never a
score input.

Script: `tools/research/a3_capitulation.py` · review CSV: `data/master/review/a3_capitulation_false_exits.csv`
Run: `PYTHONPATH=. .venv/bin/python tools/research/a3_capitulation.py` · `as_of` 2026-06-06 substrate.

## Honest caveats first
- **This re-confirms M1, it does not discover anything new about exits.** M1 already found no
  blanket take-profit/stop beats buy-and-hold cross-regime because exits trade the right tail for
  the body. A3 is the *specific* test of the F5e day-90 rule as a sell; it lands on the same
  mechanism. Do not read this as an independent second confirmation — it is the same truth, applied.
- The **longterm terminal** numbers are dominated by extreme multi-year compounding outliers
  (e.g. Kavita Fabrics fwd-term alpha +24,494%, Garden Reach +3,050%). The longterm portfolio-mean
  CI is therefore enormous (−113%..+432%) and I do **not** trust its point estimate. The clean,
  trustworthy result is in (a) the **placebo** and (b) the **boom portfolio mean** (CI excludes 0).
- F5e was validated as a *flag on outcomes* with no look-ahead; A3 inherits that PIT discipline —
  the capit flag uses ONLY closes in sessions 1..90, forward returns are measured from day 90
  onward, delisted names get survivorship-honest terminals (decision A1).

## Method
For every name with ≥95 sessions (`issue_price_adj`, exclude `unreliable_coverage`): flag `capit` =
`max(close[sessions 1..90]) < issue_price_adj` (identical to `layer3/calls.py`). For flagged names,
compute **forward alpha vs Nifty from the day-90 close** to 6m / 1y / terminal — this is exactly
what SELLING forfeits (or HOLDING captures). `sell_beat_hold` on a name = forward alpha < 0.
Placebo = the same forward-alpha measured on NON-flagged names and on ALL names (is the negative
drift flag-specific or universe-wide?). Cross-regime = boom (2020–26) vs longterm (2006–19).

Sample: scanned 2174 price files; capit flag-rate **15.5%** (336 flagged: 178 boom, 158 longterm).

## Sell-vs-hold table (forward alpha from day 90; flagged names; Wilson 95% CI on the count rate)

| cohort | horizon | N | sell_beat_hold (fwd α<0) | Wilson 95% | median fwd α | **mean fwd α** | P10 | P90 |
|--------|---------|---|--------------------------|------------|--------------|----------------|-----|-----|
| boom | 6m | 118 | 61% | 52–69% | −10.6% | +3.9% | −38% | +56% |
| boom | 1y | 82 | 67% | 56–76% | −15.4% | +6.4% | −58% | +70% |
| boom | terminal | 178 | 57% | 50–64% | −7.8% | **+29.1%** | −67% | +111% |
| longterm | 6m | 151 | 73% | 65–79% | −23.4% | −13.2% | −56% | +42% |
| longterm | 1y | 146 | 75% | 67–81% | −32.3% | −15.0% | −93% | +66% |
| longterm | terminal | 158 | 78% | 71–84% | −124.6% | +86.8%* | −401% | +182% |

\* outlier-dominated, untrustworthy point estimate (see caveats).

**The count rate (57–78% "sell beat hold") is the median trap.** Most flagged names drift down a
little after day 90, so per-name the majority are negative. But the *portfolio* you hold compounds on
the MEAN, and the mean is dragged positive by a fat right tail of recoverers. Bootstrap on the
flagged basket's terminal mean:

| cohort | N | mean fwd-term α | bootstrap 95% CI |
|--------|---|-----------------|------------------|
| boom | 178 | **+29.1%** | **+6%..+56% (excludes 0 → POSITIVE)** |
| longterm | 158 | +86.8% | −113%..+432% (straddles 0, outlier-driven) |

In the boom cohort, **selling the flagged basket at day 90 forfeits a statistically positive +29%
mean forward alpha** — it destroys value. Longterm is too noisy to claim a sell edge. Neither cohort
shows a robust "selling wins."

## Placebo — the negative drift is NOT flag-specific (this is the kill shot)
Forward-term alpha from day 90, flagged vs non-flagged vs all:

| cohort | FLAGGED median / P(fwd>0) | NON-flagged median / P(fwd>0) | ALL median |
|--------|---------------------------|-------------------------------|-----------|
| boom | −7.8% / 43% | −15.4% / 39% | −13.4% |
| longterm | −124.6% / 22% | −132.4% / 25% | −131.6% |

The flagged group's negative forward median is **indistinguishable from (slightly BETTER than) the
non-flagged control.** The post-day-90 negative-median drift is a property of the IPO universe
(alpha mean-reversion vs Nifty after the first quarter), not of the capitulation flag. A random
day-90 exit on a non-flagged name looks the same. So even the apparent "majority sell wins" rate is
regime drift, not a capitulation edge — the flag adds nothing as a sell trigger.

## False exits — eventual winners the rule would have dumped
Of flagged names with a terminal: **43% in boom (76/178) and 22% in longterm (35/158) had POSITIVE
forward-terminal alpha** — eventual recoverers the rule would have sold. 111 false exits total
(→ `data/master/review/a3_capitulation_false_exits.csv`). Top dumped winners: Garden Reach (+3,050%),
Kavita Fabrics (+24,494%), Vishal Retail (+1,534%), Bizotic (+1,361%).

**33 of 111 false exits are near-misses** (cleared issue by <5% within 90d but the flag still fired):
IRFC, Kalyan Jewellers, KFin Technologies, CreditAccess Grameen, S.J.S. Enterprises, Inox Green.
The rule is brutally threshold-sensitive.

**Fujiyama (owner's flagged near-counterexample) — confirmed.** Max close in sessions 1..90 = 225.0
vs issue 228.0 (**ratio 0.987 — missed clearing by 1.3%**) → trips the flag. Terminal close 328.3
(+44% over issue). The rule would have wrongly dumped it at day 90. Fujiyama is the archetype: the
false exits cluster exactly at the threshold the rule draws.

## Placebo / falsifier (pre-declared interpretation)
- PLACEBO (random/non-flagged day-90 exit): non-flagged names show the **same** negative forward
  drift → the "edge" is universe-wide, not the flag. **Placebo passes (rule fails).**
- FALSIFIER (what would make the sell worth acting on): flagged basket forward-MEAN alpha
  significantly **negative** (bootstrap CI excludes 0 on the negative side) in BOTH cohorts, AND
  materially below the non-flagged control. **Neither held** — boom mean is positive, longterm is
  noise, control is identical. Rule is not act-on-able.

## Conclusion & relationship to M1 / F5e
- **F5e stays exactly as it is: a display-only day-90 capitulation FLAG/LEAN on outcome risk.** It
  correctly predicts bad outcomes (validated, incremental to N14) — useful for *monitoring/warning*.
- **It must NOT become an act-on-it sell.** Selling at day 90 does not beat holding cross-regime;
  in the boom it destroys a statistically positive +29% mean forward alpha, and it dumps eventual
  multibaggers at a 22–43% false-exit rate, with near-misses (Fujiyama, IRFC, Kalyan) right at the
  line. This is M1's right-tail mechanism, not a new exception to it.
- Score policy unchanged (post-listing signal → never a score input).

## Proposed `rules/index.md` line (for the controller to integrate — A1 owns the file)
`A3 capitulation-EXIT re-test (2026-06-09): SELLING on the F5e day-90 flag does NOT beat HOLD
cross-regime — boom flagged-basket forward-term alpha mean +29.1% [boot +6..+56%, excludes 0] so
selling DESTROYS value; longterm noisy (CI straddles 0). Per-name "sell wins" 57–78% is the median
trap — placebo: non-flagged names drift identically (−7.8% vs −15.4% boom; −124.6% vs −132.4%
longterm), so the negative median is universe-wide post-d90, not flag-specific. 22–43% false-exit
rate dumps recoverers (Garden Reach +3050%, IRFC/Kalyan/KFin near-misses; Fujiyama max90=0.987
tripped→+44% terminal). VERDICT: F5e stays display-only FLAG/LEAN, NOT an act-on sell. Confirms M1.`
