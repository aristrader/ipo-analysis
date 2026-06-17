# Improvement backlog — OPEN items only (the single living menu)

> **This lists only what's LEFT to do.** Completed work → git log (history) + `rules/index.md` (signal verdicts).
> Map of all research docs → `docs/research/INDEX.md`. Deeper rationale for feeder ideas → archived planning docs.
>
> Ethos: only-what-works (3-layer validated) · free data · no ML · analog-based · survivorship-honest.
> Each item runs through `execution_pipeline.md`. Status: ⚪ proposed · 🟡 partial · 🔬 research/data-gated. Effort S/M/L.

> **Done in the 2-night batch (2026-06-09/10) — see git log:** A1 (→display-only via review), A2, A3, B1, C2,
> D3/H7, E1, H-MVP, weak-sub guard, I1, J1, J2, app honesty/nav polish. **Net: zero new live-score components
> (all tested signals landed display-only/reject/redundant — the honest outcome).**
> **Done 2026-06-10 (babysat session):** D1/D4 (NSE announcement context feed + full-history pull), **A1b
> (banker coverage-guard hybrid → PROMOTED LIVE by independent review — the ONE signal change that cleared the
> bar: recovers recall + keeps the false-veto fix).**
> **Done 2026-06-11:** A1c (richer banker-quality — built + tested + reviewed → NO live change: return DEAD
> cross-regime, downside shelved-at-parity, pricing-discipline→pop real-but-display-only; `a1c_banker_quality_2026-06-11.md`).

---

## 🔴 D-1 CORP-ACTION FIX — ⛔ NOT BUILD-READY (R11 2nd-adversarial 2026-06-17 found B1-HIGH small-bonus-drop + B2-MED coverage-boundary). NEXT: fold the `detect_gap` ROOT redesign (ratio-aware + structured return → resolves B1+B2+NIT-1) → targeted re-verify → THEN build. 🚦 HELD.
The split/bonus over-counting bug (ROLEXRINGS fake +15,272%). **Design:** `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`.
**Plan:** `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md` (10 TDD tasks; reviewed, 1 bug fixed). Principle = "price disposes".
Fixes D-1 + D-2 + T-2 + T-4 in one effort; T-3 re-derive is a follow-up. **Confidence invariant:** final values ONLY for
confidently-resolved stocks; everything unsure → flag+null (never guess). **Execution: subagent-driven TDD, gated on owner go.**

### D-1 FOLLOW-UP TODOs — SEPARATE later tasks, NOT part of the D-1 build
> These (TODO-D1a–f) are distinct tasks that **follow** the D-1 build (the plan's Tasks 0–12); **none are part of that build.**
> They're grouped here only because D-1 enables/seeds them. Each is picked up later, on its own. (TODO-D1c — the reproducibility
> OVERLAY — is its own foundational *campaign*, see its note; the D-1 build uses a targeted patch precisely to avoid needing it now.)
- **TODO-D1a — STRICT: resolve all flagged corp-action rows.** They will move the numbers materially; **many may be GENUINE
  WIPEOUTS** (not data errors). Classify each: real wipeout (−100%) / data error / real split w/ missing price data. Carry
  per-stock context (price gap vs sources, why uncertain, likely resolution). Source: the override table + the unresolved set +
  Wave-1 evidence (`data/master/review/corp_action_external_evidence.csv`, esp. the 6 STAYS-FLAGGED: CMMIPL, INDUSFILA, BANSAL,
  COOLCAPS, SILVERTUC, VAISHALI). Pick-up-and-finish, don't re-investigate.
- **TODO-D1b — re-derive downstream after the flagged rows are resolved** (bundle w/ D1a). *Targeted* re-derivation of the analysis
  layer (weights, goldens, findings, forward-test, backtests) on the corrected substrate — NOT a naive full pipeline rebuild
  (only safe once D1c exists). Also covers T-3 (re-derive `scorecard_weights.json` + re-bless goldens).
