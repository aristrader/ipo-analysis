"""STEP 3+4: recompute returns_summary rows from screener WEEKLY adjusted series for the
listing-era-gap fix set, then MERGE into data/master/returns_summary.csv.

Mirrors pipeline/07_returns_summary.py compute() definitions exactly, adapted for:
  - WEEKLY data (volatility annualized with sqrt(52); turnover = close*weekly_volume = weekly turnover)
  - screener prices already split/bonus adjusted (NO corp-action adjustment)
  - circuit_lock_frac left blank (N/A for weekly)
  - listing_open == listing_close (weekly: single weekly close near listing; we set both to the
    first weekly close on/after listing_date — there is no intraday open/high/low in the chart API,
    so all_time_high/low are computed from weekly closes)

Adds/maintains column `price_source`:
  bhavcopy_daily  — untouched existing rows
  screener_weekly — fix-set rows recomputed from screener
  none_listing_era— fix-set rows screener could NOT resolve; listing-anchored columns NULLed
                    (so no wrong values remain), issue-anchored / current metrics kept from the
                    original bhavcopy row IF those used data we can trust... but original bhavcopy
                    current/issue metrics were also computed off the wrong late-start series.
                    For none rows we keep ONLY issue_price/listing_date/type/company_name and the
                    original current_price/current_return_from_issue/outcome_class (best available),
                    and NULL every listing-anchored field per spec.

Run: PYTHONPATH=. .venv/bin/python scrapers/screener_prices_merge.py
"""
import csv, os, sys, math, statistics
from datetime import datetime, date, timedelta
from bisect import bisect_right

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))  # so listing_remediation imports
sys.path.insert(0, ROOT)                            # so layer3.config imports
from listing_remediation import remediate_listing
from layer3 import config as _l3cfg
SP_DIR = os.path.join(ROOT, 'data/raw/screener_prices')
RS_PATH = os.path.join(ROOT, 'data/master/returns_summary.csv')
TODAY = _l3cfg.AS_OF_DATE   # single canonical as-of date (was a hardcoded copy of it — drift-prone)

HORIZONS = [
    ('1d', 1), ('1w', 7), ('1m', 30), ('3m', 91), ('6m', 182),
    ('1y', 365), ('2y', 730), ('3y', 1095), ('5y', 1825), ('10y', 3650),
]
WIPEOUT_REASON_KEYS = ('compulsory', 'liquidation', 'penny', 'suspend')

# recovered BSE-bhavcopy listing day (shared with pipeline/07) — authoritative listing
# metrics for stocks whose (weekly) series lacks a reliable listing day.
LISTING_OVERRIDE = {}

def load_listing_override():
    path = os.path.join(ROOT, 'data/reference/listing_day_recovered.csv')
    d = {}
    if not os.path.exists(path):
        return d
    for r in csv.DictReader(open(path)):
        isin = (r.get('isin') or '').strip()
        try:
            o = float(r.get('open')); c = float(r.get('close')) if r.get('close') else o
        except (TypeError, ValueError):
            continue
        if isin:
            d[isin] = {'open': o, 'close': c}
    return d

# listing-anchored columns to NULL for none_listing_era rows
LISTING_ANCHORED = ['listing_open', 'listing_close', 'listing_gain_open', 'listing_gain_close']
for label, _ in HORIZONS:
    LISTING_ANCHORED += [f'return_from_listing_{label}', f'alpha_{label}']


