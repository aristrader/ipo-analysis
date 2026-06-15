# Master Schema (locked — Phase 0)

The master column list for `data/master/mainboard.csv` and `data/master/sme.csv`.
Both files share this schema (analysis differs, columns do not).

**Locked after Phase 0 exploration** (`pipeline/checks/explore_chittorgarh.py`) + spec §8 +
the column names already in use in `archive/derived/*_clean_OLD.csv`.

How to read `source`:
- `chittorgarh` — the ISIN-keyed spine (list `urls.csv` + detail `details.csv`). 2020–2025, free.
- `sharescart` — enrichment by ISIN. Subscription-split, GMP, full 3yr financials. **2023–2025 only.**
- `screener` — financials for 2020–2022 where Sharescart is absent; price history (verify).
- `exchange` — NSE/BSE official symbol↔ISIN lists (authoritative ticker).
- `derived` — computed in-pipeline from other columns (margins, growth, age, confidence).

Provenance: key multi-source fields carry a `<field>_src` tag (a string column naming the
winning source). Those `*_src` columns are listed once at the end of each group, not per field.

---

## Identity (chittorgarh spine + exchange)

| column | type | source |
|---|---|---|
| isin | str | chittorgarh |
| company_name | str | chittorgarh |
| type | str | chittorgarh |
| nse_symbol | str | chittorgarh |
| bse_script_code | str | chittorgarh |
| ticker_ns | str | exchange |
| ticker_bo | str | exchange |
| exchange | str | chittorgarh |
| listing_at | str | chittorgarh |
| chittorgarh_id | str | chittorgarh |
| chittorgarh_slug | str | chittorgarh |
| detail_url | str | chittorgarh |
| year | int | chittorgarh |
| industry | str | sharescart |
| incorporation_year | int | sharescart |
| age_at_ipo_years | float | derived |

## IPO basics (chittorgarh + sharescart)

| column | type | source |
|---|---|---|
| issue_price | float | chittorgarh |
| price_band_low | float | sharescart |
| price_band_width_pct | float | sharescart |
| book_built | str | sharescart |
| pricing_method | str | chittorgarh |
| face_value | float | chittorgarh |
| lot_size_shares | int | chittorgarh |
| min_investment_rs | float | chittorgarh |
| issue_amount_cr | float | chittorgarh |
| issue_size_cr | float | chittorgarh |
| fresh_issue_cr | float | chittorgarh |
| ofs_cr | float | chittorgarh |
| ofs_pct | float | chittorgarh |
| anchor_allocation_cr | float | chittorgarh |

## Timetable (chittorgarh)

| column | type | source |
|---|---|---|
| open_date | date | chittorgarh |
| close_date | date | chittorgarh |
| listing_date | date | chittorgarh |

## Subscription (sharescart, gated on chittorgarh)

| column | type | source |
|---|---|---|
| sub_qib_x | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_nii_x | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_retail_x | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_total_x | float | chittorgarh (total only; split gated) |
| sub_qib_cr | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_nii_cr | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_retail_cr | float | sharescart (2023-2025 only; blank pre-2023) |
| sub_total_cr | float | sharescart (2023-2025 only; blank pre-2023) |

## GMP (sharescart)

| column | type | source |
|---|---|---|
| gmp_pct | float | sharescart (MB: 2020-2026; SME: 2023-2026 only. SME data is blank pre-2023 because the informal grey market did not track SMEs back then) |

## Listing (chittorgarh)

| column | type | source |
|---|---|---|
| listing_open | float | chittorgarh |
| listing_gain_pct | float | derived |
| listing_high | float | chittorgarh |
| listing_low | float | chittorgarh |
| listing_close | float | chittorgarh |

## Promoter (chittorgarh + sharescart)

| column | type | source |
|---|---|---|
| promoter_pre_issue_pct | float | chittorgarh |
| promoter_post_issue_pct | float | chittorgarh |
| promoter_pre_shares | float | chittorgarh |
| promoter_post_shares | float | chittorgarh |

## People (chittorgarh)

| column | type | source |
|---|---|---|
| lead_manager | str | chittorgarh |
| market_maker | str | chittorgarh |
| registrar | str | chittorgarh |
| objects_of_issue | str | chittorgarh |

## Financials — 3yr (sharescart; screener for 2020-2022)

