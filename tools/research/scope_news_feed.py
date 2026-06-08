"""News-feed SCOPE probe (Thread C / future_ideas idea #2): is the FREE NSE corporate-announcements
API viable as a per-ISIN news/catalyst source? Probe a sample of recent listings, report coverage +
fields. SCOPE ONLY — decides build/no-build. No build, no staging writes."""
import json, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scrapers"))

SYMS = ['GSPCROP', 'RIIT', 'POWERICA', 'OMPOWER', 'KISSHT', 'BAGMANE', 'CITIUSINVT', 'CMPDI']
API = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={sym}"

def main():
    try:
        from nse_session import prime_nse_session
        s = prime_nse_session("https://www.nseindia.com/companies-listing/corporate-filings-announcements")
    except Exception as e:
        print(f"could not prime NSE session ({e}) — run this probe on the laptop with network.")
        return
    hits, fields = 0, set()
    for sym in SYMS:
        try:
            r = s.get(API.format(sym=sym), timeout=20)
            data = r.json() if r.status_code == 200 else []
            n = len(data) if isinstance(data, list) else len(data.get("data", []))
            if n:
                hits += 1
                sample = data[0] if isinstance(data, list) else data["data"][0]
                fields |= set(sample.keys())
            print(f"  {sym:12s} -> {n} announcements (HTTP {r.status_code})")
        except Exception as e:
            print(f"  {sym:12s} -> error: {str(e)[:60]}")
        time.sleep(1.0)
    print(f"\nCOVERAGE: {hits}/{len(SYMS)} symbols returned announcements")
    print(f"FIELDS available: {sorted(fields)}")
    print("\nVERDICT INPUT: if coverage is high + fields include date/subject/attachment, the free NSE "
          "announcements API is viable -> a build candidate (scraper -> data/live staging, ISIN-matched). "
          "If blocked/empty, fall back to BSE announcements API or RSS.")

if __name__ == "__main__":
    main()
