# Improvement backlog — OPEN items only (the single living menu)

> **This lists only what's LEFT to do.** Completed work → git log (history) + `rules/index.md` (signal verdicts).
> Map of all research docs → `docs/research/INDEX.md`. Deeper rationale for feeder ideas → archived planning docs.
>
> Ethos: only-what-works (3-layer validated) · free data · no ML · analog-based · survivorship-honest.
> Each item runs through `execution_pipeline.md`. Status: ⚪ proposed · 🟡 partial · 🔬 research/data-gated. Effort S/M/L.

> **Done in the 2-night batch (2026-06-09/10) — see git log:** A1 (→display-only via review), A2, A3, B1, C2,
> D3/H7, E1, H-MVP, weak-sub guard, I1, J1, J2, app honesty/nav polish. **Net: zero new live-score components
> (all tested signals landed display-only/reject/redundant — the honest outcome).**
> **Done 2026-06-10 (babysat session):** D1/D4 (NSE announcement context feed + full-history pull), **A1b
> (banker coverage-guard hybrid → PROMOTED LIVE by independent review — the ONE signal change that cleared the
> bar: recovers recall + keeps the false-veto fix).**

---

## QUICK / OWNED-DATA (no internet — safe to run anytime)
### F2 — durable monthly "were-we-right" scorecard  🟡 · S
The forward test runs ~monthly; make it an append-only, comparable dated artifact (the credibility spine). Small add
over `run_forward_test`. (F1 paper-portfolio sim + F3 calibration are BUILT — just confirm they're surfaced in the app.)

## OWNED-DATA, BIGGER
### C1 — deeper app polish / redesign pass  🟡 · M · needs the Playwright visual walk
Night-1 shipped the honesty/nav fixes (median-first, n_floor, COMBINED→rank, sidebar search). Remaining: the broader
navigation/redesign from `app_phase2_design.md` + `app_iteration_charter.md`. Design agents MUST load those briefs.

## NEEDS NETWORK / SCRAPING (a babysat session — NOT unattended-safe)
### D1 — RUNG-1 explanatory NSE-announcement context feed (display-only)  ⚪ · M
Dated, ISIN-keyed (free NSE API has `sm_isin`), category-tagged by local keyword taxonomy (NO LLM, NO egress).
"Context, not signal" chip. The honest near-term news product. Spec is turnkey in `newsfeed_rnd_2026-06-09.md`.
### D2 — delivery-volume % conviction signal  🔬 · S-M · DEMOTED
News R&D found it's boom-only (~2017+, no longterm coverage → can't clear cross-regime) + needs a NEW NSE delivery-
bhavcopy pull + no peer-review support. Display-only ceiling at best. Lower priority than once thought.
### D4 — start the NSE-announcement staging pull (forward-collect)  ⚪ · S
The only way to start the ~18–36mo clock that makes any predictive news hypothesis testable later. Stage raw, don't interpret.
### E3 — SME→Mainboard migration as an outcome class + feature  ⚪ · M
The big unmodeled SME escape from the dead-money trap. Needs a dated migration source (Chittorgarh r123 / BSE/NSE).

## ANALYSIS EXTENSIONS (owned-data but hit known walls)
### E2 — unblock P/E-vs-sector for SME + EV/Sales for loss-makers  ⚪ · M
Graduate the watchlisted `pe_vs_sector` (leans −43pp MB) by computing issue-time multiples ourselves. CAVEAT: H-MVP
(2026-06-10) showed valuation is STRUCTURALLY boom-only (zero longterm P/E coverage) — same wall. Boom-only at best.

## BIG / GATED (deliberate "build a new thing" decisions — not now)
### THEME H (full) — relative valuation + intrinsic value  🔬 · L
H-MVP (owned-data peers) done → redundant-with-n6, boom-only. The bigger version (all-stocks point-in-time peer panel,
intrinsic-value models) is a real sub-project; DON'T advance to it on valuation grounds (it hits the same wall). Gated.
### G1 — Microcap / SME-seasoned small-cap RISK & MOVEMENT screener  🔬 · L
The on-moat first slice beyond IPOs; build a SCREENER (risk/movement/quality), NOT a return predictor. Only after the
IPO tool's polish is fully done. Source: `archive/extension_roadmap.md`.
### G2 — Swing-trade buy/sell calls  🔬 · L
Research-gated. EXIT side tested (no blanket take-profit beats hold); ENTRY side weak. Needs a new entry signal that
survives the 3-layer protocol, or the news feed (D1/D2). Source: `archive/future_ideas.md`.

## KILLED — do NOT rabbit-hole
Social sentiment · hosted-LLM headline polarity · RSS fuzzy ISIN-matching · F&O/options-OI · all-stocks TA+FA+news
fusion · weak-subscription veto (2026-06-10: B1's tell was a young-cohort artifact, inverts on matured data) ·
90-day-capitulation SELL & hold-through-drawdown EXIT (selling forfeits the right tail; both display-lean only).

---

## How to use this
- **Pick from here.** Current do-firsts (quick, owned-data): **A1b** (proper banker fix), **I3** (weights hygiene),
  **F2** (durable scorecard). Network items (D1/D4/E3) need a babysat session; H-full/G1/G2 are big-project decisions.
- When an item ships: record it in the git commit, put the signal verdict in `rules/index.md`, remove it from here. New idea → add here first.
