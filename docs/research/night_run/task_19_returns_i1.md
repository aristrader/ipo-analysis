# task_19 — Returns/outcomes (O-1) + systemic I1 (0-vs-missing at load)

> **STATUS: NOT FINAL — design/think-only proposal for owner review.** Zero code, zero pipeline
> changes were made. Every count below was produced read-only against the real CSVs (via the `csv`
> module, never `wc -l`). Part of the overnight data-architecture run (charter
> `night_run_2026-06-17_charter.md`). Group-B task; feeds the issue register + the present/absent
> policy (task_03) + the cleaning-rules model (task_11).

---

## 1) SCOPE — the single question

**Two coupled questions:**
1. **O-1 (returns/outcomes):** is `listing_open = 0` a real bug, and are the rest of the
   returns/outcomes columns (alpha, delisting −100%, outcome_class, current_return) actually clean?
2. **I1 (the cross-cutting root cause):** *a blank / parse-fail / "source-said-zero" gets stored as the
   number `0` (or `""`) instead of being marked MISSING.* Enumerate **every** field affected across
   subscription / GMP / sales / market-cap / min-investment; find the **mechanism**; and frame the fix
   so a downstream consumer can tell apart **(a) source never published it · (b) we failed to
   fetch/parse it · (c) it is a real zero.**

I1 is the systemic spine; O-1 is one (contained) instance plus the returns audit.

---

## 2) GROUND-TRUTH INPUTS (read, by file path)

- `docs/research/alignment_audit_2026-06-16.md` — the O-series (O-1…O-16) + the "CROSS-CUTTING ROOT
  CAUSE — missing coded as 0, not NaN" section that re-confirms held item **I1** (names O-2 subscription,
  O-4 GMP, O-6 sales, O-8/O-15 market_cap, O-14 min_investment).
- `docs/schema.md` — column list + the `<field>_src` provenance convention (lines 180-194).
- `pipeline/07_returns_summary.py` — builds returns/outcomes; uses `pfloat` (returns `None`, written `''`).
- `pipeline/lib.py` — `fnum` (→ `None` on fail), `num` (type-guard → `None`).
- `pipeline/03_enrich.py` — the subscription/financials/GMP enrich step (the **I1 propagation point**, L24-30).
- `pipeline/08_build_universe.py` (L158-214) — market_cap / sector attach (copies screener value verbatim).
- `scrapers/sharescart.py` — `parse_num` (L215-220, → `None` on fail) + subscription block (L401-428).
- `data/raw/mainboard_events.csv` / `data/raw/sme_events.csv` — the **raw sharescart** output (source of truth for "is the 0 from the source?").
- `data/raw/chittorgarh_details.csv` + `data/raw/chittorgarh/details.csv` — raw chittorgarh (O-1 listing_open root).
- `data/master/ipo_analysis.csv` — THE substrate (2,384 rows verified at run-time).
- Charter cross-link: INE312H01016 (Inox) is a **Category-2 verified-genuine crash** (88-audit), NOT a
  bug to clamp — carried as protective ground truth for the returns/envelope side.

---

## 3) REPRODUCE existing issues + RE-AUDIT existing "fixes" (against CURRENT data)

### 3a. The MECHANISM of I1 (newly pinned down — it is NOT a loader/`pfloat` bug)

The audit framed I1 as "loaders write 0 instead of NaN." **Ground truth says the picture is more
specific, and the existing parsers are mostly innocent:**

- `scrapers/sharescart.py::parse_num` (L215-220) returns `None` (not 0) when the cell can't be parsed.
- `pipeline/07_returns_summary.py::pfloat` (L55-62) and `lib.py::fnum`/`num` all return `None` on fail,
  and `fmt` (07 L552-561) writes `''` for `None`. **The returns pipeline does NOT manufacture zeros.**

So where do the 124 `sub_total_x=0` rows come from? **The SOURCE emits `0`, and our parser faithfully
records it as a legitimate parse.** Verified directly against the raw sharescart events file:

```
data/raw/mainboard_events.csv : sub_total_x == '0' on 21 rows  (e.g. ESAF Small Finance, listed +16.55%)
data/raw/sme_events.csv       : sub_total_x == '0' on 111 rows (e.g. E to E Transp., listed +47.37%)
                                → 132 raw source-zeros total; 0 blanks.
```

sharescart's listing table prints `0x` subscription when the figure wasn't captured. `parse_num('0x') → '0'`.
That is the **(b) fetch/parse-can't-distinguish** + **(a) source-published-a-placeholder** case colliding.

Then `pipeline/03_enrich.py` **propagates and LAUNDERS it** (L24-30):
```python
for c in FIN:
    if o.get(c): r[c] = o[c]          # '0' is a truthy non-empty string → copied through
for c in ['sub_total_x', ...]:
    r[c+'_src'] = 'sharescart' if o.get(c) else ''   # '0' is truthy → stamped src='sharescart'
```
So the missing value is not only kept as `0`, it is **stamped with a real source provenance**. Verified:
**all 124 `sub_total_x=0` substrate rows carry `sub_total_x_src='sharescart'`** — the provenance scheme
actively asserts the fake zero is genuine. This is the deepest part of I1 and the reason a naive
"0→NaN at load" patch is insufficient — the *provenance layer itself* lies.

