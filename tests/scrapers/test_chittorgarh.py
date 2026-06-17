"""Tests for scrapers/chittorgarh.py pure-parse helpers.

Covers:
  (a) No fabrication — missing OFS field -> None; real 0 OFS -> '0'/'0.0'.
  (b) fail-vs-no-data — fetch_status column distinguishes no_url / http_<code> / ok / error_out.
All tests are offline; no network calls.
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}


def _load_cg():
    if 'cg' in _CACHE:
        return _CACHE['cg']
    path = os.path.join(ROOT, 'scrapers', 'chittorgarh.py')
    spec = importlib.util.spec_from_file_location('scr_cg', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CACHE['cg'] = mod
    return mod


# ── _ofs_from_kv ──────────────────────────────────────────────────────────────

class TestOfsFromKv:
    """CG-1: OFS value must come only from the source's 'Offer for Sale' field."""

    def test_ofs_absent_returns_none_none(self):
        """No 'Offer for Sale' key -> (None, None); never fabricates from (total - fresh)."""
        cg = _load_cg()
        kv = {'Total Issue Size': '₹ 100 Cr', 'Fresh Issue': '₹ 60 Cr'}
        ofs_cr, ofs_pct = cg._ofs_from_kv(kv)
        assert ofs_cr is None, "ofs_cr must be None when source has no 'Offer for Sale'"
        assert ofs_pct is None

    def test_ofs_present_returns_value(self):
        """Source publishes OFS -> value is returned."""
        cg = _load_cg()
        kv = {'Total Issue Size': '₹ 200 Cr', 'Fresh Issue': '₹ 120 Cr',
              'Offer for Sale': '₹ 80 Cr'}
        ofs_cr, ofs_pct = cg._ofs_from_kv(kv)
        assert ofs_cr == '80', f"expected '80', got {ofs_cr!r}"
        assert ofs_pct == '40.0', f"expected '40.0', got {ofs_pct!r}"

    def test_ofs_zero_real_zero_survives(self):
        """A genuine published OFS of 0 (₹ 0 Cr) must not be swallowed."""
        cg = _load_cg()
        kv = {'Total Issue Size': '₹ 100 Cr', 'Offer for Sale': '₹ 0 Cr'}
        ofs_cr, ofs_pct = cg._ofs_from_kv(kv)
        assert ofs_cr == '0', f"expected '0', got {ofs_cr!r}"

    def test_ofs_no_total_pct_is_none(self):
        """OFS present but no total -> ofs_cr returned, ofs_pct is None (can't divide)."""
        cg = _load_cg()
        kv = {'Offer for Sale': '₹ 50 Cr'}
        ofs_cr, ofs_pct = cg._ofs_from_kv(kv)
        assert ofs_cr == '50'
        assert ofs_pct is None

    def test_empty_kv_returns_none_none(self):
        cg = _load_cg()
        assert cg._ofs_from_kv({}) == (None, None)

    def test_only_fresh_no_ofs_returns_none_none(self):
        """Fresh-only IPO with no OFS published -> (None, None), not (0, 0)."""
        cg = _load_cg()
        kv = {'Total Issue Size': '₹ 50 Cr', 'Fresh Issue': '₹ 50 Cr'}
        assert cg._ofs_from_kv(kv) == (None, None)


# ── fetch_status in DETAIL_COLS ───────────────────────────────────────────────

class TestDetailColsFetchStatus:
    """CG-2: fetch_status column must exist so caller can distinguish outcomes."""

    def test_fetch_status_in_detail_cols(self):
        cg = _load_cg()
        assert 'fetch_status' in cg.DETAIL_COLS, (
            "DETAIL_COLS must contain 'fetch_status' (CG-2)"
        )

    def test_no_url_sets_status(self):
        """Row with no detail_url -> fetch_status='no_url', not all-None-with-no-status."""
        cg = _load_cg()

        class _FakeScraper:
            def get(self, *a, **kw):
                raise AssertionError("should not fetch when no url")

        rec = cg.scrape_detail(_FakeScraper(), {'chittorgarh_id': '123',
                                                 'isin': 'INE000X00001',
                                                 'company_name': 'Test Co',
                                                 'type': 'MB',
                                                 'detail_url': ''})
        assert rec['fetch_status'] == 'no_url', (
            f"expected 'no_url', got {rec['fetch_status']!r}"
        )

    def test_http_error_sets_status(self):
        """Non-200 HTTP response -> fetch_status='http_<code>'."""
        cg = _load_cg()

        class _FakeResp:
            status_code = 403
            text = ''

        class _FakeScraper:
            def get(self, *a, **kw):
                return _FakeResp()

        rec = cg.scrape_detail(_FakeScraper(), {'chittorgarh_id': '999',
                                                  'isin': 'INE000X00002',
                                                  'company_name': 'Blocked Co',
                                                  'type': 'SME',
                                                  'detail_url': 'https://example.com/ipo/test/999/'})
        assert rec['fetch_status'] == 'http_403', (
            f"expected 'http_403', got {rec['fetch_status']!r}"
        )
