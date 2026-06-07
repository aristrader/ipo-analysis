# Calls Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A dated, graded, gap-filling calls ledger (`data/master/calls_ledger.csv`) generated point-in-time from the validated rules, plus the live/upcoming board and the day-1 data scoping.

**Architecture:** Pure engine (`layer3/calls.py`: events → calls → grades, no I/O decisions) + CLI orchestrator (`run_calls.py`: cursor walk, modes, ledger persistence) + one scraper (`scrapers/live_board.py` → `data/live/`, never touching `data/master/`). PIT scores come from EXISTING machinery (forward-test CSV for the 2026 cohort; `score_all_pointintime` for the historical sim; live `predict()` for open issues) — the engine never scores.

**Tech Stack:** Python 3.14 (`.venv`), pandas, csv substrate at `data/master/ipo_analysis.csv`, prices at `data/prices/<isin>.csv`, Nifty calendar at `data/reference/indices/nifty50.csv`. No scipy (use rank-then-pearson if correlation needed). Run everything `PYTHONPATH=. .venv/bin/python`.

**Conventions (from docs/research/hypothesis_protocol.md):** exclude `listing_metrics_status == "unreliable_coverage"`; alpha vs Nifty; `issue_price_adj` against price files; point-in-time = only data dated ≤ call_date.

---

### Task 1: Day-1 data scoping (spec §6 — DO FIRST, decides the EARLY-call branch)

**Files:** Create `tools/research/scope_daywise_sub.py`

- [ ] Script: sample ~30 IPOs across 2021–2026 from the substrate that have a chittorgarh detail URL (check `data/raw/chittorgarh/` cache first — the detail pages are ALREADY CACHED there from pipeline 02; do NOT re-scrape if cached HTML exists). Parse each for a day-wise subscription table (look for "Day 1"/"Day 2" header patterns or `subscription-status` tables). Report: coverage % by year, fields available.
- [ ] Run it; append the branch decision (A: backtestable / B: forward-only) to `docs/research/recommendations_system_discussion.md` under a "Day-1 scoping verdict" heading.
- [ ] Commit: `git commit -m "Day-1 scoping: chittorgarh day-wise subscription coverage verdict"`

### Task 2: Engine core — calendar + events (`layer3/calls.py` part 1)

**Files:** Create `layer3/calls.py`, `tests/layer3/test_calls.py`

- [ ] Write failing tests:

```python
# tests/layer3/test_calls.py
import pandas as pd
from layer3 import calls

def _mini_df():
    return pd.DataFrame([
        {"isin": "INE0TEST1", "company_name": "A", "type": "MB", "cohort": "boom",
         "open_date": "2024-01-08", "close_date": "2024-01-10", "listing_date": "2024-01-15",
         "listing_metrics_status": "ok"},
        {"isin": "INE0TEST2", "company_name": "B", "type": "SME", "cohort": "boom",
         "open_date": "2024-02-05", "close_date": "2024-02-07", "listing_date": "2024-02-12",
         "listing_metrics_status": "ok"},
    ])

def test_events_between_emits_all_anchor_types():
    ev = calls.events_between("2024-01-01", "2024-12-31", _mini_df(), corp_actions=pd.DataFrame())
    kinds = {e["kind"] for e in ev}
    assert {"verdict", "track", "persist", "capit"} <= kinds      # close, listing, +21td, +90td

def test_events_are_date_bounded():
    ev = calls.events_between("2024-01-01", "2024-01-31", _mini_df(), corp_actions=pd.DataFrame())
    assert all("2024-01-01" <= e["date"] <= "2024-01-31" for e in ev)

def test_trading_day_offset_uses_nifty_calendar():
    d = calls.td_offset(pd.Timestamp("2024-01-15"), 21)
    assert d > pd.Timestamp("2024-02-09")       # ≥ ~4.2 calendar weeks
```

- [ ] Run: `PYTHONPATH=. .venv/bin/pytest tests/layer3/test_calls.py -q` → FAIL (module missing).
- [ ] Implement in `layer3/calls.py`: `_nifty_dates()` (cached list from nifty50.csv), `td_offset(ts, n)` (bisect index + n), `events_between(d0, d1, df, corp_actions)` returning dicts `{date(str), kind, isin, row}` for: `verdict`@close_date, `track`@listing_date, `persist`@listing+21td, `capit`@listing+90td, `corp_action`@ex_date if 30≤(ex−listing).days≤365 (corp_actions matched by isin OR nse_symbol, bonus/split only). Filter `unreliable_coverage`. Sort by date.
- [ ] Run tests → PASS. Commit.

