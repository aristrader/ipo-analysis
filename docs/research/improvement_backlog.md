# Improvement backlog — THE single living menu (started 2026-06-09)

> **This is the canonical "what we want to do" list.** It supersedes the scattered next/roadmap docs as
> the *current* menu — those (`NEXT.md`, `next_roadmap.md`, `next_capabilities_scan.md`,
> `next_factor_research.md`, `extension_roadmap.md`, `future_ideas.md`) are now FEEDERS: deeper reasoning
> lives there, but the live, deduped, status-tagged list lives HERE. We scope every work batch from this file.
>
> Ethos unchanged: only-what-works (3-layer validated) · free data · no ML · analog-based · survivorship-honest.
> Each item runs through `execution_pipeline.md`. Status: 🟢 built · 🟡 partial/needs-surfacing · ⚪ proposed · 🔬 research-gated.
> Effort S/M/L. "Proof" = the concrete case that motivates it.

---

## THEME A — Grading-driven fixes (born from the Fujiyama/Park grade, 2026-06-09)
Source: `fujiyama_park_case.md` (the case + the GRADE section). These are the most evidence-backed items we have.

### A1. Banker-flag fix — quality/size-aware, not frequency-in-our-window  ⚪  · S · **do-first**
- **What:** the `wipeout_flags` "obscure lead manager" flag fires when a banker has <12 IPOs *in our data window*.
  Replace with a SIZE-aware rule (don't fire on large MB) and/or a banker LISTING-PERFORMANCE quality measure.
- **Why / proof:** it false-positived on **Nuvama** (10 prior IPOs < 12) and knocked **Park Medi** from APPLY →
  NEUTRAL — a stock that then did **+73.9%** (allottee). Pure data-coverage artifact, not real obscurity.
  Fujiyama's Motilal (14 prior) escaped by luck, not skill. Backtestable now, fully historical.
- **Bar:** must improve OOS top-quintile lift robustly across splits, else display-only (evolve-only-if-robust).
- **Touches:** `layer3/predictor/scorecard.py` (`wipeout_flags`, `_query_flag_series`), `rules/index.md` registry.

### A2. Hold-through-drawdown / post-listing conviction signal  ⚪  · M-L · ties to north-star TA dimension
- **What:** a signal that says "this dull lister is *building strength* — hold/add" vs "this is dead money — exit."
  Distinct from the one-shot APPLY/AVOID; operates AFTER listing on the price path (+ optional delivery-%/volume).
- **Why / proof:** Fujiyama (APPLY ✓) went **−24.6% MAE, ~5 months underwater, peaked day 160** before +44%.
  Our scorecard gave NO "hold through this" signal — a real allottee would likely have capitulated. The +70% on
  both names was POST-LISTING DRIFT a single listing-time call structurally can't capture.
- **Caution:** post-listing ENTRY signals are a graveyard (dip-buy rejected, breakout falsified, issue-magnet = placebo
  — see `rules/index.md`). Frame as a HOLD/conviction overlay first, not a new buy trigger. Must beat do-nothing.
- **Related:** delivery-% (E2), 90-day-capitulation re-test (A3).

### A3. Re-validate the 90-day "capitulation" exit rule on the fresh cohort  🟡  · S-M
- **What:** the `capit@90td → EXIT_REVIEW` call (F5e) already fires when max close in sessions 1–90 stays below
  issue price. Owner wants it revisited: does selling on 90-day capitulation actually BEAT holding, on new data?
- **Why:** M1 found no blanket TP/SL beats buy-and-hold cross-regime (the right tail carries returns) — but this
  *specific* rule hasn't been re-tested on the post-freeze cohort. Honest caveat: neither Fujiyama nor Park is a
  clean counterexample (Fujiyama *just* cleared issue within 90d), so this is "re-validate," not "we know it's broken."
- **Touches:** `layer3/backtest/`, M1 exit-discipline finding; record verdict in `rules/index.md`.

---

## THEME B — Systematic miss-mining on the recent cohort (owner's 2026-06-09 idea)
### B1. Grade EVERY call for IPOs up to ~1 year old, untrained, mine BOTH error types  ⚪  · M · **high value**
- **What:** extend the OOS forward test from bucket-aggregates to a **per-IPO grade**: for every recent-cohort IPO
  (point-in-time call, analog pool = prior-only, NO training on them), join the realized outcome and build a
  **symmetric confusion-matrix mining** — both directions matter, and they fix different things:
  - **FALSE NEGATIVES — winners we called NEUTRAL/AVOID** (the "Parks"). Cost = OPPORTUNITY (missed upside, regret
    in ₹/₹1L). Fixing these improves *upside capture* — loosen/repair over-strict vetoes (e.g. the banker flag, A1).
  - **FALSE POSITIVES — losers we called APPLY** (the false APPLYs: dead-money, wipeouts, big-drawdown names).
    Cost = REAL CAPITAL. Fixing these improves *downside protection* — and given our survivorship-honest, downside-first
    ethos, **this side is arguably the higher priority** (protecting capital > catching every winner). What flag/feature
    SHOULD have fired and didn't? (e.g. a tiny-float/illiquidity/quality miss the wipeout flags didn't catch.)
  - **TRUE POS / TRUE NEG** for context (was APPLY right? was AVOID right?) → the actual hit-rate per call type.
  - Then: the *patterns* across each error class → fixable signals → SEEDS the Theme-A fixes (both loosen-vetoes AND add-guards).
