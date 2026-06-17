# D-1 Plan — TARGETED re-verify of the D1-F1 gate-scoping fix (2026-06-17)

**Scope:** NOT a full re-review. The plan already passed implementability (R5) + all-buckets correctness (R6).
This pass re-verifies ONLY the surface that changed since: the **D1-F1 gate-scoping correction** (window gate =
symbol-added subset only; ISIN-matched actions always apply), the **D1-F2 locus** (gate at the `07` call site,
one windowed `actions` list to both `load_prices` and `compute`), the **F-7 carrier column** plumbing, the
**D1-M1** anti-join comparison, and **supersession-note coherence**. READ-ONLY; no edits, no execution.

**Reviewed:** plan `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`; spec
`docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`; flaw sources
`docs/research/d1_final_correctness_2026-06-17.md` (D1-F1/F2/M1) and
`d1_final_implementability_2026-06-17.md` (F-7/F-1).
**Ground truth (re-derived live):** `pipeline/07_returns_summary.py`, `pipeline/09_assemble.py`,
`data/reference/corp_actions_merged.csv`, `data/master/ipo_analysis.csv`, `data/master/returns_summary.csv`,
`data/prices/`.

---

## VERDICT: **GO (execution-ready)**

The gate-scoping fix is **correct and complete**. The window gate is now scoped to the symbol-added subset
everywhere it matters (join-key block, Task 1 detector/helper, Task 4 reconcile + the `07` call-site gate,
Task 6, Task 8 patch set, Task 11 checklist, spec §1/§3/§6). ISIN-matched actions are stated to ALWAYS apply.
The 26 pre-coverage ISIN-matched splits (ATLANTAA/TARIL/ADANIPORTS/TITAGARH/BAJAJCON) are kept; the 44
symbol-reuse/wrong-era attachments are still dropped; KAUSHALYA's genuine reverse split is NOT a new casualty.
D1-F2, F-7, and D1-M1 are correctly diagnosed and located against the real code. No new regression introduced;
no internal contradiction in the supersession notes. The plan is execution-ready.

---

## The 6 verification items — each CONFIRMED

### 1. D1-F1 fix is correct + complete — CONFIRMED ✅
The gate is scoped to the **symbol-added subset only**, and **ISIN-matched actions ALWAYS apply**, at every locus:
- **Join-key block** (plan 30-55): ISIN-matched "ALWAYS apply … subject only to … price-validation, NOT the
  window gate"; window gate "scoped to the SYMBOL-ADDED subset ONLY"; explicit D1-F1 callout 44-55 with the five
  named regression stocks.
- **Task 1** (plan 89, 128-132): `_in_window_actions` = "(all ISIN-matched events) ∪ (symbol-added events whose
  `ex_date ∈ [first_trade, last_trade]`)"; "ISIN-matched events are NEVER window-dropped (D1-F1)".
- **Task 4 Step 4** (plan 224) + **Step 6** (plan 225): reconcile groups over the union but gates only the
  symbol-added subset; Step 6 assertion (iii) is the explicit D1-F1 regression guard ("an out-of-window event
  that is ISIN-matched … is ALWAYS KEPT").
- **Task 6** (plan 273, note): "ISIN-matched actions are never dropped, so they do NOT land here via the gate".
- **Task 8 Step 2** (plan 301): patch set = "any ISIN-matched event (always admitted) OR an in-window
  symbol-added event"; ATLANTAA/TARIL regression guard pinned.
- **Spec** §1 (26-41), §3 (58-72), §6 (190-194): all symbol-added-only; "NEVER window-drop an ISIN-matched action".

**Ground-truth spot-check of the named regression stocks** — all are ISIN-matched, pre-price-coverage, and
therefore KEPT only because the gate is symbol-added-only. `first_trade` is the **sorted** series start (the
price CSVs are NOT stored in date order; `07.load_prices:222` sorts before the window is read, so the relevant
value is the true `min(date)`):

| stock | substrate ISIN | split (ex_date) | match | first_trade (sorted) | whole-union gate | symbol-added gate |
|---|---|---|---|---|---|---|
| ATLANTAA | INE285H01022 | 5.0 @2010-11-08 | by_isin (row carries the ISIN) | 2017-01-02 | DROP (regression) | **KEEP** ✅ |
| TARIL | INE763I01026 | 1.111 @2013-06-13 (+2017/2025 in-window) | by_isin | 2017-09-29 | DROP 2013 leg | **KEEP** ✅ |
| ADANIPORTS | INE742F01042 | 5.0 @2010-09-23 | by_isin | 2012-01-17 | DROP | **KEEP** ✅ |
| TITAGARH | INE615H01020 | 5.0 @2015-04-23 | by_isin | 2017-01-02 | DROP | **KEEP** ✅ |
| BAJAJCON | INE933K01021 | 5.0 @2011-05-05 | by_isin | 2017-01-02 | DROP | **KEEP** ✅ |

Verified in `corp_actions_merged.csv` that each of these rows carries its ISIN in column 1 (e.g.
`INE285H01022,ATLANTAA,split,…,5.0,2010-11-08`), so it lands in `by_isin[substrate-ISIN]` → ISIN-matched →
never window-dropped. ATLANTAA's `adj_issue` stays 30 (=150/5), not 150. No locus over-applies the gate to
ISIN-matched actions. Fix is correct AND complete.

### 2. No NEW regression from the re-scoping — CONFIRMED ✅
The symbol-added-only gate still drops the bad attachments, AND does not swing too far:
- **PATANJALI** `,PATANJALI,split,…,0.01,2019-11-14` and `…,5.0,2007-10-29` — empty-ISIN yfinance rows →
  `by_symbol["PATANJALI"]` only (symbol-added). PATANJALI's substrate ISIN is `INE619A01035` (its real event is
  the 2025 3:1 bonus). The 2007/2019 events are pre-listing/out-of-window symbol-added → correctly DROPPED.
  (Spec 178-180 explicitly removes PATANJALI as a guardrail and notes its 0.01 would be dropped.)
