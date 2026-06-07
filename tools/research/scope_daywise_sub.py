"""Task 1 (calls-engine plan): scope chittorgarh DAY-WISE subscription coverage.
Samples ~30 IPOs across 2021-2026, fetches the per-IPO subscription page (and the detail page
as fallback), and reports whether a day-wise table (Day 1 / Day 2 / Day 3 rows) exists.
Decides the EARLY-call branch: A = backtestable, B = forward-collection only."""
import csv, random, re, sys, time
import cloudscraper

random.seed(7)  # deterministic sample
rows = list(csv.DictReader(open("data/raw/chittorgarh/urls.csv")))
by_year = {}
for r in rows:
    by_year.setdefault(r["year"], []).append(r)
sample = []
for y in sorted(by_year):
    take = by_year[y]
    random.shuffle(take)
    sample += take[:5]                      # 5 per year
print(f"sampling {len(sample)} IPOs across years {sorted(by_year)}")

sc = cloudscraper.create_scraper()
day_re = re.compile(r">\s*Day\s*([123])\b", re.I)
hits, misses, errors = [], [], []
for r in sample:
    slug, cid = r["chittorgarh_slug"], r["chittorgarh_id"]
    found = None
    for url in (f"https://www.chittorgarh.com/ipo_subscription/{slug}/{cid}/",
                r["detail_url"]):
        try:
            resp = sc.get(url, headers={"Referer": "https://www.chittorgarh.com/"}, timeout=25)
            if resp.status_code != 200:
                continue
            days = sorted(set(day_re.findall(resp.text)))
            if days:
                found = (url.split("chittorgarh.com")[1].split("/")[1], days)
                break
        except Exception as e:
            errors.append((r["company_name"], str(e)[:60]))
        time.sleep(0.4)
    (hits if found else misses).append((r["year"], r["company_name"], r["type"], found))
    time.sleep(0.4)

print(f"\nday-wise table found: {len(hits)}/{len(sample)}  (errors: {len(errors)})")
from collections import Counter
cov = Counter((h[0]) for h in hits)
tot = Counter((s["year"]) for s in sample)
for y in sorted(tot):
    print(f"  {y}: {cov.get(y,0)}/{tot[y]}")
for h in hits[:6]:
    print("  HIT ", h[0], h[1][:40], h[3])
for m in misses[:6]:
    print("  MISS", m[0], m[1][:40])
