# DRHP-PDF recovered financials — INDEPENDENT cross-validation

**Date:** 2026-06-01 · **Validator scope:** confirm/catch errors in `docs/research/drhp_recovered.csv`
against sources that are **NOT the same SEBI DRHP PDF**, before any fold-in. Read-only probe — no repo
data/code touched. Re-read of `drhp_recovered.csv` while the pipeline runs: **2 rows present** at time of
this pass (Coal India, DLF). This file should be re-run when more rows land.

## Headline

- **1 of 2 rows MATCH independent sources cleanly** (Coal India).
- **1 of 2 rows has a CRITICAL field error** (DLF): the recovered `pat_cr` is the **Profit-Before-Tax**
  line, not Profit-After-Tax. Independent source gives PAT = ₹1,941.3 cr; we recorded **₹2,549.5 cr** (= PBT).
  Net sales for DLF is correct.
- **Implication:** the value-sanity gate (sales ≥ |PAT|, FY-correct, consolidated-preferred) is **necessary
  but not sufficient** — it does not distinguish the PBT row from the PAT row, and a too-high PAT passes
  every check it makes. This is the residual error mode and it is live in the current output.

## Per-row verification table

| ISIN | Company | preFY | Field | Our value (₹cr) | Independent value (₹cr) | Verdict | Source (independent) |
|---|---|---|---|---|---|---|---|
| INE522F01014 | Coal India | FY2010 | net_sales | 44,615.25 | ≈44.6k coal sales; total income ₹52,592 cr (incl. ~₹8k other/interest income) | **MATCH** (net-sales basis) | SPTulsian Coal India IPO analysis; consistency vs reported total income |
| INE522F01014 | Coal India | FY2010 | PAT | 9,833.7 | **9,834** (EPS ₹15.57 × 631.6 cr shares ≈ 9,834) | **MATCH** (exact to rounding) | SPTulsian IPO analysis; Business Standard IPO page |
| INE271C01023 | DLF | FY2007 | net_sales / total revenue | 4,034.1 | **4,034.10** | **MATCH** (exact) | SPTulsian DLF IPO analysis |
| INE271C01023 | DLF | FY2007 | PAT | **2,549.5** | **1,941.30** (PBT 2,549.50 − tax 608.20 = PAT 1,941.30) | **MISMATCH — extracted PBT, not PAT** | SPTulsian DLF IPO analysis (arithmetic-consistent: 2549.50−608.20=1941.30) |
| INE271C01023 | DLF | FY2007 | operating_profit | 2,549.5 | n/a (also = the PBT line; equals pat_cr → corroborates the wrong-row grab) | **SUSPECT** | same |

### Detail / reasoning

**Coal India FY2010 — TRUSTWORTHY.**
Independent IPO analysis (SPTulsian) and the Business Standard IPO record both put FY10 consolidated net
profit at ~₹9,834 cr and total income at ₹52,592 cr, with EPS ₹15.57 on a 631.6-cr-share / ₹6,316-cr equity
base (15.57 × 631.6 ≈ 9,834 — internally consistent). Our PAT 9,833.7 is an exact match. Our net_sales
44,615.25 is the **net sales of coal** line; total income 52,592 includes Coal India's very large other/interest
income (the company was net-cash ~₹37,000 cr, so interest income alone is multi-thousand-crore). The gap between
44,615 and 52,592 is exactly that other income, which is the correct distinction between "net sales" and "total
income." No error. Note `verify_method` records `unit=million` and the page math (44,615.25 ≈ 4,461,525 / 100)
is consistent with a million-denominated restated statement converted to crore.

**DLF FY2007 — net_sales correct, PAT WRONG (PBT captured).**
Independent IPO analysis (SPTulsian) breaks FY07 down explicitly:
> total revenue ₹4,034.10 cr · PBT ₹2,549.50 cr · tax ₹608.20 cr · **PAT ₹1,941.30 cr**.
- Our `net_sales_cr` = 4,034.1 → **exact match**, good.
- Our `pat_cr` = 2,549.5 = the **PBT** figure → **wrong field**. The true PAT is 1,941.3. Overstated by ~31%
  (about ₹608 cr, exactly the tax line).
