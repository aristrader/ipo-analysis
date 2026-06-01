"""DRHP P&L extractor with cover-page verification gate. Stdin: pdf path + meta. Pure offline (no net)."""
import sys, re, json
import pdfplumber

# revenue line patterns, in priority order (lowercased, matched at line start after stripping)
REV_PATTERNS = [
    r'sales\s*\(net\)', r'net sales', r'sales and services', r'sales & services',
    r'income from operations', r'revenue from operations', r'total operating income',
    r'operating income', r'total income from operations', r'sales\b', r'total revenue',
    r'gross sales', r'turnover',
]
PAT_PATTERNS = [
    r'net profits?(?:/\(losses?\))? after extraordinary items',
    r'net profits?(?:/\(losses?\))? after tax',
    r'net profits?(?:/\(losses?\))? as restated',
    r'profits?(?:/\(losses?\))? after tax',
    r'net profits?(?:/\(losses?\))? for the (year|period)',
    r'restated profits?(?:/\(losses?\))? (for the year|after tax)',
    r'profits?/\(losses?\) after tax',
    r'profit/\(loss\) after tax',
    r'net profits?(?:/\(losses?\))?\b',
    r'profit after taxation',
]
OP_PATTERNS = [
    r'profit before tax', r'net profit before tax', r'operating profit', r'ebitda',
    r'profit before interest', r'profit before extraordinary',
]


def norm_tokens(name):
    STOP = {'ltd', 'limited', 'pvt', 'private', 'corp', 'co', 'company', 'the', 'com',
            'india', 'inc', 'fpo', 'and'}
    n = (name or '').lower().replace('&', ' and ')
    n = re.sub(r'\([^)]*\)', ' ', n)
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    return [t for t in n.split() if t and t not in STOP]


def cover_match(cover_text, name):
    """Return (matched_bool, overlap_ratio). Match issuer tokens against cover page."""
    ct = (cover_text or '').lower()
    toks = norm_tokens(name)
    if not toks:
        return False, 0.0
    hits = sum(1 for t in toks if t in ct)
    ratio = hits / len(toks)
    # require all significant tokens present (>=0.8) for a confident gate
    return ratio >= 0.8, ratio


def parse_num(s):
    s = s.replace(',', '').strip()
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    if s in ('', '-', '–', 'nil', 'NIL'):
        return None
    m = re.match(r'^-?\d+(\.\d+)?$', s)
    if not m:
        return None
    v = float(s)
    return -v if neg else v


def extract_row_numbers(line):
    """Pull trailing numeric columns from a P&L line. Returns list (left->right = newest->oldest usually)."""
    # find all number-like tokens including (xx.xx) and commas
    nums = re.findall(r'\(?-?[\d,]+\.\d+\)?|\(?-?[\d,]{1,}\)?(?=\s|$)', line)
    out = []
    for n in nums:
        v = parse_num(n)
        if v is not None:
            out.append(v)
    return out


PNL_TITLE = re.compile(r'(profit and loss|profits and losses|profit & loss)', re.I)
COMMONSIZE = re.compile(r'%\s*of\s*total|percentage of total income|% of total income', re.I)


def find_pnl_page(pdf, issuer_name):
    """Find the page index of the issuer's restated P&L statement (absolute ₹, not common-size).
    Returns (page_idx, text, why) or (None,None,reason). Scores candidates; prefers absolute-₹ tables
    that carry a revenue line and a profit line with numeric values + year columns.
    """
    issuer_toks = set(norm_tokens(issuer_name))
    candidates = []
    for i, pg in enumerate(pdf.pages):
        t = pg.extract_text() or ''
        tl = t.lower()
        if 'restated' not in tl or not PNL_TITLE.search(tl):
            continue
        has_rev = any(re.search(p, tl) for p in REV_PATTERNS)
        has_pat = any(re.search(p, tl) for p in PAT_PATTERNS)
        if not (has_rev and has_pat):
            continue
        # page must carry real numbers (a row with a decimal figure)
        if not re.search(r'\d,?\d*\.\d', t):
            continue
        score = 0
        head = tl[:160]
        # strong: the page TITLE is a P&L statement
        if PNL_TITLE.search(head) and ('statement' in head or 'summary' in head or 'annexure' in head):
            score += 6
        elif PNL_TITLE.search(head):
            score += 3
        # demote common-size (% of total income) pages — they are not absolute ₹
        pct_lines = sum(1 for ln in t.split('\n') if ln.count('%') >= 2 or '% of' in ln.lower())
        if COMMONSIZE.search(tl) or pct_lines >= 5:
            score -= 5
        if issuer_toks and issuer_toks & set(norm_tokens(t[:400])):
            score += 2
        if extract_year_headers(t):
            score += 2
        if 'total expenditure' in tl or 'total income' in tl or 'total revenue' in tl:
            score += 1
        candidates.append((score, -i, i, t))   # earlier page breaks ties (main statement before notes)
    if not candidates:
        return []
    candidates.sort(reverse=True)
    # return list of (page_idx, text, score), best first
    return [(c[2], c[3], c[0]) for c in candidates if c[0] > 0]


