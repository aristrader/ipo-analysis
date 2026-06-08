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

## 🏃 NOW — "NEXT-LEVEL" PROGRAM: 5 of 6 done (owner-approved 2026-06-08; plan `docs/research/NEXT.md`)
- ✅ **Thread A — portfolio sim** (`layer3/portfolio.py` + `run_portfolio.py`): ₹1L/APPLY vs Nifty,
  secondary (hero) 2.09× vs 1.27× sim · 1.34× vs 0.98× 2026 OOS. + per-stock `growth_of_1l` engine.
- ✅ **Thread A.2 — were-we-right scorecard** (`layer3/calibration.py` + `run_scorecard.py`): Wilson
  CIs, score WELL-ORDERED (Q1 38%→Q5 53% P(beat-Nifty)).
- ✅ **Thread B — hardening**: schema gate (`tools/checks/schema_gate.py`, wired into refresh) +
  GMP-history capture (`data/live/gmp_history.csv`). Post-listing monitor already in notifier.
- ✅ **Thread C** — scope-first: H2 pe_vs_sector REPLICATES (SME −48.9pp, MB −13.1pp) → DISPLAY-ONLY
  (boom-only, not score); H1 accruals + H3 SME→MB migration DATA-GATED (parked, see future_ideas).
- ✅ **News-feed SCOPE — VIABLE**: free NSE announcements API carries `sm_isin` (matching solved);
  Large→Medium build, data de-risked.
- ⏳ **REMAINING — FINAL app rework (#28, absorbs #27)**: surface all the above (portfolio equity
  curve, per-stock ₹1L charts, scorecard, pe_vs_sector display). Re-run the app-iteration pipeline.
  **NEEDS PLAYWRIGHT ON** (currently off — `docs/playwright_on_off.md`). The one piece left; build LAST.
- All new engines have CLIs + tests (254 in suite); chart/scorecard RENDERING deferred to the rework.
- Prior state (all DONE, → `DONE.md`): 3 layers + Phase-2 research + app + live calls + Telegram.
- **Running parts:** Telegram notifier LIVE (@IPO_call_bot, thrice-daily launchd; stop with
  `launchctl unload ~/Library/LaunchAgents/com.ipo.calls.plist`) · calls ledger
  `data/master/calls_ledger.csv` (~5,170 + accruing) · live board → `data/live/`.
  **Playwright = OFF by default** (company-laptop rule; on-for-testing-then-off →
  `docs/playwright_on_off.md`).
- **Commands:** app `PYTHONPATH=. streamlit run app.py` (localhost) · calls `python run_calls.py`
  (`--live` / `--backfill` / `--report`) · refresh `python run_refresh.py [--apply]` · forward test
  `python run_forward_test.py` · tests `PYTHONPATH=. pytest tests -q` · gate
  `SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q`. Change→tests routing is automatic (verify hook).
- **Phase 2 ✅ COMPLETE** (research + app) — full tally in `rules/index.md` + `DONE.md`; verdicts in
  `tier1_wave1_verdicts.md`. Headline: score stays 8 components; graduates = crowded_window (in-score)
  + F7/F5e (display); everything else honestly killed.

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
