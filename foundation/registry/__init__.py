"""foundation/registry — the column registry: load + named-function code registry + meta-validator.

columns.yaml declares every column; this module (a) loads it (rejecting duplicate keys), (b) maps the
YAML's parser/validator NAMES to real callables (metadata stays data, logic stays code), and (c) validates
the file each run so a typo'd parser, a missing field, a bad family/status, or a non-string vocab value is
caught before it bites. The schema doc + lineage are generated from here in Phase 8 — never hand-maintain
docs/schema.md.

    from foundation import registry
    registry.assert_valid()                  # raises if columns.yaml is inconsistent
    cols = registry.load()["columns"]        # the declared columns
    registry.PARSERS["parse_num"]            # -> the actual ingest.num callable
"""
import datetime
from pathlib import Path

import yaml

from foundation import ingest

REGISTRY_PATH = Path(__file__).resolve().parent / "columns.yaml"


# ── named-function code registry (columns.yaml refers to these BY NAME) ──────────
def _passthrough(x):
    """No-op parser for derived / config-computed values (already clean)."""
    return x


def _parse_date(x):
    """Normalize a date to ISO 'YYYY-MM-DD', or None. Accepts ISO + a few common Indian-source forms."""
    s = ingest.text(x)
    if s is None:
        return None
    s = s[:10] if "T" in s else s
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%b %d, %Y", "%d-%b-%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


_TRUE = {"true", "1", "yes", "y", "t"}
_FALSE = {"false", "0", "no", "n", "f"}


def _parse_bool(x):
    s = ingest.text(x)
    if s is None:
        return None
    s = s.lower()
    return True if s in _TRUE else (False if s in _FALSE else None)


def _validate_isin(v):
    """INE-form equity ISIN: 12 chars, 'INE' prefix, alphanumeric. None passes (handled via _prov).

    Rejects malformed numeric BSE codes (e.g. NPST '409536'). Verified: all 2,384 substrate ISINs are INE-form.
    """
    if v is None:
        return True
    return isinstance(v, str) and len(v) == 12 and v[:3] == "INE" and v.isalnum()


def _subscription_x_valid(v, context=None):
    """sub_total_x validity: a 0 is REAL for SME (genuine no-demand) but MASKED-MISSING for MB.

    Context-aware — board disambiguates (per columns.yaml). A 0 with no board context cannot be
    trusted, so it fails closed (-> Missing_data); Phase-2 assembly always threads `board`. Negative
    subscription is never valid. None passes (classify() already nulls a missing value upstream).
    """
    if v is None:
        return True
    if v < 0:
        return False
    if v == 0:
        return (context or {}).get("board") == "SME"
    return True


def _validate_gmp_nonzero(v):
    """gmp_pct validity: a source 0 is a placeholder (never published), not a real premium.

    Negative GMP (a grey-market discount) is REAL and valid; only 0 is rejected. None passes.
    """
    return v is None or v != 0


PARSERS = {
    "parse_text": ingest.text,            # strip; '' / placeholders -> None
    "parse_num": ingest.num,              # number or None; never mints 0
    "parse_pct": ingest.pct,              # percentage; never mints 0
    "parse_ratio": ingest.ratio_parts,    # 'a:b' -> (a, b); compare with ingest.ratios_equal (tolerant)
    "parse_date": _parse_date,            # -> ISO 'YYYY-MM-DD' or None
    "parse_bool": _parse_bool,            # -> True/False/None
    "parse_derived": _passthrough,        # value passes through; the 'derived' _prov stamp is set in assembly
    "parse_passthrough": _passthrough,    # config-computed / already clean
}

VALIDATORS = {
    "validate_isin": _validate_isin,
    "validate_nonneg": lambda v: v is None or v >= 0,
    "validate_positive": lambda v: v is None or v > 0,
    "subscription_x_valid": _subscription_x_valid,   # context-aware (board): MB 0x = masked-missing
    "validate_gmp_nonzero": _validate_gmp_nonzero,    # source 0 = placeholder; negative GMP is real
}

