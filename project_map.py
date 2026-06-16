"""SINGLE SOURCE OF TRUTH for repo structure, data flow, and navigation.

Why this file exists: structure used to live as prose scattered across CLAUDE.md,
run_all.py, and docs/ — so it drifted (e.g. a pipeline step existing but not wired,
stale counts). This module is the ONE machine-readable description. Three things
consume it:
  * run_all.py        derives its pipeline step order from PIPELINE (one DAG source).
  * verify.py         asserts every path here exists + invariants hold, and regenerates MAP.md.
  * MAP.md            is GENERATED from render_map() — never hand-edit it.

THE RULE (also in CLAUDE.md): when you add/move/retire a file, pipeline step, data
product, or signal — update THIS file. verify.py (run automatically each turn) will
flag the drift if you forget. Keep entries one line; this is a map, not documentation.
"""

# --------------------------------------------------------------------------- DAG
# The pipeline, in canonical run order. run_all.py builds its STEPS from this list.
# Each: (key passed to `run_all.py --from`, path, one-line role).
PIPELINE = [
    ("00",    "pipeline/00_build_longterm_spine.py",         "long-term (2006-19) Chittorgarh spine"),
    ("lt/02", "pipeline/longterm/02_detail.py",              "longterm: attach detail"),
    ("lt/03", "pipeline/longterm/03_subscription.py",        "longterm: subscription"),
    ("lt/04", "pipeline/longterm/04_financials.py",          "longterm: financials"),
    ("01",    "pipeline/01_build_base.py",                   "boom base table (2020-25)"),
    ("02",    "pipeline/02_attach_detail.py",                "attach Chittorgarh detail"),
    ("03",    "pipeline/03_enrich.py",                       "Sharescart enrichment"),
    ("03b",   "pipeline/03b_fill_financials_screener.py",    "pre-IPO financials from screener"),
    ("03c",   "pipeline/03c_fill_subscription_nse.py",       "NSE subscription"),
    ("03d",   "pipeline/03d_fill_ipowatch.py",               "ipowatch SME subscription + GMP"),
    ("03e",   "pipeline/03e_fill_gmp_investorgain.py",       "investorgain GMP (2nd pass)"),
    ("04",    "pipeline/04_verify.py",                       "verify tickers"),
    ("05",    "pipeline/05_reconcile.py",                    "reconcile sources (flag, never merge)"),
    ("06",    "pipeline/06_validate_tickers.py",             "validate tickers"),
    ("07",    "pipeline/07_returns_summary.py",              "prices -> returns_summary.csv (+MFE/MAE)"),
    ("merge", "scrapers/screener_prices_merge.py",           "fold screener weekly prices into returns"),
    ("08",    "pipeline/08_build_universe.py",               "build universe.csv (unified features)"),
    ("09",    "pipeline/09_assemble.py",                     "join -> ipo_analysis.csv (THE substrate)"),
]

# Files that EXIST but are intentionally NOT in the DAG. Listed so verify.py can tell
# "deliberately standalone" from "accidentally dropped" (the 03f-class goof-up).
UNWIRED = [
    ("pipeline/03f_sector_mcap.py",
     "sector + market_cap_class; folded into 08_build_universe — run standalone only to re-source"),
]

# Shared, non-numbered pipeline helpers (imported by the numbered steps).
PIPELINE_HELPERS = {
    "pipeline/lib.py":                 "pure helpers fnum/num/last_pre_listing_fy (imported by 08/03b/03d/03e)",
    "pipeline/listing_remediation.py": "listing-coverage remediation (used by 07 + the merge)",
    "pipeline/checks/":                "per-step validators",
    "pipeline/longterm/":              "2006-19 cohort enrichment steps",
}

