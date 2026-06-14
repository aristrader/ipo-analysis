"""Bring the dataset to today — new IPOs in + everyone's prices/outcomes extended.

    PYTHONPATH=. python run_refresh.py              # DRY-RUN: report what would change
    PYTHONPATH=. python run_refresh.py --apply      # do it (long: network pulls)
      --skip-tests        skip the preflight fast-suite run (discouraged)
      --with-delisting    also re-pull the delisting register (slow; default skip)

APPLY PHASES (each idempotent — raw-cache appends skip what's already present, so
re-running after a failure continues rather than duplicates):
  0 preflight   git clean + fast suite green (unless --skip-tests)
  1 snapshot    data/master -> archive/pre_refresh_<date>/ ; meta.archive_pointer
  2 ingest      new IPOs -> raw caches (chittorgarh detail, subscription, GMP, screener)
  3 chain A     pipeline 01..05 (masters now include the new ISINs)
  4 prices      bhavcopy days: min(earliest new listing, old as_of+1) .. today
  5 aux         indices refresh + corp_actions (current year, merged) [+ delisting opt-in]
  6 clock       meta.as_of = today
  7 chain B     07 -> merge -> 08 -> 09 ; then 03f (sector for new) -> 08 -> 09 again
  8 rails       meta.rows ; goldens re-derive (OLD -> NEW printed) ; fast suite MUST pass
  9 outputs     run_weights ; report rebuild ; summary

Rollback: cp archive/pre_refresh_<date>/* data/master/   (snapshot includes substrate_meta.json)
"""
import argparse
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from layer3 import spine  # noqa: E402

META = os.path.join(ROOT, "data/master/substrate_meta.json")


# ----------------------------------------------------------------- existing API (app button)
def latest_year():
    df = spine.load_substrate(equity_only=False)
    yrs = pd.to_datetime(df["listing_date"], errors="coerce").dt.year.dropna()
    return int(yrs.max()) if len(yrs) else 2025


def find_new(years=None):
    """Fetch recent Chittorgarh listings and return those whose ISIN isn't already in our raw list.
    (Kept for the app's 'Check for new listings' button.)"""
    sys.path.insert(0, os.path.join(ROOT, "tools/refresh"))
    import ingest
    years = years or list(range(latest_year(), date.today().year + 1))
    rows, _ = ingest.find_new_listings(years)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------- helpers
def meta():
    return json.load(open(META))


def write_meta(**updates):
    m = meta()
    m.update(updates)
    json.dump(m, open(META, "w"), indent=1)
    return m


def sh(args, timeout=900):
    return subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True,
                          timeout=timeout, env={**os.environ, "PYTHONPATH": ROOT})


def run_step(path, label=None, timeout=900):
    p = sh([path], timeout=timeout)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'FAIL'} {label or path}")
    if not ok:
        print(p.stderr[-1500:])
        raise SystemExit(f"step failed: {path}")
    return p.stdout


def last_price_date():
    """Newest price date on disk (sample of price files; cheap heuristic for the dry-run)."""
    newest = ""
    for f in sorted(glob.glob(os.path.join(ROOT, "data/prices/*.csv")))[:80]:
        try:
            last = open(f).readlines()[-1].split(",")[0]
            newest = max(newest, last)
        except (OSError, IndexError):
            continue
    return newest or str(meta()["as_of"])


# ----------------------------------------------------------------- dry run
def dry_run():
    m = meta()
    today = date.today()
    print(f"DRY-RUN — dataset as_of {m['as_of']}, {m['rows']} rows")
    lpd = last_price_date()
    try:
        gap = (today - datetime.strptime(lpd[:10], "%Y-%m-%d").date()).days
    except ValueError:
        gap = "?"
    print(f"  prices: newest day on disk ≈ {lpd[:10]} -> ~{gap} calendar days to pull (x2 exchanges)")
    print("  detecting new IPOs on Chittorgarh (network)…")
    try:
        nw = find_new()
    except Exception as e:
        print(f"  could not reach Chittorgarh ({type(e).__name__}: {e})")
        return
    print(f"  new IPOs not in dataset: {len(nw)}")
    if len(nw):
        cols = [c for c in ("isin", "company_name", "type", "listing_date", "year") if c in nw.columns]
        print(nw[cols].head(15).to_string(index=False))
        if len(nw) > 15:
            print(f"  … +{len(nw) - 15} more")
    print("\nRun with --apply to execute (snapshot first; rollback one-liner in docs/WORKFLOWS.md).")


