# HANDOVER — Data-Foundation Rebuild (read this FIRST to resume)

**Last worked:** 2026-06-18. **Status:** paused mid-discussion (owner stepping away). Nothing is lost —
everything is on disk; this doc is the single entry point to pick up from the exact spot.

---

## 0. Where we are, in one paragraph
We are **rebuilding the IPO dataset's data foundation** (clean · honest · correct) instead of patching bugs
forever. **Phase 0 is DONE and committed** (honest scrapers + a full fresh re-fetch into `data_build/` + a
config/registry framework). **Phase 1 task T1.1 (the provenance engine) is BUILT but UNCOMMITTED and KNOWN to
need a correction.** We then did a big research + review pass and found **40 tracked issues** (in
`10_issue_tracker.md`). We were in a **discussion phase**, sorting issues into "Claude handles" (Bucket A) vs
"needs owner decision" (Bucket B), walking Bucket A in groups of 3 — **groups 1–3 are decided, group 4 onward
is pending.** No new code has been written since T1.1; the recent work is all research docs + decisions.

## 1. What the project is
A personal research tool to find repeatable patterns in Indian IPOs (2006–2026). Full context:
`/CLAUDE.md` (project brain). The dataset/analysis was built (3 layers) but had data-quality bugs traced to a
careless build → hence this foundation rebuild. Branch: **`night-run-consolidation`**.

## 2. Why we're rebuilding (the pivot)
The root disease: the old data couldn't tell apart a **real value**, a **value the source never published**, and
a **fetch that broke** — they all collapsed into `0`/blank, silently poisoning analysis. The rebuild fixes this
at the source: honest scrapers + a provenance layer + per-field study + cross-source matching. Design docs:
- `docs/research/FOUNDATION_PLAN.md` — the decisions + the 10 phases (Phase 0..9).
- `docs/research/FOUNDATION_ARCHITECTURE.md` — how the pieces fit (registry/golden/overlay/spine).
- `docs/research/FOUNDATION_BUILD_SPEC.md` — concrete per-field facts + fallback orders (Part A).

## 3. EXACT RESUME POINT — do this next
1. **Re-read this doc + the issue tracker** (`10_issue_tracker.md`) — the 40 issues are the work queue.
2. **Finish the Bucket-A walkthrough** (you were explaining issues to the owner in groups of 3 so he understood
   them before fixing). Done: groups 1–3 (their decisions are recorded in the tracker). **Next: group 4 =
   ISS-30 (Insolation scrambled fields), ISS-32 (7 fake-zero market caps), ISS-33 (eps/pat sign).** Then the
   remaining Bucket-A items, then the **Bucket-B decisions** (§7 below).
3. **Then build, group by group, one issue at a time** — the owner's rhythm: explain → discuss → he says "go" →
   build (TDD) → independent review → he gets the summary. **Nothing is final without his explicit "go."**
4. The very first *build* action (once decisions are confirmed) is **Group 1 = correcting T1.1** (ISS-1/2/4/5).

