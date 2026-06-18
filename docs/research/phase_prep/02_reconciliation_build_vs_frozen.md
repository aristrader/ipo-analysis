# 02 — Reconciliation: fresh `data_build/` re-fetch vs frozen `data/` baseline

The build-beside-old gate (Ph7): before we swap, prove what the honest re-fetch changed. This is the
pre-computed diff.

## 1. PRICES — re-fetch is SOUND (history preserved, extended) ✅
- Files: frozen **2,383** vs build **2,373** → **12 dropped**, **2 new** (`INE11XK01017`, `INE1RQS01010`).
- **Historical-overlap test (150 sampled ISINs): closes MATCH on 150/150.** Every observed value drift is
  purely *newer trading days appended* (the re-fetch ran 2026-06-18, later than the frozen build). **No
  historical close was silently re-adjusted** — i.e. the re-fetch did NOT change the past (no rogue
  split re-adjustment). This is a strong green light for the price layer.
- ⚠ **The 12 dropped files are ALL delisted stocks** (11 MB + 1 SME; several FPO): KEW Industries, Birla
  Power Solutions, Powersoft Global, Circuit Systems, Dagger-Forst, Chemcel Bio-tech, Avon Weighing, Anu's
  Laboratories, Manjushree Extrusions, Midfield Industries, Birla Pacific Medspa, Ace Tours Worldwide.
  The current bhavcopy can't see off-exchange names, so the re-fetch produced no file. **These histories must
  be CARRIED OVER from frozen (or the bhavcopy archive), not lost** — otherwise we drop 12 delisted terminal
  returns (survivorship damage). → action item for the data-copy/merge step (doc 06): the swap must be a
  *merge that preserves delisted price files*, not a wholesale replace.

## 2. DELISTING — shape CHANGED (now a full status table) ⚠
- Frozen `delisting.csv` = 2,296 rows (delisted-ish only). Build = **2,384 rows = one per substrate ISIN**.
- Build status breakdown: **active 2,100 / delisted 139 / unknown 75 / suspended 70**.
- The 88 build-only rows are **58 active + 30 unknown** (i.e. the new file now also lists *live* names).
- **Implication:** `delisting.csv` is now a *status table for the whole universe*, not a delisted-only list.
  Step 07 (and the Phase-5 corp-action consumer) read this file to apply the compulsory/liquidation −100%
  rule (decision A1). **They must filter on `status`** (only delisted/suspended/compulsory matter) — a naive
  "every row in delisting.csv = delisted" reader would now wrongly treat 2,100 active names as delisted.
  Flag for the Phase-9 repoint guard. Also: reconcile the `reason`/status taxonomy (compulsory vs voluntary
  vs liquidation drives the −100% vs last-price decision; `delist_reason` is largely NaN in the substrate —
  see below).
- Note: `delist_reason` is NaN for all 12 dropped delisted names in the substrate → the genuine-wipeout
  (−100%) vs last-price distinction (decision A1) is currently UNRESOLVED for them. The fresh status table's
  `reason` column may fill some; worth a join at build.

## 3. CORP_ACTIONS — fresh fetch has FEWER events (−26) — likely de-dup, investigate in doc 03
- Frozen `reference/corp_actions.csv` = **1,509** vs build **1,483** (−26). Same 7-col schema
  (isin, symbol, action_type, raw_subject, ratio_factor, ex_date, source).
- Frozen also has `corp_actions_merged.csv` (1,897, includes 354 yahoo_only) + `_matches` (514) +
  `_discrepancies` (16) + `_yahoo_only` (354).
- **−26 is the headline for D-1**: fewer events could mean the fresh fetch (a) de-duplicated the
  multi-source double-counts that CAUSED the fake multibaggers, or (b) missed real events. Must diff WHICH 26
  differ and classify each. → doc 03 (corp-action deep-dive).

## 4. What the swap (data-copy/merge) must guarantee — carried to doc 06
1. **Preserve delisted price files** the re-fetch can't regenerate (the 12, and any like them).
2. **Treat `delisting.csv` as a status table** downstream (filter on status), not a delisted-only list.
3. **Re-run the corp-action de-dup** and verify the −26 is benign (de-dup) before trusting fewer events.
4. The price re-fetch itself is trustworthy to swap (history preserved) — the risk is in the *derived*
   layers (delisting semantics, corp-action collapse), not the raw prices.
