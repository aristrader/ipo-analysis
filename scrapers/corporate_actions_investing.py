"""Investing.com Corporate Actions API — splits for Layer 2 price adjustment fallback."""

import os
import re
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cr

_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def parse_date(date_str):
    """Parse date from formats like 'Oct 28, 2020' to '2020-10-28'."""
    date_str = date_str.strip()
    try:
        d = datetime.strptime(date_str, '%b %d, %Y')
        return d.strftime('%Y-%m-%d')
    except Exception:
        # Fallback to just returning the raw string or attempting other formats
        try:
            d = datetime.strptime(date_str, '%d-%m-%Y')
            return d.strftime('%Y-%m-%d')
        except Exception:
            return date_str

def fetch_investing_splits(symbol, company_slug):
    """
    Fetch stock splits for a given symbol and company slug from in.investing.com.
    Example url: https://in.investing.com/equities/reliance-industries-historical-data-splits
    """
    url = f'https://in.investing.com/equities/{company_slug}-historical-data-splits'
    
    try:
        response = cr.get(url, headers=_HEADERS, impersonate="chrome110", timeout=30)
    except Exception as e:
        print(f"Exception fetching {url}: {e}")
        return []

    if response.status_code != 200:
        print(f"Error {response.status_code} fetching {url}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    
    records = []
    
    for table in tables:
        # Find headers
        th_elements = table.find_all('th')
        if not th_elements:
            continue
            
        headers = [th.text.strip().lower() for th in th_elements]
        
        if 'date' in headers and 'ratio' in headers:
            date_idx = headers.index('date')
            ratio_idx = headers.index('ratio')
            
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > max(date_idx, ratio_idx):
                    date_val = cols[date_idx].text.strip()
                    ratio_val = cols[ratio_idx].text.strip()
                    
                    if not date_val or not ratio_val:
                        continue
                        
                    m = re.search(r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)', ratio_val)
                    if m:
                        a, b = map(float, m.groups())
                        # Usually "1:10" means 10 new shares for 1 old share.
                        factor = a / b if b != 0 else None
                        
                        records.append({
                            'symbol': symbol,
                            'action_type': 'split',
                            'raw_subject': ratio_val,
                            'ratio_factor': factor,
                            'ex_date': parse_date(date_val),
                            'source': 'investing.com'
                        })
            break

    return records

if __name__ == '__main__':
    test_symbol = 'RELIANCE'
    test_slug = 'reliance-industries'
    
    print(f"Testing Investing.com scraper for {test_symbol}...")
    splits = fetch_investing_splits(test_symbol, test_slug)
    
    os.makedirs('data/raw', exist_ok=True)
    out_path = 'data/raw/investing_splits_sample.csv'
    
    if splits:
        fields = ['symbol', 'action_type', 'raw_subject', 'ratio_factor', 'ex_date', 'source']
        with open(out_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(splits)
        print(f"Saved {len(splits)} records to {out_path}")
    else:
        print("No splits found or failed to parse. Could be blocked or dynamic content.")
