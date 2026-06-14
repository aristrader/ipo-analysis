"""Phase 7: build data/master/returns_summary.csv — one row per IPO of
price-derived OUTCOMES (horizon returns, lifetime stats, risk/liquidity, class).

READ-ONLY on master CSVs and data/prices. Builds a fresh summary only.

Inputs:
  data/prices/<isin>.csv                       raw daily OHLCV
  data/reference/corp_actions_merged.csv       splits/bonus (ratio_factor to DIVIDE by)
  data/reference/indices/nifty50.csv           benchmark
  data/master/delisting.csv                    delisting status/date/reason/last_price
  data/master/{mainboard,sme,longterm_mainboard,longterm_sme}.csv
                                               isin -> issue_price, listing_date, type, name

Output: data/master/returns_summary.csv

Run: PYTHONPATH=. .venv/bin/python pipeline/07_returns_summary.py [--test]
"""
import csv, os, sys, math, statistics
from datetime import date, timedelta
from bisect import bisect_right

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # so listing_remediation imports
sys.path.insert(0, ROOT)                                        # so layer3.config imports
from listing_remediation import remediate_listing, _outcome_class
from layer3 import config as _l3cfg
PRICES_DIR = os.path.join(ROOT, 'data/prices')
TODAY = _l3cfg.AS_OF_DATE     # canonical as-of/build date (single source; was date(2026,5,31))

HORIZONS = [
    ('1d', 1), ('1w', 7), ('1m', 30), ('3m', 91), ('6m', 182),
    ('1y', 365), ('2y', 730), ('3y', 1095), ('5y', 1825), ('10y', 3650),
]

WIPEOUT_REASON_KEYS = ('compulsory', 'liquidation', 'penny', 'suspend')

# module globals populated in main():
LISTING_OVERRIDE = {}        # isin -> {'open':float, 'close':float}  (recovered BSE bhavcopy listing day)
SC_DATES, SC_CLOSES = [], []  # Nifty Smallcap 250 benchmark (2017-04-03+)


def pdate(s):
    s = (s or '').strip()
    if not s:
        return None
    for fmt_try in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt_try).date()
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


# ---------------------------------------------------------------- load masters
def load_masters():
    """isin -> {issue_price, listing_date, type, company_name}. First file wins
    (mainboard/sme are the richer current files; longterm fills older listings)."""
    m = {}
    for f in ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']:
        path = os.path.join(ROOT, 'data/master', f + '.csv')
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
                'bse_script_code': (r.get('bse_script_code') or '').strip(),
                # Chittorgarh RAW listing quote (for the listing-coverage remediation, FIX 2)
                'chittor_listing_open': pfloat(r.get('listing_open')),
                'chittor_listing_close': pfloat(r.get('listing_close')),
            }
    return m


# ---------------------------------------------------------------- corp actions
def load_corp_actions():
    """Return (by_isin, by_symbol):
      by_isin:   isin             -> list of (ex_date, ratio_factor)
      by_symbol: NSE symbol upper -> list of (ex_date, ratio_factor)
    A face-value split often changes the ISIN, so the corp-action ISIN no
    longer matches the current/universe ISIN; matching by NSE symbol recovers
    these. Both lookups are returned so the caller can take the union."""
    by_isin, by_symbol = {}, {}
    path = os.path.join(ROOT, 'data/reference/corp_actions_merged.csv')
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


def actions_for(isin, nse_symbol, by_isin, by_symbol):
    """Union (dedup by (ex_date, ratio_factor)) of actions matched by ISIN and
    by NSE symbol (uppercased)."""
    seen = set()
    out = []
    for src in (by_isin.get(isin) or [],
                by_symbol.get((nse_symbol or '').strip().upper()) or []):
        for ex, rf in src:
            key = (ex, rf)
            if key in seen:
                continue
            seen.add(key)
            out.append((ex, rf))
    return out


