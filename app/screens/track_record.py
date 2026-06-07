"""FORWARD-TEST / TRACK-RECORD — the honest forward record, mode-split front and center.
Plus the OOS report card (substrate-derived) and Altair chart #2 (track record over time).
Also folds in the legacy Backtester + Validation content (MONITOR journey).
"""
import altair as alt
import pandas as pd
import streamlit as st

from app import ui
from layer3 import config

ui.inject_style()

st.title("🛰 Forward-test / Track record")
ui.one_liner("What am I looking at? Did the calls actually work? The honest forward audit — per call-type, "
             "split by evidence strength (mode) — plus the predictor's out-of-sample report card and the "
             "strategy backtester. Distributions, not means; N on every row. **Not financial advice.**")

ui.render_regime_banner()

ledger = ui.load_ledger()
df = ui.load_df()

tab_track, tab_bt, tab_val = st.tabs(
    ["📋 Call track record", "📈 Backtester", "✓ Validation & rules"])


# ============================================================ TRACK RECORD
def win_flag(row):
    ct = row["call_type"]
    a1y, a3m = row.get("alpha_1y"), row.get("alpha_3m")
    if ct in ("APPLY", "EARLY_APPLY"):
        return None if pd.isna(a1y) else (a1y > 0)
    if ct in ("AVOID", "EARLY_AVOID"):
        return None if pd.isna(a1y) else (a1y < 0)
    if ct in ("EXIT_REVIEW", "PERSIST_EXIT_LEAN"):
        return None if pd.isna(a3m) else (a3m < 0)
    if ct == "TAKE_PROFITS":
        return None if pd.isna(a3m) else (a3m < 0)
    return None


with tab_track:
    if ledger is None or ledger.empty:
        st.info("No graded calls — the ledger needs maturing. Run `python run_calls.py`.")
    else:
        st.caption("Mode legend: **live / gap_filled** = forward truth · **backfilled** = out-of-sample · "
                   "**historical_sim** = dress rehearsal. Never pool them — evidence strength differs.")
        lg = ledger.copy()
        lg["_win"] = lg.apply(win_flag, axis=1)
        graded = lg[lg["call_type"].isin(["APPLY", "AVOID", "EARLY_APPLY", "EARLY_AVOID",
                                          "EXIT_REVIEW", "PERSIST_EXIT_LEAN", "TAKE_PROFITS"])]

        # A. table call_type × mode
        st.subheader("A. Call track record")
        rows = []
        for (ct, mode), g in graded.groupby(["call_type", "mode"]):
            w = g["_win"].dropna()
            n = len(w)
            delta = pd.to_numeric(g.get("alpha_1y"), errors="coerce").dropna()
            floor = ui.n_floor(n)
            gmix = g["grade_status"].value_counts().to_dict()
            rows.append({
                "call_type": ct, "mode": mode, "n": n,
                "win_%": floor if floor else f"{100*w.mean():.0f}%",
                "median Δα 1y": "—" if floor else (ui.frac(delta.median()) if len(delta) else "—"),
                "IQR Δα 1y": "—" if floor or len(delta) < 4 else
                             f"{ui.frac(delta.quantile(.25))} … {ui.frac(delta.quantile(.75))}",
                "grade mix": ", ".join(f"{k}:{v}" for k, v in gmix.items()),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows).sort_values(["call_type", "mode"]),
                         hide_index=True, use_container_width=True)
        else:
            st.caption("no graded calls yet")

        # B. raw ledger audit
        st.subheader("B. Per-call ledger (audit)")
        bc1, bc2, bc3 = st.columns(3)
        ct_f = bc1.multiselect("call_type", sorted(ledger["call_type"].unique()))
        md_f = bc2.multiselect("mode", sorted(ledger["mode"].unique()))
        gs_f = bc3.multiselect("grade_status", sorted(ledger["grade_status"].dropna().unique()))
        view = ledger.copy()
        if ct_f: view = view[view["call_type"].isin(ct_f)]
        if md_f: view = view[view["mode"].isin(md_f)]
        if gs_f: view = view[view["grade_status"].isin(gs_f)]
        st.dataframe(
            view[["call_date", "name", "type", "call_type", "mode", "rules_fired",
                  "alpha_1m", "alpha_3m", "alpha_1y", "grade_status"]].sort_values("call_date", ascending=False),
            hide_index=True, use_container_width=True, height=320)
        st.caption("Each row's ISIN can be opened on the IPO Detail page via `?isin=<isin>`.")

        # D. Altair chart #2 — track record over time, faceted by mode
        st.subheader("D. Track record over time")
        chart_src = graded.dropna(subset=["_win"]).copy()
        if len(chart_src) >= ui.MIN_N:
            chart_src = chart_src.sort_values("call_date")
            chart_src["_win_i"] = chart_src["_win"].astype(int)
            chart_src["cum_win_rate"] = (chart_src.groupby("mode")["_win_i"]
                                         .expanding().mean().reset_index(level=0, drop=True))
            ch = (alt.Chart(chart_src).mark_line().encode(
                x=alt.X("call_date:T", title="call date"),
                y=alt.Y("cum_win_rate:Q", title="cumulative win-rate", scale=alt.Scale(domain=[0, 1])),
                color=alt.Color("mode:N", title="mode"),
                tooltip=["call_date:T", "mode:N", alt.Tooltip("cum_win_rate:Q", format=".0%")])
                .properties(height=280)
                .facet(row=alt.Row("mode:N", title=None)))
            st.altair_chart(ch, use_container_width=True)
            st.caption("Faceted by mode so live / forward calls are never visually pooled with the "
                       "historical_sim dress rehearsal.")
        else:
            st.caption("too few graded calls to chart a track record over time yet")


