# Recommendations system — owner discussion log (2026-06-07)

Decisions + requirements from the owner discussion BEFORE design/build. This doc seeds the
brainstorm → spec → plan chain. App design brief = `app_phase2_design.md`; this extends it.

## The core ask
Stop requiring per-stock page visits. A **Recommendations tab** that proactively surfaces calls:
"subscribe to this", "avoid", "track this new listing", "exit review", "take profits" — each
backed by a VALIDATED rule (trust chips; "only what works" — the project's core principle).

## Agreed sections (each maps to a validated finding)
1. 🟢 Worth subscribing / buying — score top-quintile + no N14 flags (forward-tested OOS).
2. 🔴 Avoid — bottom-quintile or 2+ wipeout flags.
3. 🌡️ Header strip "is now a good time?" — F7 cold/hot tape (validated 4/4) + crowded-window.
4. 👀 Recently listed: tracking cards to day 90 — month-1 path-ratio persistence rule.
5. 🚨 Exit review alerts — F5e capitulation flag (day-90 checkpoint) + F10 early bonus/split tell.
6. 📋 Track record — every call logged + graded (see ledger).
EXPLICITLY EXCLUDED (data voted no — do not add): "buy after fall" (F1 dip-buy loses, T2e null,
capitulation = continued weakness), per-stock short-term calls (SHORT score rejected; only the
F7 tape read survives at 3m and lives in the header).

## The calls ledger (owner-approved)
- `data/master/calls_ledger.csv` (or jsonl): call_id, isin, call_date, call_type, rules_fired
  (with input values), mode, grade fields (alpha at 1m/3m FROM CALL DATE), graded_at.
- **mode = live | gap_filled | backfilled** — different evidence strengths, labeled, comparable.
- Every refresh appends new calls + grades matured ones. The tab renders the ledger.

## Requirement: date-driven, NOT run-driven (owner, critical)
If the app isn't run for 10 days, the next run must generate calls FOR EACH MISSED DAY
(anchored to event dates: listing date, day-90 date, ex-date — never "today"), else the track
record becomes a biased sample of "days we ran it". Generator = idempotent cursor walk from the
ledger's last call date. Inputs are all reconstructible (daily bhavcopy, final sub, recorded GMP,
ex-dates). Property tests required: no-look-ahead + idempotence + gap-fill correctness.

## Requirement: backfill the past 5 months (owner)
Replay the 2026 holdout cohort (~88 IPOs) chronologically point-in-time → backfilled calls,
graded. HONESTY LABEL: score-based calls are genuinely OOS (weights pre-date the cohort; forward
test passed); F5e/F10/path-ratio calls are dress-rehearsal (validated on a substrate that includes
these months) — `backfilled` mode marks this. Also: a clearly-labeled historical simulation over
the boom cohort for statistically meaningful exit-alert hit rates.

## Requirement: live + upcoming IPO board (owner, new)
The sites we scrape also list LIVE (subscription window open) + UPCOMING issues. Want: see both,
and for LIVE issues get a subscribe-or-not call. Notes:
- New scraper mode (current/upcoming lists from chittorgarh/ipowatch/investorgain) → `data/live/`
  staging. LIVE DATA NEVER ENTERS THE FROZEN SUBSTRATE (refresh-only discipline preserved).
- Scoring uses the existing live-query path (predict_ipo supports a query object).
- Live calls log to the ledger with mode=live the moment they're made → true forward track record.

## Idea to test: the DAY-1 EARLY CALL (owner, new — needs data scoping FIRST)
Mechanic: subscription accumulates over the ~3-day window (QIB often lands day 3); GMP moves.
Can we issue the subscribe/avoid call on DAY 1 of the window, and how often would it match the
final (full-information) call? → measurable as P(day-1 verdict == final verdict) + the payoff of
acting early vs waiting.
- DATA GATE (T3 discipline — scope before building): we hold FINAL subscription only. Day-wise
  subscription tables exist on chittorgarh per-IPO pages (and NSE during the window) — scope
  historical coverage first; if thin, the test runs forward-only (accumulate as we go live).
- HONESTY NOTE (allotment myth): in an oversubscribed retail book, allotment is a computerized
  LOTTERY — applying day 1 vs day 3 does NOT change odds. The real value of an early call:
  UPI-mandate/cutoff crunch avoidance, GMP moves between day 1 and 3, and decision convenience.
  Frame the feature around THAT, never around "higher allotment chances".
- If day-1 signals show predictive lift beyond convenience, it's a NEW HYPOTHESIS → full 3-layer
  protocol + registry check (`docs/research/hypothesis_protocol.md`).

## Build order (proposed)
A. Calls engine: ledger schema + point-in-time generator + gap-fill + tests.
B. Backfill replay: 2026 cohort + boom historical simulation.
C. Live/upcoming board: scraper mode + live scoring + ledger hookup (depends on A).
D. Day-1 early call: data scoping → (if data) historical test → (regardless) forward accumulation.
E. Recommendations tab UI + app redesign (design agents; renders A–D). LAST.

## Process (owner instruction)
Log this discussion (this file) → superpowers brainstorming per idea (combine where sensible) →
specs → writing-plans → ONE owner discussion round → implement.
