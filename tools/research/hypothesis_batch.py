"""Batch-test the 4 agents' 48 hypotheses (deduped -> ~32 features).
Per feature: rank-IC + top-vs-bottom tercile alpha spread in each of the 4 regime
cells (MB/SME x boom/longterm) vs alpha_1y. Verdict: ROBUST (same sign 4/4 cells,
mean |IC|>=0.08) / LEAN (same sign 4/4, weaker) / MIXED / THIN (insufficient cells).
PATH features are CONDITIONING (post-listing info — for hold/exit calls, never the
pre-IPO score). Output: compact verdict table.
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config

df = spine.load_substrate()
N = lambda c: pd.to_numeric(df[c], errors="coerce") if c in df.columns else pd.Series(np.nan, index=df.index)
ld = pd.to_datetime(df["listing_date"], errors="coerce")
yr = ld.dt.year

def z_within(s, keys):
    g = s.groupby(keys)
    return (s - g.transform("mean")) / g.transform("std")

def pctl_within(s, key):
    return s.groupby(key).rank(pct=True)

# ---------- point-in-time banker track record ----------
def banker_prior(stat):
    out = pd.Series(np.nan, index=df.index)
    d = pd.DataFrame({"lm": df["lead_manager"], "ld": ld,
                      "a": N("alpha_1y"), "wipe": (df["outcome_class"] == "wipeout").astype(float)}).dropna(subset=["lm", "ld"])
    for lm, g in d.groupby("lm"):
        g = g.sort_values("ld")
        prior = g[stat].expanding().mean().shift(1)
        cnt = g[stat].expanding().count().shift(1)
        out.loc[g.index] = prior.where(cnt >= 5)
    return out

sales_cagr = (N("net_sales_yr3") / N("net_sales_yr1")).clip(lower=0) ** 0.5 - 1
FEATURES = {
 # --- pricing / structure ---
 ("band_position", "pre"): (N("issue_price") - N("price_band_low")) / N("price_band_low"),
 ("anchor_ratio", "pre"): N("anchor_allocation_cr") / N("issue_size_cr"),
 ("fixed_price", "pre"): (df["pricing_method"].str.lower().str.contains("fix", na=False)).astype(float).where(df["pricing_method"].notna()),
 ("promoter_dilution_pp", "pre"): N("promoter_pre_issue_pct") - N("promoter_post_issue_pct"),
 ("size_z_type_year", "pre"): z_within(np.log1p(N("issue_size_cr")), [df["type"], yr]),
 ("min_investment", "pre"): N("min_investment_rs"),
 ("pe_vs_sector", "pre"): N("pe_ratio") - N("pe_ratio").groupby(df["broad_sector"]).transform("median"),
 ("all_ofs", "pre"): (N("ofs_pct") >= 0.95).astype(float).where(N("ofs_pct").notna()),
 ("banker_prior_alpha", "pre"): banker_prior("a"),
 ("banker_prior_wipeout", "pre"): banker_prior("wipe"),
 # --- demand ---
 ("qib_retail_ratio", "pre"): np.log1p(N("sub_qib_x")) - np.log1p(N("sub_retail_x")),
 ("nii_froth", "pre"): pctl_within(N("sub_nii_x"), df["type"]),
 ("gmp_sub_disagree", "pre"): z_within(N("gmp_pct"), [df["type"]]) - z_within(np.log1p(N("sub_total_x")), [df["type"]]),
 ("gmp_z_type_year", "pre"): z_within(N("gmp_pct"), [df["type"], yr]),
 ("undersubscribed", "pre"): (N("sub_total_x") < 1.5).astype(float).where(N("sub_total_x").notna()),
 ("demand_per_size", "pre"): np.log1p(N("sub_total_x")) - np.log1p(N("issue_size_cr")),
 ("breadth_hot_count", "pre"): sum((pctl_within(N(c), df["type"]) > 0.5).astype(float) for c in ("sub_qib_x", "sub_nii_x", "sub_retail_x")),
 ("qib_cold_retail_hot", "pre"): ((N("sub_qib_x") < 2) & (pctl_within(N("sub_retail_x"), df["type"]) > 0.5)).astype(float).where(N("sub_qib_x").notna() & N("sub_retail_x").notna()),
 # --- fundamentals ---
 ("sales_accel_spike", "pre"): (N("net_sales_yr3") / N("net_sales_yr2")) / (N("net_sales_yr2") / N("net_sales_yr1")),
 ("cf_conversion", "pre"): (N("operating_cf_yr1") + N("operating_cf_yr2") + N("operating_cf_yr3")) / (N("pat_yr1") + N("pat_yr2") + N("pat_yr3")).where(lambda s: s.abs() > 0.01),
 ("borrow_ramp", "pre"): (N("borrowings_yr3") - N("borrowings_yr1")) / N("total_assets_yr3"),
 ("opm_trend", "pre"): N("operating_profit_yr3") / N("net_sales_yr3") - N("operating_profit_yr1") / N("net_sales_yr1"),
 ("sales_vs_asset_growth", "pre"): (N("net_sales_yr3") / N("net_sales_yr1")) - (N("total_assets_yr3") / N("total_assets_yr1")),
 ("fresh_dilution", "pre"): N("fresh_issue_cr") / N("shareholder_funds_yr3"),
 ("profitable_stagnant", "pre"): ((N("pre_ipo_pat_margin_pct") > 0) & (sales_cagr < 0.05)).astype(float).where(N("pre_ipo_pat_margin_pct").notna() & sales_cagr.notna()),
 ("objects_debt_repay", "pre"): df.get("objects_of_issue", pd.Series("", index=df.index)).fillna("").str.lower().str.contains("repay|borrow|debt").astype(float).where(df.get("objects_of_issue").notna()),
 # --- path / conditioning (POST-listing info) ---
 ("lday_close_position", "path"): (N("adj_listing_close") - N("listing_low")) / (N("listing_high") - N("listing_low")),
 ("lday_green", "path"): (N("adj_listing_close") > N("adj_listing_open")).astype(float).where(N("adj_listing_close").notna() & N("adj_listing_open").notna()),
 ("lday_giveback", "path"): (N("listing_high") - N("listing_close")) / N("listing_high"),
 ("days_to_peak_1y", "path"): N("days_to_mfe_1y"),
 ("path_ratio_1m", "path"): N("mfe_lst_1m") / N("mae_lst_1m").abs().clip(lower=0.01),
 ("volatility", "path"): N("volatility_annual"),
 ("circuit_lock", "path"): N("circuit_lock_frac"),
 ("turnover_to_size", "path"): np.log1p(N("median_daily_turnover_inr")) - np.log1p(N("issue_size_cr") * 1e7),
}

target = N("alpha_1y")
print(f"{'feature':24s} {'kind':4s} {'cells':5s} {'ICs (MBb,SMEb,MBlt,SMElt)':28s} {'spread_pp':>9s}  verdict")
verdicts = []
for (name, kind), feat in FEATURES.items():
    ics, spreads, cells = [], [], 0
    for seg in ("MB", "SME"):
        for coh in ("boom", "longterm"):
            m = (df["type"] == seg) & (df["cohort"] == coh) & feat.notna() & target.notna()
            if m.sum() < config.MIN_N_TRADABLE:
                ics.append(None); continue
            x, y = feat[m], target[m]
            if x.nunique() < 2:
                ics.append(None); continue
            cells += 1
            ic = float(x.rank().corr(y.rank()))
            ics.append(round(ic, 2))
            try:
                b = pd.qcut(x, 3, labels=False, duplicates="drop")
                spreads.append(100 * (y[b == b.max()].median() - y[b == 0].median()))
            except ValueError:
                pass
    valid = [i for i in ics if i is not None]
    if cells < 3:
        v = "THIN"
    elif all(i > 0 for i in valid) or all(i < 0 for i in valid):
        v = "ROBUST" if np.mean(np.abs(valid)) >= 0.08 else "LEAN"
    else:
        v = "MIXED"
    sp = round(float(np.mean(spreads)), 1) if spreads else None
    verdicts.append((name, kind, v, valid, sp))
    print(f"{name:24s} {kind:4s} {cells:>2}/4  {str(ics):28s} {str(sp):>9s}  {v}")

print("\nROBUST:", [v[0] for v in verdicts if v[2] == 'ROBUST'])
print("LEAN  :", [v[0] for v in verdicts if v[2] == 'LEAN'])
