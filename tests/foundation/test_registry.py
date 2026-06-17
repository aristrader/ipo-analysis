"""Tests for foundation.registry — the column registry loader + code registry + meta-validator (T0.2)."""
import pytest

from foundation import ingest, registry


def _entry(**over):
    """A minimal VALID column entry; override fields to construct invalid cases."""
    e = dict(dtype="str", family="A", sources=[], parser="parse_text", validator=None,
             as_of="static", prov=False, applicability="all", status="active", description="x")
    e.update(over)
    return e


# ── the real shipped registry must be valid ──────────────────────────────────────
def test_real_registry_is_valid():
    registry.assert_valid()                      # raises if columns.yaml is inconsistent
    assert registry.validate(registry.load()) == []


def test_named_functions_resolve_to_callables():
    assert registry.PARSERS["parse_num"] is ingest.num
    assert registry.PARSERS["parse_text"] is ingest.text


def test_validate_isin_rejects_malformed_numeric_codes():
    assert registry.VALIDATORS["validate_isin"]("INE645S01016") is True   # real ISIN
    assert registry.VALIDATORS["validate_isin"]("409536") is False        # BSE numeric code -> not a key
    assert registry.VALIDATORS["validate_isin"](None) is True             # missing handled via _prov


# ── the meta-validator catches each kind of breakage ─────────────────────────────
def test_unknown_parser_flagged():
    errs = registry.validate({"columns": {"c": _entry(parser="nope")}})
    assert any("unknown parser" in e for e in errs)


def test_bad_dtype_flagged():
    errs = registry.validate({"columns": {"c": _entry(dtype="frobnicate")}})
    assert any("bad dtype" in e for e in errs)


def test_missing_field_flagged():
    e = _entry()
    del e["as_of"]
    errs = registry.validate({"columns": {"c": e}})
    assert any("missing field" in m and "as_of" in m for m in errs)


def test_retired_needs_reason():
    assert any("retired_reason" in e
               for e in registry.validate({"columns": {"c": _entry(status="retired")}}))
    ok = _entry(status="retired", retired_reason="superseded")
    assert registry.validate({"columns": {"c": ok}}) == []


def test_prov_must_be_bool():
    assert any("prov must be" in e for e in registry.validate({"columns": {"c": _entry(prov="yes")}}))


# ── lifecycle / helper views ─────────────────────────────────────────────────────
def test_active_columns_excludes_planned_and_retired():
    active = registry.active_columns()
    assert "board" in active
    assert "universe_type" not in active        # planned
    assert "market_cap_at_ipo_cr" not in active  # planned (BL-1)
    assert "pre_ipo_eps" not in active           # retired


def test_prov_columns_are_the_ambiguous_ones():
    prov = set(registry.prov_columns())
    assert {"ofs_cr", "sub_total_x", "gmp_pct", "min_investment_rs"} <= prov
    assert "isin" not in prov                    # non-ambiguous -> no _prov carrier


# ── hardening from the design review ─────────────────────────────────────────────
def test_isin_validator_requires_INE_prefix():
    v = registry.VALIDATORS["validate_isin"]
    assert v("INE645S01016") is True
    assert v("INF200K01884") is False            # mutual-fund ISIN — not an equity join key
    assert v("409536") is False                  # numeric BSE code


def test_list_applicability_does_not_crash():
    # an accidental list must yield an ERROR string, never a TypeError
    errs = registry.validate({"columns": {"c": _entry(applicability=["ipo", "sme"])}})
    assert any("applicability" in e for e in errs)


def test_bad_family_flagged():
    assert any("family" in e for e in registry.validate({"columns": {"c": _entry(family="Z")}}))


def test_empty_description_flagged():
    assert any("description" in e for e in registry.validate({"columns": {"c": _entry(description="  ")}}))


def test_enum_allowed_values_must_be_nonempty_list():
    bad = _entry(dtype="enum", allowed_values=[])
    assert any("allowed_values" in e for e in registry.validate({"columns": {"c": bad}}))
    assert registry.validate({"columns": {"c": _entry(dtype="enum", allowed_values=["x", "y"])}}) == []


def test_named_parser_roster_registered():
    for name in ("parse_ratio", "parse_date", "parse_bool", "parse_derived"):
        assert name in registry.PARSERS


def test_duplicate_column_keys_raise(tmp_path):
    p = tmp_path / "dup.yaml"
    p.write_text("columns:\n  c:\n    dtype: str\n  c:\n    dtype: int\n")
    with pytest.raises(ValueError):
        registry.load(p)
