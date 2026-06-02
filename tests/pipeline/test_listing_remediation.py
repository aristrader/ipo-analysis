"""Unit tests for pipeline/listing_remediation.py.

This is the listing-coverage remediation that classifies every IPO's listing
metrics as ok / inferred_split / unreliable_coverage / recovered_bhavcopy, and
re-anchors issue metrics when it infers a missing split. It mutates the `out`
dict in place and returns the status string. Layer-3 listing-pop analysis trusts
this classification, so each branch is pinned here with a hand-built `out`.
"""
from datetime import date

HORIZONS = [("1y", 365), ("3y", 1095)]


def _base_out():
    return {
        "issue_price": 50.0,
        "issue_price_adj": 50.0,
        "listing_open": 100.0,
        "listing_close": 105.0,
        "listing_gain_open": None,
        "listing_gain_close": None,
        "return_from_issue_1y": 0.5,
        "return_from_issue_3y": 1.0,
        "return_from_listing_1y": 0.2,
        "return_from_listing_3y": 0.4,
        "alpha_1y": 0.1,
        "alpha_3y": 0.2,
        "current_return_from_issue": 0.8,
        "max_gain_pct": 1.2,
        "outcome_class": "winner",
    }


# ----------------------------------------------------------------- _outcome_class
def test_outcome_class_boundaries(remediation_mod):
    oc = remediation_mod._outcome_class
    assert oc(None) is None
    assert oc(-0.90) == "wipeout"      # <= -0.90
    assert oc(-0.89) == "loser"        # < -0.20
    assert oc(-0.20) == "flat"         # -0.20 is NOT < -0.20 -> flat
    assert oc(0.0) == "flat"
    assert oc(0.19) == "flat"
    assert oc(0.20) == "winner"        # 0.20 NOT < 0.20 -> winner
    assert oc(0.99) == "winner"
    assert oc(1.00) == "multibagger"   # 1.00 NOT < 1.00 -> multibagger


# ----------------------------------------------------------------- branch: ok
def test_ok_branch_leaves_metrics_untouched(remediation_mod):
    out = _base_out()
    out["listing_open"] = 100.0
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=105.0, chittor_listing_close=106.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "ok"
    # implied_factor 1.05 -> no inference, returns preserved exactly
    assert out["return_from_issue_1y"] == 0.5
    assert out["current_return_from_issue"] == 0.8
    assert out["issue_price_adj"] == 50.0


# ----------------------------------------------------------- branch: inferred_split
def test_inferred_split_reanchors_issue_metrics(remediation_mod):
    out = _base_out()
    out["listing_open"] = 20.0
    out["listing_close"] = 22.0
    out["return_from_issue_1y"] = 0.0      # -> (1+0)*scale - 1
    out["return_from_issue_3y"] = 0.0
    out["current_return_from_issue"] = 0.0
    out["max_gain_pct"] = 0.0
    # chittor 200 / computed 20 -> implied_factor 10 (in [1.5,12]), no recorded action
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=200.0, chittor_listing_close=220.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "inferred_split"
    # adj_issue = 50/10 = 5 ; scale = old_anchor(50)/adj_issue(5) = 10
    assert out["issue_price_adj"] == 5.0
    assert out["return_from_issue_1y"] == 9.0     # (1+0)*10 - 1
    assert out["current_return_from_issue"] == 9.0
    assert out["max_gain_pct"] == 9.0
    # listing gains recomputed off adj_issue
    assert out["listing_gain_open"] == 20.0 / 5.0 - 1   # 3.0
    assert out["listing_gain_close"] == 22.0 / 5.0 - 1   # 3.4
    assert out["outcome_class"] == "multibagger"          # 9.0 -> multibagger


def test_inferred_split_does_not_fire_when_corp_action_exists(remediation_mod):
    out = _base_out()
    out["listing_open"] = 20.0
    # same divergence, but a recorded corp action explains it -> NOT inferred
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=200.0, chittor_listing_close=220.0,
        has_action=True, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "ok"
    assert out["issue_price_adj"] == 50.0   # untouched


# ------------------------------------------------- branch: unreliable_coverage
def test_unreliable_when_factor_too_large_keeps_reliable_lifetime(remediation_mod):
    out = _base_out()
    out["listing_open"] = 20.0
    # chittor 2000 / 20 -> factor 100 (>12) -> unreliable; series starts within 30d -> keep issue metrics
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=2000.0, chittor_listing_close=2100.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 10), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "unreliable_coverage"
    assert out["listing_open"] is None
    assert out["listing_gain_open"] is None
    assert out["return_from_listing_1y"] is None
    assert out["alpha_3y"] is None
    # post_issue_reliable (10d) -> lifetime issue metrics retained
    assert out["current_return_from_issue"] == 0.8
    assert out["return_from_issue_1y"] == 0.5


def test_unreliable_with_late_series_nulls_issue_metrics_too(remediation_mod):
    out = _base_out()
    out["listing_open"] = 20.0
    # same, but series begins 100d after listing -> not post_issue_reliable
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=2000.0, chittor_listing_close=2100.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 4, 15), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "unreliable_coverage"
    assert out["current_return_from_issue"] is None
    assert out["return_from_issue_1y"] is None
    assert out["outcome_class"] is None


def test_unreliable_when_chittor_quote_missing(remediation_mod):
    out = _base_out()
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=None, chittor_listing_close=None,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "unreliable_coverage"
    assert out["listing_open"] is None


def test_unreliable_on_scale_inversion(remediation_mod):
    out = _base_out()
    out["listing_open"] = 200.0
    # chittor 100 / computed 200 -> factor 0.5 (<0.6), no action -> scale_inverted
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=100.0, chittor_listing_close=105.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "unreliable_coverage"
    assert out["listing_open"] is None


def test_coverage_gap_nulls_listing_for_late_bhavcopy_series(remediation_mod):
    out = _base_out()
    out["listing_open"] = 100.0
    # plausible factor, but bhavcopy series starts >30d after listing -> coverage gap
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=105.0, chittor_listing_close=106.0,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 3, 1), price_source="bhavcopy_daily",
        horizons=HORIZONS,
    )
    assert status == "unreliable_coverage"
    assert out["listing_open"] is None


# --------------------------------------------------- branch: recovered_bhavcopy
def test_recovered_bhavcopy_takes_precedence(remediation_mod):
    out = _base_out()
    out["issue_price"] = 100.0
    out["issue_price_adj"] = 100.0   # factor raw/adj = 1.0
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=None, chittor_listing_close=None,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS, recovered={"open": 150.0, "close": 160.0},
    )
    assert status == "recovered_bhavcopy"
    assert out["listing_open"] == 150.0
    assert out["listing_close"] == 160.0
    assert out["listing_gain_open"] == 150.0 / 100.0 - 1   # 0.5
    assert out["listing_gain_close"] == 160.0 / 100.0 - 1   # 0.6


def test_recovered_close_falls_back_to_open(remediation_mod):
    out = _base_out()
    out["issue_price"] = 100.0
    out["issue_price_adj"] = 100.0
    status = remediation_mod.remediate_listing(
        out, chittor_listing_open=None, chittor_listing_close=None,
        has_action=False, listing_date=date(2021, 1, 1),
        data_first=date(2021, 1, 2), price_source="bhavcopy_daily",
        horizons=HORIZONS, recovered={"open": 150.0},
    )
    assert status == "recovered_bhavcopy"
    assert out["listing_close"] == 150.0   # close fell back to open
