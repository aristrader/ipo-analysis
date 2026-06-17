# D-1 Corp-Action Fix — independent RE-REVIEW of the REVISED plan + spec (2026-06-17)

**Reviewer role:** independent, adversarial re-review of the *revised* spec + plan, after a revision pass
claimed to address the prior review (`docs/research/d1_plan_review_2026-06-17.md`). No code edits, no execution.
Every claim verified against the actual files on the working tree.

**Documents re-reviewed:**
- Revised plan: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`
- Revised spec: `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`
- Prior review: `docs/research/d1_plan_review_2026-06-17.md`
- Ground truth: `data/reference/corp_actions_merged.csv`, `data/master/ipo_analysis.csv`, `data/prices/`,
  `data/master/review/corp_action_external_evidence.csv`, `pipeline/03k_*`, `03l_*`, `07_returns_summary.py`,
  `09_assemble.py`, `tests/pipeline/test_compute_synthetic.py`, `tests/data/test_substrate_integrity.py`,
  `docs/research/alignment_audit_2026-06-16.md`.

---

## VERDICT: **CHANGES-NEEDED**

The revision correctly applied F1–F6 and the nits at the *prose/structural* level — direction-normalization,
the envelope tripwire (F2/Task 5b), the override contradiction guard (F3), the NPST count-conflict carve-out (F4),
Task 7 re-scoped to `mae_1y` (F5), full anti-join (F6), and all the line-ref corrections are now accurate.

**But the revision introduced a NEW BLOCKER (R1) while fixing F1, and it reveals a deeper, systemic DESIGN GAP
(R2) that neither the original nor the revised plan addresses.** The single edit that changed ROLEXRINGS's test
ISIN from `INE645S01024` to `INE645S01016` is **wrong on both axes** (price-file side AND factor side), and the
reason it is wrong applies to **282 symbols / 434 corp-action rows** across the dataset, not just ROLEXRINGS. The
audit helper and the Task-4 rebuild are specified to key on the corp-action ISIN, but **every corporate action in
the merged file reaches its prices/return via the SYMBOL join, never the substrate ISIN** — exactly the project's
own "corp actions match by SYMBOL" rule, which the plan never states and the helper signatures contradict.

---

## PRIORITY FINDING — the dual-ISIN / SYMBOL-join issue (the revision got this WRONG)

### R1 (BLOCKER) — Changing the ROLEXRINGS test ISIN to `INE645S01016` is wrong on BOTH axes

**Where:** plan Task 1 Step 2 parametrize (line 82: `("INE645S01016", "ROLEXRINGS")`); Task 1 Step 4 helper
signatures (`applied_cumulative_factor(isin)`, `observed_max_gap(isin)`); Task 3 Step 2 override test
(line 154: `override_for("INE645S01016")`).

**Ground truth (verified):**
- `corp_actions_merged.csv` keys ROLEXRINGS's split under **`INE645S01016`** (the NSE source row, factor 10,
  ex 2025-10-17). The two Yahoo over-count rows (ex 2025-10-03, 2025-09-19) have **empty ISIN** — they live
  under the SYMBOL only.
- The price file that EXISTS is **`data/prices/INE645S01024.csv`**. There is **no `INE645S01016.csv`**.
- The substrate (`ipo_analysis.csv`) keys ROLEXRINGS as **`INE645S01024`** (Rs10→Re1 face-value split → new ISIN).
- The Wave-1 evidence CSV keys ROLEXRINGS as **`INE645S01024`** and summarizes the bug as
  "applied factor 1000.0 (10^3)".

**(a) The price read breaks.** `observed_gap("INE645S01016", ex)` → `data/prices/INE645S01016.csv` does not
exist → returns `None` → `max_gap` defaults to `1.0`. The detector never measures the real ~20x gap.

**(b) The factor read is also wrong, and worse — it silently passes for the wrong reason.** Per the plan's own
helper spec, `applied_cumulative_factor(isin)` is keyed by ISIN:
- `applied_cumulative_factor("INE645S01016")` = **10** (only the single NSE event sits under `...016`'s ISIN).
- `applied_cumulative_factor("INE645S01024")` = **1** (nothing sits under the substrate ISIN at all).
- The actual 3x over-count (product = **1000**) only materializes through
  `actions_for(isin="INE645S01024", nse_symbol="ROLEXRINGS", ...)` — i.e. the **SYMBOL** union in `07:114-127`,
  which pulls all three events from `by_symbol["ROLEXRINGS"]`.

So the revised test (`eff = applied_effective("INE645S01016") = 10`, `max_gap = 1.0`) computes
`|ln 10| - |ln 1| = 2.30 > ln 5 = 1.61` → the assertion **passes its red baseline**, but for an entirely
spurious reason (no price file → gap = 1), NOT because it detected the triple-count. The test is green on a lie:
it would still pass if the over-count bug did not exist, and it does not exercise the production code path that
produces the +15,272% number. **This defeats the entire purpose of the TDD red baseline.**

**Concrete fix:**
- Parametrize the detector on the **substrate ISIN `INE645S01024`** AND the symbol `ROLEXRINGS`, and make the
  helpers key on the SAME (isin, symbol) union that `07.actions_for` uses (`by_isin[isin] ∪ by_symbol[symbol]`,
  dedup by `(ex_date, ratio_factor)`). Then `applied_effective` = 1000, `observed_gap("INE645S01024", ...)` ≈ 20,
  ratio = 50 → flagged for the RIGHT reason.
- Likewise change the override seed + `override_for(...)` test to `INE645S01024` (the key the evidence CSV and
  substrate actually use), or have the override loader resolve by symbol.

### R2 (BLOCKER) — Systemic: the helper + Task-4 rebuild must join by SYMBOL/substrate-ISIN, not corp-action ISIN

**Where:** plan Task 1 Step 4 (helper signatures all take a bare `isin`); Task 4 Step 4 ("group candidate events
per ISIN"); Task 8 Step 3 (recompute "the corp-action stocks"); spec §3 (never mentions the ISIN-change / symbol join).

**Why it is systemic — blast radius (quantified from ground truth):**
- **282 symbols** have a corp-action ISIN that differs from the substrate ISIN.
- **434 corp-action rows** have a non-empty ISIN that does not match the substrate ISIN for that symbol.
- Of those 434: **274** are real alphanumeric ISIN changes (ROLEXRINGS-style face-value splits, e.g. 20MICRONS
  `INE144J01019→…027`, ADANIPOWER `INE814H01011→…029`); **159** are numeric BSE-code "ISINs".
- **ZERO** of the corp-action-row ISINs have their own price file. **Every single one** reaches prices/returns
  only via `actions_for`'s SYMBOL union onto the substrate ISIN's price file.

This is the project's own non-negotiable rule (CLAUDE.md: *"corporate actions match by SYMBOL — a face-value
split changes the ISIN"*), and `07` already implements it (`load_corp_actions` builds `by_isin` AND `by_symbol`;
`actions_for` unions them). **The plan's audit helper and Task-4 reconcile contradict this** by keying on ISIN
alone. As written:
- An ISIN-keyed `applied_cumulative_factor` returns the wrong (partial or empty) factor for any of the 282
  dual-ISIN stocks — the over-adjustment detector is blind to the very class of bug it targets.
- "Group candidate events per ISIN" (Task 4 Step 4) would split a single symbol's events across the empty-ISIN
  Yahoo rows and the corp-action-ISIN NSE rows, never reconciling them — re-creating the exact leak.

**KAUSHALYA (the spec's "must-pass" guardrail) is itself an instance of this, and the spec's framing is sloppy:**
- The substrate keys symbol KAUSHALYA as `INE234I01028` ("Kaushalya Infrastructure"). The 0.01 reverse split is
  in `corp_actions_merged` under **`by_symbol["KAUSHALYA"]` with an empty ISIN** — it is NOT under any ISIN.
- I verified the gap: `INE234I01028` DOES gap ~**100.3x** near 2024-01-12, so the spec's numbers
  (applied_effective=100, gap≈100) are correct — **but only via the SYMBOL join.** An ISIN-keyed
  `applied_cumulative_factor("INE234I01028")` returns **1** (empty), so the must-pass guardrail would falsely
  read "no event applied," not the intended `≈1`. (Separately, there is a `data/prices/INE0Q2V01012.csv` which is
  a *different* company, "Kaushalya Logistics / KLL" — do not confuse the two; the spec author should name the
  ISIN to avoid this.)

**Concrete fix (must be in the plan text before build):**
1. State explicitly, in the spec principle and in Task 1/4/8, that corp actions are joined to prices/substrate
   **by the `actions_for` union (substrate ISIN ∪ NSE symbol)**, mirroring `07:91-127` — never by the
   corp-action-file ISIN alone. The over-adjustment detector, the Task-4 reconcile grouping, and the targeted-patch
   stock set must all key on **(substrate ISIN, symbol)**.
2. The "corp-action stock set" used by Task 8's anti-join and Task 6's unresolved set must be defined as the set of
   **substrate ISINs** whose symbol OR ISIN appears in the merged corp-action file (matching the `has_action` logic
   already in `09:86-89`, which correctly uses both `action_isins` and `action_symbols`).
3. Re-key R1's tests/overrides onto the substrate ISIN/symbol.

Until R1/R2 are fixed, the red baseline, the guardrails, and the Task-4 grouping are all unsound for the 282-symbol
dual-ISIN population — which includes the headline offender (ROLEXRINGS) and the headline guardrail (KAUSHALYA).

---

## Re-verification of the prior fixes F1–F6

### F1 — direction-normalization + PATANJALI removal + three-way Task 9  →  **APPLIED (correct), but undermined by R1/R2**
- `applied_effective` (= `1/ratio_factor` for reverse, = factor for forward) is defined and used; the comparison is
  log-magnitude. KAUSHALYA reverse-split-must-pass and ROLEXRINGS-must-flag math is internally correct **given the
  right factor** — but the right factor is only obtained via the symbol join (R2), which the helper does not do.
- PATANJALI is removed as a guardrail; the only remaining mentions (spec line 109, plan line 320) are explicit
  *anti-examples* ("PATANJALI is NOT a guardrail example") — that satisfies the F1 intent. ✅
- Task 9 Step 1 is genuinely three-way: (a) forward-clean NPST, (b) reverse-clean KAUSHALYA, (c) coverage-hole
  ROLEXRINGS (asserts sane `current_return_from_issue`, not the ratio). ✅
- **Residual:** F1's reverse-clean case (KAUSHALYA) will fail under the ISIN-keyed helper (R2). The math is right;
  the join is wrong.

### F2 — permanent loud envelope tripwire  →  **APPLIED (genuine)**
- Task 5b is a real, separate task implementing `check_envelope(row_or_block) -> [flags]` asserting
  `trough ≤ endpoint ≤ peak` per horizon for BOTH entries, flag-only (never clamp), wired as a permanent build step,
  feeding the unresolved set. It is explicitly distinguished from Task 5's continuity guard (single-day jumps).
- Cross-checked against the owner-locked T-4 decision (c) part 2 (`alignment_audit_2026-06-16.md:320-326`,
  "Replace the silent clamp with a loud TRIPWIRE … FLAG/RAISE … instead of silently snapping"). Now mapped. ✅

### F3 — override contradiction guard  →  **APPLIED (well-specified)**
- Task 3 Step 6 adds a failing-test-then-implement loader assertion: override honored only if the gap is
  absent/ambiguous/coverage-hole OR the `reason` cites a price-vs-web conflict with `evidence_url`; a clean gap that
  contradicts an override with no such reason hard-fails. Three test cases enumerated (ROLEXRINGS honored; clean
  contradiction raises; cited-conflict honored). Guard takes the measured gap, wired where Task 4 calls the loader. ✅
- **Nit:** Task 3 has a **duplicate "Step 6" label** — the contradiction-guard step and the commit step are both
  numbered Step 6. Renumber (contradiction guard → Step 6, commit → Step 7).
- **Note (interacts with R1):** the override test is keyed `INE645S01016`; fix per R1.

### F4 — NPST kept out of the magnitude parametrize  →  **APPLIED (correct)**
- Task 1 parametrize lists ROLEXRINGS only; an explicit note explains NPST (applied 9 → eff≈9 vs gap≈2.86 →
  9/2.86≈3.15 < 5x) is below the magnitude threshold and is caught by the **count-conflict** signal instead, with
  its resolution asserted in Task 9 Step 1 (forward-clean, after collapse to 3). Verified the math: NPST symbol-join
  product = 9.0 (3×3). The prose/test no longer disagree. ✅

### F5 — Task 7 re-scoped to the MFE/MAE block (`mae_1y`, line 110)  →  **APPLIED (correct)**
- Verified `tests/pipeline/test_compute_synthetic.py`: line 106 `return_from_issue_1y == -1.0` (already passes),
  line 110 `mae_1y == pytest.approx(-1.0)` (the failing one). Task 7 now targets `_mfe_mae_block` (`07:306-360`),
  forces MAE = −1.0 for compulsory-delisting/horizons spanning the delist date, and explicitly leaves the terminal
  logic (line 106) untouched. ✅

### F6 — full anti-join byte-identity gate + `manual_overrides.csv` enumerated  →  **APPLIED (correct)**
- Task 8 Step 2/4 and Task 11 Step 1(d) now require a **full anti-join**: every ISIN not in the corp-action set is
  byte-identical to the snapshot (not one control row); `git diff --stat` demoted to a sanity glance.
- Task 8 Step 1 explicitly enumerates `data/reference/manual_overrides.csv` (applied at `09:98-112`). ✅
- **Note (interacts with R2):** "the corp-action set" must be defined by symbol-OR-ISIN (R2 fix #2), else the
  anti-join would wrongly treat the 282 dual-ISIN substrate rows as "non-corp-action" and could flag legitimate
  patch changes as violations (or, conversely, the patch might key the wrong ISIN and miss them).

### Line refs (Check 7)  →  **ALL CORRECT NOW**
Verified against the files:
- `03k` Yahoo dedup (the 7-day same-ratio collapse in `load_yahoo_data`) = **lines 75-91** ✅
- `07` factor application = `load_prices` **223-235** + `adj_factor_after` **239-246** ✅
- `03l` union = `pd.concat` at **line 58** (44-53 row-shaping loop) ✅
- `09` skip = `and not has_action` at **line 89** (set built 86-88) ✅
- `07` `_mfe_mae_block` = **306-360** ✅; `09` manual_overrides = **98-112** ✅
- substrate delisting test = `tests/data/test_substrate_integrity.py:103` with `>= 30` at line 109 ✅;
  synthetic test lines 106/110 ✅

---

## NEW issues the revision introduced (besides R1/R2)

### R3 (NIT) — duplicate "Step 6" in Task 3
Two consecutive steps both labeled **Step 6** (the F3 contradiction-guard step and the commit step). Renumber.

### R4 (NIT) — the `observed_gap` docstring still describes a calendar-window risk vestige
The prior review's N4 (calendar-vs-trading-day window) is addressed: the revised `observed_gap` and `detect_gap`
both specify a trading-day-indexed window and a note that they must agree. Good. Minor: the two helpers are
specified in two places (Task 1 inline + Task 2 module) with the same logic — consider having Task 1 import
`detect_gap` from Task 2 rather than re-implementing `observed_gap`, to guarantee they cannot drift. (Task 2 is
authored after Task 1 in the plan order, so a small forward-reference note suffices.)

### R5 (NIT) — Task 8 `substrate_meta.json` row-count
Task 8 Step 3 says "Update `substrate_meta.json` counts if any." The patch nulls outcomes but keeps every row, so
the row count should not change; the meta's other derived counts (e.g. `outcome_class` distribution, flagged-row
counts) WILL change. State which fields are expected to move so the verify-hook invariants
(`tests/data/` GOLDEN headline numbers) are updated deliberately, not reactively. (This dovetails with the T-3
follow-up, but the row-keyed counts in meta are in-scope here.)

---

## Confirmed sound (carried over / re-verified)
- The bug is real and reproduced: ROLEXRINGS substrate `current_return_from_issue = 152.72` (+15,272%),
  `outcome_class = multibagger`; NPST `= 161.27` (+16,127%), `multibagger`. Symbol-join applied product = 1000
  (ROLEXRINGS), 9 (NPST). ✅
- Phase-0 evidence triage is genuine: `corp_action_external_evidence.csv` exists, keyed by substrate ISIN, with
  the ROLEXRINGS verdict `resolve-apply-once` and the cited coverage-hole reasoning. ✅
- The 6 Wave-1 STAYS-FLAGGED (CMMIPL, INDUSFILA, BANSAL, COOLCAPS, SILVERTUC, VAISHALI) and the dynamic
  unresolved-set construction are intact and correct. ✅
- `09`'s existing `has_action` already matches by both ISIN and symbol (`09:86-89`) — the right template for R2's
  corp-action-set definition. ✅
- Confidence invariant, flag+null vs genuine-wipeout-−100% separation, targeted-patch-not-full-rerun, DAG-orphan
  note (N3), no-op-commit removal (N1), "skipped not disabled" (N2) — all preserved/correct. ✅

---

## Recommended pre-implementation edits (ordered)
1. **R1** — re-key the ROLEXRINGS detector test + override test from `INE645S01016` to the **substrate ISIN
   `INE645S01024`** (and symbol), so the red baseline exercises the real +15,272% path. *(blocker)*
2. **R2** — make the audit helper, the Task-4 reconcile grouping, the override loader, the unresolved set, and the
   Task-8 patch/anti-join all key on the **`actions_for` symbol∪ISIN union onto the substrate ISIN** (per the
   project's "corp actions match by SYMBOL" rule), not the corp-action-file ISIN. Blast radius: 282 symbols / 434
   rows / 274 real ISIN changes — state this explicitly in the spec. *(blocker)*
3. **R3** — renumber the duplicate Task 3 Step 6.
4. **R4/R5** — share the gap helper between Task 1 and Task 2; spell out which `substrate_meta.json` fields the
   patch is expected to move.

F1–F6 and all line-ref corrections from the prior review are **correctly applied**; the revision's only defects are
the ISIN-keying regression (R1) and the systemic symbol-join gap it exposes (R2), plus three nits.
