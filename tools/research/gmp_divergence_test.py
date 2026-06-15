import pandas as pd
from layer3 import spine

def run_gmp_test():
    print("Loading Substrate and calculating Baseline Divergence...")
    df = spine.load_substrate()
    df = df[df['gmp_pct'].notna()].copy()
    
    # Force numeric to prevent string math errors
    df['gmp_pct'] = pd.to_numeric(df['gmp_pct'], errors='coerce')
    df['issue_price_adj'] = pd.to_numeric(df['issue_price_adj'], errors='coerce')
    df['listing_open'] = pd.to_numeric(df['listing_open'], errors='coerce')
    
    # Calculate mathematically exact pop and divergence
    df['expected_pop_rs'] = df['issue_price_adj'] * (df['gmp_pct'] / 100.0)
    df['actual_pop_rs'] = df['listing_open'] - df['issue_price_adj']
    df['actual_pop_pct'] = (df['actual_pop_rs'] / df['issue_price_adj']) * 100
    
    # Avoid div by 0 for literal 0% GMP
    df['gmp_forecast_error'] = (df['actual_pop_rs'] - df['expected_pop_rs']) / df['expected_pop_rs'].replace(0, pd.NA)
    df['divergence_pts'] = df['actual_pop_pct'] - df['gmp_pct']
    
    for segment in ['MB', 'SME']:
        sub = spine.segment(df, segment=segment, cohort='boom').copy()
        sub = sub[sub['divergence_pts'].notna()]
        if len(sub) == 0: continue
        
        print(f"\n=== {segment.upper()} BOOM COHORT (N={len(sub)}) ===")
        
        # Layer 1: Baseline
        print("\n[Layer 1] Baseline GMP Forecast Error (% relative to premium):")
        err_dist = spine.distribution(sub['gmp_forecast_error'].dropna())
        print(f"Median Error: {err_dist['median']:.1%}")
        print(f"P10 (Massive Undershoot): {err_dist['p10']:.1%}")
        print(f"P90 (Massive Overshoot): {err_dist['p90']:.1%}")
        
        print("\n[Layer 1] Absolute Divergence Points (Actual Pop % - GMP %):")
        pts_dist = spine.distribution(sub['divergence_pts'].dropna())
        print(f"Median Miss: {pts_dist['median']:.1f} pts")
        print(f"P10 Miss: {pts_dist['p10']:.1f} pts")
        print(f"P90 Miss: {pts_dist['p90']:.1f} pts")
        
        # Layer 2: Drift
        print("\n[Layer 2] Surprise Drift (1-month Alpha vs Nifty)")
        try:
            sub['bucket'] = pd.qcut(sub['divergence_pts'], 5, labels=['1_Worst_Miss', '2_Bad', '3_Neutral', '4_Good', '5_Massive_Surprise'])
            
            for b in ['5_Massive_Surprise', '4_Good', '3_Neutral', '2_Bad', '1_Worst_Miss']:
                b_df = sub[sub['bucket'] == b]
                b_df_mature = spine.maturity_gated(b_df, '1m')
                alpha_dist = spine.distribution(spine.alpha_series(b_df_mature, '1m'))
                if alpha_dist['n'] > 0:
                    med_alpha = f"{alpha_dist['median']:>5.1f}%" if alpha_dist['median'] is not None else " N/A "
                    print(f"  {b:<20}: N={alpha_dist['n']:<3} | Median 1m Alpha = {med_alpha}")
        except Exception as e:
            print(f"Could not bucket {segment} (probably too many tied 0 values): {e}")

if __name__ == '__main__':
    run_gmp_test()
