"""
03m_scrape_missing_88.py
========================
Extracts the 88 unresolved "mismatch" stocks from xcheck_review.csv
and forces a scrape against Trendlyne and Investing.com to find
any missing corporate actions that NSE and Yahoo missed.
"""

import os
import sys
import csv
import time
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("=" * 60)
    log("Deep-Scraping the 88 Missing Stocks")
    log("=" * 60)

    xcheck_path = os.path.join(ROOT, 'data/master/review/xcheck_review.csv')
    uni_path = os.path.join(ROOT, 'data/master/universe.csv')

    if not os.path.exists(xcheck_path):
        log(f"Error: {xcheck_path} not found.")
        return

    # 1. Get the ISINs of the 88 missing stocks
    missing_isins = []
    with open(xcheck_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('isin'):
                missing_isins.append(row['isin'].strip())

    log(f"Found {len(missing_isins)} missing ISINs in xcheck_review.csv")

    # 2. Map ISINs to NSE/BSE symbols
    symbols_to_scrape = []
    with open(uni_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            isin = row.get('isin', '').strip()
            if isin in missing_isins:
                sym = row.get('nse_symbol', '').strip()
                if not sym:
                    sym = row.get('bse_script_code', '').strip()
                if sym:
                    symbols_to_scrape.append(sym)

    # Deduplicate
    symbols_to_scrape = list(dict.fromkeys(symbols_to_scrape))
    log(f"Mapped to {len(symbols_to_scrape)} unique symbols to scrape.")

    if not symbols_to_scrape:
        return

    # 3. Save symbols to a text file
    symbols_path = os.path.join(ROOT, 'data/raw/missing_88_symbols.txt')
    with open(symbols_path, 'w') as f:
        for sym in symbols_to_scrape:
            f.write(f"{sym}\n")

    # 4. Run Trendlyne Advanced Scraper
    trendlyne_script = os.path.join(ROOT, 'scrapers/corporate_actions_trendlyne_advanced.py')
    
    log("=" * 60)
    log("Launching Trendlyne Advanced Scraper (Stealth Mode)...")
    log(f"Command: python {trendlyne_script} {' '.join(symbols_to_scrape)}")
    log("=" * 60)
    
    # We will just print the command to run it via the sandbox next
    print(f"\nREADY_TO_RUN_TRENDLYNE: {trendlyne_script} {' '.join(symbols_to_scrape)}")


if __name__ == '__main__':
    main()
