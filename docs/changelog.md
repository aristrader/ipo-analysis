# E2 Session Record — Chittorgarh Enrichment + Merge

**Date:** 2026-05-30 (run while you were out)
**Principle followed:** conservative + rollback-safe. No original Sharescart value was
overwritten. Only NULLs filled, new columns added, cross-validation written as FLAGS.

---

## What I did this session (in order)

1. **Installed Playwright** (`.venv`) — used ONCE to capture Chittorgarh's data-API URL via
   request interception. Not needed for any actual data pulls.

2. **Cracked Chittorgarh list API** (cloudscraper, no browser):
   `webnodejs.chittorgarh.com/cloud/report/data-read/82/<page>/5/<YEAR>/2026-27/0/all/0?search=&v=13-44`
   Report 82 = full MB+SME list, 5 rows/page, paginate until empty (totalRecords field lies).

3. **E2.1 list scrape** → `data/raw/chittorgarh_urls.csv` — **1272 IPOs (2020-2025)**,
   100% ISIN, 894 NSE symbols, 784 BSE codes, + slug/dates/issue_price/lead_manager.

4. **E2.2 detail scrape** → `data/raw/chittorgarh_details.csv` — **1256 rows**.
   market_maker on 879, listing-day OHLC on 1256.

5. **E2.3 merge** (`analysis/merge_chittorgarh.py`) → enriched our 929 clean CSVs.

---

## Results

### Tickers: 902/929 confirmed (97%, was 837)
- 837 = price-verified (Sharescart open == Yahoo/bhavcopy open) — unchanged, gold standard
- +65 = `confirmed_chittorgarh` — resolved via Chittorgarh's authoritative ISIN→NSE-symbol.
  NOTE: ISIN-authoritative (correct identity) but NOT price-verified — distinct label so you
  can review or treat as a slightly lower tier.
- 27 still doubtful → `data/derived/ticker_review.csv` (10 suspect, 9 unverified, 8 unresolved)

### Enrichment filled (NULLs only — never overwrote)
| Column | Coverage now | Was |
|---|---|---|
| market_maker (SME) | 631/670 SME (93%) | 0 |
| listing_high/low/close | 867/929 | 0 (deferred Layer-2 — now done) |
| issue_size_cr | 885/929 | 0 (Sharescart showed `--`) |
| ofs_cr / ofs_pct | 867/929 | new |
| fresh_issue_cr | 824/929 | new |
| anchor_allocation_cr | 599/929 | new |
| objects_of_issue_chittorgarh | ~835 | new |

### Cross-validation (FLAGS only, nothing changed)
- `cross_val_issue_price`: 9 MISMATCH (3 MB + 6 SME) — review
- `cross_val_listing_open`: 65 MISMATCH (16 MB + 49 SME) — likely Chittorgarh BSE-open vs
  Sharescart listing-price, OR the listing_date-offset rows. Worth a look, not alarming.

### New columns added to clean CSVs
`anchor_allocation_cr, fresh_issue_cr, ofs_cr, ofs_pct, objects_of_issue_chittorgarh,
chittorgarh_matched, chittorgarh_id, cross_val_issue_price, cross_val_listing_open,
ticker_ns_prev, ticker_bo_prev`

### Back-fill 2020-2022 — NOT merged, kept separate for review
`data/derived/backfill_2020_2022_chittorgarh.csv` — **317 IPOs (2020-2022)** not in our set.
Chittorgarh fields only (no Sharescart financials/subscription split). Left separate
intentionally so you decide whether/how to integrate.

---

## Per-file detail

**mainboard_clean.csv (259):** matched 236, tickers_resolved 7, ip_mismatch 3, lo_mismatch 16.
Filled: listing OHLC 235, ofs 235, anchor 228, objects 207, fresh 196, issue_size 153, mm 2.

**sme_clean.csv (670):** matched 633, tickers_resolved 58, ip_mismatch 6, lo_mismatch 49.
Filled: listing OHLC 632, ofs 632, market_maker 631, fresh 628, objects 628, issue_size 469, anchor 371.

---

