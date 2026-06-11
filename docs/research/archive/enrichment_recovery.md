# Enrichment recovery pass (research/staging only)

Run: `pipeline/research/enrich_recovery.py` (reuses `scrapers/screener.py` resolvers; 1 worker, 1.5s delay, resume-safe).
Audit trail of every attempt: `docs/research/enrichment_recovery_log.csv`.
**Did NOT touch `data/master/` or run pipeline 08/09** — staging only.

---

## Target 1 — the 24 boom-SME ISINs in `sector_mcap_skipped.csv`  →  24 / 24 RECOVERED (0 still no-match)

These were **never SME no-matches**. All 24 already have financials in `financials.csv` (they resolved in 03b),
and each BSE/NSE code resolves to a single live screener page. They were skipped by `03f` only because the company
**renamed**, so the page `<h1>` no longer name-matches the IPO-era name. The exchange code is the concrete identity
key (permanent through a rename — a face-value split would change the ISIN, not the BSE code), so accepting the page
by code is strict, not loose. Every old→new name is logged in the audit file. Examples:

| IPO-era name | resolved page (current) | broad_sector | mcap (cr) |
|---|---|---|---|
| Zomato Ltd. | Eternal Ltd | Consumer Discretionary | 240,439 |
| Burger King India | Restaurant Brands Asia | Consumer Discretionary | 3,962 |
| Macrotech Developers | Lodha Developers | Consumer Discretionary (Realty) | 90,165 |
| Angel Broking | Angel One | Financial Services | 31,008 |
| Adani Wilmar | AWL Agri Business | FMCG | 24,843 |
| Ami Organics | Acutaas Chemicals | Healthcare | 24,876 |
| Ruchi Soya FPO | Patanjali Foods | FMCG | 49,471 |
| Glenmark Life Sciences | Alivus Life Sciences | Healthcare | 12,982 |
| Schloss Bangalore | Leela Palaces Hotels & Resorts | Consumer Discretionary | 13,697 |

**24 confirmed rows appended to `data/raw/screener/sector_mcap.csv`** (same columns `isin,broad_sector,sector,industry,
market_cap_cr,source`; file 376 → **400** data rows). A re-run of `pipeline/08` folds them in via its existing
`sector_mcap.csv` read. **Status: fully RECOVERABLE, recovered.**

---

## Target 2 — the 12 `data_quality_tier=='low'` rows  →  1 partial / 11 not recoverable

Strict name-verified `resolve()`. Result: **1 fin-match (but unusable), 11 no-match.** Nothing usable to stage.

| isin | company | outcome | classification |
|---|---|---|---|
| INE475H01011 | Reliance Petroleum Ltd. | page found, financials all-zero/blank (FY2006-08 placeholders) | **legitimately absent** — delisted 2009 (merged into RIL); no real pre-IPO P&L on screener |
| INE0HPK01012 | DU Digital Technologies | NSE:DUDIGITAL → 404 | legitimately absent (SME, no screener page) |
| INE0DRT01018 | Fabino Life Sciences | BSE code now = "Fabino Enterprises Ltd" (different co) | flagged — code reassigned, do not mis-assign |
| INE07L501010 | DMR Hydroengineering | code now = "DMR Engineering Ltd" | flagged — different entity |
| INE0CWK01019 | Adishakti Loha & Ispat | code now = "AFLOAT Enterprises Ltd" | flagged — code reassigned |
| INE0EMB01015 | Rangoli Tradecomm | code now = "Suumaya Corporation Ltd" | flagged — different entity |
| INE0K5F01014 | Dhyaani Tile & Marblez | code now = "Dhyaani Tradeventtures Ltd" | flagged — renamed/repurposed, financials would be wrong |
| INE776C01039 | GMR Infrastructure | code = "GMR Airports Ltd" (restructured) | flagged — entity restructured |
| INE336C01016 | Rathi Udyog FPO | code = "Rathi Steel & Power Ltd" | flagged — uncertain identity |
| INE438H01019 | Deccan Aviation | code = "Kingfisher Airlines Ltd" | **legitimately absent** — Deccan absorbed into Kingfisher (both defunct); page financials are Kingfisher's, NOT Deccan's |
| INE347H01012 | JRG Securities | code = "Inditrade Capital Ltd" | flagged — renamed; identity not confirmable |
| INE296H01011 | Emkay Share & Stock Brokers | code = "Emkay Global Financial Services" | likely-same but pre-IPO FY off screener (2006 IPO) |