> ⚠️ **The laundering is a PATTERN, not a single-step defect.** `03_enrich.py` is the verified site for
> `sub_total_x` (all 124 carry `_src='sharescart'`), but the *same* truthy-`'0'`-copied-and-stamped-real-
> `_src` pattern recurs across OTHER enrich/backfill steps for OTHER I1 fields. Verified: the 10
> `gmp_pct==0` rows carry `gmp_pct_src ∈ {ipocentral:8, websearch:2}` — stamped by the GMP-backfill steps
> (03d/03e-type), NOT `03_enrich.py`. **Consequence:** the "validity-gate-before-`_src`" fix (proposal #4)
> must apply at **every** assemble/stamp site, not only `03_enrich.py`. The fix is a stamping *policy*, not
> a one-file patch.

### 3b. Full I1 field inventory (substrate, 2,384 rows — zero-count vs blank-count)

| field | zeros | blanks | I1 verdict |
|---|---|---|---|
| `sub_total_x` | **124** | 1129 | implausible-0 (O-2) — masked-missing |
| `sub_qib_x` | **341** | 1214 | implausible for MB (O-3); SME QIB=0 is *real* (no QIB tranche) |
| `sub_nii_x` | 156 | 1143 | mostly masked-missing |
| `sub_retail_x` | 157 | 1142 | mostly masked-missing |
| `gmp_pct` | 10 | 1274 | masked-missing (O-4) — Waaree/Vivo listed huge |
| `net_sales_yr3` | 13 | 460 | **8 are REIT/InvIT (4 reit + 4 invit, metric N/A)** + 5 equity parse-fails (O-6) |
| `pre_ipo_net_sales` | 17 | 466 | inherits net_sales_yr3 zero |
| `market_cap_cr` | 7 | 861 | parse-fail (O-8/O-15) — class still set 'micro' |
| `min_investment_rs` | 18 | 1480 | reconstructable lot×price (O-14) — masked-missing |
| `listing_open` (raw) | 1 | 32 | O-1 — Udayshivakumar, adj col correct |

**Broader footprint (charter asked for EVERY field — the audit named only 6).** A full substrate scan for
columns with ≥5 literal-zero values (excluding returns/alpha/gains where 0 is legitimate) surfaces a
much wider set. NOT all are I1 bugs — **field-awareness is required**:

| MASKED-MISSING (0 implausible/impossible) | PLAUSIBLY-REAL (0 can be genuine) | MIXED / needs per-row check |
|---|---|---|
| `sub_*_x`, `sub_*_cr`, `min_investment_rs`, `market_cap_cr`, `gmp_pct`, `net_sales_yr*` (equity) | `ofs_cr`/`ofs_pct` (725 zeros = **pure-fresh-issue IPOs — REAL 0**), `borrowings_yr*` (debt-free co = real 0) | `pat_yr*`, `operating_profit_yr*`, `operating_cf_yr*`, `eps_yr*` (a loss-maker is **negative**, not 0 → a 0 is suspicious; but a genuinely break-even micro could be ~0) |

> ⚠️ **Key correction to the audit's framing:** I1 is NOT "all zeros are wrong." `ofs_cr=0` on 725 rows
> is the single largest zero-cluster and is **correct** (fresh-issue-only IPOs). A blanket 0→NaN would
> DESTROY real data. The fix must be **per-field validity-driven**, not global.

#### 3b-i. WHICH I1 fields actually have a `_src` carrier today (provenance-coverage inventory)

The proposal (§4 Option B, §8) leans on "ride the existing `_src` columns, no parallel scheme." **Ground
truth (substrate, 220 cols) shows the existing `_src` mechanism covers only 15 columns, and among the I1
masked-missing fields ONLY two have a `_src` carrier:**

| I1 field | `_src` column exists? |
|---|---|
| `sub_total_x` | ✅ yes (`sub_total_x_src`) |
| `gmp_pct` | ✅ yes (`gmp_pct_src`) |
| `sub_qib_x` / `sub_nii_x` / `sub_retail_x` | ❌ none |
| `market_cap_cr` | ❌ none |
| `min_investment_rs` | ❌ none |
| `net_sales_yr3` / `pre_ipo_net_sales` | ❌ none |

(The full 15 `_src` cols: market_maker, fresh_issue_cr, ofs_cr, ofs_pct, anchor_allocation_cr,
listing_open/high/low/close, objects_of_issue, issue_size_cr, sub_total_x, pat_yr3, gmp_pct,
promoter_post_issue_pct.) **So "extend, don't invent" is only literally true for 2 of ~7 I1 fields.** For
the other 5 the 3-state provenance requires a **NEW provenance carrier**. Per the charter's "no per-field
boolean explosion" / compact-encoding constraint (task_03/task_06), the design must specify HOW (e.g. a
compact bit-packed per-field provenance code shared by the registry), NOT assert it free-rides existing
columns. This is the single material design-cost correction to Option B — reconciled honestly into §8.

> **Schema-vs-substrate drift (flag for task_01 / task_03):** `docs/schema.md` L184/L191 document
> `issue_price_src` and `ticker_src` as part of the `_src` convention, but **both are ABSENT from the
> actual substrate** (verified read-only). Since task_19 feeds the present/absent provenance design, this
> drift in the very scheme it builds on is surfaced here for the schema-reconciliation (task_01) and
> provenance design (task_03).

#### 3b-ii. CROSS-FIELD I1 (the real O-3): tranche-vs-total inconsistency

The aggregate per-field zero counts above MASK the actual O-3 bug, which is **cross-field**: all three
tranches `==0` while `sub_total_x` is positive. A per-field validity predicate cannot express "the
tranches sum to ~0 but the total is positive." Verified counts (read-only):

- **32 rows** have `sub_qib_x==sub_nii_x==sub_retail_x==0` yet `sub_total_x>1` (audit said 3 — undercount).
- **218 rows** have `sub_total_x>0` with ≥1 zero tranche — masked tranche-level missingness.