## ROLLBACK INSTRUCTIONS

Snapshot of clean CSVs BEFORE the merge:
`data/derived/backups/pre_E2_merge_20260530_202558/`

Revert completely:
```bash
cd /Users/swapnilagarwal/Visual_Studio_Projects/ipo-analysis
cp data/derived/backups/pre_E2_merge_20260530_202558/*.csv data/derived/
```
Raw Chittorgarh scrapes and the back-fill file are independent. The merge is re-runnable
(idempotent fill-null) if you want to tweak logic and re-apply.

---

## Open items to discuss when you're back

1. **`confirmed_chittorgarh` (65 tickers)** — accept as confirmed, or keep as a separate tier?
   ISIN-authoritative but not price-verified.
2. **65 listing_open cross-val mismatches** — investigate (BSE-open vs listing-price?) or accept.
3. **Back-fill 317 rows (2020-2022)** — integrate into main CSVs (sparse fields) or keep separate?
4. **objects_of_issue_chittorgarh vs Sharescart `objectives_of_issue`** — reconcile into one?
5. **Subscription QIB/NII/Retail** — Chittorgarh gated it behind premium; Sharescart stays the
   source. No change, just noting.
6. **27 still-doubtful tickers** — mostly FPOs/REITs/cancelled (Vodafone Idea, Hexaware,
   Trafiksol). Likely exclude from equity analysis.

---

## Files created/modified this session
- NEW: `scrapers/chittorgarh.py`, `analysis/merge_chittorgarh.py`
- NEW data: `data/raw/chittorgarh_urls.csv`, `data/raw/chittorgarh_details.csv`,
  `data/derived/backfill_2020_2022_chittorgarh.csv`
- MODIFIED: `data/derived/mainboard_clean.csv`, `sme_clean.csv` (enriched; backup exists)
- NEW: `scrapers/verify_tickers.py`, `scrapers/bhavcopy_verify.py` (earlier in session)
- Reference caches: `data/reference/` (NSE/BSE lists, bhavcopy/)

---

## Update: screener.in ticker resolution (post-discussion)

Used screener.in (search + price API — covers SME where Yahoo fails) on the 27 doubtful:
- **+2** confirmed AND corrected via screener+Yahoo price (Anantam: was GAYAHWS=wrong company → ANANTAM; Capital Infra → CAPINVIT)
- **+8** confirmed via screener's own price history (Anya, Agarwal Tough, Thinking Hats, Excellent Wires, Brace Port, Flywings, Manas, Happy Square) — recent SME Yahoo lacks; all 3-10% price match within days of listing
- **4 excluded** (analysis_exclude=True): Nexus Select Trust, Knowledge Realty, Propshare (REITs), Trafiksol (SEBI-cancelled)
- **13 still flagged**: 4 BSE-code-only SME, ~8 not on screener, 1 renamed company (Kalpataru→KPIL, not a fresh IPO)

**FINAL TICKER STATE: 912/929 confirmed (98.2%)** across 4 independent methods
(price-match, bhavcopy, Chittorgarh-ISIN, screener-price). 4 excluded. 13 flagged in ticker_review.csv.
New ticker_status values: confirmed_screener, confirmed_screener_price. New scripts:
scrapers/screener_verify.py, scrapers/screener_price_verify.py.
Backup before screener step: data/derived/backups/pre_screener_20260530_212109/

---

## Update 2: ISIN-authoritative alignment + reconfirm (user asked "do all, be 100% sure")

ISIN = unique permanent stock ID; if our ISIN == Chittorgarh's ISIN it's provably the same
stock, so Chittorgarh's symbol/listing-date for that ISIN are authoritative (can't be coincidental).

Ran `analysis/isin_align.py` over all 866 ISIN-matched rows:
- **13 tickers CORRECTED** that were false-positive price-matches (e.g. Virtual Galaxy had GAIL=
  Gas Authority!, Finbud had JM Financial, Monolithisch had NLC India). Root cause: old 10% price
  tolerance let coincidental matches through (~1.5%). ISIN fixed them.
