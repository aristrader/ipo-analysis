# Pre-IPO financials for OLD longterm IPOs — source feasibility + recovery (research/staging only)

Goal: recover `pre_ipo_pat` / `net_sales` for the latest pre-listing fiscal year for longterm IPOs that
screener.in cannot serve. **No `data/master/` edits, no 08/09 run.** Recovered hits stage to
`data/raw/screener/financials_longterm_extra.csv` (`isin,fy,metric,value`).

## The gap (data/master/ipo_analysis.csv, cohort=='longterm', pre_ipo_pat null)

| slice | rows | recoverability |
|---|---|---|
| **2012–2019 listings** (in-window) | **168** | screener via name-search + permanent-code rename-accept |
| **2006–2011 listings** (pre-window) | **303** | screener cannot serve → alternative source needed |
| no listing date | 14 | — |
| no exchange code | 0 (all 486 have a BSE and/or NSE code) | — |

## The hard boundary: screener keeps **FY2015 → FY2026** only (verified June 2026)

Empirically checked on INFY / TCS / RELIANCE: every page's earliest annual FY is **Mar-2015**. So the only
screener-recoverable rows are those whose **pre-listing fiscal year (FY) >= 2015**, regardless of how clean the
identity match is. Pre-listing FY = last completed March before the listing date (listing month >= Apr → FY = listing year, else listing year − 1).

Splitting the 168 in-window rows by pre-listing FY:
- **81 have preFY >= 2015** → screener-serveable. ← the genuinely recoverable slice.
- **87 have preFY 2011–2014** → below screener's floor → NOT recoverable via screener (even though the listing is "in window").

This is the key correction to the prior `enrichment_recovery.md` estimate: "in-window listing" is not the same as
"in-window pre-IPO FY". The recoverable count is gated by **preFY**, not listing year.

## Screener recovery result (2012–2019 slice) — 61 / 81 recovered

`pipeline/research/recover_inwindow_financials.py` — code-verified rename-accept (Target-1 style): fetch by BSE
code then NSE symbol; accept the page by the **permanent exchange code** (a rename keeps the code; only a
face-value split changes the ISIN), recording `name_ok` and the page name for human veto. Audit:
`docs/research/longterm_inwindow_log.csv`.

| outcome | count | notes |
|---|---|---|
| **STAGED (preFY present, with PAT)** | **61** | all preFY 2015–2019; all carry net_profit; all via code-verified rename-accept |
| page-found-but-preFY-off-window | 6 | page resolves but earliest FY > preFY |
| no-page / no-financials | 14 | 404 on both codes, or merger/acquisition (page = surviving entity, unsafe) |

The 61 are already in `data/raw/screener/financials_longterm_extra.csv` (61 ISINs, 1,222 rows, FY2013–2019,
146 net_profit rows incl. trajectory years preFY-2..preFY). **This re-run added 0 new rows** — the 87 remaining
in-window rows all have preFY 2011–2014, below screener's FY2015 floor, so there is no screener candidate left
to fetch. The screener-recoverable in-window slice is **exhausted**.

## Alternative sources for the OLD ones (303 @ 2006–2011, plus the 87 in-window @ preFY 2011–2014)

Tested whether structured pre-IPO financials exist for free for pre-FY2015 fiscal years.

| source | structured financials? | archive depth | verdict |
|---|---|---|---|
| **BSE corporate-announcements / financial-results API** (`api.bseindia.com/.../AnnGetData`, `strCat=Result`) | No — results are **PDF attachments** (NEWSSUB + ATTACHMENTNAME), not parseable tables | **floor ~FY2011**: querying RELIANCE (500325) returned 0 result-announcements for 2008/2009/2010, first hit in **2011** | **Not usable.** Too shallow (misses 2006–2010) AND unstructured (PDF). |
| **BSE `Comp_Results` financials endpoint** (structured P&L by scrip) | Would be structured if reachable | — | endpoint **redirects to `error_Bse.html`** for all variants tried (Comp_ResultsType / getFinancialData / Comp_GetFinancialResult); needs a session cookie/token we don't have. Even if reached, the front-end only renders recent years. **Not usable for 2006–2011.** |
| **NSE financial archives** | Same model as BSE — financial results are filing PDFs, no structured back-history | shallow, recent-years only | **Not usable** for 2006–2011. |
| **SEBI public-issues archive** (`sebi.gov.in/filings/public-issues.html`) — DRHP/RHP | **Yes, the data EXISTS** — every prospectus contains 3–5 years of audited pre-IPO P&L incl. the pre-listing FY | goes back to **2006–2007** (e.g. DLF 2007 referenced) | **Authoritative but PDF-only.** Each company = one ~300–600pp PDF; pre-IPO P&L lives in the "Financial Statements"/"Summary Financial Information" section. Extraction is **per-document manual/OCR**, not a structured pull. Effort: ~5–15 min/company → **~30–100 hrs for 303**. Do NOT mass-scrape (large PDFs, SEBI rate-limits). |
| **chittorgarh** prospectus list | Links to the same SEBI/exchange DRHP/RHP PDFs | back to ~2007 | same PDF-extraction effort as SEBI; no structured financials of its own. |
| **moneycontrol** | Structured P&L pages, but the free view truncates to ~recent years; older years gated/inconsistent and **no stable free API** | varies | unreliable for 2006–2011; not a clean programmatic source. |
| **tijorifinance** | Structured, but **login-gated** and limited free history; not free-tier for deep back-data | — | not viable free. |
| **trendlyne** | Structured financials but **login/paywall** for deep history | — | not viable free. |

## The 2006–2011 verdict

**Structured, free, programmatic pre-IPO financials for 2006–2011 IPOs do NOT exist.** BSE/NSE results archives
are both too shallow (floor ~2011) and unstructured (PDF). The only place the numbers reliably exist for that era
is the **DRHP/RHP PDF on SEBI's public-issues archive** — authoritative, but a PDF the pre-IPO P&L must be read out of
by hand or by a bespoke PDF parser. For 303 companies (+ the 87 in-window preFY-2011–2014 rows that screener also
can't serve = **390 total**), that is a **manual PDF-extraction project of ~30–100 hours**, not a scrape.

## Recommendation

1. **Stop here for the automated path.** The screener in-window slice is exhausted at 61 recovered; nothing more is
   free-and-structured. Treat the remaining **390** (303 @ 2006–2011 + 87 in-window preFY<2015) as
   **legitimately-absent for free structured sources** — the data exists only inside DRHP PDFs.
2. **If pre-IPO financials for the old cohort are truly needed for Layer 3:** scope a small **DRHP-PDF extraction**
   pass via the SEBI public-issues archive — but prioritise by analysis value (e.g. only the largest issues, or only
   rows a specific rule needs), since full coverage is ~30–100 hrs. Verify identity by ISIN/issuer name on the cover
   page (DRHP states ISIN), and record `pre_ipo_pat`,`net_sales`,`fy` + the SEBI PDF URL as provenance.
3. **Do not** use BSE/NSE results PDFs or moneycontrol/tijori/trendlyne for back-fill — shallow, gated, or
   unstructured with no free programmatic access.

## Recovered output

- `data/raw/screener/financials_longterm_extra.csv` — 61 in-window ISINs (code-verified rename-accept), with their
  pre-listing FY net_profit/sales + trajectory years. Folded by pipeline `08`/`09` via the existing
  `financials*.csv` read (NOT run here).
- Audit: `docs/research/longterm_inwindow_log.csv` (per-ISIN: page name, name_ok flag, preFY present, pat, verdict).
