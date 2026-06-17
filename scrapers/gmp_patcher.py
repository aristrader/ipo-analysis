"""GMP patcher — fills missing gmp_pct for year >= 2025 using InvestorGain + ipowatch fallback.

Fixes applied vs original:
  [Rule 1] Skip investorgain rows where gmp_tracked=False (placeholder 0.0). Computing
           gmp_pct=0 from a source placeholder is a fabrication; treat as missing instead.
  [Rule 2] Per-ISIN attempt log: every ISIN now records which sources were tried and their
           outcome ('ok' / 'ig_placeholder' / 'ig_no_match' / 'iw_ok' / 'iw_no_match' /
           'iw_error') so 96/97 silent-omissions become diagnosable.
           Raw is saved by investorgain.fetch_year() (already fixed) and ipowatch.match_and_extract()
           (already fixed). No extra save_raw needed here.
"""
import os
import re
import sys

import cloudscraper
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from investorgain import fetch_year
from ipowatch import match_and_extract


def clean_name(name):
    """Normalize company name to make matching easier."""
    n = re.sub(r'[^A-Za-z0-9 ]', ' ', str(name).lower())
    n = re.sub(r'\b(ltd|limited|pvt|private|the|ipo|company|co)\b', ' ', n)
    return re.sub(r'\s+', ' ', n).strip()


