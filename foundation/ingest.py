"""foundation/ingest.py — the scraper honesty layer (structural fix for the I1 / fetch-fail class).

Every scraper uses these helpers so it CANNOT fabricate and ALWAYS preserves the source's answer:
  * fetch()      -> a structured Fetch result that DISTINGUISHES ok / http_error / network_error / blocked /
                    empty, with per-source polite pacing + retry/backoff. (honesty rule 2)
  * save_raw()   -> persist the raw payload so reprocessing is always possible offline. (honesty rule 3 +
                    the root cause of the audit's "needs-refetch" findings: old scrapers saved only parsed CSV)
  * num/text/pct/ratio_parts/ratios_equal -> parse helpers that return None for missing — they NEVER mint a
                    0 / 'N/A' placeholder, and compare ratios with numeric tolerance. (honesty rule 1)

Pacing/limits come from docs/research/scraper_rate_limits.md (measured 2026-06-17).
"""
import time
from dataclasses import dataclass

from foundation import config

# --- fetch outcome vocabulary -----------------------------------------------------
OK = "ok"                    # 2xx with a usable payload
HTTP_ERROR = "http_error"    # got a response, non-2xx and not a known block code (e.g. genuine 404) -> NOT retryable
NETWORK_ERROR = "network_error"  # request never completed (timeout/DNS/conn reset) -> retryable
BLOCKED = "blocked"          # 403/429/503 or challenge -> rate-limited / bot-blocked -> retryable (later)
EMPTY = "empty"              # 2xx but no payload; caller decides whether that's genuine no_data

# per-source politeness (measured) — screener capped at 2 parallel per owner
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
_BLOCK_CODES = {403, 429, 503}
DEFAULT_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def limit_for(source):
    return SOURCE_LIMITS.get(source, DEFAULT_LIMIT)


@dataclass
class Fetch:
    status: str
    url: str
    http_code: int = None
    text: str = None
    error: str = None

    @property
    def ok(self):
        return self.status == OK

    @property
    def retryable(self):
        # transient / our-side failures are retryable; a clean http_error (genuine 404) is not
        return self.status in (NETWORK_ERROR, BLOCKED)


def fetch(url, session=None, source=None, headers=None, timeout=20, retries=3, backoff=2.0, pace=True):
    """Fetch a URL, returning a structured Fetch that distinguishes failure kinds (honesty rule 2).

    NEVER raises for HTTP/network problems — returns a Fetch with the right status so the caller records
    fetch_error vs no_data instead of silently minting a placeholder. Retries network/blocked with backoff.
    """
    import requests  # local import so parse-helper users don't need requests installed
    sess = session or requests.Session()
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    lim = limit_for(source)
    last = None
    for attempt in range(retries):
        try:
            r = sess.get(url, headers=h, timeout=timeout)
            if r.status_code in _BLOCK_CODES:
                last = Fetch(BLOCKED, url, r.status_code, error="block %s" % r.status_code)
            elif not (200 <= r.status_code < 300):
                return Fetch(HTTP_ERROR, url, r.status_code, text=r.text)   # genuine http error -> stop
            elif not r.text or not r.text.strip():
                return Fetch(EMPTY, url, r.status_code, text=r.text)
            else:
                return Fetch(OK, url, r.status_code, text=r.text)
        except requests.RequestException as e:
            last = Fetch(NETWORK_ERROR, url, error="%s: %s" % (type(e).__name__, e))
        time.sleep((backoff ** attempt) * lim["delay"])  # back off before retrying blocked/network
    if pace:
        time.sleep(lim["delay"])
    return last


def save_raw(source, name, content, subdir="raw"):
    """Persist a raw payload so reprocessing is always possible offline (honesty rule 3).

    Writes under OUTPUT_ROOT/raw/<source>/<subdir>/<name>; returns the path. Accepts str or bytes.
    """
    d = config.raw_dir(source) / subdir
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
    kw = {} if mode == "wb" else {"encoding": "utf-8"}
    with open(p, mode, **kw) as f:
        f.write(content)
    return p


# --- parse helpers: return None for missing, NEVER mint a placeholder (honesty rule 1) ---
_MISSING = {"", "-", "–", "—", "n/a", "na", "nan", "none", "null", "--"}


def text(x):
    """Strip to a clean string, or None if missing/placeholder. Never returns ''."""
    if x is None:
        return None
    s = str(x).strip()
    return None if s.lower() in _MISSING else s


def num(x):
    """Parse a number, or None if missing/unparseable. NEVER mints 0 for a missing value.

    A real '0' parses to 0.0; only genuine absence -> None. Strips commas, rupee sign, a trailing x/%.
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
    """Percentage parse — None if missing; never 0-mint."""
    return num(x)


def ratio_parts(x):
    """Parse an 'a:b' ratio token -> (a, b) floats, or None if not a clean ratio. No fabricated 1.0."""
    s = text(x)
    if s is None or ":" not in s:
        return None
    a, _, b = s.partition(":")
    an, bn = num(a), num(b)
    if an is None or bn is None:
        return None
    return (an, bn)


def ratios_equal(r1, r2, tol=0.01):
    """Compare two ratio factors with RELATIVE tolerance (not exact float equality).

    Fixes the USASEEDS-class bug (1.428571 vs 1.4285714 are the same ratio). None never equals anything.
    """
    if r1 is None or r2 is None:
        return False
    if r1 == 0 or r2 == 0:
        return r1 == r2
    return abs(r1 - r2) / max(abs(r1), abs(r2)) <= tol
