# Layer 3 — Strategy & Pattern Catalog (prioritized, critically reviewed)

Consolidated from a strategy panel (3 idea-generators + 1 adversarial critic), 2026-05-31.
Supersedes/extends the raw hypothesis list in `patterns.md`. Build *once data is populated*.
Everything reads off the one `returns_summary` table. Returns = **alpha** vs Nifty50 (+Smallcap250 2019+).

---

## 0. THE METHOD SPINE (non-negotiable — build BEFORE any pattern; nothing is trustworthy without it)
1. **Maturity-gating** — a horizon stat (3y/5y/10y) uses only IPOs old enough to have it; show N per horizon. Never forward-fill young IPOs into long-horizon base rates.
2. **Survivorship dual-view + COMPETING RISKS** — delisted always included; but split delisting *reason*: **wipeout/penny/compulsory ≈ −100%** vs **voluntary buyout/acquisition ≈ payout (a winner leaving)**. Lumping them inverts the truth. Report every aggregate survivors-only AND survivorship-honest.
3. **Alpha everywhere + benchmark-versioning** — measure vs Nifty50; small/micro vs Smallcap250 where available (2019+). Smallcap250 starts 2019 → explicit benchmark-version policy so the switch doesn't create a fake alpha break. Raw return only as a secondary column.
4. **Hard SME vs Mainboard split** — never pool. SME dominates the boom *count* but is illiquid/manipulated/often un-investable → pooled stats are secretly SME stats. Segment, don't footnote.
5. **Liquidity filter + liquidity-weighting** — flag phantom (thin-volume/circuit-locked) returns; report tails with and without an investable-liquidity filter; consider capital-weighting base rates by what's actually deployable.
6. **Min-N floors** — N≥30 for a tradable claim, N≥10 for a directional hint, else "insufficient analogs." Show N + distribution (P10/median/P90), never bare means (fat tails).
7. **Provenance/reliability grade per feature** — GMP (grey-market) and pre-IPO RHP financials are the dirtiest inputs; tag reliability; quarantine GMP from any score; treat noisy inputs as guilty until proven.
8. **Cross-regime out-of-sample** — boom-era (2020-25) findings are hypotheses until they hold *sign* on 2006-2019, AND within a single vintage (kills the regime confound).
9. **The "do-nothing" baseline** — every signal/strategy must beat the dumb default: "buy every (mainboard) IPO, hold to maturity, alpha-measured." Pre-register Tier-1 hypotheses; treat the rest as exploratory (multiple-comparisons discipline).

---

## TIER 1 — build first (high signal × robustness × decision value)
- **T1. Lasting-wealth base rate** (survivorship-honest, alpha) by mcap-class / sector / MB-SME, with N + full distributions. *The anchor truth of the whole tool.*
- **T2. Competing-risks survival/hazard curve** — cumulative wipeout vs premium-buyout probability by year, by MB/SME/mcap/sector. Decision-critical, hard to fake.
- **T3. Pop-fade gradient** — bucket by listing-day gain → 3y/5y alpha *from listing* (the secondary buyer). Does the biggest pop mean-revert? + issue-vs-listing wedge (allottee wins while listing-buyer loses). Base-rate gradient, NOT per-name calls.
- **T4. Anchor lock-in unlock event study** — abnormal alpha/volume around the unlock date (each IPO its own control); 50/50 two-step for post-2021; control for results-season/rebalance calendar overlap. Don't over-slice (anchor-quality stays a conditioner, not a separate study). MB-first, liquidity-gated.
- **T5. OFS / skin-in-the-game gradient** — high-OFS (insiders cashing out, no fresh capital) → worse long-term alpha + survival; dose-response on ofs_pct; stratify by mcap (mature PE-exits confound). + promoter post-issue holding.
- **T6. Sector alpha × survival matrix** — by broad-sector: 5y median alpha + multibagger rate + WIPEOUT rate together (a sector great on returns but high on hidden death is the key insight). Stability across both cohorts. Backbone of the predictor.
- **T7. Right-benchmarking discipline (H2)** — does small/micro IPO "outperformance" survive being benchmarked to Smallcap250 instead of Nifty50? (correctness infra that doubles as insight).
- **T8. MFE/MAE drawdown-tax pain map** — for eventual winners, the max drawdown + duration endured en route ("triples but you eat −60% at month 8 first"). Tells the holder what they must survive. Descriptive = robust.
- **T9. Profitable-at-IPO premium** — binary, hard-to-game: do profitable-at-IPO names have higher 5y alpha + lower wipeout, and does the gap WIDEN with horizon? (the one robust piece of the quality composite; defer PE/growth).
- **T10. Predictor HONESTY layer FIRST** — min-N floors, "insufficient analogs," show-the-distribution, provenance grading, confidence checklist. Build the honesty before the scoring.

