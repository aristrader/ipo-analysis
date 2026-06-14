"""
03l_merge_corporate_actions.py
==============================
Consolidates corporate actions into a final master reference file:
1. Starts with the authoritative NSE data.
2. For the 16 ratio mismatches, it explicitly keeps the NSE authoritative ratio.
3. Appends the 354 valid Yahoo-only events (missing from NSE).
4. (Will append Moneycontrol data later once it finishes).

Output: data/reference/corp_actions_merged.csv
"""

import os
import sys
import pandas as pd
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("=" * 60)
    log("Corporate Actions Consolidation Engine")
    log("=" * 60)

    # 1. Load the authoritative NSE data
    nse_path = os.path.join(ROOT, 'data/reference/corp_actions.csv')
    nse_df = pd.read_csv(nse_path)
    log(f"Loaded {len(nse_df)} authoritative NSE records.")

    # 2. Load the Yahoo-only data (the gaps we found)
    yahoo_path = os.path.join(ROOT, 'data/reference/corp_actions_yahoo_only.csv')
    yahoo_df = pd.read_csv(yahoo_path)
    log(f"Loaded {len(yahoo_df)} Yahoo-only records.")

    # Convert Yahoo-only to match NSE columns
    # NSE fields: isin, symbol, action_type, raw_subject, ratio_factor, ex_date, source
    yahoo_converted = []
    for _, row in yahoo_df.iterrows():
        yahoo_converted.append({
            'isin': '',  # Yahoo doesn't provide ISINs
            'symbol': row['symbol'],
            'action_type': 'split',  # Yahoo calls everything a split
            'raw_subject': f"Yahoo Finance (Ratio: {row['yahoo_ratio']})",
            'ratio_factor': row['yahoo_ratio'],
            'ex_date': row['yahoo_date'],
            'source': 'yfinance'
        })
        
    yahoo_converted_df = pd.DataFrame(yahoo_converted)
    
    # 3. Merge them together
    merged_df = pd.concat([nse_df, yahoo_converted_df], ignore_index=True)
    
    # Sort by ex_date descending
    merged_df['ex_date'] = pd.to_datetime(merged_df['ex_date'], errors='coerce')
    merged_df = merged_df.sort_values(by=['symbol', 'ex_date'], ascending=[True, False])
    
    # Format date back to string
    merged_df['ex_date'] = merged_df['ex_date'].dt.strftime('%Y-%m-%d')
    
    out_path = os.path.join(ROOT, 'data/reference/corp_actions_merged.csv')
    merged_df.to_csv(out_path, index=False)
    
    log(f"Success! Saved {len(merged_df)} total records to {out_path}")
    log(f"  NSE Authoritative: {len(nse_df)}")
    log(f"  Yahoo gap-fills:   {len(yahoo_converted_df)}")
    log("=" * 60)


if __name__ == '__main__':
    main()