- **Why / proof:** Park proved one false-negative is diagnosable & fixable; there are surely more on BOTH sides. The
  false-APPLY losers are the ones that lose money — equally worth scanning. We have the latest prices.
- **Honesty caveat:** the post-freeze cohort is young (0–~12mo) — listing/1m/3m/6m only, no 1y/3y verdicts yet; report
  N per cell, min-N floors, and frame the verdict as EARLY (same discipline as `forward_test_2026.md`).
- **Gap today:** `forward_test_2026.md` is bucket-level (B1/B2/B3 medians) only — no per-IPO, two-sided error view.
- **Touches:** `layer3/forward_test.py`, `layer3/calibration.py`, `layer3/portfolio.py` (regret/loss in ₹). Reuses the
  exact pattern used to grade Fujiyama/Park.

---

## THEME C — App re-iteration (owner: "highly user-friendly, easy to navigate")
### C1. Phase-2 app polish / redesign pass  🟡  · M
- **What:** iterate the 7-screen multipage app (`app/screens/`: home · recommendations · ipo_detail · evidence ·
  registry · track_record · data) for navigation, clarity, trust chips, display rules. Charter exists.
- **Source:** `app_phase2_design.md` (the brief — journeys/detail page/evidence/trust chips) + `app_iteration_charter.md`
  (the tapered-iteration plan) + `app_screens_v1.md`. Design agents MUST load `app_phase2_design.md`.
- **Status:** app is BUILT (7 screens live); this is the polish/redesign iteration, not a new build.

### C2. Growth-of-₹1L charts surfaced in the app (per-stock + portfolio)  🟡  · S
- **What:** "if I had invested ₹1 lakh" equity curves — per stock and for the whole APPLY portfolio — shown in the app.
- **Status:** ENGINE BUILT — `layer3/portfolio.py::growth_of_1l()` + `simulate()` + `summary()` exist and are
  honesty-reviewed (anchors at listing on first real price = exactly ₹1L; allottee vs secondary lenses; median not
  just mean; bootstrap CI). REMAINING = surface them as charts on the relevant app screens (track_record / ipo_detail).

---

## THEME D — News / catalyst (the scoped-down survivors; full map in `newsfeed_opportunity_map.md`)
### D1. RUNG-1 explanatory NSE-announcement context feed (display-only)  ⚪  · M
- Dated, ISIN-keyed (free NSE API has `sm_isin` — matching SOLVED), category-tagged by structured fields + local
  keyword taxonomy (NO LLM, NO egress). "Context, not signal" chip → can't break the honesty moat. The honest near-term product.
