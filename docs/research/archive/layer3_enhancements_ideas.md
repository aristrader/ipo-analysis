# Layer 3 — Enhancement & New-Idea Proposal (research, no code)

> Purpose: propose **additional high-value, robust** metrics/findings/predicates/strategies beyond the
> locked T1–T9 + the predictor/backtester design, and sharpen the 8 planned findings. Everything here is
> checked against the **actual columns** in `data/master/ipo_analysis.csv` and the **FEATURE COVERAGE MAP**
> in `TODO.md`. Method-spine rules (maturity-gate, SME/MB split, alpha, min-N, survivorship-honest,
> liquidity, cross-regime, provenance) apply to every item and are not repeated each time.
>
> Confidence legend: **A** = robust/hard-to-fake, official-data-backed, decision-relevant; **B** = useful but
> coverage- or noise-limited; **C** = exploratory / narrative only.
>
> Author note (date 2026-05-31): two underused but clean column families make several of these cheap:
> (1) **`return_from_listing_*` already exists** — T3 and any "secondary-buyer" view need NOT approximate
> from issue-anchored alpha; we can compute true from-listing forward return directly and difference it
> against `return_from_issue_*` to get the allottee-vs-buyer wedge. (2) The **3-year financial trajectory**
> (`net_sales_yr1-3`, `pat_yr1-3`, `operating_profit_yr1-3`, `operating_cf_yr1-3`) supports pre-IPO growth,
> margin-trend, and cash-vs-accrual quality cuts that today's plan does not touch.

---

## 1. NEW DESCRIPTIVE FINDINGS (beyond T1–T9)

### N1 — Allottee-vs-secondary-buyer wedge (the "who actually won" map)  **[A]**
- **Metric:** for each segment×cohort×listing-pop bucket, median `return_from_issue_Hy` minus median
  `return_from_listing_Hy` at H ∈ {1y,3y,5y}. This is the realized gap between an allottee (got it at issue)
  and someone who bought at listing open/close. Pair with `adj_listing_gain_open` so the listing pop and the
  subsequent wedge sit in one table.
- **Columns:** `return_from_issue_{1y,3y,5y}`, `return_from_listing_{1y,3y,5y}`, `adj_listing_gain_open`,
  `listing_metrics_status`, `type`, `cohort`. All present; from-listing returns 100%+ coverage where price exists.
- **Decision value:** the single most actionable framing of the whole tool — "should I chase on listing day, or
  is the gain already in the allottee's pocket?" Directly informs the predictor's entry-conditioned stances.
- **Guardrails:** exclude `unreliable_coverage`; maturity-gate per horizon; MB/SME split; min-N≥30 per bucket;
  liquidity-gate the from-listing leg (a listing buyer needs real liquidity).
- **Priority:** HIGH. This is an enhancement-grade superset of T3 — recommend folding into T3 (see §2).

### N2 — Subscription-vs-outcome curve, with saturation/reversal test  **[A, boom-mainly]**
- **Metric:** bucket `sub_total_x` (and separately `sub_qib_x`, `sub_retail_x`) into bands
  (<1x undersubscribed, 1–5, 5–15, 15–50, 50–100, >100x). Per band: median `adj_listing_gain_open`, median
  `alpha_1y`/`alpha_3y`, % below-issue (`current_return_from_issue<0`), % wipeout. The key question is **shape**:
  does alpha rise monotonically with demand, or does it **peak then mean-revert** at extreme oversubscription
  (the "everyone piled in → priced for perfection → fades" hypothesis)?
- **Columns:** `sub_total_x`/`sub_qib_x`/`sub_retail_x` (boom-MB 93%, boom-SME 76–84%, **longterm ~0–18%**),
  alpha_*, `adj_listing_gain_open`, `current_return_from_issue`.