# ---------------------------------------------------------------- delisting
def load_delisting():
    """isin -> {status, delist_date, reason, last_price}."""
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


# ---------------------------------------------------------------- nifty
def load_nifty():
    path = os.path.join(ROOT, 'data/reference/indices/nifty50.csv')
    dates, closes = [], []
    for r in csv.DictReader(open(path)):
        dt = pdate(r.get('date'))
        c = pfloat(r.get('close'))
        if dt is None or c is None:
            continue
        dates.append(dt)
        closes.append(c)
    # ensure sorted by date
    pairs = sorted(zip(dates, closes))
    dates = [p[0] for p in pairs]
    closes = [p[1] for p in pairs]
    return dates, closes


def nearest_on_or_before(dates, closes, target):
    """close on the last trading day <= target. None if before series start."""
    i = bisect_right(dates, target) - 1
    if i < 0:
        return None
    return closes[i]


def load_smallcap():
    """Nifty Smallcap 250 daily close (2017-04-03+). Secondary benchmark for small/micro."""
    path = os.path.join(ROOT, 'data/reference/indices/niftysmallcap250.csv')
    dates, closes = [], []
    if not os.path.exists(path):
        return dates, closes
    for r in csv.DictReader(open(path)):
        dt = pdate(r.get('date')); c = pfloat(r.get('close'))
        if dt is None or c is None:
            continue
        dates.append(dt); closes.append(c)
    pairs = sorted(zip(dates, closes))
    return [p[0] for p in pairs], [p[1] for p in pairs]


def load_listing_override():
    """isin -> recovered BSE-bhavcopy listing-day open/close, for stocks whose price
    series lacks reliable listing-day coverage (none_listing_era / no-file). Used for
    LISTING METRICS ONLY — never injected into the horizon price series."""
    path = os.path.join(ROOT, 'data/reference/listing_day_recovered.csv')
    d = {}
    if not os.path.exists(path):
        return d
    for r in csv.DictReader(open(path)):
        isin = (r.get('isin') or '').strip()
        o = pfloat(r.get('open')); c = pfloat(r.get('close'))
        if isin and o is not None:
            d[isin] = {'open': o, 'close': c if c is not None else o}
    return d


# ---------------------------------------------------------------- prices
def load_prices(isin, actions):
    """Return list of dicts sorted by date with adjusted open/high/low/close,
    raw close & volume. actions = list of (ex_date, ratio_factor)."""
    path = os.path.join(PRICES_DIR, isin + '.csv')
    rows = []
    for r in csv.DictReader(open(path)):
        dt = pdate(r.get('date'))
        if dt is None:
            continue
        o = pfloat(r.get('open')); h = pfloat(r.get('high'))
        lo = pfloat(r.get('low')); c = pfloat(r.get('close'))
        v = pfloat(r.get('volume'))
        if c is None:
            continue
        rows.append({'date': dt, 'o': o, 'h': h, 'l': lo, 'c': c, 'v': v,
                     'raw_c': c})  # raw close preserved for turnover
    rows.sort(key=lambda x: x['date'])
    # adjustment: divide pre-event prices by product of ratio_factor for
    # actions with ex_date > date[t]
    acts = sorted(actions or [], key=lambda x: x[0])
    for row in rows:
        factor = 1.0
        for ex, rf in acts:
            if ex > row['date']:
                factor *= rf
        if factor != 1.0:
            for k in ('o', 'h', 'l', 'c'):
                if row[k] is not None:
                    row[k] = row[k] / factor
    return rows


# ---------------------------------------------------------------- per-isin calc
def adj_factor_after(actions, dt):
    """product of ratio_factor for actions with ex_date > dt (to adjust a raw
    price observed at/at-around dt onto the current adjusted scale)."""
    factor = 1.0
    for ex, rf in (actions or []):
        if ex > dt:
            factor *= rf
    return factor


