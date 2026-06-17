# Cluster 3 — Cleaning Rules · Reproducibility Overlay · Reconciliation · Rule-Applicability · Features↔Data

> **STATUS: NOT FINAL.** Design / think-only synthesis for the 2026-06-17 night run. ZERO code, zero
> pipeline changes, zero commits. Every count cited is taken from the already-written Group-B issue files
> (`task_14..task_20`), `rules/index.md`, and a read-only inspection of the overlay seeds + pipeline
> read-points; where a number is load-bearing its owning task is named so it can be re-verified. This is a
> CONNECTED design section, not five fragments — the five sub-designs share ONE rule shape, ONE overlay,
> ONE provenance scheme (owned by Cluster 1), ONE identity scheme (owned by Cluster 2).
>
> **Cross-cluster ownership (referenced, not re-decided here):**
> - **Cluster 1** owns the **schema**, the **`quality` partition column** (`clean | dirty`), and the
>   **3-state present/absent provenance** (`source-never-published (a) | fetch-parse-fail OR
>   source-placeholder (b) | real-zero (c)`, plus `(d) N/A-for-instrument`). Cluster 3 *consumes* these:
>   every cleaning rule's terminal action is expressed in Cluster-1 vocabulary (`route quality=dirty`,
>   `set provenance=(b)`), never a new parallel flag.
> - **Cluster 2** owns **identity / matching** (ISIN primary key; corp-actions match by symbol∪ISIN with a
>   trading-date window; pre/post-split ISIN-drift; reused-symbol collision). Cluster 3 *invokes* the
>   resolved identity but does not redesign the join (ROLEXRINGS' INE645S01016↔INE645S01024 drift is a
>   Cluster-2 fact this section depends on).
>
> North-star throughout: **CLEAN · EXTENSIBLE · CORRECT** — declarative rules (no behavioral if/else
> sprawl), single source of truth (no duplicate overlays/registers), flag-don't-guess, flag-don't-clamp.

---

## 0. The thread that ties the five sub-designs together

The five charter items in this cluster are not independent — they are one pipeline of the same object:

```
   a data issue (Group B)                       a re-run happens
        │                                              │
        ▼                                              ▼
 ┌──────────────────┐   declarative   ┌──────────────────┐   ordered/idempotent  ┌──────────────┐
 │ CLEANING-RULES   │──── rule ──────▶│ REPRODUCIBILITY  │──── replay ──────────▶│  SUBSTRATE   │
 │ MODEL (§1)       │   shape         │ OVERLAY (§2)     │                       │ (clean/dirty)│
 └──────────────────┘                 └──────────────────┘                       └──────┬───────┘
        ▲                                      ▲                                         │
        │ which rule fires on which row        │ one-time trust build                    │ consumed by
        │                                      ▼                                         ▼
 ┌──────────────────┐                 ┌──────────────────┐                       ┌──────────────┐
 │ RULE/HYPOTHESIS  │                 │ RECONCILIATION   │                       │ FEATURES /   │
 │ APPLICABILITY(§3)│                 │ CAMPAIGN (§4)    │                       │ PREDICTOR(§5)│
 └──────────────────┘                 └──────────────────┘                       └──────────────┘
```

- A **cleaning rule** (§1) is the *unit*: condition → action → confidence → provenance-tag → owner-decision?.
- The **overlay** (§2) is *where a rule's hand-resolved output is captured* so a re-run reproduces it.
- The **reconciliation campaign** (§4) is the *one-time event* that makes `pipeline + overlay = substrate`
  trustworthy by diffing a fresh rebuild against today's substrate.
- **Rule-applicability** (§3) is the *gate* deciding which cleaning rule AND which downstream hypothesis is
  even allowed to touch a given row (era / cohort / instrument / data_quality_tier / min-N).
- **Features↔data** (§5) is the *reverse map* — for every built feature quirk, is the root cause a data bug
  one of these rules can fix at the data layer (vs a genuine modelling limitation)?

A rule that can't be captured in the overlay, can't survive reconciliation, or can't be gated by
applicability is **mis-shaped** — the four sections are mutually constraining by design.

---

## 1. CLEANING-RULES MODEL (declarative)

### 1.1 The single rule shape (one shape for ALL issue classes)

Every cleaning rule — whether it nulls a fake zero, recovers a value arithmetically, or quarantines a
corrupted financial — is ONE declarative record with the same six slots. There is exactly **one rule shape**;
issue classes differ only by what they fill in, never by bespoke code.

```
RULE
  id            : stable identifier (e.g. CR-SUB-ZERO, CR-EPS-SHAREBASE)
  target        : { columns:[...], scope-predicate (which rows this rule even considers) }
  condition     : a boolean predicate over the row (may be CROSS-FIELD — see §1.4)
  action        : ONE of
                    • FIX-VALUE     (deterministic recompute, e.g. min_inv = lot × issue_price)
                    • FLAG-ONLY     (null/keep the value, set provenance state, do NOT change quality)
                    • QUARANTINE    (route row → quality=dirty until resolved)
  confidence    : HIGH | MED | LOW   (drives whether action auto-applies or only proposes)
  provenance-tag: the Cluster-1 state to stamp — (a)/(b)/(c)/(d) + a reason string
  owner-decision: NULL  | a pending owner question id (rule is PROPOSED, not auto-applied, until answered)
  applicability : the gate from §3 (era / cohort / instrument_type / data_quality_tier / board / min-N)
```

