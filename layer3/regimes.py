"""Market-regime features at a date (POINT-IN-TIME, Nifty-based).

Standardized per docs/research/phase2_playbooks.md (regime families):
  dir60  — trailing 60-trading-day Nifty return (direction axis)
  vol20  — 20-day realized vol, annualized (volatility axis)
  phase  — distance from trailing 252-day high (cycle-phase axis; <=0)

All computed strictly from Nifty closes ON OR BEFORE the date. Used by the
Phase-2 regime tests (F3/F4/T2*) and available to the app's regime dashboard.
"""
import bisect
import csv
import math

import pandas as pd

from layer3 import config

_CACHE = {}


def _nifty():
    if "d" in _CACHE:
        return _CACHE["d"], _CACHE["c"]
    dates, closes = [], []
    with open(config.ROOT / "data/reference/indices/nifty50.csv") as f:
        for r in csv.DictReader(f):
            try:
                dates.append(pd.Timestamp(r["date"]))
                closes.append(float(r["close"]))
            except (ValueError, KeyError):
                continue
    pairs = sorted(zip(dates, closes))
    _CACHE["d"] = [p[0] for p in pairs]
    _CACHE["c"] = [p[1] for p in pairs]
    return _CACHE["d"], _CACHE["c"]


def regime_at(ts):
    """{dir60, vol20, phase} at timestamp ts (None fields where history is short)."""
    if pd.isna(ts):
        return {"dir60": None, "vol20": None, "phase": None}
    d, c = _nifty()
    i = bisect.bisect_right(d, ts) - 1          # last trading day <= ts
    if i < 0:
        return {"dir60": None, "vol20": None, "phase": None}
    out = {}
    out["dir60"] = (c[i] / c[i - 60] - 1) if i >= 60 else None
    if i >= 20:
        rets = [math.log(c[j] / c[j - 1]) for j in range(i - 19, i + 1)]
        mu = sum(rets) / len(rets)
        var = sum((r - mu) ** 2 for r in rets) / (len(rets) - 1)
        out["vol20"] = math.sqrt(var) * math.sqrt(252)
    else:
        out["vol20"] = None
    lo = max(0, i - 252)
    hi252 = max(c[lo:i + 1])
    out["phase"] = c[i] / hi252 - 1
    return out


def add_regime_features(df, date_col="listing_date"):
    """Copy of df with dir60/vol20/phase columns + tercile labels (cohort-separate cuts,
    per the spec, to avoid cross-era leakage)."""
    out = df.copy()
    ld = pd.to_datetime(out[date_col], errors="coerce")
    feats = ld.map(regime_at)
    for k in ("dir60", "vol20", "phase"):
        out[k] = feats.map(lambda f: f[k])
    # tercile labels within cohort
    for k in ("dir60", "vol20"):
        out[f"{k}_t"] = None
        for coh, g in out.groupby("cohort"):
            s = pd.to_numeric(g[k], errors="coerce")
            try:
                out.loc[g.index, f"{k}_t"] = pd.qcut(s, 3, labels=["lo", "mid", "hi"], duplicates="drop")
            except ValueError:
                pass
    out["phase_bin"] = pd.cut(pd.to_numeric(out["phase"], errors="coerce"),
                              [-1.0, -0.12, -0.03, 0.01], labels=["correction", "mid", "at_high"])
    return out
