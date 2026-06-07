# App Screens — implementer spec (v1, 2026-06-07)

Screen-by-screen build spec for the Phase-2 app. Implementer target: **Streamlit `st.navigation` /
`st.Page` multipage**, native widgets + at most **two** Altair/Plotly charts. Reader-only over the
engine, the ledger, and the live board. Grounded in `app_phase2_design.md`,
`2026-06-07-recommendations-app-design.md`, `2026-06-07-calls-engine-design.md`, and the current
`app.py`. NOT financial advice.

## Design language (apply to every screen)
- **Bloomberg-for-one-person.** Industrial/utilitarian terminal: information-dense, decision-first,
  honest about uncertainty. Color is SIGNAL, never decoration. White/paper background, near-black text,
  one monospace accent face for numbers/IDs (`st.markdown` with a tiny CSS `<style>` block injected once
  in the entry file — the only CSS allowed; no other client-side JS).
- **Trust chips — one shared helper `chip(status)`** (put in `app/ui.py`, import everywhere). Exactly four:
  `✓ VALIDATED` (green) · `~ DISPLAY-ONLY` (amber) · `⚠ THIN / HYPOTHESIS` (orange) · `✗ REJECTED` (grey,
  graveyard only). Rendered as a small inline `st.markdown` badge. **Every claim-bearing element carries one.**
  Rejected ideas NEVER get a recommendation/action surface — they appear only inside the graveyard.
- **Mode labels always visible.** Any ledger-derived number shows its `mode` mix
  (`live / gap_filled / backfilled / historical_sim`) as a small caption or a stacked count — never hidden.
- **Stat display rules (hard):** show **N** on every statistic; **min-N floor** = `config.MIN_N_HINT`
  (below it, render "too few to say — N=k", never a number); **distributions over means** (P10/median/P90
  or outcome buckets, never a lone mean — and where a mean is shown, the median sits beside it).
- **"As-of" everywhere.** Substrate `AS_OF_DATE`, ledger `graded_at` max, board `fetched_at`.
- **Lazy price loads.** Per-ISIN `data/prices/<isin>.csv` read ONLY on the IPO Detail Page, cached, and
  downsampled to weekly for multi-year charts.
- **Caching:** `@st.cache_data` on substrate / ledger / board / backtests / registry records; `predict()`
  cached keyed on the query dict; price files cached keyed on ISIN.

## Navigation (entry file `app.py` → `st.navigation`)
```
HOME                              app/pages/0_home.py
DECIDE  ▸ Recommendations         app/pages/1_recommendations.py   (DECIDE landing surface)
        ▸ IPO Detail              app/pages/2_ipo_detail.py        (drill-down; ?isin= query param)
LEARN   ▸ Evidence Browser        app/pages/3_evidence.py
        ▸ Signal Registry         app/pages/4_registry.py
        ▸ Explorer                (port existing tab — out of scope here)
MONITOR ▸ Forward-Test / Track    app/pages/5_track_record.py
        ▸ Backtester              (port existing tab — out of scope here)
DATA    ▸ Refresh / Methodology   (port existing sidebar)
```
Persistent **regime banner** (below) renders at the top of HOME, Recommendations, and Track-Record.
All cross-links land on **IPO Detail** via `st.page_link(..., url="?isin=<isin>")`.

---

## Screen 1 — HOME

**Purpose.** Orient in one glance: market climate now, the three journeys, what needs attention this week.

