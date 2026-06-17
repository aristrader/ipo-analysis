# Alignment Audit — 2026-06-16

**What this is:** a one-time, repo-wide audit triggered by the discovery that the "git is local-only"
convention was stale (a remote now exists). The owner asked: *find every place where what the docs/code
**claim** disagrees with what is **actually true**, and review the code for real bugs — surface, don't
auto-fix.*

**How it was produced:** six read-only subagents, each scoped to one dimension, run in parallel. Each was
told to establish ground truth (never assume) and report with `file:line` evidence. **Nothing in this report
has been independently re-verified by the main thread yet** — see the `STATUS` column. We will work through
this file together; fixes happen only after we agree on each item (and, per the new git policy, on a branch + PR).

> ## ✍️ HOW TO USE THIS FILE (owner)
> Each finding and each open decision has an **`✍️ OWNER:`** slot. Write your answer on that line.
> Convention for what you want done with an item:
> - **`FIX`** → I'll spawn an agent (branch + PR) to fix it. Add any constraints after the word.
> - **`DISCUSS`** → leave it for the main thread; we'll talk it through one by one.
> - **`SKIP`** / **`DEFER`** → drop it (note why if useful).
> - For a question, just write the answer (I'll infer FIX/DISCUSS from it, or ask).
>
> I will periodically read this file, action everything marked `FIX`, and leave `DISCUSS`/blank items alone.

**Severity legend:** `CRITICAL` = corrupts data/conclusions or makes a false "it works" claim · `HIGH` =
real bug / policy contradiction · `MED` = correctness-adjacent or stale-baseline · `LOW` = doc/cosmetic drift.

**STATUS legend:** `UNVERIFIED` (agent claim, needs main-thread confirmation) · `VERIFIED` (re-checked) ·
`NEEDS OWNER DECISION` (judgment call for the owner) · `FIXED`.

---

## 🗂 WORK STACK — sequential coverage (push when started · pop when DONE+verified)
**Discipline (owner 2026-06-16):** every workstream goes here the moment we start it; it is REMOVED only when
fully done + verified. Nothing leaves until covered → we can't miss anything. Work top-down; waves run in order.

### ▶ Active (background agents)
- [ ] **Structural-integrity NIT-FIX agent** — applying NIT-2 (actionable RULE A "generate via: <cmd>" message) + NIT-3
  (INDEX/README task_log path) + NIT-1 residual (de-hardcode project_map "29 findings") + convention rule + re-verify.
  Owner decision on NIT-1 guard regex: **LEAVE the adjective-evasion gap** (backstop only). **Pop when:** diff reviewed → PR (bundle DOC-3 + structural-integrity).

> **D-3/D-4 — HELD (owner 2026-06-16).** Do not verify/fix until owner re-opens. (Design is laid out under D-3/D-4 below.)
> **PROCESS RULE (owner 2026-06-16): keep rolling, but NO new agents / consequential actions without explicit approval.**

> **D-3/D-4 — HELD (owner 2026-06-16).** Do not verify/fix until owner re-opens. (Design is laid out under D-3/D-4 below.)
> **PROCESS RULE (owner 2026-06-16): keep rolling, but NO new agents / consequential actions without explicit approval.**

### ⏳ Queued (in order)
- [ ] **Structure-review SR-cluster** — triage SR-1…SR-14 (`structure_review_2026-06-16.md`). SR-6/SR-11 DONE (rules move).
  Open: SR-1 (supersedes claim), SR-5 (transition-doc orphan — KEEPING), SR-8/SR-9 (backlog/STATUS path refs), SR-10 (INDEX.md drift).
- [ ] **Corp-action external evidence — WAVE 2** — phantom (84, price says don't-apply) + unconfirmed
  single-source (~25). Spawn after Wave 1 proves useful.
- [ ] **D-1 Phases 1–3** — rebuild corp-action reconciliation around price-validation + the corroboration matrix
  (gated on Wave 1/2 evidence + the strict-mode triage decision). See LOCKED PLAN under D-1 below.
- [ ] **Main-thread `.md` items** (tackled here while agents run): strict-mode triage (53 events) · D-3 · D-4 ·
  T-2 · T-3 · T-4 · T-5 · C-2 · DOC-1…DOC-6 · STRUCT-1 · I1 systemic · O-series (O-2…O-16).

### ✅ Popped (done — detail in git log, not here)
- **DOC-2** — CLAUDE.md "5-component" → "8-component" scorecard. Fixed.
- **DOC-6** — weight precision (0.260 vs 0.26): non-issue (identical value, STATUS is internally 3-decimal). No change; real cure = STRUCT-1.
- **DOC-7 / SR-6 / SR-11** — rules registry ghost-path: was a **real code bug** (app screens read dead `rules/index.md`). Fixed by `git mv thinktank/rules → rules/` + project_map.py update; app path now resolves, CLAUDE.md correct as-is, verify.py clean. (DOC-4's a1/a1b/newsfeed code comments also done.) **[MERGED — PR #2]**
- **DOC-3** — all 7 stale project_map pointers fixed (4 moves + showdown re-point/move-back); `verify.py` PASSES. *(uncommitted → structural-integrity PR)*
- **STRUCT-1** — DESIGN LOCKED (generate→MAP.md + reference + drift-guard); build folded into the verify.py structural-integrity upgrade.

---

## Triage table (master index — OPEN items only)

| ID | Sev | Area | One-liner | Status |
|----|-----|------|-----------|--------|
| **D-1** | CRITICAL | pipeline | Corp actions double/triple-counted → ~11 stocks with absurd returns (+15,272%) misclassified `multibagger` | **PLAN LOCKED — Phase-0 running** |
| **D-2** | CRITICAL | pipeline | Reverse splits (`ratio_factor < 1`) from Yahoo applied as divisors → pre-event prices multiplied (45 rows) | **FOLDED INTO D-1** |
| **T-1** | CRITICAL | tests | Suite not green; now **349 pass / 12 fail / 12 skip**. 12 skip = SHOWDOWN-gated (by design); 12 fail = 4 root causes (T-2/3/4/5). See T-1 detail | VERIFIED — broken down |
| **D-3** | CRITICAL | layer3 | Look-ahead leak: `market_cap_class` (current, post-crash cap) used as analog gate + distance feature + in weight queries | **HELD (owner)** |
| **D-4** | HIGH | layer3 | `score_all_pointintime` passes the **full** (future-inclusive) df to `crowded_window` / `coverage_guard` → leaks into derived weights | **HELD (owner)** |
| **T-2** | HIGH | tests | MFE/MAE envelope regression: 39 substrate rows violate trough ≤ endpoint ≤ peak (the "removed clamp" left it broken) | UNVERIFIED |
| **T-3** | MED | tests | Golden baselines + canonical weights stale vs fresh derivation (refresh without re-derive) | UNVERIFIED |
| **T-4** | MED | tests | Compulsory-delisting −100% trough regression — root-caused (clamp removed prematurely; was hiding D-1). **Decision (c) LOCKED → execute POST-D-1** | RESEARCHED |
| **C-2** | MED | config | WebFetch allowlist documented as project-level, actually lives in user-level settings | UNVERIFIED |
| **T-5** | MED | tests | thinktank Streamlit UI test fails (state machine doesn't advance; "Failed to parse Final Judge JSON") | UNVERIFIED |
| **DOC-1** | LOW | docs | Test count stated as 211 / 219 / 77 across docs; real = **359** — dissolved by STRUCT-1 | DEFERRED → STRUCT-1 |
| **DOC-4** | LOW | docs | Stale paths — code comments DONE; remaining live pointers (hypothesis_protocol, app/records README) | PARTIAL |
| **DOC-5** | LOW | docs | "Gemini CLI / Antigravity context engine" section reads as live; it's aspirational/not implemented | DEFERRED (orchestration talk) |
| **SR-cluster** | mixed | structure | 14 sprawl/structure findings → `docs/research/structure_review_2026-06-16.md` (triage queue) | TO TRIAGE |
| **STRUCT-1** | — | meta | One source of truth for drifting counts (generate→MAP.md + reference + drift-guard) | DESIGN LOCKED → build |

---

## CRITICAL

### D-1 — Corp actions double/triple-counted → catastrophic over-adjustment
**Source:** pipeline/scrapers bug hunt. **Status: UNVERIFIED — verify before any fix.**

**Where:** `pipeline/03l_merge_corporate_actions.py:44-58`, `pipeline/03k_reconcile_corporate_actions.py:145-195`;
consumed in `pipeline/07_returns_summary.py:114-127` (`actions_for`) and `scrapers/screener_prices_merge.py:132-146`.

**What's wrong:** the corp-action union dedups on the exact key `(ex_date, ratio_factor)`. The same real event
reported by Yahoo and NSE on dates differing by **more than the ±10-day reconcile window** (03k) leaks into
`corp_actions_yahoo_only.csv` and is appended by 03l as a *separate* event. Step 07 multiplies every factor with
`ex_date > price_date`, so one split is applied 2–3×.

**Confirmed-by-agent impact — ~11 universe stocks** with a same-factor event clustered within ~45 days:
- **ROLEXRINGS (INE645S01024)**: split 10:1 reported 2025-09-19 (yf), 2025-10-03 (yf), 2025-10-17 (nse) →
  pre-event prices ÷ 10×10×10 = **1000×**. `issue_price_adj` = 0.9 (should be ~90), `current_return_from_issue`
  = **+15,272%**, misclassified `outcome_class = multibagger`. True return ≈ +50%.
- **NPST**: 3:1 counted twice → `current_return_from_issue = +16,127%`.
- Others named: PATANJALI, PAVNAIND, DIGIKORE, MOS, ABHISHEK, CANTABIL, GNA, VISHWARAJ, RPEL, CMMIPL.

**Why it matters:** these rows feed `ipo_analysis.csv` directly → corrupt Layer-3 base rates, multibagger odds,
the right-tail the project says "carries returns," and predictor analogs. The 09 cross-source listing-price check
that could catch it is **deliberately skipped when a stock has any corp action** (`09_assemble.py:85-89`), so
they're invisible.

**Suggested fix (do NOT apply yet):** dedup events sharing a `ratio_factor` within a tolerance window (30–45d) and
treat as one; or widen the 03k match window; add a pipeline check flagging any stock whose product-of-factors
implies an implausible (>100×) adjustment.

**Verification plan:** read the corp-action rows for INE645S01024 across the source files; recompute the applied
factor; confirm `current_return_from_issue` in `ipo_analysis.csv`. Cross-links to **T-2** (envelope regression).

> ✍️ OWNER: **DISCUSSED + PLAN LOCKED 2026-06-16. Phase-0 diagnostic agent spawned.** (covers D-2 too)

#### 🔒 LOCKED PLAN (D-1 + D-2) — "feeds propose, price disposes" + cross-source corroboration

**Root cause (reframed):** we apply scraped corp-action factors blindly with no ground-truth anchor. Every failure
mode (double-count, reverse-split, missing event, wrong ratio) comes from there being no referee.

**Principle:** the **price discontinuity is the SENIOR referee** — a real split gaps the raw price by ~the ratio on
the ex-date; that gap is the truth. Yahoo + NSE only *propose*. Cross-source agreement *corroborates on top of* price
(two sources agreeing on a phantom that the price never moved on is still rejected — price outranks source-agreement).

**Corroboration matrix (per detected price gap = one true event):**

| Price gap | Yahoo | NSE | Verdict |
|---|---|---|---|
| ✅ matches ratio | claims it | claims it | ACCEPT — high confidence, auto-apply |
| ✅ matches ratio | claims it | silent | (strict mode → FLAG; pragmatic → accept-medium) |
| ✅ gaps | 2× | 1× | FLAG — count conflict (the D-1 case; price tiebreaks → apply once) |
| ✅ gaps | ratio A | ratio B | FLAG — ratio conflict |
| ✅ gaps | silent | silent | FLAG — missing event |
| ❌ no gap | claims it | claims it | FLAG — phantom (likely duplicate/spurious) |

**MODE DECISION (owner, 2026-06-16): STRICT for now** — auto-apply only when price-gap + Yahoo + NSE all agree
(count, ratio, direction); everything else → FLAG for separate review. We accept this over-flags single-source events;
Phase-0 produces the full list and we triage which buckets are safe to auto-accept *after* seeing the distribution.

**Phases:**
- **Phase 0 — diagnose, NO logic change.** Scan all 2,384 stocks; for each corp action emit a corroboration record →
  one review CSV bucketing every event: `agree-all` / `count-conflict` / `ratio-conflict` / `phantom` / `missing` /
  `single-source`. **Agent STOPS here and returns the CSV for owner triage** before any adjustment logic changes.
- **Phase 1 — rebuild reconciliation** around price-validation + the matrix (replaces the `(ex_date, ratio_factor)` +
  10-day-window dedup in `03k`/`03l`); reverse-split direction from gap sign (fixes D-2).
- **Phase 2 — permanent continuity guard:** post-adjustment, any unexplained single-day jump → flag; also closes the
  hole where `09_assemble.py:85-89` disables the cross-source check for any stock with a corp action.
- **Phase 3 — rebuild + verify:** confirm fake multibaggers (ROLEXRINGS +15,272%, NPST +16,127%, etc.) gone, Phase-0
  buckets resolve, likely clears **T-2**. Golden/weight re-derive deferred until after D-3/D-4.

**Process:** execution pipeline / TDD — over-adjustment detector as a failing test first, independent review, branch → PR.
Phases 1–3 wait for a second agent *after* owner triages the Phase-0 list.

---

### D-2 — Reverse splits (`ratio_factor < 1`) applied as divisors
**Source:** pipeline/scrapers bug hunt. **Status: UNVERIFIED.**

**Where:** `pipeline/07_returns_summary.py:206-235` (`load_prices`), `pipeline/03l_merge_corporate_actions.py:44-53`;
source `scrapers/corporate_actions_yfinance.py`.

**What's wrong:** 45 merged rows have `ratio_factor < 1` (PATANJALI 0.01, SELMC 0.001, BURNPUR 0.2) — reverse
splits/consolidations Yahoo emits as a fractional ratio. The loop divides pre-event prices by `factor`; dividing by
0.01 *multiplies* by 100. The NSE-native parser (`scrapers/corp_actions.py:75-102`) only ever produces factors ≥ 1
("factor ≥ 1, divide" convention); the yfinance sub-1 ratios violate it silently. The `0.99–1.01` skip in 03k only
filters near-1 dividend noise, not genuine sub-1 reverse splits. (PATANJALI gets *both* a 0.01 and a 5.0 factor →
compounds with D-1.)

**Suggested fix (do NOT apply yet):** decide the canonical meaning of a reverse split; convert yfinance ratios to the
"≥1 divide" convention (or invert to multiply) at merge time; reject/flag any `ratio_factor < 1` rather than feeding
it to `load_prices`.

> ✍️ OWNER: **FOLDED INTO D-1 LOCKED PLAN** (reverse-split direction inferred from price-gap sign in Phase 1).

---

### T-1 — The test suite is NOT green (docs claim it is)
**Source:** test-suite health. **Status: VERIFIED by agent run** (~101s, Python 3.14, `.venv`).

**Ground truth:** **359 collected → 333 passed, 14 failed, 12 skipped**, 9 warnings.
- The 12 skipped = `tests/showdown/` (gated behind `SHOWDOWN=1`, by design).
- No network was hit; no scipy/statsmodels involved.

**The docs say otherwise:** CLAUDE.md / STATUS.md describe the suite as green and "mutation-validated 28/28."
That is a **false success claim** — the highest-priority class of drift to correct.

**UPDATE post-DOC-3 + structural-integrity build:** now **349 pass / 12 skip / 12 fail** (DOC-3 fix cleared the
project_map failures; +14 new structural-integrity tests pass). The remaining 12 fail = **4 root causes**, NOT 12 random breaks:

**The 12 SKIP — by design, not a problem.** All 12 are `tests/showdown/`, gated behind `SHOWDOWN=1` (the heavy
pre-release gate: sandbox pipeline re-run+diff, entry-point smokes, app browser test, ~3 min). They SHOULD skip in normal runs.

**The 12 FAIL — 4 root causes (test files in parens):**
1. **① Removed-clamp envelope breakage → T-2 + T-4** (`test_substrate_integrity`, `test_reach`, `test_compute_synthetic`).
   Commit `26cd1fd` removed the MFE/MAE clamp that forced `trough ≤ endpoint ≤ peak` and compulsory-delisting→−100%.
   Now ~39 rows violate the envelope (e.g. `INE312H01016`) + a wiped stock shows +15% trough not −1.0. **Likely the SAME
   family as the corp-action bug D-1/D-2** (bad split factors → impossible peaks/troughs). → fixing D-1 likely clears most of T-2.
2. **② Refresh-without-re-derive → T-3** (`test_headline_numbers`, `test_weights_files`). Drift tripwires working AS DESIGNED:
   a data refresh happened without re-running derive-goldens / derive-weights, so committed goldens + `scorecard_weights.json`
   diverge from fresh derivation. **Don't just re-derive** — D-1 + D-3/D-4 contaminate the derivation. Sequence: fix leaks → re-derive → re-bless.
3. **③ thinktank UI state machine → T-5** (`test_ui_execution_run`). Doesn't advance past "Confirm & Build Plan";
   "Failed to parse Final Judge JSON" (LLM mocked). Isolated to `thinktank/orchestration/` (auxiliary, not core pipeline);
   plausibly flash-lite-era. Lowest priority.

**Sequencing:** T-2 + most of T-3 are downstream of **D-1** (don't touch until corp-action fix lands, then re-derive ONCE on clean
data). **T-4** = one self-contained owner decision (restore clamp vs change −100% contract). **T-5** independent + isolated.

> ✍️ OWNER: T-1 is the umbrella — resolved by fixing T-2/T-3/T-4/T-5 (above). T-4 is the only standalone decision.

---

### D-3 — Look-ahead leak: `market_cap_class` (current cap) used in analog matching + weights
**Source:** layer3 engine bug hunt. **Status: UNVERIFIED — but the project's own findings already flag this column as circular.**

**Where:** `layer3/predictor/analogs.py:99-107, 110-136` (hard gate + ladder rung + Gower distance feature) and
`layer3/predictor/weights.py:20` (`market_cap_class` in `_QUERY_FEATS`, used by `score_all_pointintime`).

**What's wrong:** `market_cap_class` / `market_cap_cr` is scraped LIVE from Screener (`scrapers/screener.py:98-100` →
`pipeline/08_build_universe.py:163-189`) — it is the company's cap *as of the scrape*, not at-IPO. The analog engine
gates and ranks on it; point-in-time weight derivation matches every historical IPO to analogs on their *current*
(outcome-contaminated) cap. A wiped-out name reads "micro" *because* it crashed.

**Why it matters:** the findings layer deliberately **excludes** this column as reverse-causal
(`n14_wipeout_anatomy.py:32`, `docs/research/.../interactions_upside.md`), but the predictor/analog/weights path does
**not** — biasing the analog cohort optimistically and contaminating the derived data_informed weights.

**Suggested fix (do NOT apply yet):** replace with an at-IPO proxy (`issue_size_cr` is already an at-IPO Gower
feature; or compute at-IPO cap = issue_price × post-issue shares); at minimum drop `market_cap_class` from the hard
gate and `_QUERY_FEATS`. **NEEDS OWNER CONFIRMATION** — the gate ladder is structured around it, and this touches the
validated weights.

> ✍️ OWNER: ______________________________________________________________________

---

## HIGH

### D-4 — `score_all_pointintime` leaks future data into query-feature components
**Source:** layer3 engine bug hunt. **Status: UNVERIFIED.**

**Where:** `layer3/predictor/weights.py:73-74` passes the **full df** to `scorecard.crowded_window(q, df=df)` and
`scorecard.wipeout_safety(q, df=df)` even though analogs are correctly frozen to `prior`.

Two concrete leaks downstream:
- **`crowded_window`** (`scorecard.py:405`, `_heat_reference:412-428`): `pct_below` ranks the query's heat against the
  **full-history** (future-inclusive) distribution. `crowded_window` is a promoted data_informed component → its
  measured lift may be inflated by leakage.
- **`coverage_guard` thin-record SME leg** (`scorecard.py:198-200, 282`): fires on banker `freq` computed over the
  **entire window** (future IPOs included), while the quality leg is correctly point-in-time.

**Suggested fix (do NOT apply yet):** pass a date-frozen frame (`prior`) to *all* query-feature components inside
`score_all_pointintime`, not just to analog selection.

**Why it matters:** these feed the rank-IC weight derivation → the data_informed weights may be partly contaminated.
Bundle with D-3 when we decide whether to re-derive weights.

> ✍️ OWNER: ______________________________________________________________________

---

### T-2 — MFE/MAE envelope regression (39 rows) — likely a real data bug
**Source:** test-suite health (Cluster A/C). **Status: UNVERIFIED.**

- `tests/layer3/test_reach.py::test_mfe_mae_invariant_holds_on_substrate` → 39 rows violate peak ≥ endpoint ≥ trough
  (comment: "step-09 clamp regressed").
- `tests/data/test_substrate_integrity.py::test_trough_le_endpoint_le_peak` → 7 parametrized failures, single offender
  **`INE312H01016`** breaks 6 issue-anchored horizons + 1 listing-anchored.

**Hypothesis:** commit `26cd1fd` ("remove data clamping hack") rebuilt the substrate without the invariant clamp,
leaving ~39 rows outside the envelope. **Plausibly the same family as D-1/D-2** (bad corp-action factors produce
impossible MFE/MAE). Verify whether `INE312H01016` / the 39 rows overlap the D-1/D-2 stock list.

> ✍️ OWNER: ______________________________________________________________________

---

## MEDIUM

### T-3 — Golden baselines + canonical weights stale vs fresh derivation
**Source:** test-suite health (Cluster A). **Status: UNVERIFIED.**
- `tests/data/test_headline_numbers.py::test_current_computation_matches_accepted_goldens` → 5 goldens drifted
  (e.g. `mb_boom_1y_matured_n` 283→280, `mb_longterm_ever2x_3y_n` 456→370). Named fix path: `tools/refresh/derive_goldens.py`.
- `tests/data/test_weights_files.py::test_canonical_weights_match_fresh_derivation` → committed `scorecard_weights.json`
  diverges from fresh `derive_weights()` (downside_safety 0.269 vs 0.18). Fix path: `run_weights.py`.

These are **drift-detector tripwires firing as designed** — a refresh happened without re-running the derive scripts.
But do NOT just re-derive: D-3/D-4 mean the *derivation itself* may be contaminated. Sequence matters — fix leaks first,
then re-derive, then re-bless goldens.

> ✍️ OWNER: ______________________________________________________________________

---

### T-4 — Compulsory-delisting −100% trough regression  ·  **DECISION LOCKED → (c); execute POST-D-1**
**Source:** test-suite health (Cluster C). **Status: ROOT-CAUSE RESEARCHED (git archaeology, 2026-06-16).**
`tests/pipeline/test_compute_synthetic.py::test_compulsory_delisting_forces_minus_100` asserts `mae_1y == -1.0`, actual `0.15`.

#### Full history (git-verified) — what the clamp was and why this broke
- **What the clamp was:** for each horizon we compute MFE (peak), MAE (trough), endpoint. A true invariant: trough ≤ endpoint ≤ peak.
  The clamp (removed in `26cd1fd`, in `07_returns_summary.py`) was 4 lines forcing it:
  `mfe = max(mfe, endpoint)` / `mae = min(mae, endpoint)` (issue- and listing-anchored).
- **Why it existed:** a BAND-AID over bad price data. `726b0bb` extended it because *"74 inferred-split weekly rows were on the
  pre-remediation scale at short horizons"* — i.e. MFE/MAE were computed from mis-scaled prices and came out impossible; the clamp hid that.
- **Its hidden second job:** for a compulsorily-delisted stock, decision A1 sets endpoint = −100%; since `mae = min(mae, endpoint)`,
  the trough got forced to −100% too. **So delisting −100% was only ever a SIDE-EFFECT of the clamp, never explicit logic.**
- **Why it was removed:** `26cd1fd` ("remove data clamping hack… now that dataset is flawless") removed it in the SAME commit that
  "merged missing corporate actions for 88 microcap stocks." Belief: data is now clean → band-aid unneeded. Code comment:
  *"corporate actions are perfectly mapping splits and bonuses… Clamping is no longer needed."*

#### Where we messed up
The dataset was **NOT flawless** — that very corp-action merge introduced the over-counting bug **D-1** (ROLEXRINGS 1000×, double-counts,
reverse-splits) — exactly the bad-data class the clamp had been hiding. Removing the clamp didn't break anything new; it **un-hid** it:
**T-2** (39 envelope violations) = still-inconsistent prices; **T-4** = delisting −100% lost its only enforcement → shows the raw
intra-window path (+15%). Mistake = removing the safety net on a false "data is clean" assumption, when the same change had corrupted it.
(The *instinct* — stop hiding data problems behind a silent clamp — was right; the *timing* was premature.)

#### Right thing to do — DECISION (c) (not "restore clamp", not "relax test")
1. **Fix D-1 first** (corp-action rebuild) → the envelope invariant then holds naturally, no clamp needed.
2. **Replace the silent clamp with a loud TRIPWIRE:** keep checking `trough ≤ endpoint ≤ peak`, but FLAG/RAISE a violation instead of
   silently snapping it (so future bad data is caught, not hidden — a 1000× error must surface, not get clamped to look plausible).
3. **Make delisting −100% EXPLICIT** in the delisting logic (terminal = −100%, and any horizon spanning the delisting date reaches −100%),
   decoupled from the generic clamp — so survivorship-honesty (A1) no longer depends on a clamp existing.
The failing test is CORRECT to fail — it's flagging that the data + delisting logic still need the real fix.

> **SEQUENCING: execute POST-D-1** (fixing the substrate is prerequisite). Decision (c) locked 2026-06-16; T-2 fix folds in here too.

---

### C-2 — WebFetch allowlist location mismatch
**Source:** config audit. **Status: UNVERIFIED (enforcement is working; doc is imprecise).**
CLAUDE.md:104 + `trusted_sources.md` say the allowlist lives in `.claude/settings.local.json`; that file only has the
Playwright key — the actual allowlist is in user-level settings. Not a security hole, but the doc points to the wrong
file (hurts auditability). Fix: clarify the doc, or move the allowlist to project-level for visibility.

> ✍️ OWNER (clarify doc, or move allowlist to project?): ____________________________

---

### T-5 — thinktank Streamlit UI state-machine test fails
**Source:** test-suite health (Cluster D). **Status: UNVERIFIED.**
`tests/thinktank/test_ui.py::test_ui_execution_run` — after "Confirm & Build Plan" the app stays on Checkpoint 1
instead of advancing to Checkpoint 2; LLM is mocked (not env/network); "Failed to parse Final Judge JSON" logged.
Isolated to `thinktank/orchestration/` (auxiliary tooling, not the core IPO pipeline). Likely real state-transition bug
or a test lagging a refactor.

> ✍️ OWNER: ______________________________________________________________________

---

## LOW / documentation drift

### DOC-1 — Test count stated three ways; real = 359
CLAUDE.md:25,31,60 "211" (with a stale per-directory breakdown) · STATUS.md:11 "219" · README.md:46 "77" for layer3
(real 171). The 211 inventory predates `tests/app`, `tests/notify`, `tests/thinktank`, `tests/checks` and the layer3
expansion. → folds into **STRUCT-1**.

> ✍️ OWNER: ______________________________________________________________________

---

### DOC-4 — Other stale paths  *(PARTIAL — code comments fixed; pointers/showdown remain)*
✅ Done: `scorecard.py` a1/a1b → `signals/`; `layer3/news/{taxonomy,staging}.py`, `scrapers/announcements.py`,
`tests/layer3/test_news.py` newsfeed_rnd → `newsfeed/`. **NOT a doc-fix (deliberate):** historical records
(`task_log.md`, `superpowers/plans|specs/`) left intact (rewriting = falsifying history); `MAP.md`/`INDEX.md`
are generated; showdown-doc refs (`project_map.py`, `run_mutations.py`, showdown test docstrings, `WORKFLOWS.md`)
WAIT for the DOC-3 keep/drop call. **Remaining live pointers to fix:** `docs/research/hypothesis_protocol.md`
+ `app/records/README.md` → `signals/tier1_wave1_verdicts.md` (+ context_signals). **Pop when:** those + DOC-3 done.

---

### DOC-3 — `project_map.py` references 7 relocated docs (also fails 2 tests)
Moved/archived in commit `6d6730c` (2026-06-15 docs restructure) but the map wasn't updated. Fails
`tests/test_project_map.py::{test_every_mapped_path_exists,test_verify_reports_no_drift}` and trips the per-turn
`verify.py` hook.

**✅ RESOLVED 2026-06-16 (uncommitted, bundling into the structural-integrity PR).** All 7 pointers fixed; `verify.py` PASSES.
- 4 unambiguous moves updated: drhp→`data/`, newsfeed×2→`newsfeed/`, tier1→`signals/`.
- showdown (reviewed): `showdown_audit` + `showdown_pipeline_diff` → re-pointed to `archive/`; `showdown_mutation` is a
  GENERATED report (`run_mutations.py` writes `docs/research/showdown_mutation.md`) → moved back out of archive, map points there.

---

### DOC-5 — "Gemini CLI / Antigravity context engine" reads as live, isn't
CLAUDE.md "Token Saving & Multi-Model Meta-Orchestration" presents a working background context engine. Reality:
`thinktank/orchestration/nodes.py` uses the Gemini *API* (not CLI); `tools/generate_audit_md.py` hardcodes a one-off
`.gemini/antigravity-cli/...` path; no active tooling invokes the documented CLI. → mark ASPIRATIONAL/PARKED or implement.

> ✍️ OWNER (mark aspirational, or implement?): _______________________________________

---

## STRUCT-1 — Structural fix: one source of truth for drifting numbers
**Status: DESIGN LOCKED 2026-06-16 (owner: "cleanest solution, effort no object"). Build = part of the unified
verify.py structural-integrity upgrade (with the file-kind guard). Dissolves DOC-1.**

🔒 LOCKED DESIGN — **generate + reference + guard**:
1. **Generate (one machine source):** `verify.py` writes findings/tests/rows/AS_OF into a `CANONICAL FACTS
   (generated — do not hand-edit)` block at the top of **`MAP.md`** (already machine-generated each run → zero new
   git churn). `substrate_meta.json` stays the data-facts source (rows/as_of); verify.py reads it.
2. **Reference:** `CLAUDE.md` / `STATUS.md` / `README` drop all hardcoded counts → one-line pointer to MAP.md / `verify.py`.
3. **Guard (self-policing):** new `verify.py` check regex-scans the hand-docs for literal count tokens
   (`\d+ tests|findings`, `\d{3,4} rows`); any reintroduced raw count → flagged as drift by the per-turn hook.
   Makes recurrence structurally impossible (not just discouraged). + a test for the guard.

---

## Checked and found SOUND (no action)
From the bug hunts, to avoid re-litigating:
- **layer3:** `combined_score` weight renormalization (display-only/weight-0 correctly excluded); MFE/MAE signs in
  `reach_curve`/`stop_loss`/`exit_strategy`; `terminal_state` −100% for compulsory/liquidation; alpha-vs-raw separation;
  `regimes.regime_at` strictly point-in-time; `backtest/engine.strat_secondary_filtered` avoids post-listing gating;
  `wilson_ci`/`bootstrap_median_ci`/min-N floors; sales/PAT crore-scale thresholds.
- **pipeline:** ISIN-only auto-join discipline (corp actions = union of ISIN + symbol, per the face-value-split rule);
  0 returns rows fall outside universe (09 join loses nothing); issue-price adjustment *direction* correct given correct
  factors; `bhavcopy_ohlc` resume/dedup (0 duplicate-date rows in 400 files); `listing_remediation` branch math.
- **config:** row count 2384 + AS_OF_DATE 2026-06-06 consistent across substrate_meta/CLAUDE/STATUS/config; network
  default-deny enforcement is real; git branch+PR policy now matches reality; ISIN-key / returns-vs-Nifty /
  survivorship conventions hold in code.

---

## Open decisions for the owner (collected)
Mirror of the per-finding slots above — answer here or inline, whichever you prefer.

1. **D-3 / D-4 / T-3** — confirm the look-ahead fixes, then **re-derive weights + re-bless goldens** (sequence: fix
   leaks → re-derive → re-bless). Touches the validated data_informed weights — wants your sign-off.
   > ✍️ OWNER: ____________________________________________________________________
2. **DOC-3** — the 3 archived showdown docs: keep in the "testing" context as `archive/` pointers, or drop them?
   > ✍️ OWNER: ____________________________________________________________________
3. **DOC-5** — Gemini context-engine: mark aspirational/parked, or implement it?
   > ✍️ OWNER: ____________________________________________________________________
4. **STRUCT-1** — adopt "verify.py is the only source of truth for counts; docs stop hardcoding them"?
   > ✍️ OWNER: ____________________________________________________________________
5. **T-4** — compulsory-delisting trough: restore the clamp, or change the contract?
   > ✍️ OWNER: ____________________________________________________________________

## Suggested fix order (once decisions are made)
1. **Verify D-1/D-2/T-2** are the same root cause (bad corp-action factors) → fix the merge/dedup → rebuild substrate.
   This likely clears T-2 and several T-3 golden drifts at once.
2. **D-3/D-4** look-ahead fixes → re-derive weights → re-bless goldens (T-3).
3. **T-4** clamp/contract decision.
4. Config reconciliation (C-1, C-2).
5. Doc/source-of-truth (DOC-1…6, STRUCT-1).
6. **T-5** thinktank UI (isolated; lowest priority).

---

# APPENDIX A — Outlier scans (ROLEXRINGS-style data-bug hunt)
*Added 2026-06-16. Five agents: Phase-0 corp-action corroboration + 4 lane-scoped outlier hunts. All read-only.
New findings carry `O-` IDs. Status UNVERIFIED unless noted — these are agent claims to confirm before fixing.*

## Phase-0 corp-action corroboration — RESULT (feeds D-1)
Review CSV written: **`data/master/review/corp_action_corroboration_review.csv`** (259 flagged rows).
449 / 2,384 stocks have ≥1 corp action. Buckets per candidate event:

| bucket | count | meaning |
|---|---|---|
| agree-all | 436 | price gap + both sources, ratio matches → fine |
| phantom | 101 (84 stocks) | sources claim it, raw price shows NO ~ratio gap → likely duplicate/spurious |
| single-source | 78 (**53 price-confirmed**) | one source only, but price gaps → GENUINE |
| ratio-conflict | 35 | sources disagree on ratio |
| reverse-split | 27 (22 stocks) | `ratio_factor<1` / upward gap (D-2) |
| **count-conflict** | **14** | **the double/triple-count bug (D-1)** |

- **D-1 confirmed:** ROLEXRINGS = three identical 10:1 entries (2025-09-19/10-03/10-17, span 28d) → 1000× → +15,272%.
  NPST = two identical 3:1 (2024-01-22/02-02) → 9× → +16,127%. Both Yahoo-only duplicates 03l appended without
  re-dedup vs NSE. count-conflict 14: ABHISHEK, CANTABIL, CMMIPL, DIGIKORE, GNA, MOS, NPST, PAVNAIND, ROLEXRINGS,
  RPEL, USASEEDS, VISHWARAJ + INE01A501027, INE669Y01022.
- **reverse-split 22:** BAFNAPH, BANSAL, BURNPUR, GBGLOBAL, INDUSFILA, INNOVATIVE, KAUSHALYA, MANINFRA, MICEL,
  PATANJALI, PRITIKA, RAJRILTD, RMMIL, ROML, SEJALLTD, SELMC, SHEKHAWATI, SWANDEF, UEL, VERTOZ, WAAREEINDO + INE413X01035.
- **>100× cumulative:** ROLEXRINGS (1000×).
- ⚠️ **STRICT-MODE TRIAGE NEEDED:** strict "both sources must agree" would FLAG **53 single-source-but-price-confirmed**
  events that are GENUINE (price gaps by ~the ratio). Agent recommends KEEPING them (price referee already validates).
  **→ This is the triage decision the owner wanted to make after seeing the list. DECISION PENDING.**
- ⚠️ Caveat: ROLEXRINGS price file `data/prices/INE645S01024.csv` has a coverage HOLE (2024-07-05 → 2025-10-17, no rows
  between), so its true split window isn't cleanly observable — genuine adjustment is a single ~10–20× event, not 1000×.

> ✍️ OWNER (strict-mode: keep the 53 price-confirmed single-source events, or still flag? + greenlight Phase 1–3?):
> ______________________________________________________________________

## WAVE-1 external web-evidence — RESULT (feeds D-1 Phase 1) — DONE 2026-06-16
Read-only agent web-researched all **53 Wave-1 flagged stocks** (count-conflict 14 + ratio-conflict 18 + reverse-split 21;
VERTOZ in two) via `agy`/Gemini, each reconciled against its raw price gap (senior referee). CSV:
**`data/master/review/corp_action_external_evidence.csv`** (53 rows; isin/symbol/bucket/price_gap/web_action/sources/verdict).

**Verdicts:** 28 `resolve-apply-once` · 17 `resolve-correct-ratio` · 2 `resolve-reverse-direction` · 6 `STAYS-FLAGGED`.
- **Headline (price+web agree):** ROLEXRINGS = ONE 1:10 split (pipeline triple-counted → apply 10 once) · NPST = ONE bonus
  (double-counted → apply 3 once) · PATANJALI + KAUSHALYA = REAL 100:1 NCLT consolidations, price gapped ~100× → factor 0.01 keep ·
  MANINFRA = real forward 5:1 mislabeled reverse → apply 5.
- **KEY INSIGHT — most "ratio-conflicts" are NOT errors:** they're real **compound same-day split+bonus** events where Yahoo & NSE
  each captured only one leg; multiplied they match the price gap (ISHAN 10:1×2:1=30× vs price 28.6×; SBC 10:1×1:1=20× vs 19×; etc.)
  → `resolve-correct-ratio`, cumulative already ~right.
- **Genuine-distinct (keep, don't collapse):** SHARIKA, RANJEET = two real events weeks apart (factor 4.0 correct). SWANDEF = one
  real 1:275 NCLT double-entered → drop the 2023-03-17 dup.
- **STAYS-FLAGGED (6, owner triage):** CMMIPL/INDUSFILA/BANSAL (no reliable web + price coverage holes/wipeouts — likely phantom/stale;
  INDUSFILA/BANSAL have 2025/26 "actions" on stocks whose prices end 2015/2019) · COOLCAPS/SILVERTUC/VAISHALI (web claims ~10× but
  price gapped only ~3.7–6.5× → **price referee disagrees; agent refused to invent the factor** — "price disposes" working as designed).
- Caveat: a few sources came as Vertex grounding-redirect URLs (noted in-row) but cite identifiable pages (BSE/IIFL/NSE).

**This is the evidence D-1 Phase 1 builds on.** Combined with the strict-mode decision above, it unblocks the reconciliation rebuild.

## CROSS-CUTTING ROOT CAUSE — "missing coded as 0, not NaN" (re-confirms held item **I1**)
Three independent agents found the same pattern across unrelated fields: a blank/parse-fail was written as **`0`**
instead of `NaN`, so "missing" reads as a real (and damaging) value. Instances: O-2 (subscription), O-4 (GMP),
O-6 (sales yr3), O-8/O-15 (market_cap), O-14 (min_investment). STATUS.md already lists **I1 "substrate 0-vs-null
hygiene — do at pipeline-build level, not a post-hoc CSV edit"** as HELD for owner — this audit gives it concrete
teeth. **Recommend treating I1 as a single systemic fix** (loaders emit NaN on parse-fail; add NSE fallbacks) rather
than per-field patches.

> ✍️ OWNER (adopt I1 as one systemic "0→NaN at load" fix?): _______________________________________

## New findings (O-series)

### Subscription / GMP
- **O-2 [HIGH]** `sub_total_x = 0` on **124 rows** (all `src=sharescart`, 104 of them 2025) — **47 contradicted by
  premium listings** (Vibhor Steel +179%, Senco Gold +36%, Rulka +123%). Parser-blank-as-0; NSE raw total never used as
  fallback. Corrupts any subscription-as-feature finding → re-run those after fix. *(same family as the prior live-feed
  subscription-parser bug)*
  > ✍️ OWNER: __________________________________________________________
- **O-3 [MED]** 3 MB rows with QIB/NII/retail all 0 while `sub_total_x>60` (Jupiter Life Line, Cyient DLM, ideaForge) —
  category split missing-as-0. (SME QIB=0 is expected, not flagged.)
  > ✍️ OWNER: __________________________________________________________
- **O-4 [LOW]** `gmp_pct = 0` on 10 rows (src ipocentral/websearch) incl. Waaree (+70% listing), Vivo (+333%). Backfill
  from investorgain.
  > ✍️ OWNER: __________________________________________________________

### Financials
- **O-5 [HIGH]** `eps_yr1`/`eps_yr2` ~**1000× unit inflation** on 38–82 rows (ratio peaks at exactly 1000.0); `eps_yr3`/
  `eps_ttm` mostly clean. Per-year EPS share-unit/parse error. Corrupts EPS-CAGR / any yr1-yr2 EPS use.
  > ✍️ OWNER: __________________________________________________________
- **O-6 [HIGH]** `net_sales_yr3 = 0` on 13 large cos (yr2 was ₹1,400–1,900cr) → `pre_ipo_net_sales` inherits 0 →
  poisons margins. Several offenders are **NCD/debt `...25...`-series instruments mis-included** in the equity table
  (overlaps the non-equity-handling decision).
  > ✍️ OWNER: __________________________________________________________
- **O-7 [MED]** `eps_ttm` 3 absurd values (INE1I1301016=13,927 etc.) — tiny share base mis-parse.
- **O-8 [MED]** `market_cap_cr < issue_size_cr` on 169 rows + 12 with `=0`. Mostly as-of-date semantics (current vs
  at-listing cap), only ~3 true 100× errors; the 12 zeros are parse-fails. **Ties to D-3** (market_cap as-of semantics).
  > ✍️ OWNER: __________________________________________________________
- **O-9 [MED]** `pre_ipo_debt_equity` sign vs `pre_ipo_roe_pct` inconsistent on 9 rows (both derive from equity → must
  share sign); INE06ST01018 ROE 1400% clearly broken.
- **O-10 [MED]** one-off INE334L01012 `pat_margin = 983%` (`net_sales_yr3=18` corrupt latest-year cell).
- *Schema drift:* `docs/schema.md` lists `pre_ipo_eps` which does NOT exist (only `eps_yr*`/`eps_ttm`). → fold into DOC.

### Returns / outcomes (mostly CLEAN)
- **O-1 [MED]** `listing_open = 0` raw for Udayshivakumar Infra (INE0N0Y01013) — CONTAINED (adjusted col correct at
  ~₹30; Layer-3 uses adjusted). Repair raw or downgrade `listing_metrics_status`.
- ✅ Benchmark/alpha joins, delisting −100% terminal values, outcome_class bucketing, unreliable_coverage exclusions —
  all verified SOUND. Handoff note: corp-action over-adjustment is **bidirectional** — adjust-UP cases exist too
  (Pipavav 58→4,386,250), captured by Phase-0's reverse/ratio buckets.

### Structural / identity / dates / valuation
- **O-11 [HIGH]** 3 rows list BEFORE close (date transposition): Veto Switchgears (INE918N01018), GCM Commodity
  (INE168O01026), 20 Microns (INE144J01027). Ground-truth = first row of `data/prices/<isin>.csv`.
  > ✍️ OWNER: __________________________________________________________
- **O-12 [HIGH]** Bajaj Corp (INE933K01021) `market_cap_cr = 292,355` — wrong-entity screener join (~36× too large;
  implies 529cr shares vs real ~14.75cr). Proposed systemic check: implied-shares = cap×1e7/price vs issue-derived count.
  > ✍️ OWNER: __________________________________________________________
- **O-13 [HIGH]** 2 inverted price bands: Insolation Energy (band_low 131 vs issue 38), Enser (band_low 10 vs issue 70).
  `price_band_low` scraped from wrong field. Only 2/886 violate.
  > ✍️ OWNER: __________________________________________________________
- **O-14 [MED]** `min_investment_rs = 0` on 18 SME rows despite valid lot×price (clustered ingestion-batch gap).
- **O-15 [LOW]** 7 micro rows `market_cap_cr=0` but class=`micro` (0-as-null; class fine).
- **O-16 [NEEDS-VERIFY one-offs]** Wakefit (INE0E7301029) promoter post>pre; Newmalayalam (INE0TP801012) lot_size=1;
  Std Chartered IDR (INE028L21018) issue_amount 0 (non-equity → non-equity-handling decision).
- ✅ SOUND: ISIN integrity (0 dups, all valid), MB/SME labels, date ranges, P/E (negatives = real loss-makers),
  market_cap_class cutoffs, liquidity units, promoter pct in [0,100].

## Proposed systemic checks to ADD to the pipeline (from these scans)
1. **0→NaN at load** (I1) — loaders never write 0 for a parse-fail; add NSE subscription fallback.
2. **implied-shares cross-check** — flag `market_cap_cr×1e7/price` diverging >5× from issue-derived share count (O-12).
3. **band invariant** — assert `price_band_low ≤ issue_price ≤ ~1.05×band_low` (O-13).
4. **date ordering invariant** — `open ≤ close ≤ listing`, cross-checked vs first traded day (O-11).
5. **EPS reconciliation** — `eps ≈ pat_cr×1e7/shares`, flag per-year unit breaks (O-5/O-7).
6. **continuity guard** + **cumulative-factor sanity** — from the D-1 plan (Phase 2).
