# D-1 Corp-Action Fix — FINAL whole-system correctness gate (2026-06-17)

**Reviewer role:** final, READ-ONLY correctness/test-soundness/safety review of the D-1 plan + spec across
**every corp-action bucket**, end-to-end. No code edits, no execution. The plan passed four prior rounds
(`d1_plan_review`, `d1_plan_rereview`, `d1_join_strategy`, `d1_plan_final_verify`, all `_2026-06-17.md`);
this gate confirms their settled points and hunts for anything still wrong before code is written.

**Documents reviewed:** plan `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`; spec
`docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`; the four prior findings docs.
**Ground truth verified against:** `data/reference/corp_actions_merged.csv` (1897 rows),
`data/master/ipo_analysis.csv` (2384 substrate rows), `pipeline/07_returns_summary.py`,
`pipeline/09_assemble.py`, `data/prices/`, `data/master/review/corp_action_external_evidence.csv`,
`tests/pipeline/test_compute_synthetic.py`, `tests/data/test_substrate_integrity.py`. All numbers below were
re-derived live.

---

## VERDICT: **FLAW-FOUND** (one HIGH-severity correctness flaw, one MEDIUM, plus nits)

The core architecture is sound and the prior four rounds correctly settled the join-key design, F1–F6, R1–R5,
N1–N3. The over-adjustment detector, the symbol∪substrate-ISIN union, the override contradiction guard, the
flag+null discipline, the genuine-wipeout −100% separation, and the envelope tripwire are all correct in
design and exercise the real production path. **But the date-window gate — the heart of the R3/option-(d)
fix — is mis-scoped, and as written it will silently corrupt ~26 legitimate long-term stocks** (D1-F1, HIGH).
A second issue (D1-F2, MEDIUM) is that the gate applied at the wrong locus produces an *internal
inconsistency* between the price-series adjustment and the issue-price/terminal adjustment. Both are fixable
in the plan text before build; neither was caught by the prior four rounds because they all validated the gate
against ROLEXRINGS/KAUSHALYA/the 44 symbol-reuse cases (where it is correct) and never walked the
ISIN-matched, post-listing, pre-price-coverage population.

---

## Per-bucket walk — does the design do the RIGHT thing?

| # | Bucket | Expected behavior | Plan delivers? | Test exists? |
|---|---|---|---|---|
| 1 | **Forward split** (price gaps down ~ratio) | apply once, direction down | ✅ Yes — `detect_gap` direction="down"; reconcile apply-once; `applied_effective`=factor | ✅ Task 2 `test_detects_ten_to_one_split`; Task 4 three-identical-events test |
| 2 | **Reverse split / consolidation** (rf<1, price gaps UP ~1/rf; KAUSHALYA) | apply once, direction up, detector direction-normalized → PASSES | ✅ Yes — `applied_effective`=1/rf; log-magnitude compare; verified KAUSHALYA `INE234I01028` gaps 100.34× on disk, applied_eff=100 → ratio≈1 | ✅ Task 4 rf=0.01-gaps-up test; Task 9 Step 1(b) reverse-clean guardrail |
| 3 | **Compound same-day split+bonus** (ISHAN 10×3=30 vs gap 28.56) | keep BOTH legs (product), not over-count | ⚠️ Mostly — current substrate correct (ISHAN raw 80/adj 2.667 = exactly 30.0). But the reconcile's "collapse duplicates that map to the same gap" (Task 4 Step 4) is a RISK for same-day **different-type** legs — see D1-N1 | ⚠️ Partial — NO test for the compound-keep case (gap in coverage) |
| 4 | **Over-count** (same event 2–3×; ROLEXRINGS ×1000 vs gap ~20) | collapse to one; detector flags red | ✅ Yes — verified ROLEXRINGS substrate +15,272%, price gap 19.96× on 2025-10-17, product 1000 via symbol union; detector ratio≈50 flags red | ✅ Task 1 parametrize (`INE645S01024`,`ROLEXRINGS`); Task 9(c) resolved |
| 5 | **Out-of-window / reused symbol** (44 symbol-added cases) | DROP + flag `corp_action_out_of_window`, never apply | ✅ for the 44 — verified 44 symbol-added OOW (25 rf<1, 30 rows). **❌ over-reach: the same gate ALSO drops 26 LEGITIMATE ISIN-matched post-listing pre-coverage splits** → D1-F1 | ✅ Task 4 Step 6 `test_actions_for_window`; ❌ no test guards the legit-pre-coverage case |
| 6 | **Phantom** (claimed, price never gapped) | reject, not applied | ✅ Yes — "price disposes"; reconcile emits price-unsupported events to flag channel | ✅ Task 4 phantom test |
| 7 | **Coverage-hole / override** (ROLEXRINGS) | override factor applied; contradiction-guard blocks clean-gap override | ✅ Yes — evidence row IS a price-vs-web conflict (gap ~20× but web NCLT 10×); guard branch (b) honors it; clean-contradiction hard-fails | ✅ Task 3 Step 6 three cases |
| 8 | **Genuine wipeout / compulsory delisting** | −100% (NOT null), horizon-aware | ✅ Yes — Task 7 forces MAE=−1.0 + horizon-spanning −1.0 in `_mfe_mae_block`; verified the failing assertion is `mae_1y` (line 110, gets 0.15), terminal (line 106) already passes | ✅ synthetic line 110 + substrate test line 103 (≥30) |
| 9 | **Genuinely-unresolved** | flag + null (incl. `outcome_class`), keep row, never guess | ✅ Yes — 6 Wave-1 STAYS-FLAGGED verified (CMMIPL/INDUSFILA/BANSAL/COOLCAPS/SILVERTUC/VAISHALI); dynamic unresolved set; Confidence Invariant | ✅ Task 6 `test_unresolved_corp_action_rows` |

