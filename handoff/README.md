# HANDOFF — start here (onboarding for a fresh session / new account)

You are picking up a **mature, solo research project**: a personal tool for finding repeatable,
trustworthy patterns in **Indian IPOs (2006–2026, Mainboard + SME, incl. delisted)**. All three layers
are built, reviewed, and validated. This folder exists so a NEW account/session can get fully up to speed
even though two things do **not** travel with a fresh login (see "What doesn't travel" below).

> **The repo IS the brain.** Almost everything you need is already in version-controlled files that travel
> with this folder. This handoff mostly tells you WHERE to look + captures the few things that would be lost.

---

## 1. READ THESE IN ORDER (the live truth — always trust files/git over any summary)
1. **`CLAUDE.md`** (repo root) — the auto-loaded project brain: what this is, the 3 layers + status, the
   non-negotiable conventions, the repo map, how-we-work. **This supersedes any stale text anywhere.**
2. **`STATUS.md`** — live "where are we / what's next" (the NOW section). History → `git log`.
3. **`rules/index.md`** — the signal/strategy REGISTRY: every signal tested, its verdict (in-score /
   display-only / rejected) + WHY + the numbers. **Consult before re-testing anything.**
4. **`MAP.md`** — generated navigation/tree/flow + a CONTEXT INDEX ("working on X → open these files").
   Generated from `project_map.py` (never hand-edit MAP.md).
5. **`docs/research/task_log.md`** — append-only proof-of-work log, one entry per non-trivial task
   (newest at the relevant spot). The narrative of what was built and why, with verdicts.
6. **`docs/research/improvement_backlog.md`** — the single living menu of what's LEFT to do.
7. **`docs/research/execution_pipeline.md`** — HOW to work (mandatory process; see §4).

Deeper references when needed: `docs/sources.md` (data sources), `docs/schema.md` (columns),
`docs/pipeline.md` (run order), `docs/layer2.md` / `docs/layer3.md` (design), `docs/research/INDEX.md`
(map of all research docs).

## 2. WHAT THE PROJECT IS (one paragraph)
ISIN-keyed dataset of ~2,384 IPOs → daily split/bonus-adjusted prices → outcomes (alpha vs Nifty, from
LISTING) → an analysis engine (`layer3/`) with three products: **(A)** a descriptive report (29 findings),
**(B)** an analog-based "evaluate this IPO" predictor + a multi-component **scorecard**, **(C)** a
backtester vs do-nothing. Plus an interactive **Streamlit app** (`app.py`). Not financial advice; free
data only; **NO machine learning** (small data + transparency → analog/comparables + transparent formulas).

## 3. THE NON-NEGOTIABLE CONVENTIONS (memorize these — violating one = a wrong number or a broken trust rule)
- **ISIN is the primary key** and the ONLY automatic join key. Name-matching never merges (only flags).
  EXCEPTION: corporate actions / banker-style data join by **SYMBOL** (a face-value split changes the ISIN).
- **Returns are ALPHA vs Nifty 50**, measured **FROM LISTING** (secondary-buyer view); the allottee
  additionally gets the listing pop. `adj_listing_gain_*` = the pop. Raw return is secondary.
- **Survivorship-honest:** delisted included; terminal = last price, EXCEPT compulsory/liquidation = −100%.
  Failed names STAY in the denominator — never silently dropped.
- **Prices split/bonus-adjusted;** issue_price adjusted by the same factor for issue-anchored metrics.
- **Score = a SCORECARD of components** combined with preset or data-informed (backtested-lift) weights;
  **cross-regime validated** (boom 2020-26 vs longterm 2006-19). Distributions over means; min-N floors
  (suppress <12, "thin" 12-29, full ≥30); flag, never mis-assign.
