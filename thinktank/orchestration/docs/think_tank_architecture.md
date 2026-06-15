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

**The Logical Validity Gate:** The Triage Agent must evaluate the core premise. If the hypothesis relies on a logically impossible causal mechanism (e.g., "a company's name length physically alters market dynamics"), it MUST reject it as 'LOGICALLY SUSPECT' even if it is novel.

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

### Step 1.5: The Pre-Checkpoint Review Agent (CONVERGE)

Before the human sees the massive brainstorm, an automated Review Agent executes an explicit **keep/cut test** on the raw 20-40 ideas:
- **Rule:** Keep an item ONLY if (high owner value) AND (feasible with our owned data schema) AND (fits ethos).
- **The Proxy Test:** Actively check if the hypothesis is a spurious correlation or proxy for a confounding variable (e.g., sector, market cap, issue size). If the proposed signal is likely just a noisy proxy for a known factor, mark it CUT.
- **Output:** The agent outputs a pre-sorted `IN / CUT / OPEN` specification list. It must briefly justify why trivial or data-impossible ideas were moved to CUT.

---

### ⏸️ HUMAN CHECKPOINT 1: The Pruning & Expansion

The human reviews the Review Agent's pre-sorted `IN / CUT / OPEN` list. The human acts as the Portfolio Manager:
- **Review:** The human reads the sorted list, saving them the effort of reading 40 raw ideas.
- **Move:** The human can drag ideas around—promoting a CUT idea to IN, or moving an IN idea to CUT if they disagree with the Review Agent.
- **Expansion:** The human can manually add new ideas or inject their own domain knowledge.
- **Selection:** The human selects the final specific hypotheses (e.g., 1-3 ideas) to push forward to execution.

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

### Step 4.5: The Final Judge (STRUCTURE)

After the three Swarm reviewers produce their combined feedback (which can be extremely long and dense), the Final Judge agent distills the noise into an actionable structure:

1. **Verdict:** Declares a definitive `PASS` or `FAIL`. If there are ANY critical bugs, look-ahead traps, or falsification failures → `FAIL`. If all issues are minor suggestions → `PASS`.
2. **Structured Issues:** Extracts each distinct unresolved issue into a numbered JSON array: `[{"id": 1, "description": "Short summary of issue"}]`. This is what the UI renders as separate input boxes so the human can give targeted directives per issue.

**Why this step exists:** The raw Swarm feedback is a wall of text from 3 reviewers. Without the Final Judge, the human would have to manually parse thousands of words to understand what actually needs fixing. The Judge acts as the editorial layer between the Swarm's raw analysis and the Human Checkpoint.

**Output:** `swarm_verdict` (PASS/FAIL) + `unresolved_issues` (JSON array) added to state.

---

### Step 5: The Self-Correction Loop (BUILD → REVIEW → FIX, with Decaying Retries)

The pipeline does NOT stop after one Build→Review cycle. It enters a **decaying retry system** designed to maximize autonomous correction while preventing infinite grinding:

**Phase A — Autonomous Inner Loop (2 cycles max):**
Immediately after the Execution Plan is approved at Human Checkpoint 1, the system enters a tight loop:
1. Step 3 (Build Agent) generates the code.
2. Step 4 (Peer Review Swarm) reviews the code.
3. Step 4.5 (Final Judge) issues a PASS/FAIL verdict.
4. If FAIL: The Swarm's feedback is injected back into the Build Agent's prompt as `prior_swarm_feedback`, and the loop repeats.
5. If PASS: The loop breaks immediately and proceeds to Human Checkpoint 2.

This loop runs up to **2 times** autonomously. If it can't fix itself in 2 tries, a 3rd autonomous attempt rarely helps — human judgment is needed.

**Phase B — Human-Guided Outer Loop (unlimited retries):**
If the autonomous loop exhausts both cycles without a PASS, the pipeline pauses at Human Checkpoint 2. The human is presented with:
- The full **Execution History** (Run 1, Run 2) showing how the code evolved and what the Swarm kept flagging.
- A **per-issue directive text input** for each distinct unresolved issue from the Final Judge.

The human types targeted directives (e.g., "Ignore the look-ahead warning on the SMA, we are using point-in-time data") and clicks **"Refine & Retry"**. This injects the human directives into the Build Agent's prompt and runs **2 more autonomous cycles**. The human can repeat this as many times as they want — there is no hard cap on human retries because the human is consciously deciding to spend the tokens each time.

