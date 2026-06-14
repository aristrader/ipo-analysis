"""
03h_yfinance_corp_actions.py
============================
Bulk-scrape corporate actions (Splits & Bonuses) from Yahoo Finance
for the entire IPO universe using multi-threaded fetch.

Usage:
    python -u pipeline/03h_yfinance_corp_actions.py

Notes:
    - Yahoo Finance handles 20+ concurrent workers (~112 req/s) without banning.
    - See docs/scraper_tps_limits.md for rate limit documentation.
    - ticker.splits returns None for delisted/SME stocks (handled gracefully).
"""

import csv
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from scrapers.corporate_actions_yfinance import fetch_corporate_actions


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("=" * 60)
    log("Yahoo Finance Corporate Actions Bulk Scraper")
    log("=" * 60)

    rows = list(csv.DictReader(open('data/master/universe.csv')))
    symbols = []
    # yfinance uses .NS for NSE and .BO for BSE
    for r in rows:
        if r.get('nse_symbol'):
            symbols.append(r['nse_symbol'].strip() + '.NS')
        elif r.get('bse_script_code'):
            symbols.append(r['bse_script_code'].strip() + '.BO')

    log(f"Total symbols to query: {len(symbols)}")

    out_path = 'data/raw/yfinance_corporate_actions.csv'

    # Use the multi-threaded fetch (20 workers) for the entire batch at once
    log("Starting multi-threaded fetch with 20 workers...")
    start = time.time()
    result_df = fetch_corporate_actions(symbols)
    elapsed = time.time() - start

    if not result_df.empty:
        result_df.to_csv(out_path, index=False)
        log(f"Saved {len(result_df)} corporate actions to {out_path}")
        log(f"Unique symbols with actions: {result_df['Symbol'].nunique()}")
        log(f"Elapsed time: {elapsed:.1f}s ({len(symbols)/elapsed:.1f} symbols/sec)")
    else:
        log("No corporate actions found.")

    log("Done.")


if __name__ == '__main__':
    main()
