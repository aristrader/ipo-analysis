# Overnight Data-Architecture Design Run — Charter (2026-06-17)

> Quick agreement doc. Owner reviews/adds → then leaves → I run the night "thinking mode."
> TEMP (fold into the design doc + retire later). The DESIGN OUTPUT lands in separate docs (listed at bottom).
>
> **⭐ THIS IS THE "FINAL STOP" for the data foundation (owner 2026-06-17).** It ABSORBS roadmap-#1
> (pipelining/reproducibility = TODO-D1c) **and** the DATA & RULES ARCHITECTURE umbrella from
> `improvement_backlog.md`. **"FINAL STOP" = this is the single VENUE where the foundation gets *designed* in
> one place; the design OUTPUTS remain NON-FINAL proposals for owner approval (see Rules / Starting Leanings —
> nothing here is decided).** We design (for owner approval) the WHOLE data foundation here, in one place, before
> building anything else. (Backlog TODO-D1c / DATA & RULES ARCHITECTURE / roadmap #1 now point HERE for the
> design; they remain the task-tracking stubs.)

## 🚦 RULES FOR THIS RUN (hard)
- **DESIGN / THINK / REVIEW ONLY. NO implementation. NO code or pipeline changes.** Output = `.md` docs only.
- **Owner owns the design.** Even if I sketch a prototype idea, it stays a proposal — nothing is built until owner reviews & says go. (Lesson from last time: AI did the data design alone → wrong.)
- **Verify from ground truth, never memory.** Re-check claims against the actual code/data/CSVs.
- **agy for heavy reads** (big docs / CSVs / many files) to save context — but **review agents re-verify agy's claims** (don't trust blindly).
- **Capture everything durably** (this run will outlive a compaction): every round appends to the design + issue docs.
- Carry-over repo rules still apply (branch+PR if anything is ever committed; never push main; network default-deny; agy needs `dangerouslyDisableSandbox`).
- **SCOPE GUARD (enforced — `.claude/hooks/guard_bash_scope.py`, wired as a PreToolUse Bash hook + tested):** python/shell
  stay OS-sandboxed (only `agy` may disable it); **no writes outside `docs/research/`**; **no rm/mv/truncate/dd (no deletion)**;
  no destructive/committing git (reset/clean/checkout/commit/push); no sudo/chmod/chown; no network except `agy`. Agents
  must ALSO honor this verbally (briefs) — the hook is the backstop, not the only line.
- **PER-ACTION LOG (audit trail):** every Bash command is logged (timestamp · allow/block · command) to
  `docs/research/night_run/bash_action_log.tsv` for the owner's morning review.

## 🎯 THE GOAL
Design the **target DATA ARCHITECTURE** for the IPO dataset, end to end, and surface **every** data issue (past + present) with resolution ideas — through many rounds of *brainstorm → expand → find issues → resolve → review*, looping until reviews stop finding new problems.

## 📐 WHAT THE DESIGN MUST COVER
1. **Target end-state** — the full list of data/columns we ultimately want (per dataset).
2. **Sourcing per field** — where each field can come from, coverage, and the fallback order when the primary source is empty.
3. **Missing-data policy + present-vs-absent** — when not found → null; and crucially **distinguish three cases**:
   (a) the source genuinely never published it, (b) we failed to fetch/parse it, (c) it's a real zero.
   Need a per-field "do we actually have it?" flag. (This is the root of the `0`/`""`-instead-of-missing bug, item I1.)
4. **Dataset structure — NOT decided; re-derive from scratch in task_04.** Current *leaning only* (see STARTING LEANINGS
   + CANDIDATE DATA LAYOUT below, both marked NOT FINAL): 2 canonical masters (`mainboard`, `sme`, shared schema) as the
   single source of truth, with clean substrate / dirty quarantine / longterm / shortterm / combined as **derived views**
   (filters/scripts), not separate stored files; confident rows → `quality==clean`, ambiguous → `quality==dirty`
   (quarantine, promoted when fixed). Treat this as a hypothesis to challenge — task_04 re-derives how many datasets +
   masters-vs-derived, plus the sub-questions (compact present/absent encoding; one-internal-spine vs 2-stored; which structural cols).
5. **Full issue register** — consolidate ALL known data issues (corp-actions/splits, the O-series (O-1…O-16, ~16 items
   per `alignment_audit_2026-06-16.md`: subscription, GMP, EPS, sales, market-cap, dates, price-bands), + I1). For each:
   status (fixed / open / handled-before), a resolution approach, and whether it's resolvable now vs needs external data
   vs needs an owner decision.
