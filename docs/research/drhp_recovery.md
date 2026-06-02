# Pre-IPO financials recovery for OLD longterm IPOs — DRHP-PDF pass (research/staging only)

> **UPDATE 2026-06-02 (post cross-validation):** PAT field is unreliable (PBT-vs-after-tax; cross-val
> caught DLF). DLF's PAT withheld; a `pat==op` guard added to the extractor (now in `tools/drhp/`).
> Only net_sales is trustworthy, and only 2/16 are INDEPENDENTLY cross-validated → **NOT folded into
> data/master; staged + review-needed.** Pipeline preserved in `tools/drhp/`. Bulk run deferred.
>
> **FOLD-IN DECISION 2026-06-02: DO NOT FOLD (final; recorded in STATUS.md).** Impact analysis: all 16
> recovered net_sales fill NULL cells, but every value is ≥61.5cr — **none below the 25cr `tiny-sales` flag
> threshold, the only scorecard/flag/finding that consumes `pre_ipo_net_sales`.** Folding would change zero
> flags/scores/findings (16 large old MB IPOs, 16/2296 rows). With only 2/16 independently cross-validated +
> observed parsing artifacts, folding 14 unvalidated values into the frozen substrate for zero analytical gain
> fails the rigor bar. Re-open only with a concrete need + per-value independent cross-validation + the
> extractor fixes (array-artifact cleanup, PAT after-tax labeling).


**Date:** 2026-06-01 · **Scope:** recover `pre_ipo_net_sales` / `pre_ipo_pat` (+ operating profit where the
restated P&L exposes it) for the **425** longterm-cohort IPOs (`data/master/ipo_analysis.csv`,
`cohort=='longterm'`) where either field is null. **Staging only** — no `data/master/`, pipeline, predictor,
or finding edits. Supersedes the earlier stub that deferred this (the DRHP-PDF pipeline it described is now built).

Deliverables:
- `docs/research/drhp_recovered.csv` — VERIFIED rows only (passed the cover gate + the value-sanity gate).
- `docs/research/drhp_review_queue.csv` — unverified / low-confidence matches for a human pass (with `why` + raw extracted numbers).
- this file — method, per-source yield, coverage, verification approach, what is NOT recoverable + why.

## The gap

425 longterm rows missing `pre_ipo_net_sales` or `pre_ipo_pat`. By **pre-listing fiscal year** (the FY whose
sales/PAT we need = last completed March before listing):

