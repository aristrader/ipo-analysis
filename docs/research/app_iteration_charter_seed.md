# App-iteration pipeline — charter seed (owner-approved 2026-06-07, run on restart)

Owner approved the multi-stage iteration pipeline + budget (~870k tokens available, ~3h window).
Playwright is pinned localhost-only via project `.mcp.json` (activates on the restart).

## The pipeline (locked)
PHASE 0 — meta-plan, 3 PARALLEL agents:
- Thinker: propose iteration lenses/count/order + per-iteration playwright walk-scripts
  ("open X, click Y, expect Z") + exit criteria.
- UX-critic: attack that plan from the single-user research-terminal angle (not generic web
  heuristics); add missing lenses. Starting lenses to beat: 1 BREAK-IT (hostile/edge data:
  delisted ISIN, 2006 cohort no-GMP, unpriced, weird query params, every link) ·
  2 BE-THE-OWNER journeys ("Hexagon closes tomorrow — apply?" ≤2 clicks; "why is
  crowded_window in score?" ≤3 clicks; half-remembered-name findability) ·
  3 FAST-AND-CALM (page latency/caching, plain wording, hierarchy, chip consistency) ·
  candidate 4: DATA-HONESTY-ON-SCREEN (numbers correct, not just rendered).
- Code-prophet: read app/ code (app.py, app/ui.py, app/screens/*) WITHOUT running; predict bug
  hotspots (edge data, cache staleness, cross-screen state, ledger-key mismatches).
→ Main session synthesizes the LOCKED CHARTER (n iterations decided by evidence, not fixed at 3).

PER ITERATION (sequential): brainstorm-for-lens (frontend-design skill when UI changes in scope)
→ walker agent (playwright, the walk-script, findings w/ evidence) → review agent triages
(adversarial; real/cosmetic/dupe/wishlist) → fix INLINE (sequential fixes only — never parallel
on the same screens) → playwright re-walk of fixed paths + full fast suite → 3-line retro that
AMENDS the next iteration's charter. TAPER ceremony: full walker+reviewer in iter 1; shrink
review as findings drop; iter 3 likely self-triaged.

## Frontend-test policy (owner-decided)
- ADD: (a) extend tests/showdown app smoke with key-content asserts per page (≥1 call card or
  "none right now" on Recommendations, etc.); (b) ~10 unit tests for app/ui.py LOGIC (chip
  mapping, n_floor, formatters, ledger call-lookup keys — yesterday's bug class).
- SKIP (explicitly rejected as too much): per-screen browser tests, visual/snapshot tests,
  Streamlit component tests. Layout/journey QA = the recurring playwright iterations, not
  frozen test code. "Logic gets tests, layout gets walked."

## Rails
- Fixes never invent features mid-flight: big ideas → ranked owner improvement list.
- App runs at: PYTHONPATH=. streamlit run app.py --server.headless true --server.port 8597
  (port is in the playwright allowlist: 8501/8597/8598/8599).
- Suite must stay green each iteration; verify.py clean; commit per iteration.
- Final deliverable: combined report (found/fixed/deferred/improvement list) + cleanups.
