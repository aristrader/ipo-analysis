"""Recover pre-IPO financials for the IN-WINDOW longterm slice (research/staging only).

Scope: longterm rows, cohort=='longterm', pre_ipo_pat null, listed 2012-2019, AND pre-listing
FY >= 2015 (screener's *current* free window is FY2015->FY2026, empirically verified June 2026).
IPOs whose pre-listing FY < 2015 cannot be served by screener regardless of identity resolution.

Identity: code-verified accept (Target-1 style). We fetch by BSE code then NSE symbol; if the page
200s and parses, we accept it as the concrete identity (the exchange code is permanent through a
rename; only a face-value split changes the ISIN). We additionally try a strict name_match and tag
whether it passed, so renames are explicit and auditable. We REJECT merger/acquisition cases where
the resolved page name signals a different surviving entity only if name_match fails AND the codes
404 (handled naturally). All staged rows keep the page name in the audit so a human can veto.

We only STAGE the metrics for the pre-listing FY (and fy-1, fy-2 for trajectory) so the existing
03b folding logic can pick them up. Output appends to financials_longterm_extra.csv (isin,fy,metric,value).
"""
import csv, os, sys, time, json
import scrapers.screener as sc

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)
FIN_EXTRA = p('data/raw/screener/financials_longterm_extra.csv')
AUDIT = p('docs/research/longterm_inwindow_log.csv')
DELAY = 1.6


def clean(s):
    s = (s or '').strip()
    return s[:-2] if s.endswith('.0') else s


def main():
    cands = json.load(open('/tmp/inwin_cands.json'))
    done = set()
    if os.path.exists(FIN_EXTRA) and os.path.getsize(FIN_EXTRA) > 0:
        for r in csv.DictReader(open(FIN_EXTRA)):
            done.add(r['isin'])
    fnew = (not os.path.exists(FIN_EXTRA)) or os.path.getsize(FIN_EXTRA) == 0
    fin_f = open(FIN_EXTRA, 'a', newline=''); fin_w = csv.writer(fin_f)
    if fnew:
        fin_w.writerow(['isin', 'fy', 'metric', 'value'])
    anew = (not os.path.exists(AUDIT)) or os.path.getsize(AUDIT) == 0
    aud_f = open(AUDIT, 'a', newline=''); aud_w = csv.writer(aud_f)
    if anew:
        aud_w.writerow(['isin', 'company', 'preFY', 'slug', 'page_name', 'name_ok', 'preFY_present', 'pat', 'verify'])

    stats = {'staged': 0, 'pat': 0, 'page_no_fy': 0, 'nomatch': 0}
    consec_err = 0
    for c in cands:
        isin = c['isin']
        if isin in done:
            continue
        preFY = int(c['preFY'])
        nse, bse = c['nse'], clean(c['bse'])
        page_name = ''; slug = ''; fin = None; name_ok = False
        try:
            for kind, sl in [('bse', bse or None), ('nse', nse or None)]:
                if not sl:
                    continue
                html = sc.fetch_company(sl, consolidated=False)
                time.sleep(0.8)
                if not html:
                    continue
                page_name = sc.page_name(html)
                name_ok = sc.name_match(page_name, c['company'], allow_digitstrip=True)
                f = sc.parse_financials(html)
                if not f:
                    h2 = sc.fetch_company(sl, consolidated=True); time.sleep(0.8)
                    if h2:
                        f = sc.parse_financials(h2)
                fin = f or {}
                slug = f'{kind}:{sl}'
                break
            consec_err = 0
        except Exception as e:
            consec_err += 1
            aud_w.writerow([isin, c['company'], preFY, '', '', '', '', '', f'ERROR:{type(e).__name__}'])
            aud_f.flush()
            if consec_err >= 8:
                print('[circuit-breaker] stopping'); break
            time.sleep(DELAY); continue

        if not fin:
            stats['nomatch'] += 1
            aud_w.writerow([isin, c['company'], preFY, slug, page_name, name_ok, False, '', 'no-page/no-financials'])
            aud_f.flush(); time.sleep(DELAY); continue

        pat = (fin.get(preFY) or {}).get('net_profit')
        prefy_present = preFY in fin
        if prefy_present:
            for fy in (preFY - 2, preFY - 1, preFY):
                m = fin.get(fy)
                if not m:
                    continue
                for metric, val in m.items():
                    fin_w.writerow([isin, fy, metric, val])
            fin_f.flush()
            stats['staged'] += 1
            if pat is not None:
                stats['pat'] += 1
            aud_w.writerow([isin, c['company'], preFY, slug, page_name, name_ok, True, pat,
                            'STAGED' + ('' if name_ok else '(rename-code-verified)')])
            print(f"  STAGED {isin} {c['company'][:26]:26} preFY={preFY} pat={pat} name_ok={name_ok} page='{page_name[:24]}'")
        else:
            stats['page_no_fy'] += 1
            yrs = sorted(fin)
            aud_w.writerow([isin, c['company'], preFY, slug, page_name, name_ok, False, '',
                            f'page-found-but-preFY-off-window earliest={yrs[0] if yrs else "-"}'])
            print(f"  NOFY   {isin} {c['company'][:26]:26} preFY={preFY} earliest={yrs[0] if yrs else '-'} page='{page_name[:24]}'")
        aud_f.flush()
        time.sleep(DELAY)
    fin_f.close(); aud_f.close()
    print(f"\n[in-window] staged={stats['staged']} with_pat={stats['pat']} page_no_fy={stats['page_no_fy']} nomatch={stats['nomatch']}")


if __name__ == '__main__':
    main()