- **TODO-D1c — reproducibility: the remediation-OVERLAY system (the real fix; until it exists we're stuck doing targeted patches).**
  **Problem:** `data/master/ipo_analysis.csv` is NOT reproducible from the pipeline — after the last full run, **manual hand-fixes +
  DRHP staging + `data/reference/manual_overrides.csv`** were layered on top. So **any future full pipeline re-run silently WIPES those
  hand-fixes**, and we'd have to re-apply them by hand every time — error-prone, doesn't scale (this is exactly why D-1 uses a *targeted patch*, not a re-run).
  **Goal:** `fresh pipeline output + applied overlay = the substrate`, **reproducibly** — i.e. **DETERMINISTIC / IDEMPOTENT
  END-TO-END: re-running the whole thing produces the EXACT same substrate every time** (definite rules, no hand-step,
  no drift). This is a SEPARATE problem from the D-1 corp-action pipeline fix (D-1 = a targeted patch that avoids re-running).
  **The hard parts (owner-flagged 2026-06-17 — design for ALL of these):**
  1. **Capture** every post-pipeline hand-fix in a structured, machine-applicable form (not prose): target row (key = symbol∪ISIN) + column,
     old→new value, REASON/provenance, date. (The D-1 Task-8 manual-remediation INVENTORY is the first catalog of these — build the overlay ON it.)
  2. **ORDER / sequencing** — hand-fixes can be **order-dependent** (fix B builds on fix A's output; two fixes touch the same cell). The overlay
     must record + replay them in a **deterministic order**, not as an unordered bag — re-running the pipeline then re-applying must reproduce the exact substrate.
  3. **Idempotency** — applying the overlay twice == applying it once (no double-application / corruption).
  4. **Conflict detection** — when a fresh pipeline run now produces a value a hand-fix was overriding: policy = the hand-fix (a correction) usually
     wins, BUT **flag** when the underlying pipeline value changed, so an obsolete hand-fix gets re-reviewed instead of silently masking newly-correct data.
  5. **Provenance + retire-ability** — each overlay entry records WHY it exists, so once the pipeline itself is fixed to emit the right value, that entry can be retired.
  **Sequencing:** D-1's Task-8 inventory → this todo formalizes that catalog into the ordered/idempotent/conflict-aware overlay + apply-step.
  Once it exists, TODO-D1b's re-derive can become a **safe full re-run** instead of a targeted re-derive.
  **PRIORITY + PROCESS (owner 2026-06-17): this is FIRST among the big foundational items — when undertaken it is a FOCUSED CAMPAIGN that
  STOPS all other development** (no concurrent data changes while reconciling). The flow: (1) build the overlay system → (2) create the overlay
  file (seeded from the Task-8 inventory) → (3) regenerate the substrate fresh (`pipeline output + overlay`) → (4) **DIFF against the current
  substrate**: **EVERY mismatch is a BUG — in the NEW data (a pipeline/regen error) OR the OLD data (a stale/incorrect hand-fix)** — and each gets a
  **REVIEW + RESOLUTION** (never auto-accepted; classify which side is wrong, fix it). (5) Only once **every mismatch is resolved and the data is
  TRUSTED** do we declare the reproducible `pipeline + overlay = substrate` setup LIVE. NB: this reconciliation is itself the mechanism that surfaces
  latent data bugs in BOTH directions — so it doubles as a full data-integrity sweep. Do NOT rush it; data correctness is the whole point.
- **TODO-D1d — live corp-action capture (when we go live).** Wire the rebuilt `03h/03j/03k/03l` into `run_refresh.py`; store a
  **`corp_actions_as_of`** watermark in `substrate_meta.json`; live-capture pulls from **watermark − ~1 month** (overlap buffer).
  Interim safety net = the Phase-2 continuity guard (flags an un-captured split as an unexplained jump).
- **TODO-D1e — broader data-integrity checks (separate flag-only batch).** implied-shares cross-check (O-12), price-band invariant
  (O-13), date-ordering (O-11), EPS reconciliation (O-5/O-7), systemic 0→NaN at load (I1). Flag, never auto-fix.
- **TODO-D1f — Wave-2 corp-action web evidence (deferred, NOT skipped).** phantom (84 stocks) + single-source (56) — optional
  labeling; the price-disposes logic already handles these by construction (no gap → reject; gap → accept). Run later for tidiness.

## 🧹 LOW-BUCKET CLEANUP QUEUE (decided 2026-06-17 — ready to execute as branch→TDD→review→PR)
- **SR-1** — `think_tank_architecture.md` "supersedes" claim → **reframe** to WIP/forward-looking ("intended unified arch; once operational it supersedes; until then `execution_pipeline.md` + `hypothesis_protocol.md` remain canonical"). Standing briefs stay canonical. (Ties to META-O.)
- **SR-8/9** — fix 3 LIVE wrong `improvement_backlog` paths (`docs/research/` → `docs/tracker/`) in STATUS.md, thinktank/memory/README.md, think_tank_architecture.md. LEAVE the historical `task_log.md:40` (git holds the move history). Bundles w/ SR-1 on think_tank_architecture.md.
- **SR-10** — **regenerate** `docs/research/INDEX.md` via a simple generator (`os.walk` + first-line description + active/archived grouping; wired into verify.py like MAP.md). Do NOT auto-infer semantic categories (those live in backlog/rules/git). Replaces the stale hand-maintained snapshot.

## 🧹 DOC-ALIGNMENT — anti-sprawl consolidation (owner 2026-06-17) · QUEUED: discovery-first, fix-after-D-1
**The problem (owner, in their words):** "too many docs, too many places, things scattered — it should all be aligned properly."
The 2026-06 audit + D-1 work spun up many docs; state is now spread across overlapping surfaces and some info is duplicated/stale.

**Canonical-home map (the TARGET — one home per info type):** open work → THIS file (`improvement_backlog.md`) · signal/strategy
verdicts → `rules/index.md` · history → **git log** (never duplicate) · repo structure/DAG → `project_map.py` (→ generated `MAP.md`) ·
live "where are we" → `docs/tracker/STATUS.md` · conventions/decisions → `CLAUDE.md` · per-task execution proof → `docs/tracker/task_log.md` ·
research-doc index → `docs/research/INDEX.md` (should be GENERATED, see SR-10).

**Known issues to fix (seed list — the discovery pass will complete it):**
- TEMP/working docs to consolidate-then-archive once their threads close: `alignment_audit_2026-06-16.md`, `structure_review_2026-06-16.md`,
  `doc_drift_review_2026-06-16.md`, `doc_alignment_audit_2026-06-17.md`, and the **full D-1 review/evidence trail (~10 docs!):**
  `d1_plan_review`, `d1_plan_rereview`, `d1_join_strategy`, `d1_plan_final_verify`, `d1_final_implementability`, `d1_final_correctness`,
  `d1_plan_targeted_reverify`, `d1_adversarial`, `d1_remediation_inventory` (+ any further re-verify) — all under `docs/research/`.
  **AFTER D-1 ships: archive the WHOLE `d1_*` review trail** (their verdicts/history → git log + the merged code); **KEEP only the spec + plan**
  as the durable design record (or archive those too once merged). D-1 alone spun up **~11 docs** — this consolidation is NON-optional, it's the
  poster child for the DATA & RULES ARCHITECTURE + DOC-ALIGNMENT need. (Delete/merge/fix each: review docs → archive; verdicts → git/rules; nothing duplicated.)
- `INDEX.md` stale + hand-maintained → **regenerate** (SR-10, decided). `MAP.md` → already generated; keep it the only structure map.
- "supersedes" confusion (SR-1, decided) · wrong-path refs (SR-8/9, decided) · orphan transition doc `claude_transition_and_open_threads.md` (SR-5).
- DUPLICATION to hunt: the same fact (counts, status, verdicts, paths) stated in >1 place; anything in a doc that belongs in git log / rules / project_map.

**Plan: discovery FIRST (find, don't fix), then fix after D-1 + low-bucket land.**
- ✅ **DISCOVERY pass DONE (2026-06-17):** catalog at `docs/research/doc_alignment_audit_2026-06-17.md` — **DA-1…DA-14** (most prior SR/DD
  items already fixed by PRs #2/#3; verify.py PASSES). Top new: DA-1 INDEX.md badly drifted (lists 6 archived as active, misses ~37 subdir docs →
  regenerate = SR-10), DA-2 CLAUDE.md cites 5 run-scripts at root but they're in `scripts/`, DA-3 CLAUDE.md "8-component" (line 26) vs a 5-item
  list (line 116) — residual of the DOC-2 fix, DA-4 README "STATUS.md (root)", DA-8 setup.md dups thinktank arch, DA-9 PRODUCT.md overlaps CLAUDE.md.
  Temp-docs-to-archive identified (structure_review + doc_drift_review archivable now; alignment_audit keep till its 14 items close; 4 D-1 docs after D-1;
  claude_transition = orphan, harvest its 3 open architectural decisions → here, then delete). (Catalog is itself a temp doc the fix consumes.)
- ⏳ **FIX pass (after D-1):** action the catalog — move each scattered/duplicated bit to its canonical home, regenerate INDEX/MAP, archive/delete the
  spent working docs, retire `alignment_audit` once ALL its items close. Goal: a reader lands in ONE place per question, nothing duplicated/stale.

## 🧭 GROUND-UP REVIEW / RE-BASE — whole-repo consolidation (owner 2026-06-17; the capstone, after the active churn settles)
**Why:** the 2026-06 audit + D-1 + the review-heavy iterations created a LOT of churn — ~11 D-1 review docs, made-then-superseded edits,
duplicated/stale lines across files. Real bugs got caught, but cruft accumulated. Time to step back and look at the ENTIRE thing (files, lines,
code, docs), keep only what's needed, and **redesign from the base step by step — laying the proven existing work over a clean base.**
**Scope:** whole repo, not just docs (so it SUBSUMES DOC-ALIGNMENT + extends the DATA & RULES ARCHITECTURE repo-wide). Prune dead/redundant
docs+code+lines; consolidate to one home per info-type; reorganize into a clean structure; keep the validated substrate/findings/pipeline/scrapers/D-1 fix.
**NOT a rewrite-from-scratch** — don't throw away validated work; layer the clean base over it (same philosophy as roadmap #1's overlay).
**Guardrails:** the test suite + `verify.py` + git history = the net — prune aggressively but nothing leaves with tests red.
**Timing:** AFTER the active churn settles (can't clean mid-edit) — finish D-1 + low-bucket + doc-alignment → roadmap #1 (reproducibility) → then (or interleaved) this re-base. **Run as its own brainstorm→spec→build campaign** (compute-heavy → Opus). Cross-ref: `roadmap.md`, DOC-ALIGNMENT, DATA & RULES ARCHITECTURE.

## 🗺 POST-D-1 ROADMAP → **see `docs/tracker/roadmap.md`** (the dedicated home: the 3 high-priority items + time budget + model)
In brief, priority order: **1) pipelining/reproducibility** (TODO-D1c + DATA & RULES ARCHITECTURE umbrella below) → **2) pull latest data** (TODO-D1d)
→ **3) think-tank orchestration** (META-O + `think_tank_architecture.md`). All compute-heavy → **highest Claude (Opus)**. Budget: ~3 days, 4h/day + 5h nights. Full detail + timing nuance in `roadmap.md`.

