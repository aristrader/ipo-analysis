# D-1 Plan — FINAL independent convergence verification (2026-06-17)

**Reviewer role:** independent, READ-ONLY final verification of the *thrice-revised* D-1 plan + spec,
after the join-strategy verdict (R3 / option-d) and the re-review fixes (R1/R2 + nits) were folded in.
No code/data edits, no pipeline execution. This is the **convergence check**: did the core fix
(the date-windowed symbol∪substrate-ISIN join) propagate cleanly into EVERY task, or is anything
still broken? Every claim below was verified against the working-tree files.

**Documents verified:**
- Plan: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`
- Spec: `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`
- Findings folded: `d1_join_strategy_2026-06-17.md` (R3), `d1_plan_rereview_2026-06-17.md` (R1/R2),
  `d1_plan_review_2026-06-17.md` (F1–F6)
- Ground truth: `pipeline/07_returns_summary.py`, `pipeline/03k_*`, `03l_*`, `09_assemble.py`,
  `data/reference/corp_actions_merged.csv`, `data/master/ipo_analysis.csv`, `data/prices/`,
  `data/master/review/corp_action_external_evidence.csv`, `tests/pipeline/test_compute_synthetic.py`,
  `tests/data/test_substrate_integrity.py`.

---

## VERDICT: **APPROVE-WITH-NITS** — the plan is execution-ready.

The core fix (R3 / option-d: the date-windowed **symbol∪substrate-ISIN** join) has propagated cleanly
to all four loci that needed it (detector, reconcile, `07` apply-path, Task-8 patch/anti-join). The R1
test-keying regression is fully reversed (ROLEXRINGS keys on `INE645S01024`, exercising the real ×1000
path). F1–F6 are intact and not regressed. KAUSHALYA uses the correct substrate ISIN and I confirmed
the ~100× gap on disk. **No real blocker remains.** Three genuine-but-minor nits (N1–N3) are listed —
all are fix-during-build, none gate execution.

Each of the 7 mandated checks is confirmed below with file:line evidence.

---

## CHECK-BY-CHECK

### Check 1 — Join key consistent + correct EVERYWHERE → **CONFIRMED**

The date-windowed symbol∪substrate-ISIN join is applied at all four loci, and there is **no residual
ISIN-only keying that would break the symbol-reached stocks**:

- **(a) Detector (Task 1):** keys ROLEXRINGS on substrate `INE645S01024` + symbol `ROLEXRINGS`
  (plan line 80), obtains the factor via the `actions_for` union `by_isin[isin] ∪ by_symbol[symbol]`
  with the in-window filter applied inside `_in_window_actions` (plan lines 98-102). Correct.
- **(b) Reconcile (Task 4 Step 4):** "group candidate events per SUBSTRATE ISIN over the symbol∪ISIN
  union and FILTER to the trading-date window FIRST" (plan line 184). The old "group per corp-action
  ISIN" wording is gone. Correct.
- **(c) `07` apply-path (Task 4 Step 6):** the window gate is wired into `actions_for` (07:114-127) /
  `load_prices` (07:206-235) so returns/MFE/MAE/listing-metrics are all window-safe (plan line 185).
  Correct in intent (see N1 for the ordering subtlety).
- **(d) Task-8 patch/anti-join:** the corp-action set = substrate ISINs whose **symbol OR ISIN** appears
  in `corp_actions_merged` **AND have ≥1 in-window event** (plan lines 261-262). The full anti-join
  treats the 44 out-of-window-only rows as outside the patched set. Correct.

Ground-truth confirmation that ISIN-only keying WOULD break things: ROLEXRINGS's NSE corp row is keyed
`INE645S01016` (no price file — confirmed `data/prices/INE645S01016.csv` does not exist) while the
price/substrate ISIN is `INE645S01024` (file exists, 39 KB). The two yfinance over-count rows have
empty ISIN. So the ×1000 product is reachable ONLY via `by_symbol["ROLEXRINGS"]`. The plan keys on the
substrate ISIN + symbol — correct everywhere.

### Check 2 — R1 test soundness (ROLEXRINGS does not pass spuriously) → **CONFIRMED**

Plan Task 1 parametrize keys on `("INE645S01024", "ROLEXRINGS")` (line 80) — the price file that EXISTS.
Trace of the assertion (plan lines 86-90): `eff = applied_effective(INE645S01024, ROLEXRINGS)` resolves
the three events via the symbol union (all in-window) → product **1000**; `max_gap = observed_max_gap(...)`
reads `data/prices/INE645S01024.csv` → real gap ≈ 20. Assertion
`abs(ln(1000)) - abs(ln(20)) = 6.91 - 3.00 = 3.91 > ln(5) = 1.61` → **flags for the right reason**.

This is the precise fix for the prior `...016` regression: with `INE645S01016` the helper would read
`applied=10` and `gap=None→1.0` (no price file), passing `|ln10|-|ln1|=2.30 > 1.61` **spuriously** — green
even if the over-count did not exist. The current `...024` keying **fails iff the real over-count exists**
and exercises the production path. Sound.

### Check 3 — New flag `corp_action_out_of_window` wired correctly → **CONFIRMED**

- **Task 4 Step 6** emits `corp_action_out_of_window` on the dropped action and routes it to Task 6's
  unresolved set (plan line 185).
- **Task 6 Step 4** builds the unresolved set dynamically and explicitly includes "any ISIN with a
  `corp_action_out_of_window`-dropped action (the R3 date-window gate, Task 4 Step 6)" (plan line 233);
  every such ISIN gets flag + low tier + null outcomes + null `outcome_class`.
- **Task 11 Step 1(f)** checklist verifies the flag "drops the 44 wrong-era/reused-symbol attachments
  into the unresolved set" (plan line 297).
- Out-of-window matches are **dropped from adjustment and flagged, never applied** — consistent with the
  Confidence Invariant (plan lines 27-35) and spec §3 (lines 45-52). Correct.

### Check 4 — F1–F6 still intact (not regressed by this revision) → **CONFIRMED**

- **F1** (direction-normalized detector): `applied_effective` (= 1/rf for reverse, = factor for forward)
  vs gap in log-magnitude (plan lines 59, 101). PATANJALI removed as a guardrail (only anti-example
  mentions remain — spec lines 136-137, plan line 325). KAUSHALYA is the reverse-split must-pass; Task 9
  Step 1 is genuinely three-way (forward-clean / reverse-clean / coverage-hole — plan lines 270-274). Intact.
- **F2** (envelope tripwire): Task 5b is a real separate task implementing flag-only
  `trough ≤ endpoint ≤ peak`, permanent, never clamps, feeds the unresolved set (plan lines 205-221).
  Maps the owner-locked T-4 decision (c) part 2. Intact.
- **F3** (override contradiction guard): Task 3 Step 6 — override honored only if gap
  absent/ambiguous/coverage-hole OR `reason` cites a price-vs-web conflict with `evidence_url`; a clean
  contradicting gap with no such reason hard-fails (plan line 163). Intact. *(Confirmed against ground
  truth: ROLEXRINGS's evidence row is exactly a price-vs-web conflict — gap ~20× but web confirms one
  10× split, verdict `resolve-apply-once` — so it is correctly honored under branch (b), not a coverage
  hole. The plan's example reason text "price-vs-web conflict: gap≈20× but NCLT 10×" covers this.)*
- **F4** (NPST handling): kept OUT of the Task-1 magnitude parametrize; caught by the count-conflict
  signal instead (plan line 95). Confirmed on disk: NPST = NSE bonus 3.0 (ex 2024-02-02) + yfinance
  split 3.0 (ex 2024-01-22), both reach substrate `INE0FFK01017` via symbol, product = 9; both
  in-window (so the date gate does NOT drop them — they collapse via the reconcile dedup to applied 3,
  exactly as Task 9 Step 1a states). Intact.
- **F5** (Task 7 → `mae_1y`): Task 7 targets `_mfe_mae_block` (07:306-360), forces MAE = −1.0, leaves
  terminal untouched (plan lines 245-246). Verified test line numbers: `return_from_issue_1y == −1.0`
  is line 106 (already passes), `mae_1y == approx(−1.0)` is line 110 (the failing one). Plan cites both
  correctly. Intact.
- **F6** (full anti-join + manual_overrides.csv): Task 8 requires a full per-row anti-join, every
  non-corp-action ISIN byte-identical to the snapshot (plan lines 261-263); Task 8 Step 1 enumerates
  `data/reference/manual_overrides.csv` (applied at `09:98-112` — verified that exact range). Intact.

### Check 5 — State-log captures BOTH the drill-down and the solve-upward → **CONFIRMED (with N3 nit)**

The plan's "Status / review rounds" section (lines 5-8) is a living chronological log capturing the
investigation drill-down to the core cause: R1 review (F1–F6 surface fixes) → R2 re-review (the
symbol-join blocker surfaced) → R3 join-strategy (option-d, the date-windowed key = the CORE cause fix).
The task-order solve-upward (core→surface) is encoded in the task DAG: Task 1 detector → Task 4
reconcile + `07` gate (core) → Task 8 patch → Task 9 verify (surface). Both directions are present.
**N3 (nit):** the log is framed purely as "review rounds," not explicitly as the two-axis
"thought: surface→core / action: core→surface" the kickoff prompt asks for — readable but could state
the two axes by name. Non-blocking.

### Check 6 — KAUSHALYA uses substrate ISIN `INE234I01028` → **CONFIRMED**

Spec §5 (lines 125-134) names KAUSHALYA's substrate ISIN as `INE234I01028` ("Kaushalya Infrastructure
Development Corp.", listed 2007) and explicitly warns "Do NOT confuse `INE234I01028` with `INE0Q2V01012`"
— the latter being the DIFFERENT KLL Logistics SME (listed 2024). Verified on disk:
- `INE234I01028` → substrate "Kaushalya Infrastructure Development Corp.Ltd." (MB)
- `INE0Q2V01012` → substrate "Kaushalya Logistics Ltd." (SME) — a different company, own price file.
- The single corp action `KAUSHALYA split 0.01 ex 2024-01-12` has empty ISIN → reaches `INE234I01028`
  via symbol only.
- **I confirmed the ~100× gap:** `INE234I01028` close goes 9.85 (2024-01-11) → 988.3 (2024-02-06), i.e.
  a genuine ~100× jump consistent with `price/0.01 = price×100`. The ex-date 2024-01-12 is in-window
  (trades 2007-12-14 → 2026-06-05), so it is correctly admitted and passes the reverse-clean
  must-pass guardrail. Spec/plan numbers (applied_effective=100, gap≈100, ratio≈1) are accurate.

### Check 7 — New contradictions / gaps / duplicate steps / broken line-refs → **none material; 2 nits**

Line-refs re-verified on the working tree (all correct): `07` `load_corp_actions` 91-111, `actions_for`
114-127, `load_prices` 206-235, `adj_factor_after` 239-246, `_mfe_mae_block` 306-360; `03k` Yahoo dedup
75-91; `03l` `pd.concat` 58 + ISIN-blank loop 43-53; `09` `and not has_action` skip line 89, `has_action`
set 86-88, manual_overrides 98-112; synthetic test lines 106/110; substrate delisting test line 103 with
`>= 30` at line 109. Task 3's duplicate "Step 6" (the prior R3 nit) is resolved — contradiction guard =
Step 6, commit = Step 7 (plan lines 163-164). Scratch files for Task-12 cleanup all exist
(`get_bse.py`, `get_nse.py`, `nse.py`, `parse_splits.py`, `search.py`, `search_ddg.py`, `splits.html`,
`bonus.html`, `test_url.py`). TODO-D1a…f present in `improvement_backlog.md` (lines 27-43). Evidence CSV
and override file exist. No new contradiction or duplicate step introduced.

---

## NITS (fix during build; none gate execution)

### N1 (nit) — `[first_trade, last_trade]` ordering vs the `actions_for`/`load_prices` boundary
**Where:** plan Task 4 Step 6 (line 185); spec §3 (lines 50-52); `07:206-235`, `07:599-600`, `07:631`.
The plan says "pass the price series' `[first_trade, last_trade]` … into `actions_for` … and filter the
returned list **before it reaches `load_prices`**." But the trading window is only knowable AFTER the CSV
is read, and the CSV read happens **inside** `load_prices` (07:209-222) — i.e. the window does not exist
at the point `actions_for` is called (07:599 and 07:631). This is a real ordering tension, not a logic
error: the implementer must either (i) read the window cheaply before `actions_for` (a second pass over
the CSV, or a small min/max-date scan), or (ii) move the window filter INTO `load_prices` (which already
has the sorted series at line 222) and apply it there before the factor product at 226-234. Either is
fine; the plan's phrasing just implies the data is available pre-`load_prices` when it is not. Flag it so
the agent picks a locus deliberately. (The plan does hedge — "available in `load_prices`/`compute`" — so
this is a phrasing nit, not a missing requirement.)

### N2 (nit) — TWO `actions_for`/`load_prices` call sites in `07`, the plan cites only "~630"
**Where:** plan Task 4 Step 6 ("called at the per-ISIN compute (line ~630)", line 173/185).
There are **two** call sites: 07:599-600 (the targeted/debug `targets` path) and 07:630-631 (the main
build loop). Both call `actions_for(...)` then `load_prices(...)`. If the window gate is wired only at
the main loop, the debug/targeted path stays ungated — harmless for the substrate (Task 8 reuses the
real `compute()` path) but a latent inconsistency. If the gate lives inside `load_prices`/`actions_for`
itself (the cleaner locus, and the one the plan/spec prefer — spec lines 274-278), both sites are covered
automatically. Recommend implementing the gate inside the consumed helper so both call sites inherit it;
just note both exist so the agent doesn't patch only one.

### N3 (nit) — State-log framing (see Check 5)
The review-rounds log captures both the drill-down and the solve-upward but does not name the two axes
("thought: surface→core / action: core→surface") explicitly. Cosmetic.

---

## BOTTOM LINE

The convergence is clean. The core cause-fix (date-windowed symbol∪substrate-ISIN join, R3/option-d)
propagated to the detector, the reconcile, `07`'s live apply-path, and the Task-8 patch/anti-join with
no residual ISIN-only keying. The R1 spurious-pass regression is fully reversed and the red baseline now
exercises the real ×1000 path. F1–F6 are intact. KAUSHALYA, ROLEXRINGS, and NPST all check out against
on-disk ground truth. **The plan is execution-ready.** Fix N1/N2 (the window-filter locus, applied once
inside the consumed helper so both `07` call sites inherit it) during the build, and optionally tidy the
state-log framing (N3). No further plan revision is required before implementation.