# ----------------------------------------------------------------- apply
def apply(skip_tests=False, with_delisting=False):
    sys.path.insert(0, os.path.join(ROOT, "tools/refresh"))
    sys.path.insert(0, os.path.join(ROOT, "scrapers"))
    import ingest
    today = date.today()
    summary = {}

    print("[0/9] preflight")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        raise SystemExit("REFUSING: git not clean — commit or stash first.\n" + dirty)
    if not skip_tests:
        p = sh(["-m", "pytest", "tests", "-q", "-x"], timeout=900)
        if p.returncode != 0:
            raise SystemExit("REFUSING: fast suite not green before refresh:\n" + p.stdout[-1200:])
        print("  fast suite green")

    print("[1/9] snapshot")
    snap = os.path.join(ROOT, f"archive/pre_refresh_{today:%Y%m%d}")
    if not os.path.exists(snap):
        shutil.copytree(os.path.join(ROOT, "data/master"), snap)
    write_meta(archive_pointer=os.path.relpath(snap, ROOT))
    print(f"  data/master -> {os.path.relpath(snap, ROOT)}")

    print("[2/9] ingest new IPOs")
    old_asof = datetime.strptime(meta()["as_of"], "%Y-%m-%d").date()
    years = sorted({old_asof.year, today.year})
    new_rows, scraper = ingest.find_new_listings(years)
    print(f"  detected: {len(new_rows)} new IPOs (years {years})")
    summary["new_ipos"] = len(new_rows)
    if new_rows:
        summary.update(ingest.ingest_listings(new_rows, scraper))
        summary.update(ingest.ingest_subscription_nse(new_rows))
        summary.update(ingest.ingest_subscription_gmp_ipowatch(new_rows))
        summary.update(ingest.ingest_gmp_investorgain(years))
        summary.update(ingest.ingest_screener(new_rows))

    print("[3/9] pipeline chain A (01..05)")
    for step in ["pipeline/01_build_base.py", "pipeline/02_attach_detail.py", "pipeline/03_enrich.py",
                 "pipeline/03b_fill_financials_screener.py", "pipeline/03c_fill_subscription_nse.py",
                 "pipeline/03d_fill_ipowatch.py", "pipeline/03e_fill_gmp_investorgain.py",
                 "pipeline/04_verify.py", "pipeline/05_reconcile.py"]:
        run_step(step)

    print("[4/9] prices (bhavcopy, incremental)")
    import bhavcopy_ohlc as bo
    # 4a. BACKFILL for the new ISINs over manifest-covered days (their listing .. old as_of):
    # targeted parse against the new ISINs only — never clears the manifest (which would
    # duplicate the existing universe's rows; see ingest.backfill_prices_new_isins docstring).
    listed_new = [(r.get("listing_date") or "")[:10] for r in new_rows
                  if (r.get("listing_date") or "")[:10] and (r.get("listing_date") or "")[:10] <= str(today)]
    if listed_new:
        bf_start = datetime.strptime(min(listed_new), "%Y-%m-%d").date()
        summary.update(ingest.backfill_prices_new_isins(new_rows, bf_start, old_asof))
        print(f"  backfill (new isins) {bf_start}..{old_asof}: "
              f"{summary.get('backfill_rows', 0)} rows over {summary.get('backfill_days', 0)} days")
    # 4b. the recent gap for EVERYONE (manifest-naive days only)
    bo.run(datetime.combine(old_asof + timedelta(days=1), datetime.min.time()),
           datetime.combine(today, datetime.min.time()))
    summary["price_window"] = f"{old_asof + timedelta(days=1)}..{today}"

    print("[5/9] aux reference data")
    _refresh_indices_guarded()
    _refresh_corp_actions_current_year(today.year)
    if with_delisting:
        run_step("scrapers/delisting.py", "delisting register", timeout=1800)
    else:
        print("  delisting: skipped (use --with-delisting; the register changes slowly)")

    print(f"[6/9] clock: as_of {meta()['as_of']} -> {today}")
    write_meta(as_of=str(today), last_refresh=str(today))

    print("[7/9] pipeline chain B (07 -> merge -> 08 -> 09; then 03f -> 08 -> 09)")
    for step in ["pipeline/07_returns_summary.py", "scrapers/screener_prices_merge.py",
                 "pipeline/08_build_universe.py", "pipeline/09_assemble.py"]:
        run_step(step)
    run_step("pipeline/03f_sector_mcap.py", "03f sector/mcap (new rows)", timeout=1800)
    for step in ["pipeline/08_build_universe.py", "pipeline/09_assemble.py"]:
        run_step(step, step + " (fold 03f)")

    print("[8/9] rails re-derive")
    n_rows = sum(1 for _ in csv.reader(open(os.path.join(ROOT, "data/master/ipo_analysis.csv")))) - 1
    write_meta(rows=n_rows)
    print(f"  meta.rows = {n_rows}")
    print(run_step("tools/refresh/derive_goldens.py", "goldens OLD -> NEW"))
    p = sh(["-m", "pytest", "tests", "-q"], timeout=1200)
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    print(f"  {tail}")
    if p.returncode != 0:
        raise SystemExit("SUITE NOT GREEN after refresh — investigate or rollback (WORKFLOWS.md).\n"
                         + p.stdout[-2000:])

    print("[9/9] outputs")
    run_step("run_weights.py", timeout=1800)
    run_step("run_layer3_report.py", timeout=1800)

    print("[10] calls ledger (gap-fill + grade; reads the fresh substrate)")
    p = sh(["run_calls.py"], timeout=3600)            # cursor walk, mode=gap_filled
    print(p.stdout[-600:] if p.returncode == 0 else f"  CALLS PHASE FAILED (non-blocking):\n{p.stdout[-600:]}")
    try:
        from scrapers import live_board
        live_board.fetch_board()
    except Exception as ex:
        print(f"  live board fetch failed (non-blocking): {ex}")

    print("[11] schema gate (typed column/range/null contracts on the fresh products)")
    try:
        sys.path.insert(0, os.path.join(ROOT, "tools/checks"))
        import schema_gate
        viol = schema_gate.check_all()
        if viol:
            # RAISE (review C2): a drifted refresh must fail LOUD, not print-and-continue.
            # (Honest limitation: the swap already happened in steps 7-9; this catches it
            # immediately + non-zero exit so the bad state is never silently trusted. A future
            # refactor should gate a staging copy BEFORE the mv.)
            msg = "SCHEMA GATE FAILED after refresh — substrate/ledger drifted:\n" + \
                  "\n".join(f"   - {x}" for x in viol)
            raise SystemExit(msg)
        print("  clean — all pinned contracts hold.")
    except SystemExit:
        raise
    except Exception as ex:
        print(f"  schema gate skipped ({ex})")

    print("\nREFRESH COMPLETE")
    m = meta()
    print(f"  rows: {m['rows']}  as_of: {m['as_of']}  snapshot: {m['archive_pointer']}")
    for k, v in summary.items():
        print(f"  {k}: {len(v) if isinstance(v, list) else v}")
    fail_keys = [k for k, v in summary.items() if k.endswith("_failures") and v]
    if fail_keys:
        print("  NOTE: best-effort fetches with failures (gaps stay null):", fail_keys)
    print("  NOTE: new ISINs' tickers are unvalidated (06 = network step) — see review files.")


