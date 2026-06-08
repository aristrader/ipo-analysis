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
- **APP-ITERATION PIPELINE ✅ COMPLETE (2026-06-07): 4/4 iterations run.** Charter
  `docs/research/app_iteration_charter.md`; findings iter1/2/3 in `docs/research/iter*_findings.md`.
  Tally: **0 P0 anywhere** · 23 findings found · 19 fixed (all P1/P2 + cheap P3) · 4 deferred to
  the owner improvement list. App: 7 screens, glossary, staleness alarm, color-coded call badges,
  plain-language whys, deep-links everywhere. **259 tests** (243 fast + 16 ui-logic in tests/app)
  + extended key-content smoke. Run: `PYTHONPATH=. streamlit run app.py` (localhost-only).
- **RECOMMENDATIONS SYSTEM ✅ BUILT + LIVE (2026-06-07/08):** calls engine (`layer3/calls.py` +
  `run_calls.py`, 12 property tests) · ledger `data/master/calls_ledger.csv` (~5,170 calls: 2026
  backfill OOS + boom historical_sim + accruing LIVE) · headline **APPLY +6.0% vs AVOID −28.2% a1y
  (sim); 2026 OOS APPLY +13.6%/+16.4% (1m/3m) vs AVOID −3.6%/−3.1%** · live board
  `scrapers/live_board.py` → `data/live/` (day-wise sub accumulating = Branch B) · evidence records
  `app/records/` (102 signals + 21 families).
- **TELEGRAM NOTIFIER ✅ LIVE (2026-06-08):** @IPO_call_bot, thrice-daily launchd job
  (9:30/14:30/20:30) → fetch board + gap-fill/grade + ping on NEW actionable calls only. Token in
  gitignored `tools/notify/telegram.json`; on/off + revoke notes in `notify_calls.py`. Stop:
  `launchctl unload ~/Library/LaunchAgents/com.ipo.calls.plist`.
- **PLAYWRIGHT = OFF by default** (company-laptop rule) — on only for app testing, then off;
  procedure `docs/playwright_on_off.md`.
- **App ✅ shipped + 4-iteration polished + playwright-verified:** 7-screen st.navigation terminal,
  glossary / staleness alarm / color-coded call badges / plain-language whys / deep-links.
  Run: `PYTHONPATH=. streamlit run app.py` (localhost-only).
- System state: showdown-certified, refreshable (`run_refresh.py`), forward-tested on 82 never-seen
  IPOs (score ordered real outcomes monotonically). Full history → `DONE.md`.
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
  F11 serial promoters: **PARKED by owner 2026-06-07** (entity-matching = too much human
  intervention for the payoff; don't re-open unless a clean promoter-ID source appears).
- **App redesign (build LAST, design evolves after every run):** the simple 5-tab app must become
  a sequenced research platform (IPO detail pages w/ event calendars + cluster context + reference
  levels; evidence browser for hypothesis verdicts/playbooks; regime dashboard; forward-test tracker).
  Design doc: `docs/research/app_phase2_design.md` (iterated per run; implementation = end of Phase 2).

## 📋 OPEN BACKLOG (all optional — pick when wanted)
- **`docs/research/future_ideas.md`** — owner "someday" sub-projects: swing-trade buy/sell calls
  (exit side REJECTED — take-profit guts the right tail; needs a new validated entry signal first)
  + stock-news/catalyst feed (free BSE/NSE announcements API = first scoping step).
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