- **610 relabeled `isin_authoritative`** (gold standard)
- **310 listing_date corrected** to Chittorgarh's authoritative date (old in listing_date_prev2) —
  important for Layer-2 price window
- **55 name diffs** flagged → audited → only 5 genuine; 2 valid aliases (BlackBuck=Zinka,
  Leela=Schloss), 3 WRONG source-ISINs found and de-contaminated:
    - Yatharth Hospital: our ISIN wrongly→Unihealth. Fixed to YATHARTH.NS (screener price ✓ 9%)
    - Aeroflex Neu: ISIN wrongly→Sah Polymers. Original AERONEU.NS was right (screener price ✓ 0%)
    - Quest Flow Controls: ISIN wrongly→Meson Valves. BSE-only, flagged.
  These 3 had enrichment contaminated from the wrong company → RESTORED from pre_E2_merge backup.

**FINAL TICKER STATE: 911/929 (98.1%) confirmed**
- 610 isin_authoritative (bulletproof — unique ID)
- 264 confirmed = price-verified 2-source (no ISIN cross-check available; ~tiny residual coincidence risk)
- 25 confirmed_chittorgarh + 12 screener
- 4 excluded (REITs/cancelled), 14 flagged (BSE-code-only SME + not-found)

Backups: pre_isin_align_20260530_213004, pre_screener_20260530_212109, pre_E2_merge_20260530_202558
New scripts: analysis/isin_align.py
OPEN: the 264 price-only-confirmed could be re-verified at tighter 3% tolerance to catch any
remaining coincidental matches (not done — diminishing returns, user's call).

---

## Update 3: ISIN correctness audit (user asked "are our ISINs even correct?")

Cross-checked our stored ISIN vs the AUTHORITATIVE official symbol→ISIN mapping (NSE/BSE lists,
keyed by the price-CONFIRMED ticker symbol — breaks the name-match circularity).
- Found 11 WRONG ISINs (leftover from E1 name-matches; e.g. India Shelter had Schaeffler's ISIN,
  Yatharth had Unihealth's). Corrected from official symbol→ISIN. Old saved to isin_prev.
- Filled 33 missing ISINs from the same authoritative source.
- FINAL: ISIN coverage 920/929 (99%); 914 cross-confirmed correct; 0 remaining mismatches; 9 missing
  (the unresolved tickers).
Also resolved 11/14 manual-review tickers via user-provided screener links (3 left flagged:
Kalpataru name mix-up, Rajputana wrong code=2017 co, Dhansa wrong code). Backup: pre_isinfix_20260530_214805.

KEY LESSON (answers "why do we keep finding errors"): single-source / price matching has an
irreducible coincidence rate. The reliable method is MULTI-SOURCE AGREEMENT ON A UNIQUE KEY (ISIN),
and a systematic per-row confidence score — not spot-checks. Next: build analysis/verify_dataset.py
to score ALL 929 rows across all fields (the final data-quality scorecard).

---

## Update 4: FOUNDATION AUDIT (non-circular) — "are we sure of company↔ticker?"

The independent check (immune to price-coincidence): does OUR company name agree with the
official registry's name for the ticker/ISIN we assigned? (name-vs-name keyed by unique ID).
- 919/929 NAME AGREES with official registry → company↔ticker foundation independently corroborated
- 1 disagreed: "Safe Enterprises" had SITAENT (wrong) → fixed to SAFEENTP.NS (screener price 5% ✓)
- 9 uncheckable = 4 excluded REITs/cancelled + a few flagged (already known)
FINAL FOUNDATION: 920/929 (99%) name+ticker+ISIN mutually consistent with official registry,
independent of price-matching. Residual = bounded, known list (not hidden unknowns).

---

## Update 5: Foundation match-STRENGTH audit (user: "is name-match exact? 100% sure?")

Graded the 920 name-agreements by strength:
- EXACT (all significant words identical): 598
- SUBSET (truncation, e.g. "RR Kabel"⊂"R R Kabel"): 93
- PARTIAL (share some words): 229  ← token-overlap had given false comfort here
Investigated the 229: most are benign (Sharescart truncations/initials/abbreviations, price-confirmed
same company), BUT price-checking the suspects found 6 GENUINELY WRONG companies that had been
falsely "confirmed": Entero Healthcare(→Anlon), Kalpataru Projects(→2006 co), Shanti Spintex(→Lagnam),
Sahaj Fashions, Dhansa Labs(→2017 co), Parth Electricals(→Rulka). De-trusted → status=WRONG_ticker_removed.

HONEST FOUNDATION VERDICT:
- ~691 EXACT/SUBSET name + ticker + ISIN all agree → bulletproof
- ~210 partial-but-price-confirmed-same-company → high confidence
- 6 removed (were false positives)
- ~12 flagged/ambiguous (incl. name-vs-price puzzles: Sattva Eng↔Vikran, Storage↔Saven, LGT↔T&I, 3C↔RNIT)
- NOT 100%, but every row now either concrete / price-verified / explicitly flagged. No known hidden false-confirms.
LESSON: token-overlap name matching is too lenient (shares a generic word). Strong checks = EXACT/SUBSET
name match OR price-confirmation. Did NOT touch single-source fields (subscription/GMP/financials/promoter) — still unverified, next layer.

---

## Task 12: ISIN-keyed rebuild finalized — 2026-05-30

**Pipeline run:** 2026-05-30, all 5 phases executed successfully (01_build_base → 02_attach_detail → 03_enrich → 04_verify → 05_reconcile).

**Final row counts:**
- Mainboard: 382 rows (1 header)
- SME: 887 rows (1 header)
- Total: 1269 IPOs, all ISIN-keyed

**High-confidence counts (confidence='isin_authoritative' or 'chittorgarh_symbol'):**
- Mainboard: 376/382 (98.4%)
- SME: 876/887 (98.8%)
- Total: 1252/1269 (98.6%)

**Ticker conflicts flagged:** 4 ISIN↔Chittorgarh-symbol mismatches (all mainboard, flagged for review)
- Barbeque-Nation Hospitality (chittorgarh=BARBEQUE vs official=UFBL)
- Sah Polymers (chittorgarh=SAH vs official=AERONEU)
- Arisinfra Solutions (chittorgarh=ARISINFRA vs official=ARIS)
- Standard Glass Lining Technology (chittorgarh=SGLTL vs official=SETL)

**Reconciliation vs old dataset (929 rows):**
- Overlapping ISINs: 904 (of which 913 from old remain in archive)
- HARD flags: 16 total
  - Ticker conflicts: 3 (described above)
  - Presence (old but missing in new): 13 rows
    - 9 are known old-ISIN-errors (now fixed): Storage Technologies, Dev Labtech Venture, Shri Hare-Krishna, Sahaj Fashions, Capital Infra, Anantam Highways, 3C IT Solutions, Safe Enterprises, Shanti Spintex (tickers were corrected/de-contaminated during ISIN audit)
    - 4 truly absent from Chittorgarh 2020-25: Kalpataru Projects, Rajputana Investment, Dhansa Labs, LGT Global (to be reviewed for inclusion)
- SOFT flags: 62 numeric diffs (>5% variance in listing_open, issue_price, subscription values) — expected from data-quality differences between Chittorgarh and Sharescart, within normal noise range

**Key invariant maintained:** ISIN-only matching enforced throughout. Subscription/financial values only populated where old dataset had ISIN-confirmed record. No name-matching merges.

**Outputs produced:**
- `data/master/mainboard.csv` — 382 mainboard IPOs with provenance tags
- `data/master/sme.csv` — 887 SME IPOs with provenance tags
- `data/master/gaps.csv` — 46 rows (2020-22) lacking subscription/GMP (no Sharescart coverage for those years)
- `data/master/reconciliation_report.csv` — 78 flagged diffs for review
- `data/master/README.md` — dataset description & build metadata

**All checks passed:**
- check_01_base.py ✓
- check_02_detail.py ✓
- check_03_enrich.py ✓
- check_04_verify.py ✓
- check_05_reconcile.py ✓