## 🏛 DATA & RULES ARCHITECTURE — the UNIFYING design (owner 2026-06-17; connects the scattered data TODOs — design as a whole, not point-fixes)
**The insight (owner):** the corp-action fix, the overlay, the live-capture, and the data-integrity checks are all FACETS of one
missing thing — a coherent architecture for HOW data goes in, HOW rules are defined, WHICH data matches which entity, WHICH
hypothesis/check applies to which data, how OLD data gets cleaned, and how NEW data is classified/fixed in-place once live.
Worth a dedicated **brainstorm→spec** (like D-1), not scattered patches. The pieces (already captured — CONNECT them under this):
- **Ingestion** — scrapers → pipeline → substrate (exists); + live-capture for new IPOs/actions → **TODO-D1d**.
- **Identity / matching** ("which data matches what") — ISIN is the primary key, BUT corp actions need **symbol∪substrate-ISIN + a
  trading-date window + collision handling** (the D-1 join-strategy learnings — **promote from a D-1 detail to a STANDING matching principle**).
- **Rules / applicability** ("what check/hypothesis applies to which data") — data-integrity checks → **TODO-D1e**; hypothesis-applicability
  by cohort/era/quality-tier (min-N + `data_quality_tier` gating, already a convention) — make the data↔rule mapping explicit.