**Layout (text wireframe):**
```
┌─ REGIME BANNER (persistent component) ──────────────────────────────────────┐
│ Nifty 3m: +4.2%   |   IPO tape (F7): COLD ✓   |   crowding: 38th pctl  ~     │
│ → verdict: "SELECTIVE"            as-of 2026-06-07 · ledger graded · board 09:12│
└─────────────────────────────────────────────────────────────────────────────┘
TITLE: Indian IPO Analysis — research terminal      caption: not financial advice

┌ DECIDE ───────┐ ┌ LEARN ────────┐ ┌ MONITOR ──────┐    (3 st.columns journey cards)
│ Recommendations│ │ Evidence (8×26)│ │ Track record  │
│ N live · N up  │ │ Signal registry│ │ N calls graded │
│ [open →]       │ │ [browse →]     │ │ [open →]       │
└────────────────┘ └────────────────┘ └────────────────┘

NEEDS ATTENTION (this week)   — st.container, list rows, each → IPO Detail
 • windows OPEN this week (N)        from board.json open[]
 • unlocks / d21 / d90 in ≤14d (N)   from ledger anchors
 • forward-test age flag (N)         oldest ungraded live call
```
**Components & data sources:**
- *Regime banner* — `layer3.context.nifty_mom_3m(today)`; tape state F7 = `board.json.regime.tape_state`
  if present else recompute `crowded_window`-style climate (cached); crowding pctl from board header.
  One-line verdict ("ENGAGE / SELECTIVE / WAIT") is the board's `regime.verdict`. Chips: Nifty 3m bare
  (context only, no chip — F7 mom rejected as a signal); tape `✓ VALIDATED` (F7 cross-regime); crowding
  `~ DISPLAY-ONLY` (crowded_window folded but display the climate read). **As-of stamps on the banner.**
- *Journey cards* — counts: live/upcoming from `board.json`; findings/hypotheses counts from registry
  records; graded-call count from `calls_ledger.csv`. `st.page_link` per card.
- *Needs-attention strip* — board `open[]` filtered to close_date within 7d; ledger rows whose
  `call_date` is a +21td/+90td/ex-date anchor within 14d ahead (pure date math); oldest live call with
  `grade_status=pending`. Each row chip = the call's own trust chip.

**Empty/degraded:** no board.json → banner shows "live board unavailable — fetched: never" + regime from
substrate only; needs-attention renders "nothing needs attention right now" (no padding).

---

## Screen 2 — RECOMMENDATIONS  (the centerpiece, DECIDE landing)

**Purpose.** The standing answer to "an IPO is in front of me — what do I do?", as a dated, graded ledger
of calls. Pure reader of `data/master/calls_ledger.csv` + `data/live/board.json`. No engine calls at render
(except cached `predict()` for upcoming previews, and even those read cached PIT scores where available).

**Layout (text wireframe):**
```
┌─ HEADER STRIP ──────────────────────────────────────────────────────────────┐
│ ledger graded to 2026-06-06 · board fetched 2026-06-07 09:12 · [Refresh]      │
│ REGIME BANNER (same component as HOME)  → one-line verdict: SELECTIVE         │
└─────────────────────────────────────────────────────────────────────────────┘

🔴🟢 LIVE & UPCOMING BOARD
 ┌ OPEN now ───────────────────────────────────────────────────────────────┐
 │ ACME Foods (SME)   call: AVOID ✗flags    EARLY(day1): EARLY_AVOID ⚠       │
 │   why: score_q=1; n14_flags=2; tape=cold          closes in 1d  [detail →]│
 └───────────────────────────────────────────────────────────────────────────┘
 ┌ UPCOMING ────────────────────────────────────────────────────────────────┐
 │ Beta Logistics (MB)  expected score ~ 58/100 (preview)  opens 2026-06-10  │
 │   preview only — no call until close_date            ⚠ HYPOTHESIS  [detail]│
 └───────────────────────────────────────────────────────────────────────────┘

👀 TRACKING (recently listed)
 │ Gamma Tech (MB) listed 2026-05-20 · d+12 → d21 persistence read in 9d ~    │
 │ Delta Mfg (SME) listed 2026-03-01 · d+66 → d90 capitulation check in 24d ✓ │

🚨 ALERTS (≤30d old, not aged out)
 │ EXIT_REVIEW  Epsilon Ltd  fired 2026-05-30 (d90 capitulation)  ✓ VALIDATED │
 │ TAKE_PROFITS Zeta Corp    fired 2026-06-02 (bonus ex-date)  ~ VALIDATED-THIN│

📋 TRACK RECORD  (recomputed from the ledger at render)
 │ per call_type: n · win% · median Δalpha vs counterfactual · BY MODE         │
 │ (table; thin rows show "N=k — too few" not a number)                        │
```
**Components & data sources:**
- *Header strip* — `graded to` = `max(ledger.graded_at)`; `board fetched` = `board.fetched_at`; Refresh =
  button that shells `run_refresh.py` final phase (same pattern as the existing sidebar refresh, wrapped in
  try/except). Regime banner reused.
