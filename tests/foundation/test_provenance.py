"""Tests for foundation/provenance.py — the T1.1 `_prov` encoding engine.

These pin the honesty contract the data audit demanded (the "I1" root fix):
  - a REAL zero survives as `present` (protects the 725 genuine ofs_cr=0 rows);
  - a source PLACEHOLDER zero (MB `0.00x`) is `Missing_data`, NOT a fake zero;
  - blanks/placeholders are non-retryable `Missing_data`;
  - only OUR-side fetch/parse failures are retryable `error_out` (the refetch worklist, R2/G2);
  - inapplicable fields are `N/A`.
"""
import pytest

from foundation import ingest
from foundation import provenance as p


# ── code vocabulary ──────────────────────────────────────────────────────────
def test_codes_partition_into_has_value_and_null():
    assert set(p.CODES) == p.HAS_VALUE | p.NULL_CODES
    assert p.HAS_VALUE.isdisjoint(p.NULL_CODES)
    assert len(p.CODES) == 5
    assert p.HAS_VALUE == {p.PRESENT, p.DERIVED}
    assert p.NULL_CODES == {p.MISSING_DATA, p.ERROR_OUT, p.NA}


def test_retryable_is_only_error_out():
    assert p.retryable(p.ERROR_OUT) is True
    for code in (p.PRESENT, p.DERIVED, p.MISSING_DATA, p.NA):
        assert p.retryable(code) is False


# ── present: real values pass validate-before-stamp ──────────────────────────
def test_real_zero_is_present():
    """The 725 genuine ofs_cr=0 rows must NOT be destroyed."""
    r = p.classify("0", parser=ingest.num, validate=lambda v: v is None or v >= 0)
    assert r.code == p.PRESENT
    assert r.value == 0.0
    assert r.has_value


def test_positive_value_is_present():
    r = p.classify("2.5x", parser=ingest.num, validate=lambda v: v is None or v > 0)
    assert r.code == p.PRESENT
    assert r.value == 2.5


# ── missing_data: blanks, placeholders, source-side gaps (non-retryable) ─────
@pytest.mark.parametrize("raw", ["", "-", "   ", "N/A", "na", "--", "null"])
def test_blank_or_placeholder_text_is_missing_data(raw):
    r = p.classify(raw, parser=ingest.num)
    assert r.code == p.MISSING_DATA
    assert r.value is None
    assert not r.retryable


def test_http_error_is_missing_data():
    """A genuine 404 = the source has no page for this field — not our failure, not retryable."""
    r = p.classify(None, fetch_status=ingest.HTTP_ERROR, parser=ingest.num)
    assert r.code == p.MISSING_DATA
    assert not r.retryable


def test_empty_payload_is_missing_data_ignoring_stale_raw():
    """EMPTY (2xx, no payload) is a source gap — bucketed directly, never trusting a stale `raw`."""
    r = p.classify("999", fetch_status=ingest.EMPTY, parser=ingest.num)
    assert r.code == p.MISSING_DATA
    assert r.value is None
    assert not r.retryable


def test_value_parsed_but_fails_validity_is_missing_data():
    """A source placeholder that PARSES but fails its check (e.g. negative subscription) is not a real value."""
    r = p.classify("-3", parser=ingest.num, validate=lambda v: v is None or v >= 0)
    assert r.code == p.MISSING_DATA
    assert r.value is None
    assert not r.retryable


# ── the headline I1 case: the placeholder zero that parses to 0.0 ────────────
def test_mb_zero_subscription_is_masked_missing():
    """MB `0.00x` parses to 0.0 but is a masked-missing placeholder → Missing_data (board disambiguates)."""
    r = p.classify("0.00x", parser=ingest.num, validate=p.subscription_x_valid,
                   context={"board": "MB"})
    assert r.value is None
    assert r.code == p.MISSING_DATA
    assert not r.retryable  # re-scraping the same source won't cure a source placeholder


def test_sme_zero_subscription_is_real_present():
    """SME 0x can be a genuine no-demand zero → present."""
    r = p.classify("0", parser=ingest.num, validate=p.subscription_x_valid,
                   context={"board": "SME"})
    assert r.value == 0.0
    assert r.code == p.PRESENT


def test_subscription_x_valid_predicate_directly():
    assert p.subscription_x_valid(5.0) is True
    assert p.subscription_x_valid(0.0, {"board": "SME"}) is True
    assert p.subscription_x_valid(0.0, {"board": "MB"}) is False
    assert p.subscription_x_valid(-1.0) is False
    assert p.subscription_x_valid(None) is True  # None passes; classify() nulls it as Missing_data first
    assert p.subscription_x_valid(0.0) is False  # no board context → cannot trust a zero