def _terminal_state(isin, deli, actions, pdates, pclose):
    """Delisting status + the (adjusted) terminal value used for horizons AFTER delisting.
    Returns (is_delisted, reason, terminal, eff_delist). Extracted verbatim from compute()."""
    status = deli.get(isin, {}).get('status', '') if deli.get(isin) else ''
    delist_date = deli.get(isin, {}).get('delist_date') if deli.get(isin) else None
    reason = deli.get(isin, {}).get('reason', '') if deli.get(isin) else ''
    deli_last = deli.get(isin, {}).get('last_price') if deli.get(isin) else None
    is_delisted = status in ('delisted', 'suspended')

    # terminal value (adjusted) used for any horizon AFTER delisting
    terminal = None
    if is_delisted:
        rl = reason.lower()
        if any(k in rl for k in WIPEOUT_REASON_KEYS):
            terminal = 0.0
        else:
            # last adjusted close, fall back to delisting.last_price (adjusted to
            # current scale by dividing by product of post-date actions)
            terminal = pclose[-1]
            if terminal is None and deli_last is not None:
                ref_dt = delist_date or pdates[-1]
                terminal = deli_last / adj_factor_after(actions, ref_dt)

    # effective delist date for horizon logic: explicit date else last price day
    eff_delist = delist_date if (is_delisted and delist_date) else (pdates[-1] if is_delisted else None)
    return is_delisted, reason, terminal, eff_delist


def _horizon_returns(out, price_at_horizon, listing_date, adj_issue, listing_close,
                     nifty_dates, nifty_closes, nifty_base, sc_base):
    """Endpoint return + alpha at every HORIZON -> return_from_issue_* / return_from_listing_* /
    alpha_* / alpha_sc_*. Extracted verbatim from compute()."""
    for label, days in HORIZONS:
        target = listing_date + timedelta(days=days)
        val, _mature = price_at_horizon(target)
        rfi = rfl = alpha = alpha_sc = None
        if val is not None:
            if adj_issue:
                rfi = val / adj_issue - 1
            if listing_close:
                rfl = val / listing_close - 1
                nb = nifty_base
                nt = nearest_on_or_before(nifty_dates, nifty_closes, target)
                if nb and nt and rfl is not None:
                    bench = nt / nb - 1
                    alpha = rfl - bench
                # Smallcap-250 alpha (only where the index covers the listing date, 2017+)
                if sc_base and rfl is not None:
                    sct = nearest_on_or_before(SC_DATES, SC_CLOSES, target)
                    if sct:
                        alpha_sc = rfl - (sct / sc_base - 1)
        out['return_from_issue_%s' % label] = rfi
        out['return_from_listing_%s' % label] = rfl
        out['alpha_%s' % label] = alpha
        out['alpha_sc_%s' % label] = alpha_sc


