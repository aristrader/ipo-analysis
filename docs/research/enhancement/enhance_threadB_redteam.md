# Thread B hardening — red-team (could it give FALSE confidence?)

Lens: where data corruption / scraper-rot SLIPS PAST the schema gate + GMP-history capture, and
where a "clean" signal misleads. Verified against live data 2026-06-08. Each: where · how it slips ·
fix · severity.

## #1 FALSE-CONFIDENCE RISK (data-integrity-critical)
**`score` is declared `required+numeric` but has NO `max_null_rate` → 22% of the ledger's score column
is null and the gate still prints "clean".**
- VERIFIED: `calls_ledger.csv` has 1135 / 5170 null `score` (historical_sim 891, backfilled 242,
  gap_filled 2). Gate output: "SCHEMA GATE: clean — all pinned contracts hold."
- WHY it slips: `numeric` only checks min/max on the **dropna()** subset; `_check_file` only enforces
  null caps when `max_null_rate` is set. Any numeric column without a null cap can go 100% null and pass.
  Same hole on `alpha_1m/alpha_3m` (1.5% null today, but uncapped — could silently go all-null after a
  returns regression and still read "clean"). The score is the product's headline output; a refresh that
  half-breaks scoring would ship green.
- FIX: add `max_null_rate` to every `required+numeric` col (score, alpha_1m, alpha_3m, issue_price_adj
  already has one). Make `numeric` with no explicit cap default `max_null_rate=0.0`, OR have the checker
  warn when a required col has no null cap. severity: data-integrity-critical.

## Ledger ⇄ substrate disagree on which ISINs exist (important)
- VERIFIED: 4 ledger ISINs are NOT in `ipo_analysis.csv`. The gate checks each file in isolation — there
  is NO cross-file referential check. A refresh that drops/renames ISINs in the substrate while the ledger
  retains them (or vice-versa) passes both single-file contracts. Calls would grade against rows that no
  longer exist.
- FIX: add a relational assertion to `check_all()` — `set(ledger.isin) ⊆ set(substrate.isin)` (allow a
  small grandfathered set, but COUNT it and cap it). severity: important.

## Wide ranges mask real corruption (important)
- `alpha_1m min −1.5 max 50`: live data spans −1.12..2.18. A **scale flip** (×100, % vs fraction) on
  alpha lands inside −1.5..50 and passes. A −1.0 (total wipeout) is valid, so the −1.5 floor can't even
  catch a sign/scale error near zero. `score 0..100`: a typo squashing all scores to e.g. 50 stays in band.
- HOW it misleads: range gates catch only gross blowups, not the realistic failure (a transform applied
  twice, a units swap, a constant). FIX: pin a **distributional** sentinel per key column — median/IQR or
  mean within ±X of a stored golden (you already derive goldens in phase 8; reuse them here). A frozen-
  median check would catch scale flips a wide range never will. severity: important.

## Silently dropped rows pass under the floor (important)
- `_min_rows` floors are 100 (ledger) / 2000 (substrate, true count 2384). The substrate could LOSE ~380
  rows (16%) and still clear 2000. A row-count REGRESSION vs the prior snapshot is the real signal, not an
  absolute floor. FIX: compare against `substrate_meta.rows` / the archive snapshot — flag any DECREASE
  (refresh only ever adds). severity: important.

## mode/call_type typos pass (nit→important)
- `mode`/`call_type`/`grade_status` are checked only for non-null, NOT against an allowed-value set. A
  scraper-rot typo ("histroical_sim") or a new bogus mode passes. Downstream filters silently match nothing.
- FIX: add `allowed: {...}` enum check (live modes: historical_sim, backfilled, live, gap_filled). severity:
  important (it's how scoring/backtests slice the ledger).

## GMP-history dedup on (fetch_date, name) is fragile (important)
File: `scrapers/live_board.py:append_gmp_history` (+ same in `append_daywise`).
- **Name drift across fetches** — name is derived `_clean(Company).replace(" O","")` + token-matched to
  GMP. If chittorgarh tweaks the name string between fetches, dedup KEY changes → the same IPO logs TWICE
  same day, OR (worse) trajectory rows for one IPO split across two name spellings → broken time series.
  ISIN is the stable key and is captured — dedup should be `(fetch_date, isin)` with name as fallback only
  when isin is null. severity: important.
- **Same IPO, two exchanges / dual listing** — distinct only if name differs; if identical, one row is
  dropped (acceptable) — but no exchange/type in the dedup key, so an MB+SME name collision loses one.
- **Missing GMP = silent no-row, read as "captured"** — append only fires when `gmp_pct is not None`. On a
  fetch where the GMP source is down (investorgain AND ipowatch both miss), the issue produces NO row and
  the run prints "gmp-history rows appended: N" counting only the lucky ones. You THINK you have a daily
  trajectory; you actually have holes exactly on the days the source was flaky — and nothing records the
  gap. FIX: write the row anyway with `gmp_pct=null` (a captured-but-empty observation ≠ no observation),
  or emit a per-fetch coverage line "X open issues, Y had GMP". severity: important (corrupts the very
  trajectory dataset this feature exists to build).

## The gate runs AFTER the swap — bad substrate is already live (data-integrity-critical)
`run_refresh.py` phase 7-9 rebuild + OVERWRITE `data/master/*` and re-derive goldens; the swap is done by
phase 11 when the gate runs. Worse, phase 11 only **prints** "⚠ SCHEMA VIOLATIONS" — it does **not** raise,
does not roll back, does not exit non-zero. So a violation leaves the corrupt substrate live AND the run
reports "REFRESH COMPLETE". (The phase-8 pytest suite is the only real gate; the schema gate is decorative
at its current position.)
- FIX: run the gate BEFORE the swap — assemble into a temp/staging path, gate it, and only `mv` into
  `data/master/` if clean; on violation raise SystemExit (rollback is the documented snapshot copy). At
  minimum, make phase 11 `raise` on violations so the run fails loudly instead of green. severity:
  data-integrity-critical.

## "Clean" verifies less than it sounds (framing nit, but it's the meta-risk)
`test_real_data_passes_gate` asserts the LIVE data passes — so the test is green by construction and the
gate's pinned ranges were (reasonably) drawn from current data. The message "all pinned contracts hold"
reads as "the data is sound"; it actually means "≈10 columns are non-null/in a wide band, nulls mostly
uncapped, no cross-file/distribution/enum/row-regression checks." Keep the gate, but rename the success
line to scope the claim, and treat the items above as the gap between "passes the gate" and "is correct".

## Summary — fix priority
1. Add null caps to all numeric required cols (score is 22% null, reads clean) — **#1 risk**.
2. Gate BEFORE the swap + RAISE on violation (today it's post-swap and non-blocking).
3. Cross-file ISIN referential check (4 orphans live now).
4. GMP-history: dedup on isin, write null-GMP rows so gaps are recorded not invisible.
5. Distributional/golden sentinels (catch scale flips) + row-count-regression vs snapshot + enum checks.