### Task 3: `make_call` + the no-look-ahead property (`layer3/calls.py` part 2)

**Files:** Modify `layer3/calls.py`, `tests/layer3/test_calls.py`

- [ ] Failing tests:

```python
def test_verdict_call_thresholds():
    pit = pd.DataFrame([{"isin": "INE0TEST1", "score": 90.0, "n14_flags": 0},
                        {"isin": "INE0TEST2", "score": 10.0, "n14_flags": 2}])
    pit = calls.add_quintiles(pit, _mini_df())          # per-segment quintiles
    c1 = calls.make_call({"date": "2024-01-10", "kind": "verdict", "isin": "INE0TEST1",
                          "row": _mini_df().iloc[0]}, pit, prices_root="data/prices")
    assert c1["call_type"] == "APPLY"                   # top quintile + 0 flags
    c2 = calls.make_call({"date": "2024-02-07", "kind": "verdict", "isin": "INE0TEST2",
                          "row": _mini_df().iloc[1]}, pit, prices_root="data/prices")
    assert c2["call_type"] == "AVOID"                   # bottom quintile / 2 flags

def test_no_look_ahead_capit_uses_only_prices_to_call_date(tmp_path):
    # price file with closes below issue through d90, then a huge rally AFTER:
    # the capit call must be EXIT_REVIEW regardless of the future rally
    ...build synthetic prices csv (120 rows, closes 50.0 then 500.0 after row 91), issue 100...
    call = calls.make_call(capit_event, pit, prices_root=str(tmp_path))
    assert call["call_type"] == "EXIT_REVIEW"
    assert "future" not in call["rules_fired"]
```

- [ ] Run → FAIL. Implement `add_quintiles(pit, df)` (qcut per type, labels 1..5) and `make_call(event, pit, prices_root)`:
  - `verdict` → APPLY (q5 & flags==0) / AVOID (q1 | flags≥2) / NEUTRAL; rules_fired `score_q=..;n14_flags=..`.
  - `track` → TRACK.
  - `persist` → PERSIST_HOLD / PERSIST_EXIT_LEAN from path ratio over first 21 td (up-days/down-days closes from the price file, rows ≤ call date ONLY — slice `pr[pr.date <= call_date]`).
  - `capit` → EXIT_REVIEW if max(close[1..90]) < issue_price_adj else CLEARED_ISSUE (rows ≤ call date only).
  - `corp_action` → TAKE_PROFITS.
  - Stamp `tape_state` + `crowding_pctl` (trailing-60d median pop of prior same-type listers via the substrate, prior-only; percentile vs prior climates → cold/<33, hot/>67) — compute in a helper `context_at(date, df)`.
  - Returns dict with ALL ledger columns (grades None, `grade_status="pending"`).
- [ ] Run tests → PASS. Commit.

### Task 4: Grading (`layer3/calls.py` part 3)

**Files:** Modify `layer3/calls.py`, `tests/layer3/test_calls.py`

