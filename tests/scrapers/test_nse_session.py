"""Tests for the shared NSE session priming + that both scrapers delegate to it.

prime_nse_session does live network priming, so these tests verify the WIRING
(signature, constant, and that corp_actions/nse_subscription import-resolve the shared
primer through their self-bootstrapping `from nse_session import ...`) — not the live
HTTP, which needs the network.
"""
import inspect


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
