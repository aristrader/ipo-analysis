import pandas as pd
from layer3 import spine
from layer3.predictor import weights as W, analogs, scorecard


def test_component_lift_signs():
    # construct a scored frame where return_potential tracks realized alpha and quality is noise
    scored = pd.DataFrame({
        "cohort": ["boom"] * 40 + ["longterm"] * 40,
        "realized_alpha": list(range(40)) + list(range(40)),
        "return_potential": list(range(40)) + list(range(40)),     # perfectly correlated
        "multibagger_odds": list(range(40)) + list(range(40)),
        "downside_safety": list(range(40)) + list(range(40)),
        "liquidity": list(range(40)) + list(range(39, -1, -1)),     # sign flips by cohort
        "quality": [1] * 80,
    })
    lift = W.component_lift(scored)
    assert lift["return_potential"]["boom"] > 0.9 and lift["return_potential"]["longterm"] > 0.9
    assert lift["liquidity"]["boom"] > 0 and lift["liquidity"]["longterm"] < 0   # the flip


def test_derive_weights_zeroes_sign_flippers_and_normalizes():
    scored = pd.DataFrame({
        "cohort": ["boom"] * 40 + ["longterm"] * 40,
        "realized_alpha": list(range(40)) * 2,
        "return_potential": list(range(40)) * 2,
        "multibagger_odds": list(range(40)) * 2,
        "downside_safety": list(range(40)) * 2,
        "liquidity": list(range(40)) + list(range(39, -1, -1)),
        "quality": [1] * 80,
    })
    # monkeypatch the scoring step to return our frame
    import types
    orig = W.score_all_pointintime
    W.score_all_pointintime = lambda df, horizon="3y", max_ipos=None: scored
    try:
        weights, report, _ = W.derive_weights(pd.DataFrame())
    finally:
        W.score_all_pointintime = orig
    assert weights["liquidity"] == 0.0          # sign-flipper zeroed
    assert weights["quality"] == 0.0            # zero-variance (NaN IC) zeroed
    assert weights["return_potential"] > 0
    assert abs(sum(weights.values()) - 1.0) < 0.01   # normalized (3-dp rounded for display)


def test_save_load_roundtrip(tmp_path):
    p = tmp_path / "w.json"
    w = {"return_potential": 0.4, "downside_safety": 0.6}
    W.save_weights(w, p)
    assert W.load_weights(p) == w
    assert W.load_weights(tmp_path / "missing.json") is None


def test_scorecard_data_informed_profile_runs():
    df = spine.load_substrate()
    q = {"type": "MB", "broad_sector": "Financial Services", "market_cap_class": "mid"}
    r = analogs.find_analogs(q, df=df, k=50)
    sc = scorecard.scorecard(q, r["cohort"], r, profile="data_informed")
    assert sc["combined_score"] is None or (0 <= sc["combined_score"] <= 100)
    assert isinstance(sc["weights"], dict)
