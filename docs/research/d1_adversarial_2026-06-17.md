# D-1 Adversarial Edge-Case Review — last pre-build gate (2026-06-17)

**Role:** actively try to BREAK the converged D-1 plan (`docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`,
state-log R1–R7). READ-ONLY. Every claim below is verified against `data/reference/corp_actions_merged.csv`,
`data/master/ipo_analysis.csv`, `data/prices/`, and `pipeline/07_returns_summary.py`.

## VERDICT: **EDGE-CASE-FOUND** — one HIGH break (would corrupt data), plus medium/low notes.

The plan's design is sound for *symbol-reuse / wrong-era* leaks (the gate fixes those) and for *direction*
(direction-normalized detector). But it has a **structural gap that lets a whole class of over-counts survive into
the patched substrate**: the price-validation that disposes of phantom / same-event-double-counted actions lives ONLY
in the reconcile (`03k`/`03l`, Task 4), which the plan itself declares DAG-orphan and **does not reach the substrate**.
The substrate is reached only by Task 8's patch, which reuses `07`'s `compute()`/`load_prices` — and `07` applies the
**window gate ONLY, with NO price-validation**. Any phantom/duplicate action that is *in-window* therefore survives.

---

## BREAK (HIGH — would-corrupt-data): same-event / phantom in-window actions are NOT price-disposed in the substrate path

### The mechanism
- `07:99` `load_corp_actions()` reads `data/reference/corp_actions_merged.csv` directly.
- `07`'s apply path (`load_prices` 206-235, `adj_factor_after` 239-246) multiplies **every admitted ratio_factor** —
  there is **no gap check** in `07`.
- The converged gate (Task 4 Step 6) only filters the **out-of-window symbol-added** subset. In-window actions —
  including phantom duplicates — are all admitted and multiplied.
- Task 4's price-validated reconcile (the part that would drop a phantom "claimed but price never moved" leg, and
  collapse a same-event double-count) is in `03k`/`03l`. The plan's own DAG note (Task 4) + Task 8 Step 3 state these
  are orphaned and **do NOT regenerate `corp_actions_merged.csv`** in any runnable chain; Task 8 patches by reusing
  `07`'s compute path against the **unchanged** merged CSV.
- **Net:** the only corp-action correction that reaches the substrate is the symbol-added window gate. Phantom and
  same-event double-counts that are *in-window* are untouched. The price-validation that the spec's "price disposes"
  principle promises never executes on the substrate.

### Concrete failing stocks (verified, in-window, double-counted, NOT in the plan's known-offender list)

The classic pattern: **yfinance and NSE record the SAME real split a few days/weeks apart** → two near-identical
legs, both inside the trading window → factor squared. (This is exactly the "NPST count-conflict" class the plan says
is "caught by the reconcile dedup" — but the reconcile never reaches the substrate.)

| Stock | ISIN | merged actions (symbol-added, both in-window) | real event | applied factor | correct factor | substrate adj_issue | substrate return / class | correct return |
|---|---|---|---|---|---|---|---|---|
| **CANTABIL** | INE068L01024 | 5.0 @2023-10-20 (yfinance, **gap 1.01 = phantom**) + 5.0 @2023-11-02 (NSE, gap≈5×, real) | one 5:1 | **25** | 5 | **5.4** (=135/25) | **39.68× multibagger** | **7.14×** |
| **VISHWARAJ** | INE430N01022 | 5.0 @2021-09-08 (yfinance, phantom) + 5.0 @2021-10-21 (NSE, real) | one 5:1 | **25** | 5 | 2.4 (=60/25) | 1.36× multibagger | ~5.9× |
| **GICL** | INE947T01022 | 1.25 + 2.0 @2022-08-19 (yf) + 2.0 @2022-10-12 (NSE, dup) + 2.0 @2025 | dup 2:1 | over by 2× | — | 2.4 | 9.48× multibagger | ~4.7× |
| **PAVNAIND** | INE07S101038 | 2.0 @2022-08-17 (yf) + 2.0 @2022-09-05 (NSE, dup) + 10.0 @2025 | dup 2:1 | over by 2× | — | 4.125 | 2.97× multibagger | ~1.0× |
| **GNA** | INE934S01014 | 2.0 @2023-08-11 (**gap 1.003 = phantom**) + 2.0 @2023-09-01 (ISIN-matched, gap≈2×, real) | one 2:1 | **4** | 2 | **51.75** (=207/4) | **6.39× multibagger** | **2.70×** |
| **RPEL** | INE912T01018 | 2.0 @2024-11-14 (**gap 1.007 = phantom**) + 2.0 @2024-11-29 (ISIN-matched, real) | one 2:1 | **4** | 2 | 9.75 (=39/4) | (currently null) | — |
| **KNRCON** | INE634I01029 | 5.0 @2016-12-12 (yfinance, **gap 1.02 = phantom**) + 2.0 @2021-02-03 (NSE, real) | one 2:1(+?) | over by 5× | — | 17.0 (=170/10) | 6.67× multibagger | ~tripled |

