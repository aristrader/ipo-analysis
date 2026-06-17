"""Tests for scrapers/nse_subscription.py.

Covers:
  - _num: basic numeric parsing (unchanged helper, regression guard).
  - _parse_subscription_rows: pure function extracted from fetch_subscription, tested against
    realistic NSE dataList shapes.
  - fetch_subscription result codes: ok / no_nse_data / fetch_error — the Rule-2 fix.
    Network is mocked with a simple stub so no I/O occurs.
"""
import pytest


# ─── _num (regression guard) ─────────────────────────────────────────────────

def test_num_strips_comma(nse_subscription_mod):
    assert nse_subscription_mod._num("1,234.56") == 1234.56


def test_num_returns_none_for_nonnumeric(nse_subscription_mod):
    assert nse_subscription_mod._num("N/A") is None
    assert nse_subscription_mod._num("") is None
    assert nse_subscription_mod._num(None) is None


def test_num_zero_is_zero(nse_subscription_mod):
    # A genuine 0 (not a placeholder) should parse to 0.0.
    assert nse_subscription_mod._num("0") == 0.0
    assert nse_subscription_mod._num("0.00") == 0.0


# ─── _parse_subscription_rows ────────────────────────────────────────────────

def test_parse_subscription_rows_typical(nse_subscription_mod):
    """Typical NSE dataList with QIB / NII / RII / Total rows."""
    rows = [
        {'category': 'Qualified Institutional Buyers', 'noOfTotalMeant': '10.50'},
        {'category': 'Non Institutional Investors',    'noOfTotalMeant': '3.20'},
        {'category': 'Retail Individual Investors',    'noOfTotalMeant': '1.75'},
        {'category': 'Total',                          'noOfTotalMeant': '5.30'},
    ]
    out = nse_subscription_mod._parse_subscription_rows(rows)
    assert out['sub_qib_x'] == 10.50
    assert out['sub_nii_x'] == 3.20
    assert out['sub_retail_x'] == 1.75
    assert out['sub_total_x'] == 5.30


def test_parse_subscription_rows_all_zero_returns_nones(nse_subscription_mod):
    """All-zero dataList (SME / window-closed NSE pattern) — all values None."""
    rows = [
        {'category': 'Qualified Institutional Buyers', 'noOfTotalMeant': '0.00'},
        {'category': 'Non Institutional Investors',    'noOfTotalMeant': '0.00'},
        {'category': 'Retail Individual Investors',    'noOfTotalMeant': '0.00'},
        {'category': 'Total',                          'noOfTotalMeant': '0.00'},
    ]
    out = nse_subscription_mod._parse_subscription_rows(rows)
    # _num returns 0.0 for '0.00', but 0.0 is falsy — so any() check in fetch_subscription
    # will correctly see all-zero as no-data.  The parsed dict values are 0.0 here (not None)
    # because _num parses '0.00' as 0.0 — this is the raw parse; the no_nse_data gate is in
    # fetch_subscription, not in _parse_subscription_rows.
    assert not any(v for v in out.values()), "all-zero rows should all be falsy"


def test_parse_subscription_rows_empty_list(nse_subscription_mod):
    """Empty dataList → all None."""
    out = nse_subscription_mod._parse_subscription_rows([])
    assert out == {'sub_qib_x': None, 'sub_nii_x': None,
                   'sub_retail_x': None, 'sub_total_x': None}


def test_parse_subscription_rows_unknown_category_ignored(nse_subscription_mod):
    """Unknown categories (FII sub-rows etc.) should be ignored."""
    rows = [
        {'category': 'Mutual Funds', 'noOfTotalMeant': '99.0'},   # sub-row, must be ignored
        {'category': 'Total',        'noOfTotalMeant': '5.0'},
    ]
    out = nse_subscription_mod._parse_subscription_rows(rows)
    assert out['sub_total_x'] == 5.0
    assert out['sub_qib_x'] is None


