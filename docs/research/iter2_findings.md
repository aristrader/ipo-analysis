# Iteration 2 — DATA-HONESTY walk findings (2026-06-07)

Walker: iteration-2 data-honesty walker. App: http://localhost:8597 (Streamlit, headless chromium; iter-1 fixes live).
Method: for every on-screen number, computed ground truth via `PYTHONPATH=. .venv/bin/python` + pandas/engine and compared.
Ground-truth sources: `data/live/board.json`, `app/records/signals.json`, `app/records/families.json`,
`data/master/calls_ledger.csv`, `layer3.spine.load_substrate()`, `layer3.predictor.predict.predict()`,
`layer3.predictor.weights.oos_evaluate()`, `layer3.calls.td_offset`.
Note: Streamlit `st.dataframe` grids render to canvas (no text DOM; `browser_evaluate` denied) — those tables were
verified by (a) screenshot read-back where on-viewport and (b) byte-identical reproduction of the exact render code
path against the unchanged data file (deterministic ⇒ display == computed). Benign `/_stcore/health` 404s ignored.

## Per-check results

### CHECK 1 — HOME journey-card numbers
- live/upcoming: screen **"4 live · 1 upcoming"** vs board.json open=4, upcoming=1 → **MATCH**.
- records: screen **"102 signals · 12 validated"** vs signals.json len=102; chip_status==validated count=12
  (raw: validated 7 + in_score 5) → **MATCH**.
- graded: screen **"5093 calls graded (5166 total)"** vs ledger grade_status final(3523)+partial(1570)=5093,
  total 5166 → **MATCH** (iter-1 P1 graded-undercount fix confirmed live).
- "Needs attention" oldest ungraded forward call: screen **"UHM Vacation (EARLY_AVOID, 2026-06-04)"** vs ledger
  pending∧mode∈{live,gap_filled} sorted by call_date → UHM Vacation 2026-06-04 → **MATCH**.

### CHECK 2 — RECOMMENDATIONS track-record table + board calls
- Track-record groupby (call_type × mode) reproduced exactly in pandas: every (n / win% / median Δα1y / IQR) row
  matches (APPLY hist_sim n=175 win 53% med +6% IQR −30%…+57%; AVOID hist_sim n=170 win 66% med −28%;
  EXIT_REVIEW hist_sim n=112 win 62%; PERSIST_EXIT_LEAN hist_sim n=759 win 63%; TAKE_PROFITS hist_sim n=15
  win 67%) → **MATCH**.
- Modes pooled? **NO** — groupby keys on ["call_type","mode"]; never pooled. → **MATCH** (correct).
- Thin rows floored? **YES** — n<10 rows (APPLY/AVOID/TAKE_PROFITS backfilled n=0) render "N=0 — too few to say"
  via `ui.n_floor` (MIN_N=10). → **MATCH**.
- OPEN-board live calls + "why" strings: UHM Vacation/Vahh/Hexagon EARLY_AVOID, Genxai EARLY_APPLY, all live_score
  & flag strings identical to ledger rules_fired → **MATCH**.
- UPCOMING preview "Horizon Reclaim expected score ~71/100 (preview, N=50)" vs predict() = 71.2, n_cohort=50 → **MATCH**.

### CHECK 3 — TRACK RECORD page tables + OOS report card
- Table A (call_type × mode) renders identically to CHECK 2 (same code path + adds grade-mix col) → **MATCH**.
  On-viewport read-back confirmed: APPLY backfilled "N=0 — too few", APPLY hist_sim n=175 win 53% med +6%
  IQR −30%…+57% grade mix final:175,partial:5.
- OOS report-card TABLE (oos_table → W.oos_evaluate) values are correct by construction (reproduced:
  train≤2022/1y lift +22.6pp, train≤2021/1y +21.3pp, train≤2019/3y +68.3pp).
- **[P1] OOS report-card CAPTION understates the table it sits on.** track_record.py:133 caption reads
  *"Real edge at 3y (about +55pp); weak at 1y (+2-5pp)."* Ground truth: 3y OOS lift = **+68.3pp** (caption says
  ~55pp), 1y OOS lift = **+21.3 / +22.6pp** (caption says +2-5pp). screen(caption)=+55pp/+2-5pp, truth=+68.3pp/+21-23pp.
  A reader anchoring on the bold prose summary gets a materially wrong (4–10×-understated) read of the predictor's
  measured edge — a wrong number rendered as prose, directly contradicting the table beside it.
  Cause: hardcoded stale string at `app/screens/track_record.py:133`.

