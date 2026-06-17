"""
03l_merge_corporate_actions.py
==============================
Consolidates corporate actions into a final master reference file:
1. Starts with the authoritative NSE data.
2. For the 16 ratio mismatches, it explicitly keeps the NSE authoritative ratio.
3. Appends the 354 valid Yahoo-only events (missing from NSE), with corrected
   action_type and ISIN handling:
     - ratio_factor < 1.0  -> action_type='consolidation' (NOT 'split')
     - event matched in corp_actions_matches -> inherit nse_action_type from match
     - otherwise           -> action_type='unknown'  (NOT hardcoded 'split')
     - BSE numeric-code symbols -> resolved to ISIN via universe if possible,
       else marked 'unmatched_bse_code' in source and left with isin=''.

Rule: NEVER fabricate action_type='split' for an event we cannot confirm is a split
(it corrupts adjusted prices on reverse-splits / consolidations).

Output: data/reference/corp_actions_merged.csv
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from foundation import ingest  # for ingest.ratios_equal


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Pure helpers (extracted for testability) ────────────────────────────────

def infer_action_type(yahoo_ratio, matched_nse_action_type=None):
    """Infer action_type for a Yahoo-only row. Never hardcodes 'split'.

    Rules (in priority order):
    1. If ratio_factor < 1.0               -> 'consolidation'  (reverse-split)
    2. If we have a matched NSE action_type -> inherit it
    3. Otherwise                           -> 'unknown'

    Args:
        yahoo_ratio: numeric ratio factor (float).
        matched_nse_action_type: the nse_action_type from corp_actions_matches, or None.

    Returns: str action_type.
    """
    if yahoo_ratio is not None and yahoo_ratio < 1.0:
        return 'consolidation'
    if matched_nse_action_type:
        return matched_nse_action_type
    return 'unknown'


def resolve_isin(symbol, is_bse_code, bse_code_to_isin):
    """Resolve a BSE numeric-code symbol to an ISIN via the universe map.

    Returns (isin, resolved) where resolved=True means the lookup succeeded.
    If is_bse_code is False or lookup fails, returns ('', False).
    """
    if not is_bse_code:
        return '', False
    isin = bse_code_to_isin.get(str(symbol).strip())
    if isin:
        return isin, True
    return '', False


# ── Universe ISIN lookup: BSE script code -> ISIN ───────────────────────────

def build_bse_code_to_isin():
    """Scan the four universe masters, return {bse_script_code_str: isin}."""
    mapping = {}
    for name in ['mainboard', 'sme', 'longterm_mainboard', 'longterm_sme']:
        path = os.path.join(ROOT, 'data', 'master', f'{name}.csv')
        if not os.path.exists(path):
            continue
        for row in csv.DictReader(open(path, encoding='utf-8')):
            code = (row.get('bse_script_code') or '').strip()
            isin = (row.get('isin') or '').strip()
            if code and isin and code not in mapping:
                mapping[code] = isin
    return mapping


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

    # 3. Load the matches table to inherit action_type for matched events.
    #    Key: (symbol, yahoo_date) -> nse_action_type
    matches_path = os.path.join(ROOT, 'data/reference/corp_actions_matches.csv')
    match_key_to_type = {}
    if os.path.exists(matches_path):
        for row in csv.DictReader(open(matches_path, encoding='utf-8')):
            sym = (row.get('symbol') or '').strip()
            dt  = (row.get('yahoo_date') or '').strip()
            atype = (row.get('nse_action_type') or '').strip()
            if sym and dt and atype:
                match_key_to_type[(sym, dt)] = atype
        log(f"Loaded {len(match_key_to_type)} match entries for action_type inheritance.")
    else:
        log("WARNING: corp_actions_matches.csv not found; action_type inheritance disabled.")

    # 4. Build BSE script-code -> ISIN lookup for resolving numeric-code rows.
    bse_code_to_isin = build_bse_code_to_isin()
    log(f"Built BSE code->ISIN map: {len(bse_code_to_isin)} entries.")

    # 5. Convert Yahoo-only to NSE columns with corrected action_type and ISIN.
    yahoo_converted = []
    n_consolidation = 0
    n_inherited = 0
    n_unknown = 0
    n_isin_resolved = 0
    n_isin_unmatched = 0

    for _, row in yahoo_df.iterrows():
        sym = str(row['symbol']).strip()
        ydate = str(row['yahoo_date']).strip()
        yahoo_ratio = float(row['yahoo_ratio'])
        is_bse_code = str(row.get('is_bse_code', '')).strip().lower() == 'true'

        # Determine action_type: ratio<1 -> consolidation; matched -> inherit; else unknown
        matched_nse_atype = match_key_to_type.get((sym, ydate))
        atype = infer_action_type(yahoo_ratio, matched_nse_atype)

        # Track stats
        if atype == 'consolidation':
            n_consolidation += 1
        elif matched_nse_atype:
            n_inherited += 1
        else:
            n_unknown += 1

        # Resolve ISIN for BSE-numeric-code rows
        isin, resolved = resolve_isin(sym, is_bse_code, bse_code_to_isin)
        source_tag = 'yfinance'
        if is_bse_code:
            if resolved:
                n_isin_resolved += 1
            else:
                n_isin_unmatched += 1
                source_tag = 'yfinance:unmatched_bse_code'

        yahoo_converted.append({
            'isin':         isin,
            'symbol':       sym,
            'action_type':  atype,
            'raw_subject':  f"Yahoo Finance (Ratio: {yahoo_ratio})",
            'ratio_factor': yahoo_ratio,
            'ex_date':      ydate,
            'source':       source_tag,
        })

    yahoo_converted_df = pd.DataFrame(yahoo_converted)
    log(f"Yahoo converted: consolidation={n_consolidation}, inherited_nse_type={n_inherited}, "
        f"unknown={n_unknown}")
    log(f"BSE-code rows: isin_resolved={n_isin_resolved}, isin_unmatched={n_isin_unmatched}")

    # 6. Merge NSE authoritative + Yahoo gap-fills
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
