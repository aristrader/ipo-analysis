# D-1 Corp-Action Fix — independent adversarial plan review (2026-06-17)

**Reviewer role:** independent, adversarial review of the spec + plan *before* code is written. No code
edits made. Verified every claim against the actual files on `main` (commit-state as checked out 2026-06-17).

**Documents reviewed:**
- Spec: `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`
- Plan: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`
- Code: `pipeline/03k_reconcile_corporate_actions.py`, `pipeline/03l_merge_corporate_actions.py`,
  `pipeline/07_returns_summary.py`, `pipeline/09_assemble.py`, `tests/pipeline/test_compute_synthetic.py`,
  `tests/data/test_substrate_integrity.py`, `tests/layer3/test_reach.py`, `verify.py`
- Evidence: `data/master/review/corp_action_external_evidence.csv`, `docs/research/alignment_audit_2026-06-16.md`,
  `docs/tracker/improvement_backlog.md`

---

## VERDICT: **CHANGES-NEEDED**

The strategy is sound and the spec's principle ("price disposes") is correct. The Phase-0 evidence triage is
done and the override set is real. **But there is one BLOCKER (F1) that would falsely flag the plan's own
"must-pass" guardrail examples (PATANJALI/KAUSHALYA), plus a missing spec-mandated deliverable (F2, the loud
envelope tripwire from the locked T-4 decision (c)).** Several MAJOR items and a handful of nits follow. None
are fatal to the approach; all are fixable in the plan text before implementation.

---

## The 6 mandated checks — confirm / refute

### Check 1 — File:line references on current `main`  →  **MOSTLY STALE / PARTIALLY WRONG (MAJOR)**

| Plan cite | What plan says is there | What is ACTUALLY there | Verdict |
|---|---|---|---|
| `07:114-127` | "`actions_for` helper + factor-application loop" | `actions_for` IS at **114-127** ✅. But the **factor-application loop is NOT here** — it is in `load_prices` at **223-235** and `adj_factor_after` at **239-246**. | Half-right; the loop pointer is wrong. |
| `03l:44-58` | "union/append" | 44-58 is the **Yahoo→NSE conversion loop (44-53) + `pd.concat` (58)**. The actual append/union is line **58**. Close enough but "44-58" mostly covers the row-shaping loop, not the union. | Roughly right. |
| `03k:145-195` | "dedup/window logic" | 145-195 is the **reconcile matching loop** (the ±10-day NSE match + 5% ratio tolerance). The **actual Yahoo dedup (the 7-day same-ratio collapse) is at lines 75-91 in `load_yahoo_data`** — NOT in 145-195. | **WRONG** for "dedup"; the dedup the plan wants to replace lives at 75-91. |
| `09:85-89` / `09:70-90` | "the disabled cross-source check" / "remove the skip at 85-89" | The check is NOT globally disabled. It runs at **82-94** and *skips corp-action stocks* via `and not has_action` at **line 89**. The `has_action` set is built at **86-88**. Lines **70-71** are the "INVARIANT CLAMP REMOVED" comment (unrelated to the cross-source skip). | Right idea, imprecise lines; "disabled" overstates it (it's a per-stock skip, not a global disable). |

**Fix:** The plan's brownfield rule ("READ the named region before editing") will catch these at build time, so
they are not fatal. But correct the cites now to avoid an agent editing the wrong block:
- Task 1 Step 1 / Task 4: point at `07` `load_prices` (223-235) + `adj_factor_after` (239-246) for the factor
  application; and `03k` `load_yahoo_data` **75-91** for the dedup that must be replaced (the 145-195 reconcile
  loop is the *matching* logic, also touched, but the dedup is the bug locus).
- Task 5: the `09` skip to remove is the `and not has_action` clause at **line 89** (set built 86-88), not "85-89".

### Check 2 — Over-adjustment detector = factor-vs-gap MISMATCH, not magnitude  →  **CONFIRMED for Task 1, BUT BROKEN for reverse splits in Task 9 (BLOCKER — see F1)**

- Task 1's red baseline criterion `applied / max_gap > 5.0` is correctly a *mismatch* signature, not raw magnitude.
  Verified numerically: ROLEXRINGS applied=1000, observed gap≈20 → `1000/20 = 50 > 5` → correctly flagged red.
  NPST applied=9, gap≈2.86 → `9/2.86 ≈ 3.1` (would NOT trip `>5`; see F4).
- **The guardrail examples are mis-modelled.** The spec/plan assert PATANJALI/KAUSHALYA are "real 100:1 NCLT
  consolidations that gapped ~×100" and Task 9 asserts they "still ≈1 … untouched." The merged data says
  otherwise (see F1). This is the single most important correctness defect — detailed below.

### Check 3 — CONFIDENCE INVARIANT airtight (no guessed value ever written)  →  **HOLDS in design, ONE leak to close (F3)**

- Tasks 4/6/7/8 route uncertainty to flag+null and reserve final values for price-validated or override-confirmed
  stocks. The dynamic unresolved-set construction (6 Wave-1 + Task-4 flag-channel + Task-9 T-2 residuals) is
  correct and is the right closure.
- **Leak (F3):** the override table (Task 3) is itself a *writing-a-final-value* path. ROLEXRINGS' override
  (factor 10) is justified, but its evidence row literally says the price gap (≈20×) does NOT match the override
  factor (10×) — "price disposes" is *overridden by web* here. That is defensible (coverage hole) but it means
  the override is a hand-asserted value, i.e. a "confident guess." The invariant text must explicitly carve out
  "override = confident resolution" (it does, in plan §CONFIDENCE INVARIANT) AND the override loader must hard-fail
  if an override exists for a stock whose price gap *cleanly contradicts* it without a `coverage_hole`/`price-vs-web`
  reason — else the table becomes the back-door the spec §6 warns against. No test enforces this today.

### Check 4 — Test soundness (genuine fail→pass; correct assertions; valid synthetic data; type consistency)  →  **PARTIALLY REFUTED (F1, F5, F6)**

- `detect_gap`/`Gap`/`override_for`/`applied_cumulative_factor` are *named* consistently across tasks (Task 1 uses
  `applied_cumulative_factor`, reused in Task 9; `Gap(ratio,direction,gap_date)` in Tasks 2/4; `override_for` in 3/4/6).
- **But the types are not semantically consistent for reverse splits (F1):** `applied_cumulative_factor` returns a
  *product of ratio_factors* (can be < 1, e.g. KAUSHALYA 0.01) while `observed_max_gap`/`Gap.ratio` is defined as
  `max(c0/c1, c1/c0)` (always ≥ 1). Comparing them via `applied/max_gap ≈ 1` (Task 9) is only valid for forward
  splits. See F1.
- **Task 7 Step 2 mis-states the failure (F5):** it claims `test_compulsory_delisting_forces_minus_100` "FAIL
  (gets +0.15)" on `return_from_issue_1y`. Verified: `return_from_issue_1y` is **already −1.0 and PASSES**; the
  assertion that fails is **line 110, `mae_1y == −1.0`** (obtained 0.15). The real T-4 fix is in the MFE/MAE block,
  not the horizon-terminal logic. Task 7 Step 3 conflates the two.
- **Task 9 Step 1 NPST math is plausible but check the threshold (F4):** "NPST applied 3 vs gap ~2.86 → ≈1" — but
  `applied_cumulative_factor(NPST)` per Task 1's own definition is **9** (product 3×3), not 3. So the *resolved*
  state must produce applied=3 (after collapse) for `3/2.86≈1` to hold. The assertion is only valid post-fix; the
  text should state "after the rebuild collapses the double-count, applied=3" to avoid confusion with the pre-fix 9.

### Check 5 — Targeted-patch safety (Task 8): inventory gate + byte-identical control  →  **ADEQUATE-WITH-GAPS (MAJOR, F7)**

- The inventory-of-manual-remediations gate (Task 8 Step 1) is the right idea and is correctly a hard gate.
- **Gaps:** (a) the "non-corp-action control row byte-identical" check tests *one* row; a single control row does
  not prove the patch left *all* ~2,000 non-corp-action rows untouched. Strengthen to: *every* row NOT in the
  corp-action ISIN/symbol set is byte-identical to the snapshot (a full anti-join diff), not just one sampled row.
  (b) `git diff --stat data/master/` only shows file-level churn; it won't tell you *which rows* changed. The
  byte-level per-row diff is the real safety net and should be the gating assertion, with `--stat` as a sanity glance.
- The manual-overrides path already in `09_assemble.py:98-112` (`data/reference/manual_overrides.csv`) is one known
  remediation channel the inventory MUST enumerate; the plan doesn't name it. Add it explicitly to Step 1's checklist.

### Check 6 — Sequence / gaps / contradictions  →  **ONE SPEC REQUIREMENT HAS NO TASK (BLOCKER, F2); rest consistent**

- **F2 (BLOCKER):** The locked T-4 decision (c) in `alignment_audit_2026-06-16.md:320-326` has **three** parts:
  (1) fix D-1, (2) **"Replace the silent clamp with a loud TRIPWIRE … FLAG/RAISE a violation instead of silently
  snapping it,"** (3) make delisting −100% explicit. The plan implements (1) and (3) (Tasks 4/7) and a *continuity*
  guard (Task 5, a different check — single-day jumps), but **there is no task that implements the permanent
  `trough ≤ endpoint ≤ peak` envelope tripwire in the pipeline.** Task 9 Step 2 only *runs the existing T-2 test*.
  The spec's Phase 2 ("any leftover unexplained single-day price jump → flag") is the continuity guard, NOT the
  envelope invariant. The envelope tripwire is a distinct, owner-locked requirement that is currently unmapped.
- Sequencing is otherwise coherent: Phase-0 triage done → evidence CSV exists → override table seeded → 07-feeding
  rebuild → targeted patch → verify → T-3 deferred. `verify.py` does NOT run/assert goldens (only `pytest --co -q`
  for a count), so "verify.py PASS while T-3 stays red" (Task 8 Step 4 / Task 9) is internally consistent — confirmed.

---

## BLOCKERS

### F1 (BLOCKER) — Reverse-split factor/gap sign inconsistency falsely flags the plan's own guardrail examples
**Where:** spec §5; plan Task 1 Step 4, Task 9 Step 1; the "PATANJALI/KAUSHALYA stay ≈1" claim throughout.
**What's wrong:** Ground truth from `data/reference/corp_actions_merged.csv`:
- **KAUSHALYA** (INE0Q2V01012): single event `ratio_factor = 0.01` (a 1:100 *reverse* consolidation). `07`
  applies `price / 0.01 = price × 100`. `applied_cumulative_factor` (product of ratio_factors, per Task 1 def) = **0.01**.
  `observed_max_gap = max(c0/c1, c1/c0)` ≈ **100**. So `applied/max_gap = 0.01/100 = 0.0001` — **nowhere near 1.**
  Task 9 Step 1's assertion that KAUSHALYA "still ≈1" is mathematically false; the test would FAIL on a correct stock.
- **PATANJALI** (INE619A01035, listed 2022): events `3.0` (2025), `0.01` (2019, *pre-listing*), `5.0` (2007). Product
  = **0.15**, not ×100. Its current return is **+94% (winner)**, NOT a "100×" multibagger — the only post-listing
  event is the 3:1 (2025). The spec's "PATANJALI real 100:1 that gapped ~×100" is simply incorrect for the listed entity.
**Why it matters:** these are the spec's designated "legitimate large events MUST PASS" guardrails. As specified,
the resolved-state assertions would mishandle them, undermining the whole point of the detector (distinguish real
big events from over-adjustment). It also reveals the detector's `applied/gap` ratio is not direction-aware.
**Fix:**
1. Define the comparison in *log-magnitude* terms, direction-normalized: compare `|ln(applied_effective)|` to
   `|ln(gap_ratio)|`, where `applied_effective` for a reverse split is `1/ratio_factor` (so it's the price
   *multiplier*, matching how `observed_max_gap` is measured). Then KAUSHALYA: applied_effective=100, gap≈100 →
   ratio≈1 ✅; ROLEXRINGS: applied_effective=1000, gap≈20 → ratio=50 ❌ (flagged) ✅.
2. Replace the spec/plan PATANJALI example with a TRUE post-listing large forward event, or re-frame PATANJALI as a
   *reverse-split direction* test (its 0.01 is pre-listing and thus irrelevant to its return — a poor example).
   KAUSHALYA is a valid reverse-split-must-pass example *once* the log/direction normalization above is in place.
3. Task 9 must split THREE ways, not two: forward-clean (`applied_eff/gap≈1`), reverse-clean (same, after
   direction-normalizing), and coverage-hole/override (assert sane `current_return_from_issue`, not the ratio).

### F2 (BLOCKER) — Spec/owner-locked "loud envelope tripwire" (T-4 decision (c) part 2) has no implementing task
**Where:** `alignment_audit_2026-06-16.md:320-326` (locked) vs plan Tasks 1–12.
**What's wrong:** Decision (c) explicitly requires replacing the removed silent clamp with a *permanent loud
tripwire* that flags/raises `trough ≤ endpoint ≤ peak` violations in the pipeline (so a future 1000× error surfaces
instead of being hidden). The plan only re-runs the existing T-2 *test* (Task 9 Step 2) and adds a *continuity*
guard (single-day jumps, Task 5) — neither is the envelope invariant tripwire.
**Fix:** Add a task (or extend Task 5) that, after MFE/MAE computation in `07` (or as a post-assemble check in `09`),
asserts the envelope per row/horizon and routes violations to the review register (flag-only, never clamp). This is
the durable safety net; without it, the next bad factor re-introduces silent garbage exactly as before.

---

## MAJOR

### F3 — Override table is a value-writing path with no contradiction guard (Confidence-Invariant leak)
**Where:** plan Task 3; spec §3, §6.
The evidence CSV shows ROLEXRINGS' override (10×) deliberately *contradicts* its raw price gap (≈20×), justified by
a coverage hole. Fine — but nothing stops a future override from silently overriding a *clean, contradicting* price
gap (the back-door §6 warns against). **Add a loader assertion:** an override is only honored if (a) the price gap is
absent/ambiguous/coverage-hole, OR (b) the override's `reason` explicitly records a price-vs-web conflict with cited
evidence. A clean price gap that contradicts an override with no such reason must hard-fail the loader.

### F4 — NPST won't trip the `>5` red baseline; Task 1's parametrize only lists ROLEXRINGS
**Where:** plan Task 1 Step 2 (only `INE645S01024`/ROLEXRINGS is parametrized) vs the narrative claim "ROLEXRINGS/NPST".
NPST applied=9, gap≈2.86 → `9/2.86 ≈ 3.15`, which is **below** the `>5` red threshold. If NPST were added to the
Task-1 parametrize (as the prose implies), the red-baseline test would **fail to detect** NPST. Either (a) lower/justify
the threshold so 2× double-counts are caught (3.15 is a real double-count), or (b) explicitly note NPST is detected by
a *different* signal (count-conflict in the evidence bucketing, not the magnitude ratio) and keep it out of the Task-1
magnitude test. As written the prose and the test disagree on NPST.

### F5 — Task 7 mis-identifies the failing assertion (fix scope risk)
**Where:** plan Task 7 Step 2 ("FAIL (gets +0.15)").
Verified: `test_compulsory_delisting_forces_minus_100` fails at **line 110 (`mae_1y`)**, not the horizon return
(line 106 passes at −1.0). The +0.15 is the MFE/MAE *trough*, not the endpoint. Task 7 Step 3 must target the MFE/MAE
block (`_mfe_mae_block` in `07`, lines 306-360) to force MAE (and any horizon spanning the delist date) to −1.0 — not
the `price_at_horizon`/terminal logic (which is already correct). Re-word Step 2/3 accordingly or the agent will fix
the wrong place and the test will still red.

### F6 — Single-control-row byte-identical check is too weak for the targeted patch
**Where:** plan Task 8 Step 2/4, Task 11 Step 1(d).
One control row proves nothing about the other ~2,000 untouched rows. Change the gate to: *full anti-join* — every
ISIN not in the corp-action set is byte-identical to the snapshot. Also enumerate the known remediation channel
`data/reference/manual_overrides.csv` (applied in `09:98-112`) in the Task 8 Step 1 inventory; the plan omits it.

---

## NITS

### N1 — `archive/` is gitignored; Task 0 Step 4 commit is a no-op
`git check-ignore archive/` → ignored (`.gitignore` has `/archive/`). `git add archive/pre_d1_* && git commit`
(Task 0 Step 4) will add nothing and the commit will fail / be empty. Either `git add -f`, drop the commit step
(snapshot is local-only safety, which is fine), or snapshot somewhere tracked. Cosmetic but the step is broken as written.

### N2 — "09 cross-source check is disabled" overstates it
Spec §1 and plan call the `09` check "disabled." It is not disabled globally — it runs for all non-corp-action stocks
and only *skips* corp-action stocks via `and not has_action` (line 89). Re-word to "skipped for corp-action stocks"
to avoid an agent hunting for a non-existent global disable flag.

### N3 — `03k`/`03l` are not in `run_all.py` or `project_map.py` DAG
Confirmed: `grep` finds no reference to `03k/03l/03h/03j` or `corp_actions_merged` in `run_all.py`/`project_map.py`.
They are standalone scripts; the substrate is patched directly (Task 8), not regenerated. The plan's Phase-3 targeted
patch correctly works around this, but note: **the Task 4 rebuild of `03k/03l` will not flow into the substrate by
itself** — Task 8's patch tool must replicate the `07` compute path (load_prices adjustment + compute()). Make Task 8
Step 3 explicit that it reuses `07`'s `compute()`/`load_prices` rather than re-implementing the math (drift risk if it
re-implements). Also: if `03k/03l` aren't wired into any runnable DAG, consider wiring them (or note in TODO-D1c/d that
the rebuilt steps remain orphaned until live-capture, per the backlog).

### N4 — `_dord(ex_date)` in Task 1's test compares trading-day nearness using calendar ordinals
The test's `observed_gap` uses `abs(_dord(d1) - _dord(ex_date)) <= 3` — that's ±3 *calendar* days, but the docstring
says "+/-3 trading days." Over a weekend/holiday this misses the true ex-date gap. Minor (the ex-date gap is usually
day-adjacent) but the window in `detect_gap` (Task 2) should be trading-day based and the two helpers should agree.

### N5 — `test_compulsory_or_liquidation_delisting_is_minus_100` (substrate, line 103) not mentioned
There is a *second* delisting test on the substrate (`tests/data/test_substrate_integrity.py:103`) asserting
`current_return_from_issue == −1.0` for all compulsory/liquidation rows AND `m.sum() >= 30`. The plan only names the
synthetic test. After the targeted patch, verify this substrate test too (it's part of the T-4 cluster and gates on
the live data, not synthetic fixtures).

### N6 — TODO-D1a…f confirmed present (Task 10 accurate)
`docs/tracker/improvement_backlog.md:27-43` contains TODO-D1a through D1f as Task 10 claims. No action; recorded as a
positive confirmation. Task 10's "confirm + update drift, don't duplicate" is correct.

---

## Positives (confirmed sound)
- Phase-0 triage is genuinely done: `corp_action_external_evidence.csv` has 53 rows, verdicts
  `resolve-apply-once`(28) / `resolve-correct-ratio`(17) / `STAYS-FLAGGED`(6) / `resolve-reverse-direction`(2). The
  6 named STAYS-FLAGGED (CMMIPL, COOLCAPS, SILVERTUC, VAISHALI, INDUSFILA, BANSAL) match the spec/plan exactly.
- The bug mechanism is real and reproduced: ROLEXRINGS events span 2025-09-19→2025-10-17 (28 days, beyond both the
  10-day reconcile window and the 7-day Yahoo dedup), applied product = 1000, current substrate
  `current_return_from_issue = 152.7` (+15,272%), `outcome_class = multibagger`. The fix correctly targets this.
- Baseline is as the plan states: **12 failures** today (T-2 envelope ×N, T-3 weights/goldens, T-4 synthetic,
  T-5 thinktank). Confirmed via `pytest tests -q`.
- `verify.py` is structural + a pytest *count* only (no golden assertions) → "verify PASS with T-3 red" is consistent.
- The "evolve-only-if-robust" / flag-don't-fix discipline is respected; genuine wipeouts kept at −100% (Task 7) is
  correctly separated from flag+null (Task 6).

---

## Recommended pre-implementation edits (ordered)
1. **F1** — direction/log-normalize the factor-vs-gap comparison; replace/re-frame the PATANJALI example; make Task 9
   three-way (forward / reverse / coverage-hole). *(blocker)*
2. **F2** — add the loud envelope-invariant tripwire task (T-4 decision (c) part 2). *(blocker)*
3. **F5** — re-scope Task 7 to the MFE/MAE block (line 110 failure), not the terminal logic.
4. **F3** — add override-contradiction guard to the loader.
5. **F6** — full anti-join byte-identity gate + enumerate `manual_overrides.csv` in the inventory.
6. **F4** — reconcile the NPST detection claim with the actual `>5` threshold.
7. **Check-1 cites** — fix `03k` dedup pointer (75-91), `07` factor-loop pointer (223-246), `09` skip (line 89).
8. Nits N1–N5 as convenient.