Key invariants:
- **Action is the routing verb.** `FIX-VALUE` → row stays clean, cell replaced + provenance=`derived`.
  `FLAG-ONLY` → row stays clean, cell nulled + provenance=`(b)`. `QUARANTINE` → row leaves the clean
  substrate (`quality=dirty`) and joins the worklist. *Clean vs dirty is decided entirely by which action
  fires* — see §1.3.
- **Confidence governs automation, not truth.** HIGH → auto-apply on every run. MED → auto-apply but list
  in the dirty/review worklist for owner spot-check. LOW or `owner-decision != NULL` → PROPOSED-only: the
  rule computes its verdict but does NOT mutate the substrate until the owner answers.
- **Provenance-tag is mandatory and is Cluster-1's vocabulary.** A rule may never invent a new boolean
  column (that is the flag-sprawl the north-star forbids). It writes into the one compact provenance carrier.
- **No clamping.** A rule may null, recover, or quarantine — it may NEVER silently winsorize a value into a
  plausible band (the condemned T-4 / `np.clip` anti-pattern; task_16 §4 found the scorecard's own
  `np.clip` already masks Indiqube D/E −409.5 → debt-score 100, so quarantine must happen UPSTREAM of any
  consumer's clip).

### 1.2 How a rule routes a row CLEAN vs DIRTY (the decision the charter asked for)

```
        for each row, for each applicable rule (gated by §3):
        ┌───────────────────────────────────────────────────────────┐
        │ condition false?  ──▶ rule does nothing (row unaffected)   │
        │ condition true:                                            │
        │   action = FIX-VALUE  + confidence HIGH ─▶ replace cell,   │
        │                                            prov=derived,   │
        │                                            row stays CLEAN │
        │   action = FLAG-ONLY  ───────────────────▶ null cell,      │
        │                                            prov=(b)/(a),   │
        │                                            row stays CLEAN │
        │                                            (cell missing,  │
        │                                             row usable)    │
        │   action = QUARANTINE ───────────────────▶ row → DIRTY     │
        │                                            (whole row out  │
        │                                             of clean view) │
        │   owner-decision pending ────────────────▶ PROPOSED only;  │
        │                                            row → DIRTY-    │
        │                                            REVIEW (visible │
        │                                            but excluded)   │
        └───────────────────────────────────────────────────────────┘
```

The distinction the charter wants is **cell-level vs row-level damage**:
- A *single bad cell* on an otherwise-good row → `FLAG-ONLY` (null the cell, keep the row clean; the row is
  still usable for every feature that doesn't read that cell). Example: `gmp_pct=0` masked-missing → null
  `gmp_pct`, prov=(b); the row's returns/subscription are fine.
- A *value that contaminates derived features and can't be locally repaired* → `QUARANTINE` the row until a
  human/overlay supplies the fix. Example: Ujjivan `pre_ipo_net_sales=18` poisons margin + the validated
  `tiny_sales_lt25cr` flag + the analog distance → the whole row is untrustworthy for the quality component,
  so `quality=dirty` until corrected. A quarantined row is **promoted back to clean** the instant the overlay
  (§2) supplies a value that makes the condition false — the worklist shrinks, never a permanent store.

This is exactly the charter's leaning ("dirty = a derived view, a quarantine that shrinks as rows get
fixed") realized through the action verb. **`quality` is set by Cluster 1; Cluster 3's rules are the only
thing that writes it**, and they write it only via `QUARANTINE`.

### 1.3 Issue-class → rule-shape map (built DIRECTLY on Group B)

Each row is a real issue class from the Group-B re-audits, expressed in the single rule shape. Counts are
the owning task's reproduced figures (re-verify there).

| id | issue class (Group B) | condition (predicate) | action | conf | prov | owner-Q? |
|---|---|---|---|---|---|---|
| **CR-SUB-ZERO** | O-2 subscription masked-zero (task_15/19; 124 rows) | row is LISTED AND `sub_total_x == 0` | FLAG-ONLY (null) | HIGH | (b) | — |
| **CR-SUB-TRANCHE** | O-3 tranche masked-missing (task_15/19; cross-field) | `sum(qib,nii,retail) ≈ 0` (numeric) AND `sub_total_x > 0` → null the tranche CELLS, keep total | FLAG-ONLY | HIGH | (b) | — |
| **CR-QIB-BOARD** | O-3 MB-vs-SME QIB zero (task_19; 27 MB bug / 314 SME real) | `sub_qib_x == 0` AND `board == MB` AND listed | FLAG-ONLY | HIGH | (b) | — |
| | (same column, SME) | `sub_qib_x == 0` AND `board == SME` | NO-OP (real: no QIB tranche) | HIGH | (c) | — |
| **CR-GMP-ZERO** | O-4 GMP masked-zero (task_15; 10 rows) | listed AND `gmp_pct == 0` AND NOT (pre-2023 SME) | FLAG-ONLY | HIGH | (b) | Q-backfill |
| | (pre-2023 SME) | `gmp_pct == 0` AND era=pre-2023 AND board=SME | FLAG-ONLY | HIGH | (a) source-never-published | — |
| **CR-MININV-RECOVER** | O-14 min_investment masked-zero (task_18/19; 18 rows) | `min_investment_rs == 0` AND `lot_size_shares > 0` AND `issue_price > 0` | **FIX-VALUE** = `lot × issue_price` | HIGH | derived | — |
| **CR-MCAP-ZERO** | O-15 market_cap zero (task_17; 7 rows) | listed AND `market_cap_cr == 0` | FLAG-ONLY (null) + null `market_cap_class` | HIGH | (b) | — |
| **CR-MCAP-ASOF** | D-3 / O-8 as-of leak (task_17) | `market_cap_cr` is CURRENT cap on a row consumed at-IPO | split into `*_at_ipo_cr` / `*_current_cr` (§5) | MED | as-of attr | Q-asof |
| **CR-MCAP-ENTITY** | O-12 wrong-entity join (task_17; 1 row, Bajaj) | `market_cap_at_ipo_cr / issue_size_cr ∉ [1,20]` | QUARANTINE | MED | (b) | — |
| **CR-EPS-SHAREBASE** | O-5/O-7 EPS share-base discontinuity (task_16; 51/57/95 rows) | `|eps_yrN / eps_yr_latest|` implied share-base differs > ~50× | FLAG-ONLY (null the non-comparable year) | MED | (a) published-not-comparable | Q-eps |
| **CR-EPS-SIGN** | EPS↔PAT sign break (task_16; 34 rows) | `sign(eps_*) ≠ sign(pat_*)` | QUARANTINE | MED | (b) | — |
| **CR-SALES-IMPLAUS** | O-10 tiny-denominator margin (task_16; 11 rows) | `pre_ipo_net_sales < 25` AND `|implied margin| > 80%` | QUARANTINE | MED | (b) | Q-repair |
| **CR-SF-DENOM** | O-9 negative/near-zero equity (task_16; 19 rows `sf≤0`) | `shareholder_funds_yr3 ≤ 0` OR `|sf|` tiny vs pat/borrow → quarantine ROE/DE | QUARANTINE (the ratio cells) | MED | (b) | — |
| **CR-PE-NEG** | negative P/E (task_16; 46 rows) | `pe_ratio < 0` (loss-maker) | FLAG-ONLY (null) | HIGH | (b) | — |
| **CR-NONEQ-FIN** | O-6 REIT/InvIT in equity table (task_16/19; 8 rows) | `net_sales_yr3 == 0` AND `instrument_type ∈ {reit,invit}` | FLAG-ONLY (defer to instrument gate, §3) | HIGH | (d) N/A-for-instrument | Q-noneq |
| **CR-DATE-ORDER** | O-11 date transposition (task_18; 3 rows) | NOT (`open ≤ close ≤ listing`) where all present | QUARANTINE | HIGH | (b) | — |
| **CR-BAND-INVERT** | O-13 band inversion (task_18; 1 true) | `price_band_low > issue_price` | QUARANTINE | HIGH | (b) | — |
| **CR-CORP-OVERCOUNT** | D-1 over-adjustment (task_14; 8 `<Rs1`, 12 dup-clusters) | price-gap arbiter disagrees with applied cumulative factor | FIX-VALUE (collapse) / QUARANTINE if arbiter blind | MED | (b) | Q-corp |
| **CR-CORP-PROTECT** | Cat-2 genuine path (task_14/20; 67 ISIN whitelist) | ISIN ∈ Cat-2 whitelist | NO-OP (never synthesize a split) | HIGH | — | — |

Notes that keep this honest (from the re-audits):
- **CR-CORP-OVERCOUNT is the hardest** and is NOT a single predicate — it delegates the arbitration to the
  price-gap detector (task_14 Option A) and to Cluster-2's symbol∪ISIN window join. When the arbiter is
  **blind** (empty-ISIN yfinance with no own series; coverage starts after ex_date; `ex_date > last_trade`,
  e.g. E2E/FORGE multibaggers) the action is QUARANTINE/defer-to-override — **never auto-drop** (task_14
  R11-B2). The Cat-2 whitelist (CR-CORP-PROTECT) is a HIGH-confidence guard rule that runs *first* and
  vetoes any synthesis on a verified-genuine outcome.
- **Cross-field conditions are first-class** (CR-SUB-TRANCHE) — see §1.4.
- **No global "0→NaN" rule exists** — task_19 proved a blanket rule would destroy 725 legitimate `ofs_cr=0`
  fresh-issue rows + debt-free `borrowings=0`. Every zero rule is field-aware (the `(c) real-zero` column in
  task_19 §3b is the do-not-touch set, encoded as NO-OP rules).

### 1.4 Cross-field predicates (a registry requirement, not an afterthought)

task_19 §3b-ii proved a per-field predicate cannot express O-3 ("tranches sum to ~0 but total is positive",
32 rows; partial-tranche-missing, 218 rows). So the rule `condition` slot must support **multi-column
predicates** over the row. This is a constraint Cluster 3 imposes on the Cluster-1 column registry: the
registry's validity-predicate facility must accept N-column predicates, not just `f(this_cell)`. CR-EPS-SIGN
(eps vs pat), CR-SF-DENOM (ratio vs its denominator), CR-DATE-ORDER (three dates), CR-CORP-OVERCOUNT (action
vs price gap) are all inherently cross-field.

### 1.5 Worked routing examples (clean vs dirty)

- **INE0QTF01015 Vibhor Steel** — `sub_total_x=0`, listed +181%. CR-SUB-ZERO fires → null `sub_total_x`,
  prov=(b). Row **stays CLEAN** (its returns/financials are fine; only subscription-as-feature now reads
  missing). Cell-level damage → FLAG-ONLY.
- **INE334L01012 Ujjivan** — `pre_ipo_net_sales=18`, margin 983%, fires the validated `tiny_sales_lt25cr`
  flag on a multibagger bank. CR-SALES-IMPLAUS fires → **QUARANTINE** (`quality=dirty`). The whole row is
  untrustworthy for the quality/wipeout-safety components until the overlay supplies a corrected sales (DRHP
  ~₹1,800cr). Row-level damage → QUARANTINE. Promoted back to clean when the overlay value lands.
- **INE0NJ001013 CFF Fluid** — `min_investment_rs=0`, lot 400 × ₹165. CR-MININV-RECOVER fires → FIX-VALUE
  66,000, prov=derived. Row **stays CLEAN**, value recovered deterministically (no overlay needed).
- **INE933K01021 Bajaj Corp** — `market_cap_cr=292355` (wrong entity, ~36× too large). CR-MCAP-ENTITY fires
  → QUARANTINE. Row out of clean view until the join is fixed / overlaid.

---

## 2. REPRODUCIBILITY OVERLAY (`pipeline output + ordered overlay = substrate`)

### 2.1 What already exists (the seeds — verified read-only)

Two overlay seeds are LIVE today, with two different shapes and two different read-points:

- **`data/reference/manual_overrides.csv`** — shape `isin,column,value,reason,date`; **3 rows, all
  `market_maker`**. Read by `pipeline/09_assemble.py` (L98-112): `by_isin_ov` keyed on `isin`, applied at
  the very END of assemble (`row[o['column']] = o['value']`), explicitly so a re-run reproduces hand-facts
  ("they used to live only in the output files and silently vanished on re-run" — the 2026-06-04 showdown
  finding). This is the canonical "cell-override-by-ISIN" overlay and the model for the general design.
- **`data/reference/corp_actions_merged.csv`** — shape `isin,symbol,action_type,raw_subject,ratio_factor,
  ex_date,source`; **1897 rows** (nse:equities 1341, yfinance 354, nse:sme 163, **manual_thinktank_audit
  34, verification_2026-05-31 5**). Read by `pipeline/07_returns_summary.py` `load_corp_actions()` (L91-111)
  → keyed by ISIN AND symbol, deduped only by `(ex_date, ratio_factor)` in `actions_for()` (L114-127). The
  34+5 manual tags are an *embedded* overlay inside a mostly-scraped file.

Plus the un-formalized catalogs the charter/task_08 enumerate: `unresolved_88_mismatches_audit.md`
**Category-1** (21 decided-but-unapplied split overrides WITH ratios), `docs/research/data/drhp_recovered.csv`
(16 SEBI-DRHP financials with `pat_suspect` flags), and the DRHP staging. **task_20 proved these are not a
solved problem:** the Cat-1 corrections ARE in `corp_actions_merged.csv` yet the fake multibaggers persist
because the JOIN that consumes them is buggy, AND commit `e6053e7`'s hand-null of O-3 cells was CLOBBERED by
the later `26cd1fd` rebuild (a non-idempotent rebuild dropped a hand-fix). So today's overlay mechanism
fails 4 of the 5 hard parts below.

### 2.2 The unified overlay design (built ON the seeds)

**One overlay store, one shape, multiple read-points by phase.** Generalize `manual_overrides.csv`'s shape
into the canonical entry; the corp-action manual tags and Cat-1/DRHP catalogs migrate INTO it (so there is a
single source of truth, not three parallel hand-fix files — north-star).

```
OVERLAY ENTRY (one row, append-only ledger):
  key        : { isin (primary) , symbol , ex_date }   ← Cluster-2 identity; ex_date for event-overlays
  target     : column  (or action_type for a corp-action event)
  old_value  : the pipeline value this entry overrides at capture time (for conflict-detection, §2.3-4)
  new_value  : the corrected value
  op         : SET | DELETE-EVENT | ADD-EVENT | RECOMPUTE   ← so a corp-action FAKE can be removed, not just edited
  reason     : provenance string (WHY — e.g. "DRHP FY16 sales ₹1,800cr; screener 18 implausible")
  source     : manual_thinktank | drhp_recovered | cat1_88audit | verification_<date> | ...
  confidence : HIGH|MED|LOW   (mirrors the cleaning-rule confidence)
  seq        : monotonic ordering key (§2.3-2)
  date       : capture date
  retired    : bool + retire-reason  (§2.3-5)
```

This single shape subsumes BOTH seeds: a `market_maker` cell-fix is `op=SET`; a fake ROLEXRINGS split is
`op=DELETE-EVENT` keyed on `(symbol, ex_date)`; a missing Indiabulls bonus is `op=ADD-EVENT`. The substrate
identity `= pipeline_output ⊕ apply(overlay, ordered)`.

### 2.3 The five hard parts (each solved explicitly)

**1) CAPTURE** — every post-pipeline hand-fix becomes an overlay entry (never a direct edit to a master
CSV). The cleaning-rules model (§1) is the producer: a rule whose action is FIX-VALUE/FLAG-ONLY/QUARANTINE
with `owner-decision` answered emits an overlay entry carrying its `reason` and `confidence`. Today's three
embedded catalogs are CAPTURED by migrating them into the ledger: the 34 `manual_thinktank_audit` rows → 34
`ADD/SET` entries; the 21 Cat-1 splits → 21 `ADD-EVENT` entries (the one missing — INE399K01017 — stays an
OPEN owner-Q, not a silent gap); the 16 `drhp_recovered` rows → financial `SET` entries with their
`pat_suspect` flag preserved as `confidence=LOW`. **Nothing hand-fixed lives only in an output file** (the
showdown lesson, generalized).

**2) ORDER / SEQUENCING** — entries replay in a **deterministic order** by `(seq, date, id)`, NOT as an
unordered bag, because fixes can be order-dependent: a corp-action `ADD-EVENT` must apply before a
returns-recompute that consumes it; two entries touching the same cell apply last-writer-by-seq. The overlay
is applied in **phase-appropriate read-points** mirroring today's split: corp-action event-overlays are
consumed at the `07_returns_summary` phase (where `corp_actions_merged.csv` is read); cell-value overlays at
the `09_assemble` END phase (where `manual_overrides.csv` is read). `seq` is assigned at capture and is
stable, so replay is reproducible across runs and across machines.

