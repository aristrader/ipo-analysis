"""Phase 9: assemble the final Layer-2 analysis table = universe (features) JOIN returns_summary
(outcomes), by ISIN, + per-row data_quality score (C1) + cross-source integrity checks (C2).
Output: data/master/ipo_analysis.csv  (the Layer-3 substrate).  Reads only; writes the new file.
"""
import csv, os

def load(p, key='isin'):
    return {r[key]: r for r in csv.DictReader(open(p)) if r.get(key)}

uni = load('data/master/universe.csv')
ret = load('data/master/returns_summary.csv')
# A face-value split often changes the ISIN, so an ISIN-only match misses most
# split stocks. Collect both the corp-action ISINs AND the corp-action NSE
# symbols, then exclude any universe stock matched by EITHER (their adjusted
# listing_open legitimately differs from Chittorgarh's raw quote).
action_isins = set()
action_symbols = set()
for r in csv.DictReader(open('data/reference/corp_actions.csv')):
    if r.get('isin'):
        action_isins.add(r['isin'].strip())
    if r.get('symbol'):
        action_symbols.add(r['symbol'].strip().upper())

def f(x):
    try: return float(str(x).replace(',', ''))
    except (ValueError, TypeError): return None
def present(v): return (v is not None) and (str(v).strip() not in ('', 'nan', 'None', 'NA'))

# --- merge: universe rows are the spine; attach returns_summary outcome columns ---
# Both universe (Chittorgarh RAW listing quote) and returns_summary (price-derived,
# split/coverage-adjusted) carry listing_open/listing_close. Renaming the RETURNS-
# derived ones to adj_* keeps BOTH (no collapse, no duplicate headers) so the output
# preserves the raw Chittorgarh quote AND the adjusted listing metrics side by side.
RET_RENAME = {
    'listing_open': 'adj_listing_open',
    'listing_close': 'adj_listing_close',
    'listing_gain_open': 'adj_listing_gain_open',
    'listing_gain_close': 'adj_listing_gain_close',
}
uni_cols = list(next(iter(uni.values())).keys())
ret_keys = [c for c in next(iter(ret.values())).keys()
            if c not in ('isin', 'company_name', 'type', 'issue_price', 'listing_date')]
# emit-name for each returns column (renamed if it would collide / is a listing metric)
ret_cols = [RET_RENAME.get(c, c) for c in ret_keys]
out_cols = uni_cols + ret_cols + ['mfe_mae_clamped','has_price_history','data_quality_score','data_quality_tier','xcheck_flags']

# data_quality is ERA-AWARE: an IPO is not penalised for a field that COULD NOT exist for its
# era/segment (GMP only ~2020+; per-symbol subscription only boom or longterm-2017+). Otherwise
# every pre-2020 IPO was unfairly scored 'low' for missing GMP it never could have had.
QKEYS_ALWAYS = ['issue_price','listing_date','pre_ipo_pat','sector','market_cap_class']

def _applicable_qkeys(u):
    keys = list(QKEYS_ALWAYS)
    ld = (u.get('listing_date') or '')
    yr = int(ld[:4]) if ld[:4].isdigit() else None
    if u.get('cohort') == 'boom':
        keys.append('gmp_pct')                       # GMP only exists in the boom era
    if u.get('cohort') == 'boom' or (yr and yr >= 2017):
        keys.append('sub_total_x')                   # per-symbol subscription availability
    return keys
rows = []
qtier = {'high':0,'med':0,'low':0}
xcheck = []
for isin, u in uni.items():
    row = dict(u)
    r = ret.get(isin)
    if r:
        for src in ret_keys:
            row[RET_RENAME.get(src, src)] = r.get(src, '')
    # INVARIANT CLAMP (V3 review): the horizon-end price is inside the window by definition, so the
    # within-horizon peak must be >= the endpoint return and the trough <= it. Enforce on the FINAL
    # columns — robust to upstream split-remediation (which rescales returns but not MFE/MAE) and
    # source-mixing. Flag rows where the clamp moved a value materially (>1pp) so it's auditable.
    clamped = False
    for h in ('1y', '3y', '5y'):
        for mfe_c, mae_c, end_c in (('mfe_%s' % h, 'mae_%s' % h, 'return_from_issue_%s' % h),
                                    ('mfe_lst_%s' % h, 'mae_lst_%s' % h, 'return_from_listing_%s' % h)):
            end_v = f(row.get(end_c))
            if end_v is None:
                continue
            mfe_v, mae_v = f(row.get(mfe_c)), f(row.get(mae_c))
            if mfe_v is not None and mfe_v < end_v:
                if end_v - mfe_v > 0.01: clamped = True
                row[mfe_c] = end_v
            if mae_v is not None and mae_v > end_v:
                if mae_v - end_v > 0.01: clamped = True
                row[mae_c] = end_v
    row['mfe_mae_clamped'] = '1' if clamped else '0'
    row['has_price_history'] = '1' if (r and present(r.get('n_days_history')) and f(r.get('n_days_history'))) else '0'
    # C1 data_quality: fraction of ERA-APPLICABLE key fields present (+ price history)
    qkeys = _applicable_qkeys(u)
    score = sum(1 for k in qkeys if present(u.get(k)))
    score += 1 if row['has_price_history'] == '1' else 0
    denom = len(qkeys) + 1
    q = round(score/denom, 2)
    row['data_quality_score'] = q
    tier = 'high' if q >= 0.7 else ('med' if q >= 0.4 else 'low')
    row['data_quality_tier'] = tier; qtier[tier] += 1
    # C2 cross-source: bhavcopy listing_open (returns) vs Chittorgarh listing_open (universe),
    # only where NO corp action (adjustment would legitimately diverge otherwise)
    flags = []
    if r and r.get('price_source') != 'screener_weekly':   # weekly close != day-open, skip (false-positive)
        u_open, r_open = f(u.get('listing_open')), f(r.get('listing_open'))
        u_sym = (u.get('nse_symbol') or '').strip().upper()
        has_action = (isin in action_isins) or (u_sym and u_sym in action_symbols)
        if u_open and r_open and not has_action:
            rel = abs(r_open - u_open)/u_open
            if rel > 0.20:
                flags.append('listing_price_mismatch')
                xcheck.append({'isin': isin, 'company': u.get('company_name'),
                               'chittorgarh_open': u_open, 'bhavcopy_open': r_open, 'rel_diff_pct': round(rel*100,1)})
    row['xcheck_flags'] = '|'.join(flags)
    rows.append(row)

with open('data/master/ipo_analysis.csv','w',newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=out_cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
os.makedirs('data/master/review',exist_ok=True)
with open('data/master/review/xcheck_review.csv','w',newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['isin','company','chittorgarh_open','bhavcopy_open','rel_diff_pct'])
    w.writeheader(); w.writerows(sorted(xcheck, key=lambda x:-x['rel_diff_pct']))

n=len(rows); wp=sum(1 for r in rows if r['has_price_history']=='1')
print(f"ipo_analysis.csv: {n} rows ({wp} with price history, {n-wp} without)")
print(f"data_quality tiers: {qtier}")
print(f"cross-source listing-price mismatches (no-corp-action, >20%): {len(xcheck)} -> xcheck_review.csv")
