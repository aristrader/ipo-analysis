"""GOLDEN headline numbers: the key analytical outputs, asserted against the
ACCEPTED values in data/reference/golden_numbers.json.

The computation lives in layer3/goldens.py (one source). A refresh re-derives the
accepted file CONSCIOUSLY (tools/refresh/derive_goldens.py prints OLD -> NEW); a
failure here therefore means SILENT analytical drift — something changed a number
without going through the refresh/derive protocol. That is this test's entire job.
"""
import pytest

from layer3 import goldens


def test_current_computation_matches_accepted_goldens():
    accepted = goldens.load_accepted()
    current = goldens.compute()
    assert set(current) == set(accepted), (
        f"golden key set changed: only_current={set(current)-set(accepted)} "
        f"only_accepted={set(accepted)-set(current)} — re-derive consciously")
    drift = []
    for k, cur in current.items():
        tol = goldens.TOLERANCES.get(k, 0)
        if abs(cur - accepted[k]) > tol:
            drift.append((k, accepted[k], cur))
    assert not drift, (
        "SILENT ANALYTICAL DRIFT — values changed without the derive protocol "
        f"(if intentional: run tools/refresh/derive_goldens.py): {drift}")


def test_goldens_file_is_well_formed():
    accepted = goldens.load_accepted()
    assert len(accepted) >= 10
    assert all(isinstance(v, (int, float)) for v in accepted.values())
    # every key has an explicit tolerance policy
    assert set(goldens.TOLERANCES) == set(accepted)