- *Live & upcoming board* — `board.json.open[]` joined to ledger rows where `call_type ∈
  {APPLY,AVOID,NEUTRAL, EARLY_*}` and `call_date` matches the issue's close/open. Card fields:
  name/type, the call_type (chip: APPLY/AVOID/NEUTRAL `✓ VALIDATED` — score+N14 are validated; EARLY_*
  carries `⚠ THIN / HYPOTHESIS` — forward-only until day-wise data exists), `rules_fired` rendered as the
  "why", days-to-close from `close_date`, `st.page_link` to detail. `upcoming[]` shows
  `expected score ~XX/100` from cached `predict()` on the previewed query (chip `⚠ HYPOTHESIS` — preview,
  not a call). **NO subscribe/AVOID call until the close_date anchor — preview only.**
- *Tracking* — ledger `TRACK` rows (anchor=listing_date) within ~120d; day counter = `today − listing_date`
  in trading days; show the next milestone (d21 persistence `~ DISPLAY-ONLY` per path_ratio conditioning;
  d90 capitulation `✓ VALIDATED`). Link to detail.
- *Alerts* — ledger rows `call_type ∈ {EXIT_REVIEW, CLEARED_ISSUE, PERSIST_EXIT_LEAN, TAKE_PROFITS}` with
  `call_date ≥ today−30d`. Chips: EXIT_REVIEW/CLEARED_ISSUE `✓ VALIDATED` (F5e capitulation, no look-ahead);
  TAKE_PROFITS `⚠ THIN / HYPOTHESIS` labeled **VALIDATED-THIN (n=31)**; PERSIST_* `~ DISPLAY-ONLY`.
  Each alert shows `rules_fired` + link.
- *Track record* — group ledger by `call_type` AND `mode`; per group compute `n`, `win_rate` (per the
  call's win definition: APPLY/EARLY win = positive alllottee alpha vs segment median; EXIT_REVIEW win =
  fwd alpha < segment median; TAKE_PROFITS win = fwd 3m alpha < 0), `median Δalpha vs counterfactual`
  (distribution, not mean — show median + IQR). **Split by mode is mandatory** so evidence strength is
  visible (live/gap_filled = forward truth; backfilled = OOS-ish; historical_sim = dress rehearsal). Rows
  with `n < MIN_N_HINT` render "N=k — too few to grade". All numbers recomputed at render, never hardcoded.

**Empty/degraded:** each section renders "none right now" rather than padding (spec rule). No ledger file →
whole page shows "calls engine not yet run — `python run_calls.py`". Board missing → board sections show
"live board unavailable" but ledger-derived tracking/alerts/track-record still render. Ungraded calls show
`grade_status` (pending/partial) instead of a fake number.

**Traceability (acceptance):** every card → its `rules_fired` → a Signal-Registry / Evidence-Browser entry
via `st.page_link`. Never show a call whose rule is in the REJECTED set.

---

## Screen 3 — IPO DETAIL PAGE  (the hub; one template, NEW and HISTORICAL)

**Purpose.** "Why this call?" / "what do I do with this IPO?" — the full decision read for one ISIN.
Route: `?isin=<isin>`; for a not-yet-listed query, accept the session-state query dict instead.
Engine: `r = predict(query_or_row, df=load_df(), profile=...)` (cached). Eight sections, vertical, in the
order a decision-maker reads. New IPOs degrade gracefully: analog-EXPECTED values stand in where realized
would be, **labeled "expected"**.

