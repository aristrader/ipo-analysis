"""MIGRATION+ — does an at-IPO feature predict which SMEs EVENTUALLY migrate to the mainboard?

Look-ahead-safe by design: features are all known at/before listing; the outcome (eventual migration)
is future. The load-bearing trap is CENSORING — migration takes a median ~3.7y, and 0% of SMEs migrate
in their first 3y, so a recent SME labelled "didn't migrate" is just censored, not a true negative.
We therefore test ONLY the MATURE eligible set (listed ≥ MATURE_AGE_Y before AS_OF), where migration is
a well-balanced ~55/45 outcome. Discipline: rank-IC + tertile migration-rate per feature, vintage-stability
(does it hold across listing-era buckets, not one), placebo (shuffle migration labels), min-N floors. NO ML.

Run: PYTHONPATH=. python tools/research/migration_predictor.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
import pandas as pd
from layer3 import config
from tools.research.sme_migration import derive_migration
from layer3 import spine

MATURE_AGE_Y = 5.0          # listed ≥5y before AS_OF -> had a fair chance to migrate (median TTM 3.7y, p75 5.1y)
CONT_FEATURES = ["pre_ipo_pat", "pre_ipo_net_sales", "issue_size_cr", "market_cap_cr",
                 "sub_total_x", "sub_qib_x", "gmp_pct", "promoter_holding_post"]
VINTAGES = [(2012, 2016, "2012-16"), (2017, 2019, "2017-19"), (2020, 2022, "2020-22")]


def eligible(df=None):
    df = df if df is not None else spine.load_substrate()
    sme = derive_migration(df)
    sme["_ld"] = pd.to_datetime(sme["listing_date"], errors="coerce")
    asof = pd.Timestamp(config.AS_OF_DATE)
    sme["age_y"] = (asof - sme["_ld"]).dt.days / 365.25
    sme["_yr"] = sme["_ld"].dt.year
    return sme[sme["age_y"] >= MATURE_AGE_Y].copy()


def _srho(x, y):
    s = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": y}).dropna()
    return (float(s["x"].rank().corr(s["y"].rank())), len(s)) if len(s) >= 30 else (None, len(s))


def _tertile_rates(x, mig):
    s = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "m": mig}).dropna()
    if len(s) < 60:
        return None
    try:
        s["t"] = pd.qcut(s["x"], 3, labels=["low", "mid", "high"], duplicates="drop")
    except ValueError:
        return None
    return {str(t): (round(100 * g["m"].mean(), 1), len(g)) for t, g in s.groupby("t", observed=True)}


def placebo(x, mig, n=200, seed=1):
    real, nrl = _srho(x, mig)
    if real is None:
        return None
    rng = np.random.default_rng(seed)
    m = mig.values.astype(float)
    null = []
    xr = pd.to_numeric(x, errors="coerce")
    for _ in range(n):
        ic, _n = _srho(xr, pd.Series(rng.permutation(m), index=mig.index))
        if ic is not None:
            null.append(ic)
    null = np.array(null)
    return real, float(np.abs(null).mean()), float(null.std()), float((np.abs(null) >= abs(real)).mean())


def main():
    elig = eligible()
    mig = elig["migrated_to_mainboard"].astype(float)
    print(f"MATURE eligible SMEs (age ≥{MATURE_AGE_Y}y): n={len(elig)}  migrated={100*mig.mean():.1f}%")
    print(f"  by cohort: " + " ".join(f"{c}={int((elig['cohort']==c).sum())}(mig {100*mig[elig['cohort']==c].mean():.0f}%)"
                                      for c in ("boom", "longterm")))

    print("\n=== continuous at-IPO features — rank-IC vs eventual migration + placebo ===")
    for f in CONT_FEATURES:
        if f not in elig:
            continue
        res = placebo(elig[f], mig)
        ic, nrl, nstd, p = (res if res else (None, None, None, None))
        cov = int(elig[f].notna().sum())
        # vintage stability
        vints = []
        for lo, hi, lbl in VINTAGES:
            mv = (elig["_yr"] >= lo) & (elig["_yr"] <= hi)
            ivc, nvc = _srho(elig.loc[mv, f], mig[mv])
            vints.append(f"{lbl}:{('%+.2f'%ivc) if ivc is not None else 'NA'}({nvc})")
        tert = _tertile_rates(elig[f], mig)
        print(f"  {f:22s} cov={cov:3d} IC={None if ic is None else round(ic,3)} "
              f"placebo_p={p} | vintage {' '.join(vints)}")
        if tert:
            print(f"      tertile migration%: {tert}")

    print("\n=== binary/categorical ===")
    prof = (pd.to_numeric(elig["pre_ipo_pat"], errors="coerce") > 0)
    print(f"  profitable at IPO (PAT>0): mig {100*mig[prof].mean():.1f}% (n={int(prof.sum())}) "
          f"vs loss-making mig {100*mig[~prof & elig['pre_ipo_pat'].notna()].mean():.1f}% "
          f"(n={int((~prof & elig['pre_ipo_pat'].notna()).sum())})")
    if "broad_sector" in elig:
        bs = elig[elig["broad_sector"].notna()]
        print("  by broad_sector (n≥20):")
        for s, g in bs.groupby("broad_sector"):
            if len(g) >= 20:
                print(f"    {str(s)[:24]:24s}: mig {100*g['migrated_to_mainboard'].mean():.0f}% (n={len(g)})")

    print("\nDISCIPLINE: a real predictor must hold cross-vintage + beat placebo + survive the boom/longterm thinness "
          "(eligible boom set is small — migration eligibility concentrates pre-2022). Verdict → rules/index.md.")


if __name__ == "__main__":
    main()
