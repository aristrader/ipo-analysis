# DRHP/Prospectus feasibility spot-check — pre-IPO P&L for OLD IPOs (2006–2011)

**Date:** 2026-06-01 · **Scope:** spot-check only (NOT a build). Can we get latest pre-listing-year
`net_sales` + `pat` (₹cr) for the ~303 longterm IPOs (listing 2006–2011) where `pre_ipo_pat` is null,
from the SEBI prospectus PDFs? Is it EASY / MODERATE / HIGH-EFFORT?

**Method:** Picked 3 recognizable mainboard names from `data/master/ipo_analysis.csv`
(`cohort=='longterm'`, listing year 2006–2011, `pre_ipo_pat` null, FPOs excluded). For each: find the
prospectus free online, assess extraction difficulty, and pull the actual figures. Also confirmed the
"free structured sources don't have it" claim.

## Tooling note (important for any future build)
- **WebSearch** works and reliably surfaces the SEBI filing landing page (`sebi.gov.in/filings/public-issues/<mon-year>/<co>_<id>.html`).
- **WebFetch is BLOCKED** in this environment (permission denied) AND cannot parse PDF text even when allowed
  (returns raw binary). It is NOT the extraction path.
- **The working path is `curl` + local `pdfplumber`:** SEBI serves the PDFs at
  `https://www.sebi.gov.in/sebi_data/attachdocs/<numeric_id>.pdf` (HTTP 200, ~3–6 MB each, no auth, no
  rate-limit hit in this test). All 3 PDFs were **born-digital text (NOT scanned)** → `pdfplumber` extracts
  clean tables, **no OCR needed**. `pip install pdfplumber` was required (not in the venv).
- **Caveat — opaque filenames:** the `attachdocs/<id>.pdf` IDs are non-semantic. A WebSearch result PDF can be
  the WRONG company (see Sadbhav below). The reliable key is the **SEBI landing-page HTML**, from which you
  scrape the single embedded `attachdocs/...pdf` link (curl the .html, grep `attachdocs/[0-9]+\.pdf`).

## Test IPO 1 — Inox Leisure Ltd. (listed 2006-02-23, mainboard)
- **DRHP/Prospectus found?** YES. SEBI landing page:
  `https://www.sebi.gov.in/filings/public-issues/jan-2006/inox-leisure-ltd_11198.html` →
  PDF: `https://www.sebi.gov.in/sebi_data/attachdocs/1292477212251.pdf` (Prospectus dated Feb 7, 2006, 283pp, 3.4 MB, text).
- **Extraction difficulty:** EASY. "Summary statement of Profits and Losses, as restated" is a single clean
  table (PDF page 172). Note: pp.138–141 are *promoter-group* companies (GFL/IGSL) — must target the page
  headed "INOX LEISURE LIMITED … as restated", not the first table that matches.
- **Values pulled (latest pre-listing FY = FY ended Mar 31, 2005):**
  - Net Sales & Services = **₹614.82 million = ₹61.48 cr**
  - PAT (restated) = **₹72.24 million = ₹7.22 cr**

## Test IPO 2 — Sadbhav Engineering Ltd. (listed 2006, mainboard)
- **DRHP/Prospectus found?** PARTIAL / friction. No 2006 public-issue landing page surfaced in SEBI's index
  (only its 2010 rights issue and the 2015 Sadbhav *Infrastructure* IPO appear). The top WebSearch "PROSPECTUS
  Dated August 07, 2006" PDF (`attachdocs/1292308122806.pdf`) **was actually GMR Infrastructure's prospectus**,
  not Sadbhav — a real mis-hit caused by opaque SEBI filenames + a same-day GMR issue.
- **Extraction difficulty (of the doc once correctly identified):** EASY — the GMR PDF I downloaded was 450pp
  born-digital text with a clean "Summary of restated Profit and Loss Account" table (page 210), so the
  *format* is trivially parseable. Finding the *correct Sadbhav* PDF, however, took extra effort and was not
  resolved in this timeboxed spot-check.