def detect_unit(text, pdf=None, page_idx=None):
    """Detect reporting unit. Checks the page first, then nearby pages (heading often on a prior page)."""
    def scan(tl):
        # match the unit word preceded by either 'in ...' OR a bare currency/'amount' token:
        #   "in ₹ Million", "in Rs. Lacs", "(Rs. Million)", "Amount INR Thousand", "(₹ in Crore)"
        pre = r'(?:\bin\b|rs\.?|inr|₹|rupees|amounts?(?:\s+in)?)\s*(?:rs\.?|inr|₹|rupees)?\s*'
        if re.search(pre + r'crores?\b', tl) or 'in cr.' in tl or '(₹ cr' in tl or '(rs. cr' in tl:
            return 'crore', 1.0
        if re.search(pre + r'(?:lakhs?|lacs?)\b', tl):
            return 'lakh', 0.01
        if re.search(pre + r'millions?\b', tl) or 'in mn' in tl or 'rs. mn' in tl or '(₹ mn' in tl:
            return 'million', 0.1
        if re.search(pre + r'thousands?\b', tl) or "in '000" in tl or "in 000" in tl:
            return 'thousand', 0.0001
        return None
    tl = (text or '').lower()
    u = scan(tl)
    if u:
        return u
    # look back a few pages (unit heading sometimes only on the section's first page)
    if pdf is not None and page_idx is not None:
        for j in range(max(0, page_idx - 3), page_idx):
            jt = (pdf.pages[j].extract_text() or '').lower()
            u = scan(jt)
            if u:
                return u
    return 'unknown', None


def extract_year_headers(text):
    """Find the fiscal-year columns from the table header. Returns list of years (ints) left->right.

    Headers are often wrapped: 'March 31, March 31,\\n2009 2008 2007...'. Strategy: find the header
    region (before the first data line that has labels+numbers), grab the line that is mostly years.
    """
    lines = text.split('\n')
    best = []
    # combine the header region's first ~6 lines so wrapped year rows ('31-Mar-\n12 11 10') rejoin
    head_region = ' '.join(lines[:8])
    # Pattern A: explicit 'Mar-YYYY' / 'March 31, YYYY' / '31-Mar-YYYY'
    yrsA = re.findall(r'(?:mar(?:ch)?[ ,\-]*31[ ,\-]*|31[ \-]*mar(?:ch)?[ \-]*)(\d{4})', head_region, re.I)
    if len(yrsA) >= 2:
        best = [int(y) for y in yrsA]
    if not best:
        # Pattern B: hyphenated 'Mar-YY' / 'YY-Mar' (e.g. 31-Mar-12, Mar-11) -> 20YY.
        # Require a hyphen/slash adjacent to the month so 'March 31' (day=31) is NOT read as year 2031.
        yrsB = re.findall(r'(?:mar(?:ch)?[\-/](\d{2})\b|\b(\d{2})[\-/]mar)', head_region, re.I)
        yrsB = [a or b for a, b in yrsB]
        yrsB = [y for y in yrsB if 0 <= int(y) <= 26]   # plausible YY (2000-2026)
        if len(yrsB) >= 2:
            best = [2000 + int(y) for y in yrsB]
    if not best:
        # Pattern C: a line that is mostly bare 4-digit years
        for ln in lines[:12]:
            full = [int(a + b) for a, b in re.findall(r'\b(19|20)(\d{2})\b', ln)]
            full = [y for y in full if 1998 <= y <= 2026]
            toks = ln.split()
            if len(full) >= 2 and len(full) >= max(1, len([t for t in toks if re.search(r'[a-zA-Z]', t)])):
                if len(full) > len(best):
                    best = full
    # plausibility filter
    best = [y for y in best if 1998 <= y <= 2026]
    return best


