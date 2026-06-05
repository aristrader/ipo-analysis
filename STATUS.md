# STATUS — single live source of "where are we / what's next"

> **Resume the main Claude Code session:** `claude --resume 01820f2d-c29a-4f29-84ad-349ce26b70fa`
> (run from this directory; or `claude --resume` → pick top; `claude -c` = most recent)

> **Rule:** this is the ONE status file — live state + what's next ONLY. **Verify state from GROUND
> TRUTH (files / command output), never from memory.** "What happened" (history) → `DONE.md`.
> "What is this / conventions" → `CLAUDE.md`. "Findings + tested-signal registry" → `rules/index.md`.
> Quick check: `python verify.py` (counts, drift, data-vs-backup; regenerates MAP.md).

_Canonical facts (re-derived by `verify.py` each turn): **29 findings, 207 tests** (94 layer3 + 37
pipeline + 32 scrapers + 25 data + 12 showdown + 7 map), mutation-validated **28/28**. Substrate =
`data/master/ipo_analysis.csv`, **2296 rows**, frozen, as-of `config.AS_OF_DATE` (2026-05-31),
byte-identical to `archive/pre_drhp_20260601/`. Git LOCAL-ONLY._

---

## 🏃 NOW
- **Nothing in progress. The project is complete, verified, and SHOWDOWN-CERTIFIED (2026-06-04)** —
  dataset, 29 findings, predictor, backtester, validation, app, anti-drift checkpoint. The final-showdown
  program (DONE.md) proved: substrate invariants hold (16 data tests), the offline pipeline REPRODUCES the
  frozen substrate (sandbox re-run; returns_summary byte-identical; 34 substrate cells differ, all
  explained), every entry point runs green & read-only, the app renders clean, and the suite kills 28/28
  deliberate code breaks. Pre-release gate: `SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q`.
  Change→tests routing is injected automatically each turn (`verify.py` + `project_map.TEST_ROUTING`).

## 📋 OPEN BACKLOG (all optional — pick when wanted)
- **Microcap extension** — the one major optional item: apply the risk/movement analysis beyond IPOs
  (microcaps first). Scoped in `docs/research/microcap_extension_thinking.md`. A new sub-project.
- (Small-polish items — compute() split, synthetic-fixture tests, DEPS-2 pinning — all DONE 2026-06-04,
  see DONE.md.)

## 🅿 PARKED / REJECTED (decided — don't re-litigate; full evidence in DONE.md)
- **DRHP bulk recovery (~409 old IPOs) — PARKED.** Can't reliably get the useful columns (tool reads
  sales right, profit wrong, debt not at all; high effort). **Analysis unaffected** — missing values are
  skipped, never guessed; validated signals don't use them. Re-open bar + plain summary:
  `docs/research/drhp_recovery.md`. Tooling preserved in `tools/drhp/`.
- **DRHP fold-in of the 16 staged net_sales — DECIDED: DO NOT FOLD** (zero downstream impact, 2/16
  independently validated; DONE.md 2026-06-02).
- **`scrapers/http.py` (broad shared HTTP) — REJECTED** (scrapers deliberately heterogeneous; the name
  would shadow stdlib `http`). The safe slice was done instead: `scrapers/nse_session.py`.
