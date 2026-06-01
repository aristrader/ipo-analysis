import csv
for seg in ['mainboard','sme']:
    rows=list(csv.DictReader(open(f'data/master/_base_{seg}.csv')))
    for col in ['market_maker','fresh_issue_cr','ofs_cr','anchor_allocation_cr',
                'listing_open','listing_high','listing_low','listing_close','objects_of_issue']:
        assert col in rows[0], f"{seg}: detail col {col} not attached"
# SME should have market_maker on most rows
sme=list(csv.DictReader(open('data/master/_base_sme.csv')))
mm=sum(1 for r in sme if r.get('market_maker'))
assert mm > len(sme)*0.6, f"market_maker coverage too low: {mm}/{len(sme)}"
print(f"OK detail attached; SME market_maker {mm}/{len(sme)}")
