# MAP — generated, do not edit (source: project_map.py; run `python verify.py` to refresh)

> Navigation, data-flow, and a context index for this repo. Generated from `project_map.py`.

## Navigate — to do X, start here
- `PYTHONPATH=. python run_all.py` — build the dataset (whole pipeline DAG; --from to resume)
- `PYTHONPATH=. python run_layer3_report.py` — build report/layer3_partA.html (29 findings)
- `PYTHONPATH=. python predict_ipo.py --type MB --sector ...` — score/evaluate a new IPO
- `PYTHONPATH=. python run_backtest.py` — strategy backtests
- `PYTHONPATH=. python run_validation.py` — cross-regime validation
- `PYTHONPATH=. python run_weights.py` — derive data-informed weights
- `PYTHONPATH=. python -m pytest tests -q` — run all tests
- `PYTHONPATH=. streamlit run app.py` — the interactive app (5 tabs)
- `python verify.py` — structure/invariant checkpoint + regenerate MAP.md
- `PYTHONPATH=. python run_refresh.py` — bring the dataset to today (dry-run; --apply executes)
- `PYTHONPATH=. python run_forward_test.py` — score the never-seen post-refresh cohort (EARLY READ)
- `PYTHONPATH=. python run_calls.py` — calls ledger: cursor walk/gap-fill (--backfill, --grade-only, --report)
- `PYTHONPATH=. python run_portfolio.py` — ₹1L paper-portfolio sim vs Nifty (--stock ISIN = per-stock growth)
- `PYTHONPATH=. python run_scorecard.py` — were-we-right scorecard + score-ordering (--horizon 1m/3m/1y)
- `PYTHONPATH=. python scrapers/live_board.py` — fetch the live+upcoming IPO board -> data/live/

## Context index — working on X? open these
- **score / evaluate a new IPO** → `layer3/predictor/scorecard.py`, `layer3/predictor/weights.py`, `layer3/predictor/predict.py`, `layer3/predictor/analogs.py`, `rules/index.md`, `predict_ipo.py`, `tests/layer3/test_predictor.py`
- **add / edit a finding** → `layer3/findings/`, `layer3/spine.py`, `layer3/report.py`, `run_layer3_report.py`, `tests/layer3/test_findings.py`, `rules/index.md`
- **prices / returns / MFE-MAE / listing-day** → `pipeline/07_returns_summary.py`, `scrapers/screener_prices_merge.py`, `pipeline/listing_remediation.py`, `tests/pipeline/test_returns_math.py`, `tests/pipeline/test_listing_remediation.py`
- **build / fix the dataset (pipeline)** → `run_all.py`, `project_map.py`, `docs/pipeline.md`, `pipeline/`, `pipeline/lib.py`
- **scrapers / data sources** → `scrapers/`, `scrapers/nse_session.py`, `docs/sources.md`, `tests/scrapers/`
- **backtest a strategy** → `layer3/backtest/`, `run_backtest.py`, `docs/strategies.md`, `tests/layer3/test_backtest.py`, `tests/layer3/test_score_backtest.py`
- **cross-regime validation / OOS** → `layer3/validate.py`, `run_validation.py`, `run_oos.py`, `tests/layer3/test_validate.py`
- **the app / UI** → `app.py`, `docs/research/app_phase2_design.md`, `docs/research/recommendations_system_discussion.md`, `docs/research/newsfeed_opportunity_map.md`, `docs/research/fujiyama_park_case.md`
- **network / trusted sources / security policy** → `docs/research/trusted_sources.md`, `docs/playwright_on_off.md`, `.claude/settings.local.json`
- **how to work / execution pipeline** → `docs/research/execution_pipeline.md`, `docs/research/task_log.md`, `docs/research/hypothesis_protocol.md`
- **test a hypothesis / research agent brief** → `docs/research/hypothesis_protocol.md`, `rules/index.md`, `docs/research/phase2_playbooks.md`, `tools/research/`, `docs/research/tier1_wave1_verdicts.md`
- **recommendations / calls ledger / live board** → `layer3/calls.py`, `run_calls.py`, `scrapers/live_board.py`, `data/master/calls_ledger.csv`, `tests/layer3/test_calls.py`, `tests/scrapers/test_live_board.py`, `docs/superpowers/specs/2026-06-07-calls-engine-design.md`, `docs/research/recommendations_system_discussion.md`
- **what's done / what's next / project state** → `STATUS.md`, `DONE.md`, `CLAUDE.md`, `rules/index.md`
- **improvement backlog / what to build next** → `docs/research/improvement_backlog.md`, `docs/research/fujiyama_park_case.md`, `docs/research/NEXT.md`, `docs/research/future_ideas.md`
- **testing / verification / the showdown** → `tests/`, `tests/data/`, `tests/showdown/`, `tools/mutation/`, `pytest.ini`, `docs/research/showdown_audit.md`, `docs/research/showdown_pipeline_diff.md`, `docs/research/showdown_mutation.md`
- **schema / what a column means** → `docs/schema.md`, `data/master/ipo_analysis.csv`
- **DRHP financials recovery** → `tools/drhp/`, `docs/research/drhp_recovery.md`
- **refresh the data / new IPOs** → `run_refresh.py`, `tools/refresh/`, `data/master/substrate_meta.json`, `data/reference/golden_numbers.json`, `data/reference/manual_overrides.csv`, `layer3/forward_test.py`, `run_forward_test.py`, `docs/WORKFLOWS.md`

