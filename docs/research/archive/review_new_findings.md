# Adversarial review — new Layer-3 findings (N2–N12, nonequity)

Scope: `layer3/findings/{n2_subscription,n3_demand_skew,n4_issue_size,n5_anchor,n6_valuation,
n7_fundamentals,n8_accrual,n9_zombie,n10_migration,n11_sc_divergence,n12_banker,nonequity}.py`,
verified against `layer3/spine.py`, `layer3/report.py` (`_guard_table`), `data/master/ipo_analysis.csv`.

Method: read each finding, ran each `compute()` and inspected the rendered (post-`_guard_table`) tables,
hand-recomputed cells from the substrate, and probed bucket edges / guard behaviour. Confirmed scale:
`alpha_*`, `return_from_listing_*`, `adj_listing_gain_open`, `current_return_from_issue` are FRACTIONAL
(0–1; median `alpha_1y` = −0.131), so the findings' `_p(x)=round(100*x,1)` is the correct conversion for
those. `sub_total_x`/`gmp_pct`/`ofs_pct`/`roe`/`margin` are 0–100 — none of the new findings multiply those
by 100, so no scale bug there.

## CRITICAL

### C1 — N3 / N5 / N6 print maturity-gated alpha cells the report guard CANNOT suppress (no N_1y/N_3y columns)
`n6_valuation.py:27-31`, `n5_anchor.py:27-32`, `n3_demand_skew.py:26-30`.

`_guard_table` (report.py:32-61) suppresses metric cells only by detecting **count columns** on the row.
N2, N4, N7 emit `N_1y`/`N_3y` next to their gated alphas, so the guard fires correctly. But **N3, N5, N6
emit only `N`** (the band size) and never the maturity-gated `N_1y`/`N_3y`. So `median_alpha_1y_%` /
`median_alpha_3y_%` — which are computed on `spine.maturity_gated(b, ...)`, a much smaller subset — are
printed as confident numbers even when that subset is far below the N=10 floor. The guard is blind to it
because it only sees the (large) band `N`.

Concrete nonsense that reaches the rendered report:
- **N6 MB "cheap vs sector" `median_alpha_3y_% = 313.5%`** — this is the median of exactly **N_3y = 2**
  observations (`alpha_3y` = 0.39 and 5.88 → median 3.135 → 313.5%). "in-line" 3y = NaN from **N_3y = 0**.
  Hand-verified against the substrate. Displayed unguarded because the table has no `N_3y`.
- **N5 SME "low/high anchor %" `median_alpha_3y_%`** (+38.4% / −1.3%) come from **N_3y = 7** each (below floor).
- **N3 SME "QIB-led" `median_alpha_3y_% = +10.0%`** comes from **N_3y = 6** (below floor).

Fix: in N3, N5, N6 add `"N_1y": len(g1)` and `"N_3y": len(g3)` to every row dict (exactly as N2/N4/N7 do).
The guard will then suppress the sub-floor alpha cells automatically. (Alternatively guard alphas inside the
finding with `spine.guarded(...)`, but matching the N2/N4/N7 pattern is cleanest.) N8 is structurally the
same (alpha cells, no N_1y/N_3y) but happens not to trip the floor in current data (smallest N_3y = 29) — add
the columns there too for robustness.

## IMPORTANT

### I1 — `_guard_table` overwrites the band/identity label of suppressed rows for EVERY new finding
`layer3/report.py:13-15` (`_ID_COLS`) vs the label columns the new findings use.

`_ID_COLS` (the whitelist of columns never suppressed) contains `bucket, listing_pop_bucket, ofs_bucket,
group, horizon, year, label, metric, segment, cohort, market_cap_class, mcap, sector, broad_sector`. But the
new findings name their identity column descriptively and **none of those names are in the whitelist**:
`sub_total_x_band` (N2), `qib_retail_skew` (N3), `issue_size_cr_band` (N4), `anchor_pct_tertile` (N5),
`pe_vs_sector` (N6), `tertile` (N7), `cash_vs_profit` (N8), `listing_class` (N10), `instrument_type`
(nonequity), `lead_manager` (N12). Result: when a row is sub-floor, the guard treats the label as a metric
and overwrites it with `insufficient (N=k)`, destroying the row's identity. Observed in the rendered tables:
- N4 SME: the `<25 / 25-100 / 100-500 ...` band labels become `insufficient (N=1)`, `insufficient (N=0)` …
- N10 MB(longterm): the `multibagger` row label becomes `insufficient (N=8)` — reader can't tell which class.

So in every finding, suppressed rows lose the one piece of info (which band) that makes the suppression
interpretable. Fix: add the new label columns to `report._ID_COLS` (or have findings standardise on a column
literally named `label`/`bucket`). Lowest-touch fix: extend `_ID_COLS` with the ten names above.

