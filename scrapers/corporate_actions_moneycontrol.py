import os
import time
import json
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_mc_details(symbol):
    """Fetch the company slug and sc_id from Moneycontrol autosuggest API given an NSE symbol."""
    url = f"https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&type=1&format=json&query={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        for item in data:
            # Match the exact symbol in the 'pdt_dis_nm' field, e.g. ", RELIANCE,"
            if f", {symbol}," in item.get('pdt_dis_nm', '').upper() or symbol.upper() == item.get('sc_id', '').upper():
                link = item['link_src']
                parts = link.strip('/').split('/')
                # The format is typically: .../stockpricequote/<sector>/<slug>/<sc_id>
                sc_id = parts[-1]
                slug = parts[-2]
                return slug, sc_id
                
        # Fallback if no exact match, return the first one
        if data:
            link = data[0]['link_src']
            parts = link.strip('/').split('/')
            sc_id = parts[-1]
            slug = parts[-2]
            return slug, sc_id
    except Exception as e:
        print(f"Error fetching details for {symbol}: {e}")
    return None, None

def get_corporate_actions(symbol):
    """Scrape the corporate actions (Splits and Bonuses) for a given symbol."""
    slug, sc_id = get_mc_details(symbol)
    if not slug or not sc_id:
        print(f"Could not resolve Moneycontrol URL for symbol: {symbol}")
        return None, None

    # Setup headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    def scrape_table(action_type):
        url = f"https://www.moneycontrol.com/company-facts/{slug}/{action_type}/{sc_id}"
        print(f"Scraping {action_type.capitalize()} from: {url}")
        driver.get(url)
        
        # Wait for the table to render
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            time.sleep(2) # Give a short delay for data population
            
            tables = driver.find_elements(By.TAG_NAME, "table")
            if not tables:
                return pd.DataFrame()
                
            # Usually the first table contains the relevant data
            target_table = tables[0]
            rows = target_table.find_elements(By.TAG_NAME, "tr")
            
            if len(rows) <= 1:
                return pd.DataFrame()
                
            headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th") or rows[0].find_elements(By.TAG_NAME, "td")]
            
            data = []
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) == len(headers):
                    data.append([col.text.strip() for col in cols])
                    
            df = pd.DataFrame(data, columns=headers)
            df['Symbol'] = symbol
            df['Type'] = action_type.capitalize()
            return df
        except Exception as e:
            print(f"Could not extract {action_type} table: {e}")
            return pd.DataFrame()

    try:
        splits_df = scrape_table('splits')
        bonus_df = scrape_table('bonus')
    finally:
        driver.quit()

    return splits_df, bonus_df

if __name__ == "__main__":
    symbol = "RELIANCE"
    splits_df, bonus_df = get_corporate_actions(symbol)
    
    all_actions = []
    if splits_df is not None and not splits_df.empty:
        all_actions.append(splits_df)
    if bonus_df is not None and not bonus_df.empty:
        all_actions.append(bonus_df)
        
    if all_actions:
        final_df = pd.concat(all_actions, ignore_index=True)
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'moneycontrol_splits_sample.csv')
        final_df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
        print(final_df)
    else:
        print(f"No corporate action data found for {symbol}.")