### CHECK 4 — IPO DETAIL scorecard vs engine
- **INE14OX01013 (Takyon Networks, SME, delisted=False, outcome=loser):** screen Combined 47/100, Wipeout-risk
  42/100 LOW, components Return 16 / Multibagger 71 / Downside-safe 31 / Wipeout-safe 100 / Liquidity 46 /
  Quality 73 / Tradeable up 69; "No validated wipeout red flags among the 3 checked"; ledger NEUTRAL.
  vs predict(): combined 47.1, risk 42.0/LOW, comps 16.1/71.4/30.7/100/46.0/72.8/68.6, n_flags 0, n_cohort 50.
  → **MATCH** (every value).
- **INE538H01016 (Shree Ashtavinayak Cine Vision, MB, delisted=True, outcome_class=wipeout):** screen Combined
  22/100, Wipeout-risk 45/100 LOW, comps Return 7 / Multibagger 26 / Downside-safe 0 / Wipeout-safe 100 /
  Liquidity 68 / Quality n/a / Tradeable up 74; "No validated wipeout red flags among the 1 checked".
  vs predict(): combined 21.9, risk 45.0/LOW, comps 7.3/25.5/0.2/100/68.0/None/73.5, n_flags 0 → **MATCH** (values).
- **[P1] DELISTED-BADGE — terminal/delisting status disclosed NOWHERE on the detail page.** (Resolves the iter-1
  open question.) INE538H01016 went to **liquidation (−100%, outcome_class=wipeout, delisted=True)** — facts present
  in the substrate row — yet the Verdict bar shows **"💀 Wipeout-risk 45/100 🟢 LOW ✓ VALIDATED"** and the scorecard
  shows **"✅ No validated wipeout red flags."** The header reads only "listed 2007-01-10"; no terminal/−100%/delisted
  note in ①Verdict, ②Full-picture, or ③Scorecard. The sole inferable hint is the ⑥ price chart ending in 2014.
  This is the data-honesty worst case: a true, decision-critical data field (`delisted`/`outcome_class`) is suppressed
  while the page actively renders a reassuring "LOW risk / no red flags" verdict that the realized outcome refutes.
  ipo_detail.py ①Verdict (lines 158-185) never reads `row['delisted']` or `row['outcome_class']`.

