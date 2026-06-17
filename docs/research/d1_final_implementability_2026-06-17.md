# D-1 Plan — FINAL implementability & completeness review (2026-06-17)

**Lens:** can an engineer (or autonomous agent) with ZERO prior context execute this plan
end-to-end, task-by-task, as written, without stalling? NOT a correctness re-litigation
(4 prior rounds settled that). Focus: self-containedness, input availability, cross-task
symbol consistency, TDD step integrity, stall risk.

**Method:** READ-ONLY. Verified every line-reference, every named file, every key value
against on-disk ground truth (`07`, `03k`, `03l`, `09`, the named tests, the evidence CSV,
`corp_actions_merged.csv`, the price files, `substrate_meta.json`, `verify.py`). No edits, no execution.

---

## Ground-truth checks performed (all PASS unless noted)

| Claim in plan | Verified |
| --- | --- |
| `07` `load_corp_actions` 91-111, `actions_for` union 114-127, `load_prices` 206-235, `adj_factor_after` 239-246, `_mfe_mae_block` 306-360 | ✅ all exact |
| `07` two `actions_for`/`load_prices` call sites (~599-600 test-mode, ~630-631 main) | ✅ exact (N2 correct) |
| `03k` Yahoo dedup `load_yahoo_data` 75-91; matching loop 145-195 | ✅ exact |
| `03l` `pd.concat` line 58; row-shaping 44-53 | ✅ exact |
| `09` `has_action` built 86-88, `and not has_action` skip at line 89, `manual_overrides` 98-112, "INVARIANT CLAMP REMOVED" comment line 70 | ✅ all exact |
| `test_compute_synthetic.py`: `return_from_issue_1y == -1.0` line 106, `mae_1y == ...` line 110 | ✅ exact |
| `test_substrate_integrity.py`: `test_compulsory_or_liquidation...` line 103, `m.sum() >= 30` (asserts `current_return_from_issue == -1.0`) | ✅ exact |
| All 8 to-CREATE test files ABSENT; `price_gap.py`/`corp_action_audit.py`/`corp_action_overrides.py`/`corp_action_overrides.csv` ABSENT | ✅ (clean TDD slate) |
| ROLEXRINGS substrate `INE645S01024.csv` EXISTS; `INE645S01016.csv` ABSENT | ✅ (R1 keying valid) |
| KAUSHALYA `INE234I01028.csv` EXISTS | ✅ |
| 6 Wave-1 STAYS-FLAGGED stocks all present in evidence CSV (CMMIPL, INDUSFILA, BANSAL, COOLCAPS, SILVERTUC, VAISHALI) | ✅ |
| `manual_overrides.csv`, `corp_action_external_evidence.csv` EXIST | ✅ |
| `/archive/` gitignored (Task 0 Step 4 rationale) | ✅ |
| `substrate_meta.json` rows = 2384; keys = as_of/rows/archive_pointer/last_refresh | ✅ |
| `verify.py` asserts `substrate_rows == 2384` (hard invariant); test count is DYNAMIC (no hardcoded test-count assert) | ✅ (Task 8 row-count-unchanged claim keeps verify green; adding tests won't trip it) |
| ROLEXRINGS merged events: NSE 10.0 @2025-10-17 + yfinance 10.0 @2025-10-03 + yfinance 10.0 @2025-09-19 → product **1000** | ✅ confirms the 3× over-count |
| KAUSHALYA merged: single 0.01 @2024-01-12 | ✅ |
| `pipeline/lib.py` has `fnum`/`num`/`last_pre_listing_fy` | ✅ |
| `03h`/`03j` exist (spec TODO-4 live-capture targets) | ✅ |

---

## Per-task buildability table

| Task | Buildable as-is? | One-line |
| --- | --- | --- |
| 0 — branch + snapshot | **Y** | concrete commands; `/archive/` gitignore rationale correct |
| 1 — over-adjust detector (test-first) | **Y-with-nit** | full test code; but Step 4 helper has a HARD forward dependency on Task 2's `detect_gap` (F-1) + an under-specified `applied_effective`-for-multi-event rule (F-2) |
| 2 — `price_gap.detect_gap` | **Y-with-nit** | full test + dataclass + algorithm; the "noise threshold 1.5×" example can mis-handle real ~20× gaps that span a data hole — semantics need one clarifying sentence (F-3) |
| 3 — override table + loader + contradiction guard | **Y-with-nit** | concrete; but the seed-CSV column mapping from the evidence CSV is hand-wavy and the evidence CSV has comma-bleed/quoting issues (F-4); `apply_once`/`Override` field names introduced in test but not in the dataclass spec (F-5) |
| 4 — rebuild reconcile + `07` window gate | **Y-with-nit** | tests are described not coded (F-6); `corp_action_out_of_window` flag *plumbing* into a row dict is unspecified for `03k`/`03l` (they emit CSVs, not row flags) (F-7) |
| 5 — continuity guard + re-enable `09` check | **Y** | exact locus (line 89), flag-only contract clear, synthetic test described |
| 5b — envelope tripwire | **Y** | exact locus, byte-identity assertion, flag-only; column names enumerated |
| 6 — flag+null unresolved set | **Y-with-nit** | the dynamic set is well-defined, but "null the unreliable outcome columns" never enumerates WHICH columns (F-8) |
| 7 — explicit delisting −100% in MFE/MAE block | **Y** | pinpoints line 110 `mae_1y`, line 106 untouched; horizon-aware rule stated |
| 8 — targeted patch + inventory gate + anti-join | **Y-with-nit** | strong; the anti-join "byte-identical" gate needs a column-order/float-format caveat (F-9); `outcome_class` re-derivation-after-null ordering unstated (F-10) |
| 9 — verify bug dead, flip tests | **Y** | three-way criterion explicit; line-103 substrate test named |
| 10 — record TODOs | **Y** | confirm-only, already in backlog |
| 11 — independent review | **Y** | checklist (a)-(g) concrete |
| 12 — cleanup + PR | **Y** | scratch list verified to exist; grep-before-delete guard present |

**No task is N-gap.** Every task is buildable; 8 carry nits an engineer could trip on but
not stall indefinitely on. Findings below, severity-ranked.

---

## Findings

### F-1 (MEDIUM, Task 1) — forward dependency on Task 2 is acknowledged but the stub path is hand-waved
Task 1 Step 4 says `observed_max_gap` MUST "Reuse `pipeline.price_gap.detect_gap` (Task 2)" and
notes "Task 2 is authored after Task 1… stub the import and fill it when Task 2 lands." That is
honest, but an autonomous agent running strictly in task order will:
(a) write `from pipeline.price_gap import detect_gap` in `corp_action_audit.py`,
(b) the Task-1 Step-5 "expect PASS" cannot happen — the import of `corp_action_audit` will
ImportError on the missing `price_gap` module, so Step 5's green baseline is unreachable until
Task 2 exists.
**Concrete fix:** make the ordering explicit — either (i) reorder so Task 2 (`price_gap`) is built
*before* Task 1's Step 4/5, or (ii) state in Task 1 Step 5 "run Task 2 first, then return here for
the green baseline." As written, Step 5's "expect PASS" is a stall point for an in-order agent.

### F-2 (MEDIUM, Task 1) — `applied_effective` is defined for ONE event, not for a MULTI-event product
The spec/plan define `applied_effective = 1/ratio_factor` (reverse) or `= factor` (forward) — for a
*single* event. But ROLEXRINGS is a **product of three forward 10× events = 1000**, and
`applied_cumulative_factor` is explicitly "product of in-window `ratio_factor`s." For a product that
mixes forward and reverse events the rule "1/rf for reverse else rf" is ambiguous (which rf? the
product is a single number). In practice the cumulative product for ROLEXRINGS is 1000 (all forward,
>1) so `applied_effective = 1000` works, and KAUSHALYA's product is 0.01 (<1) so `applied_effective
= 1/0.01 = 100` works. The clean operational rule is: **`applied_effective = max(P, 1/P)` where P =
applied_cumulative_factor** (the price-multiplier magnitude of the whole product).
**Concrete fix:** state the multi-event rule explicitly — `applied_effective(isin,symbol) =
max(P, 1/P)` for `P = applied_cumulative_factor(...)`. Without it an engineer may apply the per-event
sign rule to a product and get nonsense for any future mixed forward+reverse stock.

### F-3 (MEDIUM, Task 2) — `detect_gap` window semantics vs the real ROLEXRINGS/KAUSHALYA data holes
Verified on disk: ROLEXRINGS's adjacent closes around the ex-date are **2024-07-05 (2516.95) →
2025-10-17 (126.10)** — a 15-MONTH series hole — giving ratio ≈ 20. KAUSHALYA: **2024-01-11 (9.85)
→ 2024-02-06 (988.3)** — a ~26-DAY hole — ratio ≈ 100. The plan's `detect_gap` is "the max adjacent-
day close ratio within `window` **trading days**… (find the first index at/after `ex_date`, scan
±window positions in the sorted close series)." This is INDEX-adjacent, so it DOES catch both (the
hole collapses to adjacent indices) — which is exactly what makes the detector fire/pass correctly.
But the synthetic test (`test_detects_ten_to_one_split`) uses *contiguous* daily dates, so it never
exercises the hole case, and the prose "within `window` trading days of `ex_date`" reads as
calendar/temporal proximity. An engineer could implement a date-proximity filter (reject pairs >N
calendar days apart), which would return `None` for ROLEXRINGS/KAUSHALYA and silently break the whole
detector.
**Concrete fix:** add one sentence + one test case: "the scan is over series-index adjacency, NOT
calendar proximity — a corp-action that coincides with a data hole still produces an index-adjacent
gap pair (this is intentional; it is how ROLEXRINGS's ~20× and KAUSHALYA's ~100× are measured)."
Add a synthetic test with a multi-week gap in the dates to lock this in.

### F-4 (MEDIUM, Task 3) — evidence-CSV → override-seed mapping is hand-wavy AND the source CSV has quoting drift
Task 3 Step 1 says "extract the price-ambiguous resolutions… seed `corp_action_overrides.csv` with
columns `isin,symbol,ex_date,canonical_factor,direction,reason,evidence_url`." Two gaps:
(1) The evidence CSV columns are `isin,symbol,company_name,bucket,pipeline_events_summary,
price_gap_summary,web_action_summary,web_source_urls,web_status,agrees_with_price,confidence,
recommended_verdict,notes` — there is **no `canonical_factor`, `direction`, or `ex_date` column**.
The mapping from `recommended_verdict` (`resolve-apply-once`/`resolve-correct-ratio`/
`resolve-reverse-direction`) + free-text summaries to a numeric `canonical_factor` is NOT specified —
an engineer must hand-parse `web_action_summary`/`pipeline_events_summary` prose. That is real manual
judgement, not a mechanical step.
(2) Verified: the evidence CSV has **comma-bleed across fields** — a naive `cut -d,` puts URLs and
free text into the verdict column, indicating embedded commas / inconsistent quoting in
`web_source_urls`/`notes`. A loader (or the seeding step) that splits on bare commas will mis-parse.
ROLEXRINGS's verdict IS `resolve-apply-once` and `canonical_factor` is knowable (10), so the one seed
the tests require is achievable — but the generic "extract from the evidence CSV" instruction will
stall on the parsing.
**Concrete fix:** (a) name the exact ROLEXRINGS seed row literally in the plan
(`INE645S01024,ROLEXRINGS,2025-10-17,10.0,down,coverage_hole,<url>`) so the test is unblocked
deterministically; (b) state "parse the evidence CSV with `csv.DictReader` (quoted), not bare split";
(c) scope the seed to ONLY the rows the tests/Task-9 need (ROLEXRINGS + any of the 6 STAYS-FLAGGED
that get an override), deferring full Wave-1 ingestion to the TODO, so the seeding is mechanical.

### F-5 (LOW, Task 3) — `Override` dataclass fields used in tests but not defined
Task 3's test asserts `o.canonical_factor` and `o.apply_once`; the Self-Review names
`Override(canonical_factor, apply_once, direction)`. But Step 4 ("Implement the CSV loader
`override_for(isin)`") never lists the dataclass fields, and the seed CSV column is `canonical_factor`
while the object attr is also `canonical_factor` (consistent) — yet the CSV has no `apply_once` column;
`apply_once` must be DERIVED (always True for these overrides) or read from a column that doesn't
exist. An engineer will guess.
**Concrete fix:** state the dataclass explicitly (`Override(isin, symbol, ex_date, canonical_factor,
direction, apply_once, reason, evidence_url)`) and that `apply_once` defaults True (the override means
"apply this factor exactly once").

### F-6 (LOW, Task 4) — reconcile tests are PROSE, not code (unlike Tasks 1/2/3)
Tasks 1, 2, 3 ship runnable test bodies. Task 4 Step 2 only *describes* three scenarios ("three
identical 10:1 events… → collapses to one"). An autonomous agent must invent the fixtures, the
synthetic price series, the exact function under test (the new reconcile entry point is unnamed — is
it `reconcile(...)`, a new function, a class?), and the assertion shape. This is the single largest
"agent will improvise" surface in the plan.
**Concrete fix:** name the function(s) the new reconcile exposes and give at least one concrete test
body (as Tasks 1-3 do), especially the "phantom event dropped" and "reverse-split-from-gap-sign" cases.

### F-7 (MEDIUM, Task 4) — `corp_action_out_of_window` flag PLUMBING is unspecified across the `03k`/`03l` vs `07` boundary
The flag must end up on a SUBSTRATE ROW (Task 6 reads it to build the unresolved set). But:
- `03k`/`03l` produce CSV files (`corp_actions_*.csv`), not per-substrate-row flags, AND are
  DAG-orphans (plan's own N3) — so a flag set in the reconcile never reaches the substrate.
- Task 4 Step 6 wires the gate into `07.actions_for`, and says "setting the `corp_action_out_of_window`
  flag on the row" — but `07` writes `returns_summary.csv`, whose columns are fixed in `columns()`
  (lines 530-549). There is **no `corp_action_out_of_window` column** there, and the plan never says to
  add one to `columns()` or where the flag is carried from `07` → `09` → `ipo_analysis.csv`.
Task 6 then expects to *read* `corp_action_out_of_window` / `corp_action_unresolved` /
`corp_action_envelope_violation` flags — but no task defines the COLUMN that carries them end to end.
**Concrete fix:** add an explicit sub-step (in Task 4 Step 6 and/or Task 6 Step 4): "add the new
flag columns to `07.columns()` and propagate them through `09`'s `out_cols` (they are returns-derived,
so they flow via `ret_keys`)." Name the carrier column(s) once and reference everywhere. Without this,
Tasks 4/5/5b/6 each set a flag that the next task can't find — a cross-task symbol gap.

### F-8 (MEDIUM, Task 6) — "null the unreliable outcome columns" never enumerates the columns
Task 6 Step 4 says null "the unreliable outcome columns (returns/alpha/MFE/MAE) and `outcome_class`."
But `returns_summary` has ~80 outcome columns (10 horizons × 4 return/alpha variants + 6×4 MFE/MAE +
6×3 timing + lifetime + risk/liquidity). "returns/alpha/MFE/MAE" is a category, not a list. An engineer
must decide whether `current_return_from_issue`, `max_gain_pct`, `max_drawdown_pct`, `all_time_high`,
`volatility_annual`, `listing_gain_*`, the `days_to_*` timing cols, etc. are in or out. The
`test_unresolved_corp_action_rows` test will pin only the few columns it asserts, leaving the rest to
guesswork — and an under-null leaves "garbage multibagger" survivors (the exact thing the spec warns
against, §3 unresolved-row handling).
**Concrete fix:** enumerate the null-set explicitly (e.g. "all `return_from_*`, `alpha_*`, `mfe_*`,
`mae_*`, `days_to_*`, `current_return_from_issue`, `max_gain_pct`, `max_drawdown_pct`, `all_time_*`,
`listing_gain_*`, `outcome_class`; KEEP identity/`issue_price`/`listing_date`/`n_days_history`/flags"),
or define it as a named constant the test imports so test and impl can't drift.

### F-9 (LOW, Task 8) — "byte-identical to the snapshot" anti-join needs a format caveat
Task 8 Step 2/4 gate on "EVERY ISIN NOT in the corp-action set is byte-identical to the snapshot."
Risk: `07`/`09` re-serialize via `fmt()` (`repr(round(v,6))`) and `csv.DictWriter`. If the patch tool
re-writes the WHOLE file (not just affected rows), float re-formatting or column-order differences
could make untouched rows differ byte-wise even when semantically identical → the gate false-fails and
the agent stalls debugging a non-bug. The plan says "reusing `07`'s compute… write back into the
existing substrate, leave all other rows untouched" which implies surgical row replacement (good), but
the anti-join must compare PARSED values for the patched set and can claim byte-identity only for rows
literally copied through.
**Concrete fix:** specify the patch writes by copying untouched rows verbatim (line-level) and only
re-serializing the affected rows; the anti-join then legitimately compares bytes. Or relax the gate to
"parsed-value-identical" for safety.

### F-10 (LOW, Task 8) — `outcome_class` re-derivation vs null ordering across Task 6/8 is implicit
Task 6 nulls `outcome_class` for unresolved rows; Task 8 recomputes via `07.compute()` which SETS
`outcome_class` from `current_return_from_issue` (line 510). If the patch recomputes first and Task-6
nulling runs in `09`, the order matters: a row that is BOTH corp-action-patched AND unresolved must end
up null, not re-labeled. The plan implies `09` (Task 6) runs after the patch, but Task 8 patches
`ipo_analysis.csv` directly (post-`09`), so the Task-6 nulling logic must also be applied inside the
patch tool — not just in `09`. This is a real ordering ambiguity for any row in both sets.
**Concrete fix:** state that the targeted patch applies the Task-6 flag+null step LAST (after
`07.compute`, before writing), so unresolved rows are nulled even though `compute()` repopulated them;
equivalently, the patch must import/reuse the Task-6 nulling helper.

### Nit-1 (INFO, Task 0 Step 3) — baseline "12 pre-existing failures"
Plan asserts "the known 12 pre-existing failures (T-2/T-3/T-4 + thinktank T-5)" as the recorded
baseline. I did not run the suite (READ-ONLY), so this count is unverified here; it is a recorded
expectation, not a blocker. The agent should record the ACTUAL count at Task 0 Step 3 and compare,
rather than assume 12.

### Nit-2 (INFO, Task 1 Step 3 vs Step 5) — two different "expected" states are easy to conflate
Step 3 expects ImportError (helper missing); Step 5 expects PASS (bug present). Between them Step 4
creates the helper. This is correct TDD-for-a-detector (the test asserts the bug EXISTS), but it
inverts the usual red→green intuition and, combined with F-1's forward dependency, is the most likely
spot for an agent to get confused about whether a green or red is "success." The plan does flag this
("the test asserts the bug is present") — keep that emphasis.

---

## Cross-task symbol consistency (explicit audit)

| Symbol | Defined in | Used in | Consistent? |
| --- | --- | --- | --- |
| `detect_gap` / `Gap(ratio,direction,gap_date)` | Task 2 | Task 1 (`observed_max_gap`), Task 4 (reconcile) | ✅ name stable; **but Task 1 consumes it before Task 2 builds it** (F-1) |
| `applied_effective` / `applied_cumulative_factor` / `observed_max_gap` | Task 1 (`corp_action_audit`) | Task 9 (flip) | ✅ names stable; multi-event rule under-specified (F-2) |
| `override_for` / `Override` | Task 3 | Task 4 (reconcile consults it) | ✅ name stable; fields incompletely listed (F-5) |
| `_in_window_actions` / date-window gate | Task 1 + Task 4 | Task 4 `07.actions_for`, Task 8 patch (via `07.compute`) | ✅ conceptually one gate; OK |
| `corp_action_out_of_window` flag | Task 4 | Task 6 (unresolved set), Task 11 checklist | ⚠️ **carrier COLUMN undefined** (F-7) |
| `corp_action_unresolved` flag | Task 6 | Task 6, Task 9 | ⚠️ same carrier-column gap (F-7) |
| `corp_action_envelope_violation` flag | Task 5b | Task 6 | ⚠️ same carrier-column gap (F-7) |
| `check_continuity` / `check_envelope` | Task 5 / 5b | wired into `07`/`09` | ✅ flag-only contract clear |
| corp-action stock set (symbol∪ISIN ∩ in-window) | Task 8 Step 2 | Task 8 Step 3, Task 11(d) | ✅ defined once, reused |

The dominant cross-task issue is **F-7**: three new flags are set by three tasks but no task defines
the column that carries them from `07` → `returns_summary.csv` → `09` → `ipo_analysis.csv` where
Task 6 reads them. Everything else is name-stable.

---

## TDD step integrity (per the rhythm: write-test → fail → implement → pass → commit)

- Tasks 1, 2, 3, 5, 5b, 6, 7, 8, 9: have the full rhythm with runnable commands. ✅
- Task 1's "fail then pass" is INVERTED-by-design (asserts the bug exists) and gated on Task 2
  (F-1) — the only place the fail-first command can't run in strict order.
- Task 4: rhythm present but the test is prose not code (F-6), so "run — FAIL" isn't reproducible
  verbatim.
- Tasks 0, 10, 11, 12: not TDD by nature (branch/confirm/review/cleanup) — appropriately so.

No task asserts on data that cannot exist at that point EXCEPT Task 1 Step 5 (needs Task 2) — F-1.

---

## Stall-risk summary (where an autonomous agent would guess or get stuck)

1. **Task 1 Step 5 green baseline** — blocked until Task 2 exists (F-1). HIGH likelihood of confusion.
2. **Task 2 `detect_gap` window semantics** — wrong (calendar) interpretation silently kills the
   whole detector on the real hole-spanning data (F-3). HIGH impact if mis-built.
3. **Task 4 reconcile** — must invent fixtures + the function name + assertions (F-6); and the
   out-of-window flag has no carrier column (F-7). MEDIUM.
4. **Task 3 evidence-CSV seeding** — manual prose-parsing + a quoting-drifted source CSV (F-4).
   MEDIUM (mitigated if ROLEXRINGS seed is named literally).
5. **Task 6 null-column set** — under-specified; risk of leaving garbage labels (F-8). MEDIUM.
6. **Task 8 anti-join byte-identity** — format/order false-fails (F-9) + Task6/8 null ordering
   (F-10). LOW-MEDIUM.

None are unrecoverable; all are "agent pauses / asks / guesses" rather than "plan is wrong."

---

## VERDICT: **CONCRETE-WITH-NITS**

The plan is implementable end-to-end as written. Every file/line reference, every named artifact,
every key value (ROLEXRINGS ×1000, KAUSHALYA single 0.01, the 6 STAYS-FLAGGED, 2384 rows, the
`/archive/` gitignore, `verify.py`'s row invariant) checks out against on-disk ground truth, and the
4 prior rounds' correctness fixes are intact. An engineer with zero context CAN execute it.

It is **not fully CONCRETE** because of two structural gaps that would make an autonomous agent stall
or improvise, both worth a one-paragraph patch before kickoff:
- **F-7 (the flag carrier column)** — three tasks set flags no column carries to where Task 6 reads
  them; this is a genuine cross-task plumbing hole, not a nit.
- **F-1 + F-3** — the Task-1↔Task-2 build-order dependency makes Task 1's green baseline unreachable
  in strict order, and `detect_gap`'s window semantics (index-adjacent, NOT calendar) are the load-
  bearing detail that makes ROLEXRINGS/KAUSHALYA work yet is only implied.

Recommended pre-build edits (all small): name the carrier column once + add it to `07.columns()` and
`09` (F-7); reorder Task 2 before Task 1's Step 4-5 or add an explicit "build Task 2 first" note (F-1);
add one sentence + one hole-spanning test to `detect_gap` (F-3); state the multi-event
`applied_effective = max(P, 1/P)` rule (F-2); enumerate the Task-6 null column set (F-8); pin the
ROLEXRINGS override seed literally and specify quoted CSV parsing (F-4). With these, the plan is
fully CONCRETE.
