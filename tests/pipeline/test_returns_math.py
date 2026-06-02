"""Unit tests for the pure math/parse helpers in pipeline/07_returns_summary.py.

These functions drive every horizon return, split adjustment, and benchmark
lookup in returns_summary.csv. They have no I/O, so we test them directly with
hand-built inputs and assert exact outputs — the synthetic-fixture safety net
the data-building half of the project previously lacked.
"""
from datetime import date


# ----------------------------------------------------------------- pdate
def test_pdate_three_supported_formats(returns_mod):
    assert returns_mod.pdate("2021-03-15") == date(2021, 3, 15)
    assert returns_mod.pdate("15-03-2021") == date(2021, 3, 15)
    assert returns_mod.pdate("15/03/2021") == date(2021, 3, 15)


def test_pdate_empty_and_garbage_return_none(returns_mod):
    assert returns_mod.pdate("") is None
    assert returns_mod.pdate(None) is None
    assert returns_mod.pdate("   ") is None
    assert returns_mod.pdate("not-a-date") is None
    assert returns_mod.pdate("2021/03/15") is None  # unsupported order


# ----------------------------------------------------------------- pfloat
def test_pfloat_parses_and_guards(returns_mod):
    assert returns_mod.pfloat("123.5") == 123.5
    assert returns_mod.pfloat("  42 ") == 42.0
    assert returns_mod.pfloat("") is None
    assert returns_mod.pfloat(None) is None
    assert returns_mod.pfloat("abc") is None


# -------------------------------------------------- adj_factor_after (split math)
def test_adj_factor_after_multiplies_only_future_actions(returns_mod):
    actions = [(date(2021, 1, 1), 2.0), (date(2022, 1, 1), 5.0)]
    # before both ex-dates -> both splits still ahead -> 2*5
    assert returns_mod.adj_factor_after(actions, date(2020, 6, 1)) == 10.0
    # between the two -> only the 5:1 is still ahead
    assert returns_mod.adj_factor_after(actions, date(2021, 6, 1)) == 5.0
    # after both -> nothing ahead -> 1.0
    assert returns_mod.adj_factor_after(actions, date(2023, 1, 1)) == 1.0


def test_adj_factor_after_is_strict_greater_than(returns_mod):
    # an action ON the same day as dt is NOT in the future -> not applied
    actions = [(date(2021, 1, 1), 2.0)]
    assert returns_mod.adj_factor_after(actions, date(2021, 1, 1)) == 1.0


def test_adj_factor_after_empty_or_none_is_identity(returns_mod):
    assert returns_mod.adj_factor_after([], date(2021, 1, 1)) == 1.0
    assert returns_mod.adj_factor_after(None, date(2021, 1, 1)) == 1.0


# -------------------------------------------------- nearest_on_or_before
def test_nearest_on_or_before_picks_last_trading_day(returns_mod):
    dates = [date(2021, 1, 1), date(2021, 1, 5), date(2021, 1, 10)]
    closes = [100.0, 110.0, 120.0]
    assert returns_mod.nearest_on_or_before(dates, closes, date(2021, 1, 5)) == 110.0   # exact
    assert returns_mod.nearest_on_or_before(dates, closes, date(2021, 1, 7)) == 110.0   # between -> earlier
    assert returns_mod.nearest_on_or_before(dates, closes, date(2021, 2, 1)) == 120.0   # past end -> last


def test_nearest_on_or_before_returns_none_before_series_start(returns_mod):
    dates = [date(2021, 1, 5)]
    closes = [110.0]
    assert returns_mod.nearest_on_or_before(dates, closes, date(2021, 1, 1)) is None


# -------------------------------------------------- actions_for (union/dedup)
def test_actions_for_unions_isin_and_symbol_and_dedups(returns_mod):
    shared = (date(2021, 1, 1), 2.0)
    by_isin = {"INE001": [shared, (date(2022, 1, 1), 5.0)]}
    by_symbol = {"ACME": [shared, (date(2023, 1, 1), 10.0)]}
    out = returns_mod.actions_for("INE001", "acme", by_isin, by_symbol)
    # shared action counted once; the two unique ones added -> 3 total
    assert len(out) == 3
    assert shared in out
    assert (date(2022, 1, 1), 5.0) in out
    assert (date(2023, 1, 1), 10.0) in out


def test_actions_for_symbol_lookup_is_case_insensitive(returns_mod):
    by_symbol = {"ACME": [(date(2021, 1, 1), 2.0)]}
    out = returns_mod.actions_for("MISSING", "AcMe", {}, by_symbol)
    assert out == [(date(2021, 1, 1), 2.0)]


def test_actions_for_no_matches_returns_empty(returns_mod):
    assert returns_mod.actions_for("X", "Y", {}, {}) == []
