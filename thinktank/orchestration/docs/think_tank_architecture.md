# The Research Lab — Unified Cognitive Architecture v3

> **This is the ONE file.** It consolidates and supersedes:
> - `docs/research/execution_pipeline.md` (the 8-step outer loop, owner mandate 2026-06-08)
> - `docs/research/hypothesis_protocol.md` (the 3-layer testing protocol for research)
> - The Think Tank ideation design (2026-06-13 session)
>
> Everything an agent needs to execute a task lives here. No cross-referencing required.

---

## Philosophy

> "Speed of execution is not that important; what is more important is the accuracy and correctness." — Owner mandate

Default for every substantive task. Slower per task; exceptional results, few/no bugs. The owner
has mandated this more than once — do NOT shortcut it unless the triage ladder says so.

The system is an **autonomous quantitative research lab**, not a code factory. Every idea must survive:
- Deep multi-dimensional ideation (not 3 bullet points — 20-40 chained hypotheses)
- Human pruning AND expansion
- Codebase-grounded execution planning
- Specialized peer review (code, math, bias — separate agents)
- Cross-regime statistical validation
- Causality/fluke checking

No rule enters the IPO scorecard without surviving all of these gates.

---

## TRIAGE FIRST — Which Path?

Top-down, FIRST match wins. Never self-rationalize into a lighter path.

| Path | When | What's required |
|---|---|---|
| **FULL** | Anything touching money numbers, score, ledger, user-facing surface, data product, or adds/changes a signal | Independent post-build REVIEW agent required. All steps below. |
| **HYPOTHESIS** | Research / testing a new idea | Diverge = expand-the-space. "Review" = placebo/falsifier (§Hypothesis Testing Protocol below). Register every verdict honestly. |
| **LIGHT** | Infra / data-capture / refactor | Diverge = 1 red-team lens (doubles as review) + TDD. |
| **HOTFIX** | Urgent fix | Say "hotfix" out loud. MINIMAL safe change + test. LOG it. Backfill review next turn. The only sanctioned skip. |
| **TRIVIAL** | True one-liner / typo / doc-tweak | Just do it. No ceremony, no log. |

"Non-trivial" = more than a one-liner OR touches data/score/money/a public surface. When unsure, go one tier heavier, not lighter.

---

## THE PIPELINE — All Steps

### Step 0: Scope the Data First

Confirm the inputs exist and are clean BEFORE designing. 2/3 of the Thread-C hypotheses were data-gated; the day-1 idea was forward-only. State the task + success criteria in one line. Open a `docs/research/task_log.md` entry (template in §Checkable Artifacts below).

### Step 0b: History Check — Has This Been Done Before?

Before any ideation, the agent MUST:
1. **Read `rules/index.md`** — the master registry of ~60 tested signals with verdicts (in-score / display-only / rejected + WHY + the numbers). If the idea has already been tested and rejected, STOP. Do not re-test without new evidence.
2. **Read `docs/research/improvement_backlog.md`** — the single living menu of what's left to do.
3. **Read `docs/research/task_log.md`** — check if a prior session already attempted this.
4. **Check the KILLED list** in `improvement_backlog.md` — ideas explicitly marked as rabbit holes.
5. **Substrate** = `data/master/ipo_analysis.csv` (load via `layer3/spine.py:load_substrate()`). Movable facts (row count, as-of) live in `data/master/substrate_meta.json` — never hardcode them.

**Output:** A brief "Prior Art Report" confirming whether this idea is novel or has prior evidence. If prior evidence exists, state it and ask the human whether to proceed.

---

### Step 1: High Ideation — The Brainstorm Explosion (DIVERGE)

**The Goal:** Transform a single 1D seed thought into a massive, chained network of hypotheses. Not 3 bullet points — 20-40 interconnected ideas where each thought spawns the next.

**The Model:** High-intelligence reasoning model (e.g., `gemini-2.5-pro` or CLI offload). This is the most expensive step and the most valuable. Do not use a cheap model here.

