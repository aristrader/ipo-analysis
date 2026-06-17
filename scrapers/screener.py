"""Screener.in — pre-IPO financials/KPIs (gap G1b) + Sector/Industry + Market Cap (Layer-1 adds).

IDENTITY BY NAME (validated): we resolve /company/<bse_code>/ or /company/<nse_symbol>/ and verify the
page's <h1> company name matches ours (normalized) — BSE-SME pages don't expose NSE:/BSE: codes, so the
old code-check wrongly rejected them. Delisted companies resolve via the search API → /company/id/<id>/.
Annual figures only (₹ Crore; EPS in ₹). Quarterly tables skipped.
"""
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from foundation import config, ingest

import urllib.request, urllib.error, urllib.parse, io, re, json, time
import pandas as pd

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

_METRICS = {
    'sales': 'sales', 'revenue': 'sales',
    'operating profit': 'operating_profit',
    'net profit': 'net_profit',
    'eps in rs': 'eps',
    'equity capital': 'equity_capital',
    'reserves': 'reserves',
    'borrowings': 'borrowings',
    'total assets': 'total_assets',
    'cash from operating activity': 'operating_cf',
}
_NAME_STOP = {'ltd', 'limited', 'pvt', 'private', 'corp', 'co', 'company', 'the', 'com', 'india', 'inc'}