# ----------------------------------------------------------------- data products
# data/master/ — the canonical outputs. THE one to start from is ipo_analysis.csv.
DATA_PRODUCTS = {
    "data/master/ipo_analysis.csv":   "THE Layer-3 substrate: features+outcomes+quality+flags (rows per substrate_meta.json)",
    "data/master/universe.csv":       "unified feature table (step 08 output)",
    "data/master/returns_summary.csv":"price-derived outcomes (step 07 output)",
    "data/master/mainboard.csv":      "boom mainboard master",
    "data/master/sme.csv":            "boom SME master",
    "data/master/longterm_mainboard.csv": "2006-19 mainboard master",
    "data/master/longterm_sme.csv":   "2006-19 SME master",
    "data/master/delisting.csv":      "delisting status/date/reason/last_price (INPUT to step 07)",
    "data/master/review/":            "flag/review registers (gaps, ticker_conflicts, xcheck, ...)",
    "data/master/calls_ledger.csv":   "the CALLS LEDGER: dated/graded recommendations (scripts/run_calls.py owns it)",
    "data/master/forward_test_history.csv": "F2 credibility spine: append-only OOS were-we-right snapshot per refresh vintage (scripts/run_forward_test.py)",
}

# live staging (scrapers/live_board.py writes here; NEVER feeds data/master directly)
DATA_LIVE = {
    "data/live/board.json":       "live+upcoming IPO board snapshot (open[]/upcoming[], GMP, sub)",
    "data/live/daywise_sub.csv":  "accumulating day-wise subscription dataset (the day-1 question, Branch B)",
    "data/live/gmp_history.csv":  "pre-listing GMP trajectory (open+upcoming, accumulating; Thread B)",
    "data/live/news/":            "NSE corporate-announcements staging (D1/D4 context feed; announcements_staging.csv + coverage_misses.csv; display-only, join by SYMBOL)",
}

# raw + reference inputs (scrapers write here; pipeline reads here)
DATA_INPUTS = {
    "data/raw/<source>/":             "raw scraped payloads (one dir per scraper)",
    "data/reference/":                "exchange lists, bhavcopy cache, corp_actions.csv, indices/",
    "data/prices/<isin>.csv":         "daily split/bonus-adjusted OHLCV per ISIN",
}

# ---------------------------------------------------------------------- top dirs
DIRS = {
    "scrapers/": "ONE file per data SOURCE; fetch RAW only, never transform",
    "pipeline/": "numbered build steps (the DAG above) + helpers",
    "data/":     "raw/ reference/ prices/ master/ (master = the outputs)",
    "layer3/":   "UI-agnostic analysis engine; reads ipo_analysis.csv only",
    "rules/":    "the rule/signal/strategy REGISTRY (index.md) — navigate logic here",
    "docs/":     "sources, schema, pipeline, strategies, layer2/3, research/",
    "tests/":    "layer3/ + pipeline/ + scrapers/ + data/ (substrate invariants) + showdown/ (SHOWDOWN=1 execution proofs)",
    "tools/":    "side tools (drhp/ = DRHP recovery; mutation/ = mutation validation; checks/ = schema gate; notify/ = telegram; refresh/; research/)",
    "report/":   "generated HTML (layer3_partA.html)",
    "archive/":  "superseded files + dataset backups (e.g. pre_drhp_20260601/)",
    "thinktank/memory/":  "onboarding pack for a fresh account/session: README (read-order + conventions) + auto_memory/ (copied, won't-travel) + ENVIRONMENT.md (gitignored config to recreate)",
}

# ------------------------------------------------------------------- layer3 core
LAYER3 = {
    "layer3/config.py":   "AS_OF_DATE, thresholds (DEAD_MONEY_RETURN, SEGMENTS, ...) — single source",
    "layer3/spine.py":    "method engine: distributions, reach_curve, exit/stop strategies, gating",
    "layer3/findings/":   "the 29 descriptive findings (one file each)",
    "layer3/predictor/scorecard.py": "the score COMPONENTS (incl. wipeout_safety, risk gauge)",
    "layer3/predictor/weights.py":   "data-informed weights (point-in-time rank-IC, cross-regime)",
    "layer3/predictor/analogs.py":   "comparables / analog selection",
    "layer3/predictor/predict.py":   "assemble the full 'Evaluate this IPO' report",
    "layer3/news/taxonomy.py":       "local rule-based announcement categories + look-ahead-safe actionable_from (no LLM/polarity)",
    "layer3/news/staging.py":        "normalize NSE announcement rows + idempotent upsert (display overlay, never substrate)",
    "layer3/backtest/":   "engine + analyses + score_backtest (vs do-nothing)",
    "layer3/validate.py": "cross-regime validation (boom vs 2006-19)",
    "layer3/calls.py":    "CALLS ENGINE: event-anchored point-in-time calls + gap-fill walk + grading",
    "layer3/portfolio.py":"PAPER-PORTFOLIO sim (₹1L/APPLY vs Nifty) + per-stock growth-of-₹1L (3 lenses)",
    "layer3/calibration.py":"were-we-right scorecard + Wilson CIs + score-ordering reliability (no scipy)",
}

