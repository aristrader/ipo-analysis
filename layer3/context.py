"""Market-context features (POINT-IN-TIME: pre-listing information only).

Each feature describes the environment an IPO was BORN into — computable for any
row from data already on disk, and for a live query at scoring time:
  ctx_nifty_mom_3m     trailing 3-month Nifty return ending at the listing date
  ctx_ipo_heat_90d     how many same-segment IPOs listed in the prior 90 days
  ctx_heat_pop_90d     median listing pop of those prior-90d IPOs (trusted statuses)
  ctx_sector_heat_180d median listing pop of same-broad-sector IPOs, prior 180 days

Status: candidate signals under the locked "evolve-only-if-robust" policy —
verdicts in docs/research/context_signals_verdict.md + rules/index.md.
"""
import bisect
import csv

import pandas as pd

from layer3 import config

TRUSTED = ("ok", "inferred_split", "recovered_bhavcopy")


def _nifty():
    dates, closes = [], []
    with open(config.ROOT / "data/reference/indices/nifty50.csv") as f:
        for r in csv.DictReader(f):
            try:
                dates.append(pd.Timestamp(r["date"]))
                closes.append(float(r["close"]))
            except (ValueError, KeyError):
                continue
    pairs = sorted(zip(dates, closes))
    return [p[0] for p in pairs], [p[1] for p in pairs]


def nifty_mom_3m(listing_ts, _cache={}):
    if "d" not in _cache:
        _cache["d"], _cache["c"] = _nifty()
    d, c = _cache["d"], _cache["c"]

    def at(t):
        i = bisect.bisect_right(d, t) - 1
        return c[i] if i >= 0 else None
    if pd.isna(listing_ts):
        return None
    base = at(listing_ts - pd.Timedelta(days=91))
    now = at(listing_ts)
    return (now / base - 1) if (base and now) else None


def add_context_features(df):
    """Return a copy of df with the ctx_* columns added (vectorized, point-in-time:
    every window ENDS strictly before the row's own listing date)."""
    out = df.copy()
    ld = pd.to_datetime(out["listing_date"], errors="coerce")
    out["_ld"] = ld
    out["ctx_nifty_mom_3m"] = ld.map(nifty_mom_3m)

    pop = pd.to_numeric(out.get("adj_listing_gain_open"), errors="coerce").where(
        out.get("listing_metrics_status").isin(TRUSTED))
    # sort once; windows via searchsorted on the sorted listing dates
    o = out[["_ld"]].assign(pop=pop, type=out["type"], sector=out.get("broad_sector")) \
        .dropna(subset=["_ld"]).sort_values("_ld")
    dates = o["_ld"].tolist()

    def window_stats(row_ld, mask_series, days):
        lo = bisect.bisect_left(dates, row_ld - pd.Timedelta(days=days))
        hi = bisect.bisect_left(dates, row_ld)          # strictly BEFORE this listing
        sl = mask_series.iloc[lo:hi]
        return sl

    heat_n, heat_pop, sector_heat = [], [], []
    for _, r in out.iterrows():
        if pd.isna(r["_ld"]):
            heat_n.append(None); heat_pop.append(None); sector_heat.append(None)
            continue
        seg = window_stats(r["_ld"], o.assign(keep=(o["type"] == r["type"])), 90)
        seg_pops = seg.loc[seg["keep"], "pop"].dropna()
        heat_n.append(int(seg["keep"].sum()))
        heat_pop.append(float(seg_pops.median()) if len(seg_pops) >= 5 else None)
        sec = window_stats(r["_ld"], o.assign(keep=(o["sector"] == r.get("broad_sector"))), 180)
        sec_pops = sec.loc[sec["keep"], "pop"].dropna()
        sector_heat.append(float(sec_pops.median()) if len(sec_pops) >= 5 else None)
    out["ctx_ipo_heat_90d"] = heat_n
    out["ctx_heat_pop_90d"] = heat_pop
    out["ctx_sector_heat_180d"] = sector_heat
    return out.drop(columns=["_ld"])
