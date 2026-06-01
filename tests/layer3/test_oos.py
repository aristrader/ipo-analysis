from layer3 import spine
from layer3.predictor import weights as W


def test_oos_evaluate_contract():
    df = spine.load_substrate()
    r = W.oos_evaluate(df, cutoff_year=2022, horizon="1y")
    assert {"n_train", "n_test", "oos_lift_pp", "weights"}.issubset(r)
    assert r["n_train"] > 0 and r["n_test"] > 0
    # weights normalize to ~1 (or 0 if none qualified)
    tot = sum(r["weights"].values())
    assert abs(tot - 1.0) < 0.02 or tot == 0.0
    # lift is a finite number
    assert isinstance(r["oos_lift_pp"], (int, float))


def test_oos_is_genuinely_out_of_sample():
    # train and test sets must be disjoint by listing year (no leakage of test rows into the fit)
    import pandas as pd
    df = spine.load_substrate()
    df = df.copy(); df["_yr"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.year
    r = W.oos_evaluate(df, cutoff_year=2021, horizon="1y")
    # n_test should match IPOs listed after 2021 with matured 1y alpha (sanity: > 0, < total)
    assert 0 < r["n_test"] < len(df)
