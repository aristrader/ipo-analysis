"""'Were-we-right' scorecard CLI (Thread A.2) — run anytime (e.g. monthly) to see whether the
calls actually worked, with honest small-sample Wilson confidence bands.
Usage: PYTHONPATH=. python run_scorecard.py [--horizon 1m|3m|1y]
"""
import argparse
import pandas as pd
from layer3 import calibration as C

LEDGER = "data/master/calls_ledger.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", default="3m", choices=["1m", "3m", "1y"])
    a = ap.parse_args()
    led = pd.read_csv(LEDGER)
    sc = C.scorecard(led, a.horizon)
    print(f"=== WERE-WE-RIGHT scorecard (horizon {a.horizon}; hit-rate with 95% Wilson CI) ===")
    if sc.empty:
        print("  no graded calls at this horizon yet"); return
    print(f"{'call_type':18s} {'mode':14s} {'n':>4} {'hit':>6} {'95% CI':>15} {'med α':>7}")
    for _, r in sc.iterrows():
        print(f"  {r['call_type']:16s} {r['mode']:14s} {r['n']:>4} {100*r['hit_rate']:>5.0f}% "
              f"[{100*r['ci_lo']:>3.0f},{100*r['ci_hi']:>3.0f}]% {r['median_alpha_pct']:>+6.1f}%")
    rel = C.score_reliability(led, a.horizon)
    if not rel.empty:
        print(f"\n=== SCORE ORDERING (does a higher score mean a higher chance of beating Nifty?) ===")
        print(f"{'bucket':>6} {'score range':>14} {'n':>4} {'P(up)':>7} {'95% CI':>15}")
        for _, r in rel.iterrows():
            print(f"  Q{r['score_bucket']:>2} {r['score_lo']:>6.0f}-{r['score_hi']:<6.0f} {r['n']:>4} "
                  f"{100*r['p_up']:>5.0f}%  [{100*r['ci_lo']:>3.0f},{100*r['ci_hi']:>3.0f}]%")
        print("  (rising P(up) down the buckets = the score is well-ordered.)")
    print("\nNOTE: live/gap_filled = real forward record (young); backfilled = 2026 OOS; "
          "historical_sim = dress rehearsal. Small n -> wide CI = honest uncertainty.")


if __name__ == "__main__":
    main()
