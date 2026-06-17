"""Tests for the Rule 2+3 bhavcopy.py cache-honesty fixes.

Pure-function and cache-logic tests only — no network calls.

Pinned behaviours:
  1. fetch_nse / fetch_bse return (text, status) tuples, never bare None.
  2. get_bhavcopy does NOT write a cache file on fetch_error.
  3. get_bhavcopy writes a holiday sentinel on holiday (404).
  4. get_bhavcopy writes status='ok' rows on successful fetch and returns the dict.
  5. An existing poisoned-empty cache file (header-only, 0 data rows) is treated as
     a cache miss so next run retries.
  6. Backward-compat: old cache files with only key,open columns are read correctly.
"""
import csv
import io
import os
import sys
import types
import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_bhavcopy():
    path = ROOT / 'scrapers' / 'bhavcopy.py'
    spec = importlib.util.spec_from_file_location('scr_bhavcopy_honesty', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_csv(rows, fieldnames):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


# ── tests ────────────────────────────────────────────────────────────────────

class TestFetchStatusTuples:
    """fetch_nse and fetch_bse must return (text_or_None, status_str) tuples."""

    def test_fetch_nse_ok(self):
        mod = _load_bhavcopy()
        import zipfile, io as _io
        # Build a minimal valid zip in memory
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('bhav.csv', 'TckrSymb,ISIN,OpnPric\nACME,INE001,10.0\n')
        zip_bytes = buf.getvalue()

        resp = MagicMock()
        resp.status_code = 200
        resp.content = zip_bytes
        with patch('requests.get', return_value=resp):
            text, status = mod.fetch_nse(datetime(2024, 8, 1))
        assert status == 'ok'
        assert 'ACME' in text

    def test_fetch_nse_404_holiday(self):
        mod = _load_bhavcopy()
        resp = MagicMock(); resp.status_code = 404
        with patch('requests.get', return_value=resp):
            text, status = mod.fetch_nse(datetime(2024, 8, 1))
        assert status == 'holiday'
        assert text is None

    def test_fetch_nse_500_fetch_error(self):
        mod = _load_bhavcopy()
        resp = MagicMock(); resp.status_code = 500
        with patch('requests.get', return_value=resp):
            text, status = mod.fetch_nse(datetime(2024, 8, 1))
        assert status == 'fetch_error'
        assert text is None

    def test_fetch_nse_exception_fetch_error(self):
        mod = _load_bhavcopy()
        import requests as req_mod
        with patch('requests.get', side_effect=req_mod.exceptions.ConnectionError('no route')):
            text, status = mod.fetch_nse(datetime(2024, 8, 1))
        assert status == 'fetch_error'
        assert text is None

    def test_fetch_bse_ok(self):
        mod = _load_bhavcopy()
        resp = MagicMock()
        resp.status_code = 200
        # content must be >1000 bytes with a comma near the start
        content = (b'TckrSymb,ISIN,OpnPric\n' + b'X' * 2000)
        resp.content = content
        resp.text = content.decode('utf-8', 'replace')
        with patch('requests.get', return_value=resp):
            text, status = mod.fetch_bse(datetime(2024, 8, 1))
        assert status == 'ok'

    def test_fetch_bse_404_holiday(self):
        mod = _load_bhavcopy()
        resp = MagicMock(); resp.status_code = 404
        with patch('requests.get', return_value=resp):
            text, status = mod.fetch_bse(datetime(2024, 8, 1))
        assert status == 'holiday'
        assert text is None


class TestGetBhavcopyCacheHonesty:
    """get_bhavcopy must not write cache on fetch_error; must write sentinel on holiday."""

    def _make_mod_with_fetch(self, text, status, tmp_path):
        """Load mod with fetch patched to return (text, status) and cache_dir set to tmp_path."""
        mod = _load_bhavcopy()
        # Patch _cache_path to use tmp_path
        mod._orig_cache_path = mod._cache_path

        def fake_cache_path(exchange, d):
            return tmp_path / f'{exchange}_{d.strftime("%Y%m%d")}.csv'

        mod._cache_path = fake_cache_path
        return mod

    def test_fetch_error_no_cache_written(self, tmp_path):
        mod = self._make_mod_with_fetch(None, 'fetch_error', tmp_path)
        d = datetime(2024, 8, 1)
        with patch.object(mod, 'fetch_nse', return_value=(None, 'fetch_error')):
            result = mod.get_bhavcopy('NSE', d)
        assert result == {}
        # No cache file should be written
        cp = tmp_path / 'NSE_20240801.csv'
        assert not cp.exists(), "fetch_error must NOT create a cache file"

    def test_holiday_writes_sentinel(self, tmp_path):
        mod = self._make_mod_with_fetch(None, 'holiday', tmp_path)
        d = datetime(2024, 8, 1)
        with patch.object(mod, 'fetch_nse', return_value=(None, 'holiday')):
            result = mod.get_bhavcopy('NSE', d)
        assert result == {}
        cp = tmp_path / 'NSE_20240801.csv'
        assert cp.exists(), "holiday must write a sentinel cache file"
        rows = list(csv.DictReader(open(cp)))
        assert len(rows) == 1
        assert rows[0]['status'] == 'holiday'
        assert rows[0]['key'] == ''

    def test_ok_writes_data_rows(self, tmp_path):
        raw_csv = 'TckrSymb,ISIN,OpnPric\nACME,INE001A01036,10.5\n'
        mod = self._make_mod_with_fetch(raw_csv, 'ok', tmp_path)
        d = datetime(2024, 8, 1)
        with patch.object(mod, 'fetch_nse', return_value=(raw_csv, 'ok')):
            with patch.object(mod.ingest, 'save_raw', return_value=tmp_path / 'raw.csv'):
                result = mod.get_bhavcopy('NSE', d)
        assert 'INE001A01036' in result
        cp = tmp_path / 'NSE_20240801.csv'
        assert cp.exists()
        rows = list(csv.DictReader(open(cp)))
        data_rows = [r for r in rows if r.get('key')]
        assert any(r['status'] == 'ok' for r in data_rows)

    def test_poisoned_empty_cache_retried(self, tmp_path):
        """An existing cache file with header only (0 data rows) is treated as cache miss."""
        mod = _load_bhavcopy()
        d = datetime(2024, 8, 1)
        cp = tmp_path / 'NSE_20240801.csv'

        # Write the old poisoned empty file (header only)
        with open(cp, 'w', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=['key', 'open']).writeheader()

        def fake_cache_path(exchange, _d):
            return cp

        mod._cache_path = fake_cache_path

        raw_csv = 'TckrSymb,ISIN,OpnPric\nACME,INE001A01036,10.5\n'
        with patch.object(mod, 'fetch_nse', return_value=(raw_csv, 'ok')) as mock_fetch:
            with patch.object(mod.ingest, 'save_raw', return_value=cp):
                result = mod.get_bhavcopy('NSE', d)
        mock_fetch.assert_called_once()  # must have re-fetched
        assert result  # must have got data

    def test_backward_compat_old_cache_no_status(self, tmp_path):
        """Old cache files (key,open only, no status column) read correctly."""
        mod = _load_bhavcopy()
        d = datetime(2024, 8, 1)
        cp = tmp_path / 'NSE_20240801.csv'

        with open(cp, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['key', 'open'])
            w.writeheader()
            w.writerow({'key': 'INE001A01036', 'open': '42.5'})

        def fake_cache_path(exchange, _d):
            return cp

        mod._cache_path = fake_cache_path
        result = mod.get_bhavcopy('NSE', d)
        assert result == {'INE001A01036': '42.5'}

    def test_second_read_uses_cache_not_fetch(self, tmp_path):
        """A successful fetch writes the cache; re-calling reads cache without fetching again."""
        raw_csv = 'TckrSymb,ISIN,OpnPric\nACME,INE001A01036,10.5\n'
        mod = _load_bhavcopy()
        d = datetime(2024, 8, 1)
        cp = tmp_path / 'NSE_20240801.csv'

        def fake_cache_path(exchange, _d):
            return cp

        mod._cache_path = fake_cache_path

        with patch.object(mod, 'fetch_nse', return_value=(raw_csv, 'ok')) as mock_fetch:
            with patch.object(mod.ingest, 'save_raw', return_value=cp):
                mod.get_bhavcopy('NSE', d)
                mod.get_bhavcopy('NSE', d)  # second call should use cache

        assert mock_fetch.call_count == 1  # only fetched once
