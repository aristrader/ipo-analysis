# Red-team: portfolio / track-record / scorecard MVPs (2026-06-08)

Lens: skeptic. Where a sharp user loses trust. Grounded in live numbers (ledger 5,170 rows;
APPLY basket = 180 historical_sim + 11 backfilled + 1 live). Severity: TRUST-CRITICAL / IMPORTANT / NIT.

## TRUST-CRITICAL

### 1. The "2.09x" headline is a dress rehearsal, not a track record
- WHERE: `track_record.py` ₹1L portfolio table; `portfolio.summary`.
- WHY: The big multiple (historical_sim/secondary = **2.09x**, allottee = 2.85x) comes from 180
  *simulated* calls. Live=1, backfilled=11. The page does caption mode, but the number sits in a
  big table next to "Growth of ₹1 lakh — followed every APPLY call" — the framing implies a record
  that was *followed*. Almost nothing here was actually followed forward.
- FIX: Lead with the live/backfilled rows (or grey-out / collapse historical_sim behind an expander
  labeled "dress rehearsal — not a real record"). Put "0 live calls have matured" as a banner ABOVE
  the table, not only in the scorecard section. Never let 2.09x be the first number the eye lands on.

### 2. The multiple is mean-driven and one winner-heavy
- WHERE: `summary()` → `mult = v.sum()/(CAPITAL*len(v))` (an equal-₹ mean of multiples).
- WHY: historical_sim/secondary mean = 2.09x but **median position = 1.18x** and **win-rate 59%**.
  Top position = 25.8x; drop it → 1.96x, drop top 3 → 1.81x. So a typical followed call roughly
  matched inflation, and the headline is carried by a handful of moonshots. A user reads "2.09x" as
  "my money roughly doubled"; the median experience is +18%.
- FIX: Show median-position multiple and win-rate WITH equal prominence to the mean, or report the
  basket as median + "(mean 2.09x, skewed by a few outliers)". The `median_mult` is already computed
  — surface it in the table, not buried.

### 3. "vs Nifty" is not what the user thinks (no idle-cash / staggered-capital model)
- WHERE: portfolio table "vs Nifty" column; `simulate()` per-call Nifty leg.
- WHY: Each call deploys a fresh ₹1L and is benchmarked over ITS OWN holding window, then summed.
  That's a fair per-call alpha, but presented as a portfolio "vs Nifty" it implies you had ₹1L×191
  to deploy and the index alternative was the same. It is NOT a real equity curve (no shared capital,
  no idle cash between calls, overlapping windows summed). "1.27x Nifty" is an average-of-benchmarks,
  not "Nifty over the same period."
- FIX: Rename to "avg per-call Nifty over same window" or similar; explicitly say this is a
  per-call comparison, not a tradable portfolio curve. Or build a true shared-capital equity curve.

