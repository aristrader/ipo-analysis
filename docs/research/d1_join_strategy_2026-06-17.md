# D-1 Join Strategy — corp-actions ↔ prices ↔ substrate (2026-06-17)

**Role:** READ-ONLY investigation. No code/data edits, no pipeline execution. Every number below was
computed directly against the working-tree files (`corp_actions_merged.csv`, `data/master/*.csv`,
`data/prices/`). This document gates the D-1 plan revision: it determines the *correct, most robust*
join key, given that **both candidate keys are imperfect** (ISIN changes on a face-value split; symbols
get renamed AND reused by different companies).

**Bottom line (the recommendation, up front):**
> Join corp actions to the substrate by **NSE symbol ∪ substrate-ISIN, but SCOPED by the stock's
> trading-date window** — i.e. an action attaches only if its `ex_date` falls inside the substrate
> row's price coverage `[first_trade, last_trade]`. Out-of-window matches are **dropped from
> adjustment and flagged**, never silently applied. This is option **(d)** below. It keeps the symbol
> join (which is load-bearing — 301 substrate rows reach their actions ONLY via symbol) while
> neutralising the one dangerous failure mode it has: symbol reuse / wrong-era attachment, which the
> date guard catches on **44 corp-action rows today (37 of them suspect reverse-splits)**.

---

## 1. The current join chain (exact, with file:line + key per hop)

### Hop A — corp-action file keying
`data/reference/corp_actions_merged.csv` has columns: `isin, symbol, action_type, raw_subject,
ratio_factor, ex_date, source`. It is **keyed by BOTH `isin` and `symbol`**, but the ISIN column is
often empty:

| | count |
|---|---|
| total rows | 1897 |
| rows with non-empty `isin` | 1543 |
| rows with empty `isin` | 354 (**all** `source=yfinance`) |
| rows with non-empty `symbol` | 1897 (**every** row has a symbol) |
| distinct ISINs | 1109 · distinct symbols | 1222 |

By source: `nse_corp_actions:equities` 1341, `yfinance` 354, `nse_corp_actions:sme` 163,
`manual_thinktank_audit` 34, `verification_2026-05-31` 5.

How it got built:
- `pipeline/03k_reconcile_corporate_actions.py` cross-validates NSE (authoritative, ISIN-carrying)
  against Yahoo (symbol-only). Yahoo events not found in NSE → `corp_actions_yahoo_only.csv`.
- `pipeline/03l_merge_corporate_actions.py:43-53` converts every Yahoo-only row to NSE shape with
  **`'isin': ''`** (line 47 — *"Yahoo doesn't provide ISINs"*) and `action_type='split'`, then
  `pd.concat`s (line 58). **This is the structural origin of the 354 empty-ISIN, symbol-only rows.**

### Hop B — apply in step 07 (the actual price join)
`pipeline/07_returns_summary.py`:
- `load_corp_actions()` (**lines 91-111**) builds **two** dicts: `by_isin[isin]` and
  `by_symbol[SYMBOL.upper()]`. Its docstring states the rationale explicitly: *"A face-value split
  often changes the ISIN, so the corp-action ISIN no longer matches the current/universe ISIN;
  matching by NSE symbol recovers these. Both lookups are returned so the caller can take the union."*
- `actions_for(isin, nse_symbol, by_isin, by_symbol)` (**lines 114-127**) returns the **UNION**
  `by_isin[isin] ∪ by_symbol[symbol]`, deduped by `(ex_date, ratio_factor)`.
- `load_prices(isin, actions)` (**206-235**) reads `data/prices/<isin>.csv` and divides every
  pre-`ex_date` OHLC by the product of `ratio_factor`s (lines 225-234). `adj_factor_after(actions, dt)`
  (**239-246**) is the same product, used to put `issue_price` and delisting `last_price` on the
  current scale. **There is no date-window guard: any action in the union adjusts the series regardless
  of whether its `ex_date` lies inside the stock's trading life.**
- `main()` calls `actions_for(isin, mrow.get('nse_symbol'), ...)` (**line 630**) for every substrate
  ISIN that has a price file.

**WHY the symbol key exists:** a face-value split mints a new ISIN. The corp-action row sits under the
OLD ISIN (or, for yfinance, under no ISIN). The substrate + price file use the NEW ISIN. Without the
symbol bridge, the action would never reach the series. This matches the project's non-negotiable rule
(CLAUDE.md: *"corporate actions match by SYMBOL — a face-value split changes the ISIN"*).

