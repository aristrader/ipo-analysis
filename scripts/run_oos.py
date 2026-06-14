"""Out-of-sample 'honest report card' for the predictor score.

Trains the scorecard weights on IPOs listed up to a cutoff year, then tests them on IPOs listed
AFTER the cutoff (never seen during fitting) and reports the top-quintile-vs-field lift on that
test set. A small/zero/negative OOS lift means the in-sample edge did NOT generalise — that's the
honest answer. Run: PYTHONPATH=. python run_oos.py
"""
from layer3 import spine
from layer3.predictor import weights as W

SPLITS = [(2022, "1y"), (2021, "1y"), (2019, "3y")]   # recent@1y (rich test) + older@3y


def main():
    df = spine.load_substrate()
    print("=" * 96)
    print("OUT-OF-SAMPLE REPORT CARD — weights fit on ≤cutoff, tested on listings AFTER cutoff (never seen)")
    print("=" * 96)
    for cutoff, h in SPLITS:
        r = W.oos_evaluate(df, cutoff_year=cutoff, horizon=h)
        print(f"\nTrain ≤{cutoff}  →  test {cutoff+1}+ at {h} horizon")
        if r.get("error"):
            print(f"  {r['error']} (train N={r['n_train']}, test N={r['n_test']})"); continue
        print(f"  train N={r['n_train']}  test N={r['n_test']}  weights={r['weights']}")
        print(f"  TEST field median alpha {r['test_field_median_%']}%  vs  top-quintile {r['test_topquintile_median_%']}%")
        print(f"  >> OUT-OF-SAMPLE LIFT: {r['oos_lift_pp']:+}pp   (top-quintile win-rate {r['top_win_rate_%']}%)")
    print("\nReading it: a clearly POSITIVE oos_lift that holds across splits = the score generalises (earns "
          "'validated'). Near-zero/negative = the in-sample edge was overfit. This is the real test.")


if __name__ == "__main__":
    main()
