import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.nseindia.com', headers={'User-Agent': 'Mozilla/5.0'})
res = urllib.request.urlopen(req, context=ctx)
cookie = res.info().get('Set-Cookie')

req = urllib.request.Request('https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=SELMC', headers={'User-Agent': 'Mozilla/5.0', 'Cookie': cookie})
res = urllib.request.urlopen(req, context=ctx)
print(res.read().decode('utf-8'))