The 1 "fin recovery" (Reliance Petroleum) was reset out of staging — its values are zero placeholders, not a real
pre_ipo_pat. **Nothing for Target 2 was staged.** These 11-12 are dominated by **legitimately-absent** (delisted/old,
no real screener page) or **code-reassigned-to-a-different-company** cases where filling would mis-assign — correctly
left as gaps per the flag-don't-mis-assign rule.

---

## Target 3 — longterm pre-IPO-financials gap (sample of 40 of 486)  →  DEFER the full grinder

Pool: **486 longterm rows missing `pre_ipo_pat`** (all have an exchange code). Sampled every-12th = 40, name-verified `resolve()`.

Raw sample: **18/40 resolved, 14/40 had any PAT, 22/40 no-match.** A naive read = 35% PAT hit-rate → ~170/486.
**That estimate is wrong** — two structural facts kill the real yield:

**(a) Screener only keeps ~12 years of annual history → the pre-IPO FY is off the front for old listings.**
Every one of the 14 "PAT-match" sample hits returned **FY2015-2026 only**. But these are 2006-2007 IPOs whose
pre-IPO FY is 2005/2006 — `pre_fy_pat_present=False` for all of them. `pipeline/08` reads only the pre-listing FY,
so it gets **nothing usable** from any of these. The page resolves; the data we need does not exist on it.

Breakdown of the 486 by era:
- **303 listed 2006-2011** → pre-IPO FY is before screener's window → **legitimately absent** (not a pull gap).
- **169 listed 2012-2019** → pre-IPO FY *is* within screener's ~12yr window → the only genuinely recoverable subset.
- 14 no listing date.

**(b) 342 of the 486 already have a screener page** (present in `financials.csv` from 03b). For those, missing
`pre_ipo_pat` means **screener lacks that specific old FY**, not that we failed to pull — re-pulling yields nothing.
Only **144 never resolved**, and most of those are the 22/40 no-match pattern: ~90% are renamed/merged/repurposed
(e.g. Binani Cement→UltraTech Nathdwara, Deccan→Kingfisher, Astral Poly Technik→Astral, Capacit'e→Capacite,
Shriram EPC→SEPC). The cosmetic renames are recoverable; the merged/acquired ones are **unsafe** (the page's
financials belong to the acquirer, not the IPO company) and must stay flagged. Only **2/22 were true 404s.**

**Realistic full-set yield for `pre_ipo_pat`:** confined to the **169 newer (2012-2019)** listings, and within those
only the ones not already resolved-without-the-FY. Best-case a few dozen rows, most via accepting cosmetic renames
(needs a code-verified accept path like Target 1, not the current strict name_match). The old 303 are
**legitimately-absent and should not be counted as fixable.**

**Recommendation: DEFER the full grinder.** High wall-clock (486 throttled fetches), and the headline 35% is an
illusion — true usable pre_ipo_pat yield is low and concentrated in the 2012-2019 slice. If pursued later, run a
**code-verified rename-accept pass (Target-1 style) scoped ONLY to the 169 listed 2012-2019**, and explicitly skip
merger/acquisition renames. Nothing from the longterm sample was staged (`financials_longterm_extra.csv` reset to
header-only — every sampled hit was already in `financials.csv` and carried no pre-IPO FY).

---

## Tally

| target | recoverable & recovered | legitimately absent / unsafe | staged |
|---|---|---|---|
| 1. boom-SME (24) | **24** sector+mcap | 0 | +24 rows → `sector_mcap.csv` |
| 2. low-tier (12) | 0 usable | 11-12 (delisted / code-reassigned / pre-FY off screener) | none |
| 3. longterm pre_ipo_pat (486) | small, ~169-row 2012-2019 slice only | 303 old (pre-FY off screener) + 342 already-resolved-no-FY | none (defer) |

**Recoverable-vs-absent headline:** Target 1 was a mislabeled-as-skipped set that is now 100% recovered. Targets 2
and 3 are dominated by **legitimately-absent** data (delisted/old companies whose pre-IPO FY predates screener's
~12-year window, or BSE codes since reassigned to a different company) — these are NOT fixable and should not be
counted against data completeness.
