import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re
import os

def search_ddg(query):
    url = "https://html.duckduckgo.com/html/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    data = {'q': query}
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return ""

def extract_gmp(text, issue_price):
    if not isinstance(text, str): return None
    
    patterns = [
        r'GMP.*?rs\.?\s*(\d+)',
        r'GMP.*?₹\s*(\d+)',
        r'premium.*?₹\s*(\d+)',
        r'grey market premium.*?rs\.?\s*(\d+)',
        r'gmp.*?is\s*(\d+)',
        r'gmp.*?of\s*₹?\s*(\d+)'
    ]
    
    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            gmp_val = float(match.group(1))
            if pd.notna(issue_price) and issue_price > 0:
                if gmp_val < issue_price * 5:
                    return round((gmp_val / issue_price) * 100, 2)
    return None

def main():
    df = pd.read_csv('data/master/sme.csv')
    df['gmp_pct'] = pd.to_numeric(df['gmp_pct'], errors='coerce')
    
    mask = (df['year'] <= 2022) & (df['gmp_pct'].isna())
    missing_gmp = df[mask].copy()
    
    print(f"Found {len(missing_gmp)} SME IPOs <= 2022 missing GMP.")
    
    results = []
    
    for idx, row in missing_gmp.iterrows():
        company = row['company_name']
        year = row['year']
        issue_price = pd.to_numeric(row['issue_price'], errors='coerce')
        
        query = f'"{company}" SME IPO GMP {year} (investorzone OR chittorgarh OR chanakyanipothi)'
        print(f"Searching: {query}")
        
        html = search_ddg(query)
        if not html:
            time.sleep(2)
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        snippets = soup.find_all('a', class_='result__snippet')
        
        found_gmp_pct = None
        for snippet in snippets:
            text = snippet.get_text()
            pct = extract_gmp(text, issue_price)
            if pct is not None:
                found_gmp_pct = pct
                print(f"Found GMP {pct}% for {company} based on text: {text}")
                break
                
        if found_gmp_pct is not None:
            results.append({
                'company_name': company,
                'year': year,
                'gmp_pct': found_gmp_pct
            })
            
        time.sleep(1.5)
        
    if results:
        res_df = pd.DataFrame(results)
        os.makedirs('data/raw', exist_ok=True)
        res_df.to_csv('data/raw/gmp_deep_hunt_2020_2022.csv', index=False)
        print("Saved findings to data/raw/gmp_deep_hunt_2020_2022.csv")
    else:
        print("Could not find any historical GMP data.")

if __name__ == '__main__':
    main()
