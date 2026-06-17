"""ipowatch.in — SME subscription split (gap G1a, SME) + GMP (gap G2), via WordPress REST.

ipowatch exposes NO ISIN/ticker, so matching is name-based — which we make CONCRETE by requiring
TWO independent agreements before trusting anything:
  1. NAME: our normalized core company-name tokens must ALL appear in the post title, AND
  2. DATE: at least one of the post's IPO Open/Close/Listing dates must EXACTLY equal ours.
If both don't hold, we return NO MATCH (acceptable — refine later). We never guess.

Read post `content.rendered` via the REST API (the rendered front-end URL is sometimes stale-cached).

gmp_status values (present in every matched result):
  ok          — GMP table found and at least one numeric value parsed.
  absent      — no GMP table found in the matched post HTML.
  parse_fail  — GMP table present (header looks right) but no numeric values could be extracted.
"""
import os
import sys
import urllib.request, urllib.parse, json, io, re, html as _html
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config, ingest

_SOURCE = 'ipowatch'

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
_BASE = 'https://ipowatch.in/wp-json/wp/v2/posts'
_STOP = {'ltd', 'limited', 'the', 'and', 'india', 'indian', 'of', 'company', 'co', 'pvt', 'private', 'ipo'}
_MONTHS = {m: i + 1 for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
     'september', 'october', 'november', 'december'])}


def _get(url, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'ignore')


def tokens(name):
    out = []
    for t in re.sub(r'[^a-z0-9 ]', ' ', (name or '').lower()).split():
        if t and t not in _STOP:
            out.append(t)
    return set(out)


def core_query(name):
    """Company name with legal suffixes/noise stripped — better WP search recall."""
    n = re.sub(r'[^A-Za-z0-9 ]', ' ', name or '')
    n = re.sub(r'\b(ltd|limited|pvt|private|the|ipo)\b', ' ', n, flags=re.I)
    return re.sub(r'\s+', ' ', n).strip()


def search_posts(query, per_page=40):
    """Raw WP search for an already-built query string."""
    q = urllib.parse.quote(query)
    try:
        return json.loads(_get(f'{_BASE}?search={q}&per_page={per_page}'))
    except Exception:
        return []


def _to_iso(s):
    """'May 20, 2022' / 'June 02, 2022' -> '2022-05-20'."""
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', s or '')
    if not m:
        return None
    mo = _MONTHS.get(m.group(1).lower())
    if not mo:
        return None
    return f'{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}'


def parse_dates(html):
    """{open,close,listing} ISO dates from the IPO-details table."""
    text = _html.unescape(re.sub(r'<[^>]+>', ' ', html)).replace('\xa0', ' ')
    out = {}
    for key, pat in [('open', r'Open Date[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})'),
                     ('close', r'Close Date[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})'),
                     ('listing', r'Listing Date[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})')]:
        m = re.search(pat, text, re.I)
        if m:
            out[key] = _to_iso(m.group(1))
    return out


def _num(x):
    s = str(x).replace(',', '').replace('x', '').replace('X', '').strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def parse_subscription(html):
    """{qib,nii,rii,total} from the FINAL day column of the subscription table; None if absent."""
    try:
        tabs = pd.read_html(io.StringIO(html))
    except ValueError:
        return None
    for t in tabs:
        col0 = t.iloc[:, 0].astype(str).str.upper().str.strip()
        if not col0.str.contains('TOTAL').any():
            continue
        if t.shape[1] < 2:
            continue
        last = t.columns[-1]   # final day = latest subscription
        rowmap = {}
        for i, lab in enumerate(col0):
            v = _num(t.iloc[i][last])
            if 'QIB' in lab: rowmap['sub_qib_x'] = v
            elif lab == 'NII' or 'NON INSTITUT' in lab: rowmap['sub_nii_x'] = v
            elif lab == 'RII' or 'RETAIL' in lab: rowmap['sub_retail_x'] = v
            elif lab == 'TOTAL': rowmap['sub_total_x'] = v
        if rowmap.get('sub_total_x') is not None:
            return rowmap
    return None


