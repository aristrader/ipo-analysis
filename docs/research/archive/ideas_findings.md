# Additional Descriptive Findings — proposal (research, no code)

> Brief: propose ONLY genuinely decision-relevant, computable, robust descriptive findings that the
> 16 already-built findings (T1,T2,T3,T5,T6,T7,T8,T9,N2,N3,N4,N5,N6,N7,N8 + non-equity) do NOT already
> cover. Author pass 2026-06-01. Method-spine rules (maturity-gate, hard MB/SME split, alpha-not-raw,
> min-N floors, survivorship-honest + competing-risks, liquidity-gate, provenance grade, cross-regime
> sign-check) apply to EVERY item and are not repeated per row.
>
> Distinct from `layer3_enhancements_ideas.md`: that doc's N1–N15 are now mostly the *built* findings or
> their enhancements. This doc only lists items that are STILL not built and clears the high bar.
>
> **Data realities verified against `data/master/ipo_analysis.csv` (2,296 rows: boom MB 382 / SME 887,
> longterm MB 507 / SME 520):**
> - `lead_manager` is **100% covered** (160 distinct first-named houses; top houses 45–144 deals) — the
>   brief's "not available" note is WRONG for this column. (Registrar/anchor-identity/pledge ARE absent.)
> - `alpha_sc_*` (vs Smallcap250) now **exists and is populated** (1y 56%, 3y 30%) — the N13 SC250 gate is OPEN.
> - `open_date`/`close_date`/`listing_date` 99–100%; `volatility_annual` 99%; `max_drawdown_duration_days`
>   99%; `all_time_high` value 99% (but **not its date** — time-to-peak still needs a price-file pass).
> - `promoter_pre/post_issue_pct` 39%/33%, `price_band_low`/`book_built` 39% (boom-skewed, sparse).

---

## Prioritized table

