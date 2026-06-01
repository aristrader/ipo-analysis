"""Enrichment recovery (research/staging only — does NOT touch data/master).

Recovers sector/market-cap/pre-IPO-financials for rows that are data-incomplete, reusing
scrapers/screener.py's resolvers (NOT a parallel scraper). Resume-safe, 1 worker, polite.

Three targets (select with argv[1] = boom_sme | low | longterm_sample | all):

  1) boom_sme  : the 24 ISINs in sector_mcap_skipped.csv. These are NOT SME no-matches —
                 every one already has financials in financials.csv (they resolved in 03b).
                 They were skipped only because the company RENAMED (Zomato->Eternal, Burger
                 King->Restaurant Brands Asia, ...) so the page <h1> no longer name-matches.
                 The exchange code (BSE/NSE) is the concrete identity key and is far stronger
                 than a name match, so for these we fetch the SAME slug, record the resolved
                 page name (rename made explicit), and extract the breadcrumb/mcap. Confirmed
                 rows append to sector_mcap.csv; we LOG the old->new name for transparency.

  2) low       : the data_quality_tier=='low' rows. Strict name-verified resolve(); recover
                 sector/mcap (-> sector_mcap.csv) and pre_ipo financials (-> financials_extra.csv).

  3) longterm_sample : SAMPLE ~40 longterm ISINs missing pre_ipo_pat, attempt name-verified
                 resolve(), report hit-rate to estimate full-set yield. Clean hits staged to
                 financials_longterm_extra.csv.

Outputs:
  data/raw/screener/sector_mcap.csv            (append; cols isin,broad_sector,sector,industry,market_cap_cr,source)
  data/raw/screener/financials_longterm_extra.csv (append; cols isin,fy,metric,value)
  docs/research/enrichment_recovery_log.csv    (per-attempt audit: target,isin,company,page_name,slug,verify,result)
"""
import csv, os, sys, time
import scrapers.screener as screener

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)

SECTOR_PATH = p('data/raw/screener/sector_mcap.csv')
FIN_EXTRA   = p('data/raw/screener/financials_longterm_extra.csv')
AUDIT_PATH  = p('docs/research/enrichment_recovery_log.csv')
DELAY = 1.5


def _clean_code(s):
    s = (s or '').strip()
    return s[:-2] if s.endswith('.0') else s


def _done_sector_isins():
    d = set()
    if os.path.exists(SECTOR_PATH) and os.path.getsize(SECTOR_PATH) > 0:
        for r in csv.DictReader(open(SECTOR_PATH)):
            d.add(r['isin'].strip())
    return d


def _done_fin_isins():
    d = set()
    if os.path.exists(FIN_EXTRA) and os.path.getsize(FIN_EXTRA) > 0:
        for r in csv.DictReader(open(FIN_EXTRA)):
            d.add(r['isin'].strip())
    return d


def _open_append(path, header):
    new = (not os.path.exists(path)) or os.path.getsize(path) == 0
    f = open(path, 'a', newline=''); w = csv.writer(f)
    if new:
        w.writerow(header); f.flush()
    return f, w


def fetch_breadcrumb_by_code(nse, bse):
    """Fetch page by exchange code (concrete key); return (page_name, sec, mcap, slug) or (None,...).
    Tries bse then nse; first that 200s wins (the code IS the identity)."""
    for kind, slug in [('bse', _clean_code(bse) or None), ('nse', (nse or '').strip() or None)]:
        if not slug:
            continue
        html = screener.fetch_company(slug, consolidated=False)
        time.sleep(0.8)
        if not html:
            continue
        pn = screener.page_name(html)
        sec = screener.page_sector(html)
        mcap = screener.page_marketcap(html)
        if not sec and mcap is None:
            h2 = screener.fetch_company(slug, consolidated=True)
            time.sleep(0.8)
            if h2:
                sec = sec or screener.page_sector(h2)
                mcap = mcap if mcap is not None else screener.page_marketcap(h2)
        return pn, sec, mcap, f'{kind}:{slug}'
    return None, {}, None, ''