**3) IDEMPOTENCY** — applying the overlay twice == once. This is the part TODAY FAILS (task_20 §3D:
`e6053e7` clobbered by `26cd1fd`). The fix: overlay application is a **pure function of (fresh pipeline
output, overlay ledger)** with no in-place accumulation — the substrate is always rebuilt from scratch +
overlay, never edited and re-saved. Because each entry carries `old_value`, re-applying is a no-op when the
cell already equals `new_value` AND can detect when the pipeline value moved (§2.3-4). A corp-action
`DELETE-EVENT` is idempotent (deleting an already-absent event is a no-op + a conflict flag). The
non-idempotent in-place rebuild that re-introduced `0` into O-3 cells is structurally eliminated.

**4) CONFLICT-DETECTION** — on each run, before applying entry E, compare the *current* fresh pipeline value
`v_now` against `E.old_value`:
- `v_now == E.old_value` → normal: the pipeline still emits the value the fix was overriding → apply
  `new_value` silently.
- `v_now == E.new_value` → the **pipeline now emits the right value natively** → the entry is a
  **retire-candidate** (§2.3-5): apply is a no-op, flag for retirement.
- `v_now ∉ {old,new}` → the **underlying pipeline value CHANGED** (e.g. a yfinance refresh changed a ratio —
  the exact mechanism behind the ROLEXRINGS triple-report). The correction usually still wins, BUT this is
  surfaced as a **reconciliation diff** (§4) so an obsolete fix gets re-reviewed rather than silently masking
  newly-correct data. This is the charter's hard requirement #4, made concrete via `old_value`.

