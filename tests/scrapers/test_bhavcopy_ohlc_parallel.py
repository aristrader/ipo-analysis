"""Unit test for the PARALLEL bhavcopy run() — fetch in parallel, writes single-threaded + date-sorted.

No network: load_universe / fetch_nse / fetch_bse / parse_day / _setup_logging are all mocked, so this
locks in the parallel ORDERING correctness (per-ISIN files stay date-sorted, no dupes) that the review +
the live integration test verified by hand. Crosses the CHUNK boundary (>250 weekdays) to prove ordering
holds across chunks too. Output is isolated to a temp dir by the autouse fixture in conftest.py.
"""
import csv
from datetime import datetime

from foundation import config

ISIN = "INE000TEST01"


def test_run_parallel_keeps_per_isin_files_date_sorted(bhavcopy_ohlc_mod, monkeypatch):
    b = bhavcopy_ohlc_mod
    monkeypatch.setattr(b, "_setup_logging", lambda: None)               # no log-file side effects
    monkeypatch.setattr(b, "load_universe", lambda: ({ISIN}, {}))         # tiny fake universe
    monkeypatch.setattr(b, "fetch_nse", lambda d: ("payload", True))      # NSE: a payload every weekday
    monkeypatch.setattr(b, "fetch_bse", lambda d: (None, True))           # BSE: nothing to add
    # parse_day yields exactly one row for our ISIN whenever there's a payload (ignores real CSV format)
    monkeypatch.setattr(b, "parse_day",
                        lambda text, isin_set, sym2isin: {ISIN: (1.0, 2.0, 0.5, 1.5, 100)} if text else {})

    # >250 weekdays -> spans multiple CHUNKs, so this also proves cross-chunk ordering.
    b.run(datetime(2024, 1, 1), datetime(2025, 6, 30), exchanges=("NSE", "BSE"), sleep=0, workers=6)

    matches = list(config.OUTPUT_ROOT.rglob(ISIN + ".csv"))
    assert matches, "per-ISIN price file should have been written"
    dates = [r["date"] for r in csv.DictReader(open(matches[0]))]

    assert len(dates) >= 350, f"expected ~390 weekdays, got {len(dates)}"
    assert dates == sorted(dates), "parallel fetch must not scramble per-ISIN date order"
    assert len(dates) == len(set(dates)), "no duplicate (isin, date) rows"
