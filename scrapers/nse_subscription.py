"""NSE Public Issues API — IPO subscription split (gap G1a, MAINBOARD only).

Authoritative exchange source. Match is CONCRETE: we query by the NSE symbol we already hold
for the ISIN (from the official EQUITY_L list), so the bid data returned is for that exact security.
SME issues return 0.00 on NSE (not populated) → use ipowatch for SME instead.

API needs a primed browser session (curl_cffi chrome impersonation + cookie priming + Referer).

Result codes (in the per-ISIN log):
  ok           — fetched + parsed; non-zero subscription values returned.
  no_nse_data  — fetch succeeded (HTTP 200) but NSE returned all-zero / empty dataList.
  fetch_error  — HTTP non-200 or exception; data unavailable; should be retried later.
"""
import json
import os
import sys
from curl_cffi import requests as cr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scrapers dir, for `nse_session`
from nse_session import prime_nse_session

# Foundation helpers: config (output paths) + ingest (save_raw).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

_REFERER = 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
_HDR = {'Referer': _REFERER, 'Accept': 'application/json'}
_SOURCE = 'nse'


def prime_session():
    """Prime an NSE session for this scraper's Referer (logic in scrapers/nse_session.py)."""
    return prime_nse_session(_REFERER)


def _num(x):
    try:
        v = float(str(x).replace(',', '').strip())
        return round(v, 2)
    except (ValueError, TypeError):
        return None


def _parse_subscription_rows(rows):
    """Extract {sub_qib_x, sub_nii_x, sub_retail_x, sub_total_x} from NSE dataList rows.

    Pure function — no I/O, no network calls. Returns the dict (values may be None).
    """
    out = {'sub_qib_x': None, 'sub_nii_x': None, 'sub_retail_x': None, 'sub_total_x': None}
    for row in rows:
        cat = (row.get('category') or '').strip()
        val = _num(row.get('noOfTotalMeant'))
        if val is None:
            continue
        if cat.startswith('Qualified Institutional Buyers'):
            out['sub_qib_x'] = val
        elif cat == 'Non Institutional Investors':
            out['sub_nii_x'] = val
        elif cat.startswith('Retail Individual Investors'):
            out['sub_retail_x'] = val
        elif cat == 'Total':
            out['sub_total_x'] = val
    return out


def fetch_subscription(session, symbol):
    """Fetch subscription data for an NSE mainboard symbol.

    Returns a dict with keys:
      result        — 'ok' | 'no_nse_data' | 'fetch_error'
      sub_qib_x, sub_nii_x, sub_retail_x, sub_total_x  — present and non-None only on 'ok'

    Distinguishes three outcomes:
      ok           — HTTP 200, dataList has at least one non-zero subscription value.
      no_nse_data  — HTTP 200 but dataList is all-zero or empty (NSE never populated it, e.g. SME).
      fetch_error  — non-200 HTTP status or an exception (transient; should be retried).

    Raw API JSON is saved via ingest.save_raw before parsing.
    """
    url = f'https://www.nseindia.com/api/ipo-active-category?symbol={symbol}'
    try:
        r = session.get(url, headers=_HDR, timeout=20)
    except Exception as exc:
        return {'result': 'fetch_error', 'error': str(exc)}

    if r.status_code != 200:
        return {'result': 'fetch_error', 'http_status': r.status_code}

    # Save raw JSON before parsing — the root-cause fix so we can reprocess offline.
    ingest.save_raw(_SOURCE, f'{symbol}.json', r.text)

    data = r.json()
    rows = data.get('dataList') or []
    parsed = _parse_subscription_rows(rows)

    # all-zero / empty → NSE didn't populate it (e.g. SME, or window closed)
    if not any(v for v in parsed.values()):
        return {'result': 'no_nse_data'}

    return {'result': 'ok', **parsed}


if __name__ == '__main__':
    import csv, time
    config.ensure(config.raw_dir(_SOURCE))
    config.ensure(config.logs_dir())
    # target: mainboard rows lacking subscription, with an NSE symbol
    targets = []
    base_path = config.src('master', '_base_mainboard.csv')
    for r in csv.DictReader(open(base_path)):
        if (r.get('sub_total_x') or '').strip():
            continue
        sym = (r.get('nse_symbol') or '').strip()
        if sym:
            targets.append({'isin': r['isin'], 'company': r['company_name'], 'symbol': sym})

    s = prime_session()
    out_rows, log_rows = [], []
    got = 0
    for i, t in enumerate(targets, 1):
        fetch_result = None
        for attempt in range(3):
            try:
                fetch_result = fetch_subscription(s, t['symbol'])
                if fetch_result['result'] != 'fetch_error':
                    break
            except Exception:
                pass
            time.sleep(1.0 * (attempt + 1))
            if attempt == 1:
                s = prime_session()      # re-prime if the session went stale

        result_code = (fetch_result or {}).get('result', 'fetch_error')
        if result_code == 'ok':
            got += 1
            out_rows.append({
                'isin': t['isin'],
                'sub_qib_x': fetch_result.get('sub_qib_x'),
                'sub_nii_x': fetch_result.get('sub_nii_x'),
                'sub_retail_x': fetch_result.get('sub_retail_x'),
                'sub_total_x': fetch_result.get('sub_total_x'),
            })
        log_rows.append({
            'isin': t['isin'], 'company': t['company'],
            'symbol': t['symbol'], 'result': result_code,
        })
        if i % 20 == 0 or i == len(targets):
            (config.logs_dir() / 'nse_subscription_progress.txt').write_text(
                f"done={i}/{len(targets)} got={got}\n")
            print(f"  {i}/{len(targets)} got={got}", flush=True)
        time.sleep(0.3)

    out_csv = config.raw_dir(_SOURCE) / 'subscription.csv'
    log_csv = config.raw_dir(_SOURCE) / 'subscription_log.csv'
    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin', 'sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x'])
        w.writeheader(); w.writerows(out_rows)
    with open(log_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin', 'company', 'symbol', 'result'])
        w.writeheader(); w.writerows(log_rows)
    print(f"\ntargets={len(targets)} got={got} → {out_csv}")