def _mfe_mae_block(out, prices, listing_date, adj_issue, listing_close, is_delisted, data_last):
    """Within-horizon peak/trough (MFE/MAE) from BOTH entries + move timing, for 1y/3y/5y.
    Reads the endpoint returns already in `out` (clamp invariant) — call AFTER _horizon_returns.
    Extracted verbatim from compute()."""
    for label, days in HORIZONS:
        # short horizons (1m/3m/6m) added 2026-06-06 for the short-vs-long lens; same math
        if label not in ('1m', '3m', '6m', '1y', '3y', '5y'):
            continue
        end = listing_date + timedelta(days=days)
        # mature AND covered: for a non-delisted name the daily series must actually reach the
        # horizon end (else the window is truncated and MFE/MAE would span < h — a silent
        # coverage artifact, same guard the endpoint uses). Delisted => full path known, no guard.
        mature = is_delisted or (end <= TODAY and end <= data_last)
        mfe = mae = mfe_lst = mae_lst = None
        days_to_mfe = days_to_mae = days_to_be = None
        if mature:
            win = [p for p in prices if listing_date <= p['date'] <= end]
            hp = [p for p in win if p['h'] is not None]
            lp = [p for p in win if p['l'] is not None]
            hi = lo = None
            if hp:
                pk = max(hp, key=lambda p: p['h']); hi = pk['h']
                days_to_mfe = (pk['date'] - listing_date).days        # TIMING of the peak
            if lp:
                tr = min(lp, key=lambda p: p['l']); lo = tr['l']
                days_to_mae = (tr['date'] - listing_date).days        # TIMING of the trough
            # how long until the ALLOTTEE was first back at/above issue (the "underwater" duration;
            # ~0 for the usual above-issue listing, informative for weak listers)
            if adj_issue:
                be = next((p for p in win if p['h'] is not None and p['h'] >= adj_issue), None)
                if be is not None:
                    days_to_be = (be['date'] - listing_date).days
            if adj_issue:                                # ALLOTTEE entry (from issue)
                if hi: mfe = hi / adj_issue - 1
                if lo: mae = lo / adj_issue - 1
            if listing_close:                            # SECONDARY-buyer entry (from listing)
                if hi: mfe_lst = hi / listing_close - 1
                if lo: mae_lst = lo / listing_close - 1
        # The horizon-end price is inside the window by definition, so the peak must be >= the
        # endpoint and the trough <= it. Clamp to enforce that invariant — guards against price-source
        # mixing (some SME returns come from the screener-weekly merge), forced-wipeout terminals
        # (−100%), and data spikes. (V3 review fix.)
        rfi_e = out.get('return_from_issue_%s' % label)
        # CLAMP REMOVED: MFE/MAE are now allowed to reflect the true mathematical peaks and troughs
        # because the corporate actions dataset perfectly split-adjusts the entire price trajectory.
        out['mfe_%s' % label] = mfe                      # from issue (allottee)
        out['mae_%s' % label] = mae
        out['mfe_lst_%s' % label] = mfe_lst              # from listing (secondary buyer)
        out['mae_lst_%s' % label] = mae_lst
        # TIMING of the move (entry-independent — the peak/trough is the same price extreme for both
        # entries): when does the IPO peak, when does it bottom, how long until the allottee recovers
        # to issue. Daily-resolution from bhavcopy; the merge recomputes these at weekly resolution.
        out['days_to_mfe_%s' % label] = days_to_mfe
        out['days_to_mae_%s' % label] = days_to_mae
        out['days_to_breakeven_%s' % label] = days_to_be


def _lifetime_block(out, prices, adj_issue, listing_open, listing_close):
    """Listing gains, all-time high/low, max gain, max drawdown (+duration).
    Extracted verbatim from compute()."""
    lg_open = (listing_open / adj_issue - 1) if (listing_open and adj_issue) else None
    lg_close = (listing_close / adj_issue - 1) if (listing_close and adj_issue) else None
    out['listing_gain_open'] = lg_open
    out['listing_gain_close'] = lg_close

    highs = [p['h'] for p in prices if p['h'] is not None]
    lows = [p['l'] for p in prices if p['l'] is not None]
    ath = max(highs) if highs else None
    atl = min(lows) if lows else None
    out['all_time_high'] = ath
    out['all_time_low'] = atl
    out['max_gain_pct'] = (ath / adj_issue - 1) if (ath and adj_issue) else None

    # max drawdown on adjusted close (worst peak-to-trough), + duration days
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
                mdd = dd
                mdd_dur = (p['date'] - peak_date).days
    out['max_drawdown_pct'] = mdd if prices else None
    out['max_drawdown_duration_days'] = mdd_dur if prices else None


