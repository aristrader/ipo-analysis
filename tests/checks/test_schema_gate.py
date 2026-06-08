"""Thread B: schema-gate behavior (catches drift the count checks miss) + the gate passes live."""
import pandas as pd
import pytest

from tools.checks import schema_gate as G


def test_real_data_passes_gate():
    assert G.check_all() == []          # the live products honor their pinned contracts


def test_gate_catches_violations(tmp_path, monkeypatch):
    # a corrupted ledger: score out of range + a null call_id + dup
    bad = tmp_path / "calls_ledger.csv"
    pd.DataFrame([
        {"call_id": "x", "isin": "I1", "call_type": "APPLY", "mode": "live", "call_date": "2026-01-01",
         "score": 999, "alpha_1m": 0.1, "alpha_3m": 0.1, "grade_status": "final"},
        {"call_id": "x", "isin": "I2", "call_type": "APPLY", "mode": "live", "call_date": "2026-01-02",
         "score": 50, "alpha_1m": 0.1, "alpha_3m": 0.1, "grade_status": "final"},
    ]).to_csv(bad, index=False)
    v = G._check_file_abs(str(bad), G.SCHEMAS["data/master/calls_ledger.csv"])
    joined = " ".join(v)
    assert "score" in joined and "max" in joined        # 999 > 100 caught
    assert "unique" in joined or "duplicates" in joined  # dup call_id caught
    assert "rows" in joined                              # below min-rows floor caught


def test_gate_catches_enum_typo(tmp_path):
    bad = tmp_path / "calls_ledger.csv"
    pd.DataFrame([{"call_id": "x", "isin": "I1", "call_type": "APPLY",
                   "mode": "histroical_sim",         # typo the red-team flagged
                   "call_date": "2026-01-01", "score": 50, "alpha_1m": 0.1, "alpha_3m": 0.1,
                   "grade_status": "final"}]).to_csv(bad, index=False)
    v = " ".join(G._check_file_abs(str(bad), G.SCHEMAS["data/master/calls_ledger.csv"]))
    assert "mode" in v and "unexpected" in v            # histroical_sim caught
