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
    # STRUCTURAL checks only: the actual values are RE-DERIVED from data by
    # run_weights (and shift after a refresh) — pinning them here would make every
    # refresh fail. Value-evolution is governed by the evolve-only-if-robust policy.
    vals = list(weights.values())
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert sum(vals) == pytest.approx(1.0, abs=0.01), f"weights sum {sum(vals)}"


def test_canonical_weights_match_fresh_derivation(weights):
    """PROTECTION (I3): the committed weights MUST equal a fresh DETERMINISTIC derivation under the
    LIVE scorecard def. Converts SILENT drift into a loud failure — catches a hard-killed research
    run that left per-month weights in the canonical file, a hand-edit, OR a score-def change (e.g.
    the banker OBSCURE_BANKER_MODE) that wasn't followed by `run_weights.py`. derive_weights is
    deterministic, so this is stable; after a conscious refresh the canonical + a fresh derive move
    together, so the invariant 'canonical == what derive produces now' always holds."""
    from layer3.predictor import weights as W
    fresh, _rep, _scored = W.derive_weights()
    fresh = {k: round(float(v), 3) for k, v in fresh.items()}
    committed = {k: round(float(v), 3) for k, v in weights.items()}
    assert committed == fresh, (
        f"canonical scorecard_weights.json drifted from a fresh derivation:\n"
        f"  committed={committed}\n  fresh    ={fresh}\n"
        f"-> re-run `PYTHONPATH=. python run_weights.py`, or investigate a stale/killed write.")


def test_calibration_parses():
    c = json.load(open(os.path.join(ROOT, "data/master/scorecard_calibration.json")))
    assert isinstance(c, dict) and len(c) >= 1
