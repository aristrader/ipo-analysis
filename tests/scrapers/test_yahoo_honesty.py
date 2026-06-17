"""Tests for yahoo.py pacing + save_raw fix.

Pure-function tests only — no network calls.

Pinned behaviours:
  1. fetch_chart routes through ingest.fetch (source='yahoo'), not urllib directly.
  2. ingest.save_raw is called with raw JSON before parsing.
  3. fetch_chart returns correct {t,open,high,low,close,volume} bars on success.
  4. fetch_chart returns None when Yahoo result is empty (no data for ticker).
  5. A non-retryable http_error (genuine 404) returns None.
  6. A retryable error (blocked/network) raises RuntimeError (so caller can decide).
"""
import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_yahoo():
    path = ROOT / 'scrapers' / 'yahoo.py'
    spec = importlib.util.spec_from_file_location('scr_yahoo_honesty', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_fetch_ok(bars):
    """Build a mock ingest.Fetch with status=ok and JSON payload for given bars."""
    from foundation import ingest as _ingest
    ts = [b['t'] for b in bars]
    opens = [b['open'] for b in bars]
    highs = [b['high'] for b in bars]
    lows = [b['low'] for b in bars]
    closes = [b['close'] for b in bars]
    volumes = [b['volume'] for b in bars]
    payload = {
        'chart': {
            'result': [{
                'timestamp': ts,
                'indicators': {'quote': [{'open': opens, 'high': highs, 'low': lows,
                                          'close': closes, 'volume': volumes}]}
            }]
        }
    }
    result = MagicMock()
    result.ok = True
    result.retryable = False
    result.status = _ingest.OK
    result.text = json.dumps(payload)
    return result


def _make_fetch_empty():
    from foundation import ingest as _ingest
    result = MagicMock()
    result.ok = True
    result.retryable = False
    result.status = _ingest.OK
    result.text = json.dumps({'chart': {'result': None}})
    return result


def _make_fetch_http_error():
    from foundation import ingest as _ingest
    result = MagicMock()
    result.ok = False
    result.retryable = False
    result.status = _ingest.HTTP_ERROR
    result.error = 'http_error 404'
    result.text = ''
    return result


def _make_fetch_blocked():
    from foundation import ingest as _ingest
    result = MagicMock()
    result.ok = False
    result.retryable = True
    result.status = _ingest.BLOCKED
    result.error = 'block 429'
    return result


SAMPLE_BARS = [
    {'t': 1704067200, 'open': 100.0, 'high': 105.0, 'low': 99.0, 'close': 103.5, 'volume': 12345},
    {'t': 1704153600, 'open': 103.5, 'high': 107.0, 'low': 102.0, 'close': 106.0, 'volume': 23456},
]


class TestFetchChartRoutesViaIngest:
    def test_uses_ingest_fetch_not_urllib(self):
        mod = _load_yahoo()
        fetch_result = _make_fetch_ok(SAMPLE_BARS)
        called_source = []
        def fake_fetch(url, source=None, **kw):
            called_source.append(source)
            return fetch_result
        with patch.object(mod.ingest, 'fetch', side_effect=fake_fetch), \
             patch.object(mod.ingest, 'save_raw'):
            mod.fetch_chart('ETERNAL.NS')
        assert called_source == ['yahoo'], "must use source='yahoo' for pacing"

    def test_save_raw_called_before_parse(self):
        mod = _load_yahoo()
        fetch_result = _make_fetch_ok(SAMPLE_BARS)
        saved = []
        with patch.object(mod.ingest, 'fetch', return_value=fetch_result), \
             patch.object(mod.ingest, 'save_raw', side_effect=lambda *a, **k: saved.append(a)):
            mod.fetch_chart('ETERNAL.NS')
        assert saved, "save_raw must be called"
        assert saved[0][0] == 'yahoo'

    def test_returns_correct_bars(self):
        mod = _load_yahoo()
        fetch_result = _make_fetch_ok(SAMPLE_BARS)
        with patch.object(mod.ingest, 'fetch', return_value=fetch_result), \
             patch.object(mod.ingest, 'save_raw'):
            bars = mod.fetch_chart('ETERNAL.NS')
        assert len(bars) == 2
        assert bars[0]['open'] == 100.0
        assert bars[1]['close'] == 106.0

    def test_empty_result_returns_none(self):
        mod = _load_yahoo()
        fetch_result = _make_fetch_empty()
        with patch.object(mod.ingest, 'fetch', return_value=fetch_result), \
             patch.object(mod.ingest, 'save_raw'):
            result = mod.fetch_chart('UNKNOWN.NS')
        assert result is None

    def test_http_error_returns_none(self):
        """A genuine 404 (non-retryable) means ticker not on Yahoo -> return None."""
        mod = _load_yahoo()
        fetch_result = _make_fetch_http_error()
        with patch.object(mod.ingest, 'fetch', return_value=fetch_result):
            result = mod.fetch_chart('NOGOOD.NS')
        assert result is None

    def test_blocked_raises_runtimeerror(self):
        """Blocked/network errors (retryable, all retries exhausted) raise RuntimeError."""
        mod = _load_yahoo()
        fetch_result = _make_fetch_blocked()
        with patch.object(mod.ingest, 'fetch', return_value=fetch_result):
            with pytest.raises(RuntimeError, match='yahoo fetch'):
                mod.fetch_chart('ETERNAL.NS')