## TIER 2 — build after, with guardrails
- Demand-skew (QIB vs RII vs NII "smart vs dumb money"), saturation/reversal at extreme oversubscription — official data, but resist regime sub-slicing.
- Flip EV / flip-vs-hold calculator — as a **cost+allotment-honest** calculator (STT/brokerage + retail allotment ≈ 1/oversubscription, and adverse selection: you get the duds, not the hot ones) — NOT an alpha claim; likely ~zero after costs.
- Day-1 open→close fade + GMP-vs-open dislocation — **mainboard only, liquidity-gated**.
- IPO lifecycle / time-to-peak curve (when does the avg IPO peak?) — *fix cohort constant* to avoid horizon-mix bias; narrative value.
- Outcome-class migration (Sankey: listing class → 1y → 3y), dud-to-star — narrative/trap-detector.
- Full quality composite (add PE-vs-alpha, pre-IPO-growth mean-reversion) — ONLY after provenance grading; equal-weight, OOS-validated.
- Regime/froth/glut — only as a *labeled overlay/conditioner* shown with its n≈2-3 caveat, NEVER a standalone predictor.
- Seasonality, price-band-width, lead-manager tier, age-at-IPO, vol/beta vs alpha — exploratory.

## SKIP / deprioritize (with reasons)
- **GMP as a tradable/scored input** — grey-market data integrity is unfixable retroactively; highest fake-alpha risk. Keep GMP only as a *displayed descriptive field*, quarantined from the score.
- **SME day-1 microstructure & circuit→continuation** — manipulation artifacts, illiquid, un-investable. Don't model.
- **Standalone PE-vs-alpha / pre-IPO-growth signals** — input noise too high; fold into the composite at most.
- **Two-step-unlock / anchor-quality as separate studies** — over-slicing T4 into N=4 cells; keep as conditioners.
- **NII funding-cost & "IPO-market momentum" as standalone modules** — collapse into demand-skew / regime; same vintage-confound trap.

---

## THE PREDICTOR (analog/comparables engine — no ML)
**Structure: hard-gate → soft-distance → show the cohort's outcome distribution → transparent score.**
- **Tier-1 hard gates** (define the universe): instrument type + MB/SME; broad sector; market-cap class (±1).
- **Tier-2 soft distance** (weighted Gower, mixed types): valuation (PE vs sector median, profitable flag), demand (QIB/NII subs, GMP*), structure (ofs_pct, log issue size), quality (ROE, D/E, PAT margin, 3y growth), sponsorship (lead-mgr tier, anchor), promoter post %. (*GMP only if provenance-graded OK.)
- **Tier-3 context** (weights, not gates): market-regime-at-IPO, IPO-glut → up-weight same-regime analogs.
- **Widening ladder** (until min-N): tight gates+era → relax era → ±1 mcap → drop industry → drop sector (financial-twin) → show which rung + how N grew + degrade confidence; log the relaxation in plain words.
- **0-100 score = transparent blend, components always shown**: (a) expected-alpha (cohort median alpha percentile vs survivorship-honest universe), (b) downside (cohort P10/P25, % below-issue / delisted-at-loss / deep MAE), (c) multibagger odds (% ≥2x/≥5x alpha). Weights exposed/adjustable; render the histogram + the named analog IPOs, never just the number.
- **What-to-do**: plain stances conditioned on entry (allottee vs listing-buyer) + horizon, paired with the dominant risk + base-rate caveat ("this is what 24 similar IPOs did, not a forecast"). Never a buy/sell order.
- **Confidence = checklist** (N, ladder rung reached, dispersion/bimodality, maturity coverage, mean data_quality) — not a single opaque %.
- **Edge cases**: no sector precedent → financial-twin rung, confidence≤Low; conflicting signals → show the opposing sub-cohorts, don't average; missing field → drop from distance + renormalize, note it; young query → use analogs' mature outcomes but never fabricate the query's own long-horizon number; delisted analogs → KEEP (most important); illiquid analogs → down-weight in upside, keep in downside; never self-match or use future analogs.

## THE BACKTESTER
Strategy = entry rule + exit rule, applied **point-in-time** (only info known at decision; freeze analog universe to pre-listing-date IPOs). Report return / **alpha** / win-rate / max-drawdown by segment, **net of costs** (STT/brokerage) and with **access realism** (allotment odds, listing liquidity). Must beat the **do-nothing baseline**. Some rules come from Tier-1/2 findings (closing the loop).

---

## The 5 traps that could make the whole analysis lie
1. **Vintage = Regime = Market-level collinearity** (only ~2-3 macro regimes in 19y) → lean on alpha; demand within-vintage survival.
2. **Conditioning collapse** (gating shatters 2300 → cells of 3-8) → min-N floors + show N/CIs + refuse sub-floor point predictions.
3. **Dirty inputs as ground truth** (GMP, RHP financials) → provenance grade; quarantine GMP from scores.
4. **Survivorship + right-censoring asymmetry** (premium-buyout vs wipeout; young IPOs) → competing-risks + maturity-gating.
5. **SME ≠ Mainboard pooling** → hard segmentation; liquidity-weighted base rates.

## Build order
Method spine (§0) → Tier-1 reports/base-rates (T1,T2,T6,T3,T5,T9) + drawdown map (T8) + benchmarking (T7) → predictor honesty layer (T10) → predictor scoring → backtester (with do-nothing baseline) → Tier-2 → iterate.