| preFY bucket | rows | recoverable from… |
|---|---|---|
| preFY ≥ 2015 | ~16 | screener (already exhausted by the prior in-window pass; 61 staged in `financials_longterm_extra.csv`) |
| preFY 2011–2014 | ~110 | DRHP PDF only (below screener's FY2015 floor) |
| preFY 2005–2010 | ~285 | DRHP PDF only |
| no listing date | ~14 | — |

Type split: **336 MB**, **89 SME**.

## Step 1 — no-network raw-data check (FREE win attempt): NEGATIVE for sales/PAT

Checked the already-scraped raw files before any network call:
- `data/raw/chittorgarh/details_longterm.csv` — carries promoter **share counts**, issue sizes, listing-day
  OHLC. **No sales/PAT/financial-statement fields.** (Promoter shares were a prior agent's free win; there is
  no financials win here.)
- `data/raw/screener/financials.csv` + `financials_longterm_extra.csv` — **342** of the 425 missing ISINs DO
  have screener financial rows, but **0** cover the company's actual **pre-IPO FY**. Screener's history floor is
  **Mar-2015**; for these 2006–2014 listings the pre-IPO FY is always below that floor, so every screener row is
  a *post*-listing year — useless for `pre_ipo_*`. (47 have screener's earliest FY = preFY+1, i.e. one year too late.)

**Conclusion:** no free no-network win for sales/PAT. The numbers exist for free only inside the DRHP/RHP PDFs.

## Step 2 — screener.in: EXHAUSTED by prior pass

The prior `recover_inwindow_financials.py` pass already recovered the screener-serveable slice (61 ISINs,
FY2015–2019, in `financials_longterm_extra.csv`). No remaining screener candidate (all remaining missing rows
have preFY < 2015).

## Step 3 — DRHP/RHP PDFs on SEBI (the only viable source for 2006–2014)

### The working path (confirmed)
`WebSearch` (the de-facto index) → SEBI **landing page** `sebi.gov.in/filings/public-issues/<mon-year>/<co>_<id>.html`
→ `curl` the landing HTML → scrape the embedded `attachdocs/<numeric_id>.pdf` link → `curl` the PDF
(`sebi.gov.in/sebi_data/attachdocs/<id>.pdf`, HTTP 200, no auth) → `pdfplumber` (born-digital text, no OCR).
Tooling (in `/tmp`, reusable for a second pass): `drhp_extract.py` (extractor + gates), `drhp_batch.py` (driver,
rate-limited, resume-safe, per-PDF 180s timeout), `build_deliverables.py` (jsonl → the three CSVs). Landing URLs
collected via WebSearch are in `/tmp/drhp_queue.csv`; raw per-PDF results in `/tmp/drhp_results.jsonl`.

NOTE: the earlier-feared "landing pages are JS-rendered" is NOT true via curl — the `attachdocs` link is in the
static HTML. The real friction is per-PDF processing time (pdfplumber scans every page) and table-shape variance.

### The COVER-PAGE VERIFICATION GATE (mandatory — the wrong-company guard)
SEBI `attachdocs` IDs are opaque and WebSearch can mis-hit (a Sadbhav query once returned GMR's prospectus).
So **no number is staged as verified unless it clears two gates**:

1. **Cover gate** — the PDF's first 3 pages must contain ≥80% of the issuer's name tokens (matched against
   `name_at_ipo`/`company_name`, rename-tolerant). Below 0.8 → `reject` (wrong company), dropped, never staged.
2. **Value-sanity gate** (guards mis-parsed tables / wrong column / footnote contamination / subsidiary tables):
   - net sales > 0 and ≥ ₹1cr;
   - net sales ≥ |PAT| (a PAT margin > 100% means a misaligned column or wrong row);
   - the revenue and PAT lines extracted the **same number of columns** (else alignment is ambiguous);
   - the picked column's **fiscal year actually equals the pre-IPO FY** (or preFY−1 if the DRHP predates the
     final pre-listing year) — never an arbitrary "newest" year. A mis-parsed header that yields the wrong year
     is exactly the wrong-data failure mode, so it is refused, not guessed.
   When multiple restated P&L tables exist (standalone vs consolidated vs subsidiary), the extractor prefers the
   **CONSOLIDATED** statement (the basis screener/most sources report) and falls through candidate pages until one
   passes; if none passes, the row goes to the **review queue** with its raw extracted numbers + the reason.

Anything failing gate 2 is staged to `drhp_review_queue.csv` (with `why`, raw rev/pat number arrays, parsed year
headers, unit, P&L page index) for a fast human read — **never** to the trusted output.

### Spot-validation of the gate (recognizable names)
- Jubilant Foodworks (preFY2009): net sales ₹280.61cr, PAT ₹6.74cr — matches the manual figure in `drhp_feasibility.md`.
- Coal India (preFY2010, consolidated): net sales ₹44,615cr, PAT ₹9,834cr — plausible vs known CIL FY10.
- DLF (preFY2007, consolidated): net sales ₹4,034cr, PAT ₹2,549cr — plausible vs known DLF FY07.
- Oberoi Realty: extraction produced sales < PAT → **correctly rejected to the review queue** (gate working).
- Cairn India / Mundra / Just Dial: unit or multi-table ambiguity → review queue (gate working).

## Yield (this pass)

This pass WebSearch-located and processed a prioritized set of large/recognizable mainboard names (the slice with
the best free-locatability). It is a demonstration + first tranche, NOT full coverage of 425.

**41 names WebSearch-located + processed; 16 VERIFIED, 25 → review queue.** (Hit rate ~39% of attempted; ~3.8%
of the 425 gap.) All 16 verified passed both gates; spot-checks match known reality (Inox Leisure FY2005
61.48/7.22cr = the manual figure in `drhp_feasibility.md`; Coal India FY2010 44,615/9,834cr; DLF FY2007
4,034/2,549cr). 8 of 16 also carry operating profit (PBT). 2 used preFY−1 (Varun FY2015, Fortis FY2006 — DRHP
predates the final pre-listing year; flagged in `reason`).

| outcome | n | which names / why |
|---|---|---|
| **VERIFIED** | **16** | Coal India, DLF, Mundra Port, Varun Beverages, Cairn India, JSW Energy, Cox & Kings, Fortis Healthcare, Parsvnath, MCX, HDIL, NHPC, MOIL, Religare, Sharda Cropchem, Inox Leisure |
| review: `no_restated_pnl_page` | 8 | P&L heading/format not matched (Prestige, Brigade, Gujarat Pipavav, Pipavav Shipyard, SJVN, Jyothy, VA Tech, Wonderla) |
| review: `pnl_lines_not_parsed` | 6 | page found, rev/PAT line labels not matched (Puravankara, Adani Power, Oil India, Bajaj Corp, MindTree, +1) |
| review: `unit_unknown`/footnote | 4 | unit not detected or footnote-superscript contamination (IRB, PC Jeweller, Omaxe, Mahindra Holidays) |
| review: `wrong_fy` / `col_mismatch` / `pat_exceeds_sales` | 7 | gate caught a mis-parsed table → refused (Oberoi, Just Dial, Ramky, Jaypee Infratech, CCCL, DB Corp, +1) |

The 25 in the review queue carry their raw extracted rev/PAT arrays + parsed year-headers + P&L page index, so a
human can confirm the right column/table in seconds (the data IS in those PDFs; the auto-parser just couldn't
safely disambiguate). Cached PDFs are in `/tmp/drhp_pdfs/` for that human pass.

**Why this is a first tranche, not 425:** each name costs a WebSearch + a 3–6 MB PDF download + a full pdfplumber
page scan (~1–3 min for large PSU prospectuses). The 41 here are the largest/most-recognizable mainboard issues
(best WebSearch locatability). Scaling to the remaining ~384 is mechanical but time-bound by per-PDF processing +
the per-name WebSearch step; the small-2006-issue and SME tail will have a lower locate rate.

## What is NOT recoverable for free (honest boundary)
- **preFY < 2015 + free + structured + programmatic = does not exist.** BSE/NSE results archives are PDF-only and
  floor ~2011; moneycontrol/tijori/trendlyne are gated or truncated. The DRHP PDF is the only free source, and it
  is per-document.
- **Locating is the bottleneck.** WebSearch surfaces the SEBI landing page reliably for large/recognizable
  mainboard names but is hit-or-miss for small 2006–2009 issues and most SME names (often no SEBI public-issues
  landing page, or the only hit is a later debt/rights filing). Those cannot be auto-located here.
- **Table-shape variance is real.** Banks/NBFCs/insurers have no "net sales" line; PSUs/holding companies carry
  multiple restated P&L tables (standalone/consolidated/subsidiary) and footnote superscripts that contaminate
  naive number extraction. The gate refuses these rather than risk wrong-company-grade errors → review queue.
- `debt_equity` is **not auto-extracted** — it is a balance-sheet ratio on a separate annexure; left blank for a
  later targeted pass (the restated P&L page does not carry it cleanly).

## Recommendation on a second pass
Worth it, but as a **semi-automated, human-in-the-loop** effort: the locator (WebSearch → landing → PDF) and the
extractor + safe gate are built. Residual work is (a) WebSearching the remaining ~380 names (many small/SME won't
resolve to a SEBI landing page) and (b) a human clearing the review queue — picking the right table column /
consolidated-vs-standalone for the ~⅓ the gate can't auto-confirm. Full coverage of 425 is not free-and-automated;
expect to verify a few hundred at most, with diminishing returns on the small/old/SME tail. Performance note for a
rerun: cache PDFs (already done in `/tmp/drhp_pdfs/`) and consider parallelism — per-PDF pdfplumber scans dominate.
