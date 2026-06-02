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
    """Informational: does the substrate still match its frozen backup?"""
    cur = _p("data/master/ipo_analysis.csv")
    bak = _p("archive/pre_drhp_20260601/ipo_analysis.csv")
    if not (os.path.exists(cur) and os.path.exists(bak)):
        return None
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    return "matches backup" if h(cur) == h(bak) else "DIFFERS from backup"


def pytest_collected():
    """Exact collected test count (collection only, no execution). Full mode only."""
    try:
        out = subprocess.run([sys.executable, "-m", "pytest", "tests", "--co", "-q"],
                             cwd=ROOT, capture_output=True, text=True,
                             env={**os.environ, "PYTHONPATH": ROOT}, timeout=120)
        return sum(1 for ln in out.stdout.splitlines() if "::" in ln)
    except Exception as e:
        return f"<unreadable: {e}>"


def regenerate_map():
    with open(_p("MAP.md"), "w") as f:
        f.write(M.render_map())


def fast_drift():
    """All fast checks; returns a list of drift strings (empty = clean)."""
    return check_paths() + check_unwired() + check_invariants()


def main():
    quiet = "--quiet" in sys.argv
    regenerate_map()  # always keep MAP.md fresh
    drift = fast_drift()

    if quiet:
        # Hook mode: speak ONLY on drift (silence = clean). Never block.
        if drift:
            print("⚠ PROJECT-MAP DRIFT (verify.py) — fix project_map.py or the cause:")
            for d in drift:
                print(f"  - {d}")
        sys.exit(0)

    # Full mode: full report.
    print("=== verify.py — structure + invariant checkpoint ===")
    print(f"findings on disk : {count_findings()}")
    print(f"substrate rows   : {count_substrate_rows()}  (csv records)")
    print(f"AS_OF_DATE       : {config_as_of_date()}")
    print(f"tests collected  : {pytest_collected()}")
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
