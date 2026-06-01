"""N11 — Benchmark divergence: Nifty-50 alpha vs Smallcap-250 alpha (small/micro/SME).

T7 argues small caps should be judged against Smallcap-250, not Nifty-50. Now that alpha_sc_* is
populated (2017+), we make that a hard number: for small/micro caps + SME, show median alpha (vs
Nifty50) MINUS median alpha_sc (vs Smallcap250) per horizon. A large positive gap = the apparent
'outperformance' is really just small-cap beta, and evaporates against the right benchmark.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding


def _rows(sub, label):
    rows = []
    for h in ["1y", "3y"]:
        gn = spine.maturity_gated(sub, h)
        a_n = spine.alpha_series(gn, h, "nifty")
        a_s = spine.alpha_series(gn, h, "smallcap")
        both = pd.DataFrame({"n": a_n, "s": a_s}).dropna()
        if len(both) < config.MIN_N_HINT:
            rows.append({"group": label, "horizon": h, "N": len(both)})
            continue
        rows.append({"group": label, "horizon": h, "N": len(both),
                     "median_alpha_nifty_%": _p(both["n"].median()),
                     "median_alpha_smallcap_%": _p(both["s"].median()),
                     "divergence_pp": _p(both["n"].median() - both["s"].median())})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    sm = df["market_cap_class"].isin(["micro", "small"])
    rows += _rows(df[sm & (df["type"] == "MB")], "small/micro MB")     # never pool MB+SME
    rows += _rows(df[sm & (df["type"] == "SME")], "small/micro SME")
    rows += _rows(df[df["type"] == "SME"], "all SME")
    rows += _rows(df[df["type"] == "MB"], "all Mainboard (control)")
    tables.append(("Nifty-50 alpha vs Smallcap-250 alpha (2017+ coverage). A large POSITIVE divergence means the "
                   "Nifty-measured 'alpha' is mostly small-cap beta — it shrinks against the proper benchmark. "
                   "Mainboard shown as a control (should diverge little).", pd.DataFrame(rows)))
    caveats += [
        "alpha_sc (Smallcap-250) covers listings 2017+ only, so this is a boom-leaning comparison; N is the "
        "both-benchmarks-available count.",
        "Use-case: for small/micro/SME, the Smallcap-250 figure is the fairer 'did it beat its peer universe' read; "
        "the Nifty figure flatters them in small-cap bull runs.",
        "Mainboard divergence should be small (they're closer to the Nifty universe) — a sanity control.",
    ]
    narrative = ("Small-cap IPOs can look like they 'beat the market' simply because small-caps as a class ran hot. "
                 "Now that we have Smallcap-250 alpha, we show the gap: how much of the Nifty-measured outperformance "
                 "survives when you benchmark small caps against actual small caps. A big gap = borrowed beta, not skill.")
    return Finding(id="n11", title="N11 · Benchmark divergence (Nifty-50 vs Smallcap-250)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
