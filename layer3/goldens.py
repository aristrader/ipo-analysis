"""GOLDEN headline numbers — ONE computation used by three consumers:
  * tests/data/test_headline_numbers.py  (assert current computation ≈ accepted JSON)
  * tools/refresh/derive_goldens.py      (re-derive + overwrite the JSON, printing OLD → NEW)
  * run_refresh.py --apply               (calls the derive tool as a phase)

The accepted values live in data/reference/golden_numbers.json — a DATA file, so a
refresh updates the rails without editing source. Tolerances are per-key absolute.
"""
import json

import pandas as pd

from layer3 import config, spine

GOLDEN_PATH = config.ROOT / "data/reference/golden_numbers.json"


def compute(df=None):
    """Re-derive every golden from the current substrate. Returns {key: value}."""
    if df is None:
        df = spine.load_substrate()
    mb_boom = spine.segment(df, segment="MB", cohort="boom")
    sme_boom = spine.segment(df, segment="SME", cohort="boom")
    mb_lt = spine.segment(df, segment="MB", cohort="longterm")
    g1 = spine.maturity_gated(mb_boom, "1y")
    pop = pd.to_numeric(
        mb_boom[mb_boom["listing_metrics_status"] != "unreliable_coverage"]["adj_listing_gain_open"],
        errors="coerce")
    g3 = spine.maturity_gated(mb_lt, "3y")
    mfe3 = pd.to_numeric(g3.get("mfe_lst_3y"), errors="coerce").dropna()
    wb = spine.wipeout_band(mb_lt)
    return {
        "equity_rows": int(len(df)),
        "mb_boom_n": int(len(mb_boom)),
        "sme_boom_n": int(len(sme_boom)),
        "mb_longterm_n": int(len(mb_lt)),
        "mb_boom_1y_matured_n": int(len(g1)),
        "mb_boom_1y_median_alpha": float(spine.alpha_series(g1, "1y").median()),
        "mb_longterm_wipeout_lower_rate": float(wb["wipeout_lower_rate"]),
        "mb_boom_median_listing_pop": float(pop.median()),
        "mb_longterm_ever2x_3y_rate": float((mfe3 >= 1.0).mean()),
        "mb_longterm_ever2x_3y_n": int(len(mfe3)),
    }


# absolute tolerance per key when ASSERTING (counts are exact; rates get float headroom)
TOLERANCES = {k: 0 for k in ("equity_rows", "mb_boom_n", "sme_boom_n", "mb_longterm_n",
                             "mb_boom_1y_matured_n", "mb_longterm_ever2x_3y_n")}
TOLERANCES.update({k: 1e-4 for k in ("mb_boom_1y_median_alpha", "mb_longterm_wipeout_lower_rate",
                                     "mb_boom_median_listing_pop", "mb_longterm_ever2x_3y_rate")})


def load_accepted():
    return json.loads(GOLDEN_PATH.read_text())["values"]


def save_accepted(values, note=""):
    GOLDEN_PATH.write_text(json.dumps(
        {"note": note or "accepted golden numbers — rewritten only by the refresh/derive tool",
         "derived_as_of": str(config.AS_OF_DATE), "values": values}, indent=1))