# --------------------------------------------------------------------- run it
ENTRYPOINTS = {
    "PYTHONPATH=. python run_all.py":            "build the dataset (whole pipeline DAG; --from to resume)",
    "PYTHONPATH=. python run_layer3_report.py":  "build report/layer3_partA.html (29 findings)",
    "PYTHONPATH=. python scripts/predict_ipo.py --type MB --sector ...": "score/evaluate a new IPO",
    "PYTHONPATH=. python scripts/run_backtest.py":       "strategy backtests",
    "PYTHONPATH=. python scripts/run_validation.py":     "cross-regime validation",
    "PYTHONPATH=. python scripts/run_weights.py":        "derive data-informed weights",
    "PYTHONPATH=. python -m pytest tests -q":    "run all tests",
    "PYTHONPATH=. streamlit run app.py":         "the interactive app (5 tabs)",
    "python verify.py":                          "structure/invariant checkpoint + regenerate MAP.md",
    "PYTHONPATH=. python scripts/run_refresh.py":        "bring the dataset to today (dry-run; --apply executes)",
    "PYTHONPATH=. python scripts/run_forward_test.py":   "score the never-seen post-refresh cohort (EARLY READ)",
    "PYTHONPATH=. python scripts/run_calls.py":          "calls ledger: cursor walk/gap-fill (--backfill, --grade-only, --report)",
    "PYTHONPATH=. python scripts/run_portfolio.py":      "₹1L paper-portfolio sim vs Nifty (--stock ISIN = per-stock growth)",
    "PYTHONPATH=. python scripts/run_scorecard.py":      "were-we-right scorecard + score-ordering (--horizon 1m/3m/1y)",
    "PYTHONPATH=. python scrapers/live_board.py": "fetch the live+upcoming IPO board -> data/live/",
    "PYTHONPATH=. python scrapers/announcements.py": "collect NSE corporate-announcement history -> data/live/news/ (D1/D4; --limit/--symbols)",
}

# ------------------------------------------------------- where the rules/state live
RULES_AND_STATE = {
    "rules/index.md":  "navigable REGISTRY: every signal/component/strategy — status (in-score/display-only/"
                       "rejected) + WHY + backtest lift/N/cross-regime. Consult before re-testing any signal.",
    "rules/README.md": "the registry entry template",
    "CLAUDE.md":       "conventions/decisions/repo-map (the brain; auto-loaded)",
    "docs/tracker/STATUS.md":       "live 'where are we / what's next' (verify from ground truth, never memory)",
}

