import urllib.request
import urllib.parse
import json
import re

def ddg_search(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        urls = re.findall(r'<a class="result__url" href="([^"]+)"', html)
        print(json.dumps(urls[:5], indent=2))
    except Exception as e:
        print(e)

ddg_search("site:trendlyne.com USASEEDS bonus")
