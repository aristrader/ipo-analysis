"""Phase 3c: fill IPO subscription split from the NSE Public Issues API (gap G1a, MAINBOARD), by ISIN.

Source cache: data/raw/nse/subscription.csv (isin, sub_qib_x, sub_nii_x, sub_retail_x, sub_total_x),
fetched by NSE symbol (authoritative). Only fills mainboard rows that currently lack subscription;
never overwrites Sharescart. Filled rows get sub_total_x_src='nse'.
"""
import csv, os

path = 'data/raw/nse/subscription.csv'
if not os.path.exists(path):
    raise SystemExit("run scrapers/nse_subscription.py first (cache missing)")
sub = {}
for r in csv.DictReader(open(path)):
    sub[r['isin']] = r

SUBCOLS = ['sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x']
filled = 0
p = 'data/master/_base_mainboard.csv'
rows = list(csv.DictReader(open(p)))
cols = list(rows[0].keys())
for r in rows:
    if (r.get('sub_total_x') or '').strip():
        continue                                   # already has subscription — don't overwrite
    s = sub.get(r['isin'])
    if not s or not (s.get('sub_total_x') or '').strip():
        continue
    wrote = False
    for c in SUBCOLS:
        v = (s.get(c) or '').strip()
        if v and not (r.get(c) or '').strip():
            r[c] = v; wrote = True
    if wrote:
        r['sub_total_x_src'] = 'nse'
        filled += 1
with open(p, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
    w.writeheader(); w.writerows(rows)
print(f"mainboard: filled subscription on {filled} rows from NSE")
