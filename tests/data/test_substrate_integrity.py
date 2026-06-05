"""Data-integrity invariants on the FROZEN analysis substrate (read-only).

This is the layer nothing previously watched: the data itself. Every invariant
here was first verified to hold on the real 2026-05-31 substrate (showdown P1),
then encoded. If one fails later, either the data was corrupted or a pipeline
change broke a guarantee — both are exactly what this suite exists to catch.
"""
from datetime import date

import pandas as pd
import pytest

from tests.data.conftest import num, offenders

HORIZONS_ME = ("1y", "3y", "5y")
AS_OF = date(2026, 5, 31)


# ---------------------------------------------------------------- identity
def test_row_count_and_isin_shape(ipo):
    assert len(ipo) == 2296
    i = ipo["isin"]
    assert i.is_unique, "duplicate isins in ipo_analysis"
    bad = ~((i.str.len() == 12) & i.str.startswith("IN"))
    assert not bad.any(), f"malformed isins: {offenders(ipo, bad)}"


def test_cohort_partition_and_type(ipo):
    assert ipo["cohort"].value_counts().to_dict() == {"boom": 1269, "longterm": 1027}
    assert set(ipo["type"].unique()) == {"MB", "SME"}


# ---------------------------------------------------------------- movement envelope
@pytest.mark.parametrize("h", HORIZONS_ME)
@pytest.mark.parametrize("entry,ep_tpl", [("", "return_from_issue_{}"), ("_lst", "return_from_listing_{}")])
def test_trough_le_endpoint_le_peak(ipo, h, entry, ep_tpl):
    mfe, mae = num(ipo, f"mfe{entry}_{h}"), num(ipo, f"mae{entry}_{h}")
    ep = num(ipo, ep_tpl.format(h))
    m = mfe.notna() & mae.notna() & ep.notna()
    bad = m & ((mae > ep + 1e-6) | (ep > mfe + 1e-6))
    assert not bad.any(), f"envelope broken ({entry or 'issue'} {h}): {offenders(ipo, bad)}"


# ---------------------------------------------------------------- classification
def test_outcome_class_matches_current_return(ipo):
    cr = num(ipo, "current_return_from_issue")

    def expected(v):
        if pd.isna(v):
            return None
        if v <= -0.90:
            return "wipeout"
        if v < -0.20:
            return "loser"
        if v < 0.20:
            return "flat"
        if v < 1.00:
            return "winner"
        return "multibagger"

    exp = cr.map(expected)
    act = ipo["outcome_class"].where(ipo["outcome_class"].notna(), None)
    bad = (exp != act) & ~(exp.isna() & act.isna())
    assert not bad.any(), f"outcome_class inconsistent: {offenders(ipo, bad)}"


def test_listing_metrics_status_enum_and_nulling(ipo):
    s = ipo["listing_metrics_status"]
    allowed = {"ok", "inferred_split", "recovered_bhavcopy", "unreliable_coverage"}
    bad = s.notna() & ~s.isin(allowed)
    assert not bad.any(), f"unknown status values: {sorted(s[bad].unique())}"
    # unreliable_coverage rows must have the ADJUSTED listing metrics nulled
    u = ipo[s == "unreliable_coverage"]
    for c in ("adj_listing_open", "adj_listing_gain_open", "adj_listing_gain_close",
              "return_from_listing_1y", "alpha_1y"):
        assert u[c].isna().all(), f"unreliable_coverage rows carry {c}: {u.loc[u[c].notna(), 'isin'].tolist()}"
    # status is null ONLY for the unpriced rows (they're absent from returns_summary; ~14)
    assert int(s.isna().sum()) <= 20, "status-null rows exploded — unpriced set changed unexpectedly"


def test_status_null_means_unpriced(ipo, returns_summary):
    unpriced = set(ipo["isin"]) - set(returns_summary["isin"])
    status_null = set(ipo.loc[ipo["listing_metrics_status"].isna(), "isin"])
    assert status_null == unpriced, (
        f"status-null != unpriced: only_null={list(status_null - unpriced)[:5]} "
        f"only_unpriced={list(unpriced - status_null)[:5]}")


