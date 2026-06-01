# Master IPO dataset

- `mainboard.csv`, `sme.csv` — Indian IPOs 2020–2025, ISIN-keyed.
- Built by `pipeline/01..05`. Spine = Chittorgarh; enriched by ISIN from Sharescart/screener.
- `<field>_src` columns show each value's source. `confidence` grades each row.
- `delisting.csv` — delisting status/date/reason/last_price per ISIN (price-pipeline INPUT for step 07 + merge); kept top-level.
- `review/` — review/flag CSVs: `reconciliation_report.csv` (diffs vs prior dataset), `gaps.csv` (unsourced fields),
  `ticker_validation.csv`, `ticker_conflicts.csv`, `name_isin_review.csv`, `screener_financials_review.csv`,
  `xcheck_review.csv`, `price_source_review.csv`, `price_missing.csv`.
- Built: 2026-05-30. Row counts: mainboard 382, sme 887 (1269 total).
