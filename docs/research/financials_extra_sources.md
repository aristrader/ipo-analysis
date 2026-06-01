# Additional FREE sources for OLD (2006–2014) pre-IPO financials — probe + verdict (research only)

**Date:** 2026-06-01 · **Scope:** find/feasibility-test sources OTHER than DRHP PDFs for the pre-listing-year
`net_sales` + `pat` of the ~400 longterm IPOs (2006–2014) whose pre-IPO financials are missing — to (a) raise
coverage and (b) give a second source to CROSS-CHECK the DRHP-extracted numbers. **THINK + PROBE only. No repo
data/code touched.** Complements `drhp_recovery.md` (DRHP-PDF pass) and `drhp_feasibility.md`.

All findings below are from **real fetches** (curl + HTTP status + content inspection), not speculation. Network
was up; probes were small (a few fetches per source) and rate-limited.

## TL;DR

There is **one materially new free source worth a real pass: chittorgarh's own IPO pages**, which carry an inline
`Company Financials (Restated)` table with the pre-IPO fiscal years — *and chittorgarh is already a repo source
with the page URL (`detail_url`) + `chittorgarh_id` stored for all 1,029 longterm IPOs*, so there is zero
"locating" cost (unlike DRHP, where WebSearch-locating is the bottleneck and can mis-hit). **The catch:** the
inline table is only in chittorgarh's **legacy page template** (the oldest ~20–30 IPO ids, the 2006 vintage);
from id ≈40 onward (≈2010+) the page is React/Next.js and the financials are client-fetched (no inline table, no
embedded JSON, no public AJAX endpoint discoverable via curl). So chittorgarh is a **high-value but small-yield**
win: a clean, free **cross-check** for the oldest tranche, not a cohort-wide replacement.

Everything else probed is a dead end for this gap (gated, truncated, paywalled, or PDF-only floored). **DRHP PDFs
remain the only cohort-wide free source.**

## Ranked source table

| # | Source | Free? | Era floor (reaches pre-2015?) | Structured / extractable? | Blocks / friction | Est. yield for our 2006–2014 gap | Effort |
|---|--------|-------|------------------------------|---------------------------|-------------------|----------------------------------|--------|
| 1 | **chittorgarh IPO page — inline "Company Financials (Restated)"** | ✅ | ✅ reaches 2002–2006 (legacy pages); pre-IPO FYs present | ✅ clean inline HTML table, trivially regex/parse-able; **URL already in repo** (`detail_url`/`chittorgarh_id`) | Inline table only on LEGACY template (id ≲ 20–30 ≈ 2006 vintage). id ≥40 = React, no inline data | **Low (~15–30 rows)** but a clean CROSS-CHECK; matched Inox FY05 PAT ₹7.22cr exactly | **Low** for the legacy slice |
| 2 | **DRHP / RHP PDFs (SEBI + BSE archive)** — *the existing pipeline* | ✅ | ✅ to 2006 (and earlier) | ✅ born-digital text → pdfplumber; gate-verified | LOCATING is the bottleneck (WebSearch, mis-hits); per-PDF parse cost | **High (a few hundred, diminishing on SME tail)** | Moderate (built; semi-auto + human review queue) |
| 3 | moneycontrol historical P&L | ✅ (view) | ❌ **floor ≈ Mar 2011** (same as screener-class); P&L is JS/AJAX-rendered, no year tokens in static HTML | ✗ not in static HTML; needs a headless browser | JS render; WebFetch BLOCKED in this env | **~0 for 2006–2010; thin for 2011–2014** | High (browser) for ~nil gain → not worth it |
| 4 | BSE financial-results archive / API | ✅ | ❌ quarterly-results era only (~2011+), and it's *results* not the RHP restated pre-IPO P&L | partial (API needs auth headers; public API 302/redirects on probe) | api.bseindia.com 302s; needs session/headers | **~0** (wrong artifact + too-recent floor) | High → dead end |
| 5 | NSE historical financials | ✅ | site root 403 to scripted UA; financials are NSE-only quarterly era, not pre-IPO restated P&L | ✗ | 403 to curl without cookie handshake | **~0** | dead end |
| 6 | **MCA / MCA21** company filings | ❌ **NOT free** (₹100/company "View Public Documents") | ✅ reaches old filings | XBRL/PDF; needs MCA's validation tool to render XBRL | Paywall + login + per-company fee + portal friction | n/a (not free) | dead end (cost) |
| 7 | tijori finance | partial | free tier = **latest data only**; historic is paid (₹3,500/yr) | n/a free | gated | **~0 free** | dead end (free) |
| 8 | trendlyne | partial | free tier truncated; deep history gated | n/a free | gated | **~0 free** | dead end (free) |
| 9 | screener.in | ✅ | ❌ **floor Mar 2015** (already exhausted; see drhp_recovery.md) | ✅ but floored | — | **0** (re-confirmed) | dead end (re-confirmed) |
| 10 | Financial-press archives (BS / ET / moneycontrol news) | ✅ | mixed; articles exist but rarely state full net-sales+PAT for the exact pre-IPO FY | ✗ unstructured prose; not citable per-figure | search noise; figures partial/absent | **low + unreliable** (per-figure prose, no table) | High, low/unreliable yield → not worth a systematic pass |
| 11 | archive.org of old company IR pages | ✅ | varies | ✗ unstructured, per-company manual | very high per-company effort | **negligible at scale** | dead end at scale |