**Design implication:** the column-registry per-field predicate model (task_06) must be **extended to
support multi-column / cross-field predicates** (e.g. `sum(tranches) ≈ sub_total_x within tolerance, else
route the tranche cells to state-(b) missing`), or this entire O-3 class falls through the I1 fix.
Captured as proposal #3a (§8).

#### 3b-iii. Financial-zero fields (the "MIXED" class — now quantified, not a placeholder)

§3b's "MIXED / needs per-row check" column listed `pat_yr*`, `operating_profit_yr*`, `operating_cf_yr*`,
`eps_yr*` with no counts. Charter §9 explicitly calls out EPS/sales/PAT corruption poisoning margins
downstream, so these are not optional. Verified zero counts (yr3):

| field | zeros (yr3) |
|---|---|
| `pat_yr3` | 61 |
| `eps_yr3` | 15 |
| `operating_profit_yr3` | 29 |
| `operating_cf_yr3` | 90 |

**Predicate seed:** a loss-maker is **negative**, not 0 — so `pat_yr3==0 AND net_sales_yr3>0` is
suspicious (a real company with sales rarely books *exactly* ₹0 PAT). The authoritative resolution of
these belongs to **task_16 (financials)**; task_19's job is to **quantify the class and hand it off
explicitly** (done here), not leave it as an unsized placeholder. See proposal #3b (§8).

### 3c. RE-AUDIT of O-1 (the "contained" returns finding) — does it still hold?

Reproduced exactly:
- **INE0N0Y01013 (Udayshivakumar Infra):** substrate `listing_open=0.00`, `adj_listing_open=30.0`,
  `listing_metrics_status='ok'`. Root cause confirmed in **raw chittorgarh**: `details.csv` itself has
  `listing_open='0.00'` (and `issue_price=None`). So O-1 is a source-origin zero.
- **Audit's "CONTAINED" claim HOLDS** — Layer-3 uses `adj_listing_open` (correct at 30.0), and only the
  raw `listing_open` display column is wrong. BUT: `listing_metrics_status='ok'` is **mislabeled** — a raw
  0 that needed the adjusted-column rescue should not read `ok`. The audit's "downgrade the status flag"
  recommendation is the right residual fix; the containment is otherwise sound.
- **Is the status-mislabel a one-off or a class?** Tested the predicate `listing_open(raw)∈{0,blank} AND
  adj_listing_open>0 AND listing_metrics_status='ok'` against the substrate → **count = 1** (only
  INE0N0Y01013). So the mislabel is a genuine **one-off**, not a class; a single-row repair / status
  downgrade is sufficient and a general status-derivation rule is NOT warranted by the data. (Recorded so
  the "is it a class?" question is answered from ground truth, not assumed.)

### 3d. RE-AUDIT of the returns/outcomes "verified SOUND" claims

The audit (O-1 section + "Checked and found SOUND") says benchmark/alpha joins, delisting −100%
terminals, outcome_class bucketing, unreliable_coverage exclusions are sound. Re-read of
`07_returns_summary.py` confirms the **construction** is clean (pfloat→None, delisting wipeout→0.0
terminal in `_terminal_state`, NULL-on-not-mature in `price_at_horizon`). **One open caveat that
crosses into task_14/T-2/T-4:** the MFE/MAE clamp was REMOVED (07 L348-353 comment) and the
trough≤endpoint≤peak invariant now relies on corp-actions being perfect — which D-1 shows they are not.
That is task_14's territory (corp-actions) + T-2/T-4 (envelope/delisting); for task_19's scope the
relevant note is: **INE312H01016 (Inox) is a Category-2 GENUINE crash — its envelope violation is REAL
DATA, must NOT be clamped** (carried per charter). I confirm task_19 proposes NO clamp on it.

---

## 4) OPTIONS (≥3, each steelmanned; leaning challenged)

The charter's **leaning** = "treat I1 as ONE systemic '0→NaN at load' fix (loaders emit NaN on
parse-fail; add NSE fallbacks)." I name it, then argue alternatives on merit.

### Option A — Global "0→NaN at load" (the audit's / charter's leaning)
**Steelman:** one change point, conceptually simple, kills the class in one sweep; matches "single
systemic fix not per-field patches."
**Reject (specific, north-star = CORRECT):** ground truth disproves the premise. (1) The zeros do NOT
originate at *load* — `parse_num`/`pfloat`/`fnum` already return `None`; the 0 comes from the **source
string** and is laundered by `03_enrich.py`, so "fix the loader" misses the actual injection site.
(2) A *global* 0→NaN would null 725 legitimate `ofs_cr=0` (fresh-issue) rows + debt-free `borrowings=0`
→ manufactures missingness from real data. (3) It cannot distinguish the 3 charter states (a/b/c) — it
collapses all to NaN, losing the very signal the charter §3 demands.

### Option B — Per-field VALIDITY RULE + 3-state provenance (proposed)
Each field declares (in the column registry, task_06) a **validity predicate** ("is 0 possible here?")
and a **present/absent provenance state**. At assemble time, a value failing the predicate is routed to
**MISSING** with a 3-state tag, never silently kept as 0. The `_src` scheme (task_03) is EXTENDED from
2-state (source-name | empty) to carry the (a)/(b)/(c) distinction.
**Steelman:** correct (field-aware — keeps real `ofs=0`, nulls fake `sub=0`); extensible (a new column
registers its predicate once, charter §8); single-source in *concept* — it reuses the provenance IDEA
already present (`_src`) rather than a competing one; makes (a)/(b)/(c) first-class. Directly answers
charter §3.
**Cost (honest, corrected per §3b-i):** "rides the existing `_src` columns with no new columns" is only
literally true for `sub_total_x` and `gmp_pct` — the other 5 I1 fields (`sub_qib/nii/retail_x`,
`market_cap_cr`, `min_investment_rs`, `net_sales_yr*`) have NO `_src` carrier today, so the 3-state
provenance **requires NEW provenance carriers** for them. The single-source north-star is satisfied not by
free-riding existing columns but by ONE compact provenance encoding (task_03) applied uniformly via the
registry (task_06) — not a per-field parallel scheme. Plus the registry must support **cross-field**
predicates (§3b-ii). Acceptable — those are sibling tasks in this very run — but the design cost is real
and is reflected in §8, not downplayed.

