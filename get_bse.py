import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# BSE API for corporate actions
url = "https://api.bseindia.com/BseIndiaAPI/api/CorporateAction/w?scripcode=543501"
res = requests.get(url, headers=headers)
print(res.text)
