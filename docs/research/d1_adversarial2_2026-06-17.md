# D-1 Adversarial Pass #2 — FRESH attack surfaces (2026-06-17)

**Role:** second, independent adversarial pass on the converged D-1 plan
(`docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`, state-log R1–R10), with a fresh attack
focus the first pass (`d1_adversarial_2026-06-17.md`, which found the orphaned-validation break → fixed by
R9 remedy (a)) did NOT cover. READ-ONLY. Every claim verified against
`data/reference/corp_actions_merged.csv`, `data/master/ipo_analysis.csv`, `data/prices/`,
`pipeline/07_returns_summary.py`.

## VERDICT: **EDGE-CASE-FOUND** — one HIGH break (B1, genuine small bonuses wrongly phantom-dropped), one MEDIUM break (B2, coverage-END-boundary ambiguity), plus surfaces 1/2/4 CLEAN.

The R9 remedy (a) per-action price-validation (Step 6b) is the right architecture and closes the in-window
double-count class the first pass found. But it leans entirely on `detect_gap` to classify each admitted
action, and `detect_gap`'s **1.5× noise floor + the three-way overload of its `None` return** create two new
break classes the plan's decision tree does not resolve. Both reach the substrate via the same `07`-call-site
path the first pass exposed.

---

## SURFACE 1 — Action TYPE confusion (bonus / split / dividend / face-value / rights) — **CLEAN**

**Why covered (verified):** `load_corp_actions` (`07:91-111`) reads ONLY `ratio_factor` + `ex_date`; it never
branches on `action_type`. The merged file has exactly three `action_type` values — `split` (1053),
`bonus` (813), `bonus+split` (31) — and **NO `dividend` or `rights` action_type at all**. For the factor math
a bonus and a same-ratio split are intentionally identical (both halve the price → same gap → same factor),
so the semantic difference is irrelevant to detection AND to the fix; nothing in the plan or `07` needs to
tell them apart.

- **Dividends cannot be mis-read as splits:** 0 PURE-dividend rows exist (every row with "dividend" in
  `raw_subject` is a bonus/split that *also* declared a dividend — e.g. `ALPSINDUS Dividend-7.50% /Bonus 1:1`
  → `ratio_factor=2.0`, the dividend ignored; `BPCL .../Dividend Rs 11/-/Bonus 1:1` → 2.0). The `ratio_factor`
  correctly captures only the bonus/split leg. A large special dividend therefore never enters as a factor
  event, and `detect_gap` is only ever called on rows that already carry a split/bonus ratio — it cannot
  "discover" a dividend drop and mistake it for a split.
- **Rights:** exactly 1 row mentions rights (`LAKSHVILAS Bonus 1:2/Rights 1:1` rf=1.5) and it is recorded as
  the bonus leg only — no rights ratio is ever applied.

**Caveat (LOW, data-quality, NOT a plan break):** `DWARKESH` (`INE366A01033`) is a genuine Rs10→Re1
face-value split mis-recorded as `ratio_factor=1.0` (factor never extracted). This is an UNDER-count, not the
over-count the plan targets; and DWARKESH is not in the substrate (no price file), so it is inert. Note it for
TODO-D1 data-quality, not for this build.

---

## SURFACE 2 — Face-value-change ISIN events (Rs10→Re1, ISIN changes) — **CLEAN**

**Why covered (verified):** the substrate is keyed on the post-change (current) ISIN, whose price file
exists; the corp-action row may carry the OLD ISIN. The `actions_for` symbol∪substrate-ISIN union
(`07:114-127`) recovers it via the NSE symbol — exactly the case the join key was designed for, and the gap
(measured on the post-change price file the substrate points at) validates the factor. I traced the compound
face-value-split cases (`bonus+split`, e.g. `BAJFINANCE Bonus 1:1/FV Split Rs10→Rs2` rf=10.0,
`DPSCLTD Bonus 22:1 + FV Rs10→Re1` rf=230.0): the combined `ratio_factor` is already the product, the price
gap measures the same product, so price-validation accepts it as one event. No mis-attribution found where an
old-ISIN FV-change failed to reach its post-change price file via the symbol join.

---

