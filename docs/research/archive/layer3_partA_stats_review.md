# Layer-3 Part A — Statistical / output-number review

Skeptical audit of the **produced numbers** in the 8 Layer-3 findings (not the code paths — that is
reviewed separately). Question asked of every cell: is it plausible, internally consistent, and not
misleading? Substrate: `data/master/ipo_analysis.csv`, loaded equity-only = 2245 rows
(2296 total − 38 fpo − 7 reit − 6 invit). Recomputed against the raw substrate with pandas where noted.

Run: `PYTHONPATH=. python run_layer3_report.py` → `report/layer3_partA.html` (8/8 findings, clean).

---

## CRITICAL (wrong or actively misleading)

### C1 — T5 (OFS gradient) is broken: unit mismatch silently drops ~70% of rows and empties every non-zero bucket
**Finding/cells:** `layer3/findings/t5_ofs.py`, both tables (MB longterm, SME longterm), every bucket except "0% (all fresh)".

`ofs_pct` in the substrate is stored as a **percentage on a 0–100 scale** (median 6.1, mean 19.9,
max 100.0; 695 rows are exactly 0, 134 are exactly 100, 1544 rows are > 1). But the T5 bucket edges
treat it as a **fraction 0–1**:
```python
BUCKETS = [("0% (all fresh)", -0.01, 0.001), ("0–25%", 0.001, 0.25), ("25–50%", 0.25, 0.50),
           ("50–75%", 0.50, 0.75), ("75–100% (mostly OFS)", 0.75, 1.0001)]
```
Consequences in the published table:
- The "0%" bucket matches `ofs_pct <= 0.001` → only the 695 true-zero rows.
- "0–25%" matches `(0.001, 0.25]` → essentially nothing (only the 2 rows with ofs between 0 and 1).
- **Every row with ofs_pct > 1 (i.e. all 1544 real OFS IPOs) falls outside ALL buckets and is silently dropped.**

That is why the published table shows N=269 / 0 / 0 / 1 / 0 (MB) and N=210 / 1 / 0 / 0 / 0 (SME):
the entire dose-response curve — the whole point of the finding — is missing, and the one or two
non-zero rows shown (e.g. SME "0–25%" median 3y alpha −40.8 on N=1, MB "50–75%" +42.0 on N=1) are
single-stock noise presented as bucket statistics.

**Corrected (bucketing on the 0–100 scale), longterm cohort:**

| seg | bucket | N | N_mat | median 3y alpha % | wipeout lo–hi % |
|---|---|---|---|---|---|
| MB | 0% | 269 | 245 | −68.9 | 30.5–39.8 |
| MB | 0–25% | 55 | 50 | −60.2 | 25.5–32.7 |
| MB | 25–50% | 48 | 45 | −33.7 | 18.8–27.1 |
| MB | 50–75% | 30 | 29 | −27.5 | 3.3–20.0 |
| MB | 75–100% | 68 | 64 | **−11.2** | **1.5–4.4** |
| SME | 0% | 210 | 190 | −38.4 | 6.2–15.7 |
| SME | 0–25% | 233 | 215 | −50.8 | 10.7–19.7 |
| SME | 25–50% | 33 | 32 | −14.8 | 3.0–9.1 |
| SME | 50–75% | 15 | 14 | +12.2 | 20.0–26.7 |
| SME | 75–100% | 27 | 27 | −37.6 | 3.7–14.8 |

