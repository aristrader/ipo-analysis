# Showdown P3 — Sandbox Pipeline Re-run vs the Frozen Substrate (2026-06-04)

**Setup:** full repo+data copied to `/tmp/ipo_showdown_sandbox`, the OFFLINE chain re-run there
(03b → 03c → 03d → 03e → 04 → 05 → 07 → merge → 08 → 09; ~30s wall) against the same raw caches,
then a cell-level diff vs the real `data/master/`. The real repo was never touched.

## Verdict: the pipeline REPRODUCES the frozen substrate
| File | Result |
|---|---|
| **returns_summary.csv** | **BYTE-IDENTICAL** — the entire Layer-2 price/outcome math is deterministic and reproduces exactly. |
| delisting / exclusions / longterm_mainboard / longterm_sme | byte-identical |
| **ipo_analysis.csv / universe.csv** | numerically identical except **34 cells** — all explained (below) |
| sme.csv / mainboard.csv / _base_* | stale STAGING snapshots (see below) — final substrate unaffected |

## The 34 explained substrate cells
1. **3 × `market_maker`** (INE00D001018, INE05FR01029, INE813V01022): a documented hand-fold
   (DONE.md 2026-06-01 "3 market-makers applied") that exists only in the final files, not in any raw
   cache — a re-run loses them. *Improvement noted: move these into a small override file a step reads.*
2. **31 × one ISIN, INE338Y01016**: its real financials came from sharescart (src tag says so) because
   screener had no match AT BUILD TIME; the screener cache GREW during later data hunts, so a fresh
   03b applies the by-design "screener wins (correctly-dated)" policy and replaces the whole yr1-yr3
   block. Not a bug — the frozen substrate predates the cache rows. On any future deliberate rebuild
   this company's financials legitimately update.

## The staging-files story (sme/mainboard/_base diffs, ~7.6k cells)
Two causes, neither affecting the final substrate:
- **Format-only (~26k cells incl. final files):** rewriting through float conversion normalizes
  "66" ↔ "66.0". Numeric-equality shows zero difference.
- **Stale staging:** the boom master/staging files are snapshots from an earlier 03b run; the raw
  screener cache grew afterwards, and those later values were folded into universe/ipo_analysis
  directly. VERIFIED: the sandbox's fresh master fills match the real ipo_analysis values (4/4 spot
  checks) — i.e. the hand-folds were faithful to what the pipeline derives, and only the
  intermediates lag. A future full rebuild resyncs them.

## Not identity-checkable offline (by nature, not by gap)
`00_build_longterm_spine` (cloudscraper), `06_validate_tickers` (yahoo), `longterm/02_detail` —
they fetch from the live web, which has moved since the freeze. They get py_compile/import checks
in the showdown suite instead.

## Encoded as a permanent test
`tests/showdown/test_pipeline_sandbox.py` re-runs this end-to-end (env-gated `SHOWDOWN=1`):
chain must exit 0 per step; returns_summary must stay byte-identical; the final substrate must be
numeric-equal except the enumerated allowed cells above; anything else FAILS the showdown.