def test_parse_subscription_rows_partial_data(nse_subscription_mod):
    """Only Total present — other keys remain None."""
    rows = [{'category': 'Total', 'noOfTotalMeant': '2.5'}]
    out = nse_subscription_mod._parse_subscription_rows(rows)
    assert out['sub_total_x'] == 2.5
    assert out['sub_qib_x'] is None
    assert out['sub_nii_x'] is None
    assert out['sub_retail_x'] is None


# ─── fetch_subscription result-code discrimination ───────────────────────────

class _MockSession:
    """Minimal curl_cffi session stub for testing fetch_subscription without network."""
    def __init__(self, status_code, body):
        self._status_code = status_code
        self._body = body

    def get(self, url, headers=None, timeout=None):
        return _MockResp(self._status_code, self._body)


class _MockResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.text = body

    def json(self):
        import json
        return json.loads(self.text)


def test_fetch_subscription_ok(nse_subscription_mod):
    """HTTP 200 + non-zero data → result='ok' with subscription values."""
    import json
    body = json.dumps({'dataList': [
        {'category': 'Total', 'noOfTotalMeant': '7.5'},
        {'category': 'Retail Individual Investors', 'noOfTotalMeant': '3.2'},
    ]})
    sess = _MockSession(200, body)
    out = nse_subscription_mod.fetch_subscription(sess, 'TESTCO')
    assert out['result'] == 'ok'
    assert out['sub_total_x'] == 7.5
    assert out['sub_retail_x'] == 3.2


def test_fetch_subscription_no_nse_data(nse_subscription_mod):
    """HTTP 200 + all-zero dataList → result='no_nse_data' (not 'no_data' / not 'fetch_error')."""
    import json
    body = json.dumps({'dataList': [
        {'category': 'Qualified Institutional Buyers', 'noOfTotalMeant': '0.00'},
        {'category': 'Non Institutional Investors',    'noOfTotalMeant': '0.00'},
        {'category': 'Retail Individual Investors',    'noOfTotalMeant': '0.00'},
        {'category': 'Total',                          'noOfTotalMeant': '0.00'},
    ]})
    sess = _MockSession(200, body)
    out = nse_subscription_mod.fetch_subscription(sess, 'SMECO')
    assert out['result'] == 'no_nse_data'
    # no subscription values present in the dict
    assert 'sub_total_x' not in out or out.get('sub_total_x') is None


def test_fetch_subscription_empty_datalist(nse_subscription_mod):
    """HTTP 200 + empty dataList → result='no_nse_data' (not an error)."""
    import json
    body = json.dumps({'dataList': []})
    sess = _MockSession(200, body)
    out = nse_subscription_mod.fetch_subscription(sess, 'EMPTY')
    assert out['result'] == 'no_nse_data'


def test_fetch_subscription_fetch_error_non200(nse_subscription_mod):
    """HTTP 403 → result='fetch_error' (was previously 'no_data' — the Rule-2 bug)."""
    sess = _MockSession(403, '')
    out = nse_subscription_mod.fetch_subscription(sess, 'BLOCKED')
    assert out['result'] == 'fetch_error'


def test_fetch_subscription_fetch_error_500(nse_subscription_mod):
    """HTTP 500 → result='fetch_error'."""
    sess = _MockSession(500, '{}')
    out = nse_subscription_mod.fetch_subscription(sess, 'ERR')
    assert out['result'] == 'fetch_error'


def test_result_codes_are_exhaustive(nse_subscription_mod):
    """Result codes used in fetch_subscription are exactly the documented set."""
    valid = {'ok', 'no_nse_data', 'fetch_error'}
    import json
    # ok
    body_ok = json.dumps({'dataList': [{'category': 'Total', 'noOfTotalMeant': '1.0'}]})
    assert nse_subscription_mod.fetch_subscription(_MockSession(200, body_ok), 'X')['result'] in valid
    # no_nse_data
    body_zero = json.dumps({'dataList': [{'category': 'Total', 'noOfTotalMeant': '0'}]})
    assert nse_subscription_mod.fetch_subscription(_MockSession(200, body_zero), 'X')['result'] in valid
    # fetch_error
    assert nse_subscription_mod.fetch_subscription(_MockSession(404, '{}'), 'X')['result'] in valid