# ------------------------------------------------------------ CONTEXT INDEX
# "I'm working on X -> go to these files." The router for context-fetching.
CONTEXTS = {
    "score / evaluate a new IPO": [
        "layer3/predictor/scorecard.py", "layer3/predictor/weights.py",
        "layer3/predictor/predict.py", "layer3/predictor/analogs.py",
        "rules/index.md", "scripts/predict_ipo.py", "tests/layer3/test_predictor.py",
    ],
    "add / edit a finding": [
        "layer3/findings/", "layer3/spine.py", "layer3/report.py",
        "scripts/run_layer3_report.py", "tests/layer3/test_findings.py", "rules/index.md",
    ],
    "prices / returns / MFE-MAE / listing-day": [
        "pipeline/07_returns_summary.py", "scrapers/screener_prices_merge.py",
        "pipeline/listing_remediation.py", "tests/pipeline/test_returns_math.py",
        "tests/pipeline/test_listing_remediation.py",
    ],
    "build / fix the dataset (pipeline)": [
        "run_all.py", "project_map.py", "docs/pipeline.md", "pipeline/", "pipeline/lib.py",
    ],
    "scrapers / data sources": [
        "scrapers/", "scrapers/nse_session.py", "docs/sources.md", "tests/scrapers/",
    ],
    "news / announcement context feed (D1/D4)": [
        "scrapers/announcements.py", "layer3/news/taxonomy.py", "layer3/news/staging.py",
        "tests/layer3/test_news.py", "data/live/news/",
        "docs/research/newsfeed_rnd_2026-06-09.md", "docs/research/newsfeed_opportunity_map.md",
    ],
    "backtest a strategy": [
        "layer3/backtest/", "scripts/run_backtest.py", "docs/strategies.md",
        "tests/layer3/test_backtest.py", "tests/layer3/test_score_backtest.py",
    ],
    "cross-regime validation / OOS": [
        "layer3/validate.py", "scripts/run_validation.py", "scripts/run_oos.py", "tests/layer3/test_validate.py",
    ],
    "the app / UI": ["app.py", "docs/research/app_phase2_design.md",
                     "docs/research/recommendations_system_discussion.md",
                     "docs/research/newsfeed_opportunity_map.md",
                     "docs/research/fujiyama_park_case.md"],
    "network / trusted sources / security policy": [
        "docs/research/trusted_sources.md", "docs/playwright_on_off.md", "thinktank/config/settings.local.json",
    ],
    "how to work / execution pipeline": [
        "docs/research/execution_pipeline.md", "docs/tracker/task_log.md",
        "docs/research/hypothesis_protocol.md",
    ],
    "test a hypothesis / research agent brief": [
        "docs/research/hypothesis_protocol.md", "rules/index.md",
        "docs/research/phase2_playbooks.md", "tools/research/",
        "docs/research/tier1_wave1_verdicts.md",
    ],
    "recommendations / calls ledger / live board": [
        "layer3/calls.py", "scripts/run_calls.py", "scrapers/live_board.py",
        "data/master/calls_ledger.csv", "tests/layer3/test_calls.py",
        "tests/scrapers/test_live_board.py",
        "docs/superpowers/specs/2026-06-07-calls-engine-design.md",
        "docs/research/recommendations_system_discussion.md",
    ],
    "what's done / what's next / project state": ["docs/tracker/STATUS.md", "CLAUDE.md", "rules/index.md"],
    "improvement backlog / what to build next": [
        "docs/tracker/improvement_backlog.md", "docs/research/fujiyama_park_case.md",
        "docs/research/INDEX.md",   # map of all research docs (active + archived feeders)
    ],
    "testing / verification / the showdown": [
        "tests/", "tests/data/", "tests/showdown/", "tools/mutation/", "pytest.ini",
        "docs/research/showdown_audit.md", "docs/research/showdown_pipeline_diff.md",
        "docs/research/showdown_mutation.md",
    ],
    "schema / what a column means": ["docs/schema.md", "data/master/ipo_analysis.csv"],
    "DRHP financials recovery": ["tools/drhp/", "docs/research/drhp_recovery.md"],
    "refresh the data / new IPOs": [
        "scripts/run_refresh.py", "tools/refresh/", "data/master/substrate_meta.json",
        "data/reference/golden_numbers.json", "data/reference/manual_overrides.csv",
        "layer3/forward_test.py", "scripts/run_forward_test.py", "docs/WORKFLOWS.md",
    ],
}