- **Layering / overlay** ("rules/fixes on file over file") — hand-fixes layered OVER pipeline output (`pipeline output + ordered overlay
  = substrate`) → **TODO-D1c** (the reproducibility spine).
- **Old-data cleanup** — the reconciliation campaign (regenerate → diff → every mismatch is a bug → review+resolve → trust) → **TODO-D1c**.
- **New-data handling (once live)** — classify + apply rules/fixes **IN-PLACE as data arrives**, so we never re-accumulate a hand-fix backlog
  → **TODO-D1d** + the live system. (Owner: do the classify/rules/fixes then-and-there for new records.)
**Sequencing:** design AFTER D-1 (D-1 + its follow-ups surface the concrete requirements); run as brainstorm→spec since it's foundational.
Until then, D1c/D1d/D1e are the concrete pieces and THIS umbrella keeps them coherent. Connects to META-O (model routing) + DOC-ALIGNMENT (one home per info type).

---

## QUICK / OWNED-DATA (no internet — safe to run anytime)
### SCORING-ARCHITECTURE — discuss: one consolidated score vs multiple purpose-specific scores?  ⚪ · DISCUSS · owner 2026-06-11
Open question to scope WITH the owner: should the tool keep ONE consolidated score, or split into MULTIPLE
purpose-specific scores (e.g. an allottee/APPLY-pop score vs a from-listing/secondary-buyer alpha score vs a
downside/wipeout-risk score) AND a consolidated roll-up? Motivation surfaced by A1c: signals behave very
differently by HORIZON/role — e.g. pricing-discipline predicts the listing POP (allottee) but NOT sustained
alpha; banker-downside predicts wipeouts but not returns. A single blended score can muddy "good for the
allottee" vs "good for the secondary buyer." Discuss the UX + the validation implications before any build.