**Token Budget:** Each Build→Review cycle = 5 LLM calls (Build + 3 Reviewers + Final Judge). The happy path (PASS on first try) costs **9 total calls** (4 setup + 5 loop). The autonomous worst case costs **14 calls** (4 setup + 2×5 loop). Each human "Refine & Retry" click adds up to 10 more calls (2 inner cycles × 5).

**STOP RULE:** The autonomous loop MUST stop after 2 cycles. The human loop has no artificial cap — the human decides when to stop and record a verdict.

---

### ⏸️ HUMAN CHECKPOINT 2: Review of Results & Reasoning

The pipeline pauses and presents a structured interactive UI:

**Execution History Panel:**
The UI displays tabbed views for each Build→Review run (e.g., `Run 1 (FAIL)`, `Run 2 (FAIL)`, `Run 3 (PASS)`). Each tab shows:
- The generated Python code for that run
- The Peer Review Swarm's full feedback for that run
- The Final Judge's verdict for that run

This allows the human to trace exactly how the code evolved and what the Swarm kept flagging across iterations.

**Human Interaction Layer:**
If the final verdict is FAIL:
- Each distinct unresolved issue from the Final Judge is rendered as a **separate text input box** (e.g., "Issue 1: GARCH model non-convergence risk" → [text input]).
- The human can type a specific directive per issue (e.g., "Wrap in try-except and skip tickers with <50 observations").
- A **"Refine & Retry"** button injects the directives and kicks the system back into the inner loop.

If the final verdict is PASS:
- The issues are still shown (for optional review), but framed as minor notes.
- The human can proceed directly to recording the verdict.

**Final Decision:**
The human selects one of:
- **PASS** — The code and logic are accepted. Proceed to Step 7 (Record).
- **REJECT** — The hypothesis is killed. Proceed to Step 7 (Record with REJECT verdict).
- **NEEDS REVISION** — Log the current state and defer to a future session.

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
8. **Write the full Execution History to the Single Dynamic Dossier.** The dossier must capture every Build→Review run (code, feedback, verdict) so the human can audit the full self-correction journey. Do not write only the final state — intermediate attempts are valuable diagnostic data.