```
HEADER: ACME Foods · SME · listed 2024-08-12 · ISIN ...   [profile ▾]  as-of …

① VERDICT BAR
   COMBINED 58/100 (data_informed)   |   💀 WIPEOUT-RISK 71/100  🔴 HIGH
   ledger call (if any): AVOID ✗  fired 2024-08-09 · why: score_q=1;n14_flags=2

② THE FULL PICTURE — what happened to the N most-similar past IPOs (by 3y, from issue)
   [Doubled+ 18%] [Up 20–100% 22%] [≈Flat ±20% 19%] [Down<−20% 41%]   N=… 
   Best P90 +210%   Median −9%   Worst P10 −78%      terminal: dead-money 17% · wipeout 8–14%

③ SCORECARD  (8 components; w0 ones tagged "(display)")
   Return · Multibagger · Downside-safe · Wipeout-safe | Liquidity(w0) Quality(w0)
   Tradeable-up(w0) · + WIPEOUT RED-FLAG badges (tiny-sales / loss-making / obscure-banker)

④ CLUSTER CONTEXT
   its competitive window (same-segment IPOs ±N days) · GMP rank within cluster

⑤ EVENT CALENDAR
   close → listing → d21 (persistence) → d90 (capitulation check) → corp-action ex-dates
   F1c anchor-unlock rows = INFORMATION ONLY (no edge chip — falsified)
   corp-action ex-date rows carry a TAKE-PROFITS marker ⚠ VALIDATED-THIN (F10)

⑥ PATH vs REFERENCE LEVELS   ← Altair chart #1
   price + issue-price line + listing-day-high line; reclaim/breakout status; reach ladder
   🚩 CAPITULATION BADGE if never closed above issue in td 1–90 (F5e) ✓ VALIDATED

⑦ PLAYBOOKS THAT APPLY
   registry filtered by applicability predicate · payoff vs buy-and-hold · trust chip each

⑧ COMPARABLES TABLE
   r["named_analogs"] — the closest past IPOs, linked to their own detail pages
```
**Components & data sources:**
- ① Verdict bar — `r["scorecard"]["combined_score"]` + profile; `r["risk_assessment"]["risk_score_0_100"]`
  + `risk_band`. Ledger call line: lookup `calls_ledger.csv` by isin (latest APPLY/AVOID/NEUTRAL) →
  call_type chip + `rules_fired`. Combined score chip `~ DISPLAY-ONLY` (in-sample/indicative ranking, per
  the locked caveat); wipeout-risk chip `✓ VALIDATED` (N14 flags). For a NEW IPO with `n_cohort <
  MIN_N_HINT`, replace the score with "INSUFFICIENT analogs (N=k)".
- ② Full picture — `r["outcome_breakdown"]` (buckets, P90/median/P10, terminal dead-money +
  `terminal_wipeout_band_%`). Distribution bar of analog alpha via `spine.alpha_series(
  spine.maturity_gated(cohort,h), h)` (reuse the existing `st.bar_chart` block — NOT one of the two
  Altair charts). Chip `✓ VALIDATED` (base rates / barbell are headline cross-regime). SME dead-money rule
  caption when SME and dead-money ≥5% (reuse existing copy).
- ③ Scorecard — `r["scorecard"]["components"]` + `["weights"]`; w0 components tagged "(display)". Wipeout
  badges from `r["risk_assessment"]["flags"]` + `per_flag` with/without base-rate table. Component chips:
  return/multibagger/downside/wipeout-safe `✓ VALIDATED` (in-score, OOS-tested); liquidity/quality/
  tradeable-up `~ DISPLAY-ONLY`.
- ④ Cluster context — a cluster helper: same-`type` IPOs with `open_date` within ±N days; rank this IPO's
  `gmp_pct` within the cluster. Works on historical clusters now. Chip `~ DISPLAY-ONLY` (cluster framing is
  descriptive). Empty → "no cluster peers in window".
- ⑤ Event calendar — pure date math: close_date, listing_date, listing+21td, listing+90td (via Nifty
  trading calendar), and corp-action ex-dates from `data/reference/corp_actions.csv` (match by SYMBOL,
  `ex_date ≤ listing+365d`). Dose from `anchor_allocation_cr` where present, else "dose: unknown" (never
  fake). Anchor-unlock rows = INFORMATION ONLY, no chip (F1 falsified). Corp-action rows get a
  **TAKE-PROFITS** marker, chip `⚠ THIN / HYPOTHESIS` labeled VALIDATED-THIN (F10). d90 row chip
  `✓ VALIDATED` (F5e). Verify anchor share present per row before showing dose.
- ⑥ Path vs reference — **Altair chart #1.** Lazy-load `data/prices/<isin>.csv`, downsample to weekly for
  >1y span; overlay two `hline`s: `issue_price_adj` and listing-day high. Reclaim/breakout status +
  `r["reach_curve_h"]` ladder. **🚩 CAPITULATION badge** (F5e): compute from the loaded price series —
  flag if the stock never closed above `issue_price_adj` across trading days 1–90 (12% of IPOs →
  bad-outcome 55% vs 13%). Chip `✓ VALIDATED` (cross-regime, no look-ahead). NEW IPO → "expected path"
  framing or hide the chart (no price file yet) and label "expected" on reach ladder.
