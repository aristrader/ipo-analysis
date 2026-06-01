"""Derive data-informed scorecard weights from each component's cross-regime predictive lift,
print the report, and persist to data/master/scorecard_weights.json (used by the
`--profile data_informed` predictor).

Run: PYTHONPATH=. python run_weights.py
"""
from layer3 import spine
from layer3.predictor import weights as W


def main():
    df = spine.load_substrate()
    print("Deriving data-informed weights (point-in-time scoring of matured IPOs)… this takes a moment.")
    weights, report, scored = W.derive_weights(df, horizon="3y")
    print("\n" + "=" * 90)
    print("COMPONENT PREDICTIVE LIFT (Spearman rank-IC vs realized 3y alpha, point-in-time, per cohort)")
    print(f"scored {len(scored)} matured IPOs with prior-listed analogs")
    print("=" * 90)
    print(report.to_string(index=False))
    print("\nData-informed weights (cross-regime-consistent lift, normalized):")
    for c, w in weights.items():
        print(f"  {c:18s}: {w}")
    W.save_weights(weights)
    print(f"\nsaved → {W.WEIGHTS_PATH}")
    # calibration: combined-score quintiles + top-quintile lift (for the predictor's calibration readout)
    calib = W.derive_calibration(df, horizon="3y")
    W.save_calibration(calib)
    print(f"calibration: quintile thresholds {calib['score_quintiles']}, top-quintile lift "
          f"+{calib['top_quintile_lift_pp']}pp (n={calib['n_scored']}) → saved {W.CALIB_PATH}")
    print("Use with:  PYTHONPATH=. python predict_ipo.py --profile data_informed --type MB --sector ...")


if __name__ == "__main__":
    main()
