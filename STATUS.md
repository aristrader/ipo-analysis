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
- **⏸ AUTONOMOUS BATCH 2026-06-09 PAUSED (owner ended session) — work is on branch `auto/6hr-batch`, NOT main.**
  Full record + resume map: `docs/research/batch_run_2026-06-09.md`. SHIPPED on branch: App C1 honesty/nav
  polish (median-first ₹1L, n_floor scorecard, COMBINED→rank, sidebar search; walked) · B1 two-sided
  miss-mining of 364 recent IPOs (obscure-banker = sole blocker on 34/52 missed winners; weak-sub = false-APPLY
  tell) · News R&D (delivery-% demoted, H7 promoted). **WIP (DO NOT MERGE): A1 banker-flag fix** (`8c87960` —
  impl in scorecard.py passes tests but needs new-tests + evolve-only-if-robust verdict + adversarial review).
  NOT STARTED: A3 / H7 / E1 / H-MVP / A2 + a weak-subscription false-APPLY guard. Full suite 269p/12s, verify
  exit 0, Playwright OFF. **Next session: review the branch, finish A1 (resume from its commit checklist), then
  pick from `improvement_backlog.md`.**
- **Nothing in progress — next-level program + the full multi-dimensional ENHANCEMENT pass COMPLETE
  (2026-06-08).** Every task with current work went through diverge (thinking-agent lenses) →
  converge → build → review → test. System at rest, forward-tracking itself. History → `DONE.md`.
- **Enhancement outcomes:** Task 1 portfolio/scorecard — 2 review rounds caught + fixed real
  misleading-number bugs (median now shown next to mean, lift made apples-to-apples, ₹1L chart
  starts clean, APPLY graded on allottee view). Task 3 (Thread B) — gate hardened (enums,
  scoped-score, referential, scale-inversion; raises on refresh; runs each turn). Task 4 (Thread C)
  — 3 NEW hypotheses generated + tested with placebo, all rejected (0 new signals = honest).
- **Future builds (get their own divergence pass WHEN built, not before):** news-feed (scoped
  VIABLE), broader app redesign. Both in `docs/research/future_ideas.md` / NEXT.md.
- **Running parts:** Telegram notifier (thrice-daily) · calls ledger ~5,170 · schema gate in the
  per-turn verify hook + refresh · Playwright OFF by default.
- **Commands:** app `streamlit run app.py` · `run_portfolio.py` · `run_scorecard.py` ·
  `run_calls.py` · `run_refresh.py [--apply]` · tests `pytest tests -q` (262).

## 📋 OPEN BACKLOG (all optional — pick when wanted)
- **B1 miss-mining DONE (2026-06-09, `docs/research/miss_mining_2026-06.md`):** per-IPO grade of all 364
  recent (~12mo) IPOs, both error types. Confusion matrix TP68/FP59/FN52/TN158; APPLY hit-rate 44.2%,
  mean +28.6% vs cohort median −5.1% (the ranking adds value). Seeds: **A1 banker-flag fix** (obscure-banker
  flag = SOLE blocker on 34/52 missed winners, 17 top-quintile flips ~₹0.93M/₹1L — hypothesis CONFIRMED) +
  a **new low-subscription FALSE-POS guard** (all 59 losers we APPLY'd were 0-flag; sub 2.2× vs 6.6× — must
  pass 3-layer/placebo before any veto). EARLY READ (young cohort); re-run as it matures. Reproduce:
  `PYTHONPATH=. python tools/research/miss_mining.py`.
- **`docs/research/future_ideas.md`** — owner "someday" sub-projects: swing-trade buy/sell calls
  (exit side REJECTED — take-profit guts the right tail; needs a new validated entry signal first)
  + stock-news/catalyst feed (free BSE/NSE announcements API = first scoping step).
- **Re-run the forward test (~monthly)** as the 2026 cohort ages — the OOS verdict hardens; also
  re-test the SHORT-horizon idea then (parked: data said no, sample was young).
- **Watchlist signals** (rules/index.md): qib_retail_ratio (lean-positive; display-only candidate).
  [pe_vs_sector RESOLVED 2026-06-08 → display-only, placebo-confirmed, boom-only.]
- **Microcap extension** — the one major optional sub-project
  (`docs/research/microcap_extension_thinking.md`).

## 🅿 PARKED / REJECTED (decided — don't re-litigate; evidence in DONE.md + rules/index.md)
- **~30 hypothesis-batch rejections** + earlier: SHORT score, market-momentum/sector-heat/commodity
  context, "hot pops fade" (opposite holds), exit-timing rules vs buy-and-hold.
- **DRHP bulk recovery** — parked (can't get the useful columns reliably; analysis unaffected).
- **`scrapers/http.py` (broad)** — rejected (heterogeneous scrapers; stdlib-`http` shadowing).
