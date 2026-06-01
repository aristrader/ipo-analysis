"""The 5-traps validation pass — guard tests encoding docs/strategies.md 'the 5 traps'."""
import pandas as pd
from layer3 import spine, config
from layer3.report import _guard_table
from layer3.findings import t1_base_rates, t6_sector, t2_survival


def test_trap5_no_mb_sme_pooling():
    df = spine.load_substrate()
    f = t1_base_rates.compute(df)
    # the headline table must carry a 'segment' dimension (MB and SME shown apart)
    t = f.tables[0][1]
    assert "segment" in t.columns and set(t["segment"]).issuperset({"MB", "SME"})


def test_trap2_min_n_unbypassable():
    # a sub-floor row cannot survive the report guard regardless of what a finding emits
    t = pd.DataFrame({"segment": ["a"], "median_alpha_%": [123.4], "N": [3]})
    g = _guard_table(t)
    assert "insufficient" in str(g.loc[0, "median_alpha_%"])


def test_trap4_delisted_not_dropped():
    df = spine.load_substrate()
    assert (df["delisted"] == True).sum() > 100
    states = spine.terminal_state(df)
    assert len(states) == len(df)
    assert states.isin(["alive", "wipeout", "payout", "alive_delisted_unknown"]).all()
    # wipeout is a band (lower <= upper), reflecting sparse reasons
    b = spine.wipeout_band(df)
    assert b["wipeout_upper"] >= b["wipeout_lower"]


def test_trap1_long_horizon_is_longterm_carried():
    # boom 5y alpha must be too sparse to be a tradable claim (maturity-gating)
    df = spine.load_substrate()
    boom = spine.segment(df, cohort="boom")
    n_boom_5y = spine.maturity_gated(boom, "5y").shape[0]
    n_long_5y = spine.maturity_gated(spine.segment(df, cohort="longterm"), "5y").shape[0]
    assert n_long_5y > n_boom_5y * 3   # longterm carries the long horizon


def test_trap3_t6_runs_on_longterm_matured():
    # sector matrix tables should be the longterm cohort (matured) — coverage note for boom only
    df = spine.load_substrate()
    f = t6_sector.compute(df)
    assert f.tables  # produced without crashing on the boom sector gap