- **WAAREEINDO** `,WAAREEINDO,split,…,0.01,2022-06-27` — empty-ISIN, symbol-added, out-of-window → DROPPED.
- **SWANDEF** `,SWANDEF,split,…,0.0036…,2023-07-14 / 2023-03-17` — empty-ISIN, symbol-added → DROPPED.
- **KAUSHALYA `0.01` empty-ISIN row** — this is the subtle one. It is symbol-added (empty ISIN →
  `by_symbol["KAUSHALYA"]`, NOT `by_isin[INE234I01028]`), so under the new scoping it IS in the gated subset.
  I verified its admission does NOT regress: `INE234I01028.csv` is unsorted on disk (first physical row
  2024-12-20) but `min(date) = 2007-12-14` and the file DOES contain 2024-01-11 and 2024-02-06. So the true
  in-window check is `2024-01-12 ∈ [2007-12-14, 2026-06-05]` → **in-window → admitted** → its genuine ~100×
  reverse split (bucket 2 must-pass) stays applied. The symbol-added-only scoping does NOT inadvertently drop
  KAUSHALYA. Spec 166-177 documents exactly this (in-window symbol-added, admitted; the two KAUSHALYA companies
  `INE234I01028` vs `INE0Q2V01012`/KLL are disambiguated correctly).

No swing-too-far: the bad reuse/wrong-era rows still drop; the genuine in-window symbol-added event (KAUSHALYA)
is still kept. The re-scoping touches only the **out-of-window** symbol-added set, which is exactly the 44.

### 3. D1-F2 locus — CONFIRMED ✅
The windowed `actions` list is to be built at the CALL SITE and passed to BOTH `load_prices` and `compute()`,
not filtered only inside `load_prices`:
- Plan 57-63 (D1-F2 block), 211, Step 6 (225); spec 66-72 — all say "build the windowed `actions` list ONCE at
  each call site (~599-600, ~630-631) … pass the SAME list to BOTH `load_prices` AND `compute()`" and explicitly
  "Do NOT filter only inside `load_prices`."
- The diagnosis is real against the code: `compute(isin, mrow, prices, actions, …)` (07:424) consumes `actions`
  at `adj_factor_after(actions, listing_date)` (07:438, issue→adj_issue) AND via `_terminal_state(isin, deli,
  actions, …)` → `adj_factor_after(actions, ref_dt)` (07:270, terminal). `load_prices(isin, actions)` is a
  separate consumer (07:600/631, series at 206-235). Three consumers, one list — so filtering only inside
  `load_prices` would desync issue/terminal from the series exactly as F2 claims.
