"""Phase 03f: recover MISSING sector/industry/market-cap for the BOOM cohort.

Known gap: the boom screener enrichment (03b) grabbed financials only, not the
sector/industry/market-cap breadcrumb — so company_meta.csv covers longterm well but
barely touches boom. broad_sector is ~22% for boom vs ~72% for longterm.

These companies ALREADY resolved on screener (their financials prove it). This is a
cheap, targeted RE-PULL of just the sector + market_cap breadcrumb for boom ISINs that
(a) have screener financials and (b) currently lack broad_sector in universe.csv.

REUSES scrapers/screener.py's resolve() — same name-verified resolution, same
page_sector()/page_marketcap() extractors used to build longterm's sector. NOT a parallel
scraper. Strict: a row is written only when resolve() name-matches the page (the project
rule is flag/skip, never mis-assign); skips are logged.

Output (resume-safe checkpoint): data/raw/screener/sector_mcap.csv
  columns: isin,broad_sector,sector,industry,market_cap_cr,source   (source='screener')
  (broad_sector is screener's "Broad Sector" breadcrumb — the SAME field 08's company_meta
   fold reads for longterm; we keep it so the fold fills broad_sector faithfully rather than
   inventing a sector->broad_sector mapping the pipeline doesn't have.)

Run (1 worker, polite, resume-safe — re-run continues where it stopped):
    PYTHONPATH=. python pipeline/03f_sector_mcap.py [DELAY_SECONDS]

screener throttles aggressively → 1 worker, internal+between-company sleeps, circuit
breaker after consecutive errors. Re-run to resume after a block.
"""
import csv
import os
import sys
import time

import scrapers.screener as screener

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*a):
    return os.path.join(ROOT, *a)


def build_targets():
    """Boom ISINs that resolved on screener (in financials.csv) but lack broad_sector in
    universe.csv. Identity (nse/bse/company) is taken from the base master files so we can
    re-resolve via the SAME resolve() path that originally found the financials."""
    # boom rows missing broad_sector
    boom_missing = set()
    boom_total = 0
    for r in csv.DictReader(open(p('data/master/universe.csv'))):
        if r.get('cohort') == 'boom':
            boom_total += 1
            if not (r.get('broad_sector') or '').strip():
                boom_missing.add(r['isin'].strip())

    # ISINs that resolved on screener (have financials)
    resolved = set()
    for r in csv.DictReader(open(p('data/raw/screener/financials.csv'))):
        resolved.add(r['isin'].strip())

    # identity (nse_symbol / bse_script_code / company_name) from the boom base masters
    ident = {}
    for fn in ('_base_mainboard.csv', '_base_sme.csv'):
        path = p('data/master', fn)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            ident[r['isin'].strip()] = {
                'company': r.get('company_name', ''),
                'nse': (r.get('nse_symbol') or '').strip(),
                'bse': (r.get('bse_script_code') or '').strip(),
            }

    targets = []
    for isin in (boom_missing & resolved):
        info = ident.get(isin)
        if not info or not (info['nse'] or info['bse']):
            continue   # no exchange code to re-resolve with → skip (logged in summary)
        targets.append({'isin': isin, **info})
    return targets, boom_total, len(boom_missing)


