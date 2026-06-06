"""New-IPO ingestion for the refresh flow: per-source fetchers that APPEND to the
existing raw caches (same schemas the pipeline already consumes). Idempotent —
every function skips ISINs/years already present, so re-running is safe.

Sources wired (all callables already exist in scrapers/):
  chittorgarh  pull_year + scrape_detail  -> urls.csv + details.csv
  NSE          fetch_subscription         -> data/raw/nse/subscription.csv   (MB only)
  ipowatch     match_and_extract          -> data/raw/ipowatch/matches.csv   (SME sub + GMP)
  investorgain fetch_year                 -> data/raw/investorgain/gmp.csv   (GMP 2nd pass)
  screener     resolve                    -> financials.csv + sector_mcap.csv (best-effort,
                                             RATE-LIMITED — failures recorded, never blocking)

Ticker validation (06/yahoo) is intentionally NOT run here: new rows get
ticker_needs_review handling via the normal review files; flagged in the summary.
"""
import csv
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scrapers"))
sys.path.insert(0, ROOT)

URLS = os.path.join(ROOT, "data/raw/chittorgarh/urls.csv")
DETAILS = os.path.join(ROOT, "data/raw/chittorgarh/details.csv")
NSE_SUB = os.path.join(ROOT, "data/raw/nse/subscription.csv")
IPOWATCH = os.path.join(ROOT, "data/raw/ipowatch/matches.csv")
INVESTORGAIN = os.path.join(ROOT, "data/raw/investorgain/gmp.csv")
SCR_FIN = os.path.join(ROOT, "data/raw/screener/financials.csv")
SCR_SECTOR = os.path.join(ROOT, "data/raw/screener/sector_mcap.csv")


def _existing(path, key="isin"):
    if not os.path.exists(path):
        return set()
    return {r[key] for r in csv.DictReader(open(path)) if r.get(key)}


def _append(path, rows, fieldnames=None):
    """Append dict rows using the file's existing header (extras ignored)."""
    if not rows:
        return 0
    header = fieldnames or list(csv.DictReader(open(path)).fieldnames or [])
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writerows(rows)
    return len(rows)


# ------------------------------------------------------------------ chittorgarh
def find_new_listings(years):
    """Chittorgarh list rows (urls.csv schema) whose ISIN is not yet in urls.csv."""
    import chittorgarh as ch
    have = _existing(URLS)
    scraper = ch.cloudscraper.create_scraper()
    new = []
    for y in years:
        for row in ch.pull_year(scraper, y):
            isin = (row.get("isin") or "").strip()
            if isin and isin not in have and row.get("type") in ("MB", "SME"):
                row["year"] = str(y)
                new.append(row)
    return new, scraper


def ingest_listings(new_rows, scraper):
    """Append new rows to urls.csv and scrape+append each detail page."""
    import chittorgarh as ch
    n_urls = _append(URLS, new_rows)
    have_detail = _existing(DETAILS)
    details, failed = [], []
    for row in new_rows:
        if row["isin"] in have_detail:
            continue
        try:
            rec = ch.scrape_detail(scraper, row)
            if rec:
                details.append(rec)
            time.sleep(0.8)
        except Exception as e:
            failed.append((row["isin"], str(e)[:80]))
    n_det = _append(DETAILS, details)
    return {"urls_appended": n_urls, "details_appended": n_det, "detail_failures": failed}


# ------------------------------------------------------------------ subscription
def ingest_subscription_nse(new_rows):
    """MB subscription via the NSE public-issues API (by symbol)."""
    import nse_subscription as ns
    have = _existing(NSE_SUB)
    todo = [r for r in new_rows if r["type"] == "MB" and r["isin"] not in have and r.get("nse_symbol")]
    if not todo:
        return {"nse_sub_appended": 0, "nse_sub_failures": []}
    out, failed = [], []
    s = ns.prime_session()
    for r in todo:
        try:
            sub = ns.fetch_subscription(s, r["nse_symbol"])
            if sub and any(sub.values()):
                out.append({"isin": r["isin"], **sub})
            time.sleep(0.7)
        except Exception as e:
            failed.append((r["isin"], str(e)[:80]))
    return {"nse_sub_appended": _append(NSE_SUB, out), "nse_sub_failures": failed}


def ingest_subscription_gmp_ipowatch(new_rows):
    """SME subscription + GMP via ipowatch (strict name+date matching)."""
    import ipowatch as iw
    have = _existing(IPOWATCH)
    todo = [r for r in new_rows if r["isin"] not in have]
    out, failed = [], []
    for r in todo:
        try:
            m = iw.match_and_extract(r.get("company_name", ""), r.get("open_date"),
                                     r.get("close_date"), r.get("listing_date"))
            if m is not None:                       # None = no exact-date corroboration (never guess)
                out.append({"isin": r["isin"], "matched": "1", **m})
            time.sleep(0.8)
        except Exception as e:
            failed.append((r["isin"], str(e)[:80]))
    return {"ipowatch_appended": _append(IPOWATCH, out), "ipowatch_failures": failed}


def ingest_gmp_investorgain(years):
    """Investorgain GMP year pages — append rows for (year,name) pairs we lack."""
    import investorgain as ig
    have = {(r["year"], r["name"]) for r in csv.DictReader(open(INVESTORGAIN))}
    scraper = ig.cloudscraper.create_scraper()
    out = []
    for y in years:
        try:
            for row in ig.fetch_year(scraper, y):
                if (str(row.get("year", y)), row.get("name", "")) not in have:
                    row.setdefault("year", str(y))
                    out.append(row)
            time.sleep(1.0)
        except Exception:
            continue
    return {"investorgain_appended": _append(INVESTORGAIN, out)}


# ------------------------------------------------------------------ screener (rate-limited)
def ingest_screener(new_rows, max_failures=8):
    """Financials + sector/mcap per new ISIN. Best-effort: screener blocks hard, so
    failures are recorded and NEVER block the refresh (gaps stay null, as designed)."""
    import screener as sc
    have_fin = _existing(SCR_FIN)
    have_sec = _existing(SCR_SECTOR)
    fin_rows, sec_rows, failed = [], [], []
    for r in new_rows:
        isin = r["isin"]
        if isin in have_fin and isin in have_sec:
            continue
        if len(failed) >= max_failures:
            failed.append((isin, "skipped — failure budget exhausted"))
            continue
        try:
            fin, sec, mcap, slug, verify = sc.resolve(
                r.get("nse_symbol"), r.get("bse_script_code"), r.get("company_name", ""), sleep=1.2)
            if fin and isin not in have_fin:
                for fy, metrics in fin.items():
                    for metric, value in metrics.items():
                        fin_rows.append({"isin": isin, "fy": fy, "metric": metric, "value": value})
            if isin not in have_sec and (sec or mcap is not None):
                sec_rows.append({"isin": isin,
                                 "broad_sector": sec.get("Broad Sector", "") if sec else "",
                                 "sector": sec.get("Sector", "") if sec else "",
                                 "industry": sec.get("Industry", "") if sec else "",
                                 "market_cap_cr": mcap if mcap is not None else "",
                                 "source": f"screener:{slug}" if slug else "screener"})
            time.sleep(2.5)                      # screener cooldown (it blocks aggressively)
        except Exception as e:
            failed.append((isin, str(e)[:80]))
    return {"screener_fin_appended": _append(SCR_FIN, fin_rows),
            "screener_sector_appended": _append(SCR_SECTOR, sec_rows),
            "screener_failures": failed}