def parse_gmp_last(html):
    """Latest non-empty GMP value (₹) from the GMP table (Date|GMP|Kostak|Subject).

    Returns (value_or_None, gmp_status) where gmp_status is one of:
      'ok'         — GMP table found and at least one numeric value extracted.
      'absent'     — no table with a GMP header found in this HTML.
      'parse_fail' — a GMP-header table was found but no numeric value could be extracted.

    Callers should record gmp_status to distinguish the 153-matched-but-no-GMP case.
    """
    try:
        tabs = pd.read_html(io.StringIO(html))
    except Exception:
        # ValueError  — no tables found (pandas raises this on truly table-free HTML).
        # XMLSyntaxError / OSError — lxml raises on empty or completely malformed HTML.
        # Both mean: no GMP table present → 'absent'.
        return None, 'absent'
    saw_gmp_table = False
    for t in tabs:
        head = ' '.join(str(c) for c in t.columns) + ' ' + ' '.join(str(x) for x in t.iloc[0])
        if 'GMP' not in head.upper():
            continue
        saw_gmp_table = True
        # Found a GMP-header table — attempt numeric extraction.
        # GMP column is the 2nd column; rows are dated; take the last numeric ₹ value.
        vals = []
        for i in range(len(t)):
            cell = str(t.iloc[i, 1])
            mv = re.search(r'₹?\s*(\d+(?:\.\d+)?)', cell)
            if mv:
                vals.append(float(mv.group(1)))
        if vals:
            return vals[-1], 'ok'   # most recent (table is chronological top→bottom)
        # no numeric value in THIS gmp table — keep scanning later tables before giving up
    return (None, 'parse_fail') if saw_gmp_table else (None, 'absent')


def _named(posts, ours):
    """posts whose title contains ALL our core tokens (strong name match), deduped by id."""
    seen, out = set(), []
    for p in posts:
        pid = p.get('id')
        if pid in seen:
            continue
        if ours <= tokens(p.get('title', {}).get('rendered', '')):
            seen.add(pid); out.append(p)
    return out


def _evaluate(named, our_dates, isin=None):
    """(matched_date, sub, gmp, gmp_status) across the named posts.

    matched_date is set only when a post's Open/Close/Listing date EXACTLY equals one of ours
    (concrete corroboration). gmp_status is 'ok'/'absent'/'parse_fail'; None before any GMP post
    is examined.

    For each post that matches, raw HTML is saved via ingest.save_raw so it can be reprocessed
    offline (root-cause fix for the 153-matched-but-undiagnosed-GMP-status rows).
    """
    matched_date, sub, gmp, gmp_status = None, None, None, None
    for p in named:
        html = p.get('content', {}).get('rendered', '')
        slug = p.get('slug', '')
        pid = p.get('id', 'unknown')
        if matched_date is None:
            for k, v in parse_dates(html).items():
                if v and v in our_dates:
                    matched_date = f'{k}={v}'
                    # Save raw HTML of the matched post for offline reprocessing.
                    label = isin or 'unknown'
                    ingest.save_raw(_SOURCE, f'{label}_{pid}.html', html)
                    break
        if sub is None and 'subscription' in slug:
            sub = parse_subscription(html)
        if gmp_status is None and ('gmp' in slug or 'grey-market' in slug or 'review' in slug):
            gmp, gmp_status = parse_gmp_last(html)
            ingest.save_raw(_SOURCE, f'{isin or "unknown"}_{pid}_gmp.html', html)  # preserve GMP post for offline reprocessing
    return matched_date, sub, gmp, gmp_status


