"""live_board parser tests (fixtures, no network) + the staging-only property."""
from datetime import date

from scrapers import live_board as lb


def _api_row(open_d="05-Jun-2026", close_d="09-Jun-2026", cat="SME"):
    return {
        "Company": '<a href="https://www.chittorgarh.com/ipo/x-ipo/99/">X Ltd.</a>',
        "Issue Category": cat, "Opening Date": open_d, "Closing Date": close_d,
        "Issue Price (Rs.)": "98.00 to 103.00",
        "Total Issue Amount (Incl.Firm reservations) (Rs.cr.)": "54.27",
        "~isin": "INE000TEST", "~nse_symbol": "XL", "Lead Manager": "Foo Capital",
        "~URLRewrite_Folder_Name": "x-ipo",
    }


def test_parse_open_issue():
    e = lb.parse_list_row(_api_row(), today=date(2026, 6, 7))
    assert e["status"] == "open" and e["type"] == "SME"
    assert e["price_band_low"] == 98.0 and e["price_band_high"] == 103.0
    assert e["isin"] == "INE000TEST" and e["issue_size_cr"] == 54.27


def test_parse_upcoming_and_past():
    up = lb.parse_list_row(_api_row("12-Jun-2026", "16-Jun-2026"), today=date(2026, 6, 7))
    assert up["status"] == "upcoming"
    past = lb.parse_list_row(_api_row("01-May-2026", "05-May-2026"), today=date(2026, 6, 7))
    assert past is None


def test_day_n():
    e = lb.parse_list_row(_api_row(), today=date(2026, 6, 7))
    assert lb.day_n(e, date(2026, 6, 7)) == 3          # opened Jun 5 -> day 3


def test_parse_subscription_html():
    # Mirrors the REAL chittorgarh page: a DECOY table first (short labels QIB/Total, offered/percent
    # columns, NO 'x') that the OLD regex wrongly matched, THEN the real subscription-TIMES table with
    # the long labels + 'Nx'. The parser must read the times-table, not the decoy. (Regression for the
    # live-feed bug where QIB/NII came back None and retail/total were bogus wrong-table values.)
    decoy = ("<table><tr><td>QIB</td><td>21,54,000</td><td>24.99</td><td>45.56%</td></tr>"
             "<tr><td>Retail</td><td>1,20,000</td><td>1.13</td><td>11%</td></tr>"
             "<tr><td>Total</td><td>47,28,000</td><td>54.84</td><td>100%</td></tr></table>")
    real = ("<table><tr><td>Qualified Institutional</td><td>17.58x</td></tr>"
            "<tr><td>Non Institutional</td><td>30.91x</td></tr>"
            "<tr><td>Retail Individual</td><td>12.59x</td></tr>"
            "<tr class='fw-bold'><td>Total Subscription</td><td>16.99x</td></tr></table>")
    s = lb.parse_subscription_html(decoy + real)
    assert s == {"qib": 17.58, "nii": 30.91, "retail": 12.59, "total": 16.99}

def test_parse_subscription_short_qib_label_variant():
    # chittorgarh varies the QIB label: some pages use the short 'QIB' (not 'Qualified Institutional').
    # The parser must catch it — and still ignore the decoy table (short labels, NO trailing 'x').
    decoy = "<table><tr><td>QIB</td><td>21,54,000</td><td>24.99</td></tr></table>"
    real = ("<table><tr><td>QIB</td><td>9.90x</td></tr>"
            "<tr><td>Non-Institutional</td><td>4.00x</td></tr>"
            "<tr><td>Total Subscription</td><td>6.50x</td></tr></table>")
    s = lb.parse_subscription_html(decoy + real)
    assert s == {"qib": 9.9, "nii": 4.0, "retail": None, "total": 6.5}

def test_parse_subscription_sme_no_qib_row():
    # SME pages may omit QIB entirely → qib stays None (correct, not a miss).
    html = ("<table><tr><td>Non Institutional</td><td>74.08x</td></tr>"
            "<tr><td>Retail Individual</td><td>100.18x</td></tr>"
            "<tr><td>Total Subscription</td><td>87.17x</td></tr></table>")
    s = lb.parse_subscription_html(html)
    assert s == {"qib": None, "nii": 74.08, "retail": 100.18, "total": 87.17}


def test_subscription_unknowns_stay_none():
    s = lb.parse_subscription_html("<p>page without table</p>")
    assert all(v is None for v in s.values())


def test_gmp_attach_by_symbol_and_name():
    es = [lb.parse_list_row(_api_row(), today=date(2026, 6, 7))]
    ig = [{"name": "X Ltd", "nse": "XL", "gmp_rs": 20.0, "ipo_price": 103.0}]
    out = lb.attach_gmp(es, ig)
    assert out[0]["gmp_rs"] == 20.0
    assert abs(out[0]["gmp_pct"] - 19.42) < 0.01


def test_daywise_append_dedupes(tmp_path):
    e = lb.parse_list_row(_api_row(), today=date(2026, 6, 7))
    e["day_n"] = 3
    n1 = lb.append_daywise([e], date(2026, 6, 7), str(tmp_path))
    n2 = lb.append_daywise([e], date(2026, 6, 7), str(tmp_path))
    assert (n1, n2) == (1, 0)                          # same fetch-day never duplicated


def test_outputs_never_target_data_master():
    assert "data/master" not in lb.LIVE_DIR and lb.LIVE_DIR.endswith("data/live")


# --- honesty status fields: parse_list_row must initialise them to None ---

def test_parse_list_row_status_fields_initialised_to_none():
    """New honesty status fields must be present and None in a freshly parsed entry
    (before any fetch; distinguishes 'not yet fetched' from a fetch error)."""
    e = lb.parse_list_row(_api_row(), today=date(2026, 6, 7))
    assert e is not None
    assert "sub_fetch_status" in e, "sub_fetch_status missing from parse_list_row output"
    assert "gmp_fetch_status" in e, "gmp_fetch_status missing from parse_list_row output"
    assert "gmp_source" in e, "gmp_source missing from parse_list_row output"
    assert e["sub_fetch_status"] is None
    assert e["gmp_fetch_status"] is None
    assert e["gmp_source"] is None


def test_attach_gmp_sets_gmp_source():
    """attach_gmp must set gmp_source='investorgain' on matched entries."""
    es = [lb.parse_list_row(_api_row(), today=date(2026, 6, 7))]
    ig = [{"name": "X Ltd", "nse": "XL", "gmp_rs": 15.0, "ipo_price": 103.0}]
    out = lb.attach_gmp(es, ig)
    assert out[0]["gmp_source"] == "investorgain"


def test_attach_gmp_no_match_leaves_gmp_source_none():
    """attach_gmp must not set gmp_source when no GMP row matches."""
    es = [lb.parse_list_row(_api_row(), today=date(2026, 6, 7))]
    ig = [{"name": "Completely Different Company", "nse": "CDC", "gmp_rs": 5.0, "ipo_price": 100.0}]
    out = lb.attach_gmp(es, ig)
    assert out[0]["gmp_source"] is None
