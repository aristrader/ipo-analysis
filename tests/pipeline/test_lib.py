"""Unit tests for pipeline/lib.py — the shared pure helpers that several
pipeline steps depend on. Pinning them here is the regression net that makes the
copy-paste -> single-source dedup safe.
"""


def test_fnum_coerces_and_strips_commas(lib_mod):
    f = lib_mod.fnum
    assert f("1,234.5") == 1234.5
    assert f(42) == 42.0
    assert f("42") == 42.0
    assert f("abc") is None
    assert f(None) is None
    assert f("") is None


def test_num_is_a_type_guard_not_a_parser(lib_mod):
    n = lib_mod.num
    assert n(5) == 5
    assert n(5.0) == 5.0
    assert n(-3) == -3
    # strings are REJECTED, not parsed (this is what distinguishes it from fnum)
    assert n("5") is None
    assert n(None) is None
    assert n("abc") is None


def test_last_pre_listing_fy_uses_april_fiscal_boundary(lib_mod):
    f = lib_mod.last_pre_listing_fy
    assert f("2022-05-15") == 2022   # May -> FY ending Mar-2023 not done -> last done is 2022
    assert f("2022-04-01") == 2022   # April boundary -> current year
    assert f("2022-03-31") == 2021   # March -> previous fiscal year
    assert f("2022-01-10") == 2021
    # guards
    assert f("") is None
    assert f(None) is None
    assert f("2022") is None         # too short (< 7 chars)
