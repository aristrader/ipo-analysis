"""Execution proof #1: the OFFLINE pipeline chain still runs end-to-end and
REPRODUCES the frozen substrate (up to the enumerated, documented exceptions).

Method (evidence: docs/research/showdown_pipeline_diff.md):
  copy repo+data to /tmp sandbox -> run 03b..05, 07, merge, 08, 09 there ->
  returns_summary must be byte-identical; ipo_analysis must be NUMERIC-equal
  except the allowed cells below. Anything new/unexplained fails the showdown.

The real repo is never written to. Network steps (00/06/lt-02) are excluded by
nature (live web moved since the freeze) — they get compile checks instead.
"""
import hashlib
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SANDBOX = "/tmp/ipo_showdown_sandbox_test"
CHAIN = [
    "pipeline/03b_fill_financials_screener.py", "pipeline/03c_fill_subscription_nse.py",
    "pipeline/03d_fill_ipowatch.py", "pipeline/03e_fill_gmp_investorgain.py",
    "pipeline/04_verify.py", "pipeline/05_reconcile.py", "pipeline/07_returns_summary.py",
    "scrapers/screener_prices_merge.py", "pipeline/08_build_universe.py", "pipeline/09_assemble.py",
]

# ---- the EXPLAINED differences (showdown_pipeline_diff.md) ----
# 1. three hand-folded market makers (exist only in final files, not raw caches)
ALLOWED_CELLS = {("INE00D001018", "market_maker"), ("INE05FR01029", "market_maker"),
                 ("INE813V01022", "market_maker")}
# 2. one ISIN whose screener cache rows arrived after the freeze (screener-wins refill)
ALLOWED_ISINS_ANY_COL = {"INE338Y01016"}
# staging/master snapshots are stale relative to the grown raw cache — final substrate unaffected
SKIP_FILES = {"sme.csv", "mainboard.csv", "_base_sme.csv", "_base_mainboard.csv"}


@pytest.fixture(scope="module")
def sandbox():
    """Build the sandbox and run the chain once for all tests in this module."""
    if os.path.exists(SANDBOX):
        shutil.rmtree(SANDBOX)
    subprocess.run(["rsync", "-a", "--exclude", ".git", "--exclude", ".venv",
                    "--exclude", "logs", "--exclude", "__pycache__",
                    "--exclude", ".pytest_cache", f"{ROOT}/", f"{SANDBOX}/"],
                   check=True, capture_output=True)
    os.makedirs(os.path.join(SANDBOX, "logs"), exist_ok=True)
    results = {}
    for step in CHAIN:
        p = subprocess.run([sys.executable, step], cwd=SANDBOX,
                           env={**os.environ, "PYTHONPATH": SANDBOX},
                           capture_output=True, text=True, timeout=600)
        results[step] = p
    yield results
    shutil.rmtree(SANDBOX, ignore_errors=True)


def test_every_offline_step_exits_zero(sandbox):
    failed = {s: p.returncode for s, p in sandbox.items() if p.returncode != 0}
    detail = "\n".join(f"{s}: rc={rc}\n{sandbox[s].stderr[-800:]}" for s, rc in failed.items())
    assert not failed, f"pipeline steps failed in sandbox:\n{detail}"


def test_returns_summary_reproduces_byte_identical(sandbox):
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    assert h(f"{ROOT}/data/master/returns_summary.csv") == h(f"{SANDBOX}/data/master/returns_summary.csv"), \
        "returns_summary.csv no longer reproduces byte-identically — the Layer-2 math changed!"


def test_substrate_numeric_identical_except_allowed(sandbox):
    a = pd.read_csv(f"{ROOT}/data/master/ipo_analysis.csv", dtype=str).set_index("isin")
    b = pd.read_csv(f"{SANDBOX}/data/master/ipo_analysis.csv", dtype=str).set_index("isin")
    assert set(a.index) == set(b.index), "substrate isin sets differ after re-run"
    b = b.loc[a.index]
    unexplained = []
    neq = (a.fillna("§") != b.fillna("§"))
    for col in a.columns[neq.any()]:
        m = neq[col]
        av, bv = a.loc[m, col], b.loc[m, col]
        an, bn = pd.to_numeric(av, errors="coerce"), pd.to_numeric(bv, errors="coerce")
        fmt_only = an.notna() & bn.notna() & np.isclose(an, bn, rtol=1e-9, atol=1e-12)
        for isin in av.index[~fmt_only]:
            if (isin, col) in ALLOWED_CELLS or isin in ALLOWED_ISINS_ANY_COL:
                continue
            unexplained.append((isin, col, str(av[isin]), str(bv[isin])))
    assert not unexplained, (
        f"{len(unexplained)} UNEXPLAINED substrate diffs after re-run (first 10): {unexplained[:10]}")


def test_real_repo_untouched_by_sandbox_run(sandbox):
    """The whole point: the real data/master must not have moved."""
    h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    real = f"{ROOT}/data/master/ipo_analysis.csv"
    bak = f"{ROOT}/archive/pre_drhp_20260601/ipo_analysis.csv"
    if os.path.exists(bak):
        assert h(real) == h(bak), "REAL substrate changed during the showdown — investigate immediately"


def test_run_weights_executes_in_sandbox(sandbox):
    """run_weights WRITES data/master/*.json, so its execution proof lives here
    (the sandbox), never in the in-place entry-point smokes. (Showdown gap-close.)"""
    import json
    p = subprocess.run([sys.executable, "run_weights.py"], cwd=SANDBOX,
                       env={**os.environ, "PYTHONPATH": SANDBOX},
                       capture_output=True, text=True, timeout=600)
    assert p.returncode == 0, f"run_weights failed:\n{p.stderr[-1200:]}"
    w = json.load(open(f"{SANDBOX}/data/master/scorecard_weights.json"))
    assert sum(w.values()) == pytest.approx(1.0, abs=0.01)


def test_network_steps_at_least_compile():
    import py_compile
    for step in ("pipeline/00_build_longterm_spine.py", "pipeline/06_validate_tickers.py",
                 "pipeline/longterm/02_detail.py"):
        py_compile.compile(os.path.join(ROOT, step), doraise=True)