- Corroborating tell inside our own row: `operating_profit_cr` is also 2,549.5, identical to `pat_cr`. The
  extractor latched onto one number near the bottom of the P&L (the PBT/"profit before tax and after
  extraordinary items" line) and wrote it into both the PAT and operating-profit slots. The actual PAT row,
  one or two lines below after the tax provision, was not picked.
- (Side note, not an extraction error but a known data caveat: DLF's FY07 profit was itself inflated by a
  ₹2,207-cr related-party sale to DLF Assets Pvt Ltd. That affects interpretation of the number, not whether
  we extracted the right line. We still want the genuine PAT, 1,941.3.)

## Why the gate let DLF through (residual error mode)

The value-sanity gate checks: sales>0, sales ≥ |PAT|, same column count on the rev & PAT lines, FY equals
pre-IPO FY, consolidated preferred. **None of these can tell PBT from PAT.** PBT is always positive, always
≤ sales (for a normal company), shares the table's column structure, and sits in the same fiscal-year column.
So a PBT value sails through every gate. The gate guards against *wrong company*, *wrong year*, *wrong unit*,
*sales/PAT column swap*, and *subsidiary tables* — all real and worth guarding — but it has **no row-label
discrimination** between the several "profit" lines a restated P&L stacks (operating profit → profit before
tax → profit before extraordinary items → **profit after tax**). For multi-line P&Ls (which is every DRHP),
that is the dominant residual risk, and DLF demonstrates it is not hypothetical.

Secondary residual modes still possible on un-spot-checked rows:
- **Pre-tax / pre-minority-interest vs final PAT** — same family as the DLF error.
- **Net sales vs total income** — Coal India shows the extractor *did* take net sales (good), but on tables
  where the restated statement leads with "Total income," a row could grab total income instead. Cross-source
  numbers differ on this basis, so a ±(other income) discrepancy is expected and not necessarily an error.
- **Standalone vs consolidated** — gate prefers consolidated but falls through to standalone if consolidated
  doesn't parse; a silent standalone substitution would be undetectable from the row alone.
- **Restated vs as-reported** — DRHPs restate prior years; restated ≠ the figure the press reported that year.
  Small deltas vs press archives can be legitimate restatement, not extraction error — do not auto-fail on them.

## Method assessment

- **Cover gate (≥80% name-token match on first 3 pages): adequate** for the wrong-company failure mode.
  Both rows show ratio=1.00. This is the right guard and appears to work.
- **Value-sanity gate: insufficient as the sole trust basis for PAT.** It correctly rejected Oberoi/Cairn/
  Mundra/Just Dial per the method doc (good — the structural guards fire), but it **cannot catch the
  PBT-as-PAT substitution**, and that error is present in 1 of the only 2 produced rows. A 50%-of-sample
  field-level error rate on PAT is disqualifying for silent fold-in.
- **`confidence=high` is overstated** for DLF given the PAT error. Confidence is currently driven by the cover
  ratio + sanity pass, neither of which sees the PBT/PAT problem, so "high" does not mean PAT-correct.

## Recommended cross-validation protocol (before any fold-in)

1. **Row-label capture, not just value capture.** The extractor should record the *exact P&L line label* it
   read for each of net_sales / PAT / operating_profit (e.g. "Profit after tax", "Profit before tax",
   "Total income", "Net sales"). Stage that label. A row whose PAT label is not an after-tax label
   ("profit after tax", "profit/(loss) after tax", "net profit after tax") must go to the review queue.
2. **Tax-reconciliation check.** If the table exposes PBT and tax, assert PAT ≈ PBT − tax (±2%). DLF would
   have failed this and gone to review. Where only one "profit" line is captured, flag that the PBT/PAT
   distinction is unconfirmed.
3. **Independent second-source check on every staged row, not just spot-checks.** For recognizable names this
   is cheap (IPO-analysis sites — SPTulsian, Chittorgarh, Business Standard IPO pages — and Wikipedia for the
   majors). Target ≥1 independent source per row; verdict MATCH / CLOSE(±5%) / MISMATCH / UNVERIFIABLE.
   Restatement deltas (a few %) are acceptable as CLOSE; a tax-sized gap (DLF: +31%) is a MISMATCH.
4. **operating_profit ≠ pat sanity.** If operating_profit_cr == pat_cr (as in DLF), flag — it is a strong
   signal the same line was reused for two fields.
5. **Net-sales vs total-income labelling.** Record which one was taken; downstream features should know whether
   the field is sales-of-product or total-income, since cross-source comparison depends on it.
6. **Keep the backup, but do not fold the current 2 rows in as-is.** Fix DLF PAT to 1,941.3 (or re-extract the
   after-tax line) before any merge.

## Verdict on trustworthiness of the recovered set

**NOT yet trustworthy enough to fold in silently. Needs human / second-source review first.**

- The locating + cover gate + unit handling are sound (Coal India is exactly right; DLF net_sales exactly right).
- But **PAT is the field most consumers care about, and it is wrong in 1 of 2 rows** because the gate has no
  row-label discrimination. That is the critical error mode the task asked us to catch, and it is live.
- **Action:** before fold-in, (a) correct DLF `pat_cr` 2,549.5 → **1,941.3** and clear `operating_profit_cr`
  (currently a duplicated PBT); (b) add the row-label + tax-reconciliation gates above and re-run the extractor
  over staged PDFs; (c) require an independent second source per row. With those, the set can be folded in with
  the backup retained. As it stands, treat every `pat_cr` as suspect until row-label-confirmed.

## Sources used (independent of the SEBI DRHP PDF)

- SPTulsian — Coal India IPO analysis: https://www.sptulsian.com/f/ipo-analysis/coal-india
- SPTulsian — DLF IPO analysis: https://www.sptulsian.com/f/ipo-analysis/dlf-limited
- Business Standard — Coal India Ltd IPO 2010 record: https://www.business-standard.com/markets/ipo/coal-india-ltd-ipo-12019
- Business Standard — DLF Ltd IPO 2007 record: https://www.business-standard.com/markets/ipo/dlf-ltd-ipo-6890
- Chittorgarh — DLF IPO: https://www.chittorgarh.com/ipo/dlf_ipo/86/
- Wikipedia — DLF (company): https://en.wikipedia.org/wiki/DLF_(company)
- Wikipedia — Coal India: https://en.wikipedia.org/wiki/Coal_India