def run_boom_sme(sec_w, audit_w):
    rows = list(csv.DictReader(open(p('data/raw/screener/sector_mcap_skipped.csv'))))
    done = _done_sector_isins()
    recovered = nomatch = 0
    print(f"[boom_sme] {len(rows)} skipped ISINs; already-in-sector_mcap={sum(1 for r in rows if r['isin'] in done)}")
    for r in rows:
        isin = r['isin'].strip()
        if isin in done:
            continue
        # parse the original skip reason to get the exchange codes used (bse:CODE / nse:SYM)
        reason = r.get('reason', '')
        nse = bse = ''
        for tok in reason.replace('no-name-match[', '').rstrip(']').split('|'):
            if tok.startswith('bse:'):
                bse = tok.split(':', 1)[1].split('→')[0].strip()
            elif tok.startswith('nse:'):
                nse = tok.split(':', 1)[1].split('→')[0].strip()
        pn, sec, mcap, slug = fetch_breadcrumb_by_code(nse, bse)
        if pn is None:
            nomatch += 1
            audit_w.writerow(['boom_sme', isin, r['company'], '', slug, 'no-page', 'nomatch'])
            print(f"  NOMATCH {isin} {r['company'][:30]} (no live page)")
        else:
            broad = sec.get('Broad Sector', ''); sector = sec.get('Sector', ''); ind = sec.get('Industry', '')
            if not broad and not sector and not ind and mcap is None:
                nomatch += 1
                audit_w.writerow(['boom_sme', isin, r['company'], pn, slug, 'page-no-breadcrumb', 'nomatch'])
                print(f"  NOBREADCRUMB {isin} {r['company'][:30]} -> page='{pn}'")
            else:
                recovered += 1
                sec_w.writerow([isin, broad, sector, ind, mcap if mcap is not None else '', 'screener'])
                # rename made explicit in audit (old name -> resolved page name)
                audit_w.writerow(['boom_sme', isin, r['company'], pn, slug,
                                  f'rename-code-verified', f'RECOVERED broad={broad}|sec={sector}|mcap={mcap}'])
                print(f"  RECOVERED {isin} {r['company'][:28]:28} -> '{pn[:28]}' | {broad}/{sector} mcap={mcap}")
        time.sleep(DELAY)
    print(f"[boom_sme] recovered={recovered} nomatch={nomatch}")
    return recovered, nomatch


def run_low(sec_w, fin_w, audit_w):
    rows = [r for r in csv.DictReader(open(p('data/master/ipo_analysis.csv')))
            if r.get('data_quality_tier') == 'low']
    sdone = _done_sector_isins(); fdone = _done_fin_isins()
    sec_rec = fin_rec = nomatch = 0
    print(f"[low] {len(rows)} low-tier rows")
    for r in rows:
        isin = r['isin'].strip()
        nse = (r.get('nse_symbol') or '').strip()
        bse = _clean_code(r.get('bse_script_code'))
        try:
            fin, sec, mcap, slug, why = screener.resolve(nse, bse, r['company_name'])
        except Exception as e:
            audit_w.writerow(['low', isin, r['company_name'], '', '', f'ERROR:{type(e).__name__}', 'error'])
            time.sleep(DELAY); continue
        if fin is None:
            nomatch += 1
            audit_w.writerow(['low', isin, r['company_name'], '', slug, why, 'nomatch'])
            print(f"  NOMATCH {isin} {r['company_name'][:32]} | {why[:50]}")
            time.sleep(DELAY); continue
        broad = sec.get('Broad Sector', ''); sector = sec.get('Sector', ''); ind = sec.get('Industry', '')
        got = []
        if (broad or sector or ind or mcap is not None) and isin not in sdone:
            sec_w.writerow([isin, broad, sector, ind, mcap if mcap is not None else '', 'screener'])
            sec_rec += 1; got.append(f'sector={broad}/{sector} mcap={mcap}')
        if fin and isin not in fdone:
            nyr = 0
            for fy, m in fin.items():
                for metric, val in m.items():
                    fin_w.writerow([isin, fy, metric, val]); nyr += 1
            if nyr:
                fin_rec += 1; got.append(f'fin {len(fin)}yr')
        audit_w.writerow(['low', isin, r['company_name'], screener.page_name(''), slug, why,
                          'RECOVERED ' + '; '.join(got) if got else 'matched-no-new-data'])
        print(f"  {'RECOVERED' if got else 'MATCH-NODATA'} {isin} {r['company_name'][:30]:30} | {'; '.join(got)}")
        time.sleep(DELAY)
    print(f"[low] sector_recovered={sec_rec} fin_recovered={fin_rec} nomatch={nomatch}")
    return sec_rec, fin_rec, nomatch


