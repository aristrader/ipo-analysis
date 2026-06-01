"""Part C — run the strategy backtester and print comparison tables (vs do-nothing baseline).

Run: PYTHONPATH=. python run_backtest.py
"""
from layer3 import spine
from layer3.backtest import engine


def main():
    df = spine.load_substrate()
    print("=" * 100)
    print("IPO STRATEGY BACKTEST — point-in-time, net of costs. Secondary strategies measured in ALPHA")
    print("(vs Nifty, from listing price); allottee strategies in RAW return. Do-nothing = index (break-even).")
    print("SME and Mainboard never pooled. Access realism noted per strategy.")
    print("=" * 100)
    for seg in ["MB", "SME"]:
        for h in ["1y", "3y"]:
            print(f"\n### {seg} · horizon {h} " + "-" * 70)
            tbl = engine.run(df, horizon=h, segment=seg)
            cols = ["strategy", "kind", "N", "measure", "median_%", "mean_%", "win_rate_%",
                    "worst_%", "boom_median_%", "long_median_%", "verdict"]
            print(tbl[[c for c in cols if c in tbl.columns]].to_string(index=False))
    print("\nNote: 'flip_at_listing' raw gains ignore allotment probability + adverse selection — "
          "the realistic flip EV is far lower (you rarely get the hot ones). See access_realism column.")

    # the loop-closer: does the predictor's own combined score beat the field?
    from layer3.backtest.score_backtest import combined_score_backtest
    print("\n" + "=" * 100)
    print("COMBINED-SCORE BACKTEST (loop-closer) — do top-quintile predictor-score IPOs beat the field?")
    print("(point-in-time scoring + data-informed weights; realized 3y alpha; must hold cross-regime)")
    print("=" * 100)
    res, verdict = combined_score_backtest(df, horizon="3y")
    print(res.to_string(index=False))
    print(f"\nVERDICT: {verdict}")

    from layer3.backtest import analyses
    print("\n" + "=" * 100)
    print("HOLDING-PERIOD SWEEP — secondary buy-at-listing, exit at each horizon ('when do I sell?')")
    print("=" * 100)
    for seg in ["MB", "SME"]:
        print(f"\n### {seg} (alpha vs Nifty50):")
        print(analyses.holding_period_sweep(df, seg).to_string(index=False))
    print("\n### SME vs SMALLCAP-250 (the fairer benchmark for small caps, 2017+):")
    print(analyses.holding_period_sweep(df, "SME", benchmark="smallcap").to_string(index=False))

    print("\n" + "=" * 100)
    print("PORTFOLIO BASKET (equal-weight buy-every-IPO) vs do-nothing — dispersion-adjusted (NOT Sharpe)")
    print("=" * 100)
    print(analyses.portfolio_summary(df, horizon="1y").to_string(index=False))

    print("\n" + "=" * 100)
    print("FLIP ALLOTMENT-REALISM EV — what you ACTUALLY capture after allotment odds + adverse selection")
    print("=" * 100)
    for seg in ["MB", "SME"]:
        ev = analyses.flip_allotment_ev(df, seg)
        if ev:
            print(f"  {seg}: naive flip {ev['naive_mean_flip_%']}% → allotment-weighted "
                  f"{ev['allotment_weighted_flip_%']}% (adverse-selection cost {ev['adverse_selection_cost_pp']}pp; "
                  f"median allotment prob {ev['median_allotment_prob']}, N={ev['N']})")


if __name__ == "__main__":
    main()
