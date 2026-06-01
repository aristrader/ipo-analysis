# Microcap / SME-seasoned small-cap extension — scoping & thinking

> Status: STRATEGY / SCOPING NOTE, not committed work. Companion to `extension_roadmap.md` (STEP 1).
> This is the THINK-THROUGH for the microcap RISK & MOVEMENT SCREENER. No code, no implementation.
> Framing is agreed and not re-debated: extend the MOAT (survivorship-honesty + movement/risk lens +
> dead-money/wipeout anatomy + clean-compounder quality signal) to illiquid microcaps as a **RISK &
> MOVEMENT SCREENER, NOT a return predictor**. Return-prediction on seasoned stocks is efficient-market
> turf with no edge; risk/illiquidity/wipeout structure in retail-dominated microcaps is on-moat.

---

## 0. One-paragraph thesis
Our SME/small IPOs do not vanish after listing — they *season* into the broader illiquid microcap pool.
That pool is where the same forces that make IPOs exploitable (retail-dominated, thin liquidity, circuit
locks, wipeout risk, dead-money zombies) persist *without* the listing event. So we drop the event-anchored
machinery (issue price, listing pop, subscription, GMP, OFS, allottee-vs-secondary) and keep the
event-agnostic machinery (reach/exit curves, no-stop-beats-hold, barbell dispersion, terminal-state /
wipeout band, dead-money detection, clean-compounder quality). The product answers: **"Is this seasoned
microcap a liquidity / dead-money / wipeout trap, and what does its movement-and-exit profile look like?"**
— never "what return will it give."

---

## 1. Universe definition

### The trap to avoid (learned in Layer 1/2)
`market_cap` is **reverse-causation-prone**: a stock is microcap *because* it fell (price collapse shrinks
the cap), so a live mcap band silently selects post-collapse names and contaminates any forward statistic.
We must not define the universe by current/point-in-time mcap and then measure "what happens to microcaps."

### Proposed robust definition (multi-pronged, structural, point-in-time)
Define membership **as-of a snapshot date** using slow-moving structural traits, not the volatile price:

1. **Exchange-segment anchor (primary, structural):** all names on **NSE Emerge / BSE SME** boards, plus
   Mainboard names that are *small by float and turnover* — segment is a near-permanent label, not a price
   artifact. This already overlaps our cohort heavily (every SME IPO lands here).
2. **Liquidity-defined microcap (the honest size proxy):** rank the *whole tradable universe* by
   **median daily traded value (turnover, INR)** over the trailing window at the snapshot, take the bottom
   band (e.g. bottom ~40–50% by turnover, with an absolute floor like < a few ₹cr/day median). Turnover is
   far less reverse-causal than mcap (a fallen large-cap still trades heavily; a true microcap never did).
3. **Mcap only as a coarse ceiling, never the selector:** apply a generous upper mcap cap (e.g. exclude
   anything that has *ever* been clearly mid/large, using the trailing-max mcap, not spot) to keep
   genuinely-large fallen names out — but rank/define by turnover + segment, not spot mcap.
4. **Point-in-time, always:** universe membership is recomputed *as-of each snapshot* from data available
   only up to that date. A name can enter/leave the universe over time. No "is microcap today" backfill.

Net: **universe = {NSE Emerge + BSE SME} ∪ {Mainboard names in the bottom turnover band under the mcap
ceiling}, computed as-of date, using trailing (not spot) liquidity.** This is structural, point-in-time, and
dodges the mcap reverse-causation trap.

### Rough size
- Our IPO substrate is ~2,296 names. The investable microcap pool is materially larger.
- NSE Emerge + BSE SME alone are well over **~1,000** listed names and growing fast.
- Adding the small-by-turnover Mainboard tail puts the candidate universe in the **~2,500–4,000** range
  of names with any tradable history — call it **single-digit thousands**, an order of magnitude more
  *names* than the IPO tool but the same order of magnitude in *engineering* because the price/financial
  plumbing is identical (bhavcopy + screener, both already built).

