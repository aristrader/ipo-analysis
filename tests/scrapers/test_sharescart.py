"""Tests for scrapers/sharescart.py pure-parse helpers.

Covers:
  (a) No fabrication — absent price-band -> (None, None); real data -> real values.
  (b) Fixed-price IPO (low == high) -> book_built='False' only when source gave the data.
All tests are offline; no network calls.
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}


def _load_sc():
    if 'sc' in _CACHE:
        return _CACHE['sc']
    path = os.path.join(ROOT, 'scrapers', 'sharescart.py')
    spec = importlib.util.spec_from_file_location('scr_sc', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CACHE['sc'] = mod
    return mod


# ── _book_built_fields ────────────────────────────────────────────────────────

class TestBookBuiltFields:
    """SC-1: book_built / price_band_width_pct must not be fabricated when data is absent."""

    def test_no_price_band_returns_none_none(self):
        """Basic Info block absent -> both fields must be None, not 'False'/'0'."""
        sc = _load_sc()
        bb, width = sc._book_built_fields(None, None)
        assert bb is None, f"book_built must be None when price_band_low is absent, got {bb!r}"
        assert width is None, f"price_band_width_pct must be None when price_band_low absent, got {width!r}"

    def test_no_price_band_low_returns_none_none(self):
        """Only issue_price known, no band -> (None, None)."""
        sc = _load_sc()
        bb, width = sc._book_built_fields(None, '185')
        assert bb is None
        assert width is None

    def test_no_issue_price_returns_none_none(self):
        """Only band_low known, no issue_price -> (None, None)."""
        sc = _load_sc()
        bb, width = sc._book_built_fields('175', None)
        assert bb is None
        assert width is None

    def test_book_built_true_when_band_spread(self):
        """Price band 175–185 -> book_built='True', width ~5.71%."""
        sc = _load_sc()
        bb, width = sc._book_built_fields('175', '185')
        assert bb == 'True', f"expected 'True', got {bb!r}"
        assert width is not None
        assert abs(float(width) - 5.71) < 0.02, f"width {width} out of tolerance"

    def test_book_built_false_when_fixed_price(self):
        """Fixed-price IPO (low == high) -> book_built='False', width='0.00'."""
        sc = _load_sc()
        bb, width = sc._book_built_fields('100', '100')
        assert bb == 'False', f"expected 'False', got {bb!r}"
        assert width == '0.00', f"expected '0.00', got {width!r}"

    def test_real_zero_price_band_low_width_none(self):
        """Edge: price_band_low='0' -> width is None (divide-by-zero guard, not fabricated '0')."""
        sc = _load_sc()
        bb, width = sc._book_built_fields('0', '100')
        # book_built is True (0 != 100), but width should be None (can't compute %)
        assert bb == 'True'
        assert width is None, f"expected None for zero-low, got {width!r}"

    def test_non_numeric_inputs_return_none_none(self):
        """Garbage input -> (None, None), not crash."""
        sc = _load_sc()
        bb, width = sc._book_built_fields('n/a', '--')
        assert bb is None
        assert width is None