## SURFACE 3 — Multi-corp-action stocks (≥3 events) — **partly CLEAN, surfaces B1/B2 below**

**Population (verified):** 59 substrate stocks carry ≥3 union actions; 25 of them have ≥3 *admitted* events.
Highest cumulative products: ROLEXRINGS 1000 (the seeded case), FCL/DHARAN 100, AEPL 87.78, SIKKO 60,
RAJMET/SBC 45, HARDWYN 28. I traced each high-product 3+-event stock's per-event price gap.

**The genuine multi-event compounds are CLEAN under the design:** FCL (2015 2× + 2015 5× + 2025 combined 10×,
each gap-supported), ASTRAL, PERSISTENT, NBCC, KSOLVES etc. each gap-validate per ex-date, and the
**same-day different-ratio compound** legs (D1-N1 class) are confirmed real and kept: `SBC` 2022-02-22 rf=2 + rf=10
→ product 20 vs gap 19.0; `HARDWYN` 2023-06-05 rf=1.333 + rf=10 → 13.3 vs gap 12.2; `FCL` 2025-10-31 rf=2 + rf=5
→ 10 vs gap 13.0. The "collapse same-ratio legs to one gap BUT keep compound legs whose PRODUCT matches the gap"
rule (Task 4 Step 4 / Step 6b) is correct for these.

**But three high-product 3+-event stocks expose the two break classes (B1/B2):** `DHARAN`, `AEPL`,
`E2E`, `LTFOODS`, `FORGE` all carry a large ISIN-matched split with a **flat / unmeasurable** price gap that
is currently applied to `adj_issue`. These are detailed as B1/B2.

---

## BREAK B1 (HIGH — would corrupt data) — genuine SMALL bonuses (rf 1.1–1.5) are below `detect_gap`'s 1.5× noise floor → wrongly PHANTOM-DROPPED

### Mechanism
The plan pins `detect_gap`'s noise floor at **1.5×** (Task 2 Step 3, verbatim: *"`None` if no ratio exceeds a
noise threshold (e.g. 1.5×)"*). A genuine **5:4 bonus (rf=1.25)**, **6:5 (rf=1.2)**, **4:3 (rf=1.333)** or
**11:10 (rf=1.1)** produces a real price gap of ~1.2–1.4×, which is **below 1.5×** → `detect_gap` returns
`None`. In the Step 6b decision tree a `None` with **price present around the ex-date** is classified
**PHANTOM → DROP + flag `corp_action_no_price_gap`** → the row is routed to the unresolved set and flag+nulled
(Confidence Invariant). So a perfectly legitimate small bonus is dropped, and the whole stock's outcome
columns are nulled.

### Scale (verified)
- **350 events** in the merged file have `1.0 < rf ≤ 1.5` (141 at exactly 1.5; ~209 strictly below).
- Restricting to **ISIN-matched, in-window events whose actual price gap MATCHES the claimed small ratio but
  is < 1.5×** (i.e. unambiguously genuine, yet below the floor): **23 substrate stocks**, including large,
  popular names:

| Stock | ISIN | ex_date | claimed rf | measured gap |
|---|---|---|---|---|
| **POWERGRID** | INE752E01010 | 2023-09-12 | 1.333 | 1.383 |
| **POWERGRID** | INE752E01010 | 2021-07-29 | 1.333 | 1.363 |
| **RECLTD** | INE020B01018 | 2022-08-17 | 1.333 | 1.302 |
| **PFC** | INE134E01011 | 2023-09-21 | 1.25 | 1.249 |
| **RITES** | INE320J01015 | 2019-08-08 | 1.25 | 1.261 |
| **OIL** | INE274J01014 | 2017-01-12 | 1.333 | 1.398 |
| **NTPC** | INE733E01010 | 2019-03-19 | 1.2 | 1.177 |
| **ECLERX** | INE738I01010 | 2015-12-17 | 1.333 | 1.306 |
| (… 15 more: OMAXE, BIRLACOT, JAGRAN, RUCHIRA, LIBAS×2, UEL, ORIENTTECH, TULSI, PRADIP, DPWIRES, …) | | | | |

