# Iteration 1 — BREAK-IT walk findings (2026-06-07)

Walker: iteration-1 break-it walker. App: http://localhost:8597 (Streamlit, headless chromium).
Method: walked all 7 screens + 6 edge ISINs + 4 hostile params + every distinct link/button + the 13 prophet repros.
Ground-truth cross-checks done in python against `data/master/calls_ledger.csv`, `ipo_analysis.csv`, `layer3/spine.py`.
Benign `/_stcore/health` + `/_stcore/host-config` 404s ignored throughout (present on every page, 2 each).

## Findings (one line each)

- [P1] ipo_detail · "detail →" links drop the ISIN — land on the bare lookup form, not the target IPO · repro: Recommendations → click any Tracking/Alerts "detail →" (e.g. Aureate Tradde) → lands `http://localhost:8597/ipo_detail` with NO `?isin=` · evidence: every "detail →" link renders `/url: ipo_detail` (no query); after click URL = `…/ipo_detail`, page header = "🔎 Look up or score an IPO". (CONFIRMS thinker isin_link bug + prophet repro structure.)
- [P1] ipo_detail · `?isin=GARBAGE123` silently shows the SCORE FORM, no "ISIN not found" message · repro: navigate `?isin=GARBAGE123` · evidence: renders "🔎 Look up or score an IPO" form identically to no-param; no not-found copy. (CONFIRMS prophet #5 / thinker step 8.)
- [P1] home · "Track record — N graded" undercounts: shows **3523 graded (5166 total)** = `grade_status=="final"` only, dropping 1570 `partial` rows · repro: open HOME, read MONITOR card "3523 calls graded (5166 total)" · evidence: ledger value_counts = {final 3523, partial 1570, pending 73}; charter known-fix says graded = final+partial = 5093. Contradicts Recommendations/Track-Record which aggregate partial too. (CONFIRMS prophet #2/#5 numbering — the graded-undercount.)
- [P2] ipo_detail · unreliable-coverage REIT `?isin=INE2OVN25015` silently falls through to the lookup form (looks like a garbage ISIN) · repro: navigate `?isin=INE2OVN25015` · evidence: row EXISTS in substrate (Bagmane Prime Office REIT, type MB, listing_metrics_status=unreliable_coverage) but `spine.load_substrate(equity_only=True)` default drops reit/invit/fpo, so `df[df.isin==…]` is empty → score form. Correct exclusion, but no "REIT — excluded from equity analysis" message; indistinguishable from a typo.
- [P2] recommendations · "Run refresh now" does NOT bust caches in-place — tells user to re-open · repro: Recommendations → 🔄 Refresh popover → "Run refresh now" · evidence: status message "Refresh attempted — re-open the page to see updates." Board stamp does not refresh on screen. (CONFIRMS prophet #1 cache-staleness gap; no `st.cache_data.clear()`.)
- [P2] ipo_detail · lowercase ISIN `?isin=ine14ox01013` not found → silent score-form fallthrough (no case-insensitivity) · repro: navigate `?isin=ine14ox01013` (valid ISIN, lowercased) · evidence: lands on "🔎 Look up or score an IPO" form; `df.isin==isin` is case-sensitive. Same silent-fallthrough class as garbage.
- [P3] track_record · Backtester tab is slow to compute (~30–40s with header "Running…" before tables appear) · repro: Track Record → 📈 Backtester tab · evidence: tabpanel empty for ~30s, then full content (strategy tables, flip EV, exit-discipline, combined-score loop-closer) renders correctly. No crash; latency only (iter4 budget item).
- [P3] track_record · OOS report-card copy renders numbers with markdown strikethrough ("Real edge at 3y (~~+55pp~~); weak at 1y (~~+2–5pp~~)") · repro: Track Record → 📋 Call track record → section C blurb · evidence: snapshot shows `deletion` nodes around "+55pp" / "+2–5pp" — stray `~` in the markdown string. Cosmetic.
- [P3] ipo_detail · Vega-Lite console warnings on chart-heavy detail pages (Infinite extent / Scale-binding / discrete-width) · repro: any detail page with histogram + price chart (e.g. INE538H01016 → 19 warnings) · evidence: `WARN Infinite extent for field "count_start"…`, `WARN Scale bindings only supported for unbinned continuous domains`. Charts still render correctly. Cosmetic.

## Screens walked cleanly (no exception, honest empty states)
- Home, Recommendations, Evidence Browser (+ tabs), Signal Registry, Track Record (all 3 tabs), Data & Methodology (all 4 tabs) — all render; as-of stamps present (substrate 2026-06-06, ledger 2026-06-07, board 2026-06-07T18:29:17).
- Edge ISINs all render full 8-section detail with graceful degradation, NO raw nan/None:
  - INE538H01016 (delisted/liquidation MB) — full read; price chart ends ~2014. NOTE: no explicit "delisted / terminal −100%" badge in Verdict (degrades silently — borderline P3, see open question).
  - INE583L01014 (delisted, blank reason MB) — full read; NEUTRAL ledger call, capitulation + obscure-banker flags; blank delist_reason never shown as "None".
  - INE627H01017 (2006 no-GMP MB) — full read; cluster shows peers without a GMP-rank line; no `nan`.
  - INE1RQS01010 (unpriced SME) — ⑥ shows "No price file for this IPO — showing the *expected* reach ladder from analogs instead." NO empty-axes error.
  - INE0DRT01018 (no-sector SME) — full read; cluster "12 same-segment peers"; no `nan`.
- Hostile `?isin=` (empty) → lookup form (correct, empty string falsy). `?foo=bar`-style handled the same.
- Score-a-new-IPO form (MB, all defaults) → full "New IPO · MB" read, N=50, graceful "no open_date / no dated events / no price file", wipeout "not assessed — unknown ≠ safe". predict() did NOT crash.

## Prophet's 13 predictions — confirm/deny
1. Refresh doesn't bust caches — **CONFIRMED** (P2). "Run refresh now" → "re-open the page to see updates"; no in-place cache clear.
2. Every OPEN board card shows "call: pending" — **DENIED / STALE** (fixed). OPEN cards show real EARLY_AVOID/EARLY_APPLY calls with live_score. BUT board ISINs ARE null → OPEN cards have no clickable detail ("detail — no ISIN yet"). The isin_link drop is real on Tracking/Alerts rows → see P1 above.
3. `?isin=garbage` silent score form — **CONFIRMED** (P1, GARBAGE123). Also lowercase + REIT fall through the same way (P2 each).
4. Blank-ISIN name dropdown dead-end — **DENIED / not reproducible**. App df (equity_only, 2329 rows) has 0 blank-ISIN rows; the dropdown can't surface one.
5. HOME undercounts graded (final only, drops 1570 partial) — **CONFIRMED** (P1). 3523 vs final+partial 5093.
6. predict() unguarded on detail page → raw traceback — **NOT REPRODUCED in walk**. Broad/default score query returns N=50 (analog finder backs off to type-only), so no empty cohort surfaced; the unguarded call still exists in code (ipo_detail.py:~108) but I could not force a thin-enough cohort through the UI.
7. `n_cohort < MIN_N` assumes int (tied to #6) — **NOT REPRODUCED** (same reason; n_cohort always populated in tested paths).
8. `o['name']`/`o['type']` direct-index KeyError on partial board.json — **NOT REPRODUCED** (live board.json well-formed; would need a hand-corrupted board to trigger; not done — file-edit out of scope).
9. SME dead-money `>= 5` string-compare TypeError — **DENIED**. INE1RQS01010 + INE0DRT01018 (both SME, dead-money 20.5% / 6.1%) render the SME dead-money rule alert cleanly; values are numeric.
10. corp_actions direct-index KeyError — **NOT REPRODUCED** (schema intact on all walked detail pages; no ex-date rows broke).
11. n_floor string mixed in numeric track-record column — **NOT OBSERVED as broken** (track-record table rendered; thin rows show "too few" per the section blurb; no garbled cell seen in the walk).
12. TRACK age bdate-vs-calendar mismatch ("d21 in ~Xd") — **PLAUSIBLE/UNVERIFIED** (display). Tracking rows show "d21 persistence read in ~Nd" with strikethrough day counts (e.g. ~~28d~~); did not reconcile trading-vs-calendar days this pass (iter2/3 data-honesty item).
13. timezone-naive now() midnight flip — **N/A this pass** (not testable mid-session; no anomaly observed).

## Open question for owner (not a defect call)
- Delisted/liquidation names (INE538H01016) render a normal read with no prominent "delisted / terminal −100%" badge in the Verdict. Thinker's script expected the delisting surfaced. Currently it's only inferable from the price chart ending early. Flag for iter2 data-honesty triage (borderline P2/P3).

## Severity counts
- P0: 0
- P1: 3 (isin_link drop · ?isin=garbage silent form · HOME graded undercount)
- P2: 3 (REIT silent fallthrough · refresh doesn't bust cache · lowercase ISIN not found)
- P3: 3 (backtester latency ~30–40s · OOS strikethrough copy · Vega chart console warnings)
- Total: 9 findings. Zero raw tracebacks reachable across all edge ISINs + hostile params.
