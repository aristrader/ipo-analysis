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


def live_calls(df, led):
    """Score OPEN issues from data/live/board.json (they are NOT in the substrate yet) and
    append mode=live calls: EARLY_* while the window is open, the final verdict on close day.
    Thresholds = the same segment quintile cuts the backfill used (pit cache scores)."""
    import json
    from datetime import date
    from layer3 import calls
    from layer3.predictor import predict as P
    board_path = "data/live/board.json"
    if not os.path.exists(board_path):
        print("no board.json — run scrapers/live_board.py first")
        return led
    board = json.load(open(board_path))
    pit = pd.read_csv(PIT_CACHE) if os.path.exists(PIT_CACHE) else None
    cuts = {}
    if pit is not None:
        p = pit.merge(df[["isin", "type"]], on="isin", how="left")
        for seg, g in p.groupby("type"):
            s = pd.to_numeric(g["score"], errors="coerce").dropna()
            if len(s) >= 30:
                cuts[seg] = (s.quantile(0.2), s.quantile(0.8))
    today = date.today().isoformat()
    have = set(led["call_id"]) if led is not None and len(led) else set()
    rows = []
    for e in board.get("open", []):
        key = e.get("isin") or e.get("slug") or e["name"]
        is_close_day = today >= e["close_date"]
        prefix = "" if is_close_day else "EARLY_"
        anchor = e["close_date"] if is_close_day else e["open_date"]
        q = {"type": e["type"], "issue_size_cr": e.get("issue_size_cr"),
             "issue_price": e.get("price_band_high"), "lead_manager": e.get("lead_manager"),
             "gmp_pct": e.get("gmp_pct"), "sub_total_x": e.get("sub_total_x"),
             "sub_qib_x": e.get("sub_qib_x"), "sub_retail_x": e.get("sub_retail_x")}
        try:
            res = P.predict({k: v for k, v in q.items() if v is not None}, df=df,
                            profile="data_informed")
            sc = res["scorecard"].get("combined_score")
            wf = res.get("wipeout_flags", {})
            nf = wf.get("n_flags") if isinstance(wf, dict) else None
        except Exception as ex:
            print(f"  live scoring failed for {e['name']}: {ex}")
            continue
        lo, hi = cuts.get(e["type"], (None, None))
        if sc is None or lo is None:
            ct = prefix + "NEUTRAL"
        elif sc >= hi and (nf or 0) == 0:
            ct = prefix + "APPLY"
        elif sc <= lo or (nf or 0) >= 2:
            ct = prefix + "AVOID"
        else:
            ct = prefix + "NEUTRAL"
        cid = f"{key}|{ct}|{anchor}"
        if cid in have:
            continue
        ctx = calls.context_at(today, df)
        rows.append({"call_id": cid, "isin": key, "name": e["name"], "type": e["type"],
                     "cohort": "live", "call_date": anchor, "call_type": ct, "mode": "live",
                     "rules_fired": f"live_score={sc};n14_flags={nf};day_n={e.get('day_n')};"
                                    f"gmp={e.get('gmp_pct')};sub={e.get('sub_total_x')}",
                     "score": sc, "score_quintile": None, "n14_flags": nf,
                     "tape_state": ctx["tape_state"], "crowding_pctl": ctx["crowding_pctl"],
                     "pop_pct": None, "alpha_1m": None, "alpha_3m": None, "alpha_1y": None,
                     "early_final_agree": None, "grade_status": "pending", "graded_at": None})
        print(f"  LIVE {ct}: {e['name']} (score {sc}, flags {nf})")
    if rows:
        new = pd.DataFrame(rows, columns=calls.LEDGER_COLUMNS)
        led = pd.concat([led, new], ignore_index=True) if led is not None and len(led) else new
    return led


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", nargs=2, metavar=("FROM", "TO"))
    ap.add_argument("--mode", default=None)
    ap.add_argument("--pit", default="cache",
                    choices=["forward_test", "pointintime", "cache"])
    ap.add_argument("--cohort", default=None, help="restrict to a cohort (e.g. boom)")
    ap.add_argument("--grade-only", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--live", action="store_true",
                    help="score OPEN issues from data/live/board.json -> mode=live calls")
    a = ap.parse_args()

    df = spine.load_substrate()
    led = load_ledger()

    if a.report:
        if led is None:
            sys.exit("no ledger yet")
        report(led)
        return
    if a.live:
        led = live_calls(df, led)
        save_ledger(led)
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
