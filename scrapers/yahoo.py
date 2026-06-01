"""Yahoo Finance daily chart fetcher.

Yahoo ticker conventions (matches what pipeline/04_verify.py produces):
  - NSE listing : <SYMBOL>.NS        e.g. ETERNAL.NS
  - BSE listing : <numeric code>.BO  e.g. 543982.BO   (NOT the alphabetic scrip_id)

fetch_chart() returns a list of daily bars or None when Yahoo has no data for the ticker.
Used by ticker validation (pipeline/06) and, later, Layer 2 price-history building.
"""
import json, urllib.request, urllib.error

_UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
_BASE = 'https://query1.finance.yahoo.com/v8/finance/chart/'


def fetch_chart(ticker, rng='1mo', interval='1d', timeout=20):
    """Fetch daily OHLCV bars for a Yahoo ticker.

    Args:
        ticker: Yahoo symbol, e.g. 'ETERNAL.NS' or '543982.BO'.
        rng: Yahoo range string ('5d','1mo','1y','max', ...).
        interval: bar size ('1d').
        timeout: socket timeout seconds.

    Returns:
        list of dicts {t,open,high,low,close,volume} (t = epoch seconds), or
        None if the ticker has no data on Yahoo.

    Raises:
        urllib.error.HTTPError / URLError on transport failures (caller retries).
    """
    url = f'{_BASE}{ticker}?range={rng}&interval={interval}'
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
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
