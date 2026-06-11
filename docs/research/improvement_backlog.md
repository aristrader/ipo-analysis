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
> **Done 2026-06-11:** A1c (richer banker-quality — built + tested + reviewed → NO live change: return DEAD
> cross-regime, downside shelved-at-parity, pricing-discipline→pop real-but-display-only; `a1c_banker_quality_2026-06-11.md`).

---

## QUICK / OWNED-DATA (no internet — safe to run anytime)
### SCORING-ARCHITECTURE — discuss: one consolidated score vs multiple purpose-specific scores?  ⚪ · DISCUSS · owner 2026-06-11
Open question to scope WITH the owner: should the tool keep ONE consolidated score, or split into MULTIPLE
purpose-specific scores (e.g. an allottee/APPLY-pop score vs a from-listing/secondary-buyer alpha score vs a
downside/wipeout-risk score) AND a consolidated roll-up? Motivation surfaced by A1c: signals behave very
differently by HORIZON/role — e.g. pricing-discipline predicts the listing POP (allottee) but NOT sustained
alpha; banker-downside predicts wipeouts but not returns. A single blended score can muddy "good for the
allottee" vs "good for the secondary buyer." Discuss the UX + the validation implications before any build.

## OWNED-DATA, BIGGER
### C1 — deeper app polish / redesign pass  🟡 · M · needs the Playwright visual walk
Night-1 shipped the honesty/nav fixes (median-first, n_floor, COMBINED→rank, sidebar search). Remaining: the broader
navigation/redesign from `app_phase2_design.md` + `app_iteration_charter.md`. Design agents MUST load those briefs.

## DISCUSSION THREADS — owner wants to expand these (scope before building)  ⚪ · owner 2026-06-11
### NEWS+ — extend the announcement feed beyond display (DISCUSS first)
D1/D4 shipped the display-only context feed (built, full history pulled). Owner: "a lot we can discuss and do."
Open directions to scope WITH the owner before building (don't pick unilaterally):
- **surface it in the app** — the last D1 piece: render filings + category chips under each IPO's price chart
  (needs the app work + a visual walk). This is the obvious near-term win.
- per-company **catalyst timeline** / "upcoming events" (board-meeting + event-calendar endpoints exist).
- whether ANY of it can become a *signal* later (RUNG-2) — gated on forward-collected DATE+CATEGORY+DIRECTION and
  the full 3-layer/cross-regime bar; the red-team's prior is "unlikely to clear it" for a daily/free tool. Keep honest.
- D2 delivery-volume% (below) is the other news-adjacent idea.
### MIGRATION+ — extend the SME→Mainboard migration work (DISCUSS first)
E3 shipped the descriptive outcome class (333/1468 = 22.7% migrate; +170% vs −6%). Owner: "a lot we can discuss and
improve." Directions to scope WITH the owner:
- the PREDICTIVE question: an **early, at-IPO marker of EVENTUAL migration** (e.g. IPO-time profitability, issue size,
  subscription, sector) — a look-ahead-SAFE signal, run through the 3-layer/placebo protocol. The real prize.
- add `migrated_to_mainboard` + `migration_date` as substrate COLUMNS at the next pipeline-build (not a post-hoc edit).
- migration as a positive scorecard/analog input IF an at-IPO predictor of it validates.
- time-to-migration distribution + does an SME that migrates *keep* outperforming post-migration (or is the move spent)?

## NEEDS NETWORK / SCRAPING (a babysat session — NOT unattended-safe)
### D2 — delivery-volume % conviction signal  🔬 · S-M · DEMOTED
News R&D found it's boom-only (~2017+, no longterm coverage → can't clear cross-regime) + needs a NEW NSE delivery-
bhavcopy pull + no peer-review support. Display-only ceiling at best. Lower priority than once thought.

> **DONE this session (2026-06-10):** D1 (feed engine + taxonomy), D4 (full-history pull, gitignored), E3
> (SME→Mainboard migration outcome class — owned-data). See git log + `rules/index.md`.

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