- ⑦ Playbooks that apply — registry records filtered by each record's `applies_predicate` against this
  row/query; render payoff grid vs buy-and-hold; each playbook its own trust chip (from the record's
  `status`). REJECTED records are never matched here. Empty → "no validated playbook applies to this IPO".
- ⑧ Comparables — `r["named_analogs"]` dataframe; each row links to that ISIN's detail page.

**Empty/degraded:** missing price file → hide ⑥'s chart, keep reach ladder labeled "expected"; missing
fundamentals → scorecard components show "n/a", risk shows "not assessed — unknown ≠ safe"; `n_cohort` thin
→ banner-level INSUFFICIENT warning. `listing_metrics_status == unreliable_coverage` → exclude from
listing-anchored reads (existing convention).

---

## Screen 4 — EVIDENCE BROWSER  (Family → Hypothesis → 3-layer tabs)

**Purpose.** "What does the research say?" — browse the 8 families × 26→50 hypotheses as DATA RECORDS,
graveyard first-class. Generic renderer over hypothesis records (`docs/research/*` verdict docs +
`rules/index.md` distilled into structured records under `app/records/` — implementer builds the loader;
records carry `{id, family, tier, mechanism, status, existence{}, magnitude[], playbook{}}`).

**Layout:**
```
LEFT: family index (8 rows)         RIGHT: selected family → hypothesis list
  Family · status rollup (✓/~/⚠/✗ counts) · tier filter · status filter
  click a hypothesis → its page:

  ┌ HYPOTHESIS PAGE — tabs in protocol order ────────────────────────────────┐
  │ [EXISTENCE]  [MAGNITUDE]  [PLAYBOOK]                                       │
  │ EXISTENCE: plain-English verdict + chip · FALSIFIER & PLACEBO result       │
  │            PROMINENT · cross-regime ✓ / OOS chips · N                      │
  │ MAGNITUDE: dose-response table(s) — distributions, min-N per cell          │
  │ PLAYBOOK : the WHOLE pre-declared grid (never best-cell-only) ·            │
  │            payoffs vs buy-and-hold · FAILURE CELLS block ·                 │
  │            "applies to N live IPOs →" link (filters Recommendations)       │
  └───────────────────────────────────────────────────────────────────────────┘
  GRAVEYARD: same template + a "why rejected / DO-NOT-RETEST" panel (✗ chip)
```
**Components & data sources:**
- *Family index* — records grouped by `family`; status rollup = chip counts; `st.selectbox`/`st.radio`
  tier + status filters. Graveyard = the `status==REJECTED` view of the same records (e.g. dip-buy, F1
  anchor-unlock, F5a/c/d, contrarian-entry, banker-alpha, the 48-batch rejections).
- *Existence tab* — `record.existence{verdict, falsifier, placebo, cross_regime, oos, n}`; falsifier &
  placebo rendered PROMINENT (the discipline is the point). Chip from `record.status`.
- *Magnitude tab* — `record.magnitude[]` dose-response tables; every cell shows N; cells under MIN_N_HINT
  suppressed. Distributions, not means.
- *Playbook tab* — `record.playbook{grid, payoffs, failure_cells, applies_predicate}`; render the FULL
  grid + a dedicated FAILURE CELLS block; "applies to N live IPOs" computes `applies_predicate` over
  `board.json` + recent ledger, links to a filtered Recommendations view.

**Empty/degraded:** family with no records yet → "no hypotheses recorded for this family"; a record missing
a layer → that tab shows "not computed for this hypothesis" (never fabricate a dose-response).

---

## Screen 5 — SIGNAL REGISTRY

**Purpose.** The single navigable landscape of every tested signal and its verdict — in-score /
display-only / watchlist / GRAVEYARD — so nothing gets re-tested blindly. Renders the
`rules/index.md` tested-signal registry as a structured, filterable table (distill into `app/records/`
registry records; implementer builds the loader).

