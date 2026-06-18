"""foundation/provenance.py — the `_prov` encoding engine (Phase 1, task T1.1: the "I1" root fix).

THE PROBLEM IT CURES
--------------------
A cell that says `0` (or is blank) used to mean three different things that nobody could tell apart:
a REAL zero, a value the source NEVER published, or a fetch that BROKE on our side. That single
ambiguity corrupted the data (a naive "0 -> missing" sweep would destroy 725 genuine ofs_cr=0 rows).

THE FIX: split the value from "how we know it"
----------------------------------------------
For every genuinely-ambiguous field we keep TWO things — the value (NULL when we truly don't have it,
so math skips it) and a `_prov` code that records the state. There are exactly five codes:

    present       a real value the source published AND it passed its validity check
    derived       we computed it from other fields with a validated formula (stamped by T1.3)
    Missing_data  the source never published it / returned a placeholder — re-scraping won't help
    error_out     OUR fetch or parser failed — retryable; THIS is the refetch worklist (R2/G2)
    N/A           the field does not apply to this row (e.g. an SME-only field on a mainboard IPO)

`present`/`derived` carry a value; `Missing_data`/`error_out`/`N/A` carry NULL.

THE GOLDEN RULE: VALIDATE BEFORE YOU STAMP
------------------------------------------
A value earns `present` only after passing its validity check. This is what stops "provenance
laundering" — the old bug where a placeholder `0.00x` (which parses to a real-looking 0.0) got
stamped as if the source really meant zero. `classify()` runs the check first; a parsed-but-invalid
value falls to `Missing_data`, never `present`.

THE REFETCH-BUCKET RULE (R2/G2)
-------------------------------
Only `error_out` is retryable. A network/blocked fetch or a parser crash is OUR failure and worth
retrying. A source blank or a source placeholder is the SOURCE's gap — re-scraping the same page
won't cure it, so it is `Missing_data` and stays off the refetch worklist.

    from foundation import provenance as p
    r = p.classify("0.00x", parser=ingest.num, validate=p.subscription_x_valid, context={"board": "MB"})
    r.code   -> "Missing_data"   # masked-missing placeholder, not a real zero
    r.value  -> None

Phase 2 (spine assembly) calls this engine as it materializes each `prov: true` column; T1.3 uses
`derived()` for arithmetic recoveries. This module only builds the MECHANISM.
"""
import inspect
from dataclasses import dataclass

from foundation import ingest, registry

# ── the five canonical codes ─────────────────────────────────────────────────
PRESENT = "present"
DERIVED = "derived"
MISSING_DATA = "Missing_data"
ERROR_OUT = "error_out"
NA = "N/A"

CODES = (PRESENT, DERIVED, MISSING_DATA, ERROR_OUT, NA)
HAS_VALUE = frozenset({PRESENT, DERIVED})              # these carry a real value
NULL_CODES = frozenset({MISSING_DATA, ERROR_OUT, NA})  # for these the value is NULL


def retryable(code):
    """Belongs on the refetch worklist? Only `error_out` (our-side fetch/parse failure) — R2/G2.

    A source blank / placeholder is `Missing_data` (re-scraping the same source won't cure it).
    """
    return code == ERROR_OUT


@dataclass(frozen=True)
class Prov:
    """The outcome of classifying one field value: the cleaned value (or None) + its `_prov` code."""
    value: object
    code: str

    @property
    def has_value(self):
        return self.code in HAS_VALUE

    @property
    def retryable(self):
        return retryable(self.code)


def _identity(x):
    return x


def _run_validate(validate, value, context):
    """Run a validity predicate, supporting both 1-arg `f(value)` and 2-arg `f(value, context)` forms.

    Honesty guards: a validator MUST return a real bool — a non-bool result is a programming error
    and raises (we never coerce truthy garbage into a `present` stamp). A validator that *raises* is
    also a programming error and propagates loudly (fail fast — a code bug is not a data state to
    silently bucket as `error_out`/`Missing_data`).
    """
    if validate is None:
        return True
    try:
        nparams = len(inspect.signature(validate).parameters)
    except (TypeError, ValueError):
        nparams = 1
    result = validate(value, context) if nparams >= 2 else validate(value)
    if not isinstance(result, bool):
        raise TypeError("validator %r must return bool, got %r"
                        % (getattr(validate, "__name__", validate), result))
    return result


