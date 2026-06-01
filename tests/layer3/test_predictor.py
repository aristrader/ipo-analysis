import pandas as pd
import pytest
from layer3 import spine, config
from layer3.predictor import analogs, scorecard
from layer3.predictor.predict import predict, format_text


@pytest.fixture(scope="module")
def df():
    return spine.load_substrate()


def test_find_analogs_basic(df):
    q = {"type": "MB", "broad_sector": "Finance", "market_cap_class": "mid",
         "ofs_pct": 0.5, "issue_size_cr": 1000}
    r = analogs.find_analogs(q, df=df, k=40)
    assert r["n_cohort"] >= 1
    assert "analog_distance" in r["cohort"].columns
    # distances sorted ascending, all in [0,1] or NaN
    d = r["cohort"]["analog_distance"].dropna()
    assert (d >= 0).all() and (d <= 1).all()
    assert list(d) == sorted(d)


def test_widening_ladder_relaxes_when_sparse(df):
    # an obscure combo should force the ladder to relax
    q = {"type": "SME", "broad_sector": "Healthcare", "market_cap_class": "large"}
    r = analogs.find_analogs(q, df=df, target_n=30, k=50)
    assert r["rung_idx"] >= 0
    assert r["n_gated"] >= 1


def test_no_self_match(df):
    row = df.iloc[0]
    q = {"type": row["type"], "broad_sector": row.get("broad_sector"),
         "market_cap_class": row.get("market_cap_class"), "isin": row["isin"]}
    r = analogs.find_analogs(q, df=df, exclude_isin=row["isin"])
    assert (r["cohort"]["isin"] != row["isin"]).all()


def test_scorecard_components_and_combined(df):
    q = {"type": "MB", "broad_sector": "Finance", "market_cap_class": "mid",
         "pre_ipo_pat": 1.0, "pre_ipo_roe_pct": 18, "pre_ipo_debt_equity": 0.4}
    r = analogs.find_analogs(q, df=df, k=50)
    sc = scorecard.scorecard(q, r["cohort"], r, profile="balanced")
    assert set(sc["components"]) == {"return_potential", "multibagger_odds",
                                     "downside_safety", "liquidity", "quality", "tradeable_upside"}
    for c in sc["components"].values():
        assert c["score"] is None or (0 <= c["score"] <= 100)
    assert sc["combined_score"] is None or (0 <= sc["combined_score"] <= 100)
    assert sc["confidence"]["label"] in {"high", "medium", "low"}
    # tradeable_upside is weight-0 everywhere (display-only) -> must NOT enter the combined score
    assert all(p["tradeable_upside"] == 0.0 for p in scorecard.PRESETS.values())


def test_quality_uses_query_own_fundamentals():
    good = scorecard.quality({"pre_ipo_pat": 1.0, "pre_ipo_roe_pct": 25, "pre_ipo_debt_equity": 0.1})
    bad = scorecard.quality({"pre_ipo_pat": -1.0, "pre_ipo_roe_pct": 2, "pre_ipo_debt_equity": 2.5})
    assert good["score"] > bad["score"]
    assert scorecard.quality({})["score"] is None   # no fundamentals -> insufficient


def test_predict_end_to_end_and_text(df):
    q = {"type": "MB", "name": "Test Co", "broad_sector": "Finance", "market_cap_class": "mid",
         "ofs_pct": 0.6, "pe_ratio": 28, "pre_ipo_pat": 1.0, "issue_size_cr": 1200}
    r = predict(q, df=df, profile="balanced")
    assert "scorecard" in r and "distribution" in r and len(r["named_analogs"]) >= 1
    txt = format_text(r)
    assert "IPO SCORECARD" in txt and "COMBINED" in txt and "CONFIDENCE" in txt
    assert "NOT a forecast" in txt


def test_risk_assessment_monotone_and_relative(df):
    from layer3.predictor import scorecard
    clean = scorecard.risk_assessment({"type": "SME", "pre_ipo_net_sales": 200, "pre_ipo_pat": 20}, df)
    flagged = scorecard.risk_assessment({"type": "SME", "pre_ipo_net_sales": 8, "pre_ipo_pat": -2}, df)
    # a clean IPO must read lower-risk than a flagged one, and 0-flags must be band LOW
    assert clean["n_flags"] == 0 and clean["risk_band"] == "LOW"
    assert flagged["n_flags"] >= 1
    assert flagged["fail_rate_at_this_flag_load_%"] >= clean["fail_rate_at_this_flag_load_%"]
    # the gauge is relative to the segment base, and per-flag detail shows with-vs-without
    assert clean["segment_base_fail_%"] is not None
    assert all(d["failed_with_flag_%"] is not None for d in flagged["per_flag"])


def test_format_text_renders_with_wipeout_flags(df):
    # regression: a query WITH wipeout flags must render end-to-end (the per-flag loop once clobbered `d`)
    q = {"type": "SME", "name": "Flagged Co", "broad_sector": "Industrials",
         "pre_ipo_net_sales": 8, "pre_ipo_pat": -2, "lead_manager": "Tiny Cap"}
    txt = format_text(predict(q, df=df))
    assert "WIPEOUT-RISK" in txt and "red flag" in txt and "FULL PICTURE" in txt
    assert "WHAT" in txt and "SIMILAR IPOs DID" in txt        # the line that used to crash


def test_risk_assessment_no_inputs_is_not_scored_low(df):
    # blocker fix: a query with NO risk inputs must NOT be labeled LOW/scored (unknown != safe)
    from layer3.predictor import scorecard
    ra = scorecard.risk_assessment({"type": "SME"}, df)
    assert ra.get("insufficient_inputs") is True
    assert ra["risk_band"] is None and ra["risk_score_0_100"] is None
    # but a checked-and-clean query IS allowed a LOW read
    clean = scorecard.risk_assessment({"type": "SME", "pre_ipo_net_sales": 200, "pre_ipo_pat": 20}, df)
    assert clean["risk_band"] == "LOW"
