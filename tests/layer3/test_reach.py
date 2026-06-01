from layer3 import spine


def test_mfe_mae_columns_present():
    df = spine.load_substrate()
    for c in ["mfe_1y", "mae_1y", "mfe_3y", "mae_3y"]:
        assert c in df.columns, f"{c} missing — re-run step 07"


def test_reach_curve_shape_and_monotonicity():
    df = spine.load_substrate()
    rc = spine.reach_curve(df[df["type"] == "MB"], "1y")
    assert rc["n"] > 100
    up = [u["pct_reached"] for u in rc["reach_up"]]
    # higher target → lower (or equal) chance of reaching it (monotone non-increasing)
    assert all(a >= b - 1e-6 for a, b in zip(up, up[1:]))
    # within-horizon peak should exceed the buy-hold endpoint on average
    assert rc["median_peak_pct"] >= (rc["median_endpoint_pct"] or -999)
    # downside ladder: deeper loss → lower chance
    dn = [d["pct_fell_to"] for d in rc["reach_down"]]
    assert all(a >= b - 1e-6 for a, b in zip(dn, dn[1:]))


def test_exit_strategy_both_entries():
    from layer3 import spine
    df = spine.load_substrate(); mb = df[df["type"] == "MB"]
    for entry in ("issue", "listing"):
        es = spine.exit_strategy(mb, entry=entry, horizon="1y")
        assert es["n"] > 100 and 0 <= es["pct_ever_gave_an_exit"] <= 100
        got = [r["pct_got_the_exit"] for r in es["ladder"]]
        assert all(a >= b - 1e-6 for a, b in zip(got, got[1:]))   # tighter target → hit more often
    # secondary buyer always traded >= its listing price at some point (day 1) -> ~100%
    assert spine.exit_strategy(mb, entry="listing")["pct_ever_gave_an_exit"] >= 99


def test_stop_loss_strategy():
    from layer3 import spine
    df = spine.load_substrate(); mb = df[df["type"] == "MB"]
    sl = spine.stop_loss_strategy(mb, entry="listing", horizon="1y")
    assert sl["n"] > 100 and sl["buy_hold_mean_%"] is not None
    pct = [r["pct_stopped_out"] for r in sl["ladder"]]
    assert all(a >= b - 1e-6 for a, b in zip(pct, pct[1:]))   # tighter stop → stopped more often
    for r in sl["ladder"]:
        assert 0 <= r["stopped_but_recovered_%"] <= 100
        assert 0 <= r["stop_saved_%"] <= 100


def test_exit_discipline_backtest_shape():
    from layer3 import spine
    from layer3.backtest import analyses
    t = analyses.exit_discipline_backtest(spine.load_substrate(), "1y")
    assert len(t) > 0
    for c in ["segment", "cohort", "entry", "target", "rule_mean_%", "buy_hold_mean_%", "beats_hold"]:
        assert c in t.columns
    assert t["beats_hold"].dtype == bool


def test_mfe_mae_invariant_holds_on_substrate():
    """Peak >= endpoint >= trough must hold for every row/horizon/entry (the horizon-end price is
    inside the window by definition). Guards the step-09 invariant clamp against regressions."""
    import pandas as pd
    df = spine.load_substrate(equity_only=False)
    viol = 0
    for h in ("1y", "3y", "5y"):
        for mfe, mae, end in [(f"mfe_{h}", f"mae_{h}", f"return_from_issue_{h}"),
                              (f"mfe_lst_{h}", f"mae_lst_{h}", f"return_from_listing_{h}")]:
            m = pd.to_numeric(df[mfe], errors="coerce"); a = pd.to_numeric(df[mae], errors="coerce")
            e = pd.to_numeric(df[end], errors="coerce")
            viol += int(((m < e - 1e-6) & m.notna() & e.notna()).sum())
            viol += int(((a > e + 1e-6) & a.notna() & e.notna()).sum())
    assert viol == 0, f"{viol} peak<endpoint or trough>endpoint violations — step-09 clamp regressed"


def test_outcome_breakdown_buckets_sum_and_fields():
    from layer3 import spine
    df = spine.load_substrate(); mb = spine.segment(df, segment="MB", cohort="boom")
    ob = spine.outcome_breakdown(mb, "3y")
    assert ob["n"] > 30
    s = sum(v for v in ob["horizon_buckets"].values() if v is not None)
    assert 99.0 <= s <= 101.0                      # horizon buckets partition the cohort
    assert ob["best_case_p90_%"] >= ob["base_rate_median_%"] >= ob["worst_case_p10_%"]


def test_wipeout_flags_fire_and_skip():
    from layer3 import spine
    from layer3.predictor import scorecard
    df = spine.load_substrate()
    wf = scorecard.wipeout_flags({"pre_ipo_net_sales": 10, "pre_ipo_pat": -3}, df=df)
    names = [n for n, _ in wf["flags"]]
    assert "tiny pre-IPO sales" in names and "loss-making at IPO" in names
    assert "lead_manager" in wf["unknown"]         # not provided -> reported as unknown, not assumed safe
    clean = scorecard.wipeout_flags({"pre_ipo_net_sales": 500, "pre_ipo_pat": 50}, df=df)
    assert clean["n_flags"] == 0


def test_partial_exit_and_basket_dispersion():
    from layer3 import spine
    g = spine.maturity_gated(spine.segment(spine.load_substrate(), segment="SME", cohort="longterm"), "3y")
    pe = spine.partial_exit_strategy(g, entry="listing", horizon="3y")
    assert pe["n"] > 100 and pe["hold_mean_%"] is not None
    bd = spine.basket_dispersion(g, "3y", entry="listing")
    assert bd["mean_%"] > bd["median_%"]           # right-skew barbell: mean above median


def test_n15_clean_compounder_is_super_additive_cross_regime():
    """Lock in the one validated interaction: low-debt × high-ROE BOTH-cell must beat the base in
    BOTH cohorts (the cross-regime super-additive property that earned it a finding)."""
    from layer3 import spine
    from layer3.findings import n15_clean_compounder as n15
    f = n15.compute(spine.load_substrate())
    df = f.tables[0][1]
    assert len(df) >= 3
    for cohort in ("boom", "longterm"):
        sub = df[df["cohort"] == cohort]
        if not len(sub):
            continue
        # in each cohort at least one segment's BOTH median alpha beats its base
        assert (sub["BOTH_medα_%"] > sub["base_medα_%"]).any(), f"{cohort}: BOTH never beats base"
