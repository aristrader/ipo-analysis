"""Refresh-flow machinery tests (no network): meta round-trip, goldens protocol,
manual-overrides schema, year-window logic, ingest idempotency helpers."""
import csv
import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_substrate_meta_well_formed():
    m = json.load(open(os.path.join(ROOT, "data/master/substrate_meta.json")))
    assert {"as_of", "rows", "archive_pointer"} <= set(m)
    assert m["rows"] >= 2296
    # the pointer must exist on disk and contain a substrate snapshot
    snap = os.path.join(ROOT, m["archive_pointer"], "ipo_analysis.csv")
    assert os.path.exists(snap), f"archive pointer dangling: {m['archive_pointer']}"


def test_config_as_of_matches_meta():
    from layer3 import config
    m = json.load(open(os.path.join(ROOT, "data/master/substrate_meta.json")))
    assert str(config.AS_OF_DATE) == m["as_of"]


def test_goldens_protocol_files_consistent():
    from layer3 import goldens
    accepted = goldens.load_accepted()
    assert set(goldens.TOLERANCES) == set(accepted)


def test_manual_overrides_schema_and_application():
    path = os.path.join(ROOT, "data/reference/manual_overrides.csv")
    rows = list(csv.DictReader(open(path)))
    assert rows and {"isin", "column", "value", "reason", "date"} <= set(rows[0])
    # every override actually present in the live substrate (09 applied them)
    import pandas as pd
    df = pd.read_csv(os.path.join(ROOT, "data/master/ipo_analysis.csv"), dtype=str).set_index("isin")
    for o in rows:
        assert df.loc[o["isin"], o["column"]] == o["value"], f"override not applied: {o['isin']}.{o['column']}"


def test_boom_year_window_is_dynamic():
    # 01 executes on import (script-style) — inspect the source instead of importing
    src = open(os.path.join(ROOT, "pipeline/01_build_base.py")).read()
    assert "_boom_years" in src, "dynamic year helper missing"
    assert "('2020','2021'" not in src.replace(" ", ""), "year window must not be a hardcoded tuple"


def test_ingest_append_is_idempotent(tmp_path):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools/refresh"))
    import ingest
    p = tmp_path / "x.csv"
    p.write_text("isin,foo\nA,1\n")
    assert ingest._existing(str(p)) == {"A"}
    n = ingest._append(str(p), [{"isin": "B", "foo": "2", "extra": "ignored"}])
    assert n == 1
    assert ingest._existing(str(p)) == {"A", "B"}
