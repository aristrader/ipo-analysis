import csv, os
for seg in ['mainboard','sme']:
    p=f'data/master/_base_{seg}.csv'
    assert os.path.exists(p), f"missing {p}"
    rows=list(csv.DictReader(open(p)))
    assert rows, f"{p} empty"
    isins=[r['isin'] for r in rows]
    assert all(isins), f"{seg}: every row needs ISIN"
    assert len(isins)==len(set(isins)), f"{seg}: ISIN must be unique (dupes found)"
    for col in ['isin','company_name','type','nse_symbol','bse_script_code',
                'open_date','close_date','listing_date','issue_price']:
        assert col in rows[0], f"{seg}: missing column {col}"
mb=len(list(csv.DictReader(open('data/master/_base_mainboard.csv'))))
sme=len(list(csv.DictReader(open('data/master/_base_sme.csv'))))
print(f"OK base: mainboard={mb}, sme={sme}, total={mb+sme} (expect ~1272)")
