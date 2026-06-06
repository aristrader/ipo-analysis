"""Context features: computable + point-in-time (a row never sees its own pop)."""
import pandas as pd
from layer3 import context, spine


def test_context_features_compute_on_substrate_sample():
    df = spine.load_substrate().head(300)
    out = context.add_context_features(df)
    for c in ("ctx_nifty_mom_3m", "ctx_ipo_heat_90d", "ctx_heat_pop_90d", "ctx_sector_heat_180d"):
        assert c in out.columns
    assert pd.to_numeric(out["ctx_nifty_mom_3m"], errors="coerce").notna().sum() > 200


def test_heat_window_excludes_own_listing_day():
    df = pd.DataFrame({"isin": ["A", "B"], "type": ["MB", "MB"],
                       "listing_date": ["2021-01-01", "2021-01-01"],
                       "adj_listing_gain_open": [0.5, 0.5],
                       "listing_metrics_status": ["ok", "ok"], "broad_sector": ["X", "X"]})
    out = context.add_context_features(df)
    # same-day listings must NOT count each other (window is strictly before)
    assert (out["ctx_ipo_heat_90d"] == 0).all()
