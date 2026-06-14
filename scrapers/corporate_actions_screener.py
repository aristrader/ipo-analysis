import requests
import pandas as pd
import json
import argparse
import sys
import os

def get_company_id(symbol, session):
    """Resolve NSE symbol to Screener company ID."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    search_url = f"https://www.screener.in/api/company/search/?q={symbol}&v=3"
    response = session.get(search_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    # Try to find exact match in URL
    for item in data:
        parts = [p for p in item.get('url', '').split('/') if p]
        if symbol.upper() in parts:
            return item['id']
            
    # Fallback to first result if no exact match found
    if data:
        return data[0]['id']
    return None

def fetch_corporate_actions(symbol, session=None):
    """Fetch corporate actions (Splits and Bonuses) for a given symbol from Screener."""
    if session is None:
        session = requests.Session()
    
    company_id = get_company_id(symbol, session)
    if not company_id:
        print(f"Could not find company ID for symbol: {symbol}")
        return pd.DataFrame()
        
    print(f"Found Company ID {company_id} for {symbol}")
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',  # Necessary for fetching the modal HTML
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    actions_url = f"https://www.screener.in/company/actions/{company_id}/"
    response = session.get(actions_url, headers=headers)
    
    if response.status_code == 200:
        if 'Login' in response.text or 'Register' in response.text:
            print(f"Warning: Screener.in might require login to view corporate actions for {symbol}. Pass a valid session cookie.")
        
        try:
            tables = pd.read_html(response.text)
            if not tables:
                print(f"No tables found in the corporate actions page for {symbol}")
                return pd.DataFrame()
                
            # Usually corporate actions tables contain Action, Ex-Date, Purpose
            actions_df = pd.DataFrame()
            for t in tables:
                actions_df = pd.concat([actions_df, t], ignore_index=True)
                
            if not actions_df.empty:
                # Filter for Splits and Bonuses if those columns exist
                # This depends on the exact table structure returned by Screener
                actions_df['Symbol'] = symbol
                
            return actions_df
        except ValueError as e:
            print(f"Error parsing HTML tables (likely redirected to login or empty table): {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
    else:
        print(f"Failed to fetch corporate actions. Status code: {response.status_code}")
        return pd.DataFrame()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape corporate actions (Splits, Bonus) from Screener.in')
    parser.add_argument('--symbol', type=str, default='RELIANCE', help='NSE Symbol to scrape')
    parser.add_argument('--cookie', type=str, help='Session cookie (if required to bypass login redirect)')
    parser.add_argument('--output', type=str, default='screener_splits_sample.csv', help='Output CSV file path')
    
    args = parser.parse_args()
    
    session = requests.Session()
    if args.cookie:
        session.headers.update({'Cookie': args.cookie})
        
    print(f"Fetching corporate actions for {args.symbol}...")
    df = fetch_corporate_actions(args.symbol, session)
    
    if not df.empty:
        os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
        df.to_csv(args.output, index=False)
        print(f"Successfully saved corporate actions for {args.symbol} to {args.output}")
        print(df.head())
    else:
        print(f"No data retrieved for {args.symbol}. It might require authentication.")
