# CLAUDE.md — project brain (read this first)

Auto-loaded context for Claude/any AI working on this repo. Keep it current: when you add a pipeline
step, a data source, a decision, or a rule, update the relevant section + the pointer here.

## What this is
A personal research tool to find **repeatable, trustworthy patterns in Indian IPOs (2006–2025, Mainboard + SME,
incl. delisted)** and turn them into (a) descriptive truths, (b) an analog-based predictor for new IPOs, and
(c) a strategy backtester. Not financial advice. Free data sources only.

## The 3 layers (and status)
- **Layer 1 — the dataset (event/identity + enrichment).** ✅ DONE. ISIN-keyed, ~2,296 IPOs across a boom cohort
  (2020–25, 1,269) and a long-term cohort (2006–19, 1,027). Identity verified; enriched with subscription, GMP,
  financials, sector, market-cap, promoter, etc. (with documented gaps).
- **Layer 2 — price history + outcomes.** ✅ DONE — built, reviewed (2 adversarial passes), remediated. Daily prices
  (official bhavcopy, split/bonus adjusted) → `returns_summary` → joined with features into **`ipo_analysis.csv`**
  (THE analysis substrate, 2296 rows) + per-row `data_quality_tier` + cross-source checks. Returns/alpha/delisting/
  liquidity verified sound. Listing-day metrics carry `listing_metrics_status` = ok(2043)/inferred_split(85)/
  unreliable_coverage(142, nulled+flagged) — Layer-3 listing-pop analysis should exclude `unreliable_coverage`.
  Has BOTH raw `listing_open` (Chittorgarh) and `adj_listing_open/adj_listing_gain_*` (adjusted, use these for gains).
  CANONICAL RUN ORDER for Layer 2: `07_returns_summary` → `scrapers/screener_prices_merge` → `08_build_universe`
  → `09_assemble` (with `pipeline/listing_remediation.py` used inside 07 + the merge).
- **Layer 3 — analysis.** ✅ BUILT (2026-05-31), reviewed + remediated. Engine in `layer3/` (UI-agnostic).
  **Part A** (descriptive report): `layer3/spine.py` (method spine) + findings in `layer3/findings/` → `run_layer3_report.py` → `report/layer3_partA.html` (**29 findings**, **108 tests**).
  **Part B** (analog predictor + 5-component scorecard): `layer3/predictor/` → `predict_ipo.py --type MB --sector ...`.
  **Part C** (backtester vs do-nothing): `layer3/backtest/` → `run_backtest.py`. **Cross-regime validation:**
  `layer3/validate.py` → `run_validation.py` (VALIDATED: lasting-wealth, pop-fade; MIXED/not-robust: ofs-skin,
  profitable). **Data-informed scorecard weights:** `layer3/predictor/weights.py` → `run_weights.py` (point-in-time
  rank-IC, cross-regime; return/multibagger/downside carry weight, liquidity/quality→0; `predict_ipo.py --profile
  data_informed`). Tests: **108 total** — `tests/layer3/` (77, incl. 5-traps) + `tests/pipeline/` (22) +
  `tests/scrapers/` (9), the latter two = TEST-1's data-building safety net (returns math / listing remediation /
  corp-actions parsing). Design: `docs/strategies.md`+`docs/layer3.md`; results:
  `rules/index.md`. KEY: `alpha` is FROM-LISTING (secondary-buyer, vs Nifty); allottee additionally gets the pop.
  **Interactive app:** `app.py` (Streamlit, 5 tabs: report / score-a-new-IPO / explorer / backtester / validation+rules) →
  `PYTHONPATH=. streamlit run app.py`. Remaining (polish): DRHP-PDF financials, live-refresh commit path.
  **Predictor now = a full "Evaluate this IPO" report**: outcome breakdown (doubled+/up/flat/down) + best-P90/
  median/worst-P10 + terminal dead-money & wipeout band + reach/exit movement + a prominent WIPEOUT RED-FLAG badge
  (`scorecard.wipeout_flags`: tiny-sales / loss-making / obscure-banker — validated cross-regime in N14).
  **SCORE POLICY (locked): "evolve-only-if-robust"** — a new signal enters the weighted score only if it improves the
  out-of-sample top-quintile lift robustly across splits; else display-only. The tested-signal registry (in-score /
  display-only / rejected, incl. WHY) is in `rules/index.md` — consult it before re-testing any signal.
  **Movement lens** (2026-06-01): the tool now measures the MOVE + the LIKELIHOOD, not
  single endpoints. Step 07 emits within-horizon peak/trough **MFE/MAE** from BOTH entries — `mfe_*`/`mae_*` (from
  adj issue = allottee) and `mfe_lst_*`/`mae_lst_*` (from listing = secondary buyer). Spine: `reach_curve`
  (P touched +X% / fell −X%), `exit_strategy` (take-profit ladder), `stop_loss_strategy` (SL-only). Finding M1
  (`findings/m1_exit_discipline`) = exit-discipline & stop-loss base rates, entry-split. `multibagger_odds` now
  also reports P(EVER 2x) (vs endpoint-2x; the gap = the timing tax). `tradeable_upside` = a 6th scorecard
  component, WEIGHT 0 (display-only — see `STATUS.md`). `backtest/analyses.exit_discipline_backtest`.
  KEY TRUTH: no take-profit/stop-loss rule beats buy-and-hold cross-regime (the right tail carries returns);
  tight stops actively hurt the secondary buyer (whipsaw). Combined TP+SL is NOT computable (MFE/MAE don't reveal
  which fired first). Catalog: `docs/research/ideas_movement_lens.md`.

