"""Loaders for the scraper test suite.

Scrapers are guarded by ``if __name__ == '__main__'`` so importing them runs no
network code — only top-level imports + pure helper definitions. We still load
by file path (uniform with the pipeline suite) and cache per session.
"""
import importlib.util
import os
import sys

import pytest

# See tests/pipeline/conftest.py: avoid serving a stale .pyc for path-loaded source.
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
def corp_actions_mod():
    """scrapers/corp_actions.py — split/bonus text -> ratio_factor parsing."""
    return _load("scrapers/corp_actions.py", "scr_corp_actions")


@pytest.fixture(scope="session")
def screener_mod():
    """scrapers/screener.py — financials parsing + name matching."""
    return _load("scrapers/screener.py", "scr_screener")


@pytest.fixture(scope="session")
def ipowatch_mod():
    """scrapers/ipowatch.py — subscription/GMP/date parsing."""
    return _load("scrapers/ipowatch.py", "scr_ipowatch")


@pytest.fixture(scope="session")
def sharescart_mod():
    """scrapers/sharescart.py — list/detail text normalizers."""
    return _load("scrapers/sharescart.py", "scr_sharescart")


@pytest.fixture(scope="session")
def chittorgarh_mod():
    """scrapers/chittorgarh.py — the IPO spine source normalizers."""
    return _load("scrapers/chittorgarh.py", "scr_chittorgarh")


@pytest.fixture(scope="session")
def nse_session_mod():
    """scrapers/nse_session.py — shared NSE anti-bot session priming."""
    return _load("scrapers/nse_session.py", "scr_nse_session")


@pytest.fixture(scope="session")
def nse_subscription_mod():
    """scrapers/nse_subscription.py — delegates priming to nse_session."""
    return _load("scrapers/nse_subscription.py", "scr_nse_subscription")
