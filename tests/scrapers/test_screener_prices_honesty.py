"""Tests for screener_prices.py repoint + save_raw (Rule 1+2, audit CLEAN).

Pure-function tests only — no network calls.

Pinned behaviours:
  1. OUT_DIR is a pathlib.Path (from config.raw_dir), not a hardcoded string.
  2. fetch_chart calls ingest.save_raw before parsing.
  3. fetch_chart returns correct {date, close, volume} dicts; volume=None preserved as None.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_screener_prices():
    path = ROOT / 'scrapers' / 'screener_prices.py'
    spec = importlib.util.spec_from_file_location('scr_screener_prices_honesty', path)
    mod = importlib.util.module_from_spec(spec)
    # screener_prices imports screener at top level; stub it
    import types
    stub = types.ModuleType('screener')
    stub.UA = {'User-Agent': 'test'}
    stub.fetch_company = lambda *a, **k: None
    stub.page_name = lambda h: ''
    stub.name_match = lambda *a, **k: False
    stub.search_company = lambda *a, **k: []
    sys.modules.setdefault('screener', stub)
    spec.loader.exec_module(mod)
    return mod


class TestOutDirIsPath:
    def test_out_dir_is_pathlib(self):
        mod = _load_screener_prices()
        assert isinstance(mod.OUT_DIR, Path), "OUT_DIR must be a pathlib.Path (from config.raw_dir)"


class TestFetchChartSavesRaw:
    def _make_chart_payload(self):
        return json.dumps({
            'datasets': [
                {'metric': 'Price', 'values': [['2024-01-01', '100.5'], ['2024-01-08', '102.0']]},
                {'metric': 'Volume', 'values': [['2024-01-01', 50000], ['2024-01-08', 60000]]},
            ]
        })

    def test_save_raw_called_with_company_id(self):
        mod = _load_screener_prices()
        raw = self._make_chart_payload()
        saved = []
        with patch.object(mod, '_get', return_value=raw), \
             patch.object(mod.ingest, 'save_raw', side_effect=lambda *a, **k: saved.append(a)):
            mod.fetch_chart('12345', sleep=0)
        assert saved, "save_raw must be called"
        assert saved[0][0] == 'screener_prices'
        assert '12345' in saved[0][1]

    def test_fetch_chart_parses_price_and_volume(self):
        mod = _load_screener_prices()
        raw = self._make_chart_payload()
        with patch.object(mod, '_get', return_value=raw), \
             patch.object(mod.ingest, 'save_raw'):
            rows = mod.fetch_chart('12345', sleep=0)
        assert len(rows) == 2
        assert rows[0]['date'] == '2024-01-01'
        assert rows[0]['close'] == 100.5
        assert rows[0]['volume'] == 50000.0

    def test_none_volume_preserved_as_none(self):
        """Volume missing from volmap -> None (not fabricated as 0)."""
        mod = _load_screener_prices()
        payload = json.dumps({
            'datasets': [
                {'metric': 'Price', 'values': [['2024-01-01', '100.5']]},
                # no Volume dataset at all
            ]
        })
        with patch.object(mod, '_get', return_value=payload), \
             patch.object(mod.ingest, 'save_raw'):
            rows = mod.fetch_chart('99999', sleep=0)
        assert rows[0]['volume'] is None, "missing volume must be None, not 0"
