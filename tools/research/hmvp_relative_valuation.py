"""H-MVP — relative valuation via EARLIER-IPO peers (Theme H, the bounded owned-data MVP).

HYPOTHESES (P0):
  (a) RE-RATING: an IPO priced CHEAP on issue-time P/E vs its EARLIER-IPO peers (same industry,
      similar issue size) earns higher forward alpha (catches up); rich-vs-peers fades.
  (b) PEER-PROXIMITY DOSE: the effect strengthens with a tighter / better-populated peer set.

PEER SET (look-ahead-CLEAN): for IPO i, peers = IPOs that listed STRICTLY BEFORE i's listing_date,
  in the same industry bucket, with issue_size within a +/- band, min peer count. We then compute i's
  issue-time P/E PERCENTILE within that peer set (0=cheapest .. 1=richest), sign/tertile it, and join
  forward alpha (1y/3y) + bad-outcome. Issue-time P/E only (allottee/issue-anchored valuation).

DATA conventions (hypothesis_protocol.md): alpha vs Nifty; exclude unreliable_coverage (load_substrate
  already does); issue-time fields only; min-N floors (<12 suppress, 12-29 thin, >=30 report);
  distributions over means; srho (no scipy); Wilson CI on bad-outcome.

HONEST WALL (pre-declared): pe_ratio/eps_ttm have ZERO coverage in the 2006-19 longterm cohort, so the
  VALUATION signal is structurally BOOM-ONLY (same as n6/pe_vs_sector). The cross-regime gate CANNOT be
  cleared with the data we own. The MVP therefore (1) tests within boom-MB and boom-SME, (2) asks the
  real question: is PEER-matched percentile INCREMENTAL over the existing SECTOR-MEDIAN version (n6),
  and (3) runs a label-shuffle PLACEBO. Verdict is bounded to display-only at best by construction.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine

OUT_CSV = "data/master/review/hmvp_relative_valuation_review.csv"
RNG = np.random.default_rng(20260610)

# peer-matcher params (pre-declared). We run THREE configs to separate "signal is weak" from
# "peer set is too sparse": (A) strict fine-industry+size-band, (B) broad_sector+size-band,
# (C) broad_sector, NO size band (the loosest fair definition = closest to n6's sector pool).
MIN_PEERS = 5         # need >=5 prior peers or the row is ABSTAIN (no rank)
MIN_N = 12            # min-N floor for reporting a cell
CONFIGS = [
    ("A_fine_ind_band3", "industry", 3.0),
    ("B_broad_band3",    "broad_sector", 3.0),
    ("C_broad_noband",   "broad_sector", None),
]


def srho(a, b):
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")


def wilson(k, n):
    return spine.wilson_ci(int(k), int(n)) if n else (float("nan"), float("nan"))


def load():
    df = spine.load_substrate()
    # load_substrate already drops unreliable_coverage; keep the protocol-listed statuses explicit anyway
    df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
    N = lambda c: pd.to_numeric(df[c], errors="coerce")
    df["ip"] = N("issue_price"); df["eps"] = N("eps_ttm")
    # issue-time P/E: compute from issue_price / eps_ttm, fall back to provided pe_ratio
    pe = np.where((df["ip"] > 0) & (df["eps"] > 0), df["ip"] / df["eps"], np.nan)
    df["pe"] = pd.Series(pe, index=df.index).fillna(N("pe_ratio"))
    df.loc[df["pe"] <= 0, "pe"] = np.nan               # loss-makers have no meaningful P/E
    df["size"] = N("issue_size_cr")
    df["a1y"] = N("alpha_1y"); df["a3y"] = N("alpha_3y")
    df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
    # bad outcome (downside) — wipeout OR dead-money <=-50% terminal, survivorship-honest via spine band
    df["bad"] = N("return_from_listing_1y") <= -0.50    # simple downside proxy at 1y (display)
    return df


def peer_rank(df, bucket_col, size_band):
    """Point-in-time peer P/E percentile + sector-median rel-P/E, both look-ahead clean.

    For each IPO (sorted by listing_date), peers = strictly-earlier-listed IPOs of the SAME segment,
    same `bucket_col` bucket, issue_size within the factor band (or any size if size_band is None),
    with a valid P/E. Returns:
      pe_pctl   = rank of this IPO's P/E within its peer set, in [0,1] (0=cheapest, 1=richest)
      n_peers   = peer count (dose)
      pe_relsec = this IPO's P/E / the EARLIER-PEER median P/E (the n6 analogue, but PIT & prior-only
                  on the SAME pool — so the incremental comparison is apples-to-apples)
    """
    df = df.sort_values("ld").reset_index(drop=False).rename(columns={"index": "_orig"})
    df["ind"] = df[bucket_col]
    pe_pctl = np.full(len(df), np.nan)
    n_peers = np.zeros(len(df), dtype=int)
    pe_relsec = np.full(len(df), np.nan)
    for i in range(len(df)):
        r = df.iloc[i]
        if pd.isna(r["pe"]) or pd.isna(r["size"]) or pd.isna(r["ld"]) or pd.isna(r["ind"]):
            continue
        prior = df.iloc[:i]
        prior = prior[(prior["ld"] < r["ld"]) & (prior["type"] == r["type"]) &
                      (prior["ind"] == r["ind"]) & prior["pe"].notna() & prior["size"].notna()]
        if size_band is not None:
            prior = prior[(prior["size"] >= r["size"] / size_band) & (prior["size"] <= r["size"] * size_band)]
        n = len(prior)
        n_peers[i] = n
        if n >= MIN_PEERS:
            pe_pctl[i] = float((prior["pe"] < r["pe"]).mean())
            med = prior["pe"].median()
            if pd.notna(med) and med > 0:
                pe_relsec[i] = r["pe"] / med
    df["pe_pctl"] = pe_pctl; df["n_peers"] = n_peers; df["pe_relsec"] = pe_relsec
    return df.set_index("_orig")


def cell_report(sub, signal, horizon, label):
    """L1+L2 for one cell: IC, cheap/rich split (median + bootstrap CI), bad-outcome split."""
    a = sub[f"a{horizon}"]
    g = spine.maturity_gated(sub, horizon)             # maturity-gate the forward window (no look-ahead)
    g = g[g[signal].notna() & g[f"a{horizon}"].notna()]
    n = len(g)
    if n < MIN_N:
        return {"cell": label, "signal": signal, "horizon": horizon, "N": n, "note": "thin/suppressed"}
    ic = srho(g[signal], g[f"a{horizon}"])
    # tertiles on the signal (cheap = low percentile / low rel-PE)
    q1, q2 = g[signal].quantile([1/3, 2/3])
    cheap = g[g[signal] <= q1]; rich = g[g[signal] >= q2]
    mc, mr = cheap[f"a{horizon}"].median(), rich[f"a{horizon}"].median()
    ci_c = spine.bootstrap_median_ci(cheap[f"a{horizon}"]) if len(cheap) >= MIN_N else {"lo": None, "hi": None, "p_positive": None}
    ci_r = spine.bootstrap_median_ci(rich[f"a{horizon}"]) if len(rich) >= MIN_N else {"lo": None, "hi": None, "p_positive": None}
    # bad-outcome (display, 1y downside proxy) cheap vs rich + Wilson
    bc, br = cheap["bad"], rich["bad"]
    return {
        "cell": label, "signal": signal, "horizon": horizon, "N": n,
        "IC": round(ic, 3),
        "cheap_N": len(cheap), "rich_N": len(rich),
        "cheap_med_alpha_%": round(100*mc, 1), "rich_med_alpha_%": round(100*mr, 1),
        "spread_cheap_minus_rich_pp": round(100*(mc - mr), 1),
        "cheap_ci": None if ci_c["lo"] is None else f"[{100*ci_c['lo']:.0f},{100*ci_c['hi']:.0f}]",
        "rich_ci": None if ci_r["lo"] is None else f"[{100*ci_r['lo']:.0f},{100*ci_r['hi']:.0f}]",
        "cheap_bad_%": round(100*bc.mean(), 1), "rich_bad_%": round(100*br.mean(), 1),
        "rich_bad_wilson": f"[{100*wilson(br.sum(), len(br))[0]:.0f},{100*wilson(br.sum(), len(br))[1]:.0f}]",
    }


def placebo(sub, signal, horizon, n_shuffle=1000):
    """Shuffle the peer-relative rank across rows; how often does a fake spread match the real one?"""
    g = spine.maturity_gated(sub, horizon)
    g = g[g[signal].notna() & g[f"a{horizon}"].notna()]
    if len(g) < 3 * MIN_N:
        return None
    a = g[f"a{horizon}"].values; s = g[signal].values
    def spread(sig):
        q1, q2 = np.quantile(sig, [1/3, 2/3])
        cheap = a[sig <= q1]; rich = a[sig >= q2]
        return np.median(cheap) - np.median(rich)
    real = spread(s)
    null = np.array([spread(RNG.permutation(s)) for _ in range(n_shuffle)])
    # one-sided: hypothesis is cheap>rich (positive spread). p = P(null >= real) if real>0
    p = float((null >= real).mean()) if real >= 0 else float((null <= real).mean())
    return {"real_spread_pp": round(100*real, 1), "null_mean_pp": round(100*null.mean(), 1),
            "null_sd_pp": round(100*null.std(), 1), "p_one_sided": round(p, 3), "N": len(g)}


def incremental_vs_sector(sub, horizon):
    """Head-to-head: does PEER-matched percentile add over the SECTOR-MEDIAN rel-P/E (n6 analogue),
    on the SAME maturity-gated rows where BOTH are defined? Compares IC and the tertile spread."""
    g = spine.maturity_gated(sub, horizon)
    g = g[g["pe_pctl"].notna() & g["pe_relsec"].notna() & g[f"a{horizon}"].notna()]
    if len(g) < MIN_N:
        return {"horizon": horizon, "N": len(g), "note": "thin"}
    ic_peer = srho(g["pe_pctl"], g[f"a{horizon}"])
    ic_sec = srho(g["pe_relsec"], g[f"a{horizon}"])
    # partial: residualize peer-percentile rank on sector-rel rank, IC of the residual (does peer add?)
    pr = g["pe_pctl"].rank(); sr = g["pe_relsec"].rank(); ar = g[f"a{horizon}"].rank()
    # residual of peer-rank after removing sector-rank (linear)
    b = np.polyfit(sr, pr, 1); resid = pr - (b[0]*sr + b[1])
    ic_resid = float(pd.Series(resid).corr(ar))
    return {"horizon": horizon, "N": len(g),
            "IC_peer_pctl": round(ic_peer, 3), "IC_sector_rel": round(ic_sec, 3),
            "IC_peer_resid_after_sector": round(ic_resid, 3),
            "verdict": ("peer adds" if abs(ic_resid) > 0.05 and np.sign(ic_resid) == np.sign(ic_peer)
                        else "redundant-with-sector")}


def main():
    df = load()
    print("="*78)
    print("H-MVP — relative valuation via earlier-IPO peers")
    print(f"params: MIN_PEERS={MIN_PEERS}, MIN_N={MIN_N}, configs={[c[0] for c in CONFIGS]}")
    print("="*78)

    # coverage / the honest wall
    print("\nCOVERAGE (the cross-regime wall):")
    for (c, t), s in df.groupby(["cohort", "type"]):
        print(f"  {c}/{t}: N={len(s)} pe>0={s['pe'].notna().sum()} "
              f"industry={s['industry'].notna().sum()} broad_sector={s['broad_sector'].notna().sum()}")
    print("  => longterm P/E coverage is ZERO -> valuation re-rating is STRUCTURALLY boom-only.")

    rows = []
    review_rows = []
    coverage_rows = []
    for cfg_name, bucket_col, size_band in CONFIGS:
        print("\n" + "#"*78)
        print(f"# CONFIG {cfg_name}: bucket={bucket_col} size_band={size_band}")
        print("#"*78)
        for seg in ("MB", "SME"):
            sub = df[(df["cohort"] == "boom") & (df["type"] == seg)].copy()
            sub = peer_rank(sub, bucket_col, size_band)
            matched = sub[sub["pe_pctl"].notna()]
            cov = {"config": cfg_name, "seg": seg,
                   "rows_with_pe_size_bucket": int((sub["pe"].notna() & sub["size"].notna() & sub["ind"].notna()).sum()),
                   "peer_matched": len(matched),
                   "median_peer_count": int(matched["n_peers"].median()) if len(matched) else 0}
            coverage_rows.append(cov)
            print(f"\n--- BOOM / {seg} [{cfg_name}] ---")
            print(f"  candidate rows (P/E & size & bucket): {cov['rows_with_pe_size_bucket']}; "
                  f"PEER-MATCHED (>= {MIN_PEERS} prior peers): {len(matched)} "
                  f"({100*len(matched)/max(1,len(sub)):.0f}% of segment); "
                  f"median peer count: {cov['median_peer_count']}")
            # review rows only from the loosest config that actually populates (avoid dup) — tag config
            for _, r in matched.iterrows():
                review_rows.append({"config": cfg_name, "isin": r["isin"], "type": seg, "cohort": "boom",
                                    "listing_date": r["ld"].date() if pd.notna(r["ld"]) else None,
                                    "bucket": r["ind"],
                                    "issue_size_cr": round(float(r["size"]), 1) if pd.notna(r["size"]) else None,
                                    "pe": round(float(r["pe"]), 2), "n_peers": int(r["n_peers"]),
                                    "pe_pctl": round(float(r["pe_pctl"]), 3),
                                    "pe_relsec": round(float(r["pe_relsec"]), 3) if pd.notna(r["pe_relsec"]) else None,
                                    "alpha_1y": round(float(r["a1y"]), 4) if pd.notna(r["a1y"]) else None,
                                    "alpha_3y": round(float(r["a3y"]), 4) if pd.notna(r["a3y"]) else None})
            if len(matched) < MIN_N:
                print("  -> below min-N floor; cell suppressed.")
                continue
            # L1+L2: cheap = low pctl. Re-rating => cheap outperforms rich (positive spread).
            for h in ("1y", "3y"):
                res = cell_report(matched, "pe_pctl", h, f"boom/{seg}")
                res["config"] = cfg_name; rows.append(res)
                print("  L1/L2:", {k: res.get(k) for k in ("horizon", "N", "IC", "spread_cheap_minus_rich_pp", "rich_bad_%", "note")})
            # dose: split by peer count
            if len(matched) >= 3*MIN_N:
                med = matched["n_peers"].median()
                for lbl, dd in (("hi-peer-count", matched[matched["n_peers"] >= med]),
                                ("lo-peer-count", matched[matched["n_peers"] < med])):
                    r = cell_report(dd, "pe_pctl", "1y", f"boom/{seg}/{lbl}")
                    print(f"  DOSE {lbl}:", {k: r.get(k) for k in ("N", "IC", "spread_cheap_minus_rich_pp")})
            # placebo
            for h in ("1y", "3y"):
                pl = placebo(matched, "pe_pctl", h)
                print(f"  PLACEBO {h}:", pl)
                if pl:
                    rows.append({"cell": f"boom/{seg}", "config": cfg_name, "test": f"placebo_{h}", **pl})
            # incremental vs sector-median
            for h in ("1y", "3y"):
                inc = incremental_vs_sector(matched, h)
                print(f"  INCREMENTAL-vs-sector {h}:", inc)
                rows.append({"cell": f"boom/{seg}", "config": cfg_name, "test": f"incremental_{h}", **inc})

    pd.DataFrame(review_rows).to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(review_rows)} peer-matched rows (all configs, tagged) -> {OUT_CSV}")
    print("\nCOVERAGE BY CONFIG:")
    print(pd.DataFrame(coverage_rows).to_string(index=False))
    print("\nSUMMARY TABLE:")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
