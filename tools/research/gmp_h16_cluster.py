import pandas as pd
import numpy as np
import os

def analyze_gmp_clusters():
    df = pd.read_csv('data/master/ipo_analysis.csv', low_memory=False)
    
    # Filter valid rows
    df = df.dropna(subset=['listing_date', 'gmp_pct', 'alpha_1m'])
    df['listing_date'] = pd.to_datetime(df['listing_date'])
    df = df.sort_values('listing_date')
    
    clusters = []
    current_cluster = []
    
    for _, row in df.iterrows():
        if not current_cluster:
            current_cluster.append(row)
        else:
            last_date = current_cluster[-1]['listing_date']
            if (row['listing_date'] - last_date).days <= 3:
                current_cluster.append(row)
            else:
                clusters.append(current_cluster)
                current_cluster = [row]
    
    if current_cluster:
        clusters.append(current_cluster)
        
    cluster_records = []
    
    for i, cluster in enumerate(clusters):
        if len(cluster) >= 2:
            cdf = pd.DataFrame(cluster)
            cdf = cdf.sort_values('gmp_pct', ascending=False).reset_index(drop=True)
            
            rank1 = cdf.iloc[0]
            rank2 = cdf.iloc[1]
            
            cluster_records.append({
                'rank1_name': rank1['company_name'],
                'rank1_type': rank1['type'],
                'rank1_gmp_pct': rank1['gmp_pct'],
                'rank1_alpha_1m': rank1['alpha_1m'],
                'rank2_name': rank2['company_name'],
                'rank2_type': rank2['type'],
                'rank2_gmp_pct': rank2['gmp_pct'],
                'rank2_alpha_1m': rank2['alpha_1m'],
            })
            
    res_df = pd.DataFrame(cluster_records)
    
    res_df['rank1_outperforms'] = res_df['rank1_alpha_1m'] > res_df['rank2_alpha_1m']
    win_rate = res_df['rank1_outperforms'].mean()
    
    mean_alpha_rank1 = res_df['rank1_alpha_1m'].mean()
    mean_alpha_rank2 = res_df['rank2_alpha_1m'].mean()
    median_alpha_rank1 = res_df['rank1_alpha_1m'].median()
    median_alpha_rank2 = res_df['rank2_alpha_1m'].median()
    
    print("\n--- RESULTS (All IPO Clusters) ---")
    print(f"Total Clusters: {len(res_df)}")
    print(f"Win Rate (#1 outperforms #2): {win_rate:.2%}")
    print(f"Median 1M Alpha - Rank 1 (Highest GMP): {median_alpha_rank1:.2%}")
    print(f"Median 1M Alpha - Rank 2 (Second Highest): {median_alpha_rank2:.2%}")
    
    mb_df = res_df[(res_df['rank1_type'] == 'MB') & (res_df['rank2_type'] == 'MB')]
    if len(mb_df) > 0:
        mb_win_rate = mb_df['rank1_outperforms'].mean()
        mb_median1 = mb_df['rank1_alpha_1m'].median()
        mb_median2 = mb_df['rank2_alpha_1m'].median()
        
        print("\n--- RESULTS (Pure Mainboard Clusters) ---")
        print(f"Total MB pure clusters: {len(mb_df)}")
        print(f"Win Rate (#1 outperforms #2): {mb_win_rate:.2%}")
        print(f"Median 1M Alpha - Rank 1: {mb_median1:.2%}")
        print(f"Median 1M Alpha - Rank 2: {mb_median2:.2%}")

    sme_df = res_df[(res_df['rank1_type'] == 'SME') & (res_df['rank2_type'] == 'SME')]
    if len(sme_df) > 0:
        sme_win_rate = sme_df['rank1_outperforms'].mean()
        sme_median1 = sme_df['rank1_alpha_1m'].median()
        sme_median2 = sme_df['rank2_alpha_1m'].median()
        
        print("\n--- RESULTS (Pure SME Clusters) ---")
        print(f"Total SME pure clusters: {len(sme_df)}")
        print(f"Win Rate (#1 outperforms #2): {sme_win_rate:.2%}")
        print(f"Median 1M Alpha - Rank 1: {sme_median1:.2%}")
        print(f"Median 1M Alpha - Rank 2: {sme_median2:.2%}")

if __name__ == '__main__':
    analyze_gmp_clusters()
