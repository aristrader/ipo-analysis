# Two-sided miss-mining of recent-cohort IPO calls (B1) — 2026-06-09

Task B1 (`improvement_backlog.md` Theme B). Extends the OOS forward test from bucket-aggregates to a
**per-IPO grade**, then mines BOTH error types of our genuine, point-in-time APPLY/NEUTRAL/AVOID calls.
Script: `tools/research/miss_mining.py` · grades: `data/master/review/miss_mining_grades.csv`.

## READ THIS FIRST — honest caveats (the cohort is YOUNG)
- **Cohort = 364 IPOs listed in the last ~12 months** (2025-06-07 → 2026-06-06; SME 257, MB 107),
  equity only, `unreliable_coverage` listing rows dropped. They are **0–~12 months old**.
- **This is an EARLY READ.** "Winner/loser" here is judged on the realized-to-date outcome
  (`current_return_from_issue` + `outcome_class` + path), NOT a matured 1y/3y verdict. A name that is
  "+50% so far" could still round-trip; a "−40% so far" could recover. **No 1y/3y verdicts are claimed.**
- **Point-in-time honest:** each IPO's analog pool = ONLY IPOs that listed STRICTLY BEFORE it
  (`df._ld < r._ld`); data-informed weights derived on prior-only data, refreshed per listing-month.
  The target and all later IPOs are invisible to its own call. (Weights barely drift across the span —
  the prior pool is ~2,000 matured IPOs — so per-month derivation is honest and ~30× cheaper than per-IPO.)
- **Survivorship-honest:** delisted kept; wipeout terminal = −100%. (0 wipeouts have surfaced in this
  young cohort yet — wipeouts take years; absence here is youth, not safety.)
- **Method match to `calls.py`:** APPLY = top-segment-quintile AND 0 flags · AVOID = bottom-quintile OR
  ≥2 flags · else NEUTRAL. Quintiles are computed PER SEGMENT (MB/SME) from each month's prior-only
  scored pool, exactly as `calls.py:add_quintiles` does. Verified reproduces the Fujiyama/Park grade
  (Park: score ~65, q5, 1 obscure-banker flag → NEUTRAL; Fujiyama: APPLY).

## THE CONFUSION MATRIX (N=364; 27 rows are "flat & not-applied" = neither error nor a scored hit)
| | called APPLY | called NEUTRAL / AVOID |
|---|---|---|
| **winner** (outcome winner/multibagger OR allottee >+25%) | **TRUE POS = 68** | **FALSE NEG = 52** (missed winners) |
| **loser** (loser/wipeout OR allottee <−15% OR ended-down w/ deep DD) | **FALSE POS = 59** (capital loss) | **TRUE NEG = 158** |

- Call counts: **APPLY 154 · NEUTRAL 193 · AVOID 17.**
- **APPLY hit-rate (won) = 68/154 = 44.2%** (Wilson95 36.5–52.0%). APPLY allottee **median +7.0%, mean
  +28.6%, P10/P90 −50/+97%, 0 wipeouts.**
- **Does the call system add value over do-nothing? YES, even this early.** Whole-cohort allottee median
  = **−5.1%**; APPLY median **+7.0%** / mean **+28.6%**; NEUTRAL median **−11.9%**; AVOID median **−11.0%**.
  APPLY sorts clearly above NEUTRAL/AVOID — the ranking works; the errors below are the residual to fix.
