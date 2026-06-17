# task_15 — Subscription + GMP: issue register & re-audit  (NOT FINAL)

> **STATUS: NOT FINAL — design/think only.** Group-B issue-register task. Reproduces O-2 / O-3 / O-4
> against current data, finds the 0-instead-of-missing root cause, re-audits the existing
> subscription/GMP parser + fallback fixes, and proposes (non-final) data-layer resolutions.
> All counts below were derived read-only from `data/master/ipo_analysis.csv` (2,384 rows) and the raw caches.

---

## 1. SCOPE
The single question: **For the subscription block (`sub_*_x`, `sub_*_cr`) and GMP (`gmp_pct`), what is the
correct present-vs-absent / sourcing / fallback design, and do the existing fixes actually hold?**
Concretely the three known issues:
- **O-2 [HIGH]** `sub_total_x = 0` on 124 rows (bid-multiple cell parsed as 0 — for 88/124 the shares/`_cr` layer
  WAS captured, so this is a partial parse, not an empty block; NSE raw never used as fallback).
- **O-3 [MED]** category split (`sub_qib_x/sub_nii_x/sub_retail_x`) all 0 while `sub_total_x` is real.
- **O-4 [LOW]** `gmp_pct = 0` on premium-listing rows (the % column reads as a real zero).
Root question underneath all three (item **I1**): a blank/parse-fail is stored as **`0`**, indistinguishable
from a true zero, and the secondary-source fallback is **gated on a truthy check that `0` satisfies**, so it
never fires.

## 2. GROUND-TRUTH INPUTS (read, by path)
- `docs/research/alignment_audit_2026-06-16.md` lines 507–530, 574 (O-2/O-3/O-4 + the I1 root-cause section).
- `rules/index.md` — the tested-signal registry. RELEVANT entries (read BEFORE proposing any subscription/GMP
  signal): **n2-subscription** + **n3-demand-skew** (both `reported — boom-only / SINGLE-REGIME`; longterm
  subscription ≈0 so they cannot be cross-validated), the **REJECTED SHORT score** (GMP+subscription percentiles),
  and the **REJECTED weak-subscription false-APPLY guard** (young-cohort artifact). Bearing on §7.6 (below).
- `docs/data_review.md` + `data/master/review/gaps.csv` (317 rows) — the pre-existing coverage-gap register;
  includes a catalogued `subscription,financials,gmp (no Sharescart 2020–22)` MB NULL-gap. VERIFIED: the 124
  zero-sub rows have **0 overlap** with gaps.csv (they are 2023–26 zero-filled-block rows, a DISTINCT phenomenon
  from the 2020–22 no-page gap — both must be handled by the present-vs-absent design).
- Scraper (source of the value): `scrapers/sharescart.py` — subscription parse block lines 405–428 (shares from
  `cells[2]`→`_cr` at 410+424–428; bid-multiple from `cells[3]`→`_x` at 411–422); `parse_num` lines 215–220;
  GMP parse lines 430–442 (line 435 already skips `--`/`-- %` → NULL, so sharescart does NOT mint GMP zeros).
- Fallback pipeline steps:
  - `pipeline/03c_fill_subscription_nse.py` line 22 (MB subscription from NSE) — skip-on-truthy guard.
  - `pipeline/03d_fill_ipowatch.py` line 37 (SME subscription + GMP from ipowatch) — fill-only-if-not-truthy guard.
  - `pipeline/03e_fill_gmp_investorgain.py` line 48 (GMP from investorgain) — skip-on-truthy guard.
- `pipeline/09_assemble.py` lines 27, 48–59 — `present()` helper + era-aware quality-tier feature keys (QKEYS).
- Other GMP scrapers (scope-limited backfills): `scrapers/gmp_patcher.py` (filters `year >= 2025` **AND**
  `gmp_pct.isna()`); `scrapers/gmp_deep_hunter.py` (filters `year <= 2022` **AND** `gmp_pct.isna()` — the
  OPPOSITE window, explicitly targeting OLD IPOs). NOTE: the O-4 zeros came in via `src=ipocentral`/`websearch`,
  for which **NO scraper exists in-repo** (grep of `scrapers/` + `pipeline/` for `ipocentral` returns nothing).
- Data: `data/master/ipo_analysis.csv`; raw `data/raw/mainboard_events.csv`, `data/raw/sme_events.csv`,
  `data/raw/nse/subscription.csv` (126 rows), `data/raw/nse/subscription_longterm.csv` (89 rows — also a
  candidate MB source; VERIFIED 0/18 overlap with the MB zero-rows), `data/raw/ipowatch/matches.csv`,
  `data/raw/investorgain/gmp.csv`.

