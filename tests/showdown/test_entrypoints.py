"""Execution proof #2: every analysis entry point still RUNS, green, against the
real (read-only) substrate — with a hash guard proving none of them wrote to it.

run_weights is deliberately absent: it WRITES data/master/scorecard_weights.json,
so it is exercised only inside the sandbox (see test_pipeline_sandbox), never here.
run_refresh needs the network -> excluded (documented in the audit).
"""
import hashlib
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _hash_master():
    h = hashlib.md5()
    for f in sorted(os.listdir(os.path.join(ROOT, "data/master"))):
        if f.endswith(".csv") or f.endswith(".json"):
            h.update(open(os.path.join(ROOT, "data/master", f), "rb").read())
    return h.hexdigest()


def _run(args, timeout=420):
    before = _hash_master()
    p = subprocess.run([sys.executable] + args, cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": ROOT},
                       capture_output=True, text=True, timeout=timeout)
    after = _hash_master()
    assert before == after, f"{args[0]} WROTE to data/master — it must stay read-only!"
    assert p.returncode == 0, f"{args[0]} failed rc={p.returncode}:\n{p.stderr[-1500:]}"
    return p.stdout


def test_report_builds_with_29_findings():
    out = _run(["run_layer3_report.py"])
    html = os.path.join(ROOT, "report", "layer3_partA.html")
    assert os.path.exists(html) and os.path.getsize(html) > 100_000
    text = open(html, encoding="utf-8", errors="ignore").read()
    assert text.count("<h2") >= 29, "report has fewer than 29 finding sections"


def test_predictor_scores_mb_and_sme():
    for t in ("MB", "SME"):
        out = _run(["predict_ipo.py", "--type", t, "--sector", "Healthcare",
                    "--sub_total_x", "20", "--gmp_pct", "30", "--revenue", "150"])
        assert "score" in out.lower() or "COMBINED" in out, f"predictor ({t}) produced no score output"


def test_backtester_runs():
    out = _run(["run_backtest.py"])
    assert len(out) > 200


def test_validation_runs():
    out = _run(["run_validation.py"])
    assert len(out) > 200


def test_oos_runs():
    out = _run(["run_oos.py"])
    assert len(out) > 100
