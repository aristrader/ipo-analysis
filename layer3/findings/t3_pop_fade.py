"""T3 — Listing-pop → fade gradient.

Bucket by listing-day pop (adj_listing_gain_open) → forward RAW return-from-listing at 1y/3y
(the secondary buyer's gross return). NOTE on alpha: stored alpha_* is itself measured FROM the
listing price (alpha = return_from_listing − benchmark), so it does NOT contain the listing pop;
we report RAW return-from-listing here as the plainest secondary-buyer measure and show the
allottee-vs-secondary wedge alongside. Excludes unreliable_coverage listing rows. MB and SME apart.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

# (label, lo, hi) on adj_listing_gain_open (a fraction)
BUCKETS = [("<0% (discount)", -10, 0.0), ("0–25%", 0.0, 0.25), ("25–50%", 0.25, 0.50),
           ("50–100%", 0.50, 1.00), (">100%", 1.00, 1e9)]


def compute(df):
    tables, charts, caveats = [], [], []
    d = df[df["listing_metrics_status"].isin(config.TRUSTED_LISTING_STATUS)].copy()
    d["pop"] = pd.to_numeric(d["adj_listing_gain_open"], errors="coerce")

    rows = []
    for seg in config.SEGMENTS:
        sub = d[d["type"] == seg]
        for label, lo, hi in BUCKETS:
            b = sub[(sub["pop"] >= lo) & (sub["pop"] < hi)]
            r1 = spine.listing_return(b, "1y"); r3 = spine.listing_return(b, "3y")
            rows.append({"segment": seg, "listing_pop_bucket": label, "N": len(b),
                         "median_listing_pop_%": _p(b["pop"].median()),
                         "fwd_ret_from_listing_1y_%": _p(r1.median()),
                         "N_1y": int(r1.notna().sum()),
                         "fwd_ret_from_listing_3y_%": _p(r3.median()),
                         "N_3y": int(r3.notna().sum())})
    tables.append(("Listing-pop bucket → forward RAW return from the listing price (secondary buyer). "
                   "NOT alpha (alpha already contains the pop). Does the biggest pop fade? "
                   "Read down each segment.", pd.DataFrame(rows)))

    # the issue-vs-listing wedge: allottee return vs secondary-buyer return, by bucket (MB)
    wedge = []
    sub = d[d["type"] == "MB"]
    for label, lo, hi in BUCKETS:
        b = sub[(sub["pop"] >= lo) & (sub["pop"] < hi)]
        ri = pd.to_numeric(b.get("return_from_issue_1y"), errors="coerce")
        rl = spine.listing_return(b, "1y")
        wedge.append({"listing_pop_bucket": label, "N": len(b),
                      "allottee_1y_from_issue_%": _p(ri.median()),
                      "secondary_buyer_1y_from_listing_%": _p(rl.median())})
    tables.append(("Mainboard: allottee (bought at issue) vs secondary buyer (bought at listing) — the wedge. "
                   "Allottees keep the pop; listing-day buyers don't.", pd.DataFrame(wedge)))

    # movement view (mv-T3-reach): does the secondary buyer's UPSIDE OPPORTUNITY fade as hard as the
    # endpoint, or do hot IPOs stay volatile-both-ways? Reach-curve per pop bucket, from listing.
    reach = []
    for seg in config.SEGMENTS:
        sub = d[d["type"] == seg]
        for label, lo, hi in BUCKETS:
            b = sub[(sub["pop"] >= lo) & (sub["pop"] < hi)]
            rc = spine.reach_curve(b, "1y", entry="listing")
            if rc["n"] < config.MIN_N_HINT:
                continue
            up = {u["move"]: u["pct_reached"] for u in rc["reach_up"]}
            dn = {x["move"]: x["pct_fell_to"] for x in rc["reach_down"]}
            reach.append({"segment": seg, "listing_pop_bucket": label, "N": rc["n"],
                          "ever +20%": up.get("+20%"), "ever +50%": up.get("+50%"), "ever +100%": up.get("+100%"),
                          "ever −20%": dn.get("-20%"), "ever −30%": dn.get("-30%"), "ever −50%": dn.get("-50%"),
                          "ended_positive_%": rc["pct_ended_positive"]})
    tables.append(("Movement view — the SECONDARY buyer's reach-curve by pop bucket: chance the price ever "
                   "TOUCHED +20/50/100% (and ever fell −20/30/50%) within 1y, vs the % that actually ENDED up. "
                   "Tells you whether the *opportunity* to exit in profit survives even where the endpoint fades.",
                   pd.DataFrame(reach)))

    from layer3 import charts as ch
    mb = pd.DataFrame(rows)
    mb = mb[mb["segment"] == "MB"]
    charts.append(("Mainboard: forward 1y return from listing by listing-pop bucket",
                   ch.bar_png(mb["listing_pop_bucket"].tolist(),
                              [v if v is not None else 0 for v in mb["fwd_ret_from_listing_1y_%"]],
                              ns=mb["N_1y"].tolist(),
                              title="MB: forward 1y return (from listing) by listing pop",
                              ylabel="median fwd 1y return %")))

    caveats += [
        "Forward return here is RAW (from the listing price), not alpha — by design, to avoid double-counting "
        "the listing pop that issue-anchored alpha already includes.",
        "SME listing-day prices are manipulation-prone and many use weekly screener data — treat SME buckets "
        "as exploratory.",
        "unreliable_coverage listing rows are excluded; recovered_bhavcopy + inferred_split are included.",
        "High-pop SME buckets are often a BARBELL (a cluster of deep losses + a cluster of big winners), so the "
        "median understates the dispersion — read the median alongside the wide spread, not as a typical outcome.",
        "Reach-curve = the move was AVAILABLE at some point, not that you captured it (you'd have had to time "
        "the exit). T3's pop-fade direction holds cross-regime but its within-vintage robustness was downgraded — "
        "treat the reach view as descriptive texture, not a tradable signal.",
    ]
    narrative = ("Do IPOs that pop hardest on day one then fade for the person who buys at listing? We bucket by "
                 "the listing-day pop and follow the SECONDARY buyer's raw forward return — kept separate from the "
                 "allottee, who already pocketed the pop. This is the flip-vs-hold reality check, as a base-rate "
                 "gradient (not per-name calls).")
    return Finding(id="t3", title="T3 · Listing-pop → fade gradient",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
