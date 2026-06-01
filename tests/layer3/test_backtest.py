import pandas as pd
import pytest
from layer3 import spine
from layer3.backtest import engine


@pytest.fixture(scope="module")
def df():
    return spine.load_substrate()


def test_run_returns_all_strategies(df):
    t = engine.run(df, horizon="1y", segment="MB")
    assert set(t["strategy"]) == set(engine.STRATEGIES)
    assert (t["N"] >= 0).all()


def test_secondary_uses_alpha_allottee_uses_return(df):
    t = engine.run(df, horizon="1y", segment="MB")
    sec = t[t["kind"] == "secondary"]
    al = t[t["kind"] == "allottee"]
    assert (sec["measure"] == "alpha").all()
    assert (al["measure"] == "ret").all()


def test_filtered_strategy_is_subset(df):
    # the filtered secondary strategy should never have more names than the unfiltered one
    t = engine.run(df, horizon="1y", segment="MB")
    n_all = int(t.loc[t.strategy == "secondary_hold", "N"].iloc[0])
    n_filt = int(t.loc[t.strategy == "secondary_filtered", "N"].iloc[0])
    assert n_filt <= n_all


def test_point_in_time_no_lookahead(df):
    # maturity-gating: a 3y strategy must use fewer/equal names than 1y (older IPOs only)
    t1 = engine.run(df, horizon="1y", segment="SME")
    t3 = engine.run(df, horizon="3y", segment="SME")
    n1 = int(t1.loc[t1.strategy == "secondary_hold", "N"].iloc[0])
    n3 = int(t3.loc[t3.strategy == "secondary_hold", "N"].iloc[0])
    assert n3 <= n1


def test_costs_applied(df):
    # secondary alpha should be net of the cost drag (strictly less than gross)
    sub = spine.segment(df, segment="MB")
    res, kind, _ = engine.strat_secondary_hold(sub, "1y")
    gross = pd.to_numeric(sub.loc[res.index, "alpha_1y"], errors="coerce")
    net = pd.to_numeric(res["alpha"], errors="coerce")
    assert (net.dropna() < gross.dropna() + 1e-9).all()
    assert abs((gross - net).dropna().mean() - engine.COST_SECONDARY) < 1e-6
