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
    html = ("<table><tr><td>QIB</td><td>2.50x</td></tr><tr><td>NII</td><td>5.10x</td></tr>"
            "<tr><td>Retail</td><td>1.20x</td></tr><tr><td>Total</td><td>2.10x</td></tr></table>")
    s = lb.parse_subscription_html(html)
    assert s == {"qib": 2.5, "nii": 5.1, "retail": 1.2, "total": 2.1}


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
