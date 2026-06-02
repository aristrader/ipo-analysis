"""Unit tests for the scalar text normalizers across the data scrapers.

These tiny functions are where silent data corruption hides — a sentinel like
"-"/"N/A" parsed as a number, a "2.5x" subscription not stripping the x, a
thousands comma surviving into a float, a date format slipping through. Each
feeds a real feature (financials -> wipeout flags, subscription/GMP, the spine),
so behavior is pinned exactly against what the live parsers do today.

Note the deliberate return-type split, preserved from the sources:
  * screener._num / ipowatch._num  -> float (or None)
  * sharescart.parse_num / chittorgarh._num -> the matched STRING (or None)
"""


# ============================ screener.py ============================
def test_screener_num_handles_commas_pct_and_sentinels(screener_mod):
    n = screener_mod._num
    assert n("1,234") == 1234.0
    assert n("12.5%") == 12.5
    assert n("-5") == -5.0
    # sentinels -> None (both hyphen and en-dash, plus nan/None/empty)
    assert n("-") is None
    assert n("–") is None
    assert n("nan") is None
    assert n("None") is None
    assert n("") is None
    assert n("abc") is None


def test_screener_norm_tokens_collapses_single_letters(screener_mod):
    # "G-M Breweries" -> punctuation to space -> single-letter run g+m collapses to "gm"
    assert screener_mod._norm_tokens("G-M Breweries") == ["gm", "breweries"]


def test_screener_name_match_basic(screener_mod):
    assert screener_mod.name_match("Tata Steel", "Tata Steel") is True
    assert screener_mod.name_match("Tata Steel", "Reliance Power") is False
    assert screener_mod.name_match("", "Tata Steel") is False


def test_screener_page_marketcap_parses_rupee_number(screener_mod):
    html = ('Market Cap </span> <span class="..."> ₹ '
            '<span class="number">1,23,456</span>')
    assert screener_mod.page_marketcap(html) == 123456.0
    assert screener_mod.page_marketcap("no market cap here") is None


# ============================ ipowatch.py ============================
def test_ipowatch_num_strips_x_suffix_and_commas(ipowatch_mod):
    n = ipowatch_mod._num
    assert n("2.5x") == 2.5          # subscription multiple
    assert n("2.5X") == 2.5
    assert n("1,234") == 1234.0
    assert n("abc") is None


def test_ipowatch_to_iso_month_name_dates(ipowatch_mod):
    f = ipowatch_mod._to_iso
    assert f("May 20, 2022") == "2022-05-20"
    assert f("June 02, 2022") == "2022-06-02"
    assert f("garbage") is None
    assert f("") is None


# ============================ sharescart.py ============================
def test_sharescart_parse_num_returns_matched_string(sharescart_mod):
    f = sharescart_mod.parse_num
    assert f("Rs 1,234.5") == "1234.5"   # strips commas/spaces, then matches number
    assert f("-50") == "-50"
    assert f("abc") is None
    assert f("") is None


def test_sharescart_clean_normalizes_whitespace(sharescart_mod):
    c = sharescart_mod.clean
    assert c("  a  b ") == "a b"
    assert c("\xa0") is None             # nbsp-only collapses to empty -> None
    assert c(None) is None


def test_sharescart_parse_year_extracts_four_digit_year(sharescart_mod):
    f = sharescart_mod._parse_year
    assert f("20 May 2022") == 2022
    assert f("12345") is None            # 5 digits -> no \b\d{4}\b match
    assert f("") is None


# ============================ chittorgarh.py ============================
def test_chittorgarh_iso_to_date_truncates_timestamp(chittorgarh_mod):
    f = chittorgarh_mod._iso_to_date
    assert f("2022-12-30T00:00:00.000Z") == "2022-12-30"
    assert f("not-a-date") == ""
    assert f("") == ""


def test_chittorgarh_num_returns_matched_string(chittorgarh_mod):
    f = chittorgarh_mod._num
    assert f("Rs 66") == "66"
    assert f("1,234.5") == "1234.5"
    assert f(None) is None


def test_chittorgarh_cr_from_text(chittorgarh_mod):
    f = chittorgarh_mod._cr_from_text
    assert f("₹ 1,234 Cr") == "1234"
    assert f("₹ 66 Cr") == "66"
    assert f("no amount") is None
