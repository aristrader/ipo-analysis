"""Mutation batch runner: apply each deliberate break, run its test scope, demand
a FAILURE (the mutant is 'killed'), restore via git, clear pycache (the stale-.pyc
lesson). Writes docs/research/showdown_mutation.md. Exit 1 if any mutant SURVIVES.

Safety: refuses to start unless every target file is committed-clean in git.
Run:  PYTHONPATH=. .venv/bin/python tools/mutation/run_mutations.py
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mutations import MUTATIONS  # noqa: E402


def sh(args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)


def clear_pyc():
    for d in ("layer3", "pipeline", "scrapers", "tests"):
        for root, dirs, _ in os.walk(os.path.join(ROOT, d)):
            for x in list(dirs):
                if x == "__pycache__":
                    shutil.rmtree(os.path.join(root, x), ignore_errors=True)


def main():
    targets = sorted({m["file"] for m in MUTATIONS})
    dirty = sh(["git", "status", "--porcelain", "--"] + targets).stdout.strip()
    if dirty:
        print(f"REFUSING: target files not committed-clean:\n{dirty}")
        sys.exit(2)

    results = []
    for i, m in enumerate(MUTATIONS, 1):
        path = os.path.join(ROOT, m["file"])
        src = open(path).read()
        if src.count(m["old"]) != 1:
            results.append((m["label"], "BAD-PATTERN", f"old text found {src.count(m['old'])}x"))
            print(f"[{i:2d}/{len(MUTATIONS)}] {m['label']:42s} BAD-PATTERN")
            continue
        open(path, "w").write(src.replace(m["old"], m["new"], 1))
        clear_pyc()
        p = sh([sys.executable, "-m", "pytest", m["tests"], "-q", "-x"],
               env={**os.environ, "PYTHONPATH": ROOT}, timeout=300)
        killed = p.returncode != 0
        sh(["git", "checkout", "--", m["file"]])
        clear_pyc()
        results.append((m["label"], "KILLED" if killed else "SURVIVED", m["tests"]))
        print(f"[{i:2d}/{len(MUTATIONS)}] {m['label']:42s} {'KILLED' if killed else '** SURVIVED **'}")

    survived = [r for r in results if r[1] == "SURVIVED"]
    bad = [r for r in results if r[1] == "BAD-PATTERN"]
    killed_n = sum(1 for r in results if r[1] == "KILLED")
    with open(os.path.join(ROOT, "docs/research/showdown_mutation.md"), "w") as f:
        f.write("# Showdown P4 — Mutation Validation of the Test Suite\n\n")
        f.write(f"**{killed_n}/{len(results)} mutants killed** · "
                f"{len(survived)} survived · {len(bad)} bad patterns\n\n")
        f.write("Each row = a deliberate code break; KILLED means at least one test failed "
                "(the net works there). SURVIVED = vacuous coverage -> a test was added.\n\n")
        f.write("| mutation | result | test scope |\n|---|---|---|\n")
        for label, res, t in results:
            f.write(f"| {label} | {res} | `{t}` |\n")
    print(f"\n{killed_n}/{len(results)} killed; survivors={len(survived)}; bad={len(bad)}")
    sys.exit(1 if (survived or bad) else 0)


if __name__ == "__main__":
    main()
