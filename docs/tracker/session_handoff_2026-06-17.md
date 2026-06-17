# Session Handoff / State Snapshot — 2026-06-17 (comprehensive, pre-compaction)

> The "save state" for the big 2026-06-16/17 session (alignment audit → structural-integrity → D-1 corp-action fix).
> Read this first after a compaction; it points to the durable homes for detail. This doc is itself TEMP — fold into
> STATUS.md + retire during the GROUND-UP RE-BASE (see backlog).

## 🚦 CARRY-OVER RULES (read first — these govern what you may do)
- **Builds are HELD** — do NOT start the D-1 build or the low-bucket batch until the **owner explicitly says "go".**
- **No new agents / consequential actions without explicit owner approval.** (Read-only review agents have been the pattern, but still confirm.)
- **GIT:** branch + PR, push freely; **NEVER push `main` directly without owner OK.** No secrets in commits.
- **NETWORK default-deny** (company laptop): only the project `.claude/settings.local.json` WebFetch allowlist is fetchable. `agy` (Antigravity CLI) works for agents ONLY with the Bash `dangerouslyDisableSandbox:true` flag (silent-auth needs network). Scrapers reach hardcoded URLs via Bash (not WebFetch).
- **Verify from ground truth, never memory.** Count CSV records via the `csv` module, not `wc -l`.
- **Execution pipeline:** TDD + independent review for non-trivial work.

## 🥇 PRIORITY ORDER — all open work, ranked (owner-discussed 2026-06-17)
1. **D-1** — ⛔ **NOT build-ready** (R11 2nd-adversarial found B1-HIGH + B2-MED). **Next: fold the `detect_gap` ROOT redesign** (ratio-aware + structured return; resolves B1+B2+NIT-1 together) → targeted re-verify → THEN build (subagent-driven, hard-stop Task 8). The immediate boulder, but the root fix comes first.
2. **Low-bucket night batch** — SR-1 · SR-8/9 · SR-10 · DA-2/3/4. Quick PRs, runs in parallel with D-1. (Also HELD for go.)
3. **D-1 follow-ups: D1a (resolve flagged rows) → D1b (re-derive)** — finish the corp-action data right after the build (D1a: many flagged may be GENUINE wipeouts).
4. **POST-D-1 ROADMAP big-3** (`roadmap.md`, ~3-day budget, Opus): **(1) pipelining/REPRODUCIBILITY** [D1c overlay + DATA & RULES ARCH] → **(2) pull latest data** [D1d] → **(3) think-tank ORCHESTRATION** [META-O + the 3 SR-5 decisions + think_tank_architecture]. *(Pull #3 earlier if the cheaper-plan switch is imminent.)*
5. **DOC-ALIGNMENT → GROUND-UP RE-BASE** — the cleanup capstone (consolidate docs, prune cruft, run the temp-doc cleanup checklist). After the big work settles.
6. **Deferred / held / lower:** T-5 (do with #3 orchestration) · D-3/D-4 (🚦 HELD by owner) · O-2..O-16 + I1 + D1e broader-checks (do with #1 reproducibility) · D1f Wave-2 · DA-9.

## ✅ DONE this session (merged / resolved)
- **PR #2 (merged):** git-policy reconciliation across 9 docs (branch+PR, never push main) + Playwright OFF + DOC-2 (scorecard "5"→"8") + DOC-4 code-comment paths + **DOC-7/SR-6/SR-11 = a real app bug: moved `rules/` back to root from `thinktank/rules/`** (app screens read `config.ROOT/'rules/index.md'`).
- **PR #3 (merged):** structural-integrity — **STRUCT-1** (counts single-source-of-truth: generated CANONICAL FACTS in MAP.md + a count-guard) + **FILE_KINDS** marking/enforcement in project_map.py/verify.py + **DOC-3** (7 stale project_map pointers fixed) + **DD-1/2/3/4** doc-drift fixes (generated files moved out of archive; `nodes.py` wrong `task_log` path fixed). `verify.py` PASSES on main.
- **DOC-6** (weight precision) = non-issue. **C-2** (allowlist) = RESOLVED: the financial domains (nseindia/bseindia/sebi/screener/moneycontrol/livemint/economictimes/tradebrains) were NOT actually in any config (earlier grep hits were transcript pollution) — now **added to the project `.claude/settings.local.json`** (valid JSON) so unattended agents fetch them without prompts; docs now accurate.
- **Wave-1 corp-action web evidence** (53 flagged stocks) → `data/master/review/corp_action_external_evidence.csv`.

## 🔴 D-1 CORP-ACTION FIX — ⛔ NOT BUILD-READY (R11 found B1/B2 → `detect_gap` ROOT redesign needed first), 🚦 HELD (the night's big boulder)
The bug: split/bonus factors over-/mis-counted → fake returns (ROLEXRINGS +15,272% etc.). Fix principle = **"price disposes"** (validate every adjustment against the raw price gap). **Targeted patch** of the existing (non-reproducible) substrate; **hard-stop at Task 8** (substrate patch + manual-remediation inventory + owner approval — the only irreversible step).
- **Design:** `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`. **Plan (12 tasks, TDD):** `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md` — its **state-log (R1–R10)** is the full review saga.
- **10 review rounds → R10 GO.** Two HIGH issues caught by *new lenses* (R6: date-window gate was over-scoped → fixed to symbol-added-only, ISIN-matched always applies; R8 adversarial: "price disposes" was orphaned in `03k/03l` and never reached the substrate → R9 remedy (a) wired per-action price-validation into the `07` call site). Fixes verified: CANTABIL 25→5 (~7.14×, not multibagger), GNA 4→2 (~2.70×), ATLANTAA stays winner, ROLEXRINGS via override seed.
- **1 LOW build-time nit (NIT-1):** add an explicit 5th decision-tree branch ("gap present but ≠ claimed ratio → defer to override") + a real-ROLEXRINGS test — fold during Task 4 build (non-blocking).
- **Build approach when owner says go:** subagent-driven TDD, Tasks 0–7+5b+9 autonomous (reversible), **HARD-STOP at Task 8** (owner gate).
- **R11 — 2nd adversarial (`docs/research/d1_adversarial2_2026-06-17.md`): EDGE-CASE-FOUND → NOT build-ready (supersedes R10 GO).**
  - **B1 (HIGH):** genuine small bonuses (5:4/6:5/4:3, gap ~1.2–1.4×) fall below `detect_gap`'s 1.5× absolute floor → wrongly phantom-dropped + nulled — **23 stocks incl POWERGRID/NTPC/PFC/RECLTD/RITES/OIL.**
  - **B2 (MED):** phantom-vs-coverage-hole undecidable when ex_date is PAST coverage-end (closes before ex, none after) — 6 events (E2E/FORGE/LEMERITE multibaggers).
  - **ROOT CAUSE (B1 + B2 + R10-NIT-1 all share it):** `detect_gap` uses an ABSOLUTE threshold + its `None` return OVERLOADS genuine-small / phantom-flat / coverage-missing / boundary / wrong-ratio. **FIX = redesign `detect_gap` to be RATIO-AWARE (accept iff gap ≈ the CLAIMED ratio, not an absolute floor) + return a STRUCTURED result; rebuild the decision tree (Task 2 + Task 4). Resolves B1+B2+NIT-1 together.** Then targeted re-verify → THEN build. *(Also: log DWARKESH rf=1.0 under-count — inert, not in substrate — to TODO-D1.)*
  - **Clean (verified) in this pass:** action-type confusion (no dividend/rights factor events), face-value-change ISIN join, same-ratio-different-event (29 stocks, each own gap, not collapsed).
- **Build approach (after the root fix + re-verify):** subagent-driven TDD, Tasks 0–7+5b+9 autonomous (reversible), **HARD-STOP at Task 8** (owner gate).

## 🗺 POST-D-1 ROADMAP (the 3 big items — `docs/tracker/roadmap.md`)
Priority: **1) Pipelining/REPRODUCIBILITY** (deterministic/idempotent `pipeline+overlay=substrate`; TODO-D1c + DATA & RULES ARCHITECTURE) → **2) Pull latest data** (live; TODO-D1d) → **3) Think-tank ORCHESTRATION** (cheaper-plan motivated; META-O + think_tank_architecture). Budget ~3 days (4h/day owner + 5h nights), all compute-heavy → **Opus**. Timing nuance: pull #3 earlier if cheaper-plan switch is imminent.

