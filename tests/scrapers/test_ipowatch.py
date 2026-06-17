"""Tests for scrapers/ipowatch.py.

Covers:
  - parse_gmp_last: the new (value, gmp_status) return — ok / absent / parse_fail.
  - _evaluate: propagates gmp_status (4-tuple now).
  - Existing parse helpers: _num, _to_iso (regression guard).
"""
import io
import pytest


# ─── regression guards ───────────────────────────────────────────────────────

def test_num_strips_x_suffix(ipowatch_mod):
    assert ipowatch_mod._num("2.5x") == 2.5
    assert ipowatch_mod._num("2.5X") == 2.5


def test_num_returns_none_for_nonnumeric(ipowatch_mod):
    assert ipowatch_mod._num("abc") is None
    assert ipowatch_mod._num("") is None


def test_to_iso_parses_month_name(ipowatch_mod):
    assert ipowatch_mod._to_iso("May 20, 2022") == "2022-05-20"
    assert ipowatch_mod._to_iso("June 02, 2022") == "2022-06-02"
    assert ipowatch_mod._to_iso("garbage") is None


# ─── parse_gmp_last — new (value, gmp_status) contract ──────────────────────

def _gmp_table_html(rows):
    """Build minimal HTML with a GMP table for testing parse_gmp_last."""
    row_html = ''.join(f'<tr><td>2024-0{i+1}-01</td><td>₹{v}</td><td>-</td><td>-</td></tr>'
                       for i, v in enumerate(rows))
    return f'<table><thead><tr><th>Date</th><th>GMP</th><th>Kostak</th><th>Subject</th></tr></thead><tbody>{row_html}</tbody></table>'


def test_parse_gmp_last_ok_returns_last_value(ipowatch_mod):
    """GMP table present with numeric rows → (last_value, 'ok')."""
    html = _gmp_table_html([100, 150, 200])
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert status == 'ok'
    assert val == 200.0


def test_parse_gmp_last_single_row(ipowatch_mod):
    html = _gmp_table_html([75])
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert status == 'ok'
    assert val == 75.0


def test_parse_gmp_last_absent_no_table(ipowatch_mod):
    """HTML with no GMP table at all → (None, 'absent')."""
    html = '<p>No tables here.</p>'
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert val is None
    assert status == 'absent'


def test_parse_gmp_last_absent_non_gmp_table(ipowatch_mod):
    """HTML with a table but no GMP header → (None, 'absent')."""
    html = ('<table><thead><tr><th>Investor Category</th><th>Subscription</th></tr></thead>'
            '<tbody><tr><td>QIB</td><td>10x</td></tr></tbody></table>')
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert val is None
    assert status == 'absent'


def test_parse_gmp_last_parse_fail_gmp_header_no_values(ipowatch_mod):
    """GMP header present but cells have no numeric content → (None, 'parse_fail')."""
    # Table with GMP in header but cells that contain only dashes / text.
    html = ('<table><thead><tr><th>Date</th><th>GMP</th><th>Kostak</th></tr></thead>'
            '<tbody><tr><td>2024-01-01</td><td>N/A</td><td>-</td></tr>'
            '<tr><td>2024-01-02</td><td>-</td><td>-</td></tr></tbody></table>')
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert val is None
    assert status == 'parse_fail'


def test_parse_gmp_last_invalid_html_is_absent(ipowatch_mod):
    """Malformed HTML that pandas can't parse → (None, 'absent') not an exception."""
    html = '<<<not html>>>'
    val, status = ipowatch_mod.parse_gmp_last(html)
    assert val is None
    assert status in ('absent', 'parse_fail')


def test_parse_gmp_last_gmp_status_is_string(ipowatch_mod):
    """gmp_status must always be a string, never None."""
    for html in ['', '<p>x</p>', _gmp_table_html([50])]:
        _, status = ipowatch_mod.parse_gmp_last(html)
        assert isinstance(status, str)


# ─── _evaluate — 4-tuple propagation ─────────────────────────────────────────

def _make_post(slug, html, pid=1, dates_html=''):
    """Build a minimal ipowatch post dict for _evaluate testing."""
    full_html = dates_html + html
    return {'id': pid, 'slug': slug,
            'title': {'rendered': 'Test IPO'},
            'content': {'rendered': full_html}}


def test_evaluate_propagates_gmp_status_ok(ipowatch_mod):
    """When a GMP-slug post has a parseable GMP table, gmp_status='ok' propagates."""
    dates_part = ('<p>Open Date: May 01, 2024</p>'
                  '<p>Close Date: May 03, 2024</p>'
                  '<p>Listing Date: May 10, 2024</p>')
    gmp_html = _gmp_table_html([120, 150])
    post = _make_post('test-ipo-gmp', gmp_html, pid=10, dates_html=dates_part)
    our_dates = {'2024-05-10'}
    matched_date, sub, gmp, gmp_status = ipowatch_mod._evaluate([post], our_dates)
    assert gmp_status == 'ok'
    assert gmp == 150.0


def test_evaluate_gmp_status_absent_when_no_gmp_slug(ipowatch_mod):
    """A subscription-only post has no GMP slug → gmp_status is None (not examined)."""
    dates_part = '<p>Open Date: May 01, 2024</p>'
    # Subscription table (has TOTAL row but NOT a GMP slug)
    sub_html = ('<table><thead><tr><th>Category</th><th>Subscription</th></tr></thead>'
                '<tbody><tr><td>Total</td><td>5x</td></tr></tbody></table>')
    post = _make_post('test-ipo-subscription', sub_html, pid=20, dates_html=dates_part)
    our_dates = {'2024-05-01'}
    _, sub, gmp, gmp_status = ipowatch_mod._evaluate([post], our_dates)
    assert gmp_status is None   # no GMP-slug post examined


def test_evaluate_no_match_when_dates_dont_agree(ipowatch_mod):
    """Post with wrong dates → matched_date=None."""
    post = _make_post('test-ipo-gmp', _gmp_table_html([100]), pid=30,
                      dates_html='<p>Listing Date: January 01, 2020</p>')
    our_dates = {'2024-05-10'}
    matched_date, sub, gmp, gmp_status = ipowatch_mod._evaluate([post], our_dates)
    assert matched_date is None


# ─── match_and_extract — gmp_status in result ────────────────────────────────

def test_match_and_extract_requires_dates():
    """No dates → None immediately (cannot corroborate)."""
    # Import directly to avoid fixture machinery
    import importlib.util, os
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec = importlib.util.spec_from_file_location('_iw', os.path.join(ROOT, 'scrapers/ipowatch.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert m.match_and_extract('Test IPO', None, None, None) is None