Calibration check (the plan's own anchor): **ROLEXRINGS** (the known +15,272% case) sits in the SAME failing class
(3× counted 10:1 → factor 1000), and is only fixed by the **override table** (Task 3) — NOT by the window gate
(all three ROLEXRINGS legs are in-window). The above stocks have **no override entry** and are **not in the
Wave-1 STAYS-FLAGGED 6**, so nothing in the plan touches them. They will keep their inflated factors after the patch.

### Numeric proof of the corruption (verified)
```
GNA      current_price 382.55: over-counted adj 207/4=51.75 -> return 6.392 ; correct 207/2=103.5 -> 2.696
CANTABIL current_price 219.65: over-counted adj 135/25=5.4 -> return 39.676 ; correct 135/5=27.0 -> 7.135
```
GNA's return is overstated 2.4×; CANTABIL's is overstated 5.6× — both keep a `multibagger` label that is real in
direction but wrong in magnitude (and feeds the descriptive findings + the data-informed weights).

### Why the envelope tripwire (Task 5b) does NOT catch it (verified)
A uniform extra post-listing factor divides `adj_issue` and the post-event price extremes by the SAME constant, so
`trough ≤ endpoint ≤ peak` ordering is **preserved**. The tripwire is a consistency check, not a magnitude check —
it is provably blind to a self-consistent over-count. Confirmed numerically: GNA/CANTABIL satisfy the envelope while
being 2.4×/5.6× wrong.

### Blast radius
- **13 substrate rows** carry a same-ratio near-duplicate (within 21 days, <2% ratio diff) among their *admitted*
  (in-window) actions: ROLEXRINGS, NAZARA, NPST, PAVNAIND, CLOUD, USASEEDS, DIGIKORE, MOS, GPIL, CANTABIL, GNA, RPEL,
  Ranjeet Mechatronics. Of these, ROLEXRINGS+NPST are the only ones the plan addresses.
- Broadening to **any in-window symbol-added event claiming a split (rf>1.05) with no supporting price gap (<1.3×)**
  yields **59 events across ~50 stocks** (many small bonuses are benign/ambiguous, but the high-magnitude ones —
  ASIANTILES 5.0/gap1.01, CANTABIL 5.0, VISHWARAJ 5.0, KNRCON 5.0, PAVNAIND 2.0, GICL 2.0, GNA 2.0, RPEL 2.0 — are
  unambiguous over-counts). This is materially larger than the named offenders.

### Severity: **HIGH.** Corrupts return/multibagger labels on real, popular stocks; survives every guard in the plan
(gate keeps in-window, envelope is blind, override only seeds named stocks, reconcile is orphaned). The fix's headline
promise — "price disposes" — does not actually run on the substrate for the in-window phantom class.

### Minimum remedy (for the converge team, not implemented here)
Either (a) make Task 8's substrate-reaching path apply **price-validation per admitted action** (reuse
`pipeline.price_gap.detect_gap` from Task 2 at the `07` call site: drop/flag an admitted leg whose claimed ratio has
no supporting index-adjacent gap, with same-event collapse), OR (b) make `03k`/`03l` regenerate
`corp_actions_merged.csv` and have Task 8 consume the reconciled file — closing the orphan so the price-validation
reaches the substrate. Without one of these, the gate alone cannot deliver "price disposes."

---

## Attack-surface-by-surface

**1. Mixed ISIN-matched + symbol-added (per-action scoping).** CLEAN *as designed* (the gate correctly keeps
ISIN-matched, window-tests only symbol-added) BUT it surfaces the HIGH break: of the 13 mixed stocks, **GNA, RPEL,
AARON** have an in-window symbol-added leg that *duplicates* a real ISIN-matched/other split. The gate keeps both →
double-count. Scoping is right; price-disposal is missing on the substrate path (see HIGH break).