# ── allowed vocabularies (the meta-validator enforces these) ─────────────────────
ALLOWED_DTYPE = {"str", "float", "int", "bool", "date", "enum"}
ALLOWED_STATUS = {"active", "planned", "retired"}
ALLOWED_ASOF = {"static", "at_ipo", "current"}
ALLOWED_APPLICABILITY = {"all", "ipo", "equity", "sme", "mainboard", "non_equity"}
ALLOWED_FAMILY = set("ABCDEFGHIJK")
REQUIRED_FIELDS = {"dtype", "family", "sources", "parser", "validator",
                   "as_of", "prov", "applicability", "status", "description"}


# ── duplicate-key-safe YAML loader (last-key-wins silently corrupts at scale) ────
class _DupSafeLoader(yaml.SafeLoader):
    pass


def _no_dup_mapping(loader, node, deep=False):
    seen = set()
    for k_node, _ in node.value:
        k = loader.construct_object(k_node, deep=deep)
        if k in seen:
            raise ValueError(f"duplicate key {k!r} in columns.yaml")
        seen.add(k)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_DupSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)


def load(path=REGISTRY_PATH):
    """Parse columns.yaml into a dict (raises ValueError on duplicate keys)."""
    return yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_DupSafeLoader)


def _is_in(value, allowed):
    """Membership test that won't crash if `value` is unhashable (e.g. a list written by mistake)."""
    try:
        return value in allowed
    except TypeError:
        return False


def validate(data):
    """Return a list of human-readable problems with a loaded registry dict (empty = valid)."""
    cols = data.get("columns") if isinstance(data, dict) else None
    if not isinstance(cols, dict) or not cols:
        return ["registry has no columns mapping"]
    errors = []
    for name, e in cols.items():
        if not isinstance(e, dict):
            errors.append(f"{name}: entry is not a mapping")
            continue
        missing = REQUIRED_FIELDS - set(e)
        if missing:
            errors.append(f"{name}: missing field(s) {sorted(missing)}")
        if not _is_in(e.get("dtype"), ALLOWED_DTYPE):
            errors.append(f"{name}: bad dtype {e.get('dtype')!r}")
        if not _is_in(e.get("family"), ALLOWED_FAMILY):
            errors.append(f"{name}: bad family {e.get('family')!r} (must be A..K)")
        if not _is_in(e.get("status"), ALLOWED_STATUS):
            errors.append(f"{name}: bad status {e.get('status')!r}")
        if not _is_in(e.get("as_of"), ALLOWED_ASOF):
            errors.append(f"{name}: bad as_of {e.get('as_of')!r}")
        if not _is_in(e.get("applicability"), ALLOWED_APPLICABILITY):
            errors.append(f"{name}: bad applicability {e.get('applicability')!r}")
        if not isinstance(e.get("prov"), bool):
            errors.append(f"{name}: prov must be true/false")
        if not isinstance(e.get("sources"), list):
            errors.append(f"{name}: sources must be a list")
        if not str(e.get("description") or "").strip():
            errors.append(f"{name}: description must be non-empty")
        parser = e.get("parser")
        if parser is not None and parser not in PARSERS:
            errors.append(f"{name}: unknown parser {parser!r} (not in PARSERS)")
        validator = e.get("validator")
        if validator is not None and validator not in VALIDATORS:
            errors.append(f"{name}: unknown validator {validator!r} (not in VALIDATORS)")
        if e.get("status") == "retired" and not e.get("retired_reason"):
            errors.append(f"{name}: retired column needs a retired_reason")
        if e.get("dtype") == "enum" and "allowed_values" in e:
            av = e.get("allowed_values")
            if not isinstance(av, list) or not av:
                errors.append(f"{name}: enum allowed_values must be a non-empty list")
    return errors


def assert_valid(path=REGISTRY_PATH):
    """Load + validate; raise ValueError listing every problem if invalid."""
    errors = validate(load(path))
    if errors:
        raise ValueError("columns.yaml is invalid:\n  - " + "\n  - ".join(errors))


def active_columns(data=None):
    """Names of columns that are actually materialized (status == active)."""
    data = data or load()
    return [n for n, e in (data.get("columns") or {}).items() if e.get("status") == "active"]


def prov_columns(data=None):
    """Names of columns that carry a companion _prov code (the _prov column is generated in assembly)."""
    data = data or load()
    return [n for n, e in (data.get("columns") or {}).items() if e.get("prov")]
