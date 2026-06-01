"""T6 — Sector alpha × survival × multibagger matrix (predictor backbone).

Per broad_sector: median long-horizon alpha + multibagger rate + WIPEOUT rate together — a
sector great on returns but high on hidden death is the key insight. Computed on the LONGTERM
cohort (matured outcomes + good sector coverage); boom sector (now ~94% MB coverage) is too
young for a 5y matrix and is flagged for the predictor instead. Per segment; low-N sectors
suppressed by the report's N-guard.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _sector_rows(sub, horizon):
    rows = []
    for sec, g in sub.groupby("broad_sector"):
        gm = spine.maturity_gated(g, horizon)
        a = spine.alpha_series(gm, horizon)
        rfi = pd.to_numeric(gm.get(f"return_from_issue_{horizon}"), errors="coerce").dropna()
        wb = spine.wipeout_band(g)
        rows.append({"broad_sector": sec, "N": len(g), "N_matured": len(gm),
                     f"median_alpha_{horizon}_%": _p(spine.distribution(a)["median"]),
                     "pct_2x": _p(spine.proportion(rfi >= 1.0)["rate"]),
                     "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                     "wipeout_upper_%": _p(wb["wipeout_upper_rate"])})
    return sorted(rows, key=lambda r: (r[f"median_alpha_{horizon}_%"] is None,
                                       -(r.get(f"median_alpha_{horizon}_%") or -1e9)))


def compute(df):
    tables, charts, caveats = [], [], []
    longt = spine.segment(df, cohort="longterm")
    longt = longt[longt["broad_sector"].notna()]

    for seg in config.SEGMENTS:
        sub = longt[longt["type"] == seg]
        if len(sub) < config.MIN_N_HINT:
            continue
        tables.append((f"{seg} sector matrix (longterm cohort, 5y): median alpha + 2x-rate + wipeout band "
                       f"together. Sectors with N<10 are suppressed.",
                       pd.DataFrame(_sector_rows(sub, "5y"))))

    # scatter: sector median 5y alpha (x) vs wipeout lower-rate (y), bubble = N — longterm MB+SME pooled view
    from layer3 import charts as ch
    secrows = _sector_rows(longt, "5y")
    secrows = [r for r in secrows if r["N"] >= config.MIN_N_HINT and r["median_alpha_5y_%"] is not None]
    if secrows:
        charts.append(("Sector landscape (longterm): median 5y alpha vs wipeout rate (bubble = N). "
                       "Top-left = high return + low death; bottom-right = the landmines.",
                       ch.scatter_png([r["median_alpha_5y_%"] for r in secrows],
                                      [r["wipeout_lower_%"] for r in secrows],
                                      sizes=[r["N"] for r in secrows],
                                      labels=[str(r["broad_sector"])[:14] for r in secrows],
                                      title="Sector: 5y alpha vs wipeout rate",
                                      xlabel="median 5y alpha %", ylabel="wipeout % (lower)")))

    # boom coverage note table (so the reader knows boom sector exists for the predictor)
    boom = spine.segment(df, cohort="boom")
    tables.append(("Boom-cohort sector coverage (for the predictor; too young for a 5y matrix here).",
                   pd.DataFrame([{"segment": s, "N": len(boom[boom.type == s]),
                                  "pct_with_sector": _p(boom[boom.type == s]["broad_sector"].notna().mean())}
                                 for s in config.SEGMENTS])))

    caveats += [
        "Matrix is on the LONGTERM cohort (matured 5y outcomes + good sector coverage). Boom sector is now ~94% "
        "for mainboard but too young for a 5y base rate — used by the predictor, not shown as a matrix here.",
        "Wipeout is a band (sparse delist reasons). A sector can look good on alpha yet hide a high death rate.",
        "broad_sector is screener-sourced; sectors below the N floor are suppressed, not shown as noise.",
    ]
    narrative = ("Which industries actually produce lasting winners — and which are landmines? For each sector we "
                 "show median 5-year alpha, the 2x-rate, AND the wipeout rate together, because a sector that looks "
                 "great on returns can hide a high death rate. This is the backbone the predictor leans on for "
                 "sector context.")
    return Finding(id="t6", title="T6 · Sector alpha × survival matrix",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return None if (x is None or pd.isna(x)) else round(100 * x, 1)
