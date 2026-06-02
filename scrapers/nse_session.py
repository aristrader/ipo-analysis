"""Shared NSE anti-bot session priming (curl_cffi).

corp_actions.py and nse_subscription.py both need a curl_cffi 'chrome'-impersonated
session with NSE's anti-bot cookies primed (hit the home page, then the page-specific
Referer). The priming flow is consolidated here so the part most likely to change —
how you get past NSE's bot protection — lives in ONE place. The Referer differs per
scraper, so it is a parameter.

Deliberately NOT named scrapers/http.py: that would shadow the stdlib `http` module
(which curl_cffi / requests / urllib all import) because a script's own directory is
placed on sys.path[0] when run as `python scrapers/<x>.py`.
"""
from curl_cffi import requests as cr

NSE_HOME = 'https://www.nseindia.com'


def prime_nse_session(referer):
    """Return a curl_cffi session with NSE anti-bot cookies set (home page + referer)."""
    s = cr.Session(impersonate='chrome')
    s.get(NSE_HOME, timeout=20)
    s.get(referer, timeout=20)
    return s
