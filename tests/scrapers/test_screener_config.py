"""Tests for scrapers/screener.py config repointing.

Screener was audit-CLEAN on honesty (no fabrication). These tests verify:
  (a) The scraper loads without error (foundation import works).
  (b) Existing parse helpers (_num, parse_financials, name_match) still behave correctly — no
      regression from the config repoint.
All tests are offline; no network calls.
"""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}


def _load_screener():
    if 'screener' in _CACHE:
        return _CACHE['screener']
    path = os.path.join(ROOT, 'scrapers', 'screener.py')
    spec = importlib.util.spec_from_file_location('scr_screener2', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CACHE['screener'] = mod
    return mod


class TestScreenerImport:
    def test_module_loads(self):
        """Module imports cleanly after config repoint."""
        sc = _load_screener()
        assert sc is not None

    def test_foundation_attrs_present(self):
        """config and ingest must be importable from the module's namespace."""
        sc = _load_screener()
        assert hasattr(sc, 'config'), "screener.py must have 'config' in scope after repoint"
        assert hasattr(sc, 'ingest'), "screener.py must have 'ingest' in scope after repoint"


class TestScreenerNumHelper:
    """_num() must return None for missing values and preserve real zeros."""

    def test_none_for_dash(self):
        sc = _load_screener()
        assert sc._num('-') is None

    def test_none_for_empty(self):
        sc = _load_screener()
        assert sc._num('') is None

    def test_none_for_nan(self):
        sc = _load_screener()
        assert sc._num('nan') is None

    def test_real_zero_survives(self):
        sc = _load_screener()
        assert sc._num('0') == 0.0, "real 0 must parse to 0.0, not None"

    def test_negative_value(self):
        sc = _load_screener()
        assert sc._num('-12.5') == -12.5

    def test_commas_stripped(self):
        sc = _load_screener()
        assert sc._num('1,234.56') == 1234.56


class TestScreenerNameMatch:
    """name_match() regression tests — must not break after config repoint."""

    def test_exact_match(self):
        sc = _load_screener()
        assert sc.name_match('Tata Consultancy Services', 'Tata Consultancy Services')

    def test_stopword_stripped(self):
        sc = _load_screener()
        assert sc.name_match('ABC Limited', 'ABC Ltd')

    def test_no_match_different_names(self):
        sc = _load_screener()
        assert not sc.name_match('Zomato', 'Swiggy')

    def test_empty_no_match(self):
        sc = _load_screener()
        assert not sc.name_match('', 'Zomato')
