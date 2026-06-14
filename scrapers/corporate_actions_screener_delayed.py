import os
import csv
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from urllib.request import Request, urlopen

# Enforce strict maximum TPS of 1
TPS_SLEEP = 1.5

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def get_company_id(symbol):
    """Resolve symbol to company ID using Screener's search API."""
    q = urllib.parse.quote(symbol)
    url = f'https://www.screener.in/api/company/search/?q={q}'
    try:
        time.sleep(TPS_SLEEP)
        req = Request(url, headers=UA)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and isinstance(data, list) and len(data) > 0:
                url_path = data[0].get('url', '')
                company_id = data[0].get('id')
                return company_id, url_path
    except Exception as e:
        print(f"Error fetching search for {symbol}: {e}")
    return None, None

def check_endpoint(url):
    """Fetch URL and check for redirects to login."""
    try:
        time.sleep(TPS_SLEEP)
        req = Request(url, headers=UA)
        # Prevent urllib from automatically following redirects
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                infourl = urllib.response.addinfourl(fp, headers, req.get_full_url())
                infourl.status = code
                infourl.code = code
                return infourl
            http_error_301 = http_error_303 = http_error_307 = http_error_302

        opener = urllib.request.build_opener(NoRedirectHandler)
        response = opener.open(req, timeout=10)
        
        status = response.getcode()
        body = response.read().decode('utf-8')
        
        if status in (301, 302):
            location = response.headers.get('Location', '')
            if 'login' in location.lower():
                return 'login_redirect', None
            return f'redirect_to_{location}', None
            
        return 'success', body
    except urllib.error.HTTPError as e:
        if e.code in (301, 302):
            location = e.headers.get('Location', '')
            if 'login' in location.lower():
                return 'login_redirect', None
        return f'http_error_{e.code}', None
    except Exception as e:
        return f'error_{str(e)}', None

def main():
    os.makedirs('data/raw', exist_ok=True)
    out_path = 'data/raw/screener_splits_sample_delayed.csv'
    
    symbols = ['RELIANCE']
    results = []
    
    for symbol in symbols:
        print(f"Processing {symbol}...")
        cid, url_path = get_company_id(symbol)
        if not cid:
            print(f"  Could not resolve ID for {symbol}")
            continue
            
        print(f"  Resolved to ID: {cid}, Path: {url_path}")
        
        candidates = [
            f"https://www.screener.in/api/company/{cid}/corporate-actions/",
            f"https://www.screener.in/api/company/{cid}/equity-history/",
            f"https://www.screener.in/api/company/{cid}/dividends/",
            f"https://www.screener.in/api/company/{cid}/splits/",
            f"https://www.screener.in/company/{cid}/corporate-actions/",
            f"https://www.screener.in{url_path}corporate-actions/",
            f"https://www.screener.in{url_path}consolidated/corporate-actions/"
        ]
        
        found_data = False
        for endpoint in candidates:
            status, data = check_endpoint(endpoint)
            print(f"  Endpoint {endpoint} -> {status}")
            
            if status == 'success':
                print(f"    Success fetching {endpoint}!")
                try:
                    jdata = json.loads(data)
                    results.append({'symbol': symbol, 'endpoint': endpoint, 'status': 'success', 'data_snippet': str(jdata)[:200]})
                    found_data = True
                except:
                    results.append({'symbol': symbol, 'endpoint': endpoint, 'status': 'success', 'data_snippet': 'HTML content'})
                    found_data = True
                    
            elif status == 'login_redirect':
                results.append({'symbol': symbol, 'endpoint': endpoint, 'status': 'login_redirect', 'data_snippet': ''})
                
        if not found_data:
            print(f"  No unauthenticated endpoints with data found for {symbol}.")
            
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'endpoint', 'status', 'data_snippet'])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\\nDone. Output saved to {out_path}")

if __name__ == '__main__':
    main()