def main():
    DELAY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2   # between companies
    MAX_CONSEC_ERR = 8

    os.makedirs(p('data/raw/screener'), exist_ok=True)
    OUT_PATH = p('data/raw/screener/sector_mcap.csv')
    SKIP_PATH = p('data/raw/screener/sector_mcap_skipped.csv')
    os.makedirs(p('logs'), exist_ok=True)

    targets, boom_total, boom_missing = build_targets()

    # resume: skip ISINs already written (recovered) or definitively skipped
    done = set()
    if os.path.exists(OUT_PATH) and os.path.getsize(OUT_PATH) > 0:
        for r in csv.DictReader(open(OUT_PATH)):
            done.add(r['isin'].strip())
    if os.path.exists(SKIP_PATH) and os.path.getsize(SKIP_PATH) > 0:
        for r in csv.DictReader(open(SKIP_PATH)):
            done.add(r['isin'].strip())
    todo = [t for t in targets if t['isin'] not in done]

    print(f"boom total={boom_total}  boom missing broad_sector={boom_missing}")
    print(f"targets (boom-missing & resolved-on-screener & have exchange code)={len(targets)}")
    print(f"already done (recovered+skipped)={len(done)}  to fetch this run={len(todo)}", flush=True)

    out_new = (not os.path.exists(OUT_PATH)) or os.path.getsize(OUT_PATH) == 0
    skip_new = (not os.path.exists(SKIP_PATH)) or os.path.getsize(SKIP_PATH) == 0
    out_f = open(OUT_PATH, 'a', newline=''); out_w = csv.writer(out_f)
    skip_f = open(SKIP_PATH, 'a', newline=''); skip_w = csv.writer(skip_f)
    if out_new:
        out_w.writerow(['isin', 'broad_sector', 'sector', 'industry', 'market_cap_cr', 'source'])
        out_f.flush()
    if skip_new:
        skip_w.writerow(['isin', 'company', 'slug', 'reason']); skip_f.flush()

    counts = {'recovered': 0, 'skipped': 0, 'error': 0}
    consec_err = 0
    blocked = False
    n = 0
    for t in todo:
        try:
            # SAME resolution path that found the financials: name-verified resolve().
            fin, sec, mcap, slug, why = screener.resolve(t['nse'], t['bse'], t['company'])
        except Exception as e:
            fin, sec, mcap, slug, why = None, {}, None, '', f'ERROR:{type(e).__name__}'
        n += 1

        if why.startswith('ERROR'):
            counts['error'] += 1
            consec_err += 1
            skip_w.writerow([t['isin'], t['company'], slug, why]); skip_f.flush()
        elif fin is None:
            # resolve() returned no name match → strict skip, do NOT guess
            counts['skipped'] += 1
            consec_err = 0
            skip_w.writerow([t['isin'], t['company'], slug, why]); skip_f.flush()
        else:
            # page name-matched the company. Write breadcrumb/mcap if we got any of them.
            broad_sector = sec.get('Broad Sector', '')
            sector = sec.get('Sector', '')
            industry = sec.get('Industry', '')
            if not broad_sector and not sector and not industry and mcap is None:
                counts['skipped'] += 1
                consec_err = 0
                skip_w.writerow([t['isin'], t['company'], slug, f'matched-but-no-breadcrumb({why[:40]})'])
                skip_f.flush()
            else:
                counts['recovered'] += 1
                consec_err = 0
                out_w.writerow([t['isin'], broad_sector, sector, industry,
                                mcap if mcap is not None else '', 'screener'])
                out_f.flush()

        if n % 10 == 0 or n == len(todo):
            msg = (f"  {n}/{len(todo)} recovered={counts['recovered']} "
                   f"skipped={counts['skipped']} error={counts['error']} consec_err={consec_err}")
            print(msg, flush=True)
            open(p('logs/sector_mcap_progress.txt'), 'w').write(msg + "\n")

        if consec_err >= MAX_CONSEC_ERR:
            blocked = True
            print(f"[circuit-breaker] {consec_err} consecutive errors — screener likely blocking, "
                  f"stopping. Re-run to resume.", flush=True)
            break
        time.sleep(DELAY)

    out_f.close(); skip_f.close()
    remaining = len(todo) - n if blocked else 0
    print(f"\npass done: recovered={counts['recovered']} skipped={counts['skipped']} "
          f"error={counts['error']} blocked={blocked} remaining_this_run={remaining}")
    print(f"checkpoint → {OUT_PATH}")
    sys.exit(2 if blocked else 0)


if __name__ == '__main__':
    main()
