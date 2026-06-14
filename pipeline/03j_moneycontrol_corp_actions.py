"""
03j_moneycontrol_corp_actions.py
================================
Bulk-scrape corporate actions (Splits & Bonuses) from Moneycontrol
for the SME stocks that Yahoo Finance could not resolve.

Usage:
    python -u pipeline/03j_moneycontrol_corp_actions.py

Logs:
    - Prints timestamped progress to stdout (use -u for unbuffered)
    - Saves incremental results every 5 symbols to prevent data loss
"""

import sys
import os
import time
import traceback
import pandas as pd
from datetime import datetime

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scrapers.corporate_actions_moneycontrol import get_corporate_actions


def log(msg):
    """Print a timestamped log message with flush."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    log("=" * 60)
    log("Moneycontrol Corporate Actions Scraper - Starting")
    log("=" * 60)

    missing_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'yfinance_missing_symbols.txt')
    if not os.path.exists(missing_path):
        log(f"ERROR: Missing symbols file not found at {missing_path}")
        return

    with open(missing_path, 'r') as f:
        raw_lines = [line.strip() for line in f if line.strip()]
    log(f"Read {len(raw_lines)} raw lines from {missing_path}")

    # Strip Yahoo-specific suffixes (.NS and .BO) and deduplicate
    symbols = [line.replace('.NS', '').replace('.BO', '') for line in raw_lines]
    symbols = list(dict.fromkeys(symbols))  # deduplicate preserving order
    log(f"After dedup: {len(symbols)} unique symbols to query")

    out_path = os.path.join(PROJECT_ROOT, 'data', 'raw', 'moneycontrol_corporate_actions.csv')
    all_actions = []
    skipped_symbols = set()

    # Resume logic
    if os.path.exists(out_path):
        existing_df = pd.read_csv(out_path)
        skipped_symbols = set(existing_df['Symbol'].unique())
        all_actions.append(existing_df)
        symbols = [s for s in symbols if s not in skipped_symbols]
        log(f"RESUME: {len(skipped_symbols)} already fetched. {len(symbols)} remaining.")
    else:
        log("No existing output file found. Starting fresh.")

    if not symbols:
        log("Nothing to do — all symbols already scraped!")
        return

    log(f"Starting scrape of {len(symbols)} symbols...")
    log("-" * 60)

    success_count = 0
    error_count = 0
    no_data_count = 0
    total = len(symbols)

    for i, sym in enumerate(symbols, 1):
        try:
            log(f"[{i}/{total}] Scraping {sym}...")
            splits_df, bonus_df = get_corporate_actions(sym)

            found_splits = splits_df is not None and not splits_df.empty
            found_bonus = bonus_df is not None and not bonus_df.empty

            if found_splits:
                all_actions.append(splits_df)
                log(f"  -> Found {len(splits_df)} split(s) for {sym}")
            if found_bonus:
                all_actions.append(bonus_df)
                log(f"  -> Found {len(bonus_df)} bonus(es) for {sym}")
            if not found_splits and not found_bonus:
                no_data_count += 1
                log(f"  -> No corporate actions found for {sym}")

            success_count += 1

        except Exception as e:
            error_count += 1
            log(f"  !! ERROR scraping {sym}: {e}")
            log(f"     Traceback: {traceback.format_exc().strip()}")

        # Incremental save every 5 symbols
        if i % 5 == 0 and all_actions:
            merged = pd.concat(all_actions, ignore_index=True)
            merged.to_csv(out_path, index=False)
            log(f"  [CHECKPOINT] Saved {len(merged)} rows to {out_path}")
            log(f"  [PROGRESS] Success={success_count} | NoData={no_data_count} | Errors={error_count} | Remaining={total - i}")

    # Final save
    if all_actions:
        final_df = pd.concat(all_actions, ignore_index=True)
        final_df.to_csv(out_path, index=False)
        log("=" * 60)
        log(f"DONE! Final save: {len(final_df)} total rows to {out_path}")
        log(f"Summary: Success={success_count} | NoData={no_data_count} | Errors={error_count}")
        log("=" * 60)
    else:
        log("No corporate actions found across all symbols.")


if __name__ == '__main__':
    main()
