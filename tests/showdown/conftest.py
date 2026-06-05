"""Showdown suite gate: these are slow EXECUTION PROOFS (sandbox pipeline re-run,
entry-point smokes, app browser test). They are skipped unless SHOWDOWN=1, so the
default `pytest tests` stays fast. Run them with:

    SHOWDOWN=1 PYTHONPATH=. pytest tests/showdown -q

This is the pre-release / major-change gate (see docs/WORKFLOWS.md).
"""
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# applied to every test in this package
def pytest_collection_modifyitems(config, items):
    gate = pytest.mark.skipif(os.environ.get("SHOWDOWN") != "1",
                              reason="execution proof — set SHOWDOWN=1 to run")
    for item in items:
        if "/tests/showdown/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(gate)
            item.add_marker(pytest.mark.showdown)
