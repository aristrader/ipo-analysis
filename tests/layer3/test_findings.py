import pandas as pd
import pytest
from layer3 import spine
from layer3.report import Finding
from layer3.findings import (t1_base_rates, t2_survival, t3_pop_fade, t5_ofs,
                             t6_sector, t7_benchmark, t8_drawdown, t9_profitable,
                             n4_issue_size, n2_subscription, n3_demand_skew, n5_anchor,
                             n7_fundamentals, n8_accrual, n6_valuation,
                             n9_zombie, n10_migration, n11_sc_divergence, n12_banker, nonequity)

ALL = [t7_benchmark, t1_base_rates, t2_survival, t6_sector,
       t3_pop_fade, t5_ofs, t9_profitable, t8_drawdown, n4_issue_size, n2_subscription,
       n3_demand_skew, n5_anchor, n7_fundamentals, n8_accrual, n6_valuation,
       n9_zombie, n10_migration, n11_sc_divergence, n12_banker, nonequity]


@pytest.fixture(scope="module")
def df():
    return spine.load_substrate()


@pytest.mark.parametrize("mod", ALL, ids=[m.__name__.split(".")[-1] for m in ALL])
def test_compute_contract(mod, df):
    f = mod.compute(df)
    assert isinstance(f, Finding)
    assert f.id and f.title and isinstance(f.narrative, str) and f.narrative
    assert f.tables, f"{mod.__name__} produced no tables"
    for cap, t in f.tables:
        assert isinstance(t, pd.DataFrame) and len(t) >= 1
        assert any(c == "N" or c == "n" or c.startswith("N_") for c in t.columns), \
            f"{mod.__name__} table '{cap}' has no count (N) column"
    for cap, uri in f.charts:
        assert uri.startswith("data:image/png;base64,")


def test_t3_uses_raw_not_alpha(df):
    # T3 must report return-from-listing columns, never an 'alpha' column (methodology fix #1)
    f = t3_pop_fade.compute(df)
    cols = [c for _, t in f.tables for c in t.columns]
    assert any("from_listing" in c for c in cols)
    assert not any("alpha" in c.lower() for c in cols)
