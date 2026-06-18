# 01 — Phase 1 provenance: bucket counts, recovery identities, cross-field

Source: frozen `data/master/ipo_analysis.csv` (2,384 rows). Board: SME 1,471 / MB 913.

## 1. Ambiguous-column zero/null census (validates T1.1 expected output)
Every `_src`-carrying zero below is a **provenance-laundered** value today (a 0 stamped with a source) —
exactly what T1.1's validate-before-stamp must stop. Counts confirm `FOUNDATION_BUILD_SPEC.md` row I1 to the row.

| column | n | null | zero | neg | zero-carries-src (laundered) | verdict |
|---|---|---|---|---|---|---|
| `ofs_cr` | 2384 | 17 | **725** | 0 | 725 | **all 725 are REAL** (fresh-issue, MB 367/SME 358) → must stay `present` |
| `sub_total_x` | 2384 | 1129 | **124** | 0 | 124 | SME 106 / MB 18 — board disambiguates (below) |
| `sub_qib_x` | 2384 | 1214 | 341 | 0 | — | mostly SME-real per spec (27 MB implausible / 314 SME) |
| `sub_nii_x` | 2384 | 1143 | 156 | 0 | — | same class |
| `sub_retail_x` | 2384 | 1142 | 157 | 0 | — | same class |
| `gmp_pct` | 2384 | 1274 | **10** | 0 | 10 | source placeholder 0 → `Missing_data` (now wired: `validate_gmp_nonzero`) |
| `min_investment_rs` | 2384 | 1480 | 18 | 0 | — | recoverable (below) |
| `market_cap_cr` | 2384 | 861 | 7 | 0 | — | check vs issue size (Ph3 mcap-val) |
| `net_sales_yr3` | 2384 | 460 | 13 | 0 | — | 0 sales likely real-or-missing; financial, leave NULL+flag |
| `pre_ipo_net_sales` | 2384 | 466 | 17 | 0 | — | same |
| `issue_amount_cr` | 2384 | 0 | 1 | 0 | — | 1 IDR row (the Std-Chartered case, see doc 04) |

### sub_total_x zeros by board — the headline I1 case
- **MB zeros = 18** → masked-missing (no real mainboard IPO is 0×-subscribed). T1.1 `subscription_x_valid`
  now correctly routes these to `Missing_data`. These 18 are the MB-subscription refetch worklist (T1.4 / OD-4).
- **SME zeros = 106** → *could* be real no-demand. Per BUILD_SPEC, 75/106 are fixable from the existing
  ipowatch cache (network-free); the remainder stay `present`-if-real / honest-NULL.
- `ofs_cr=0` (725) split MB 367 / SME 358 — confirms these are genuine fresh-issue zeros, NOT missing.
  **This is the case a global `0→NaN` would have destroyed.** T1.1 preserves them (`validate_nonneg` admits 0).

## 2. ⚠ T1.3a subscription arithmetic recovery — the identity is NOT clean
Formula (OD-3): `sub_total_x ≈ sub_total_cr / issue_size_cr`.
- **Recoverable rows: 88** (x missing/0 but `sub_total_cr`>0 and `issue_size_cr`>0) — matches spec exactly.
- **BUT validating on the 778 rows that have all three + x>0:** the identity holds within 5% on only
  **605 (78%)**. Median relative error 0.9% (most rows dead-on), but **p90 = 28%** — a heavy tail diverges.

**Implication for the build (this changes T1.3):** blind recovery of the 88 would inject a wrong value on
~1-in-5. Do NOT stamp `derived` unconditionally. Options, in preference order:
1. **Recover + flag confidence**: stamp `derived`, but carry a recovery-residual quality flag; only treat as
   trustworthy where a *corroborating* source agrees (ipowatch) — matches the spec's overlay-corroboration spirit.
2. **Tighten the gate**: only recover the subset whose `(sub_total_cr, issue_size_cr)` basis is internally
   consistent (investigate WHY the 22% diverge — likely `issue_size_cr` is fresh-only vs total-offer, or
   `sub_total_cr` is a shares×price vs amount basis mismatch; the divergence is structured, not noise).
3. Recover only the rows where an independent check (e.g. `sub_qib/nii/retail_cr` sum ≈ `sub_total_cr`) passes.
**Action at build:** before applying OD-3, bucket the 88 by which of the divergence causes applies (re-run the
778-row validation split by board / era / book_built to find the clean subset). The 78% is the real ceiling.

