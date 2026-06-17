import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5'
}

session = requests.Session()
session.headers.update(headers)
session.get("https://www.nseindia.com")
res = session.get("https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=USASEEDS")
print(res.text)
