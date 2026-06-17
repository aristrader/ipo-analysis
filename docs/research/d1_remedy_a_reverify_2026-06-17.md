# D-1 Remedy (a) Targeted Re-Verify — price-validation reaches the `07` substrate path (2026-06-17)

**Scope:** ONE fix only — R8/remedy (a): does the per-action price-validation now genuinely reach the substrate-reaching
`07` path (Task 4 Step 6b), inherited by the Task-8 patch via `07.compute()`, and does it introduce no new regression?
**READ-ONLY.** Not a full re-review. Verified against `pipeline/07_returns_summary.py`,
`data/reference/corp_actions_merged.csv`, `data/master/ipo_analysis.csv`, `data/prices/`, the spec, and the plan
(Task 4 Step 6/6b, Tasks 1/6/8/9, state-log R9).

---

## VERDICT: **GO (build-ready)**

Remedy (a) is correctly folded. The price-validation is wired at the genuine substrate-reaching locus (the `07` call
site, both ~599-600 and ~630-631), inherited by the Task-8 patch via `07.compute()`, and is NOT confined to the
orphaned `03k`/`03l`. The CANTABIL/GNA collapse logic produces exactly the corrected magnitudes the plan claims
(~7.14× and ~2.70×) when traced against the real price files. The phantom-drop vs coverage-hole-defer distinction is
present in both spec and plan and ROLEXRINGS is protected via its override seed. No new regression on legitimate
single splits or ISIN-matched events. The plan is build-ready. One LOW documentation nit (#1) is worth folding for
build-time clarity but is not a blocker — the implementation behavior is already correct because the override is
consulted with the measured gap.

---

## Confirm / refute the 6 required items

### 1. Price-validation reaches the substrate path — **CONFIRMED**
The two `07` call sites are exactly as the plan states (verified on disk):
- Test-mode: `pipeline/07_returns_summary.py:599-601` — `actions = actions_for(...)` → `prices = load_prices(isin, actions)` → `build_row(... actions ...)`.
- Main: `pipeline/07_returns_summary.py:630-632` — identical structure.
`build_row` (564-571) calls `compute(... actions ...)` (424), and inside `compute` the SAME `actions` list feeds
`adj_factor_after` for `adj_issue` (438) and the terminal (449→270), while `load_prices` (206-235) adjusts the series.
There is currently **no gap check anywhere in `07`** (confirmed: `load_prices` 226-234 and `adj_factor_after` 239-246
blindly multiply every `ratio_factor`). So Step 6b's insertion point — building the validated `actions` list once at
each call site and passing the SAME list to BOTH `load_prices` AND `compute()` — is genuinely the substrate-reaching
path. Task 8's patch reuses `07.compute()`/`load_prices` (plan Task 8 Step 3), so it inherits the validation
automatically. The DAG-orphaned `03k`/`03l` are NOT relied upon for substrate correctness. The R8 break (validation
only in the orphan) is closed. **No path where an unvalidated factor still reaches the substrate.**

### 2. CANTABIL + GNA collapse to ONE — **CONFIRMED (traced against real prices)**
Corp-action rows (`corp_actions_merged.csv`):
- CANTABIL `INE068L01024`: 5.0 @2023-11-02 (NSE, ISIN `INE068L01016` = old pre-split ISIN) + 5.0 @2023-10-20 (yfinance, symbol-only). **Both reach the substrate purely via `by_symbol["CANTABIL"]`** (the NSE leg's ISIN `INE068L01016` ≠ substrate `INE068L01024`), so both are symbol-added, both in-window → bare product 25.
- GNA `INE934S01014`: 2.0 @2023-09-01 (NSE, **ISIN-matched**) + 2.0 @2023-08-11 (yfinance, symbol-only) → bare product 4.

Index-adjacent price gaps (`data/prices/<substrate-ISIN>.csv`, window ±3 series positions):
- CANTABIL 2023-10-20: max adjacent ratio **1.05** (1131.25→…) = PHANTOM → DROP. 2023-11-02: **5.20** (1131.25→217.75) = real → APPLY. Net factor **5** → adj_issue 135/5 = 27.0 → return 219.65/27 − 1 = **7.14×** ✅ (NOT a multibagger by magnitude; current substrate shows adj_issue 5.4, cur_ret 39.68, class `multibagger`).
- GNA 2023-08-11: max ratio **1.02** = PHANTOM → DROP. 2023-09-01: **1.88 (~2×)** = real → APPLY. Net factor **2** → adj_issue 207/2 = 103.5 → return 382.55/103.5 − 1 = **2.70×** ✅ (current substrate: adj_issue 51.75, cur_ret 6.39, class `multibagger`).

The collapse logic produces the exact magnitudes the plan claims. They are in the tests: Task 1 detector parametrize
(RED — pre-validation squared factor 25/4, plan lines 127-128), Task 8 Step 2 substrate GREEN (~7.14× / ~2.70×, NOT
multibagger, plan line 324), Task 9 Step 1(a) resolved-detector (`applied_effective/max_gap ≈ 1` after collapse, plan
line 334). GNA additionally proves the mixed case (phantom = symbol-added yfinance, real = ISIN-matched) — the window
gate alone keeps BOTH (both in-window); only the per-action price-validation drops the phantom, which is precisely the
load-bearing point of remedy (a).

### 3. Phantom-drop vs coverage-hole-defer distinction — **CONFIRMED (with LOW nit #1)**
Both spec (`...design.md:92-98`) and plan (Step 6b line 247; Task 4 Step 2 lines 241-242) carry the four-way outcome
and EXPLICITLY distinguish: "no gap because price PRESENT (flat) → phantom → DROP + `corp_action_no_price_gap`" vs
"no gap because price MISSING (coverage hole) → defer to override (apply if seed, else flag); never wrongly drop."
ROLEXRINGS is named as the coverage-hole case and the plan asserts it is NOT phantom-dropped (Task 4 Step 2 line 242;
Task 8 Step 2 line 324; Task 9 Step 1(c) line 336). The override seed is real: `corp_action_external_evidence.csv`
carries `INE645S01024,ROLEXRINGS,...resolve-apply-once...factor 10.0...gap ~19.96x...ONE real 10:1`, and the plan pins
this seed literally (F-4, line 204). ROLEXRINGS resolves via override → stays resolved (not nulled, not dropped).
**See nit #1 for the one wording imprecision** (the gap is NON-None ~20×, not literally "missing"), which does not
change the correct outcome.

### 4. No NEW regression on legitimate splits — **CONFIRMED**
- A clean in-window single split WITH a supporting gap → branch (1) gap-supports → applied unchanged. CANTABIL's
  2023-11-02 leg (gap 5.20 ≈ 5) and GNA's 2023-09-01 leg (gap 1.88 ≈ 2) are themselves the proof: the real legs are
  kept, only the flat phantoms are dropped.
- ISIN-matched events ALWAYS apply (D1-F1, never window-dropped) and are subject only to price-validation, which keeps
  a real gap. ATLANTAA `INE285H01022` (5:1 @2010-11-08, ISIN-matched, pre-coverage) verified in substrate: adj_issue
  30.0, cur_ret +36.3%, class `winner` — the D1-F1 regression guard. TARIL `INE763I01026` has three ISIN-matched legs
  (all own-ISIN) — never window-gated. The validation does not drop an ISIN-matched real split that has a gap; for a
  pre-coverage ISIN-matched split whose ex-date sits before `first_trade`, the gap is absent due to missing data
  (coverage hole) → defer to override / flag, NOT phantom-drop (the same safety as ROLEXRINGS). The interaction with
  the window gate (symbol-added-only) + override + ISIN-matched-always-apply is internally consistent.

### 5. Carrier column + envelope-blindness — **CONFIRMED**
- `corp_action_no_price_gap` is added to `07.columns()` (plan Task 4 modify bullet, line 230; spec 102-106). The F-7
  plumbing is real and verified on disk: `09_assemble.py:41-45` builds `ret_keys` from the returns-summary keys
  (excluding identity cols) → `ret_cols` (44) → `out_cols` (45) → `ipo_analysis.csv`. Any new `07` column flows
  automatically; no extra `09` wiring needed. Task 6 reads `corp_action_no_price_gap` to route phantom-dropped rows to
  the unresolved set (line 296). The flag is not inert.
- The uniform-over-count class the envelope tripwire is blind to (`trough ≤ endpoint ≤ peak` is preserved when
  adj_issue and the extremes are divided by the SAME constant — verified numerically true for GNA/CANTABIL in the R8
  doc) is now caught by the price-validation instead of the tripwire. The plan asserts this explicitly (Task 11(g)
  line 360; Task 4 Step 6b line 247; spec 230-234). Correct division of labor: tripwire = consistency (permanent
  safety net for future bad factors); price-validation = magnitude (catches the self-consistent over-count).

### 6. No internal contradiction introduced by R9 — **CONFIRMED**
R9 layers cleanly on R3 (window gate) / R6 (ISIN-matched-always-apply) / Task 3 (override):
- Step 6b runs AFTER the Step 6 window gate (line 247: "immediately AFTER the windowed `actions` list is built ...
  BEFORE it is passed to `load_prices`/`compute`"). Order: build union → gate symbol-added subset → price-validate each
  admitted action → pass validated list to both consumers. No ordering conflict with D1-F2 (same call-site locus).
- ISIN-matched-always-apply (R6/D1-F1) is preserved: an ISIN-matched action is admitted by the gate, then
  price-validated — a real gap applies it, a coverage-hole defers to override/flag (never phantom-dropped). The plan's
  Task 6 note (line 296) correctly states a collapsed double-count (CANTABIL/GNA) is *confidently resolved* (carries
  final values) while only a phantom-DROP routes to flag+null — no double-jeopardy.
- The override (Task 3) is consulted by the price-validation for the coverage-hole/ambiguous branch (Task 4 Step 4
  line 245: "consult `override_for` ... passing in the measured gap so the contradiction guard can fire"). Single
  shared helper (Step 4 ↔ Step 6b, line 245/247) prevents drift. No contradiction.

---

## Findings (numbered — only where something is off)

### NIT-1 (LOW, documentation precision — not a blocker)
**`docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md:95-98` and plan line 247** describe the coverage-hole
branch as "no gap because price data is MISSING around the ex-date (no closes to compare) → `detect_gap` returns None
→ defer to override." But the REAL ROLEXRINGS series (verified) does NOT return None: its index-adjacent window
straddles the 15-month hole and yields a NON-None gap of **~19.96×** (`2024-07-05 2516.95 → 2025-10-17 126.10`). The
real factor is 10× (the extra ~2× is genuine price decline across the missing 15 months). So ROLEXRINGS is actually a
**"gap present but ~20× ≠ claimed 10×" price-ambiguous case**, NOT a literal "no closes" case.

This does **not** change the correct outcome, because:
- Task 4 Step 4 (line 245) and Task 9 Step 1(c) (line 336) already treat ROLEXRINGS as override-resolved with the
  measured gap passed to the contradiction guard ("its observed gap is unreliable BY DEFINITION ... do NOT use the
  ratio"). Task 1 (line 102) explicitly references "the real ~20× gap."
- The override contradiction guard (Task 3 Step 6) honors the override BECAUSE the reason cites `price-vs-web conflict`
  with evidence (`gap≈20× but web confirms ONE 10:1`), which is exactly case (b) of the guard.

**Why fold it anyway:** the four-way decision tree as literally written keys the coverage-hole branch on
`detect_gap → None`. An implementer following the literal tree could route ROLEXRINGS into the "gap present, doesn't
match claimed ratio" sub-case — for which the tree does NOT spell out a branch (it has "gap-supports → apply",
"same-ratio legs → collapse", "price-present-flat → phantom-drop", "data-missing-None → override"). A ~20×-gap-vs-10×-
claim is none of those four literally. **Fix:** add a fifth explicit branch (or merge into the override branch):
"gap PRESENT but does NOT match the claimed ratio within tolerance, AND not a clean flat-phantom → price-AMBIGUOUS →
defer to `override_for` (apply if confident override, else flag-unresolved)." This makes the ROLEXRINGS path
deterministic from the tree alone and removes reliance on the implementer inferring it. The Task-4 Step-6b test (iv)
should assert ROLEXRINGS specifically (gap ~20×, claim 10×, override factor 10) resolves via override and is NOT
phantom-dropped — not just a synthetic None-gap fixture, since the real case never produces None.

---

## Bottom line
Remedy (a) is **correct** and reaches the substrate. The CANTABIL (25→5 → 7.14×) and GNA (4→2 → 2.70×) collapses are
arithmetically confirmed against the real price files; the phantom legs (gap 1.05 / 1.02) are unambiguously flat; the
ISIN-matched / window-gate / override invariants are intact; the carrier column and envelope-blindness handoff are
real; no new regression on legitimate splits or ISIN-matched events. The one nit (NIT-1) is a documentation-precision
gap in the decision tree's coverage-hole branch wording — the BEHAVIOR is already correct (override consulted with the
measured gap), but folding the explicit "gap-present-but-mismatched → override" branch + a real-ROLEXRINGS test would
make the tree self-contained. **The plan is NOW build-ready (GO).**