## OWNED-DATA, BIGGER
### C1 — deeper app polish / redesign pass  🟡 · M · needs the Playwright visual walk
Night-1 shipped the honesty/nav fixes (median-first, n_floor, COMBINED→rank, sidebar search). Remaining: the broader
navigation/redesign from `app_phase2_design.md` + `app_iteration_charter.md`. Design agents MUST load those briefs.

## DISCUSSION THREADS — owner wants to expand these (scope before building)  ⚪ · owner 2026-06-11
### NEWS+ — extend the announcement feed beyond display (DISCUSS first)
D1/D4 shipped the display-only context feed (built, full history pulled). Owner: "a lot we can discuss and do."
Open directions to scope WITH the owner before building (don't pick unilaterally):
- **surface it in the app** — the last D1 piece: render filings + category chips under each IPO's price chart
  (needs the app work + a visual walk). This is the obvious near-term win.
- per-company **catalyst timeline** / "upcoming events" (board-meeting + event-calendar endpoints exist).
- whether ANY of it can become a *signal* later (RUNG-2) — gated on forward-collected DATE+CATEGORY+DIRECTION and
  the full 3-layer/cross-regime bar; the red-team's prior is "unlikely to clear it" for a daily/free tool. Keep honest.
- D2 delivery-volume% (below) is the other news-adjacent idea.
### MIGRATION+ — extend the SME→Mainboard migration work
- ✅ **The PREDICTIVE question was TESTED (2026-06-11) → no new signal** (`migration_predictor_2026-06-11.md`): the
  strong market_cap predictor was circular (current mcap); the real at-IPO features (sales/PAT/issue-size) are
  weak + pre-2020-only + redundant → display-only. **Re-test cross-regime once the 2020-21 SME cohort matures (~2026-27)**
  — that's the only way to get a real boom-eligible set. Censoring reframe: ~55.5% of SMEs that SURVIVE ≥5y migrate.
- STILL OPEN (owner discuss): add `migrated_to_mainboard` + `migration_date` as substrate COLUMNS at the next
  pipeline-build (not a post-hoc edit); does an SME that migrates *keep* outperforming post-migration, or is the move spent?

## NEEDS NETWORK / SCRAPING (a babysat session — NOT unattended-safe)
### D2 — delivery-volume % conviction signal  🔬 · S-M · DEMOTED
News R&D found it's boom-only (~2017+, no longterm coverage → can't clear cross-regime) + needs a NEW NSE delivery-
bhavcopy pull + no peer-review support. Display-only ceiling at best. Lower priority than once thought.