---

## FINDINGS (severity-ordered)

### D1-F1 (HIGH — correctness flaw, NOT previously caught) — the date-window gate wrongly drops ~26 legitimate ISIN-matched post-listing splits, corrupting their issue-anchored returns

**Where:** spec §1/§3 + plan "CANONICAL JOIN KEY" (lines 28–36), Task 1 Step 4 (`_in_window_actions`), Task 4
Step 6 (the `07` window gate), Task 8 patch set. The window is defined as `[first_trade, last_trade]` = the
**price-file coverage span**.

**What's wrong.** The gate's purpose is to catch **symbol-reuse** (a freed NSE symbol re-assigned to a later
listing → the OLD company's action attaches via the symbol join). That failure mode lives **only in the
symbol-added subset** (empty-ISIN yfinance / foreign-ISIN NSE rows). But the plan applies the window filter to
the **entire union**, including **ISIN-matched** actions. For old stocks, the daily-bhavcopy price file starts
~2017 even though the stock listed years earlier — so a **legitimate post-listing split that occurred in the
pre-coverage gap** has its `ex_date < first_trade` and gets dropped.

**Quantified blast radius (live):**
- **86** total union actions are out-of-window (vs the plan's "44"). The plan's 44 counts ONLY symbol-added
  rows; there are **~42 additional ISIN-matched out-of-window actions** the gate also drops.
- Of those, **26 are POST-listing, pre-coverage, ISIN-matched splits** — genuine events that MUST stay applied.
- These splits are currently applied via **`adj_factor_after(actions, listing_date)`** (07:438) to set
  `issue_price_adj`. Dropping them un-divides the issue price and corrupts every issue-anchored return.

**Concrete damage (verified in the current substrate — these stocks are in the patched set):**
| symbol | isin | listing | split (dropped) | adj_issue now | cur_ret now | if dropped |
|---|---|---|---|---|---|---|
| ATLANTAA | INE285H01022 | 2006-09-25 | 5.0 (ex 2010-11-08) | 30.0 (=150/5) | **+36.3% winner** | adj_issue→150 ⇒ return deeply negative, **winner→loser flip** |
| TARIL | INE763I01026 | 2007-12-28 | 1.111 (ex 2013-06-13) | 20.93 | **+1,434% multibagger** | adj_issue shifts ⇒ multibagger return distorted |
| ADANIPORTS | INE742F01042 | 2007-11-27 | 5.0 (ex 2010-09-23) | 88.0 (=440/5) | (null today) | adj_issue→440 ⇒ 5× wrong if/when priced |
| TITAGARH | INE615H01020 | 2008-04-21 | 5.0 (ex 2015-04-23) | 108.0 (=540/5) | (null) | adj_issue→540 ⇒ 5× wrong |
| BAJAJCON | INE933K01021 | 2010-08-18 | 5.0 (ex 2011-05-05) | 132.0 (=660/5) | (null) | adj_issue→660 ⇒ 5× wrong |

ATLANTAA flips winner→loser; TARIL's multibagger label is at risk. Task 8 reruns `07.compute` with the gate,
so the patch **introduces** these regressions into a previously-correct part of the substrate — the exact
collateral-damage class this review is meant to catch. (Note: several of the ~38 current T-2 envelope
violations — e.g. HUBTOWN ret=+0.58 vs mfe=−0.59 — are themselves issue-anchored adjustment artifacts, so the
issue-price path is already known to be load-bearing here.)

**Why the prior four rounds missed it.** They validated the gate on ROLEXRINGS (in-window), KAUSHALYA
(in-window), and the 44 symbol-reuse cases (correctly dropped). None walked the ISIN-matched pre-coverage
population. The `d1_join_strategy` doc explicitly scoped its 44-count to "symbol-ADDED actions … NOT already
present under the row's own ISIN" — so by construction it never measured the ISIN-matched OOW actions the plan's
union-wide gate also drops.

**Fix (pick one; (a) is cleanest):**
- **(a) Scope the window gate to the symbol-added subset only.** An action that matches by **substrate ISIN** is
  by definition the stock's own corporate event and must NOT be window-dropped — it should always apply
  (subject to the existing price-validation). Apply the date-window guard ONLY to actions reached via
  `by_symbol` that are NOT also in `by_isin[substrate-ISIN]`. This precisely targets symbol-reuse and leaves the
  26 legitimate ISIN-matched pre-coverage splits intact. (This matches the join-strategy doc's own framing,
  which counted exactly the symbol-added subset.)
- **(b) Define the window as the security's trading LIFE, not the price-file coverage** — i.e.
  `[min(listing_date, first_trade) − slack, last_trade]`. This keeps post-listing pre-coverage splits in-window.
  Weaker than (a): it still drops a legit symbol-matched listing-era split if listing_date is missing (699
  substrate rows have no symbol and many longterm rows have no listing_date), and it does not distinguish
  ISIN-matched from symbol-matched.
- Either way, **add a test**: a stock listed pre-coverage with an ISIN-matched post-listing split before
  `first_trade` keeps the split applied (`adj_issue` divided correctly); assert ATLANTAA-style adj_issue and
  outcome label are unchanged by the patch.

### D1-F2 (MEDIUM — correctness flaw / internal inconsistency) — gating only inside `load_prices` desynchronizes the price series from `adj_factor_after` (issue + terminal)

**Where:** plan Task 4 Step 6 + final-verify N1/N2 ("apply the window gate INSIDE the consumed helper … inside
`load_prices`"). `07:206-235` (`load_prices`) vs `07:239-246` (`adj_factor_after`).

**What's wrong.** The `actions` list returned by `actions_for` (07:114-127, lacks the price window) feeds **three**
independent consumers, not one:
1. `load_prices(isin, actions)` — adjusts the price SERIES (07:600/631).
2. `adj_factor_after(actions, listing_date)` — adjusts `issue_price → adj_issue` (07:438).
3. `adj_factor_after(actions, ref_dt)` — adjusts the delisting `last_price → terminal` (07:270).

The final-verify doc's recommended locus ("filter inside `load_prices`") fixes only consumer #1. Consumers #2
and #3 would still see the **unfiltered** actions list → the price series would be window-gated while
`adj_issue`/terminal are computed with the un-gated factor. For any stock with a dropped OOW action, that is an
internal scale mismatch (series on one factor, issue/terminal on another) → wrong returns even for the rows the
gate is supposed to "fix."

**Fix.** Filter the `actions` list to the window **once, at the point prices and actions meet** — at the two
call sites (07:599-600 and 07:630-631): read the window from the loaded/sorted prices, filter the list, then
pass the **same filtered list** to BOTH `load_prices` and `compute()` (so `adj_factor_after` inside `compute`
sees it too). Equivalently, do the read+filter inside a small wrapper and have `compute` receive only windowed
actions. The plan must state that the filtered list is the single source for series-adjustment AND
issue/terminal adjustment — "wire into `load_prices`" alone is insufficient. (This finding compounds D1-F1: if
F1 is fixed by scoping to symbol-added, F2 still applies to whatever subset IS dropped.)

### D1-M1 (MEDIUM — test/safety gap) — full anti-join byte-identity (F6) breaks the moment new flag columns are added

**Where:** plan Task 6 (adds `corp_action_unresolved` / `corp_action_out_of_window` /
`corp_action_envelope_violation`) + Task 8 Step 2/4 + Task 11(d) (the full anti-join gate).

**What's wrong.** The current substrate has NO `corp_action_*` columns (verified: flag-ish columns are only
`liquidity_flag`, `data_quality_tier`, `xcheck_flags`). Task 6 introduces them as NEW columns. Adding a column
re-serializes **every** row (a new trailing/empty cell), so a literal "every non-corp-action ISIN is
byte-identical to the snapshot" anti-join would **fail trivially for all 2384 rows** — masking real regressions
and giving a false red, or tempting the implementer to weaken the gate.

**Fix.** Define the anti-join over the **intersection of pre-existing columns** (compare each non-corp-action row
restricted to the snapshot's column set), not the raw serialized line. State that the new flag columns are
expected to be empty on every non-corp-action row and are excluded from the byte-identity comparison. (R5
already lists which `substrate_meta.json` fields move; extend it to name the new columns explicitly.)

### D1-N1 (NIT — test gap) — no test pins the compound same-day split+bonus (bucket 3) when the gap IS in coverage

**Where:** Task 4 reconcile "collapse duplicates that map to the same gap."
ISHAN (`INE0LCW01025`): same-day (2024-01-25) 10:1 split + 2:1 bonus, product 30, price gap 28.56× — both legs
legitimate, must be KEPT. They survive the `(ex_date, ratio_factor)` dedup because the ratios differ (10.0 vs
3.0). But the new reconcile matches events to a single observed gap; a naive "one event per gap" collapse could
drop one leg (28.56× ≈ one 30× event). Current substrate is correct (adj 2.667 = 80/30). Add a Task-4 test:
two same-day, different-`action_type` legs whose PRODUCT matches the gap are BOTH retained (not collapsed to
one). Without it, the reconcile could regress the 18 compound `ratio-conflict` evidence cases.

### D1-N2 (NIT — already flagged, restated for completeness) — trading-day-indexed window is load-bearing for suspension cases

KAUSHALYA's price file has **no rows between 2024-01-11 and 2024-02-06** (a ~3.5-week suspension around the
consolidation), so the actual gap (9.85→988.3) is the FIRST trading row at/after the ex_date. A
**calendar-day** window would miss it; the **trading-day-indexed** window (`bisect` to first index ≥ ex_date,
scan ±window positions) catches it. The plan/Task 2 already specify trading-day indexing (good) — this note just
confirms it is correct AND essential, and that Task 1's `observed_max_gap` MUST reuse the same `detect_gap`
(R4) so the two never diverge on a suspension boundary.

---

## Cross-cutting checks (the four the kickoff asked for)

**Tests validate for the RIGHT reason.** Confirmed fail-first on the live tree:
`test_compulsory_delisting_forces_minus_100` FAILS today at line 110 (`mae_1y` = 0.15, expects −1.0); lines
106/107 (terminal) PASS — so Task 7's MFE/MAE-block scoping is correct. Baseline = **12 failures** (T-2 reach +
envelope, T-3 weights, T-4 synthetic, T-5 thinktank) — confirmed. Task 1's red baseline keys on
`INE645S01024`+`ROLEXRINGS` (price file exists, real 19.96× gap, product 1000) → flags for the right reason
(the prior `INE645S01016` spurious-pass regression is fully reversed). **Coverage gaps:** buckets 3 (compound,
D1-N1) and 5-legit (pre-coverage, D1-F1) have NO test.

**Confidence invariant airtight?** Mostly. The three value-writing paths (auto-derived factor, override table,
genuine-wipeout −100%) each gate on confidence; the override contradiction guard closes the §6 back-door
(verified ROLEXRINGS is a genuine price-vs-web conflict, branch (b)). **One leak via D1-F1/F2:** a stock whose
legitimate ISIN-matched split is wrongly dropped gets a CONFIDENTLY-WRONG (not flagged) value — the gate
silently changes `adj_issue` without routing the row to flag+null, so a guessed-wrong value reaches a row the
system believes it resolved. Fixing D1-F1 closes this.

**Targeted-patch safety.** Anti-join + inventory gate (incl. `manual_overrides.csv` at 09:98-112, verified) +
reuse of `07.compute` are correct in design. **But** (a) D1-M1 (new columns break byte-identity), and (b) the
patch set "symbol-OR-ISIN with ≥1 in-window event" INCLUDES the 26 D1-F1 stocks, so the patch is the vector
that injects the F1 regression. Both must be resolved before the patch is trusted.

**No double-jeopardy?** The three guards interact cleanly: out-of-window (cause-side, drops before
`load_prices`), continuity (single-day jump, flag-only), envelope tripwire (`trough ≤ endpoint ≤ peak`,
flag-only). A row flagged by one is routed to the same dynamic unresolved set (Task 6) and flag+nulled once —
no conflicting handling. The envelope tripwire correctly never clamps (T-4 decision (c) part 2). ✅

---

## Confirmed sound (carried from prior rounds, re-verified live)
- ROLEXRINGS +15,272% / NPST +16,127% / KAUSHALYA 100.34× gap / ISHAN 30× — all reproduced on disk.
- Evidence CSV: 53 rows, verdicts 28 apply-once / 17 correct-ratio / 2 reverse-direction / 6 STAYS-FLAGGED;
  the 6 named match exactly; ROLEXRINGS row is a genuine coverage-hole/price-vs-web conflict.
- All line-refs accurate: `07` 91/114/206/239/306/424 + two `actions_for` call sites 599+630; `09` has_action
  (ISIN∪symbol) at 88, skip at 89, manual_overrides 98-112; synthetic test 106/110; substrate test 103 (≥30).
- F1–F6, R1–R5, N1–N3 from prior rounds: all correctly applied. The detector is direction-normalized; PATANJALI
  removed as a guardrail; override guard wired; NPST out of the magnitude parametrize; anti-join is full.

---

## Recommended pre-implementation edits (ordered)
1. **D1-F1 (HIGH)** — scope the date-window gate to the **symbol-added subset only** (or define the window as
   the security's trading life), so the 26 legitimate ISIN-matched post-listing pre-coverage splits stay
   applied; add a pre-coverage-split regression test (ATLANTAA winner-stays-winner, TARIL multibagger intact).
2. **D1-F2 (MEDIUM)** — filter the `actions` list at the call-site (07:599-600/630-631) and pass the SAME
   windowed list to both `load_prices` AND `compute`, so `adj_factor_after` (issue + terminal) cannot desync
   from the series adjustment.
3. **D1-M1 (MEDIUM)** — make the full anti-join compare over the snapshot's pre-existing column set (new flag
   columns excluded / asserted empty on non-corp-action rows), so adding columns doesn't false-fail the gate.
4. **D1-N1 (NIT)** — add a Task-4 test that same-day, different-type compound legs (ISHAN) are BOTH retained.
5. **D1-N2 (NIT)** — keep the trading-day-indexed window + the single shared `detect_gap` (already specified);
   note the KAUSHALYA-suspension reliance so it isn't "simplified" to calendar days during build.

**Bottom line:** the fix is the right shape and kills the headline bug, but the window gate is over-scoped and
mis-located in a way that would corrupt ~26 legitimate long-term stocks and desync the issue-price adjustment.
**Not execution-ready until D1-F1 + D1-F2 are folded in** (both are plan-text edits, no design rethink). With
those two fixed (and the M1/N1 test gaps closed), the design is correct, safe, and adequately tested end-to-end.