def pick_line(text, patterns):
    """Return (matched_pattern, numbers_list) for the FIRST matching P&L line, preferring earlier patterns."""
    lines = text.split('\n')
    for pat in patterns:
        for ln in lines:
            low = ln.strip().lower()
            # the label must be near the start of the line (before the numbers)
            m = re.search(pat, low)
            if m and m.start() <= 35:
                nums = extract_row_numbers(ln)
                if nums:
                    return pat, nums
    return None, None


def evaluate_page(ptext, pdf, idx, preFY):
    """Extract rev/pat/op for the pre-IPO FY from one P&L page's text and apply the sanity gate.
    Returns a result dict with confidence in {verified, unverified}."""
    r = {}
    unit_name, unit_mult = detect_unit(ptext, pdf, idx)
    rev_pat, rev_nums = pick_line(ptext, REV_PATTERNS)
    pat_pat, pat_nums = pick_line(ptext, PAT_PATTERNS)
    op_pat, op_nums = pick_line(ptext, OP_PATTERNS)
    year_hdr = extract_year_headers(ptext)
    r.update({'year_headers': year_hdr, 'unit': unit_name, 'rev_label': rev_pat, 'pat_label': pat_pat,
              'rev_nums': rev_nums, 'pat_nums': pat_nums, 'op_nums': op_nums})
    if unit_mult is None:
        r['confidence'] = 'unverified'; r['reason'] = 'unit_unknown'; return r
    if not (rev_nums and pat_nums):
        r['confidence'] = 'unverified'; r['reason'] = 'pnl_lines_not_parsed'; return r
    r['unit_mult'] = unit_mult

    # detect a LEADING interim/stub column (e.g. 'period ended June 30, 2007' / 'X months ended' /
    # 'nine month period') that precedes the full annual columns. If present, the first data column is
    # a partial period and must be skipped — and if its year duplicates the first annual year, the year
    # header carries a duplicate that would otherwise mis-route the pick to the stub.
    htext = ptext[:600].lower()
    has_stub = bool(re.search(r'(period ended|months? ended|months? period|quarter ended|half year)', htext))
    yh = list(year_hdr)
    # drop a leading duplicate year caused by 'period ended <Y>' + 'year ended <Y>'
    if has_stub and len(yh) >= 2 and yh[0] == yh[1]:
        stub_lead = True
        yh_eff = yh[1:]
    elif has_stub and len(yh) >= 1:
        # stub present but distinct year (interim of the NEXT year) — drop leading col only if nums longer
        stub_lead = True
        yh_eff = yh
    else:
        stub_lead = False
        yh_eff = yh

    def pick_col(nums):
        if not yh_eff or not nums:
            return None, None
        # align the rightmost len(yh_eff) numbers to the effective (annual) year columns,
        # i.e. drop any leading stub/partial-period column(s)
        n = nums[-len(yh_eff):] if len(nums) >= len(yh_eff) else None
        if n is None or len(n) != len(yh_eff):
            return None, None
        if preFY in yh_eff:
            return n[yh_eff.index(preFY)], preFY
        return n[0], yh_eff[0]

    rv, ry = pick_col(rev_nums)
    pv, py = pick_col(pat_nums)
    opv, opy = pick_col(op_nums)
    r['guess_fy'] = ry if ry == py else None
    r['guess_net_sales_cr'] = round(rv * unit_mult, 2) if rv is not None else None
    r['guess_pat_cr'] = round(pv * unit_mult, 2) if pv is not None else None
    r['guess_op_cr'] = round(opv * unit_mult, 2) if opv is not None and opy == ry else None
    same_ncols = len(rev_nums) == len(pat_nums)
    sales_pos = rv is not None and rv >= 1.0
    margin_ok = (rv is not None and pv is not None and rv >= abs(pv) * 0.999)
    fy_ok = (preFY is not None and ry is not None and ry == py and ry in (preFY, preFY - 1))
    # PAT-suspect guard (cross-validation 2026-06-02 caught DLF: pat==op == PBT, not after-tax). If the
    # PAT pick equals the operating/PBT pick, the after-tax line wasn't isolated -> PAT is untrustworthy.
    pat_suspect = (r['guess_pat_cr'] is not None and r['guess_op_cr'] is not None
                   and abs(r['guess_pat_cr'] - r['guess_op_cr']) < 0.01)
    r['pat_suspect'] = pat_suspect
    if pat_suspect:
        r['confidence'] = 'unverified'
        r['reason'] = 'pat==op (likely PBT not after-tax) — net_sales may be OK, PAT to review'
        return r
    if rv is not None and pv is not None and fy_ok and sales_pos and margin_ok and same_ncols:
        r['confidence'] = 'verified'
        if ry == preFY - 1:
            r['reason'] = f'used_preFY-1({ry}); DRHP predates preFY{preFY}'
        else:
            r['reason'] = ''
    else:
        r['confidence'] = 'unverified'
        r['reason'] = (f'gate(years={year_hdr},pickFY={ry},preFY={preFY},fy_ok={fy_ok},'
                       f'nrev={len(rev_nums)},npat={len(pat_nums)},sales={rv},pat={pv},'
                       f'pos={sales_pos},margin={margin_ok},ncols={same_ncols})')
    return r