The corrected MB result is a clean, monotone, and *counter-intuitive* gradient (see Interesting #1).
The bug doesn't just lose precision — it deletes the finding and replaces it with N=1 artifacts.
**Fix:** divide `ofs_pct` by 100 before bucketing (or rescale the bucket edges to 0–100). Until then
the T5 table must not be shown.

### C2 — T6 sector tables show sub-floor sectors the caption claims are suppressed (one row ranked #1 on a single stock)
**Finding/cells:** `layer3/findings/t6_sector.py`, both sector tables. Caption asserts *"Sectors with N<10 are suppressed."*

The N-guard is applied to the *whole segment* (`if len(sub) < MIN_N_HINT: continue`) and to the
*scatter chart* (`r["N"] >= MIN_N_HINT`), but **`_sector_rows()` returns every sector** — there is no
per-sector suppression in the tables. Sub-floor sectors actually shown:
- **MB:** Energy N=5, Telecommunication N=2, Utilities N=9.
- **SME:** Energy N=2 (N_matured=**1**), Diversified N=3, Telecommunication N=4, Utilities N=5.

Because the SME table is **sorted by median alpha descending**, the SME Energy row — **median 5y alpha
+628.8% computed on a single matured stock** — is printed at the **top of the table**, reading as the
best SME sector. MB Energy (N=5, +24% wedge between its lower/upper wipeout band) sits at rank #2.
The scatter chart correctly excludes these, so the table and the chart of the same finding disagree.
This is misleading: a reader scanning the matrix sees one-stock sectors leading the ranking under a
caption that promises they were removed. **Fix:** filter `_sector_rows` to `N >= MIN_N_HINT` (or guard
each cell with `spine.guarded`), matching the caption and the chart.

---

## IMPORTANT (defensible numbers, but real interpretation / presentation risk)

### I1 — T2/T1 "SME is safer than Mainboard on wipeout" is very likely an illiquidity / under-capture artifact, not flagged as such
**Finding/cells:** T2 survival (all SME rows read below MB at every year), T1 lifetime band
(SME 3.8–7.6% vs MB 12.8–17.7%).

The mechanics are sound (band lower≤upper everywhere; N_matured monotone-decreasing 739→368 MB,
1203→153 SME). But the headline that SME wipes out *less* than MB is suspect:
- **50% of SME rows (708/1404) are `liquidity_flag = low`** vs only 10% of MB (87/841). A thinly-traded
  SME that has effectively died can sit circuit-locked / stale-printed and never register a ≤ −90%
  terminal return, so the price-based wipeout label under-counts SME deaths.
- For SME wipeouts, only **22 of 54 are confirmed delisted**; 32 are price-based. SME delisting-feed
  capture is known-weak (CLAUDE.md / data_review). So both legs of the wipeout definition under-detect
  SME failure relative to MB.
- SME `longterm` only starts in **2012** (platform launch) vs MB from 2006, so SME longterm IPOs are
  structurally younger and have had less time to die. T2's per-year maturity-gating mitigates this, but
  the lifetime band in T1 does not age-normalise.

None of the three T2 caveats nor the T1 caveats warn that the MB-vs-SME wipeout *ordering* is biased by
SME illiquidity/under-capture. A reader will take "SME 3.8% vs MB 12.8%" at face value. **Recommend** a
caveat: SME wipeout is a *lower bound that is itself downward-biased* by illiquidity and weak SME
delisting capture; do not read SME < MB as "SME is safer."

### I2 — T9 prints a 5-year boom number on N_matured = 5, with no per-cell suppression and an N column that hides it
**Finding/cells:** `layer3/findings/t9_profitable.py`, boom "loss-making at IPO" row, `median_alpha_5y_%` = **+36.7**.

The table's N column shows the *group* size (boom loss-making N=64), but the 5y median is maturity-gated
to only the IPOs old enough for a 5y horizon: **N_matured = 5** (below the MIN_N=10 floor). T9 applies no
per-horizon guard, so +36.7% is printed as if it carried the row's N=64. This produces the eye-catching
but unsupported reading "boom loss-makers beat profitable companies at 5y (+36.7% vs −45.9%)" off five
stocks. (The profitable boom 5y cell is itself only N_matured=64 — thin but above floor.) **Fix:** guard
each horizon cell with `spine.guarded(...)` / show the per-cell matured N, and suppress boom-5y here just
as T1's caption intends. The longterm 5y comparison (profitable −35.2 on N=438 vs loss-making −70.1 on
N=47) is the genuinely supported version and has the right sign.

### I3 — T3 SME ">100% pop" 3-year median (+53.9%) is a median over a barbell; reads as "huge pops recover" but hides a 50/50 split
**Finding/cell:** T3 table, SME `>100%` bucket, `fwd_ret_from_listing_3y_%` = +53.9 on `N_3y` = 18.

The 18 underlying 3y returns are bimodal: nine are deep losses (−21% to −82%) and nine are large
winners (+36% to +1795%). The median (+53.9%) lands on the upper cluster and reads as "the biggest SME
pops keep rising at 3y," contradicting the fade gradient the finding is built to show — when the reality
is a coin-flip with a fat right tail on N=18. N_3y=18 is at least shown in the table (good), but the
median is the wrong summary for a barbell. **Recommend** flagging this cell as non-representative (show
p10/p90 or the share negative), or suppress at N<20. The MB pop-fade gradient is clean and not affected.

---

## MINOR

### M1 — T1 caption is stale/incorrect about which cells are suppressed
T1 caption: *"Sub-floor cells (N<10) are suppressed — e.g. boom 5y."* But boom 5y is **not** suppressed:
MB boom 5y N=32 and SME boom 5y N=39 are both shown (and both above the floor). No boom cell in T1 is
actually below the floor, so nothing is suppressed at all. Harmless to the numbers, but the caption
misdescribes the table. Fix the example or drop the clause.

