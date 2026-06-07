# Calls Engine — design spec (2026-06-07)

Owner requirements: `docs/research/recommendations_system_discussion.md` (pre-approved).
Owner granted assumption-autonomy for small decisions (logged in §Assumptions).

## Purpose
Turn the validated rules into NAMED, DATED, GRADED CALLS in a persistent ledger, so the app's
Recommendations tab renders a track record instead of on-demand opinions. Date-driven (gap-fill),
point-in-time, idempotent, label-honest (live / gap_filled / backfilled / historical_sim).

## Components (each independently testable)

### 1. The ledger — `data/master/calls_ledger.csv`
One row per call; grades updated in place (idempotent by `call_id`).
Columns:
- `call_id` = `{isin}|{call_type}|{call_date}` (natural key, dedup anchor)
- `isin, name, type` (MB/SME), `cohort`
- `call_date` (the date the call is FOR — event-anchored, never "run date")
- `call_type` — see §2
- `mode` — `live | gap_filled | backfilled | historical_sim`
- `rules_fired` — compact `rule=value;rule=value` (e.g. `score_q=5;n14_flags=0;tape=cold`)
- inputs: `score, score_quintile, n14_flags, tape_state, crowding_pctl`
- grades: `pop_pct` (APPLY only), `alpha_1m, alpha_3m, alpha_1y` (FROM CALL DATE; APPLY/EARLY
  grade from listing as the allottee), `early_final_agree` (EARLY only), `grade_status`
  (`pending|partial|final`), `graded_at`
CSV not JSONL: project convention, DuckDB-queryable, app reads it directly.

### 2. Call types & event anchors (only validated rules — "only what works")
| call_type | anchor date | rule | grading |
|---|---|---|---|
| APPLY / AVOID / NEUTRAL | close_date (final sub knowable that evening) | PIT score quintile within segment + N14 flags. APPLY = top-quintile AND 0 flags; AVOID = bottom-quintile OR ≥2 flags; else NEUTRAL | allottee: pop + alpha 1m/3m/1y from listing |
| EARLY_APPLY / EARLY_AVOID / EARLY_NEUTRAL | open_date | same engine on day-1 partial inputs (day-1 sub + day-1 GMP). FORWARD-ONLY until day-wise data exists | `early_final_agree` vs the close-date call + same allottee payoffs |
| TRACK | listing_date | every new listing gets a tracking card | informational; alpha snapshots |
| PERSIST_HOLD / PERSIST_EXIT_LEAN | listing + 21 trading days | month-1 path-ratio persistence rule (robust 4/4) | forward alpha from call date (did the lean point right?) |
| EXIT_REVIEW / CLEARED_ISSUE | listing + 90 trading days | F5e capitulation flag (validated, no-look-ahead) | forward alpha from call date (EXIT_REVIEW "wins" if fwd alpha < segment median ⇒ exiting saved money) |
| TAKE_PROFITS | corp-action ex_date if ≤365d post-listing | F10 early bonus/split tell (thin n=31 — chip says "validated-thin") | forward 3m alpha from ex_date (win = negative) |
Tape state (F7 trailing climate) + crowding stamped as INPUT COLUMNS on every call (header
context), never separate per-stock short-term calls (rejected). NO dip-buy calls (rejected).

### 3. Generator — `layer3/calls.py` (pure, UI-agnostic) + `run_calls.py` (CLI)
- `events_between(d0, d1, df, ca)` → dated events from substrate + corp_actions (close dates,
  listing dates, +21td, +90td anchors via the Nifty trading calendar, ex-dates).
- `make_call(event, pit_scores, prices_root)` → call dict using ONLY data dated ≤ call_date.
- `run_calls.py`: cursor = max(call_date) in ledger → walks cursor+1 .. today → appends new,
  grades matured (`--grade-only`, `--backfill FROM TO`, `--mode` override). Gap-fill = the SAME
  cursor walk; a 10-day gap produces 10 days of calls, each dated to its event.
- PIT scores: passed IN as a frame — sources: forward-test scoring (2026 cohort),
  `score_all_pointintime` (historical_sim), live-query predict (live). Generator never scores.
- Refresh hook: `run_refresh.py` final phase invokes the cursor walk + grading (mode=gap_filled
  when filling missed days; live calls made same-day get mode=live).

### 4. Backfill replay (`run_calls.py --backfill`)
- 2026 cohort (listings after substrate prior as-of 2026-01): mode=`backfilled`. Score-based
  calls genuinely OOS; F5e/F10/persistence = dress rehearsal (labeled).
- Boom cohort 2020-25: mode=`historical_sim` — statistically meaningful exit-alert hit rates.
- Longterm cohort EXCLUDED (GMP/sub coverage too sparse for honest apply calls).

### 5. Live & upcoming board — `scrapers/live_board.py` → `data/live/`
- Fetches: chittorgarh current+upcoming list (+ per-IPO detail for live ones: day-wise sub if
  shown, GMP via ipowatch/investorgain live pages).
- Writes `data/live/board.json` {fetched_at, upcoming[], open[]} + appends daily snapshot rows to
  `data/live/daywise_sub.csv` (isin?, name, date, day_n, sub_qib/nii/retail/total, gmp) — this
  ACCUMULATES the day-wise dataset for the day-1 accuracy question (forward path).
- **Never writes under `data/master/`** (frozen-substrate discipline). IPOs enter the substrate
  only via `run_refresh.py` later. Live scoring via the existing predict query path.

### 6. Day-1 scoping — `tools/research/scope_daywise_sub.py` (DO FIRST in the plan)
Sample ~30 historical chittorgarh IPO pages across 2021-2026; report day-wise-subscription table
coverage. Branch A (coverage good): scrape + backtest P(day-1 verdict == final). Branch B (thin):
forward-collection only (owner accepted). Verdict recorded in the discussion doc.

## No-look-ahead, idempotence, gap-fill — PROPERTY TESTS (tests/layer3/test_calls.py)
1. Generator fed data truncated at call_date produces the identical call (no future columns used).
2. Running the walk twice == once (call_id dedup; grades stable).
3. Walking [d0,d5] then [d6,d10] == walking [d0,d10] in one go.
4. Grades recompute only `pending|partial`; `final` rows never change.
5. Ledger schema lock (columns + dtypes) — mirrors substrate invariant tests.

## Integration & wiring
- `project_map.py`: new files registered; CONTEXT "recommendations / calls"; TEST_ROUTING
  (`layer3/calls.py` → `tests/layer3/test_calls.py`).
- `verify.py` picks paths up automatically. STATUS/rules untouched (engine, not findings).
- App (spec 2) is a pure READER of ledger + board.json.

## Assumptions made under owner autonomy (flag at discussion round)
A1 CSV ledger (not jsonl). A2 Thresholds: top/bottom QUINTILE within segment + flag rules as
above (parameters, easy to change). A3 Close-date = the apply-call anchor (final sub published
that evening; T+3 leaves a day before listing to act for secondary planning; allotment-window
nuance noted). A4 EXIT_REVIEW "win" definition = fwd alpha below segment median. A5 Longterm
cohort excluded from historical_sim. A6 Live board sources = chittorgarh + ipowatch/investorgain
(existing scraper stack), best-effort parsing with explicit "unknown" fields (never fake).
