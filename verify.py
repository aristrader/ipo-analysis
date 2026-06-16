"""Structure + invariant checkpoint. Regenerates MAP.md and reports DRIFT.

Run modes:
  python verify.py            full report (incl. exact pytest-collected test count); always exits 0
  python verify.py --quiet    FAST checks only; prints ONLY if drift; for the per-turn hook

The per-turn UserPromptSubmit hook runs `--quiet` so its stdout (drift, if any) is
injected into the assistant's context BEFORE it acts — preventing action on stale
state. It NEVER blocks (always exit 0); it only informs.

Checks (fast): every path named in project_map.py exists; UNWIRED steps exist and
are not also wired; findings count, substrate row count (via csv, NOT wc -l), and
AS_OF_DATE match project_map.INVARIANTS; the data substrate matches its backup.
Full mode adds: exact pytest-collected test count + doc-count consistency.
"""
import csv
import glob
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import project_map as M


def _p(*a):
    return os.path.join(ROOT, *a)


def _exists(path):
    # directory entries in the map end with '/'
    full = _p(path)
    return os.path.isdir(full) if path.endswith("/") else os.path.exists(full)


def check_paths():
    missing = sorted(p for p in M.all_referenced_paths() if not _exists(p))
    return [f"path missing (in project_map, not on disk): {p}" for p in missing]


def check_unwired():
    issues = []
    wired = {path for _k, path, _r in M.PIPELINE}
    for path, _role in M.UNWIRED:
        if not _exists(path):
            issues.append(f"UNWIRED step listed but file missing: {path}")
        if path in wired:
            issues.append(f"step is in BOTH PIPELINE and UNWIRED: {path}")
    return issues


def count_findings():
    fs = [f for f in glob.glob(_p("layer3/findings/*.py")) if not f.endswith("__init__.py")]
    return len(fs)