### Overlap with the existing IPO cohort
- **Direct superset relationship:** essentially every SME IPO in our 2,296 *becomes* a member of this
  universe once it has seasoned. Our cohort is the "freshly-arrived" subset; the microcap universe is the
  steady-state pool they flow into.
- This gives a **free validation bridge:** any finding we re-test on the microcap universe can be
  cross-checked against the seasoned trajectories of our own IPO names (we already track them post-listing
  to long horizons), so the two modules sanity-check each other.

---

## 2. Data — have vs need

| Data | Status | Where | Effort to extend |
|---|---|---|---|
| **Daily OHLC, whole market (NSE+BSE)** | **Already pulled, per date** | `data/reference/bhavcopy/` (559 daily files cached; `scrapers/bhavcopy.py` fetches/parses NSE old + NSE UDiFF + BSE UDiFF; newer format is ISIN-keyed with OpnPric/etc.) | LOW–MED. We already download the *whole* bhavcopy each date for the IPO pipeline — the other ~99% of rows are simply discarded today. Extending = *keep* them and assemble per-ISIN series for non-IPO names. The scraper, format-handling, and cache exist. |
| **Split/bonus adjustment** | Built | `pipeline/` corp-actions + `data/reference/corp_actions.csv` (match by SYMBOL per decision) | MED. Logic exists but corp_actions coverage is currently scoped to our cohort; needs widening to the full universe (more SYMBOL→action rows to pull). |
| **Screener financials (low-debt × high-ROE etc.)** | Built, name/code-resolved, **works on delisted names** | `scrapers/screener.py` (resolves `/company/<code>/`, verifies `<h1>`, falls back to search API for delisted) | MED–HIGH. Per-name pull; screener **blocks aggressively** (1 worker + cooldowns — noted in CLAUDE.md). Scaling from ~2,296 to several thousand names is mostly *time*, not new code. Resume-safe already. |
| **Delisting / terminal state** | Built as a pipeline INPUT | `data/master/delisting.csv` (2,296 rows: status/delist_date/reason/last_price/source_flags) | MED–HIGH. This is THE survivorship spine and must be rebuilt for the wider universe (the delisted microcaps are exactly the names that "disappear" from a naive screen). Sources/scraper exist (`scrapers/delisting.py`); coverage must expand. |
| **Index benchmarks** | Built | `data/reference/indices/` (nifty50, niftysmallcap250) | NONE (reuse). Benchmark policy already routes small/micro → Smallcap-250 (2017+) via `spine.benchmark_for`. |
| **Sector / industry** | Built | screener-derived `broad_sector`/`sector`/`industry` columns | LOW (same pull as financials). |
| **Exchange membership lists (segment label)** | Built | `data/reference/{nse_emerge_sme,nse_mainboard,nse_equity_list,bse_master}.csv` | LOW. Already have the SME/Mainboard segment lists needed for the universe definition. |

**Headline:** the two heavy data rails — **whole-market bhavcopy** and **screener financials** — already
exist and run. The microcap module is mostly **(a) stop discarding the non-IPO bhavcopy rows** and
**(b) widen the delisting + corp-action coverage**, not new scraping infrastructure. The single biggest
*effort* cost is patient, rate-limited screener pulls for thousands of names, and building a survivorship-
honest delisting spine for the wider set.

---

## 3. What the screener actually outputs (the honest "question it answers")

For a given seasoned microcap (ticker/ISIN) as-of a date, the screener returns a **risk + movement card**,
NOT a return forecast:

1. **Illiquidity / dead-money risk** — median daily turnover, circuit-lock frequency, % of days with zero
   trades, and a dead-money flag (alive but languishing far below a relevant anchor on thin volume). Answers:
   *"If I buy this, can I get out, and is it a value trap that just sits?"* Reuses `liquidity_flag`,
   `median_daily_turnover_inr`, `circuit_lock_frac`, and the n9 zombie / dead-money logic.
