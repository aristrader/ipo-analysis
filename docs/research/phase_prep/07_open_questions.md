# 07 — Decisions & open questions for the owner (ranked)

Consolidated from docs 01–06. These are the calls that need YOU; everything else is mechanical and specced.

## A. Decide BEFORE the build proceeds (they change the design)
1. **Corp-actions: adopt union-merge (append-only) across fetches?** [doc 03/06] — STRONGLY recommended. Without
   it we lose 25 verified recent splits/bonuses → fake crashes. Cost: the merge must dedup the union (the 45d
   collapse handles it). *Recommend: yes.*
2. **Swap = union/preserve, not replace, for the price layer?** [doc 02/06] — preserves the 12 delisted
   histories the re-fetch can't regenerate. *Recommend: yes.* (Otherwise survivorship damage.)
3. **T1.3 subscription recovery (88 rows) — how to gate the 78% identity ceiling?** [doc 01] — options: (a)
   recover+flag-confidence, only trust where ipowatch corroborates; (b) recover only the internally-consistent
   subset after diagnosing the 22% divergence; (c) recover all + carry a residual flag. *Recommend: (b) then (a)
   for the remainder.* This is the biggest correctness fork in Phase 1.
4. **T1.2 tranche predicate = `Σparts ≤ total` (not equality)?** [doc 01] — the 401 "mismatches" are mostly
   legitimate missing anchor/employee tranches, not errors. Equality is wrong. *Recommend: one-directional bound.*

## B. Adjudications I resolved tonight (confirm you agree)
5. **ROLEXRINGS = one 1:10 split, factor 10×, no second factor** (web-verified trendlyne/exchange). The 19.96×
   is pure double-count. → golden catalog ratio 10.0, ex 2025-10-17. *(Resolves PLAN §4b open item.)*
6. **Standard Chartered PLC IDRS → `instrument_type='idr'`** (1-row relabel). *(Resolves the IDR mislabel.)*
7. **`delisting.csv` is now a status table** → downstream filters on `status`. *(Phase-9 repoint guard.)*

## C. Still UNRESOLVED — need external evidence (couldn't settle from local data)
8. **Indiabulls Power (INE399K01017) "bonus" fix — LIKELY A PHANTOM.** Tonight (internet): Indiabulls Power was
   **renamed RattanIndia Power Ltd (RTNPOWER, BSE 533122)** in 2014 (name change → ISIN unchanged, so
   INE399K01017 = RTNPOWER). Trendlyne shows **NO bonus and NO split ever** for RTNPOWER. → the orphaned "bonus"
   fix is probably (a) a phantom to **DELETE-EVENT**, or (b) a misclassified **rights issue** (RattanIndia did
   rights issues, which are NOT price-adjustment events like bonuses). **Verify against the exchange filing
   before migrating** — do not assume a bonus ratio. This also creates an identity-history golden entry
   (Indiabulls Power → RattanIndia Power, name_change, 2014). *(Was a Phase-7 blocker; now has a strong lead.)*
9. **NPST & CANTABIL exact true ratios + ex-dates** — substrate confirms they're fakes (161×, 39.7×); the
   single-event ratios (3.0, 5.0) are likely right but the dates need golden verification.
10. **The 6 stays-flagged corp-action stocks** (CMMIPL, COOLCAPS, SILVERTUC, VAISHALI, INDUSFILA, BANSAL) —
    disposition (flag / quarantine / exclude) — Phase-5 T5.4 from price evidence. (SILVERTUC also appears in the
    25 dropped-events list — its 2026 split+bonus must be union-merged first.)
11. **Canonical yfinance matcher (69 vs 52)** — pick one before the Phase-5 arbiter.

## D. Measure-at-build (quantify before committing a rule)
12. Whole-row quarantine row-loss — count rows removed before committing each Phase-6 rule.
13. market_cap_class re-bucketing churn on the 67 dual-cap rows (Phase-5 pre-task).
14. The 33-row wrong-entity worklist [doc 05] — manual price×shares verification each; build the identity golden.

## E. Things that are FINE (no action — verified tonight)
- The price re-fetch preserved history (150/150 overlap match) — trustworthy to swap (with the union rule).
- All T1.1 zero/null counts match the spec; min-investment recovery is clean (99%).
- The wired validators (`subscription_x_valid`, `validate_gmp_nonzero`) target exactly the right rows.
- No corp-action historical re-adjustment crept in (the past wasn't silently changed).

## Suggested next-run targets (if another autonomous block happens, internet on)
- Source Indiabulls Power bonus ratio + NPST/CANTABIL ex-dates (golden seeding).
- Diagnose the T1.3 22% subscription-divergence (split by board/era/book_built to find the clean subset).
- Verify the remaining ~20 dropped-event symbols are real (spot-check 5) to fully justify union-merge.
- Build the price-layer union-diff as an actual report (per-ISIN: frozen-only / build-only / both).
