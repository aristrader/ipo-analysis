"""NSE Public Issues API — IPO subscription split (gap G1a, MAINBOARD only).

Authoritative exchange source. Match is CONCRETE: we query by the NSE symbol we already hold
for the ISIN (from the official EQUITY_L list), so the bid data returned is for that exact security.
SME issues return 0.00 on NSE (not populated) → use ipowatch for SME instead.

API needs a primed browser session (curl_cffi chrome impersonation + cookie priming + Referer).
"""
from curl_cffi import requests as cr

_REFERER = 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'
_HDR = {'Referer': _REFERER, 'Accept': 'application/json'}


def prime_session():
    """Return a curl_cffi session with NSE anti-bot cookies set."""
    s = cr.Session(impersonate='chrome')
    s.get('https://www.nseindia.com', timeout=20)
    s.get(_REFERER, timeout=20)
    return s


def _num(x):
    try:
        v = float(str(x).replace(',', '').strip())
        return round(v, 2)
    except (ValueError, TypeError):
        return None


def fetch_subscription(session, symbol):
    """Return {sub_qib_x, sub_nii_x, sub_retail_x, sub_total_x} for an NSE mainboard symbol,
    or None if the symbol has no (non-zero) subscription data.

    Picks the aggregate category rows; ignores FII/MF/Corporate sub-rows and the later
    'Non Institutional Investors(Bid amount ...)' split rows.
    """
    r = session.get(f'https://www.nseindia.com/api/ipo-active-category?symbol={symbol}',
                    headers=_HDR, timeout=20)
    if r.status_code != 200:
        return None
    rows = r.json().get('dataList') or []
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
    # all-zero / empty means NSE didn't populate it (e.g. SME) — treat as no data
    if not any(v for v in out.values()):
        return None
    return out


if __name__ == '__main__':
    import csv, os, time
    os.makedirs('data/raw/nse', exist_ok=True)
    # target: mainboard rows lacking subscription, with an NSE symbol
    targets = []
    for r in csv.DictReader(open('data/master/_base_mainboard.csv')):
        if (r.get('sub_total_x') or '').strip():
            continue
        sym = (r.get('nse_symbol') or '').strip()
        if sym:
            targets.append({'isin': r['isin'], 'company': r['company_name'], 'symbol': sym})

    s = prime_session()
    out_rows, log_rows = [], []
    got = 0
    for i, t in enumerate(targets, 1):
        sub = None
        for attempt in range(3):
            try:
                sub = fetch_subscription(s, t['symbol']); break
            except Exception:
                time.sleep(1.0 * (attempt + 1))
                if attempt == 1:
                    s = prime_session()      # re-prime if the session went stale
        if sub:
            got += 1
            out_rows.append({'isin': t['isin'], **sub})
            log_rows.append({'isin': t['isin'], 'company': t['company'], 'symbol': t['symbol'], 'result': 'ok'})
        else:
            log_rows.append({'isin': t['isin'], 'company': t['company'], 'symbol': t['symbol'], 'result': 'no_data'})
        if i % 20 == 0 or i == len(targets):
            open('logs/nse_subscription_progress.txt', 'w').write(f"done={i}/{len(targets)} got={got}\n")
            print(f"  {i}/{len(targets)} got={got}", flush=True)
        time.sleep(0.3)

    with open('data/raw/nse/subscription.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin', 'sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x'])
        w.writeheader(); w.writerows(out_rows)
    with open('data/raw/nse/subscription_log.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['isin', 'company', 'symbol', 'result']); w.writeheader(); w.writerows(log_rows)
    print(f"\ntargets={len(targets)} got={got} → data/raw/nse/subscription.csv")