**DONE = ALL of:** criteria met · review clean (or placebo passed) · suite+verify green · docs updated · committed with trailer · task_log entry closed · verdict honest · dossier contains full execution history. Anything open → not done.

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
## Execution History (Step 5 — Self-Correction Loop)
### Run 1
#### Generated Code
#### Peer Review Feedback
#### Verdict: FAIL
### Run 2
#### Generated Code
#### Peer Review Feedback  
#### Verdict: PASS
## ⏸️ Human Checkpoint 2 — Decision & Directives
## Verdict & Registry Entry (Step 7)
```

The human only ever needs to open ONE file to see the full journey of an idea from seed to verdict, including every self-correction attempt.

---

## Model Routing Strategy

**Current Implementation:** All steps use a single model controlled by the `THINKTANK_MODEL` environment variable (default: `gemini-3.1-flash-lite`). This is a temporary testing configuration.

**Target Architecture (requires paid API subscriptions — see §Model Viability TODO in `setup.md`):**

| Step | Requirement | Ideal Model Tier | Rationale |
|---|---|---|---|
| Step 0 (Triage) | Fast classification + logical validity check | Cheap/Fast (e.g., Flash) | Simple yes/no + brief reasoning |
| Step 0b (History Check) | File reading + matching | Cheap/Fast | Pattern matching against existing docs |
| Step 1 (High Ideation) | Deep reasoning, chain-of-thought | **Frontier** (Claude Sonnet / Gemini Pro) | Most valuable step — quality here determines everything downstream |
| Step 1.5 (Review Agent) | Critical filtering + proxy detection | **Frontier** | Must detect spurious correlations and confounding variables |
| Step 2 (Execution Planning) | Codebase reading + logic | **Frontier** | Must understand existing helpers and produce grounded plans |
| Step 3 (Code Generation) | Code writing + testing | **Frontier** | Must write correct, idiomatic code using project conventions |
| Step 4 (Peer Review Board) | Each reviewer: focused analysis | Mid-tier (parallelizable; 3 independent reviewers) | Can be cheaper since each reviewer has a narrow, focused task |
| Step 4.5 (Final Judge) | Verdict + issue extraction | Mid-tier | Structured JSON extraction from existing text |
| Step 7 (Recording) | Documentation | Cheap/Fast | Template-filling, no reasoning needed |

**Key Insight from Testing (2026-06-15):** The free-tier `gemini-3.1-flash-lite` model successfully ran the full pipeline end-to-end, proving the orchestration framework works. However, it lacked the reasoning depth to:
- Reject a fundamentally flawed hypothesis ("IPO name length affects stock price") at the Triage stage
- Detect that "name length" is a spurious proxy for sector/market-cap at the Review stage
- Push back on the premise even when placed in the Falsifier persona (it flagged issues but still let it through)

A frontier model (Claude 3.5 Sonnet, Gemini 2.5 Pro) would have caught these at Step 0.

**Rate-limit safety:** On the free tier, parallel calls may hit 429 errors. The `THINKTANK_MODEL` env var allows instant model swapping without code changes. See the **Model Viability & Subscriptions TODO** in `setup.md` for the plan to integrate paid API tiers.

---

## Future Integration (TODO — tracked in `setup.md`)
- **File-Based IPC:** LangGraph writes `handoff.md` → Antigravity CLI processes it → writes `approved.md` → LangGraph resumes.
- **LangGraph Studio / Web App Visualizer:** Once the engine is proven in the terminal, wrap it in a visual UI for graphical node-maps and clickable Approve/Reject buttons.
- **Model Viability & Subscriptions:** Determine how to integrate frontier models (Claude, Gemini Pro) for production use. Map API subscriptions vs consumer Pro subscriptions. Route expensive steps (Ideation, Planning, Code Gen) to frontier models and cheap steps (Triage, Recording) to flash-tier models. See `setup.md` for full details.
- **Per-Step Model Routing:** Replace the single `THINKTANK_MODEL` env var with a per-step routing config (e.g., `THINKTANK_MODEL_IDEATION`, `THINKTANK_MODEL_REVIEW`) so different steps can use different model tiers.

---

## State Schema (`ThinkTankState`)

The LangGraph pipeline passes the following TypedDict between nodes:

| Key | Type | Produced By | Consumed By | Purpose |
|---|---|---|---|---|
| `task_description` | `str` | Input | Step 0, 7 | The original user prompt |
| `dossier_path` | `str` | Input | Step 7 | Output directory |
| `prior_art_report` | `str` | Step 0 | Human, Step 7 | Summary of novelty/logical validity |
| `raw_ideas` | `str` | Step 1 | Step 1.5, 7 | The 20-40 chained hypotheses |
| `sorted_ideas` | `str` | Step 1.5 | Human Checkpoint 1 | `IN/CUT/OPEN` JSON array |
| `approved_ideas` | `str` | Human | Step 2, 7 | Pruned list of ideas to test |
| `execution_plan` | `str` | Step 2 | Step 3, 4, 7 | Codebase-grounded blueprint |
| `code_execution_result`| `str` | Step 3 | Step 4, 5, 7 | Generated Python code |
| `peer_review_feedback` | `str` | Step 4 | Step 4.5, 5, 7 | Combined swarm critique |
| `swarm_verdict` | `str` | Step 4.5 | Step 5, Human Checkpoint 2 | `PASS` / `FAIL` |
| `unresolved_issues` | `List[dict]` | Step 4.5 | Human Checkpoint 2 | `[{"id": 1, "description": "..."}]` |
| `execution_history` | `List[dict]` | Step 5 | Human Checkpoint 2, 7 | Log of all self-correction loops |
| `prior_swarm_feedback` | `str` | Step 5 | Step 3 | Feedback injected into next build |
| `human_directives` | `str` | Human | Step 3 | User overrides per issue |
| `human_retry_count` | `int` | Human | UI | Tracks manual interventions |
| `final_verdict` | `str` | Human | Step 7 | `PASS` / `REJECT` / `NEEDS REVISION` |
| `messages` | `List` | All | All | Chat transcript (append-only) |
| `errors` | `List[str]` | All | All | System-level error log |

---

## KICKOFF (paste at task start)

> A non-trivial task is picked. Triage the path, then execute the steps in this document:
> scope-data → history-check → diverge (parallel multi-lens agents, chain-of-thought explosion,
> fixed output contract) → ⏸️ human prune/expand → plan (codebase-grounded) → build →
> peer review swarm (code + math + falsifier) → final judge (verdict + structured issues) →
> self-correction loop (3 autonomous cycles, decaying to 2 human-guided retries) →
> ⏸️ human review (per-issue directives, execution history) → test+verify
> → cleanup with task_log entry + pipeline commit trailer + full execution history in dossier.
> Honor the DATA-TRUTH INVARIANTS and STANDING CONSTRAINTS.
> If skipping a stage, say which and why up front.
