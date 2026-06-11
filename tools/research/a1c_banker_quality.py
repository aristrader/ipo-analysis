"""A1c harness — test the banker-quality measure against the two PRE-REGISTERED primaries.

DOWNSIDE arm (vs live coverage_guard): threshold the shrunk PIT bad-rate at BAD_RATE and compare
  bad-outcome RECALL/precision + 4-cell discrimination + false-veto. Bar: recall must NOT regress.
RETURN arm (the n12 re-test, presumed dead): rank-IC of the shrunk PIT banker-alpha vs realized
  alpha, per 4-cell, with a shuffle-banker-label placebo. A two-sided banker→return signal must be
  cross-regime + placebo-clean to overturn n12.

Pre-registered params (banker_quality defaults): H=3y, k=5, taper 0.45/0.30/0.20/0.05, BAD_RATE=0.40.
Run: PYTHONPATH=. python tools/research/a1c_banker_quality.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
import pandas as pd
from layer3 import spine
from layer3.predictor import banker_quality as bq, scorecard

PANELS = [("MB", "boom"), ("MB", "longterm"), ("SME", "boom"), ("SME", "longterm")]
REPUTABLE = ["Nuvama", "Morgan Stanley", "Smart Horizon", "Choice", "Indorient", "Anand Rathi"]


def load():
    df = spine.load_substrate()
    if "listing_metrics_status" in df.columns:
        df = df[df["listing_metrics_status"] != "unreliable_coverage"]
    return df.reset_index(drop=True)


def srho(x, y):
    s = pd.DataFrame({"x": x, "y": y}).dropna()
    return float(s["x"].rank().corr(s["y"].rank())) if len(s) >= 12 else None


def downside_arm(df):
    bad = scorecard._bad_outcome_mask(df).astype(bool)
    total_bad = int(bad.sum())
    print(f"\n=== DOWNSIDE arm — recall vs live coverage_guard (total bad = {total_bad}) ===")
    cg = scorecard._obscure_banker_series(df, df).fillna(0).astype(bool)         # live baseline
    q = bq.banker_quality_series(df, df, target="bad")                            # A1c shrunk PIT bad-rate
    a1c = (q >= scorecard.OBSCURE_BAD_RATE).fillna(False)
    for name, fired in [("coverage_guard (LIVE)", cg), ("A1c bad-rate ≥0.40", a1c)]:
        nf = int(fired.sum()); caught = int((fired & bad).sum())
        rec = round(100 * caught / total_bad, 1) if total_bad else None
        prec = round(100 * caught / nf, 1) if nf else None
        print(f"  {name:24s}: fires {nf:4d} | recall {rec}% | precision {prec}%")
    # 4-cell discrimination of the A1c flag
    print("  A1c 4-cell bad% (flagged vs clean):")
    for seg, co in PANELS:
        m = (df["type"] == seg) & (df["cohort"] == co)
        f = a1c[m]; o = bad[m]
        nfl = int(f.sum()); ncl = int((~f).sum())
        bf = round(100 * o[f].mean(), 1) if nfl else None
        bc = round(100 * o[~f].mean(), 1) if ncl else None
        lift = round(bf - bc, 1) if (bf is not None and bc is not None) else None
        print(f"    {seg}-{co:8s}: flag n={nfl:3d} bad%={bf} | clean n={ncl:3d} bad%={bc} | lift={lift}pp")
    # false-veto on reputable banks
    lm = df["lead_manager"].astype(str)
    print("  false-veto (reputable banks flagged by A1c):")
    for nm in REPUTABLE:
        mask = lm.str.contains(nm, case=False, na=False)
        if int(mask.sum()):
            print(f"    {nm:16s}: {int(a1c[mask].sum())}/{int(mask.sum())} flagged")


def _arm(df, feature_target, outcomes, n_shuffle, label):
    """For one banker-quality FEATURE, report per-cell rank-IC vs each OUTCOME horizon + a pooled
    shuffle-banker-label placebo. Tests the horizon-split point: short horizons (pop/1m) are the
    allottee/listing dynamic, long horizons (1y) the company's performance — different questions."""
    print(f"\n  -- feature = banker-Q-{label} --")
    q = bq.banker_quality_series(df, df, target=feature_target)
    for outcome in outcomes:
        oc = pd.to_numeric(df[outcome], errors="coerce")
        cells, real_pooled = [], []
        for seg, co in PANELS:
            m = (df["type"] == seg) & (df["cohort"] == co)
            ic = srho(q[m], oc[m]); n = int((q[m].notna() & oc[m].notna()).sum())
            cells.append(f"{seg[:1]}{co[:1].upper()} {('%+.2f' % ic) if ic is not None else 'NA'}(n{n})")
            if ic is not None:
                real_pooled.append(ic)
        pooled = float(np.mean(real_pooled)) if real_pooled else None
        # pooled placebo
        rng = np.random.default_rng(1); null = []; d = df.copy(); base = d["lead_manager"].values.copy()
        for _ in range(n_shuffle):
            d["lead_manager"] = rng.permutation(base)
            qs = bq.banker_quality_series(d, d, target=feature_target)
            ics = [srho(qs[(d["type"] == s) & (d["cohort"] == c)],
                        pd.to_numeric(d.loc[(d["type"] == s) & (d["cohort"] == c), outcome], errors="coerce"))
                   for s, c in PANELS]
            ics = [x for x in ics if x is not None]
            if ics:
                null.append(float(np.mean(ics)))
        null = np.array(null)
        p = float((np.abs(null) >= abs(pooled)).mean()) if (pooled is not None and len(null)) else None
        same_sign = len({np.sign(x) for x in real_pooled}) == 1 if real_pooled else False
        print(f"    {outcome:22s}: {' '.join(cells)} | pooled={None if pooled is None else round(pooled,3)} "
              f"p={p} same-sign-cells={same_sign}")


def return_arm(df, n_shuffle=100):
    print("\n=== RETURN arm — does banker-quality predict outcomes ACROSS HORIZONS? (n12 re-test) ===")
    print("  (short horizons = listing/allottee pop dynamic; long = company performance — tested separately)")
    OUTCOMES = ["adj_listing_gain_open", "alpha_1m", "alpha_3m", "alpha_1y"]
    # feature built from prior ALPHAS (the track-record arm) vs every horizon:
    _arm(df, "alpha", OUTCOMES, n_shuffle, "alpha-track")
    # feature built from prior LISTING POPS (the pricing-discipline arm) — natural short-horizon predictor:
    _arm(df, "pop", ["adj_listing_gain_open", "alpha_1m"], n_shuffle, "pop-track")


def main():
    df = load()
    print(f"panel: {len(df)} rows (unreliable_coverage excluded); banker-quality params "
          f"H={bq.DEFAULT_H} k={bq.DEFAULT_K} taper={bq.TAPER}")
    downside_arm(df)
    return_arm(df)
    print("\nDISCIPLINE: SME-boom-alone = boom-only (NOT live). Return arm must be cross-regime + placebo-clean "
          "to overturn n12. Promotion (if any) → independent review → evolve-only-if-robust.")


if __name__ == "__main__":
    main()
