"""Calls ledger orchestrator — cursor walk / backfill / grading over layer3/calls.py.

Usage (PYTHONPATH=. .venv/bin/python run_calls.py ...):
  (no args)                      cursor walk: max(call_date)+1 .. today, mode=gap_filled
  --backfill FROM TO             generate for a window (with --mode backfilled|historical_sim)
  --mode MODE                    override mode label
  --pit forward_test|pointintime|cache   PIT-score source (default cache = union of both files)
  --grade-only                   grade matured calls, write back
  --report                       print the track-record summary and exit

PIT sources: docs/research/forward_test_2026_per_ipo.csv (2026 cohort, genuinely OOS) and
data/master/review/pit_scores_cache.csv (score_all_pointintime over matured rows; cached).
The ledger is data/master/calls_ledger.csv (atomic tmp+rename writes)."""
import argparse
import os
import sys

import pandas as pd

from layer3 import calls, spine
from layer3.predictor import weights as W

LEDGER = "data/master/calls_ledger.csv"
PIT_CACHE = "data/master/review/pit_scores_cache.csv"
FWD_CSV = "docs/research/forward_test_2026_per_ipo.csv"


def n14_flags_series(df):
    """The validated prospectus flags per row (same defs as scorecard N14)."""
    sales = pd.to_numeric(df.get("pre_ipo_net_sales"), errors="coerce")
    pat = pd.to_numeric(df.get("pre_ipo_pat"), errors="coerce")
    lm = df.get("lead_manager").astype(str).str.strip()
    freq = lm.map(lm.value_counts())
    return ((sales < 25).fillna(False).astype(int) + (pat <= 0).fillna(False).astype(int) +
            (freq < 12).fillna(False).astype(int))


def pit_pointintime(df):
    """score_all_pointintime component-mean per matured IPO (cached — ~minutes to build)."""
    if os.path.exists(PIT_CACHE):
        return pd.read_csv(PIT_CACHE)
    scored = W.score_all_pointintime(df, "1y")
    scored["score"] = scored[W.COMPONENTS].mean(axis=1, skipna=True)
    out = scored[["isin", "score"]].merge(
        df[["isin"]].assign(n14_flags=n14_flags_series(df)), on="isin", how="left")
    out.to_csv(PIT_CACHE, index=False)
    return out


def pit_forward_test(df):
    f = pd.read_csv(FWD_CSV)
    return pd.DataFrame({"isin": f["isin"], "score": pd.to_numeric(f["score"], errors="coerce"),
                         "n14_flags": pd.to_numeric(f["red_flags"], errors="coerce")})


def pit_frame(which, df):
    if which == "forward_test":
        p = pit_forward_test(df)
    elif which == "pointintime":
        p = pit_pointintime(df)
    else:                                   # cache = union, forward_test wins on overlap
        parts = []
        if os.path.exists(FWD_CSV):
            parts.append(pit_forward_test(df))
        if os.path.exists(PIT_CACHE):
            parts.append(pd.read_csv(PIT_CACHE))
        if not parts:
            sys.exit("no PIT score source on disk — run with --pit pointintime first")
        p = pd.concat(parts, ignore_index=True).drop_duplicates("isin", keep="first")
    return calls.add_quintiles(p, df)


def load_ledger():
    return pd.read_csv(LEDGER) if os.path.exists(LEDGER) else None


def save_ledger(led):
    led = led.sort_values(["call_date", "isin"]).reset_index(drop=True)
    tmp = LEDGER + ".tmp"
    led.to_csv(tmp, index=False)
    os.replace(tmp, LEDGER)
    print(f"ledger: {len(led)} calls -> {LEDGER}")


def report(led):
    print(f"\n=== TRACK RECORD (as of ledger state; n={len(led)}) ===")
    g = led.groupby(["mode", "call_type"]).agg(
        n=("call_id", "count"),
        a1m=("alpha_1m", "median"), a3m=("alpha_3m", "median"), a1y=("alpha_1y", "median"),
        pop=("pop_pct", "median")).reset_index()
    for _, r in g.iterrows():
        def f(v, s=100):
            return f"{s*v:+.1f}%" if pd.notna(v) else "  --  "
        print(f"  {r['mode']:>14} {r['call_type']:<17} n={int(r['n']):>5}  pop {f(r['pop'],1):>7}  "
              f"a1m {f(r['a1m']):>7}  a3m {f(r['a3m']):>7}  a1y {f(r['a1y']):>7}")
    # the headline: APPLY vs AVOID spread per mode
    for mode, gm in led.groupby("mode"):
        ap = pd.to_numeric(gm.loc[gm["call_type"] == "APPLY", "alpha_1y"], errors="coerce").dropna()
        av = pd.to_numeric(gm.loc[gm["call_type"] == "AVOID", "alpha_1y"], errors="coerce").dropna()
        if len(ap) >= 12 and len(av) >= 12:
            print(f"  >> {mode}: APPLY a1y {100*ap.median():+.1f}% (n={len(ap)}) vs "
                  f"AVOID {100*av.median():+.1f}% (n={len(av)}) — spread {100*(ap.median()-av.median()):+.1f}pp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--mode", default=None)
    ap.add_argument("--pit", default="cache",
                    choices=["forward_test", "pointintime", "cache"])
    ap.add_argument("--cohort", default=None, help="restrict to a cohort (e.g. boom)")
    ap.add_argument("--grade-only", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    df = spine.load_substrate()
    led = load_ledger()

    if a.report:
        if led is None:
            sys.exit("no ledger yet")
        report(led)
        return
    if a.grade_only:
        if led is None:
            sys.exit("no ledger yet")
        led = calls.grade_calls(led, df)
        save_ledger(led)
        report(led)
        return

    frame = df[df["cohort"] == a.cohort].copy() if a.cohort else df
    pit = pit_frame(a.pit, df)
    if a.backfill:
        d0, d1 = a.backfill
        mode = a.mode or "backfilled"
    else:
        if led is None or not len(led):
            sys.exit("empty ledger: run --backfill first to seed it")
        d0 = (pd.Timestamp(led["call_date"].max()) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        d1 = pd.Timestamp.now().strftime("%Y-%m-%d")
        mode = a.mode or "gap_filled"
    print(f"walk {d0} .. {d1} mode={mode} pit={a.pit} pool={len(frame)}")
    led = calls.walk(frame, pit, d0, d1, mode=mode, ledger=led)
    led = calls.grade_calls(led, df)
    save_ledger(led)
    report(led)


if __name__ == "__main__":
    main()