- **Values pulled:** none for Sadbhav (wrong-company PDF). [For reference, the mis-fetched GMR FY2006 table was
  fully extractable: Operating Income 574.39 mn, PBT 355.07 mn.] Sadbhav's true FY2006 figures remain to be
  pulled from the correct PDF (likely locatable via the BSE IPO archive `bseindia.com/downloads/IPO/...` or a
  tighter SEBI search).

## Test IPO 3 — Jubilant Foodworks Ltd. (listed 2010-02-08, mainboard)
- **DRHP/RHP found?** YES, trivially. RHP hosted on **BSE**:
  `https://www.bseindia.com/downloads/IPO/2010115181247JFL RHP.pdf` (382pp, 6.3 MB, text). SEBI landing page
  also exists: `.../public-issues/jan-2010/jubilant-foodworks-limited_5553.html`.
- **Extraction difficulty:** EASY. "Annexure II – Restated Summary Statement of Profit and Loss Account" is a
  clean table (PDF page 178). (Watch out for a subsidiary JEPL table on p.156 — target the issuer's annexure.)
- **Values pulled (latest pre-listing FY = FY ended Mar 31, 2009):**
  - Sales (Net) = **₹2,806.10 million = ₹280.61 cr**
  - PAT (Net Profit after Extraordinary Items, restated) = **₹67.43 million = ₹6.74 cr**

## Easier free alternatives — confirmed NOT viable for these years
- **screener.in:** fetched Inox Leisure's page directly — earliest P&L column is **Mar 2011**. FY2005–2008 are
  simply not on the page. (Screener only keeps ~last ~12 fiscal years.) Confirmed absent: Mar 2005/06/07/08.
- **moneycontrol:** WebSearch returned nothing usable for FY2005–06 Sadbhav P&L.
- Prior work's conclusion stands: **free structured sources do not expose pre-~2011 standalone P&L** for these
  old IPOs. The prospectus PDF is the only source.

## VERDICT: **MODERATE** (lean toward "scriptable, but budget for a manual fallback")

**Why not EASY:** When the doc is found and is the right company, extraction is genuinely trivial — born-digital
text, clean restated-P&L tables, `pdfplumber`, no OCR (2 of 3 done in minutes). PDFs are free, unauthenticated,
and curl-able straight from SEBI/BSE.

**Why not fully EASY (the friction is in LOCATING, not extracting):**
1. **No clean machine index from name → PDF.** SEBI's `attachdocs` IDs are opaque; the listing pages are
   JS-rendered (curl of `public-issues.html` yields no static links). You must go name → WebSearch →
   landing-page `.html` → scrape its embedded `attachdocs/...pdf`. WebSearch is the de-facto index, and it
   **mis-hit on Sadbhav** (served GMR), so a name/cover-page verification step is mandatory.
2. **Per-company table-shape variance.** Each prospectus labels the revenue line differently
   ("Sales & Services" / "Sales (Net)" / "Operating Income" / "Income from operations") and embeds
   subsidiary/promoter-group P&L tables that must NOT be mistaken for the issuer's. No single regex works for
   all ~303; expect a parser with a small set of patterns + a human spot-check.
3. Some won't be findable via SEBI alone and will need the BSE IPO archive or manual search.

**Recommended shape if pursued (not done here):** semi-automated pipeline — (a) WebSearch per company →
landing page → curl PDF; (b) verify cover-page company name + issue date; (c) `pdfplumber` locate the page
whose header contains the issuer name + "restated" + "Profit and Loss"; (d) regex the latest-FY revenue & PAT
(in ₹mn, ÷10 → ₹cr), tag units; (e) human review queue for the ~10–25% that fail auto-match (mis-hits,
odd labels, unfound docs). Plausibly a few focused days for ~303 names, NOT a one-liner — hence MODERATE,
not EASY. It is clearly worth doing if pre-IPO P&L is load-bearing for Layer 3 analogs, since no free
structured source covers these years.