# ------------------------------------------------------------ TEST ROUTING
# "You changed X -> run THESE tests." Ordered; FIRST match wins; '*' = fallback.
# verify.py maps `git status` changes through this and injects the commands into
# the assistant's context every turn (mechanical, not memory). `--route` = on demand.
# SHOWDOWN=1 pytest tests/showdown = the pre-release gate (docs/WORKFLOWS.md).
TEST_ROUTING = [
    ("app/ui.py", ["PYTHONPATH=. pytest tests/app -q"]),
    ("app/", ["PYTHONPATH=. pytest tests/app -q",
              "SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_app_smoke.py -q  # browser boot"]),
    ("app.py", ["SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_app_smoke.py -q"]),
    ("layer3/calls.py", ["PYTHONPATH=. pytest tests/layer3/test_calls.py -q"]),
    ("layer3/portfolio.py", ["PYTHONPATH=. pytest tests/layer3/test_portfolio.py -q"]),
    ("scripts/run_portfolio.py", ["PYTHONPATH=. pytest tests/layer3/test_portfolio.py -q"]),
    ("layer3/calibration.py", ["PYTHONPATH=. pytest tests/layer3/test_calibration.py -q"]),
    ("scripts/run_scorecard.py", ["PYTHONPATH=. pytest tests/layer3/test_calibration.py -q"]),
    ("tools/checks/schema_gate.py", ["PYTHONPATH=. pytest tests/checks -q"]),
    ("scrapers/live_board.py", ["PYTHONPATH=. pytest tests/scrapers/test_live_board.py -q"]),
    ("scripts/run_calls.py", ["PYTHONPATH=. pytest tests/layer3/test_calls.py -q"]),
    ("scrapers/live_board.py", ["PYTHONPATH=. pytest tests/scrapers/test_live_board.py -q"]),
    ("scrapers/announcements.py", ["PYTHONPATH=. pytest tests/layer3/test_news.py -q"]),
    ("layer3/news/*", ["PYTHONPATH=. pytest tests/layer3/test_news.py -q"]),
    ("pipeline/07_returns_summary.py",
     ["PYTHONPATH=. pytest tests/pipeline tests/data -q",
      "SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_pipeline_sandbox.py -q  # before release"]),
    ("scrapers/screener_prices_merge.py",
     ["PYTHONPATH=. pytest tests/pipeline/test_merge_math.py tests/data -q",
      "SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_pipeline_sandbox.py -q  # before release"]),
    ("pipeline/listing_remediation.py", ["PYTHONPATH=. pytest tests/pipeline -q"]),
    ("pipeline/lib.py", ["PYTHONPATH=. pytest tests/pipeline -q"]),
    ("pipeline/*", ["PYTHONPATH=. pytest tests/pipeline tests/data -q",
                    "SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_pipeline_sandbox.py -q  # before release"]),
    ("layer3/predictor/*", ["PYTHONPATH=. pytest tests/layer3/test_predictor.py tests/layer3/test_weights.py "
                            "tests/layer3/test_oos.py tests/layer3/test_gap_math.py -q"]),
    ("layer3/backtest/*", ["PYTHONPATH=. pytest tests/layer3/test_backtest.py tests/layer3/test_analyses.py "
                           "tests/layer3/test_score_backtest.py tests/layer3/test_gap_math.py -q"]),
    ("layer3/findings/*", ["PYTHONPATH=. pytest tests/layer3/test_findings.py tests/layer3/test_report.py -q"]),
    ("layer3/spine.py", ["PYTHONPATH=. pytest tests/layer3 -q"]),
    ("layer3/config.py", ["PYTHONPATH=. pytest tests -q  # config feeds everything"]),
    ("layer3/*", ["PYTHONPATH=. pytest tests/layer3 -q"]),
    ("scrapers/*", ["PYTHONPATH=. pytest tests/scrapers -q"]),
    ("data/master/*", ["PYTHONPATH=. pytest tests/data -q"]),
    ("app.py", ["SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown/test_app_smoke.py -q"]),
    ("scripts/run_refresh.py", ["PYTHONPATH=. pytest tests/pipeline/test_refresh_lib.py tests/data -q"]),
    ("layer3/forward_test.py", ["PYTHONPATH=. pytest tests/layer3/test_forward_test.py -q"]),
    ("scripts/run_forward_test.py", ["PYTHONPATH=. pytest tests/layer3/test_forward_test.py -q"]),
    ("tools/refresh/*", ["PYTHONPATH=. pytest tests/pipeline/test_refresh_lib.py tests/data -q"]),
    ("project_map.py", ["PYTHONPATH=. pytest tests/test_project_map.py -q"]),
    ("verify.py", ["PYTHONPATH=. pytest tests/test_project_map.py -q"]),
    ("tests/*", ["PYTHONPATH=. pytest tests -q"]),
    ("*", ["PYTHONPATH=. pytest tests -q  # fallback: full fast suite"]),
]

