"""NSE Corporate Actions API — splits + bonus for Layer 2 price adjustment.

Authoritative exchange source. We pull the full corporate-actions feed year-by-year
(2006..2025) for BOTH index=equities AND index=sme, keep only FACE VALUE SPLITS and
BONUS issues, parse them into a price multiplier (ratio_factor), and write a de-duped
reference table.

ratio_factor = how much a historical (pre-event) traded price must be DIVIDED by to be
comparable with a post-event price (equivalently, the multiplier of share count):
  SPLIT  "From Rs 10 To Rs 2"  -> faceVal_old / faceVal_new = 10/2 = 5.0
  BONUS  "Bonus a:b"           -> (a + b) / b   (a new shares for every b held)

API needs a primed browser session (curl_cffi chrome impersonation + cookie priming + Referer),
mirroring scrapers/nse_subscription.py. Re-prime on stale session / timeout.
"""
import os
import re
import sys
import time
from curl_cffi import requests as cr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scrapers dir, for `nse_session`
from nse_session import prime_nse_session

_REFERER = 'https://www.nseindia.com/companies-listing/corporate-filings-actions'
_HDR = {'Referer': _REFERER, 'Accept': 'application/json'}
_API = 'https://www.nseindia.com/api/corporates-corporateActions'


def prime_session():
    """Prime an NSE session for this scraper's Referer (logic in scrapers/nse_session.py)."""
    return prime_nse_session(_REFERER)


def fetch_year(session, index, year):
    """Fetch the full corporate-actions list for one calendar year and index.

    index: 'equities' or 'sme'. Returns the raw list of row dicts (may be empty).
    Raises on non-200 / non-JSON so the caller can retry / re-prime.
    """
    url = (f'{_API}?index={index}'
           f'&from_date=01-01-{year}&to_date=31-12-{year}')
    r = session.get(url, headers=_HDR, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f'HTTP {r.status_code} for {index} {year}')
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f'unexpected payload for {index} {year}: {type(data)}')
    return data


def classify(subject):
    """Return 'split', 'bonus', 'bonus+split', or None for a subject string.

    Some events combine a bonus AND a split in one ex-date (e.g.
    'Bonus 1:1 And Face Value Split From Rs.10 To Re.1'); the true price multiplier
    is the PRODUCT of the two factors, so they get their own type.
    """
    s = (subject or '').lower()
    has_bonus = 'bonus' in s
    has_split = 'split' in s or 'face value' in s
    if has_bonus and has_split:
        return 'bonus+split'
    if has_bonus:
        return 'bonus'
    if has_split:
        return 'split'
    return None


_RS = re.compile(r'(?:rs|re)\.?\s*([0-9]+(?:\.[0-9]+)?)', re.I)
# Also match a bare integer face value like '10/-' (no Rs/Re prefix),
# e.g. 'Face Value Split From 10/- To Face Value 2/-' (SHARONBIO).
_FV_BARE = re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*/[-–]', re.I)
# Widen to allow an optional dash/dash separator between 'Bonus' and the ratio,
# e.g. 'Bonus - 1:1' (HINDZINC) as well as the normal 'Bonus 4:1'.
_BONUS = re.compile(r'bonus\s*[-–]?\s*([0-9]+)\s*:\s*([0-9]+)', re.I)


def parse_split_factor(subject):
    """SPLIT: extract old and new face values -> old/new = price multiplier. Returns float or None.

    Primary: Rs/Re-prefixed values e.g. 'From Rs 10 To Rs 2' -> 10/2 = 5.0.
    Fallback: bare integer followed by /- e.g. '10/- To ... 2/-' -> also 5.0.
    This covers SHARONBIO ('Face Value Split From 10/- To Face Value 2/-').
    """
    nums = _RS.findall(subject or '')
    if len(nums) >= 2:
        old, new = float(nums[0]), float(nums[1])
        if old > 0 and new > 0:
            return round(old / new, 6)
    # Fallback: bare face-value tokens with /- suffix (no Rs/Re)
    bare = _FV_BARE.findall(subject or '')
    if len(bare) >= 2:
        old, new = float(bare[0]), float(bare[1])
        if old > 0 and new > 0:
            return round(old / new, 6)
    return None


def parse_bonus_factor(subject):
    """BONUS 'a:b' -> (a + b) / b. Returns float or None.

    'Bonus 4:1' (4 new for every 1 held) -> 5.0. Handles spaces e.g. 'Bonus 1: 1'.
    Also handles an optional separator before the ratio, e.g. 'Bonus - 1:1' (HINDZINC).
    Returns None for non-ratio "bonus" subjects (e.g. debenture scheme-of-arrangement).
    """
    m = _BONUS.search(subject or '')
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if b <= 0:
        return None
    return round((a + b) / b, 6)


_MONTHS = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
           'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}


