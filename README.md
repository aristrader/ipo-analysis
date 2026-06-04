# IPO Pattern Analysis

Indian IPO dataset (Mainboard + SME, 2006–2025, incl. delisted) for repeatable-pattern research. Not financial advice.

> **Resume the main Claude Code session** (run from this directory):
> ```
> claude --resume 01820f2d-c29a-4f29-84ad-349ce26b70fa
> ```
> (or `claude --resume` and pick the top one; `claude -c` continues the most recent.)

## Start here (read in order)
1. `CLAUDE.md` — the project brain (3-layer status, conventions, run order) — read first
2. `docs/sources.md` — what each data site provides (free/premium/coverage)
3. `docs/schema.md` — the master dataset columns and where each comes from
4. `docs/pipeline.md` — how the dataset is built (run order)
5. `docs/strategies.md` + `docs/layer3.md` — the analysis design; `rules/index.md` — the findings + results

## Folder map
- `scrapers/` — one file per data source; each fetches raw data only.
- `pipeline/` — numbered build steps (00→09 + 03b–03e + `longterm/`), run in sequence. `pipeline/checks/` validates each.
- `data/raw/` — untouched scraped data, per source.
- `data/reference/` — NSE/BSE symbol↔ISIN lists, bhavcopy cache, corp_actions, indices.
- `data/master/` — THE outputs: `ipo_analysis.csv`, `universe.csv`, `returns_summary.csv`, `{mainboard,sme}.csv`,
  `{longterm_mainboard,longterm_sme}.csv` (+ `_base_*` staging, `delisting.csv`). `data/master/review/` holds review/flag CSVs.
- `layer3/` — the analysis engine (Layer 3): `spine.py` (method spine) + `findings/` (descriptive report) +
  `predictor/` (analog predictor + scorecard) + `backtest/` (strategy backtester). UI-agnostic.
- `report/` — generated HTML report output. `rules/` — navigable registry of every finding/rule + its result.
- `archive/` — superseded scripts + old datasets (kept for rollback + reconciliation).
- `docs/` — sources, schema, pipeline, strategies, layer2/layer3, patterns, decisions, changelog, `research/` (review logs).

## Build the dataset (Layers 1–2)
```bash
source .venv/bin/activate
# whole pipeline in canonical order (--from <step> to resume, --list for step keys):
PYTHONPATH=. python run_all.py
```

## Analyze (Layer 3)
```bash
source .venv/bin/activate
PYTHONPATH=. python run_layer3_report.py        # → open report/layer3_partA.html (descriptive findings)
PYTHONPATH=. python predict_ipo.py --type MB --sector Finance --mcap mid --profitable 1 --ofs_pct 60
                                                # score a NEW IPO vs historical analogs (--help for all options)
PYTHONPATH=. python run_backtest.py             # strategy backtest vs the do-nothing baseline
PYTHONPATH=. python run_validation.py           # cross-regime sign-validation
PYTHONPATH=. pytest tests/layer3/ -q            # 77 tests
```
Note: `alpha` = market-adjusted return measured from the LISTING price (the secondary-buyer's view); the
allottee additionally captures the listing-day pop. Returns benchmarked to Nifty 50 (Smallcap-250 for small/micro).

### Interactive app (everything in one browser UI)
```bash
pip install streamlit                           # one-time
PYTHONPATH=. streamlit run app.py               # → http://localhost:8501
```
Tabs: **Findings report** · **Score a new IPO** (predictor form) · **Backtester** · **Validation & rules**.

## Key principle
ISIN is the primary key and the only automatic match key. Name-matching never merges data.
