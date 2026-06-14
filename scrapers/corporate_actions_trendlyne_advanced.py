"""Advanced scraper for Trendlyne Corporate Actions (Splits/Bonuses) bypassing Cloudflare.

This script uses multiple advanced techniques to bypass Cloudflare protection:
1. curl_cffi (Chrome impersonation)
2. Playwright with stealth settings

Usage:
  python corporate_actions_trendlyne_advanced.py RELIANCE TCS
"""

import os
import sys
import time
import csv
import json
import logging
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_with_curl_cffi(url):
    """Attempt to fetch the URL using curl_cffi with Chrome impersonation."""
    try:
        from curl_cffi import requests
        logger.info(f"Attempting to fetch {url} with curl_cffi...")
        r = requests.get(url, impersonate="chrome110", timeout=15)
        if "Cloudflare" in r.text or "Just a moment..." in r.text or r.status_code == 403:
            logger.warning("Cloudflare detected with curl_cffi.")
            return None
        return r.text
    except ImportError:
        logger.error("curl_cffi not installed. Try: pip install curl_cffi")
        return None
    except Exception as e:
        logger.error(f"curl_cffi error: {e}")
        return None

def fetch_with_playwright(url):
    """Attempt to fetch the URL using Playwright with stealth plugins."""
    try:
        from playwright.sync_api import sync_playwright
        logger.info(f"Attempting to fetch {url} with Playwright...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            # Add stealth script
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait a bit to let any CF challenges complete
            time.sleep(5)
            
            if "Cloudflare" in page.content() or "Just a moment" in page.content():
                logger.info("Playwright hit Cloudflare challenge, waiting to see if it clears...")
                time.sleep(10)
            
            content = page.content()
            browser.close()
            
            if "Cloudflare" in content or "Just a moment" in content:
                logger.warning("Could not bypass Cloudflare with Playwright.")
                return None
            return content
            
    except ImportError:
        logger.error("Playwright not installed. Try: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None

def get_trendlyne_url_for_symbol(symbol):
    """
    Finds the specific Trendlyne URL (with ID) for a given symbol.
    Uses duckduckgo search as a workaround if direct Trendlyne search fails.
    """
    try:
        from curl_cffi import requests
        search_url = f"https://duckduckgo.com/html/?q=site:trendlyne.com/equity/corporate-actions/ {symbol}"
        r = requests.get(search_url, impersonate="chrome110", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href')
            if href and 'trendlyne.com/equity/corporate-actions' in href and symbol.upper() in href.upper():
                # Extract the actual URL
                return "https://" + href.split('//')[-1].strip()
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
    
    # Fallback to direct guess if we can't search
    logger.warning("Could not find exact URL, falling back to basic guess.")
    return f"https://trendlyne.com/equity/corporate-actions/{symbol}/"

def parse_corporate_actions(html_content, symbol):
    """
    Parses the Trendlyne Corporate Actions HTML to extract splits and bonuses.
    """
    records = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # This selector depends on Trendlyne's actual DOM structure
    # As an approximation, we look for tables or divs containing "Split" or "Bonus"
    tables = soup.find_all('table')
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all('th')]
        if not headers:
            continue
            
        for row in table.find_all('tr')[1:]:
            cols = [td.text.strip() for td in row.find_all('td')]
            if len(cols) == len(headers):
                row_data = dict(zip(headers, cols))
                
                # Check if this row represents a split or bonus
                purpose = ""
                for key in row_data:
                    if 'purpose' in key or 'action' in key or 'subject' in key:
                        purpose = row_data[key]
                        break
                
                if 'split' in purpose.lower() or 'bonus' in purpose.lower():
                    records.append({
                        'symbol': symbol,
                        'action_type': 'split' if 'split' in purpose.lower() else 'bonus',
                        'raw_subject': purpose,
                        'ex_date': row_data.get('ex-date', row_data.get('date', '')),
                        'source': 'trendlyne'
                    })
    return records

def process_symbol(symbol):
    logger.info(f"Processing {symbol}...")
    url = get_trendlyne_url_for_symbol(symbol)
    if not url:
        logger.error(f"Could not determine URL for {symbol}")
        return []
    
    logger.info(f"Target URL: {url}")
    
    # Try fast curl_cffi first
    html = fetch_with_curl_cffi(url)
    
    # Fallback to Playwright
    if not html:
        logger.info("Falling back to Playwright...")
        html = fetch_with_playwright(url)
        
    if not html:
        logger.error(f"Failed to fetch content for {symbol} after all attempts.")
        return []
        
    logger.info(f"Successfully fetched page for {symbol}. Parsing data...")
    records = parse_corporate_actions(html, symbol)
    logger.info(f"Found {len(records)} corporate actions for {symbol}.")
    return records

def main():
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ['RELIANCE']
    
    all_records = []
    for symbol in symbols:
        records = process_symbol(symbol)
        all_records.extend(records)
        time.sleep(2) # be polite between symbols
        
    if not all_records:
        logger.warning("No records extracted.")
        return
        
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'trendlyne_splits_sample_advanced.csv')
    
    fields = ['symbol', 'action_type', 'raw_subject', 'ex_date', 'source']
    
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_records)
        
    logger.info(f"Saved {len(all_records)} records to {out_path}")

if __name__ == '__main__':
    main()
