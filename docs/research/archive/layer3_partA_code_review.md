# Layer 3 Part A — Code Review (correctness & methodology-compliance)

**Reviewer stance:** adversarial — assume bugs exist. Scope: `layer3/` package + `run_layer3_report.py` + `tests/layer3/`, checked against the spec (`docs/superpowers/plans/2026-05-31-layer3-partA-descriptive.md`), the 6 must-fixes (`docs/research/layer3_methodology_review.md`), strategies §0, and the live substrate `data/master/ipo_analysis.csv` (2,245 equity rows).

**Build status:** `PYTHONPATH=. pytest tests/layer3/ -q` → **28 passed**. `PYTHONPATH=. python run_layer3_report.py` → **8/8 findings, 309 KB**. Tests are green and the report builds.

**Substrate has been re-pulled since the methodology review:** `alpha_sc_*` now exists; `listing_metrics_status` = ok 2024 / inferred_split 78 / recovered_bhavcopy 73 / unreliable_coverage 59 / NaN 11; `delisted`=203, `delist_reason` non-null=40; `outcome_class` NaN=13; **boom-MB sector coverage is now 94.3%** (the review's C2 "3%" concern is moot). Several methodology-review concerns are therefore already addressed by data, not code.

**Spot-checks against the raw substrate (all matched the engine):**
- T1 boom-MB 1y: engine N=277, median alpha −10.68% = manual recompute exactly.
- Wipeout band overall: lower=162 (=`outcome_class==wipeout` count), upper=256 (+94 unknown-reason delisted). Correct.
- T3 MB >100%-pop bucket: N=23, median fwd-1y-from-listing −26.32%. Buckets cover all 805 trusted-MB rows with zero double-count and zero drop.
- T8 MB winners drawdown: `max_drawdown_pct` is negative; p10=−0.915 is the deepest → "worst" math is correct.

## Must-fix verification summary

| # | Must-fix | Verdict |
|---|----------|---------|
| 1 | T3 uses RAW return_from_listing, never alpha | **PASS** — T3 reads only `return_from_listing_*`; "alpha" appears only in prose. Enforced by `test_t3_uses_raw_not_alpha`. |
| 2 | Long-horizon = longterm-carried; boom long-horizon suppressed, no cohort-switching line | **PARTIAL FAIL** — charts never switch cohorts (OK), but T1 and T9 **print boom 3y/5y base-rate cells next to longterm** with no suppression/illustrative tag. See C1. |
| 3 | Competing-risks wipeout is a BAND, no monotonicity assumption | **PASS** — `wipeout_band` returns lower/upper; T2 has no monotonicity test/assumption. |
| 4 | `current_return_from_issue` NOT used for base rates | **PASS** — never read anywhere; base rates use maturity-gated horizon columns. |
| 5 | Min-N suppression UNBYPASSABLE in `report._guard_table` | **FAIL** — bypassable; see C2 (T2/T8 count columns invisible to the guard) and C3 (guard keys on group-N while metric is computed on a smaller matured-N). |
| 6 | SME vs Mainboard never pooled | **FAIL in T9** — T9 pools MB+SME within cohort. See C4. |

---

## CRITICAL

### C1 — T1 & T9 show boom long-horizon (3y/5y) base rates as if mature (violates must-fix #2)
**Files:** `layer3/findings/t1_base_rates.py:34-43`, `layer3/findings/t9_profitable.py:25,36-39`

`config.py:13-15` comments that long horizons "default to longterm-only to avoid a cohort-swap trend," but no code enforces it. T1 loops `KEY_HORIZONS = [1y,3y,5y]` over **both** cohorts and emits boom-5y cells in the same table as longterm-5y. Rendered report (verified) shows:
- T1: `boom · MB · 5y · N=32 · median −57.7%` and `boom · SME · 5y · N=39 · median −8.2%` — these clear the N≥30 floor and print as confident base rates, exactly the "boom long-horizon as if mature" the must-fix forbids.
- T9: `boom · loss-making · 5y · median +36.7%` — **computed on only 5 matured rows** (verified), printed unsuppressed because the guard sees the group N=64 (see C3). `boom · profitable · 5y · −45.9%` is on 64 matured rows.

**Fix:** For `h in LONG_HORIZONS`, either restrict the row set to `cohort=="longterm"`, or tag every boom long-horizon cell `illustrative (boom, not mature)` and exclude it from any narrated comparison. Simplest: in T1/T9, only emit 3y/5y rows for the longterm cohort (keep boom at 1y), matching the config promise.

### C2 — Min-N guard is bypassable by count-column naming (violates must-fix #5)
**File:** `layer3/report.py:29` (`_guard_table`)

The guard fires only when a column is **exactly** `"N"` or `"n"`. Three findings name their count column otherwise, so the guard **never runs** on them:
- T2 (`t2_survival.py:40`) → `N_matured`
- T8 (`t8_drawdown.py:22`) → `N_winners`
- T7 coverage tables (`t7_benchmark.py:22,33`) → `N_with_alpha` / `N_nifty_alpha`

Today no sub-floor row happens to appear in T2/T8 (smallest live cell is T2 SME-10y N=153; T8 min N=389), so the report doesn't currently lie here — but the protection is **absent**, not satisfied. The spec's Task-6 contract and the methodology review (§Trap-2 fix) require the floor to be a property of the assembler. As soon as T8 gains its planned mcap split or T2 gains a cohort split (both in the spec), sub-floor numbers will print unguarded.

**Fix:** In `_guard_table`, detect the count column by pattern, e.g. `ncol = next((c for c in t.columns if c=="N" or c=="n" or c.startswith("N_") or c.startswith("n_")), None)`. If multiple `N_*` columns exist (T3, T5, T6 carry both `N` and `N_1y`/`N_matured`), guard each metric against its **own** governing count (see C3) rather than a single column.

### C3 — Guard checks group-N but metrics are computed on a smaller maturity-gated N (violates must-fix #5 intent)
**Files:** `t9_profitable.py:24-28`, `t5_ofs.py:22-25`, `t6_sector.py:21-25`; guard at `report.py:40`

In T5/T6/T9 the displayed `N` (or first count column) is the **full group size**, while `median_alpha_{h}` is computed on `maturity_gated(group, h)` — a strictly smaller set (`N_matured`). The guard suppresses on the full `N`, so a metric backed by <10 matured rows prints whenever the group total ≥10. Confirmed live in T9 (boom loss-making 5y: group N=64, matured N=5, prints +36.7%). T5/T6 don't trigger today only because longterm matured-N tracks group-N closely.

**Fix:** Guard each horizon metric against the count that actually produced it. Either (a) name per-metric counts (`N_3y`, `N_5y`) and have the improved guard (C2) suppress `median_alpha_5y_%` when `N_5y<10`, or (b) inside the finding, return the metric as `spine.guarded(value, n_matured)` so it is pre-suppressed before the table is built.

### C4 — T9 pools MB and SME (violates must-fix #6)
**File:** `layer3/findings/t9_profitable.py:18-39`

`_rows(sub, cohort)` segments only by cohort + profitability; it never splits on `type`. The output table has columns `[cohort, group, N, median_alpha_*, wipeout]` with **no segment dimension** — MB and SME are pooled inside each cohort. The Task-13 spec says "MB/SME separate; cross-regime," and strategies §0 trap 5 forbids pooling (a pooled boom number is "secretly an SME stat"). The narrative/caveats don't even mention segmentation.

**Fix:** Add the MB/SME loop: `for seg in config.SEGMENTS: for cohort in config.COHORTS: _rows(segment(df, segment=seg, cohort=cohort), seg, cohort)` and add a `segment` column. (T1, T3, T5, T6, T8 all segment correctly — T9 is the lone offender.)

---

## IMPORTANT

### I1 — T2 "cumulative wipeout by year" is not a real time-since-listing hazard
**File:** `layer3/findings/t2_survival.py:17-42`

`age_y = (TODAY − listing_date)` is age-to-today, and a company is counted as wiped out in **every** matured year `y ≤ age_y`, regardless of *when* it actually delisted (there is no delisting-date column in the substrate — confirmed only `delisted`/`delist_reason` exist). So a 2007 IPO that wiped out at age 2 is counted as a wipeout in the year-1, 2, 3, 5, 7 and 10 denominators alike. The curve is therefore "fraction that have *ever* wiped out, among IPOs old enough to reach year Y" — **not** "wiped out *by* year Y." The year-1 rate is inflated by late wipeouts, and the curve's upward slope is mostly denominator survivorship (older IPOs had more calendar time to die), not genuine listing-age hazard. The caveat ("read the band per year, not as a smooth survival curve") softens but the table is still titled/framed as cumulative-by-year.

**Fix:** Either (a) re-title to "share ever-wiped-out among IPOs with ≥Y years listed" and drop "cumulative … by year" language, or (b) acquire a delisting/last-trade date to time the event (likely a substrate gap → log in `docs/data_review.md`). At minimum state explicitly that wipeout timing is unknown and the curve is not a hazard.

### I2 — `proportion(rfi >= 1.0)` counts NaN as False, inflating the denominator
**Files:** `t1_base_rates.py:24-25`, `t6_sector.py:24` (`pct_2x`)

`proportion` does `pd.Series(mask).dropna()`, but the mask is built as `rfi >= 1.0` / `rfi < 0` where `rfi` may be NaN. `NaN >= 1.0` evaluates to `False` (not NaN) **before** the dropna, so rows with missing `return_from_issue_{h}` are counted in the denominator as "not 2x"/"not below issue." Currently harmless because `return_from_issue_{h}` is non-null wherever `alpha_{h}` is (verified: longterm-MB-5y 427/427), but it is a latent silent-understatement bug if coverage ever diverges.

**Fix:** Mask first: `rfi = rfi[rfi.notna()]` before `proportion`, or pass a nullable boolean (`pd.Series(np.where(rfi.notna(), rfi>=1.0, np.nan))`) so the NaN rows drop.

### I3 — Benchmark policy claimed but never wired into any metric
**Files:** `config.py:27-29`, `spine.benchmark_for` (`spine.py:73-75`), all findings; report header `report.py:68`

`benchmark_for` and `SMALLCAP_MCAP` imply small/micro/SME metrics use Smallcap-250 alpha. No finding calls `alpha_series(..., "smallcap")` for a metric — every base rate uses Nifty-50. T7 only reports smallcap *coverage*. The report header states "Smallcap-250 for small/micro where available," which **overstates what the engine does**. Per the methodology review §5, all micro/small/SME alpha is Nifty-mismatched (overstated upper bound). This is consistent with the plan (Part A = Nifty-50 + caveat) but the header/config wording misrepresents it.

**Fix:** Either wire `benchmark_for` into T1/T6/T8 micro/small/SME rows, or soften the header to "alpha is vs Nifty 50 for all metrics in Part A; for micro/small/SME this overstates alpha in small-cap bull regimes — Smallcap-250 application deferred." Update the `config.py:27-29` comment to match.

---

## MINOR

- **M1 — `_NEVER_SUPPRESS` over-broad whitelist** (`report.py:13-14`): includes generic words `label`, `metric`, `group`, `bucket`, `horizon`, `year`. A finding that puts a per-group *metric* in a column named one of these would bypass suppression. No current finding does, but it widens the C2 attack surface. Prefer an explicit allow-list of identifier columns per finding, or restrict to `{N, n, segment, cohort, *_class, broad_sector, *_bucket}`.
- **M2 — T8 column mislabel** (`t8_drawdown.py:25`): `p90_worst_drawdown_%` holds `distribution(dd)["p10"]`. The value is correct (p10 of a negative series is the deepest drawdown) but the name says p90. Rename to `worst_drawdown_p10_%` or `deepest_decile_dd_%`.
- **M3 — Suppressed rows also blank their `N_matured`/secondary counts** (`report.py:33,43-48`): because `N_matured`, `N_1y`, `N_3y` aren't in `_NEVER_SUPPRESS`, a suppressed T3/T6 row loses the matured count too, so the reader can't see how close to the floor it was. Add the secondary count columns to the never-suppress set.
- **M4 — T3 first bucket lower bound `-10`** (`t3_pop_fade.py:14`): a listing discount below −1000% would escape all buckets. Impossible in practice (verified 0 rows < −100%), but `-1e9` or explicit `-inf` would be cleaner and intention-revealing.
- **M5 — NaN pops silently dropped from T3 buckets** (`t3_pop_fade.py:27`): rows with NaN `adj_listing_gain_open` fall into no bucket and vanish without a count. Verified 0 such rows in trusted-MB today, but add a coverage line ("N with usable pop / N trusted") so a future gap is visible.
- **M6 — `run_layer3_report.py:31` subtitle is a pooled N** ("N = 2245 equity IPOs"): the methodology review (C7) asks for segmented counts so a pooled number doesn't anchor the reader. Low priority but trivially fixable.

---

## What was done well
- Spine edge-cases are clean: empty / all-NaN series → n=0 and None with no division-by-zero; `wilson_ci(0,0)=(None,None)`, boundaries p=0/p=1 clamp correctly to [0,1] with correct sign.
- `terminal_state` never drops delisted rows; `outcome_class==wipeout` is correctly authoritative; the band (lower=confirmed, upper=+unknown-reason) is exactly the must-fix #3 shape, and matches hand counts.
- T3 correctly avoids alpha entirely (the central trap) and the avoidance is test-enforced.
- T1's `N` column IS the maturity-gated N, so its guard is honest (unlike T5/T6/T9 — see C3).
- T6 computes its 5y matrix on the longterm cohort only and reports boom coverage as a note — the right structure, and now that boom-MB sector is 94% the C2-era concern is gone.
- Charts grey sub-floor bars and annotate N; no chart line switches cohorts (must-fix #2 letter honored).
