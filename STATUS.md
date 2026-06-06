# STATUS — single live source of "where are we / what's next"

> **Resume the main Claude Code session:** `claude --resume 01820f2d-c29a-4f29-84ad-349ce26b70fa`
> (run from this directory; or `claude --resume` → pick top; `claude -c` = most recent)

> **Rule:** this is the ONE status file — live state + what's next ONLY. **Verify state from GROUND
> TRUTH (files / command output), never from memory.** "What happened" (history) → `DONE.md`.
> "What is this / conventions" → `CLAUDE.md`. "Findings + tested-signal registry" → `rules/index.md`.
> Quick check: `python verify.py` (counts, drift, data-vs-backup; regenerates MAP.md).

_Canonical facts (re-derived by `verify.py` each turn): **29 findings, 211 tests** (96 layer3 + 37
pipeline + 32 scrapers + 25 data + 12 showdown + 7 map), mutation-validated **28/28**. Substrate =
`data/master/ipo_analysis.csv` — movable facts (rows / as-of / backup pointer) live in
`data/master/substrate_meta.json` (currently **2384 rows, as-of 2026-06-06**; snapshot
`archive/pre_refresh_20260606/`). Git LOCAL-ONLY._

---

## 🏃 NOW
- **Nothing in progress. SHOWDOWN-CERTIFIED (2026-06-04) + FIRST REFRESH EXECUTED (2026-06-06):**
  dataset 2296 → **2384 rows** (+88 new 2026 IPOs, prices through 2026-06-05). Full evidence in DONE.md.
- **Short-horizon lens shipped (2026-06-06):** MFE/MAE+timing now at 1m/3m/6m too. Study verdicts:
  crowded-IPO-window signal REAL & negative (display-only, fold-candidate); "hot pops fade" NOT supported
  (strength persists); SHORT score rejected — the LONG score is the better short-horizon predictor
  (`docs/research/context_signals_verdict.md`).
- **Forward test (true OOS, 82 never-seen IPOs): the score ordered early outcomes monotonically**
  (low-score bucket 1m −7.7% / 3m −11.3% vs high-score +6.7% / +8.4%; wipeout-flagged −7.7% vs clean
  +2.9% at 1m). EARLY READ only — `docs/research/forward_test_2026.md`; re-run `run_forward_test.py`
  as the cohort ages.
- The commands that matter: fast suite `PYTHONPATH=. pytest tests -q` (~85s) · pre-release gate
  `SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q` · refresh `python run_refresh.py [--apply]`.
- Change→tests routing is automatic each turn (`verify.py` hook + `project_map.TEST_ROUTING`).

## 📋 OPEN BACKLOG (all optional — pick when wanted)
- **Microcap extension** — the one major optional item: apply the risk/movement analysis beyond IPOs
  (microcaps first). Scoped in `docs/research/microcap_extension_thinking.md`. A new sub-project.

## 🅿 PARKED / REJECTED (decided — don't re-litigate; full evidence in DONE.md)
- **DRHP bulk recovery (~409 old IPOs) — PARKED.** Can't reliably get the useful columns (tool reads
  sales right, profit wrong, debt not at all; high effort). **Analysis unaffected** — missing values are
  skipped, never guessed; validated signals don't use them. Re-open bar + plain summary:
  `docs/research/drhp_recovery.md`. Tooling preserved in `tools/drhp/`.
- **DRHP fold-in of the 16 staged net_sales — DECIDED: DO NOT FOLD** (zero downstream impact, 2/16
  independently validated; DONE.md 2026-06-02).
- **`scrapers/http.py` (broad shared HTTP) — REJECTED** (scrapers deliberately heterogeneous; the name
  would shadow stdlib `http`). The safe slice was done instead: `scrapers/nse_session.py`.