def _refresh_indices_guarded():
    """Refresh the benchmark indices WITH a shrink-guard.

    2026-06-06 incident: the yahoo/investing endpoints changed; scrapers/indices.py
    swallowed the failures (exit 0) and rewrote nifty50.csv truncated + smallcap250
    header-only — silently destroying alpha for early vintages. The test gate caught
    it. Guard: if either file SHRINKS, restore both from git and continue with the
    (slightly stale) benchmarks — staleness is honest, truncation is corruption.
    """
    files = ["data/reference/indices/nifty50.csv", "data/reference/indices/niftysmallcap250.csv"]
    before = {f: sum(1 for _ in open(os.path.join(ROOT, f))) for f in files}
    p = sh(["scrapers/indices.py"], timeout=300)
    after = {f: sum(1 for _ in open(os.path.join(ROOT, f))) for f in files}
    shrunk = [f for f in files if after[f] < before[f]]
    if p.returncode != 0 or shrunk:
        for f in files:
            blob = subprocess.run(["git", "show", f"HEAD:{f}"], cwd=ROOT,
                                  capture_output=True, text=True)
            if blob.returncode == 0:
                open(os.path.join(ROOT, f), "w").write(blob.stdout)
        print(f"  indices: PULL UNUSABLE (shrunk: {shrunk or 'rc!=0'}) -> restored from git; "
              "benchmarks are a few days stale (honest), NOT truncated (corrupt)")
    else:
        print(f"  indices: OK (nifty50 {before[files[0]]}->{after[files[0]]} rows, "
              f"smallcap {before[files[1]]}->{after[files[1]]})")


def _refresh_corp_actions_current_year(year):
    """Pull the current year's splits/bonuses and merge-dedupe into corp_actions.csv."""
    import corp_actions as ca
    path = os.path.join(ROOT, "data/reference/corp_actions.csv")
    existing = list(csv.DictReader(open(path)))
    seen = {(r["isin"] or r["symbol"], r["symbol"], r["action_type"], r["ex_date"], r["ratio_factor"])
            for r in existing}
    added = []
    try:
        s = ca.prime_session()
        for index in ("equities", "sme"):
            for row in ca.fetch_year(s, index, year):
                rec = ca.parse_row(row)
                if not rec:
                    continue
                key = (rec["isin"] or rec["symbol"], rec["symbol"], rec["action_type"],
                       rec["ex_date"], str(rec["ratio_factor"]))
                if key not in seen:
                    rec["source"] = f"nse_corp_actions:{index}"
                    added.append(rec)
                    seen.add(key)
    except Exception as e:
        print(f"  corp_actions {year}: fetch failed ({str(e)[:80]}) — continuing without")
    if added:
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["isin", "symbol", "action_type", "raw_subject",
                                              "ratio_factor", "ex_date", "source"], extrasaction="ignore")
            w.writerows(added)
    print(f"  corp_actions {year}: +{len(added)} new events")


def main():
    ap = argparse.ArgumentParser(description="Bring the dataset to today (dry-run by default)")
    ap.add_argument("--apply", action="store_true", help="execute the refresh (default: dry-run)")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--with-delisting", action="store_true")
    a = ap.parse_args()
    if a.apply:
        apply(skip_tests=a.skip_tests, with_delisting=a.with_delisting)
    else:
        dry_run()


if __name__ == "__main__":
    main()