### Hop C — substrate / price-file keying
- Substrate masters (`data/master/{mainboard,sme,longterm_mainboard,longterm_sme}.csv` → assembled
  into `ipo_analysis.csv`) are keyed by **substrate ISIN** (the NEW, post-split ISIN). 2384 ISINs.
- Price files are `data/prices/<ISIN>.csv` — **filename IS the key**; the file content has no ISIN
  column (`date,open,high,low,close,volume`). 2383 files; **2382 of the 2384 substrate ISINs have a
  price file** (1 substrate ISIN has none). So **price-file ISIN == substrate ISIN** by construction.
- `09_assemble.py:86-89` defines `has_action = (isin in action_isins) or (u_sym in action_symbols)` —
  i.e. it *already* uses the symbol-OR-ISIN union to know whether a row has any corp action (used to
  suppress a false-positive cross-check). This is the right template for the corp-action set.

### Full chain, one line per hop
```
corp_action row        key = ISIN (often empty) AND/OR SYMBOL          [03k/03l, ISIN blanked at 03l:47]
   ↓ (no reconcile to substrate ISIN happens; ISIN is left as-is or empty)
apply in 07            key = SYMBOL ∪ substrate-ISIN (actions_for)     [07:114-127, called 07:630]
   ↓                   (NO date-window scoping)
price series           key = substrate ISIN (filename)                 [data/prices/<ISIN>.csv]
   ↓
substrate row          key = substrate ISIN                            [ipo_analysis.csv]
```

---

## 2. Quantified failure modes of EACH key

### Key = ISIN
**Failure mode:** a face-value split changes the ISIN, so the corp-action ISIN ≠ substrate/price ISIN.

| metric | value |
|---|---|
| distinct corp-action ISINs | 1109 |
| corp-action ISINs present in substrate (ISIN join works) | **148** |
| corp-action ISINs NOT in substrate | 961 |
| …of those, how many have their OWN price file | **0** |
| substrate rows whose actions reach via ISIN ONLY | **26** |

**Blast radius of an ISIN-only strategy: catastrophic.** ZERO non-substrate corp-action ISINs have a
price file — so an ISIN-only join silently drops every action that underwent a face-value split. Only
**26** substrate rows would still get adjusted via ISIN-only. This is the bug the D-1 re-review already
flagged: keying the detector/reconcile on the corp-action ISIN reads a partial/empty factor for the
282 dual-ISIN stocks (e.g. ROLEXRINGS: `applied_cumulative_factor("INE645S01016")=10`,
`applied_cumulative_factor("INE645S01024")=1`, but the real applied product is **1000** — obtainable
only via the symbol union). **ISIN-only is not viable.**

*(Note on "the 274": the re-review's "274 real ISIN changes / 282 symbols / 434 rows" reproduces here
as 434 corp-action ROWS whose non-empty ISIN ≠ substrate ISIN for a symbol that resolves to the
substrate, across 340 distinct corp ISINs / 282 distinct symbols. The 274 vs 340 gap is the
numeric-BSE-code "ISINs" being filtered; either way the conclusion is identical — none have a price
file.)*

### Key = symbol
**Failure mode 1 — symbol RENAME (a company changes ticker over time).** Detectability is limited: the
substrate carries exactly ONE `nse_symbol` per ISIN (its current/listing symbol). 699 of 2384
substrate ISINs carry **no** `nse_symbol` at all (older/SME rows). There is no NSE symbol-change ledger
in the repo, so a *historical* rename is largely **unknowable from on-tree data** — the corp-action row
under the old symbol simply won't match the substrate's current symbol. This is a *miss* (action
dropped), not a *mis-attachment*, so it is the less dangerous direction. Quantifiable proxy: of the 502
symbol-added actions, 44 fall outside the trading window (see below) — some of those are renames, some
are reuse; the data can't cleanly separate the two.

**Failure mode 2 — symbol COLLISION / REUSE (the dangerous one).** A symbol is freed when a company
delists/renames, then NSE re-assigns it to a *different* company. A naive symbol join then attaches the
OLD company's corporate action to the NEW company's price series (or vice-versa).

How load-bearing the symbol key is (substrate rows WITH a price file that receive any action):