6. **Re-audit the "already fixed" items** — verify each past fix actually holds; if a fix is weak, propose a better one.
7. **The cleaning model** — how a dirty row gets cleaned and **promoted** to clean (so re-runs never lose hand-fixes);
   note: an overlay already exists today (`09_assemble.py` reads `data/reference/manual_overrides.csv`; `07` reads
   `data/reference/corp_actions_merged.csv`) — plus other hand-fix catalogs enumerated in §A / task_08.
8. **Extensibility — adding a NEW column later.** Design so adding a column is a *config/registration* step, NOT a
   bespoke new script each time. When the new column has gaps, the SAME missing-policy (present-vs-absent, source
   fallback, dirty-routing) applies automatically — no special-casing. Define: where a column is declared, how its
   source(s)+parser+fallback+validity-check are registered, and how it flows into clean/dirty without touching the spine.
9. **Features ↔ data (reverse map).** We've already built a lot (predictor, analog engine, scorecard, backtester,
   findings, validation). For each, ask: **is any known feature quirk/limitation actually a DATA problem fixable here?**
   (e.g. D-3 market-cap leak, the EPS/sales corruption poisoning margins, subscription-as-feature breaking on the 0-bug.)
   Output a "feature issue → data root cause → fix-at-data-layer" table so this run also heals downstream features.
   **AS-OF SEMANTICS (a CLASS, not one instance):** D-3's market-cap leak is the visible face of a general problem —
   `market_cap_class`/`market_cap_cr` is CURRENT (post-outcome) cap, and that same as-of-date contamination poisons the
   migration analysis too (circular rank-IC 0.564, see `rules/index.md` / migration_predictor) and ANY field scraped
   "as of now" rather than at-IPO (incl. future live-price/listed-stock fields per #10). Treat it as a class: task_02 /
   task_03 must give every TIME-VARYING field an explicit **as-of attribute** (at-IPO snapshot vs current/live) recording
   its as-of date so it can't silently leak future state. The two KNOWN instances (D-3 mcap leak, migration circular-mcap)
   are examples of this one class.
10. **Future universe (extensibility #2).** We'll later want (a) **more stocks, not just IPOs**, and (b) **live/daily
    price data** flowing in. Design the schema/identity/ingestion so those slot in WITHOUT re-architecting — e.g. a
    `universe_type` (ipo / listed-stock) + `source`/`frequency` abstraction; IPO-specific fields degrade to null for
    non-IPO rows (present-vs-absent handles it). Don't build it now — just make sure the design doesn't BLOCK it.
11. **Reproducibility / overlay (ABSORBED from roadmap-#1 / TODO-D1c).** `fresh pipeline output + ordered overlay =
    substrate`, **deterministic & idempotent end-to-end** — re-running produces the EXACT same substrate every time,
    no hand-step, no drift. Design for all 5 hard parts (below).
12. **Re-run reapplication + the reconciliation campaign.** The pipeline WILL be re-run many times; fixes must
    **reapply on top automatically & in the right order.** Design the one-time campaign: build overlay → regenerate
    fresh → **DIFF vs current substrate → every mismatch is a BUG (new-data OR old-data) → review+resolve each → trust → go live.**
13. **DATA & RULES ARCHITECTURE unification** — treat ingestion / identity-matching / rule-applicability / overlay-layering /
    old-data-cleanup / new-data-in-place-handling as ONE coherent design, not scattered patches (see merged section below).

## ⭐ NORTH STAR (owner): every output must be **CLEAN · EXTENSIBLE · CORRECT**
Minimal structural flags (no behavioral if/else sprawl) · declarative data-driven rules (not hardcoded branches) ·
single source of truth (no duplication) · expandable (new columns/stocks/live-data slot in without restructuring) ·
correctness over speed (don't rush; flag rather than guess).

## 🔁 EXECUTION SEQUENCE (the MACRO ordering only — the real unit of work is the PER-TASK METHOD below)
**The "levels" you asked for, run in this order:** brainstorm → ideate → expand → issue-find → issue-resolve →
**review (loop-until-dry)** → (last, optional) web-evidence.

> ⚠️ **AUTHORITATIVE:** the stages below are just the high-level phase ordering. The ACTUAL execution unit is the
> **PER-TASK METHOD** (next section): every `task_x.md` gets the full 8-step deep treatment (scope → ground-truth →
> reproduce/re-audit → options → analysis → TEST-against-data → multi-lens review looped-until-quiet → non-final proposal).
> Where a stage below says "parallel agents / lenses", that is realized as the corresponding **deeply-worked task files**,
> NOT a single light pass. If the stage wording and the per-task method ever conflict, the **per-task method wins.**
>
> ⚠️ **GLOBAL-STAGE OWNERSHIP (so non-task stages aren't skipped — the per-task guarantee covers only `task_x` files).**
> Every global stage gets a named artifact + its own review, NOT just the leaf tasks:
> - **STAGE 0 (context load) → `docs/research/night_run/context_map.md`** (what we know / fixed / open).
> - **STAGE 2 (CONVERGE) → `data_architecture_design_2026-06-17.md` as an explicit SYNTHESIS task with its OWN review
>   pass** — the converged design is NOT an un-reviewed staple-together of task files; the rollup itself is reviewed
>   under the canonical 5 lenses.
> - **STAGE 6 (web evidence) → optional, last only.**
> An agent may NOT declare "all tasks done" while the synthesis/convergence rollup is unwritten or unreviewed.

- **STAGE 0 — Context load (ground truth, via agy + targeted reads).** Mine ALL existing docs so we build on prior
  knowledge, not from scratch. Required reads (agy summarizes, review agents later re-verify):
  `docs/research/alignment_audit_2026-06-16.md` (the O-series + corp-actions), `data_review.md` +
  `data/master/review/*.csv`, `docs/schema.md`, `docs/sources.md`, `rules/index.md`, `STATUS.md`, the `d1_*` trail,
  `docs/research/INDEX.md`, the pipeline code (`01..09`, `03h/j/k/l`), the scrapers, and **the actual master CSVs**
  (count via `csv`, never `wc -l`). Output: a context map (what we know, what's fixed, what's open).
- **STAGE 1 — DIVERGE (multi-lens design brainstorm).** Parallel design agents, each one lens:
  (a) end-state schema / what data we ultimately want; (b) sourcing per field + fallback order + present-vs-absent
  (distinguish "source never published" / "we failed to fetch-parse" / "real zero"); (c) dataset layout = 2 masters +
  derived views + the structural-column set; (d) extensibility — the **column registry** + new-column-with-gaps auto-handling;
  (e) reproducibility overlay + re-run reapplication; (f) **features↔data reverse-map** (every built feature → is its
  quirk a data bug fixable here?); (g) future-universe expandability seams (non-IPO / live-daily — design-open, not built).
- **STAGE 2 — CONVERGE.** Synthesize the lenses into the **target data-architecture design doc** (resolving conflicts,
  picking the clean/extensible/correct option, recording rejected alternatives + why).
- **STAGE 3 — ISSUE REGISTER (issue-find + resolve).** Parallel agents sweep EVERY data area (corp-actions/splits, the
  O-series O-1…O-16 (subscription/GMP/EPS/sales/market-cap/dates/price-bands), I1 0-vs-missing) → one consolidated register.
  Per issue: status (open / fixed / handled-before), **re-AUDIT the "already-fixed" ones (does the fix actually hold? if weak,
  propose better)**, resolution approach, resolvable-now? vs needs-external-data vs needs-owner-decision.
- **STAGE 4 — CLEANING RULES (design, declarative).** For each issue class, design the data-driven cleaning rule
  (condition → action → confidence → clean-or-quarantine), consistent with the overlay + registry. No code.
- **STAGE 5 — REVIEW LOOP (loop-until-dry; "even 50 reviews").** Fresh-lens review agents each round check the CANONICAL
  5-lens set (inherited from PER-TASK METHOD step 7): (a) **correctness**, (b) **completeness** ("what did we miss — a
  field, an issue, a source, an edge case?"), (c) **context-pickup** ("did we actually read & honor the prior docs / past
  resolutions, or re-invent?"), (d) **north-star adherence** (clean/extensible/correct, minimal flags), (e) **adversarial
  (try to break it — MANDATORY).** Each finding → fix the design/register → re-review. **Stop per the explicit stop rule
  in step 7** (≥2 consecutive independent fresh-agent rounds with zero new findings ≥LOW; hard floor ≥2 rounds; every
  round logged). Review agents are lower-context (cheaper) but must be DIFFERENT from the author.
- **STAGE 6 — (LAST, OPTIONAL) web evidence.** ONLY if everything above is finished: agy gathers web evidence on
  still-flagged stocks. Never let this block or stall the design work.

## 🧱 PER-TASK METHOD (each decision = its own `task_x.md`; nothing assumed final)
The work is split into ~20 focused tasks (architecture decisions + per-area issue register). **Each task gets the SAME
deep treatment** — this is the guarantee:
1. **Scope** — the single question this task decides.
2. **Ground-truth inputs** — read/verify the real code/docs/CSVs first.
3. **Reproduce + re-audit (the "already-faced" part).** List every issue we've ALREADY hit in this area and **run/reproduce
   it against current data** (does it still manifest, with what counts/examples?). For every fix we ALREADY have,
   **verify its viability** — does it actually hold on current data, or is it weak/partial? (Covers existing issues + existing fixes.)
   **Re-audit division of labor (avoid the responsibility gap):** Group-B tasks 14-19 do the AUTHORITATIVE per-area
   re-audit of their own fixes here in step 3; **task_20 is a CONSOLIDATION + gap-check** that verifies every known fix was
   re-audited by some task and flags any uncovered — it is NOT a from-scratch re-audit and does NOT excuse a thin step 3.
   The canonical "already-fixed items" list to be covered = the O-series (O-1…O-16) + the D-1 corp-action fixes + the
   88-audit corrections; task_20 checks coverage against that list.
4. **Options** — enumerate ≥2-3, challenge even the "obvious" one. **No strawmen:** each option must be STEELMANNED (its
   strongest case stated); each rejected option carries a SPECIFIC reason tied to the north-star (clean/extensible/correct)
   or to data evidence — never just "worse". For any task that has a STARTING LEANING, name the leaning, then argue at
   least one credible NON-leaning alternative on its merits before converging (the charter says to *challenge* leanings —
   this enforces it).
5. **Analysis** — reason step by step.
6. **TEST / validate (must produce numbers — bare "validated against data" is FORBIDDEN).** Check the proposal
   **empirically against the real data** (read-only): state the exact predicate/query used, report the COUNTS it returns
   (caught / missed / over-caught — i.e. BOTH false-negatives AND false-positives, quantified), and give **≥2 worked row
   examples by ISIN/symbol**. (Design-time validation, NOT code.) For a purely architectural task with no directly testable
   predicate (e.g. task_04 layout, task_06 registry), write an explicit **"testability: N/A because <reason>; validated
   instead by <walkthrough against M real rows / schema cross-check>"** — never skip the step silently.
7. **Multi-lens review (loop-until-quiet — see explicit stop rule below).** Several DIFFERENT review agents, each a
   different agent from the author: correctness · completeness · context-pickup (did we honor prior docs/resolutions?) ·
   north-star (clean/extensible/correct) · **adversarial (try to break it — MANDATORY, the highest-value lens).** This
   5-lens set is CANONICAL (STAGE 5 inherits it). **STOP RULE:** review continues until **2 consecutive INDEPENDENT
   fresh-agent rounds each produce ZERO new findings (severity ≥ LOW)**, with a **hard floor of ≥2 total rounds even if
   round 1 is clean**. The reviewer must be a different agent than the author. Each round is logged in the review_log with
   its findings — or an explicit "NONE, and here is what I checked" — so "quiet" is AUDITABLE, not merely asserted. A
   restated/re-labeled prior finding does NOT count as resolved.
8. **Non-final proposal + open owner-questions** — explicitly marked NOT final.

**DONE CHECKLIST (stamp at the bottom of every `task_x.md`; a box unchecked = task INCOMPLETE):**
☐ all 8 steps present and non-empty · ☐ ground-truth inputs cited by FILE PATH · ☐ step-6 numbers present
(caught/missed/over-caught + ≥2 ISIN examples, or the "testability: N/A …" clause) · ☐ review-loop stop rule satisfied
with every round logged in the review_log · ☐ NOT-FINAL marker + open-owner-questions block present.

**Sequencing (my call, per owner):** issue-register + existing-fix re-audit tasks run FIRST (largely parallel — they're
independent and they inform the design with ground truth) → then the architecture-design tasks in dependency order
(mostly sequential, each fully reviewed before its dependents). Independent tasks may overlap; nothing dependent starts
on an unreviewed predecessor.

> ⚠️ **NUMBERING ≠ EXECUTION ORDER.** Task numbers below are THEMATIC labels, not run order. **Group B (task_14-20) runs
> BEFORE Group A (task_01-13)** — the numeric order is the inverse of the execution order. Do NOT run task_01 first.

**Group A dependency edges (the hard ones; everything else is parallelizable):**
- Group B (14-20, parallel) → ALL of Group A (B's ground truth feeds the design).
- task_03 (missing-data/present-vs-absent policy) **before** task_01 (end-state schema) — the schema encodes the policy.
- task_01 → task_05 (structural columns) → task_06 (column registry) → task_04 (dataset layout) — registry+columns
  define what a master/view holds before layout is fixed.
- task_07 (identity/matching) is independent of the schema chain; may run in parallel after B.
- task_08 (overlay) **before** task_09 (reconciliation campaign) **before** task_11 (cleaning-rules model).
- task_10 (rule-applicability) and task_12 (features↔data) depend on task_01+task_05 being reviewed.
- task_13 (future-universe seams) last — it stress-tests the converged layout/registry.
"Fully reviewed before dependents" applies along these edges; unlisted pairs may overlap.

### THE TASK LIST (~20 — may be split finer, never coarser; nothing assumed final)
> **NOTE: numbering is THEMATIC, not execution order — Group B (14-20) runs BEFORE Group A (01-13). See Sequencing above for the dependency edges.**

**Group B — issue register + existing-fix re-audit (run FIRST, parallel):**
- **task_14** corp-actions / splits / bonuses (D-1 family + fake returns) — reproduce + re-audit existing fixes.
  **Inputs (ground truth):** `data/reference/corp_actions_merged.csv` (tags `manual_thinktank_audit`=34, `verification_2026-05-31`=5) +
  `docs/research/unresolved_88_mismatches_audit.md` **Category 1** (21 manually-identified missing splits/bonuses WITH ratios —
  Aishwarya 2:1, Darshan 5:1+11:10, 7NR 1:10-rev+10:1+1:5, etc. — NOT yet in `manual_overrides.csv`: decided-but-unapplied
  corrections to absorb). **Protective ground truth — the verified-genuine-outcome WHITELIST:** the 88-audit **Category 2** = 67
  stocks manually verified as GENUINE crashes/wipeouts/scams with ZERO unrecorded corp action (Aster Silicates -91.6%, Future
  Capital, Maytas, Inox INE312H01016, etc.). Load these as ground truth so the rebuild does NOT manufacture a split/bonus
  "correction" for a real wipeout. Cross-link the 88-audit explicitly here and into task_19/T-2 and task_20.
- **task_15** subscription + GMP (incl. 0-instead-of-missing instances).
- **task_16** financials — EPS / net_sales / margins / debt-equity-vs-ROE.
- **task_17** market-cap — wrong-entity joins, as-of semantics, zeros.
- **task_18** dates / identity / price-bands / min-investment / one-offs.
- **task_19** returns/outcomes + systemic I1 (0-vs-missing at load). **Re T-2 envelope-violation:** INE312H01016 (Inox) is the
  SINGLE T-2 envelope offender AND a Category-2 verified-genuine crash — its path is REAL DATA, not a bug to clamp; the
  envelope tripwire (T-4 decision-c) must treat it as real, not clamp it. Carry the Category-2 whitelist as input here.
- **task_20** re-audit ALL already-"fixed" items — **CONSOLIDATION + gap-check** (per step-3 division of labor): verify every
  known fix (O-1…O-16, D-1 corp-actions, 88-audit Cat-1 corrections) was re-audited by some task; flag any uncovered. Also
  carry the Category-2 verified-crash whitelist so no task "re-fixes" a genuine wipeout.

**Group A — architecture decisions (run AFTER B, dependency order, mostly sequential):**
- **task_01** target end-state schema (what data we ultimately want). **Ground-truth FIRST:** reconcile `docs/schema.md`
  against the ACTUAL substrate (verified 220 columns vs the doc's shorter list); catalog every drift (missing/extra/renamed
  — e.g. the doc lists `pre_ipo_eps` which is ABSENT from the substrate). The end-state schema SUPERSEDES the stale doc as
  the single source of truth.
- **task_02** sourcing per field + fallback order. **Add an "as-of semantics" attribute** to the column registry (at-IPO
  snapshot vs current/live) for every TIME-VARYING field so it records its as-of date and can't leak future state (known
  instances: D-3 market-cap leak, migration circular-mcap — see §9).
- **task_03** missing-data policy + present-vs-absent + compact provenance encoding. **Ground-truth FIRST:** inventory the
  provenance mechanism that ALREADY EXISTS — the `<field>_src` columns (e.g. `issue_price_src`, `sub_total_x_src`,
  `gmp_pct_src`, `pat_yr3_src`), plus `confidence` / `confidence_reason` / `isin_xchg_check`. Design the 3-state
  present/absent encoding (source-never-published / fetch-parse-failed / real-zero) as an **EXTENSION or replacement of the
  existing `_src` scheme**, explicitly reconciling with what's already stored — do NOT re-invent in parallel (north-star:
  single source of truth, no duplication).
- **task_04** dataset layout — how many datasets? masters vs derived? (re-derive from scratch — nothing assumed).
- **task_05** structural columns / minimal-flags design. **(See task_05b for the instrument-type seam.)**
- **task_05b** instrument-type / asset-class dimension. The substrate's `type` encodes only board (MB/SME); a separate
  `instrument_type` column ALREADY EXISTS ({equity:2329, fpo:38, reit:9, invit:8} — verify counts at run-time). Design:
  (i) whether `instrument_type`/asset-class is the canonical structural column distinguishing equity-IPO vs FPO/IDR/REIT/
  InvIT/NCD (build on the existing column, don't invent a new one); (ii) **de-contaminate the equity financials table** —
  O-6 (NCD/…25…-series mis-included poisoning sales/margins), O-16 (Std Chartered IDR issue_amount=0); (iii) the
  **exclude-vs-analyze-separately** owner decision (STATUS.md pending; `rules/index.md` x-nonequity) as a first-class owner
  question. **This is the natural seam for the `universe_type` extensibility (§10/task_13) — UNIFY them.**
- **task_06** column registry / new-column extensibility.
- **task_07** identity & matching architecture (ISIN + symbol + windows + collisions).
- **task_08** reproducibility overlay (capture / order / idempotency / conflict / provenance). **Discover EVERY pre-existing
  override catalog as a ground-truth step (do NOT assume the three named files are the whole set).** Enumerate and ingest:
  `data/reference/manual_overrides.csv` (verified 3 rows, all market_maker), `data/reference/corp_actions_merged.csv`
  (tags `manual_thinktank_audit`=34 + `verification_2026-05-31`=5), `docs/research/unresolved_88_mismatches_audit.md`
  **Category 1** (21 decided-but-unapplied split/bonus overrides with ratios), and `docs/research/data/drhp_recovered.csv`
  (16 SEBI-DRHP-recovered financials — Coal India FY10 sales, DLF, etc. — incl. its pat_suspect / review-needed flags), and
  the DRHP staging. If any of these is not absorbed, the overlay is incomplete and task_09's diff will mis-classify these
  decided corrections as bugs.
- **task_09** re-run reconciliation campaign design. **Flag silent-drop as a diff CLASS:** vanished rows (from naked
  try/except row-drops, see §D) must surface as reconciliation diffs, not disappear silently.
- **task_10** rule-applicability (which check/hypothesis applies to which data). **Equity-only findings must NOT run on
  non-equity rows** (NCD/IDR/REIT/InvIT/FPO) — gate via the instrument-type dimension from task_05b.
- **task_11** cleaning-rules model (declarative).
- **task_12** features ↔ data reverse-map.
- **task_13** future-universe expandability seams (design-open, not built) — unify with task_05b's instrument-type seam.

## 📤 WHAT YOU'LL WAKE UP TO (for your end-to-end morning review)
- **Target data-architecture design doc** (end-state schema · sourcing · present-vs-absent policy · 2-masters+derived-views
  layout · column registry/extensibility · reproducibility overlay · future-universe seams · cleaning model).
- **Consolidated issue register** (every data issue · status · re-audit of fixed items · resolution proposal · resolvable-now? · owner-decision-needed?).
- **Cleaning-rules design** (declarative rule per issue class).
- **Features↔data reverse-map** (feature quirk → data root cause → fix-at-data-layer).
- **Review log** (each round: what it found, what changed, when it went "dry").
- **"Decisions needed from owner"** list pinned at the top of the design doc.
- **NO code changes.** (A *proposed* implementation outline for next session may be included — clearly marked proposal.)

## 🏛 ABSORBED: REPRODUCIBILITY OVERLAY + DATA & RULES ARCHITECTURE (merged from roadmap-#1 / backlog)
The design MUST resolve these as part of the foundation (this is why this doc is the "final stop"):

**A. The reproducibility overlay (TODO-D1c) — `pipeline output + ordered overlay = substrate`, design for all 5 hard parts:**
1. **Capture** every post-pipeline hand-fix in machine-applicable form: target row (key = symbol∪ISIN) + column, old→new value, REASON/provenance, date.
2. **Order / sequencing** — fixes can be order-dependent (B builds on A; two touch one cell). Overlay records + replays in a deterministic order, not an unordered bag.
3. **Idempotency** — applying the overlay twice == once (no double-application / corruption).
4. **Conflict detection** — when a fresh run now produces a value a fix was overriding: the correction usually wins, BUT **flag** that the underlying pipeline value changed so an obsolete fix gets re-reviewed (not silently masking newly-correct data).
5. **Provenance + retire-ability** — each entry records WHY it exists, so once the pipeline emits the right value natively, the entry retires.
- Today's seed (the FULL set of pre-existing hand-fix catalogs — task_08 must enumerate all, not assume these are complete):
  `data/reference/manual_overrides.csv` (read by `09`; verified 3 rows, all market_maker) +
  `data/reference/corp_actions_merged.csv` (read by `07`; tags `manual_thinktank_audit`=34 + `verification_2026-05-31`=5) +
  `docs/research/unresolved_88_mismatches_audit.md` Category-1 (21 decided-but-unapplied split/bonus overrides with ratios) +
  `docs/research/data/drhp_recovered.csv` (16 SEBI-DRHP-recovered financials, incl. pat_suspect/review-needed flags) +
  DRHP staging. Formalize these into the ordered/idempotent/conflict-aware overlay.

**B. The reconciliation campaign (old-data cleanup) — STOPS all other dev while it runs:**
build overlay → regenerate fresh → DIFF vs current substrate → EVERY mismatch is a bug (new-data error OR stale hand-fix) → review+resolve each (classify which side is wrong) → only when ALL resolved + TRUSTED do we declare `pipeline+overlay=substrate` LIVE. Doubles as a full data-integrity sweep (surfaces latent bugs both directions).

**C. The unifying DATA & RULES ARCHITECTURE — six facets, one design:**
- **Ingestion** — scrapers → pipeline → substrate (exists) + live-capture for new IPOs/actions/stocks.
- **Identity / matching** — ISIN primary key; corp actions = symbol∪substrate-ISIN + trading-date window + collision handling (promote D-1's join learnings to a STANDING principle).
- **Rules / applicability** — which check/hypothesis applies to which data (cohort/era/`data_quality_tier` gating, min-N) — make the data↔rule mapping explicit.
- **Layering / overlay** — fixes layered over pipeline output (= A above).
- **Old-data cleanup** — the reconciliation campaign (= B above).
- **New-data handling (once live)** — classify + apply rules/fixes IN-PLACE as data arrives, so we never re-accumulate a hand-fix backlog.

**D. Fence the known reproducibility breakers** (verified in code + `improvement_backlog.md` Technical-Debt items 1/6/7).
Design how to make a re-run replay deterministically from cached raw. The full breaker set the design must fence:
- `06_validate_tickers.py` (`fetch_chart` → LIVE Yahoo calls) — non-deterministic external dependency.
- re-running scrapers OVERWRITES the raw cache — destroys the replayable input.
- **date/year TIMEBOMBS** (backlog TD-1): `01_build_base` `hi=2026` fallback (breaks in 2027), chittorgarh `YEARS` array,
  the `'2026-27'` FY param, the `page<=300` limit — hardcoded values that silently change behavior over time.
- **silent try/except row-drops** (backlog TD-7): naked `except` blocks that DROP tickers — this breaks BOTH
  reproducibility AND completeness (rows vanish non-deterministically). At minimum task_09 (reconciliation) must flag
  silent-drop as a diff CLASS so vanished rows surface rather than disappearing.

## 🧩 STARTING LEANINGS — **NOT FINAL** (owner 2026-06-17)
> ⚠️ **NOTHING here is decided — including the data layout.** Every item below is only a *starting point*. Each is to be
> **re-derived from scratch, one by one, in its own task_x.md**, worked through properly, and put through multiple/different
> review lenses BEFORE any proposal is offered to the owner. Treat these as hypotheses to challenge, not answers.
1. **Data layout (leaning) = 2 canonical masters + derived views** (see next section). 2 sources of truth (`mainboard`, `sme`,
   shared schema); ALL other datasets (clean substrate, dirty worklist, longterm/shortterm cohorts, combined) are
   **derived views** = scripts that filter/pull from the 2, regenerated on demand. Readable physical files, single
   source of truth, no duplication.
2. **Dirty set = a derived view** (`quality==dirty`) of the 2 masters — a **quarantine** (rows get cleaned → flip to
   clean → it shrinks). Not a permanent separate store.
3. **Minimal flags = avoid BEHAVIORAL flags; keep a tiny set of STRUCTURAL partition columns** (`board`, `quality`,
   compact present/absent provenance). Structural columns REPLACE if/else, behavioral flags CREATE it.
4. **Scope = design + issue-register + cleaning-RULES design** (rules designed declarative/data-driven, NOT hardcoded
   branches). Still **zero code**.
5. **Column registry IS the target** — adding a column = register it once (name · source(s) · parser · missing-policy ·
   validity check); the pipeline handles it generically. No bespoke script per column. New-column gaps auto-handled by the same missing-policy.
6. **Future universe = expandable, NOT built now.** Don't add non-IPO/live-data capability; just ensure the design
   won't need restructuring to add them later (e.g. a `universe_type` seam, source/frequency abstraction kept open).
7. **Web evidence = LAST step only, optional.** Design-only run; if (and only if) everything else is finished, agy may
   gather web evidence on flagged stocks as the final step. Never let web search block the design work.
8. **Sequencing = base-first, layer-by-layer.** Tonight: EVERYTHING except code (design + issue-register + cleaning
   rules + reviews). Tomorrow: owner reviews end-to-end → discuss → approve → **then build the base** → **then** fix
   D-1 + other pipeline issues *through* the now-solid base. (D-1 is no longer the immediate boulder; the foundation is.)

## 🗄 CANDIDATE DATA LAYOUT — **NOT FINAL** (a starting point; re-derived in its own task, multi-lens reviewed)
```
SOURCE OF TRUTH (2 files, one shared schema via the column registry):
  mainboard.csv   ─┐  all years; every row; carries structural cols: board, quality(clean|dirty),
  sme.csv         ─┘  + compact present/absent provenance. NO behavioral flags.

DERIVED VIEWS (scripts/filters — regenerated, never hand-edited, can be temp or materialized):
  clean analysis substrate    = rows where quality==clean       (what Layer-3 / app consume)
  dirty / quarantine worklist = rows where quality==dirty       (the cleanup queue → promote when fixed)
  longterm / shortterm cohort = date-range filters
  combined MB+SME             = union, when a view needs both
```
- **Why:** matches "2 base files, others are just scripts" + minimal flags + extensibility, with one source of truth.
- **Open sub-designs for the run:** (a) compact present/absent encoding (no per-field boolean explosion);
  (b) whether the 2 masters are stored directly or themselves materialized from one internal spine (impl detail);
  (c) exactly which structural columns are essential vs droppable.

## 📝 NOTE — backlog/roadmap reconciliation (do during tomorrow's review, not tonight)
This charter now owns the foundation DESIGN. After owner approval: update `improvement_backlog.md` (TODO-D1c /
DATA & RULES ARCHITECTURE) + `roadmap.md` + the handoff to point here and reflect base-first sequencing. (Flagged so it isn't forgotten.)

## 📎 DESIGN OUTPUT DOCS (created during the run)
- **`docs/research/night_run/task_NN_*.md`** — ONE file per task (the deep per-task work + its multi-lens review trail + its non-final proposal). The primary artifacts.
- `docs/research/data_architecture_design_2026-06-17.md` — the synthesized target design (rolls up the architecture tasks: schema · sourcing · present-vs-absent · layout · registry · overlay · reconciliation · cleaning-rules · features↔data · future-universe seams).
- `docs/research/data_issue_register_2026-06-17.md` — the consolidated issue register (rolls up the Group-B tasks; incl. re-audit of already-fixed items).
- `docs/research/night_run_2026-06-17_review_log.md` — the review-round log (every task, every round, findings, when each went dry).
- All carry a **"decisions needed from owner"** block for the morning review. **Nothing is final.**

---
_Safety verified 2026-06-17: scope-guard live for BOTH Bash and Write/Edit (tested — out-of-folder writes/deletes/commits/network blocked, docs/research writes allowed); per-action + per-edit logging on at `docs/research/night_run/bash_action_log.tsv`._
