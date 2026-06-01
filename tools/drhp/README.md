# tools/drhp — DRHP/RHP pre-IPO financials recovery pipeline (preserved + gated)

Productionized from the recovery prototype (was in /tmp). Recovers pre-IPO net sales / PAT for OLD
(2006–2014) IPOs from SEBI DRHP PDFs — the only viable free source for that era (screener floors at FY2015).

## Pipeline
`WebSearch → SEBI public-issues landing page → curl attachdocs/<id>.pdf → pdfplumber → 2-gate verify`
- `drhp_extract.py` — extractor + verification gates (run per-PDF; stdin meta).
- `drhp_batch.py` — driver (rate-limited, resume-safe, per-PDF timeout).
- `drhp_queue.csv` / `drhp_results.jsonl` — the located landing URLs + raw per-PDF results from the 2026-06-01 run.

## Verification gates (the wrong-data guards)
1. **Cover-page name match ≥80%** (rename-tolerant) — guards wrong-company PDFs.
2. **Value sanity** — sales>0 & ≥1cr; sales ≥ |PAT|; equal rev/PAT column counts; the picked column's
   fiscal year == pre-IPO FY (never "newest"); consolidated-preferred.
3. **PAT-suspect guard (added 2026-06-02)** — if the PAT pick == the operating/PBT pick, the after-tax
   line wasn't isolated → confidence=unverified (net_sales may still be OK; PAT → review). Caught DLF.

## Current state (2026-06-02)
- 16 names extracted → `docs/research/drhp_recovered.csv`; 25 → `docs/research/drhp_review_queue.csv`.
- net_sales cross-validates (Coal India, DLF exact). PAT is the weak field (PBT-vs-after-tax across varied
  old-DRHP table formats) — only 1/16 independently confirmed; DLF's withheld by the new guard.
- **NOT folded into data/master** (only 2/16 net_sales independently cross-validated; marginal coverage).

## NEXT PASS (deferred — see STATUS.md): the ~384 remaining names (bulk), full cross-validation of all
## recovered net_sales, and PAT hardening (require an explicit after-tax row label + a PBT−tax reconciliation).