## 3. REPRODUCE + RE-AUDIT (against current data)

### 3.1 O-2 — subscription `= 0` (REPRODUCED EXACTLY)
Predicate: `sub_total_x` parses to `0.0`.
- **124 rows** with `sub_total_x == 0`. **All `src=sharescart`.** By type: **SME 106, MB 18**. By year:
  **2025 ×104, 2023 ×15, 2024 ×4, 2026 ×1** — matches the audit ("124 rows, all sharescart, 104 of them 2025").
- **CORRECTED (the `_x` columns are zero, the `_cr` columns are NOT uniform — verified read-only from
  `data/master/ipo_analysis.csv`):** all 124 rows have all four `sub_*_x` columns = 0 (that part holds), **but the
  `sub_*_cr` (rupee-demand) columns are NOT uniformly zero.** Distribution of the four `_cr` cells across the 124:
  - **88/124** carry ≥1 NON-zero `_cr` value (76 have all four `_cr` non-zero) — real subscription DEMAND was
    captured. Example: `INE01R501028` **Vikran Engineering** — `sub_total_x=0` but `sub_total_cr=4679.45`
    (`sub_qib_cr=821.77`, `sub_nii_cr=1824.47`, `sub_retail_cr=2033.21`). Also `INE1CEJ01017` **E to E
    Transportation** `sub_total_cr=29554.71`; `INE0R7301013` **Rulka** `sub_total_cr=797.40`.
  - **18/124** are TRUE strict uniform-zero blocks (all 8 `_x`+`_cr` == 0.0); a further **18/124** have all four
    `_cr` blank (36/124 total have no usable `_cr` value).
  So **only 18/124 are true uniform-zero blocks, NOT 124/124.** The earlier "uniform zero block / no value
  captured" framing was FALSE for ~71% of the population — the share-count (→`_cr`) layer WAS parsed; only the
  bid-multiple (`_x`) cell came through as 0. (This collapses the §6 "~0 false positives because no row has a 0
  total with non-zero detail" argument — see §6, re-derived.)
- **MB-vs-SME divergence (load-bearing for the fix):** of the 18 MB zero-rows only **1** has a non-zero `_cr`
  (the MB cohort is genuinely empty → needs re-scrape/NULL); of the 106 SME zero-rows **87** have a non-zero
  `_cr` (recoverable). The two boards therefore have DIFFERENT root causes and need DIFFERENT treatments (see §4
  Option D + §8).
- **Contradiction by listing pop:** using the correct column `adj_listing_gain_open` (a FRACTION, e.g. 0.183 =
  18.3% — note: the bare `listing_gain_pct`/`adj_listing_gain_pct` names do not exist in the substrate),
  **33 of 124** had a pop ≥ +20% and **77 of 124** had ANY positive pop — i.e. they were clearly subscribed,
  proving the 0 is missing-data, not a real undersubscription. (Audit said "47 contradicted"; the gap is just a
  different threshold/column — direction confirmed.) Worked examples:
  - `INE0QTF01015` **Vibhor Steel Tubes** (MB) — `sub_total_x=0`, listing pop **+181%**.
  - `INE0R7301013` **Rulka Electricals** (SME) — `sub_total_x=0`, pop **+123%**.

**ROOT CAUSE (verified at the raw + scraper layer — there are TWO distinct mechanisms, not one):**
The `0` is **born in the scraper, not the pipeline.** `data/raw/mainboard_events.csv` already stores literal `0`
for 21 rows and `data/raw/sme_events.csv` for 111 rows. `parse_num('--')` → `None` (tested), so the `0` is NOT
from a `--` placeholder. BUT the single "empty table → 0-filled block" story is wrong for the majority:
- **Mechanism 1 — partial parse (the ~88 majority, mostly SME):** in `scrapers/sharescart.py` the `_cr` columns
  are COMPUTED from the shares cell `cells[2]` × `issue_price` (lines 410, 424–428), while `sub_*_x` comes from
  the SEPARATE bid-multiple cell `cells[3]` (lines 411–422). The 88 rows with non-zero `_cr` PROVE the shares/value
  cells parsed successfully — the table was NOT empty and NOT "zero-filled". Only the bid-multiple cell parsed to 0.
  VERIFIED: `parse_num('0.00x'.replace('x',''))` → `'0.00'` (NOT `None`) — its regex matches the digits — so a
  `'0.00x'`/blank multiplier cell MINTS `sub_total_x=0` while the same row's shares yield a real non-zero `_cr`.
  This is a per-cell parse failure / source-rendered-0 on the multiplier column specifically, and the `_x` value is
  in principle RECOVERABLE (the shares ratio is known via `_cr`; see §4 Option D).
- **Mechanism 2 — genuinely empty table (the ~18 MB + ~18 all-blank-`_cr` rows):** here the subscription table
  rendered nothing usable, so both `_x` and `_cr` are absent/0 — the original "no value captured" story holds, but
  ONLY for this minority. The MB side (18 rows, 17 with empty `_cr`) is overwhelmingly this case.
The scraper copies the 0 verbatim into `sub_total_x` with `src=sharescart`, and **downstream every fallback then
treats it as present.** Misdiagnosing all 124 as "empty table" would mis-route the 88 recoverable rows to a naive
0→NULL discard (a real over-catch — see §6).

**Why the fallbacks don't repair it (re-audit of the existing fixes):**
- `03c` (NSE→MB) skip guard line 22: `if (r.get('sub_total_x') or '').strip(): continue`. `'0'.strip()` → `'0'`
  (truthy) → the row is **skipped as "already has subscription"**. The NSE fallback never runs on a 0-row.
  *(Same I1 defect-class as `03e` line 48 — a skip-on-truthy guard; `03d` line 37 shares the defect in a
  different guard SHAPE, see §3.4.)*
- Even if the guard were fixed, **neither NSE cache can repair the (mostly empty-`_cr`) MB 0-rows right now:**
  `data/raw/nse/subscription.csv` (126 rows) overlaps **0/18** MB ISINs and `data/raw/nse/subscription_longterm.csv`
  (89 rows) ALSO overlaps **0/18** (both verified). NSE Public-Issues API only serves a recent window, so the
  caches are sparse/stale for the 2023–25 MB 0-rows. → MB repair needs a **re-scrape**, not just a guard fix.

### 3.2 O-3 — category split all-0 while total real (REPRODUCED EXACTLY)
Predicate: `type=MB AND sub_total_x>60 AND sub_qib_x=sub_nii_x=sub_retail_x=0`.
- **3 rows, exactly the audit's three:** `INE682M01012` Jupiter Life Line (tot 64.8), `INE055S01018` Cyient DLM
  (tot 71.3), `INE349Y01013` ideaForge (tot 106.1) — all `src=sharescart`, all three category cells 0.
- **Broadened** (any row `sub_total_x>2` with all three category cells blank-or-0): **41 rows (SME 22, MB 19)** —
  so the "have a total but no usable split" population is wider than the audit's 3 strict MB cases. (SME QIB=0 is
  legitimately expected and should NOT be flagged; the design must gate O-3 to MB or to "split-sum ≠ total".)
