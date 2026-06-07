# CODE-PROPHET iteration plan — predicted breakages (read-only audit, app NOT run)

Audited: `app.py`, `app/ui.py`, all `app/screens/*`, `layer3/calls.py` (td_offset/context_at),
`layer3/predictor/predict.py` schema, `app/records/signals.json` (5 recs), `data/live/board.json`.
Live data observed: board has `isin: null` on every open/upcoming row; ledger has grade_status
{final 3523, partial 1570, pending 73}, mode {historical_sim 4693, backfilled 469, live 4}.

## 1. RANKED PREDICTED BUGS (file:line · trigger · symptom · repro)

### P0 — likely crash / wrong number a walker will hit on a normal click

1. **`ipo_detail.py:328` listing-day high — empty-mask `.iloc[0]` on KeyError-shaped slice.**
   `prices[prices["date"] == prices[prices["date"] >= list_d]["date"].min()]` → if NO price row is on/after
   `list_d` (price file ends before listing_date, or all dates < list_d), inner `.min()` is `NaT`, outer mask is
   all-False, `ld_rows` empty → guarded by `len(ld_rows)`. BUT if `prices` has a date exactly == NaT match it can
   return 0 rows; the `.high.iloc[0]` is guarded. Lower risk than it looks, but the double-mask is fragile and slow.
   Repro: open a delisted/early IPO whose `data/prices/<isin>.csv` predates its `listing_date`. `?isin=<that>`.

2. **`home.py:28` `n_graded` counts only `grade_status=="final"`, silently dropping 1570 `partial` rows.**
   Trigger: always. Symptom: HOME shows "N calls graded" far LOWER than Recommendations/Track-Record imply (those
   use `_win`/groupby across partial too) — an internal contradiction the walker will flag as the app "lying."
   Repro: open HOME, read "Track record — N graded (M total)"; cross-check Track Record tab table sum.

3. **`recommendations.py:101` + `home.py` live-call lookup keyed by ISIN set — board ISINs are ALL null.**
   `keys = {k for k in (isin, slug, name) if k}` then `ledger["isin"].isin(keys)`. With live `run_calls --live`
   keying by slug/name this works ONLY if the ledger stored slug/name in the `isin` column. Observed ledger is
   100% exchange-ISIN keyed (historical_sim/backfilled); the 4 `live` rows are the only ones that could match by
   slug. So every OPEN board row → "call: pending" even when a live call exists keyed by exchange ISIN that the
   board hasn't resolved yet. This is the exact known-bug class (slug-keyed live vs ISIN-keyed ledger).
   Repro: open Recommendations with a live board present; confirm every OPEN card says "pending."

4. **`ipo_detail.py:44-45` name dropdown builds 2,296-row `df.apply(_name_of, axis=1)` every render, unkeyed.**
   Not a crash but: `_name_of` (line 18-23) returns `row.get("isin")` when all name cols are NaN floats; if `isin`
   itself is NaN the option label is `nan (MB, nan)` and `options[pick]` maps to a NaN ISIN → `st.query_params["isin"]
   = nan` → next load `df[df["isin"]==nan]` empty → falls through to the score form (silent dead-end, no error).
   Repro: pick any row whose isin is blank from the "Search by name" selectbox.

### P1 — wrong/garbage handling, friendly-error gaps

5. **`ipo_detail.py:26-34` `?isin=` garbage → silently shows the SCORE FORM, not a "not found" message.**
   `qp.get("isin")` truthy but `m` empty → `row=None`, `session_q=None` → score-form branch. User who typed a bad
   ISIN sees a generic form with no "ISIN X not found." Repro: `?isin=GARBAGE123`.