### 4. Per-stock ₹1L chart: the three lines start at different heights
- WHERE: `ipo_detail.py` growth-of-₹1L chart; `growth_of_1l()`.
- WHY: at-listing and Nifty both start at ₹100,000 on day 1; **at-IPO (if allotted) starts at
  ₹129,317** (verified example) because the pop is baked into day-1 value. Visually the green line
  launches from above — easy to misread as "the IPO beat the index from the same start." It also
  silently overclaims: "if allotted" assumes a full ₹1L fill, but median allotment prob is ~3.5%
  (the file's own docstring) — you almost never get ₹1L allotted.
- FIX: Caption already says "won the allotment lottery" but the chart needs a visible day-1 marker
  ("at-IPO starts higher = the listing pop you'd have captured") AND an explicit "assumes full ₹1L
  allotted — unrealistic; see allotment odds." Consider starting all three at ₹100,000 and showing
  the pop as a step, so the head-start is legible rather than implicit.

### 5. Scorecard AVOID/APPLY win-rule ignores the applicant's pop — asymmetrically
- WHERE: `calibration._WIN_RULE`: `AVOID right if alpha<0`, `APPLY right if alpha>0`, on FROM-LISTING
  alpha. The caption admits this. But the consequence is under-stated.
- WHY: from-listing alpha excludes the listing-day pop. For an APPLY call the *applicant* also banks
  the pop, so an APPLY that listed +40% then drifted to from-listing alpha −5% is scored WRONG even
  though the applicant made money. AVOID is scored generously for the same reason. The win-rates are
  therefore biased: APPLY hit-rate understated, AVOID overstated. This is the headline credibility
  table — a sharp user will catch the asymmetry.
- FIX: Grade APPLY on an allottee-inclusive return (issue→horizon incl. pop), or show BOTH grading
  lenses side by side. At minimum the caption must say the direction AND rough magnitude of the bias,
  not "slightly generous / slightly harsh."

## IMPORTANT

### 6. "P(beat Nifty)" reliability buckets pool modes and small n
- WHERE: `score_reliability()` — buckets all APPLY/NEUTRAL/AVOID with a score+alpha by quintile.
- WHY: It pools historical_sim with backfilled/live (the rest of the page is careful never to pool).
  With ~398 graded APPLY/AVOID, 5 buckets ≈ 80/bucket but dominated by sim. Monotonicity here is an
  in-sample/sim property, sold as "the ranking means something."
- FIX: Tag the table "(includes dress-rehearsal calls)" and ideally split sim vs OOS, or restrict to
  backfilled+live once n allows.

### 7. Wipeout = ₹0 endpoint hides the ride; no drawdown anywhere on the money views
- WHERE: `_exit_price` (wipeout→0), `growth_of_1l` (→0 at terminal), portfolio (counts ₹0).
- WHY: Survivorship-honest on the endpoint — good. But both money surfaces show endpoint multiples
  only; a 25x winner that round-tripped through −60%, or a name that sat dead for 3 years, looks
  identical to a smooth ride. The project's own thesis is "the move + the path matters" (MFE/MAE) —
  the money views drop that lens entirely.
- FIX: Add a max-drawdown / time-underwater chip to the per-stock chart (data is in the price file),
  and a "worst intra-hold drawdown" stat to the portfolio table. At least caption: "endpoint only —
  the ride was bumpier."

### 8. Wipeout terminal date / Nifty anchor for stale delisted names
- WHERE: `_exit_price` returns terminal date; Nifty anchored to it (good P0 fix). But a delisted
  name's "terminal" can be years stale, and the per-call windows differ wildly (1 call held 6 years,
  another 6 months) yet are summed equally into one multiple.
- FIX: Show the basket's holding-period dispersion (median/range of hold length) so "2.09x" isn't
  read as a fixed-horizon return.

## NIT
- 9. Portfolio table "₹1L → now" = value_now/n is the mean ending value, restating the mean multiple;
  redundant with the multiple column and reinforces the mean-not-median read.
- 10. `win %` uses `>CAPITAL` (nominal), not vs-Nifty — "win" silently means "beat ₹0 return," not
  "beat the index," next to a "vs Nifty" column. Easy to conflate. Label it "% above cost."
- 11. growth_of_1l needs only `len(pr)>=5` rows — a name with 5 days of data draws a confident-looking
  line. Add a min-history guard or a "thin history" caption.

## The single biggest "looks better than it is" risk
**The ₹1L portfolio "2.09x / 2.85x vs 1.27x Nifty" headline.** It is (a) ~94% simulated calls that
were never actually followed, (b) a skew-mean carried by a few outliers while the median followed
call returned ~18%, (c) a per-call benchmark dressed as a portfolio-vs-index curve, and (d) endpoint-
only with no drawdown. Each flaw pushes the same direction — up. A sharp user who pokes any one of
them (mode mix, median, "is this a real curve?", the ride) loses trust in the whole track-record
surface. Fix order: demote/segregate historical_sim, lead with median+win-rate, rename the Nifty
column to "per-call," add a drawdown stat.