### I2 — N11 "small/micro caps" group pools MB + SME (violates the never-pool rule)
`n11_sc_divergence.py:33`. `df[df["market_cap_class"].isin(["micro","small"])]` mixes **688 SME + 292 MB**
rows into one "small/micro caps" group, then reports a single Nifty-vs-Smallcap divergence for the blend.
CLAUDE.md / KEY FACTS: "SME and MB never pooled." The finding does also show "all SME" and "all MB (control)"
separately, so the segmented numbers exist — but the headline pooled row blends the two segments' alphas and
should be split (`small/micro MB` vs `small/micro SME`) or dropped in favour of the already-present segment
rows. (Sign convention itself is correct: `divergence_pp = median(nifty) − median(smallcap)`, computed only on
rows where BOTH benchmarks are non-null via `pd.DataFrame({...}).dropna()` — verified.)

## MINOR

### M1 — N12 `_split_managers` over-splits banker names containing "," or " and "
`n12_banker.py:16-22`. Single names get shredded: `'SBI Capital Markets Ltd., Mumbai'` → `['SBI Capital
Markets Ltd.', 'Mumbai']`; `'A and B Securities'` → `['A','B Securities']`. This both invents phantom managers
and double-counts a deal. No phantom token currently crosses the `MIN_DEALS=15` floor (checked both segments),
so there is no visible impact today, and N12 is descriptive-only / not a score input — hence Minor. Still a
latent correctness bug; prefer splitting on `|`/`;` only, or a curated separator that isn't a name substring.

### M2 — N2 / N3 compute `cri` (current_return_from_issue) then never use it
`n2_subscription.py:24`, `n3_demand_skew.py:25`. Dead code; harmless. Remove.

### M3 — N4 `pct_2x_from_listing` denominator (rfl1 non-null) has no own count column
`n4_issue_size.py:24,31`. The 2x-rate is over `return_from_listing_1y` non-null, a different count than
`N`/`N_1y`. It is *currently* protected only because `N_1y` happens to track that non-null count closely
(e.g. MB ">10000": N_1y=8 suppresses the row, and the 2x denom is also 8). Fragile coincidence rather than a
guarantee. Optional: emit the 2x denominator as `N_2x` so the guard keys on the right count.

### M4 — N11 MB "control" diverges +14.9pp at 3y, contradicting its own "should be small" narrative
`n11_sc_divergence.py:44` caveat. Not a bug — at 3y Smallcap-250 fell harder than Nifty so MB looks better vs
smallcap (nifty −24.7 vs smallcap −39.6 → +14.9). Real data, but it undercuts the "control should diverge
little" framing; worth a sentence acknowledging the control isn't small at 3y.

## CHECKED AND CLEAN
- **Bucket edges MECE, right scale.** N2 bands `(s>lo)&(s<=hi)` partition `sub_total_x` exactly (MB 344=344,
  SME 739=739; no drop/double-count). Tertiles (N3/N5/N6/N7) use `<=q1` for bottom and `(>q1)&(<=q2)` for
  middle — boundary value lands in bottom only, no double-count. `_cls` thresholds in N10 are on the fractional
  scale (correct).
- **MB/SME split** enforced in N2–N10, N12 via `df[df["type"]==seg]` / `spine.segment(...,segment=seg)`.
  (Sole violation: I2.)
- **Single-regime flags accurate.** N2/N3/N5/N6 each carry an explicit "⚠ SINGLE-REGIME / boom-only / cannot
  be cross-regime validated" caveat and slice `cohort="boom"`. N7/N8 correctly labelled "not separately
  cross-regime-validated — descriptive." N10 holds cohort constant (longterm). Verified.
- **N9 zombie** uses `current_return_from_issue` (current STATE, not a maturity-gated horizon base rate) per
  spec; threshold −0.50 + `liquidity_flag=='low'` + alive. `bad_outcome = zombie + wipeout_lower`. Correct.
- **N10 migration** cohort held constant (longterm, 3y-matured), `unreliable_coverage` excluded, start=listing
  pop class, end=`return_from_issue_3y` class. Correct.
- **N8 accrual** red-flag = `operating_cf_yr3 <= 0 & pat_yr3 > 0` on rows where both known. Correct columns.
- **`proportion()` / NaN** handling: `wilson_ci` guards n=0; `proportion` drops NaN before `.astype(bool)`;
  `distribution` coerces+dropna. Sound.
- **Min-N suppression fires** when a count column is present and below floor (verified on N4 SME / N10 MB) —
  the C1/I1 defects are about *which* columns the guard can see / protect, not the suppression mechanic itself.

## CELLS RECOMPUTED BY HAND (match the code)
1. **N9 SME boom zombie** — N=884, zombie=157, **17.8%**. ✔ matches.
2. **N4 MB issue 500–2000 `median_alpha_1y_%`** — N=275, N_1y=237, **−11.1%**. ✔ matches.
3. **N8 SME loss-making `wipeout_lower_%`** — N=76, **6.6%**. ✔ matches.
4. **N6 MB "cheap vs sector" `median_alpha_3y_%`** — recomputed **313.5%**, and confirmed it is the median of
   only **2** observations → this is the evidence for C1.