def main():
    # 1. Read master files from the frozen baseline (INPUT_ROOT).
    mb_path = config.src('master', 'mainboard.csv')
    sme_path = config.src('master', 'sme.csv')

    mb = pd.read_csv(mb_path)
    sme = pd.read_csv(sme_path)

    # Filter for year >= 2025 and gmp_pct is missing.
    mb_missing = mb[(mb['year'] >= 2025) & (mb['gmp_pct'].isna())].copy()
    sme_missing = sme[(sme['year'] >= 2025) & (sme['gmp_pct'].isna())].copy()

    df_missing = pd.concat([mb_missing, sme_missing], ignore_index=True)

    if df_missing.empty:
        print("No missing GMP data for year >= 2025.")
        return

    print(f"Found {len(df_missing)} IPOs missing GMP for year >= 2025.")

    # 2. Fetch data from InvestorGain (fetch_year now saves raw JSON + emits gmp_tracked).
    scraper = cloudscraper.create_scraper()
    ig_data = []
    for y in [2025, 2026]:
        try:
            print(f"Fetching Investorgain data for {y}...")
            rows = fetch_year(scraper, y)
            ig_data.extend(rows)
        except Exception as e:
            print(f"Error fetching Investorgain {y}: {e}")

    # Build IG lookup DataFrame.
    ig_df = pd.DataFrame(ig_data) if ig_data else pd.DataFrame(
        columns=['name', 'clean_name', 'nse', 'bse', 'gmp_rs', 'gmp_tracked', 'ipo_price'])
    if not ig_df.empty:
        ig_df['clean_name'] = ig_df['name'].apply(clean_name)

    # 3. Patch missing.
    patched_rows = []
    attempt_log = []   # per-ISIN attempt log: every ISIN recorded (Rule 2)

    for _, row in df_missing.iterrows():
        isin = row['isin']
        company = row['company_name']
        ipo_price = float(row['issue_price']) if pd.notna(row.get('issue_price')) else None

        c_name = clean_name(company)

        gmp_pct = None
        gmp_source = None
        attempt_notes = []

        # --- Try InvestorGain ---
        match_ig = None
        if not ig_df.empty:
            # Match by BSE code (most precise).
            if pd.notna(row.get('bse_script_code')) and str(row.get('bse_script_code')).strip():
                try:
                    bse_code = str(int(float(row['bse_script_code'])))
                    m = ig_df[ig_df['bse'] == bse_code]
                    if not m.empty:
                        match_ig = m.iloc[0]
                except (ValueError, TypeError):
                    pass

            # Match by NSE symbol.
            if match_ig is None and pd.notna(row.get('nse_symbol')) and str(row.get('nse_symbol')).strip():
                m = ig_df[ig_df['nse'] == str(row['nse_symbol']).strip()]
                if not m.empty:
                    match_ig = m.iloc[0]

            # Match by normalized name (last resort for IG).
            if match_ig is None:
                m = ig_df[ig_df['clean_name'] == c_name]
                if not m.empty:
                    match_ig = m.iloc[0]

        if match_ig is not None:
            # [Rule 1] Only use the value if InvestorGain actually tracked this IPO's GMP.
            # gmp_tracked=False means the source returned a placeholder 0 ("never tracked");
            # computing gmp_pct from that would fabricate a 0% GMP.
            if match_ig.get('gmp_tracked') and pd.notna(match_ig.get('gmp_rs')):
                g_rs = match_ig['gmp_rs']
                i_pr = match_ig['ipo_price'] if pd.notna(match_ig.get('ipo_price')) else ipo_price
                if g_rs is not None and i_pr:
                    gmp_pct = round((g_rs / i_pr) * 100, 2)
                    gmp_source = 'investorgain'
                    attempt_notes.append('ig:ok')
            else:
                # Placeholder zero — skip it (this was the Rule 1 bug: 96/97 rows computed 0%).
                attempt_notes.append('ig:placeholder')
        else:
            attempt_notes.append('ig:no_match')

        # --- Fallback to ipowatch ---
        if gmp_pct is None:
            print(f"Trying IPOWatch fallback for {company}...")
            try:
                res = match_and_extract(
                    company,
                    row.get('open_date'), row.get('close_date'), row.get('listing_date'),
                    isin=isin,
                )
                if res and res.get('gmp_rs') is not None and ipo_price:
                    gmp_pct = round((res['gmp_rs'] / ipo_price) * 100, 2)
                    gmp_source = 'ipowatch'
                    attempt_notes.append('iw:ok')
                else:
                    attempt_notes.append('iw:no_match')
            except Exception as e:
                print(f"Error IPOWatch fallback for {company}: {e}")
                attempt_notes.append(f'iw:error({type(e).__name__})')

        # [Rule 2] Record every ISIN's attempt outcome regardless of success.
        attempt_log.append({
            'isin': isin,
            'company_name': company,
            'sources_tried': ','.join(attempt_notes),
            'outcome': 'patched' if gmp_pct is not None else 'unresolved',
            'gmp_pct': gmp_pct,
            'gmp_source': gmp_source,
        })

        if gmp_pct is not None:
            patched_rows.append({
                'isin': isin,
                'company_name': company,
                'gmp_pct': gmp_pct,
                'gmp_source': gmp_source,
            })
            print(f"Patched {company} -> {gmp_pct}% ({gmp_source})")
        else:
            print(f"Could not patch {company} (tried: {','.join(attempt_notes)})")

    # 4. Save results.
    config.ensure(config.raw_dir())
    out_path = str(config.raw_dir() / 'gmp_patch_2025_2026.csv')
    log_path = str(config.raw_dir() / 'gmp_patch_attempt_log.csv')

    if patched_rows:
        out_df = pd.DataFrame(patched_rows)
        out_df.to_csv(out_path, index=False)
        print(f"Saved {len(out_df)} patched records to {out_path}.")
    else:
        print("No GMP data could be retrieved.")

    # Always write the attempt log — the per-ISIN audit trail (Rule 2).
    log_df = pd.DataFrame(attempt_log)
    log_df.to_csv(log_path, index=False)
    patched_n = sum(1 for x in attempt_log if x['outcome'] == 'patched')
    unresolved_n = sum(1 for x in attempt_log if x['outcome'] == 'unresolved')
    print(f"Attempt log: {len(attempt_log)} ISINs — patched={patched_n} unresolved={unresolved_n} → {log_path}")


if __name__ == '__main__':
    main()
