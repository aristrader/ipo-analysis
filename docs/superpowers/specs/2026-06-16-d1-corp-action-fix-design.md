# D-1 Corp-Action Fix — design spec (2026-06-16)

**Status:** design approved (brainstormed with owner 2026-06-16); reviewed across 7 rounds (R1–R4 + R5 implementability + R6 final-correctness + R8 adversarial edge-case hunt, all `_2026-06-17`). The DESIGN is unchanged (price-disposes, flag+null, genuine-wipeout=−100%, confidence invariant, targeted-patch); R6 corrected the join-key SCOPE (window gate = symbol-added subset only; ISIN-matched always applies — D1-F1), the gate LOCUS (call site, not inside `load_prices` — D1-F2), the flag carrier column (F-7), the gap-window semantics (series-index-adjacent — F-3), and the anti-join comparison (pre-existing column set — D1-M1). **R8 folded remedy (a) (`docs/research/d1_adversarial_2026-06-17.md`): the price-validation ("price disposes") now runs PER ADMITTED ACTION at the `07` substrate-reaching call site — not only in the DAG-orphaned `03k`/`03l` reconcile — so in-window phantoms / same-event double-counts (CANTABIL, GNA, …) are dropped/collapsed before they reach the substrate, even while `03k`/`03l` stay orphaned.** Implementation plan: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`.
**Scope:** fix the corp-action over-/mis-counting (D-1) + its downstream test failures (T-2, T-4; sets up T-3).
**Not in scope:** T-5 (thinktank UI, unrelated); Wave-2 web research (deferred); broader data-integrity checks (separate batch).

---

## 1. Problem

The pipeline applies scraped corporate-action (split/bonus/consolidation) factors **blindly**. The same real
event reported by multiple sources on dates beyond the ±10-day reconcile window leaks through `03k`→`03l` and is
applied 2–3× in `07`. Effects (Phase-0 + Wave-1 confirmed):
- **ROLEXRINGS** one 1:10 split counted 3× → ÷1000 → fake `current_return_from_issue` ≈ **+15,272%**, mislabeled `multibagger`.
  Note: ROLEXRINGS keys on its **substrate ISIN `INE645S01024`** (post-split; the price file that exists); the corp-action
  rows sit under `INE645S01016` / empty-ISIN yfinance rows and reach the price series ONLY via the NSE-**symbol** join.
- **NPST** one bonus counted 2× → ≈ **+16,127%**. Reverse splits (`ratio_factor<1`) from Yahoo applied as divisors (D-2).
- The `09_assemble` cross-source listing-price check is **skipped for** any stock with a corp action (the `and not has_action`
  clause at `09:89`; it is not globally disabled — it still runs for all non-corp-action stocks) → corp-action stocks are invisible to it.
- **(R8) In-window phantoms / same-event double-counts survive into the substrate** because "price disposes" did NOT reach the
  substrate path. The price-validating reconcile is in `03k`/`03l`, which are DAG-orphaned (never regenerate
  `corp_actions_merged.csv`); the only substrate-reaching path is Task 8 → `07.compute()`, and `07` reads
  `corp_actions_merged.csv` directly + applies the **window gate ONLY, with NO gap check**. So a real split reported by two
  sources a few days/weeks apart (both in-window) is applied twice → factor squared, on NON-seeded stocks the override table
  never touches and the envelope tripwire is provably blind to (a uniform over-count divides `adj_issue` and the price
  extremes by the same constant, preserving `trough ≤ endpoint ≤ peak`). Verified offenders: **CANTABIL** (factor 25, should
  be 5 → 39.68× vs correct 7.14×), **GNA** (factor 4, should be 2 → 6.39× vs 2.70×), plus RPEL/VISHWARAJ/GICL/PAVNAIND/
  KNRCON/ASIANTILES (~13 strict, ~tens broad). **Remedy (a, folded):** apply price-validation PER ADMITTED ACTION at the
  `07` substrate-reaching call site — see Phase 1.

**Join-key truth (set by the 2026-06-17 join-strategy investigation, `docs/research/d1_join_strategy_2026-06-17.md`,
SCOPED by the 2026-06-17 final-correctness gate, `docs/research/d1_final_correctness_2026-06-17.md` / D1-F1):**
a face-value split mints a NEW ISIN, so the corp-action ISIN ≠ the substrate/price ISIN — **0** of the 961 non-substrate
corp-action ISINs have their own price file, and **301** substrate rows reach their actions ONLY via the **NSE symbol**.
Therefore the join key is the **`07.actions_for` union (substrate ISIN ∪ NSE symbol)**, never the corp-action-file ISIN alone.
**The trading-date window gate is scoped to the SYMBOL-ADDED subset ONLY (D1-F1, non-negotiable):**
- An **ISIN-matched** action (`ex` ∈ `by_isin[substrate-ISIN]`) is, by definition, the stock's OWN corporate event and
  **ALWAYS applies, regardless of the price-coverage span** (subject only to price-validation). The daily-bhavcopy price
  file starts ~2017 for old stocks, so a legitimate post-listing split that fell in the pre-coverage gap has `ex_date <
  first_trade` yet is genuine — gating it would corrupt the issue-anchored return (e.g. ATLANTAA's winner→loser flip,
  TARIL's multibagger label). **NEVER window-drop an ISIN-matched action.**
- The symbol key gets **reused** by a later listing, so only **symbol-added** matches (in `by_symbol` but NOT in
  `by_isin[substrate-ISIN]`) are **GATED by the trading-date window** (`ex_date ∈ [first_trade, last_trade]`, small
  pre-listing slack); out-of-window symbol-added matches are **dropped + flagged `corp_action_out_of_window`**
  (→ unresolved set).

This is **option (d)** in the join-strategy doc, scoped to the symbol-added subset per D1-F1. Of the **86** total
out-of-window union actions, only the symbol-added subset (the prior "44" — 37 yfinance, 25 with `ratio_factor<1`) is
droppable; the ~42 ISIN-matched OOW actions (incl. ~26 legit post-listing pre-coverage splits) stay applied. This removes
the wrong-era/reused-symbol attachments while keeping the legitimate ISIN-matched ones — fixing the CAUSE of the
over-adjustment (the envelope tripwire only catches the symptom) WITHOUT introducing the D1-F1 regression.
`09:86-89`'s `has_action` already unions ISIN+symbol — the right template.

**Linked downstream (same root cause — the removed MFE/MAE "clamp" un-hid them):**
- **T-2** — 39 rows violate `trough ≤ endpoint ≤ peak` (impossible envelopes from bad factors).
- **T-4** — compulsory-delisting no longer shows −100% (the clamp was its only enforcement).
- **T-3** — committed weights/goldens stale; must be re-derived **after** the data is clean (not before — derivation is contaminated).

## 2. Principle — "feeds propose, price disposes"

The **raw daily price discontinuity is the senior referee.** A real split gaps the raw price by ~the ratio on the
ex-date; that gap is the truth. Yahoo/NSE/web only *propose*; cross-source agreement *corroborates on top of* price
(two sources agreeing on a phantom the price never moved on is still rejected — price outranks source agreement).

## 3. Design

### Phase 1 — rebuild reconciliation (`03k`/`03l`; consumed by `07`)
- **Join key = symbol∪substrate-ISIN with the window gate on the SYMBOL-ADDED subset only (option (d) + D1-F1, §1).**
  Build the candidate set as the `07.actions_for` union (`by_isin[substrate-ISIN] ∪ by_symbol[NSE-symbol]`, dedup by
  `(ex_date, ratio_factor)`). **ISIN-matched events ALWAYS admitted** (the stock's own event — never window-dropped, D1-F1).
  **Only symbol-added events** (in `by_symbol` but NOT in `by_isin[substrate-ISIN]`) **are admitted only if their `ex_date ∈
  [first_trade, last_trade]`** (small few-trading-day slack before `first_trade` for a listing-day split); out-of-window
  symbol-added events are **dropped from adjustment and flagged `corp_action_out_of_window`** (routed to the unresolved set) —
  never silently applied. The admitted set = (all ISIN-matched events) ∪ (in-window symbol-added events). Group candidate
  events per **substrate ISIN**; NEVER group/key on the corp-action-file ISIN alone (0 of those have a price file; 301 rows
  reach actions only via the symbol). **The window gate is implemented AT THE CALL SITE where actions+prices meet — NOT
  inside `load_prices` (D1-F2):** the `actions` list feeds `load_prices` (the price SERIES), `adj_factor_after`
  (`issue_price → adj_issue`, `07:438`), AND `adj_factor_after` (delisting `last_price → terminal`, `07:270`). Build the
  windowed list ONCE at each call site (~599-600, ~630-631) — read the window from the loaded prices, apply the
  symbol-added-only gate — and pass the SAME list to BOTH `load_prices` AND `compute()`, so the series, issue, and terminal
  adjustments cannot desync. EVERY downstream consumer (returns, MFE/MAE, listing metrics, issue/terminal) is then
  window-safe and consistent, and the Task-8 targeted patch (which reuses `07.compute`) inherits it.
- **(R8 — remedy (a)) PER-ACTION PRICE-VALIDATION AT THE `07` CALL SITE — this is where "price disposes" actually REACHES
  the substrate.** The price-validating `03k`/`03l` reconcile is the OFFLINE source-of-truth, but it is DAG-orphaned and does
  NOT regenerate `corp_actions_merged.csv` in any runnable chain — so the SUBSTRATE enforcement is HERE, at the same call site
  where the windowed `actions` list is built (right after the symbol-added window gate, before the list is passed to
  `load_prices`/`compute`). For EACH admitted action (already window-passed), call `detect_gap` (Task 2, series-index-adjacent)
  against the loaded price series and decide:
  - **Gap supports the claimed ratio** (within tolerance, direction-normalized) → **apply** the action.
  - **Multiple same-ratio legs that map to ONE price gap** (e.g. yfinance + NSE recording the same 5:1 a few days apart) →
    **collapse to a single application** (this is the double-count fix — it is what reduces CANTABIL 25→5 and GNA 4→2).
  - **No supporting gap, but price data EXISTS around the ex-date** (the series has closes spanning the ex-date and they did
    NOT jump by ~the ratio) → **true PHANTOM** → **DROP the action + flag `corp_action_no_price_gap`** → route the row to the
    unresolved set. NEVER multiply a phantom into the factor.
  - **No gap because price data is MISSING around the ex-date** (a coverage hole — no closes to compare, e.g. ROLEXRINGS's
    15-month hole) → this is NOT a phantom → **defer to the override table** (apply the canonical factor if a confident override
    exists; else flag-unresolved). **MUST distinguish "no gap because phantom" (data present, no jump) from "no gap because
    data missing" (coverage hole)** — a coverage-hole legitimate case must NOT be wrongly dropped.
  This makes the headline "price disposes" promise execute on `07.compute()` (which Task 8 reuses), so the substrate is correct
  **even if `03k`/`03l` stay orphaned**. The same per-action validation is what the detector (Task 1) and reconcile (Task 4)
  measure, so all three agree on what the substrate will actually apply.
- **Flag carrier column (F-7, + R8) — define + plumb end-to-end.** The `corp_action_out_of_window` / `corp_action_unresolved` /
  `corp_action_envelope_violation` / **`corp_action_no_price_gap`** (R8 phantom-drop) flags must ride a real column from
  `07` → `returns_summary.csv` → `09` → `ipo_analysis.csv`. Add the columns to `07.columns()` (which ends at
  `listing_metrics_status`, `price_source`); they flow automatically into `09`'s `out_cols` via `ret_keys` (`09:41-45`).
  Without this the flag mechanism is inert and the unresolved set (which reads these columns) has nothing to consume.
- Replace the `(ex_date, ratio_factor)` + 10-day-window dedup with **price-validation**: for each admitted candidate event,
  measure the actual price gap (via `detect_gap`, a **series-INDEX-adjacent** window — NOT calendar — so a gap that spans a
  data hole or suspension is still measured: ROLEXRINGS ~20× over a 15-month hole, KAUSHALYA ~100× over a ~3.5-week
  suspension, F-3); **apply once** to match the real gap; infer reverse-split **direction from the gap sign** (fixes D-2).
  When collapsing duplicates that map to one gap, **keep distinct same-day legs whose PRODUCT matches the gap** — a compound
  same-day split+bonus (ISHAN: 10:1 split + 2:1 bonus = 30 vs gap 28.56×) must keep BOTH legs, not drop one (D1-N1); the
  multi-event price-multiplier magnitude is `applied_effective = max(P, 1/P)` for `P = applied_cumulative_factor` (F-2).
- **Factor source = auto-derive + small override table:**
  - *Auto-derive* the factor from the price gap itself for the clean cases (Wave-1 evidence CSV cross-checks it).
  - *Override table* (tiny, explicit) only for price-ambiguous cases the gap can't settle (coverage holes, e.g. ROLEXRINGS),
    sourced from the Wave-1 verdicts (`data/master/review/corp_action_external_evidence.csv`). This same table feeds the strict-resolve TODO.
- The "strict-mode" toggle is **dropped** — price-validation subsumes it (single-source + real gap = accept; no gap = reject).

### Phase 2 — continuity guard (flag-only, never silently fix)
- After adjustment, any leftover **unexplained single-day price jump** → **flag** (data_quality / review register), do NOT clamp.
- Close the hole: `09_assemble` must run the cross-source listing-price check **even for** stocks with corp actions.
- This is also the **safety net for deferred live-capture** (an un-captured future split surfaces here as a flagged jump).

### Unresolved-row handling (owner decision 2026-06-16)
**Confidence invariant (non-negotiable):** a FINAL corrected value is written ONLY for stocks we can confidently resolve
(price gap validates the factor, or a confident override exists). Every stock we cannot confidently resolve →
flag + null (keep the row); we NEVER write a guessed value. "Unsure → flag+null", never "unsure → best-guess". The
unresolved set is dynamic (the known Wave-1 STAYS-FLAGGED + anything the rebuild can't validate + T-2 residuals).

- **Genuinely-unsure** rows (price ambiguous / coverage hole / price-vs-source conflict — e.g. the 6 Wave-1 STAYS-FLAGGED:
  CMMIPL, INDUSFILA, BANSAL, COOLCAPS, SILVERTUC, VAISHALI), PLUS any stock with a dropped out-of-window **symbol-added**
  action (D1-F1 — ISIN-matched drops never occur), PLUS **any stock with a price-validation-dropped PHANTOM action
  (`corp_action_no_price_gap`, R8 remedy (a))**: **keep the row**, set `corp_action_unresolved` flag + low
  `data_quality_tier`, and **null the specific unreliable outcome columns AND the derived `outcome_class` label**
  (else a garbage multibagger/wipeout tag survives) so a known-garbage number cannot pollute base rates. **NULL-SET (F-8 —
  enumerated, define as a named constant the test imports):** all `return_from_issue_*`, `return_from_listing_*`, `alpha_*`,
  `alpha_sc_*`, `mfe_*`, `mae_*`, `mfe_lst_*`, `mae_lst_*`, `days_to_mfe_*`, `days_to_mae_*`, `days_to_breakeven_*`,
  `current_return_from_issue`, `max_gain_pct`, `max_drawdown_pct`, `max_drawdown_duration_days`, `all_time_high`,
  `all_time_low`, `listing_gain_open`, `listing_gain_close`, `volatility_annual`, `outcome_class`. **KEEP:** identity,
  `issue_price`/`issue_price_adj`, `listing_date`, `n_days_history`, turnover/liquidity identity, all flag columns,
  `delisted`/`delist_reason`. **Nothing force-excluded** — analysis chooses to include/down-weight with eyes open.
- **Critical distinction — genuine wipeouts are NOT nulled.** A confirmed compulsory delisting/liquidation stays **−100%**
  (decision A1, the truth). Nulling applies ONLY to can't-determine cases. Many flagged rows may turn out to be genuine wipeouts —
  classification happens in the strict-resolve TODO, not here.

### T-4 folded in — explicit delisting −100%
- Enforce −100% **explicitly** in the delisting logic: terminal = −100%, and any horizon whose window spans the delisting
  date reaches −100% — decoupled from the removed clamp. Result: genuine wipeouts read −100%, unresolved-unknowns read null. Clean separation.

### Phase 3 — TARGETED PATCH (not a full re-run)
- **The substrate is NOT byte-reproducible** (post-pipeline manual remediations + DRHP staging). A naive full re-run would
  regress those. Therefore: **inventory the post-pipeline manual remediations FIRST**, then apply the corp-action correction
  **surgically** to the existing `ipo_analysis.csv` — recompute only the **affected stocks'** price-derived columns
  (the corp-action stocks = substrate ISINs with ≥1 **admitted** event: any ISIN-matched event OR an in-window symbol-added
  event after the D1-F1-scoped gate), preserving every other manual fix.
- Snapshot to `archive/` first; **diff** before/after to confirm only intended rows changed — the anti-join compares each
  non-corp-action row over the **PRE-EXISTING column set ONLY** (D1-M1: the new `corp_action_*` columns are appended to every
  row and would false-fail a raw byte compare; additionally assert those new columns are empty on non-corp-action rows).
  Confirm the fakes are gone (ROLEXRINGS/NPST/…), the legit ISIN-matched pre-coverage splits are UNCHANGED (ATLANTAA stays a
  winner, TARIL stays a multibagger — D1-F1 regression guard), T-2 envelope violations clear, continuity guard reports clean.

### Then (after the data is clean) — T-3 + downstream re-derive
- Re-derive `scorecard_weights.json` + re-bless goldens (`derive_goldens.py` / `run_weights.py`); re-run the affected
  Layer-3 derivations so all downstream numbers reflect corrected data. Re-run mutation/showdown gates (the substrate changed).

## 4. TODOs this creates (record durably in `docs/tracker/improvement_backlog.md`, with full context)

1. **STRICT — resolve all flagged corp-action rows.** They will move the numbers materially, and **many may be genuine
   wipeouts** (not data errors). Each flagged row must be classified: *real wipeout (−100%) / data error / real split with
   missing price data*. Carry per-stock context (price gap vs sources, why uncertain, likely resolution) so it's pick-up-and-finish.
2. **Re-derive all downstream numbers again once the flagged rows are resolved** (bundle with #1). Method = *targeted*
   re-derivation of the analysis layer on the corrected substrate (weights, goldens, findings, forward-test, backtests) —
   NOT a naive full pipeline rebuild, which only becomes safe once the remediation-overlay (#3) exists.
3. **Reproducibility — remediation overlay.** The substrate must become regenerable. Move all post-pipeline hand-fixes into a
   **separate overlay file** that is **superimposed** onto fresh pipeline output (pipeline output + overlay = substrate). Until
   this exists we are stuck doing targeted patches; this is the real fix and must be done.
4. **Live corp-action capture (Q2).** Wire the rebuilt `03h/03j/03k/03l` steps into `run_refresh.py`; store a
   **`corp_actions_as_of`** watermark in `substrate_meta.json`; live-capture pulls from **watermark − ~1 month** (overlap buffer).
   Do when we go live (the continuity guard is the interim safety net).
5. **Broader data-integrity checks (separate flag-only batch).** implied-shares cross-check (O-12), price-band invariant (O-13),
   date-ordering (O-11), EPS reconciliation (O-5/O-7), systemic 0→NaN at load (I1).

## 5. Process
- Execution pipeline / TDD: write the **over-adjustment detector as a failing test first**. The detector signature is
  **applied cumulative factor inconsistent with the observed price gap** (e.g. ROLEXRINGS applied ×1000 but price gapped ~×20),
  NOT a blanket magnitude threshold — *legitimate large events must pass*.
- **Direction-normalize the comparison (forward AND reverse splits).** `applied_cumulative_factor` is a product of
  `ratio_factor`s and can be < 1 for a reverse split (e.g. a 1:100 consolidation = 0.01), while the observed price gap
  is always measured as `max(c0/c1, c1/c0) ≥ 1`. Comparing them directly mis-flags reverse splits. So define
  **`applied_effective`** = the price-MULTIPLIER equivalent of the WHOLE product: for `P = applied_cumulative_factor`,
  **`applied_effective = max(P, 1/P)`** (F-2 — the single clean multi-event rule; ROLEXRINGS `P=1000 → 1000`, KAUSHALYA
  `P=0.01 → 100`; do NOT apply the per-event `1/rf`-vs-`rf` sign rule to a product). Compare in log-magnitude:
  `|ln(applied_effective)|` vs `|ln(gap_ratio)|` (equivalently `applied_effective / gap`). Then a clean event ≈ 1; an
  over-adjustment is far from 1.
- **Guardrail (legitimate-large-event MUST-PASS) example — KAUSHALYA (substrate ISIN `INE234I01028`, "Kaushalya
  Infrastructure Development Corp.", listed 2007).** KAUSHALYA is a single 1:100 *reverse* split (`ratio_factor = 0.01`,
  ex 2024-01-12, a symbol-only/empty-ISIN yfinance row reached via `by_symbol["KAUSHALYA"]`); `07` applies
  `price / 0.01 = price × 100`, and the raw price gaps UP ~×100 on the ex-date. After direction-normalization:
  `applied_effective = 1/0.01 = 100` vs `gap ≈ 100` → ratio ≈ 1 ✅ (untouched, correct). This is the canonical
  reverse-split-must-pass case. **It also illustrates the symbol-reuse / in-window guard (symbol-added subset, D1-F1):**
  KAUSHALYA's event is a symbol-only/empty-ISIN yfinance row (reached via `by_symbol`, NOT `by_isin[INE234I01028]`), so it IS
  in the gated subset — and its 2024-01-12 ex-date is IN-window for the 2007-listed `INE234I01028`, so it is correctly
  admitted. A freed symbol re-assigned to a *later* listing would have its action fall OUT-of-window and be dropped+flagged.
  (Had this been an ISIN-matched action, it would apply regardless of window per D1-F1.) **Do NOT confuse `INE234I01028` with
  `INE0Q2V01012`** — the latter is a DIFFERENT company, **"KLL Logistics" (Kaushalya Logistics, symbol `KLL`, listed
  2024)**, with its own price file; name the substrate ISIN explicitly so the two are never mixed up.
  *(PATANJALI is NOT a guardrail example: it is a +94% winner whose only post-listing event is a 3:1 bonus in 2025;
  its 100:1 (0.01) was PRE-listing and irrelevant to its return — and would in fact be dropped as `corp_action_out_of_window`
  under the date gate — do not use it.)*
- Assert: ROLEXRINGS/NPST resolve to the single correct factor; KAUSHALYA's real ~100× (direction-normalized) stays intact.
  Independent review. Branch → PR.
- Stage sensibly: Phase 1–3 + T-4 = the corp-action fix PR; T-3 + targeted downstream re-derivation = a follow-up once the flagged rows are resolved.

## 6. Risks / open items
- Targeted patch depends on a correct **inventory of manual remediations** — if one is missed, a recompute could clobber it. The
  inventory step is mandatory and gated before any recompute.
- Override table must stay tiny and justified (each entry = a price-ambiguous case with cited Wave-1 evidence) — it is not a
  back-door for guessing.
- **Gate over-scope (D1-F1, HIGH — the would-be regression).** The window gate MUST be scoped to the symbol-added subset only;
  applying it to ISIN-matched actions would wrongly drop ~26 legitimate post-listing pre-coverage splits (the daily-bhavcopy
  price file starts ~2017), corrupting their issue-anchored returns and flipping winners to losers (ATLANTAA, TARIL,
  ADANIPORTS, TITAGARH, BAJAJCON). ISIN-matched = the stock's own event = always applies. Real OOW union count = 86 (44 was
  symbol-added only). Regression-guard tests required.
- **Gate locus (D1-F2, MEDIUM — internal desync).** The gate must be applied at the call site, with one windowed `actions`
  list passed to BOTH `load_prices` AND `compute()`; gating only inside `load_prices` desyncs the issue-price (`07:438`) and
  terminal (`07:270`) adjustments from the series.
- **Anti-join false-fail (D1-M1, MEDIUM).** Adding the new `corp_action_*` columns re-serializes every row, so the byte-identity
  anti-join must compare over the pre-existing column set only (+ assert the new columns empty on non-corp-action rows).
- **Substrate-reaching enforcement (R8, HIGH — the would-be-corruption the adversarial round caught).** "Price disposes" must run
  on the `07` substrate path, NOT only in the orphaned `03k`/`03l` reconcile — otherwise in-window phantoms / same-event
  double-counts (CANTABIL 25→5, GNA 4→2, RPEL/VISHWARAJ/GICL/PAVNAIND/KNRCON/ASIANTILES) survive with inflated multibagger
  magnitudes, invisible to the envelope tripwire (provably blind to a uniform over-count) and to the override table (named
  seeds only). The per-action price-validation at the call site (Phase 1, Task 4) closes this. **The phantom-DROP path must
  not wrongly drop a coverage-hole legitimate case** — distinguish "no gap because phantom" (price present, no jump → drop+flag)
  from "no gap because data missing" (coverage hole → defer to override; ROLEXRINGS stays resolved via its seed).