- **SCORE POLICY = "evolve-only-if-robust":** a new signal enters the live weighted score ONLY if it
  robustly improves out-of-sample top-quintile lift across splits; else display-only. The default is
  conservative (don't change the live score). The tested-signal registry is `rules/index.md`.
- **No look-ahead / no reverse-causation** (a feature that's secretly an outcome — e.g. CURRENT market cap).
  Point-in-time always.
- **GIT IS LOCAL-ONLY** — `git init`'d for local history/rollback. **NEVER add a remote / push / connect to
  GitHub** until the owner explicitly says so. (Standing owner instruction.)
- **NETWORK = DEFAULT-DENY, trusted-only, ZERO downloads.** Only allowlisted domains are fetchable; off-list
  source → STOP and ask. Read-only, no file downloads. Registry: `docs/research/trusted_sources.md`.
- **Playwright = ALWAYS ON but localhost-pinned** (isolated/headless/version-locked to localhost:8501/8597-99
  only). Rationale: `docs/playwright_on_off.md`. After use: `browser_close`.

## 4. HOW TO WORK (owner mandate — NON-NEGOTIABLE for non-trivial tasks)
Full pipeline per `docs/research/execution_pipeline.md`: **triage path → scope-data → DIVERGE (2-3 parallel
multi-lens thinking agents incl. a red-team) → converge (YAGNI) → plan → BUILD (TDD) → independent REVIEW
agent AFTER the build → fix-to-stop-rule → test+verify → cleanup + task_log entry + pipeline commit trailer.**
The **independent review is non-negotiable on anything showing money numbers / scores** — the owner does NOT
read code, so the review agent IS the quality gate; default conservative (display-only) when not robust.
For research, the placebo/falsifier (`docs/research/hypothesis_protocol.md`) is the "review". Log every
non-trivial task in `task_log.md`. Right-size for trivial work, but say so if skipping a stage.

## 5. SIGNAL-HUNT STATE (digest — full detail in `rules/index.md`)
The tool's signal hunting is essentially **exhausted** and the honest pattern is "most things don't beat
do-nothing." What's LIVE in the score: return-potential, multibagger-odds, downside-safety, **crowded_window**,
wipeout_safety (with the **A1b coverage_guard** banker flag), via data-informed weights. The big VALIDATED
descriptive truths: lasting-wealth (MB underperforms long-run), pop-fade, the SME bimodal "dead-money trap"
(among SMEs that survive ≥5y, ~55% migrate to mainboard and soar; the rest rot). Dozens of hypotheses landed
**display-only or rejected** (banker→alpha is null = "n12"; take-profit/stop-loss don't beat buy-and-hold;
valuation is structurally boom-only; delivery%/weak-sub/etc. — see the registry). **Don't re-test a rejected
signal without new evidence.**

## 6. CURRENT STATE / WHAT'S NEXT (snapshot — confirm against STATUS.md + backlog, which are live)
All 3 layers DONE + reviewed. Recent work (mid-2026): NSE announcement context feed (D1/D4, built + full
history pulled), A1b banker flag (promoted live), I3/F2 hygiene, E3 SME-migration outcome class, A1c
banker-quality (tested → no live change), MIGRATION+ (tested → no signal, corrected the migration base rate).
**What's left is owner-gated, not unattended-safe:** discussion items (scoring architecture: one blended score
vs separate allottee/secondary-buyer/wipeout scores; news-feed and migration directions) and app/UX work (C1
redesign + surfacing the news feed — needs a Playwright visual walk). Big gated builds: Theme-H-full, G1
microcap screener, G2 swing-trade calls. **The quick owned-data signal hunts are done.**

## 7. RUNNING IT
`source .venv/bin/activate`, then: `PYTHONPATH=. python run_all.py` (build dataset) ·
`run_layer3_report.py` / `predict_ipo.py` / `run_backtest.py` / `run_validation.py` / `run_weights.py`
(analysis) · `PYTHONPATH=. streamlit run app.py` (app) · `pytest tests -q` (suite) · `python verify.py`
(checkpoint — also runs each turn via a hook). Env: `PYTHONPATH=.`; **NO scipy/statsmodels** (pure-Python
srho/Wilson/bootstrap helpers). Long pulls are resume-safe + rate-limited.

## 8. WHAT DOESN'T TRAVEL WITH A FRESH LOGIN (captured here)
1. **Auto-memory** (`handoff/auto_memory/`) — lives in `~/.claude/projects/.../memory/`, OUTSIDE the repo, so
   a new account won't have it. Copied here. ⚠ Some of it is HISTORICAL (e.g. old "1269 IPOs / 382 mainboard"
   counts predate the rebuild to 2,384) — **CLAUDE.md/STATUS.md are the live truth; the memory is context.**
   The durable, still-true bits: the owner's **execution-pipeline mandate**, the **movement-lens philosophy**
   ("capture the MOVE + the LIKELIHOOD, not single endpoints; split every analysis by entry"), and the
   ISIN/bhavcopy/Yahoo-can't-do-SME data lessons.
2. **Gitignored config** (`handoff/ENVIRONMENT.md`) — `.claude/settings.local.json` (network allowlist, hooks,
   enabled MCP/plugins) is gitignored; recreate it from that doc. `.mcp.json` (Playwright) IS tracked.
3. **Gitignored DATA** — `data/raw/`, `data/prices/`, `data/reference/bhavcopy/`, `data/live/news/` are
   gitignored (large + regenerable via the scrapers). The CANONICAL outputs (`data/master/*.csv`) ARE tracked.

## 9. OWNER PROFILE (how to work WITH them)
Solo researcher, deeply hands-on about the domain, honesty-first. Does NOT review code → you are the quality
gate (lean on independent review + conservative defaults). Wants the full multi-agent pipeline, not
one-dimensional work. Thinks in movements/likelihoods, not single data points. Privacy/security-conscious
(company laptop): local-only git, no egress, no downloads. Values honest "this doesn't work" verdicts over
forced positives. Re-states the pipeline mandate when it's skipped — treat it as a hard default.
