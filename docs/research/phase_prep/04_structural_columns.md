# 04 — Structural columns (Phase 2): instrument_type, date-ordering, market-cap

## 1. instrument_type — the IDR mislabel CONFIRMED, and it's a 1-row fix
- Current values: `equity 2329 / fpo 38 / reit 9 / invit 8` (= 2,384). **No `idr` rows exist.**
- **`Standard Chartered PLC IDRS` is labelled `instrument_type='equity'`** (board=MB, `issue_amount_cr=0` — it's
  also the lone issue_amount_cr=0 row). This is the D7/OD-6 mislabel. **Phase-2 fix = relabel this 1 row to
  `instrument_type='idr'`** (the registry already lists `idr` as an allowed value). After the fix, the
  equity-only WHERE-view correctly excludes it.
- Non-equity total to exclude from equity analyses: 38 fpo + 9 reit + 8 invit + 1 idr = **56 rows**
  (the registry's `applicability: equity` gate). Matches the non-equity decision ([[foundation-nonequity-decision]]).

## 2. Date-ordering (O-11) — confirmed exactly as spec
- `open_date > close_date`: **0**. `close_date > listing_date`: **3** — `20 Microns` (2008), `Veto Switchgears`
  (2012), `GCM Commodity` (2013). `listing_date` NULL: **14**.
- close→listing gap: median 8d, p99 28d, **15 rows >30d, max 140d** (Vaswani per spec).
- **Phase-2 rule (CR-date):** whole-chain `open ≤ close ≤ listing` validity gate (applicability = all-three-present
  AND has_price_history), identifying WHICH bound is violated; resolve the corrupt field against the first row of
  `data/prices/<isin>.csv`; era-calibrated close→listing bound (~30d is a good flag threshold; the 15 >30d rows
  are review candidates, not auto-errors — some long gaps are real for older/SME IPOs).

## 3. market_cap_cr / kpi_market_cap_post_ipo — unreliable, but the predictor already excludes them
- `kpi_market_cap_post_ipo` gross parse error confirmed: **HDFC AMC = ₹7.8cr vs ₹2,800cr issue** (the canonical
  O-mcap-val case). This field is UNVETTED — do not adopt as the at-IPO primary without a parse-quality pass.
- `market_cap_cr` (current) has wrong-entity contamination (see doc 05, Bajaj Corp ₹292,355cr) AND missing/zero
  values (Bansal Multiflex, Supreme Impex mc=0 with a live price). **It is `as_of: current` in the registry →
  display-only, NEVER feeds the predictor** — so the leak is structurally contained; but as a *displayed* number
  it needs the wrong-entity + zero cleanup (doc 05) before it's shown with confidence.
- **The at-IPO market cap stays BLOCKED on `shares_outstanding` (BL-1)** — the as-of mechanism is done, but there
  is no trustworthy at-IPO cap value yet (honestly absent, not sourced). No change tonight.

## 4. board / cohort
- board(type): SME 1,471 / MB 913. cohort is config-derived from listing_date (not stored truth) — the
  `COHORT_BOUNDARY = 2020-01-01` split is in `foundation/config.py`. No anomalies found.

## Action items into Phase 2
1. Relabel Standard Chartered → `instrument_type='idr'` (1 row). ✅ trivial, do in the structural pass.
2. Implement CR-date whole-chain validity (3 hard violations + 14 null + 15 long-gap review).
3. Defer market_cap cleanup to doc 05 (identity) + BL-1 (at-IPO cap).
