"""T2 — Competing-risks survival / wipeout curve.

Cumulative wipeout probability by years-since-listing, maturity-gated each year (only IPOs
old enough to have reached that year count toward its denominator). Wipeout is a BAND
(reasons are sparse). NO monotonicity assumption — maturity-gating changes the denominator
each year, so the pooled rate need not be monotone (methodology fix #4).
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

TODAY = config.AS_OF_DATE          # one canonical as-of date (consistent with the substrate's gating)
YEARS = [1, 2, 3, 5, 7, 10]


def _age_years(listing_date):
    d = pd.to_datetime(listing_date, errors="coerce")
    if pd.isna(d):
        return None
    return (pd.Timestamp(TODAY) - d).days / 365.25


def compute(df):
    tables, charts, caveats = [], [], []
    d = df.copy()
    d["age_y"] = d["listing_date"].map(_age_years)
    term = spine.terminal_state(d)
    d["is_wipeout"] = (term == "wipeout")
    d["is_unknown_delist"] = (term == "alive_delisted_unknown")

    rows = []
    for seg in config.SEGMENTS:
        sub = d[d["type"] == seg]
        for y in YEARS:
            at_risk = sub[sub["age_y"] >= y]              # matured to year y
            n = len(at_risk)
            low = int(at_risk["is_wipeout"].sum())
            up = low + int(at_risk["is_unknown_delist"].sum())
            rows.append({"segment": seg, "year": y, "N_listed_ge_y": n,
                         "ever_wiped_lower_%": _p(low / n if n else None),
                         "ever_wiped_upper_%": _p(up / n if n else None)})
    tbl = pd.DataFrame(rows)
    tables.append(("Share EVER wiped out among IPOs that have been listed at least Y years (NOT a point-in-time "
                   "hazard — we have no delist-date, so a wipeout counts in every year-bucket it qualifies for). "
                   "Band: lower = confirmed, upper adds delisted-unknown-reason.", tbl))

    # chart: lower-bound cumulative wipeout by year, MB vs SME
    from layer3 import charts as ch
    series = {}
    for seg in config.SEGMENTS:
        ys, ns = [], []
        s = tbl[tbl["segment"] == seg]
        for y in YEARS:
            r = s[s["year"] == y]
            v = r["ever_wiped_lower_%"].iloc[0] if len(r) else None
            ys.append(v if v is not None else 0)
        series[seg] = ys
    charts.append(("Share ever-wiped-out (lower bound) among IPOs listed ≥ Y years — MB vs SME",
                   ch.line_png(YEARS, series, title="Ever-wiped-out by years-listed (lower bound)",
                               ylabel="ever-wiped-out %", xlabel="min years since listing")))

    caveats += [
        "⚠ SME wipeout reads LOWER than Mainboard, but this is likely a SURVIVORSHIP ARTIFACT: ~50% of SME is "
        "low-liquidity (vs ~10% of MB), so a dead-but-stale SME often never prints a −90% terminal price and is "
        "not captured as a wipeout. Read SME downside as an UNDER-count; the upper band is closer to reality.",
        "Wipeout = outcome_class 'wipeout' (≈ −100%) OR delist reason Compulsory/Liquidation. Upper bound adds "
        "delisted-with-unknown-reason (some of which are voluntary buyouts = winners leaving, not wipeouts).",
        "No delist-date exists, so this is 'ever wiped out among IPOs ≥Y years listed', not a true per-year hazard "
        "— don't read the slope as a hazard rate. Voluntary delisting (payout) is tracked separately, not as wipeout.",
    ]
    narrative = ("Among IPOs that have been listed at least N years, what share have been wiped out (≈ total loss) — "
                 "the survivorship-honest downside, split MB vs SME, as a band (we have an explicit delisting reason "
                 "for only a minority). NOTE the SME figure is an under-count (see caveat).")
    return Finding(id="t2", title="T2 · Competing-risks survival / wipeout",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
