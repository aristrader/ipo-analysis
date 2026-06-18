# 11 — Per-field SOURCING & TRUST map (where each kind of data comes from, coverage, what's trustable)

Built from a review-agent sweep of the frozen substrate (2,384 rows) + `columns.yaml` + BUILD_SPEC Part A +
the `_src` columns. Partitions: cohort **boom 1357 / longterm 1027**; board **MB 913 / SME 1471**.

## The single most important structural fact
**Only 3 of the 15 `_src` columns are genuinely multi-source.** The rest are single-source attribution stamps:
- **multi-source** (a real cross-source pick happens): `sub_total_x` (sharescart 904 / nse 215 / ipowatch 136),
  `pat_yr3` (screener 1328 / sharescart 598), `gmp_pct` (ipowatch 689 / investorgain 333 / sharescart 55 / …).
- **chittorgarh-only** `_src` (the stamp means "chittorgarh or null"): `ofs_cr`, `fresh_issue_cr`, `ofs_pct`,
  `anchor_allocation_cr`, `issue_size_cr`, `market_maker`, all `listing_*`, `objects_of_issue`, `promoter_post`.
→ **Consequence for the cross-source match (ISS-7/8):** for most fields there is NO second source in the
substrate today. Corroboration there means re-parsing the raw (we have it) or accepting single-source-but-
authoritative. The 2-source match applies cleanly only to subscription / financials / GMP. (Tracked: ISS-40.)

## Source trust ranking (most → least authoritative)
| Rank | Source | Authoritative for | Caveat |
|---|---|---|---|
| 1 | **Exchange lists (NSE/BSE)** | symbol↔ISIN↔name identity, `listing_date` | the cross-check of record |
| 1 | **Bhavcopy (NSE/BSE EOD)** | all daily prices, adj listing-day, returns/alpha, MFE/MAE, liquidity, delisting terminal | official, ISIN-keyed, covers SME; 100% of `price_source` |
| 2 | **Chittorgarh (the SPINE)** | ISIN, dates, issue_price/size/amount, fresh/OFS, anchor, promoter, market_maker, raw listing OHLC, financials-fallback | the `_src` default; prefer exchange for `listing_date` |
| 3 | **Screener** | financials/KPIs (esp. longterm), sector | name-keyed → wrong-entity risk; CURRENT mcap leaks; boom TTM/PE only |
| 4 | **Sharescart** | boom band/lot/min-inv, boom subscription, GMP, boom financials, promoter% | boom-only; mints the `0x` placeholder bug; possible post-IPO financial contamination |
| 5 | **ipowatch** | SME subscription + GMP | only SME category source |
| 5 | **investorgain** | GMP (single ₹) | its cache has gmp=0 for the O-4 rows |
| 6 | **NSE Public Issues API** | MB subscription only — **EARLY SNAPSHOT, not final** (Antony Waste 0.5x, Radiant 0.53x); SME=0.00 always | treat 215 nse-sourced `sub_total_x` as suspect (ISS-6/7) |
| 7 | **Yahoo** | MB price fallback / symbol-only corp-action corroboration | poor for SME; action_type all "split" |
| — | **NOT viable (don't re-add)** | BSE official IPO API, ipocentral, trendlyne-scrape, moneycontrol financials | — |
| top | **Overlay** (manual_overrides 3 + corp audit tags + drhp 16) | highest priority in the fallback walk, conflict-flagged | — |

## Per-family source priority + coverage + trust (condensed)
- **IDENTITY:** isin/company_name/instrument_type 100%. `nse_symbol` 1685 (SME thin 807/1471), `bse_script_code`
  1704. `instrument_type` — **ISIN position-7 digit is authoritative** (`isin[7]=='2'` = the 18 trust/DR units,
  incl. the 1 mislabeled Std-Chartered IDR INE028L21018). `face_value` INVERTED: ~0% boom / 48% longterm.
- **OFFER MECHANICS:** issue_price/size/amount/fresh/ofs 99–100% (chittorgarh, authoritative; spot-verified
  Zomato ₹76, Nykaa ₹1125, LIC ₹949). `price_band_low`/`lot_size`/`min_investment`/`book_built` = **boom-only
  (0% longterm)**, from sharescart. **`issue_expenses_cr` = 100% EMPTY (dead).**
- **TIMETABLE:** open/close 100% (chittorgarh); `listing_date` **prefer exchange** (anchors cohort + as-of), 14 null.
- **DEMAND (weakest family):** `sub_total_x` 53% present, **only 9% of longterm**. Priority overlay → sharescart
  → NSE(MB) → ipowatch(SME). `gmp_pct` boom-only (0% longterm). `anchor_allocation_cr` 38% present.
- **FINANCIALS:** screener authoritative for longterm; sharescart fills boom (post-IPO contamination risk; no
  as-of attribute). Coverage cliff boom 97% vs longterm ~59%. TTM/PE fields **boom-only**. ~1000× share-base
  discontinuity in EPS is REAL (not a parse bug). `kpi_roce_pre_ipo` 100% empty; `kpi_roe` ~0%.
- **MARKET CAP:** `market_cap_cr` is **CURRENT → not predictor-safe (leaks outcome)**; `market_cap_at_ipo_cr`
  PLANNED (blocked on shares_outstanding BL-1) → **no predictor-legal cap exists today.**
- **SECTOR:** 63% present (888 blank), even boom/longterm; all 3 sector cols co-miss.
- **RETURNS/OUTCOMES (highest-trust enriched family):** bhavcopy-driven, ~88–100%; adj listing gains
  spot-verified (Eternal +51%, Nykaa +79%, LIC −8%). Horizon coverage decays (5y boom only 79). `price_source`
  100% bhavcopy. `delist_reason` only on 40 MB rows (SME absent).
- **QUALITY:** data_quality_tier 100% (high 2030/med 341/low 13). `confidence` + identity-check cols **boom-only**
  (1027 longterm never identity-checked). `ticker_needs_review` DEAD (100% empty).

## PRESENT-WHERE / ABSENT-WHERE (the coverage map)
- **Boom-only (≈0% longterm)** — the entire sharescart-enrichment + boom-identity-verification layer never ran on
  2006–19: `ticker_ns/bo`, `price_band_low`, `lot_size_shares`, `min_investment_rs`, `book_built`, `gmp_pct`,
  `sub_*_cr`, `pat_ttm_cr`, `sales_ttm_cr`, `eps_ttm`, `pe_ratio`, `promoter_pre/post`, `confidence`,
  identity-check cols, `name_at_ipo`, `official_isin_name`.
- **Longterm-only (≈0% boom):** `face_value`, the `kpi_*` longterm-fetch fields.
- **Well-covered everywhere:** identity, offer mechanics, timetable, the whole price/returns/liquidity/delisting
  family, data_quality tiers.
- **Weakest families:** subscription (53%, lt 9%), sector (63%), current market cap (64%, and leaks).

## Net guidance
- For analysis-critical at-IPO fields, **chittorgarh + exchange + bhavcopy are the trustable core** (99–100%, both cohorts).
- The **boom/longterm asymmetry is the dominant coverage truth** — any longterm finding stands on a much thinner
  feature set; subscription/GMP/band/lot/financial-TTM are essentially boom-only.
- **No predictor-legal market cap exists** until BL-1 (shares_outstanding).