def _risk_liquidity_block(out, prices, n):
    """Annualised volatility, median turnover (RAW close*volume), circuit-lock share,
    liquidity flag. Extracted verbatim from compute()."""
    rets = []
    prev = None
    for p in prices:
        c = p['c']
        if c is None or c <= 0:
            prev = c
            continue
        if prev is not None and prev > 0:
            rets.append(c / prev - 1)
        prev = c
    out['volatility_annual'] = (statistics.stdev(rets) * math.sqrt(252)) if len(rets) >= 2 else None

    # turnover uses RAW close*volume (raw_c preserved before adjustment)
    turnovers = [p['raw_c'] * p['v'] for p in prices
                 if p['raw_c'] is not None and p['v'] is not None]
    out['median_daily_turnover_inr'] = statistics.median(turnovers) if turnovers else None

    lock_days = sum(1 for p in prices
                    if p['o'] is not None and p['h'] is not None and p['l'] is not None
                    and p['o'] == p['h'] == p['l'])
    out['circuit_lock_frac'] = (lock_days / n) if n else None
    med_turn = out['median_daily_turnover_inr']
    out['liquidity_flag'] = 'low' if (med_turn is not None and med_turn < 1e6) else 'ok'


def compute(isin, mrow, prices, actions, deli, nifty_dates, nifty_closes):
    # price_source default = 'bhavcopy_daily' so the schema is consistent for every row;
    # scrapers/screener_prices_merge.py later overwrites the fix-set rows to
    # 'screener_weekly' / 'none_listing_era'. Canonical run order:
    #   07_returns_summary.py -> screener_prices_merge.py -> 08_build_universe.py -> 09_assemble.py
    out = {'isin': isin, 'type': mrow['type'], 'price_source': 'bhavcopy_daily'}
    issue_price = mrow['issue_price']
    listing_date = mrow['listing_date']

    # issue_price is on the RAW (at-IPO) scale. The price series is adjusted to
    # the CURRENT scale, so a split AFTER listing means the raw issue_price must
    # be divided by the post-listing adjustment factor to compare on one scale.
    adj_issue = issue_price
    if issue_price is not None and listing_date is not None:
        adj_issue = issue_price / adj_factor_after(actions, listing_date)

    n = len(prices)
    out['n_days_history'] = n
    if n == 0 or listing_date is None:
        return None  # nothing to compute

    pdates = [p['date'] for p in prices]
    pclose = [p['c'] for p in prices]

    # ---- delisting / terminal handling (see _terminal_state)
    is_delisted, reason, terminal, eff_delist = _terminal_state(isin, deli, actions, pdates, pclose)
    out['delisted'] = is_delisted
    out['delist_reason'] = reason

    # ---- entry refs
    out['issue_price'] = issue_price           # RAW (for display)
    out['issue_price_adj'] = adj_issue         # split-adjusted to current scale
    # first trading day on/after listing_date
    li = bisect_right(pdates, listing_date - timedelta(days=1))  # first idx with date >= listing_date
    listing_close = listing_open = None
    if li < n:
        listing_close = prices[li]['c']
        listing_open = prices[li]['o']
    out['listing_close'] = listing_close
    out['listing_open'] = listing_open

    data_first = pdates[0]
    data_last = pdates[-1]

    # ---- horizon returns
    def price_at_horizon(target):
        """adjusted close used for a horizon ending at `target`. Returns
        (value, mature_bool). mature False => leave NULL (not mature)."""
        # delisting takes precedence: if delisted strictly before target, terminal
        if is_delisted and eff_delist is not None and eff_delist < target:
            return terminal, True
        # maturity: horizon end in the future and not delisted-before -> NULL
        if target > TODAY:
            return None, False
        # need price within data coverage
        if target < data_first:
            return None, True  # mature in time but no early data -> unavailable NULL
        val = nearest_on_or_before(pdates, pclose, target)
        if target > data_last:
            # horizon end past our last price day but in the past relative to TODAY:
            # use last available close (data gap) — treat as unavailable -> NULL
            return None, True
        return val, True

    nifty_base = nearest_on_or_before(nifty_dates, nifty_closes, listing_date)
    sc_base = nearest_on_or_before(SC_DATES, SC_CLOSES, listing_date) if SC_DATES else None

    _horizon_returns(out, price_at_horizon, listing_date, adj_issue, listing_close,
                     nifty_dates, nifty_closes, nifty_base, sc_base)

    # within-horizon peak/trough (MFE/MAE) + timing — must follow _horizon_returns (clamp)
    _mfe_mae_block(out, prices, listing_date, adj_issue, listing_close, is_delisted, data_last)

    # listing gains, ATH/ATL, max gain, max drawdown
    _lifetime_block(out, prices, adj_issue, listing_open, listing_close)

    # current price: last adj close, or terminal if delisted
    current_price = terminal if (is_delisted and terminal is not None) else pclose[-1]
    out['current_price'] = current_price
    out['current_return_from_issue'] = (current_price / adj_issue - 1) if (current_price is not None and adj_issue) else None

    # ---- risk / liquidity
    _risk_liquidity_block(out, prices, n)

    # ---- outcome_class on current_return_from_issue (same thresholds as the
    # remediation module; the inline copy was identical -> deduped to one source)
    out['outcome_class'] = _outcome_class(out['current_return_from_issue'])

    # ---- FIX 2: listing-coverage remediation (unrecorded split / bad coverage)
    has_action = bool(actions)
    out['listing_metrics_status'] = remediate_listing(
        out,
        chittor_listing_open=mrow.get('chittor_listing_open'),
        chittor_listing_close=mrow.get('chittor_listing_close'),
        has_action=has_action,
        listing_date=listing_date,
        data_first=data_first,
        price_source=out.get('price_source', 'bhavcopy_daily'),
        horizons=HORIZONS,
        recovered=LISTING_OVERRIDE.get(isin),
    )

    return out


