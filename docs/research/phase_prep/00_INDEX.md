# Phase-prep research — findings index

**Built:** 2026-06-18 (overnight autonomous research run; owner away).
**Scope:** read-only analysis on LOCAL data + targeted internet verification (owner enabled it mid-run). No code
changed, nothing committed. Purpose: pre-compute the slow, thinking-heavy checks the foundation phases (1–9)
will need, so we read conclusions instead of waiting on long runs later.

**Method note:** counts derived from `data/master/ipo_analysis.csv` (frozen 2,384-row substrate, 220 cols) +
the fresh `data_build/` re-fetch. Scripts were ephemeral (not saved, per owner). Internet facts are
web-verified and sourced inline. Where a finding diverges from `FOUNDATION_BUILD_SPEC.md` it is flagged ⚠ —
re-confirm at build.

## Documents
- `01_phase1_provenance.md` — Ph1 bucket counts, T1.3 recovery identities, T1.2 cross-field. **2 ⚠ that change the build.**
- `02_reconciliation_build_vs_frozen.md` — Ph7: what the honest re-fetch changed vs frozen.
- `03_corp_action_d1.md` — Ph5: the D-1 over-count AND a NEW under-coverage bug (25 dropped real events).
- `04_structural_columns.md` — Ph2: IDR mislabel, date-ordering, market-cap.
- `05_identity_outliers.md` — Ph3: wrong-entity-join sweep + identity coverage.
- `06_joining_and_merge.md` — joining integrity + data-copy/merge/corp-action improvement proposals (the synthesis).
- `07_open_questions.md` — ranked decisions for the owner.
- `08_additional_findings.md` — smaller findings (tripwire scope, overlay surface, quality census, clean cross-checks).

## HEADLINE CONCLUSIONS (read this first)
1. **NEW BUG — corp-actions must be UNION-merged, not replaced.** The fresh NSE fetch returns a rolling window
   and **dropped 25 real recent (2026) corporate actions** that frozen had (MCX 1:5, LICI 1:1 bonus, IRB,
   METROPOLIS, V2RETAIL, … — web-verified). Building on `data_build` alone → 25 un-adjusted splits → fake
   crashes. **Highest-priority fix.** (doc 03)
2. **The swap must MERGE/PRESERVE, not replace — for prices too.** 12 delisted price histories the re-fetch
   can't regenerate would be lost by a wholesale replace (survivorship damage). (doc 02/06)
3. **`delisting.csv` changed shape** → now a full status table (2,384 rows: active 2,100 / delisted 139 /
   unknown 75 / suspended 70). Consumers (step 07, Phase-5) must **filter on `status`**. (doc 02)
4. **Price re-fetch itself is SOUND** — historical closes match 150/150 (only newer days appended; no silent
   re-adjustment). Trustworthy to swap (with the union rule). (doc 02)
5. **T1.3 subscription recovery: the 22% identity failure is SYSTEMATIC (0.72×), not noise** — concentrated in
   book-built MB issues; ≈ an anchor-portion basis mismatch. Fixable → recover against the net-offer base, not
   abandon. (doc 01) **T1.2 tranche check must be `Σparts ≤ total`, not equality** (401 "mismatches" = legit
   missing anchor tranches). (doc 01)
6. **D-1 collapse window calibrated to 45d** (not 30d — VISHWARAJ spans 43d), keyed on `(symbol, rounded-ratio,
   ≥2 sources)` to avoid false-merging the 10–17 different-ratio real pairs. (doc 03)
7. **Adjudications resolved (web-verified):** ROLEXRINGS = one 1:10 split, factor 10× (the 19.96× is pure
   double-count, no second factor); Std Chartered IDRS → relabel `idr` (1 row); Indiabulls Power = RattanIndia
   Power, has NO bonus/split ever → its orphaned "bonus" fix is likely a phantom/misclassified rights issue. (docs 03/04/07)
8. **Wrong-entity joins aren't ratio-detectable** — Bajaj Corp's ₹292,355cr cap (a different Bajaj) is real
   contamination, but naive ratios flag real winners. Needs the ISIN-only join + identity-history golden file;
   33-row outlier worklist seeded for manual verification. (doc 05)
9. **All T1.1 counts reproduce the spec exactly**; the wired validators target the right rows; min-investment
   recovery is clean (99%). The 09 cross-source tripwire is wrongly disabled for 423 corp-action rows. (docs 01/08)

### RUN STATUS — ALL COMPLETE
- [x] 01 provenance · [x] 02 reconciliation · [x] 03 corp-action · [x] 04 structural
- [x] 05 identity · [x] 06 joining/merge · [x] 07 open questions · [x] 08 additional

### WHERE I STOPPED / suggested next-run targets (internet on)
Covered all 5 planned areas + joining/merge synthesis + extras, with web verification of 6 corp-actions/entities.
Remaining high-value (listed in doc 07 §"next-run"): diagnose-confirm the T1.3 anchor-basis hypothesis on the
778 rows; source NPST/CANTABIL exact ex-dates + the Indiabulls/RattanIndia rights-issue truth; build the
per-ISIN price union-diff as a materialized report; spot-verify 5 more of the dropped events. **Nothing here is
committed — review the docs, then we fold the ⚠ items into the Phase-1/5 build plans.**