**Diverge mechanics:** 2-3 DISTINCT lenses, spawned in PARALLEL, wait for all. Lenses: user-value · analytical-depth · RED-TEAM (for a hypothesis: expand-space · test-design · falsifier). Each agent returns a FIXED contract:
```
PROPOSALS (each: what · feasibility-from-owned-data · effort S/M/L · ethos-fit)
TOP PICK
BLOCKERS/TRAPS
```
Essays don't converge — enforce the contract.

**The Bar — Second-Order Only:**
First-order screens ("undersubscribed → bad") are done and mostly dead. A testable idea must be an INTERACTION, SEQUENCE, REGIME-CONDITION, or CROSS-IPO mechanic, with a stated economic MECHANISM (whose money moves, why, when). Exemplar: "4 strong IPOs in one week → limited wallet → the 2 with lower GMP get starved at listing but outperform after week 1."

**Example — The GMP Chain of Thought:**
- *Seed:* "Does GMP have an effect on the stock price?"
- *Chain of Thought Explosion:*
    1. Does GMP affect the listing day price?
    2. Does GMP dictate how the stock will do in the long term?
    3. Does GMP dictate performance in the initial 3 months?
    4. Is the GMP reported on unofficial sites exactly followed by the market?
    5. What is the range (in percentage) in which the listing day price varies from the grey market premium?
    6. How many stocks had a positive GMP (more than the average range) but still opened negative?
    7. Did the broader market performance (Nifty) on that specific day override the GMP?
    8. Does the GMP-SURPRISE residual (listed above/below what GMP implied) carry 1w/1m drift?
    9. Does GMP meaning flip by regime — froth signal in hot markets, scarcity signal in cold?
    10. Did the T+3 listing rule (mandatory 2023-12-01) tighten GMP→pop transmission? A natural experiment.
    11. Is GMP × retail-share an interaction? (Self-fulfilling only when the GMP-watching crowd is the marginal buyer)
    12. For IPOs with extremely high GMP: do they list well but fade within 1 month? (Pop-fade variant)
    13. For IPOs with negative GMP: are they actually contrarian opportunities or genuinely bad?
    14. Does GMP accuracy vary by IPO type (MB vs SME)?
    15. Is there a GMP threshold below which listing-day performance becomes random noise?
    16. Within a cluster of overlapping IPOs, does GMP RANK inside the cluster matter more than absolute level?
    17. Do retail investors anchor on GMP more than institutional investors? (QIB subscription vs retail subscription split)
    18. Is GMP a proxy for something else entirely (e.g., issue size, sector heat)?
    19. Has GMP predictive power changed over the years as more retail investors became aware of it?
    20. For high-GMP IPOs that open negative despite the premium: what happens in the following week? Is there a recovery pattern?

**Note:** Every seed idea should generate this level of chained exploration. Some chains will be shorter (5-10); some longer (30-40). The point is EXHAUSTIVE exploration, not hitting a number.

**Documentation Output:** Findings appended to the **Single Dynamic Dossier** (see §UX Strategy below).

---

### ⏸️ HUMAN CHECKPOINT 1: The Pruning & Expansion

