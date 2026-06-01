# Pipeline (run once, in order)

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | 01_build_base.py | data/raw/chittorgarh/urls.csv | data/master/_base_{mb,sme}.csv |
| 2 | 02_attach_detail.py | _base + chittorgarh/details.csv | _base+detail |
| 3 | 03_enrich.py | _base+detail + sharescart + screener (by ISIN) | _enriched |
| 4 | 04_verify.py | _enriched + exchange_lists + bhavcopy | mainboard.csv, sme.csv |
| 5 | 05_reconcile.py | master vs archive/derived/*_OLD.csv | reconciliation_report.csv |

Each step has a matching `pipeline/checks/check_0N_*.py` that must pass before proceeding.