### D2. Delivery-volume % conviction signal  🔬  · S-M · the surprise do-first from the news sweep
- Free, in the bhavcopy family, 2006+ (cross-regime), the honest "real-move vs noise" daily proxy. 3-layer test;
  could become a HOLD-overlay input for A2. **Honest blocker:** confirm we can get the NSE *delivery* bhavcopy (we have OHLCV).
### D3. H7 — corp-action euphoria-top backtest  ⚪  · S
- `corp_actions.csv` (1,509 rows, 2006+, ISIN-keyed), no news feed, no look-ahead. Widens the thin F10 flag (n=31).
  Run to KILL-or-keep (watch F10 double-count).
### D4. Start the NSE-announcement staging pull (forward-collect)  ⚪  · S
- The only way to start the ~18–36mo clock that makes any *predictive* news hypothesis testable later. Stage raw, don't interpret.
### Killed (do NOT rabbit-hole): social sentiment · hosted-LLM polarity · RSS fuzzy-match · F&O-OI · all-stocks TA+FA+news fusion.

---

## THEME E — Analysis extensions (the original mission; each = a 3-layer test). Source: `NEXT.md` Thread C / `next_factor_research.md`
### E1. Pre-IPO discretionary accruals (Modified-Jones)  ⚪  · M — best evidence-to-effort new signal; upgrades the proven binary n8 flag; inputs already in screener data.
### E2. Unblock P/E-vs-sector for SME + EV/Sales for loss-makers  ⚪  · M — graduate the watchlisted `pe_vs_sector` (leans −43pp MB) by computing issue-time multiples ourselves.
### E3. SME→Mainboard migration as an outcome class + feature  ⚪  · M — the big unmodeled SME escape from the dead-money trap; free dated source.

---

## THEME F — Close-the-loop credibility (mostly BUILT; verify surfaced). Source: `NEXT.md` Thread A
### F1. Paper-portfolio sim of live calls vs Nifty  🟢 built (`portfolio.py`); surface/verify in app.
### F2. Monthly "were-we-right" scorecard as a durable dated artifact  🟡 — forward test runs; make it an append-only comparable series.
### F3. Calibration tracking (reliability / Brier) + Wilson intervals on base rates  🟢 built (`calibration.py`); ensure surfaced.

---

## THEME H — Relative valuation vs peers + intrinsic value (the FA dimension; owner 2026-06-09)  🔬 · L · could be its own 10–50-task project
Source: this idea + `fujiyama_park_case.md` candidate #3 (sector/fundamental tailwind) + existing `n6 / pe_vs_sector`.
**The hypothesis cluster:** an IPO's issue-time valuation RELATIVE to comparable listed companies predicts post-listing
outcomes — cheap-vs-peers re-rates UP ("catches up"), rich-vs-peers fades. Sub-questions the owner raised: peers' P/E &
market-cap; nearest-mcap matching; does a lower issue-PE-vs-peers lead to catch-up; does an intrinsic-value gap matter.
- **Ember (NOT a cold start):** `n6 / pe_vs_sector` already tests PE-vs-SECTOR-MEDIAN → forward alpha and leans **−43pp MB**
  (rich-vs-sector → worse; DISPLAY-ONLY, blocked on SME PE data — see E2). This idea = graduate that from sector-median to
  MATCHED PEERS + add intrinsic value. Directionally supported, not greenfield.
- **What we HAVE (point-in-time at IPO):** the IPO's own `pe_ratio`, `market_cap_cr`, sector/industry, full financials
  (sales/PAT/EPS/ROE/margin/OCF, 3-yr). **What we LACK:** peer lists, intrinsic-value estimates, and the killer —
  point-in-time valuations of the PEER (mostly non-IPO) universe at each IPO date.