> **DONE this session (2026-06-10):** D1 (feed engine + taxonomy), D4 (full-history pull, gitignored), E3
> (SME→Mainboard migration outcome class — owned-data). See git log + `rules/index.md`.

## ANALYSIS EXTENSIONS (owned-data but hit known walls)
### E2 — unblock P/E-vs-sector for SME + EV/Sales for loss-makers  ⚪ · M
Graduate the watchlisted `pe_vs_sector` (leans −43pp MB) by computing issue-time multiples ourselves. CAVEAT: H-MVP
(2026-06-10) showed valuation is STRUCTURALLY boom-only (zero longterm P/E coverage) — same wall. Boom-only at best.

## BIG / GATED (deliberate "build a new thing" decisions — not now)
### THEME H (full) — relative valuation + intrinsic value  🔬 · L
H-MVP (owned-data peers) done → redundant-with-n6, boom-only. The bigger version (all-stocks point-in-time peer panel,
intrinsic-value models) is a real sub-project; DON'T advance to it on valuation grounds (it hits the same wall). Gated.
### G1 — Microcap / SME-seasoned small-cap RISK & MOVEMENT screener  🔬 · L
The on-moat first slice beyond IPOs; build a SCREENER (risk/movement/quality), NOT a return predictor. Only after the
IPO tool's polish is fully done. Source: `archive/extension_roadmap.md`.
### G2 — Swing-trade buy/sell calls  🔬 · L
Research-gated. EXIT side tested (no blanket take-profit beats hold); ENTRY side weak. Needs a new entry signal that
survives the 3-layer protocol, or the news feed (D1/D2). Source: `archive/future_ideas.md`.

