"""Forward-test module: structure + honesty rails (no network; uses real frames)."""
from layer3 import forward_test as ft


def test_cohort_is_never_seen_and_listed():
    old, new = ft.load_frames()
    c = ft.forward_cohort(old, new)
    assert len(c) > 0
    assert not set(c["isin"]) & set(old["isin"].astype(str)), "cohort leaked already-seen isins"


def test_analyze_carries_early_read_label():
    import pandas as pd
    scored = pd.DataFrame({"isin": ["A"] * 25, "score": range(25), "n_flags": [0] * 25,
                           "gmp_pct": [None] * 25, "pop": [0.1] * 25,
                           "ret_1m": [0.05] * 25, "ret_3m": [None] * 25})
    res = ft.analyze(scored)
    assert "EARLY READ" in res["label"]
    assert res["n_scored"] == 25
