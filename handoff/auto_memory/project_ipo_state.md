---
name: ipo-project-state
description: "Current state of IPO analysis project — rebuilt ISIN-keyed dataset, repo structure, where everything lives"
metadata: 
  node_type: memory
  type: project
  originSessionId: 01820f2d-c29a-4f29-84ad-349ce26b70fa
---

## REBUILT (2026-05-30): ISIN-keyed master dataset + reorganized repo

The project was re-architected from a fragile Sharescart-name-matched base into a clean
ISIN-keyed pipeline. **Chittorgarh is the spine** (100% ISIN, complete 2020-2025 universe);
all other sources attach BY ISIN ONLY (name-matching never merges).

### Repo structure (navigate from README.md)
- `docs/sources.md` — THE source map (per site: access, fields, free/premium, coverage). Read first.
- `docs/schema.md` — locked master columns → type → source (120 cols)
- `docs/pipeline.md` — runbook; `docs/decisions.md` (was discussion.md); `docs/changelog.md`
- `scrapers/` — one file per source: chittorgarh.py, sharescart.py, screener.py, exchange_lists.py, bhavcopy.py
- `pipeline/` — numbered, run in order: 01_build_base → 02_attach_detail → 03_enrich → 04_verify → 05_reconcile. `pipeline/checks/` validates each.
- `data/raw/<source>/` — untouched scraped data. `data/reference/` — NSE/BSE lists, bhavcopy cache.
- `data/master/` — **OUTPUTS: mainboard.csv (382), sme.csv (887)** + README, gaps.csv, ticker_conflicts.csv, name_isin_review.csv, reconciliation_report.csv
- `archive/` — old one-off scripts + old 929 CSVs (`*_clean_OLD.csv` = reconciliation baseline). Nothing deleted.

### Build command
`source .venv/bin/activate; PYTHONPATH=. python pipeline/01_build_base.py && ... 05_reconcile.py`
Then `for c in pipeline/checks/check_0*.py; do PYTHONPATH=. python $c; done` (all print OK).

### Final state (1269 IPOs, 2020-2025)
- Identity: every row ISIN-keyed + unique; ticker from official ISIN→symbol (authoritative).
- High-confidence: 376/382 MB, 876/887 SME.
- Subscription/financials/GMP: ISIN-gated from Sharescart (2023-25 only); 0 gating violations. 317 gaps (2020-22) → gaps.csv.
- market_maker: 879/887 SME (Chittorgarh).

### RESOLVED (2026-05-31 review with user)
- **15 renames/conflicts confirmed + applied** via `data/reference/name_overrides.csv` (isin→latest_name,
  human-verified). 04_verify reads it: adopts latest company_name (original kept in `name_at_ipo`),
  clears the review/conflict flag, marks `renamed_confirmed`. Includes Burger King→Restaurant Brands Asia,
  Zomato→Eternal, Adani Wilmar→AWL, Barbeque→United Foodbrands(UFBL), Sah Polymers→Aeroflex Neu(AERONEU),
  Arisinfra(ARIS), Standard Glass(SETL), Meson Valves→Quest Flow Controls, Sai Swami→Dolphin Kitchen(DKUAL),
  Ambey Laboratories→Dhansa Labs, etc. → `ticker_conflicts.csv` and `name_isin_review.csv` now EMPTY.
  Any NEW unlisted name↔ISIN mismatch still gets flagged (safety net preserved).
- **BSE ticker bug fixed**: BSE-only stocks were wrongly `.NS`; now exchange-aware — NSE listing (official
  list OR Chittorgarh symbol) → `SYMBOL.NS`; BSE-only → `{numeric scrip code}.BO` (Yahoo-correct, NOT the
  alphabetic scrip_id the old data used). 374 SME + 3 MB now correct `.BO`. Every row now has a ticker.
- **All 13 "missing" old rows = old-ISIN errors**: each company IS in new data under its correct ISIN
  (verified). Kalpataru Projects→Kalpataru Ltd, Rajputana Investment→Rajputana Biodiesel, LGT Global→LGT
  Business Connextions, Dhansa Labs→Ambey Laboratories(renamed). ZERO genuinely-missing IPOs.