These are real corporate events with a matching gap, yet the 1.5× floor classifies each as "no gap." For a
stock whose ONLY (or last-remaining) admitted event is such a bonus, the gap-less drop nulls its returns; for
multi-event stocks (POWERGRID, RECLTD, etc.) it under-counts the cumulative factor → inflates `adj_issue` →
**deflates** every return, the mirror of the over-count bug the fix is trying to kill.

### Why the first pass missed it
The first pass concluded (its §5) that "Detector thresholds (>5× / log-5 for magnitude; ~1.5× noise floor for
gaps) look correctly placed for the cases inspected" — but it only inspected the *phantom* legs (gaps ~1.0,
far below the floor, correctly rejected). It never tested a **genuine** event whose true gap sits in the
1.0–1.5 band. That band is exactly where 209 real small bonuses live.

### Root cause + severity
`detect_gap` overloads `None` to mean three different things — *genuine-but-small*, *true-phantom-flat*, and
*coverage-missing* — and the Step 6b tree only discriminates "price present vs missing," which cannot separate
the first two. **Severity HIGH:** corrupts factors/returns on large-cap, popular stocks (POWERGRID, NTPC,
PFC, RECLTD, OIL) and can null otherwise-clean rows.

### Minimum remedy (for the converge team, not implemented here)
Make the small-ratio acceptance **ratio-aware, not a single magnitude floor**: accept an admitted event if the
measured gap is within tolerance of the *claimed* ratio (e.g. `|log(gap) − log(rf_effective)| < log(1.25)`),
regardless of whether the gap clears an absolute 1.5×. Reserve the absolute floor only for the *phantom*
verdict (claimed rf ≫ 1.5 but gap ≈ 1.0). Add a test pinning POWERGRID/PFC small-bonus = APPLIED (not dropped).

---

## BREAK B2 (MEDIUM — would corrupt data) — phantom-vs-coverage-hole is undecidable at the COVERAGE-END boundary (ex_date after the last price)

### Mechanism
Step 6b's load-bearing safety is the distinction *"no gap because phantom (closes present around ex, no jump
→ DROP)"* vs *"no gap because data missing (coverage hole → defer to override / flag-unresolved, never
drop)."* The discriminator is "are there closes around the ex-date." This is well-defined for an INTERIOR
hole (ROLEXRINGS' 15-month gap has closes on BOTH sides → index-adjacent pair → a real ~20× gap). It is
**undecidable when the ex_date falls AFTER the price series ends** — there are closes *before* ex but NONE
at/after, so there is no adjacent pair to measure and no way to tell a real post-coverage split from a
phantom one.

### Scale (verified) — 6 ISIN-matched rf>1.3 events with `ex_date > last_trade`:

| Stock | ISIN | ex_date | coverage end | rf | current adj_issue | current class |
|---|---|---|---|---|---|---|
| **E2E** | INE255Z01019 | 2026-06-05 | 2026-06-04 | 10.0 | 5.7 | **multibagger (+74.7×)** |
| **LEMERITE** | INE0G1L01017 | 2026-05-29 | 2026-05-27 | 5.0 | 15.0 | **multibagger (+1.67×)** |
| **FORGE** | INE319Y01016 | 2021-10-07 | 2018-01-12 (3.5 yr gap) | 5.0 (+1.75) | 3.31 | **multibagger (+1.41×)** |
| **IVRPRIME** | INE414I01018 | 2010-05-20 | 2010-04-12 | 1.5 | 366.7 | loser |
| **INE224B01024** | — | 2009-04-24 | 2006-04-26 | 10.0 | 3.5 | flat |
| **INE0E4I01027** | — | 2025-02-14 | 2025-02-14 | 10.0 | 2.6 | (null) |

The outcome flips on a coin-toss the plan does not call:
- If E2E's `ex=2026-06-05` (one day past the last close 2026-06-04) is read as **coverage-hole → defer to
  override → no override → flag-unresolved**, E2E loses its multibagger label and is nulled.
- If read as **phantom → drop the rf=10**, adj_issue becomes 57, return ≈ +6.5×, and E2E **stays** a
  multibagger (correct magnitude).

These two are materially different and the plan's decision tree (Task 4 Step 6b / Step 4) specifies only
"price present vs missing" — it never addresses "ex_date beyond the coverage END," where closes are present
*before* but absent *at/after*. FORGE is the starkest: a 5× factor applied at an ex-date **3.5 years after**
its 63-row price series ends, carrying a multibagger label, with no way to gap-validate.

### Severity
MEDIUM: 6 stocks, several carrying multibagger/extreme labels; the ambiguity means the build could go either
way and both branches are defensible-looking, so it is a latent correctness hazard, not a guaranteed
corruption. (It is lower than B1 only because the population is small and several rows may legitimately route
to flag+null.)

### Minimum remedy
Add an explicit 5th decision-tree branch for **ex_date strictly after `last_trade` (or before `first_trade`
with no prior close)** = *gap unmeasurable at this boundary* → treat as coverage-hole (defer to override; else
flag-unresolved) — NEVER silently apply the un-validated factor (current behaviour) and never silently
phantom-drop. Pin E2E + FORGE as tests. Note this is adjacent to, but distinct from, R10's NIT-1 (which
covered "gap PRESENT but wrong ratio"); B2 is "gap NOT MEASURABLE because ex is past coverage."