- **Decision value:** subscription is **official, hard-to-fake** (unlike GMP) and is the headline number every
  retail investor sees. A documented saturation point ("above ~Nx, more subscription stops predicting and starts
  hurting forward alpha") is a genuinely tradable, defensible truth.
- **Guardrails:** **single-regime (boom only)** — explicitly flag it cannot be cross-regime validated (longterm
  subscription coverage ≈0). Listing-gain leg vs forward-alpha leg told apart. MB/SME split. Min-N≥30/band.
- **Priority:** HIGH (descriptive) — but mark "boom-cohort rule, not regime-validated."

### N3 — QIB/Retail demand-skew ("smart vs dumb money")  **[A→B, boom-mainly]**
- **Metric:** ratio `sub_qib_x / sub_retail_x` (and QIB share of `sub_total_x`). Tertile it. Per tertile:
  forward alpha 1y/3y, wipeout rate, % below-issue. Hypothesis: QIB-led demand (institutions) → better forward
  outcomes than retail-led froth.
- **Columns:** `sub_qib_x`, `sub_retail_x`, `sub_nii_x` (boom only), alpha_*.
- **Decision value:** separates institutional conviction from retail FOMO; both are official.
- **Guardrails:** boom-only; need all three sub legs non-null (intersection coverage drops — show N honestly);
  MB/SME split; the ratio is undefined when retail≈0 → handle as its own bucket.
- **Priority:** MED-HIGH. Already seeded as `pred-demand-skew`; this is its descriptive backbone.

### N4 — Issue-size / market-cap "Goldilocks" curve  **[A]**
- **Metric:** bucket `issue_size_cr` (log bands) and separately `market_cap_class`. Per bucket: median forward
  alpha 1y/3y/5y, multibagger %, wipeout %. Test the classic supply hypothesis (very large issues digest poorly
  short-term) **and** the survival hypothesis (micro/SME tiny issues have far higher wipeout). Show both ends.
- **Columns:** `issue_size_cr` (100% all cohorts), `market_cap_class` (boom-MB only 3% — lean on longterm + SME
  + the planned re-pull), alpha_*, `outcome_class`, terminal_state.
- **Decision value:** size is fully covered and hard-to-fake; the wipeout-by-size gradient is decision-critical
  for downside-safety scoring.
- **Guardrails:** mcap class sparse for boom-MB → use issue_size_cr as the always-available proxy and flag where
  mcap is "unknown"; MB/SME split; maturity-gate the long horizons (rely on longterm).
- **Priority:** HIGH.

### N5 — Anchor-conviction gradient (anchor % of issue)  **[B, boom-MB-mainly]**
- **Metric:** derive `anchor_pct = anchor_allocation_cr / issue_size_cr`. Tertile. Per tertile: forward alpha,
  wipeout %, below-issue %. Hypothesis: heavier anchor participation = stronger institutional pre-commitment =
  better forward outcomes / lower wipeout.
- **Columns:** `anchor_allocation_cr` (boom-MB 97%, boom-SME 46%, longterm sparse), `issue_size_cr` (100%).
- **Decision value:** anchor allocation is disclosed/official (cleaner than GMP), and the **derived ratio** is
  more comparable than the raw ₹-cr. Feeds a "sponsorship" sub-signal in the quality/return components.
- **Guardrails:** boom-MB primary; SME anchor disclosure thin → hint-only; cap anchor_pct at sane bounds
  (data errors); MB/SME split. Single-regime flag.
- **Priority:** MED.

### N6 — Valuation: PE percentile-vs-sector → forward alpha  **[B, boom-only]**
- **Metric:** within each `broad_sector` (boom), rank `pe_ratio` into percentiles; bucket {cheap (bottom tertile),
  mid, expensive (top tertile)}. Per bucket: forward alpha 1y/3y, multibagger %, below-issue %. Test the
  mean-reversion hypothesis (expensive-vs-peers IPOs underperform).
- **Columns:** `pe_ratio` (boom-MB 67%, boom-SME 71%, **longterm 0%**), `broad_sector` (boom near-absent until the
  re-pull lands — this finding is GATED on the sector/mcap recovery noted in TODO).
- **Decision value:** valuation discipline is a core fundamental signal; relative-to-sector is far more robust
  than absolute PE (which is sector-confounded).
- **Guardrails:** **double-gated on coverage** (needs both PE and sector) → likely "hint" tier until the boom
  sector re-pull; boom-only / single-regime; drop loss-makers (negative/NaN PE) into a separate "no-PE" bucket,
  never impute; MB/SME split.
- **Priority:** MED (HIGH after the sector re-pull).

### N7 — Quality tertiles (ROE / margin / debt) vs survival & alpha  **[A→B]**
- **Metric:** three independent tertile cuts — `pre_ipo_roe_pct`, `pre_ipo_pat_margin_pct`,
  `pre_ipo_debt_equity` — each vs forward alpha (1y/3y/5y) and **wipeout rate**. Hypothesis: high-debt /
  low-ROE / thin-margin IPOs die more and trail. The debt one is the most decision-critical (leverage → death).
- **Columns:** `pre_ipo_roe_pct`, `pre_ipo_pat_margin_pct`, `pre_ipo_debt_equity` (boom 90–99%; **longterm
  27–72%** — partial but enough for a directional longterm check), alpha_*, terminal_state.
- **Decision value:** these are the cleanest single-fundamental survival predictors; debt/equity especially is a
  textbook bankruptcy signal and feeds downside-safety + quality components.
- **Guardrails:** RHP-financials provenance caveat (dirtier input — tag reliability, treat as hint where coverage
  is low); MB/SME split; cross-regime where longterm coverage allows (debt/equity ~34–72% is workable for a
  sign-check); winsorize extreme ratios.
- **Priority:** HIGH (this is the **expansion of T9** from a binary into a graded fundamentals panel — see §2).

### N8 — Pre-IPO growth & margin-trend (the 3-year trajectory)  **[B]**
- **Metric:** from `net_sales_yr1-3` and `pat_yr1-3`, compute 2-yr CAGR of sales and PAT and a margin-trend
  (`operating_profit_yr3/net_sales_yr3` vs yr1). Tertile sales-CAGR; per tertile show forward alpha + a
  **mean-reversion test** (do the fastest pre-IPO growers fade hardest post-listing — "growth pulled forward
  into the IPO window?"). Also a cash-quality flag: `operating_cf_yr3 <= 0` while `pat_yr3 > 0` (accrual/paper
  profit) → its forward alpha & wipeout vs clean-cash peers.
- **Columns:** `net_sales_yr1-3`, `pat_yr1-3`, `operating_profit_yr1-3`, `operating_cf_yr1-3` (boom good,
  longterm partial), alpha_*.
- **Decision value:** the accrual/cash-flow divergence flag is a hard-to-fake quality red-flag rarely surfaced;
  the growth mean-reversion test is a known IPO pathology.
- **Guardrails:** EPS NOT used (share-base not comparable — per TODO); use absolute ₹-cr only; provenance caveat;
  require ≥2 years present (`pre_ipo_years_available`); MB/SME split; min-N.
- **Priority:** MED.

### N9 — GMP as DISPLAY-only accuracy diagnostic (quarantined)  **[B, display-only]**
- **Metric:** (a) directional hit-rate — of positive-GMP IPOs, % that `adj_listing_gain_open > 0`; of
  negative/zero-GMP, % that opened down. (b) calibration — bucket `gmp_pct` and plot median realized
  `adj_listing_gain_open` per bucket (does GMP over- or under-predict?). (c) the **failure cell**: positive GMP
  but opened below issue — count + which sectors/segments.
- **Columns:** `gmp_pct` (boom-MB 99%, boom-SME 77%, **longterm 0%**), `adj_listing_gain_open`,
  `listing_metrics_status`.
- **Decision value:** users will look for GMP; this *honestly characterizes* its accuracy and its failure mode
  while keeping it **quarantined from every score** (per design). Showing "GMP is right X% on direction but
  systematically over-states magnitude by Y%" is itself the deliverable.
- **Guardrails:** **DISPLAY ONLY, never enters a score or the predictor distance unless provenance-graded** (it
  isn't); boom-only; exclude `unreliable_coverage`; MB/SME split; label grey-market provenance loudly.
- **Priority:** MED (it's in the original 3a sketch; this sharpens it into accuracy + calibration + failure-cell).

### N10 — Holding-period-to-peak & time-to-wipeout  **[A→B]**
- **Metric:** (a) **time-to-peak**: for eventual winners/multibaggers, days from listing to `all_time_high`
  (need to derive the date of ATH from `data/prices/<isin>.csv`; `all_time_high` value is in the substrate but
  not its date — so this requires a small price-series pass). (b) **time-to-wipeout**: for terminal_state=wipeout,
  days from listing to the −90% crossing (also a price-series pass). Report distributions by MB/SME/mcap.
- **Columns:** substrate has `all_time_high`, `all_time_low`, `max_drawdown_duration_days`; the **dates**
  need the per-ISIN price files (`data/prices/`). `max_drawdown_duration_days` is available NOW as a partial proxy.
- **Decision value:** answers "how long must I hold for the upside, and how fast does the downside arrive?" —
  the temporal companion to T8's magnitude map.
- **Guardrails:** requires a price-series derivation step (flag as a small build add-on); maturity-gate
  (a young IPO's "peak" may not have happened); liquidity-gate SME (peak may be an illiquid print); MB/SME split.
- **Priority:** MED (HIGH narrative value; needs the price-series pass — note the dependency).

### N11 — Wipeout & multibagger sector/size concentration  **[A]**
- **Metric:** of all terminal_state=wipeout names, what share sit in which `broad_sector` / `market_cap_class` /
  `type`? Same for multibaggers. A simple concentration table + Herfindahl-style index. "Death is concentrated in
  micro-SME + sectors X/Y" is a strong downside map.
- **Columns:** terminal_state (derived), `broad_sector`, `market_cap_class`, `type`, `outcome_class`.
- **Decision value:** tells the predictor's downside component **where** the bodies are buried; complements T6
  (which is per-sector rates) with the absolute distribution.
- **Guardrails:** sector coverage caveat (boom gap); show "unknown-sector" share explicitly; MB/SME split.
- **Priority:** MED-HIGH (cheap; pairs with T2/T6).

### N12 — `listing_metrics_status` × outcome (data-quality bias audit)  **[A, infra]**
- **Metric:** cross-tab `listing_metrics_status` {ok, inferred_split, unreliable_coverage, recovered_bhavcopy}
  and `data_quality_tier` against `outcome_class` and median alpha. Question: are the low-quality / unreliable
  rows **systematically** worse/better outcomes? If so, excluding them biases every base rate.
- **Columns:** `listing_metrics_status`, `data_quality_tier`, `outcome_class`, alpha_*. All present.
- **Decision value:** a **self-audit** that protects every other finding — if "unreliable_coverage" rows skew
  toward wipeouts (plausible: dead/illiquid names have bad coverage), then dropping them inflates survivorship.
  This quantifies the bias so it can be disclosed.
- **Guardrails:** none beyond honest reporting; this IS a guardrail finding.
- **Priority:** HIGH (correctness infra, like T7; cheap; protects the whole report).

### N13 — Nifty50-vs-Smallcap250 alpha divergence for small/micro  **[A when SC250 lands]**
- **Metric:** for small/micro mcap (and SME), `alpha_Hy` (vs Nifty50) minus `alpha_sc_Hy` (vs Smallcap250) at
  each horizon. If small-cap "outperformance" largely vanishes vs the right benchmark, the divergence column
  proves it numerically.
- **Columns:** `alpha_*` (present) and `alpha_sc_*` (**NOT yet built per Part-A plan / TODO — Smallcap250 alpha
  deferred**). So: **GATED on the SC250 integration pass.** Until then it's a structured placeholder under T7.
- **Decision value:** the core correctness insight of T7, made quantitative per-horizon.
- **Guardrails:** SC250 only valid 2017+ (benchmark-version policy); maturity-gate; do not present a fake alpha
  break at the 2017/2019 benchmark switch.
- **Priority:** MED now (placeholder), HIGH after SC250 lands. **Coverage limitation: blocked on SC250 build.**

### N14 — Pricing-method & price-band-width cut  **[B/C]**
- **Metric:** `book_built` (and `pricing_method`) split: fixed-price vs book-built listing-gain & forward-alpha
  distributions (fixed-price is heavily SME and historically weaker/illiquid). Plus
  `price_band_width = (issue_price - price_band_low)/price_band_low` as an issuer-uncertainty proxy vs outcome.
- **Columns:** `book_built`, `pricing_method`, `price_band_low`, `issue_price`. Coverage to verify at build
  (band_low present but completeness unknown — check before claiming).
- **Decision value:** modest; mostly re-expresses the SME/MB and quality story. Band-width is a weak signal.
- **Guardrails:** likely collinear with SME → don't double-count; MB/SME split; exploratory tier.
- **Priority:** LOW-MED (exploratory).

### N15 — Promoter dilution (skin-in-the-game) gradient  **[B, sparse]**
- **Metric:** `promoter_post_issue_pct` tertiles, and the **dilution delta**
  (`promoter_pre_issue_pct - promoter_post_issue_pct`) vs forward alpha & wipeout. Hypothesis: heavy dilution /
  low post-issue promoter stake → weaker alignment → worse long-term.
- **Columns:** `promoter_post_issue_pct` (boom 54–63%, **longterm 0%**), `promoter_pre_issue_pct`.
- **Decision value:** classic alignment signal; complements T5's OFS view from the holdings side.
- **Guardrails:** sparse (boom-only, ~54–63%) → hint-tier; fold into T5 as a second lens rather than standalone;
  MB/SME split.
- **Priority:** MED (as a T5 sub-cut — see §2).

---

## 2. ENHANCEMENTS TO THE 8 PLANNED FINDINGS (T1,T2,T3,T5,T6,T7,T8,T9)

- **T1 (base rates):** add **% below-issue today** using `current_return_from_issue<0` as a separate column from
  alpha (an investor cares about nominal "am I underwater" too). Add a **survivors-only vs survivorship-honest
  delta column** (not just two tables) so the survivorship tax is a single visible number per cell. Add a
  `data_quality_tier` breakdown row so readers see how much of each cell is `low` quality.

- **T2 (competing-risks survival):** add a **third competing outcome — "languishing/zombie"** (alive but
  `current_return_from_issue` deeply negative, e.g. < −50%, and `liquidity_flag=='low'`): not delisted but
  effectively dead money. The binary alive/wipeout hides these. Also surface **time-to-wipeout** (N10) on the
  same axis. Add survivor-count + censored-count at each year so the hazard denominators are explicit.

- **T3 (pop-fade):** **use the real `return_from_listing_*` columns** instead of approximating from issue-anchored
  alpha (the plan says "approximate / state the wedge" — we don't have to; the from-listing columns exist).
  Compute forward **alpha-from-listing** properly, and add **N1's allottee-vs-buyer wedge** as the paired panel.
  Sharper bucketing at the extreme top (>100% pop is where mean-reversion bites). Keep SME buckets exploratory.

- **T5 (OFS):** add **N15's promoter-dilution delta** as the second lens (OFS% is the flow; post-issue promoter %
  is the resulting stock — show both). Add an explicit **PE-exit vs promoter-exit** flag where derivable (mature
  large-cap high-OFS is benign; micro high-OFS is the red flag) by always stratifying the OFS gradient within
  `market_cap_class`. Show the wipeout-rate-by-OFS curve, not just alpha.

- **T6 (sector matrix):** add a **third axis — multibagger:wipeout ratio** (a sector with great median alpha but a
  2:1 wipeout:multibagger ratio is a trap). Add **N11's absolute concentration** alongside the rates. Strongly
  flag the boom-sector coverage hole and, if the re-pull lands, re-run. Bubble chart: x=median alpha, y=wipeout
  rate, size=N, color=multibagger rate.

- **T7 (benchmarking):** wire in **N13** (Nifty50−Smallcap250 divergence) as the headline once SC250 alpha exists;
  until then keep the coverage table + the raw-vs-alpha small/micro illustration, and add an explicit
  **benchmark-version-switch audit** (show there's no artificial alpha discontinuity at the 2017/2019 boundary).

- **T8 (drawdown-tax):** add **time dimension** — pair `max_drawdown_pct` with `max_drawdown_duration_days`
  (already present!) so it's "you ate −X% **for Y months**," not just magnitude. Add a "**worst dip you had to
  hold through and still won**" P90 figure (the discipline test). Split the SME winners by `liquidity_flag` —
  illiquid SME drawdowns are partly print artifacts and should be shown separately, not blended.

- **T9 (profitable-at-IPO):** **graduate it into N7's fundamentals panel** — keep the clean binary headline
  (profitable yes/no, gap widening with horizon) but add the ROE / margin / debt tertiles and N8's cash-quality
  flag as the supporting graded view. This turns the "one robust piece of the quality composite" into the actual
  composite, with the binary still leading for hard-to-game clarity.

**Cross-cutting display enhancements:** every finding should expose (a) N per cell, (b) the maturity-gate horizon
used, (c) a one-line coverage/provenance caveat, and (d) cross-regime sign-agreement marker (✓/✗/n.a.) so a
reader instantly sees which findings survived the 2006–19 out-of-sample check.

---

## 3. NEW PREDICATES / SCORE-COMPONENT IDEAS (Part B)

Each is an IF-THEN with a measurable outcome distribution, mapped to a scorecard component.

| id (proposed) | predicate (IF) | outcome to show | feeds component | conf | coverage note |
|---|---|---|---|---|---|
| `pred-sub-saturation` | sub_total_x in the extreme top band (e.g. >100x) | forward alpha mean-reverts vs the 15–50x band | return-potential (penalty at extremes) | A | boom-only |
| `pred-demand-skew` (sharpen) | sub_qib_x/sub_retail_x in top tertile (QIB-led) | higher 1y/3y alpha, lower wipeout | return-potential + quality | A | boom-only |
| `pred-debt-death` | pre_ipo_debt_equity in top tertile | elevated wipeout rate, weaker 3y alpha | downside-safety + quality | A→B | longterm partial — sign-checkable |
| `pred-accrual-flag` | operating_cf_yr3 ≤ 0 while pat_yr3 > 0 | worse forward alpha / higher wipeout | quality (red flag) | B | provenance caveat |
| `pred-anchor-conviction` | anchor_pct (anchor/issue) in top tertile | better forward alpha, lower wipeout | return-potential / sponsorship | B | boom-MB |
| `pred-overvalued-vs-sector` | pe_ratio top tertile within broad_sector | mean-reversion: weaker forward alpha | return-potential (penalty) | B | gated on sector re-pull, boom-only |
| `pred-size-survival` | micro mcap OR issue_size_cr bottom band | much higher wipeout rate | downside-safety | A | issue_size 100% covered |
| `pred-dilution-misalign` | promoter dilution delta in top tertile (heavy dilution) | weaker long-term alpha | quality / sponsorship | B | sparse, boom-only |
| `pred-zombie-risk` | low liquidity_flag + below-issue at 1y | high probability of languishing (dead money) | liquidity + downside-safety | A | liquidity 87%+ covered |
| `pred-pop-fade` (keep) | adj_listing_gain_open top band | from-listing forward alpha mean-reverts | return-potential (for listing-buyer entry) | A | exclude unreliable_coverage |

**Score-component construction notes (for the scorecard):**
- **downside-safety** should be a blend of: wipeout-probability (from analog terminal_state), P10/P25 of analog
  alpha, % below-issue, AND a **liquidity-realizability haircut** (an illiquid −60% you can't exit is worse than a
  liquid one). Surface each sub-term.
- **liquidity** component: built from `liquidity_flag`, `median_daily_turnover_inr`, `circuit_lock_frac` — and it
  should **gate the upside claims** (a multibagger you can't sell isn't realizable upside).
- **quality** component: the N7 panel (profitable flag + ROE + margin + debt tertiles + N8 cash-flow flag),
  equal-weighted, provenance-graded, only the profitable-flag piece is "validated-grade," the rest "hint."
- **Data-informed weighting honesty:** every `pred-*` above must report lift + N + cross-regime sign before its
  component weight is trusted; boom-only predicates (subscription/GMP/anchor/PE) **cannot** earn data-informed
  weight from cross-regime validation → cap their weight or mark "single-regime, preset-only."

---

## 4. BACKTESTER STRATEGY IDEAS (Part C) — point-in-time, vs do-nothing

Baseline (do-nothing): buy every mainboard IPO at listing, hold to maturity, alpha-measured. Every strategy must
beat it net of STT/brokerage and with access realism (allotment odds, listing liquidity).

| id (proposed) | entry | exit | what it tests / why honest | conf | coverage note |
|---|---|---|---|---|---|
| `strat-flip-listing` (seeded) | listing open | listing close (same day) | the flip; net of costs likely ≈0 — honest null result is valuable | A | MB-only, liquidity-gated |
| `strat-hold-1y` (seeded) | listing close | +1y | secondary-buyer base case vs do-nothing | A | exclude unreliable_coverage |
| `strat-buy-dip` (seeded) | after X% dip from listing (X=10/20/30) | +1y / +3y | dead-cat vs real recovery; needs price-series, point-in-time | B | MB-only; SME = print artifacts |
| `strat-quality-gate` | listing close, ONLY if profitable_at_ipo AND debt/equity not-top-tertile | hold 3y | does the quality gate lift alpha vs ungated buy-all? | A→B | uses N7 features; provenance caveat |
| `strat-avoid-froth` | listing close, ONLY if sub_total_x NOT in extreme top band | hold 1y | does skipping the most-hyped IPOs beat buying all? (saturation) | A | boom-only |
| `strat-demand-skew` | listing close, ONLY if QIB-led (top tertile QIB/retail) | hold 1y/3y | smart-money filter vs buy-all | A | boom-only |
| `strat-size-survival` | listing close, EXCLUDE micro/bottom-issue-size | hold 3y | does dodging the wipeout-prone tail beat buy-all (esp. survivorship-honest)? | A | issue_size 100% |
| `strat-combined-score` | listing close, top-quintile combined scorecard | hold 1y/3y | the loop-closer: does the predictor's own score beat do-nothing? | A | the integration test of Part B |
| `strat-sector-rotate` | listing close, ONLY in sectors with validated positive alpha×survival (from T6) | hold 3y | does the sector matrix translate into a tradable filter? | B | gated on sector coverage |

**Honesty requirements (all strategies):** freeze the analog/feature universe to pre-listing-date info only;
allotment realism for any "apply" strategy (retail allotment ≈ 1/oversubscription, and adverse selection — you
get the duds); SME realizability haircut; report alpha (not raw), win-rate, max-drawdown, **and the
do-nothing delta**; cross-regime split (does the edge survive on 2006–19?). A strategy that only works in the
boom cohort is labeled regime-dependent, not "validated."

---

## 5. TOP-8 ADDITIONS (ranked)

1. **N1 / T3-merge — allottee-vs-secondary-buyer wedge** using the real `return_from_listing_*` columns (stop
   approximating). The single most actionable framing; feeds entry-conditioned predictor stances. **[A]**
2. **N12 — `listing_metrics_status` × outcome data-quality bias audit.** Correctness infra that protects every
   other base rate from a silent survivorship/coverage skew. Cheap, high-leverage. **[A]**
3. **N7 + T9-expansion — graded fundamentals panel (ROE / margin / debt tertiles) vs survival & alpha**, with
   debt/equity as the headline death-signal; keeps the clean profitable-at-IPO binary on top. **[A→B]**
4. **N2 — subscription-vs-outcome curve with saturation/reversal test** (official, hard-to-fake; documents where
   more demand stops predicting and starts hurting). Boom-only, flagged. **[A]**
5. **N4 — issue-size / mcap Goldilocks + wipeout-by-size gradient** (issue_size is 100% covered all cohorts;
   strongest always-available downside-safety input). **[A]**
6. **N11 — wipeout/multibagger sector & size concentration map** (tells the downside component WHERE the bodies
   are; pairs with T2/T6). **[A]**
7. **`strat-combined-score` + `strat-size-survival` / `strat-avoid-froth` backtests** — close the loop: prove the
   scorecard and the simplest robust filters beat do-nothing, cross-regime. **[A]**
8. **N8 — pre-IPO growth mean-reversion + accrual/cash-flow red-flag** (the cash-vs-paper-profit divergence is a
   rarely-surfaced, hard-to-fake quality signal). **[B]**

**Two infra dependencies to flag:** N13 (Nifty50−SC250 divergence) is **blocked on the Smallcap250 alpha build**;
N6 (PE-vs-sector) and parts of T6 are **gated on the boom sector/mcap re-pull** noted in TODO. Both are worth
pre-wiring as placeholders so they light up automatically when the data lands.
