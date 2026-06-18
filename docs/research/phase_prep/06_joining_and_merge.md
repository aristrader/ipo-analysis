# 06 — Joining, data-copy/merge, and corp-action improvements (synthesis + proposals)

This is the "how do we improve copy / merge / corp-action / joining" thought-process the owner asked for,
grounded in tonight's measurements. The design docs (`FOUNDATION_ARCHITECTURE.md` §8–9) already specify the
target mechanics; below = what the DATA proved, and the concrete improvements that follow.

## A. JOINING — ISIN-only is right; the gaps are at the non-ISIN bridges
**Confirmed working:** ISIN-only auto-join + names-only-flag would have swept out the Bajaj Corp wrong-entity
cap (₹292,355cr = a different Bajaj). The architecture's `_src_entity_id` / `_src_entity_name` stamping per
join is the correct mechanism — **implement it** so the verify-time detector can assert the source's entity
name matches the canonical stem.

**The real risk is the non-ISIN sources** (screener, ipowatch, investorgain, sharescart) — they carry no ISIN,
so they join via a name/symbol→ISIN *resolution pre-step*. Improvements:
1. **Resolution must be point-in-time + listing-date-confirmed** (architecture §8 bridge rule): `(symbol|name-slug)
   → exchange-list ISIN → confirm listing_date within N days → ISIN`. On ambiguity/failure → NULL + `error_out`
   (retryable), never a name-merge. The wrong-entity joins all originate here.
2. **The identity-history golden file is the keystone** — without it, face-value-split ISIN renames (MCX
   INE745G01043, ROLEXRINGS old→new) break symbol/ISIN joins. Seed it from: (a) every corp-action that renamed
   an ISIN, (b) the manual_thinktank_audit symbols, (c) tonight's 33-row wrong-entity worklist (doc 05).
3. **Corp-actions are the ONE carved-out SYMBOL-join** (a face-value split changes the ISIN) — keep it governed
   by the identity golden + a pre-listing-date filter, never a blind symbol match (the symbol-only-yf dups —
   ENGINERSIN, OPTOCIRCUITS, GICL — are corroboration-only).

## B. DATA-COPY / MERGE — the build→swap must MERGE, not REPLACE (tonight's biggest lesson)
The "build-beside-old → swap" plan is sound, but tonight showed a **wholesale replace would silently lose data**.
Three concrete copy/merge rules the swap step must enforce:

1. **Preserve delisted price files the re-fetch can't regenerate.** The fresh bhavcopy produced 2,373 price
   files vs 2,383 frozen — **12 delisted names dropped** (off-exchange, no current bhavcopy). The swap must be
   `union(frozen_prices, build_prices)` keeping the frozen file where the re-fetch has none — else 12 delisted
   terminal returns vanish (survivorship damage). Generalize: **price layer = append/union, never replace.**
2. **Corp-actions = append-only UNION across fetches.** The NSE endpoint returns a rolling window; the fresh
   fetch **dropped 25 real recent (2026) events** that frozen had (MCX, LICI, IRB, METROPOLIS, …) AND frozen
   lacked 2 old ones the fresh fetch found. Neither fetch is complete. **Truth = union of all fetches + golden.**
   This is the single highest-impact merge fix (doc 03).
3. **`delisting.csv` changed shape → consumers must adapt.** It's now a full *status table* (2,384 rows: active
   2,100 / delisted 139 / unknown 75 / suspended 70), not a delisted-only list. Step 07 + the Phase-5 corp-action
   consumer must **filter on `status`** (only delisted/suspended/compulsory drive the −100% A1 rule). A naive
   reader would treat 2,100 active names as delisted. (Phase-9 repoint guard item.)

**General merge principle to adopt:** every source layer is a *partial, time-varying view*; the substrate is the
**monotonic union** of all observations + golden + overlay. Re-fetch ADDS/UPDATES; it never deletes silently. A
deletion (a value that disappears upstream) is itself an event to record (the D15 change-detection), not a drop.

## C. CORP-ACTION engine — concrete improved recipe (supersedes the loose spec leanings)
1. **Union-merge** all corp-action fetches + the 5 `verification_2026-05-31` golden rows (append-only). [B.2]
2. **Collapse same-event double-reports:** key = `(symbol, round(ratio_factor,2))`, require `≥2 distinct sources`,
   ex-dates `≤45d apart` (calibrated: max real cluster span = 43d; 30d misses VISHWARAJ). Collapse → 1 event.
   - Do NOT key on symbol alone (10–17 symbols have a *different-ratio* real event within 30–60d).
   - Numeric-tolerance ratio compare (USASEEDS 1.428571 vs 1.4285714 are equal) — already partly present at 03k.
3. **Golden override first** (verified ratio/date wins): seed with tonight's verified rows —
   `ROLEXRINGS split 10.0 ex-2025-10-17 (ONE event, no bonus — resolves the 19.96× as pure double-count)`,
   `MCX 5.0 ex-2026-01-02 (new ISIN INE745G01043)`, `LICI bonus 2.0 ex-2026-05-29`, NPST/CANTABIL (verify date).
4. **Fallback order:** golden catalog → price-gap arbiter (source-agnostic) → source-reconcile dedup → flag.
5. **Re-enable the 09 cross-source listing-price tripwire** for corp-action stocks (it's disabled at 09:88-89).
6. **Preserve yfinance action_type** (03l hardcodes 'split' for all 354 yahoo rows — a real bonus/dividend is
   mislabeled). Corroboration-only; never adjust on yf alone.

## D. CORRECTIONS / OVERLAY — improvements
- **Migrate ALL scattered hand-fixes into one overlay ledger** (manual_overrides 3 + manual_thinktank_audit/
  verification corrections + drhp_recovered 16 + the orphaned Indiabulls Power fix). Each carries `old_value` +
  fetch-time for conflict detection.
- **Conflict policy (already specified):** still-broken → apply; now-matches → retire; moved-to-third → HOLD.
- **Baseline caveat (R5):** migrated hand-fixes lack a recorded `old_value` → conflict-detection is INERT for
  them until reconstructed. Reconstruct from the frozen substrate (it IS the pre-fix baseline for many).
- **Indiabulls Power (INE399K01017) bonus ratio is still unknown** — a Phase-7 prerequisite; must be sourced
  (RHP/exchange) before its orphaned fix migrates. (Could not resolve from local data tonight.)

## E. Quick-win checklist (low-risk, high-value, ready for the build)
- [ ] Swap = union/preserve for prices (keep the 12 delisted) — **prevents silent data loss**.
- [ ] Corp-actions union-merge + re-inject 5 golden rows — **recovers 25 dropped real events**.
- [ ] Collapse rule `(symbol, ratio, ≥2 src, ≤45d)`.
- [ ] `delisting.csv` consumers filter on `status`.
- [ ] Relabel Standard Chartered → `idr` (doc 04).
- [ ] Min-investment arithmetic recovery (clean, 18 rows) — apply; subscription recovery (88) — gate at 78% (doc 01).
- [ ] T1.2 predicate = `Σparts ≤ total·(1+tol)`, not equality (doc 01).
- [ ] Seed golden corp-action catalog with the 5 web-verified rows.
