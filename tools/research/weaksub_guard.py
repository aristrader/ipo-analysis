"""Weak-subscription false-APPLY guard (B1 seed) — 2026-06-09.

THE NEW ANGLE (not the dead first-order "undersubscribed -> bad" screen):
  CONDITIONED on a would-be APPLY (top-segment-quintile AND 0 wipeout flags), does adding a
  LOW-SUBSCRIPTION veto improve APPLY PRECISION (fewer false-APPLYs / losers) WITHOUT killing
  the winners -- and does it hold cross-regime? This is a guard ON the APPLY decision, distinct
  from raw undersubscribed-predicts-returns (REJECTED first-order, see rules/index.md).

METHOD (point-in-time, mirrors miss_mining.py / calls.py):
  * For each MATURED IPO (listed >=~12mo before AS_OF so a 1y outcome exists) we reproduce the
    genuine PIT would-be-APPLY call: analog pool = ONLY IPOs that listed strictly before its
    listing-month; data-informed weights derived on prior-only data (per listing-month, the
    established cheap PIT pattern -- pool is dominated by 2000+ matured IPOs, weights barely drift);
    per-SEGMENT combined-score quintiles from the same prior-only scored frame; wipeout flags.
    would-be-APPLY = top-quintile AND 0 flags (exactly calls.py APPLY).
  * Among would-be-APPLYs WITH subscription data, split LOW (sub_total_x < THRESH) vs ADEQUATE
    (>= THRESH). Compare bad-outcome rate + forward alpha_1y/return_1y, Wilson95 CIs.
  * Winners-lost if you VETO the low-sub APPLYs = how many true winners you'd dump.
  * PLACEBO: shuffle sub_total_x across the APPLY pool, re-split, re-measure (a real edge must
    NOT reproduce under a shuffled label).
  * Cross-regime: boom-matured (2020-2023) vs recent-matured (2024-2025). Longterm (2006-19) has
    only ~89/1010 sub-coverage -> reported as NOT TESTABLE (honest limitation), not a pass.

HONESTY RAILS: PIT only (target + later IPOs never in its pool); survivorship-honest (wipeout
  terminal -100%); exclude unreliable_coverage listing rows; min-N floors; distributions; N stated.
REVERSE-CAUSATION NOTE: subscription closes ~T-1 to listing, so it IS pre-listing-readable (a
  legit ex-ante input), BUT it is itself a demand OUTCOME (partly the same thing the analog score
  proxies). The whole point is the DISAGREEMENT (analog says top-quintile, own demand says weak).

Run: PYTHONPATH=. python tools/research/weaksub_guard.py
Writes: data/master/review/weaksub_guard_apply_pool.csv
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
import pandas as pd

from layer3 import config
from layer3.forward_test import _query_from_row
from layer3.predictor import predict as P, weights as W

THRESH = 3.0               # low-subscription threshold (B1 used <3x); we also sweep below
APPLY_QUINTILE, AVOID_FLAGS = 5, 2
OUT_CSV = config.ROOT / "data/master/review/weaksub_guard_apply_pool.csv"
SEED = 20260609


def num(s):
    return pd.to_numeric(s, errors="coerce")


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def build_apply_pool(df, asof):
    """Reproduce the PIT would-be-APPLY call for every MATURED IPO; return the APPLY pool frame."""
    # matured = a 1y outcome can exist (listed >= 365d before AS_OF); equity; reliable listing.
    # Restrict to 2020+ where subscription data + analog machinery are both usable (longterm
    # 2006-19 has ~9% sub coverage and feature-sparse priors -> declared NOT-TESTABLE separately).
    mat = df[df["_ld"].notna() & (df["_ld"] <= asof - pd.Timedelta(days=365))
             & (df["_ld"] >= pd.Timestamp("2020-01-01"))].copy()
    if "instrument_type" in mat.columns:
        mat = mat[mat["instrument_type"].fillna("equity") == "equity"]
    mat = mat[mat["listing_metrics_status"].astype(str) != "unreliable_coverage"]
    mat["_month"] = mat["_ld"].dt.to_period("M")
    print(f"matured cohort (>=365d old, equity, reliable listing): {len(mat)} "
          f"({mat['type'].value_counts().to_dict()})")

    wpath = W.WEIGHTS_PATH
    saved = wpath.read_bytes() if wpath.exists() else None
    rows = []
    try:
        for month, mg in mat.groupby("_month"):
            month_start = month.to_timestamp()
            prior = df[df["_ld"] < month_start]
            if len(prior) < config.MIN_N_TRADABLE:
                continue
            w, _rep, scored = W.derive_weights(prior, horizon="3y")
            if scored.empty or "isin" not in scored.columns:
                continue                       # feature-sparse early prior -> skip month
            W.save_weights(w)
            scored = scored.reset_index(drop=True)
            type_map = prior.drop_duplicates("isin").set_index("isin")["type"].to_dict()
            scored["type"] = scored["isin"].map(type_map)
            scored["combined"] = scored.apply(lambda r: W._combined(r, w), axis=1)
            seg_thr = {}
            for seg, g in scored.groupby("type"):
                s = g["combined"].dropna()
                if len(s) >= 5:
                    seg_thr[seg] = [float(s.quantile(q)) for q in (0.2, 0.4, 0.6, 0.8)]
            for _, r in mg.iterrows():
                try:
                    res = P.predict(_query_from_row(r), df=prior, profile="data_informed")
                    cs = res["scorecard"].get("combined_score")
                    wf = res.get("wipeout_flags", {}) or {}
                    n_flags = wf.get("n_flags")
                except Exception:
                    cs, n_flags = None, None
                thr = seg_thr.get(r["type"])
                quint = (sum(cs >= t for t in thr) + 1) if (thr and cs is not None) else None
                is_apply = (quint == APPLY_QUINTILE and n_flags == 0)
                if not is_apply:
                    continue
                rows.append(_outcome_row(r, cs, quint, n_flags))
    finally:
        if saved is not None:
            wpath.write_bytes(saved)
    return pd.DataFrame(rows)


def _outcome_row(r, cs, quint, n_flags):
    oc = str(r.get("outcome_class"))
    is_wipeout = (oc == "wipeout")
    allottee = num(pd.Series([r.get("current_return_from_issue")])).iloc[0]
    allottee_eff = -1.0 if is_wipeout else allottee
    a1y = num(pd.Series([r.get("alpha_1y")])).iloc[0]
    r1y = num(pd.Series([r.get("return_from_issue_1y")])).iloc[0]
    mdd = num(pd.Series([r.get("max_drawdown_pct")])).iloc[0]
    # BAD outcome (the false-APPLY definition, allottee-anchored, survivorship-honest)
    is_bad = (oc in ("loser", "wipeout")) or (pd.notna(allottee_eff) and allottee_eff < -0.15) \
        or (pd.notna(mdd) and mdd <= -0.50 and not (pd.notna(allottee_eff) and allottee_eff > 0))
    is_winner = (oc in ("winner", "multibagger")) or (pd.notna(allottee_eff) and allottee_eff > 0.25)
    if is_bad and is_winner:                       # ended-up wins (matches miss_mining tie-break)
        if pd.notna(allottee_eff) and allottee_eff > 0:
            is_bad = False
        else:
            is_winner = False
    ld = r["_ld"]
    return {
        "isin": r["isin"], "name": r.get("company_name"), "type": r["type"],
        "listing_date": ld.date().isoformat(), "year": ld.year,
        "sub_total_x": round(float(num(pd.Series([r.get("sub_total_x")])).iloc[0]), 2)
        if pd.notna(num(pd.Series([r.get("sub_total_x")])).iloc[0]) else None,
        "issue_size_cr": round(float(num(pd.Series([r.get("issue_size_cr")])).iloc[0]), 1)
        if pd.notna(num(pd.Series([r.get("issue_size_cr")])).iloc[0]) else None,
        "score": cs, "quintile": quint, "n_flags": n_flags,
        "allottee_ret": round(float(allottee_eff), 4) if pd.notna(allottee_eff) else None,
        "alpha_1y": round(float(a1y), 4) if pd.notna(a1y) else None,
        "ret_1y": round(float(r1y), 4) if pd.notna(r1y) else None,
        "outcome_class": oc, "is_bad": bool(is_bad), "is_winner": bool(is_winner),
    }


def split_table(pool, label, thresh=THRESH):
    """Among would-be-APPLYs WITH sub data, split low vs adequate; print bad-rate + fwd + winners-lost."""
    p = pool[pool["sub_total_x"].notna()].copy()
    if len(p) < 12:
        print(f"\n[{label}] APPLY-with-sub n={len(p)} < 12 -> SUPPRESS (thin)")
        return None
    lo = p[p["sub_total_x"] < thresh]
    hi = p[p["sub_total_x"] >= thresh]
    print(f"\n[{label}] would-be-APPLY with sub data: n={len(p)} "
          f"(low<{thresh}x: {len(lo)}, adequate>={thresh}x: {len(hi)})")
    print(f"  {'cell':10s} {'n':>4s} {'bad%':>7s} {'Wilson95':>15s} {'winner%':>8s} "
          f"{'a1y_med%':>9s} {'ret1y_med%':>11s}")
    out = {}
    for name, cell in (("LOW", lo), ("ADEQUATE", hi)):
        n = len(cell)
        if n == 0:
            continue
        bad = int(cell["is_bad"].sum())
        win = int(cell["is_winner"].sum())
        a1y = cell["alpha_1y"].median()
        r1y = cell["ret_1y"].median()
        print(f"  {name:10s} {n:4d} {100*bad/n:6.1f}% {str(wilson(bad,n)):>15s} "
              f"{100*win/n:7.1f}% {100*a1y if pd.notna(a1y) else float('nan'):8.1f}% "
              f"{100*r1y if pd.notna(r1y) else float('nan'):10.1f}%")
        out[name] = {"n": n, "bad": bad, "win": win, "bad_pct": round(100*bad/n, 1),
                     "wilson": wilson(bad, n), "a1y_med": a1y, "r1y_med": r1y}
    # WINNERS-LOST if you veto the low-sub APPLYs
    if len(lo):
        win_lost = int(lo["is_winner"].sum())
        bad_avoided = int(lo["is_bad"].sum())
        print(f"  --> VETO low-sub: dumps {len(lo)} APPLYs; avoids {bad_avoided} losers, "
              f"DUMPS {win_lost} winners (lost-winner median allottee "
              f"{100*lo[lo['is_winner']]['allottee_ret'].median():.0f}% )"
              if win_lost else
              f"  --> VETO low-sub: dumps {len(lo)} APPLYs; avoids {bad_avoided} losers, DUMPS 0 winners")
        out["veto"] = {"dumps": len(lo), "bad_avoided": bad_avoided, "winners_lost": win_lost}
    return out


def placebo(pool, label, thresh=THRESH, n_iter=2000):
    """Shuffle sub_total_x across the APPLY pool; how often does a real-or-bigger bad-rate gap appear?"""
    p = pool[pool["sub_total_x"].notna() & pool["is_bad"].notna()].copy()
    if len(p) < 24:
        print(f"\n[{label}] placebo SKIP (n={len(p)} < 24)")
        return
    sub = p["sub_total_x"].values
    bad = p["is_bad"].values.astype(float)
    real_lo = bad[sub < thresh].mean() if (sub < thresh).any() else np.nan
    real_hi = bad[sub >= thresh].mean() if (sub >= thresh).any() else np.nan
    real_gap = real_lo - real_hi
    rng = np.random.default_rng(SEED)
    ge = 0
    for _ in range(n_iter):
        sh = rng.permutation(sub)
        glo = bad[sh < thresh].mean() if (sh < thresh).any() else np.nan
        ghi = bad[sh >= thresh].mean() if (sh >= thresh).any() else np.nan
        if pd.notna(glo) and pd.notna(ghi) and (glo - ghi) >= real_gap:
            ge += 1
    print(f"\n[{label}] PLACEBO (shuffle sub, {n_iter} iters): real bad-rate gap "
          f"low-adequate = {100*real_gap:+.1f}pp ; shuffled >= real in {ge}/{n_iter} "
          f"(pseudo-p {ge/n_iter:.3f}) -> {'PASS (real)' if ge/n_iter < 0.05 else 'FAIL (placebo reproduces)'}")


def redundancy_note(df, asof):
    """Is low-sub-among-APPLY just the dead first-order undersubscribed screen? Show the marginal."""
    print("\n" + "=" * 70)
    print("REDUNDANCY-WITH-EXISTING check (vs REJECTED first-order undersubscribed / demand_per_size)")
    print("=" * 70)
    mat = df[df["_ld"].notna() & (df["_ld"] <= asof - pd.Timedelta(days=365))].copy()
    mat = mat[mat["listing_metrics_status"].astype(str) != "unreliable_coverage"]
    sub = num(mat["sub_total_x"])
    a1y = num(mat["alpha_1y"])
    m = sub.notna() & a1y.notna()
    lo = a1y[m & (sub < THRESH)]
    hi = a1y[m & (sub >= THRESH)]
    print(f"  UNCONDITIONAL (the dead screen): low-sub a1y median {100*lo.median():.1f}% (n={len(lo)}) "
          f"vs adequate {100*hi.median():.1f}% (n={len(hi)})")
    print("  -> first-order undersubscribed is REJECTED in rules/index.md; this guard is only NEW if it")
    print("     adds signal CONDITIONED ON would-be-APPLY (the disagreement), tested above.")


def main():
    df = pd.read_csv(config.ROOT / "data/master/ipo_analysis.csv", low_memory=False)
    df["_ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
    asof = pd.Timestamp(config.AS_OF_DATE)

    pool = build_apply_pool(df, asof)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pool.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(pool)} would-be-APPLY rows -> {OUT_CSV}")
    print(f"APPLY pool: {pool['type'].value_counts().to_dict()}; "
          f"sub coverage {pool['sub_total_x'].notna().sum()}/{len(pool)}")

    print("\n" + "=" * 70)
    print("WOULD-BE-APPLY SPLIT BY SUBSCRIPTION (low vs adequate), cross-regime")
    print("=" * 70)
    split_table(pool, "ALL-MATURED")
    boom = pool[(pool["year"] >= 2020) & (pool["year"] <= 2023)]
    recent = pool[(pool["year"] >= 2024)]
    long_ = pool[pool["year"] <= 2019]
    split_table(boom, "BOOM-MATURED 2020-2023")
    split_table(recent, "RECENT-MATURED 2024-2025")
    print(f"\n[LONGTERM 2006-2019] APPLY pool with sub data: "
          f"{long_['sub_total_x'].notna().sum()} -> NOT TESTABLE (longterm sub coverage ~9%); "
          f"cross-regime claim CANNOT be made on the longterm cohort.")

    placebo(pool, "ALL-MATURED")
    placebo(boom, "BOOM-MATURED")

    redundancy_note(df, asof)


if __name__ == "__main__":
    main()
