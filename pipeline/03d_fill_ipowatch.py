"""Phase 3d: fill SME subscription split + GMP from ipowatch.in (gaps G1a-SME, G2), by ISIN.

Source cache: data/raw/ipowatch/matches.csv — only rows where matched=1, each confirmed by a STRICT
name + exact-IPO-date corroboration at fetch time (scrapers/ipowatch.py). Every value here is concrete.

- SME subscription: fill SME rows lacking sub_total_x → src='ipowatch'.
- GMP: gmp_pct = gmp_rs / issue_price * 100 for any row lacking gmp_pct (needs issue_price) → src='ipowatch'.
Never overwrites existing values.
"""
import csv, os

path = 'data/raw/ipowatch/matches.csv'
if not os.path.exists(path):
    raise SystemExit("run scrapers/ipowatch.py first (cache missing)")
match = {}
for r in csv.DictReader(open(path)):
    if r.get('matched') == '1':
        match[r['isin']] = r


def fnum(s):
    try:
        return float(str(s).replace(',', ''))
    except (ValueError, TypeError):
        return None


SUBCOLS = ['sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x']
sub_filled = gmp_filled = 0
for seg in ['mainboard', 'sme']:
    p = f'data/master/_base_{seg}.csv'
    rows = list(csv.DictReader(open(p)))
    cols = list(rows[0].keys())
    for r in rows:
        m = match.get(r['isin'])
        if not m:
            continue
        # SME subscription (mainboard subscription comes from NSE)
        if seg == 'sme' and not (r.get('sub_total_x') or '').strip() and (m.get('sub_total_x') or '').strip():
            wrote = False
            for c in SUBCOLS:
                v = (m.get(c) or '').strip()
                if v and not (r.get(c) or '').strip():
                    r[c] = v; wrote = True
            if wrote:
                r['sub_total_x_src'] = 'ipowatch'; sub_filled += 1
        # GMP: convert ₹ premium to % of issue price
        gmp_rs = fnum(m.get('gmp_rs'))
        issue = fnum(r.get('issue_price'))
        if gmp_rs is not None and issue and not (r.get('gmp_pct') or '').strip():
            r['gmp_pct'] = round(gmp_rs / issue * 100, 2)
            r['gmp_pct_src'] = 'ipowatch'; gmp_filled += 1
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    print(f"{seg}: ipowatch applied")
print(f"filled SME subscription on {sub_filled} rows, GMP on {gmp_filled} rows (src='ipowatch')")
