"""Live & upcoming IPO board → data/live/ (STAGING ONLY — never writes data/master/).

Sources (existing stack, same endpoints/rate discipline):
- chittorgarh list API (report 82, current year) → upcoming + open issues w/ band/dates/isin
- investorgain GMP table (current year) → gmp_rs / ipo_price for not-yet-listed issues
- chittorgarh ipo_subscription page per OPEN issue → current category-wise subscription snapshot

Outputs:
- data/live/board.json            {fetched_at, open:[...], upcoming:[...]}
- data/live/daywise_sub.csv       APPEND one row per open issue per fetch-day (this slowly
                                  builds the day-wise dataset the day-1 question needs — Branch B)

An IPO enters the real dataset ONLY later via run_refresh.py. Unknown fields stay None."""
import csv
import json
import os
import re
import sys
import time
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "live")
LIST_API = ("https://webnodejs.chittorgarh.com/cloud/report/data-read/82/"
            "{page}/5/{year}/2026-27/0/all/0?search=&v=13-44")
HDR = {"Referer": "https://www.chittorgarh.com/"}
RATE = 0.4

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _clean(x):
    return re.sub(r"<[^>]+>", "", str(x or "")).strip()


def _iso(s):
    m = re.match(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", _clean(s))
    if not m:
        return None
    mo = _MONTHS.get(m.group(2).lower())
    return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(1)):02d}" if mo else None


def parse_list_row(row, today):
    """One chittorgarh report-82 row -> a board entry dict, or None if already listed/past.
    status: 'open' (window contains today) | 'upcoming' (opens later) | None (otherwise)."""
    o, c = _iso(row.get("Opening Date")), _iso(row.get("Closing Date"))
    if not o or not c:
        return None
    t = today.strftime("%Y-%m-%d")
    status = "open" if o <= t <= c else ("upcoming" if o > t else None)
    if status is None:
        return None
    band = _clean(row.get("Issue Price (Rs.)"))
    lo = hi = None
    nums = re.findall(r"[\d.]+", band)
    if nums:
        lo = float(nums[0]); hi = float(nums[-1])
    cat = _clean(row.get("Issue Category"))
    return {
        "name": _clean(row.get("Company")).replace(" O", "").strip(),
        "type": "SME" if "sme" in cat.lower() else "MB",
        "status": status, "open_date": o, "close_date": c,
        "price_band_low": lo, "price_band_high": hi,
        "issue_size_cr": (lambda v: float(v) if v else None)(
            re.sub(r"[^\d.]", "", _clean(row.get("Total Issue Amount (Incl.Firm reservations) (Rs.cr.)")))),
        "isin": _clean(row.get("~isin")) or None,
        "nse_symbol": _clean(row.get("~nse_symbol")) or None,
        "lead_manager": _clean(row.get("Lead Manager")) or None,
        "detail_url": (re.findall(r'href="([^"]+)"', str(row.get("Company") or "")) or [None])[0],
        "slug": _clean(row.get("~URLRewrite_Folder_Name")) or None,
        "gmp_rs": None, "gmp_pct": None,
        "sub_qib_x": None, "sub_nii_x": None, "sub_retail_x": None, "sub_total_x": None,
        "day_n": None,
        # Honesty status fields: distinguish a fetch error from genuine no-data.
        # sub_fetch_status: 'ok' | 'error:<ExcType>' | 'no_detail_url'
        # gmp_fetch_status: 'ok' | 'error:<ExcType>' | 'not_attempted' (skipped because gmp already set)
        # gmp_source: 'investorgain' | 'ipowatch' | None
        "sub_fetch_status": None,
        "gmp_fetch_status": None,
        "gmp_source": None,
    }


