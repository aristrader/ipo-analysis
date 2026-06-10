"""NSE corporate-announcements -> data/live/news/ (STAGING ONLY — never writes data/master/).

The RUNG-1 explanatory context feed (D1/D4): per-symbol corporate filings, ISIN-keyed via the
payload's `sm_isin`, locally category-tagged (no LLM, no polarity), look-ahead-safe. This module
does the NETWORK + orchestration only; the pure logic (categorize / actionable_from / dedup) lives
in `layer3/news/{taxonomy,staging}.py` and is unit-tested without a network.

Discipline (docs/research/newsfeed_rnd_2026-06-09.md §2 + trusted_sources.md):
- Host www.nseindia.com (on the WebFetch allowlist); production pull = this curl_cffi scraper.
- ZERO downloads — we GET the JSON API only; `attchmntFile` URLs are stored, never fetched.
- Idempotent on (sm_isin, an_dt, desc-hash); re-runs only append. Resume-safe (loads + upserts).
- Never touches the frozen substrate.

KEY EMPIRICAL FACTS (verified 2026-06-10, see git log / task_log):
- The default per-symbol call ALREADY returns the FULL filing history (back to ~Sept-2004, no row
  cap observed up to ~5k rows, delisted names included to delisting). So this one pull IS the
  historical backfill — no date paging needed. Recent names (e.g. GSPCROP, 28 filings) are short
  only because they are genuinely young, not because of truncation.
- `index=equities` is the SUPERSET for ALL names incl. SME/EMERGE (BTML: equities 327 vs sme 115);
  so we query equities universally — more complete and simpler.
- JOIN CAVEAT for the D1 render step: the payload `sm_isin` is the POINT-IN-TIME ISIN, which can be
  a PRE-SPLIT ISIN (a face-value split changes the ISIN — same reason corp_actions match by SYMBOL).
  e.g. BTML files under INE0EEJ01015 while the substrate's current ISIN is INE0EEJ01023. Therefore
  the render join must key on SYMBOL (we store both), not only the current ISIN. We record 0-row
  symbols to a misses file so symbol-drift / no-filing gaps are FLAGGED, never silent.

Run (babysat session, network on):
  source .venv/bin/activate
  PYTHONPATH=. python scrapers/announcements.py --limit 50      # smoke
  PYTHONPATH=. python scrapers/announcements.py                  # full forward-collect
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scrapers dir, for `nse_session`
from nse_session import prime_nse_session

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)  # repo root, for `layer3.news`
from layer3.news import staging

_REFERER = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
_HDR = {"Referer": _REFERER, "Accept": "application/json"}
_API = "https://www.nseindia.com/api/corporate-announcements"
_RATE = 1.0  # seconds between requests (match the project's NSE pulls)
_FLUSH_EVERY = 25  # persist staging every N symbols so a crash keeps progress

STAGING_DIR = os.path.join(_ROOT, "data", "live", "news")
STAGING_PATH = os.path.join(STAGING_DIR, "announcements_staging.csv")
MISSES_PATH = os.path.join(STAGING_DIR, "coverage_misses.csv")  # 0-row symbols (drift / no-filing)
SUBSTRATE = os.path.join(_ROOT, "data", "master", "ipo_analysis.csv")


class _NetworkDown(Exception):
    """Raised when the NSE session can't be (re-)primed after backoff — i.e. the network is down,
    not a single bad symbol. The run aborts gracefully (progress already flushed) so a re-run resumes."""


def prime_session():
    """Prime an NSE session for the announcements Referer (logic in scrapers/nse_session.py)."""
    return prime_nse_session(_REFERER)


def _safe_reprime(sleep, attempts=4):
    """Re-prime with exponential backoff. Raises _NetworkDown if every attempt fails (outage), so
    the caller can stop cleanly instead of marking the whole remaining universe as 'misses'."""
    last = None
    for k in range(attempts):
        try:
            return prime_session()
        except Exception as e:  # noqa: BLE001 — DNS/connection failures during priming
            last = e
            time.sleep(sleep * (2 ** k))
    raise _NetworkDown(f"could not re-prime NSE session after {attempts} tries: {last}")


def fetch_symbol(session, symbol, extra_params=None):
    """Return the raw announcement list for one symbol (may be empty).

    `extra_params` (dict) is appended to the query — the hook for date-range backfill once the
    working param names are confirmed (e.g. from_date/to_date). Forward-collect passes none.
    Raises on non-200 / non-JSON so the caller can retry / re-prime.
    """
    params = {"index": "equities", "symbol": symbol}
    if extra_params:
        params.update(extra_params)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    r = session.get(f"{_API}?{qs}", headers=_HDR, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} for {symbol}")
    data = r.json()
    if isinstance(data, dict):  # some NSE endpoints wrap the list under 'data'
        data = data.get("data", [])
    if not isinstance(data, list):
        raise RuntimeError(f"unexpected payload for {symbol}: {type(data)}")
    return data


def load_staging(path=STAGING_PATH):
    """Load existing staging rows (empty list if none)."""
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_staging(rows, path=STAGING_PATH):
    """Write staging rows atomically-ish (temp then replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=staging.STAGING_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def read_universe_symbols(path=SUBSTRATE):
    """Sorted unique non-empty `nse_symbol` values from the substrate (the pull set)."""
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        syms = {(r.get("nse_symbol") or "").strip() for r in csv.DictReader(f)}
    return sorted(s for s in syms if s)


def collect(symbols, out_path=STAGING_PATH, extra_params=None, sleep=_RATE, record_misses=True):
    """Collect the full announcement history for `symbols` into the staging CSV (idempotent upsert).

    Re-primes the session on error and retries the symbol once. Flushes periodically so a
    mid-run interruption keeps progress. A symbol with no captured filings (0 rows = symbol drift /
    no filing / wrong platform, OR a repeated transient failure) is "uncovered"; uncovered symbols
    are recorded to MISSES_PATH so coverage gaps are flagged, never silent. `record_misses=False`
    (subset/smoke runs) leaves the canonical misses file untouched so it isn't clobbered.
    Returns (n_symbols_done, n_rows_total, n_with_news, n_misses).
    """
    rows = load_staging(out_path)
    already = {r["symbol"] for r in rows if r.get("symbol")}  # resume: symbols already pulled (have rows)
    if already:
        print(f"resume: {len(already)} symbols already have staged rows — will skip them")
    session = prime_session()
    done = with_news = 0
    covered = set(already)  # already-staged symbols count as covered (single source for miss classification)
    aborted = False
    for i, sym in enumerate(symbols, 1):
        if sym in already:
            done += 1
            continue
        try:
            for attempt in (1, 2):
                try:
                    raw = fetch_symbol(session, sym, extra_params=extra_params)
                    if raw:
                        with_news += 1
                        covered.add(sym)
                    rows = staging.upsert(rows, [staging.normalize(r) for r in raw])
                    print(f"  [{i}/{len(symbols)}] {sym:14s} -> {len(raw)} filings")
                    break
                except Exception as e:  # noqa: BLE001 — transient NSE/network; re-prime + retry once
                    if attempt == 1:
                        print(f"  [{i}/{len(symbols)}] {sym:14s} -> error ({str(e)[:50]}); re-priming")
                        time.sleep(sleep * 2)
                        session = _safe_reprime(sleep)  # raises _NetworkDown on a real outage
                    else:
                        print(f"  [{i}/{len(symbols)}] {sym:14s} -> FAILED ({str(e)[:50]}); skipping")
        except _NetworkDown as nd:
            print(f"\nNETWORK DOWN — {nd}\nflushing progress and stopping; re-run to resume from here.")
            aborted = True
            break
        done += 1
        if i % _FLUSH_EVERY == 0:
            write_staging(rows, out_path)
        time.sleep(sleep)
    write_staging(rows, out_path)
    # only classify misses on a COMPLETE run (an abort would mislabel the un-reached tail as misses)
    misses = [s for s in symbols if s not in covered]
    if record_misses and not aborted:
        _write_misses(misses, MISSES_PATH)
    return done, len(rows), with_news, len(misses)


def _write_misses(symbols, path=MISSES_PATH):
    """Record symbols with no captured filings (drift / no-news / wrong-platform) for review."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nse_symbol", "reason"])
        for s in symbols:
            w.writerow([s, "no_announcements_returned"])


def main():
    ap = argparse.ArgumentParser(description="NSE corporate-announcements forward-collect (staging only)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of symbols (smoke test)")
    ap.add_argument("--symbols", default=None, help="comma-separated symbols (override the universe)")
    ap.add_argument("--sleep", type=float, default=_RATE, help="seconds between requests")
    args = ap.parse_args()

    subset = bool(args.symbols or args.limit)  # don't clobber the canonical misses file on subset runs
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = read_universe_symbols()
    if args.limit:
        symbols = symbols[: args.limit]

    print(f"collecting NSE announcements for {len(symbols)} symbols -> {STAGING_PATH}")
    done, total, with_news, misses = collect(symbols, sleep=args.sleep, record_misses=not subset)
    where = "(subset run — misses not recorded)" if subset else f"(-> {MISSES_PATH})"
    print(f"\nDONE: {done} symbols, {with_news} had filings, {misses} misses {where}, "
          f"{total} staged rows total.")


if __name__ == "__main__":
    main()