- **FALSE NEG total regret ≈ ₹3.82M** per ₹1L-each (52 missed winners, allottee median **+50%**, P90 +154%).
- **FALSE POS total loss ≈ −₹2.18M** per ₹1L-each (59 losers we APPLY'd, allottee median **−36%**, P10 −60%).

> Both error piles are real and roughly comparable in ₹. Per the downside-first ethos the **FALSE-POS side
> is the priority** (it's actual capital lost, not foregone upside), but the FALSE-NEG side has the single
> cleanest, cheapest fix (the banker flag) — so we seed both.

---

## FALSE POSITIVES — the losers we APPLY'd (downside-first; the capital-loss side). N=59
Ranked shared traits (all with N stated):
1. **A PURE BLIND SPOT — every single FALSE_POS carried 0 wipeout flags** (flag load: `{'-': 59}`). None of
   the three validated flags (tiny-sales / loss-making / obscure-banker) fired on a single loser we APPLY'd.
   Whatever sank them, our flag set does not see it.
2. **WEAK DEMAND was the missed tell.** Subscription (sub_total_x) median **2.2× for FALSE_POS vs 6.6× for
   TRUE_POS** — a clean separation. **32 of 58 FALSE_POS with sub data were subscribed < 3×.** We APPLY'd
   them anyway because the *cohort-analog* components (return/multibagger/downside) scored them top-quintile
   on look-alike past IPOs, while the IPO's OWN tepid demand was not a score input or a flag.
   - Caveat: GMP did NOT separate (FALSE_POS median 13.5% vs TRUE_POS 11.2% — basically equal). Demand
     *subscription*, not GMP, is the discriminator here. (Consistent with the rejected-GMP-as-flag history.)
3. **Smaller issues skew worse.** Issue size median **₹63cr (FALSE_POS) vs ₹83.5cr (TRUE_POS)**; 24/59 were
   <₹50cr. SME dominates the damage: **FALSE_POS SME n=37, allottee median −48%, ≈−₹1.58M;** MB n=22, median
   −28%, ≈−₹0.60M. The deep-loss tail is an SME/small-issue phenomenon.
4. **Sector tilt (thin, hint-only):** Industrials 8, Consumer-Discretionary 4, Commodities 3, FMCG 3,
   Services 3. No single sector dominates; treat as context, not a rule (each cell < MIN_N).

**What SHOULD have fired and didn't:** a *low-subscription* guard (sub_total_x < ~3× on the IPO's own
demand) and/or a small-SME-issue caution. Both are point-in-time, prospectus/close-date readable, and
backtestable. This is the FALSE-POS seed (Theme-A new guard — see below).

---

## FALSE NEGATIVES — the winners we waved off (the Park family). N=52
- 52 missed winners (49 called NEUTRAL, 3 AVOID), allottee **median +50%, P90 +154%**; SME 42 / MB 10.
- **Flag breakdown of the 52:** `obscure lead manager` ALONE = **34**; no-flag (knocked below top-quintile
  on score, not by a flag) = 10; `tiny pre-IPO sales` = 4; `loss-making at IPO` = 2; tiny-sales+obscure = 2.
- So **the obscure-banker flag is the dominant single cause of missed winners** (34 of 52 = 65%). The
  10 no-flag misses were simply not top-quintile (their cohort-analog score landed q2–q4) — that's the
  score being conservative, not a broken veto; harder to "fix" without loosening the APPLY bar.

### THE OBSCURE-BANKER FALSE-NEGATIVE HYPOTHESIS — **CONFIRMED (systematic, and partly a pure artifact)**
The flag fires when a banker has < 12 IPOs *in our data window*. Findings on the 34 obscure-only misses:
- **17 of 34 were TOP-QUINTILE** — i.e. the obscure-banker flag was the **SOLE blocker**; remove/repair it
  and they flip straight to **APPLY**. **Recoverable regret ≈ ₹0.93M per ₹1L-each** (these 17 alone),
  allottee median **+37.8%**. Includes Park Medi (Nuvama, +74%), Sambhv Steel & Anand Rathi & KSH (all
  Nuvama, +29/+27/+113%), Samay & BharatRohan (Smart Horizon, 25 IPOs!, +24/+44%), LG Electronics India
  (Morgan Stanley, +32%), Influx Healthtech (+149%), Sai Parenteral (Arihant, +39%).
- **12 of 34 bankers have ≥10 IPOs in the FULL data — NOT obscure by any reasonable definition**, flagged
  purely because they sat just under the 12-in-our-window cutoff (Nuvama 12, Motilal Oswal Inv. 15, Smart
  Horizon 25, Choice 13, Indorient 13, Prime Cable's Indorient 13, etc.). These are **pure data-coverage
  artifacts** — the flag measured "under-represented in OUR window," not "low quality." Nuvama (ex-Edelweiss)
  and Morgan Stanley being tagged "obscure" is the proof.
- **BUT the flag is not purely wrong:** the median banker_total of the 34 is only **7**, and ~22 of them are
  genuinely small bankers. The problem is the flag is **frequency-based and quality-blind** — it lumps
  "reputable but under-counted" together with "genuinely tiny shop," and in a hot SME tape *both* cohorts
  ran. The fix is not "delete the flag" but "make it quality/size-aware."

**Verdict on the hypothesis:** the obscure-banker flag **systematically causes missed winners** — it is the
single largest false-negative driver (65% of misses), ≥1/3 of which are pure coverage artifacts on
reputable banks, and 17 are one flag away from being correct APPLYs worth ~₹0.93M/₹1L. This is exactly the
Park/Nuvama pattern, now shown to be a *recurring* class, not a one-off. **Confirmed.**

---

## FIXES THIS SEEDS (patterns → backlog items)
1. **A1 (banker-flag fix) — STRONGLY CONFIRMED, do-first.** Replace the frequency-in-our-window rule with a
   **size/recognition-aware** rule (don't fire on large MB; and/or whitelist by total-IPO-count ≥ ~10 as a
   reputability floor) OR a banker **listing-performance quality** measure. Evidence: 34/52 misses, 17
   top-quintile flips, ₹0.93M recoverable, 12 reputable banks mis-tagged. Bar: must improve OOS top-quintile
   lift robustly across splits (evolve-only-if-robust), else display-only. Touches `scorecard.py`
   (`wipeout_flags`, `_query_flag_series`), `rules/index.md`.
2. **NEW FALSE-POS GUARD — low-subscription / small-SME-issue caution (downside-first, the higher-value
   half).** The 59 capital-losers were a flag blind spot with a clean tell: own-IPO subscription median 2.2×
   vs 6.6× for winners; 32/58 were < 3× subscribed; SME small issues took the −48% median hit. Propose a
   *display-first* low-demand red flag (sub_total_x < ~3×) and re-test whether folding a demand-veto into the
   APPLY gate (not the score) cuts FALSE_POS without gutting TRUE_POS. **Caveat:** first-order demand screens
   are mostly dead in `rules/index.md` (undersubscribed→bad is known); the NEW angle is *conditional* — weak
   demand AMONG names the analog-score rates top-quintile (the disagreement is the signal). Frame as a
   second-order interaction and run the full 3-layer + placebo before any veto. Touches `scorecard.py`,
   a new finding, `rules/index.md`.
3. **A2 (post-listing conviction overlay) — supported, not actioned here.** 10 of 52 misses were no-flag,
   just-below-top-quintile names that ran post-listing (the drift our one-shot call can't catch). Reinforces
   the case for a hold/strength overlay, but this analysis doesn't add new evidence beyond the count.

## Honesty flags for the controller to double-check
- **Young-cohort labels are provisional.** "Winner"/"loser" use realized-to-date returns; a re-run as the
  cohort matures (the script is repeatable) is the real test. The ₹ figures are per-₹1L *paper* outcomes at
  the current data window, not closed trades.
- **Quintile method choice:** I used PER-SEGMENT prior-pool quintiles (matching `calls.py`), derived from the
  combined-score distribution of each month's prior scored frame. This is the defensible PIT analogue of
  `add_quintiles`; a pooled-calibration quintile (as `predict.py`'s readout uses) would shift a few borderline
  q4/q5 boundary cases. The headline patterns are robust to this; the exact 17-flip count could move ±2 under
  the alternate quintile definition.
- **The "17 would flip to APPLY" is a counterfactual** assuming ONLY the obscure-banker flag is removed and
  nothing else changes; it does not re-derive weights without the flag. Treat ₹0.93M as an upper-ish bound on
  the *clean* recoverable regret, not a guaranteed gain.
- **`current_return_from_issue` mixes horizons** (each IPO is a different age). The per-horizon columns
  (1m/3m/6m) are in the CSV for a cleaner age-matched re-cut if wanted.

## Reproduce
`PYTHONPATH=. python tools/research/miss_mining.py` (reads substrate + forward_test/predictor/weights
machinery; restores the committed `scorecard_weights.json` afterward; writes the grades CSV + prints the
confusion matrix and both pattern sections). ~15 min (13 monthly weight derivations + 364 PIT predicts).
