"""
03k_reconcile_corporate_actions.py
===================================
Cross-validate corporate actions data across multiple sources:
  1. NSE API (authoritative) — data/reference/corp_actions.csv
  2. Yahoo Finance           — data/raw/yfinance_corporate_actions.csv
  3. Moneycontrol (SME)      — data/raw/moneycontrol_corporate_actions.csv (when available)

Output:
  - data/reference/corp_actions_reconciled.csv   — final merged dataset
  - data/reference/corp_actions_discrepancies.csv — flagged conflicts for human review
  - data/reference/corp_actions_yahoo_only.csv   — actions Yahoo found but NSE missed

Usage:
    python -u pipeline/03k_reconcile_corporate_actions.py
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_nse_data():
    """Load the authoritative NSE corp_actions.csv."""
    path = os.path.join(ROOT, 'data/reference/corp_actions.csv')
    if not os.path.exists(path):
        log(f"WARNING: NSE data not found at {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df['ex_date'] = pd.to_datetime(df['ex_date'], errors='coerce')
    df['ratio_factor'] = pd.to_numeric(df['ratio_factor'], errors='coerce')
    df['source_file'] = 'nse'
    log(f"NSE data: {len(df)} records loaded")
    log(f"  Splits: {len(df[df['action_type'] == 'split'])}")
    log(f"  Bonuses: {len(df[df['action_type'] == 'bonus'])}")
    log(f"  Combined: {len(df[df['action_type'] == 'bonus+split'])}")
    log(f"  Date range: {df['ex_date'].min()} to {df['ex_date'].max()}")
    log(f"  Unique symbols: {df['symbol'].nunique()}")
    return df


def load_yahoo_data():
    """Load the Yahoo Finance yfinance_corporate_actions.csv.

    Yahoo reports both splits and bonuses as 'Stock Splits' with a numeric ratio.
    It uses .NS/.BO suffixed symbols.
    """
    path = os.path.join(ROOT, 'data/raw/yfinance_corporate_actions.csv')
    if not os.path.exists(path):
        log(f"WARNING: Yahoo data not found at {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Split_Ratio'] = pd.to_numeric(df['Split_Ratio'], errors='coerce')

    # Normalize symbol: strip .NS/.BO suffix
    df['symbol_clean'] = df['Symbol'].str.replace(r'\.(NS|BO)$', '', regex=True)
    # Also remove numeric-only BO codes (like '543244')
    df['is_bse_code'] = df['symbol_clean'].str.match(r'^\d+$')

    log(f"Yahoo data: {len(df)} records loaded")
    log(f"  Unique symbols: {df['Symbol'].nunique()}")
    log(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")

    # Deduplicate: Yahoo often reports the same event on consecutive days.
    # Group by symbol + ratio, and if two events are within 7 days, keep only the first.
    deduped = []
    for sym, group in df.groupby('symbol_clean'):
        group = group.sort_values('Date')
        prev_date = None
        prev_ratio = None
        for _, row in group.iterrows():
            if (prev_date is not None and prev_ratio == row['Split_Ratio']
                    and abs((row['Date'] - prev_date).days) <= 7):
                continue  # skip duplicate
            deduped.append(row)
            prev_date = row['Date']
            prev_ratio = row['Split_Ratio']

    deduped_df = pd.DataFrame(deduped)
    log(f"Yahoo after dedup: {len(deduped_df)} records (removed {len(df) - len(deduped_df)} duplicates)")
    return deduped_df


def load_moneycontrol_data():
    """Load Moneycontrol data if available."""
    path = os.path.join(ROOT, 'data/raw/moneycontrol_corporate_actions.csv')
    if not os.path.exists(path):
        log("Moneycontrol data not available yet — skipping")
        return pd.DataFrame()
    df = pd.read_csv(path)
    log(f"Moneycontrol data: {len(df)} records loaded")
    return df


def reconcile(nse_df, yahoo_df):
    """Cross-reference NSE and Yahoo data to find matches, gaps, and discrepancies."""

    log("=" * 60)
    log("RECONCILIATION: NSE vs Yahoo Finance")
    log("=" * 60)

    if nse_df.empty or yahoo_df.empty:
        log("Cannot reconcile — one or both datasets are empty")
        return [], [], []

    # Build NSE lookup: symbol -> list of (ex_date, ratio_factor, action_type)
    nse_lookup = defaultdict(list)
    for _, row in nse_df.iterrows():
        sym = str(row['symbol']).strip().upper()
        nse_lookup[sym].append({
            'ex_date': row['ex_date'],
            'ratio_factor': row['ratio_factor'],
            'action_type': row['action_type'],
            'raw_subject': row.get('raw_subject', ''),
            'isin': row.get('isin', ''),
        })

    matches = []        # Yahoo event matches an NSE event
    yahoo_only = []     # Yahoo found something NSE doesn't have
    discrepancies = []  # Both have it but ratios don't match

    for _, yrow in yahoo_df.iterrows():
        sym = str(yrow['symbol_clean']).strip().upper()
        y_date = yrow['Date']
        y_ratio = yrow['Split_Ratio']

        if pd.isna(y_date) or pd.isna(y_ratio):
            continue

        # Skip tiny ratios (likely dividends misclassified as splits)
        if y_ratio <= 1.01 and y_ratio >= 0.99:
            continue

        # Search NSE for a matching event: same symbol, date within 10 days, similar ratio
        nse_events = nse_lookup.get(sym, [])
        best_match = None
        best_date_diff = None

        for nse_event in nse_events:
            nse_date = nse_event['ex_date']
            if pd.isna(nse_date):
                continue
            date_diff = abs((y_date - nse_date).days)
            if date_diff <= 10:
                if best_match is None or date_diff < best_date_diff:
                    best_match = nse_event
                    best_date_diff = date_diff

        if best_match:
            nse_ratio = best_match['ratio_factor']
            ratio_diff = abs(y_ratio - nse_ratio)
            # Check if ratios are close enough (within 5% tolerance)
            if nse_ratio > 0 and ratio_diff / nse_ratio > 0.05:
                discrepancies.append({
                    'symbol': sym,
                    'yahoo_date': y_date.strftime('%Y-%m-%d'),
                    'nse_date': best_match['ex_date'].strftime('%Y-%m-%d'),
                    'yahoo_ratio': y_ratio,
                    'nse_ratio': nse_ratio,
                    'nse_action_type': best_match['action_type'],
                    'nse_raw_subject': best_match['raw_subject'],
                    'date_diff_days': best_date_diff,
                    'status': 'RATIO_MISMATCH',
                })
            else:
                matches.append({
                    'symbol': sym,
                    'yahoo_date': y_date.strftime('%Y-%m-%d'),
                    'nse_date': best_match['ex_date'].strftime('%Y-%m-%d'),
                    'yahoo_ratio': y_ratio,
                    'nse_ratio': nse_ratio,
                    'nse_action_type': best_match['action_type'],
                    'date_diff_days': best_date_diff,
                    'status': 'MATCH',
                })
        else:
            yahoo_only.append({
                'symbol': sym,
                'original_symbol': yrow['Symbol'],
                'yahoo_date': y_date.strftime('%Y-%m-%d'),
                'yahoo_ratio': y_ratio,
                'is_bse_code': yrow.get('is_bse_code', False),
                'status': 'YAHOO_ONLY',
            })

    log(f"Results:")
    log(f"  Exact matches:   {len(matches)}")
    log(f"  Yahoo-only:      {len(yahoo_only)}")
    log(f"  Ratio mismatches: {len(discrepancies)}")

    return matches, yahoo_only, discrepancies


def save_results(matches, yahoo_only, discrepancies):
    """Save reconciliation results to CSV files."""
    out_dir = os.path.join(ROOT, 'data/reference')

    if discrepancies:
        df = pd.DataFrame(discrepancies)
        path = os.path.join(out_dir, 'corp_actions_discrepancies.csv')
        df.to_csv(path, index=False)
        log(f"Saved {len(df)} discrepancies to {path}")
        log("TOP DISCREPANCIES:")
        for _, row in df.head(20).iterrows():
            log(f"  {row['symbol']}: Yahoo={row['yahoo_ratio']} vs NSE={row['nse_ratio']} "
                f"(Yahoo date={row['yahoo_date']}, NSE date={row['nse_date']}, "
                f"type={row['nse_action_type']})")

    if yahoo_only:
        df = pd.DataFrame(yahoo_only)
        path = os.path.join(out_dir, 'corp_actions_yahoo_only.csv')
        df.to_csv(path, index=False)
        log(f"Saved {len(df)} Yahoo-only records to {path}")
        # Show examples
        log("SAMPLE YAHOO-ONLY (potential gaps in NSE data):")
        for _, row in df[~df['is_bse_code']].head(20).iterrows():
            log(f"  {row['symbol']}: ratio={row['yahoo_ratio']} date={row['yahoo_date']}")

    if matches:
        df = pd.DataFrame(matches)
        path = os.path.join(out_dir, 'corp_actions_matches.csv')
        df.to_csv(path, index=False)
        log(f"Saved {len(df)} confirmed matches to {path}")


def main():
    log("=" * 60)
    log("Corporate Actions Reconciliation Engine")
    log("=" * 60)

    nse_df = load_nse_data()
    yahoo_df = load_yahoo_data()
    mc_df = load_moneycontrol_data()

    matches, yahoo_only, discrepancies = reconcile(nse_df, yahoo_df)
    save_results(matches, yahoo_only, discrepancies)

    # Summary statistics
    log("")
    log("=" * 60)
    log("FINAL SUMMARY")
    log("=" * 60)
    log(f"NSE (authoritative):    {len(nse_df)} records")
    log(f"Yahoo Finance:          {len(yahoo_df)} records (after dedup)")
    log(f"Moneycontrol:           {len(mc_df)} records")
    log(f"")
    log(f"Cross-validation:")
    log(f"  Confirmed matches:    {len(matches)}")
    log(f"  Yahoo-only (gaps):    {len(yahoo_only)}")
    log(f"  Ratio mismatches:     {len(discrepancies)}")
    log(f"")

    if discrepancies:
        log("⚠️  ACTION REQUIRED: Review discrepancies in data/reference/corp_actions_discrepancies.csv")
    if yahoo_only:
        log("⚠️  ACTION REQUIRED: Review Yahoo-only records in data/reference/corp_actions_yahoo_only.csv")
        log("   These may be corporate actions missing from the NSE dataset.")

    log("=" * 60)
    log("Reconciliation complete.")


if __name__ == '__main__':
    main()
