import yfinance as yf
import pandas as pd
import os
import argparse
import concurrent.futures

def fetch_corporate_actions(symbols):
    all_splits = []
    
    def process_symbol(symbol):
        try:
            print(f"Fetching data for {symbol}...")
            ticker = yf.Ticker(symbol)
            splits = ticker.splits
            if splits is not None and not splits.empty:
                df = splits.reset_index()
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df.columns = ['Date', 'Split_Ratio']
                df['Symbol'] = symbol
                return df
            else:
                return None
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    # Use 20 concurrent workers to max out the safe API limit
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process_symbol, symbols))
        
    for result in results:
        if result is not None:
            all_splits.append(result)
            
    if all_splits:
        result_df = pd.concat(all_splits, ignore_index=True)
        # Rearrange columns
        result_df = result_df[['Symbol', 'Date', 'Split_Ratio']]
        # Sort by Symbol and Date (descending)
        result_df = result_df.sort_values(by=['Symbol', 'Date'], ascending=[True, False]).reset_index(drop=True)
        return result_df
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch historical Corporate Actions (Splits and Bonuses) using yfinance.")
    parser.add_argument("--symbols", nargs="+", default=["RELIANCE.NS"], help="List of stock symbols to fetch (e.g., RELIANCE.NS TCS.NS)")
    parser.add_argument("--output", type=str, default="data/raw/yfinance_splits_sample.csv", help="Output CSV file path")
    
    args = parser.parse_args()
    
    print(f"Symbols to fetch: {args.symbols}")
    
    df = fetch_corporate_actions(args.symbols)
    
    if not df.empty:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"Successfully saved corporate actions to {args.output}")
        print("Preview:")
        print(df.head(10))
    else:
        print("No corporate actions to save.")