6. **`ipo_detail.py:108-110` predict() failure surfaces as a RAW TRACEBACK (no try/except).**
   `predict_cached(...)` is unguarded on the detail page (Recommendations preview at :147 IS guarded). Any analog/
   scorecard exception (e.g. a malformed session query, an unknown sector slug, an all-NaN numeric) → Streamlit red
   traceback, not a friendly error. Repro: score a new IPO with Sector="(any)" + everything 0 so the query is just
   `{type, name}` and force a thin/empty cohort; or pass a sector that exists in the list but has <1 analog of that type.

7. **`ipo_detail.py:136` `ar["n_cohort"] < ui.MIN_N` assumes `n_cohort` always present & int.**
   If `find_analogs` ever returns n_cohort=None (no rows), `None < int` → TypeError crash. Tied to #6.

8. **`recommendations.py:107`,`149` `o['name']` / `o['type']` direct-index (not `.get`).**
   Board row missing `name` or `type` → KeyError raw traceback. The de-dupe at :89 uses `.get` but the render uses
   `o['name']`. A stale/partial board.json (known class) triggers it. Repro: hand-edit board.json to drop a `name`.

9. **`ipo_detail.py:198` SME dead-money: `(ob.get('terminal_dead_money_%') or 0) >= 5` — value may be a STRING.**
   `outcome_breakdown` bucket values render as `f"{bd.get(key,'—')}%"` (line 181) implying they're numbers, but if
   any come through as preformatted strings, `"x" >= 5` → TypeError in py3. Verify the spine returns numerics.
   Repro: open any SME detail with ≥5% dead-money analogs.

10. **`ipo_detail.py:295` `sym.upper()` — guarded by isinstance(str), OK; but `a['action_type']`/`a['symbol']`
    direct-index at :295/:299 assume corp_actions columns exist.** If `corp_actions.csv` schema drifts (no
    `symbol`/`action_type`/`ex_date`), KeyError. Repro: trim a column from corp_actions.csv.

### P2 — display lies / staleness (no crash)

11. **`ui.py:198` `n_floor`→`win_%` shows the FLOOR STRING in a numeric column.** Track-record table mixes
    `"N=3 — too few to say"` strings with `"61%"` strings in `win_%` — fine as object col, but `median Δα` then
    shows "—". Cosmetic; a walker may read it as broken. (recommendations.py:233, track_record.py:66)

12. **`recommendations.py:163` TRACK age uses calendar-day `call_date` filter but milestones map td→cal by
    fixed 30/126 (`age_d<30`,`<126`).** bdate-vs-NSE-calendar mismatch (known class): a name listed 28 calendar
    days ago but only ~19 trading days shows "d21 in ~2d" when d21 already passed. Display only. Repro: any TRACK
    row 20–30 days old.

13. **`home.py:69` `0 <= (cd-today).days <= 7` uses `pd.Timestamp.now().normalize()` vs board `close_date`** —
    a window closing TODAY at a past hour still counts (fine), but `today` here vs `today` in recommendations
    (`pd.Timestamp.now().normalize()`) are consistent. No bug, but timezone-naive now() can flip at midnight UTC vs IST.

## 2. CACHE-STALENESS MAP (every `@st.cache_data` in app/ui.py — all default TTL = ∞)

| Loader | Reads | What busts it | What NEVER busts it |
|---|---|---|---|
| `load_df` (217) | substrate CSV | only `exclude_low_quality` arg change | editing `ipo_analysis.csv` on disk |
| `sectors` (222) | load_df | — | substrate change |
| `load_ledger` (227) | `calls_ledger.csv` | nothing | **`run_calls.py` rewriting the CSV** ← stale after Refresh |
| `load_board` (238) | `board.json` | nothing | **`scrapers.live_board` rewriting board.json** ← stale after Refresh |
| `load_records` (249) | `signals.json` | nothing | records agent writing the file |
| `load_families` (262) | `families.json` | nothing | regeneration |
| `load_prices(isin)` (274) | per-ISIN CSV | the `isin` arg | price-file edits |
| `load_corp_actions` (287) | corp_actions.csv | nothing | corp-action refresh |
| `predict_cached` (295) | query+profile | query/profile/excl change | **substrate change (df reloaded but cached-by-args)** |
| `regime_read` (321) | load_df + context | nothing (no args) | substrate change AND wall-clock day rollover (uses `datetime.now()` but cached → freezes "today") |
| `oos_table`/`backtest_tables`/`validation_table` (track_record) | load_df | nothing | substrate change |