def _get(url, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8', 'ignore')


def fetch_company(slug, consolidated=True):
    """HTML for /company/<slug>/[consolidated/]; None on 404. slug may be a full '/company/...' path."""
    if slug.startswith('/'):
        path = slug if slug.endswith('/') else slug + '/'
    else:
        path = f'/company/{slug}/consolidated/' if consolidated else f'/company/{slug}/'
    url = 'https://www.screener.in' + path
    try:
        html = _get(url)
        # Save raw company page before parsing
        safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', path.strip('/'))[:80]
        suffix = '_consolidated' if consolidated else ''
        ingest.save_raw('screener', f'{safe}{suffix}.html', html)
        return html
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


# ---------- identity (name) ----------
def page_name(html):
    m = re.search(r'<h1[^>]*>\s*([^<]+)', html)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


def _norm_tokens(name):
    n = (name or '').lower().replace('&', ' and ')
    n = re.sub(r'\([^)]*\)', ' ', n)
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    toks = [t for t in n.split() if t and t not in _NAME_STOP]
    out, buf = [], ''                       # collapse single-letter runs: "g m" -> "gm"
    for t in toks:
        if len(t) == 1:
            buf += t
        else:
            if buf:
                out.append(buf); buf = ''
            out.append(t)
    if buf:
        out.append(buf)
    return out


def name_match(a, b, allow_digitstrip=False):
    ta, tb = _norm_tokens(a), _norm_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    A, B = set(ta), set(tb)
    inter = A & B
    if inter and len(inter) / min(len(A), len(B)) >= 0.8 and len(inter) / len(A | B) >= 0.5:
        return True
    if inter and len(inter) / len(A | B) >= 0.8:
        return True
    if allow_digitstrip:
        ds = lambda s: {re.sub(r'\d', '', x) for x in s if re.sub(r'\d', '', x)}
        if ds(A) and ds(A) == ds(B):
            return True
    return False


def search_company(name):
    q = urllib.parse.quote(' '.join(_norm_tokens(name)))
    url = f'https://www.screener.in/api/company/search/?q={q}'
    try:
        raw = _get(url)
        # Save raw search response
        safe_q = re.sub(r'[^a-zA-Z0-9_]', '_', q)[:60]
        ingest.save_raw('screener', f'search_{safe_q}.json', raw)
        d = json.loads(raw)
        return d if isinstance(d, list) else []
    except Exception:
        return []


# ---------- page data ----------
def page_marketcap(html):
    m = re.search(r'Market Cap\s*</span>\s*<span[^>]*>\s*₹?\s*<span class="number">([\d.,]+)</span>', html)
    return float(m.group(1).replace(',', '')) if m else None


def page_sector(html):
    out = {}
    for lab, val in re.findall(r'title="(Broad Sector|Sector|Broad Industry|Industry)"[^>]*>([^<]+)</a>', html):
        out[lab] = re.sub(r'&amp;', '&', val).strip()
    return out


def _num(x):
    s = str(x).replace(',', '').replace('%', '').strip()
    if s in ('', 'nan', 'None', '-', '–'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_financials(html):
    """{fy_year:int -> {metric -> value}} from the ANNUAL P&L + Balance-Sheet + Cash-Flow tables."""
    out = {}
    for t in pd.read_html(io.StringIO(html)):
        cols = list(t.columns)
        if len(cols) < 2 or str(cols[0]) != 'Unnamed: 0':
            continue
        periods = cols[1:]
        if not all(('Mar' in str(c) or 'TTM' in str(c)) for c in periods):
            continue
        labels = [re.sub(r'\s+', ' ', str(v)).replace('\xa0', '').strip().lower().rstrip('+').strip()
                  for v in t.iloc[:, 0]]
        for ri, lab in enumerate(labels):
            key = _METRICS.get(lab)
            if not key:
                continue
            for c in periods:
                m = re.search(r'Mar (\d{4})', str(c))
                if not m:
                    continue
                val = _num(t.iloc[ri][c])
                if val is not None:
                    out.setdefault(int(m.group(1)), {})[key] = val
    return out


def resolve(nse_symbol, bse_code, company_name, sleep=0.8):
    """Resolve a company on screener by NAME match. Returns
    (financials, sector_dict, market_cap, slug, verify) or (None, {}, None, slug, reason)."""
    tried = []
    for kind, slug in [('bse', str(bse_code) if bse_code else None), ('nse', nse_symbol or None)]:
        if not slug:
            continue
        html = fetch_company(slug, consolidated=False)   # default page = screener's best view (full history)
        time.sleep(sleep)
        if not html:
            tried.append(f'{kind}:{slug}→404'); continue
        pn = page_name(html)
        if not name_match(pn, company_name, allow_digitstrip=True):   # code in URL corroborates → digitstrip ok
            tried.append(f'{kind}:{slug}→{pn}'); continue
        fin, sec, mcap = parse_financials(html), page_sector(html), page_marketcap(html)
        if not fin:                                      # no annual tables on default → try consolidated
            h2 = fetch_company(slug, consolidated=True)
            time.sleep(sleep)
            if h2:
                fin = parse_financials(h2)
                if not sec:
                    sec = page_sector(h2)
                if mcap is None:
                    mcap = page_marketcap(h2)
        return fin or {}, sec, mcap, slug, f'name-direct-{kind}({pn})'
    # search fallback (handles delisted /company/id/<id>/)
    for c in search_company(company_name):
        if name_match(c.get('name', ''), company_name):
            html = fetch_company(c.get('url', ''))
            time.sleep(sleep)
            if html and name_match(page_name(html), company_name):
                return (parse_financials(html) or {}, page_sector(html), page_marketcap(html),
                        c.get('url', ''), f'name-search({c.get("name")})')
    return None, {}, None, (tried[0].split('→')[0] if tried else ''), f'no-name-match[{"|".join(tried)[:90]}]'


# ---- cache builder: resolve financials + sector + market cap for rows lacking financials ----
if __name__ == '__main__':
    import csv, sys, os
    DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2   # between companies; resolve() also sleeps internally
    MAX_CONSEC_ERR = 10
    config.ensure(config.raw_dir('screener'))
    FIN_PATH  = str(config.raw_dir('screener') / 'financials.csv')
    LOG_PATH  = str(config.raw_dir('screener') / 'match_log.csv')
    META_PATH = str(config.raw_dir('screener') / 'company_meta.csv')

    done_isins = set()
    if os.path.exists(LOG_PATH):
        done_isins = {r['isin'] for r in csv.DictReader(open(LOG_PATH))
                      if not (r.get('verify') or '').startswith('ERROR')}

    # target: rows lacking financials (pre_ipo_pat empty) across BOTH cohorts (boom _base + long-term)
    targets, seen = [], set()
    for path in ('data/master/_base_mainboard.csv', 'data/master/_base_sme.csv',
                 'data/master/longterm_mainboard.csv', 'data/master/longterm_sme.csv'):
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            isin = r.get('isin', '')
            if not isin or isin in done_isins or isin in seen:
                continue
            if (r.get('pre_ipo_pat') or '').strip():
                continue
            nse = (r.get('nse_symbol') or '').strip()
            bse = (r.get('bse_script_code') or '').strip()
            if nse or bse:
                seen.add(isin)
                targets.append({'isin': isin, 'company': r['company_name'], 'nse': nse, 'bse': bse})

    def _empty(p):
        return (not os.path.exists(p)) or os.path.getsize(p) == 0
    fin_new, log_new, meta_new = _empty(FIN_PATH), _empty(LOG_PATH), _empty(META_PATH)
    fin_f = open(FIN_PATH, 'a', newline=''); fin_w = csv.writer(fin_f)
    log_f = open(LOG_PATH, 'a', newline=''); log_w = csv.writer(log_f)
    meta_f = open(META_PATH, 'a', newline=''); meta_w = csv.writer(meta_f)
    if fin_new:
        fin_w.writerow(['isin', 'fy', 'metric', 'value']); fin_f.flush()
    if log_new:
        log_w.writerow(['isin', 'company', 'slug', 'verify', 'n_years']); log_f.flush()
    if meta_new:
        meta_w.writerow(['isin', 'screener_name', 'broad_sector', 'sector', 'broad_industry', 'industry', 'market_cap_cr', 'slug', 'verify']); meta_f.flush()

    counts = {'resolved': 0, 'nomatch': 0, 'error': 0}
    done = 0; consec_err = 0; blocked = False; t0 = time.time()
    for t in targets:
        try:
            fin, sec, mcap, slug, why = resolve(t['nse'], t['bse'], t['company'])
        except Exception as e:
            fin, sec, mcap, slug, why = None, {}, None, '', f'ERROR:{type(e).__name__}'
        done += 1
        if why.startswith('ERROR'):
            counts['error'] += 1; consec_err += 1
        elif fin is not None:                       # resolved (name matched); fin may be {} if no annual tables
            counts['resolved'] += 1; consec_err = 0
            for fy, m in (fin or {}).items():
                for metric, val in m.items():
                    fin_w.writerow([t['isin'], fy, metric, val])
            meta_w.writerow([t['isin'], '', sec.get('Broad Sector', ''), sec.get('Sector', ''),
                             sec.get('Broad Industry', ''), sec.get('Industry', ''),
                             mcap if mcap is not None else '', slug, why]); meta_f.flush()
        else:
            counts['nomatch'] += 1; consec_err = 0
        log_w.writerow([t['isin'], t['company'], slug, why, len(fin) if fin else 0])
        fin_f.flush(); log_f.flush()
        if done % 20 == 0 or done == len(targets):
            open(str(config.logs_dir() / 'screener_fetch_progress.txt'), 'w').write(
                f"done={done}/{len(targets)} resolved={counts['resolved']} nomatch={counts['nomatch']} "
                f"error={counts['error']} consec_err={consec_err}\n")
            print(f"  {done}/{len(targets)} resolved={counts['resolved']} nomatch={counts['nomatch']} error={counts['error']}", flush=True)
        if consec_err >= MAX_CONSEC_ERR:
            blocked = True
            print(f"[circuit-breaker] {consec_err} consecutive errors — screener blocked, stopping pass", flush=True)
            break
        time.sleep(DELAY)
    fin_f.close(); log_f.close(); meta_f.close()
    print(f"\npass done: resolved={counts['resolved']} nomatch={counts['nomatch']} error={counts['error']} "
          f"remaining≈{len(targets)-counts['resolved']-counts['nomatch']} blocked={blocked}")
    sys.exit(2 if blocked else 0)
