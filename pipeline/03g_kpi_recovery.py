import csv
import os
import re
import time
import urllib.request
from bs4 import BeautifulSoup

def _num(s):
    if not s: return None
    m = re.search(r'-?[\d,]+(?:\.\d+)?', str(s).replace(',', ''))
    return m.group() if m else None

def scrape_kpis(url):
    rec = {
        'face_value': None,
        'kpi_pe_pre_ipo': None,
        'kpi_market_cap_post_ipo': None,
        'kpi_roe_pre_ipo': None,
        'kpi_roce_pre_ipo': None,
        'issue_expenses_cr': None
    }
    if not url: return rec
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        kv = {}
        for t in soup.find_all('table'):
            for tr in t.find_all('tr'):
                cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
                if len(cells) >= 2 and cells[0]:
                    kv[cells[0].strip()] = cells[1].strip()
                    
        for k, v in kv.items():
            k_low = k.lower()
            if 'face value' in k_low: rec['face_value'] = _num(v)
            if 'p/e (x)' in k_low: rec['kpi_pe_pre_ipo'] = _num(v)
            if 'market cap' in k_low: rec['kpi_market_cap_post_ipo'] = _num(v)
            if 'roe' in k_low: rec['kpi_roe_pre_ipo'] = _num(v)
            if 'roce' in k_low: rec['kpi_roce_pre_ipo'] = _num(v)
            if 'issue expenses' in k_low: rec['issue_expenses_cr'] = _num(v)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return rec

if __name__ == "__main__":
    urls_file = 'data/raw/chittorgarh/urls_longterm.csv'
    out_file = 'data/raw/chittorgarh/kpis_recovered.csv'
    
    # Check what we already recovered to resume
    done = set()
    if os.path.exists(out_file):
        with open(out_file, 'r') as f:
            done = {r['isin'] for r in csv.DictReader(f)}
    
    rows = list(csv.DictReader(open(urls_file)))
    print(f"Total rows to check: {len(rows)}")
    
    with open(out_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['isin', 'detail_url', 'face_value', 'kpi_pe_pre_ipo', 'kpi_market_cap_post_ipo', 'kpi_roe_pre_ipo', 'kpi_roce_pre_ipo', 'issue_expenses_cr'])
        if not done:
            writer.writeheader()
            
        count = 0
        for r in rows:
            isin = r.get('isin')
            if not isin or isin in done: continue
            
            kpis = scrape_kpis(r.get('detail_url'))
            kpis['isin'] = isin
            kpis['detail_url'] = r.get('detail_url')
            
            writer.writerow(kpis)
            f.flush()
            count += 1
            if count % 10 == 0:
                print(f"Recovered {count} KPIs...")
            time.sleep(0.5)
    print("Done recovery.")