**5) PROVENANCE + RETIRE-ABILITY** — every entry records WHY (`reason`, `source`, `confidence`). When
conflict-detection finds `v_now == new_value` (pipeline now native-correct), the entry flips `retired=true`
with reason "pipeline emits natively as of <run>". Retired entries stay in the ledger (audit trail / git
history is the drift-free record) but no longer apply. This is how the overlay SHRINKS as the pipeline
improves — the same shrink-to-zero discipline as the dirty quarantine in §1.

### 2.4 Testability

Architectural; validated by walkthrough against the seeds: (i) the 3 `manual_overrides` rows replay as 3
`SET` entries at the 09 phase — bit-identical to today's behavior; (ii) the ROLEXRINGS fake-split is
expressible as `op=DELETE-EVENT key=(ROLEXRINGS, 2025-09-19 & 2025-10-03)` — which today's
`(ex_date,ratio_factor)`-only dedup canNOT express (it keeps distinct ex_dates), proving the new `op`
vocabulary is necessary; (iii) the e6053e7 clobber is impossible under the pure-rebuild model because the
O-3 null is an overlay entry re-applied on every run, not an in-place CSV edit.

---

## 3. RULE / HYPOTHESIS APPLICABILITY (the data ↔ rule mapping, declarative)

### 3.1 The problem

