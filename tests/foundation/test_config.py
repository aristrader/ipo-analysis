"""Tests for foundation.config — the central control-plane config (T0.3)."""
import importlib
from datetime import date

import foundation.config as cfg


def test_output_root_defaults_to_data_build():
    # INTENTIONAL: this asserts the real DEFAULT (build-beside-old). It must NOT be isolated/overridden
    # — that's why the OUTPUT_ROOT isolation fixture lives in tests/scrapers/conftest.py, not here.
    assert cfg.OUTPUT_ROOT.name == "data_build"
    assert cfg.OUTPUT_ROOT.parent == cfg.REPO_ROOT


def test_output_root_env_override(monkeypatch):
    monkeypatch.setenv("IPO_OUTPUT_ROOT", "data")
    try:
        reloaded = importlib.reload(cfg)
        assert reloaded.OUTPUT_ROOT.name == "data"
    finally:
        monkeypatch.delenv("IPO_OUTPUT_ROOT", raising=False)
        importlib.reload(cfg)  # restore default for other tests


def test_path_helpers_join_under_output_root():
    assert cfg.raw_dir("chittorgarh") == cfg.OUTPUT_ROOT / "raw" / "chittorgarh"
    assert cfg.raw_dir() == cfg.OUTPUT_ROOT / "raw"
    assert cfg.master_dir() == cfg.OUTPUT_ROOT / "master"
    assert cfg.prices_dir() == cfg.OUTPUT_ROOT / "prices"
    assert cfg.reference_dir() == cfg.OUTPUT_ROOT / "reference"


def test_input_root_is_frozen_data():
    assert cfg.INPUT_ROOT.name == "data"
    assert cfg.src("master", "ipo_analysis.csv") == cfg.INPUT_ROOT / "master" / "ipo_analysis.csv"


def test_cohort_split_on_2020_boundary():
    assert cfg.cohort_of(date(2019, 12, 31)) == "longterm"
    assert cfg.cohort_of(date(2020, 1, 1)) == "boom"
    assert cfg.cohort_of(date(2023, 6, 1)) == "boom"
    assert cfg.cohort_of(date(2006, 1, 1)) == "longterm"