## Per-source notes (the evidence)

### 1. chittorgarh IPO page — the one real new win (cross-check, small yield)
- The IPO page embeds `Company Financials (Restated)` as a clean inline HTML table with the pre-IPO fiscal years.
  Verified examples (real fetches, HTTP 200):
  - **Inox Leisure** (`/ipo/inox-leisure-ipo/2883/`): Period Ended 30 Sep 2005 / 31 Mar 2005 / 31 Mar 2004 /
    31 Mar 2003 — Total Income 63.77cr, **PAT 7.22cr (FY05)**, Net Worth 59.03. → **matches the DRHP-extracted
    Inox FY05 PAT of ₹7.22cr in `drhp_feasibility.md` exactly** — proves it is a valid independent cross-check.
  - **Gayatri Projects** (id 11): Restated **Consolidated**, FY2002–FY2006, Total Income 309.89→376.41.
  - **Action Construction Equip** (id 4), **Fiem** (id 10), **JHS Svendgaard** (id 13), **Voltamp** (id 1),
    **Usher Agro** (id 7, fiscal year ends Jun/May — non-March, table still clean): all had the inline table.
  - Legacy-template probe: **6/6 of the oldest ids (1–13) and id=20 carried the inline table.**
- **Labels present:** `Total Income`, `Profit After Tax`, `Net Worth`, `Total Borrowing`, `Assets`, units
  `Amount in ₹ Crore`. Note it is **Total Income** (not "net sales") and sometimes **Consolidated/restated** — same
  caveat as DRHP: revenue-line label varies; reconcile definitions before trusting equality with DRHP "net sales".
- **The boundary (why yield is small):** the inline table lives only in chittorgarh's **legacy template**. Sweep:
  id 20 = inline table present; id **40, 60, 80, 100, 200, 250, 300, 450, 600, 750, 900, 1000** = **React/Next.js
  page, NO inline table**, no `__NEXT_DATA__` financials blob, `Total Income`/`PAT` absent from static HTML.
  Boundary is by **page template (id), not IPO date** — only the first ~20–30 ids (2006 vintage) qualify.
- **No public AJAX endpoint:** guessed financial-data endpoints (`/documents/ipo/financials/<id>`,
  `/api/ipo/financials/<id>`, `*.asp?id=`) returned 308-redirects or 404. The React pages fetch financials from a
  non-trivially-discoverable client endpoint; not curl-able in this probe.
- **Repo-readiness:** `data/raw/chittorgarh/details_longterm.csv` already has `chittorgarh_id` + `detail_url` for
  **all 1,029** longterm rows — so for the legacy slice there is **zero locating cost** (the DRHP pipeline's main
  pain). A tiny scraper over the ~20–30 legacy URLs would harvest a clean cross-check set in minutes.