## Where to start / how it flows
1. `docs/sources.md` — every data source (access, fields, coverage, free/premium). 2. `docs/schema.md` — columns.
3. `docs/pipeline.md` — run order. 4. `docs/strategies.md` — the prioritized Layer-3 catalog (rules/predictors/
backtests + the method spine). 5. `docs/layer2.md` / `docs/layer3.md` — design decisions. 6. `docs/data_review.md`
— every doubtful/partial item to fix later. 7. `STATUS.md` / `DONE.md` — work tracking.

## Repo map
- `scrapers/` — one file per SOURCE (chittorgarh, sharescart, screener, exchange_lists, bhavcopy, bhavcopy_ohlc,
  nse_subscription, ipowatch, investorgain, indices, corp_actions, delisting, screener_prices, yahoo). Fetch raw only.
- `pipeline/` — numbered, run in order: `00` long-term spine · `01` base · `02` detail · `03` Sharescart enrich ·
  `03b` screener financials · `03c` NSE subscription · `03d` ipowatch sub+GMP · `03e` investorgain GMP ·
  `03f` sector/market-cap · `04` verify tickers · `05` reconcile · `06` validate tickers · `07` returns_summary ·
  `08` build universe · `09` assemble.
  `pipeline/checks/` validates each. `pipeline/longterm/` enriches the 2006–19 cohort.
- `data/raw/<source>/` raw scraped · `data/reference/` exchange lists, bhavcopy cache, corp_actions, indices ·
  `data/prices/<isin>.csv` daily OHLCV · `data/master/` THE outputs (see below) · `archive/` superseded.
- `docs/` — sources, schema, pipeline, strategies, layer2, layer3, patterns, data_review, discussion, changelog.

## Key data products (`data/master/`)
- **`ipo_analysis.csv`** — THE Layer-3 substrate: features (universe) + outcomes (returns_summary) + data_quality + flags.
- `universe.csv` — unified feature table (2,296). `returns_summary.csv` — price-derived outcomes.
- `{mainboard,sme}.csv` (boom) + `{longterm_mainboard,longterm_sme}.csv` (2006–19). `_base_*.csv` = staging.
- Review/flag files: `data_review.md` (register) + `data/master/review/` holds the review CSVs
  (`xcheck_review.csv`, `screener_financials_review.csv`, `ticker_conflicts.csv`, `name_isin_review.csv`,
  `gaps.csv`, `price_source_review.csv`, `reconciliation_report.csv`, `ticker_validation.csv`, `price_missing.csv`).
  `delisting.csv` stays at `data/master/` top level (it is a price-pipeline data INPUT, read by step 07 + the merge).

## Non-negotiable conventions / decisions
- **GIT IS LOCAL-ONLY** — `git init`’d for local history/rollback only. NEVER add a remote / push / connect to GitHub until the user explicitly says so (their standing instruction, 2026-06-02).
- **ISIN is the primary key**; the ONLY automatic join key. Name-matching never merges (only flags).
  Exception: **corporate actions match by SYMBOL** (a face-value split changes the ISIN).
- **Returns are ALPHA** vs Nifty 50 (+ Smallcap 250 where available, 2019+). Raw return is secondary.
- **Survivorship-honest**: delisted included; terminal = last price, EXCEPT compulsory/liquidation → −100% (decision A1).
- **Prices split/bonus-adjusted**; issue_price adjusted by the same factor for issue-anchored metrics.
- **NO machine learning** (small data + transparency). Predictor = **analog/comparables** ("show similar past IPOs").
- **Score = a SCORECARD of components** (return-potential, multibagger-odds, downside-safety, liquidity, quality),
  combined with preset or data-informed (backtested-lift) weights; cross-regime validated. See `docs/layer3.md`.
- **Rigor**: boom-era findings are hypotheses until they hold on the 2006–19 cohort; always show sample size N;
  distributions over means; min-N floors; flag (never silently mis-assign).
- Full source map + the "tested & not viable" list are in `docs/sources.md`.

## Rules / predicates / strategies registry  (← navigable, AI-pickable)
When Layer 3 is built, every rule/predicate/score-component/strategy lives in **`rules/`** as a structured entry
(see `rules/README.md` for the template + index). Each carries: id, type, plain description, the predicate/logic,
features used, status (hypothesis/validated/rejected), backtest result (lift/hit-rate/N/cross-regime-stability),
priority, and source (which `docs/strategies.md` item). This is the single place to navigate/extend the logic.

## Running
`source .venv/bin/activate`, then either run the whole chain via the orchestrator
`PYTHONPATH=. python run_all.py` (canonical order; `--from <step>` to resume, `--list` to see step keys),
or run individual `pipeline/` steps in order (PYTHONPATH=. python pipeline/NN_*.py).
Long pulls (prices, screener) are resume-safe and rate-limited; screener blocks aggressively (1 worker + cooldowns).

## Pending / next  (single source of truth = `STATUS.md`; this is just the headline)
- **All 3 layers ✅ DONE + reviewed** (cleanup done; Layer 3 built, 3-subagent reviewed, cross-regime validated,
  data-informed weights derived). Remaining is POLISH (none blocking): optional Streamlit app; more enhancement
  findings; small integration residuals (75 scale-inversion listing rows, 24 boom-SME sectors). See `STATUS.md`.
- **Decisions awaiting the user** (`STATUS.md` "Analysis-time caveats"): non-equity handling (exclude vs analyze
  separately), data-quality threshold, whether to remediate the 75 scale-inversion rows, Streamlit timing.
- **To resume after any break: read this file → `STATUS.md` (what's left) → `rules/index.md` (findings + results).
  Run: `run_all.py` (dataset) / `run_layer3_report.py` + `predict_ipo.py` + `run_backtest.py` + `run_validation.py`
  (analysis). No need to re-explain the project.**