## 📋 D-1 FOLLOW-UP TODOs (separate later tasks — `improvement_backlog.md`, D1a–f)
- **D1a** strict-resolve all flagged corp-action rows (many may be GENUINE wipeouts — classify each).
- **D1b** re-derive downstream (targeted) after D1a (incl. T-3 goldens/weights).
- **D1c** reproducibility OVERLAY — the deterministic/idempotent regeneration campaign: build overlay → regenerate → DIFF vs current substrate → every mismatch is a BUG (new-data OR old-data) → review+resolve each → trust → go live. Ordered/idempotent/conflict-aware/provenance. STOPS other dev when run.
- **D1d** live corp-action capture + `corp_actions_as_of` watermark (pull from watermark−1mo); classify/fix new records in-place.
- **D1e** broader data-integrity checks (O-12 implied-shares, O-13 price-band, O-11 date-order, O-5/O-7 EPS, I1 0→NaN) — flag-only.
- **D1f** Wave-2 corp-action web evidence (phantom 84 + single-source 56) — deferred, not skipped.

## 🧹 CLEANUP / ARCHITECTURE (backlog)
- **DOC-ALIGNMENT** (after D-1): consolidate scattered docs into canonical homes; archive the temp working+review docs; regenerate INDEX/MAP. Catalog: `docs/research/doc_alignment_audit_2026-06-17.md` (DA-1..14; most prior SR/DD already fixed).
- **GROUND-UP RE-BASE** (the capstone): whole-repo prune+reorganize, keep validated work, layer clean base over it (NOT a rewrite); guardrails = tests + verify.py + git; after the churn settles. Subsumes DOC-ALIGNMENT.
- **D-1 spun up ~11 docs** (spec + plan + ~9 review/evidence) → archive the `d1_*` trail after D-1 ships; keep spec+plan.