The human reviews the generated ideas. The human acts as the Portfolio Manager:
- **Pruning:** Discarding ideas that are uninteresting, already tested (cross-reference with `rules/index.md`), or data-gated (we don't have the columns).
- **Expansion:** The human can manually add new ideas, inject their own domain knowledge, or tweak the AI's hypotheses if the AI missed a crucial angle. The human's domain intuition is the most valuable input in the system.
- **Selection:** Selecting the final specific hypotheses (e.g., 3-8 ideas) to push forward to execution.
- **Priority ordering:** Which ideas to test first (cheapest data requirement, highest expected insight).

**CONVERGE** with an explicit keep/cut test — keep an item ONLY if (high owner value) AND (feasible now) AND (fits ethos); else CUT or OPEN-QUESTION. Output an `IN / CUT / OPEN` spec. Show the owner the dimensions surfaced.

---

### Step 2: Execution Planning — The Codebase-Grounded Blueprint (PLAN)

**The Goal:** For each approved idea, define *exactly* how it will be mathematically tested — before writing a single line of code.

Break into small, independently-testable sub-tasks. Builds are SEQUENTIAL (parallel edits to the same files conflict).

**Mandatory Codebase Grounding (the agent must read these files):**

| File | What it teaches the planner |
|---|---|
| `layer3/spine.py` | The METHOD SPINE. All helpers: `load_substrate()`, `segment()`, `maturity_gated()`, `alpha_series()`, `listing_return()`, `distribution()`, `wilson_ci()`, `bootstrap_median_ci()`, `proportion()`, `wipeout_band()`, `outcome_profile()`. **Reuse these. Do not write generic Pandas.** |
| `layer3/config.py` | All constants: `MIN_N_HINT=10`, `MIN_N_TRADABLE=30`, `HORIZONS`, `KEY_HORIZONS=[1y,3y,5y]`, `SEGMENTS=[MB,SME]`, `COHORTS=[boom,longterm]`, `TRUSTED_LISTING_STATUS`, `AS_OF_DATE` (from `substrate_meta.json`). **Never hardcode these values.** |
| `layer3/validate.py` | The cross-regime sign-validation gate: a rule must hold the SAME directional sign in both `boom` (2020-26) and `longterm` (2006-19). If it flips, it is a regime effect, not a robust truth. Also: within-vintage consistency check, fragility heuristic. |
| `rules/index.md` | The tested-signal registry. Confirm the planned test doesn't duplicate an existing verdict. |
| `docs/schema.md` | Column definitions. Confirm the required columns exist and are populated for the target cohort. |
| `docs/research/deep_hypotheses_2026-06.md` | Existing curated hypotheses (8 families, ~26 tests). Check if the planned idea overlaps with or extends these. |

**The Hypothesis Testing Protocol — 3 Layers (every test, in this order):**

1. **L1 EXISTENCE** — does the pattern exist at all?
   - Pre-declare the FALSIFIER (what result kills it) before running.
   - PLACEBO wherever possible: fake level / shuffled labels / pre-regulation cohort / pseudo-events matched on confounders. A pattern that also shows up in the placebo is DEAD (this killed F1 and F5a — it earns its keep).

2. **L2 MAGNITUDE & SHAPE** — size, duration, dose-response tables, % of cases affected.
   Monotonicity across buckets matters more than a single split.

3. **L3 PLAYBOOK** — the conditional TRADE: pre-declared entry grid (fixed BEFORE looking), horizons, win-rate / median / P10 / P90 vs the buy-and-hold counterfactual, and the FAILURE CELLS. Report the WHOLE grid — no best-cell cherry-picking.

**Data Conventions (non-negotiable):**
- Exclude `listing_metrics_status == "unreliable_coverage"`.
- Returns = **alpha vs Nifty** (raw secondary). From-listing = secondary buyer; from-issue = allottee.
- Adjusted prices everywhere → use `issue_price_adj` (not `issue_price`) against `data/prices/*.csv`.
- Min-N floors: <12 suppress · 12–29 say "thin" · ≥30 report. Always print N.
- Distributions over means (median + P10/P90); medians for skewed outcomes (the 2.09×-mean-vs-1.18×-median lesson).
- Cross-regime gate: a headline cell must hold in boom (2020–25) AND longterm (2006–19), ideally MB and SME separately (the 4-cell check). One-cohort effects = "boom-only/MIXED", not validated.
- OOS where horizons permit: train ≤2021, test ≥2022 (or the 2026 forward cohort).

**Look-Ahead Traps (each was actually caught in this project):**
- `days_to_peak`, lifetime turnover, anything computed over the FULL window then used to classify at entry (F5b's touch-and-fail used future 60d — never tradable).
- Trailing/rolling features must be point-in-time: only data from BEFORE the row's listing/event date (≥5 priors or null). Regime features: `layer3/regimes.py` (already PIT-safe).
- Endpoint columns (`alpha_1y` etc.) start at LISTING — if your signal forms at day X, measure forward returns from day X+1 (the F5e graduation required the d91→d341 re-test).
- No reverse-causation: a feature that's actually an outcome (e.g., CURRENT `market_cap_class` — a wipeout reads "micro" because it crashed, not because it was micro at IPO).

**Score Policy (LOCKED: "evolve-only-if-robust"):**
A surviving signal enters the weighted score ONLY if it improves OOS top-quintile lift robustly across splits (fold harness: `tools/research/heat_fold_test.py` / `climate_fold_test.py` pattern; folds 2021/2022/2023 × 1y/3y). Otherwise: display-only. Post-listing signals (e.g. the day-90 capitulation flag) are monitoring/exit flags, never score inputs.

**Documentation Output:** Execution plan appended to the Single Dynamic Dossier.

---

### Step 3: Code Generation & Testing (BUILD — TDD)

- **TDD:** Failing test → minimal code → green → commit. Small steps, frequent commits.
- **Environment:**
  - `PYTHONPATH=. .venv/bin/python` (plain `python` doesn't exist on this box).
  - **No scipy/statsmodels** → no `.corr(method="spearman")`. Use the srho helper (rank both, then pearson) — copy from `tools/research/wave2_substrate.py`.
  - `wc -l` lies on the CSVs (embedded newlines) — count records via the `csv` module / DuckDB.
  - Price files: `data/prices/<isin>.csv` (date,open,high,low,close,volume), already split/bonus adjusted; filter `date >= listing_date` and re-index to trading days from listing.
- **Scripts:** Live in `tools/research/`. Copy conventions of existing ones (e.g., `wave2_substrate.py`, `wave2_pricepath.py`). Use `spine.py` functions.
- **Data:** Load substrate via `spine.load_substrate()`.
- **Git:** LOCAL-ONLY. Never push. Never add a remote. Company laptop: Playwright OFF by default, Streamlit localhost-only, no secrets tracked.

---

### Step 4: The Peer Review Board (REVIEW — The Specialized Swarm)

The post-build review repeatedly catches what pre-build divergence cannot — INCLUDING new errors the build/fix itself introduced (proven twice on 2026-06-08). FULL path: independent review is NON-NEGOTIABLE for money/score numbers. The owner does NOT read code, so the review agent IS the quality gate.

Before the human sees test results, a swarm of specialized reviewers examines the work:

**Reviewer 1 — The Code Auditor:**
- Are Pandas merges correct? (ISIN is the ONLY automatic join key; name-matching never merges.)
- Does the code use `spine.py` helpers correctly?
- Are there off-by-one errors in date filtering?
- Does the code accidentally drop delisted rows (survivorship bias)?
- Is `listing_metrics_status` filtered correctly?
- Run the test suite: `PYTHONPATH=. pytest tests -q` must be green.

**Reviewer 2 — The Logic & Math Auditor:**
- Are percentage calculations correct? (alpha = return − benchmark, not return / benchmark)
- Does the code use median + P10/P90 (not just mean)?
- Are Wilson CIs used for proportions (not naive p ± 1.96√(p(1-p)/n))?
- Is the Min-N floor enforced? Are "thin" results labeled?
- Does the 4-cell check (MB×boom, MB×longterm, SME×boom, SME×longterm) actually run?

**Reviewer 3 — The Fluke & Bias Checker (The Falsifier):**
- **The Causality Test:** "Does this result make logical, economic sense?" Not just "is it statistically significant?"
    - *Example PASS:* "High GMP correlates with strong 3-day listing performance. This makes logical sense: GMP reflects immediate retail momentum/hype, which carries over to the first few trading sessions where the same crowd is buying."
    - *Example REJECT:* "High GMP correlates with 10-year wealth generation. REJECT. It is logically impossible for pre-listing retail hype to dictate a company's business fundamentals for a decade. This correlation is noise, likely driven by a small N of survivor-biased winners."
- **Look-Ahead Trap Check:** Does any feature use information from AFTER the decision point?
- **Reverse-Causation Check:** Is any feature secretly an outcome?
- **Placebo Check:** Did the placebo/falsifier run? Did the real signal significantly exceed the null distribution?
- **Cross-Regime Consistency:** Does the signal hold the same sign in both `boom` and `longterm`? If not → "MIXED — regime effect, not robust."
- **Within-Vintage Consistency:** Does the signal hold in a majority of individual listing years? (The `_within_vintage` check in `validate.py` — cross-regime alone can miss vintage-level noise.)
- **Fragility Assessment:** Is the binding sample N large enough? Is within-vintage consistency ≥60%? (`validate.py` heuristic: `min_n >= MIN_N_TRADABLE` + `cons/tested >= 0.6` → "robust".)

Check output against the **DATA-TRUTH INVARIANTS** (§below).

**The Disagreement Rule:** If reviewers conflict on anything showing a NUMBER, the red-team/falsifier (Reviewer 3) wins. Otherwise, surface the trade-off to the owner.

---

### ⏸️ HUMAN CHECKPOINT 2: Review of Results & Reasoning

The pipeline pauses. The human reviews the Single Dynamic Dossier containing:
1. What was tested (from Step 1 + Step 2)
2. The raw results (from Step 3)
3. The Peer Review Board's verdicts with reasoning (from Step 4)
4. For each idea: PASS (with causal explanation) / REJECT (with reason) / NEEDS MORE DATA

The human can:
- Accept a finding and promote it
- Reject a finding the reviewers passed (override)
- Request additional testing on a borderline result
- Ask "why did this pass/fail?" and get the full reasoning chain

---

### Step 5: Fix → Re-Review Loop

Loop review↔fix until a pass finds ZERO new substantive findings.

**STOP RULE:** If a 3rd pass still finds new bugs → STOP and escalate to the owner (don't grind).

---

### Step 6: Test + Verify

- `PYTHONPATH=. .venv/bin/pytest tests -q` — all green.
- `.venv/bin/python verify.py` — clean (counts, schema gate, backup match, MAP.md regenerated).

---

### Step 7: Record & Clean Up

1. Append the verdict + numbers to `rules/index.md` (so it's never re-tested blind).
2. Append the verdict to `docs/research/tier1_wave1_verdicts.md` (the ledger).
3. Append a task entry to `docs/research/task_log.md` (see §Checkable Artifacts).
4. Update `STATUS.md` (live state only; completed work leaves STATUS — history = git log).
5. Update `project_map.py` if structure changed.
6. Script stays in `tools/research/` (reproducibility).
7. Commit with the pipeline trailer: `Pipeline: path=FULL diverge=3 review=agent tests=green`.

**DONE = ALL of:** criteria met · review clean (or placebo passed) · suite+verify green · docs updated · committed with trailer · task_log entry closed · verdict honest. Anything open → not done.

---

### ⏸️ HUMAN CHECKPOINT 3 (Optional): Score Promotion Decision

If the signal PASSED all reviews and the human wants to consider adding it to the live weighted score:
- The signal must pass the `evolve-only-if-robust` OOS gate (top-quintile lift across splits).
- Fold harness: `tools/research/heat_fold_test.py` / `climate_fold_test.py` pattern; folds 2021/2022/2023 × 1y/3y.
- Default is conservative: **display-only** unless robustly proven.
- The human makes the final call on promotion.

---

## DATA-TRUTH INVARIANTS

Check at REVIEW + VERIFY — the hard-won rules. Violating one = a wrong number.

- **Survivorship-honest:** delisted → terminal (compulsory/wipeout = −100%, else last price); failed names STAY in the denominator (never silently dropped).
- **Never pool** modes (live/gap_filled/backfilled/historical_sim) or segments — judge MB/SME × boom/longterm separately (the 4-cell check).
- **Min-N floors** (suppress <12, "thin" 12-29, full ≥30) + **distributions over means** (median + P10/P90; a few winners drive the mean — the 2.09×-mean-vs-1.18×-median lesson).
- **Evidence-strength labeled** always (live = forward truth · sim/backfill = rehearsal/OOS); headline the HONEST number (median, correct benchmark, correct units) — never the flattering one.
- **No look-ahead** (no future-window classification, lifetime stats, days_to_peak). **No reverse-causation** (a feature that's actually an outcome, e.g. post-crash market_cap).
- **Refactor = behavior-identical PROOF** (before/after on real rows; data/master byte-identical) before calling a dedup/cleanup safe.

---

## STANDING CONSTRAINTS (always)

Verify from GROUND TRUTH, never memory (`wc -l` LIES on the CSVs — count via csv/DuckDB). Env: `PYTHONPATH=. .venv/bin/python`; NO scipy/statsmodels (use the srho/Wilson/bootstrap pure-Python helpers). **GIT IS LOCAL-ONLY** — never add a remote / push. Company laptop: Playwright OFF by default (`docs/playwright_on_off.md`), Streamlit localhost-only, no secrets tracked.

---

## THE CHECKABLE ARTIFACTS

Makes "followed the pipeline" a FACT on disk, not a claim.

**`docs/research/task_log.md`** — append-only, ONE entry per non-trivial task. Doubles as crash-resume (an agent died mid-task on 2026-06-08; a log survives that). Template:
```
## YYYY-MM-DD — <task one-liner>  [path: FULL|LIGHT|HYPOTHESIS|HOTFIX]
scope: <data confirmed?>  · diverge: <lenses / agent ids>  · converge: <spec / IN-CUT>
build: <commits>  · review: <agent verdict / placebo result>  · tests: <suite> · verify: <clean?>
verdict: <honest outcome>
```

**Commit trailer** on the task's final commit: `Pipeline: path=FULL diverge=3 review=agent tests=green`.

**verify.py tripwire:** warns when the latest commit changed substantive code (layer3/pipeline/scrapers/app/tools) but didn't touch task_log.md — so a skipped pipeline is visible, not silent.

---

## UX & Documentation Strategy — The Single Dynamic Dossier

**Problem:** Too many `.md` files confuse the human. Complex folder structures hide information.

**Solution:** For each research task, the agents maintain ONE file: `agent_workspace/dossiers/YYYY-MM-DD_<task_slug>.md`.

As the pipeline progresses, each step APPENDS to this file under clear headers:
```markdown
# Research Dossier: <Task Name>
## Prior Art Report (Step 0b)
## Ideation Explosion (Step 1)
## ⏸️ Human Checkpoint 1 — Pruning Notes
## Execution Plan (Step 2)
## Results (Step 3)
## Peer Review (Step 4)
## ⏸️ Human Checkpoint 2 — Decision
## Verdict & Registry Entry (Step 7)
```

The human only ever needs to open ONE file to see the full journey of an idea from seed to verdict.

---

## Model Routing Strategy

| Step | Requirement | Model |
|---|---|---|
| Step 0 (Triage) | Fast classification | `gemini-2.5-flash` |
| Step 0b (History Check) | File reading + matching | `gemini-2.5-flash` |
| Step 1 (High Ideation) | Deep reasoning, chain-of-thought | `gemini-2.5-pro` or CLI offload (highest quality) |
| Step 2 (Execution Planning) | Codebase reading + logic | `gemini-2.5-pro` or CLI offload |
| Step 3 (Code Generation) | Code writing + testing | `gemini-2.5-pro` or CLI offload |
| Step 4 (Peer Review Board) | Each reviewer: focused analysis | `gemini-2.5-flash` (parallelizable; 3 independent reviewers) |
| Step 7 (Recording) | Documentation | `gemini-2.5-flash` |

**Rate-limit safety:** On the free tier, parallel `pro` calls may hit 429 errors. Use "CLI Offloading" (pasting complex logic into the Antigravity chat) as a fallback for Step 1 and Step 2.

---

## Future Integration (TODO — tracked in `setup.md`)
- **File-Based IPC:** LangGraph writes `handoff.md` → Antigravity CLI processes it → writes `approved.md` → LangGraph resumes.
- **LangGraph Studio / Web App Visualizer:** Once the engine is proven in the terminal, wrap it in a visual UI for graphical node-maps and clickable Approve/Reject buttons.

---

## KICKOFF (paste at task start)

> A non-trivial task is picked. Triage the path, then execute the steps in this document:
> scope-data → history-check → diverge (parallel multi-lens agents, chain-of-thought explosion,
> fixed output contract) → ⏸️ human prune/expand → plan (codebase-grounded) → build (TDD) →
> peer review board (code + math + falsifier) → ⏸️ human review → fix-to-stop-rule → test+verify
> → cleanup with task_log entry + pipeline commit trailer. Honor the DATA-TRUTH INVARIANTS and
> STANDING CONSTRAINTS. If skipping a stage, say which and why up front.