| column | type | source |
|---|---|---|
| fin_year_yr3 | str | sharescart |
| fin_year_yr2 | str | sharescart |
| fin_year_yr1 | str | sharescart |
| net_sales_yr3 | float | sharescart |
| net_sales_yr2 | float | sharescart |
| net_sales_yr1 | float | sharescart |
| operating_profit_yr3 | float | sharescart |
| operating_profit_yr2 | float | sharescart |
| operating_profit_yr1 | float | sharescart |
| pat_yr3 | float | sharescart |
| pat_yr2 | float | sharescart |
| pat_yr1 | float | sharescart |
| eps_yr3 | float | sharescart |
| eps_yr2 | float | sharescart |
| eps_yr1 | float | sharescart |
| shareholder_funds_yr3 | float | sharescart |
| shareholder_funds_yr2 | float | sharescart |
| shareholder_funds_yr1 | float | sharescart |
| borrowings_yr3 | float | sharescart |
| borrowings_yr2 | float | sharescart |
| borrowings_yr1 | float | sharescart |
| total_assets_yr3 | float | sharescart |
| total_assets_yr2 | float | sharescart |
| total_assets_yr1 | float | sharescart |
| operating_cf_yr3 | float | sharescart |
| operating_cf_yr2 | float | sharescart |
| operating_cf_yr1 | float | sharescart |
| pe_ratio | float | sharescart |
| pat_ttm_cr | float | sharescart |
| sales_ttm_cr | float | sharescart |
| eps_ttm | float | sharescart |
| roe_pct | float | sharescart |
| roce_pct | float | sharescart |
| debt_equity | float | sharescart |
| sales_cagr_3y | float | derived |
| pat_cagr_3y | float | derived |

## pre_ipo_* (normalized, sharescart; derived margins)

| column | type | source |
|---|---|---|
| pre_ipo_fin_year | str | sharescart |
| pre_ipo_net_sales | float | sharescart |
| pre_ipo_operating_profit | float | sharescart |
| pre_ipo_pat | float | sharescart |
| pre_ipo_eps | float | sharescart |
| pre_ipo_shareholder_funds | float | sharescart |
| pre_ipo_borrowings | float | sharescart |
| pre_ipo_total_assets | float | sharescart |
| pre_ipo_operating_cf | float | sharescart |
| pre_ipo_pat_margin_pct | float | derived |
| pre_ipo_ebitda_margin_pct | float | derived |
| pre_ipo_debt_equity | float | derived |
| pre_ipo_net_sales_growth_pct | float | derived |
| pre_ipo_pat_growth_pct | float | derived |
| pre_ipo_roe_pct | float | derived |
| pre_ipo_roce_pct | float | derived |
| pre_ipo_years_available | int | sharescart |
| has_post_ipo_financials | bool | derived |

## Provenance (derived)

| column | type | source |
|---|---|---|
| issue_price_src | str | derived |
| listing_open_src | str | derived |
| sub_total_x_src | str | derived |
| gmp_pct_src | str | derived |
| pat_yr3_src | str | derived |
| promoter_post_issue_pct_src | str | derived |
| market_maker_src | str | derived |
| ticker_src | str | derived |
| confidence | str | derived |
| confidence_reason | str | derived |
| isin_xchg_check | str | derived |

---

## Notes from Phase 0 exploration (Chittorgarh detail pages)

Chittorgarh detail pages provide (free): IPO Details (dates, face value), Total Issue Size /
Reserved-for-Market-Maker / Fresh Issue / OFS, Issue Reservation (NII/Retail offered shares & %),
IPO Lot Size, Company Financials (Restated — a compact assets/income block, present on most but
not all SME pages), Objects of the Issue, KPI (P/E, Promoter Holding Pre/Post), Issue Expenses,
and Listing Day Trading Information (final issue price + OHLC).

**Gated:** the IPO Subscription Status table renders only category headers — per-category
subscription times (QIB/NII/Retail) are NOT free. Only `sub_total_x` is obtainable from
Chittorgarh; the split comes from Sharescart (2023–2025 only).

**Available but unplanned (newly observed):** `face_value`, `issue_expenses_cr` (Issue Expenses
table), and `kpi_pe_pre_ipo` (KPI table P/E). `face_value` is included above; the others are noted
here as future-candidate columns, not yet in the locked schema.