- The call sites are correct: `actions_for(...)` at 599 (test-mode) and 630 (main); `load_prices` at 600/631;
  `build_row(... actions ...)` at 601/632 forwards the same `actions` arg into `compute`. (Minor naming note,
  not a defect: the call sites invoke `build_row`, which forwards `actions` unchanged to `compute`; the plan
  names `compute()` directly. Passing the windowed list as the `actions` arg at the call site reaches both
  `build_row`/`compute` and `load_prices`, achieving the plan's intent verbatim.)

### 4. F-7 carrier column — CONFIRMED ✅ (plumbing claim is real)
- `07.columns()` (07:530-549) currently ends at `listing_metrics_status`, `price_source` — verified on disk; no
  `corp_action_*` column exists yet. Plan 212 + spec 73-77 add the three flag columns here.
- The `09` plumbing is real and exactly as claimed: `ret_keys` is built from the returns-summary row keys
  (09:41-42, excluding identity cols) → `ret_cols = [RET_RENAME.get(c,c) for c in ret_keys]` (09:44) →
  `out_cols = uni_cols + ret_cols + [...]` (09:45), and each row copies `ret_keys` through at 09:68-69. So any
  new column added to `07.columns()` (and emitted by `07`) flows automatically into `ipo_analysis.csv` via
  `ret_keys` with **no extra `09` wiring** — the plan's claim (212) holds. The three flags are not in the
  `RET_RENAME` map and are not identity columns, so they pass through under their own names.
- Confirmed `returns_summary.csv` header today ends `…/listing_metrics_status/price_source` (matches
  `07.columns()`), so the new columns are genuinely additive.

### 5. D1-M1 — CONFIRMED ✅
The anti-join compares the PRE-EXISTING column set only:
- Premise holds: `ipo_analysis.csv` has NO `corp_action_*` columns today (verified header) → the three flags are
  NEW columns that re-serialize every row, which would false-fail a raw byte compare across all 2384 rows.
- Plan states the corrected comparison consistently: 15 (architecture), 301 (Task 8 Step 2: "compared over the
  PRE-EXISTING column set ONLY … restrict each non-corp-action row to the snapshot's column set and additionally
  assert the new flag columns are empty"), 303 (Step 4), 337 (Task 11(d)); spec 128-129. No locus still asks for
  a raw byte-identity over the full new column set.

### 6. Supersession-note coherence — CONFIRMED ✅ (no internal contradiction)
The historical R3/R4 entries vs the new symbol-added-only scope are reconciled, not contradictory:
- **R3** (plan 8) originally said "GATED by the trading-date window" over the whole symbol∪ISIN union, but carries
  an explicit inline correction: *"(SCOPE CORRECTED by R6/D1-F1 below: the gate is symbol-added-only — ISIN-matched
  actions always apply; the real OOW union count is 86, of which only the symbol-added subset (~44) is droppable;
  and the gate is at the `07` CALL SITE, not inside `load_prices`, per R6/D1-F2.)"*
- **R4** (plan 9) N1 ("apply the gate INSIDE `load_prices`") carries an explicit *"NOTE: R6/D1-F2 SUPERSEDES
  this — gate at the CALL SITE"* and the entry is marked *"(superseded by R5/R6)"*.
- The bare **"44"** mentions are all either (a) historical entries with the correction note attached (line 8), or
  (b) R6 finding text that explicitly frames 44 as "symbol-added only" (lines 46, 367), or (c) the self-review
  (367) — none are live build instructions. Every live build instruction (Tasks 1/4/6/8/11, architecture,
  invariants) uses the symbol-added-only scope and the 86/44 split coherently. The R6 fold note (367) accurately
  enumerates where each fix landed. No contradiction.

---

## Plainly stated
- **Is the gate-scoping fix correct?** Yes. The window gate is applied to the symbol-added subset only;
  ISIN-matched actions always apply; verified at every relevant locus and against the on-disk corp-action +
  price data for all five named regression stocks (all ISIN-matched, all pre-coverage, all kept) and the four
  bad-case symbol-reuse stocks (all symbol-added, out-of-window, dropped). KAUSHALYA's genuine in-window
  symbol-added reverse split is correctly preserved — the re-scoping did not over-correct.
- **Is the plan now execution-ready?** Yes. D1-F1, D1-F2, F-7, and D1-M1 are correctly diagnosed, correctly
  located against the real code, and coherently folded with no residual contradictions. GO.

## Notes (informational, NOT blockers)
- N-i: The call sites invoke `build_row` (07:601/632), which forwards `actions` unchanged into `compute`; the
  plan/spec name `compute()` directly. Functionally equivalent — building the windowed list at the call site and
  passing it as the `actions` arg reaches `load_prices`, `build_row`, and `compute`. An implementer should pass
  the windowed list to `build_row` (the actual call) as well as `load_prices`. Cosmetic; intent is unambiguous.
- N-ii: `first_trade`/`last_trade` MUST be read from the **sorted** price series (the CSVs are not stored in
  date order). `07.load_prices` already sorts at 07:222; the gate reads the window after the sort, so this is
  handled — but the implementer must take the window from the sorted dates (`min`/`max`), never the first/last
  physical row. The plan/spec say "read the window from the loaded/sorted prices" (plan 62, spec 69), which is
  correct; this note just underscores why (KAUSHALYA would falsely appear out-of-window otherwise).
