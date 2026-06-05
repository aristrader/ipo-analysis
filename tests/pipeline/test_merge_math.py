"""Showdown P2 — hermetic tests for compute_weekly() in scrapers/screener_prices_merge.py,
the weekly-close mirror of step 07's compute(). It rebuilds returns + MFE/MAE + timing for
the screener-weekly fix-set rows of the substrate, so its math is pinned the same way 07's is:
hand-built weekly series, hand-computed expectations, adversarial traps.
"""
from datetime import date

import pytest

ISSUE = 100.0
LISTING = date(2024, 1, 1)


def _w(d, c):
    return {"date": d, "c": c, "v": 50000.0}


def _prices():
    # weekly closes: listing week 110, spring 150, year-end 180, year-2 90 (+1 week so the
    # 2y target 2025-12-31 sits INSIDE coverage — the data-gap gate otherwise nulls it, correctly)
    return [_w(LISTING, 110.0), _w(date(2024, 3, 4), 150.0),
            _w(date(2024, 12, 30), 180.0), _w(date(2025, 12, 29), 90.0),
            _w(date(2026, 1, 5), 92.0)]


def _mrow(**over):
    m = {"issue_price": ISSUE, "listing_date": LISTING, "type": "SME",
         "company_name": "WeeklyCo", "nse_symbol": "WKLY",
         # chittor quote ~= computed weekly close -> remediation status 'ok'
         # (without it the merge's remediate_listing call nulls the listing metrics)
         "chittor_listing_open": 110.0, "chittor_listing_close": 110.0}
    m.update(over)
    return m


FLAT_NIFTY = ([date(2023, 1, 1), date(2027, 1, 1)], [100.0, 100.0])


def _run(merge_mod, prices=None, deli=None, mrow=None):
    return merge_mod.compute_weekly("TESTWKLY0001", mrow or _mrow(), prices or _prices(),
                                    deli or {}, *FLAT_NIFTY, {}, {})


def test_weekly_entry_refs_and_endpoints(merge_mod):
    out = _run(merge_mod)
    assert out["price_source"] == "screener_weekly"
    assert out["issue_price_adj"] == ISSUE                  # no corp action
    assert out["listing_close"] == 110.0 and out["listing_open"] == 110.0  # weekly: open==close
    # 1y target 2024-12-31 -> nearest weekly close 180 (2024-12-30)
    assert out["return_from_issue_1y"] == pytest.approx(0.80)
    assert out["return_from_listing_1y"] == pytest.approx(180 / 110 - 1)
    assert out["alpha_1y"] == pytest.approx(out["return_from_listing_1y"])  # flat benchmark
    # 2y target 2025-12-31 -> close 90
    assert out["return_from_issue_2y"] == pytest.approx(-0.10)


def test_weekly_mfe_mae_and_timing(merge_mod):
    out = _run(merge_mod)
    # 1y window: closes 110/150/180 -> peak 180 (day 364), trough 110 (day 0)
    assert out["mfe_1y"] == pytest.approx(0.80)
    assert out["mae_1y"] == pytest.approx(0.10)             # weekly never printed below issue
    assert out["days_to_mfe_1y"] == 364
    assert out["days_to_mae_1y"] == 0
    assert out["days_to_breakeven_1y"] == 0                 # listed above issue
    assert out["mfe_lst_1y"] == pytest.approx(180 / 110 - 1)
    assert out["mae_lst_1y"] == pytest.approx(0.0)          # clamp keeps trough <= endpoint
    # envelope invariant
    assert out["mae_1y"] <= out["return_from_issue_1y"] <= out["mfe_1y"]


def test_weekly_immature_horizon_stays_null(merge_mod):
    out = _run(merge_mod)
    # 3y target 2026-12-31 > TODAY (2026-05-31) -> not mature -> NULL, never guessed
    assert out["return_from_issue_3y"] is None
    assert out["mfe_3y"] is None and out["days_to_mfe_3y"] is None


def test_weekly_forced_wipeout_clamps_to_minus_100(merge_mod):
    deli = {"TESTWKLY0001": {"status": "delisted", "delist_date": date(2024, 6, 2),
                             "reason": "Compulsory Delisting", "last_price": 40.0}}
    out = _run(merge_mod, deli=deli)
    assert out["delisted"] is True
    assert out["return_from_issue_1y"] == pytest.approx(-1.0)   # terminal 0 past delist date
    assert out["mae_1y"] == pytest.approx(-1.0)                 # clamp brackets the endpoint
    assert out["outcome_class"] == "wipeout"