2. **Wipeout / terminal-risk band** — for *names like this* (peer cohort by segment/sector/size), the
   competing-risks terminal-state band: alive vs confirmed-wipeout (lower) vs delisted-unknown (upper),
   re-validated on seasoned microcaps. Answers: *"What share of names like this die, and how do they die?"*
   Reuses `terminal_state` / `wipeout_band` and the n14 wipeout-anatomy red-flags.
3. **Movement / exit profile** — the reach curve (P(reached +X%) / P(fell to −X%) within a rolling
   horizon), the exit-discipline ladder, the stop-loss diagnostics (stopped-but-recovered vs stop-saved),
   and the barbell/basket dispersion (mean-is-a-mirage). Answers: *"What does the path look like — how far
   does it typically swing, and does cutting losses or taking profits help, for names like this?"* Reuses
   `reach_curve`, `exit_strategy`, `stop_loss_strategy`, `partial_exit_strategy`, `basket_dispersion`,
   `lifecycle` — all already `entry`-parameterized and substrate-agnostic.
4. **Clean-compounder quality screen** — the low-debt × high-ROE signal (n15), recomputed from screener
   financials. Answers: *"Does this name carry the quality fingerprint that, in our data, separated the
   survivors from the zombies?"* Note: framed as a *quality/risk* screen (fragility avoidance), NOT a buy
   signal — quality reduces wipeout/dead-money odds; it does not promise alpha.

**Explicit non-output:** no "expected return," no "target price," no analog *return* predictor. The IPO
predictor's return-scorecard does NOT cross over — that edge lived in the listing event.

---

## 4. What transfers directly vs needs re-validation

### Transfers (mostly) directly — event-agnostic machinery
- **Survivorship-honesty discipline** (include delisted, terminal = last price except compulsory/liquidation
  → −100%, decision A1). Pure methodology; transfers wholesale.
- **The spine math** — `distribution`, `wilson_ci`, `bootstrap_median_ci`, `proportion`, `terminal_state`,
  `wipeout_band`, `reach_curve`, `exit_strategy`, `stop_loss_strategy`, `partial_exit_strategy`,
  `basket_dispersion`, `lifecycle`. These take a dataframe + an `entry`/`horizon` and don't care whether
  the time-zero is a listing or a snapshot. **This is the reuse jackpot.**
- **Liquidity / dead-money detection** — turnover, circuit-lock, zombie logic. Designed for exactly this
  population; transfers directly.
- **Distributions-over-means, min-N floors, flag-never-mis-assign, hard segment split** — methodology,
  transfers wholesale.

### Needs RE-VALIDATION on the new universe (different population, no listing event)
- **Wipeout red-flags (n14)** — derived on *IPOs*. Must be re-tested as predictors of *seasoned-microcap*
  wipeout; the discriminating features may differ (no IPO-specific signals like OFS/anchor remain).
- **Dead-money / zombie thresholds (n9)** — the "−50% & illiquid" cut was IPO-anchored to issue price;
  with no issue price, must be re-anchored (see §5) and re-validated.
- **No-stop-beats-hold (m1) & barbell (f_basket_dispersion)** — these were "buy every IPO at listing"
  truths. On seasoned names with a rolling/as-of entry, the dispersion shape and the stop-vs-hold verdict
  could change (no listing-pop right-tail to dominate the mean). **Re-test before asserting.**
