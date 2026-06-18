# 08 — Additional findings (smaller, but worth recording)

Loose findings from the sweep that don't need their own doc but shouldn't be lost.

## 1. The 09 cross-source listing-price tripwire is disabled for 423 universe rows
`09_assemble.py:88-89` disables the cross-source listing-price sanity check for ANY stock with a corp action.
**423 universe rows (18%)** have a corp action → 423 rows bypass the check. Re-enabling it (doc 06 C.5) is not a
niche fix — it restores a data-quality guard across nearly a fifth of the universe. The corp-action stocks are
*exactly* the ones most likely to have a price glitch, so disabling the check there is backwards.

## 2. Overlay migration surface (Phase 4) — small and enumerable
Scattered hand-fixes to consolidate into ONE append-only overlay ledger:
- `data/reference/manual_overrides.csv` — **3 rows** (market_maker corrections).
- `corp_actions_merged.csv` source-tagged — **39 rows** (34 `manual_thinktank_audit` + 5 `verification_2026-05-31`).
- `drhp_recovered.csv` — spec says 16 DRHP financials; **file NOT found** at `data/reference/` or
  `data/master/review/` tonight → locate at build (may be elsewhere / renamed).
- Total known surface ≈ **42 + 16 = ~58 fixes.** (The architecture's "34+21+16" — the "21" resolves to 5
  verification rows tonight; reconcile the count at build.)
- R5 caveat stands: migrated fixes lack a recorded `old_value` → conflict-detection inert until reconstructed
  (reconstruct from the frozen substrate, which is the pre-fix baseline).

## 3. Data-quality / coverage census
- `data_quality_tier`: **high 2,030 / med 341 / low 13** (= 2,384).
- 16 rows have **no price history** (`has_price_history=0`) → `returns_summary` = 2,368 (= 2,384 − 16). Matches
  the substrate_meta unpriced count. These are the genuinely-unpriced (Layer-3 already excludes them).
- `exclusions.csv` = header only (0 rows) — empty by design (no universe exclusions applied yet).

## 4. Substrate row-count note
`ipo_analysis.csv` / `universe.csv` = **2,384** data rows (the CSV had a trailing blank making `wc -l` look like
2,387 — confirms the CLAUDE.md "wc -l lies on the CSVs, count records via csv" warning). All analyses used the
pandas row count (2,384), consistent with `substrate_meta.json`.

## 5. Cross-checks that came back CLEAN (negative results worth recording)
- No `open_date > close_date` violations (0).
- No price file had its **historical** closes altered by the re-fetch (150/150 overlap match) — the only price
  changes are appended recent days.
- All ambiguous-column zero/null counts reproduce the BUILD_SPEC exactly (ofs 725 / sub_total_x 124 = 106+18 /
  gmp 10 / min-inv 18 / sub_qib 341 / sub_nii 156 / sub_retail 157).
- Every substrate row has at least one trading ticker (no all-four-null rows).