### Tracked files (current)
- `ticker_conflicts.csv` = 0 unresolved; `name_isin_review.csv` = 0 unresolved.
- `reconciliation_report.csv`: 904 overlap; **15 HARD all explained** (2 confirmed renames SETL/ARIS +
  13 old-wrong-ISIN rows present-under-correct-ISIN); 262 BSE_FMT (expected numeric-.BO fixes);
  62 SOFT numeric diffs (incl. decimal-bug fixes).
- `gaps.csv` (317): 2020-22 subscription/GMP — no free source yet (deferred TODO).

### Key principle (learned the hard way)
Verify by UNIQUE KEY (ISIN) multi-source agreement, never by price (coincides) or name (too lenient).
Yahoo BSE tickers are NUMERIC code + .BO (not alphabetic). Subscription QIB/NII/Retail split:
Chittorgarh premium-gated, only Sharescart has it (2023-25).

### Sources found for gaps (2026-05-31, tested — in docs/sources.md; integration pending)
- **G1a subscription split**: NSE Public Issues API `ipo-active-category?symbol=` (mainboard, curl_cffi,
  authoritative, reaches 2020; SME returns 0) + **ipowatch.in** WP REST (SME + all, use content.rendered).
- **G1b financials/KPIs**: **screener.in** `/company/<TICKER>/` (plain UA, 10+ yrs incl pre-listing FY20/21).
- **G2 GMP**: **ipowatch.in** (date series, MB+SME) + **investorgain.com** (single %, ISIN-keyed).
- Dead-ends (don't re-research): BSE IPO API (blocked), ipocentral (sparse), trendlyne (JS-gated),
  moneycontrol financials (5yr only — but its autosuggest API is a good ISIN↔ticker bridge).
- Match keys: NSE=symbol(via EQUITY_L), ipowatch=name+date, screener=ISIN→ticker, investorgain=ISIN.

### UPDATE 2026-05-31 (later) — Layer 3 BUILT (all 3 parts)
- **Layer 3 engine lives in `layer3/`** (UI-agnostic). Part A report (`run_layer3_report.py`→`report/layer3_partA.html`,
  spine + 8 findings t1..t9), Part B predictor (`predict_ipo.py`, `layer3/predictor/`: analogs + 5-comp scorecard),
  Part C backtester (`run_backtest.py`, `layer3/backtest/`). 39 tests in `tests/layer3/`. Reviewed by 3 subagents.
- **Integration pass ran first** (refreshed `ipo_analysis.csv`): +pre-2007 alpha, +Smallcap-250 alpha (`alpha_sc_*`),
  +79 recovered listing days (`listing_metrics_status='recovered_bhavcopy'`), boom sector 3%→94%. Backups in
  `archive/pre_integration_20260531/`. Staged-fix sources in `docs/research/` (verified by adversarial agents).
- **CRITICAL fact for analysis:** `alpha_*` = FROM-LISTING alpha (return_from_listing − Nifty), i.e. secondary-buyer
  market-adjusted; the allottee additionally gets the listing pop. `ofs_pct`/subs/gmp/roe/margin are 0–100 scale.
- Results in `rules/index.md`. Remaining polish in `TODO.md` (cross-regime validation, data-informed weights, Streamlit app).
- Full play-by-play: `docs/research/autonomous_session_log.md`.

### UPDATE 2026-05-31 — Layers 1 & 2 DONE; CLAUDE.md is now the live brain
- **`CLAUDE.md` (repo root) is the auto-loaded project brain — read it first; it supersedes the stale bits above.**
  Status/run-order/conventions/pointers all live there. `TODO.md`=what's left, `DONE.md`=done, `docs/data_review.md`=residuals.
- **Layer 1 fully enriched + integrated** (subscription via NSE API + ipowatch; GMP via ipowatch+investorgain → 1017/1269;
  financials/sector/mcap via screener; instrument_type). The "G1/G2 sources... integration pending" line above is now DONE.
- **Layer 2 DONE** — daily bhavcopy prices (split/bonus adj) → `returns_summary` → joined into **`data/master/ipo_analysis.csv`**
  (2296 rows, THE Layer-3 substrate). Reviewed by 2 adversarial agents + remediated. Review CSVs now live in `data/master/review/`.
- **Layer 3 = NEXT** (designed in `docs/strategies.md`+`docs/layer3.md`; rules seeded in `rules/`). Decisions so far:
  NO ML; analog/comparables predictor + 5-component SCORECARD; SME & Mainboard as SEPARATE tracks (same framework);
  build ALL Part-A findings via parallel agents. Interface (static report vs Streamlit app) = user still deciding.

### Residual-fix research agents (2026-05-31) — findings STAGED in `docs/research/`, integration pass PENDING
Ran 4 background agents; all done. An integration pass (apply staged fixes together, re-run step 07 + assemble) is queued, NOT yet run:
- **Benchmarks:** Nifty 50 history extended back to 1990 (byte-identical on overlap) + Nifty Smallcap 250 populated 2017-04-03+
  → written to `data/reference/indices/`. Fills pre-2007 alpha gap + enables Smallcap-250 alpha (needs step-07 recompute).
- **Price recovery:** the "142+26" gaps were mostly pipeline artifacts; 81 true gaps → **79 recovered** from BSE bhavcopy
  (matched by SC_CODE since ISIN drifts a char after FV splits) → `docs/research/recovered_listing_day.csv`. 2 flagged for manual fix.
- **Verification:** 85 inferred_split → 0 contradicted; **5 missing-feed splits found** (Aditya Vision/Insolation/Angel One 1:10,
  Trident 14:10 bonus, MIC 5:1); screener vindicated on all 21 financial flags; 9 corrections in `docs/research/verification_corrections.csv`.
- **Cleanup:** archived superseded scripts + old `data/derived/`; review CSVs → `data/master/review/` (code paths updated); added `run_all.py`.
- New working sources for the map: Sdaas GitHub Nifty50 CSV, NSE `ind_close_all` daily all-index archive. New dead-ends: stooq (captcha), niftyindices POST (hangs).

### UPDATE 2026-06-01 — MOVEMENT LENS added (user's core philosophy, applied across the tool)
- **The user's philosophy (durable):** "in markets you can't rely on a single-date data point — capture the
  MOVEMENT and the LIKELIHOOD of patterns repeating." Reach-probability curves over single endpoints; and
  EVERY analysis split by ENTRY (allottee=from issue / secondary=from listing) because the entry price
  changes the answer. Also wants exit-discipline (was it ever profitable / did it ever give an exit; what
  would a take-profit or break-even exit have captured).
- **Built (21 findings / 69 tests, all green):** step 07 emits within-horizon peak/trough **MFE/MAE** from
  both entries (`mfe_*`/`mae_*` from adj issue; `mfe_lst_*`/`mae_lst_*` from listing). Spine: `reach_curve`,
  `exit_strategy` (take-profit), `stop_loss_strategy` (SL-only). Finding **M1** (`findings/m1_exit_discipline`).
  `multibagger_odds` now also reports P(EVER 2x). T3 got a reach-by-pop-bucket table. `exit_discipline_backtest`.
  New scorecard component `tradeable_upside` (WEIGHT 0 = display-only). App: dual-entry exit display, Explorer
  entry toggle + stop-loss, exit backtest. Verified end-to-end via Playwright.
- **KEY TRUTH found:** NO take-profit or stop-loss rule beats buy-and-hold cross-regime — the right tail
  carries IPO returns, so capping/cutting forfeits it; tight stops actively HURT the secondary buyer (whipsaw,
  e.g. MB −10% stop drops mean 9.0%→1.2%). Combined TP+SL is NOT computable (MFE/MAE don't reveal order).
- **Deferred (judgment calls, written to `NEEDS_YOUR_INPUT.md`):** whether to weight `tradeable_upside` into
  the score (needs weights re-fit + OOS re-run); promote the stop-loss finding to cross-regime-validated;
  exit/reach thresholds; and a prices re-pass for time-to-peak / trailing stops (not computable now).
- Catalog of all movement-lens reframes + what was deliberately skipped: `docs/research/ideas_movement_lens.md`.