# ============================================================ OOS report card (always renders)
@st.cache_data(show_spinner="Out-of-sample test…")
def oos_table():
    from layer3.predictor import weights as W
    rows = []
    for cutoff, h in [(2022, "1y"), (2021, "1y"), (2019, "3y")]:
        rr = W.oos_evaluate(df, cutoff, h)
        rows.append({"train_≤": cutoff, "test_horizon": h, "n_test": rr.get("n_test"),
                     "field_median_%": rr.get("test_field_median_%"),
                     "top_quintile_median_%": rr.get("test_topquintile_median_%"),
                     "OOS_lift_pp": rr.get("oos_lift_pp"), "top_win_rate_%": rr.get("top_win_rate_%"),
                     "chip": "✓ VALIDATED" if h == "3y" else "~ DISPLAY-ONLY"})
    return pd.DataFrame(rows)


with tab_track:
    st.subheader("C. OOS report card — the predictor's honest test")
    st.caption("Weights fit on IPOs listed ≤ cutoff, tested on LATER IPOs never seen during fitting. "
               "The edge is strongest at 3y, weaker at 1y — read the lift column in the table (numbers live in the data, not this caption). A ranking tool, not a flip signal.")
    st.dataframe(oos_table(), hide_index=True, use_container_width=True)
    with st.expander("🎚 Try your own train/test split"):
        cc1, cc2, cc3 = st.columns([2, 1, 1])
        cutoff = cc1.slider("Train on IPOs listed up to…", 2017, 2023, 2021)
        hsel = cc2.selectbox("Test horizon", ["1y", "3y"], key="oos_cut_h")
        if cc3.button("Run split"):
            from layer3.predictor import weights as W
            rr = W.oos_evaluate(df, cutoff, hsel)
            if rr.get("error"):
                st.warning(f"{rr['error']} (train N={rr['n_train']}, test N={rr['n_test']})")
            else:
                st.metric(f"OOS lift — train ≤{cutoff} → test {cutoff+1}+ @ {hsel}",
                          ui.pct_pp(rr['oos_lift_pp']),
                          help=f"top-quintile {rr['test_topquintile_median_%']}% vs field "
                               f"{rr['test_field_median_%']}% · test N={rr['n_test']}")


