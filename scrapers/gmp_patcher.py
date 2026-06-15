import pandas as pd
import numpy as np
import cloudscraper
import os
import re

# Import existing scrapers if we want to reuse them
from scrapers.investorgain import fetch_year
from scrapers.ipowatch import match_and_extract

def clean_name(name):
    """Normalize company name to make matching easier."""
    n = re.sub(r'[^A-Za-z0-9 ]', ' ', str(name).lower())
    n = re.sub(r'\b(ltd|limited|pvt|private|the|ipo|company|co)\b', ' ', n)
    return re.sub(r'\s+', ' ', n).strip()

def main():
    # 1. Read master files
    mb_path = 'data/master/mainboard.csv'
    sme_path = 'data/master/sme.csv'
    
    mb = pd.read_csv(mb_path)
    sme = pd.read_csv(sme_path)
    
    # Filter for year >= 2025 and gmp_pct is missing
    mb_missing = mb[(mb['year'] >= 2025) & (mb['gmp_pct'].isna())].copy()
    sme_missing = sme[(sme['year'] >= 2025) & (sme['gmp_pct'].isna())].copy()
    
    df_missing = pd.concat([mb_missing, sme_missing], ignore_index=True)
    
    if df_missing.empty:
        print("No missing GMP data for year >= 2025.")
        return
        
    print(f"Found {len(df_missing)} IPOs missing GMP for year >= 2025.")
    
    # 2. Fetch data from InvestorGain
    scraper = cloudscraper.create_scraper()
    ig_data = []
    for y in [2025, 2026]:
        try:
            print(f"Fetching Investorgain data for {y}...")
            rows = fetch_year(scraper, y)
            ig_data.extend(rows)
        except Exception as e:
            print(f"Error fetching Investorgain {y}: {e}")
            
    # Process IG data for matching
    ig_df = pd.DataFrame(ig_data)
    if not ig_df.empty:
        ig_df['clean_name'] = ig_df['name'].apply(clean_name)
    else:
        ig_df = pd.DataFrame(columns=['name', 'clean_name', 'nse', 'bse', 'gmp_rs', 'ipo_price'])

    # 3. Patch missing
    patched_rows = []
    
    for _, row in df_missing.iterrows():
        isin = row['isin']
        company = row['company_name']
        ipo_price = float(row['issue_price']) if pd.notna(row['issue_price']) else None
        
        c_name = clean_name(company)
        
        gmp_pct = None
        gmp_source = None
        
        # Try InvestorGain Match
        match_ig = None
        if not ig_df.empty:
            # Match by BSE code
            if pd.notna(row['bse_script_code']) and str(row['bse_script_code']).strip():
                try:
                    bse_code = str(int(float(row['bse_script_code'])))
                    m = ig_df[ig_df['bse'] == bse_code]
                    if not m.empty:
                        match_ig = m.iloc[0]
                except ValueError:
                    pass
            
            # Match by NSE symbol
            if match_ig is None and pd.notna(row['nse_symbol']) and str(row['nse_symbol']).strip():
                m = ig_df[ig_df['nse'] == str(row['nse_symbol']).strip()]
                if not m.empty:
                    match_ig = m.iloc[0]
                    
            # Match by Name
            if match_ig is None:
                m = ig_df[ig_df['clean_name'] == c_name]
                if not m.empty:
                    match_ig = m.iloc[0]
                    
        if match_ig is not None and pd.notna(match_ig.get('gmp_rs')):
            g_rs = match_ig['gmp_rs']
            i_pr = match_ig['ipo_price'] if pd.notna(match_ig.get('ipo_price')) else ipo_price
            if g_rs is not None and i_pr:
                gmp_pct = round((g_rs / i_pr) * 100, 2)
                gmp_source = 'investorgain'
                
        # Fallback to IPOWatch
        if gmp_pct is None:
            print(f"Trying IPOWatch fallback for {company}...")
            try:
                res = match_and_extract(company, row.get('open_date'), row.get('close_date'), row.get('listing_date'))
                if res and res.get('gmp_rs') is not None and ipo_price:
                    gmp_pct = round((res['gmp_rs'] / ipo_price) * 100, 2)
                    gmp_source = 'ipowatch'
            except Exception as e:
                print(f"Error IPOWatch fallback for {company}: {e}")
                
        if gmp_pct is not None:
            patched_rows.append({
                'isin': isin,
                'company_name': company,
                'gmp_pct': gmp_pct,
                'gmp_source': gmp_source
            })
            print(f"Patched {company} -> {gmp_pct}% ({gmp_source})")
        else:
            print(f"Could not patch {company}")
            
    # 4. Save results
    if patched_rows:
        out_df = pd.DataFrame(patched_rows)
        out_path = 'data/raw/gmp_patch_2025_2026.csv'
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        out_df.to_csv(out_path, index=False)
        print(f"Saved {len(out_df)} successfully scraped records to {out_path}.")
    else:
        print("No GMP data could be retrieved.")

if __name__ == '__main__':
    main()