## Flow — data pipeline (DAG, canonical order)
```
WEB SOURCES --scrapers/--> data/raw/ + data/reference/ + data/prices/
            --pipeline (below)--> data/master/  --layer3/--> report/ + predictions + app

  00     pipeline/00_build_longterm_spine.py              long-term (2006-19) Chittorgarh spine
  lt/02  pipeline/longterm/02_detail.py                   longterm: attach detail
  lt/03  pipeline/longterm/03_subscription.py             longterm: subscription
  lt/04  pipeline/longterm/04_financials.py               longterm: financials
  01     pipeline/01_build_base.py                        boom base table (2020-25)
  02     pipeline/02_attach_detail.py                     attach Chittorgarh detail
  03     pipeline/03_enrich.py                            Sharescart enrichment
  03b    pipeline/03b_fill_financials_screener.py         pre-IPO financials from screener
  03c    pipeline/03c_fill_subscription_nse.py            NSE subscription
  03d    pipeline/03d_fill_ipowatch.py                    ipowatch SME subscription + GMP
  03e    pipeline/03e_fill_gmp_investorgain.py            investorgain GMP (2nd pass)
  04     pipeline/04_verify.py                            verify tickers
  05     pipeline/05_reconcile.py                         reconcile sources (flag, never merge)
  06     pipeline/06_validate_tickers.py                  validate tickers
  07     pipeline/07_returns_summary.py                   prices -> returns_summary.csv (+MFE/MAE)
  merge  scrapers/screener_prices_merge.py                fold screener weekly prices into returns
  08     pipeline/08_build_universe.py                    build universe.csv (unified features)
  09     pipeline/09_assemble.py                          join -> ipo_analysis.csv (THE substrate)
```

**Exists but NOT wired into run_all (intentional — verify before running):**
- `pipeline/03f_sector_mcap.py` — sector + market_cap_class; folded into 08_build_universe — run standalone only to re-source

## Data products (`data/master/`)
- `data/master/ipo_analysis.csv` — THE Layer-3 substrate: features+outcomes+quality+flags (rows per substrate_meta.json)
- `data/master/universe.csv` — unified feature table (step 08 output)
- `data/master/returns_summary.csv` — price-derived outcomes (step 07 output)
- `data/master/mainboard.csv` — boom mainboard master
- `data/master/sme.csv` — boom SME master
- `data/master/longterm_mainboard.csv` — 2006-19 mainboard master
- `data/master/longterm_sme.csv` — 2006-19 SME master
- `data/master/delisting.csv` — delisting status/date/reason/last_price (INPUT to step 07)
- `data/master/review/` — flag/review registers (gaps, ticker_conflicts, xcheck, ...)
- `data/master/calls_ledger.csv` — the CALLS LEDGER: dated/graded recommendations (run_calls.py owns it)

## Live staging (`data/live/` — display/calls only, never feeds data/master)
- `data/live/board.json` — live+upcoming IPO board snapshot (open[]/upcoming[], GMP, sub)
- `data/live/daywise_sub.csv` — accumulating day-wise subscription dataset (the day-1 question, Branch B)
- `data/live/gmp_history.csv` — pre-listing GMP trajectory (open+upcoming, accumulating; Thread B)

## Tree — directories
- `scrapers/` — ONE file per data SOURCE; fetch RAW only, never transform
- `pipeline/` — numbered build steps (the DAG above) + helpers
- `data/` — raw/ reference/ prices/ master/ (master = the outputs)
- `layer3/` — UI-agnostic analysis engine; reads ipo_analysis.csv only
- `rules/` — the rule/signal/strategy REGISTRY (index.md) — navigate logic here
- `docs/` — sources, schema, pipeline, strategies, layer2/3, research/
- `tests/` — layer3/ + pipeline/ + scrapers/ + data/ (substrate invariants) + showdown/ (SHOWDOWN=1 execution proofs)
- `tools/` — side tools (drhp/ = DRHP recovery; mutation/ = mutation validation; checks/ = schema gate; notify/ = telegram; refresh/; research/)
- `report/` — generated HTML (layer3_partA.html)
- `archive/` — superseded files + dataset backups (e.g. pre_drhp_20260601/)

## Layer-3 engine
- `layer3/config.py` — AS_OF_DATE, thresholds (DEAD_MONEY_RETURN, SEGMENTS, ...) — single source
- `layer3/spine.py` — method engine: distributions, reach_curve, exit/stop strategies, gating
- `layer3/findings/` — the 29 descriptive findings (one file each)
- `layer3/predictor/scorecard.py` — the score COMPONENTS (incl. wipeout_safety, risk gauge)
- `layer3/predictor/weights.py` — data-informed weights (point-in-time rank-IC, cross-regime)
- `layer3/predictor/analogs.py` — comparables / analog selection
- `layer3/predictor/predict.py` — assemble the full 'Evaluate this IPO' report
- `layer3/backtest/` — engine + analyses + score_backtest (vs do-nothing)
- `layer3/validate.py` — cross-regime validation (boom vs 2006-19)
- `layer3/calls.py` — CALLS ENGINE: event-anchored point-in-time calls + gap-fill walk + grading
- `layer3/portfolio.py` — PAPER-PORTFOLIO sim (₹1L/APPLY vs Nifty) + per-stock growth-of-₹1L (3 lenses)
- `layer3/calibration.py` — were-we-right scorecard + Wilson CIs + score-ordering reliability (no scipy)

## Rules & state
- `rules/index.md` — navigable REGISTRY: every signal/component/strategy — status (in-score/display-only/rejected) + WHY + backtest lift/N/cross-regime. Consult before re-testing any signal.
- `rules/README.md` — the registry entry template
- `CLAUDE.md` — conventions/decisions/repo-map (the brain; auto-loaded)
- `STATUS.md` — live 'where are we / what's next' (verify from ground truth, never memory)
- `DONE.md` — append-only history

## Invariants (re-derived by verify.py)
- n_findings = 29
- substrate_rows = 2384
- as_of_date = 2026-06-06
- archive_pointer = archive/pre_refresh_20260606