def parse_subscription_html(html):
    """Category-wise subscription TIMES (x) from a chittorgarh ipo_subscription page.
    Returns {qib, nii, retail, total} (floats, x-times) — None where absent.

    The page has MULTIPLE tables; the one we want is the subscription-times table whose rows are
    `<td>CATEGORY</td><td>N.NNx</td>` with the FULL category labels:
      'Qualified Institutional', 'Non Institutional', 'Retail Individual', 'Total Subscription'.
    We anchor on those specific labels + require the trailing `x`. (The previous regex used the short
    forms 'QIB'/'NII'/'Retail'/'Total' and accepted the first `Nx` anywhere → it matched a DIFFERENT
    table and returned bogus values, and missed QIB/NII because the times-table labels are the long
    forms. See docs — this was a real defect, live-feed only; the substrate uses the NSE JSON API.)"""
    out = {"qib": None, "nii": None, "retail": None, "total": None}
    txt = re.sub(r"\s+", " ", html)
    # Scope to the subscription-TIMES <table> (the one with a 'Total Subscription' row); other tables on
    # the page use offered/percent columns (no trailing 'x') and are thereby excluded. Then map EACH row's
    # label fuzzily — chittorgarh varies the label ('Qualified Institutional' vs 'QIB', 'Non Institutional'
    # vs 'NII', etc.), and SME pages may omit QIB entirely (→ stays None, which is correct).
    anchor = re.search(r"Total\s+Subscription", txt, re.I)
    if not anchor:
        return out
    start = txt.rfind("<table", 0, anchor.start())
    end = txt.find("</table>", anchor.start())
    table = txt[(start if start != -1 else 0):(end if end != -1 else len(txt))]
    cat = (("qib", ("qualified institutional", "qib")),
           ("nii", ("non institutional", "non-institutional", "nii")),
           ("retail", ("retail individual", "retail", "rii")),
           ("total", ("total subscription", "total")))
    for m in re.finditer(r"<td[^>]*>(.*?)</td>\s*<td[^>]*>\s*([\d,.]+)\s*x", table):
        label = re.sub(r"<[^>]+>", "", m.group(1)).strip().lower()
        try:
            val = float(m.group(2).replace(",", ""))
        except ValueError:
            continue
        for key, names in cat:
            if out[key] is None and any(n in label for n in names):
                out[key] = val
                break
    return out


def attach_gmp(entries, ig_rows):
    """Match investorgain GMP rows to board entries by nse_symbol, else name-token overlap."""
    def toks(s):
        return {w for w in re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split()
                if len(w) > 2 and w not in ("ltd", "limited", "ipo", "india", "the", "and")}
    for e in entries:
        best = None
        for g in ig_rows:
            if e.get("nse_symbol") and g.get("nse") and e["nse_symbol"] == g["nse"]:
                best = g
                break
            ov = len(toks(e["name"]) & toks(g.get("name")))
            if ov >= 2 and (best is None or ov > best.get("_ov", 0)):
                best = dict(g, _ov=ov)
        if best:
            e["gmp_rs"] = best.get("gmp_rs")
            px = best.get("ipo_price") or e.get("price_band_high")
            if e["gmp_rs"] is not None and px:
                e["gmp_pct"] = round(100.0 * float(e["gmp_rs"]) / float(px), 2)
            if e["gmp_rs"] is not None:        # only claim attribution when real GMP was obtained
                e["gmp_source"] = "investorgain"
    return entries


def day_n(entry, today):
    """1-based day of the subscription window (None if not open)."""
    if entry["status"] != "open":
        return None
    return (today - datetime.strptime(entry["open_date"], "%Y-%m-%d").date()).days + 1


def append_daywise(entries, today, out_dir):
    """Accumulate per-fetch-day subscription snapshots (the Branch-B day-wise dataset)."""
    path = os.path.join(out_dir, "daywise_sub.csv")
    cols = ["fetch_date", "name", "isin", "type", "day_n", "open_date", "close_date",
            "sub_qib_x", "sub_nii_x", "sub_retail_x", "sub_total_x", "gmp_rs", "gmp_pct"]
    seen = set()
    if os.path.exists(path):
        with open(path) as f:
            seen = {(r["fetch_date"], r["name"]) for r in csv.DictReader(f)}
    new = [e for e in entries if e["status"] == "open"
           and (today.strftime("%Y-%m-%d"), e["name"]) not in seen]
    if not new:
        return 0
    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for e in new:
            w.writerow(dict(e, fetch_date=today.strftime("%Y-%m-%d")))
    return len(new)


def append_gmp_history(entries, today, out_dir):
    """Accumulate the pre-listing GMP TRAJECTORY for BOTH open AND upcoming issues — a dataset no
    free tool keeps cleanly (Thread B). One row per issue per fetch-day; dedup on (fetch_date,name)."""
    path = os.path.join(out_dir, "gmp_history.csv")
    cols = ["fetch_date", "name", "isin", "type", "status", "open_date", "close_date",
            "price_band_high", "gmp_rs", "gmp_pct"]
    fd = today.strftime("%Y-%m-%d")
    # dedup on (fetch_date, ISIN-or-slug-or-name): ISIN/slug is stable; name can drift between
    # fetches (review fix). Write a row even when GMP is MISSING so a flaky-source day is a VISIBLE
    # null in the trajectory, not an invisible hole.
    def _key(e):
        return (fd, str(e.get("isin") or e.get("slug") or e["name"]))
    seen = set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                seen.add((r["fetch_date"], str(r.get("isin") or r.get("name"))))
    new = [e for e in entries if e["status"] in ("open", "upcoming") and _key(e) not in seen]
    if not new:
        return 0
    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for e in new:
            w.writerow(dict(e, fetch_date=fd))
    return len(new)


