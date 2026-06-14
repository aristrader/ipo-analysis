# Pipeline (run once, in order)

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | 01_build_base.py | data/raw/chittorgarh/urls.csv | data/master/_base_{mb,sme}.csv |
| 2 | 02_attach_detail.py | _base + chittorgarh/details.csv | _base+detail |
| 3 | 03_enrich.py | _base+detail + sharescart + screener (by ISIN) | _enriched |
| 4 | 04_verify.py | _enriched + exchange_lists + bhavcopy | mainboard.csv, sme.csv |
| 5 | 05_reconcile.py | master vs archive/derived/*_OLD.csv | reconciliation_report.csv |

### Documentation & Audits
- **Corporate Actions Audit:** Over 88 deeply unresolved microcap/SME price mismatches were audited via a massive multi-agent web scraping operation. See `docs/research/unresolved_88_mismatches_audit.md` for the breakdown of legitimate market crashes vs genuine missing stock splits.

Each step has a matching `pipeline/checks/check_0N_*.py` that must pass before proceeding.