### ORCHESTRATION — open architecture decisions (harvested from `claude_transition_…md` Part 2 via SR-5, 2026-06-17; for roadmap #3 / META-O)
The think-tank/orchestration campaign (roadmap #3) must resolve these 3 paused decisions before/while running META-O:
1. **Master-orchestrator architecture (core):** pivot was **Claude Code CLI as master orchestrator + Gemini as a backend tool** (away
   from the manual copy-paste handoff in `thinktank/orchestration/ui.py`). OPEN: does Claude Code **replace `graph.py`**, or **write a
   wrapper** that calls the Claude API (reasoning) + Gemini API (context)? **Where do the API keys live?** (Ties to META-O's routing table + DOC-5.)
2. **Human-in-the-loop UI:** `ui.py` runs a synchronous `for i in range(2):` loop that BYPASSES `graph.py`'s node/edge structure. OPEN:
   rebuild **pause → give directive → resume** cleanly in the Streamlit app. **(Same area as the failing T-5 test — fix together.)**
3. **Execution-pipeline testing:** the hypothesis-vs-data logic is functional but needs **rigorous testing once the dual-model orchestration is wired.**
(Once recorded here, `claude_transition_and_open_threads.md` is safe to delete — see the cleanup checklist in `session_handoff_2026-06-17.md`.)

### META-O — multi-model orchestration tournament (which model where?)  🔬 · L · owner 2026-06-16
**Goal:** empirically decide *which model + which orchestration shape* to use *where*, instead of guessing. We have a
think-tank/workflow orchestration that can route steps to different engines (Claude Opus / Sonnet, Gemini Pro / Flash
via `agy`, GPT-OSS). Run the SAME task through many model-combination permutations (e.g. Flash-everywhere vs
Opus-everywhere vs Opus-plans+Flash-reads vs Gemini-reads+Claude-edits), then **review/judge agents compare the outputs**
to rank combos and map "task-type → best engine + role." Output = a decision table: for each orchestration step
(scout/read, plan, build, review/judge), which model is the accuracy/cost/speed sweet spot, and where the
multi-model orchestration actually earns its keep vs a single model.
**Design notes (so we start right):**
- Needs **gradeable benchmark tasks** — ones with a known/verifiable answer (a planted bug to find, a finding with a
  recorded verdict, a known-correct analysis) so "accuracy" is measurable, not vibes.
- Compare on **3 axes, not 1**: accuracy AND token-cost AND latency (the whole point of Flash/Gemini is cost; Opus is
  accuracy — a 2%-better-but-10×-cost combo matters). agy/Gemini egress is free for this repo (owner) → exploit it.
- The **`Workflow` tool is the natural harness** (fan the same task across configs + run judge panels). Explicit
  multi-agent opt-in — fine for this when we run it.
- Connects to **DOC-5** (the CLAUDE.md "multi-model meta-orchestration" section — currently aspirational; this is how we
  decide what to actually wire in) and to the live `agy` context-engine experiment. SCOPE/run this as its own session;
  not now (mid-audit). Recorded here so it isn't lost.
- **PRIOR ART (this is NOT new — it extends an existing thread):** the orchestration design + open routing decisions
  already live in `thinktank/orchestration/docs/think_tank_architecture.md` → **`## Model Routing Strategy`** (global
  `THINKTANK_MODEL` today; per-step `THINKTANK_MODEL_<STEP>` routing is a pending TODO) + **`## Future Integration (TODO)`**
  ("Model Viability & Subscriptions" = paid APIs vs consumer Pro; CLI File-Based IPC) — TODOs tracked in `docs/setup.md`.
  META-O is the **empirical method** those open TODOs lack: a tournament that produces the routing decision table with data.
  ⚠️ Documented evidence motivating this (think_tank_architecture.md, **"Key Insight from Testing 2026-06-15"**):
  free-tier `gemini-3.1-flash-lite` RAN the pipeline end-to-end but **lacked the depth to reject flawed hypotheses / detect
  spurious proxies** — i.e. lighter models produced work that needed cleanup (consistent with the current audit backlog).

**OPEN DESIGN — extend this, THEN define the test + metrics (scaffolding, not final):**
- **WHAT WE VARY (the config grid — keep it small & meaningful, not full cartesian):** model assigned to each
  orchestration ROLE/step — scout/read · plan · build/generate · review/judge. Candidate engines per role: Claude Opus,
  Claude Sonnet, Gemini Pro, Gemini Flash (+ flash-lite as the known-weak floor), GPT-OSS. Meaningful combos to seed:
  all-Flash · all-Opus · Opus-plans+Flash-reads · Gemini-reads(agy)+Claude-edits · Pro-reasoning+Flash-mechanical.
- **WHAT WE HOLD CONSTANT:** the task, the prompts, the input context, the harness — so only the model mix varies.
- **METRICS TO DEFINE (candidates — refine into the final scorecard):**
  1. **Accuracy / correctness** — needs gradeable benchmark tasks (planted bug found? finding-verdict matches recorded
     truth? analysis correct?). Per-task pass/fail or graded score.
  2. **Judgment quality** — did it REJECT flawed hypotheses / catch spurious proxies / refuse a bad call? (This is the
     exact axis flash-lite failed — arguably the most important for reasoning steps; design tasks that probe it.)
  3. **Cost** — tokens (and ₹/$ where APIs are paid; agy/Gemini = free for this repo, factor that in).
  4. **Latency** — wall-clock per step / per task.
  5. **Reliability/variance** — run each config N times; report spread, not a single sample (model output is noisy).
- **METHOD/HARNESS:** the `Workflow` tool — fan the same task across configs, then a judge panel scores each output on
  the metrics above; blind the judge to which config produced which output where possible. Output = a decision table
  (role × engine → recommended pick, with the accuracy/cost/latency tradeoff shown).
- **OPEN QUESTIONS to resolve before building:** which benchmark tasks (and how many) give real signal? how to grade
  "judgment quality" objectively? do we judge with a frontier model, a panel, or against a fixed answer key? what's the
  acceptable accuracy floor per role (e.g. a cheap model may be fine for read/scout but never for review)?

## KILLED — do NOT rabbit-hole
Social sentiment · hosted-LLM headline polarity · RSS fuzzy ISIN-matching · F&O/options-OI · all-stocks TA+FA+news
fusion · weak-subscription veto (2026-06-10: B1's tell was a young-cohort artifact, inverts on matured data) ·
90-day-capitulation SELL & hold-through-drawdown EXIT (selling forfeits the right tail; both display-lean only).

---

## How to use this
- **Pick from here.** As of 2026-06-11 the quick/owned-data signal hunts are EXHAUSTED (A1/A1b/A1c, B1, E1,
  H7, H-MVP, weak-sub all resolved — see git log + rules/index). What remains is: DISCUSSION items (scoring-
  architecture, NEWS+, MIGRATION+) that need owner input first; APP/UX work (C1 + surfacing the news feed) that
  needs the owner present for a Playwright visual walk; walled analysis extensions (E2, D2 — boom-only); and the
  big GATED builds (Theme-H-full, G1, G2). The single best unattended-safe research bet left = **MIGRATION+**
  (an early at-IPO marker of eventual SME→mainboard escape — a chance at a genuinely NEW validated signal).
- When an item ships: record it in the git commit, put the signal verdict in `rules/index.md`, remove it from here. New idea → add here first.

---

## Technical Debt & Hacky Workarounds (Discovered 2026-06)

*(Note: The MFE/MAE Clamping Hack was removed in `pipeline/07_returns_summary.py` and `pipeline/09_assemble.py` during this audit).*

1. **Hardcoded Date/Year Limitations (`pipeline/01_build_base.py`)**: `_boom_years()` uses a hardcoded fallback year (`hi = 2026`). The current fallback will cause a bug in 2027. **Action:** Replace `hi = 2026` with dynamic logic.
2. **Financial Data Dropped (`pipeline/03_enrich.py`)**: Screener financials for 2020-2022 are skipped, relies on legacy cached files and dumps the rest into `gaps.csv`. **Action:** Integrate real back-filling.
3. **Brittle Search Workaround (`scrapers/corporate_actions_trendlyne_advanced.py`)**: Uses DuckDuckGo HTML parsing. **Action:** Replace with proper URL discovery or API call.
4. **Incomplete Detail Scraper (`scrapers/chittorgarh.py`)**: Detail parsing phase is incomplete (market_maker, OFS, anchor, subscription, financials). **Action:** Implement detailed parsing.
5. **Multi-Model Orchestration (`thinktank/orchestration/`)**: **Action:** Modify `nodes.py` and `graph.py` to support dual-agent UI pauses.
6. **Hardcoded Timebombs (`scrapers/chittorgarh.py`)**: `YEARS` array, `2026-27` FY parameter, and `page <= 300` limit are hardcoded. **Action:** Make dynamic.
7. **Silent Try-Except Data Drops (Multiple Files)**: Naked `try...except Exception:` blocks silently drop tickers instead of crashing. **Action:** Remove naked exceptions, handle known errors explicitly.