| reach path | count |
|---|---|
| via ISIN only | 26 |
| via **SYMBOL only** (no ISIN match — fully symbol-dependent) | **301** |
| via both | 122 (symbol adds extra events on 13 of them) |

→ The symbol join carries **301 of 449** action-receiving rows. You cannot drop it.

Collision census (alphabetic ISINs only, ignoring numeric BSE-code "symbols"):
- Symbols mapping to >1 substrate ISIN *within* the substrate: **0** (substrate symbols are unique).
- Symbols mapping to >1 distinct real ISIN across corp+substrate that span >1 issuer family: **1**
  alphabetic symbol — `MANUAL` — which is a **placeholder, not a real symbol**: it is the literal
  `symbol` value on the 34 `manual_thinktank_audit` rows (those rows carry real ISINs, all 20 in the
  substrate, so they reach prices via ISIN; `MANUAL` matches no substrate symbol → harmless).
- The real, dangerous collisions don't show up in a pure ISIN-set census because the dangerous rows are
  the **354 yfinance empty-ISIN rows** — a reused symbol with NO ISIN to disambiguate it. These are
  invisible to "count ISINs per symbol" and only surface via the **date-window test** below.

**Example — KAUSHALYA (verified, the re-review's starting point):**
- `corp_actions_merged` has one `KAUSHALYA` row: `split, ratio_factor=0.01, ex_date=2024-01-12,
  source=yfinance, isin=(empty)`.
- Substrate keys symbol `KAUSHALYA` → **`INE234I01028` "Kaushalya Infrastructure Development Corp."**
  (listed 2007-12-14, trades 2007→2026 per its price file).
- A *different* company — **`INE0Q2V01012` "Kaushalya Logistics" (KLL Logistics)** — listed
  2024-01-08, symbol `KLL`, has its own price file (586 rows, 2024→2026).
- `actions_for("INE234I01028", "KAUSHALYA")` returns `[(2024-01-12, 0.01)]` via the symbol join — i.e.
  a **0.01 reverse split** (suspect) gets attached to the OLD infra company, whose 2007 history would
  be divided by 0.01 ⇒ multiplied 100×. The substrate already shows `INE234I01028` gapping ~100× near
  2024-01-12, so the symbol join *does* fire here. Whether the action truly belongs to the infra co or
  is a mislabeled artifact, the point stands: a symbol-only key applies a 2024 reverse-split to a
  2007-listed company with no ISIN check possible.

**Failure mode 2 — quantified blast radius (the decisive number):** of the **502 symbol-added actions**
(across 314 substrate rows) that are NOT already present under the row's own ISIN:
- **458** have `ex_date` INSIDE the stock's trading window `[first_trade, last_trade]` (legitimate).
- **44** have `ex_date` OUTSIDE the trading window — these are wrong-era / reused-symbol attachments.
  - by source: **37 yfinance**, 3 nse:equities, 4 nse:sme.
  - **25 of the 44 carry `ratio_factor < 1`** (reverse-splits / suspect tiny ratios) — exactly the
    kind that produce the +15,000% over-adjustment artifacts D-1 is fixing.

Concrete out-of-window examples (the wrong-era attachments a date guard catches):
| substrate ISIN | symbol | company | corp ex_date | rf | trading window |
|---|---|---|---|---|---|
| INE619A01035 | PATANJALI | Patanjali Foods | 2019-11-14 / 2007-10-29 | 0.01 / 5.0 | 2020-01-27 → 2026 |
| INE866K01023 | WAAREEINDO | Indosolar (old) | 2022-06-27 | 0.01 | 2025-06-19 → 2026 |
| INE542F01020 | SWANDEF | Pipavav Shipyard (old) | 2023-* | 0.0036 | 2025-01-20 → 2026 |
| INE268L01046 | SHEKHAWATI | Shekhawati Poly-Yarn | 2013-04-10 | 10.0 | 2024-09-10 → 2026 |
| INE955I01044 | SEJALLTD | Sejal Arch. Glass | 2010-2011 | 10.0 / 0.1 | 2021-12-13 → 2026 |

All five are symbols reused by a new listing (or a re-listing under a new ISIN) where the old company's
NSE/yfinance history is keyed under the same symbol. Every one is correctly excluded by the date guard.

---

## 3. Summary table — key → failure mode → blast radius → example

| key | failure mode | quantified blast radius | example |
|---|---|---|---|
| **ISIN** | face-value split mints a new ISIN; corp ISIN ≠ substrate ISIN | 961/1109 corp ISINs not in substrate; **0** have a price file; only **26** substrate rows reach actions via ISIN-only | ROLEXRINGS: action under `INE645S01016`, substrate/price under `INE645S01024` |
| **symbol — rename** | company changes ticker; old-symbol action misses current symbol; 699 substrate rows have no symbol at all | a *miss* (drop), hard to count exactly; subset of the 44 out-of-window | historical renames; unknowable without an NSE symbol-change ledger |
| **symbol — reuse/collision** | freed symbol reassigned to a different company → wrong company's action applied | **44** of 502 symbol-added actions land OUTSIDE the trading window (37 yfinance, 25 with rf<1) | KAUSHALYA 0.01→old infra co; PATANJALI; WAAREEINDO; SWANDEF |
| **symbol — coverage** | symbol join is load-bearing | **301** substrate rows reach actions via SYMBOL ONLY; dropping it loses almost all adjustments | ROLEXRINGS, NPST, ADANIPOWER-class face-value splits |

---

## 4. Recommended strategy

### Options considered
- **(a) symbol-only** — loses the 148 ISIN-disambiguated cases and is fully exposed to the 44 reuse
  collisions. Rejected.
- **(b) ISIN-only** — drops every face-value-split action (0 of them have a price file under the corp
  ISIN); only 26 rows survive. Rejected — this is the bug the D-1 re-review already condemned.
- **(c) symbol ∪ substrate-ISIN (the current `actions_for`)** — correct coverage (327 rows reach via
  symbol/ISIN), but **no collision guard**: it applies all 44 wrong-era actions, including 25 suspect
  reverse-splits. This is *part* of the D-1 over-adjustment bug.
- **(d) symbol ∪ substrate-ISIN, SCOPED by ISIN-family and/or trading-date window** ← **RECOMMENDED.**
- **(e) canonical entity-mapping table (ISIN-family ↔ symbol ↔ substrate row)** — the cleanest
  long-term design, but it needs an authoritative ISIN-family/symbol-history source that the repo does
  not have (NETWORK = default-deny; no NSE symbol-change ledger on tree). **Keep as the eventual
  target; not buildable now without a new trusted source.** Option (d) is (e)'s behaviour approximated
  from data already on disk (the price coverage window IS the per-entity trading life).

### RECOMMENDED: option (d) — symbol ∪ ISIN union, gated by the trading-date window

For each substrate ISIN with a price file, build the candidate action set exactly as today
(`by_isin[isin] ∪ by_symbol[symbol]`, dedup by `(ex_date, rf)`), then **admit an action to the
adjustment only if BOTH guards pass; otherwise DROP it from adjustment and FLAG it** (flag-don't-guess):

1. **Date-window guard (primary, catches symbol reuse):** the action's `ex_date` must fall within the
   stock's price coverage `[first_trade, last_trade]` (a small slack of a few trading days before
   `first_trade` is acceptable for a split effective right at listing). An `ex_date` before listing or
   after the last trade ⇒ it belongs to a *different era / different company under the same symbol* ⇒
   **drop + flag** `corp_action_out_of_window`. This guard alone removes the 44 known bad attachments
   (37 yfinance, 25 reverse-splits) while keeping all 458 legitimate symbol matches.
2. **ISIN-family preference (secondary, disambiguation + confidence):** when a candidate action carries
   a non-empty ISIN, prefer the one whose issuer family (`INE` + 5-char issuer code) matches the
   substrate ISIN's family; an empty-ISIN (yfinance) action is admitted only on the strength of the
   date-window guard. Use the family match to set a `corp_action_match=isin_family|symbol_in_window`
   confidence stamp rather than to *reject* (since the legitimate face-value-split case deliberately has
   a *different* security suffix but usually the *same* issuer code).

When the union cannot be disambiguated — e.g. two candidate actions with the SAME `ex_date` inside the
window but contradictory ratios, or a symbol that, after the date guard, still maps to ≥2 issuer
families with in-window events — **do not pick one. Null the listing/return metrics for that row and
raise it into the unresolved/flagged set** (mirroring the project's existing flag-don't-guess discipline
and `09`'s `has_action` set). This is the guard that fires when the join genuinely can't decide.

**Why (d) and not just (c)+a tripwire:** the D-1 envelope tripwire (Task 5b) catches the *symptom*
(trough ≤ endpoint ≤ peak violated) AFTER a bad adjustment has already distorted the series. The
date-window guard prevents the *cause* — it stops the wrong-era action from ever entering `load_prices`.
Both should exist (defence in depth), but the date guard is what makes the symbol join *safe*, which is
the question this investigation was asked to answer.

---

## 5. Exactly which D-1 plan tasks must change to use this

References below are to the revised plan/spec re-reviewed in
`docs/research/d1_plan_rereview_2026-06-17.md` (R1/R2 are the open blockers there).

1. **Over-adjustment detector test (plan Task 1 — the red baseline).**
   - Key the detector helpers on the **substrate ISIN ∪ symbol union** (the `actions_for` set), NOT the
     corp-action ISIN — already mandated by R1/R2. **Additionally** make the helper apply the
     **date-window guard**: `applied_effective` must be computed over only the in-window candidate
     actions, so the detector measures what production *should* apply. Re-key ROLEXRINGS to substrate
     `INE645S01024` + symbol `ROLEXRINGS` (its three events are all in-window → product 1000 → flagged
     for the right reason). KAUSHALYA's 0.01 is in-window for `INE234I01028`, so it is admitted (the
     guardrail's "reverse-clean must-pass" still holds) — but PATANJALI/WAAREEINDO-class events are now
     correctly EXCLUDED before the magnitude test.

2. **Task 4 — the reconcile/rebuild grouping.**
   - Group candidate events by **substrate ISIN via the symbol∪ISIN union**, then **filter to the
     trading-date window** before computing the cumulative factor. The "group per corp-action ISIN"
     wording (R2) must become "group per substrate ISIN over in-window union events." This is where the
     44 out-of-window actions get dropped+flagged rather than reconciled into a leak.

3. **Task 8 — the targeted patch + anti-join.**
   - Define the **corp-action stock set** as substrate ISINs whose symbol OR ISIN appears in
     `corp_actions_merged` **and that have ≥1 in-window event** (mirror `09:86-89`'s `has_action`,
     extended with the window filter). The full byte-identity anti-join then correctly treats the 44
     out-of-window-only rows as *non-adjusted* (they should match the snapshot once the leak is fixed).

4. **Step 07 itself (`actions_for` / `load_prices`).** The window guard is most robustly implemented
   right where the union is consumed: `actions_for` (07:114-127) already has the symbol and ISIN; pass
   the price series' `[first_trade, last_trade]` (available in `load_prices`/`compute`) and filter the
   returned list, emitting a `corp_action_out_of_window` flag onto the row. This makes EVERY downstream
   consumer (returns, MFE/MAE, listing metrics) automatically safe, not just the audited rows.

5. **Override loader / unresolved set (plan Task 3/Task 6).** Same union+window keying; an override is
   honored only when the in-window union is absent/ambiguous (consistent with R1/R2's fix).

---

## 6. Verification notes / what is unknowable

- All counts re-derived live from `corp_actions_merged.csv` (1897 rows), `data/master/{mainboard,sme,
  longterm_*}.csv` (2384 substrate ISINs, 1685 distinct nonempty symbols), and `data/prices/` (2383
  files). Trading windows read per-ISIN from the price files (min/max `date`, sorted in-memory — the
  on-disk CSVs are NOT date-sorted, so any analysis must sort, as `07:222` does).
- **Unknowable from on-tree data:** historical NSE symbol RENAMES (no symbol-change ledger in the repo;
  substrate carries only the current symbol; 699 substrate rows carry no symbol at all). The
  date-window guard turns a *rename collision* into a safe *drop+flag* even though we can't positively
  identify it as a rename — which is the right failure direction.
- **Caveat on the 44-count:** it measures symbol-added actions outside `[first_trade, last_trade]`.
  Genuine splits effective exactly at/just-before listing could in principle sit a day or two before
  `first_trade`; the recommended guard therefore allows a few-trading-day slack before `first_trade` to
  avoid dropping a legitimate listing-day split. None of the 44 examples are within such slack (they are
  years off), so the slack does not reintroduce any of them.
- No code or data was modified; no pipeline step was run.