- **Three honest blockers:** (1) **look-ahead is lethal** — screener gives *today's* peer multiples; using them on a past
  IPO is catastrophic contamination → quick versions are LIVE-FORWARD only, never a backtest. (2) **point-in-time peer
  valuations = the all-stocks data problem** → collides with `extension_roadmap.md` (deliberately deferred: negative-ROI,
  maintenance tax). (3) **peer ID + intrinsic value are fuzzy** — comp-matching = the F11/news matching swamp; DCF is
  assumption-garbage (prefer transparent Graham / earnings-power / residual-income, still need clean financials).
- **Feasibility upgrade (owner 2026-06-09):** screener keeps a HISTORICAL PE/price/EPS series (the median-PE
  valuation chart) → blocker #2 (point-in-time peer multiples) may be RECONSTRUCTABLE from screener history, not
  requiring the full all-stocks build. BUT scraping screener history for many peers is network-heavy + screener
  blocks aggressively → a babysat, rate-limited job, NOT unattended-safe. Keeps P4 research-gated; improves its odds.
- **THE SMART MVP (sidesteps blocker #2):** peers = **earlier IPOs in the same industry/mcap band**, valued with the
  point-in-time data we ALREADY own. ~2,384 IPOs with issue-time PE/mcap/financials + dates → look-ahead-clean, in-house,
  zero new scraping. Tests "priced cheap vs comparable recent IPOs → outperforms?" BEFORE touching the all-stocks panel.
  If it dies here, it dies cheap.
- **Unfold (phased, ~10–50 tasks):** P0 define hypotheses (re-rating · IV-gap · peer-proximity) → P1 **MVP IPO-vs-prior-IPO
  peers** (clean) → P2 graduate `pe_vs_sector` to peer-matched + EV/Sales for loss-makers → P3 transparent intrinsic value
  (Graham/EPV/residual-income) → P4 all-stocks point-in-time peer panel *(big sub-project, GATED on a P1 go/no-go)* →
  P5 3-layer test each (boom → 2006-19 → OOS, evolve-only-if-robust) → P6 scorecard component + peer table on IPO-detail screen.
- **Verdict:** high-interest FA dimension with a real ember; **start at the MVP (P1) — it's bounded, owned-data, honest.**
  Do NOT jump to P4 (the all-stocks panel) until P1 proves the signal is worth the data tax. Likely its own brainstorm→spec later.
- **Touches:** `layer3/findings/n6_valuation`, `layer3/predictor/scorecard.py`, a new peer-matching helper, `rules/index.md`
  (E2 `pe_vs_sector` is the same lineage — merge verdicts there).

## THEME G — Beyond IPOs (strategy note, not committed). Source: `extension_roadmap.md`
### G1. Microcap / SME-seasoned small-cap RISK & MOVEMENT screener  🔬 · L — the on-moat first slice outward; build a SCREENER (risk/movement/quality), NOT a return predictor. Only after the IPO tool's polish is done.
### G2. Swing-trade buy/sell calls  🔬 · L — research-gated; EXIT side tested (no blanket TP beats hold), ENTRY side weak. Needs a new entry signal that survives the 3-layer protocol, or D1/D2.

## THEME I — Data quality (from the 2026-06-09 "are we sure" subscription re-check)
### I1. Subscription category breakdown stored as 0 instead of null (~32 rows)  🟢 DONE (2026-06-10, safe-substrate method + verifier agent)
- ~32 substrate rows have `sub_total_x` present but `sub_qib_x`/`sub_nii_x`/`sub_retail_x` = 0 — the breakdown
  (esp. QIB) was UNCAPTURED and stored as 0; the TOTAL is correct. Found via the at-scale consistency check
  (total outside [min,max] of categories → all 35 trace to this benign cause, not corruption).
- **Fix:** where total is present and a category is 0-with-no-real-bid, set it to null (0-vs-null hygiene); then
  re-confirm `n3_demand_skew` (QIB/retail ratio) excludes/handles them — today it reads 0, marginally biasing the
  boom-only finding for those rows. Cheap, owned-data, no scraping. **NOT the live-feed parser bug** (that's fixed).
- **Source:** `batch_run_2026-06-09.md` §"are we sure". **Touches:** substrate build step + `findings/n3_demand_skew`.

## THEME J — Observability / Telegram ops-channel (owner 2026-06-09)
Use the existing Telegram channel as the single owner-ops bus (today it carries only call alerts). Tag streams in
ONE channel (`🟢 CALL` / `🚨 HEALTH` / `✅ RUN`); never let ops chatter bury trade signals.
### J1. FAIL-LOUD health alerts  ⚪ · S · **do-first of this theme**
- `notify_calls.py` runs live_board → run_calls → --live with NO error checking; a real failure (e.g. board
  fetch raises/returns empty, schema gate raises, run errors) currently passes SILENTLY on stale data.
- **Fix:** wrap each step; on a failure that left **no usable result** (board empty/stale, exception, gate block),
  send a tagged `🚨 HEALTH` Telegram message. Alert on OUTCOME not every caught exception (today's DNS blip
  RECOVERED — must NOT alert on transient-but-recovered). Throttle/dedupe (no repeat-panic). Telegram send is
  best-effort (different host than the failing scraper). **Touches:** `tools/notify/notify_calls.py`.
### J2. Heartbeat / last-run stamp — make SILENCE meaningful  ⚪ · S
- Stamp each successful run ('last good run @ T'); surface a long gap on the next run (catches runs missed while
  the Mac was off — pairs with the new RunAtLoad login-catch-up). Optional Phase-2: a daily `✅ RUN` digest
  ('ran 3×, N calls, 0 errors'). **Honest limit:** can only alert WHEN a run fires (login-gated launchd) — true
  24/7 dead-man's-switch needs an always-on server (out of scope for the free/local moat; documented, not built).
### Scope: J1 first (high-value, small), then J2. Keep ONE channel + tags + throttle. NOT a code-change firehose.

---

## How to use this
- **Pick the work batch from here.** Today's grade makes **A1 (banker-flag) the clear do-first**, with **B1
  (systematic miss-mining)** as the high-value companion that finds the *next* A-items, and **A2/A3** as the
  post-listing/hold thread. C2 is a cheap, satisfying app win (engine already built).
- When an item ships, mark it 🟢 and move the verdict to `rules/index.md`. When a new idea appears, add it here first.

## NIGHT-2 follow-ups (2026-06-10)
### A1b — banker-flag coverage-guard hybrid  ⚪ · M
- A1's quality-aware def fixes the reputable-bank false-veto but ABSTAINS on thin-record bankers → halves wipeout
  recall (the 78 small-shop SME wipeouts). HYBRID: use NEW (quality-aware) to EXONERATE reputable banks for the
  display badge + as the artifact-free narrative, AND retain a frequency/size leg for THIN-RECORD SME so genuinely-
  obscure small shops still flag. Promotion to LIVE requires recall NOT to regress (vs the legacy freq<12 baseline)
  AND cross-regime lift. Until then the legacy flag stays live. Code is staged behind `OBSCURE_BANKER_NEW`. Source: a1_banker_flag_2026-06.md + review.
### I3 — canonical scorecard_weights.json silently re-derived/overwritten  ⚪ · S · test/data hygiene
- During dev/suite runs the canonical `data/master/scorecard_weights.json` gets overwritten with slightly-VARYING
  (non-deterministic) but sane re-derivations by an as-yet-unpinned derive+save path (NOT run_calls/run_refresh —
  they don't save; showdown run_weights is sandboxed; suspect an agent/dev derive call). Values stay sane so live
  score is unaffected, but the CANONICAL validated weights can silently drift. FIX: pin the writer + make
  derive_weights deterministic + protect/guard the canonical file (or assert-vs-canonical in a test). Not a live bug.