def classify(raw, *, applicable=True, fetch_status=ingest.OK, parser=None, validate=None, context=None):
    """Classify one raw field value into a `Prov(value, code)` — the heart of the I1 fix.

    Args:
        raw:          the raw cell as the source gave it (str / number / None).
        applicable:   does this field apply to this row? False -> N/A.
        fetch_status: the ingest.fetch outcome for the source call (OK / EMPTY / HTTP_ERROR /
                      BLOCKED / NETWORK_ERROR). Defaults to OK for values already in hand.
        parser:       raw -> cleaned value or None (e.g. ingest.num). Defaults to identity.
        validate:     value(+context) -> bool. The validate-BEFORE-stamp gate. None = always valid.
        context:      optional row context for cross-aware predicates (e.g. {"board": "MB"}).

    Decision order (first match wins):
        not applicable                          -> N/A
        our fetch failed (network / blocked)    -> error_out    (retryable; the refetch worklist)
        HTTP error (404) or empty 2xx payload   -> Missing_data (source has nothing here)
        our parser crashed                      -> error_out    (our bug; retryable after a fix)
        parser returned None (blank/placeholder)-> Missing_data
        parsed value FAILS its validity check   -> Missing_data (placeholder that looked real)
        parsed value PASSES                     -> present
    """
    if not applicable:
        return Prov(None, NA)

    # OUR-side fetch failure -> retryable.
    if fetch_status in (ingest.NETWORK_ERROR, ingest.BLOCKED):
        return Prov(None, ERROR_OUT)
    # A genuine HTTP error (e.g. 404) or an empty 2xx payload means the source has nothing here ->
    # not our failure, not retryable. (EMPTY is bucketed directly, never trusting a stale `raw`.)
    if fetch_status in (ingest.HTTP_ERROR, ingest.EMPTY):
        return Prov(None, MISSING_DATA)
    # OK: the source responded with a payload -> parse + validate below.

    parser = parser or _identity
    try:
        value = parser(raw)
    except Exception:
        # The source DID provide something our parser choked on -> our bug, retryable once fixed.
        return Prov(None, ERROR_OUT)

    if value is None:
        # Blank, or a placeholder the parser correctly rejected ("-", "N/A", ...).
        return Prov(None, MISSING_DATA)

    if not _run_validate(validate, value, context):
        # Parsed to a real-looking value but failed its check (e.g. MB `0.00x` -> 0.0). Masked-missing.
        return Prov(None, MISSING_DATA)

    return Prov(value, PRESENT)


def classify_column(col_name, raw, *, applicable=True, fetch_status=ingest.OK, context=None,
                    registry_data=None):
    """`classify()` driven by the column registry: looks up the column's parser + validator BY NAME.

    Raises KeyError if the column is not declared in columns.yaml.
    """
    data = registry_data or registry.load()
    spec = (data.get("columns") or {}).get(col_name)
    if spec is None:
        raise KeyError("%r is not declared in columns.yaml" % col_name)
    parser_name, validator_name = spec.get("parser"), spec.get("validator")
    parser = registry.PARSERS.get(parser_name) if parser_name else None
    validate = registry.VALIDATORS.get(validator_name) if validator_name else None
    return classify(raw, applicable=applicable, fetch_status=fetch_status, parser=parser,
                    validate=validate, context=context)


def derived(value):
    """Stamp a value recovered by a validated formula (T1.3 arithmetic recovery) as `derived`.

    `derived` BYPASSES validate-before-stamp by design: T1.3 validates the recovery identity itself
    (e.g. sub_total_x = sub_total_cr / issue_size_cr only on rows where it holds) before calling this.
    """
    return Prov(value, DERIVED)


# Context-aware validity predicates live in the registry (the single home for named validators) so
# columns.yaml can reference them by name; re-exported here for direct use. `subscription_x_valid`
# is the headline I1 case (board disambiguates a real SME 0 from a masked-missing MB 0x) — now wired
# to sub_total_x in columns.yaml, so the registry-driven path (classify_column) kills the bug too.
subscription_x_valid = registry.VALIDATORS["subscription_x_valid"]