---

## SURFACE 4 — same-ratio legs that are NOT the same event (must NOT collapse) — **CLEAN**

**Why covered (verified):** 29 substrate stocks have ≥2 same-ratio (≥2×) events >180 days apart
(PERSISTENT two 2:1 splits 9 yr apart, ASTRAL 4 yr, KSOLVES 3.4 yr, NMDC 16.6 yr, etc.). The collapse rule is
keyed on the **price GAP**, not the ratio: I confirmed each distant same-ratio event has its OWN distinct gap
— PERSISTENT (2.20 @2015, 2.03 @2024), ASTRAL (1.91 @2010, 2.10 @2014), KSOLVES (1.94 @2021, 2.28 @2025). Two
genuine 2:1 splits map to two separate gaps → kept separate, not collapsed. The collapse only fires when
multiple same-ratio legs map to a SINGLE gap (the CANTABIL/GNA double-count), which is exactly the intended
behaviour. **One caveat that B1 already captures:** the damped/illiquid-fill sub-case the surface flags ("a
real split whose gap is below threshold") IS real — but it manifests as the genuine-small-bonus band of B1
(gap < 1.5 floor), not as a same-ratio collapse error. Folded into B1.

---

## SURFACE 5 — detect_gap threshold robustness (small-ratio near noise) — **EDGE-CASE = B1**

This surface IS the B1 break. The 1.5× noise floor cannot accommodate the 209 genuine small bonuses
(rf 1.1–1.4) whose true gaps fall in the 1.0–1.5 band. See B1 for the verified list and remedy. A legit small
bonus IS lost under the current threshold spec.

---

## Bottom line
The R9 remedy-(a) architecture (per-action price-validation at the `07` call site) is sound and closes the
first pass's in-window double-count class. Surfaces 1, 2 and 4 are genuinely clean (action-type is ignored by
the factor math; FV-change ISINs are recovered by the symbol join; distant same-ratio events are kept by
gap-keyed collapse). But the validation's reliance on a single **1.5× absolute noise floor** plus the
**three-way overload of `detect_gap`'s `None`** opens two new break classes that reach the substrate via the
same `07` path:

- **B1 (HIGH):** 23 genuine small bonuses (POWERGRID, NTPC, PFC, RECLTD, RITES, OIL, …) sit below the 1.5×
  floor → wrongly phantom-dropped/under-counted → returns corrupted or rows nulled. Fix: make small-ratio
  acceptance **ratio-aware** (gap-matches-claimed-ratio), not a single absolute floor.
- **B2 (MEDIUM):** 6 ISIN-matched events with `ex_date > last_trade` (E2E, LEMERITE, FORGE, …) hit an
  undecidable phantom-vs-coverage-hole boundary the decision tree doesn't specify; the build could null real
  multibaggers or keep un-validated factors. Fix: an explicit "ex beyond coverage boundary → coverage-hole
  branch" rule + tests.

**Recommendation: fold B1 (and the B2 boundary rule) into Task 2/Task 4 before build.** Both are concrete,
data-verified, reach the substrate, and are not covered by any prior round (R1–R10) or the first adversarial
pass.
