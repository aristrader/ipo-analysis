"""Study: (A) market-context signal verdicts, (C) hot-pop fade + SHORT score + quadrant
categories, validated on the 2026 never-seen holdout. Read-only; writes docs/research/*.md.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd, numpy as np
from layer3 import spine, config, context

df = spine.load_substrate()
df = context.add_context_features(df)
N = lambda s: pd.to_numeric(s, errors="coerce")

# =============== A. context signal tests (IC vs 1y alpha, cross-regime) ===============
print("=" * 70); print("A. MARKET-CONTEXT SIGNALS — rank-IC vs alpha_1y (maturity-gated)")
res_a = []
for feat in ("ctx_nifty_mom_3m", "ctx_ipo_heat_90d", "ctx_heat_pop_90d", "ctx_sector_heat_180d"):
    for seg in ("MB", "SME"):
        for coh in ("boom", "longterm"):
            g = spine.maturity_gated(spine.segment(df, segment=seg, cohort=coh), "1y")
            x, y = N(g[feat]), N(g["alpha_1y"])
            m = x.notna() & y.notna()
            if m.sum() < config.MIN_N_TRADABLE:
                continue
            ic = float(x[m].rank().corr(y[m].rank()))
            # tercile spread
            try:
                b = pd.qcut(x[m], 3, labels=False, duplicates="drop")
                spread = float(100 * (y[m][b == b.max()].median() - y[m][b == 0].median()))
            except ValueError:
                spread = None
            res_a.append({"feature": feat, "seg": seg, "cohort": coh, "n": int(m.sum()),
                          "rank_ic": round(ic, 3),
                          "top_minus_bottom_tercile_alpha_pp": round(spread, 1) if spread is not None else None})
ta = pd.DataFrame(res_a)
print(ta.to_string(index=False))

# =============== C1. hot-pop fade (uses the NEW short-horizon movement) ===============
print("=" * 70); print("C1. HOT FIRST MONTH -> WHAT NEXT? (boom, matured 1y, from listing)")
res_c = []
for seg in ("MB", "SME"):
    g = spine.maturity_gated(spine.segment(df, segment=seg, cohort="boom"), "1y")
    g = g[g["listing_metrics_status"].isin(context.TRUSTED)]
    mfe1m = N(g["mfe_lst_1m"]); r1m = N(g["return_from_listing_1m"]); r1y = N(g["return_from_listing_1y"])
    for lab, lo, hi in (("cold(<+5%)", -9, 0.05), ("warm(5-25%)", 0.05, 0.25),
                        ("hot(25-60%)", 0.25, 0.60), ("blazing(>60%)", 0.60, 99)):
        m = mfe1m.notna() & r1y.notna() & (mfe1m >= lo) & (mfe1m < hi)
        if m.sum() < config.MIN_N_HINT:
            res_c.append({"seg": seg, "first_month_peak": lab, "n": int(m.sum()), "insufficient": True}); continue
        after = (1 + r1y[m]) / (1 + r1m[m].clip(lower=-0.95)) - 1   # drift AFTER month 1
        res_c.append({"seg": seg, "first_month_peak": lab, "n": int(m.sum()),
                      "median_1m_end_%": round(100 * float(r1m[m].median()), 1),
                      "median_1y_end_%": round(100 * float(r1y[m].median()), 1),
                      "median_drift_after_m1_%": round(100 * float(after.median()), 1),
                      "pct_1y_below_1m": round(100 * float((r1y[m] < r1m[m]).mean()), 1)})
tc = pd.DataFrame(res_c)
print(tc.to_string(index=False))

# =============== C2. SHORT score (transparent, no-ML) + quadrants, train<=2025 ===============
print("=" * 70); print("C2. SHORT score (pre-listing features only; percentile blend) — train<=2025")
ld = pd.to_datetime(df["listing_date"], errors="coerce")
train = df[(ld <= "2025-12-31")].copy()
def short_score(frame, ref):
    """0-100: within-segment percentile blend of GMP and subscription (the two
    strongest pre-listing 'demand' reads). Transparent, no fitting."""
    out = pd.Series(index=frame.index, dtype=float)
    for seg in ("MB", "SME"):
        ref_g = ref[ref["type"] == seg]
        fr_g = frame[frame["type"] == seg]
        gmp_ref = N(ref_g["gmp_pct"]).dropna()
        sub_ref = N(ref_g["sub_total_x"]).dropna()
        gmp = N(fr_g["gmp_pct"]); sub = N(fr_g["sub_total_x"])
        pg = gmp.map(lambda v: (gmp_ref < v).mean() * 100 if pd.notna(v) else np.nan)
        ps = sub.map(lambda v: (sub_ref < v).mean() * 100 if pd.notna(v) else np.nan)
        out.loc[fr_g.index] = pd.concat([pg, ps], axis=1).mean(axis=1, skipna=True)
    return out
train["short"] = short_score(train, train)
g = spine.maturity_gated(train[train["cohort"] == "boom"], "1y")
g = g[g["listing_metrics_status"].isin(context.TRUSTED)]
hit = (N(g["mfe_lst_1m"]) >= 0.25)
s = g["short"]
rows = []
for lab, lo, hi in (("low(<33)", -1, 33), ("mid(33-66)", 33, 66), ("high(>66)", 66, 101)):
    m = s.notna() & (s >= lo) & (s < hi) & N(g["mfe_lst_1m"]).notna()
    rows.append({"short_bucket": lab, "n": int(m.sum()),
                 "P(touch +25% in month 1)": round(100 * float(hit[m].mean()), 1) if m.sum() >= 10 else None,
                 "median_1y_from_listing_%": round(100 * float(N(g["return_from_listing_1y"])[m].median()), 1) if m.sum() >= 10 else None})
print(pd.DataFrame(rows).to_string(index=False))

# =============== C3. validate on the 2026 never-seen holdout ===============
print("=" * 70); print("C3. HOLDOUT (2026 never-seen): SHORT bucket vs realized first-month move")
old = pd.read_csv("archive/pre_refresh_20260606/ipo_analysis.csv", dtype=str)
hold = df[~df["isin"].isin(set(old["isin"]))].copy()
hold = hold[pd.to_datetime(hold["listing_date"], errors="coerce") <= pd.Timestamp(config.AS_OF_DATE)]
hold["short"] = short_score(hold, train)
mfe1m_h = N(hold["mfe_lst_1m"]); r1m_h = N(hold["return_from_listing_1m"])
rows = []
for lab, lo, hi in (("low(<33)", -1, 33), ("mid(33-66)", 33, 66), ("high(>66)", 66, 101)):
    m = hold["short"].notna() & (hold["short"] >= lo) & (hold["short"] < hi)
    mm = m & mfe1m_h.notna()
    rows.append({"short_bucket": lab, "n_scored": int(m.sum()), "n_with_1m": int(mm.sum()),
                 "P(touched +25% m1)": round(100 * float((mfe1m_h[mm] >= 0.25).mean()), 1) if mm.sum() >= 8 else None,
                 "median_1m_end_%": round(100 * float(r1m_h[mm].median()), 1) if mm.sum() >= 8 else None})
print(pd.DataFrame(rows).to_string(index=False))
json.dump({"A": res_a, "C1": res_c}, open("/tmp/study_raw.json", "w"), indent=1, default=str)
print("\nraw -> /tmp/study_raw.json")
