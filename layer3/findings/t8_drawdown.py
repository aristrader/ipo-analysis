"""T8 — Drawdown-tax pain map (for eventual winners).

For IPOs that ended up winners/multibaggers: the maximum drawdown + its duration they made
holders endure en route ("it triples, but you eat −60% for 8 months first"). Descriptive and
robust. Per segment; an investable-liquidity subset shown to separate real pain from thin-trade
artifacts.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

WINNERS = ["winner", "multibagger"]


def _rows(sub):
    rows = []
    for seg in config.SEGMENTS:
        g = sub[(sub["type"] == seg) & (sub["outcome_class"].isin(WINNERS))]
        dd = pd.to_numeric(g["max_drawdown_pct"], errors="coerce").dropna()
        dur = pd.to_numeric(g["max_drawdown_duration_days"], errors="coerce").dropna()
        d = spine.distribution(dd)
        rows.append({"segment": seg, "N_winners": len(g),
                     "median_max_drawdown_%": _p(d["median"]),
                     "deepest_decile_drawdown_%": _p(d["p10"]),   # p10 of dd = the deepest tenth (dd is negative)
                     "median_drawdown_duration_days": int(dur.median()) if len(dur) else None,
                     "pct_endured_>50%_dd": _p((dd <= -0.50).mean() if len(dd) else None)})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    tables.append(("Among EVENTUAL winners/multibaggers: the max drawdown they made you survive first, by segment. "
                   "Even the winners demand stomach.", pd.DataFrame(_rows(df))))
    tables.append(("Same, INVESTABLE subset only (liquidity_flag ok) — strips thin-trade drawdown artifacts.",
                   pd.DataFrame(_rows(spine.investable(df)))))

    # FORWARD recovery mirror (mv-T8-recovery): NO winner look-ahead. Among names that hit a deep
    # trough (MAE) within the horizon, what share RECOVERED to break-even / +20% by the horizon end?
    rec = []
    for seg in config.SEGMENTS:
        g = spine.maturity_gated(spine.segment(df, segment=seg, cohort="boom"), "1y")
        for entry, elab in [("issue", "allottee"), ("listing", "secondary")]:
            s = g
            if entry == "listing" and "listing_metrics_status" in s.columns:
                s = s[s["listing_metrics_status"] != "unreliable_coverage"]
            mae_c, _, end_c = spine._entry_cols(entry, "1y")  # MAE col, endpoint col
            mae_c = mae_c.replace("mfe", "mae")
            mae = pd.to_numeric(s.get(mae_c), errors="coerce")
            end = pd.to_numeric(s.get(end_c), errors="coerce")
            for thr in (-0.30, -0.50):
                deep = s[(mae <= thr) & end.notna()]
                e = pd.to_numeric(deep.get(end_c), errors="coerce").dropna()
                if len(e) < config.MIN_N_HINT:
                    continue
                rec.append({"segment": seg, "entry": elab, "hit_trough": "≤%d%%" % round(thr * 100),
                            "N": len(e),
                            "recovered_to_breakeven_%": _p((e > 0).mean()),
                            "recovered_to_+20%_%": _p((e > 0.20).mean()),
                            "median_endpoint_%": _p(e.median())})
    tables.append(("FORWARD recovery (boom, 1y, maturity-gated — no winner look-ahead): among names that fell to a "
                   "deep trough WITHIN the year, the share that still ENDED the year at break-even / +20%. The "
                   "optimist's mirror of the pain map — and the honest case against a tight stop-loss.",
                   pd.DataFrame(rec)))

    from layer3 import charts as ch
    g = df[(df["type"] == "MB") & (df["outcome_class"].isin(WINNERS))]
    dd = pd.to_numeric(g["max_drawdown_pct"], errors="coerce").dropna() * 100
    if len(dd):
        charts.append(("Mainboard eventual-winners: distribution of the worst drawdown endured en route",
                       ch.hist_png(dd.tolist(), bins=25,
                                   title="MB winners: max drawdown endured", xlabel="max drawdown %")))

    caveats += [
        "Winners defined by lifetime outcome_class (raw return) — this is intentionally the 'did it end up a winner' "
        "set; the point is the pain en route, not a forward prediction.",
        "SME drawdowns can be liquidity artifacts (gaps/circuit); compare the full vs investable tables.",
        "Drawdown is on split/bonus-adjusted close.",
        "The FORWARD recovery table is maturity-gated and forward (no winner look-ahead) — it answers 'if it "
        "dipped deep, did it come back by year-end', which is exactly the question a stop-loss decision turns on. "
        "Recovery here = the endpoint was back above the line; it does NOT mean the dip came before the recovery "
        "(MFE/MAE give magnitude, not order). Boom cohort for cleaner entry coverage.",
    ]
    narrative = ("Even the IPOs that eventually win make you suffer first. For eventual winners and multibaggers we "
                 "map the deepest drawdown — and how long it lasted — that a holder had to survive to collect the "
                 "win. This tells you what conviction the upside actually required.")
    return Finding(id="t8", title="T8 · Drawdown-tax pain map",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
