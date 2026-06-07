# Recommendations Tab + App Redesign — design spec (2026-06-07)

Extends `docs/research/app_phase2_design.md` (the standing design brief) with the owner's
recommendations-first requirement. BUILD ORDER: app implementation is LAST (after the calls
engine ships and the ledger is populated); design agents iterate screens before build.

## The change to the IA
The Phase-2 app's DECIDE journey now LANDS on the **Recommendations page** (the "needs
attention" strip from the brief, promoted to the primary surface). Detail pages remain the
drill-down ("why this call?" → IPO Detail Page).

## Recommendations page (renders `data/master/calls_ledger.csv` + `data/live/board.json`)
1. **Header strip** — as-of stamp ("ledger graded to DATE · board fetched AT · refresh") +
   regime banner (Nifty 3m, tape temp F7, crowding) → one line verdict: "engage / selective / wait".
2. **🔴🟢 Live & upcoming board** — open issues w/ subscribe-or-not call (and EARLY call on day 1),
   upcoming list w/ expected-score preview. Each card: trust chips + "why" (rules_fired) + link.
3. **👀 Tracking** — recently listed, day counter to d21 (persistence read) and d90 (capit check).
4. **🚨 Alerts** — EXIT_REVIEW / TAKE_PROFITS calls not yet aged out (≤30d old).
5. **📋 Track record** — per call_type: n, win rate, median alpha vs counterfactual, split by
   mode (live vs gap_filled vs backfilled vs historical_sim — evidence strength visible).
Empty-state honesty: every section renders "none right now" rather than padding.

## Display rules (inherited, non-negotiable)
Trust chips on every card (✓ validated / ~ display-only / ⚠ thin / ✗ rejected-never-shown);
min-N floors; distributions over means; mode labels always visible; "as-of" always visible;
NO dip-buy or per-stock short-term sections (rejected by data — registry is the gatekeeper).

## Rest of the app
Per the standing brief (`app_phase2_design.md`): three journeys, IPO Detail Page hub (8
sections), Evidence Browser (hypothesis records w/ 3-layer tabs incl. graveyard), st.navigation
multipage, lazy price loads, no DB/auth/JS. The two new validated findings land as: F5e → IPO
Detail Page section ⑥ (path vs reference levels gets a "capitulation" badge) + the d90 alert;
F10 → event calendar + TAKE_PROFITS alert.

## Design-agent flow (before build)
Design agents (frontend-design plugin + this spec + the brief) produce per-screen specs/mockups
→ owner reviews screens → build → playwright-verify each screen against its spec.

## Acceptance
- Page loads from ledger+board files only (no engine calls at render time except cached).
- Every displayed call traceable: card → rules_fired → Evidence Browser entry.
- Track-record numbers recomputed from the ledger at render (no hardcoded stats).
