import requests

urls = [
    "https://trendlyne.com/equity/corporate-actions/bonus/USASEEDS/upsurge-seeds-of-agriculture-ltd/",
    "https://trendlyne.com/equity/bonus/USASEEDS/upsurge-seeds-of-agriculture-ltd/",
    "https://trendlyne.com/equity/corporate-action/bonus/USASEEDS/upsurge-seeds-of-agriculture-ltd/",
    "https://www.moneycontrol.com/company-facts/upsurgeseedsofagriculture/bonus/USA",
    "https://www.moneycontrol.com/company-facts/upsurgeseedsofagricultureltd/bonus/USA"
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for url in urls:
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"{url}: {res.status_code}")
    except Exception as e:
        print(f"{url}: {e}")