### 🧹 DEFINITIVE TEMP-DOCS CLEANUP CHECKLIST (owner: "clear ALL these after the night run — no clutter")
Tick-list so nothing is missed. **Guardrail: their VERDICTS/history live in git log + rules/index + the merged code — the docs are scaffolding.**
- [ ] `docs/research/structure_review_2026-06-16.md` — superseded by `doc_alignment_audit` → **archive/delete now-ish.**
- [ ] `docs/research/doc_drift_review_2026-06-16.md` — superseded → **archive/delete now-ish.**
- [ ] `docs/research/doc_alignment_audit_2026-06-17.md` — the catalog; **delete after the DOC-ALIGNMENT fix consumes it.**
- [ ] The full **`d1_*` review/evidence trail** → archive after D-1 ships: `d1_plan_review`, `d1_plan_rereview`, `d1_join_strategy`,
      `d1_plan_final_verify`, `d1_final_implementability`, `d1_final_correctness`, `d1_plan_targeted_reverify`, `d1_adversarial`,
      `d1_remedy_a_reverify`, `d1_adversarial2`, `d1_remediation_inventory` (all `docs/research/*_2026-06-17.md`/`.md`).
- [ ] `docs/research/alignment_audit_2026-06-16.md` — **retire once ALL its items close** (still tracks D-3/D-4/O-series/T-5 etc.).
- [ ] `docs/tracker/session_handoff_2026-06-17.md` (this doc) — **fold into STATUS.md, then delete.**
- [ ] `docs/superpowers/specs|plans/2026-06-16-d1-*.md` — KEEP until D-1 merges, then archive (the design record).
- [ ] Scratch scripts at repo root (`get_bse.py`, `get_nse.py`, `nse.py`, `parse_splits.py`, `search*.py`, `*.html`, `test_url.py`) — **delete** (pre-existing cruft).
- [ ] `docs/tracker/claude_transition_and_open_threads.md` — delete after SR-5 harvest (owner keeping for the handoff till then).
**End state:** docs/research/ holds only durable research + an `archive/`; the canonical homes (CLAUDE, STATUS, improvement_backlog, roadmap, rules/index, project_map, MAP) are the only live trackers.

## ⏳ OTHER OPEN (not yet actioned)
- **T-2/T-4** bundled with D-1 (clear when substrate rebuilt); **T-3** re-derive after.
- **T-5** thinktank UI test — DEFERRED (thinktank WIP → roadmap #3).
- **D-3/D-4** look-ahead leaks (market_cap_class + full-df) — **HELD by owner**; design in the audit doc.
- **O-2..O-16** data issues (need owner / after reproducibility). **I1** 0→NaN.
- **SR-5 ✅ DONE** — the transition doc's 3 open orchestration decisions harvested → backlog (ORCHESTRATION block by META-O); doc now safe to delete in cleanup (owner keeping it for the ~4-day handoff till then). **DA-9** PRODUCT.md vs CLAUDE.md overlap (still open).
- **DOC-5** the CLAUDE.md "multi-model meta-orchestration / agy context-engine" section is aspirational — agy CLI verified working (Gemini Pro, web-search); resolve via META-O.

## 🧹 LOW-BUCKET NIGHT BATCH (decided, READY, 🚦 HELD until owner go)
SR-1 (thinktank "supersedes"→WIP reframe) · SR-8/9 (improvement_backlog path fixes) · SR-10 (regenerate INDEX.md via a small generator) · DA-2 (CLAUDE.md run-scripts → `scripts/`) · DA-3 (CLAUDE.md "8-component" headline vs a 5-item list) · DA-4 (README "STATUS.md (root)"). Each: branch→TDD→review→**PR (not merged)**.

## 🗂 RESUME-FILE MAP
- **This handoff** (entry point): `docs/tracker/session_handoff_2026-06-17.md`
- Open work / TODOs / roadmap-pointer / architecture / cleanup: `docs/tracker/improvement_backlog.md`
- The 3 big items + budget: `docs/tracker/roadmap.md`
- Live state: `docs/tracker/STATUS.md` · Conventions/brain: `CLAUDE.md` · History: **git log**
- Audit triage (open items): `docs/research/alignment_audit_2026-06-16.md`
- D-1 design: `docs/superpowers/specs/2026-06-16-d1-corp-action-fix-design.md`
- D-1 plan + R1–R10 state-log: `docs/superpowers/plans/2026-06-16-d1-corp-action-fix.md`
- D-1 evidence: `docs/research/d1_*_2026-06-17.md` + `data/master/review/corp_action_external_evidence.csv`

## ▶ NEXT ACTION (when owner says "go")
Launch **D-1 build** (subagent-driven, hard-stop at Task 8) **+ the low-bucket batch** in parallel — all PRs, nothing merged to `main`. Fold NIT-1 during Task 4. If the 2nd-adversarial pass (in flight) found anything, fold it first.
