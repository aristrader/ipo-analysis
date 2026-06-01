import csv, sys
urls=list(csv.DictReader(open('data/raw/chittorgarh/urls.csv')))
det=list(csv.DictReader(open('data/raw/chittorgarh/details.csv')))
assert len(urls) >= 1200, f"expected ~1272 urls, got {len(urls)}"
assert all(r.get('isin') for r in urls), "every url row must have an ISIN"
years={r['year'] for r in urls}; assert {'2020','2021','2022','2023','2024','2025'} <= years, years
assert len(det) >= 1200, f"expected ~1256 details, got {len(det)}"
print(f"OK chittorgarh: {len(urls)} urls (100% ISIN), {len(det)} details, years {sorted(years)}")
