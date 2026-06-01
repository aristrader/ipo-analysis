import csv
# Build ISIN set from old Sharescart data (the source of subscription/financials)
old=list(csv.DictReader(open('archive/derived/mainboard_clean_OLD.csv'))) + \
    list(csv.DictReader(open('archive/derived/sme_clean_OLD.csv')))
old_isin={r['isin'] for r in old if r.get('isin')}
for seg in ['mainboard','sme']:
    rows=list(csv.DictReader(open(f'data/master/_base_{seg}.csv')))
    for col in ['sub_total_x','sub_qib_x','pat_yr3','gmp_pct','promoter_post_issue_pct','sub_total_x_src']:
        assert col in rows[0], f"{seg}: enrich col {col} missing"
    # INVARIANT: any subscription value MUST carry a known provenance (sub_total_x_src), and
    # Sharescart-sourced values must still have had an ISIN match in the old data.
    # New sources (nse symbol-matched, ipowatch strict name+date-matched) are blessed via their src tag.
    ALLOWED = {'sharescart', 'nse', 'ipowatch'}
    for r in rows:
        if r.get('sub_total_x'):
            src = (r.get('sub_total_x_src') or '').strip()
            assert src in ALLOWED, f"{seg}: {r['company_name']} subscription with unknown src '{src}'"
            if src == 'sharescart':
                assert r['isin'] in old_isin, f"{seg}: {r['company_name']} sharescart subscription without ISIN match!"
print("OK enrich: subscription/financials/gmp present with known provenance (sharescart=ISIN-gated, nse/ipowatch tagged)")