def run_longterm_sample(fin_w, audit_w, n_sample=40):
    rows = [r for r in csv.DictReader(open(p('data/master/ipo_analysis.csv')))
            if r.get('cohort') == 'longterm' and not (r.get('pre_ipo_pat') or '').strip()
            and ((r.get('nse_symbol') or '').strip() or _clean_code(r.get('bse_script_code')))]
    total = len(rows)
    # deterministic spread sample across the list (every k-th) so it's representative, not head-biased
    step = max(1, total // n_sample)
    sample = rows[::step][:n_sample]
    fdone = _done_fin_isins()
    hit = pat_hit = nomatch = 0
    print(f"[longterm_sample] full missing-pat pool={total}; sampling {len(sample)} (every {step}th)")
    for r in sample:
        isin = r['isin'].strip()
        nse = (r.get('nse_symbol') or '').strip()
        bse = _clean_code(r.get('bse_script_code'))
        try:
            fin, sec, mcap, slug, why = screener.resolve(nse, bse, r['company_name'])
        except Exception as e:
            audit_w.writerow(['longterm_sample', isin, r['company_name'], '', '', f'ERROR:{type(e).__name__}', 'error'])
            time.sleep(DELAY); continue
        if fin is None:
            nomatch += 1
            audit_w.writerow(['longterm_sample', isin, r['company_name'], '', slug, why, 'nomatch'])
            print(f"  NOMATCH  {isin} {r['company_name'][:34]:34} | {why[:46]}")
        else:
            hit += 1
            has_pat = any('net_profit' in m for m in fin.values())
            if has_pat: pat_hit += 1
            if fin and isin not in fdone:
                for fy, m in fin.items():
                    for metric, val in m.items():
                        fin_w.writerow([isin, fy, metric, val])
            audit_w.writerow(['longterm_sample', isin, r['company_name'], '', slug, why,
                              f'MATCH years={len(fin)} has_pat={has_pat}'])
            print(f"  MATCH    {isin} {r['company_name'][:34]:34} | years={len(fin)} has_pat={has_pat}")
        time.sleep(DELAY)
    print(f"\n[longterm_sample] n={len(sample)} resolved={hit} with_pat={pat_hit} nomatch={nomatch}")
    if sample:
        pat_rate = pat_hit / len(sample)
        print(f"[longterm_sample] PAT hit-rate={pat_rate:.1%} -> est full-set PAT recoveries ~{round(pat_rate*total)} of {total}")
    return len(sample), hit, pat_hit, nomatch, total


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    os.makedirs(p('docs/research'), exist_ok=True)
    sec_f, sec_w = _open_append(SECTOR_PATH, ['isin', 'broad_sector', 'sector', 'industry', 'market_cap_cr', 'source'])
    fin_f, fin_w = _open_append(FIN_EXTRA, ['isin', 'fy', 'metric', 'value'])
    aud_f, aud_w = _open_append(AUDIT_PATH, ['target', 'isin', 'company', 'page_name', 'slug', 'verify', 'result'])
    try:
        if which in ('boom_sme', 'all'):
            run_boom_sme(sec_w, aud_w); sec_f.flush(); aud_f.flush()
        if which in ('low', 'all'):
            run_low(sec_w, fin_w, aud_w); sec_f.flush(); fin_f.flush(); aud_f.flush()
        if which in ('longterm_sample', 'all'):
            run_longterm_sample(fin_w, aud_w); fin_f.flush(); aud_f.flush()
    finally:
        sec_f.close(); fin_f.close(); aud_f.close()


if __name__ == '__main__':
    main()
