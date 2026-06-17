"""Yahoo Finance daily chart fetcher.

Yahoo ticker conventions (matches what pipeline/04_verify.py produces):
  - NSE listing : <SYMBOL>.NS        e.g. ETERNAL.NS
  - BSE listing : <numeric code>.BO  e.g. 543982.BO   (NOT the alphabetic scrip_id)

fetch_chart() returns a list of daily bars or None when Yahoo has no data for the ticker.
Used by ticker validation (pipeline/06) and, later, Layer 2 price-history building.

Requests are routed through ingest.fetch (source='yahoo') for pacing + retry/backoff,
so 429 bursts are retried transparently rather than surfacing as errors. Raw chart JSON
is saved via ingest.save_raw before parsing.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

_BASE = 'https://query1.finance.yahoo.com/v8/finance/chart/'


def fetch_chart(ticker, rng='1mo', interval='1d', timeout=20):
    """Fetch daily OHLCV bars for a Yahoo ticker via ingest.fetch (paced, retried).

    Args:
        ticker: Yahoo symbol, e.g. 'ETERNAL.NS' or '543982.BO'.
        rng: Yahoo range string ('5d','1mo','1y','max', ...).
        interval: bar size ('1d').
        timeout: socket timeout seconds (passed to ingest.fetch).

    Returns:
        list of dicts {t,open,high,low,close,volume} (t = epoch seconds), or
        None if the ticker has no data on Yahoo.

    Raises:
        RuntimeError on non-retryable fetch failures (http_error from a genuine 404).
        On blocked/network errors, ingest.fetch already retried with backoff; if all
        retries exhausted, raises RuntimeError so the caller can decide to skip/retry.
    """
    url = f'{_BASE}{ticker}?range={rng}&interval={interval}'
    result = ingest.fetch(url, source='yahoo', timeout=timeout)

    if not result.ok:
        if result.retryable:
            raise RuntimeError(f'yahoo fetch {ticker}: {result.status} after retries — {result.error}')
        # http_error (genuine 404 / not found) -> no data for this ticker
        return None

    raw = result.text
    # Save raw chart JSON before parsing (honesty rule: raw always preserved)
    safe_ticker = ticker.replace('/', '_').replace('%', 'pct')
    ingest.save_raw('yahoo', f'{safe_ticker}_{rng}.json', raw)

    data = json.loads(raw)
    res = (data.get('chart') or {}).get('result')
    if not res or not res[0].get('timestamp'):
        return None
    r = res[0]
    ts = r['timestamp']
    q = r['indicators']['quote'][0]
    bars = []
    for i, t in enumerate(ts):
        bars.append({'t': t, 'open': q['open'][i], 'high': q['high'][i],
                     'low': q['low'][i], 'close': q['close'][i], 'volume': q['volume'][i]})
    return bars
