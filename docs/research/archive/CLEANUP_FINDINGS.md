# Cleanup findings — handoff for the cleanup chat

**Compiled:** 2026-06-02 · **Scope:** read-only sweep of the whole repo (pipeline, layer3, scrapers, tests, docs, root/config). No changes were made producing this list.

## How to use this doc
- Findings are grouped by area, each with **severity / file:line / problem / fix**.
- **Line numbers are best-effort** from a point-in-time scan — `grep` to confirm before editing (the codebase is moving; several files were touched in the last 48h).
- **No version control exists** (see INFRA-1), so there's no diff/rollback safety net. Doing INFRA-1 first is strongly advised before any refactor.
- Severity = HIGH (correctness / blocks fresh clone / no safety net), MED (maintainability debt that's growing), LOW (polish).

## Canonical facts (verified 2026-06-02 — use these to reconcile docs)
- **29 findings** (`ls layer3/findings/*.py | grep -v __init__ | wc -l` = 29; all 29 ARE registered in `run_layer3_report.py` `FINDINGS` — no missing registrations).
- **77 tests** (`pytest tests/ --collect-only` = 77).
- **~12,800 lines** of Python (excl. `.venv`/`__pycache__`/`archive`); +2,200 in `archive/`. ~9,000 lines of markdown docs.
- `EXECUTION_STATUS.md` is the current live status tracker; `DONE.md` is a dated changelog (its older entries showing 20/26/28 findings are historical-by-design — NOT bugs; only reconcile the *headline/most-recent* references elsewhere).

---

## INFRA — repo-wide infrastructure (do these first)

- **INFRA-1 · HIGH · repo root** — Not a git repo. No history, no rollback; the growing `archive/` (17 MB) is a manual substitute for what git would do. **Fix:** `git init` + first commit after INFRA-2.
- **INFRA-2 · HIGH · no `.gitignore`** — Without it, a first commit sweeps in `.venv/` (662 MB), `__pycache__/`, `.pytest_cache/`, `logs/` (47 files, 3.4 MB), and arguably `archive/` (17 MB) + `data/raw/`. **Fix:** add `.gitignore`:
  ```
  .venv/
  __pycache__/
  *.pyc
  .pytest_cache/
  logs/
  *.egg-info/
  .DS_Store
  ```
  (decide separately whether `archive/`, `data/raw/`, `data/prices/` belong in git or in external storage.)
- **INFRA-3 · HIGH · no `pyproject.toml` / `setup.py`** — Package isn't installable, forcing `PYTHONPATH=.` on every invocation (see ROOT-2). **Fix:** add a minimal `pyproject.toml` with `[project]`, deps, and `[tool.pytest.ini_options]`; then `pip install -e .` removes all `PYTHONPATH=.` prefixes.
- **INFRA-4 · MED · clutter to clean once ignored** — `logs/` (47 files), `__pycache__/` across 5 dirs, `.pytest_cache/`, and `archive/` (17 MB, grew from 11 MB). **Fix:** gitignore + a one-line `make clean`; document which `archive/` subdirs (`pre_integration_*`) are worth keeping.

## DEPS — dependencies & packaging

- **DEPS-1 · HIGH · `requirements.txt`** — `streamlit` is imported by `app.py` but **not listed**; `pytest` also missing. A fresh clone can't launch the app or run tests. **Fix:** add `streamlit`, `pytest` (+ `numpy` explicitly).
- **DEPS-2 · HIGH · `requirements.txt`** — Nothing is version-pinned (`requests`, `pandas`, `cloudscraper`, `beautifulsoup4`, `lxml` all unpinned). **Fix:** pin all (`pip freeze` the working `.venv`); consider splitting `requirements-dev.txt` (pytest) from prod.

---

## PIPELINE (`pipeline/`)

### HIGH
- **PIPE-1 · duplicated `fnum()`** in `03b_fill_financials_screener.py:44`, `03d_fill_ipowatch.py:21`, `03e_fill_gmp_investorgain.py:22`, `08_build_universe.py:91`. **Fix:** move to new `pipeline/lib.py`, import in all.
- **PIPE-2 · duplicated `num()`** in `03b_…:40`, `05_reconcile.py:12`, `08_build_universe.py:87`. **Fix:** `pipeline/lib.py`.
- **PIPE-3 · duplicated `last_pre_listing_fy()`** in `03b_…:33` and `08_build_universe.py:80` (08:68 comment even says "exact logic from 03b" but copies it). **Fix:** `pipeline/lib.py`.
- **PIPE-4 · duplicated `YR_METRICS`/`YR_COLS` constants** in `03b_…:51`, `08_build_universe.py:98`, `longterm/04_financials.py:37`. **Fix:** `pipeline/lib.py` module constants.
- **PIPE-5 · god-function `compute()`** at `07_returns_summary.py:247` (~260 lines): price-adjustment + horizons + corp-action + MFE/MAE + delisting + classification in one function — the most correctness-critical, least-testable code in the pipeline. **Fix:** decompose into `compute_price_metrics / compute_horizons / compute_wipeout / classify_outcome`, orchestrate in `compute()`.
- **PIPE-6 · fragile coupling** — `07_returns_summary.py:23` imports `listing_remediation` via `sys.path` injection (also used by `screener_prices_merge`). Hidden, breaks if moved. **Fix:** make `pipeline/` a package (`__init__.py`) and use normal imports, or move shared logic into `pipeline/lib.py`.

### MED
- **PIPE-7 · `checks/` not wired into the chain** — `pipeline/checks/` has `check_01…check_05` + `check_chittorgarh`, but `run_all.py` invokes none (verified: 0 references). Validation is manual/optional → a bad step flows downstream silently. **Fix:** add a `--checks` mode to `run_all.py` that runs each step's check and fails fast.
- **PIPE-8 · inconsistent ROOT/path handling** — some steps hardcode relative paths (`'data/master/_base_*.csv'`), others compute `ROOT`+`os.path.join`; `p()` path-helper duplicated in `08:18`, `03f_sector_mcap.py:38`, `research/recover_inwindow_financials.py:21`, `research/enrich_recovery.py:33`; root variable named `ROOT`/`BASE`/`BASE_DIR` across files. **Fix:** central `pipeline/lib.py` path constants + one `ROOT`.
- **PIPE-9 · missing type hints/docstrings on core fns** — `07_returns_summary.py` `pdate:40`, `pfloat:53`, `compute:247`, `columns:511`, `fmt:533`; `08` `last_pre_listing_fy/num/fnum`. **Fix:** add signatures + one-line docstrings.
- **PIPE-10 · large `listing_remediation.remediate_listing()`** (~114 lines, no docstring/types). **Fix:** split `_implied_factor / _check_unrecorded_split / _check_bad_coverage / _adjust_for_split`.
- **PIPE-11 · no boundary validation between steps** — late steps trust upstream column shape. **Fix:** assert required columns + ISIN-uniqueness at the top of each step.

### LOW
- **PIPE-12 · `pipeline/research/` disconnected** — `recover_inwindow_financials.py`, `enrich_recovery.py` not referenced by `run_all.py` or any step; `recover_inwindow_financials.py:33` reads a hardcoded `/tmp/inwin_cands.json`. **Fix:** document as one-off scripts or move to `scripts/research/`; parameterize the input path.
- **PIPE-13 · no `__init__.py`** in `pipeline/` or subdirs → implicit imports. **Fix:** add empty `__init__.py`.
- **PIPE-14 · `load_nifty()` (`07:147`) loads more than nifty** — misleading name. **Fix:** rename/split.

---

## LAYER3 (`layer3/`)

> Architecture here is the strongest in the repo (clean `spine.py` method-chokepoint, uniform `compute(df)->Finding` contract, centralized `load_substrate`). Findings below are debt, not rot.

### HIGH
- **L3-1 · LIVE BUG: hardcoded date** — `findings/t2_survival.py:13` `TODAY = date(2026, 5, 31)`. Survival/age is computed against a frozen past date (already wrong as of today). **Fix:** `date.today()` or inject as a param.
- **L3-2 · duplicate magic threshold, two names** — `DEAD_THRESHOLD = -0.50` (`findings/n14_wipeout_anatomy.py:29`) and `ZOMBIE_THRESHOLD = -0.50` (`findings/n9_zombie.py:12`) are the same dead-money cutoff. **Fix:** one `DEAD_MONEY_RETURN = -0.50` in `config.py`, import both.
- **L3-3 · no type hints on public API** — `spine.py` (~30 public fns, e.g. `load_substrate`, `distribution`, `wilson_ci`), `predictor/scorecard.py` (~14 fns), `predictor/weights.py` (~12 fns). **Fix:** annotate signatures + returns.

### MED
- **L3-4 · `_p()` percentage-formatter copy-pasted across ~19 findings** (`def _p(x): return None if x is None else round(100*x,1)`), with inconsistent null-checks (`x is None` vs `x is None or pd.isna(x)`). Locations: `t1_base_rates:89`, `t2_survival:79`, `t3_pop_fade:103`, `t5_ofs:60`, `t6_sector:78`, `t8_drawdown:90`, `t9_profitable:72`, `n2_subscription:68`, `n3_demand_skew:55`, `n4_issue_size:83`, `n5_anchor:61`, `n6_valuation:62`, `n7_fundamentals:63`, `n8_accrual:53`, `n9_zombie:93`, `n10_migration:65`, `n11_sc_divergence:55`, `n12_banker:64`, `nonequity:42`. **Fix:** single `spine.pct()` (a `pct()` already exists at `spine.py:514`), import everywhere, standardize the null-check.
- **L3-5 · scattered bucket/band definitions** — `t3_pop_fade.py:14` (pop buckets), `t5_ofs.py:12` (OFS buckets), `n2_subscription.py:13` (subscription bands), `n4_issue_size.py:14` (size bands). **Fix:** centralize in `config.py` as named constants.
- **L3-6 · scattered classification thresholds** — `t8_drawdown.py:26,50,58` (`-0.50/-0.30/0.20`), `n5_anchor.py:17` (`0.60` cap), `n10_migration.py:17,19,21` (`-0.20/0.20/1.00`), `predict.py:126-127` (`0.25` barbell), `predict.py:155` (`0.3` confidence). **Fix:** name them at module top or in `config.py`.
- **L3-7 · `numpy` imported inside function bodies** — `spine.py:121,243,267,397,446`, `predict.py:119`, `backtest/score_backtest.py:45`. **Fix:** hoist `import numpy as np` to module level.

### LOW
- **L3-8 · `FINDINGS` registry is a hand-maintained list** (`run_layer3_report.py:18`). Currently complete (all 29 registered — verified), but a forgotten future finding would silently never run *and* be untested (`test_findings.py` keys off the same list). **Fix:** auto-discover `findings/*.py`, or have the runner and tests import one shared list.
- **L3-9 · `validate.py:61` `SIGNALS`** is a 6-item subset of findings with no docstring saying so. **Fix:** add a docstring clarifying it's a curated subset.
- **L3-10 · threshold constants lack inline comments** (e.g. `n14:29`). **Fix:** one-line `# 50%+ loss & illiquid = dead money`.

---

## SCRAPERS (`scrapers/`)

> No shared base — each of ~16 scrapers reinvents HTTP/cache/rate-limit. Highest-duplication area in the repo. Recommended umbrella fix: create `scrapers/http.py` (session, headers, retry, 429-backoff) + `scrapers/paths.py`/`config.py` (URLs, dirs, rate-limits, timeouts).

### HIGH
- **SCR-1 · duplicated User-Agent/header blocks** — `screener.py:11`, `ipowatch.py:14`, `bhavcopy.py:34`, `bhavcopy_ohlc.py:63`, `indices.py:9`, `yahoo.py:12`. **Fix:** `scrapers/http.py` `DEFAULT_UA`.
- **SCR-2 · duplicated/divergent HTTP wrappers** — custom `_get`/fetch in `screener.py:27`, `screener_prices.py:43`, `ipowatch.py:22`, `bhavcopy_ohlc.py:98`, `sharescart.py:167`, inline `requests.get` in `bhavcopy.py`. **Fix:** one `http.fetch(url, *, timeout, referer, retries)`.
- **SCR-3 · mixed HTTP libraries** — urllib (`screener`, `ipowatch`), requests (`bhavcopy`, `bhavcopy_ohlc`, `sharescart`), cloudscraper (`chittorgarh`, `delisting`), curl_cffi (`corp_actions`, `nse_subscription`). **Fix:** standardize where possible; isolate the anti-bot ones behind the same interface.
- **SCR-4 · no HTTP 429 handling anywhere** — retry loops only check `==200`; backoff exists only in `sharescart.py:182`, `corp_actions.py:183`. **Fix:** detect 429 + `Retry-After` in the shared wrapper, exponential backoff.
- **SCR-5 · hardcoded URLs across 8+ files** (e.g. `bhavcopy.py:50/52`, `chittorgarh.py:43`, `delisting.py:99/105/119/149`, `bhavcopy_ohlc.py:112-136`, `screener.py:38/91`, `nse_subscription.py:11/18/38`, `investorgain.py:14`, `corp_actions.py:20/22/28`). **Fix:** `scrapers/config.py` `ENDPOINTS` dict.
- **SCR-6 · scattered rate-limit constants** — `sharescart:52` 0.5, `chittorgarh:46` 0.3, `screener:185` 1.2, `bhavcopy_ohlc:256` 0.4, `nse_subscription:96` 0.3, `investorgain:87` 0.5, `corp_actions:204` 0.7, `ipowatch:246` 0.25. **Fix:** `RATE_LIMITS` dict keyed by source + `@rate_limit` decorator.
- **SCR-7 · scattered dir-creation/path constants** — `chittorgarh.py:59/130/268`, `screener_prices.py:162`, `indices.py:51`, `delisting.py:254`, `sharescart.py:61/270`. **Fix:** `scrapers/paths.py`, `ensure_dirs()` once.

### MED
- **SCR-8 · god-file `sharescart.py` (766 lines)** — `scrape_detail()` (~299–507) mixes fetch + BeautifulSoup parse + field extraction. **Fix:** split `fetch_detail_page / parse_detail_page / extract_field`.
- **SCR-9 · fragile parsing, no validation** — index assumptions `cells[10/11]` (`sharescart.py:256`), `cells[1/2]` (`chittorgarh.py:246`); unchecked `soup.find` (`sharescart.py:310,368`); trusted CSV headers (`bhavcopy.py:79`, `bhavcopy_ohlc.py:147`); `pd.read_html` col-order (`screener.py:123`). **Fix:** validate required cols/tags at parse entry, log+skip on mismatch.
- **SCR-10 · inconsistent timeouts** — 25/30/20/40/60s scattered (`screener:28`, `bhavcopy:55`, `chittorgarh:112`, `bhavcopy_ohlc:100`, `delisting:99/149`). **Fix:** `TIMEOUTS` in config.
- **SCR-11 · caching inconsistency** — manifest/resume only in `bhavcopy_ohlc.py:23` + `screener_prices.py:15`; `chittorgarh`, `sharescart`, `ipowatch`, `corp_actions` re-fetch fully. **Fix:** shared checkpoint helper + `--resume`.
- **SCR-12 · inconsistent error handling** — bare `except`/silent returns (`chittorgarh`, `screener_prices.py:82`, `ipowatch.py:46`). **Fix:** `log.exception()`, sentinel only for expected failures.
- **SCR-13 · missing type hints/docstrings** on ~100 functions. **Fix:** annotate fetch/parse entry points first.
- **SCR-14 · file-handle leaks** — `open()` without context manager in `screener_prices_merge.py:51`, `delisting.py:188`. **Fix:** `with open(...)`.

### LOW
- **SCR-15 · inconsistent logging setup** (`sharescart:60`, `bhavcopy_ohlc:296`, `chittorgarh:58` vs bare `getLogger`). **Fix:** `scrapers/logging.py` `setup_logger()`.
- **SCR-16 · referer header duplicated** (`delisting:100`, `bhavcopy_ohlc:117`, `bhavcopy:55/68`, `sharescart:159`, `indices:34`). **Fix:** `REFERRERS` in config.
- **SCR-17 · unanchored regex** (`corp_actions.py:73`, `ipowatch.py:52`). **Fix:** anchor / `re.fullmatch`.
- **SCR-18 · dead/inline-able code** (`delisting.py:248 _cache_bounds`, `screener.py:215 _empty`). **Fix:** inline or remove.

---

## TESTS (`tests/`)

### HIGH
- **TEST-1 · zero coverage of `scrapers/` (16 files) and `pipeline/` (27 files)** — only `layer3/` is tested. The untested layers feed the "verified" findings, so a scraper-format change or `screener.resolve()` name-match break cascades into wrong financials → wrong findings, undetected. **Fix:** add unit tests for parsers (mocked HTTP) and an integration test on synthetic raw → 1-2 pipeline steps → assert output schema.
- **TEST-2 · the 5-traps tests are too thin** (`tests/layer3/test_traps.py`) — they assert a guard *runs*, not that it *prevents the trap*:
  - trap5 (`:8-13`) checks `segment` column exists, not that MB/SME values are actually un-pooled.
  - trap2 (`:16-20`) checks an "insufficient" token appears for N=3, not that the small-N row is suppressed from claims.
  - trap1 (`:34-40`) checks `n_long_5y > n_boom_5y*3`, not that boom 5y is gated out / wipeouts retained.
  - trap3 (`:43-47`) checks `tables` non-empty, not that it's longterm-only. **Fix:** make each adversarial — feed a crafted input that would trigger the trap and assert it's caught.

### MED
- **TEST-3 · tests aren't hermetic** — all layer3 tests call `spine.load_substrate()` on the real 2,296-row master (`test_spine.py:8`, `test_backtest.py:9`, `test_predictor.py:10`, `test_findings.py:19`, `test_analyses.py`, `test_oos.py`, `test_reach.py`). Pass/fail depends on on-disk data; can't test edge cases; slow. **Fix:** `tests/layer3/conftest.py` with a synthetic ~50-row fixture for unit tests; keep real-data tests in separate `test_integration_*.py`.
- **TEST-4 · duplicated `df` fixture** copy-pasted in `test_spine.py:6`, `test_backtest.py:7`, `test_predictor.py:8`, `test_findings.py:17`. **Fix:** one fixture in `conftest.py`.
- **TEST-5 · brittle data-dependent assertions** — hardcoded magnitudes: `test_spine.py:71` (`>= 140`), `:12` (`> 2000`), `:40-43` (`>1000/>500`), `test_reach.py:13,29,40,100` (`>100`). **Fix:** assert logic/relations (`upper >= lower`) or proportions, not absolute data values.
- **TEST-6 · parametrized `test_findings.py:22`** runs all findings as one param set; one failure obscures which. **Fix:** keep param but ensure per-id reporting (it already ids by module — confirm `-tb=short`), or note as acceptable.

---

## DOCS

> Canonical = **29 findings / 77 tests**. `EXECUTION_STATUS.md:20` is correct. `DONE.md` is a dated changelog — its intermediate counts (20/26/28, 70/73) are historical-by-design; do **not** "fix" them, optionally add a one-line banner that it's a historical log and EXECUTION_STATUS.md is current.

### HIGH (stale counts to reconcile to 29/77)
- **DOC-1 · `CLAUDE.md:24`** says "**28 findings, 73 tests**" → 29 / 77. (This is the auto-loaded AI brain — highest-impact stale number.)
- **DOC-2 · `CLAUDE.md:30`** says "Tests: `tests/layer3/` (62…)" → 77, and contradicts line 24 within the same file. **Fix:** reconcile both lines to 77.
- **DOC-3 · `README.md:40`** comment "# 62 tests" → 77.
- **DOC-4 · `NEEDS_YOUR_INPUT.md:3`** "28 findings, 73 tests green" → 29 / 77.
- **DOC-5 · `TODO.md:72`** "73 tests" → 77 (note: `TODO.md:9` and `:41` already correct at 29/77).
- **Recommended root fix:** stop hand-maintaining counts in prose — generate them (`len(FINDINGS)` + pytest count) or keep a single source (EXECUTION_STATUS.md) and have other docs point to it.

### MED
- **DOC-6 · `docs/research/` — 35 scratch/session-log files** in the authoritative docs namespace (session logs, `ideas_*`, review reports, recovery logs). **Fix:** move to `archive/research_scratch/` (or `docs/archive/`), leaving a short README pointer.
- **DOC-7 · `docs/superpowers/` — 3 agent build-plans/specs**, not user docs. **Fix:** move to `archive/`.
- **DOC-8 · `rules/README.md` promises per-rule `<id>.md` files** that don't exist (only `index.md` is populated). **Fix:** either amend the README to say "registry is index-only by design," or generate the per-rule files.
- **DOC-9 · `docs/patterns.md`** is superseded by `strategies.md` but not clearly marked. **Fix:** add a `**DEPRECATED — see docs/strategies.md**` header.
- **DOC-10 · `README.md` "start here" path omits `docs/data_review.md`** though `CLAUDE.md:54` lists it. **Fix:** add it to the README onboarding list.

---

## Suggested order of attack
1. **INFRA-1/2/3** (git + .gitignore + pyproject) — establishes the safety net and kills `PYTHONPATH=.`.
2. **DEPS-1/2** (requirements: add streamlit/pytest, pin) — makes a fresh clone runnable.
3. **L3-1** (`TODAY` live bug) + **DOC-1..5** (reconcile counts) — quick, high-value correctness/clarity.
4. **PIPE-1..4** → `pipeline/lib.py`; **L3-4** → `spine.pct()`; **SCR-1..7** → `scrapers/http.py` + `config.py` — the three big de-duplication wins.
5. **PIPE-7** (wire `checks/` into the chain) + **TEST-2/3** (adversarial traps + hermetic fixture) — hardens the verification chain that the project's trustworthiness rests on.
6. Remaining MED/LOW as capacity allows; **PIPE-5** (`compute()` split) is the largest single refactor — do it last, with tests in place first.