### M2 — T8 "investable subset" SME N drops sharply but is unlabeled as a sample shift
T8 SME winners go from N=661 (all) to N=447 (investable) — a 32% drop, because half of SME is
`liquidity_flag=low`. The drawdown numbers barely move (−63.7 → −60.5 median), which is reassuring, but
the table doesn't note that the investable SME winner sample is a materially different (larger-cap,
more-liquid) population. Minor; the two rows invite a direct comparison that is partly apples-to-oranges.
Signs are all correct (drawdowns negative, min −100%, none positive).

### M3 — T6 caption "~94% MB coverage" vs boom SME sector coverage 32.7%
The boom-coverage table correctly shows SME sector coverage at only 32.7% (vs MB 94.3%), but the
narrative/caveats emphasise the 94% MB figure; a predictor leaning on boom SME sector will be working off
one-third coverage. Worth stating the SME gap explicitly. Numbers themselves are fine.

---

## Checks that PASSED (numbers verified sound)

- **T1 internal consistency & hand-recompute.** MB boom 1y recomputed by hand from the substrate:
  N=277, median alpha −10.7%, p10 −55.0, p90 +86.6, %positive-alpha 44.0, %2x 20.2, %below-issue 33.2 —
  **exact match** to the published cell. %positive-alpha (44) and %below-issue (33) are not contradictory:
  only 2/277 rows are simultaneously alpha-positive and below issue (a stock can beat a falling Nifty while
  still under its IPO price). alpha and return_from_issue are both stored as fractions and scaled ×100
  consistently.
- **T3 uses RAW return-from-listing, not alpha** (confirmed in code and values) — correctly avoiding the
  pop-already-in-alpha double count. The **allottee-vs-secondary wedge is directionally right**: in the MB
  >100% bucket allottees keep +87.7% (from issue) while listing-day buyers get −26.3% (from listing). The
  MB pop-fade gradient is monotone and believable.
- **T2 band mechanics:** lower ≤ upper in every cell; N_matured strictly decreases with year in both
  segments; the SME year-10 cliff (494→153) is a true maturity artifact of the 2012 SME-platform start,
  not an error.
- **Cross-finding wipeout reconciliation:** terminal_state = {alive 1986, wipeout 162, alive_delisted_unknown
  94, payout 3}; outcome_class=='wipeout' = 162 (defined as current_return ≤ −90%, confirmed: min −1.0,
  max −0.90). T1's lifetime lower band sums back to these 162 and the upper band adds the 94 unknown
  delistings — internally consistent. 65% of the 162 wipeouts are confirmed delisted; the rest are
  price-based near-zeros, which is honest.
- **T7 selection-bias audit (N12)** is well constructed and not misleading: it explicitly shows the
  excluded low-quality rows carry 20.6–32.5% wipeout vs 5.9–9.4% for the kept rows, correctly warning that
  base rates are *optimistically* biased. Good practice.
- **T8 sign checks** all pass; drawdowns negative, bounded at −100%, none positive.
- **T9 longterm direction** correct (profitable > loss-making at every horizon, sign-consistent).
- **T7 coverage table** denominators reconcile with the substrate (boom long-horizon N collapses as
  expected; longterm carries 3y/5y/10y).

---

## Genuinely interesting robust results worth surfacing

1. **(After fixing C1) Mainboard OFS is a clean *inverse* signal.** Once bucketed correctly, MB median 3y
   alpha rises monotonically with OFS: 0% → −68.9, 0–25% → −60.2, 25–50% → −33.7, 50–75% → −27.5,
   75–100% → **−11.2**, and wipeout falls from 30.5% to **1.5%**. The naive "insiders cashing out = bad"
   hypothesis is *reversed* for Mainboard — high-OFS MB IPOs are disproportionately clean
   PE/large-cap exits (the confound the caveat names), and they are the *safest, best* MB sub-group on a
   3y view. This is a strong, decision-relevant pattern that the bug was entirely hiding.

2. **The listing-pop fade and the allottee/secondary wedge are real and quantified.** For Mainboard, the
   secondary buyer's forward 1y return is negative in every pop bucket and *most* negative in the biggest
   pops (>100% pop → −26.3% at 1y), while the allottee who got the IPO keeps +87.7%. Clean evidence that
   chasing a hot listing at the open is a losing base rate, separate from the allottee's gain.

3. **Survivorship-honest downside is large for Mainboard and rises with age.** Maturity-gated cumulative
   wipeout for MB climbs 14.6%→28.0% (lower bound) from year 1 to year 10, with the upper band at 38.3%
   by year 10 — i.e. roughly a quarter to a third of Mainboard IPOs are near-total losses within a decade.
   This is robust (price-based + delisting, banded) and is the kind of number a buyer never sees in
   survivor-only IPO marketing. (Caveat: the *SME-looks-safer* comparison is not robust — see I1.)
