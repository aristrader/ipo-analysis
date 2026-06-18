# 03 — Corp-action D-1 deep-dive (the original bug + a NEW under-coverage bug)

Two bugs live here, in OPPOSITE directions:
- **D-1 over-count** (known): one event reported by ≥2 sources on near dates → counted ≥2× → fake multibaggers.
- **NEW under-coverage** (found tonight): the fresh NSE fetch returns a *rolling window* and **dropped 25 real
  recent corporate actions** that frozen had → those splits would go UN-adjusted → fake crashes.

## 1. The −26 corp-action delta decomposes cleanly
Frozen `reference/corp_actions.csv` 1,509 → build 1,483 (−26):
- **−5** = the `verification_2026-05-31` manual golden rows (hand-verified, never in a raw scrape). **Expected**
  to vanish from a fresh fetch — they belong in the OVERLAY/golden and must be re-injected there (validates the
  overlay design: manual corp-action fixes are append-only golden, not scraped).
- **−21 net scraped** (with a finer key: 41 frozen-only events vs 20 build-only) = NSE API rolling-window variance.

## 2. ⚠⚠ NEW BUG: 25 real recent corporate actions DROPPED by the fresh fetch
Of the 41 events present in frozen but missing from the fresh scrape, **25 have a symbol IN our IPO universe** —
and they are all **recent (Jan–Jun 2026)**:

`MCX 1:5`, `ANGELONE 1:10`, `INFOBEAN 4:1 bonus`, `SILVERTUC 2:1 bonus + 1:5 split`, `V2RETAIL 1:10`,
`METROPOLIS 4:1 bonus`, `ECLERX 2:1 bonus`, `IRB 2:1 bonus`, `LICI 1:1 bonus`, `ANANDRATHI 2:1 bonus`,
`E2E 1:10`, `RNBDENIMS split+bonus`, `PASHUPATI 1:10`, `AHCL split+bonus`, `AVROIND 1:10`, `KAPSTON`,
`ORIENTTECH`, `AXITA`, `DHARIWAL`, `FOCE`, `RMDRIP`, `LEMERITE`, …

**Internet-verified (sample):**
- **MCX** — real 1:5 split, ex-date **2026-01-02**, FV ₹10→₹2, **new ISIN INE745G01043** (face-value split
  changes the ISIN — confirms the "corp-actions match by SYMBOL" rule).
- **LICI** — real **1:1 bonus**, ex-date **2026-05-29** (first since its 2022 listing).

**Why it matters:** the NSE corp-action endpoint apparently returns a window relative to "now"; by the
2026-06-18 re-fetch, the Jan–May 2026 events had aged out. If the swap uses `data_build`'s corp-actions
*alone*, these 25 splits/bonuses go un-adjusted → those price series show a fake −80–90% "crash" on the ex-date.
**This is a correction the project would otherwise miss.**

### Fix (this is a data-copy/merge principle, doc 06)
- **Corp-actions must be UNION-merged across all fetches (append-only), never replaced.** Each fetch is a
  partial window; the truth is the union. (Frozen also *lacked* 2 old events the fresh fetch found — HDIL 2008,
  INVENTURE 2012 — so union is bidirectional.)
- Widen the fetch's date range so recent events aren't lost (or accept that union-with-frozen covers it).
- Re-verify the union against the live source periodically (the D15 "periodic full re-fetch/diff").

## 3. D-1 over-count: 10 double-count clusters confirmed
Predicate: same `symbol` + same **rounded** `ratio_factor`, **≥2 distinct sources**, ex-dates **2–90d apart**.
On `corp_actions_merged.csv` (1,897 rows / 1,222 symbols) → **10 clusters**:

`ROLEXRINGS(10.0, 3 rows, 28d)`, `CANTABIL(5.0, 13d)`, `DIGIKORE(2.0,14d)`, `GNA(2.0,21d)`, `MOS(2.0,18d)`,
`NPST(3.0,11d)`, `PAVNAIND(2.0,19d)`, `RPEL(2.0,15d)`, `USASEEDS(1.43,14d)`, `VISHWARAJ(5.0,43d)`.

Substrate confirms the fakes (current return-from-issue):
- **Rolex Rings 152×** (a single 10:1 split counted 3× → ×1000 region). Internet: ONE 1:10 split, ex ~2025-10
  → golden ratio = 10.0 once.
- **NPST 161×** (3:1 counted 2×). **Cantabil 39.7×** while −57% at 5y (clearly over-adjusted).
- GNA (6.4× / 5y 3.4×) and Pavna (3.0× / 5y 3.9×) look internally consistent → likely *real* multibaggers whose
  cluster is a benign double-report; the de-dup must not zero them, just collapse to ×1.

## 4. Same-event collapse window — CALIBRATED
- Cluster ex-date spans: **min 11d, median 16d, p90 29d, max 43d** (VISHWARAJ).
- A **30d** window (the spec's T5.3 leaning) **MISSES VISHWARAJ (43d)**. **Use ~45d.**
- **But widening the window raises false-merge risk:** keyed on *symbol alone*, 10 / 14 / 17 symbols have a
  **different-ratio** event within 30 / 45 / 60d (e.g. `538706` has a 1.5 bonus AND a 5.0 split 1 day apart —
  two REAL events). So the collapse predicate **must key on (symbol, rounded-ratio) AND require ≥2 distinct
  sources** — the multi-source signal is the real disambiguator, not proximity.
- **Calibrated rule:** collapse to ONE event when `same symbol` + `same rounded ratio` + `≥2 distinct sources`
  + `ex-dates ≤ 45d apart`. Catches all 10 dup-clusters; never merges the different-ratio real pairs.
- Residual edge: two *genuinely distinct* events with the *same* rounded ratio ≤45d apart, same source — NOT
  merged by this rule (conservative; kept distinct). Flag any such for manual golden review.

## 5. The golden corp-action catalog (P-1) — seed it with these verified rows
| symbol | true action | ratio_factor | ex/record date | note |
|---|---|---|---|---|
| ROLEXRINGS | split (FV 10→1) | 10.0 (×1) | ~2025-10-17 (rec 09-19) | counted 3× in merged → fake 152× |
| NPST | split | 3.0 (×1) | — verify | counted 2× → fake 161× |
| CANTABIL | split | 5.0 (×1) | — verify | over-adjusted, −57% at 5y |
| MCX | split (FV 10→2) | 5.0 | 2026-01-02 | NEW ISIN INE745G01043; lost by fresh fetch |
| LICI | bonus 1:1 | 2.0 | 2026-05-29 | lost by fresh fetch |
*(verify the remaining clusters' true single-event ratio + date at build; fallback order golden → price-gap
arbiter → source-reconcile → flag, per spec §2.9.)*

## 6. Action items into Phase 5
1. **Union-merge corp-actions (append-only)** — fixes the 25 dropped recent events. ⚠ highest priority.
2. Collapse rule: `(symbol, rounded-ratio, ≥2 sources, ≤45d)` → one event. ⚠ (45d, not 30d).
3. Re-inject the 5 `verification_2026-05-31` golden rows via the overlay.
4. Seed the golden catalog with the verified ratios above; the symbol-only-yf dups (ENGINERSIN, OPTOCIRCUITS,
   GICL) are corroboration-only (D12) — never adjust on yf alone.
5. The price-gap arbiter remains the source-agnostic backstop where sources disagree.

Sources: angelone.in (MCX), licindia.in / businesstoday.in (LICI), trendlyne.com / choiceindia.com (Rolex Rings).
