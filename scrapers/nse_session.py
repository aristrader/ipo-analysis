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

# Status codes that indicate a successful (or acceptable redirect) priming response.
_PRIME_OK_CODES = {200, 301, 302}

# Cloudflare/bot-challenge indicators in the response body.
_CHALLENGE_MARKERS = ("cf-chl", "cf_chl", "cloudflare", "just a moment", "checking your browser")


def _check_prime_response(r, label):
    """Raise RuntimeError if the priming response looks blocked or is a challenge page.

    Callers rely on a healthy session; a 403/429/Cloudflare-challenge response returned
    as if healthy would cause every subsequent API call to silently mint placeholders.
    """
    if r.status_code not in _PRIME_OK_CODES:
        raise RuntimeError(
            f"NSE session priming failed at {label!r}: HTTP {r.status_code} — "
            "session may be blocked (403/429) or rate-limited; aborting so callers "
            "know the session is not healthy."
        )
    body = (r.text or "").lower()
    # Detect a Cloudflare challenge page: these are served as 200 HTML but contain
    # 'cf-chl' or similar markers, and JSON callers would silently receive the HTML.
    if "text/html" in r.headers.get("content-type", "") or any(
        m in body for m in _CHALLENGE_MARKERS
    ):
        # Only flag as a challenge if challenge markers are actually present in the body.
        if any(m in body for m in _CHALLENGE_MARKERS):
            raise RuntimeError(
                f"NSE session priming returned a bot-challenge page at {label!r} "
                "(Cloudflare or similar); session is NOT healthy — callers should not proceed."
            )


def prime_nse_session(referer):
    """Return a curl_cffi session with NSE anti-bot cookies set (home page + referer).

    Raises RuntimeError if either priming GET returns a non-2xx/3xx status or a
    bot-challenge page — so callers know the session is blocked rather than treating
    a blocked/challenge response as empty data.
    """
    s = cr.Session(impersonate='chrome')
    r_home = s.get(NSE_HOME, timeout=20)
    _check_prime_response(r_home, NSE_HOME)
    r_ref = s.get(referer, timeout=20)
    _check_prime_response(r_ref, referer)
    return s
