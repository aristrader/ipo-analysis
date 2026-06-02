"""Shared loaders for the pipeline test suite.

The numbered pipeline files (e.g. ``07_returns_summary.py``) cannot be imported
with a normal ``import`` statement because the module name starts with a digit,
and ``pipeline/`` is intentionally not a package. We load them by file path via
importlib. The modules self-bootstrap their own ``sys.path`` (inserting the
pipeline dir + repo root) at import time, so ``from listing_remediation import
...`` and ``from layer3 import config`` resolve correctly when exec'd here.

Loaded modules are cached so each is exec'd at most once per test session.
"""
import importlib.util
import os
import sys

import pytest

# Load pipeline source fresh, never via cached bytecode: these modules are loaded
# by file path, and a sub-second edit/rerun can otherwise serve a stale .pyc whose
# source-mtime collides with the edited file (a real footgun this suite hit once).
sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}


def _load(relpath, name):
    if name in _CACHE:
        return _CACHE[name]
    path = os.path.join(ROOT, relpath)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CACHE[name] = mod
    return mod


@pytest.fixture(scope="session")
def returns_mod():
    """pipeline/07_returns_summary.py — the price-derived outcomes math."""
    return _load("pipeline/07_returns_summary.py", "p07_returns")


@pytest.fixture(scope="session")
def remediation_mod():
    """pipeline/listing_remediation.py — listing-coverage remediation branches."""
    return _load("pipeline/listing_remediation.py", "p_listing_remediation")


@pytest.fixture(scope="session")
def lib_mod():
    """pipeline/lib.py — shared pure helpers (fnum/num/last_pre_listing_fy)."""
    return _load("pipeline/lib.py", "p_lib")