# ── error_out: our-side failures only (the refetch worklist) ─────────────────
def test_network_error_is_error_out_retryable():
    r = p.classify("anything", fetch_status=ingest.NETWORK_ERROR, parser=ingest.num)
    assert r.code == p.ERROR_OUT
    assert r.value is None
    assert r.retryable


def test_blocked_is_error_out_retryable():
    r = p.classify("x", fetch_status=ingest.BLOCKED, parser=ingest.num)
    assert r.code == p.ERROR_OUT
    assert r.retryable


def test_parser_crash_is_error_out():
    """A parser bug on a value the source DID provide is our-side → retryable after we fix the parser."""
    def boom(x):
        raise ValueError("parser bug")
    r = p.classify("realvalue", parser=boom)
    assert r.code == p.ERROR_OUT
    assert r.retryable


# ── n/a: field does not apply to this row ────────────────────────────────────
def test_not_applicable_is_na():
    r = p.classify("5", applicable=False, parser=ingest.num)
    assert r.code == p.NA
    assert r.value is None
    assert not r.retryable


# ── derived helper (used by T1.3 arithmetic recovery) ────────────────────────
def test_derived_helper_stamps_value():
    r = p.derived(4.2)
    assert r.code == p.DERIVED
    assert r.value == 4.2
    assert r.has_value
    assert not r.retryable


# ── classify_column: pulls parser+validator from the registry by name ────────
def test_classify_column_ofs_cr_real_zero_present():
    r = p.classify_column("ofs_cr", "0")
    assert r.code == p.PRESENT
    assert r.value == 0.0  # validate_nonneg accepts a real 0


def test_classify_column_issue_price_positive_present():
    r = p.classify_column("issue_price", "120")
    assert r.code == p.PRESENT
    assert r.value == 120.0


def test_classify_column_issue_price_zero_fails_positive():
    r = p.classify_column("issue_price", "0")  # validate_positive rejects 0
    assert r.code == p.MISSING_DATA
    assert r.value is None


def test_classify_column_unknown_raises():
    with pytest.raises(KeyError):
        p.classify_column("does_not_exist", "1")


# ── the headline I1 fix MUST hold via the registry path (what Phase 2 uses) ──
def test_classify_column_sub_total_x_mb_placeholder_zero_is_missing():
    """The bug T1.1 exists to kill: MB `0.00x` parses to 0.0 but must NOT be stamped present."""
    r = p.classify_column("sub_total_x", "0.00x", context={"board": "MB"})
    assert r.value is None
    assert r.code == p.MISSING_DATA
    assert not r.retryable


def test_classify_column_sub_total_x_sme_zero_is_present():
    r = p.classify_column("sub_total_x", "0", context={"board": "SME"})
    assert r.value == 0.0
    assert r.code == p.PRESENT


def test_classify_column_sub_total_x_real_value_present():
    r = p.classify_column("sub_total_x", "12.4x", context={"board": "MB"})
    assert r.value == 12.4
    assert r.code == p.PRESENT


def test_classify_column_gmp_placeholder_zero_is_missing():
    r = p.classify_column("gmp_pct", "0")
    assert r.value is None
    assert r.code == p.MISSING_DATA


def test_classify_column_gmp_negative_is_real_present():
    """A grey-market DISCOUNT (negative GMP) is a real value, not a placeholder."""
    r = p.classify_column("gmp_pct", "-5")
    assert r.value == -5.0
    assert r.code == p.PRESENT


def test_classify_column_passthrough_enum_present():
    """A passthrough column with no validator: a non-None value stamps present (documents N1)."""
    r = p.classify_column("quality", "clean")
    assert r.value == "clean"
    assert r.code == p.PRESENT


# ── the context-aware validators are reachable (not dead code) ───────────────
def test_context_aware_validators_registered():
    from foundation import registry
    assert "subscription_x_valid" in registry.VALIDATORS
    assert "validate_gmp_nonzero" in registry.VALIDATORS


# ── honesty guards on the validate-before-stamp gate ─────────────────────────
def test_non_bool_validator_raises():
    """A validator returning truthy non-bool must NOT launder into present — it's a programming error."""
    with pytest.raises(TypeError):
        p.classify("5", parser=ingest.num, validate=lambda v: "yes")


def test_validator_exception_propagates():
    """A validator that raises is a code bug — it fails loud, not silently bucketed as a data state."""
    with pytest.raises(ZeroDivisionError):
        p.classify("5", parser=ingest.num, validate=lambda v: 1 / 0)


def test_two_arg_validator_arity_detected():
    r = p.classify("0", parser=ingest.num, validate=p.subscription_x_valid, context={"board": "SME"})
    assert r.code == p.PRESENT  # 2-arg validator called with context, not mis-called as 1-arg
