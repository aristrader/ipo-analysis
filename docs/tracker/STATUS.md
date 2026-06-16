# STATUS — single live source of "where are we / what's next"

> **Resume the main Claude Code session:** `claude --resume 01820f2d-c29a-4f29-84ad-349ce26b70fa`
> (run from this directory; or `claude --resume` → pick top; `claude -c` = most recent)

> **Rule:** this is the ONE status file — live state + what's next ONLY. **Verify state from GROUND
> TRUTH (files / command output), never from memory.** "What happened" (history) → **git log**.
> "What is this / conventions" → `CLAUDE.md`. "Findings + tested-signal registry" → `rules/index.md`.
> Quick check: `python verify.py` (counts, drift, data-vs-backup; regenerates MAP.md).

_Canonical facts (re-derived by `verify.py` each turn): **29 findings, 219 tests**, mutation-validated
28/28. Substrate = `data/master/ipo_analysis.csv`; movable facts in `data/master/substrate_meta.json`
(**2384 rows, as-of 2026-06-06**; snapshot `archive/pre_refresh_20260606/`). Score = **8 components**;
`data_informed` weights: downside 0.269 · **crowded_window 0.260** · multibagger 0.201 · return 0.189 ·
wipeout 0.080 (top-quintile lift +39.5pp in-sample; forward-tested OOS on the 2026 cohort). Banker wipeout-flag
= `coverage_guard` (A1b, LIVE 2026-06-10). Git: remote `origin` (github.com/aristrader/ipo-analysis); branch + PR, never push `main` directly without owner OK._

---