## 4. Reading order to get back up to speed (end-to-end)
Read in this order; it takes ~20 min and fully reloads context:
1. `CLAUDE.md` — project brain (skim).
2. **THIS doc** — the resume state.
3. `docs/research/phase_prep/10_issue_tracker.md` — **the 40-issue work queue (the core)**.
4. `docs/research/phase_prep/00_INDEX.md` — index to the research docs (01–11).
5. The research docs as needed (each is short):
   - `01_phase1_provenance.md` — Phase-1 counts + recovery findings.
   - `02_reconciliation_build_vs_frozen.md` — what the fresh re-fetch changed.
   - `03_corp_action_d1.md` — corp-action over-count + the 25-dropped-events bug.
   - `04_structural_columns.md` · `05_identity_outliers.md` — structural + identity.
   - `06_joining_and_merge.md` — joining + data-copy/merge improvement proposals.
   - `07_open_questions.md` — early decision list (superseded by the tracker's Bucket B).
   - `08_additional_findings.md` — smaller findings + clean negatives.
   - `09_t1_1_corrected_rules.md` — **the T1.1 correction we worked out (subscription rule etc.).**
   - `11_sourcing_trust_map.md` — **per-field: where to source, coverage, what's trustable.**
6. `foundation/README.md` — the Phase-0 package map (config/ingest/registry/refetch).
7. `foundation/provenance.py` + `tests/foundation/test_provenance.py` — the T1.1 engine (the code under correction).

## 5. DONE / committed vs WIP / uncommitted
**Committed (Phase 0, all on branch `night-run-consolidation`, head `1f17b33`):**
- `foundation/` framework: `config.py` (the `OUTPUT_ROOT`→`data_build` knob), `ingest.py` (honesty layer),
  `registry/` (column catalog T0.2), `refetch.py` (orchestrator).
- All live scrapers made honest; 9 dead scrapers deleted.
- **The full fresh re-fetch is on disk in `data_build/`** (~3.5 GB, all raw payloads saved, 2,373 price files).
  Old `data/` is FROZEN as the comparison baseline.

**UNCOMMITTED (this is the live edge):**
- `foundation/provenance.py` + `tests/foundation/test_provenance.py` (T1.1 engine — BUILT, 288 tests green, but
  **ISS-1 says its subscription rule is WRONG and must be corrected before committing**).
- `foundation/registry/__init__.py` + `columns.yaml` (the two validators we added — also to be corrected per ISS-1/3).
- `docs/research/phase_prep/` (ALL the research + this handover — 13 files: docs 00–11 + HANDOVER).
- `docs/tracker/task_log.md`, `MAP.md` (auto).

⚠ **Preservation:** none of the above is committed. To be safe, consider a WIP commit on the branch (see §10).

## 6. The 40 issues — pointer + the critical ones
Full queue: `10_issue_tracker.md` (8 groups, each issue has a fix + status box). The 2 **CRITICAL**:
- **ISS-27** — MFE/MAE use raw issue_price vs adjusted → biased movement lens (sequence AFTER corp-action fixes).
- **ISS-28** — `market_cap_cr` is current → look-ahead leak (decided: mark current/exclude, loud).

High-impact others: **ISS-11** (corp-actions must be union-merged — 25 real recent events were dropped),
**ISS-40** (`listing_remediation.py` is a parallel split-guesser that can erase real crashes — reconcile with
the corp-action fix), **ISS-6/7/8** (subscription early-snapshot + cross-source matching), **ISS-29** (FPO fake
listing pops). Everything else is med/low and enumerated in the tracker.

## 7. Decisions — locked vs pending
**LOCKED (recorded in the tracker):**
- T1.1 subscription rule (ISS-1): a listed IPO can't be 0-subscribed → `0`/neg = `Missing_data`, keep `>0`, **no
  board logic**. (Owner proved the old "SME 0 = real" rule false.)
- ISS-10: downgrade the tranche-sum check (we have the total directly + cross-source match does the real work).
- ISS-27: sequence after the corp-action fixes (adjusted price must be right first).
- ISS-28: mark `market_cap_cr`/class current + state exclusion loudly; building an at-IPO cap = deferred.
- ISS-37: centralise the listing-metrics counts into MAP.md (don't hardcode in docs).

**Bucket A vs B (the split from the discussion):** every issue in the tracker **NOT** in the PENDING list below
is **Bucket A** = Claude implements it directly (it's either already decided above or has one obvious-correct
fix) — still following the working loop (owner's "go" before building each). The **walkthrough state**: Bucket-A
groups 1–3 were explained & OK'd; resume the explanation at **group 4 (ISS-30/32/33)**, then the rest of A.

**PENDING — need the owner (Bucket B):**
1. ISS-3 — GMP `0`: real 0% possible, or always placeholder? (lean: missing-but-flagged)
2. ISS-6/7/8/39 — the cross-source MATCH strategy (most fields are single-source — see `11_sourcing_trust_map.md`).
3. ISS-9 — T1.3 subscription recovery against the net-offer (anchor) base for book-built MB.
4. ISS-11/12/17 — corp-action union-merge + 45-day collapse + price-swap-preserve (lean: yes).
5. ISS-29 — exclude FPO/REIT/InvIT from listing-pop analysis (lean: yes).
6. ISS-21/22 — identity-history golden file + one canonical ticker + the 1,027 unverified longterm rows.
7. ISS-24 — Indiabulls/RattanIndia phantom bonus (verify → delete or reclassify).
8. ISS-23 — the gated refetch (18 MB-sub + 10 GMP).
9. ISS-26/BL-1 — build an at-IPO market cap, or leave absent?
10. ISS-38 — SME delistings have no reason text (affects the −100% rule).
11. ISS-35/36 — retire dead columns (`issue_expenses_cr`, `kpi_roce/roe`) or source them?

## 8. Principles we banked (the "how we work" + key insights — don't relearn these)
- **The honesty contract:** never mint a value; distinguish fetch-fail vs no-data; save raw before parsing.
- **Gate vs match (the key design insight):** the per-value **gate** (provenance engine) only rejects the
  *impossible* and marks doubt as `Missing_data`; it must **never bless an uncertain value as real**. *Promoting*
  a doubtful value to `present` belongs to the **cross-source match** (Phase 2). A single plausibility check
  can't catch a plausible-but-wrong value (e.g. Adani Wilmar's `0.26` snapshot) — only matching/study can.
- **"A `0` that can't physically be real is missing, not real"** — proved on subscription (a listed IPO can't be
  0-subscribed) and listing prices.
- **Study each kind of data before trusting it** — generic checks are a floor, not a guarantee.
- **Build-beside-old → swap, but the swap MERGES/PRESERVES (never wholesale-replace)** — else we lose delisted
  prices + dropped corp-actions.
- **ISIN is the only join key; names only flag** (a name-join silently missed Adani Wilmar in our own analysis).
- **Working loop:** explain → discuss → owner says "go" → build (TDD) → independent review → summary. Nothing
  final without explicit "go." Right-size the execution pipeline per `docs/research/execution_pipeline.md`.

## 9. Key facts
- **NO re-pull needed** — everything required is on disk: the fresh `data_build/` raw (all payloads, incl. the
  full chittorgarh pages that already hold the final subscription tables) + the frozen `data/` baseline. Fixes
  are re-parse/re-logic jobs, not re-fetch. The only future fetch is the owner-gated worklist (ISS-23).
- Substrate = `data/master/ipo_analysis.csv`, **2,384 rows** (count via pandas, not `wc -l`), 220 cols.
- Network is **default-deny** normally; it was opened for the research run. Playwright OFF by default.
- Branch + PR workflow; **never push to `main` without owner approval**; commit messages end with the
  `Co-Authored-By: Claude Opus 4.8 (1M context)` line.

## 10. To preserve the work (recommended before fully stepping away)
Everything is on disk but **uncommitted**. To make it bullet-proof, do a WIP commit on the branch:
```
git add docs/research/phase_prep/ docs/tracker/task_log.md foundation/ tests/foundation/ MAP.md
git commit -m "wip(foundation): T1.1 engine (pre-correction) + phase-prep research + 40-issue tracker + handover"
git push        # branch only — never main
```
(`data_build/` is gitignored by design — it's reproducible via `foundation/refetch.py`, so it stays local.)
This is reversible (branch only) and means a clean checkout later loses nothing. Ask the owner before committing
if unsure — but for a long pause, preserving is the safer default.

---

**Bottom line for resuming:** read §3 + the tracker, finish the Bucket-A walkthrough at **group 4**, settle the
Bucket-B decisions in §7, then build one issue at a time starting with the T1.1 correction (Group 1). The
hard thinking is done and written down — resuming is just working the queue.
