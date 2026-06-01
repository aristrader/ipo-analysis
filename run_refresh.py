"""Live-refresh: pull newly-listed IPOs from Chittorgarh and find the ones not yet in our dataset.

DRY-RUN by default (just previews what's new — touches nothing). `--commit` stages the new rows to
data/raw/chittorgarh/new_listings.csv for folding through the pipeline. New IPOs naturally enter as
TEST/LIVE (no matured outcome yet) and roll into training as they age (per the train/test cutoff).

    PYTHONPATH=. python run_refresh.py            # preview new IPOs
    PYTHONPATH=. python run_refresh.py --commit   # + stage them for the pipeline
"""
import sys
import pandas as pd
from layer3 import spine, config


def latest_year():
    df = spine.load_substrate(equity_only=False)
    yrs = pd.to_datetime(df["listing_date"], errors="coerce").dt.year.dropna()
    return int(yrs.max()) if len(yrs) else 2025


def find_new(years=None):
    """Fetch recent Chittorgarh listings and return those whose ISIN isn't already in our dataset."""
    import cloudscraper  # noqa
    sys.path.insert(0, str(config.ROOT / "scrapers"))
    import chittorgarh as ch
    have = set(spine.load_substrate(equity_only=False)["isin"].dropna().astype(str))
    years = years or list(range(latest_year(), 2028))
    scraper = ch.cloudscraper.create_scraper()
    rows = []
    for y in years:
        for r in ch.pull_year(scraper, y):
            isin = (r.get("isin") or "").strip()
            if isin and isin not in have:
                rows.append({"isin": isin, "year": y,
                             "company": r.get("company_name") or r.get("name") or r.get("Company"),
                             "listing_date": r.get("listing_date"), "type": r.get("type")})
    return pd.DataFrame(rows)


def main():
    commit = "--commit" in sys.argv
    print(f"Latest IPO in our data: {latest_year()}. Fetching recent Chittorgarh listings…")
    try:
        nw = find_new()
    except Exception as e:
        print(f"Could not reach Chittorgarh ({type(e).__name__}: {e}). Run with network access.")
        return
    print(f"\nNEW IPOs not yet in the dataset: {len(nw)}")
    if len(nw):
        print(nw.to_string(index=False))
    if not commit:
        print("\n(DRY-RUN — nothing changed. Re-run with --commit to stage these for the pipeline.)")
        return
    out = config.ROOT / "data/raw/chittorgarh/new_listings.csv"
    nw.to_csv(out, index=False)
    print(f"\nStaged {len(nw)} → {out}. Next: enrich (03*) + price (bhavcopy) + run 08→09 to fold them in.")


if __name__ == "__main__":
    main()
