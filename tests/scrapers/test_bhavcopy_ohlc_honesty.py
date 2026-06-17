"""Tests for the Rule 2 bhavcopy_ohlc.py sentinel/retry fix.

Pure-function tests only — no network calls.

Pinned behaviours:
  1. fetch_nse / fetch_bse return (text_or_None, fetch_ok_bool) tuples.
  2. load_done excludes rows with rows=-1 (fetch_error sentinel).
  3. mark_done writes the given n_rows value faithfully.
  4. run() calls mark_done with -1 on fetch failure (not 0).
  5. run() calls ingest.save_raw after a successful fetch.
"""
import csv
import io
import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_ohlc():
    path = ROOT / 'scrapers' / 'bhavcopy_ohlc.py'
    spec = importlib.util.spec_from_file_location('scr_bhavcopy_ohlc_honesty', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── fetch return-type tests ──────────────────────────────────────────────────

class TestFetchReturnTuples:
    def test_fetch_nse_ok(self):
        import zipfile
        mod = _load_ohlc()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('f.csv', 'TckrSymb,ISIN\nACME,INE001\n')
        zip_bytes = buf.getvalue()
        resp = MagicMock(); resp.status_code = 200; resp.content = zip_bytes
        with patch('requests.get', return_value=resp):
            text, ok = mod.fetch_nse(datetime(2024, 8, 1))
        assert ok is True
        assert text is not None

    def test_fetch_nse_fail(self):
        mod = _load_ohlc()
        import requests as req_mod
        with patch('requests.get', side_effect=req_mod.exceptions.ConnectionError('x')):
            text, ok = mod.fetch_nse(datetime(2024, 8, 1))
        assert ok is False
        assert text is None

    def test_fetch_bse_ok(self):
        mod = _load_ohlc()
        content = b'TckrSymb,ISIN\n' + b'X' * 25000
        resp = MagicMock()
        resp.status_code = 200
        resp.content = content
        resp.text = content.decode('utf-8', 'replace')
        with patch('requests.get', return_value=resp):
            text, ok = mod.fetch_bse(datetime(2024, 8, 1))
        assert ok is True

    def test_fetch_bse_non200_fail(self):
        mod = _load_ohlc()
        resp = MagicMock(); resp.status_code = 404
        with patch('requests.get', return_value=resp):
            text, ok = mod.fetch_bse(datetime(2024, 8, 1))
        assert ok is False
        assert text is None


# ── manifest sentinel tests ──────────────────────────────────────────────────

class TestManifestSentinel:
    def test_load_done_excludes_minus1(self, tmp_path):
        mod = _load_ohlc()
        manifest = tmp_path / '_days_done.csv'
        with open(manifest, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['exchange', 'date', 'rows'])
            w.writerow(['NSE', '2024-08-01', 100])   # success
            w.writerow(['BSE', '2024-08-01', -1])    # fetch error -> must NOT be in done
            w.writerow(['NSE', '2024-08-02', 0])     # holiday -> in done (rows=0 is genuine)

        with patch.object(mod, '_manifest', return_value=manifest):
            done = mod.load_done()

        assert ('NSE', '2024-08-01') in done
        assert ('BSE', '2024-08-01') not in done, "rows=-1 must be excluded from done"
        assert ('NSE', '2024-08-02') in done

    def test_mark_done_writes_sentinel(self, tmp_path):
        mod = _load_ohlc()
        manifest = tmp_path / '_days_done.csv'
        with patch.object(mod, '_manifest', return_value=manifest):
            mod.mark_done('BSE', '2024-08-01', -1)
        rows = list(csv.DictReader(open(manifest)))
        assert len(rows) == 1
        assert int(rows[0]['rows']) == -1

    def test_mark_done_holiday_zero(self, tmp_path):
        mod = _load_ohlc()
        manifest = tmp_path / '_days_done.csv'
        with patch.object(mod, '_manifest', return_value=manifest):
            mod.mark_done('NSE', '2024-08-01', 0)
        rows = list(csv.DictReader(open(manifest)))
        assert int(rows[0]['rows']) == 0


# ── run() integration test ───────────────────────────────────────────────────

class TestRunSentinelAndSaveRaw:
    def test_run_marks_minus1_on_fetch_fail(self, tmp_path):
        """When fetch returns (None, False), run must write rows=-1 not rows=0."""
        mod = _load_ohlc()
        isin_set = {'INE001A01036'}
        sym2isin = {}
        d = datetime(2024, 8, 1)

        marked = []

        def fake_load_universe():
            return isin_set, sym2isin

        def fake_load_done():
            return set()

        def fake_mark_done(exchange, date_str, n_rows):
            marked.append((exchange, date_str, n_rows))

        def fake_fetch_nse(_d):
            return (None, False)

        def fake_fetch_bse(_d):
            return (None, False)

        with patch.object(mod, 'load_universe', fake_load_universe), \
             patch.object(mod, 'load_done', fake_load_done), \
             patch.object(mod, 'mark_done', fake_mark_done), \
             patch.object(mod, 'fetch_nse', fake_fetch_nse), \
             patch.object(mod, 'fetch_bse', fake_fetch_bse), \
             patch.object(mod, '_setup_logging'), \
             patch.object(mod.config, 'ensure'), \
             patch.object(mod, 'append_day'):
            mod.run(d, d, exchanges=('NSE', 'BSE'), sleep=0)

        nse_entry = next((e for e in marked if e[0] == 'NSE'), None)
        bse_entry = next((e for e in marked if e[0] == 'BSE'), None)
        assert nse_entry is not None and nse_entry[2] == -1, "NSE fetch fail -> rows=-1"
        assert bse_entry is not None and bse_entry[2] == -1, "BSE fetch fail -> rows=-1"

    def test_run_saves_raw_on_success(self, tmp_path):
        """Successful fetch must call ingest.save_raw before parsing."""
        mod = _load_ohlc()
        isin_set = {'INE001A01036'}
        sym2isin = {}
        d = datetime(2024, 8, 1)
        raw_csv = 'TckrSymb,ISIN,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\nACME,INE001A01036,10.0,11.0,9.0,10.5,1000\n'
        saved = []

        def fake_save_raw(source, name, content, **kw):
            saved.append((source, name))

        with patch.object(mod, 'load_universe', return_value=(isin_set, sym2isin)), \
             patch.object(mod, 'load_done', return_value=set()), \
             patch.object(mod, 'mark_done'), \
             patch.object(mod, 'fetch_nse', return_value=(raw_csv, True)), \
             patch.object(mod, 'fetch_bse', return_value=(None, False)), \
             patch.object(mod, '_setup_logging'), \
             patch.object(mod.config, 'ensure'), \
             patch.object(mod, 'append_day'), \
             patch.object(mod.ingest, 'save_raw', side_effect=fake_save_raw):
            mod.run(d, d, exchanges=('NSE', 'BSE'), sleep=0)

        assert any(s[0] == 'bhavcopy_ohlc' for s in saved), "save_raw must be called with source='bhavcopy_ohlc'"
