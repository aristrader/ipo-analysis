"""E1 — pre-IPO total-accruals (earnings-quality) signal.

DATA RESOLUTION (the gating question first):
  Full Modified-Jones discretionary accruals needs ΔReceivables — there is NO receivables
  column in the substrate (confirmed: only pat_yr*, operating_cf_yr*, total_assets_yr*,
  net_sales_yr*, operating_profit_yr*). So Modified-Jones stays DATA-GATED (Thread-C verdict
  stands). What IS computable is the *total-accruals* proxy:

      TA = (PAT - operating CFO) / average total assets       (pre-IPO latest FY)

  This is the graded version of the proven binary n8 flag ("PAT>0 but CFO<=0"). High TA = a
  large slice of reported profit is NOT backed by cash = lower earnings quality. We test whether
  the GRADED measure adds anything over the binary flag + existing N14 flags.

  Year semantics: yr3 is the LATEST pre-IPO FY (pre_ipo_pat matches pat_yr3 in 1590/1920 rows);
  yr3 also has the best coverage (TA proxy ~71% ending-assets / ~64% avg-assets). We use avg
  assets (ta2+ta3)/2 when available, else ending assets ta3.

3-LAYER: tertile TA within each cohort x segment cell -> forward alpha (1y/3y, maturity-gated,
  alpha vs Nifty) + bad-outcome rate (wipeout OR dead-money). Wilson CI, distributions, min-N
  floors. PLACEBO = shuffle the TA labels within cell. Incremental test vs the n8 binary flag.

No look-ahead: TA is built only from pre-IPO financials; forward alpha is maturity-gated.
No scipy. Run: PYTHONPATH=. .venv/bin/python tools/research/e1_accruals.py
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine, config

RNG = np.random.default_rng(20260609)
MIN_CELL = 30          # min-N floor for a reportable cell (config.MIN_N_TRADABLE)
DEAD_MONEY = config.DEAD_MONEY_RETURN   # -0.5


def srho(a, b):
    a, b = pd.Series(a), pd.Series(b); m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")


def load():
    df = spine.load_substrate()                      # equity-only
    df = df[df["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)].copy()
    N = lambda c: pd.to_numeric(df[c], errors="coerce")
    pat, cfo, ta3, ta2 = N("pat_yr3"), N("operating_cf_yr3"), N("total_assets_yr3"), N("total_assets_yr2")
    avg_assets = (ta2 + ta3) / 2.0
    avg_assets = avg_assets.where(avg_assets.notna(), ta3)     # fallback ending assets
    avg_assets = avg_assets.where(avg_assets > 0)              # divide-by-zero / negative-equity guard
    df["accruals"] = (pat - cfo) / avg_assets                  # TA proxy
    # binary n8 flag (the proven signal) on the SAME latest FY for an apples-to-apples increment test
    df["n8_flag"] = ((pat > 0) & (cfo <= 0)).where(pat.notna() & cfo.notna())
    return df


def bad_outcome_mask(df):
    """Bad outcome = confirmed-wipeout-class OR dead-money (alive, deeply negative from issue,
    illiquid) — the n9-zombie definition. Survivorship-honest: terminal_state never drops
    delisted; dead-money uses the longest-finished issue-anchored return."""
    state = spine.terminal_state(df)
    wipe = state == "wipeout"
    # dead money: alive but terminal return-from-issue <= -50% and illiquid (low liquidity_flag)
    ret = None
    for h in ["3y", "2y", "1y"]:           # longest finished first, then backfill shorter
        c = f"return_from_issue_{h}"
        if c in df.columns:
            r = pd.to_numeric(df[c], errors="coerce")
            ret = r if ret is None else ret.fillna(r)
    if ret is None:
        ret = pd.Series(np.nan, index=df.index)
    illiquid = df["liquidity_flag"].astype(str) == "low"
    dead = (state == "alive") & (ret <= DEAD_MONEY) & illiquid
    return (wipe | dead), state


def tertile(s):
    """Within-cell tertiles by accruals (Q1 = lowest accruals = highest earnings quality)."""
    s = pd.to_numeric(s, errors="coerce")
    valid = s.dropna()
    if valid.nunique() < 3 or len(valid) < 9:
        return pd.Series(index=s.index, dtype=object)
    try:
        q = pd.qcut(s, 3, labels=["Q1_low_accrual", "Q2_mid", "Q3_high_accrual"], duplicates="drop")
    except ValueError:
        return pd.Series(index=s.index, dtype=object)
    return q.astype(object)


def cell_table(sub, label):
    """One cohort x segment cell: accruals tertiles -> fwd alpha 1y/3y + bad-outcome rate."""
    out = []
    sub = sub.copy()
    sub["tert"] = tertile(sub["accruals"])
    bad_all, _ = bad_outcome_mask(sub)
    for t in ["Q1_low_accrual", "Q2_mid", "Q3_high_accrual"]:
        m = sub["tert"] == t
        b = sub[m]
        g1 = spine.maturity_gated(b, "1y"); g3 = spine.maturity_gated(b, "3y")
        a1 = spine.alpha_series(g1, "1y"); a3 = spine.alpha_series(g3, "3y")
        bad = bad_all[m]
        k, n = int(bad.sum()), int(bad.notna().sum() if hasattr(bad, "notna") else len(bad))
        lo, hi = spine.wilson_ci(k, n) if n else (None, None)
        d1, d3 = spine.distribution(a1), spine.distribution(a3)
        out.append({
            "cell": label, "tertile": t, "N": int(m.sum()),
            "N_1y": d1["n"], "med_alpha_1y": _r(d1["median"]) if d1["n"] >= config.MIN_N_HINT else None,
            "N_3y": d3["n"], "med_alpha_3y": _r(d3["median"]) if d3["n"] >= config.MIN_N_HINT else None,
            "bad_k": k, "bad_n": n, "bad_rate": _r(k / n) if n else None,
            "bad_ci_lo": _r(lo), "bad_ci_hi": _r(hi),
        })
    return out


def spread(cell_rows, key):
    """Q3 (high accrual) minus Q1 (low accrual). Negative alpha-spread / positive bad-spread
    = high accruals worse = thesis-consistent."""
    q1 = next((r for r in cell_rows if r["tertile"] == "Q1_low_accrual"), None)
    q3 = next((r for r in cell_rows if r["tertile"] == "Q3_high_accrual"), None)
    if not q1 or not q3 or q1[key] is None or q3[key] is None:
        return None
    return round(q3[key] - q1[key], 4)


def placebo(sub, n_iter=1000):
    """Shuffle accruals labels within the cell; record the Q3-Q1 bad-rate spread null distribution.
    Real spread inside the null body => DEAD."""
    bad_all, _ = bad_outcome_mask(sub)
    bad_all = bad_all.reindex(sub.index)
    acc = sub["accruals"].values
    valid = ~pd.isna(acc) & bad_all.notna().values
    acc_v = acc[valid]; bad_v = bad_all.values[valid].astype(float)
    if valid.sum() < 30 or pd.Series(acc_v).nunique() < 3:
        return None
    def q3_q1_spread(a, b):
        try:
            t = pd.qcut(pd.Series(a), 3, labels=[0, 1, 2], duplicates="drop")
        except ValueError:
            return np.nan
        m1, m3 = (t == 0), (t == 2)
        if m1.sum() < 5 or m3.sum() < 5: return np.nan
        return b[m3.values].mean() - b[m1.values].mean()
    real = q3_q1_spread(acc_v, bad_v)
    null = []
    for _ in range(n_iter):
        s = q3_q1_spread(RNG.permutation(acc_v), bad_v)
        if not np.isnan(s): null.append(s)
    null = np.array(null)
    if len(null) < 100 or np.isnan(real):
        return None
    p_two = float((np.abs(null) >= abs(real)).mean())
    return {"real_spread": round(float(real), 4), "null_mean": round(float(null.mean()), 4),
            "null_sd": round(float(null.std()), 4), "p_two_sided": round(p_two, 4), "n_null": len(null)}


def incremental_vs_n8(sub):
    """Does the GRADED accrual add over the binary n8 flag? Within n8-CLEAN names (flag=False),
    does the top accrual tertile still show a worse bad-outcome rate? (the marginal info)."""
    clean = sub[sub["n8_flag"] == False].copy()
    if len(clean) < 60:
        return None
    clean["tert"] = tertile(clean["accruals"])
    bad_all, _ = bad_outcome_mask(clean)
    res = {}
    for t in ["Q1_low_accrual", "Q3_high_accrual"]:
        m = (clean["tert"] == t)
        bad = bad_all[m]
        k, n = int(bad.sum()), int(len(bad))
        res[t] = {"k": k, "n": n, "rate": _r(k / n) if n else None}
    if res.get("Q1_low_accrual", {}).get("rate") is None or res.get("Q3_high_accrual", {}).get("rate") is None:
        return None
    res["spread_q3_minus_q1"] = round(res["Q3_high_accrual"]["rate"] - res["Q1_low_accrual"]["rate"], 4)
    # also: n8-flagged base rate for context
    flagged = sub[sub["n8_flag"] == True]
    fb, _ = bad_outcome_mask(flagged)
    res["n8_flagged_bad_rate"] = _r(int(fb.sum()) / len(flagged)) if len(flagged) else None
    res["n8_flagged_n"] = int(len(flagged))
    return res


def _r(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


def main():
    df = load()
    cov = df["accruals"].notna().mean()
    print(f"=== E1 accruals (TA proxy) ===  rows={len(df)}  TA coverage={cov:.1%}\n")

    all_rows, summary = [], []
    for coh in config.COHORTS:
        for seg in config.SEGMENTS:
            sub = df[(df["cohort"] == coh) & (df["type"] == seg)].copy()
            label = f"{seg}-{coh}"
            n_valid = sub["accruals"].notna().sum()
            print(f"--- {label}: N={len(sub)}  TA-valid={n_valid}")
            if n_valid < MIN_CELL:
                print(f"    SUPPRESSED (TA-valid {n_valid} < {MIN_CELL})\n"); continue
            rows = cell_table(sub, label)
            all_rows += rows
            for r in rows:
                print(f"    {r['tertile']:16s} N={r['N']:4d}  "
                      f"med_a1y={r['med_alpha_1y']}  med_a3y={r['med_alpha_3y']}  "
                      f"bad={r['bad_rate']} [{r['bad_ci_lo']},{r['bad_ci_hi']}] (k={r['bad_k']}/{r['bad_n']})")
            sp_a3 = spread(rows, "med_alpha_3y"); sp_a1 = spread(rows, "med_alpha_1y"); sp_bad = spread(rows, "bad_rate")
            ic = srho(sub["accruals"], spine.alpha_series(sub, "3y"))
            pb = placebo(sub)
            inc = incremental_vs_n8(sub)
            print(f"    Q3-Q1 spread: alpha1y={sp_a1} alpha3y={sp_a3} bad_rate={sp_bad}  | rank-IC(acc,a3y)={round(ic,3) if not np.isnan(ic) else None}")
            print(f"    PLACEBO: {pb}")
            print(f"    INCREMENTAL vs n8 (within n8-clean): {inc}\n")
            summary.append({"cell": label, "N_valid": int(n_valid),
                            "spread_alpha_1y": sp_a1, "spread_alpha_3y": sp_a3,
                            "spread_bad_rate": sp_bad, "rank_IC_acc_a3y": round(ic, 3) if not np.isnan(ic) else None,
                            "placebo_p": pb["p_two_sided"] if pb else None,
                            "placebo_real": pb["real_spread"] if pb else None,
                            "placebo_null_mean": pb["null_mean"] if pb else None,
                            "incr_n8clean_spread": inc["spread_q3_minus_q1"] if inc else None})

    # write review CSVs
    rev = config.ROOT / "data/master/review"
    rev.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(rev / "e1_accruals_review.csv", index=False)
    pd.DataFrame(summary).to_csv(rev / "e1_accruals_summary.csv", index=False)
    print("=== SUMMARY (Q3 high-accrual minus Q1 low-accrual; thesis: alpha-spread<0, bad-spread>0) ===")
    print(pd.DataFrame(summary).to_string(index=False))
    print(f"\nwrote {rev/'e1_accruals_review.csv'} and {rev/'e1_accruals_summary.csv'}")


if __name__ == "__main__":
    main()
