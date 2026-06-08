"""Thread A.2 tests: Wilson interval correctness, scorecard win-rules, score ordering."""
import pandas as pd

from layer3 import calibration as C


def test_wilson_known_values():
    lo, hi = C.wilson(5, 10)                      # 50% of 10 -> ~ (0.24, 0.76)
    assert 0.20 < lo < 0.30 and 0.70 < hi < 0.80
    assert C.wilson(0, 0) == (0.0, 1.0)
    lo2, hi2 = C.wilson(10, 10)                   # 100% -> upper near 1, lower well below 1 (honest)
    assert hi2 <= 1.0 and lo2 < 1.0
    # more data tightens the interval
    w_small = C.wilson(8, 10); w_big = C.wilson(80, 100)
    assert (w_big[1] - w_big[0]) < (w_small[1] - w_small[0])


def test_brier():
    assert C.brier([1.0, 0.0], [1, 0]) == 0.0     # perfect
    assert C.brier([0.5, 0.5], [1, 0]) == 0.25
    assert C.brier([], []) is None


def test_scorecard_win_rules():
    led = pd.DataFrame([
        {"call_type": "APPLY", "mode": "backfilled", "alpha_3m": 0.10},   # right (up)
        {"call_type": "APPLY", "mode": "backfilled", "alpha_3m": -0.05},  # wrong
        {"call_type": "AVOID", "mode": "backfilled", "alpha_3m": -0.20},  # right (avoided a loser)
        {"call_type": "TRACK", "mode": "backfilled", "alpha_3m": 0.30},   # no win-rule -> excluded
    ])
    sc = C.scorecard(led, "3m")
    ap = sc[sc["call_type"] == "APPLY"].iloc[0]
    assert ap["n"] == 2 and ap["hit_rate"] == 0.5
    av = sc[sc["call_type"] == "AVOID"].iloc[0]
    assert av["hit_rate"] == 1.0
    assert "TRACK" not in set(sc["call_type"])     # excluded (no rule)


def test_score_reliability_orders():
    # construct: high score -> usually up, low score -> usually down
    import numpy as np
    rows = []
    for s in range(100):
        score = s
        up = s >= 50
        rows.append({"call_type": "NEUTRAL", "score": score,
                     "alpha_3m": 0.1 if up else -0.1})
    rel = C.score_reliability(pd.DataFrame(rows), "3m", bins=5)
    assert not rel.empty
    # p_up should rise from first bucket to last
    assert rel.iloc[0]["p_up"] < rel.iloc[-1]["p_up"]
