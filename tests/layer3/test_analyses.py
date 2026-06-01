from layer3 import spine, config
from layer3.backtest import analyses


def test_holding_period_sweep():
    df = spine.load_substrate()
    t = analyses.holding_period_sweep(df, "MB")
    assert list(t["exit"]) == config.HORIZONS
    assert (t["N"] >= 0).all()
    # smallcap benchmark variant runs
    assert len(analyses.holding_period_sweep(df, "SME", benchmark="smallcap")) == len(config.HORIZONS)


def test_portfolio_summary():
    df = spine.load_substrate()
    t = analyses.portfolio_summary(df, horizon="1y")
    assert {"segment", "basket_mean_alpha_%", "cross_name_dispersion_%", "beats_donothing"}.issubset(t.columns)
    assert set(t["segment"]).issubset({"MB", "SME"})


def test_flip_allotment_ev():
    df = spine.load_substrate()
    ev = analyses.flip_allotment_ev(df, "MB")
    assert ev is not None
    # adverse selection: hot IPOs are harder to get, so allotment-weighted <= naive (cost >= ~0)
    assert ev["adverse_selection_cost_pp"] == round(ev["naive_mean_flip_%"] - ev["allotment_weighted_flip_%"], 1)
    assert 0 < ev["median_allotment_prob"] <= 1
