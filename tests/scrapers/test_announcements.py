"""Tests for scrapers/announcements.py pure helpers (no network).

_write_misses is pure (filesystem only) so we test it directly with tmp_path.
The collect() / fetch_symbol() orchestration touches the network and is not tested here.
"""
import csv
import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_announcements():
    path = os.path.join(ROOT, "scrapers", "announcements.py")
    spec = importlib.util.spec_from_file_location("scr_announcements", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ann():
    return _load_announcements()


# --- _write_misses: pure function (writes a CSV) ---

def test_write_misses_no_data_reason(ann, tmp_path):
    """Symbols with genuine empty lists must be written with reason='no_announcements_returned'."""
    path = tmp_path / "misses.csv"
    ann._write_misses(["AAPL", "RELIANCE"], set(), str(path))
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    reasons = {r["nse_symbol"]: r["reason"] for r in rows}
    assert reasons["AAPL"] == "no_announcements_returned"
    assert reasons["RELIANCE"] == "no_announcements_returned"


def test_write_misses_fetch_failed_reason(ann, tmp_path):
    """Symbols that errored on both fetch attempts must be written with reason='fetch_failed'."""
    path = tmp_path / "misses.csv"
    ann._write_misses([], {"FAIL1", "FAIL2"}, str(path))
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    reasons = {r["nse_symbol"]: r["reason"] for r in rows}
    assert reasons["FAIL1"] == "fetch_failed"
    assert reasons["FAIL2"] == "fetch_failed"


def test_write_misses_mixed_reasons_are_distinct(ann, tmp_path):
    """A run with both kinds must produce both reason values — they must NOT be conflated."""
    path = tmp_path / "misses.csv"
    ann._write_misses(["EMPTY_SYM"], {"ERR_SYM"}, str(path))
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    reasons = {r["nse_symbol"]: r["reason"] for r in rows}
    assert reasons["EMPTY_SYM"] == "no_announcements_returned"
    assert reasons["ERR_SYM"] == "fetch_failed"
    # The old bug: both would have been 'no_announcements_returned'.
    assert reasons["EMPTY_SYM"] != reasons["ERR_SYM"], (
        "fetch_failed and no_announcements_returned must NOT be the same reason string"
    )


def test_write_misses_empty_run_writes_header_only(ann, tmp_path):
    """No misses -> file must still be written with a header (makes downstream readers safe)."""
    path = tmp_path / "misses.csv"
    ann._write_misses([], set(), str(path))
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == []  # header present, no data rows


def test_write_misses_header_columns(ann, tmp_path):
    """The CSV header must be exactly [nse_symbol, reason]."""
    path = tmp_path / "misses.csv"
    ann._write_misses(["X"], set(), str(path))
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["nse_symbol", "reason"]