- **Bonus (helps the DRHP pipeline, not a financials source):** the React IPO pages expose the **SEBI public-issues
  landing-page URL directly in their anchors** (e.g. Muthoot → `sebi.gov.in/filings/public-issues/apr-2011/...`).
  That eliminates the WebSearch mis-hit/locating risk in `drhp_recovery.md` for any cohort row whose chittorgarh
  page is the React template — worth wiring into the DRHP locator.

### 3. moneycontrol — truncated + JS-rendered (confirmed, not just inherited)
- Fetched the actual P&L page (`/financials/inoxleisure/profit-lossVI/IL03`, HTTP 200, 700KB) **and** its
  paginated `/2` variant (HTTP 200) **and** the old-format `/profit-loss/` (301). **No fiscal-year column tokens
  (`Mar 20xx`) in the static HTML** in any variant — the table is JS/AJAX-hydrated. WebFetch (which would render)
  is BLOCKED in this env. Independent of that, moneycontrol's documented depth is ~last decade, floor ≈ Mar 2011 —
  below our 2006–2010 bulk. Verdict: needs a headless browser for ≈0 incremental coverage. **Not worth it.**

### 4–5. BSE / NSE — wrong artifact + too-recent floor
- BSE: `bseindia.com/downloads/IPO/` root = 404 (but a *specific* old IPO PDF, the cited Jubilant RHP, still
  serves 200/6.3MB — i.e. BSE is a *PDF host* for the existing DRHP path, not a structured-financials source).
  The corporate-results page redirects to a quarterly-results UI (era ≈2011+); the JSON API
  (`api.bseindia.com/.../Corpresults`) **302-redirects** without a session — and it serves quarterly *results*,
  not the RHP's restated pre-IPO P&L. NSE root 403s to a scripted UA. Both = **dead ends** for this gap.

### 6. MCA / MCA21 — **not free**
- "View Public Documents" charges **₹100 per company per year**, requires login, and XBRL filings need MCA's own
  validation tool to render. Reaches old filings, but it is **paywalled + high-friction** → out of scope (free only).

### 7–9. tijori / trendlyne / screener — re-confirmed gated/floored
- **tijori:** free tier = *latest data only*; historic behind ₹3,500/yr. **trendlyne:** deep history gated.
  **screener:** floor **Mar 2015**, already exhausted (`drhp_recovery.md`). No new win.

### 10–11. Financial press / archive.org — unstructured, unreliable per-figure
- News articles at listing time mention valuations/highlights but rarely state the full net-sales **and** PAT for
  the **exact** pre-IPO FY in a citable, structured way; archive.org IR pages are per-company manual. **Not a
  systematic source**; at best a last-resort manual lookup for a stubborn individual name.

## Recommendation

1. **Do a small real pass on chittorgarh's legacy IPO pages (Source #1).** It is free, already-located (URLs in
   repo), trivially parseable, and gives an **independent cross-check** for the oldest 2006-vintage tranche
   (~15–30 rows) — and it already validated against the DRHP Inox figure. High confidence, low effort. Treat it as
   a **cross-check + small coverage top-up**, NOT a cohort-wide source.
2. **Wire the SEBI landing-page URL that chittorgarh's React pages expose into the DRHP locator** (Source #1 bonus)
   — it removes the DRHP pipeline's WebSearch mis-hit risk for cohort rows. This *improves the existing best
   source* rather than adding a new one.
3. **Everything else is a dead end** (don't re-research): moneycontrol (truncated + JS), BSE/NSE APIs (wrong
   artifact + too recent), MCA (paywalled), tijori/trendlyne/screener (gated/floored), press/archive.org
   (unstructured/unreliable).

## Final answer
The best ADDITIONAL free source is **chittorgarh's own IPO pages' inline "Company Financials (Restated)" table** —
but realistically only for the **oldest ~2006-vintage tranche (~15–30 of our gap rows)**, because the table is
present only on chittorgarh's legacy page template; newer pages are React-rendered with no curl-able financials.
Its real value is as a **clean, zero-locating-cost cross-check** (it reproduced the DRHP Inox FY05 PAT exactly) and
a small coverage top-up. **For the bulk of the 2006–2014 gap, DRHP/RHP PDFs remain the only viable free source.**
