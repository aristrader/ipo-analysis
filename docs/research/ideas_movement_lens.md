# Movement-lens idea catalog — reframe everything around the MOVE and the LIKELIHOOD

> Status: PROPOSAL (no code written). Date 2026-06-01.
> Lens (user's philosophy): *"in markets you can't rely on a single-date data point — capture the
> MOVEMENT and the LIKELIHOOD of patterns repeating."* We now have, per horizon and per ENTRY
> (issue=allottee / listing=secondary buyer): within-horizon peak/trough **MFE/MAE**
> (`mfe_1y/3y/5y`, `mae_1y/3y/5y`, `mfe_lst_*`, `mae_lst_*`), the spine **reach-curve**
> (P(touched +X% / fell to −X%)), and the spine **exit-strategy** take-profit ladder. Almost every
> existing finding/score/strategy is built on a *single endpoint* (`alpha_h` / `return_from_listing_h`).
> This doc says which to REFRAME and which NEW rules to add, in this paradigm.

## The hard honesty constraints (apply to EVERY item below — repeated so they don't get lost)
1. **MFE/MAE give the magnitude of the peak/trough but NOT its date or order.** So any *combined*
   take-profit **+** stop-loss rule is order-ambiguous (did it hit +50% before or after −30%?). We can
   bound it (best-case / worst-case ordering) but cannot resolve it. Flag this on every TP+SL item.
2. **No time-to-peak / date-of-MFE columns exist.** We only have `max_drawdown_duration_days` (the
   all-time, lifetime, not-entry-anchored, not-horizon-scoped max-DD duration). So *time-to-peak*,
   *trailing stops*, and *"how long until the exit appeared"* are **NOT computable now** — they need a
   new pipeline pass over `data/prices/<isin>.csv` to emit per-horizon `days_to_mfe_*` / `days_to_mae_*`.
   Items needing this are marked **(needs new column)** and default to MAYBE/SKIP, not BUILD.
3. **Reaching a level = opportunity, not capture.** A reach-curve says "the move was *available*";
   booking it needs timing you didn't model. Always pair reach with the buy-and-hold endpoint (the
   spine already does this) so the gap between "available" and "captured" is visible.
4. **Method-spine still binds:** hard SME/MB split, maturity-gating, min-N floors (N≥30 tradable /
   N≥10 directional), distributions over means, Wilson/bootstrap CIs, competing-risks wipeout band,
   exclude `unreliable_coverage` listing rows for any listing-anchored cut.
5. **Cross-regime / OOS honesty unchanged:** long horizons (3y/5y) are longterm-cohort-carried; boom
   5y is early-survivor-biased. A movement finding is a hypothesis until its *sign* holds in both
   cohorts (and ideally within-vintage). Subscription/GMP-conditioned cuts are boom-only → single-regime.
6. **Entry split is mandatory, not optional.** Allottee (from issue, gets the pop) and secondary buyer
   (from listing) get *different* MFE/MAE and therefore different reach/exit answers. Report both.

---

## TOP 5 BUILD PICKS (highest value: the reframes + new rules that change a decision)

