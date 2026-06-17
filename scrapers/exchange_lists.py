"""Authoritative symbol↔ISIN maps from cached NSE/BSE reference lists."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config

REF = str(config.src('reference'))

def load():
    """Load symbol↔ISIN maps from cached exchange lists.

    Returns:
        (sym2isin, isin2sym) — dicts mapping symbols to ISINs and vice versa.
    """
    sym2isin = {}
    isin2sym = {}

    # NSE Mainboard
    for f, sc, ic in [('nse_mainboard.csv', 'SYMBOL', ' ISIN NUMBER'),
                       ('nse_emerge_sme.csv', 'SYMBOL', 'ISIN_NUMBER')]:
        p = os.path.join(REF, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            s = (r.get(sc) or '').strip()
            i = (r.get(ic) or '').strip()
            if s and i:
                sym2isin[s] = i
                isin2sym[i] = s

    # BSE Master
    bp = os.path.join(REF, 'bse_master.csv')
    if os.path.exists(bp):
        for r in csv.DictReader(open(bp)):
            s = (r.get('scrip_id') or '').strip()
            i = (r.get('ISIN_NUMBER') or '').strip()
            if s and i:
                sym2isin['BSE:' + s.upper()] = i
                isin2sym.setdefault(i, s)

    return sym2isin, isin2sym