- [ ] Failing tests: `grade_calls(ledger_df, df, prices_root, today)` fills `alpha_1m/3m/1y` (21/63/250 td alpha vs Nifty from call_date; APPLY/EARLY/TRACK grade from LISTING date with `pop_pct` from substrate), sets `grade_status` partial→final (final when 1y horizon passed or delisted), NEVER mutates rows already `final` (test: poison a final row's alpha, re-grade, value unchanged).
- [ ] Implement (price closes + nifty ratio, same pattern as tools/research scripts), run → PASS. Commit.

### Task 5: CLI + cursor walk + idempotence/gap-fill (`run_calls.py`)

**Files:** Create `run_calls.py`; modify `tests/layer3/test_calls.py`

- [ ] Failing tests (drive via functions, not subprocess):

```python
def test_walk_idempotent(tmp_path):
    led1 = calls.walk(_mini_df(), pit, "2024-01-01", "2024-12-31", mode="historical_sim", ledger=None)
    led2 = calls.walk(_mini_df(), pit, "2024-01-01", "2024-12-31", mode="historical_sim", ledger=led1)
    assert len(led2) == len(led1)                        # no duplicates (call_id key)

def test_gap_fill_equals_one_shot():
    a = calls.walk(_mini_df(), pit, "2024-01-01", "2024-06-30", mode="historical_sim", ledger=None)
    a = calls.walk(_mini_df(), pit, "2024-07-01", "2024-12-31", mode="historical_sim", ledger=a)
    b = calls.walk(_mini_df(), pit, "2024-01-01", "2024-12-31", mode="historical_sim", ledger=None)
    assert sorted(a["call_id"]) == sorted(b["call_id"])
```

- [ ] Implement `calls.walk(df, pit, d0, d1, mode, ledger)` (events → make_call → concat, dedupe on call_id keeping first) and `run_calls.py` CLI: default = cursor walk from `max(call_date)+1d` to today with `mode=gap_filled`; `--backfill FROM TO --mode backfilled|historical_sim`; `--grade-only`; `--pit {forward_test|pointintime}` selects the score source (forward-test CSV `docs/research/forward_test_2026_per_ipo.csv` [cols: isin, score, red_flags] vs `weights.score_all_pointintime` component-mean). Writes `data/master/calls_ledger.csv` atomically (tmp+rename).
- [ ] Run tests → PASS. Commit.

### Task 6: Execute the backfills (data run, not code)

- [ ] `PYTHONPATH=. .venv/bin/python run_calls.py --backfill 2026-01-01 2026-06-07 --mode backfilled --pit forward_test`
- [ ] `PYTHONPATH=. .venv/bin/python run_calls.py --backfill 2020-01-01 2025-12-31 --mode historical_sim --pit pointintime` (boom cohort only — filter inside; longterm excluded per spec A5; expect ~20-40 min for the PIT scoring; cache the PIT frame to `data/master/review/pit_scores_cache.csv` so re-runs are instant)
- [ ] `... run_calls.py --grade-only`
- [ ] Sanity report (print): calls per type per mode; APPLY vs AVOID graded alpha medians (the track record!); EXIT_REVIEW save-rate. Eyeball against known truths (top-quintile lift ≈ +39pp in-sample, forward-test ordering).
- [ ] Commit ledger + cache.

### Task 7: Live & upcoming board (`scrapers/live_board.py`)

**Files:** Create `scrapers/live_board.py`, `tests/scrapers/test_live_board.py`, dir `data/live/`

- [ ] Test with a saved HTML fixture (fetch one real page once into `tests/scrapers/fixtures/`): parser extracts {name, type, open/close dates, price band, gmp?} rows; unknown fields stay None (never fake). Test that `data/master/` is never written (function takes explicit out_dir).
- [ ] Implement: reuse the existing chittorgarh scraper session/headers (`scrapers/chittorgarh.py` conventions + rate limits); fetch the current+upcoming listing page; for OPEN issues optionally fetch detail for day-wise sub; write `data/live/board.json` {fetched_at, upcoming:[...], open:[...]} and APPEND `data/live/daywise_sub.csv` (one row per open-issue per fetch-day: date, name, day_n, sub_*, gmp) — this accumulates the day-1 dataset (Branch B engine).
- [ ] Run test → PASS. Commit.

### Task 8: Wiring + suite + docs

**Files:** Modify `project_map.py`, `run_refresh.py`, `STATUS.md`

- [ ] project_map: register new files (pipeline products/dirs as appropriate), CONTEXT entry "recommendations / calls ledger" → [layer3/calls.py, run_calls.py, scrapers/live_board.py, data/master/calls_ledger.csv, docs/superpowers/specs/2026-06-07-calls-engine-design.md], TEST_ROUTING (`layer3/calls.py` → tests/layer3/test_calls.py; `scrapers/live_board.py` → tests/scrapers/test_live_board.py; `run_calls.py` → tests/layer3/test_calls.py).
- [ ] run_refresh.py: add a final phase "calls" → cursor walk + grade (mode=gap_filled), AFTER the substrate swap + test gate (so calls always read the fresh, verified substrate).
- [ ] `PYTHONPATH=. .venv/bin/pytest tests -q` (full fast suite green) + `.venv/bin/python verify.py` (PASS).
- [ ] STATUS.md NOW section + commit.

## Self-review (done at write time)
- Spec coverage: §1→T5 ledger, §2→T3/T4, §3→T2/T3/T5, §4→T6, §5→T7, §6→T1, property tests→T2-T5, wiring→T8. ✓
- Type consistency: `events_between(d0,d1,df,corp_actions)` / `make_call(event,pit,prices_root)` / `add_quintiles(pit,df)` / `grade_calls(ledger,df,prices_root,today)` / `walk(df,pit,d0,d1,mode,ledger)` used consistently. ✓
- Known honest gap: T7 parser details depend on live page HTML (unknowable until fetched) — the plan pins the CONTRACT (fields, None-for-unknown, fixture test) rather than fake selectors.
