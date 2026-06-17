"""Regression tests for bugs caught by the adversarial review of the scraper-fix wave (T0.1)."""
from scrapers import ipowatch, live_board


def test_parse_gmp_last_scans_past_empty_gmp_table():
    # BLOCKER regression: a placeholder GMP table BEFORE the real one must not abort the scan.
    html = (
        "<table><tr><th>Date</th><th>GMP</th></tr><tr><td>x</td><td>N/A</td></tr></table>"
        "<table><tr><th>Date</th><th>GMP</th></tr><tr><td>2024-01-01</td><td>150</td></tr></table>"
    )
    val, status = ipowatch.parse_gmp_last(html)
    assert status == "ok" and val == 150.0


def test_parse_gmp_last_single_empty_gmp_table_is_parse_fail():
    html = "<table><tr><th>Date</th><th>GMP</th></tr><tr><td>x</td><td>N/A</td></tr></table>"
    val, status = ipowatch.parse_gmp_last(html)
    assert val is None and status == "parse_fail"


def test_parse_gmp_last_no_gmp_table_is_absent():
    html = "<table><tr><th>Date</th><th>Price</th></tr><tr><td>x</td><td>100</td></tr></table>"
    val, status = ipowatch.parse_gmp_last(html)
    assert val is None and status == "absent"


def test_attach_gmp_no_source_attribution_when_gmp_missing():
    # BUG regression: a matched IG row with gmp_rs=None must NOT claim gmp_source='investorgain'.
    entries = [{"name": "Acme Ltd", "nse_symbol": "ACME", "price_band_high": 100,
                "gmp_rs": None, "gmp_pct": None, "gmp_source": None}]
    ig_rows = [{"nse": "ACME", "name": "Acme Ltd", "gmp_rs": None, "ipo_price": 100}]
    out = live_board.attach_gmp(entries, ig_rows)
    assert out[0]["gmp_source"] is None


def test_attach_gmp_sets_source_when_gmp_present():
    entries = [{"name": "Beta Ltd", "nse_symbol": "BETA", "price_band_high": 100,
                "gmp_rs": None, "gmp_pct": None, "gmp_source": None}]
    ig_rows = [{"nse": "BETA", "name": "Beta Ltd", "gmp_rs": 20.0, "ipo_price": 100}]
    out = live_board.attach_gmp(entries, ig_rows)
    assert out[0]["gmp_source"] == "investorgain" and out[0]["gmp_rs"] == 20.0
