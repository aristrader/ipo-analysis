"""GOLDEN headline numbers (showdown gap-close): the project's key analytical
outputs, pinned from the frozen substrate THROUGH the spine machinery.

Purpose: the data file is hash-checked and the functions are unit/mutation-tested,
but a gating/segmentation change on an unmutated path could still shift the
REPORTED numbers silently. These goldens close that hole.

If one fails after an INTENTIONAL change (e.g. remediating the 75 scale-inversion
rows, or a deliberate substrate rebuild): re-derive and update the constants
consciously — that is the test doing its job, not an error to suppress.
Derived 2026-06-04 from the frozen 2026-05-31 substrate.
"""
import pandas as pd
import pytest

from layer3 import spine


@pytest.fixture(scope="module")
def df():
    return spine.load_substrate()


def test_equity_universe_size(df):
    assert len(df) == 2245                      # equity-only default view of the 2296


def test_segment_sizes(df):
    assert len(spine.segment(df, segment="MB", cohort="boom")) == 370
    assert len(spine.segment(df, segment="SME", cohort="boom")) == 884
    assert len(spine.segment(df, segment="MB", cohort="longterm")) == 471


def test_mb_boom_1y_median_alpha(df):
    g = spine.maturity_gated(spine.segment(df, segment="MB", cohort="boom"), "1y")
    assert len(g) == 279
    assert float(spine.alpha_series(g, "1y").median()) == pytest.approx(-0.098405, abs=1e-4)


def test_mb_longterm_wipeout_lower_rate(df):
    wb = spine.wipeout_band(spine.segment(df, segment="MB", cohort="longterm"))
    assert wb["n"] == 471
    assert wb["wipeout_lower_rate"] == pytest.approx(0.227176, abs=1e-4)


def test_mb_boom_median_listing_pop(df):
    mb = spine.segment(df, segment="MB", cohort="boom")
    mb = mb[mb["listing_metrics_status"] != "unreliable_coverage"]
    pop = pd.to_numeric(mb["adj_listing_gain_open"], errors="coerce")
    assert float(pop.median()) == pytest.approx(0.103441, abs=1e-4)


def test_mb_longterm_ever_2x_within_3y(df):
    g = spine.maturity_gated(spine.segment(df, segment="MB", cohort="longterm"), "3y")
    mfe = pd.to_numeric(g.get("mfe_lst_3y"), errors="coerce").dropna()
    assert len(mfe) == 457
    assert float((mfe >= 1.0).mean()) == pytest.approx(0.347921, abs=1e-4)
