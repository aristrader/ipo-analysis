"""Integrity of the persisted scorecard weights/calibration (showdown gap-close).

These JSONs steer the data_informed scoring profile; a corrupted or hand-mangled
file would silently change every score. run_weights EXECUTION is proven in the
sandbox (tests/showdown/test_pipeline_sandbox.py) since it writes to data/master.
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def weights():
    return json.load(open(os.path.join(ROOT, "data/master/scorecard_weights.json")))


def test_weights_components_match_registry(weights):
    from layer3.predictor import weights as W
    assert set(weights.keys()) == set(W.COMPONENTS), (
        f"weights file components {sorted(weights)} != registry {sorted(W.COMPONENTS)}")


def test_weights_are_normalized_and_sane(weights):
    vals = list(weights.values())
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert sum(vals) == pytest.approx(1.0, abs=0.01), f"weights sum {sum(vals)}"
    # the validated decisions: liquidity/quality carry 0; wipeout_safety earned 0.13
    assert weights["liquidity"] == 0.0 and weights["quality"] == 0.0
    assert weights["wipeout_safety"] == pytest.approx(0.13, abs=0.02)


def test_calibration_parses():
    c = json.load(open(os.path.join(ROOT, "data/master/scorecard_calibration.json")))
    assert isinstance(c, dict) and len(c) >= 1
