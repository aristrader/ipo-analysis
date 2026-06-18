# 09 — T1.1 corrected review + rule set + fix list (owner-driven, 2026-06-18)

Outcome of the owner's review of the provenance engine. The owner's two principles drove this:
(1) a single-source plausibility check is necessary but NOT sufficient — it can't catch plausible-wrong values,
so the real defense is **2-source matching + per-field study**; (2) the gate should only apply rules it can
stand behind with one source, and "when in doubt → Missing_data", never a hopeful `present`.

## A. The withdrawn-IPO question — answered
- **In the SOURCE sites (chittorgarh):** yes, withdrawn/failed IPOs exist and are tracked there.
- **In OUR substrate: NONE.** The spine is built from exchange-LISTED, ISIN-keyed names, so a withdrawn IPO
  (no listing, no ISIN-on-exchange) never enters. Evidence:
  - 17 rows show `0 < sub_total_x < 1` but **all listed with price history** — they are REAL listed companies,
    a MIX of (a) genuinely weak-but-listed (Star Health 0.79, Yes Bank FPO 0.93 — large issues carried by
    QIB/anchor meeting their minimums) and (b) **data errors** (AWL/Adani Wilmar `0.26` — really ~17×; a
    wrong day-1 snapshot). So `<1.0` is NOT a withdrawn signal and NOT a clean validity bound.
  - 16 no-price rows = 2 just-listed-2026 (Merritronix, SMR Jewels; price files pending) + 14 old DATA GAPS
    for names that definitely listed (Tech Mahindra, Sun TV, GMR Infra). None are withdrawals.
