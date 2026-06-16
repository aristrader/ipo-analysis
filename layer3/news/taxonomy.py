"""Local, rule-based category taxonomy + look-ahead-safe timestamps for NSE announcements.

100% LOCAL — no LLM, no network, no egress. Tags an announcement with one or more coarse
categories from keywords over its `desc` + `attchmntText`. POLARITY (good/bad) is DELIBERATELY
NOT computed: keyword polarity botches the context-dependent cases ("resignation"/"results" cut
both ways), and a local small-model is the only ethos-fit polarity path, which is blocked pending
egress sign-off. Category is a DISPLAY label only — "context, not a signal".
Spec: docs/research/newsfeed/newsfeed_rnd_2026-06-09.md §2b.

Also encodes the spine's look-ahead rule (§2c): an announcement disseminated at/after the
15:30-IST market close is not actionable until the next trading session — so a move you see on
the announcement day already happened with the market unable to trade on the filing.
`actionable_from` makes that explicit and is the hard rule any future predictive test inherits.

Precision over recall: a wrong tag drives a wrong glance-judgment, so triggers are written to be
specific (e.g. bare "order" is NOT an order-win trigger, because "adjudication order" is regulatory);
when nothing matches we honestly fall back to `other`.
"""
import re
from datetime import datetime, date, timedelta

MARKET_CLOSE = (15, 30)  # IST close; an_dt time >= this => actionable next session

# Ordered, most-specific-first. Multi-label allowed (a filing can carry several). `other` is the
# fallback when nothing matches. Triggers are lowercase substrings matched against the joined text.
CATEGORY_KEYWORDS = [
    ("earnings", ("financial results", "quarterly results", "audited", "un-audited", "unaudited",
                  "q1 results", "q2 results", "q3 results", "q4 results", "half year", "half-year",
                  "standalone results", "consolidated results")),
    ("sebi-regulatory", ("sebi", "show cause", "adjudication", "penalty", "settlement order",
                         "regulatory order", "circular")),
    ("pledge-encumbrance", ("pledge", "encumbrance", "invocation", "creation of charge",
                           "reg. 31", "reg 31", "regulation 31")),
    ("m&a-openoffer", ("acquisition", "amalgamation", "scheme of arrangement", "open offer",
                       "sast", "merger")),
    ("management", ("resignation", "appointment", "cessation", "auditor", "kmp", "director",
                    "chief financial officer", "cfo", "ceo", "managing director", "company secretary")),
    ("index-inclusion", ("index inclusion", "index exclusion", "reconstitution", "f&o",
                         "futures and options", "addition to index", "removal from index")),
    ("order-win", ("work order", "purchase order", "supply order", "letter of intent", "loi",
                   "bagged", "awarded", "tender", "new contract", "received order", "order win")),
    ("corp-action", ("bonus", "stock split", "sub-division", "subdivision", "dividend",
                     "rights issue", "buyback", "buy-back")),
    ("capital-raise", ("preferential", "qip", "qualified institutions placement", "fund raising",
                       "fund-raising", "raising of funds", "warrants")),
    ("ratings", ("crisil", "icra", "care ratings", "reaffirmed", "downgrade", "upgrade", "credit rating",
                 "rating")),
    ("litigation", ("litigation", "nclt", "insolvency", "winding up", "arbitration",
                    "insolvency and bankruptcy")),
]
DEFAULT_CATEGORY = "other"

# Match on WORD BOUNDARIES (not bare substrings) so triggers don't fire inside longer words —
# e.g. "rating" must NOT match "narrating"/"operating"/"generating", "loi" must not match
# "loiter", "sast" must not match "sastra". The trailing `s?` lets a singular trigger also catch
# its plural ("rating"->"ratings", "director"->"directors") without a second list entry.
_COMPILED = [
    (cat, [re.compile(r"\b" + re.escape(k) + r"s?\b", re.IGNORECASE) for k in kws])
    for cat, kws in CATEGORY_KEYWORDS
]


def categorize(*texts):
    """Return the list of matched categories (in CATEGORY_KEYWORDS order), or ['other'].

    Multi-label: a filing matching several buckets gets all of them. Matching is case-insensitive
    and word-boundary-anchored (see _COMPILED) — precision over recall, so a near-miss falls to
    `other` rather than driving a wrong glance-judgment.
    """
    blob = " ".join(t for t in texts if t)
    hits = [cat for cat, pats in _COMPILED if any(p.search(blob) for p in pats)]
    return hits or [DEFAULT_CATEGORY]


def parse_an_dt(s):
    """Parse an NSE announcement timestamp into a datetime.

    Primary format is `an_dt` ("29-May-2026 15:54:27"); falls back to the ISO `sort_date`
    ("2026-05-29 15:54:27"). Raises ValueError if neither parses.
    """
    s = (s or "").strip()
    for fmt in ("%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # date-only (no time): time is UNKNOWN -> stamp it at the 15:30 close so actionable_from takes
    # the conservative, look-ahead-safe path (treat as after-hours -> next session), never leaks.
    try:
        return datetime.strptime(s, "%d-%b-%Y").replace(hour=15, minute=30)
    except ValueError:
        pass
    raise ValueError(f"unparseable announcement timestamp: {s!r}")


def actionable_from(dt):
    """Date from which a secondary buyer could first act on an announcement made at `dt`.

    Rule (look-ahead-safe): a filing at/after the 15:30-IST close is actionable only from the
    NEXT trading session; an intraday filing is actionable the same session. We then roll the
    result forward over weekends (Sat/Sun). CAVEAT: NOT exchange-holiday-aware — `actionable_from`
    can land on a holiday and is therefore a *floor* (earliest plausible), used for display + as
    the hard rule a future predictive backtest must inherit. Returns a `date`.
    """
    after_close = (dt.hour, dt.minute) >= MARKET_CLOSE
    d = dt.date() + timedelta(days=1) if after_close else dt.date()
    while d.weekday() >= 5:  # Sat=5, Sun=6
        d += timedelta(days=1)
    return d
