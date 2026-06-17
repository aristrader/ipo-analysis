import urllib.request
import urllib.parse
import re

def search(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        links = re.findall(r'<a class="result__url" href="([^"]+)">([^<]+)</a>', html)
        for link, text in links:
            print(text.strip(), urllib.parse.unquote(link))
    except Exception as e:
        print("Error:", e)

search("SELMC stock split bonus history moneycontrol")
search("SELMC nclt capital reduction 2021 BSE corporate action")
