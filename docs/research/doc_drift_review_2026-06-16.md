# Doc / Structural-Drift Review — 2026-06-16

Read-only hunt for the "generator/citation moved out of sync with the file" mistake-class
(the one that hid `showdown_mutation.md`). Companion to `alignment_audit_2026-06-16.md`
(claims-vs-truth) and `structure_review_2026-06-16.md` (sprawl). NOTHING was changed.
Every concrete claim below was verified with `ls`/`grep` against disk (agy used only for breadth).

## Summary
- **8 findings** (3 new generated-vs-archive, 1 new live code-path bug, 4 stale-pointer clusters; several overlap prior audits and are cross-referenced not re-litigated).
- **Top 3:** (1) **DD-1/DD-2/DD-3** — three artifacts (`unresolved_88_mismatches_audit.md`, `enrichment_recovery_log.csv`, `longterm_inwindow_log.csv`) are WRITTEN by live scripts to `docs/research/` but the only on-disk copies sit in `docs/research/archive/` — *identical* to the showdown_mutation bug, just not yet caught. (2) **DD-4** — `thinktank/orchestration/nodes.py:223` READS `docs/research/task_log.md`, which does not exist (it's at `docs/tracker/task_log.md`): a real runtime broken read. (3) **DD-7** — `verify.py` PASSES on all of the above because it has no notion of file *kind*; that blind spot is the root cause.
- `showdown_mutation.md` itself is now CORRECT (generator + project_map both point at the live `docs/research/showdown_mutation.md`, which exists; no archive copy). The `rules/index.md` root-path issue (prior SR-7) is also RESOLVED (file now exists at root, 40KB). Listed here only to confirm closure.

---

## (1) Code path ↔ disk mismatch

### DD-4 — HIGH — `nodes.py` reads a task_log path that does not exist
- `thinktank/orchestration/nodes.py:223`: `task_log_path = ROOT_DIR / "docs" / "research" / "task_log.md"`.
- On disk: `docs/research/task_log.md` → **does NOT exist**. Real file: `docs/tracker/task_log.md` (38KB) — **exists**.
- project_map.py:191 and the generated MAP.md:34 already use the correct `docs/tracker/task_log.md`, so the code disagrees with the authority. If this node ever writes/reads the log it lands in the wrong dir or errors.
- Also wrong-pathed (doc-only, lower stakes, same root cause): CLAUDE.md:126 ("Log every non-trivial task in `docs/research/task_log.md`"), `docs/research/INDEX.md:27`, `docs/research/README.md:11`, `thinktank/memory/README.md:23`, `thinktank/orchestration/ui.py:229` (info-string only), `thinktank/orchestration/docs/{think_tank,app_think_tank}_architecture.md` (×4). `execution_pipeline.md` lines 24/73/83 also say `docs/research/task_log.md`.
- **Fix:** repoint the runtime read in `nodes.py:223` to `docs/tracker/task_log.md`; sweep the doc references (CLAUDE.md:126, INDEX.md:27, README.md:11, the thinktank docs) to the tracker path. (NOT covered by structure_review SR-8, which only handled `improvement_backlog`/`STATUS`.)
- **Kind:** `docs/tracker/task_log.md` = HISTORICAL (append-only log).

### DD-5 — INFO/RESOLVED — app screens reading `rules/index.md`
- `app/screens/registry.py:95` and `app/screens/track_record.py:331`: `config.ROOT / "rules/index.md"`.
- On disk: `rules/index.md` → **NOW EXISTS** (root, 40KB, modified today). The dead-path issue noted in the brief (and prior SR-7) is **resolved**; verified, no action.
- **Kind:** `rules/index.md` = CANONICAL (the verdict registry).

---

## (2) Generated-vs-static / archived confusion  (the core mistake-class)

### DD-1 — HIGH — `unresolved_88_mismatches_audit.md`: generator writes live, file lives in archive
- Generator: `tools/generate_audit_md.py:80` → `open('docs/research/unresolved_88_mismatches_audit.md', 'w')`.
- On disk: live path → **does NOT exist**; only copy is `docs/research/archive/unresolved_88_mismatches_audit.md` (9.4KB). **Exact showdown_mutation pattern.**
- Cited as live by an ACTIVE doc: `docs/pipeline.md:12` — "See `docs/research/unresolved_88_mismatches_audit.md`" → that path is dead. A reader/code following the pointer 404s.
- **Fix:** decide kind. Either (a) treat it as GENERATED → leave generator writing to `docs/research/`, delete the stale archive copy, re-run when needed (the file is a deterministic regeneration); or (b) treat it as a one-off concluded ARCHIVED audit → move/keep it in `archive/`, point `tools/generate_audit_md.py` and `docs/pipeline.md:12` at the archive path. Given it is a script-regenerable report, (a) is cleaner. NOTE: `generate_audit_md.py` itself is a one-off (hardcodes a `.gemini/antigravity-cli/...` source path — see alignment_audit DOC-5); confirm it still runs before relying on (a).
- **Kind:** GENERATED (deterministic script output).

### DD-2 — HIGH — `enrichment_recovery_log.csv`: pipeline writes live, file lives in archive
- Writer: `pipeline/research/enrich_recovery.py:37` → `AUDIT_PATH = p('docs/research/enrichment_recovery_log.csv')` (per-attempt audit trail).
- On disk: live path → **does NOT exist**; only copy `docs/research/archive/enrichment_recovery_log.csv` (11.2KB, 2026-06-01). Next run of the script will silently re-create it at `docs/research/` while the archive copy goes stale → two-homes drift.
- **Fix:** pick kind. It's an append/overwrite audit log from a re-runnable pipeline step → GENERATED. Either let it regenerate to `docs/research/` (delete archive copy) or repoint the writer to a logs/archive location and update the script's own header comment (`enrich_recovery.py:27`).
- **Kind:** GENERATED (pipeline audit CSV).

### DD-3 — HIGH — `longterm_inwindow_log.csv`: pipeline writes live, file lives in archive
- Writer: `pipeline/research/recover_inwindow_financials.py:23` → `AUDIT = p('docs/research/longterm_inwindow_log.csv')`.
- On disk: live path → **does NOT exist**; only copy `docs/research/archive/longterm_inwindow_log.csv` (9.9KB, 2026-06-01). Same drift mechanism as DD-2.
- **Fix:** same as DD-2 (decide GENERATED home, delete or repoint).
- **Kind:** GENERATED (pipeline audit CSV).

### DD-6 — INFO/RESOLVED — `showdown_mutation.md` (the original bug)
- Generator `tools/mutation/run_mutations.py:58` writes `docs/research/showdown_mutation.md`; file **exists** there (2.5KB); **no** archive copy; project_map.py:214 + MAP.md:39 + WORKFLOWS.md:57 all point at the live path. Fully consistent now. Verified, no action — included to confirm the fix held and to anchor the pattern the other DD-1/2/3 share.
- **Kind:** GENERATED.

---

## (3) Archived-but-cited-as-live

### DD-7 — LOW — archive roadmap/idea docs read as "live to-do" but are not cited as canonical
- agy flagged 5 `archive/` docs whose prose reads as active menus: `future_ideas.md`, `ideas_validation.md`, `layer3_enhancements_ideas.md`, `next_roadmap.md`, `technical_debt_todo.md`.
- Verified: none is cited by an authority as THE live source. Active references are casual idea-numbering only (`future_ideas` #2/Thread-C in `tools/research/scope_news_feed.py:1`, `newsfeed/*`, `signals/tier1_wave1_verdicts.md:185`); the canonical open-work menu is `improvement_backlog.md`. So this is *internal tone*, not a broken live pointer.
- **Fix:** optional — add a one-line "ARCHIVED — superseded by improvement_backlog.md" banner to the top of these 5 so their present-tense prose doesn't mislead. Low priority.
- **Kind:** ARCHIVED.
- (No ACTIVE-doc/code reference to a `docs/research/archive/...` path as a live source was found anywhere — the dangerous form of this category is absent.)

---

## (4) Stale pointers in the authorities

### DD-8 — MED (cross-ref, partly known) — `improvement_backlog.md` cited under `docs/research/`, lives in `docs/tracker/`
- File: `docs/tracker/improvement_backlog.md` (exists). Stale `docs/research/...`/bare references: `docs/tracker/STATUS.md:39`, `docs/research/README.md:11`, `docs/research/INDEX.md:10,15` (lists it as a `docs/research/` ACTIVE file), `thinktank/memory/README.md:25`, `thinktank/orchestration/docs/think_tank_architecture.md:59`.
- **Already documented as `structure_review_2026-06-16.md` SR-8 (HIGH).** Recorded here only because it is the same path-drift mechanism as DD-4 and should be fixed in the same sweep. No new evidence beyond SR-8.
- **Kind:** CANONICAL (the open-work menu).

### Authority spot-check results (no new findings)
- `project_map.py`: every quoted `.py/.md/.csv/.html` path resolves on disk (scripted existence check + `verify.py` PASS). No stale project_map pointers in *this* class beyond what alignment_audit already lists (drhp_recovery, newsfeed, tier1 → already noted in alignment_audit's DOC table). MAP.md (generated from project_map) is consistent with it.
- CLAUDE.md: root-path mentions of `run_layer3_report.py`/`predict_ipo.py`/`run_backtest.py`/`run_validation.py`/`run_weights.py` are bare (no dir); the actual files live in `scripts/` (e.g. `scripts/run_layer3_report.py`). Bare names read as root entrypoints that don't exist at root — borderline; flagged LOW (likely already implied by alignment_audit). Only `task_log.md` (DD-4) and `STATUS.md` (→ `docs/tracker/`, prior SR-9) are concrete CLAUDE.md path drifts.

---

## Prevention mechanism — recommendation

**Root cause (DD-7 lesson):** `verify.py` checks *existence* but not *kind*, so a GENERATED file rotting in `archive/` while its generator writes elsewhere is invisible. The fix is to give files a machine-checkable **kind** and let `verify.py` enforce kind-specific invariants.

**Recommended: option (b) — central classification in `project_map.py`, enforced by `verify.py`.** Not (a) per-file front-matter.

Rationale:
- The set that actually needs marking is *small* (see counts below) — front-matter on hundreds of concluded write-ups is overkill, and CSV/HTML artifacts can't carry markdown front-matter at all (DD-2/DD-3/DD-6 are CSV/HTML). A central map covers every file type uniformly.
- The authority is *already* `project_map.py` (verify.py already reads it every turn via the hook). Adding a `KIND` dict there is one new structure, zero new tooling, and it's the same place a file's path is declared — so kind and path can't drift apart.
- Front-matter (a) re-introduces the exact failure mode: the tag lives in the file, so when the file is moved the enforcement context moves with it and nothing notices a *missing* file (the showdown case was a missing live file, which front-matter can't catch).

Concrete enforcement to add to `verify.py` (3 rules):
1. **GENERATED must not live under `archive/`** and **its declared generator's write-path must equal its mapped on-disk path** (catches DD-1/2/3/6 directly — the rule that would have caught the original showdown bug).
2. **GENERATED file's mapped path must exist OR be marked regenerable** (so a not-yet-run generator doesn't false-alarm).
3. **ARCHIVED must not be referenced as a live source by CANONICAL files** (grep the authority set for `archive/<name>` used outside an index) — catches the DD-7 *dangerous* form before it appears.

Minimal schema in project_map.py:
```python
FILE_KINDS = {
    "docs/research/showdown_mutation.md": ("GENERATED", "tools/mutation/run_mutations.py"),
    "docs/research/unresolved_88_mismatches_audit.md": ("GENERATED", "tools/generate_audit_md.py"),
    "docs/research/enrichment_recovery_log.csv": ("GENERATED", "pipeline/research/enrich_recovery.py"),
    "docs/research/longterm_inwindow_log.csv": ("GENERATED", "pipeline/research/recover_inwindow_financials.py"),
    "MAP.md": ("GENERATED-INDEX", "verify.py"),
    "report/layer3_partA.html": ("GENERATED", "scripts/run_layer3_report.py"),
    # CANONICAL / HISTORICAL only where enforcement adds value:
    "rules/index.md": ("CANONICAL", None),
    "docs/tracker/STATUS.md": ("CANONICAL", None),
    "docs/tracker/task_log.md": ("HISTORICAL", None),
    "docs/tracker/improvement_backlog.md": ("CANONICAL", None),
    # archive dir: default-classify everything under docs/research/archive/ as ARCHIVED
}
```

### Rough file-count per kind (only what's worth tagging)
- **GENERATED:** ~6 (showdown_mutation.md, unresolved_88…md, enrichment_recovery_log.csv, longterm_inwindow_log.csv, report/layer3_partA.html, + the data/master review CSVs if desired). These are the only ones needing rule #1 — small, high-value.
- **GENERATED-INDEX:** 1 (MAP.md; already hash-guarded by verify.py).
- **CANONICAL:** ~6 (CLAUDE.md, project_map.py, rules/index.md, STATUS.md, improvement_backlog.md, the standing-brief docs). Need rule #3's "don't be superseded by archive."
- **HISTORICAL:** ~3 (task_log.md, batch_run_2026-06-09.md, the superpowers/plans|specs — legitimately name old paths; exempt from live-pointer checks).
- **ARCHIVED:** ~50 (everything under `docs/research/archive/` — classify by directory default, not per-file).
- **REFERENCE / write-ups:** the remaining ~50 concluded `docs/research/*.md` need NO tag (don't over-engineer).

Net: ~16 explicit entries + a directory default. That is the right size — it covers every file in the dangerous classes (GENERATED, CANONICAL, ARCHIVED-cited) without tagging the long tail.