### Option C — Keep storage as-is; fix only at the CONSUMER (Layer-3 masks zeros)
**Steelman:** zero pipeline change; Layer-3 already excludes some columns; fastest.
**Reject (north-star = CLEAN, single-source):** pushes the lie downstream — every consumer (predictor,
findings, app, future stocks) must re-implement "is this 0 fake?" → behavioral-flag sprawl, the exact
anti-pattern the north-star forbids. And it leaves `_src='sharescart'` asserting a false provenance in
the master. Fixes the symptom, not the corrupt source-of-truth.

**Converge → Option B**, with the charter's "NSE fallback" idea folded in as the *recovery* leg of
B (when a field is MISSING, try the fallback chain from task_02 before giving up), not as the whole fix.

---

## 5) ANALYSIS (step by step)

1. **I1 is a 2-layer defect, not 1.** Layer 1: the source emits a placeholder `0`. Layer 2:
   an enrich/backfill step treats `'0'` as truthy → copies it AND stamps a real `_src`. A correct fix must
   act at **both**: (i) recognize source-placeholder-zero at ingest, (ii) never let an invalid value claim
   a real provenance. **The Layer-2 site is NOT only `03_enrich.py`:** that step is the verified injector
   for `sub_total_x`, but the GMP-backfill steps replicate the identical truthy-`'0'`/stamp-real-`_src`
   pattern (the 10 `gmp_pct==0` rows carry `_src ∈ {ipocentral, websearch}`, not `sharescart`). So the
   stamping-validity-gate (proposal #4) is a **policy applied at every stamp site**, not a single-file
   patch.
2. **The 3 charter states map cleanly onto observed data:**
   - (a) **source-never-published** → e.g. pre-2023 SME GMP (grey market didn't track SMEs); the row was
     never offered the field. Today = blank/EMPTY `_src`. *Mostly correct, but NOT cleanly separable yet:*
     verified all 1129 `sub_total_x` blanks carry empty `_src`, which is **indistinguishable** between
     (a) source-never-published and (b) a fetch/parse that returned blank — exactly the ambiguity §3a notes
     (parsers return `None→''` on failure). So a blank is as ambiguous as a zero; asserting blanks are
     "correct already" is NOT verified. The present/absent encoding must distinguish (a) vs (b) for
     **blanks too** (record attempted-and-failed vs never-offered for the source/era), not only for zeros.
   - (b) **fetch/parse-failed OR source-placeholder** → the 124 `sub_total_x=0`, the 7 `market_cap_cr=0`,
     the 18 `min_investment_rs=0`. Today = `0` with a (false) real `_src`. *The bug.*
   - (c) **real zero** → 725 `ofs_cr=0` (fresh-issue), debt-free `borrowings=0`. Today = `0`. *Must be PRESERVED.*
   The registry's per-field validity predicate is what lets assemble route a `0` to (b) vs (c).
3. **Why provenance must be 3-state, not just "null the value":** if we merely null the fake zeros, we
   lose *why* — and on a re-run (charter §11) the same source-placeholder reappears and we can't tell it
   from a newly-fetched real value. Encoding state (b) makes the missingness **reproducible and
   self-explaining**, and lets the fallback chain (task_02) know to retry from NSE/ipowatch.
4. **min_investment is special — it's RECONSTRUCTABLE, not just missing.** `min_investment_rs ≈
   lot_size_shares × issue_price`. For the 18 zeros this is computable on the row itself → this becomes a
   **derived-recovery cleaning rule** (task_11), not merely a null. (e.g. CFF: 400×165 = 66,000.)
5. **net_sales_yr3=0 splits into two root causes** (CORRECTED count) → of the 13 zeros, **8 are
   REIT/InvIT** (4 reit + 4 invit; metric genuinely N/A for the instrument — a 4th flavor of "absent",
   handled by task_05b's instrument_type gate, NOT by I1) + **5 are equity** parse-fails (true I1-b). So
   **8 rows defer to the instrument gate (task_05b)** and only **5 equity rows** route to I1-b recovery/flag.
   The 8 non-equity ISINs: reit `INE0CCU25019, INE0NDH25011, INE19RO25021, INE041025011`; invit
   `INE0NHL23019, INE1UA823019, INE2Q7823014, INE183W23014`. The 5 equity ISINs: `INE320H01019,
   INE698H01018, INE009Q01019, INE695X01011, INE705X01026`. **Caveat on the 5 equity rows:** "equity
   parse-fail" is not automatic — `INE320H01019` and `INE009Q01019` ALSO have `net_sales_yr2==0`, so those
   two need a per-row check (possibly a genuinely pre-revenue/financials-unavailable company), not a blind
   recover. I1's rule must defer non-equity rows to the instrument dimension rather than "recover" a sales
   figure that doesn't exist. (Substrate `company_name`/`name_at_ipo` is blank for all 13 zero rows — the
   ISINs are the only reliable identifiers; earlier drafts' company names were not derivable from the data.)
6. **Returns/outcomes are largely OUT of I1's blast radius** — they're built by 07 with `pfloat`→None.
   O-1 is the only returns-side zero, source-origin, and contained. The returns side's real risk is the
   corp-action envelope (task_14), not I1.

---

## 6) TEST / VALIDATE — predicates, counts (caught / missed / over-caught), worked examples

**Predicate tested (proposed I1-b detector for subscription):**
`sub_total_x ∈ {0, 0.0} AND adj_listing_gain_open > 0.20` → flag as masked-missing.

> **Scale/column note (CORRECTED):** the substrate has NO `listing_gain` column. The only listing-gain
> columns are `adj_listing_gain_open` and `adj_listing_gain_close`, stored as **FRACTIONS** (e.g. 1.81 =
> +181%, median 0.058, max 3.87) — so "+20%" means `>0.20`, not `>20`. The predicate below names the exact
> column and threshold so it is reproducible.

- **Caught (true positives):** **32 rows** (`sub_total_x==0` AND `adj_listing_gain_open>0.20`). (The
  `adj_listing_gain_close>0.20` variant yields **36** — the choice of column changes the count; we report
  against the open anchor, the allottee-relevant listing print. This does not change the conclusion: the
  true detector is the validity rule, not the +20% demonstrator.) Examples by ISIN, gains quoted from BOTH
  columns to be unambiguous:
  - `INE0QTF01015` Vibhor Steel Tubes — sub=0, listing-open gain **+181%** / close **+196%**, src=sharescart → clearly missing, not 0.
  - `INE423Y01016` SBFC Finance — sub=0, listing-open gain **+44%** / close **+62%**, src=sharescart.
  - `INE602W01027` Senco Gold — sub=0, listing-open gain **+36%** / close **+28%** (audit's named example) — reproduced. (Note: here the OPEN gain is the higher figure — confirming the per-example numbers must name their column, not be quoted as a single ambiguous "+X%".)
- **Missed (false negatives) of this narrow predicate:** the other **92** of 124 sub=0 rows that listed
  flat/down (124 − 32) — a strong listing is sufficient-not-necessary evidence; the *real* detector is the
  validity predicate "a LISTED IPO must have sub_total_x > 0" (an IPO cannot list with literally zero
  subscription), which catches **all 124**. The +20% predicate is just the high-confidence demonstrator.
- **Over-caught (false positives) check:** of the 124 sub=0 rows, **0** are plausibly real (an IPO that
  closed and listed had *some* subscription; 0.00× is impossible post-listing). So validity-predicate
  over-catch = **0** here. Contrast `ofs_cr=0`: validity predicate "ofs_cr ≥ 0 is always valid" → catches
  **0** of 725 → correctly preserves all fresh-issue rows (over-null avoided).

**Predicate tested (min_investment recoverability):** `min_investment_rs ∈ {0} AND lot_size_shares>0 AND
issue_price>0` → recoverable.
- **Caught:** all 18 zeros satisfy it. Worked examples:
  - `INE0NJ001013` CFF Fluid Control — 0, lot 400 × ₹165 = **₹66,000** recoverable.
  - `INE0SIK01014` Gujarat Peanut — 0, lot 3200 × ₹80 = **₹2,56,000** recoverable.
- **Over-caught:** 0 (all 18 have valid lot×price; none is a genuine ₹0 investment).

**Predicate tested (market_cap parse-fail):** `market_cap_cr ∈ {0} AND issue_size_cr>0`.
- **Caught:** all 7 (e.g. `INE971P01012` Supreme Impex — mcap 0 but issue_size ₹8cr; `INE301Z01011` Soni
  Soya — mcap 0, issue ₹5cr). A listed company cannot have ₹0 market cap → all 7 are I1-b. Over-caught: 0.

**O-1 reproduction (returns side):** `INE0N0Y01013` listing_open=0 (raw) / adj=30.0 / status='ok' —
matches the audit; root confirmed in raw chittorgarh `details.csv` (`listing_open='0.00'`).

**REIT/InvIT carve-out check (CORRECTED):** `net_sales_yr3=0` → 13 rows; **8 carry
`instrument_type∈{reit,invit}`** (4 reit: `INE0CCU25019, INE0NDH25011, INE19RO25021, INE041025011`;
4 invit: `INE0NHL23019, INE1UA823019, INE2Q7823014, INE183W23014`) → these are state-(d)/N/A, must route
to the instrument gate (task_05b), NOT I1 recovery. The remaining **5 are equity** (`INE320H01019,
INE698H01018, INE009Q01019, INE695X01011, INE705X01026`) = the I1-b residual; of those, two
(`INE320H01019, INE009Q01019`) also have `net_sales_yr2==0` and need a per-row check. So the carve-out
defers **8** rows (not 5) and the I1-equity recovery set is **5** (not 8). Over-catch avoided by the
instrument check. (Substrate names are blank for these rows — identifiers are the ISINs above.)

**Cross-field (O-3) check:** `sub_qib_x==sub_nii_x==sub_retail_x==0 AND sub_total_x>1` → **32 rows**
(implausible: all tranches zero yet a positive total). `sub_total_x>0 AND ≥1 tranche==0` → **218 rows**
(partial tranche-missingness). A per-field predicate catches NEITHER — demonstrates the registry needs
cross-field predicate support (§3b-ii). Worked example: any of the 32 has a positive `sub_total_x` with all
three tranche cells `0` — these tranche cells must route to state-(b), the total kept.

**MB `sub_qib_x==0` (the implausible-MB branch):** `sub_qib_x==0` → **341 rows** = **314 SME** (state (c)
real — many SME issues genuinely have no QIB tranche, gate by board) + **27 MB** (state (b) — a listed
mainboard IPO cannot have a literally-zero QIB tranche). The 27 MB zeros are the bug case the audit flags
and route to null+flag; the SME zeros are preserved. Board-gating is what separates them.

**Financial-zero hand-off check:** verified yr3 zero counts `pat_yr3=61, eps_yr3=15,
operating_profit_yr3=29, operating_cf_yr3=90`. Predicate seed `pat_yr3==0 AND net_sales_yr3>0` is
suspicious (a loss-maker is negative, not 0). Authoritative resolution deferred to **task_16**; counts +
hand-off recorded here so the MIXED class is quantified, not a placeholder.

---

## 7) MULTI-LENS REVIEW (loop-until-quiet; stop rule = ≥2 consecutive fresh rounds, 0 new ≥LOW)

> Reviews are self-conducted here as distinct lens-passes (night-run, single agent); logged so "quiet"
> is auditable. Author lens excluded from each pass.

### Round 1
- **Correctness:** ✅ verified the mechanism by reading the raw events file (132 source-zeros) AND the
  `03_enrich.py` truthy-`'0'` propagation — not asserted from memory. FINDING-1 (LOW): the table in §3b
  reported substrate `sub_total_x` zeros=124 but raw events=132 — confirm the 8-row delta is real, not an
  error. → *Resolved (count) / DOWNGRADED (cause):* both counts are individually correct (132 raw zeros,
  124 substrate zeros). The earlier "the 8-row delta = NSE/ipowatch backfilled 8 raw-zeros" explanation is
  **NOT verified and is downgraded to a hypothesis** — the raw events files (`mainboard_events.csv` /
  `sme_events.csv`) are keyed by `company_name`, NOT `isin` (no `isin` column), so the raw→substrate join
  on the placeholder zeros cannot be performed as the explanation implied, and an ISIN join returns
  nothing. The delta is **consistent-with** the fallback chain working (substrate `sub_total_x_src` does
  carry nse/ipowatch tags) but is **not demonstrated**. To close it properly would require a name→ISIN map
  then showing which 8 raw-zero names carry a non-zero substrate value from `src∈{nse,ipowatch}`. Not
  load-bearing for the design (Option B's fallback leg stands on its own); left as an unclosed minor check
  rather than a falsely-resolved finding.
- **Completeness:** FINDING-2 (MED): audit named 6 I1 fields; I added the broader scan but must say
  explicitly which broader columns are IN-scope for the I1 fix vs deferred. → *Resolved:* §3b now splits
  masked-missing / plausibly-real / mixed; only masked-missing + mixed-after-check are I1; plausibly-real
  (ofs/borrowings) explicitly excluded.
- **Adversarial:** FINDING-3 (MED): "your validity predicate 'listed ⇒ sub>0' could itself be wrong — what
  about a withdrawn/undersubscribed IPO?" → *Resolved:* an undersubscribed IPO has sub_total_x ∈ (0,1),
  e.g. 0.4×, NOT exactly 0.00; a withdrawn issue never lists (no listing_date) so it's excluded by the
  "listed" guard. Exactly-0 on a listed name remains impossible. Predicate holds.

### Round 2
- **Context-pickup:** ✅ honored prior docs — used the existing `_src` scheme (didn't invent a parallel
  one), cross-linked the REIT/InvIT carve-out to task_05b, carried the Inox/Cat-2 whitelist per charter,
  deferred corp-action/envelope to task_14/T-2/T-4 instead of re-litigating. No new finding.
- **North-star:** ✅ Option B = field-driven (declarative, registry), single-source (extends `_src`),
  minimal-flags (3-state provenance is structural not behavioral), extensible (new column registers its
  predicate). No new finding.
- **Adversarial round 2:** tried "could 0→MISSING break a finding that currently counts these rows?" →
  it SHOULD — subscription-as-feature is currently poisoned by 124 fake zeros (audit O-2 says re-run
  those findings after fix); nulling them is the correct, intended consequence, flagged for re-derive. No
  new finding.

### Round 3 (hard-floor confirm)
- Correctness + completeness + adversarial re-pass: **NONE.** Checked: raw-vs-substrate delta explained,
  field carve-outs explicit, predicates have 0 over-catch on tested fields, O-1 reproduced from raw,
  non-equity deferred. 

> ⚠️ **Rounds 1-3 stop was PREMATURE — re-opened by an external review round (2026-06-17).** A fresh
> adversarial/correctness/completeness/context-pickup/north-star pass against ground truth found multiple
> HIGH findings the self-review missed. Logged below as Round 4; the stop rule is re-established only after
> Round 4's fixes settle. (The "auditable quiet" only counts when an INDEPENDENT fresh agent confirms it —
> which it now did NOT.)

### Round 4 (external fresh-agent review — re-verified all numbers against `data/master/ipo_analysis.csv`)
- **Correctness (HIGH):** REIT/InvIT carve-out was INVERTED — 13 `net_sales_yr3==0` = **8 non-equity
  (4 reit + 4 invit) + 5 equity**, not "5 REIT/InvIT + rest equity"; the named companies (Mindspace,
  Bharat Highways, Citius, IRB, Embassy) are NOT derivable (substrate names blank). → *Fixed* in §3b/§5/§6
  (correct counts + actual ISINs + the two-equity `yr2==0` caveat).
- **Correctness (HIGH):** §6 subscription predicate cited a non-existent `listing_gain` column and wrong
  example gains (+196/+62/+28); only `adj_listing_gain_open/close` exist (fractions). Re-run: open>0.20 →
  **32**, close>0.20 → 36. → *Fixed* — exact column+threshold stated, both-column gains quoted, count 32,
  false-negatives recomputed to 92.
- **Completeness (HIGH):** Option B's "rides existing `_src`, no parallel scheme" overstated — only
  `sub_total_x`/`gmp_pct` have a `_src` carrier; 5 other I1 fields have none. → *Fixed* — added §3b-i
  inventory + corrected the Option B cost + §8.
- **Completeness (HIGH):** cross-field O-3 (all-tranches-0-with-positive-total) not addressable by per-field
  predicates; real counts 32 / 218 (audit said 3 / 214). → *Fixed* — added §3b-ii + §6 cross-field check +
  proposal #3a (registry needs multi-column predicates).
- **Completeness (MED):** financial-zero MIXED class unquantified. → *Fixed* — §3b-iii counts
  (pat=61/eps=15/op_profit=29/op_cf=90) + task_16 hand-off + §6 check.
- **Completeness (MED):** state-(a) blanks asserted "correct already" but blank+empty-`_src` conflates
  (a)/(b). → *Fixed* — §5 item 2 corrected; encoding must distinguish blanks too.
- **Correctness (MED):** MB `sub_qib_x==0` (27 implausible) had no resolution branch. → *Fixed* — §6 +
  proposal #3 MB branch (314 SME real / 27 MB → state-b).
- **Context-pickup (MED):** FINDING-1's "8 backfilled" causal story unverified (raw is name-keyed, not
  ISIN). → *Downgraded* from "resolved" to "consistent-with-but-not-demonstrated" in Round 1 entry.
- **Correctness (LOW):** laundering framed as `03_enrich.py`-only; gmp_pct stamping is via ipocentral/
  websearch steps. → *Fixed* — §3a + §5 item 1 + proposal #4 generalized to all stamp sites.
- **Context-pickup (LOW):** schema.md L184/L191 document `issue_price_src`/`ticker_src` absent from
  substrate. → *Fixed* — flagged in §3b-i for task_01/task_03.
- **Correctness (LOW):** O-1 status-mislabel not checked for class-vs-one-off. → *Fixed* — §3c predicate
  run, count=1 (one-off).

### Round 5 (hard-floor confirm after Round-4 fixes — fresh re-pass, all numbers re-verified)
- Correctness + completeness + context-pickup + north-star + adversarial: **NONE.** Re-verified against
  `data/master/ipo_analysis.csv`: net_sales_yr3 split 8/5 ✓, sub==0 open>0.20 = 32 ✓ / close = 36 ✓,
  Vibhor open +181%/close +196% ✓, SBFC +44%/+62% ✓, Senco +36%/+28% ✓, _src cols = 15 (only 2 I1) ✓,
  cross-field 32 / 218 ✓, MB qib zeros 27 / SME 314 ✓, financial zeros 61/15/29/90 ✓, O-1 status class = 1
  ✓, gmp_pct==0 srcs ipocentral/websearch ✓. No new findings ≥LOW.

**STOP:** Round 5 is one clean fresh round after the Round-4 fixes. Per the stop rule (≥2 consecutive clean
independent rounds), **a further independent confirming round is still owed** — this task does NOT yet meet
the ≥2-consecutive-clean floor post-reopen. Marked OPEN for one more review pass before "quiet" is claimed.
(Recorded honestly rather than re-asserting a premature stop.)

---

## 8) NON-FINAL PROPOSAL + open owner-questions

### Proposal (NOT FINAL)
1. **Reframe I1** from "0→NaN at load" to **"field-aware validity routing + 3-state present/absent
   provenance"** (Option B). The zeros are *source placeholders laundered by the enrich/backfill steps*,
   not loader output — so the fix lives at **assemble/registration time**, governed by a per-field validity
   predicate declared in the column registry (task_06), with the missing-state encoded by a single compact
   provenance scheme (task_03). **Provenance-carrier reality (corrected):** only `sub_total_x` and
   `gmp_pct` have a `_src` column today; the other 5 I1 fields (`sub_qib/nii/retail_x`, `market_cap_cr`,
   `min_investment_rs`, `net_sales_yr*`) have NONE. So this is NOT a zero-new-column "just extend `_src`"
   change — it requires **adding a compact, registry-driven provenance carrier** (per the charter's
   no-per-field-boolean-explosion constraint, task_03) that covers ALL columns uniformly. The single-source
   north-star is met by one shared encoding, not by free-riding 2 existing columns.
2. **Three (really four) present/absent states**, encoded compactly via ONE registry-driven provenance
   carrier (NEW for the 5 uncarried I1 fields; reuses the IDEA of `_src` where it exists):
   `(a) source-never-published` · `(b) fetch/parse-fail OR source-placeholder` · `(c) real-zero` · plus
   `(d) N/A-for-instrument` (REIT/InvIT financials) which **defers to task_05b's instrument_type**, not I1.
   **(a)/(b) must be distinguished for BLANKS too**, not only zeros — verified all 1129 `sub_total_x`
   blanks carry empty `_src`, so a blank conflates never-published vs fetch-failed exactly as a zero does;
   the encoding must record attempted-and-failed vs never-offered.
3. **Per-field validity predicates** (the cleaning-rule seeds for task_11), each with 0 over-catch as
   tested in §6:
   - subscription `sub_total_x`: a **listed** IPO with value `==0` → state (b) (null + flag) — 124 rows.
   - subscription tranches `sub_qib_x`: gate by board — **SME** `==0` is state (c) real (no QIB tranche,
     314 rows, preserve); **MB** `==0` is state (b) (a listed mainboard IPO cannot have a literally-zero QIB
     tranche — 27 rows → null+flag, e.g. the 27 MB rows in the 341 total). Same board-gate for nii/retail.
   - `min_investment_rs==0` with lot×price>0 → **recover** = lot_size_shares × issue_price (a derived
     cleaning rule, not just null).
   - `market_cap_cr==0` on a listed name → state (b) (null; keep `market_cap_class` only if independently
     derivable — note O-8/D-3 as-of-semantics belongs to task_17).
   - `gmp_pct==0` → state (b) unless pre-2023 SME (then state (a)); backfill from investorgain (task_02).
   - `net_sales_yr3==0` (13 rows): if instrument_type∈{reit,invit} → state (d) defer to task_05b (**8 rows**
     — 4 reit + 4 invit); else state (b) equity recover/flag (**5 rows**), but per-row check the two with
     `net_sales_yr2==0` too (`INE320H01019, INE009Q01019`) — they may be genuinely financials-unavailable,
     not a parse-fail.
   - **DO NOT touch** `ofs_cr`/`ofs_pct==0` (real fresh-issue) or `borrowings_*==0` (real debt-free) —
     these are state (c); a global rule would corrupt 725+ correct rows.
3a. **Cross-field validity predicates (the real O-3) — the registry must support multi-column predicates.**
   Per-field rules cannot express "tranches sum to ~0 but total is positive." Add a predicate class:
   `sum(sub_qib_x, sub_nii_x, sub_retail_x) consistent with sub_total_x within tolerance, else route the
   tranche cells to state-(b) missing` (keep the total). Verified targets: **32** all-tranches-zero-with-
   positive-total + **218** partial-tranche-missing rows. If task_06's registry stays per-field-only, this
   O-3 class falls through — so the cross-field predicate is a first-class registry requirement.
3b. **Financial-zero fields → hand off to task_16 (quantified, not dropped).** `pat_yr3=61, eps_yr3=15,
   operating_profit_yr3=29, operating_cf_yr3=90` zeros. Seed predicate `pat_yr3==0 AND net_sales_yr3>0` is
   suspicious (loss-maker is negative, not 0). Authoritative resolution belongs to task_16; task_19 records
   the counts + the explicit hand-off so the MIXED class is not an unsized placeholder.
4. **Stop EVERY enrich/backfill step from stamping a real `_src`/provenance on a placeholder** (the
   laundering is a multi-site pattern, not a `03_enrich.py`-only defect): `03_enrich.py` stamps it for
   `sub_total_x` (all 124 carry `_src='sharescart'`), and the GMP-backfill steps stamp it for `gmp_pct`
   (the 10 zeros carry `_src∈{ipocentral, websearch}`). The fix is a **stamping policy applied at every
   assemble/stamp site**: a value must pass its validity predicate before it earns a source tag; otherwise
   it gets the (b) provenance state.
5. **O-1 residual:** repair the raw `listing_open` for INE0N0Y01013 from the adjusted value, OR downgrade
   `listing_metrics_status` from `ok` (it relied on the adjusted-column rescue). Containment otherwise
   holds — Layer-3 already uses the correct adjusted column.
6. **Returns/outcomes:** no I1 change needed (07 already emits None→''); the only returns-side risk is the
   corp-action envelope, owned by task_14 / T-2 / T-4 — and **INE312H01016 (Inox) must NOT be clamped**
   (Cat-2 genuine crash).
7. **Re-derive downstream:** once the 124 fake subscription zeros become MISSING, any
   subscription-as-feature finding must be re-run (audit O-2) — intended, flagged for the reconciliation
   campaign (task_09).

### OPEN OWNER-QUESTIONS
1. **Adopt the field-aware reframe** (Option B) over the original global "0→NaN at load" leaning?
   (Ground truth shows a global rule would corrupt 725 real `ofs_cr=0` + debt-free `borrowings=0` rows.)
2. **min_investment_rs:** RECOVER from lot×price (derived), or just mark MISSING? (Recovery is exact and
   row-local; 18 rows.)
3. **3-state vs 4-state provenance:** keep REIT/InvIT "N/A-for-instrument" as a *separate* state (d) routed
   to task_05b, or fold it into "absent (a)"? (Recommend separate — it's a different truth.)
4. **`market_cap_class` on a (b)-nulled `market_cap_cr`:** drop the class too, or keep it if independently
   derivable? (Crosses D-3/task_17 as-of-semantics.)
5. **O-1:** repair raw `listing_open` (write 30.0), or leave raw=0 and only downgrade
   `listing_metrics_status`? (No Layer-3 impact either way; question is master-display honesty.)
6. **Scope of the I1 sweep:** apply the per-field validity routing to the FULL ≥5-zero column list (§3b)
   now, or only the 6 audit-named fields first and expand via the registry later?
7. **New provenance carrier (cost surfaced):** 5 of 7 I1 fields have NO `_src` column today (§3b-i). Accept
   adding a compact registry-driven provenance carrier covering ALL columns uniformly (one shared
   encoding), vs. only the 2 fields that already have `_src`? (Recommend the uniform carrier — single
   source of truth, north-star — but it is a larger task_03/task_06 change than "just extend `_src`".)
8. **Cross-field predicates in the registry:** approve extending task_06's per-field registry to support
   multi-column validity predicates (needed for the O-3 tranche-vs-total class, 32+218 rows)?

---

### DONE CHECKLIST
- ☑ all 8 steps present and non-empty
- ☑ ground-truth inputs cited by FILE PATH (§2)
- ☑ step-6 numbers present (caught/missed/over-caught + ≥2 ISIN examples per predicate: Vibhor/SBFC/Senco
  with exact columns; CFF/Gujarat Peanut; Supreme/Soni Soya; Udayshivakumar; the 8 REIT/InvIT + 5 equity
  net_sales ISINs; cross-field 32/218; MB-qib 27/SME 314; financial-zero hand-off counts)
- ☐ review-loop stop rule NOT yet satisfied — REOPENED by external review (round 4 found HIGH findings; round 5
  clean but the post-reopen ≥2-consecutive-clean floor needs one more independent confirming round; logged §7)
- ☑ NOT-FINAL marker + open-owner-questions block present