- **Clean-compounder (n15)** — the signal may hold (it's a fundamentals truth), but the *base rates* it
  shifts (survival, dead-money odds) must be recomputed on the microcap population.
- **Benchmark/alpha framing** — alpha was issue-anchored; on seasoned names alpha must be defined from the
  *snapshot* (see §5), vs Smallcap-250. The relative-return *concept* transfers; the anchor changes.

### Does NOT transfer (event-only)
Subscription, GMP, OFS-skin, anchor, allottee-vs-secondary pop, pop-fade, the flip-trap, demand-skew, the
issue-size effect — all require the IPO event. Drop them from this module entirely.

---

## 5. The time-zero problem (no listing event)

IPOs have a clean t0 (listing) and a clean anchor (issue price). Seasoned microcaps have neither. Proposal:

- **Entry = as-of-date snapshots, evaluated over ROLLING windows.** Instead of one t0 per name, sample many
  **(name, snapshot-date)** observations — e.g. quarterly or monthly snapshots — and from each snapshot run
  the forward reach/exit/movement curves over fixed horizons (1y/3y/5y, maturity-gated as today). The
  "buyer" is "someone who bought on the snapshot date." This is the seasoned analog of `entry='listing'`.
- **Anchor for dead-money / drawdown = snapshot price** (and trailing peak), not issue price. Dead-money
  becomes "bought at snapshot, still deeply underwater later on thin volume," and drawdown is peak→trough
  from the snapshot. This replaces the issue-price anchor cleanly.
- **Horizons unchanged conceptually** (1y/3y/5y forward from snapshot), reusing maturity-gating: a snapshot
  only contributes to the 3y stat if 3y of forward data exists *and was in the past* (no look-ahead).
- **Pooling discipline:** overlapping snapshots of the *same* name are correlated → must not be treated as
  independent. Either (a) one snapshot per name per regime, or (b) report name-clustered / block-bootstrap
  CIs (extend `bootstrap_median_ci` to cluster by ISIN). **This is a real statistical subtlety the IPO tool
  never faced** (one row per IPO) and must be designed in from day one.
- **Alpha** from each snapshot = forward return minus Smallcap-250 over the same window. Concept transfers;
  anchor is the snapshot.

Recommendation: **as-of-date snapshots on a fixed grid (quarterly), forward rolling windows, name-clustered
CIs.** It gives many observations (good for small-N segments) while staying point-in-time and honest.

---

## 6. Pitfalls

1. **Survivorship bias — the #1 risk.** A naive "all microcaps trading today" screen *is* the survivorship
   trap in pure form: the dead microcaps are exactly the lesson. The delisting spine MUST be rebuilt for the
   full universe *before* any base rate is reported, or every statistic is optimistically biased. This is
   the hardest data task and the gating dependency.
2. **Reverse-causation / look-ahead in features.** mcap as a selector (a name is microcap *because* it
   crashed); current-liquidity as a feature when liquidity *followed* the collapse; any feature read after
   the snapshot date. Mitigation: define universe by trailing turnover + segment (§1); compute every feature
   strictly as-of the snapshot (point-in-time); never use spot mcap as a driver.
3. **Correlated observations from rolling snapshots** (§5) — overstated significance if overlapping windows
   of one name are counted as independent. Mitigation: name-clustered/block bootstrap; min one-per-regime.
4. **Much larger N + compute.** Whole-market bhavcopy assembly = millions of price rows; screener pulls for
   thousands of names against an aggressive blocker. Mitigation: reuse the resume-safe, rate-limited
   pullers; assemble per-ISIN price series incrementally; cache hard; do MVP on a *bounded* slice first (§7).
5. **Maintenance / freshness.** A live screener implies ongoing bhavcopy + screener + delisting refresh for a
   large universe. Mitigation: keep it a *batch* product (periodic refresh), not real-time; reuse the
   existing orchestrator pattern (`run_all.py --from`).
6. **Universe instability.** Names enter/leave the turnover band over time; a name "graduating" out of
   microcap mid-window must be handled (does it stay in the cohort for that window? — yes, classify by the
   snapshot's as-of membership, not the endpoint, to avoid look-ahead).
7. **Screener identity at scale.** Name-resolution works but at thousands of names mis-resolution risk rises;
   keep the existing `<h1>`-verify + flag-never-merge discipline; flag, don't guess.

---

## 7. Phased build plan (smallest valuable first)

### Phase 0 — Universe + survivorship spine (the unglamorous prerequisite)
Build the **point-in-time universe definition** (§1) and the **expanded delisting/terminal spine** (§6.1)
for a **bounded slice** first: **NSE Emerge + BSE SME names only** (segment-defined, ~1,000+ names, and the
direct ring outward from our SME IPOs). This avoids the fuzzy turnover-band Mainboard tail for now and reuses
the SME segment lists we already have. Deliverable: a clean, survivorship-honest as-of-date membership table.
Effort: **MED** (data assembly + delisting coverage; little new analysis code).

### Phase 1 — MVP: the RISK card on the SME-seasoned slice (the cheapest proof-of-value)
On the Phase-0 universe, run the **already-built, entry-agnostic spine** with `entry='snapshot'`:
- liquidity / dead-money flags (transfers directly),
- terminal-state / wipeout band re-validated on seasoned SME (transfers, recompute base rates),
- the reach / exit / stop-loss / basket-dispersion movement card from as-of snapshots (§5).
Output: a per-name **risk & movement card** + a descriptive report ("what happens to seasoned SME microcaps,
survivorship-honest"), cross-checked against our own IPO names' seasoned trajectories (the §1 validation
bridge). **This is the MVP.** Effort: **MED** — most analysis code is reused; cost is the snapshot harness,
clustered CIs, and re-running findings on the new substrate.

### Phase 2 — Quality screen + red-flag re-validation
Pull screener financials for the slice; recompute the **clean-compounder (low-debt × high-ROE)** quality
screen and **re-validate the wipeout red-flags (n14)** as predictors of *seasoned* wipeout. Add the quality
panel to the risk card. Effort: **MED–HIGH** (rate-limited screener pulls dominate).

### Phase 3 — Widen the universe + interaction layer
Add the small-by-turnover **Mainboard tail** (full §1 universe), then surface as a tab in `app.py`
(reusing the Streamlit shell). Effort: **MED**.

### Phase 4 (optional) — periodic refresh / "screen the live universe"
Batch refresh pipeline for ongoing use. Effort: **MED**, mostly ops.

### Rough total effort
Phase 0+1 (the MVP): on the order of a **focused multi-week** build, dominated by *data assembly &
survivorship spine*, not by new analytics (the spine is done). Phases 2–4 are incremental and gated on the
MVP proving value.

---

## 8. MVP recommendation (explicit)
**Build Phase 0 + Phase 1: a survivorship-honest RISK & MOVEMENT card for the NSE Emerge + BSE SME seasoned
slice, driven by as-of-date snapshots through the existing spine.** Segment-defined universe (no fuzzy
turnover band yet), risk + movement outputs only (no quality pull, no return prediction).

It is the cheapest proof-of-value because: (a) it reuses the heaviest assets we already own — whole-market
bhavcopy and the entire `layer3/spine.py` movement/risk machinery, which is already `entry`-parameterized;
(b) the universe is *defined* (a board membership list we already have), so no fuzzy turnover-band engineering
or screener pulls are needed to ship something real; (c) it is the *direct ring outward* from our SME IPOs, so
our own cohort's seasoned trajectories give a built-in validation bridge; and (d) it forces us to solve the
two genuinely-new problems (the survivorship spine for the wider set, and the snapshot/time-zero design) on a
*bounded* universe before scaling.

---

## 9. The single biggest risk to watch
**Survivorship bias in the seasoned universe.** Unlike the IPO cohort (where the listing event guarantees we
know every name that ever existed), a microcap universe assembled from "names with price history" silently
omits the microcaps that *died and delisted* — and those are precisely the wipeout/dead-money lessons the
whole product exists to surface. If the expanded delisting spine (Phase 0) is incomplete, every base rate
will be optimistically biased and the screener will *understate* exactly the risk it claims to measure,
quietly inverting its core value. This must be solved and adversarially audited *before* any base rate is
published.
