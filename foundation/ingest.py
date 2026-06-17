"""foundation/ingest.py — the scraper HONESTY layer: collect data without lying or losing it.

Every scraper uses these helpers, which enforce the three honesty rules the data audit was built on:

    Rule 1  Never invent a value.   -> num()/text() return None for missing, never a fake 0/'N/A'.
    Rule 2  Tell apart the outcomes.-> fetch() distinguishes ok / http_error / network_error / blocked / empty,
                                       so "the site failed us" is never recorded as "the site had no data".
    Rule 3  Keep the original.      -> save_raw() persists the raw payload BEFORE parsing, so the source's
                                       real answer is never thrown away (the #1 root cause we found).

Quick reference
---------------
    from foundation import ingest

    r = ingest.fetch(url, source="screener")     # -> Fetch(status, text, ...); r.ok / r.retryable
    ingest.save_raw("screener", "INFY.html", r.text)   # persist raw under OUTPUT_ROOT/raw/screener/raw/

    ingest.num("0")      ->  0.0        # a REAL zero survives
    ingest.num("")       ->  None       # missing stays missing (never minted as 0)
    ingest.num("2.5x")   ->  2.5        # strips commas / ₹ / trailing x or %
    ingest.text(" - ")   ->  None       # placeholder text -> None
    ingest.ratio_parts("1:10")        -> (1.0, 10.0)
    ingest.ratios_equal(1.428571, 1.4285714)  -> True   # relative tolerance, not exact float ==

Pacing per source comes from docs/research/scraper_rate_limits.md (measured 2026-06-17).
"""
import time
from dataclasses import dataclass

from foundation import config


# ═════════════════════════════════════════════════════════════════════════════
# 1. FETCH  (Rule 2: distinguish the outcomes; pace politely)
# ═════════════════════════════════════════════════════════════════════════════

# The five outcomes a fetch can have:
OK = "ok"                    # 2xx with a usable payload
EMPTY = "empty"              # 2xx but no payload (caller decides if that's genuine "no data")
HTTP_ERROR = "http_error"    # a real response, non-2xx and not a block (e.g. genuine 404) -> NOT retryable
BLOCKED = "blocked"          # 403/429/503 or a challenge page -> rate-limited / bot-blocked -> retry later
NETWORK_ERROR = "network_error"  # request never completed (timeout/DNS/conn reset)    -> retryable

_BLOCK_CODES = {403, 429, 503}
DEFAULT_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# How hard we may hit each source (measured). screener is owner-capped at 2 parallel.
SOURCE_LIMITS = {
    "screener":     {"max_parallel": 2, "delay": 0.7},
    "nse":          {"max_parallel": 4, "delay": 0.3},
    "bse":          {"max_parallel": 4, "delay": 0.3},
    "chittorgarh":  {"max_parallel": 4, "delay": 0.5},
    "investorgain": {"max_parallel": 4, "delay": 0.3},
    "ipowatch":     {"max_parallel": 4, "delay": 0.3},
    "sharescart":   {"max_parallel": 4, "delay": 0.5},
    "yahoo":        {"max_parallel": 2, "delay": 0.8},  # paced; prefer the yfinance library for splits/history
}
DEFAULT_LIMIT = {"max_parallel": 2, "delay": 0.5}


def limit_for(source):
    """Politeness limits for a source (falls back to a conservative default)."""
    return SOURCE_LIMITS.get(source, DEFAULT_LIMIT)


@dataclass
class Fetch:
    """The result of a fetch — carries WHICH outcome happened, so callers never guess."""
    status: str               # one of OK / EMPTY / HTTP_ERROR / BLOCKED / NETWORK_ERROR
    url: str
    http_code: int = None
    text: str = None
    error: str = None         # repr of the problem when not OK

    @property
    def ok(self):
        return self.status == OK

    @property
    def retryable(self):
        # transient / our-side failures are worth retrying; a clean http_error (e.g. genuine 404) is not
        return self.status in (NETWORK_ERROR, BLOCKED)


