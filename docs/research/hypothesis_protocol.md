# Hypothesis-testing protocol — THE agent brief (paste/point every research agent here)

Purpose: any agent (or future session) testing an IPO hypothesis works at the standard this
project reached in Phase 2 — from its FIRST prompt, without being re-taught. This file is the
single source for HOW to test; `rules/index.md` is the single source for WHAT was already tested.

## 0. Before testing ANYTHING
- **Check `rules/index.md` first.** ~60 signals/hypotheses already carry verdicts (in-score /
  display-only / rejected, with WHY). Re-testing a rejected idea without new evidence is wasted spend.
- Substrate = `data/master/ipo_analysis.csv` (load via `layer3/spine.py:load_substrate()`).
  Movable facts (row count, as-of) live in `data/master/substrate_meta.json` — never hardcode them.
- Working scripts live in `tools/research/` — copy the conventions of an existing one
  (e.g. `wave2_substrate.py`, `wave2_pricepath.py`).

## 1. The bar: second-order only
First-order screens ("undersubscribed → bad") are done and mostly dead. A testable idea must be an
INTERACTION, SEQUENCE, REGIME-CONDITION, or CROSS-IPO mechanic, with a stated economic MECHANISM
(whose money moves, why, when). Exemplar: "4 strong IPOs in one week → limited wallet → the 2 with
lower GMP get starved at listing but outperform after week 1."

## 2. The 3-layer protocol (every test, in order)
1. **L1 EXISTENCE** — does the pattern exist at all?
   - Pre-declare the FALSIFIER (what result kills it) before running.
   - PLACEBO wherever possible: fake level / shuffled labels / pre-regulation cohort /
     pseudo-events matched on confounders. A pattern that also shows up in the placebo is DEAD
     (this killed F1 and F5a — it earns its keep).
2. **L2 MAGNITUDE & SHAPE** — size, duration, dose-response tables, % of cases affected.
   Monotonicity across buckets matters more than a single split.
3. **L3 PLAYBOOK** — the conditional TRADE: pre-declared entry grid (fixed BEFORE looking),
   horizons, win-rate / median / P10 / P90 vs the buy-and-hold counterfactual, and the FAILURE
   CELLS. Report the WHOLE grid — no best-cell cherry-picking.

## 3. Data conventions (non-negotiable)
- Exclude `listing_metrics_status == "unreliable_coverage"`.
- Returns = **alpha vs Nifty** (raw secondary). From-listing = secondary buyer; from-issue = allottee.
- Adjusted prices everywhere → use `issue_price_adj` (not `issue_price`) against `data/prices/*.csv`.
- Min-N floors: <12 suppress · 12–29 say "thin" · ≥30 report. Always print N.
- Distributions over means (median + P10/P90); medians for skewed outcomes.
- Cross-regime gate: a headline cell must hold in boom (2020–25) AND longterm (2006–19), ideally
  MB and SME separately (the 4-cell check). One-cohort effects = "boom-only/MIXED", not validated.
- OOS where horizons permit: train ≤2021, test ≥2022 (or the 2026 forward cohort).

## 4. Look-ahead traps (each of these was actually caught here — check every feature)
- "days_to_peak", lifetime turnover, anything computed over the FULL window then used to classify
  at entry (F5b's touch-and-fail used future 60d — never tradable).
- Trailing/rolling features must be point-in-time: only data from BEFORE the row's listing/event
  date (≥5 priors or null). Regime features: `layer3/regimes.py` (already PIT-safe).
- Endpoint columns (`alpha_1y` etc.) start at LISTING — if your signal forms at day X, measure
  forward returns from day X+1 (the F5e graduation required the d91→d341 re-test).

## 5. Score policy (LOCKED: "evolve-only-if-robust")
A surviving signal enters the weighted score ONLY if it improves OOS top-quintile lift robustly
across splits (fold harness: `tools/research/heat_fold_test.py` / `climate_fold_test.py` pattern;
folds 2021/2022/2023 × 1y/3y). Otherwise: display-only. Post-listing signals (e.g. the day-90
capitulation flag) are monitoring/exit flags, never score inputs.

## 6. Environment gotchas
- Run with `PYTHONPATH=. .venv/bin/python` (plain `python` doesn't exist on this box).
- **No scipy** → no `.corr(method="spearman")`. Use the srho helper (rank both, then pearson) —
  copy it from `tools/research/wave2_substrate.py`.
- `wc -l` lies on the CSVs (embedded newlines) — count records via the `csv` module / DuckDB.
- Price files: `data/prices/<isin>.csv` (date,open,high,low,close,volume), already split/bonus
  adjusted; filter `date >= listing_date` and re-index to trading days from listing.

## 7. Recording the verdict (the chain — ALWAYS, kill or survive)
1. Append the verdict + numbers to `docs/research/tier1_wave1_verdicts.md` (the ledger).
2. Append a registry line to `rules/index.md` (so it's never re-tested blind).
3. Update the Phase-2 block in `STATUS.md`.
4. Script stays in `tools/research/` (reproducibility). Commit (git is LOCAL-ONLY — never push).