| # | id | what it is | why it's top-5 |
|---|---|---|---|
| 1 | `mv-stoploss-base` | **Stop-loss base-rate study** via MAE: of names that fell to −X% within a horizon, what share *ended above issue / above that level / went on to 2x*? Tests the user's own hypothesis: given ~96% eventually trade above issue, does cutting at −X% protect you or stop you out of recoverers? | Directly answers a question the endpoint findings *can't*: the cost of a stop. Pure MAE→endpoint, fully computable, decision-critical, novel. |
| 2 | `mv-T3-reach` | **Reframe T3 pop-fade as reach-curves by pop bucket** (secondary entry): not just "median fwd return fades" but P(secondary buyer ever +20/50/100%) and P(ever −20/30/50%) per listing-pop bucket. | T3 is a Tier-1 anchor but its within-vintage robustness was DOWNGRADED; the movement view (does the upside *opportunity* survive even when the endpoint fades?) is a stronger, more honest restatement. |
| 3 | `mv-multibagger-ever` | **Reframe `multibagger_odds` + T1 "%2x" to P(EVER 2x/5x within horizon)** using MFE, not endpoint-2x — alongside the endpoint version, with the capture gap shown. | The scorecard's multibagger component currently undercounts: a stock that touched 3x then settled at 1.4x scores as "not a 2x." P(ever 2x) is the truer "upside was on the table" number; pairing the two *is* the insight. |
| 4 | `mv-tradeable-upside` | **New scorecard component: "tradeable upside" = P(analog cohort reached +X%)** within the score horizon, entry-split, paired with capture-gap honesty. | Adds the movement lens to the predictor itself (currently 5 endpoint/quality components). A high-reach / low-endpoint cohort is exactly the "trader's IPO" the current score is blind to. |
| 5 | `mv-exit-backtest` | **Exit-discipline backtest: take-profit ladder vs buy-and-hold** (per segment × cohort × entry), using `spine.exit_strategy`; report median captured & win-rate vs the do-nothing/secondary-hold baseline. Bounded SL overlay shown as a best/worst-order *band* (constraint #1), not a point. | Closes the loop: the spine has `exit_strategy` but no backtest *uses* it. Given secondary-hold LOSES cross-regime, "does a +T exit rule beat holding?" is the natural, high-value next strategy. |

---

## FULL CATALOG

### A. REFRAMES of existing findings/predicates/components/strategies

| id | reframe of | what it answers (movement version) | columns | computable now? | robustness / guardrails | effort | verdict |
|---|---|---|---|---|---|---|---|
| `mv-T3-reach` | T3 pop-fade (`findings/t3_pop_fade`) | Per listing-pop bucket, the secondary buyer's **reach-curve**: P(ever +20/50/100%) and P(ever fell −20/30/50%) within 1y/3y, plus the endpoint already there. Does the *opportunity* fade as hard as the endpoint, or do hot IPOs stay volatile-both-ways? | `mfe_lst_*`, `mae_lst_*`, `adj_listing_gain_open`, `return_from_listing_*` | **Yes** (`spine.reach_curve(b, h, entry="listing")` per bucket) | T3 sign holds x-regime but within-vintage WEAK → frame as descriptive, not a signal. SME pop buckets are barbell/manipulation-prone → directional only. Exclude `unreliable_coverage`. Min-N per bucket. | M | **BUILD** |
| `mv-multibagger-ever` | `scorecard.multibagger_odds` + T1 `%2x_from_issue` | P(cohort **ever touched** 2x/5x within horizon) via MFE vs endpoint-2x, both shown + the capture gap. Truer "multibagger odds" = the upside was reachable. | `mfe_*` (issue), `mfe_lst_*` (listing), existing `return_from_issue/listing_*` | **Yes** | Reaching ≠ capturing (constraint #3) — must show both numbers side by side or it overstates. Entry-split. Maturity-gated. Keep endpoint version too (don't silently swap). | S | **BUILD** |
| `mv-T1-exitdisc` | T1 base rates (`findings/t1_base_rates`) | Add an **exit-discipline base-rate block** to the anchor: per segment×cohort×entry, the `exit_strategy` ladder (break-even / +20 / +50% TP) — % that ever gave a ≥break-even exit, median captured vs hold-to-endpoint. | `mfe_*`/`mfe_lst_*`, `return_from_*` | **Yes** (`spine.exit_strategy`) | "You'd have to time the exit" honesty banner. Long-horizon = longterm cohort. The "% ever ≥ break-even" is the headline (ties to the ~96%-eventually-above-issue claim — verify the exact rate per segment, don't assume). | S | **BUILD** |
| `mv-T8-recovery` | T8 drawdown-tax (`findings/t8_drawdown`) | Flip T8's framing: among names that hit a deep MAE (−50/−70%) **early**, what share **recovered** to break-even / +X% by the horizon end? (recovery-curve, the optimist's mirror of the pain map). | `mae_*`, `mfe_*`, `return_from_issue_*` | **Yes** (magnitude). Recovery *timing* / "how long underwater" = **needs new column** (#2). | T8 uses lifetime `outcome_class` (winner-defined) — the recovery version must be maturity-gated & forward (no winner look-ahead). Investable subset to strip thin-trade DD. | M | **BUILD** (magnitude) / SKIP timing until column exists |
| `mv-return-potential-reach` | `scorecard.return_potential` | Supplement the median-alpha component with the cohort's **median MFE** (typical peak reached) and median MAE (typical trough) as displayed context — not a new weighted score, a richer display so the score isn't a single endpoint. | `mfe_*`, `mae_*` | **Yes** | Display-only (don't double-count into the weighted blend). Entry-split. | S | **MAYBE** (nice display; low decision-impact) |
| `mv-holdingsweep-reach` | `strat-holding-sweep` (`backtest/analyses.holding_period_sweep`) | The sweep shows secondary alpha worsens monotonically with horizon. Add: at each horizon, P(ever positive) / median MFE — i.e. was the *opportunity* there even though the endpoint decayed? Reframes "sooner is better" as "the move was early, the decay is the holder's tax." | `mfe_lst_*`, `mae_lst_*` | **Yes** | Same monotonic-honesty; pair reach with endpoint. Min-N per horizon. | S | **MAYBE** |
| `mv-avoidhot-reach` | `strat-secondary-avoid-hot` | Re-express the "skip >25% pop" filter in reach terms: does skipping hot IPOs change P(reach +X%) or just the endpoint? (avoid-hot showed no endpoint improvement — does it change the *opportunity set*?) | `mfe_lst_*`, `adj_listing_gain_open` | **Yes** | avoid-hot already "loses cross-regime"; this is diagnostic, not a new signal. Low priority. | S | **SKIP** (subsumed by `mv-T3-reach`) |
| `mv-downside-mae` | `scorecard.downside_safety` | Currently uses lifetime `max_drawdown_pct` + endpoint below-issue. Reframe the deep-drawdown term to **entry-anchored, horizon-scoped MAE** (P(cohort fell to −50% from the *buyer's* entry within the score horizon)) instead of the lifetime peak-to-trough DD. | `mae_*` / `mae_lst_*` | **Yes** | More honest than lifetime DD (which can be post-entry irrelevant). Keep wipeout band term. Entry-split → the allottee and secondary buyer get different safety reads. | M | **BUILD** (folds into #4's family; do together) |

### B. NEW rules / findings / predictions in the movement paradigm

| id | what it is & answers | columns | computable now? | robustness / guardrails | effort | verdict |
|---|---|---|---|---|---|---|
| `mv-stoploss-base` | **Stop-loss base rates.** Of cohort names whose MAE ≤ −X% (X∈{20,30,50}) within horizon h, what % (a) ended above the buyer's entry, (b) ended above −X% (i.e. the stop saved you), (c) went on to a higher MFE later? Quantifies cut-losses-vs-hold *given* ~96% eventually trade above issue. Entry-split. | `mae_*`/`mae_lst_*`, `mfe_*`, `return_from_issue/listing_*` | **Yes for the magnitude/whether-recovered question.** Whether the stop *would have triggered before* the recovery = order-ambiguous → can only bound (constraint #1). | THE flagship honesty case: state plainly we can't see if −X% came before or after the peak; report it as "of names that *touched* −X%, this share *also* ended up / *also* touched +Y% — so a stop *might* have cut them" with best/worst bounds. SME/MB split; maturity-gate; min-N. Verify the "~96% above issue" rate per segment first. | M | **BUILD** |
| `mv-exit-backtest` | **Exit-discipline backtest** (Part C strategy): take-profit ladder (exit at +T if MFE≥T else hold to endpoint) vs buy-and-hold secondary, per segment×cohort×entry, net of cost, vs do-nothing baseline. Adds an SL overlay as a **best-case/worst-case band** only. | `mfe_*`/`mfe_lst_*`, `return_from_*`, `alpha_*` | **Yes** for TP (spine.exit_strategy is exactly this). TP+SL combined only as a *band*. | Cross-regime verdict like other strats ('beats' only if median > 0 in BOTH cohorts). Cost drag (`COST_SECONDARY`). The capture is upper-bound optimistic (assumes you exit exactly at T the instant it's touched). Flag order-ambiguity on the SL band. | M | **BUILD** |
| `mv-tradeable-upside` | **New scorecard component "tradeable upside" = P(analog cohort reached +X% within score horizon)**, entry-split, scaled 0–100, displayed with the capture gap (median endpoint) so it's never read as guaranteed. | `mfe_*`/`mfe_lst_*` | **Yes** | Must show the capture gap or it inflates expectations (#3). Sub-floor → None (insufficient analogs), like other components. Decide weight via the existing data-informed cross-regime rank-IC machinery (`weights.py`) — don't hand-weight; it may earn 0 like liquidity/quality did. | M | **BUILD** |
| `mv-ever-gave-exit` | **"Did it ever give an exit" base rate** + (the honest subset of) time. Per segment×cohort×entry: % of names whose MFE ever ≥ break-even / ≥ +20%. The "you had a chance to get out flat" rate. | `mfe_*`/`mfe_lst_*` | **Yes** for the rate (it's `exit_strategy.pct_ever_gave_an_exit`). **Time-to-that-exit = needs new column** (#2). | Largely overlaps `mv-T1-exitdisc` — fold in there rather than a standalone finding. Time component deferred. | S | **MAYBE** (merge into `mv-T1-exitdisc`) |
| `mv-time-to-peak` | **Time-to-peak / lifecycle curve** (Tier-2 "when does the avg IPO peak?"): days from entry to MFE, distribution by segment/cohort. | needs `days_to_mfe_*` per horizon×entry | **NO — needs new pipeline column** (#2; `max_drawdown_duration_days` is lifetime DD only, not time-to-peak). | Cohort-constant to avoid horizon-mix; SME thin-trade peaks are noisy. Genuinely useful (informs exit timing) but blocked on data. | L (pipeline pass over `data/prices/`) | **MAYBE** (BUILD only if a prices re-pass is already planned) |
| `mv-trailing-stop` | **Trailing-stop approximation** (give back X% from peak then exit). | needs the *path* or at least `days_to_mfe` + post-peak trough | **NO — not derivable from MFE/MAE** (we have peak & trough magnitudes but not "trough *after* the peak"). | Would require a real per-day path pass. High fake-precision risk if approximated from MFE/MAE. | L | **SKIP** (until a path-level layer exists; honestly out of scope) |
| `mv-reach-by-feature` | **Reach-curves conditioned on a pre-listing feature**: e.g. high-OFS vs low-OFS → P(reach +X%) and P(fall −X%); same for issue-size band, profitable-at-IPO, debt tertile. "Does insider-exit / size / quality change the *shape* of the move, not just the endpoint?" | `mfe_*`/`mae_*` × `ofs_pct`, `issue_size_cr`, `pre_ipo_pat`, `pre_ipo_debt_equity` | **Yes** | Inherit each parent finding's regime verdict: OFS is MIXED x-regime (don't sell as a signal), profitable-at-IPO MIXED, debt-flag holds. So this is *descriptive texture* on validated/mixed findings, not new signals. Min-N per cell shatters fast → keep to 2–3 buckets. | M | **MAYBE** (do OFS + debt only, as texture on the strongest parents) |
| `mv-reach-by-subscription` | Reach-curves by subscription / QIB-skew tertile (does hot demand → higher reach for the secondary buyer, even if endpoint fades?). | `mfe_lst_*`, `sub_total_x`, QIB/retail ratio | **Yes** but **boom-only** (longterm subscription ≈ 0). | Single-regime → cannot cross-validate (same limit as n2/n3). Exploratory only. | M | **MAYBE** |
| `mv-allottee-vs-secondary-reach` | **Entry-split reach wedge made first-class**: side-by-side allottee (`mfe_*`) vs secondary (`mfe_lst_*`) reach-curves for the same cohorts — quantifies how much of the "upside opportunity" is just the listing pop the secondary buyer never gets. | `mfe_*` vs `mfe_lst_*`, `mae_*` vs `mae_lst_*` | **Yes** | This is the cleanest expression of the user's entry-split philosophy; low risk (descriptive). Could live inside `mv-T1-exitdisc` or `mv-T3-reach` rather than standalone. | S | **BUILD** (as a shared sub-view) |
| `mv-dd-then-recover-feature` | Among deep-MAE names, does a pre-listing feature (profitable / low-debt) predict *recovery* (`mv-stoploss-base` conditioned)? "Is a quality name's −50% more survivable?" | `mae_*`, `mfe_*`, `return_from_*`, `pre_ipo_*` | **Yes** (magnitude) | Cells get small fast; debt-flag is the one validated quality lever → restrict to that. Maturity-gate. | M | **MAYBE** |

---

## Build sequencing (if approved)
1. **Reframe family first (shared plumbing):** `mv-multibagger-ever`, `mv-T1-exitdisc`(+`mv-allottee-vs-secondary-reach`, `mv-ever-gave-exit`), `mv-T3-reach` — all reuse `spine.reach_curve`/`exit_strategy`, no new columns, highest value-per-effort.
2. **New downside studies:** `mv-stoploss-base` (+ `mv-downside-mae` folded into the scorecard).
3. **Predictor + backtest:** `mv-tradeable-upside` (component, then run through `weights.py` for an honest cross-regime weight), `mv-exit-backtest`.
4. **Texture (optional):** `mv-reach-by-feature` (OFS + debt), `mv-T8-recovery` magnitude.
5. **Blocked on a new prices pass (defer):** `mv-time-to-peak`, recovery-timing, `mv-trailing-stop`.

## What this does NOT add (deliberately, no padding)
- No new GMP-conditioned reach (GMP stays quarantined from scores — spine rule §7).
- No SME day-1 microstructure reach (manipulation artifacts — strategies.md SKIP list).
- No combined TP+SL as a *point* estimate anywhere (order-ambiguous; band-only or not at all).
- No time-to-peak / trailing-stop claims off MFE/MAE (we'd be inventing the path we don't have).