## 🏃 NOW
- **✅ 2026-06-10 BABYSAT/AWAY SESSION COMPLETE — 5 backlog items shipped, all via the execution pipeline (build →
  independent review → test → verify → commit). The whole QUICK + NETWORK backlog is now cleared.**
  - **D1/D4 — NSE announcement context feed** (`scrapers/announcements.py` + `layer3/news/{taxonomy,staging}.py`):
    display-only "context, not signal", ISIN/symbol-keyed, locally category-tagged, look-ahead-safe. Independent
    review confirmed substrate-untouched + zero-download rails airtight. **History R&D: the default API returns FULL
    history (~2004→, delisted included) → one pull = the backfill, no paging.** Full pull running/seeded into the
    gitignored `data/live/news/` (regenerable, ~180MB; re-pull via the scraper). Render-join = by SYMBOL (sm_isin
    can be pre-split). 22 tests.
  - **A1b — banker wipeout-flag coverage-guard hybrid → PROMOTED LIVE** (`OBSCURE_BANKER_MODE="coverage_guard"`): the
    ONE signal change that cleared the bar. Recovers recall (24.6% ≈ legacy 25.4%, vs quality's 13.2%) WHILE keeping
    the false-veto fix; independent adversarial review promoted it (the −3 net recall is a quality-improving swap).
    Re-derived weights (wipeout 0.099→0.080). [[rules/index.md]] A1b entry.
  - **I3** — weights drift now caught by a protection test (canonical == fresh deterministic derive).
  - **F2** — durable append-only OOS were-we-right history (`data/master/forward_test_history.csv`); first vintage
    seeded (spread_1m +12.9). App trajectory table added (wants a visual walk).
  - **E3** — SME→Mainboard migration outcome class, derived from OWNED DATA (no scraping): 333/1468 (22.7%) migrated;
    quantifies the bimodal dead-money trap (both cohorts). DESCRIPTIVE only (selection + look-ahead → not scored).
  - **Remaining backlog (need owner / gated, NOT autonomous):** C1 app redesign (Playwright visual walk), E2 (boom-only
    wall), Theme-H-full / G1 / G2 (big build decisions). `docs/research/improvement_backlog.md`.
- **✅ AUTONOMOUS BATCH COMPLETE + MERGED to main (nights of 2026-06-09 + 06-10).** Branches deleted; full suite 300p/12s,
  verify 0. I1 DONE (merged). Docs consolidated (DONE.md removed → history=git log; 7 feeders archived; INDEX.md map;
  anti-sprawl discipline in CLAUDE.md). Full record: `docs/research/batch_run_2026-06-09.md`.
  - **NIGHT-1 shipped:** App C1 honesty/nav polish (median-first ₹1L, n_floor scorecard, COMBINED→rank, sidebar
    search; visually walked) · B1 two-sided miss-mining of 364 recent IPOs · News R&D (delivery-% demoted, H7 promoted).
  - **Subscription-parser bug** (live-feed only): found + fixed + hardened (label-variant robust); 8 affected live
    calls remediated (Genxai APPLY→NEUTRAL, etc.); substrate verified clean; blast-radius fully scoped.
  - **NIGHT-2 analysis (7 tasks, ALL reviewed):** H7 (display-only F10-narrow) · A3 (F5e lean, confirms M1) ·
    **A1 banker-flag → adversarial review DOWNGRADED to display-only**, reverted to legacy baseline (halved recall) ·
    E1 accruals (display-only, longterm-only) · A2 hold-drawdown (REJECT-as-exit) · weak-sub guard (REJECT —
    B1's tell was a young-cohort artifact) · H-MVP relative-valuation (redundant-with-n6, boom-only).
    **NET: ZERO new live-score components — evolve-only-if-robust held; the gate caught A1's overclaim.**
  - **Infra:** Playwright ALWAYS-ON (localhost-pinned) · notifier RunAtLoad login-catch-up · **J1/J2 Telegram
    ops-channel** (fail-loud health alerts + heartbeat, tested, [TEST] pings delivered).
  - **HELD for owner:** I1 (substrate 0-vs-null hygiene — do at pipeline-build level, not a post-hoc CSV edit).
  - Full suite **300p/12s**, verify exit 0, tree clean. **Next: review/merge `auto/6hr-batch`; decide I1; backlog
    has A1b (banker coverage-guard hybrid) + I3 (weights-file churn hygiene).**
- **Nothing in progress — next-level program + the full multi-dimensional ENHANCEMENT pass COMPLETE
  (2026-06-08).** Every task with current work went through diverge (thinking-agent lenses) →
  converge → build → review → test. System at rest, forward-tracking itself. History → git log.
- **Enhancement outcomes:** Task 1 portfolio/scorecard — 2 review rounds caught + fixed real
  misleading-number bugs (median now shown next to mean, lift made apples-to-apples, ₹1L chart
  starts clean, APPLY graded on allottee view). Task 3 (Thread B) — gate hardened (enums,
  scoped-score, referential, scale-inversion; raises on refresh; runs each turn). Task 4 (Thread C)
  — 3 NEW hypotheses generated + tested with placebo, all rejected (0 new signals = honest).
- **Future builds (get their own divergence pass WHEN built, not before):** news-feed (scoped
  VIABLE), broader app redesign. Both in `docs/research/archive/` (future_ideas / NEXT).
- **Running parts:** Telegram notifier (thrice-daily + RunAtLoad login-catch-up) · calls ledger ~5,170 · schema
  gate in the per-turn verify hook + refresh · Playwright ALWAYS ON, localhost-pinned (owner 2026-06-10).
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
- **`docs/research/archive/future_ideas.md`** — owner "someday" sub-projects: swing-trade buy/sell calls
  (exit side REJECTED — take-profit guts the right tail; needs a new validated entry signal first)
  + stock-news/catalyst feed (free BSE/NSE announcements API = first scoping step).
- **Re-run the forward test (~monthly)** as the 2026 cohort ages — the OOS verdict hardens; also
  re-test the SHORT-horizon idea then (parked: data said no, sample was young).
- **Watchlist signals** (rules/index.md): qib_retail_ratio (lean-positive; display-only candidate).
  [pe_vs_sector RESOLVED 2026-06-08 → display-only, placebo-confirmed, boom-only.]
- **Microcap extension** — the one major optional sub-project
  (`docs/research/microcap_extension_thinking.md`).

## 🅿 PARKED / REJECTED (decided — don't re-litigate; evidence in git log + rules/index.md)
- **~30 hypothesis-batch rejections** + earlier: SHORT score, market-momentum/sector-heat/commodity
  context, "hot pops fade" (opposite holds), exit-timing rules vs buy-and-hold.
- **DRHP bulk recovery** — parked (can't get the useful columns reliably; analysis unaffected).
- **`scrapers/http.py` (broad)** — rejected (heterogeneous scrapers; stdlib-`http` shadowing).
