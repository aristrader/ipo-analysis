import csv, os
for seg in ['mainboard','sme']:
    p=f'data/master/{seg}.csv'
    assert os.path.exists(p), f"missing {p}"
    rows=list(csv.DictReader(open(p)))
    for col in ['ticker_ns','ticker_bo','isin','confidence','confidence_reason']:
        assert col in rows[0], f"{seg}: missing {col}"
    # ISIN↔symbol conflicts: do NOT fail, but report them for review
    conflicts=[r for r in rows if r.get('isin_xchg_check')=='CONFLICT']
    if conflicts:
        print(f"{seg}: {len(conflicts)} ISIN↔symbol CONFLICT rows (review needed):")
        for r in conflicts:
            print(f"    {r.get('company_name','')}: chittorgarh={r.get('nse_symbol','')} official={(r.get('ticker_ns','') or '').replace('.NS','')}")
    else:
        print(f"{seg}: 0 ISIN↔symbol CONFLICT rows")
    conf=sum(1 for r in rows if r['confidence'] in ('isin_authoritative','chittorgarh_symbol'))
    print(f"{seg}: {conf}/{len(rows)} high-confidence (isin_authoritative + chittorgarh_symbol), {len(conflicts)} conflicts")
print("OK verify")