Two distinct populations of logic must be gated to the right rows: **cleaning rules** (§1 — must not fire on
rows where the condition is genuinely valid) and **downstream hypotheses/findings/score-components**
(`rules/index.md` — must not run on data they were never validated on). A naive "run everything on every row"
re-introduces every false-positive the Group-B re-audits found (the global-0→NaN that nukes `ofs=0`; an
equity-only finding running on a REIT). Applicability is the gate that prevents this — and it must be
**declarative data**, not hardcoded `if instrument_type == 'reit'` branches scattered across consumers.

### 3.2 The applicability vector (attached to every rule AND every hypothesis)

Each rule/hypothesis declares a gate over five structural dimensions — all already columns (or
Cluster-1/2-owned dimensions) on the substrate, so the gate is pure data:

| dimension | values | who owns it | example gate |
|---|---|---|---|
| **instrument_type** | equity / fpo / reit / invit / idr / ncd | Cluster 2 / task_05b | equity-only financials & N14 wipeout flags |
| **board** | MB / SME | substrate `type` | QIB-zero rule (SME real, MB bug); anchor finding (MB-only) |
| **era / cohort** | boom (2020-26) / longterm (2006-19) | listing date | subscription/GMP findings (boom-only — longterm sub ≈ 0); pe_vs_sector (no longterm P/E) |
| **data_quality_tier** | high / medium / low | substrate | exclude `low` from optimistic base rates (t7 bias audit: low-tier wipeout 21-33% vs 6-9%); exclude `unreliable_coverage` from listing-pop |
| **min-N floor** | integer | per-finding | suppress a sector/segment cell below ~30 (n15 cell floor; T-2c "thin") |

### 3.3 Declarative mapping (built on `rules/index.md` ground truth)

The mapping is a table, not code. `rules/index.md` ALREADY records the applicability verdict for every
signal — it is the de-facto applicability register; this section formalizes it as a machine-readable gate so
consumers stop re-deriving it. Representative gates pulled from `rules/index.md`:

