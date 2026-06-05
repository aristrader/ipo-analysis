"""Hermetic synthetic-fixture tests for step 07's compute() — the core function
that turns a price series into every outcome column in returns_summary.csv.

A tiny hand-built IPO (4 price rows) with hand-computed expectations, plus
adversarial traps: forced-wipeout terminal, maturity gating, split re-anchoring.
No files, no network — compute() is called directly with in-memory inputs.
All expectations assume TODAY = config.AS_OF_DATE = 2026-05-31 (frozen).
"""
from datetime import date

import pytest

ISSUE = 100.0
LISTING = date(2024, 1, 1)


def _row(d, o, h, lo, c, v=20000.0):
    return {"date": d, "o": o, "h": h, "l": lo, "c": c, "v": v, "raw_c": c}


def _prices():
    return [
        _row(LISTING,           120.0, 130.0, 115.0, 110.0),
        _row(date(2024, 6, 1),  145.0, 160.0, 140.0, 150.0),
        _row(date(2024, 12, 31),178.0, 185.0, 175.0, 180.0),
        _row(date(2025, 12, 31), 92.0,  95.0,  85.0,  90.0),
    ]


def _mrow(**over):
    m = {"issue_price": ISSUE, "listing_date": LISTING, "type": "MB",
         "company_name": "Synthetic Ltd", "nse_symbol": "SYN",
         # chittor quote == computed open -> remediation branch 'ok'
         "chittor_listing_open": 120.0, "chittor_listing_close": 110.0}
    m.update(over)
    return m


FLAT_NIFTY = ([date(2023, 1, 1), date(2027, 1, 1)], [100.0, 100.0])  # alpha == rfl


@pytest.fixture()
def out(returns_mod):
    return returns_mod.compute("TESTISIN0001", _mrow(), _prices(), [], {}, *FLAT_NIFTY)


# ------------------------------------------------------------ the normal IPO
def test_entry_refs_and_listing_gains(out):
    assert out["issue_price_adj"] == ISSUE          # no corp action
    assert out["listing_open"] == 120.0
    assert out["listing_close"] == 110.0
    assert out["listing_gain_open"] == pytest.approx(0.20)
    assert out["listing_gain_close"] == pytest.approx(0.10)
    assert out["listing_metrics_status"] == "ok"


def test_horizon_returns_hand_computed(out):
    # 1y target 2024-12-31 -> close 180
    assert out["return_from_issue_1y"] == pytest.approx(0.80)
    assert out["return_from_listing_1y"] == pytest.approx(180 / 110 - 1)
    # flat benchmark -> alpha == return_from_listing
    assert out["alpha_1y"] == pytest.approx(out["return_from_listing_1y"])
    # 2y target 2025-12-31 -> close 90
    assert out["return_from_issue_2y"] == pytest.approx(-0.10)
    # 3y target 2026-12-31 > AS_OF_DATE -> not mature -> None
    assert out["return_from_issue_3y"] is None
    # 1d target 2024-01-02 -> nearest on-or-before = listing day close 110
    assert out["return_from_issue_1d"] == pytest.approx(0.10)


def test_mfe_mae_year1_hand_computed(out):
    # window [2024-01-01, 2024-12-31]: high 185 on 12-31, low 115 on day 0
    assert out["mfe_1y"] == pytest.approx(0.85)          # 185/100-1 (allottee)
    assert out["mae_1y"] == pytest.approx(0.15)          # 115/100-1
    assert out["mfe_lst_1y"] == pytest.approx(185 / 110 - 1)   # secondary
    assert out["mae_lst_1y"] == pytest.approx(115 / 110 - 1)
    assert out["days_to_mfe_1y"] == 365
    assert out["days_to_mae_1y"] == 0
    assert out["days_to_breakeven_1y"] == 0              # listed above issue
    # invariant: trough <= endpoint <= peak
    assert out["mae_1y"] <= out["return_from_issue_1y"] <= out["mfe_1y"]


def test_lifetime_drawdown_and_outcome(out):
    assert out["all_time_high"] == 185.0
    assert out["all_time_low"] == 85.0
    assert out["max_gain_pct"] == pytest.approx(0.85)
    # peak close 180 (2024-12-31) -> 90 (2025-12-31): -50% over 365 days
    assert out["max_drawdown_pct"] == pytest.approx(-0.50)
    assert out["max_drawdown_duration_days"] == 365
    assert out["current_price"] == 90.0
    assert out["current_return_from_issue"] == pytest.approx(-0.10)
    assert out["outcome_class"] == "flat"                # -0.20 <= -0.10 < 0.20
    assert out["delisted"] is False
    assert out["liquidity_flag"] == "ok"                 # turnover ~2e6 > 1e6
    assert out["circuit_lock_frac"] == 0.0               # no o==h==l day


# ------------------------------------------------------------ trap: forced wipeout
def test_compulsory_delisting_forces_minus_100(returns_mod):
    deli = {"TESTISIN0001": {"status": "delisted", "delist_date": date(2024, 6, 2),
                             "reason": "Compulsory Delisting", "last_price": 50.0}}
    out = returns_mod.compute("TESTISIN0001", _mrow(), _prices(), [], deli, *FLAT_NIFTY)
    assert out["delisted"] is True
    # horizon past the delist date -> terminal 0.0 -> exactly -100% (decision A1)
    assert out["return_from_issue_1y"] == pytest.approx(-1.0)
    assert out["current_return_from_issue"] == pytest.approx(-1.0)
    assert out["outcome_class"] == "wipeout"
    # MFE/MAE clamp: trough can't sit above the -100% endpoint
    assert out["mae_1y"] == pytest.approx(-1.0)


# ------------------------------------------------------------ trap: maturity gating
def test_unreached_horizons_stay_null_not_guessed(returns_mod):
    recent = date(2026, 3, 1)                            # ~3 months before AS_OF_DATE
    prices = [_row(recent, 120.0, 130.0, 115.0, 110.0),
              _row(date(2026, 5, 30), 118.0, 122.0, 112.0, 115.0)]
    m = _mrow(listing_date=recent)
    out = returns_mod.compute("TESTISIN0002", m, prices, [], {}, *FLAT_NIFTY)
    assert out["return_from_issue_1m"] is not None       # 1m matured
    assert out["return_from_issue_1y"] is None           # 1y is in the future -> NULL
    assert out["mfe_1y"] is None                         # movement gated the same way


# ------------------------------------------------------------ trap: split re-anchoring
def test_post_listing_split_reanchors_issue_price(returns_mod):
    # 2:1 split after listing: price series arrives on the ADJUSTED scale (halved),
    # so issue_price must be divided by the same factor before any comparison.
    actions = [(date(2024, 6, 15), 2.0)]
    prices = [_row(LISTING,            60.0, 65.0, 57.5, 55.0),
              _row(date(2024, 12, 31), 89.0, 92.5, 87.5, 90.0),
              _row(date(2025, 12, 31), 46.0, 47.5, 42.5, 45.0)]
    m = _mrow(chittor_listing_open=120.0, chittor_listing_close=110.0)  # RAW quote
    out = returns_mod.compute("TESTISIN0003", m, prices, actions, {}, *FLAT_NIFTY)
    assert out["issue_price_adj"] == pytest.approx(50.0)         # 100 / 2
    assert out["listing_gain_open"] == pytest.approx(0.20)       # 60/50-1, scale-consistent
    assert out["return_from_issue_1y"] == pytest.approx(0.80)    # 90/50-1
    # recorded action explains the chittor-vs-computed gap -> NOT inferred_split
    assert out["listing_metrics_status"] == "ok"