def pdate(s):
    s = (s or '').strip()
    if not s:
        return None
    for f in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def pfloat(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_masters():
    m = {}
    for f in ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']:
        path = os.path.join(ROOT, 'data/master', f + '.csv')
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            isin = (r.get('isin') or '').strip()
            if not isin or isin in m:
                continue
            m[isin] = {
                'issue_price': pfloat(r.get('issue_price')),
                'listing_date': pdate(r.get('listing_date')),
                'type': (r.get('type') or '').strip(),
                'company_name': (r.get('company_name') or '').strip(),
                'nse_symbol': (r.get('nse_symbol') or '').strip(),
                'chittor_listing_open': pfloat(r.get('listing_open')),
                'chittor_listing_close': pfloat(r.get('listing_close')),
            }
    return m


def load_corp_actions():
    """Return (by_isin, by_symbol): isin/symbol -> list of (ex_date, ratio_factor).
    A face-value split often changes the ISIN, so match by NSE symbol too."""
    by_isin, by_symbol = {}, {}
    path = os.path.join(ROOT, 'data/reference/corp_actions.csv')
    for r in csv.DictReader(open(path)):
        isin = (r.get('isin') or '').strip()
        sym = (r.get('symbol') or '').strip().upper()
        rf = pfloat(r.get('ratio_factor'))
        ex = pdate(r.get('ex_date'))
        if rf is None or ex is None or rf == 0:
            continue
        if isin:
            by_isin.setdefault(isin, []).append((ex, rf))
        if sym:
            by_symbol.setdefault(sym, []).append((ex, rf))
    return by_isin, by_symbol


def adj_factor_after(isin, nse_symbol, listing_date, by_isin, by_symbol):
    """Product of ratio_factor (dedup by (ex_date,ratio_factor)) for this stock's
    actions matched by ISIN OR NSE symbol with ex_date > listing_date."""
    seen = set()
    factor = 1.0
    for src in (by_isin.get(isin) or [],
                by_symbol.get((nse_symbol or '').strip().upper()) or []):
        for ex, rf in src:
            key = (ex, rf)
            if key in seen:
                continue
            seen.add(key)
            if listing_date is not None and ex > listing_date:
                factor *= rf
    return factor


def load_delisting():
    d = {}
    path = os.path.join(ROOT, 'data/master/delisting.csv')
    for r in csv.DictReader(open(path)):
        isin = (r.get('isin') or '').strip()
        if not isin:
            continue
        d[isin] = {
            'status': (r.get('status') or '').strip().lower(),
            'delist_date': pdate(r.get('delist_date')),
            'reason': (r.get('reason') or '').strip(),
            'last_price': pfloat(r.get('last_price')),
        }
    return d


def load_nifty():
    path = os.path.join(ROOT, 'data/reference/indices/nifty50.csv')
    pairs = []
    for r in csv.DictReader(open(path)):
        dt = pdate(r.get('date'))
        c = pfloat(r.get('close'))
        if dt is not None and c is not None:
            pairs.append((dt, c))
    pairs.sort()
    return [p[0] for p in pairs], [p[1] for p in pairs]


def nearest_on_or_before(dates, closes, target):
    i = bisect_right(dates, target) - 1
    if i < 0:
        return None
    return closes[i]


def load_screener_series(isin):
    """list of dicts {date, c, v} sorted, from data/raw/screener_prices/<isin>.csv."""
    path = os.path.join(SP_DIR, isin + '.csv')
    if not os.path.exists(path):
        return []
    rows = []
    for r in csv.DictReader(open(path)):
        dt = pdate(r.get('date'))
        c = pfloat(r.get('close'))
        v = pfloat(r.get('volume'))
        if dt is None or c is None:
            continue
        rows.append({'date': dt, 'c': c, 'v': v})
    rows.sort(key=lambda x: x['date'])
    return rows


def compute_weekly(isin, mrow, prices, deli, nd, nc, by_isin, by_symbol):
    """Mirror pipeline/07 compute() on weekly adjusted closes."""
    out = {'isin': isin, 'type': mrow['type'], 'price_source': 'screener_weekly'}
    issue_price = mrow['issue_price']
    listing_date = mrow['listing_date']
    # screener prices are already split/bonus adjusted to the current scale, so
    # the RAW issue_price must be divided by the post-listing adjustment factor
    # (matched by ISIN or NSE symbol) to compare on the same scale.
    adj_issue = issue_price
    if issue_price is not None and listing_date is not None:
        adj_issue = issue_price / adj_factor_after(
            isin, mrow.get('nse_symbol'), listing_date, by_isin, by_symbol)
    n = len(prices)
    out['n_days_history'] = n
    if n == 0 or listing_date is None:
        return None

    pdates = [p['date'] for p in prices]
    pclose = [p['c'] for p in prices]

    di = deli.get(isin, {})
    status = di.get('status', '')
    delist_date = di.get('delist_date')
    reason = di.get('reason', '')
    deli_last = di.get('last_price')
    is_delisted = status in ('delisted', 'suspended')

    terminal = None
    if is_delisted:
        rl = reason.lower()
        if any(k in rl for k in WIPEOUT_REASON_KEYS):
            terminal = 0.0
        else:
            terminal = pclose[-1]
            if terminal is None and deli_last is not None:
                terminal = deli_last  # screener adjusted; no further adjustment
    out['delisted'] = is_delisted
    out['delist_reason'] = reason
    eff_delist = delist_date if (is_delisted and delist_date) else (pdates[-1] if is_delisted else None)

    out['issue_price'] = issue_price        # RAW (for display)
    out['issue_price_adj'] = adj_issue      # split-adjusted to current scale
    # first weekly point on/after listing_date
    li = bisect_right(pdates, listing_date - timedelta(days=1))
    listing_close = listing_open = None
    if li < n:
        listing_close = prices[li]['c']
        listing_open = prices[li]['c']  # weekly: no separate open
    out['listing_close'] = listing_close
    out['listing_open'] = listing_open

    data_first = pdates[0]
    data_last = pdates[-1]

    def price_at_horizon(target):
        if is_delisted and eff_delist is not None and eff_delist < target:
            return terminal, True
        if target > TODAY:
            return None, False
        if target < data_first:
            return None, True
        val = nearest_on_or_before(pdates, pclose, target)
        if target > data_last:
            return None, True
        return val, True

    nifty_base = nearest_on_or_before(nd, nc, listing_date)
    for label, days in HORIZONS:
        target = listing_date + timedelta(days=days)
        val, _ = price_at_horizon(target)
        rfi = rfl = alpha = None
        if val is not None:
            if adj_issue:
                rfi = val / adj_issue - 1
            if listing_close:
                rfl = val / listing_close - 1
                nt = nearest_on_or_before(nd, nc, target)
                if nifty_base and nt and rfl is not None:
                    alpha = rfl - (nt / nifty_base - 1)
        out['return_from_issue_%s' % label] = rfi
        out['return_from_listing_%s' % label] = rfl
        out['alpha_%s' % label] = alpha

    out['listing_gain_open'] = (listing_open / adj_issue - 1) if (listing_open and adj_issue) else None
    out['listing_gain_close'] = (listing_close / adj_issue - 1) if (listing_close and adj_issue) else None

    # within-horizon peak/trough (MFE/MAE) from WEEKLY CLOSES. The chart API has no intraday H/L, so
    # this is a WEEKLY-CLOSE-resolution peak/trough — coarser than the bhavcopy-daily MFE/MAE, but
    # consistent with the weekly-close returns above (so the same source feeds both, and the invariant
    # peak>=endpoint>=trough holds). Same coverage gate as the endpoint; clamped to bracket the
    # endpoint return (handles forced-wipeout terminals and any data spikes uniformly).
    for label, days in HORIZONS:
        if label not in ('1y', '3y', '5y'):
            continue
        end = listing_date + timedelta(days=days)
        mature = is_delisted or (end <= TODAY and end <= data_last)
        mfe = mae = mfe_lst = mae_lst = None
        days_to_mfe = days_to_mae = days_to_be = None
        if mature:
            wp = [(pdates[i], prices[i]['c']) for i in range(n)
                  if listing_date <= pdates[i] <= end and prices[i]['c'] is not None]
            if wp:
                pk = max(wp, key=lambda x: x[1]); hi = pk[1]; days_to_mfe = (pk[0] - listing_date).days
                tr = min(wp, key=lambda x: x[1]); lo = tr[1]; days_to_mae = (tr[0] - listing_date).days
                if adj_issue:
                    mfe, mae = hi / adj_issue - 1, lo / adj_issue - 1
                    be = next((d for d, c in wp if c >= adj_issue), None)
                    if be is not None:
                        days_to_be = (be - listing_date).days
                if listing_close:
                    mfe_lst, mae_lst = hi / listing_close - 1, lo / listing_close - 1
        rfi_e = out.get('return_from_issue_%s' % label)
        rfl_e = out.get('return_from_listing_%s' % label)
        if rfi_e is not None:                     # endpoint price is within the window by definition
            if mfe is not None: mfe = max(mfe, rfi_e)
            if mae is not None: mae = min(mae, rfi_e)
        if rfl_e is not None:
            if mfe_lst is not None: mfe_lst = max(mfe_lst, rfl_e)
            if mae_lst is not None: mae_lst = min(mae_lst, rfl_e)
        out['mfe_%s' % label] = mfe
        out['mae_%s' % label] = mae
        out['mfe_lst_%s' % label] = mfe_lst
        out['mae_lst_%s' % label] = mae_lst
        out['days_to_mfe_%s' % label] = days_to_mfe
        out['days_to_mae_%s' % label] = days_to_mae
        out['days_to_breakeven_%s' % label] = days_to_be

    # weekly closes used for ATH/ATL (no intraday H/L in chart API)
    ath = max(pclose) if pclose else None
    atl = min(pclose) if pclose else None
    out['all_time_high'] = ath
    out['all_time_low'] = atl
    out['max_gain_pct'] = (ath / adj_issue - 1) if (ath and adj_issue) else None

    peak = None; peak_date = None; mdd = 0.0; mdd_dur = 0
    for p in prices:
        c = p['c']
        if c is None:
            continue
        if peak is None or c > peak:
            peak = c; peak_date = p['date']
        if peak and peak > 0:
            dd = c / peak - 1
            if dd < mdd:
                mdd = dd; mdd_dur = (p['date'] - peak_date).days
    out['max_drawdown_pct'] = mdd if prices else None
    out['max_drawdown_duration_days'] = mdd_dur if prices else None

    current_price = terminal if (is_delisted and terminal is not None) else pclose[-1]
    out['current_price'] = current_price
    out['current_return_from_issue'] = (current_price / adj_issue - 1) if (current_price is not None and adj_issue) else None

    # weekly returns -> annualize with sqrt(52)
    rets = []
    prev = None
    for p in prices:
        c = p['c']
        if c is None or c <= 0:
            prev = c; continue
        if prev is not None and prev > 0:
            rets.append(c / prev - 1)
        prev = c
    out['volatility_annual'] = (statistics.stdev(rets) * math.sqrt(52)) if len(rets) >= 2 else None

    # weekly turnover = close * weekly volume
    turnovers = [p['c'] * p['v'] for p in prices if p['c'] is not None and p['v'] is not None]
    out['median_daily_turnover_inr'] = statistics.median(turnovers) if turnovers else None

    out['circuit_lock_frac'] = None  # N/A for weekly
    med_turn = out['median_daily_turnover_inr']
    out['liquidity_flag'] = 'low' if (med_turn is not None and med_turn < 1e6) else 'ok'

    cr = out['current_return_from_issue']
    if cr is None:
        oc = None
    elif cr <= -0.90:
        oc = 'wipeout'
    elif cr < -0.20:
        oc = 'loser'
    elif cr < 0.20:
        oc = 'flat'
    elif cr < 1.00:
        oc = 'winner'
    else:
        oc = 'multibagger'
    out['outcome_class'] = oc

    # ---- FIX 2: listing-coverage remediation (unrecorded split / bad coverage)
    out['listing_metrics_status'] = remediate_listing(
        out,
        chittor_listing_open=mrow.get('chittor_listing_open'),
        chittor_listing_close=mrow.get('chittor_listing_close'),
        has_action=(isin in by_isin)
                   or ((mrow.get('nse_symbol') or '').strip().upper() in by_symbol),
        listing_date=listing_date,
        data_first=data_first,
        price_source='screener_weekly',
        horizons=HORIZONS,
        recovered=LISTING_OVERRIDE.get(isin),
    )

    out['company_name'] = mrow['company_name']
    out['listing_date'] = mrow['listing_date'].isoformat() if mrow['listing_date'] else ''
    return out


def main():
    global LISTING_OVERRIDE
    LISTING_OVERRIDE = load_listing_override()
    masters = load_masters()
    deli = load_delisting()
    nd, nc = load_nifty()
    ca_by_isin, ca_by_symbol = load_corp_actions()

    # existing rows + header
    with open(RS_PATH) as fh:
        rd = csv.DictReader(fh)
        orig_cols = rd.fieldnames[:]
        rows = {r['isin']: r for r in rd}

    # fix set = same definition as scraper
    sys.path.insert(0, os.path.join(ROOT, 'scrapers'))
    import screener_prices as sp
    fixset = sp.build_fixset()

    # which fix-set ISINs have a screener series (resolved) vs not
    resolved = {i for i in fixset if os.path.exists(os.path.join(SP_DIR, i + '.csv'))}
    unresolved = [i for i in fixset if i not in resolved]

    new_cols = orig_cols[:]
    if 'listing_metrics_status' not in new_cols:
        new_cols.append('listing_metrics_status')
    if 'price_source' not in new_cols:
        new_cols.append('price_source')

    n_screener = n_none = 0
    for isin in fixset:
        if isin not in rows:
            continue
        mrow = masters.get(isin)
        if isin in resolved and mrow:
            prices = load_screener_series(isin)
            res = compute_weekly(isin, mrow, prices, deli, nd, nc, ca_by_isin, ca_by_symbol)
            if res is not None and res.get('listing_open') is not None:
                # build full row dict (str) from res
                rows[isin] = {c: '' for c in new_cols}
                rows[isin]['isin'] = isin
                for k, v in res.items():
                    if k in new_cols:
                        rows[isin][k] = fmt(v)
                rows[isin]['price_source'] = 'screener_weekly'
                n_screener += 1
                continue
        # unresolved OR resolved-but-no-listing-point -> none_listing_era: NULL listing-anchored
        r = rows[isin]
        # ...unless we have a recovered BSE-bhavcopy listing day for it (authoritative)
        ov = LISTING_OVERRIDE.get(isin)
        if ov:
            try:
                iss = float(r.get('issue_price') or 0) or None
                iss_adj = float(r.get('issue_price_adj') or 0) or iss
            except (TypeError, ValueError):
                iss = iss_adj = None
            factor = (iss / iss_adj) if (iss and iss_adj) else 1.0
            lo, lc = ov['open'], ov['close']
            r['listing_open'] = fmt(lo / factor)
            r['listing_close'] = fmt(lc / factor)
            r['listing_gain_open'] = fmt((lo / iss - 1) if (lo and iss) else None)
            r['listing_gain_close'] = fmt((lc / iss - 1) if (lc and iss) else None)
            r['listing_metrics_status'] = 'recovered_bhavcopy'
            if not r.get('price_source'):
                r['price_source'] = 'none_listing_era'
            continue
        for col in LISTING_ANCHORED:
            if col in r:
                r[col] = ''
        r['price_source'] = 'none_listing_era'
        if 'listing_metrics_status' in r:
            r['listing_metrics_status'] = 'unreliable_coverage'
        n_none += 1

    # everything not in fixset = bhavcopy_daily
    for isin, r in rows.items():
        if 'price_source' not in r or not r.get('price_source'):
            r['price_source'] = 'bhavcopy_daily'

    # write back, preserving original isin sort order
    isins_sorted = sorted(rows.keys())
    with open(RS_PATH, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=new_cols, extrasaction='ignore')
        w.writeheader()
        for isin in isins_sorted:
            row = {c: rows[isin].get(c, '') for c in new_cols}
            w.writerow(row)

    print(f"fixset={len(fixset)} resolved_files={len(resolved)} unresolved={len(unresolved)}")
    print(f"merged: screener_weekly={n_screener} none_listing_era={n_none}")
    print(f"output: {RS_PATH}")


def fmt(v):
    if v is None:
        return ''
    if isinstance(v, bool):
        return 'True' if v else 'False'
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ''
        return repr(round(v, 6))
    return str(v)


if __name__ == '__main__':
    main()