**2. Multi-event / same-day legs.** Mostly CLEAN. The compound same-day split+bonus case (ISHAN class, D1-N1) is
explicitly preserved by the plan's "keep distinct legs whose product matches the gap." The break is the *opposite*
problem (legs that should collapse but don't, because collapse lives in the orphaned reconcile) — covered in the
HIGH break. AARON (INE721Z01010): 2020-09-03 rf=1.909 is real (54→30); 2019-08-29 rf=1.1 has no gap (small, ambiguous,
low severity).

**3. Pre-listing slack.** CLEAN. Empirically **zero** symbol-added events fall in the
`[first_trade − 10d, first_trade)` slack zone across the whole dataset, and zero legitimate just-before-listing splits
are at risk of being dropped. The slack's blast radius is effectively nil on current data — neither admits a wrong-era
action nor drops a legit one. (If the slack is widened later, re-test.)

**4. Borderline gaps.** Partially exposed by the HIGH break: the phantom legs (GNA gap 1.003, RPEL 1.007, CANTABIL
1.01, ASIANTILES 1.01) sit far BELOW any sane noise threshold — a price-validator WOULD reject them cleanly. The
problem is not detector calibration; it is that no validator runs on the substrate path. Detector thresholds
(>5× / log-5 for magnitude; ~1.5× noise floor for gaps) look correctly placed for the cases inspected.

**5. Direction edge cases (reverse vs bonus vs split).** CLEAN for the named cases. KAUSHALYA (rf=0.01, real ~100×
reverse, in-window) and CMMIPL are handled by direction-normalization. Two additional in-window symbol-added reverse
legs exist — **MANINFRA** (INE949H01023, rf=0.135 @2014-08-28; substrate adj 1244 vs issue 252, return −90.8%
wipeout) and **VERTOZ** (rf=0.1 @2025-06-25) — these warrant a spot-check during build (reverse + possible
multi-source duplication), but direction handling itself is sound.

**6. Flag co-occurrence / cascade.** CLEAN on the design (Task 6 builds the unresolved set as a UNION of all flag
sources, so a row with two flags is handled once). No cascade issue found. Caveat: the HIGH-break stocks (GNA,
CANTABIL, …) raise **NO** flag at all (in-window, envelope-consistent) → they are never routed to the unresolved set
→ they silently keep wrong values. The gap is *under*-flagging, not flag overlap.

**7. Coverage holes / index-adjacent window.** CLEAN for the calibration cases (ROLEXRINGS 15-month hole, KAUSHALYA
~3.5-week suspension are exactly what the series-index-adjacent window measures, and the plan forbids a calendar
filter). No additional coverage-hole stock found that the index-adjacent window mis-measures. (This surface only
matters for the detector/reconcile, which — per the HIGH break — don't run on the substrate anyway.)

**8. Diverse trace (8 stocks, end-to-end through the patch path):**
- **ROLEXRINGS** (override) → fixed via Task 3 override. OK.
- **KAUSHALYA** (reverse, in-window) → direction-normalized, unchanged. OK.
- **ATLANTAA / TARIL** (ISIN-matched pre-coverage split) → always-apply, stay winners. OK (D1-F1 guard holds).
- **GNA** (forward split + phantom dup, in-window) → **BREAK**: factor 4, return 6.39 (should be 2.70).
- **CANTABIL** (yfinance+NSE same 5:1, in-window) → **BREAK**: factor 25, return 39.7 (should be 7.1).
- **RPEL** (phantom dup, in-window) → **BREAK**: factor 4 (currently null, but adj_issue 9.75 vs correct 19.5).
- **MANINFRA** (old MB, reverse + possible dup) → needs build-time spot-check.

---

## Bottom line
The plan correctly fixes the **symbol-reuse / wrong-era** leak (the gate) and **direction** (normalization), and the
D1-F1 always-apply guard protects the legit pre-coverage splits. But the **"price disposes" promise does not reach the
substrate** because the price-validating reconcile is DAG-orphaned and the only substrate path (Task 8 → `07` compute)
applies the window gate with no gap check. This lets **in-window phantom / same-event double-counts** (CANTABIL, GNA,
RPEL, VISHWARAJ, GICL, PAVNAIND, KNRCON, ASIANTILES, … — at least 13 strict, ~tens broad) survive with inflated
returns and spurious magnitude on multibagger labels — invisible to the envelope tripwire (provably blind to uniform
over-count) and to the override table (named seeds only). **Recommend: close the orphan or add per-action
price-validation to the substrate-reaching path BEFORE build.**