def count_substrate_rows():
    """Accurate CSV record count (handles quoted multiline fields; wc -l does not)."""
    path = _p("data/master/ipo_analysis.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1  # minus header


def config_as_of_date():
    try:
        from layer3 import config
        return str(config.AS_OF_DATE)
    except Exception as e:
        return f"<unreadable: {e}>"


def check_invariants():
    issues = []
    nf = count_findings()
    if nf != M.INVARIANTS["n_findings"]:
        issues.append(f"findings: {nf} on disk vs {M.INVARIANTS['n_findings']} in project_map.INVARIANTS")
    rows = count_substrate_rows()
    if rows is not None and rows != M.INVARIANTS["substrate_rows"]:
        issues.append(f"substrate rows: {rows} vs {M.INVARIANTS['substrate_rows']} in INVARIANTS")
    aod = config_as_of_date()
    if aod != M.INVARIANTS["as_of_date"]:
        issues.append(f"AS_OF_DATE: config={aod} vs INVARIANTS={M.INVARIANTS['as_of_date']}")
    return issues


def data_backup_status():
    """Informational: does the substrate still match its archive snapshot?
    The snapshot location is a MOVABLE fact — substrate_meta.json's archive_pointer
    (run_refresh.py re-points it when it archives the previous substrate)."""
    cur = _p("data/master/ipo_analysis.csv")
    bak = _p(M.INVARIANTS.get("archive_pointer", ""), "ipo_analysis.csv")
    if not (os.path.exists(cur) and os.path.exists(bak)):
        return None
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    return "matches backup" if h(cur) == h(bak) else "DIFFERS from backup (expected right after a refresh)"


def pytest_collected():
    """Exact collected test count (collection only, no execution). Full mode only."""
    try:
        out = subprocess.run([sys.executable, "-m", "pytest", "tests", "--co", "-q"],
                             cwd=ROOT, capture_output=True, text=True,
                             env={**os.environ, "PYTHONPATH": ROOT}, timeout=120)
        return sum(1 for ln in out.stdout.splitlines() if "::" in ln)
    except Exception as e:
        return f"<unreadable: {e}>"


def regenerate_map(n_tests=None):
    with open(_p("MAP.md"), "w") as f:
        f.write(M.render_map(n_tests=n_tests))


def check_schema():
    """Schema-gate contracts (Thread B): surfaced as drift each turn (warn, never fail the hook).
    Catches data corruption the count/path checks miss — null headline cols, enum typos,
    ledger↔substrate referential gaps, listing-gain scale-inversion."""
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools/checks"))
        import schema_gate
        return [f"schema: {v}" for v in schema_gate.check_all()]
    except Exception as e:
        return [f"schema gate skipped ({type(e).__name__})"]


# ----------------------------------------------------- STRUCT-1: count-token guard
# The volatile counts (findings/tests/rows) live ONLY in the generated MAP.md
# CANONICAL FACTS block. Hand-docs must POINT there, never restate a literal. This
# regex catches a reintroduced "<number> tests/findings/rows" (and "<n> substrate
# rows"); it is deliberately narrow to avoid firing on legit prose (weights like
# "0.269", component counts like "8 components", "00->09 steps", "2026").
_COUNT_TOKEN = re.compile(r"\b\d{1,4}\s+(?:substrate\s+)?(tests|findings|rows)\b", re.I)


def _scan_count_tokens(path):
    """Return the offending '<n> <noun>' snippets found in a file (empty = clean)."""
    full = _p(path) if not os.path.isabs(path) else path
    if not os.path.exists(full):
        return []
    text = open(full, encoding="utf-8", errors="replace").read()
    return [m.group(0) for m in _COUNT_TOKEN.finditer(text)]


def check_doc_counts():
    """DRIFT if a guarded hand-doc reintroduces a hardcoded count token."""
    issues = []
    for doc in M.GUARDED_DOCS:
        for hit in _scan_count_tokens(doc):
            issues.append(
                f"hardcoded count in {doc}: {hit!r} — counts are canonical in MAP.md "
                "(point to `python verify.py`), don't restate them")
    return issues


# ----------------------------------------------- FILE_KINDS rules (mechanism (b))
# RULE B is deliberately SCOPED (the brief: "if a rule is too noisy, scope it down").
# DD-7 verified the *dangerous* form — an archive doc cited AS THE LIVE/CURRENT source —
# is absent; what's present are benign "superseded → see archive" / "lives in archive"
# pointers (rules/index.md, STATUS.md, CLAUDE.md). We must NOT flag those. So RULE B
# fires only on a LIVE-SOURCE directive: an archive path immediately preceded by phrasing
# that presents it as the authoritative place to look NOW (e.g. "the current ... is",
# "canonical ... :", "single source of truth"). Benign "see/in/lives in archive" is exempt.
_LIVE_SOURCE_CUE = re.compile(
    r"(?:current|canonical|single source(?: of truth)?|authoritative|the live)\b[^.\n]{0,40}$",
    re.I)


def _canonical_cites_archive(canonical_docs, archive_token, roots=None):
    """RULE B helper: report CANONICAL docs that cite an ARCHIVED path AS A LIVE SOURCE
    (not a benign 'see archive' pointer). `roots` lets tests point at a tmp dir."""
    roots = roots or [ROOT]
    issues = []
    for doc in canonical_docs:
        full = doc if os.path.isabs(doc) else _p(doc)
        if not os.path.exists(full):
            continue
        text = open(full, encoding="utf-8", errors="replace").read()
        idx = text.find(archive_token)
        while idx != -1:
            preceding = text[max(0, idx - 80):idx]
            if _LIVE_SOURCE_CUE.search(preceding):
                issues.append(
                    f"CANONICAL {os.path.relpath(full, roots[0])} cites ARCHIVED "
                    f"{archive_token} as a live source (RULE B)")
                break
            idx = text.find(archive_token, idx + 1)
    return issues


def _gen_cmd(gen):
    """Runnable hint to (re)generate a GENERATED file from its FILE_KINDS generator.
    `gen` is the generator's script path (or None). Derived here so the command is
    never a second hand-maintained literal that could drift from the path."""
    if not gen:
        return "see project_map.FILE_KINDS"
    if gen == "verify.py":
        return "python verify.py"
    return f"PYTHONPATH=. python {gen}"


def check_file_kinds(file_kinds=None):
    """FILE_KINDS enforcement (added to drift, never crashes):
    RULE A — a GENERATED file must NOT live only under archive/; where its generator's
             mapped write-path is known, the live mapped path must exist on disk.
    RULE B — an ARCHIVED file must NOT be cited as a live source by a CANONICAL doc."""
    fk = file_kinds if file_kinds is not None else M.FILE_KINDS
    issues = []
    # RULE A
    for path, (kind, gen) in fk.items():
        if kind not in ("GENERATED", "GENERATED_INDEX"):
            continue
        if "archive/" in path:
            issues.append(f"RULE A: GENERATED {path} is mapped under archive/ — move to its live write-path")
            continue
        live = _p(path)
        arch_candidate = _p(os.path.join("docs/research/archive", os.path.basename(path)))
        if not os.path.exists(live):
            if os.path.exists(arch_candidate):
                # the dangerous form: the only copy is stranded in archive/ — a real drift.
                issues.append(
                    f"RULE A: GENERATED {path} missing at its mapped live path "
                    "(a stale copy still sits in archive/) — "
                    "generator write-path, mapped path, and disk must agree")
            else:
                # benign on a fresh clone: a build artifact whose generator hasn't run yet.
                # KEEP the warning (visible drift) but make it ACTIONABLE — name the generator.
                issues.append(
                    f"RULE A: {path} (GENERATED) not present — generate via: {_gen_cmd(gen)}")
    # RULE B — scan CANONICAL docs (default set) for any ARCHIVED file citation
    canonical = [p for p, (k, _g) in fk.items() if k == "CANONICAL"]
    archived = sorted(glob.glob(_p("docs/research/archive/*")))
    for ap in archived:
        token = os.path.relpath(ap, ROOT)
        issues.extend(_canonical_cites_archive(canonical, token))
    return issues


def fast_drift():
    """All fast checks; returns a list of drift strings (empty = clean)."""
    return (check_paths() + check_unwired() + check_invariants() + check_schema()
            + check_doc_counts() + check_file_kinds())


# substantive code dirs whose changes mean "real task in progress / shipped"
_CODE_DIRS = ("layer3/", "pipeline/", "scrapers/", "app/", "tools/", "run_", "verify.py", "project_map.py")


def _is_code(p):
    return any(p.startswith(d) or ("/" + d) in p for d in _CODE_DIRS) and p.endswith(".py")


def pipeline_nudges():
    """Execution-pipeline reminders — CONDITIONAL (not every turn):
    (1) work-in-progress: substantive code is uncommitted → remind to follow the pipeline;
    (2) tripwire: the last commit changed code but didn't touch task_log.md → flag a possibly
        un-logged (one-dimensioned) task."""
    out = []
    try:
        changed = changed_files()
        if any(_is_code(p) for p in changed):
            out.append("◆ Code in progress — follow docs/research/execution_pipeline.md "
                       "(triage → diverge → converge → build → REVIEW → test). Log it in task_log.md.")
        last = subprocess.run(["git", "show", "--name-only", "--pretty=format:", "HEAD"],
                              cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.split()
        if any(_is_code(p) for p in last) and not any("task_log.md" in p for p in last):
            out.append("⚠ Last commit changed code but didn't update docs/research/task_log.md — "
                       "was the pipeline followed/logged? (skip only for a true one-liner/hotfix).")
    except Exception:
        pass
    return out


# ------------------------------------------------------ change -> tests routing
def changed_files():
    """Paths with uncommitted changes (staged or not), per git."""
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    paths = []
    for line in out.splitlines():
        p = line[3:].strip().strip('"')
        if " -> " in p:                      # renames: take the new side
            p = p.split(" -> ", 1)[1]
        paths.append(p)
    return paths


def route(paths):
    """Map changed paths through project_map.TEST_ROUTING (first glob match wins).
    Returns {path: [commands]} for files that matched."""
    import fnmatch
    routed = {}
    for p in paths:
        for pattern, cmds in M.TEST_ROUTING:
            if fnmatch.fnmatch(p, pattern):
                routed[p] = cmds
                break
    return routed


def routing_lines(paths):
    """Human/assistant-readable 'CHANGED -> RUN' lines (deduped commands last)."""
    routed = route(paths)
    if not routed:
        return []
    lines = ["CHANGED FILES → TESTS TO RUN (project_map.TEST_ROUTING):"]
    cmds = []
    for p, cs in sorted(routed.items()):
        lines.append(f"  {p}")
        for c in cs:
            if c not in cmds:
                cmds.append(c)
    lines.append("  RUN:")
    lines.extend(f"    {c}" for c in cmds)
    return lines


def main():
    quiet = "--quiet" in sys.argv
    # Full mode embeds the exact pytest-collected count into MAP.md's CANONICAL FACTS
    # block; the fast hook skips pytest (stays ~0.1s) and writes a "run verify.py" pointer.
    n_tests = None if (quiet or "--route" in sys.argv) else pytest_collected()
    if isinstance(n_tests, str):  # "<unreadable: ...>" — don't bake an error into MAP.md
        n_tests = None
    regenerate_map(n_tests=n_tests)  # always keep MAP.md fresh
    drift = fast_drift()

    if quiet:
        # Hook mode. Pipeline reminder fires ONLY when substantive code is uncommitted (work in
        # progress) — not every chat turn (red-team #3: every-turn noise habituates → ignored).
        # Plus a TRIPWIRE: if the last commit changed code but skipped task_log.md, the pipeline
        # may have been one-dimensioned silently (red-team #1) — surface it.
        for line in pipeline_nudges():
            print(line)
        if drift:
            print("⚠ PROJECT-MAP DRIFT (verify.py) — fix project_map.py or the cause:")
            for d in drift:
                print(f"  - {d}")
        for ln in routing_lines(changed_files()):
            print(ln)
        sys.exit(0)

    if "--route" in sys.argv:
        ch = changed_files()
        lines = routing_lines(ch)
        print("\n".join(lines) if lines else "no uncommitted changes — nothing to route")
        sys.exit(0)

    # Full mode: full report.
    print("=== verify.py — structure + invariant checkpoint ===")
    print(f"findings on disk : {count_findings()}")
    print(f"substrate rows   : {count_substrate_rows()}  (csv records)")
    print(f"AS_OF_DATE       : {config_as_of_date()}")
    print(f"tests collected  : {n_tests if n_tests is not None else pytest_collected()}")
    bak = data_backup_status()
    if bak:
        print(f"substrate vs backup: {bak}")
    print("MAP.md regenerated.")
    if drift:
        print("\nDRIFT:")
        for d in drift:
            print(f"  - {d}")
    else:
        print("\nPASS — no structural/invariant drift.")
    sys.exit(0)


if __name__ == "__main__":
    main()
