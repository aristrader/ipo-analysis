"""Shared pure helpers for the pipeline steps.

These three functions were copy-pasted across several numbered pipeline files
(08, 03b, 03d, 03e). They are consolidated here verbatim (byte-identical bodies,
AST-verified before the move) so there is a single tested source.

NOTE: pipeline/05_reconcile.py also defines a function named ``num``, but it is a
DIFFERENT function (``float(x)`` coercion, not a type-guard); it is intentionally
left in place and NOT replaced by ``lib.num``.

Importable from a numbered sibling via the pipeline-dir-on-path convention used
by step 07: ``sys.path.insert(0, dirname(__file__)); from lib import fnum, ...``.
"""


def fnum(s):
    """Coerce a possibly comma-grouped string/number to float, else None."""
    try:
        return float(str(s).replace(',', ''))
    except (ValueError, TypeError):
        return None


def num(v):
    """Pass through only if already an int/float; otherwise None (a type-guard,
    NOT a coercion — strings are rejected, not parsed)."""
    return v if isinstance(v, (int, float)) else None


def last_pre_listing_fy(listing_date):
    """Last fiscal year fully before listing. India FY ends Mar 31, so the last
    pre-listing FY = listing-year if listing-month >= April, else listing-year-1.
    Expects an ISO 'YYYY-MM-...' string; None/too-short -> None."""
    if not listing_date or len(listing_date) < 7:
        return None
    y, m = int(listing_date[:4]), int(listing_date[5:7])
    return y if m >= 4 else y - 1