### CHECK 5 — Tracking "d21 read in ~Nd" (prophet #12, calendar-vs-trading-day)
- **[P3] d21/d90 milestone countdown uses a calendar-day approximation that drifts low.** recommendations.py:176-181
  uses `age_d=(today−listed).days` and `30−age_d` (d21) / `126−age_d` (d90). Empirically (Nifty calendar, 2023-24):
  21 trading days = **mean 31.5 cal-days** (range 29-36) and 90 td = **mean 134.5 cal-days** (128-139). So the d21
  read under-states remaining by ~1.5d and the d90 read by ~8.5d. Example: Aureate Tradde (listed 2026-06-05,
  age 2) shows "~28d"; a true-td anchor would be ~29-30d. NOT a data-from-file error and the figure is hedged with
  "~" + strikethrough; low-severity display approximation only. (`td_offset` can't compute these directly because the
  Nifty index file doesn't extend to June 2026 — confirming the calendar fallback is the live code path.)

### CHECK 6 — EVIDENCE / REGISTRY counts + rejected-only-in-graveyard
- Per-family validated/rejected rollups (Evidence Browser, grouped by `rec['family']`) reproduced via chip_status:
  e.g. Score components ✓3 ~3, F5 reference-points ✓1 ~1 ✗5, F7 ✓1 ✗1, N14 ✓2 ✗3 → **MATCH** to record-derived counts.
  Note: Evidence groups by the 44-value per-record `family` field; families.json (21 entries) is a coarser separate
  taxonomy — only used on HOME/registry as metadata, not as a contradicting on-screen number.
- Spot-checked 3 records' numbers (signals.json verbatim render): F7 disposition (cells 4/4, edge +2.6..+18.2pp),
  F5e capitulation (flag_rate 12%, bad 55% vs 13%) — F5e numbers also match the detail-page ⑥ caption
  ("~12% … 55% vs 13%") → **MATCH / internally consistent**.
- REJECTED items appear ONLY in graveyard surfaces: Evidence WHY-REJECTED tab + Registry §③ GRAVEYARD. Excluded
  from Recommendations (chip is per call_type) and from Detail ⑦Playbooks (`relevant()` returns False for rejected,
  ipo_detail.py:392) — confirmed on both detail pages (only ✓ VALIDATED playbooks shown) → **MATCH** (correct).
- **[P3] families.json metadata drift: sum(n_validated)=13 but record-chip validated=12.** Not shown as a number on
  any screen (HOME counts records, not families.json), so no on-screen wrong number — flagged as a latent
  cross-source inconsistency to reconcile.

### CHECK 7 — Chip audit (every chip vs registry standing)
All chips reconcile to the record status / signal registry standing → **MATCH**:
- Regime banner: tape F7 → **✓ VALIDATED**, crowding → **~ DISPLAY-ONLY** (matches registry: F7 validated,
  ctx crowding display-only); Nifty-3m labelled CONTEXT-only ✓.
- Recommendations: EARLY_APPLY/EARLY_AVOID → **⚠ THIN (forward-only)**; CLEARED_ISSUE/EXIT_REVIEW → **✓ VALIDATED**;
  PERSIST_EXIT_LEAN → **~ DISPLAY-ONLY**; TAKE_PROFITS → THIN(n=31). All match `_CHIP_FOR`.
- Detail scorecard: in-score comps (Return/Multibagger/Downside/Wipeout-safe + crowded_window) → **✓ VALIDATED**;
  display comps (Liquidity/Quality/Tradeable-up) → **~ DISPLAY-ONLY** — matches weights (0 ⇒ display).
- `chip_status` alias map is complete: all 6 raw statuses (rejected/validated/in_score/display_only/watchlist/parked)
  map cleanly; NO unknown-status fallthrough.

### CHECK 8 — As-of stamps + min-N floors
- As-of stamps: HOME ✓, Recommendations ✓, Track Record ✓ (regime banner stamp), IPO Detail ✓ (header asof line),
  Data & Methodology ✓ (data.py:38). **[P2] Registry and Evidence Browser have NO as-of stamp anywhere** — no
  substrate/ledger/board date, no freshness anchor for the governance records. Violates charter "as-of stamps on
  every screen." (registry.py / evidence.py never call a stamp helper or render_regime_banner.)
- Min-N floor: every statistical claim observed was ≥ MIN_N(10) or floored. Track-record n<10 rows → "too few".
  Detail outcome-breakdown / reach-ladder / analog-dist N were 35 and 49 (≥10). Cluster context peer counts
  (33; 10) are descriptive listings, not statistical claims, so not floored (acceptable). **No un-floored n<10
  statistic found.** → **MATCH** (floor verifiably enforced where stats are shown).

## Severity counts
- P0: 0
- P1: 2 — (1) OOS caption understates measured lift (+55pp/+2-5pp vs true +68.3pp/+21-23pp), track_record.py:133;
  (2) delisted/terminal status disclosed nowhere on IPO Detail (verdict shows "Wipeout-risk LOW / no red flags" on a
  liquidated −100% company), ipo_detail.py:158-185.
- P2: 1 — Registry + Evidence Browser missing as-of stamp.
- P3: 2 — d21/d90 calendar-day countdown drifts ~1.5d/~8.5d low (recommendations.py:176-181);
  families.json n_validated(13) vs record-chip validated(12) metadata drift (not on-screen).
- Total: 5 findings. Every reconciled on-screen NUMBER equals ground truth (all of CHECK 1-7's numeric values MATCH);
  the two P1s are a wrong PROSE summary and a SUPPRESSED true field — not a mis-rendered computed number.

## Worst 5 (data-honesty priority)
1. **[P1] Delisted/wipeout detail page shows "Wipeout-risk LOW / no red flags"** with no terminal disclosure
   (INE538H01016 went to liquidation) — actively misleads on the single most decision-critical fact.
2. **[P1] OOS report-card caption understates predictor edge** 4–10× (~+55pp/+2-5pp vs +68.3pp/+21-23pp),
   contradicting the table beside it.
3. **[P2] Registry & Evidence Browser have no as-of stamp** — governance records with no freshness anchor.
4. **[P3] d21/d90 milestone countdown uses 30/126 cal-days** vs true ~31.5/~134.5 — drifts low (~1.5d / ~8.5d).
5. **[P3] families.json sum(n_validated)=13 vs record-derived 12** — latent cross-source metadata drift.
</content>
</invoke>
