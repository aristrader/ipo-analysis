"""Normalize raw NSE announcement rows into staging rows + idempotent upsert.

Staging is a DISPLAY OVERLAY, NEVER the frozen substrate (`ipo_analysis.csv` stays the
survivorship-clean, point-in-time research base). Rows are keyed on (sm_isin, an_dt, desc-hash)
so re-pulls are idempotent and forward-collection only ever appends genuinely new filings.
Zero-download discipline: we keep the `attchmntFile` URL only — never the file.
Spec: docs/research/newsfeed_rnd_2026-06-09.md §2d.
"""
import hashlib

from layer3.news import taxonomy

STAGING_FIELDS = [
    "sm_isin", "symbol", "sm_name", "an_dt", "actionable_from",
    "categories", "desc", "attchmntText", "attchmntFile", "smIndustry", "row_hash",
]


def _hash(s):
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()[:12]


def normalize(raw):
    """Raw NSE announcement dict -> a staging row dict with exactly STAGING_FIELDS.

    Categories are local display labels; `actionable_from` bakes in the look-ahead rule;
    `row_hash` = stable dedup id over (sm_isin, an_dt, desc).
    """
    desc = (raw.get("desc") or "").strip()
    att = (raw.get("attchmntText") or "").strip()
    an_dt = (raw.get("an_dt") or raw.get("sort_date") or "").strip()
    isin = (raw.get("sm_isin") or "").strip()

    try:
        actionable = taxonomy.actionable_from(taxonomy.parse_an_dt(an_dt)).isoformat()
    except ValueError:
        actionable = ""

    return {
        "sm_isin": isin,
        "symbol": (raw.get("symbol") or "").strip(),
        "sm_name": (raw.get("sm_name") or "").strip(),
        "an_dt": an_dt,
        "actionable_from": actionable,
        "categories": ";".join(taxonomy.categorize(desc, att)),
        "desc": desc,
        "attchmntText": att,
        "attchmntFile": (raw.get("attchmntFile") or "").strip(),  # URL only — never downloaded
        "smIndustry": (raw.get("smIndustry") or "").strip(),
        # dedup key includes attchmntText: NSE often files several DISTINCT attachments in the same
        # minute under an identical subject `desc` (e.g. "Outcome of Board Meeting"); hashing desc
        # alone would collapse them and silently drop a real filing. Conservative (keep near-dups).
        "row_hash": _hash(f"{isin}|{an_dt}|{desc}|{att}"),
    }


def upsert(existing, new):
    """Merge `new` staging rows into `existing`, idempotent on row_hash. First-seen wins
    (the original capture is preserved), so a re-pull of the same filing never duplicates it."""
    seen = {r["row_hash"] for r in existing}
    merged = list(existing)
    for r in new:
        if r["row_hash"] not in seen:
            merged.append(r)
            seen.add(r["row_hash"])
    return merged