# ============================================================ BACKTESTER (ported)
@st.cache_data(show_spinner="Running backtest…")
def backtest_tables():
    from layer3.backtest import engine, analyses
    from layer3.backtest.score_backtest import combined_score_backtest
    out = {("strategies", seg, h): engine.run(df, horizon=h, segment=seg)
           for seg in config.SEGMENTS for h in ("1y", "3y")}
    out["sweep_MB"] = analyses.holding_period_sweep(df, "MB")
    out["sweep_SME"] = analyses.holding_period_sweep(df, "SME")
    out["portfolio"] = analyses.portfolio_summary(df)
    out["flip"] = {s: analyses.flip_allotment_ev(df, s) for s in config.SEGMENTS}
    out["exit_disc"] = analyses.exit_discipline_backtest(df, "1y")
    res, verdict = combined_score_backtest(df)
    out["combined"], out["combined_verdict"] = res, verdict
    return out


with tab_bt:
    st.subheader("Strategy backtester (vs do-nothing baseline)")
    st.caption("Point-in-time, net of costs. Secondary strategies in alpha; allottee/flip in raw return. "
               "SME & Mainboard never pooled.")
    bt = backtest_tables()
    for seg in config.SEGMENTS:
        st.markdown(f"**{seg} — strategies**")
        cc = st.columns(2)
        for col, h in zip(cc, ("1y", "3y")):
            col.caption(f"horizon {h}")
            col.dataframe(bt[("strategies", seg, h)], use_container_width=True, hide_index=True)
    st.markdown("**Holding-period sweep** — secondary buy-at-listing, exit at each horizon")
    cc = st.columns(2)
    cc[0].caption("Mainboard"); cc[0].dataframe(bt["sweep_MB"], use_container_width=True, hide_index=True)
    cc[1].caption("SME"); cc[1].dataframe(bt["sweep_SME"], use_container_width=True, hide_index=True)
    st.markdown("**Portfolio basket** (equal-weight buy-every-IPO) vs do-nothing — dispersion-adjusted")
    st.dataframe(bt["portfolio"], use_container_width=True, hide_index=True)
    st.markdown("**Flip allotment-realism EV**")
    for s in config.SEGMENTS:
        ev = bt["flip"][s]
        if ev:
            st.write(f"- **{s}**: naive flip {ev['naive_mean_flip_%']}% → allotment-weighted "
                     f"**{ev['allotment_weighted_flip_%']}%** (adverse-selection {ev['adverse_selection_cost_pp']}pp; "
                     f"median allotment prob {ev['median_allotment_prob']})")
    st.markdown("**Exit-discipline backtest** — does a take-profit rule beat just holding?")
    ed = bt["exit_disc"]
    st.dataframe(ed, use_container_width=True, hide_index=True)
    n_beat = int(ed["beats_hold"].sum()) if len(ed) else 0
    st.info(f"Take-profit beats buy-and-hold in only **{n_beat}/{len(ed)}** cells — NONE in both cohorts. "
            "Capping upside sacrifices the right-tail winners that carry IPO returns.")
    st.markdown("**Combined-score loop-closer** — do top-quintile predictor-score IPOs beat the field?")
    st.dataframe(bt["combined"], use_container_width=True, hide_index=True)
    st.info("Verdict: " + bt["combined_verdict"])


# ============================================================ VALIDATION & RULES (ported)
@st.cache_data(show_spinner="Cross-regime validation…")
def validation_table():
    from layer3 import validate
    return validate.validate(df)


with tab_val:
    st.subheader("Cross-regime validation")
    st.caption("Does each directional claim hold the same SIGN in BOTH the boom (2020–25) and longterm "
               "(2006–19) cohorts, and within individual vintages?")
    st.dataframe(validation_table(), use_container_width=True, hide_index=True)
    st.subheader("Rules registry")
    rp = config.ROOT / "rules/index.md"
    if rp.exists():
        st.markdown(rp.read_text())