**Layout:**
```
FILTERS: state [IN-SCORE | DISPLAY-ONLY | WATCHLIST | REJECTED] · regime-robust [y/n]
TABLE (one row per signal):
  signal · state-chip · weight (if in score) · evidence (rank-IC boom/long · OOS lift) ·
  WHY (the one-line verdict) · → Evidence Browser entry
SECTIONS: ① Score components (in-score + display-only + weights)
          ② Context signals (crowded_window folded; nifty_mom rejected; …)
          ③ GRAVEYARD (rejected, with the WHY — first-class, browsable)
```
**Components & data sources:**
- Registry records from `rules/index.md` (tested-signal registry + context-signal verdicts + the
  hypothesis-batch verdicts). Each row: `state` → chip (IN-SCORE→`✓`, DISPLAY-ONLY/WATCHLIST→`~`/`⚠`,
  REJECTED→`✗`); `weight` from `layer3.predictor.weights` (data_informed profile) for in-score rows;
  `evidence` + `why` from the record. Link each to its Evidence-Browser hypothesis where one exists.
- The **SCORE POLICY** ("evolve-only-if-robust") shown as a header note so the table reads as a governance
  ledger, not a menu.

**Empty/degraded:** none expected (records are static); a signal without a linked hypothesis shows the WHY
inline and no link.

---

## Screen 6 — FORWARD-TEST / TRACK-RECORD

**Purpose.** "Did the calls work?" — the honest forward record, with mode-split evidence strength front and
center. Distinct from the in-Recommendations track-record summary: this is the full audit with the
counterfactual and the backtest loop-closer.

**Layout:**
```
REGIME BANNER (persistent)

A. CALL TRACK RECORD (from ledger) — recomputed at render
   table: call_type × mode → n · win% · median Δalpha vs counterfactual · IQR · grade_status mix
   mode legend: live/gap_filled = forward truth · backfilled = OOS · historical_sim = dress rehearsal
   thin rows: "N=k — too few"

B. PER-CALL LEDGER (audit) — st.dataframe of the raw ledger
   filter by call_type / mode / grade_status; each isin → IPO Detail

C. OOS REPORT CARD (the predictor's honest test)   ← reuse existing oos_table()
   train≤cutoff → test later · top-quintile median vs field · OOS lift pp · win-rate
   + "try your own split" expander  (caption: 3y real edge +55pp; 1y weak)

D. CHART — track record over time   ← Altair chart #2 (the only other allowed chart)
   cumulative win-rate or median-Δalpha by call_date, faceted by mode (so live vs sim are
   visually separated, never pooled into one line)
```
**Components & data sources:**
- A & B — `calls_ledger.csv` grouped/aggregated at render (no hardcoded stats — acceptance rule). Win
  definitions per call_type as in the calls spec. Distributions (median+IQR), N on every row, min-N floor.
- C — existing `oos_table()` + the train/test-split expander (port from current `app.py` Validation tab).
  Chip on each OOS row: `✓ VALIDATED` at 3y, `~ DISPLAY-ONLY` at 1y (weak).
- D — **Altair chart #2.** Faceted by `mode` so historical_sim and live are never visually pooled; x =
  call_date, y = cumulative win-rate or rolling median Δalpha. Caption states the modes plainly.

**Empty/degraded:** no graded calls yet → A/B/D show "no graded calls — the ledger needs maturing"; C still
renders (it's substrate-derived, not ledger-derived).

---

## Cross-cutting build notes
- **Two charts only:** ⑥ path-vs-reference (Detail) and D track-record-over-time (Track). Everything else =
  `st.bar_chart`/`st.dataframe`/`st.metric`/native. The analog-alpha distribution bar reuses the existing
  `st.bar_chart` (native, doesn't count against the two).
- **`predict()` query handoff:** Score-form (ported from current `tab_score`) writes the query dict to
  `st.session_state` and `st.switch_page` → IPO Detail, which reads either `?isin=` or the session query.
- **No DB, no auth, no live client-side JS, no precompute-all-hypotheses-per-load.** The only CSS is the
  one injected `<style>` block for the monospace/number face + chip colors.
- **Trust-chip → status mapping is the contract:** IN-SCORE/validated cross-regime → `✓`; folded-but-
  display/cluster/path-conditioning → `~`; thin-N (TAKE_PROFITS/F10, EARLY_*) or hypothesis preview → `⚠`;
  rejected → `✗` (graveyard only, never an action surface).
- **Verify-before-build gates:** anchor share present per calendar row (else "dose: unknown"); ledger and
  board files exist (else the honest "not yet run" empty states); price file exists before drawing ⑥.
```
