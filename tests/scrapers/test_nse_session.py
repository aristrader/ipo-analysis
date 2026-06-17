"""Tests for the shared NSE session priming + that both scrapers delegate to it.

prime_nse_session does live network priming, so these tests verify the WIRING
(signature, constant, and that corp_actions/nse_subscription import-resolve the shared
primer through their self-bootstrapping `from nse_session import ...`) — not the live
HTTP, which needs the network.

_check_prime_response IS pure (takes a response-like object) so we test it directly.
"""
import inspect
import types

import pytest


def test_prime_nse_session_signature_and_constant(nse_session_mod):
    assert nse_session_mod.NSE_HOME == "https://www.nseindia.com"
    sig = inspect.signature(nse_session_mod.prime_nse_session)
    assert list(sig.parameters) == ["referer"]


def test_corp_actions_prime_shim_resolves(corp_actions_mod):
    # importing corp_actions must successfully resolve `from nse_session import ...`
    assert callable(corp_actions_mod.prime_session)
    assert callable(corp_actions_mod.prime_nse_session)


def test_nse_subscription_uses_shared_primer(nse_subscription_mod):
    assert callable(nse_subscription_mod.prime_session)
    assert callable(nse_subscription_mod.prime_nse_session)


# --- _check_prime_response: pure-function tests (no network) ---

def _fake_response(status_code, text="", content_type="application/json"):
    """Minimal response-like object for testing _check_prime_response."""
    r = types.SimpleNamespace()
    r.status_code = status_code
    r.text = text
    r.headers = {"content-type": content_type}
    return r


def test_check_prime_response_200_ok(nse_session_mod):
    # A clean 200 JSON response must not raise.
    r = _fake_response(200, text='{"data":[]}')
    nse_session_mod._check_prime_response(r, "https://www.nseindia.com")  # no exception


def test_check_prime_response_301_ok(nse_session_mod):
    # Redirects are acceptable priming responses.
    r = _fake_response(301, text="")
    nse_session_mod._check_prime_response(r, "https://www.nseindia.com/home")


def test_check_prime_response_403_raises(nse_session_mod):
    r = _fake_response(403, text="Forbidden")
    with pytest.raises(RuntimeError, match="403"):
        nse_session_mod._check_prime_response(r, "https://www.nseindia.com")


def test_check_prime_response_429_raises(nse_session_mod):
    r = _fake_response(429, text="Too Many Requests")
    with pytest.raises(RuntimeError, match="429"):
        nse_session_mod._check_prime_response(r, "https://www.nseindia.com")


def test_check_prime_response_cloudflare_challenge_raises(nse_session_mod):
    # Cloudflare challenge pages are served as 200 HTML but contain 'cf-chl'.
    challenge_html = (
        "<html><head><title>Just a moment...</title></head><body>"
        "<div id='cf-chl-widget-abc'>checking your browser</div>"
        "</body></html>"
    )
    r = _fake_response(200, text=challenge_html, content_type="text/html; charset=utf-8")
    with pytest.raises(RuntimeError, match="challenge"):
        nse_session_mod._check_prime_response(r, "https://www.nseindia.com")


def test_check_prime_response_plain_html_no_challenge_ok(nse_session_mod):
    # A normal HTML page (home page) that contains no challenge markers must not raise.
    normal_html = "<html><body><h1>NSE India</h1><p>Welcome to the National Stock Exchange</p></body></html>"
    r = _fake_response(200, text=normal_html, content_type="text/html; charset=utf-8")
    nse_session_mod._check_prime_response(r, "https://www.nseindia.com")  # no exception