| logic | applicability gate (declarative) | source in rules/index.md |
|---|---|---|
| n2-subscription, n3-demand-skew, n6-valuation, pe_vs_sector | `era == boom` (longterm has ~0 subscription / no P/E) | "boom-only" / "single-regime" markers |
| n5-anchor | `era == boom AND board == MB` | "boom-MB primary (SME anchor thin)" |
| x-nonequity | `instrument_type ∈ {fpo,reit,invit}` — analyzed SEPARATELY, never pooled with equity | "SEPARATE from equity IPOs (user decision)" |
| n14 wipeout flags, all financial findings (n7/n8/n13/n15/t9) | `instrument_type == equity` | NCD/REIT contaminate financials (task_16 O-6) |
| t7 base rates / optimistic stats | EXCLUDE `data_quality_tier == low` | "excluding them biases optimistic" |
| listing-pop analyses | EXCLUDE `listing_metrics_status == unreliable_coverage` | CLAUDE.md Layer-2 note |
| strat-combined-score | `horizon == 3y` (OOS-validated); 1y display-only | "3-YEAR ranking tool ... NOT a 1-year signal" |
| any cross-regime claim | requires sign-stable in BOTH `era` cells | validate.py VALIDATED set |

### 3.4 The gate runs in TWO places (and they must agree)

- **At clean time** — a cleaning rule's `applicability` decides whether its condition is even evaluated
  (CR-QIB-BOARD only on MB; CR-NONEQ-FIN only on reit/invit). Mis-gating = the false-positives the re-audits
  killed.
- **At analysis time** — a finding/score-component's `applicability` decides which substrate rows feed it.
  Equity-only findings MUST NOT run on the 8 REIT/InvIT `net_sales=0` rows (task_19) — gated via
  instrument_type from Cluster-2/task_05b.

**Single source of truth:** the gate is declared ONCE per logic item (in the rule/finding registry) and read
by both the cleaner and the analyzer — never re-implemented per consumer. This is the §3 contribution to the
north-star: applicability is data, applied uniformly, not behavioral branches.

### 3.5 Testability

`rules/index.md` is the ground-truth cross-check: every "boom-only / MB-only / separate / not-cross-regime"
marker in it maps to exactly one gate above (walkthrough confirms 1:1 coverage of the named markers). The
over-catch test: applying the equity-financials gate drops the 5 big O-6 REIT/InvIT offenders from the equity
table (task_16) — 0 legitimate equity rows lost (the 5 equity shells route to I1, not the gate).

---

## 4. RECONCILIATION CAMPAIGN (the one-time trust build)

### 4.1 The campaign (charter §B, made concrete)

```
  1. BUILD the overlay   — migrate all hand-fix catalogs into the unified ledger (§2.2):
                           manual_overrides (3) + corp_actions manual (34+5) + Cat-1 (21) + drhp (16).
  2. REGENERATE fresh    — run the full pipeline from CACHED RAW (no live calls — §4.3) → fresh output;
                           apply the overlay (ordered, idempotent) → candidate substrate.
  3. DIFF vs current     — cell-by-cell + row-membership diff candidate vs today's data/master/ipo_analysis.csv.
  4. EVERY mismatch is a BUG — classify each diff:
                           • new-data error  (the fresh pipeline regressed / a buggy join — e.g. D-1)
                           • stale hand-fix  (an overlay entry the pipeline now supersedes → retire, §2.3-5)
                           • silent-drop     (a row that VANISHED — see §4.2)
                           • genuine improvement (a real bug the rebuild fixes — expected, must be confirmed)
  5. REVIEW + RESOLVE    — resolve each diff (fix the join / retire the entry / restore the dropped row),
                           re-run, re-diff, until the only diffs are intended improvements.
  6. TRUST → LIVE        — only when all diffs are resolved + owner-trusted do we declare
                           `pipeline + overlay = substrate` LIVE. Doubles as a full integrity sweep.
```

This campaign STOPS other dev while it runs (charter §B). task_20 is the evidence it is needed: the substrate
was rebuilt at `26cd1fd` WITH the corrections present, yet 7 fake multibaggers persist (broken join) and an
O-3 hand-null was reverted (non-idempotent rebuild) — exactly the class of bug the diff in step 4 surfaces.

### 4.2 Silent-drop is a first-class diff CLASS

task_09/charter §D require this: naked `try/except` row-drops (backlog TD-7) make rows vanish
non-deterministically — breaking BOTH reproducibility and completeness. The diff in step 3 therefore compares
**row membership (by ISIN set)**, not just cell values. A row present in today's substrate but absent from the
fresh rebuild (or vice-versa) is a `silent-drop` diff — it must surface and be explained, never disappear
quietly. (This is also why the substrate row-count is "movable" and must be read from `substrate_meta.json`,
not assumed.)

### 4.3 Fencing the reproducibility breakers (so the rebuild is deterministic)

The campaign's "regenerate fresh" step is only trustworthy if the rebuild is deterministic. The known
breakers (verified in code + charter §D) and their fences:

| breaker | where | fence |
|---|---|---|
| **Live Yahoo calls** | `06_validate_tickers.py` L38 `fetch_chart(ticker, rng='1mo')` (imported L15 from `scrapers.yahoo`) | replay from a **pinned snapshot** of the validation pull; the rebuild must NOT hit the network. A yfinance refresh becomes an explicit, dated snapshot bump that surfaces as a §4 diff, not a silent drift. |
| **Scrapers overwrite raw cache** | re-running any scraper clobbers `data/raw/<source>/` — destroys the replayable input | separate **immutable pinned raw snapshots** (the rebuild input) from the live scrape area; the rebuild reads the pinned snapshot. A new scrape is a deliberate, versioned snapshot, diffed via §4. (Directly fixes the ROLEXRINGS mechanism: a yfinance refresh silently changing ratios/dates.) |
| **Date/year timebombs** (TD-1) | `01_build_base` `hi=2026` fallback (breaks 2027), chittorgarh `YEARS`, `'2026-27'` FY, `page<=300` | replace hardcoded year/page constants with derived/config values so the SAME inputs produce the SAME output across calendar years — a determinism prerequisite, flagged to the build phase. |
| **Silent try/except drops** (TD-7) | naked `except` in pipeline steps | surfaced via the §4.2 silent-drop diff class as the minimum; ideally the bare excepts are narrowed in the build phase so drops are explicit + logged. |

