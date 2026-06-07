# STATUS — single live source of "where are we / what's next"

> **Resume the main Claude Code session:** `claude --resume 01820f2d-c29a-4f29-84ad-349ce26b70fa`
> (run from this directory; or `claude --resume` → pick top; `claude -c` = most recent)

> **Rule:** this is the ONE status file — live state + what's next ONLY. **Verify state from GROUND
> TRUTH (files / command output), never from memory.** "What happened" (history) → `DONE.md`.
> "What is this / conventions" → `CLAUDE.md`. "Findings + tested-signal registry" → `rules/index.md`.
> Quick check: `python verify.py` (counts, drift, data-vs-backup; regenerates MAP.md).

_Canonical facts (re-derived by `verify.py` each turn): **29 findings, 219 tests**, mutation-validated
28/28. Substrate = `data/master/ipo_analysis.csv`; movable facts in `data/master/substrate_meta.json`
(**2384 rows, as-of 2026-06-06**; snapshot `archive/pre_refresh_20260606/`). Score = **8 components**;
`data_informed` weights: downside 0.264 · **crowded_window 0.254** · multibagger 0.197 · return 0.185 ·
wipeout 0.099 (top-quintile lift +39.5pp in-sample; forward-tested OOS on the 2026 cohort). Git LOCAL-ONLY._

---

## 🏃 NOW
- **Nothing in progress.** System state: showdown-certified, refreshable (`run_refresh.py`), forward-
  tested on 82 never-seen IPOs (score ordered real outcomes monotonically), 48-hypothesis batch done
  (1 fold, 1 conditioning rule, ~30 to the rejected registry). Full history → `DONE.md`.
- Commands: fast suite `PYTHONPATH=. pytest tests -q` (~90s) · pre-release gate
  `SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q` · refresh `python run_refresh.py [--apply]` ·
  forward test `python run_forward_test.py` · app `PYTHONPATH=. streamlit run app.py`.
- Change→tests routing is automatic each turn (`verify.py` hook + `project_map.TEST_ROUTING`).

## 🚀 PHASE 2 — declared 2026-06-06 (deep-hypothesis program + app redesign)
- **Research program: ✅ COMPLETE (2026-06-07)** — 12 families / ~33 tests run, 3-layer protocol.
  Master docs: `deep_hypotheses_2026-06.md` + `phase2_playbooks.md`; ALL verdicts in
  `tier1_wave1_verdicts.md` + `rules/index.md`. **Final tally: 3 graduates** (crowded_window
  IN-SCORE 0.254 · F7 disposition contagion VALIDATED display, 3m timing · F5e capitulation flag
  VALIDATED display, day-90 checkpoint, incremental to N14) **+ 1 thin survivor** (F10 early
  bonus/split = exit tell, n=31) **+ 2 mechanism confirmations** (F2d congestion tax, F2c SME
  fatigue) **+ 1 display-watch** (F6a GMP-surprise) — everything else honestly killed (~26,
  incl. F1/F3/F4/F5a-d/f/F8/F9/F12/T2a-j). F7 fold 1/5 → NOT in score (score stays 8 components).
  Only gated remainder: F11 serial promoters (needs entity-matching infra).
- **App redesign (build LAST, design evolves after every run):** the simple 5-tab app must become
  a sequenced research platform (IPO detail pages w/ event calendars + cluster context + reference
  levels; evidence browser for hypothesis verdicts/playbooks; regime dashboard; forward-test tracker).
  Design doc: `docs/research/app_phase2_design.md` (iterated per run; implementation = end of Phase 2).

## 📋 OPEN BACKLOG (all optional — pick when wanted)
- **Re-run the forward test (~monthly)** as the 2026 cohort ages — the OOS verdict hardens; also
  re-test the SHORT-horizon idea then (parked: data said no, sample was young).
- **Watchlist signals** (re-open conditions in rules/index.md): pe_vs_sector (needs SME PE data),
  qib_retail_ratio (lean-positive; display-only candidate).
- **Microcap extension** — the one major optional sub-project
  (`docs/research/microcap_extension_thinking.md`).

## 🅿 PARKED / REJECTED (decided — don't re-litigate; evidence in DONE.md + rules/index.md)
- **~30 hypothesis-batch rejections** + earlier: SHORT score, market-momentum/sector-heat/commodity
  context, "hot pops fade" (opposite holds), exit-timing rules vs buy-and-hold.
- **DRHP bulk recovery** — parked (can't get the useful columns reliably; analysis unaffected).
- **`scrapers/http.py` (broad)** — rejected (heterogeneous scrapers; stdlib-`http` shadowing).