# --------------------------------------------------------------- INVARIANTS
# Ground-truth facts the checkpoint re-derives and compares. STRUCTURAL facts are
# literals; MOVABLE facts (rows / as-of / backup pointer) come from
# data/master/substrate_meta.json, which only `scripts/run_refresh.py --apply` writes —
# so a refresh updates the rails as data, never as code edits.
def _meta():
    import json
    import os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data/master/substrate_meta.json")
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return {"as_of": "2026-05-31", "rows": 2296, "archive_pointer": "archive/pre_drhp_20260601"}


_M = _meta()
INVARIANTS = {
    "n_findings":     29,                    # ls layer3/findings/*.py minus __init__ (structural)
    "substrate_rows": int(_M["rows"]),       # csv records in ipo_analysis.csv (NOT wc -l)
    "as_of_date":     _M["as_of"],           # layer3/config.AS_OF_DATE reads the same meta
    "archive_pointer": _M.get("archive_pointer", ""),
    # exact test count comes from `pytest --co` (run by `python verify.py`, not the fast hook).
}


# --------------------------------------------------------------- helpers
def dag_steps():
    """(key, path) pairs in run order — run_all.py builds its STEPS from this."""
    return [(key, path) for key, path, _role in PIPELINE]


def all_referenced_paths():
    """Every concrete path mentioned in the map (for verify.py existence checks).
    Skips template paths containing '<' and bare commands."""
    paths = set()
    for _k, p, _r in PIPELINE:
        paths.add(p)
    for p, _r in UNWIRED:
        paths.add(p)
    for d in (PIPELINE_HELPERS, DATA_PRODUCTS, DATA_LIVE, DIRS, LAYER3, RULES_AND_STATE):
        paths.update(d.keys())
    for files in CONTEXTS.values():
        paths.update(files)
    return {p for p in paths if "<" not in p}


def render_map():
    """Generate MAP.md from the structures above. Never hand-edit MAP.md."""
    L = []
    L.append("# MAP — generated, do not edit (source: project_map.py; run `python verify.py` to refresh)\n")
    L.append("> Navigation, data-flow, and a context index for this repo. Generated from `project_map.py`.\n")

    L.append("## Navigate — to do X, start here")
    for cmd, what in ENTRYPOINTS.items():
        L.append(f"- `{cmd}` — {what}")
    L.append("")

    L.append("## Context index — working on X? open these")
    for ctx, files in CONTEXTS.items():
        L.append(f"- **{ctx}** → {', '.join('`%s`' % f for f in files)}")
    L.append("")

    L.append("## Flow — data pipeline (DAG, canonical order)")
    L.append("```")
    L.append("WEB SOURCES --scrapers/--> data/raw/ + data/reference/ + data/prices/")
    L.append("            --pipeline (below)--> data/master/  --layer3/--> report/ + predictions + app")
    L.append("")
    for key, path, role in PIPELINE:
        L.append(f"  {key:6s} {path:48s} {role}")
    L.append("```")
    if UNWIRED:
        L.append("\n**Exists but NOT wired into run_all (intentional — verify before running):**")
        for p, role in UNWIRED:
            L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Data products (`data/master/`)")
    for p, role in DATA_PRODUCTS.items():
        L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Live staging (`data/live/` — display/calls only, never feeds data/master)")
    for p, role in DATA_LIVE.items():
        L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Tree — directories")
    for p, role in DIRS.items():
        L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Layer-3 engine")
    for p, role in LAYER3.items():
        L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Rules & state")
    for p, role in RULES_AND_STATE.items():
        L.append(f"- `{p}` — {role}")
    L.append("")

    L.append("## Invariants (re-derived by verify.py)")
    for k, v in INVARIANTS.items():
        L.append(f"- {k} = {v}")
    L.append("")
    return "\n".join(L)
