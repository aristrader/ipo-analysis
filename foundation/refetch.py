#!/usr/bin/env python3
"""foundation/refetch.py — orchestrate the FULL re-fetch into OUTPUT_ROOT, with live progress.

Runs each scraper in order as a subprocess. Scrapers read their work-list from the FROZEN baseline
(config.src -> INPUT_ROOT, i.e. the old data/) and write fresh data + raw payloads into OUTPUT_ROOT
(data_build/). Continues on failure (one bad source never kills the run). Writes a live status file
after every step, so the run's progress is inspectable AT ANY MOMENT:

    cat  <OUTPUT_ROOT>/logs/REFETCH_STATUS.txt     # high-level: done / running / pending + timings
    tail -f <OUTPUT_ROOT>/logs/<step>.log          # full detail for one step

Usage (always with the venv + PYTHONPATH=.):
    PYTHONPATH=. .venv/bin/python foundation/refetch.py            # full run
    PYTHONPATH=. .venv/bin/python foundation/refetch.py --list     # show the plan
    PYTHONPATH=. .venv/bin/python foundation/refetch.py --only indices   # one step (smoke test)
    PYTHONPATH=. .venv/bin/python foundation/refetch.py --from screener  # resume from a step onward
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation import config

TODAY = date.today().isoformat()

# (name, argv-after-python, human note).  Ordered: fast/high-value first, the price long-pole last.
STEPS = [
    ("corp_actions",       ["scrapers/corp_actions.py"],
        "NSE corp actions (splits/bonus) 2006-2025 — the D-1 source"),
    ("delisting",          ["scrapers/delisting.py"],
        "delisting status (NSE + BSE)"),
    ("indices",            ["scrapers/indices.py"],
        "Nifty 50 / Smallcap 250 (benchmark for alpha)"),
    ("chittorgarh_list",   ["scrapers/chittorgarh.py", "--phase", "list", "--years", "2020-2025"],
        "IPO list + identity (ISIN/symbols/dates)"),
    ("chittorgarh_detail", ["scrapers/chittorgarh.py", "--phase", "detail"],
        "IPO detail pages (OFS, financials, listing OHLC)"),
    ("sharescart",         ["scrapers/sharescart.py", "--phase", "all"],
        "SME IPO enrichment"),
    ("nse_subscription",   ["scrapers/nse_subscription.py"],
        "subscription multiples (mainboard)"),
    ("ipowatch",           ["scrapers/ipowatch.py"],
        "SME subscription + GMP"),
    ("investorgain",       ["scrapers/investorgain.py"],
        "GMP (primary)"),
    ("gmp_patcher",        ["scrapers/gmp_patcher.py"],
        "GMP patch (investorgain + ipowatch)"),
    ("screener",           ["scrapers/screener.py"],
        "pre-IPO financials + sector / market-cap"),
    ("screener_prices",    ["scrapers/screener_prices.py"],
        "weekly price gap-fill (listing-era)"),
    ("bhavcopy_ohlc",      ["scrapers/bhavcopy_ohlc.py", "--start", "2006-01-01", "--end", TODAY, "--sleep", "0.1"],
        "daily OHLCV bhavcopy 2006..today  <-- LONG POLE (archives tolerant; sleep 0.1)"),
]
# NOTE: corporate_actions_yfinance is intentionally NOT run here — it needs an explicit symbol list and
# Yahoo throttles bursts; yfinance is corroboration-only (the NSE corp_actions step above is primary).
# Run it attended later if needed.


def _now():
    return datetime.now().isoformat(timespec="seconds")


def write_status(state, header_note=""):
    config.ensure(config.logs_dir())
    done = sum(1 for s in state if s["status"] == "done")
    failed = sum(1 for s in state if s["status"].startswith("FAILED"))
    lines = [
        "RE-FETCH STATUS",
        f"updated:     {_now()}",
        f"output_root: {config.OUTPUT_ROOT}",
        f"progress:    {done} done / {failed} failed / {len(state)} total   {header_note}",
        "",
    ]
    for s in state:
        timing = ""
        if s.get("seconds") is not None:
            timing = f"  ({s['seconds']}s)"
        elif s["status"] == "running":
            timing = f"  (started {s.get('started','')})"
        lines.append(f"  [{s['status']:14}] {s['name']:20} {s['note']}{timing}")
    (config.logs_dir() / "REFETCH_STATUS.txt").write_text("\n".join(lines) + "\n")
    (config.logs_dir() / "REFETCH_STATUS.json").write_text(json.dumps(state, indent=2))


def run(steps):
    config.ensure(config.logs_dir())
    state = [{"name": n, "status": "pending", "note": note, "argv": a,
              "started": None, "finished": None, "seconds": None} for (n, a, note) in steps]
    write_status(state, "(starting)")
    overall_t0 = time.time()
    for i, (name, argv, note) in enumerate(steps):
        state[i]["status"] = "running"
        state[i]["started"] = _now()
        write_status(state)
        logf = config.logs_dir() / f"{name}.log"
        env = dict(os.environ)
        env["PYTHONPATH"] = "."
        t0 = time.time()
        try:
            with open(logf, "w") as lf:
                lf.write(f"# {name}: {' '.join(argv)}\n# started {_now()}\n\n")
                lf.flush()
                rc = subprocess.run([sys.executable] + argv, cwd=str(config.REPO_ROOT),
                                    env=env, stdout=lf, stderr=subprocess.STDOUT).returncode
            state[i]["status"] = "done" if rc == 0 else f"FAILED(rc={rc})"
        except Exception as e:  # binary missing / unexpected — log and keep going
            with open(logf, "a") as lf:
                lf.write(f"\n# ORCHESTRATOR ERROR: {type(e).__name__}: {e}\n")
            state[i]["status"] = "FAILED(orch)"
        state[i]["seconds"] = round(time.time() - t0)
        state[i]["finished"] = _now()
        write_status(state)
    write_status(state, f"(complete in {round(time.time() - overall_t0)}s)")
    return state


def main():
    ap = argparse.ArgumentParser(description="Full re-fetch orchestrator")
    ap.add_argument("--list", action="store_true", help="show the step plan and exit")
    ap.add_argument("--only", metavar="STEP", help="run a single step (smoke test)")
    ap.add_argument("--from", dest="from_", metavar="STEP", help="run from this step onward")
    args = ap.parse_args()

    names = [s[0] for s in STEPS]
    if args.list:
        print(f"output_root = {config.OUTPUT_ROOT}\n")
        for n, a, note in STEPS:
            print(f"  {n:20} {note}")
        return
    if args.only:
        if args.only not in names:
            sys.exit(f"unknown step {args.only!r}; valid: {', '.join(names)}")
        steps = [s for s in STEPS if s[0] == args.only]
    elif args.from_:
        if args.from_ not in names:
            sys.exit(f"unknown step {args.from_!r}; valid: {', '.join(names)}")
        steps = STEPS[names.index(args.from_):]
    else:
        steps = STEPS

    print(f"Re-fetch: {len(steps)} step(s) -> {config.OUTPUT_ROOT}")
    print(f"Live status: {config.logs_dir() / 'REFETCH_STATUS.txt'}")
    run(steps)
    print("Done. Final status in REFETCH_STATUS.txt")


if __name__ == "__main__":
    main()