- **How to identify a withdrawn IPO — CORRECTED (owner caught a flaw).** "Absent from the exchange list" is
  **NOT definitive** and must NOT be done by name-matching — it causes false negatives (a real listed IPO whose
  name/key doesn't match the list would be wrongly tagged "withdrawn"). The join key is **ISIN**, never name.
  Use **POSITIVE evidence of withdrawal**, not absence:
  1. A source `withdrawn`/`failed`/`refunded` status (chittorgarh carries this) — the primary signal.
  2. No `listing_date` AND no price history AND no ISIN-on-exchange — corroborating, not sufficient alone.
  3. **Flag-don't-drop:** an unmatched/ambiguous row is a REVIEW item, never a silent "withdrawn" classification.
  (Proof the name-risk is real: my own substrate↔chittorgarh join below MISSED Adani Wilmar because the
  substrate calls it "AWL Agri Business" and chittorgarh "Adani Wilmar" — a name join silently drops renamed
  companies. ISIN `INE699H01024` joins them correctly.)

## A2. ⚠⚠ SUBSCRIPTION early-snapshot bug — bigger than the zeros (owner: "pick the latest row")
The owner's instinct was right: the sites carry **day-by-day subscription tables**, and we must take the
**FINAL row (bidding-close)**. We are NOT doing that consistently:
- **Adani Wilmar:** substrate `sub_total_x = 0.26` (source = `nse`, an early Day-1/2 snapshot — Day-2 QIB was
  0.39, matching the <1 fingerprint). **True final = 17.37×** (web-confirmed: QIB 5.73 / NII 56.3 / retail 3.92,
  Jan-31 close). **Chittorgarh already had 13.44** for the same IPO — i.e. the source-priority pick chose the
  BAD nse snapshot over the better chittorgarh value.
- Other confirmed early-snapshot victims: **Antony Waste (0.50 vs chittorgarh 9.82)**, **Radiant Cash (0.53 vs
  1.10)** — and the count is UNDER-stated because the name-join misses renamed names (do it by ISIN).
- **Two distinct bugs here:**
  1. **Sourcing:** the `nse` subscription extraction grabs an early/partial snapshot, not the final day-3 row.
     Fix in the scraper/extraction: parse the day-wise table and take the **last/close-of-bidding** figure.
  2. **Cross-source selection:** even with a bad nse value, a `0.26` vs `13.44` disagreement (~50×) should have
     **FLAGGED**, not silently picked nse. Source-priority alone is insufficient — the match must compare and
     flag large disagreements (this is the owner's "2-source match" point, made concrete).

## B. What STAYS (the engine is sound)
- The 5-code `Prov` engine + `classify()` decision tree (N/A → error_out → Missing_data(404/empty) → error_out
  (parser crash) → Missing_data(None/placeholder) → validity → present).
- validate-before-stamp; only `error_out` retryable; `EMPTY`→`Missing_data`; fail-loud validators (non-bool
  raises, exceptions propagate); `classify_column`, `derived`.
- **The gate-scope principle (now explicit):** the gate applies ONLY single-source-defensible rules — strip
  placeholders, classify our-fail vs source-gap, reject the IMPOSSIBLE. It must NOT *promote* a doubtful value
  to `present`; promotion of uncertain values is the MATCH's job (Phase 2). Default uncertain → `Missing_data`.

## C. What's WRONG and must be FIXED (in what we built)
| # | Problem | Fix |
|---|---|---|
| **F1** | `subscription_x_valid` uses a board rule ("SME 0 → present"). The owner proved this false: a listed IPO **cannot** have 0 total subscription (it wouldn't have listed). | **Rewrite:** `0` or negative → invalid (→ `Missing_data`, recoverable). `>0` → value kept. **No board context. No ≥1.0 floor** (real companies listed <1.0). |
| **F2** | `columns.yaml` `sub_total_x` description says "SME 0x can be REAL" — false. | Update description: "0× is impossible for a listed IPO → Missing_data; <1× kept but flagged for cross-source review." |
| **F3** | `validate_gmp_nonzero` assumes a source `0` GMP is always a placeholder. But a genuine **0% GMP is plausible-real** (many IPOs have no grey-market premium). This is the same over-stepping as F1. | **Review/soften:** treat source-`0` as `Missing_data` ONLY as a documented source-behavior assumption (investorgain reports 0 when untracked), and FLAG it — don't silently null a possibly-real 0. Decide with the owner. |
| **F4** | Tests encode the wrong rules (SME-0 → present; the direct `subscription_x_valid` board cases). | Flip: SME-0 → `Missing_data`; add a `0<x<1` real-listing case (stays a value, flagged); add the `=0` impossible case; drop the board assertions. |

## D. NEW rules for the 0<x<1 and cross-source layers (carry into the build)
- **`sub_total_x` validity (final):** `=0`/neg → `Missing_data`; `0<x<1` → KEEP the value but set a **review
  flag** (could be weak-but-real OR a wrong-snapshot error like Adani Wilmar) — resolve in the MATCH; `≥1` →
  value kept. No board.
- **The MATCH layer (Phase 2) owns correctness:** per field, fallback order + record `_src` + **flag on
  disagreement, never silently pick**. This is where Adani Wilmar's `0.26` gets caught (vs ipowatch/NSE ~17×).
- **Per-field study is mandatory** before trusting a field — like this subscription study. Generic plausibility
  checks are the floor, not the guarantee.

## E. The fix LIST (do these, in order, before moving ahead — awaiting owner go)

### E1 — Fix what we built in T1.1 (the gate)
1. Rewrite `_subscription_x_valid` in `foundation/registry/__init__.py` per F1 (drop board; reject 0/neg; keep >0).
2. Update `sub_total_x` description in `columns.yaml` per F2.
3. Decide F3 (GMP-0): keep-as-placeholder-with-flag vs accept-real-0. Then adjust `validate_gmp_nonzero` + its
   column description accordingly.
4. Update `tests/foundation/test_provenance.py` per F4 (flip SME-0 case; add 0<x<1 + =0 cases; drop board).
5. Re-run the suite + verify; update the T1.1 task-log entry to record the correction.
6. THEN consider committing T1.1 (corrected).

### E2 — Recorded for the BUILD (not T1.1 code; these are the real correctness fixes A2 exposed)
7. **Subscription final-row sourcing:** the `nse` subscription extraction must take the **last/close-of-bidding**
   row of the day-wise table, not an early snapshot (fixes Adani Wilmar 0.26→17.37, Antony Waste, Radiant…).
   This is a scraper/extraction fix → Phase 0/2, tracked here so it isn't lost.
8. **ISIN-only joins for the cross-source match** (never name) — proven necessary (the AWL name-join miss).
9. **Cross-source disagreement flagging** in the match (Phase 2): when two sources differ by >Nx, FLAG (don't
   silently pick by priority). This is where the early-snapshot/wrong-value cases get caught.
10. Re-run the subscription disagreement census **by ISIN** to get the true count of early-snapshot rows.
11. Apply the withdrawn-IPO detection by POSITIVE evidence + ISIN + flag-don't-drop (A1) — not name-absence.

## F. Principle banked (for the whole foundation)
> The gate rejects the impossible and normalizes honesty (doubt → Missing_data). The match decides truth across
> sources and is the only layer allowed to bless an uncertain value. Every field gets studied before its rule is
> trusted. A plausible-but-wrong value is caught by the match, never by the gate alone.