### 4.4 Testability

The campaign is the test. The acceptance criterion is concrete and falsifiable: after resolution, a fresh
`pipeline-from-pinned-raw + overlay` reproduces the trusted substrate **bit-for-bit on a second run** (proves
idempotency + determinism), and the ROLEXRINGS/NPST/CANTABIL returns are corrected (proves the D-1 join fix
landed), and the O-3 cells stay nulled across two rebuilds (proves the e6053e7 clobber class is gone).

---

## 5. FEATURES ↔ DATA reverse-map (is each quirk a DATA bug fixable at this layer?)

For every built artifact (predictor / analog engine / scorecard / backtester / findings / weights), the
question: is a known quirk actually a DATA bug fixable by a §1 cleaning rule + §2 overlay — or a genuine
modelling limitation that NO data fix removes? Grounded in `rules/index.md` + task_16/17/19.

### 5.1 The table

| feature / consumer | known quirk | DATA root cause | fixable at data layer? | fix |
|---|---|---|---|---|
| **predictor analog distance** (`analogs.py` Gower features: pe_ratio, roe, d/e, margin) | analogs distorted by corrupt fundamentals | O-9 neg-equity ROE/DE (Indiqube 1400% / −409.5), O-10 Ujjivan margin 983%, negative P/E (46) | **YES — data bug** | CR-SF-DENOM, CR-SALES-IMPLAUS, CR-PE-NEG quarantine/null BEFORE analogs reads them |
| **data-informed weights** (`weights.py` query features → rank-IC) | learned weights polluted by the same corrupt fundamentals | same O-9/O-10 cells feed the point-in-time rank-IC | **YES — data bug** | same rules; corrupt rows quarantined out of the weight-derivation panel |
| **quality scorecard component** (`scorecard.py` profitable/ROE/D-E/margin) | `np.clip` MASKS corruption (Indiqube D/E −409.5 → debt-score 100) | O-9 neg-equity reaches `scorecard.quality()` un-quarantined | **YES — data bug** | CR-SF-DENOM quarantines UPSTREAM of the clip (the clip must not be the safety net) |
| **wipeout-safety (IN-SCORE)** + `tiny_sales_lt25cr` validated flag | false-fires on a multibagger bank (Ujjivan) | O-10 implausible `pre_ipo_net_sales=18` (raw screener value, NBFC sales-definition mismatch) | **YES — data bug** | CR-SALES-IMPLAUS quarantine + overlay the DRHP ~₹1,800cr value; re-derive the flag |
| **`pre_ipo_net_sales` IC-0.20 at-IPO predictor** | poisoned feature value | same O-10 implausible sales | **YES — data bug** | same; corrected via overlay |
| **D-3 market-cap leak / migration_predictor circular IC 0.564** | predictor fed CURRENT (post-outcome) cap → look-ahead | `market_cap_cr` is current cap with NO as-of attribute; same as-of class poisons SME→MB migration | **YES — data bug (the named as-of class)** | CR-MCAP-ASOF: split into `*_at_ipo_cr` (source: Chittorgarh KPI / issue_price×post-issue-shares) vs `*_current_cr`; bind predictors to `*_at_ipo_cr` only |
| **subscription-as-feature** (n2/n3 + low-sub veto candidate) | breaks on the 0-bug | O-2 124 `sub_total_x=0` masked-missing + the `_src` laundering (stamped `sharescart`) | **YES — data bug** | CR-SUB-ZERO null + (b); STOP the enrich step stamping `_src` on a placeholder (task_19 #4, multi-site policy) |
| **n14 `declining_pat` flag** | false-fires (no `p1>0` guard, unlike `declining_revenue`) | per-year PAT zeros (pat_yr1 184) interpreted as a real value | **PARTLY data** | CR (per-year pat zero → (b)) fixes the DATA half; the missing `p1>0` guard is a FEATURE-code bug handed to the feature owner (task_12) — NOT fixable purely at the data layer |
| **corp-action fake returns** (ROLEXRINGS +15,272%, NPST +16,127%) | absurd multibaggers in every return-based finding/backtest | D-1 over-count: 3× duplicate split events surviving `(ex_date,ratio)` dedup; pre/post-split ISIN drift | **YES — data bug** | CR-CORP-OVERCOUNT (price-gap arbiter, `DELETE-EVENT` overlay) + Cluster-2 join fix + §4 campaign |
| **EPS-CAGR / EPS-trajectory** (NOT currently a feature; `eps_yr*` unread) | share-base discontinuity would corrupt it IF built | O-5 EPS on changing share base (51/57 rows; NOT a ÷1000 parse bug) | **PARTLY** — null-and-flag (CR-EPS-SHAREBASE, A2) is a data fix; a *recompute* on constant share base (A1) is BLOCKED on the missing total-shares-outstanding data (same gap as O-12) → not fully fixable at this layer today |
| **liquidity / quality score components** | weight 0 (no signal) | NOT a data bug — IC genuinely flips sign (rules/index.md) | **NO — genuine modelling/empirical result** | none; leave display-only |
| **take-profit / stop-loss never beats hold** | a strategy "limitation" | NOT a data bug — the right tail genuinely carries returns | **NO — genuine empirical truth** | none |
| **strat-combined-score 1y weak / 3y strong** | horizon-specific | NOT a data bug — real OOS result | **NO — genuine** | applicability gate (§3) restricts to 3y; nothing to clean |

### 5.2 The verdict

The corruption that leaks into **scored** features (analog distance, learned weights, in-score
wipeout-safety + quality, the IC-0.20 sales predictor, D-3 mcap leak, corp-action fake returns) is
**overwhelmingly DATA bugs** fixable here via §1 rules + §2 overlay + §4 campaign — task_16's central
correction was that this is "scored-feature corruption, NOT display-only." The non-data residue is small and
honest: liquidity/quality-have-no-signal, no-exit-rule-beats-hold, horizon-specificity — these are genuine
empirical results that NO data fix changes (and must not be "fixed" away). Two items are PARTLY data: the
`declining_pat` missing guard (feature-code half goes to the feature owner) and EPS-recompute (blocked on a
data gap — total shares outstanding — shared with O-12).

---

## OPEN OWNER-QUESTIONS

1. **Overlay consolidation.** Approve migrating the three embedded hand-fix catalogs (corp_actions
   `manual_thinktank_audit`+`verification` 39 rows; 88-audit Cat-1 21 splits; `drhp_recovered` 16) INTO a
   single unified overlay ledger (§2.2) — so there is ONE source of truth — vs keeping them in their current
   separate files with a shared reader? (Recommend consolidate; north-star single-source.)

2. **Overlay `op` vocabulary.** Confirm the overlay needs `DELETE-EVENT` / `ADD-EVENT` (not just `SET`) so a
   FAKE corp-action can be removed and a MISSING one added — `manual_overrides.csv`'s SET-only shape cannot
   express the ROLEXRINGS triple-split removal.

3. **Conflict policy when the pipeline value moves.** When `v_now ∉ {old,new}` (a yfinance refresh changed a
   ratio): does the overlay's `new_value` still win automatically (with a reconciliation flag), or HOLD the
   row in dirty-review until the owner re-confirms? (Charter leans "correction wins + flag"; confirm.)

4. **Reconciliation campaign timing & freeze.** The campaign STOPS other dev while it runs (charter §B).
   Confirm we run it as the FIRST build action after design approval, and accept the live substrate keeps the
   3 fake multibaggers (ROLEXRINGS/NPST/CANTABIL) until it completes.

5. **Cleaning-rule default severity.** When a validity rule fails, default to QUARANTINE the whole row
   (`quality=dirty`) or FLAG-ONLY (null the offending cell, keep the row)? This trades aggressiveness vs
   coverage; it likely differs per class (recommend: cell-local damage → FLAG-ONLY; derived-feature
   contamination → QUARANTINE — as in §1.2), but the owner should set the DEFAULT for ambiguous cases.

6. **Confidence threshold for auto-apply.** Auto-apply HIGH + MED rules and only gate LOW behind owner-Q
   (the §1.1 default), or auto-apply HIGH only and route ALL MED to the dirty-review worklist for spot-check
   first? (Affects how much lands automatically vs needs a human pass in the campaign.)

7. **Applicability register home.** `rules/index.md` is already the de-facto applicability register (every
   boom-only/MB-only/separate marker). Formalize the §3 gate AS structured fields in `rules/index.md`
   entries, or as a separate machine-readable applicability table that `rules/index.md` links to? (Recommend
   in-place fields — single source of truth.)

8. **As-of split adoption (D-3).** Confirm `market_cap_cr` is split into `*_at_ipo_cr` (predictor-bound) +
   `*_current_cr` (display-only), and predictors/migration analysis re-bound to `*_at_ipo_cr` — this is the
   data fix for the D-3 leak AND the circular migration IC 0.564 (one as-of class, two instances). Source for
   `*_at_ipo_cr` for the boom cohort: Chittorgarh KPI vs `issue_price × post-issue shares` (the latter blocked
   on the same missing total-shares data as EPS-recompute) — which? (Cross-ref Cluster 1/task_17.)

9. **EPS recompute (A1 vs A2).** Will per-year EPS ever feed a feature? If NO → null-and-flag (A2,
   CR-EPS-SHAREBASE) suffices and stays a pure data fix. If YES → recompute on a constant share base (A1) —
   but A1 is BLOCKED on total-shares-outstanding data not in the substrate. (Cross-ref task_16.)

10. **Cross-field predicate support.** Confirm Cluster 1's column registry will support multi-column validity
    predicates (needed for O-3 tranche-vs-total 32+218 rows, CR-EPS-SIGN, CR-SF-DENOM, CR-DATE-ORDER) — not
    just per-cell predicates. Without it, those classes fall through (task_19 §3b-ii).

---

### CROSS-CLUSTER DEPENDENCIES (so this section isn't read in isolation)
- **Cluster 1** must deliver: the `quality` column, the compact 3-state(+d) provenance carrier (covering ALL
  columns, not just the 2 that have `_src` today — task_19 §3b-i), and a column registry whose
  validity-predicate facility accepts CROSS-FIELD predicates (§1.4 / §3 / OQ-10).
- **Cluster 2** must deliver: the resolved symbol∪ISIN window join + pre/post-split ISIN-drift handling that
  CR-CORP-OVERCOUNT and the §4 campaign depend on (ROLEXRINGS INE645S01016↔INE645S01024).
- **task_05b** must deliver: the `instrument_type` dimension the §3 applicability gate uses to keep
  equity-only cleaning rules + findings off REIT/InvIT/NCD rows.

> **NOT FINAL — proposal for owner approval.** No code, no data changes. Counts are the Group-B tasks'
> reproduced figures; re-verify in the owning task before relying. Review-loop (multi-lens, stop-rule) for
> THIS synthesis is owed under STAGE-5 of the macro sequence and is not yet run.