def fetch(url, session=None, source=None, headers=None, timeout=20, retries=3, backoff=2.0, pace=True):
    """GET a URL and return a Fetch describing the outcome — NEVER raises for HTTP/network problems.

    The caller inspects .status (or .ok / .retryable) and records the right thing — a fetch failure
    instead of a fabricated value. Network/blocked outcomes are retried with backoff; a genuine HTTP
    error (like 404) returns immediately.
    """
    import requests  # local import so the parse-helper users below don't need requests installed
    sess = session or requests.Session()
    hdrs = {"User-Agent": DEFAULT_UA}
    if headers:
        hdrs.update(headers)
    lim = limit_for(source)
    last = None
    for attempt in range(retries):
        try:
            r = sess.get(url, headers=hdrs, timeout=timeout)
            if r.status_code in _BLOCK_CODES:
                last = Fetch(BLOCKED, url, r.status_code, error="block %s" % r.status_code)
            elif not (200 <= r.status_code < 300):
                return Fetch(HTTP_ERROR, url, r.status_code, text=r.text)   # genuine error -> stop
            elif not r.text or not r.text.strip():
                return Fetch(EMPTY, url, r.status_code, text=r.text)
            else:
                return Fetch(OK, url, r.status_code, text=r.text)
        except requests.RequestException as e:
            last = Fetch(NETWORK_ERROR, url, error="%s: %s" % (type(e).__name__, e))
        time.sleep((backoff ** attempt) * lim["delay"])   # back off before retrying blocked/network
    if pace:
        time.sleep(lim["delay"])
    return last


# ═════════════════════════════════════════════════════════════════════════════
# 2. SAVE RAW  (Rule 3: keep the source's original answer)
# ═════════════════════════════════════════════════════════════════════════════
def save_raw(source, name, content, subdir="raw"):
    """Persist a raw payload so it's always reprocessable offline.

    Writes to OUTPUT_ROOT/raw/<source>/<subdir>/<name>; returns the path. Accepts str or bytes.
    """
    folder = config.raw_dir(source) / subdir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if isinstance(content, (bytes, bytearray)):
        with open(path, "wb") as f:
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 3. PARSE HELPERS  (Rule 1: missing -> None, never a minted placeholder)
# ═════════════════════════════════════════════════════════════════════════════

# Strings that mean "no value" — these become None, not '' or 0.
_MISSING = {"", "-", "–", "—", "n/a", "na", "nan", "none", "null", "--"}


def text(x):
    """Clean string, or None if missing/placeholder. Never returns ''."""
    if x is None:
        return None
    s = str(x).strip()
    return None if s.lower() in _MISSING else s


def num(x):
    """Number, or None if missing/unparseable — NEVER mints 0 for a missing value.

    A real '0' parses to 0.0; only genuine absence -> None. Strips commas, ₹/Rs, a trailing x or %.
    """
    s = text(x)
    if s is None:
        return None
    s = s.replace(",", "").replace("₹", "").replace("Rs", "").replace("rs", "").strip()
    s = s.rstrip("xX%").strip()
    try:
        return float(s)
    except ValueError:
        return None


def pct(x):
    """A percentage value — None if missing; never 0-minted. (Same parsing as num.)"""
    return num(x)


def ratio_parts(x):
    """Parse an 'a:b' ratio token -> (a, b) floats, or None if not a clean ratio. No fabricated 1.0."""
    s = text(x)
    if s is None or ":" not in s:
        return None
    a, _, b = s.partition(":")
    a_num, b_num = num(a), num(b)
    if a_num is None or b_num is None:
        return None
    return (a_num, b_num)


def ratios_equal(r1, r2, tol=0.01):
    """Are two ratio factors equal within RELATIVE tolerance? (not exact float ==).

    Fixes the USASEEDS-class bug: 1.428571 and 1.4285714 are the same ratio. None equals nothing.
    """
    if r1 is None or r2 is None:
        return False
    if r1 == 0 or r2 == 0:
        return r1 == r2
    return abs(r1 - r2) / max(abs(r1), abs(r2)) <= tol
