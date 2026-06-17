import json
import re

with open('splits.html', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', content)
if match:
    data = json.loads(match.group(1))
    tabs = data.get('props', {}).get('pageProps', {}).get('data', {}).get('tabsData', {})
    print("Tabs data:", tabs)
else:
    print("No next data found")