def main():
    meta = json.loads(sys.argv[1])
    pdf_path = meta['pdf']
    name = meta['name']
    preFY = meta.get('preFY')
    result = {'verify_method': '', 'confidence': 'reject', 'reason': ''}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            npages = len(pdf.pages)
            cover = ''
            for p in pdf.pages[:3]:
                cover += (p.extract_text() or '') + '\n'
            matched, ratio = cover_match(cover, name)
            # capture cover issue date
            dm = re.search(r'(prospectus|red herring).{0,40}?(dated|date[d]?)\s*[:\-]?\s*'
                           r'([A-Z][a-z]+ \d{1,2},? \d{4})', cover, re.I)
            cover_date = dm.group(3) if dm else ''
            result['cover_ratio'] = round(ratio, 2)
            result['cover_date'] = cover_date
            result['npages'] = npages
            if not matched:
                result['reason'] = f'cover_name_mismatch(ratio={ratio:.2f})'
                result['confidence'] = 'reject'
                print(json.dumps(result)); return
            # find candidate P&L pages, try each (consolidated-preferred ordering), keep first that PASSES sanity.
            cands = find_pnl_page(pdf, name)
            if not cands:
                result['reason'] = 'no_restated_pnl_page'
                result['confidence'] = 'unverified'
                result['verify_method'] = f'cover_ok(ratio={ratio:.2f}) but no_restated_pnl_page'
                print(json.dumps(result)); return
            # prefer CONSOLIDATED statements (matches typical reported basis), then score order
            cands.sort(key=lambda c: (0 if 'consolidated' in c[1][:120].lower() else 1, -c[2]))
            best_fail = None
            for idx, ptext, score in cands:
                ev = evaluate_page(ptext, pdf, idx, preFY)
                ev['pnl_page'] = idx
                ev['verify_method'] = (f'cover_ok(ratio={ratio:.2f},date={cover_date}); '
                                       f'pnl_page={idx}(score={score},'
                                       f'{"consol" if "consolidated" in ptext[:120].lower() else "standalone"}); '
                                       f'unit={ev.get("unit")}')
                ev['cover_ratio'] = result['cover_ratio']
                ev['cover_date'] = cover_date
                ev['npages'] = npages
                if ev['confidence'] == 'verified':
                    print(json.dumps(ev)); return
                if best_fail is None:
                    best_fail = ev
            print(json.dumps(best_fail)); return
    except Exception as e:
        result['reason'] = f'ERROR:{type(e).__name__}:{e}'
        result['confidence'] = 'reject'
        print(json.dumps(result))


if __name__ == '__main__':
    main()