# ---------------------------------------------------------------- column order
def columns():
    cols = ['isin', 'company_name', 'type', 'issue_price', 'issue_price_adj',
            'listing_date', 'listing_open', 'listing_close',
            'listing_gain_open', 'listing_gain_close']
    for label, _ in HORIZONS:
        cols += ['return_from_issue_%s' % label,
                 'return_from_listing_%s' % label,
                 'alpha_%s' % label, 'alpha_sc_%s' % label]
    for label in ('1m', '3m', '6m', '1y', '3y', '5y'):
        cols += ['mfe_%s' % label, 'mae_%s' % label, 'mfe_lst_%s' % label, 'mae_lst_%s' % label]
    for label in ('1m', '3m', '6m', '1y', '3y', '5y'):
        cols += ['days_to_mfe_%s' % label, 'days_to_mae_%s' % label, 'days_to_breakeven_%s' % label]
    cols += ['max_gain_pct', 'max_drawdown_pct', 'max_drawdown_duration_days',
             'all_time_high', 'all_time_low', 'current_price',
             'current_return_from_issue', 'outcome_class',
             'volatility_annual', 'median_daily_turnover_inr',
             'circuit_lock_frac', 'liquidity_flag',
             'delisted', 'delist_reason', 'n_days_history',
             'listing_metrics_status', 'price_source']
    return cols


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


def build_row(isin, mrow, raw_prices, actions, deli, nd, nc):
    """raw_prices: rows already loaded (adjusted)."""
    res = compute(isin, mrow, raw_prices, actions, deli, nd, nc)
    if res is None:
        return None
    res['company_name'] = mrow['company_name']
    res['listing_date'] = mrow['listing_date'].isoformat() if mrow['listing_date'] else ''
    return res


