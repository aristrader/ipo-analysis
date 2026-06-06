# App Phase-2 Design — Information Architecture (v1, 2026-06-06)

Living design doc — iterate after every research run; IMPLEMENT at end of Phase 2.
Grounded in app.py + the engine's predict() return shape + the Phase-2 program.

## Core idea: three JOURNEYS, one hub object (the IPO)
The 5-tab app is a flat menu of engine outputs; Phase 2 triples content. Reorganize by user intent:
- **DECIDE** — "an IPO is in front of me, what do I do?" → Score form → **IPO Detail Page** (hub) →
  Live & Upcoming cluster board.
- **LEARN** — "what does the research say?" → Findings report · **Evidence Browser** (8 families ×
  26 hypotheses × 3 layers) · **Signal Registry** (in-score/display/watchlist/GRAVEYARD) · Explorer.
- **MONITOR** — "what's happening now / did past calls work?" → **Event Calendar** (anchor unlocks
  day-30/90 = knowable in advance!) · Forward-Test Tracker · Backtester.
- DATA — refresh + methodology.
HOME = regime banner (Nifty 3m, IPO climate, persistent app-wide) + 3 journey cards + "needs
attention" strip (windows open this week, unlocks in 14d, forward-test age).
Drill-down spine everywhere: list → object → layer. Cross-links all land on the IPO Detail Page.

## Trust language (non-negotiable, every card): chips
✓ VALIDATED (cross-regime+OOS) · ~ DISPLAY-ONLY · ⚠ HYPOTHESIS · ✗ REJECTED — one shared chip()
helper, same colors everywhere. The graveyard is first-class and browsable.

## The IPO Detail Page (the centerpiece; one template for NEW and HISTORICAL IPOs)
Vertical order = how a decision-maker reads: ① VERDICT bar (combined score + wipeout-risk gauge)
→ ② THE FULL PICTURE (analog outcome buckets, P90/median/P10, terminal risks) → ③ scorecard (8
components + flags) → ④ CLUSTER CONTEXT (its competitive window, GMP rank in cluster) → ⑤ EVENT
CALENDAR (its day-30/90 unlocks + F1c triple-warning) → ⑥ PATH vs REFERENCE LEVELS (price chart
with issue-price + listing-day-high lines, reclaim/breakout status, reach ladder) → ⑦ PLAYBOOKS
THAT APPLY (registry filtered by applicability predicate, with trust chips) → ⑧ comparables table.
New IPOs degrade gracefully: analog-expected values where realized would be, labeled "expected".

## Evidence Browser (Family → Hypothesis → the 3 layer-tabs)
Family index with status rollups + tier/status filters. Hypothesis page = tabs in protocol order:
EXISTENCE (plain-English verdict + falsifier/placebo result PROMINENT + cross-regime/OOS chips) ·
MAGNITUDE (dose-response tables) · PLAYBOOK (the WHOLE pre-declared grid — never best-cell-only —
payoffs vs buy-and-hold + FAILURE CELLS block + "applies to N live IPOs" link). Graveyard uses the
same template with a "why rejected / do-not-retest" panel.
**Structural investment:** hypotheses + registry entries become DATA RECORDS
{id, family, tier, mechanism, status, existence{...}, magnitude[tables], playbook{grid, payoffs,
failure_cells, applies_predicate}}; browser + per-IPO playbook matcher = generic renderers.
That makes 26→50 hypotheses a data problem, not a UI rewrite.

## BUILDABLE NOW (before any new hypothesis lands; ranked value/effort)
1. Persistent regime banner (context.nifty_mom_3m + 60d pop median) — do first.
2. IPO Detail Page on historical IPOs (predict() already returns everything).
3. Event Calendar from anchor math (pure date arithmetic; dose from anchor_allocation_cr; ships
   DISPLAY-ONLY before F1 graduates).
4. rules/index.md → structured Signal Registry records + screen.
5. Path-vs-reference chart (per-ISIN prices + 2 hlines).
6. Cluster helper + Live board skeleton (works on historical clusters now).
7. Score-form → compact verdict card → "open full evaluation" (session-state handoff).
8. Shared trust-chip component.

## Tech notes
Switch tabs → st.navigation/st.Page multipage (tabs re-render everything every rerun; pages don't,
and cross-links need URLs). cache_data on substrate/backtests/records; cache predict() keyed on
query. Load price files LAZILY per detail page, downsample to weekly for multi-year charts. Altair/
Plotly only for the two charts Streamlit natives can't do (reference-line chart, cluster Gantt).
DO NOT: add a database, auth, live feeds, client-side JS, or precompute all hypotheses per load.
Verify before calendar build: anchor share present per row, else show "dose: unknown" (never fake).