def _save_raw_sub(entry, html):
    """Persist raw subscription HTML for one open IPO so the parse can be re-run offline."""
    try:
        from foundation import ingest  # noqa: PLC0415 — optional; not all envs have foundation
        slug = entry.get("slug") or re.sub(r"[^a-z0-9]+", "_", entry["name"].lower())[:40]
        ingest.save_raw("live_board_sub", f"{slug}_sub.html", html)
    except Exception:  # noqa: BLE001 — save_raw failure must not abort the board fetch
        pass


def fetch_board(out_dir=LIVE_DIR, today=None):
    """The full fetch. Returns the board dict (also written to out_dir/board.json)."""
    import cloudscraper
    from scrapers import investorgain
    today = today or date.today()
    sc = cloudscraper.create_scraper()
    entries, page, seen_keys = [], 1, set()
    while True:
        r = sc.get(LIST_API.format(page=page, year=today.year), headers=HDR, timeout=25)
        rows = r.json().get("reportTableData", [])
        for row in rows:
            e = parse_list_row(row, today)
            k = (e["name"], e["open_date"]) if e else None
            if e and k not in seen_keys:                 # pages can overlap — dedupe
                seen_keys.add(k)
                entries.append(e)
        if len(rows) < 25 or page >= 4:
            break
        page += 1
        time.sleep(RATE)
    try:
        ig = investorgain.fetch_year(sc, today.year)
    except Exception as ex:
        print(f"investorgain GMP unavailable ({ex}) — gmp fields stay None")
        ig = []
    entries = attach_gmp(entries, ig)
    # investorgain only covers LISTED issues — for open/upcoming, best-effort ipowatch GMP
    from scrapers import ipowatch
    for e in entries:
        if e["gmp_pct"] is not None:
            # already set by investorgain; no need to try ipowatch
            e["gmp_fetch_status"] = "not_attempted"
            continue
        try:
            m = ipowatch.match_and_extract(e["name"], e["open_date"], e["close_date"], None)
            g = (m or {}).get("gmp_rs")
            px = e.get("price_band_high")
            if g is not None and px:
                e["gmp_rs"] = float(g)
                e["gmp_pct"] = round(100.0 * float(g) / float(px), 2)
                e["gmp_source"] = "ipowatch"
            # fetch succeeded regardless of whether GMP data was present
            e["gmp_fetch_status"] = "ok"
        except Exception as _gmp_exc:
            # fetch/parse failed — gmp_rs/gmp_pct remain None but the REASON is recorded
            e["gmp_fetch_status"] = f"error:{type(_gmp_exc).__name__}"
        time.sleep(RATE)
    for e in entries:
        e["day_n"] = day_n(e, today)
        if e["status"] == "open":
            if not e.get("detail_url"):
                e["sub_fetch_status"] = "no_detail_url"
            else:
                try:
                    sub_url = e["detail_url"].replace("/ipo/", "/ipo_subscription/")
                    resp = sc.get(sub_url, headers=HDR, timeout=25)
                    # save raw subscription HTML so the parse can be re-run offline
                    _save_raw_sub(e, resp.text)
                    s = parse_subscription_html(resp.text)
                    e.update(sub_qib_x=s["qib"], sub_nii_x=s["nii"],
                             sub_retail_x=s["retail"], sub_total_x=s["total"])
                    e["sub_fetch_status"] = "ok"
                except Exception as _sub_exc:
                    # sub_qib/nii/retail/total stay None; status records the error type
                    e["sub_fetch_status"] = f"error:{type(_sub_exc).__name__}"
                time.sleep(RATE)
    os.makedirs(out_dir, exist_ok=True)
    board = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
             "open": [e for e in entries if e["status"] == "open"],
             "upcoming": sorted((e for e in entries if e["status"] == "upcoming"),
                                key=lambda e: e["open_date"])}
    with open(os.path.join(out_dir, "board.json"), "w") as f:
        json.dump(board, f, indent=1)
    n = append_daywise(entries, today, out_dir)
    g = append_gmp_history(entries, today, out_dir)
    print(f"board: {len(board['open'])} open, {len(board['upcoming'])} upcoming; "
          f"daywise rows appended: {n}; gmp-history rows appended: {g}")
    return board


if __name__ == "__main__":
    fetch_board()