- This is the SAME 0-as-missing bug confined to the category columns: sharescart got the Total row but not the
  per-category rows, and wrote 0 for the missing categories.
- **Inverse check the 88-row finding enables (completeness):** beyond the `_x` split, the substrate can also test
  `Σ(category _cr) vs total _cr` and reconstruct `category _x` from `_cr` — i.e. the `_cr` layer gives an
  independent cross-field consistency lever (used in §7 #5's cross-field rule and §4 Option D). The cross-column
  contradiction `sub_total_x==0 while sub_total_cr>0` should itself be a first-class validity rule in the task_11
  cleaning model, not just an O-3 special case.

### 3.3 O-4 — GMP `= 0` on premium listings (REPRODUCED EXACTLY)
Predicate: `gmp_pct` parses to `0.0`.
- **10 rows, by src: ipocentral ×8, websearch ×2** (matches audit's "src ipocentral/websearch"). Note: NONE are
  `src=investorgain` — the `03e` fallback never reached them.
- **5 of 10 had pop ≥ +20%:** Vivo Collaboration **+333%** (`INE0IA701014`), KN Agri **+105%** (`INE0KNW01016`),
  Krishna Defence **+92%** (`INE0J5601015`), Timescan **+61%** (`INE0IJY01014`), Nupur **+23%**. So `gmp_pct=0`
  is masking real pre-listing premia. (Audit named Waaree/Vivo; Vivo confirmed.)
- **Source/year breakdown:** by year the 10 O-4 rows are **2021×4, 2022×4, 2020×1, 2023×1** (verified) — so
  **9/10 fall in the `year <= 2022` window**, with the single 2023 row outside it.
- **GMP-0 root cause is NOT sharescart.** `scrapers/sharescart.py` line 435 already skips `--`/`-- %` → NULL, so
  sharescart does not mint these GMP zeros. The 10 zeros carry `src=ipocentral` (8) / `websearch` (2), and
  **NEITHER source has any scraper in `scrapers/` or any reference in `pipeline/`** (grep returns nothing). The
  zeros entered via some external/one-off ingestion path that is not in-repo — so the O-4 fix must be directed
  THERE, not at `scrapers/sharescart.py` (correcting §7 item 1's mis-pointed file for the O-4 population).
- **Re-audit of `03e` (investorgain fallback): it CANNOT repair these from cache.** I matched the 10 by
  nse/bse-id + listing_date against `data/raw/investorgain/gmp.csv`: **9–10/10 match an investorgain row** (the
  exact figure depends on the field-mapping/date tolerance used; pin the key when this is acted on), **and
  investorgain's `gmp_rs = 0.0` for every matched one** (verified for VIVO/TIMESCAN/KNAGRI). These are 2020–23-era
  IPOs for which investorgain itself never recorded a GMP. So for the % column this is genuinely
  **"source never published"** — backfill needs a DIFFERENT source.
- **Re-audit of the backfill hunters (CORRECTED — the two are NOT both `year>=2025`):**
  `scrapers/gmp_patcher.py` filters `year >= 2025 AND gmp_pct.isna()` (line 26). `scrapers/gmp_deep_hunter.py`
  filters `year <= 2022 AND gmp_pct.isna()` (line 50) — the OPPOSITE window, explicitly for OLD IPOs. So
  **9/10 O-4 rows are already IN-SCOPE for `gmp_deep_hunter`**; only the single 2023 row falls in the
  >2022/<2025 gap covered by NEITHER hunter. The earlier "both hunters skip these (year>=2025)" claim was wrong.
  **BUT a second I1-class bug blocks the hunters regardless:** both filter on `gmp_pct.isna()`, and the O-4 rows
  hold literal `0` (NOT NaN), so even within the right year window the hunters skip them. The 0→NULL fix
  (Proposal #1) is therefore a HARD PREREQUISITE for `gmp_deep_hunter` to ever pick up the 9 pre-2023 O-4 rows —
  independent of any year-window change. (Open: whether `gmp_deep_hunter` was ever actually run for these symbols,
  or whether its web-search simply found nothing — re-audit when acted on.)

### 3.4 Systemic confirmation (I1) + a downstream contamination found
- The same I1 DEFECT-CLASS (a `'0'` string is truthy, so absence reads as present) afflicts all three fill steps,
  but in **two guard SHAPES** (it is NOT one identical guard): skip-on-truthy — `if (...).strip(): continue` at
  `03c:22` and `03e:48` — vs fill-only-if-not-truthy — `if seg=='sme' and not (...).strip() and (...).strip():`
  at `03d:37` (an inline fill-when-absent condition). One systemic class, two code shapes; the shared
  "fill-if-absent" replacement (§7 #2) must subsume BOTH shapes (and 03d needs a different edit shape than 03c/03e).
- A THIRD instance of the same I1 class sits inside the proposed remediation tool: `gmp_patcher`/`gmp_deep_hunter`
  filter `gmp_pct.isna()`, which a literal-`0` O-4 row does not satisfy (see §3.3) — so the 0→NULL fix is a
  prerequisite for those hunters too.
- **Downstream contamination — QUANTIFIED:** `09_assemble.py present()` (line 27) treats `0` as present, and
  `sub_total_x`/`gmp_pct` are era-aware quality-tier feature keys (QKEYS, lines 48–59). VERIFIED: **all 124
  `sub_total_x==0` rows are `cohort=='boom'`**, and per `_applicable_qkeys` `sub_total_x` is an applicable QKEY for
  EVERY boom row (and `gmp_pct` for the 10 boom O-4 rows). So the tier-contamination scope is exactly bounded —
  124 subscription rows + the (boom) 10 GMP rows — all currently scored as "has subscription/GMP" when they don't.
  Converting these 0s → NULL will (correctly) lower some tiers. EXACT tier-movement count (how many of the 124+10
  actually drop a tier under the QKEYS logic) is a concrete target for the GOLDEN tier-count test update (§7 #6),
  not "some".

### Re-audit verdict
The existing subscription/GMP fixes (NSE/ipowatch/investorgain fallbacks) are **structurally sound in intent but
defeated by the I1 guard** (truthy-skip lets `0` block the fallback) AND, for MB-subscription and O-4-GMP,
**limited by sparse/empty caches** (a guard fix alone won't fully repair them).

## 4. OPTIONS (≥3, steelmanned)

**Option A — Per-field patch: change each fill step's skip guard to treat 0 as missing, then re-run fills.**
- *Steelman:* smallest change; immediately repairs the SME subscription cohort (see §6: 75 rows fixable from the
  EXISTING ipowatch cache, no re-scrape). Localized, low-risk.
- *Reject for the architecture:* it leaves `0` in the masters (only overwrites where a fallback has data), keeps
  three parallel copies of the same guard logic (north-star: no duplication), and silently re-introduces the bug
  the next time a column is added. It is a tactical repair, not the present-vs-absent design the charter wants.
  *(Keep it as the cheap immediate-win sub-step, not the design.)*

**Option B (leaning) — Fix at the source + a 3-state present/absent encoding (charter I1/task_03).**
Two coordinated moves:
  (i) **Source layer:** `parse_num` / the subscription+GMP extractors emit **NULL, never `0`,** when a value is
  absent/placeholder; distinguish a real captured zero (rare for subscription) from "table empty / row missing".
  (ii) **Provenance layer:** every value carries the task_03 3-state status — `published` / `fetch_parse_failed`
  / `real_zero` — extending the existing `*_src` columns (`sub_total_x_src`, `gmp_pct_src`) rather than inventing
  a parallel scheme. Fallback order then keys off the status (fill only when status≠published), so the
  truthy-skip bug is structurally impossible.
- *Steelman:* matches the north-star (single encoding, declarative fallback, "0 can never masquerade as data"),
  heals O-2/O-3/O-4 AND the quality-tier contamination at once, and generalizes to every column via task_06's
  registry. This is the charter's intended fix.
- *Cost:* depends on task_03 (present/absent encoding) + task_02 (sourcing/fallback order) — so it's a design
  dependency, not a standalone change.

**Option C — Drop sharescart subscription/GMP entirely; source subscription only from NSE (MB) + ipowatch
(SME), GMP only from investorgain/ipowatch.**
- *Steelman:* removes the single source that manufactures the 0s; the authoritative exchange/aggregator feeds
  are cleaner.
- *Reject:* sharescart is the PRIMARY coverage for the boom cohort — §3 shows 568/679 SME and 239/260 MB
  sharescart rows carry a REAL `sub_total_x`. Dropping it to kill 124 bad rows would null ~800 good rows. The
  problem is the missing-value encoding, not the source. Fails correctness/coverage.

**Option D — In-substrate arithmetic RECOVERY of `sub_*_x` from the `_cr` demand (network-free).**
For the 88/124 rows where `sub_*_cr` is present (87 SME + 1 MB), `sub_total_x` is derivable WITHOUT a re-scrape
and WITHOUT any external source as approximately `sub_total_cr / issue_size_cr` (demand value ÷ issue value), since
the underlying shares ratio that drives `_cr` is the same quantity that `_x` reports. Worked: `INE0R7301013` Rulka
`797.40 / 26.0 ≈ 30.7×`; `INE01R501028` Vikran `4679.45 / 772.0 ≈ 6.1×` — both plausible subscription multiples.
- *Steelman:* the cheapest CORRECT path — it RECOVERS real subscription data for the majority instead of
  discarding it, needs zero network, and exposes the partial-parse mechanism (Mechanism 1) directly. It also
  shrinks the "irreparable without network" population materially (the MB-empty and all-blank-`_cr` rows are the
  only true residual).
- *Caveats (must be designed in, not waved away):* (i) it needs a VALIDITY check — derived `_x` cross-checked
  against any cache value (ipowatch for SME) and against a sane range; the ratio is approximate (issue-size basis
  vs exact offered-shares basis) so some derived multiples may be off (e.g. `INE1CEJ01017` E2E derives ~352× —
  flag, don't blindly accept). (ii) it must carry a provenance `status=derived` (NOT `published`) so it never
  masquerades as source-captured. (iii) it applies only where `_cr` AND `issue_size_cr` are both present.
- *Verdict:* a strong COMPLEMENT to Option B, not a competitor — B fixes the encoding/fallback structurally;
  D supplies a network-free recovery for the 88-row recoverable bucket. The MB-empty/all-blank residual still
  falls back to NULL (status `fetch_parse_failed`) per B.

## 5. ANALYSIS
The three issues share ONE defect-class — **a missing/unparsed measurement encoded as `0`, then protected from
repair by a fallback guard that accepts `0` as present** — but the O-2 population splits into TWO mechanisms
(partial parse with recoverable `_cr` for ~88; genuinely-empty table for ~36) and the O-4 GMP zeros enter via an
EXTERNAL ingestion path (ipocentral/websearch), not sharescart. So the fix is not monolithic; it requires:
1. **Stop minting the `0`** (source parser emits null) — without this, even a perfect fallback only patches the
   subset for which a secondary source exists; the rest stay `0` (the residual rows with no cache AND no `_cr`
   would remain falsely "subscribed at 0×"). NOTE the residual is SMALLER than first thought: the 88 `_cr`-present
   rows are recoverable in-substrate (Option D), so only the MB-empty + all-blank-`_cr` rows are the true
   no-coverage residual.
2. **Make absence repairable** (3-state provenance so the fallback fires on absent, and so a genuinely-absent
   value reads as NULL, not 0, for Layer-3 — this is what un-poisons subscription-as-feature and the quality
   tier).
Coverage reality (from §6) sets expectations: the SME subscription cohort is mostly self-healing from existing
caches; MB subscription and the O-4 GMP rows need fresh fetches (NSE re-scrape; a non-investorgain GMP source).
O-3 splits split into "recoverable" (re-scrape the category rows) and "genuinely unpublished" (leave NULL).
So the design must also classify **"NULL because nobody published it"** as a first-class, non-error state.

## 6. TEST / VALIDATE (numbers, read-only)

**O-2 caught/missed counts (CORRECTED against ground truth):**
- Predicate `sub_total_x==0` → **124 caught** (the `_x`-bug population). Population split (verified read-only from
  `data/master/ipo_analysis.csv`): all 124 have all four `_x`==0; **88/124 carry ≥1 non-zero `_cr`** (76 all-four
  non-zero) — RECOVERABLE; **36/124 have no usable `_cr`** (18 strict all-8-zero + 18 all-`_cr`-blank) — genuinely
  missing. By board: MB 18 (only 1 with `_cr`) vs SME 106 (87 with `_cr`).
- **False-positives of the PREDICATE (real undersubscriptions wrongly flagged):** still ~0 — the flag is on the
  `_x` column ALONE, and no row shows a 0 `_x` total with a non-zero `_x` category (a real 0.xx× undersubscription
  signature). Independent corroboration: 77/124 had a positive listing pop, 33/124 ≥ +20%. **NOTE the earlier
  "124/124 uniform-zero block" justification was FALSE** (88 rows have non-zero `_cr`); the corrected support for
  "these aren't genuine undersubscriptions" is (a) the listing-pop evidence and (b) the large `_cr` demand on 88 rows.
- **False-positives (OVER-CATCH) of a NAIVE FIX (the number the charter requires):** a blanket `0→NULL` rule that
  discards all 124 would OVER-catch the **88 recoverable rows** (it throws away real, in-substrate-derivable data).
  Only **36** (18 strict) are truly-missing. So the proposed remedy has **88 over-catches, not ~0** — which is why
  Option D (recover the 88) + Option B (NULL only the 36 residual) is the correct design, not a naive 0→NULL.
- **Repairability — three buckets (network cost ascending):**
  1. **cache-repairable, network-free:** of the 106 SME 0-rows, **75 have a non-zero `sub_total_x` already in
     `data/raw/ipowatch/matches.csv`** (all 75 > 0). Fixing the `03d` guard + re-running repairs **75/106 SME rows
     with NO re-scrape.** Worked: `INE0NUL01018` Auro Impex → ipowatch **66.94×**; `INE0NJ001013` CFF Fluid
     Control → **8.45×**.
  2. **`_cr`-derivable, network-free (Option D):** of the rows NOT cache-repairable, the subset with non-zero
     `_cr` + present `issue_size_cr` is recoverable arithmetically (status=`derived`, with the validity check) —
     materially shrinking the "needs network" residual below the previously-stated 31 SME + 18 MB.
  3. **genuinely needs re-scrape → NULL until then:** the residual with neither cache nor `_cr` — dominated by the
     MB-empty rows. The NSE cache overlaps **0/18** of the MB ISINs; the longterm NSE cache
     (`data/raw/nse/subscription_longterm.csv`, 89 rows) ALSO overlaps **0/18** (verified) — so the MB re-scrape
     conclusion holds across BOTH NSE caches. Until fetched these become **NULL (status=`fetch_parse_failed`)**, not `0`.

**O-3:** strict MB predicate → **3 caught** (Jupiter/Cyient DLM/ideaForge), 0 false positives at the strict
level. Broadened predicate (total>2, all 3 cats blank-or-0) → **41** (22 SME false-positive-prone because SME
QIB=0 is legitimate → design must gate to MB or to "Σcategories ≠ total" to avoid over-catching).

**O-4:** `gmp_pct==0` → **10 caught** (8 ipocentral, 2 websearch; years 2021×4/2022×4/2020×1/2023×1), **5 with
pop ≥ +20%** (Vivo +333%, KN Agri +105% worked examples). Repairability: matching by nse/bse-id + listing_date
against `data/raw/investorgain/gmp.csv` reproduces **9–10/10 matched** (the exact figure depends on which substrate
column maps to which investorgain field + the date tolerance — pin this key when acted on), **all matched with
`gmp_rs=0`** → **0 fixable from current caches** → must be NULLed (status: source-unpublished-for-now) and queued
for a fresh GMP source; not silently kept as 0. The 9 pre-2023 rows are in `gmp_deep_hunter`'s `year<=2022` window
(only the 2023 row is in the inter-window gap), but the hunter's `gmp_pct.isna()` filter skips all 10 today (they
hold literal 0) — so 0→NULL must land FIRST before any hunter can repair them.

*Testability note:* the architecture half (3-state encoding) is design-level — validated here by walking the
real fallback caches (counts above) rather than a single predicate.

## 7. NON-FINAL PROPOSAL

1. **Encode absence, never 0 (I1, source + provenance):**
   - The **subscription** `_x` extractor in `scrapers/sharescart.py` (and the fill steps) emit **NULL** when the
     bid-multiple cell is absent/placeholder. A `0`/`0.00x` from that cell is treated as **not-yet-captured (NULL +
     status `fetch_parse_failed`)**, NOT a real 0 — even when the row's shares (`_cr`) DID parse (Mechanism 1). (A
     genuine real-zero undersubscription is vanishingly rare and would show non-zero category `_x` rows — keep that
     as the only `real_zero` path.)
   - For **GMP O-4 specifically, sharescart is NOT the source** (line 435 already NULLs `--`/`-- %`): the 10 zeros
     came in via `src=ipocentral`/`websearch`, for which NO scraper exists in-repo. The 0→NULL fix for O-4 must be
     directed at the actual (external/one-off) ingestion path — trace/flag it; do not point the O-4 fix at sharescart.
   - Extend `sub_total_x_src` / `gmp_pct_src` into the task_03 **3-state status** (`published` /
     `fetch_parse_failed` / `real_zero`), plus a `derived` provenance for Option-D recovered `_x`. Single encoding,
     no parallel booleans.
2. **One shared "fill-if-absent" guard** (kill the duplicated truthy-skip in `03c/03d/03e`): a fallback fires
   when status ≠ `published`. Order of preference per field declared in task_02 (MB sub: sharescart→NSE; SME sub:
   sharescart→ipowatch; GMP: sharescart→investorgain→ipowatch→hunter). This makes the I1 bug structurally
   impossible and removes three copies of the guard.
3. **Immediate wins, both network-free (can be the first build steps once approved):**
   - (a) flip the `03d` guard to treat 0 as absent → repairs **75/106 SME subscription rows** from the existing
     ipowatch cache.
   - (b) **Option D arithmetic recovery** of `sub_total_x` from `sub_total_cr / issue_size_cr` for the 88
     `_cr`-present rows (status=`derived`, with a validity cross-check vs cache/range) — recovers real multiples
     instead of discarding them. Apply AFTER (a) so cache values win where present.
4. **Re-scrape backlog (needs network, owner-gated) — the true residual only:** NSE Public-Issues for the MB
   empty-`_cr` 0-rows (BOTH NSE caches overlap 0/18); a non-investorgain GMP source for the 10 O-4 rows. The
   hunters: `gmp_deep_hunter` (year<=2022) already covers 9/10 O-4 rows; only the 2023 row needs a window tweak —
   BUT both hunters ALSO filter `gmp_pct.isna()`, so the 0→NULL fix (Proposal #1) is a HARD PREREQUISITE for them
   to ever pick up these literal-0 rows. Until fetched → values stay **NULL**, status `fetch_parse_failed` /
   `source_unpublished`.
5. **O-3 / cross-field validity rule (declarative, task_11):**
   - O-3 split: when `sub_total_x` is present but `Σ(qib,nii,retail) == 0` (or ≠ total) → null the category cells
     with status `fetch_parse_failed`, **gated to MB** (or "split present"), so legitimate SME QIB=0 is never flagged.
   - First-class consistency rule: flag/clean any row where `sub_total_x==0` but `sub_total_cr>0` (or
     `Σ category_cr>0`) — the cross-column contradiction at the heart of the 88-row finding. **Specify the
     `_x`/`_cr` policy explicitly:** if `_x` is NULLed, decide whether `_cr` stays (recommended — it's real demand),
     is also NULLed, or is USED to recover `_x` (Option D). Nulling `_x` while keeping a non-zero `_cr` must be a
     deliberate, documented state, not an accidental internal inconsistency. (Owner question added in §8.)
6. **Downstream:** converting the 124+10 zeros to null/derived will move some `data_quality_tier` assignments.
   Scope is bounded: all 124 sub rows + 10 GMP rows are boom-cohort and present()-counted as having
   subscription/GMP today; the GOLDEN tier-count test update should target the EXACT count that drops a tier under
   the QKEYS logic (compute it), not "some". Then re-run subscription/GMP Layer-3 findings — see §7.6.

### 7.6 Feature ↔ data link (for task_12) — scoped to data hygiene, NOT signal revival
The named findings that touch this root cause (per `rules/index.md`) are **n2-subscription**
(`findings/n2_subscription`) and **n3-demand-skew** (`findings/n3_demand_skew`). Both are recorded as
`reported — boom-only / SINGLE-REGIME` (longterm subscription ≈0, so they cannot be cross-validated). Therefore the
0→NULL/derive fix improves their INPUT cleanliness (no `0` masquerading as a real 0× demand) but **cannot lift them
to cross-regime VALIDATED** — that is a data-availability limit, not a cleanliness one. Likewise, the SHORT score
(GMP+subscription percentiles) and the weak-subscription false-APPLY guard are already **REJECTED** in
`rules/index.md`, so "healing this heals downstream features" is scoped to **data hygiene** (cleaner inputs, honest
quality tiers), NOT to reviving rejected/single-regime signals. (Corrects the earlier over-promise.)

## 8. OPEN OWNER-QUESTIONS
1. **Adopt I1 as one systemic "0→NULL at source + 3-state provenance" fix** (vs per-field patches)? (Charter §9 /
   audit line 515.) — leaning YES.
2. **Real-zero policy:** is a genuine 0.xx× *undersubscription* ever expected in our universe, or can we treat
   ALL `sub_total_x==0` as missing/recoverable? (Evidence: none of the 124 shows a 0 `_x` total with a non-zero
   `_x` category — the real-undersubscription signature — and 88/124 carry positive `_cr` demand + 77/124 a
   positive listing pop → all 124 look safely "missing, not a real 0×"; but confirm we never want to record a true
   undersubscribed IPO as 0.)
3. **MB subscription & O-4 GMP re-scrape:** approve a network re-fetch (NSE for 18 MB rows; a fresh GMP source
   for 10 rows)? If not now, are NULLs acceptable interim values? (Network is default-deny — needs explicit OK.)
4. **O-3 scope:** flag only the strict 3 MB rows, or the broadened "split missing" population — and do we
   formally exempt SME QIB=0 from any subscription-completeness check?
5. **GMP coverage threshold:** GMP is only ~2020+; are NULLs for pre-2020 / source-unpublished rows fine as a
   permanent state (already handled by `09_assemble` era-gating lines 48–59), and should `gmp_pct=0`-as-data be
   purged retroactively?
6. **Recover-vs-NULL for the 88 `_cr`-present rows:** do we RECOVER `sub_total_x` arithmetically (Option D,
   status=`derived` — keeps real data) or NULL it (lossy but simpler)? Leaning: recover, with a validity check.
7. **MB-empty vs SME-recoverable = two distinct fixes:** confirm the split implies different treatments —
   re-scrape/NULL for the (genuinely-empty) MB side vs cache-fill + arithmetic recovery for the SME side — rather
   than one uniform 0→NULL rule.
8. **`_x`/`_cr` consistency policy:** when `_x` is NULLed/derived, what happens to a non-zero `_cr` — keep it
   (real demand), NULL it too, or use it to derive `_x`? Needed so the substrate never carries a silent
   `_x==NULL, _cr>0` (or vice-versa) inconsistency.

---

### DONE CHECKLIST
- [x] all 8 steps present and non-empty
- [x] ground-truth inputs cited by FILE PATH
- [x] step-6 numbers present (caught/missed/over-caught + ≥2 ISIN examples)
- [ ] review-loop stop rule satisfied — **NOT YET SATISFIED.** Round-1 review HAS run (findings below applied);
  the stop rule (≥2 consecutive independent fresh-agent rounds with zero ≥LOW findings, hard floor ≥2 rounds) is
  NOT yet met — round-1 found HIGH correctness errors, so ≥1 more fresh round is required, all logged in the review_log.
- [x] NOT-FINAL marker + open-owner-questions block present

> ⚠️ Review state: **round-1 multi-lens review applied** (2026-06-17) — the false "uniform-zero block" claim
> corrected (88/124 carry non-zero `_cr`), the two-mechanism root cause and MB-vs-SME split added, Option D
> (in-substrate recovery) added, the gmp_deep_hunter `year<=2022` + `.isna()` corrections made, rules/index.md
> + gaps.csv + longterm cache context picked up, and over-catch quantified. Stop rule NOT yet met — re-review next
> round; do not mark done until ≥2 consecutive clean fresh rounds are logged in
> `docs/research/night_run_2026-06-17_review_log.md`.