def iso_date(d):
    """'21-Sep-2021' -> '2021-09-21'. Returns '' if unparseable."""
    d = (d or '').strip()
    m = re.match(r'(\d{1,2})-([A-Za-z]{3})-(\d{4})', d)
    if not m:
        return ''
    day, mon, yr = m.group(1), m.group(2).lower(), m.group(3)
    if mon not in _MONTHS:
        return ''
    return f'{yr}-{_MONTHS[mon]:02d}-{int(day):02d}'


def parse_row(row):
    """Turn a raw NSE row into an output record, or None if not a split/bonus we can parse."""
    subject = (row.get('subject') or '').strip()
    kind = classify(subject)
    if kind is None:
        return None
    if kind == 'split':
        factor = parse_split_factor(subject)
    elif kind == 'bonus':
        factor = parse_bonus_factor(subject)
    else:  # bonus+split: combined multiplier is the product of both legs
        bf = parse_bonus_factor(subject)
        sf = parse_split_factor(subject)
        # Both legs must parse; a missing leg is NOT a silent 1.0 — surface as parse-fail.
        if bf is None or sf is None:
            factor = None
        else:
            factor = round(bf * sf, 6)
    if factor is None:
        return None
    return {
        'isin': (row.get('isin') or '').strip(),
        'symbol': (row.get('symbol') or '').strip(),
        'action_type': kind,
        'raw_subject': subject,
        'ratio_factor': factor,
        'ex_date': iso_date(row.get('exDate')),
    }


if __name__ == '__main__':
    import csv
    import json
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from foundation import config, ingest

    config.ensure(config.reference_dir())
    config.ensure(config.logs_dir())
    LOG = open(config.logs_dir() / 'corp_actions.log', 'w')

    def log(msg):
        line = f'{time.strftime("%H:%M:%S")} {msg}'
        print(line, flush=True)
        LOG.write(line + '\n')
        LOG.flush()

    YEARS = list(range(2006, 2026))   # 2006..2025
    INDEXES = ['equities', 'sme']

    s = prime_session()
    log(f'primed session; pulling {len(YEARS)} years x {len(INDEXES)} indexes = '
        f'{len(YEARS) * len(INDEXES)} calls')

    records = []          # parsed split/bonus output rows
    failed = []           # (index, year) that never succeeded
    raw_counts = {}       # (index, year) -> raw row count

    for index in INDEXES:
        source = f'nse_corp_actions:{index}'
        for year in YEARS:
            rows = None
            for attempt in range(4):
                try:
                    rows = fetch_year(s, index, year)
                    break
                except Exception as e:
                    log(f'  retry {index} {year} attempt={attempt + 1} err={e}')
                    time.sleep(1.0 * (attempt + 1))
                    if attempt >= 1:
                        try:
                            s = prime_session()
                        except Exception as pe:
                            log(f'    re-prime failed: {pe}')
            if rows is None:
                failed.append((index, year))
                log(f'FAILED {index} {year}')
                continue

            raw_counts[(index, year)] = len(rows)
            # Save raw API payload so the file can be reprocessed offline (Rule 2).
            raw_name = f'corp_actions_{index}_{year}.json'
            ingest.save_raw('nse_corp_actions', raw_name, json.dumps(rows, ensure_ascii=False))
            kept = 0
            for row in rows:
                rec = parse_row(row)
                if rec is None:
                    continue
                rec['source'] = source
                records.append(rec)
                kept += 1
            log(f'{index} {year}: raw={len(rows)} kept={kept}')
            time.sleep(0.7)

    # de-dupe: same security + same ex_date + same action + same factor is one event.
    # Prefer keeping a row that has an ISIN over one that does not.
    by_key = {}
    for rec in records:
        key = (rec['isin'] or rec['symbol'], rec['symbol'], rec['action_type'],
               rec['ex_date'], rec['ratio_factor'])
        existing = by_key.get(key)
        if existing is None or (not existing['isin'] and rec['isin']):
            by_key[key] = rec
    deduped = list(by_key.values())
    deduped.sort(key=lambda r: (r['ex_date'], r['symbol'], r['action_type']))

    fields = ['isin', 'symbol', 'action_type', 'raw_subject',
              'ratio_factor', 'ex_date', 'source']
    with open(config.reference_dir() / 'corp_actions.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(deduped)

    n_split = sum(1 for r in deduped if r['action_type'] == 'split')
    n_bonus = sum(1 for r in deduped if r['action_type'] == 'bonus')
    n_isin = sum(1 for r in deduped if r['isin'])
    dates = [r['ex_date'] for r in deduped if r['ex_date']]
    span = f'{min(dates)} .. {max(dates)}' if dates else 'none'
    log(f'DONE total={len(deduped)} (pre-dedupe={len(records)}) '
        f'split={n_split} bonus={n_bonus} with_isin={n_isin} span={span} '
        f'failed={failed}')
    print(f'\n-> {config.reference_dir() / "corp_actions.csv"} '
          f'rows={len(deduped)} split={n_split} bonus={n_bonus} '
          f'with_isin={n_isin} span=[{span}] failed={failed}')
    LOG.close()
