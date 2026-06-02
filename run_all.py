#!/usr/bin/env python3
"""
run_all.py — single orchestrator for the IPO-analysis data pipeline.

Runs every pipeline step in the CANONICAL order documented in CLAUDE.md:

    00  build long-term identity spine (2006-2019 cohort)
    longterm/02  attach Chittorgarh detail to long-term masters
    longterm/03  long-term subscription enrichment
    longterm/04  long-term financials enrichment
    01  build base (boom cohort 2020-2025)
    02  attach Chittorgarh detail
    03  enrich (GMP / sector / mcap / promoter ... + writes review/gaps.csv)
    03b fill financials from screener
    03c fill subscription from NSE
    03d fill subscription + GMP from ipowatch
    03e fill GMP from investorgain
    04  verify tickers (ISIN<->symbol)
    05  reconcile vs old dataset
    06  validate tickers (resolve on Yahoo)
    07  returns_summary (uses pipeline/listing_remediation.py internally)
    scrapers/screener_prices_merge  merge screener weekly prices + listing remediation
    08  build universe (unified feature table)
    09  assemble (-> data/master/ipo_analysis.csv)

Each step is invoked as:  PYTHONPATH=. python <path>

Notes
-----
* Long pulls (prices, screener, ticker validation) are resume-safe and rate-limited;
  this orchestrator just chains the steps. It does NOT re-scrape if a step is a no-op.
* Stops on the FIRST non-zero exit.
* Resume from any step with `--from <step>` (e.g. `--from 07` or `--from lt/03`
  or `--from merge`). Use `--list` to see the step keys.

This file is conservative: it ONLY shells out to existing scripts in their
canonical order. It does not delete or move anything.

Usage:
    PYTHONPATH=. python run_all.py
    PYTHONPATH=. python run_all.py --from 07
    PYTHONPATH=. python run_all.py --list
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# (key, path) in canonical run order. `key` is what you pass to --from.
# SINGLE SOURCE: derived from project_map.PIPELINE so the DAG can never drift
# between the orchestrator and the map. To change the pipeline, edit project_map.py.
sys.path.insert(0, ROOT)
from project_map import dag_steps
STEPS = dag_steps()


def main():
    keys = [k for k, _ in STEPS]
    ap = argparse.ArgumentParser(description="Run the IPO-analysis pipeline in canonical order.")
    ap.add_argument("--from", dest="start", metavar="STEP",
                    help=f"resume from this step key (one of: {', '.join(keys)})")
    ap.add_argument("--list", action="store_true", help="list step keys + paths and exit")
    args = ap.parse_args()

    if args.list:
        for k, p in STEPS:
            print(f"{k:6s} {p}")
        return 0

    start_idx = 0
    if args.start:
        if args.start not in keys:
            print(f"ERROR: unknown --from step {args.start!r}. Valid keys: {', '.join(keys)}",
                  file=sys.stderr)
            return 2
        start_idx = keys.index(args.start)

    todo = STEPS[start_idx:]
    env = dict(os.environ)
    env["PYTHONPATH"] = "." + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    print(f"Running {len(todo)} step(s) starting at {todo[0][0]!r}\n")
    for i, (key, path) in enumerate(todo, 1):
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            print(f"ERROR: step {key} -> {path} not found", file=sys.stderr)
            return 1
        print(f"==== [{i}/{len(todo)}] step {key}: PYTHONPATH=. python {path} ====", flush=True)
        rc = subprocess.run([sys.executable, full], cwd=ROOT, env=env).returncode
        if rc != 0:
            print(f"\nSTOP: step {key} ({path}) exited with code {rc}", file=sys.stderr)
            return rc
        print(f"---- step {key} OK ----\n", flush=True)

    print("All steps completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
