"""Batch DRHP recovery driver.
Input: /tmp/drhp_queue.csv with cols isin,name,preFY,landing_url (landing_url from WebSearch).
For each: curl landing HTML -> extract attachdocs pdf link -> download -> run extractor.
Writes /tmp/drhp_results.jsonl (one json line per isin) + caches PDFs in /tmp/drhp_pdfs/.
Rate-limited. Resume-safe (skips isins already in results).
"""
import csv, os, re, json, time, subprocess, urllib.request, urllib.error

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
PDFDIR = '/tmp/drhp_pdfs'
RES = '/tmp/drhp_results.jsonl'
QUEUE = '/tmp/drhp_queue.csv'
os.makedirs(PDFDIR, exist_ok=True)


def get(url, timeout=40, binary=False):
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return data if binary else data.decode('utf-8', 'ignore')


def landing_pdf_links(html):
    return list(dict.fromkeys(re.findall(r'attachdocs/(\d+)\.pdf', html)))


def main():
    done = set()
    if os.path.exists(RES):
        for ln in open(RES):
            try:
                done.add(json.loads(ln)['isin'])
            except Exception:
                pass
    rows = list(csv.DictReader(open(QUEUE)))
    out = open(RES, 'a')
    for i, r in enumerate(rows):
        isin = r['isin']
        if isin in done:
            continue
        rec = {'isin': isin, 'name': r['name'], 'preFY': r.get('preFY')}
        url = (r.get('landing_url') or '').strip()
        try:
            preFY = int(float(r['preFY'])) if r.get('preFY') else None
        except Exception:
            preFY = None
        if not url:
            rec.update({'confidence': 'reject', 'reason': 'no_landing_url'})
            out.write(json.dumps(rec) + '\n'); out.flush(); continue
        try:
            if url.endswith('.pdf'):
                pdf_ids = [re.search(r'(\d+)\.pdf', url).group(1)]
                pdf_urls = [url]
            else:
                html = get(url)
                time.sleep(1.0)
                ids = landing_pdf_links(html)
                if not ids:
                    rec.update({'confidence': 'reject', 'reason': 'no_pdf_link_on_landing'})
                    out.write(json.dumps(rec) + '\n'); out.flush(); continue
                pdf_ids = ids
                pdf_urls = [f'https://www.sebi.gov.in/sebi_data/attachdocs/{x}.pdf' for x in ids]
        except Exception as e:
            rec.update({'confidence': 'reject', 'reason': f'landing_fetch_err:{type(e).__name__}'})
            out.write(json.dumps(rec) + '\n'); out.flush(); continue

        best = None
        for pid, purl in zip(pdf_ids, pdf_urls):
            pdfpath = f'{PDFDIR}/{isin}_{pid}.pdf'
            try:
                if not os.path.exists(pdfpath) or os.path.getsize(pdfpath) < 10000:
                    data = get(purl, binary=True)
                    open(pdfpath, 'wb').write(data)
                    time.sleep(1.5)
                meta = json.dumps({'pdf': pdfpath, 'name': r['name'], 'preFY': preFY})
                p = subprocess.run(['python', '/tmp/drhp_extract.py', meta],
                                   capture_output=True, text=True, timeout=180)
                ext = json.loads(p.stdout.strip().split('\n')[-1]) if p.stdout.strip() else {
                    'confidence': 'reject', 'reason': f'extract_err:{p.stderr[-200:]}'}
                ext['pdf_id'] = pid
                ext['pdf_url'] = purl
                order = {'verified': 3, 'unverified': 2, 'reject': 1}
                if best is None or order.get(ext.get('confidence'), 0) > order.get(best.get('confidence'), 0):
                    best = ext
                if ext.get('confidence') == 'verified':
                    break
            except Exception as e:
                best = best or {'confidence': 'reject', 'reason': f'pdf_err:{type(e).__name__}:{e}', 'pdf_id': pid}
        rec.update(best or {'confidence': 'reject', 'reason': 'no_pdf_processed'})
        out.write(json.dumps(rec) + '\n'); out.flush()
        print(f"[{i+1}/{len(rows)}] {isin} {r['name'][:30]:30} -> {rec.get('confidence')} {rec.get('reason','')[:40]}", flush=True)
        time.sleep(0.5)
    out.close()


if __name__ == '__main__':
    main()