def main():
    test_mode = '--test' in sys.argv
    masters = load_masters()
    ca_by_isin, ca_by_symbol = load_corp_actions()
    deli = load_delisting()
    nd, nc = load_nifty()
    global LISTING_OVERRIDE, SC_DATES, SC_CLOSES
    LISTING_OVERRIDE = load_listing_override()
    SC_DATES, SC_CLOSES = load_smallcap()
    print(f'  listing-day overrides: {len(LISTING_OVERRIDE)} · smallcap250 days: {len(SC_DATES)}',
          file=sys.stderr)

    price_isins = set(x[:-4] for x in os.listdir(PRICES_DIR) if x.endswith('.csv'))

    if test_mode:
        targets = ['INE192R01011', 'INE522F01014', 'INE0DG401010']
        # add one SME with a price file
        for isin, mrow in masters.items():
            if mrow['type'] == 'SME' and isin in price_isins:
                targets.append(isin)
                break
        for isin in targets:
            mrow = masters.get(isin)
            if not mrow:
                print(f'{isin}: NOT IN MASTER'); continue
            actions = actions_for(isin, mrow.get('nse_symbol'), ca_by_isin, ca_by_symbol)
            prices = load_prices(isin, actions)
            row = build_row(isin, mrow, prices, actions, deli, nd, nc)
            print('=' * 70)
            print(f"{isin}  {mrow['company_name']}  [{mrow['type']}]")
            if row is None:
                print('  (no data)'); continue
            for k in ['issue_price', 'listing_date', 'listing_open', 'listing_close',
                      'listing_gain_close', 'return_from_listing_1y', 'return_from_issue_1y',
                      'return_from_issue_3y', 'return_from_issue_5y', 'return_from_issue_10y',
                      'current_price', 'current_return_from_issue', 'outcome_class',
                      'max_gain_pct', 'max_drawdown_pct', 'volatility_annual',
                      'median_daily_turnover_inr', 'liquidity_flag', 'circuit_lock_frac',
                      'delisted', 'delist_reason', 'n_days_history']:
                print(f'  {k:32s} {fmt(row.get(k))}')
        return

    cols = columns()
    out_path = os.path.join(ROOT, 'data/master/returns_summary.csv')
    rows_written = 0
    cov = {label: 0 for label, _ in HORIZONS}
    listing_gains = []
    n_multibagger = n_wipeout = n_classed = 0

    isins_sorted = sorted(i for i in masters if i in price_isins)
    with open(out_path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for idx, isin in enumerate(isins_sorted):
            mrow = masters[isin]
            try:
                actions = actions_for(isin, mrow.get('nse_symbol'), ca_by_isin, ca_by_symbol)
                prices = load_prices(isin, actions)
                row = build_row(isin, mrow, prices, actions, deli, nd, nc)
            except Exception as e:
                print(f'  ERROR {isin}: {e}', file=sys.stderr)
                row = None
            if row is None:
                continue
            w.writerow({c: fmt(row.get(c)) for c in cols})
            rows_written += 1
            for label, _ in HORIZONS:
                if row.get('return_from_issue_%s' % label) is not None:
                    cov[label] += 1
            if row.get('listing_gain_close') is not None:
                listing_gains.append(row['listing_gain_close'])
            oc = row.get('outcome_class')
            if oc:
                n_classed += 1
                if oc == 'multibagger':
                    n_multibagger += 1
                elif oc == 'wipeout':
                    n_wipeout += 1
            if (idx + 1) % 500 == 0:
                print(f'  ... {idx+1}/{len(isins_sorted)}', file=sys.stderr)

    print(f'\nrows_written: {rows_written}')
    print('coverage (return_from_issue non-null):')
    for label, _ in HORIZONS:
        print(f'  {label:4s}: {cov[label]}')
    if listing_gains:
        print(f'median listing_gain_close: {statistics.median(listing_gains):.4f}')
    if n_classed:
        print(f'%% multibagger: {100*n_multibagger/n_classed:.2f}%  (n={n_multibagger})')
        print(f'%% wipeout:     {100*n_wipeout/n_classed:.2f}%  (n={n_wipeout})')
    print(f'output: {out_path}')


if __name__ == '__main__':
    main()