# ---------------------------------------------------------------- survivorship honesty
def test_compulsory_or_liquidation_delisting_is_minus_100(ipo):
    m = (ipo["delisted"] == "True") & ipo["delist_reason"].str.lower().str.contains(
        "compulsor|liquidat", na=False)
    cr = num(ipo, "current_return_from_issue")
    bad = m & ((cr + 1.0).abs() >= 1e-9)
    assert not bad.any(), f"forced delistings not at -100%: {offenders(ipo, bad)}"
    assert int(m.sum()) >= 30, "compulsory/liquidation set shrank — delisting data changed?"


# ---------------------------------------------------------------- bounds
def test_return_and_price_bounds(ipo):
    for c in ("current_return_from_issue", "return_from_issue_1y", "return_from_issue_10y"):
        v = num(ipo, c)
        bad = v.notna() & (v < -1.0 - 1e-9)
        assert not bad.any(), f"{c} below -100%: {offenders(ipo, bad)}"
    ip = num(ipo, "issue_price")
    bad = ip.notna() & (ip <= 0)
    assert not bad.any(), f"non-positive issue_price: {offenders(ipo, bad)}"
    g = num(ipo, "gmp_pct")
    bad = g.notna() & ((g < -100) | (g > 500))
    assert not bad.any(), f"gmp_pct out of [-100,500]: {offenders(ipo, bad)}"


def test_listing_dates_in_project_window(ipo):
    ld = pd.to_datetime(ipo["listing_date"], errors="coerce")
    present = ld.notna()
    bad = present & ((ld < pd.Timestamp(2006, 1, 1)) | (ld > pd.Timestamp(AS_OF) + pd.Timedelta(days=365)))
    assert not bad.any(), f"listing_date outside window: {offenders(ipo, bad)}"
    assert int((~present).sum()) <= 20, "null listing_date count exploded"


# ---------------------------------------------------------------- joins
def test_master_files_join_cleanly(ipo, universe, returns_summary):
    assert universe["isin"].is_unique and returns_summary["isin"].is_unique
    assert set(universe["isin"]) == set(ipo["isin"]), "universe and ipo_analysis key sets differ"
    assert set(returns_summary["isin"]) <= set(ipo["isin"]), "returns_summary has isins missing from ipo_analysis"
    assert len(returns_summary) >= 2200, "priced-rows count collapsed"


# ---------------------------------------------------------------- alpha recomputation
def test_alpha_1y_recomputes_from_nifty_on_sample(ipo):
    """alpha_1y must equal return_from_listing_1y minus the Nifty return over the
    same window, re-derived from the reference index file (50-row deterministic sample)."""
    import bisect
    import csv
    import os
    from datetime import timedelta

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dates, closes = [], []
    with open(os.path.join(root, "data/reference/indices/nifty50.csv")) as f:
        for r in csv.DictReader(f):
            try:
                d = pd.Timestamp(r["date"]).date()
                c = float(r["close"])
            except (ValueError, KeyError):
                continue
            dates.append(d)
            closes.append(c)
    pairs = sorted(zip(dates, closes))
    dates = [p[0] for p in pairs]
    closes = [p[1] for p in pairs]

    def nifty_at(d):
        i = bisect.bisect_right(dates, d) - 1
        return closes[i] if i >= 0 else None

    cand = ipo[(ipo["listing_metrics_status"] == "ok")
               & (ipo["price_source"] == "bhavcopy_daily")
               & ipo["alpha_1y"].notna() & ipo["return_from_listing_1y"].notna()
               & ipo["listing_date"].notna()].sort_values("isin").head(50)
    assert len(cand) == 50
    bad = []
    for _, r in cand.iterrows():
        ld = pd.Timestamp(r["listing_date"]).date()
        base, end = nifty_at(ld), nifty_at(ld + timedelta(days=365))
        if not base or not end:
            continue
        expected = float(r["return_from_listing_1y"]) - (end / base - 1)
        if abs(expected - float(r["alpha_1y"])) > 2e-4:  # ±2bp (CSV rounding headroom)
            bad.append((r["isin"], round(expected, 5), r["alpha_1y"]))
    assert not bad, f"alpha_1y doesn't recompute: {bad[:5]}"
