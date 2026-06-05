"""Showdown P2 — tests for the bhavcopy parsers (they feed ALL daily prices).

Both exchange CSV dialects are pinned: UDiFF (NSE-new + BSE, TckrSymb/OpnPric/ISIN)
and NSE-old (SYMBOL/OPEN/SERIES, no ISIN). Inline fixture payloads, exact asserts.
A silent parse regression here corrupts data/prices and every return downstream.
"""
from datetime import date

import pytest


@pytest.fixture(scope="session")
def bhavcopy_mod():
    from tests.scrapers.conftest import _load
    return _load("scrapers/bhavcopy.py", "scr_bhavcopy")


@pytest.fixture(scope="session")
def ohlc_mod():
    from tests.scrapers.conftest import _load
    return _load("scrapers/bhavcopy_ohlc.py", "scr_bhavcopy_ohlc")


UDIFF = (
    "TckrSymb,ISIN,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
    "ACME,INE001A01036,100.5,110.0,99.0,105.25,12345\n"
    "NOISIN,,55.0,56.0,54.0,55.5,100\n"
    "BLANKOPEN,INE002B02027,,60.0,58.0,59.0,200\n"
)

NSE_OLD = (
    "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TOTTRDQTY\n"
    "ACME,EQ,100.5,110.0,99.0,105.25,12345\n"
    "ACME,BL,999.0,999.0,999.0,999.0,1\n"        # non-equity series -> skipped
    "OTHER,EQ,10.0,11.0,9.0,10.5,500\n"           # not in our universe -> skipped
)


# ------------------------------------------------------------ bhavcopy.parse_bhavcopy
def test_parse_bhavcopy_udiff_keys_isin_and_symbol(bhavcopy_mod):
    out = bhavcopy_mod.parse_bhavcopy(UDIFF, "NSE", date(2024, 1, 1))
    assert out["INE001A01036"] == "100.5"
    assert out["SYM:ACME"] == "100.5"
    assert "SYM:NOISIN" in out and out["SYM:NOISIN"] == "55.0"   # no ISIN -> symbol key only
    assert "INE002B02027" not in out                              # blank open -> dropped


def test_parse_bhavcopy_old_nse_symbol_only(bhavcopy_mod):
    out = bhavcopy_mod.parse_bhavcopy(NSE_OLD, "NSE", date(2010, 1, 1))
    assert out["SYM:ACME"] == "100.5"
    assert all(k.startswith("SYM:") for k in out)                 # old format has no ISIN keys


def test_parse_bhavcopy_empty_and_garbage(bhavcopy_mod):
    assert bhavcopy_mod.parse_bhavcopy("", "NSE", date(2024, 1, 1)) == {}
    assert bhavcopy_mod.parse_bhavcopy("a,b\n1,2\n", "NSE", date(2024, 1, 1)) == {}


# ------------------------------------------------------------ bhavcopy_ohlc.parse_day
def test_parse_day_udiff_full_ohlcv(ohlc_mod):
    out = ohlc_mod.parse_day(UDIFF, {"INE001A01036"}, {})
    assert out == {"INE001A01036": ("100.5", "110.0", "99.0", "105.25", "12345")}


def test_parse_day_udiff_symbol_fallback_to_isin(ohlc_mod):
    # row with blank ISIN resolves through sym2isin
    text = ("TckrSymb,ISIN,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
            "MAPPED,,42.0,43.0,41.0,42.5,999\n")
    out = ohlc_mod.parse_day(text, {"INE0MAPPED99"}, {"MAPPED": "INE0MAPPED99"})
    assert out["INE0MAPPED99"][0] == "42.0"


def test_parse_day_old_nse_equity_series_only(ohlc_mod):
    out = ohlc_mod.parse_day(NSE_OLD, {"INE001A01036"}, {"ACME": "INE001A01036"})
    assert out["INE001A01036"][0] == "100.5"          # EQ row, not the BL row
    assert len(out) == 1                               # OTHER not in universe


def test_parse_day_universe_filter_and_empty(ohlc_mod):
    assert ohlc_mod.parse_day(UDIFF, set(), {}) == {}  # nothing in universe
    assert ohlc_mod.parse_day("", {"X"}, {}) == {}
    assert ohlc_mod._num("  7.5 ") == "7.5" and ohlc_mod._num(None) == ""