| # | proposal | what it answers | columns used | computable? | robust / guardrails | cross-regime? | effort | recommendation |
|---|---|---|---|---|---|---|---|---|
| **A1** | **Zombie / dead-money base rate** (alive but `current_return_from_issue < −50%` AND `liquidity_flag=low`) by MB/SME/mcap | "What's the chance I end up in a name that never delists but never recovers and I can't exit?" — the missing 3rd competing outcome | `current_return_from_issue`, `liquidity_flag`, `delisted`, `type`, `cohort`, `outcome_class` | **YES** — 340 candidates (MB 69 / SME 271), well-populated | Distinct from T2 wipeout (those are −100%); these are the living dead T2 misses. Min-N ok. SME dominates → split hard. Define threshold once, show sensitivity (−40/−50/−60%) | **YES** (both cohorts have alive+below-issue+illiquid names) | LOW | **BUILD** — fills the T2 competing-risks gap that the enhancement note flagged but nobody built; cheap; decision-critical downside framing |
| **A2** | **Outcome-class migration** (listing-class → 1y → 3y transition matrix: dud→star, star→dud, persistence) | "Does a weak debut tend to stay weak? Does a hot listing fade by year 3? What's the churn?" | `adj_listing_gain_open` (listing class), `alpha_1y`, `alpha_3y` (or `return_from_listing_*`), `type` | **YES** — 1,297 rows have both 1y & 3y | Maturity-gate (3y needs ≥3y-old IPOs). Hold cohort constant per matrix to avoid horizon-mix bias (trap #1). MB primary; SME exploratory (print-noise). Classes via percentile bands, not arbitrary cutoffs | **YES** (compute one matrix per cohort, compare flows) | MED | **BUILD** — explicitly listed in strategies Tier-2; the canonical narrative/trap-detector ("most listing-day stars are not 3y stars"); not covered by T3 (T3 is a forward-return gradient, not a class-transition matrix) |
| **A3** | **Volatility / turbulence regime → outcome** (`volatility_annual` tertiles, and `circuit_lock_frac`, vs forward alpha + wipeout) | "Do the most volatile post-listing names deliver more, or just more pain and death?" | `volatility_annual` (99%), `circuit_lock_frac`, `max_drawdown_pct`, alpha_*, `outcome_class` | **YES** — 99% coverage | Volatility is partly an illiquidity artifact in SME → liquidity-gate + MB-first. Risk of being a restatement of T8/liquidity → frame as *ex-ante turbulence → outcome*, not redundant drawdown magnitude | **YES** (vol computable both cohorts) | LOW | **MAYBE** — robust + cheap, but partially overlaps T8 drawdown-tax & the liquidity component. Build only as a short panel, not a headline; risk of duplication |
| **A4** | **Banker league table** (lead-manager deal-flow concentration + per-house listing-pop & survival, top houses N≥15) | "Who underwrites the most, and do top-tier bankers' IPOs behave differently?" | `lead_manager` (100%), `adj_listing_gain_open`, alpha_*, `outcome_class`, `type` | **YES** — 100% covered, 160 houses, clean concentration | **Checked empirically: NO clean banker-quality→alpha monotonicity** (top houses Axis/Kotak/ICICI cluster near the field; 1y-alpha spread is noisy & cohort-confounded). Listing-pop spread is modest (≈0–18% across MB houses). League-table-as-DESCRIPTION is honest; banker-tier-as-SIGNAL is fragile | Partial (house identities shift across eras; survivorship of boutiques) | MED | **MAYBE** — build the *descriptive league table + concentration* (genuinely new, 100% covered, users ask "who's the banker"), but **do NOT** ship a "tier→alpha" predicate; mark it explicitly non-predictive |
| **A5** | **Smallcap250 benchmark-divergence column** (`alpha_Hy − alpha_sc_Hy` for small/micro & SME) | "Does small-cap IPO 'outperformance' survive the *right* benchmark?" — T7's core insight made quantitative | `alpha_1y/3y/5y`, `alpha_sc_1y/3y/5y`, `market_cap_class`, `type` | **YES now** — `alpha_sc_*` is populated (gate the enhancement-doc thought was closed is OPEN) | SC250 valid 2017+ → benchmark-version policy, no fake break at boundary; maturity-gate; coverage 56%/30% so 5y thin | Partial (SC250 only 2017+; longterm pre-2017 uses Nifty only) | LOW | **BUILD** — was deferred as "blocked on SC250 build"; the data now EXISTS. Directly upgrades T7 from a coverage table to the numerical proof. Low effort, high correctness value |
| **A6** | **IPO-glut / issuance-intensity overlay** (listings-per-quarter at time of IPO → forward alpha) | "Do IPOs that list during a flood of other IPOs do worse (supply indigestion / peak-froth timing)?" | derive issuance count from `listing_date`; alpha_*, `type` | **YES** (issuance spikes clear: 2017–18, 2023–25) | **Trap #1 (vintage = regime = market-level collinearity)**: only ~2–3 macro regimes in 19y → glut is nearly collinear with the regime. Can be shown as a *labeled overlay/conditioner* ONLY, never a standalone signal (strategies §SKIP says exactly this) | Weak (the confound IS the finding's enemy) | MED | **MAYBE** — narrative value, but high fake-signal risk; ship only as a caveated conditioner with the n≈2–3-regime warning. Lean SKIP-as-signal |
| **A7** | **Seasonality (listing month/quarter)** vs listing-pop & forward alpha | "Is there a good/bad month to list?" | `listing_date`, `adj_listing_gain_open`, alpha_* | YES | Months are unevenly populated (Oct 322, Jan 120) but enough N. **No credible mechanism**; any pattern is almost certainly the issuance-cycle/regime confound in disguise (Dec/Oct cluster ≈ pre-FY-end & festive issuance windows). Multiple-comparisons across 12 months → easy false positive | No (regime-confounded) | LOW | **SKIP** — fails the "decision-relevant AND robust" bar; pure data-dredge risk; mechanism-free |
| **A8** | **Days close→listing** vs outcome | "Does a faster/slower listing timeline signal anything?" | `close_date`, `listing_date` | YES (median 8d, p10–p90 = 4–19) | Range is narrow and regulator-mandated (T+ timeline tightened over the period) → the variable is mostly a *date-of-listing* proxy, i.e. another regime confound. No mechanism | No | LOW | **SKIP** — regulated, low-variance, mechanism-free; would mostly re-measure the calendar |
| **A9** | **Price-band-width** (`(issue_price − price_band_low)/price_band_low`) vs outcome | "Does a wide band (issuer uncertainty) predict worse listings?" | `price_band_low` (39%), `issue_price` | partial | **39% coverage, boom-skewed**; band width is tiny/standardized for most book-builts → near-constant; heavily collinear with MB/SME. Already judged LOW in the prior doc | No (sparse) | MED | **SKIP** — sparse, near-constant, collinear with the SME/MB story we already segment on |
| **A10** | **Time-to-peak & time-to-wipeout** (days listing→ATH; days listing→−90% crossing) | "How long must I hold for the upside, and how fast does the downside arrive?" | needs per-ISIN `data/prices/<isin>.csv` (ATH/wipeout *dates* not in substrate); `max_drawdown_duration_days` is a partial proxy | partial — **requires a price-series derivation pass** (was N10, still not built) | Maturity-gate (young IPO's peak may not have happened → right-censoring); liquidity-gate SME (peak may be an illiquid print); the wipeout-timing leg is robust, the peak-timing leg is censoring-fragile | YES (price files exist both cohorts) | HIGH | **MAYBE** — high narrative value (temporal companion to T8) but needs a new price-file pass + careful censoring handling; defer unless the price pass is being built anyway |

---

## Top BUILD picks (tight)

Five items clear the bar; three are ruthless SKIPs and two MAYBEs.

**BUILD A1 — zombie/dead-money base rate.** The competing-risks view (T2) only counts the −100% wipeouts and the
clean survivors; it misses the ~340 names (MB 69 / SME 271) that never delist but sit below −50% from issue and
can't be exited (`liquidity_flag=low`). This is the single most under-served downside truth, cheap (one filter,
all columns present at high coverage), cross-regime-able, and decision-critical for the downside-safety component.

**BUILD A2 — outcome-class migration matrix (listing → 1y → 3y).** 1,297 rows support it; it's the canonical
"dud-to-star / star-to-dud" narrative every IPO investor discusses, it's already on the Tier-2 list, and it is NOT
what T3 measures (T3 is a forward-return gradient by pop bucket, not a class-transition matrix). Hold cohort
constant per matrix to dodge the horizon-mix trap; MB primary, SME exploratory.

**BUILD A5 — Smallcap250 benchmark-divergence column.** The enhancement doc deferred this as "blocked on the
SC250 build," but `alpha_sc_*` is now populated. Computing `alpha − alpha_sc` for small/micro/SME turns T7's
headline insight ("does small-cap outperformance survive the right benchmark?") from a coverage table into a hard
per-horizon number. Low effort, pure correctness leverage.

**MAYBE A4 — banker league table (descriptive only).** `lead_manager` is 100% covered (the brief mis-stated this),
160 houses with real concentration, and users genuinely ask "who's the banker." But I checked the data: there is
**no clean banker-tier→alpha monotonicity** (top houses cluster near the field; 1y-alpha spread is noisy and
cohort-confounded). So ship the league table + deal-flow concentration as DESCRIPTION, and explicitly refuse to
make it a scored predicate.

**MAYBE A3 / A10 — turbulence-regime panel and time-to-peak/wipeout.** A3 is robust and cheap but overlaps T8/
liquidity, so build only as a short non-headline panel. A10 has the best narrative ("how long to the peak, how fast
to the grave") but needs a new price-file pass and careful right-censoring; defer unless that pass is happening.

**SKIP A6/A7/A8/A9** — IPO-glut, seasonality, days-to-listing, and price-band-width all founder on the same rock:
trap #1 (vintage = regime collinearity) or sparse/near-constant coverage, with no mechanism that survives the
confound. A6 (glut) is salvageable only as a caveated conditioner, never a signal.