### ⚠ UPDATE — the divergence is SYSTEMATIC (0.72×), not noise — so it's FIXABLE
Diagnosing the 173 failing rows: the pred/actual ratio is **tightly clustered at median 0.72 (p25 0.70,
p75 0.74)** — a consistent ~28% under-prediction, NOT random scatter. And it concentrates predictably:
- **bad rate by board: MB 37% vs SME 16%**; **by book_built: True 27% vs False 9%.**
- So the failures are overwhelmingly **book-built mainboard** issues.

**Interpretation:** for book-built MB issues, `issue_size_cr` (the denominator) is ~1.39× the base the
subscription multiple is actually measured against — almost certainly because the published subscription `x` is
computed on the **net offer excluding the anchor portion**, while `issue_size_cr` is the **total** issue. A
~0.72 factor ≈ (1 − anchor%) for a typical ~28% anchor allocation. **This means the recovery is rescuable**, not
abandoned:
- **SME / non-book-built rows (bad rate ≤9–16%): recover directly + stamp `derived`** (safe).
- **Book-built MB rows: apply the recovery against the net-offer base** (issue_size_cr − anchor_allocation_cr)
  where anchor is known, OR carry the 0.72 systematic correction with a flag, OR corroborate via ipowatch.
- This turns "78% ceiling, risky" into "≈100% recoverable once the anchor basis is corrected" — **a materially
  better outcome than the spec's blind division.** Verify the anchor-basis hypothesis at build on the 778 rows.

## 3. T1.3b min-investment recovery — CLEAN, safe to apply
Formula (CR-MININV): `min_investment_rs = lot_size_shares × issue_price`.
- Recoverable rows: **18** (matches spec). Identity holds within 5% on **881/886 = 99%** of rows that have all
  three. **Verdict: safe to recover + stamp `derived`** with no extra gate. `price_band_low` fallback adds 0
  (no row is missing issue_price while having a band) — so issue_price is the only needed input.

## 4. ⚠ T1.2 cross-field tranche reconciliation — 401 mismatches, not ~250
Check: `sub_total_cr` vs `sub_qib_cr + sub_nii_cr + sub_retail_cr`.
- Rows with all four present and total>0: **868**. Σparts differs from total by >5% on **401** of them.
- `FOUNDATION_BUILD_SPEC.md` O-3 cites **32 + 218 = 250**. **The live number is materially higher (401).**
- `total missing but ≥1 part present` (the recoverable-total class) = **0** — total is never missing when parts
  are present, so there is no "reconstruct the total from parts" recovery here (contradicts an implied recovery path).

**Implication:** the 401 is almost certainly because the three retail/HNI/QIB `_cr` tranches do **not** sum to
`sub_total_cr` by construction — Indian IPO subscription tables often exclude anchor/employee/shareholder
reservation tranches from the three headline categories, so Σ(3 parts) < total legitimately. Before T1.2 treats
these as errors, **confirm whether the tranche set is complete**; if anchor/other tranches are missing from the
sum, the reconciliation predicate must include them (or use a one-directional `Σparts ≤ total` sanity bound, not
equality). Re-deriving the spec's "32 + 218" split: 32 was likely the *over*-sum (parts > total = a real error)
and 218 a tighter tolerance — re-confirm both definitions at build. **The equality predicate as written is wrong;
the bound should be Σparts ≤ total·(1+tol).**

## 5. T1.4 refetch worklist (the `error_out` bucket, owner-gated)
From the above, the small high-value refetch targets are unchanged from spec: **18 MB-subscription zeros** +
**10 GMP zeros**. Both are source-side gaps; per R2/G2 they are `Missing_data` *until* an OD-4-approved
re-fetch from a *different* source can fill them (re-scraping the same source won't help). Big long-term
backfills (band/lot/identity/face_value/anchor) remain BL-5, honest-NULL for now.

## What to carry into the build
1. **T1.3 subscription recovery needs a confidence gate** (78% ceiling) — biggest new finding. ⚠
2. **T1.2 predicate must be Σparts ≤ total, not equality** — 401 "mismatches" are mostly legitimate missing
   tranches, not errors. ⚠
3. T1.3 min-investment recovery is clean — apply freely.
4. All T1.1 zero/null counts confirm the spec; the engine's wired validators (`subscription_x_valid`,
   `validate_gmp_nonzero`) target exactly the 18 MB + 10 GMP + 124 sub zeros.