**THE refresh gap (CRITICAL):** `recommendations.py:30-37` "Run refresh now" calls `run_refresh.find_new()` which
rewrites `board.json`/`calls_ledger.csv` on disk, then says "re-open the page." But `load_board`/`load_ledger` are
cached with NO TTL and NO `st.cache_data.clear()` after refresh → **the page shows the OLD board/ledger until the
whole server restarts.** Same for `data.py:97` "Check for new listings." `regime_read` additionally freezes
`datetime.now()` so the regime banner's "today"-anchored tape never advances within a server session.
**Fix direction:** call `st.cache_data.clear()` (or per-loader `.clear()`) inside both refresh buttons; give
`regime_read` a date arg so day-rollover busts it.

## 3. TOP-5 FILES/FUNCTIONS WORTH A UNIT TEST (feeds tests/app/test_ui_logic.py)

1. **`ui.chip_status` / `ui.chip`** — feed every status seen in signals.json (`in_score`, `display_only`,
   `parked`, `graveyard`), plus `None`, `float('nan')`, `""`, unknown string → assert all map to one of 4 keys and
   `chip()` never KeyErrors. (Guards the known NaN-to-.strip() class: line 55 `str(status)` already coerces — assert it.)
2. **`ui.match_cond`** — literal, dict {gte/lte/in/neq}, NaN val, string-vs-float, missing key → assert no raise.
3. **`ui.money`/`frac`/`pct`/`pct_pp`/`n_floor`** — None, NaN, non-numeric string, 0, negative, ≥1000 → assert
   formatting + that `n_floor` returns "N unknown" on garbage and the floor string below MIN_N.
4. **`track_record.win_flag` / `recommendations.win_flag`** (duplicated! extract to ui) — APPLY/AVOID/EXIT with
   NaN alpha_1y/alpha_3m, unknown call_type → assert None vs bool, never raise. Also assert the two copies match.
5. **board-call matching logic (`recommendations.py:99-104`)** — extract to a pure `find_live_call(ledger, isin,
   slug, name)`; test the slug-keyed-vs-ISIN-keyed mismatch (bug #3) with both a null-ISIN board row and an
   ISIN-keyed ledger; assert it finds the call by slug AND documents that exchange-ISIN-only calls won't match.

---
## 10-LINE SUMMARY — top-5 predicted bugs
1. **Refresh does NOT bust caches** (ui.py 227/238, recommendations.py 30): "Run refresh now" rewrites board.json
   + calls_ledger.csv but cached loaders have no TTL/clear → page keeps showing stale data until server restart.
2. **Every OPEN board card shows "call: pending"** (recommendations.py 101): board ISINs are all null; ledger is
   exchange-ISIN-keyed, so slug/name `.isin()` lookup never matches live calls (the known slug-vs-ISIN class).
3. **`?isin=garbage` silently shows the score FORM** (ipo_detail.py 26-37) instead of a "not found" message —
   and picking a blank-ISIN name from the dropdown dead-ends the same way.
4. **predict() on the detail page is unguarded** (ipo_detail.py 108) → a thin/empty cohort or odd query surfaces a
   raw red traceback, not a friendly error (the preview path at :147 IS guarded; detail isn't).
5. **HOME undercounts graded calls** (home.py 28): counts only grade_status=="final", dropping 1570 "partial" rows,
   so HOME contradicts the Track-Record table — reads as the app lying. Plus board `o['name']` direct-index (rec.py
   107) crashes on a stale/partial board.json.