def match_and_extract(company_name, open_date, close_date, listing_date, isin=None):
    """Return {sub_*, gmp_rs, gmp_status, evidence} for an IPO only if a post matches on NAME +
    an EXACT IPO date, else None. Strict: both required. Escalates to targeted queries so the
    dates/subscription/GMP posts are reliably surfaced (most rows resolve on the first, general query).

    gmp_status in the result is one of 'ok' / 'absent' / 'parse_fail' — distinguishing why gmp_rs
    may be None for a matched post (the 153-matched-but-no-GMP ambiguity is now diagnosable).
    When no GMP post was examined at all, gmp_status is omitted (sub-only match with no GMP slug).
    """
    ours = tokens(company_name)
    if not ours:
        return None
    our_dates = {d for d in (open_date, close_date, listing_date) if d}
    if not our_dates:
        return None                              # no date to corroborate against → never guess
    q = core_query(company_name)
    posts = search_posts(q)
    named = _named(posts, ours)
    matched_date, sub, gmp, gmp_status = _evaluate(named, our_dates, isin=isin)
    # escalate if not yet corroborated OR we still have neither datum (the needed post may be missing)
    if matched_date is None or (sub is None and gmp is None):
        for extra in (f'{q} subscription', f'{q} gmp'):
            posts += search_posts(extra)
        named = _named(posts, ours)
        matched_date, sub, gmp, gmp_status = _evaluate(named, our_dates, isin=isin)
    if matched_date is None:
        return None                              # no exact-date corroboration → reject
    if sub is None and gmp is None:
        return None    # no usable datum (a bare gmp_status with no value is NOT a match → don't inflate matched count)
    res = {'evidence': f'name+{matched_date}', 'gmp_rs': gmp}
    if gmp_status is not None:
        res['gmp_status'] = gmp_status
    if sub:
        res.update(sub)
    return res


if __name__ == '__main__':
    import csv, time, threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 3   # gentle: WP can throttle
    config.ensure(config.raw_dir(_SOURCE))
    config.ensure(config.logs_dir())
    OUT = str(config.raw_dir(_SOURCE) / 'matches.csv')
    FIELDS = ['isin', 'matched', 'sub_qib_x', 'sub_nii_x', 'sub_retail_x', 'sub_total_x',
              'gmp_rs', 'gmp_status', 'evidence']

    done = set()
    if os.path.exists(OUT):
        done = {r['isin'] for r in csv.DictReader(open(OUT))}

    # target: SME rows lacking subscription (for sub + GMP) OR any row lacking GMP
    targets = []
    for seg in ('mainboard', 'sme'):
        src_path = config.src('master', f'_base_{seg}.csv')
        for r in csv.DictReader(open(src_path)):
            if r['isin'] in done:
                continue
            need_sub = seg == 'sme' and not (r.get('sub_total_x') or '').strip()
            need_gmp = not (r.get('gmp_pct') or '').strip()
            if need_sub or need_gmp:
                targets.append({'isin': r['isin'], 'company': r['company_name'],
                                'open': r.get('open_date'), 'close': r.get('close_date'),
                                'listing': r.get('listing_date')})

    f = open(OUT, 'a', newline=''); w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    if not done:
        w.writeheader(); f.flush()
    counts = {'matched': 0}; doneN = 0; lock = threading.Lock(); t0 = time.time()

    def work(t):
        for attempt in range(3):
            try:
                return t, match_and_extract(t['company'], t['open'], t['close'], t['listing'],
                                            isin=t['isin'])
            except Exception:
                time.sleep(0.8 * (attempt + 1))
        return t, None

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, t) for t in targets]
        for fut in as_completed(futs):
            t, res = fut.result()
            with lock:
                doneN += 1
                row = {'isin': t['isin'], 'matched': 0}
                if res:
                    counts['matched'] += 1
                    row.update({'matched': 1, 'gmp_rs': res.get('gmp_rs'),
                                'gmp_status': res.get('gmp_status'),
                                'evidence': res.get('evidence'),
                                'sub_qib_x': res.get('sub_qib_x'), 'sub_nii_x': res.get('sub_nii_x'),
                                'sub_retail_x': res.get('sub_retail_x'), 'sub_total_x': res.get('sub_total_x')})
                w.writerow(row); f.flush()
                if doneN % 20 == 0 or doneN == len(targets):
                    rate = doneN / (time.time() - t0 + 0.01)
                    (config.logs_dir() / 'ipowatch_progress.txt').write_text(
                        f"done={doneN}/{len(targets)} matched={counts['matched']} rate={rate:.2f}/s "
                        f"eta={(len(targets)-doneN)/rate:.0f}s\n")
                    print(f"  {doneN}/{len(targets)} matched={counts['matched']}", flush=True)
            time.sleep(0.25)
    f.close()
    print(f"\nattempted={len(targets)} matched={counts['matched']} → {OUT} (resume-safe)")
