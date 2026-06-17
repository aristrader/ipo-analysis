"""Unit tests for pipeline/03l_merge_corporate_actions.py pure functions.

The critical invariants:
  - ratio_factor < 1.0  -> action_type MUST be 'consolidation', never 'split'
    (reverse-splits mislabeled as splits would multiply prices by ~10-100x)
  - A matched NSE action_type is inherited when ratio >= 1.0
  - Unmatched, ratio >= 1.0 -> 'unknown' (not guessed as 'split')
  - BSE numeric-code rows: resolve to ISIN when in universe, else isin='' + unmatched_bse_code flag
  - ratios_equal used for comparisons (not exact float equality)
"""
import importlib.util
import os
import sys

import pytest

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
def merge_mod():
    """pipeline/03l_merge_corporate_actions.py pure helpers."""
    return _load("pipeline/03l_merge_corporate_actions.py", "pipeline_03l")


# ── infer_action_type ────────────────────────────────────────────────────────

class TestInferActionType:
    def test_ratio_less_than_1_is_consolidation(self, merge_mod):
        """37 yahoo rows have ratio < 1.0; applying them as splits would corrupt prices."""
        f = merge_mod.infer_action_type
        assert f(0.1) == 'consolidation'      # e.g. 534563 ratio=0.1
        assert f(0.5) == 'consolidation'
        assert f(0.9999) == 'consolidation'

    def test_ratio_less_than_1_overrides_matched_type(self, merge_mod):
        """consolidation wins even if NSE matched something — ratio is the ground truth."""
        f = merge_mod.infer_action_type
        assert f(0.1, matched_nse_action_type='split') == 'consolidation'

    def test_matched_nse_type_inherited_when_ratio_ge_1(self, merge_mod):
        f = merge_mod.infer_action_type
        assert f(2.0, matched_nse_action_type='split')       == 'split'
        assert f(2.0, matched_nse_action_type='bonus')       == 'bonus'
        assert f(2.0, matched_nse_action_type='bonus+split') == 'bonus+split'

    def test_no_match_no_consolidation_is_unknown(self, merge_mod):
        """When we don't know, we say unknown — never fabricate 'split'."""
        f = merge_mod.infer_action_type
        assert f(2.0) == 'unknown'
        assert f(1.5, matched_nse_action_type=None) == 'unknown'
        assert f(1.5, matched_nse_action_type='') == 'unknown'

    def test_exactly_1_ratio_with_no_match_is_unknown(self, merge_mod):
        """Ratio=1.0 means no-op; without confirmation from NSE, call it unknown."""
        f = merge_mod.infer_action_type
        assert f(1.0) == 'unknown'


# ── resolve_isin ─────────────────────────────────────────────────────────────

class TestResolveIsin:
    def test_non_bse_code_returns_empty(self, merge_mod):
        f = merge_mod.resolve_isin
        isin, resolved = f('RELIANCE', False, {'534001': 'INE002A01018'})
        assert isin == '' and not resolved

    def test_bse_code_found_in_universe(self, merge_mod):
        f = merge_mod.resolve_isin
        isin, resolved = f('534001', True, {'534001': 'INE002A01018'})
        assert isin == 'INE002A01018' and resolved

    def test_bse_code_not_in_universe(self, merge_mod):
        f = merge_mod.resolve_isin
        isin, resolved = f('999999', True, {'534001': 'INE002A01018'})
        assert isin == '' and not resolved

    def test_bse_code_lookup_uses_string_key(self, merge_mod):
        """Symbol column from CSV comes in as string even if it looks numeric."""
        f = merge_mod.resolve_isin
        isin, resolved = f('534422', True, {'534422': 'INE123A01234'})
        assert isin == 'INE123A01234' and resolved


# ── ratios_equal usage ───────────────────────────────────────────────────────

class TestRatiosEqual:
    """Confirm ingest.ratios_equal is importable and behaves correctly for tolerance checks."""

    def test_exact_match(self):
        from foundation import ingest
        assert ingest.ratios_equal(2.0, 2.0)

    def test_near_match_within_tolerance(self):
        from foundation import ingest
        # 1.4285714... vs 1.428571 — same 1/7 ratio, float repr differs
        assert ingest.ratios_equal(1.4285714, 1.4285715)

    def test_clearly_different_ratios_not_equal(self):
        from foundation import ingest
        assert not ingest.ratios_equal(2.0, 3.0)

    def test_none_never_equal(self):
        from foundation import ingest
        assert not ingest.ratios_equal(None, 2.0)
        assert not ingest.ratios_equal(2.0, None)
        assert not ingest.ratios_equal(None, None)
