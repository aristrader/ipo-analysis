"""IPO Analysis — Streamlit app (Layer 3 front-end).

A thin UI over the existing engine: the descriptive report, the analog predictor (score a new IPO),
the strategy backtester, and the cross-regime validation + rules registry. The engine is
UI-agnostic; this file only calls it and renders. Run:

    source .venv/bin/activate
    PYTHONPATH=. streamlit run app.py
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from layer3 import spine, config, validate
from layer3.predictor import analogs
from layer3.predictor.predict import predict, format_text
from layer3.backtest import engine, analyses
from layer3.backtest.score_backtest import combined_score_backtest

st.set_page_config(page_title="Indian IPO Analysis", layout="wide", page_icon="📈")
ROOT = config.ROOT


def _p(x):           # x is a fraction (0.12 -> +12%)
    return "—" if x is None else f"{100*x:+.0f}%"


def _pp(x):          # x is already a percent (12.0 -> +12%)
    return "—" if x is None else f"{x:+.0f}%"


@st.cache_data(show_spinner=False)
def load_df(exclude_low_quality=False):
    return spine.load_substrate(exclude_low_quality=exclude_low_quality)


@st.cache_data(show_spinner=False)
def sectors():
    return sorted(load_df()["broad_sector"].dropna().unique())


@st.cache_data(show_spinner="Running backtest…")
def backtest_tables():
    df = load_df()
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


@st.cache_data(show_spinner="Cross-regime validation…")
def validation_table():
    return validate.validate(load_df())


@st.cache_data(show_spinner="Out-of-sample test…")
def oos_table():
    from layer3.predictor import weights as W
    df = load_df()
    rows = []
    for cutoff, h in [(2022, "1y"), (2021, "1y"), (2019, "3y")]:
        r = W.oos_evaluate(df, cutoff, h)
        rows.append({"train_≤": cutoff, "test_horizon": h, "n_test": r.get("n_test"),
                     "field_median_%": r.get("test_field_median_%"),
                     "top_quintile_median_%": r.get("test_topquintile_median_%"),
                     "OOS_lift_pp": r.get("oos_lift_pp"), "top_win_rate_%": r.get("top_win_rate_%")})
    return pd.DataFrame(rows)


with st.sidebar:
    st.header("📈 IPO Analysis")
    st.markdown("Research over **~2,296 Indian IPOs** (2006–2025, Mainboard + SME, incl. delisted). Free data only.")
    st.markdown("**How to read it**")
    st.markdown("- **alpha** = your return *minus the market* (Nifty 50), measured from the **listing price** "
                "(what a public buyer actually pays). Positive = beat the market.\n"
                "- **SME and Mainboard are never mixed** — they behave very differently.\n"
                "- Every number shows **N** (how many IPOs it's based on); thin samples are hidden, not faked.")
    st.warning("⚠ The **predictor score** is a transparent *ranking* (in-sample / indicative) — **not** a proven "
               "money-maker. The **descriptive findings** are the solid, fact-based part.")
    excl_lq = st.toggle("Exclude low-data-quality rows (sensitivity)", value=False,
                        help="Drops the 12 rows with the sparsest data (data_quality_tier='low') so you can check a "
                             "finding isn't driven by them. Affects the Explorer + Score tabs. NOTE: this does NOT "
                             "exclude wipeouts — those are real outcomes; dropping them would be survivorship bias "
                             "(the −100%s are exactly what makes the averages honest).")
    _d0 = load_df(excl_lq)
    c_a, c_b = st.columns(2)
    c_a.metric("IPOs" + (" (ex-low-q)" if excl_lq else ""), f"{len(_d0):,}")
    c_b.metric("MB / SME", f"{int((_d0['type']=='MB').sum())} / {int((_d0['type']=='SME').sum())}")
    with st.expander("🔄 Refresh data (pull new IPOs)"):
        st.caption("Fetches IPOs listed since our latest data date. New IPOs enter as test/live (no track record "
                   "yet) and roll into training as they age.")
        if st.button("Check for new listings"):
            try:
                import run_refresh
                with st.spinner("Fetching from Chittorgarh…"):
                    nw = run_refresh.find_new()
                if len(nw):
                    st.success(f"{len(nw)} new IPOs found")
                    st.dataframe(nw, hide_index=True, use_container_width=True)
                    st.caption("Stage with `python run_refresh.py --commit`, then re-run the pipeline to fold them in.")
                else:
                    st.info("No new IPOs since our last data date.")
            except Exception as e:
                st.warning(f"Couldn't reach the source ({type(e).__name__}). Needs network access.")
    st.caption("**Not financial advice.**")

st.title("📈 Indian IPO Analysis — 2006–2025 (Mainboard + SME)")
st.caption("Repeatable-pattern research over ~2,296 IPOs. Returns = **alpha** (market-adjusted, from the listing "
           "price) vs Nifty 50. SME & Mainboard never pooled. **Not financial advice.**")

tab_report, tab_score, tab_explore, tab_bt, tab_val = st.tabs(
    ["📊 Findings report", "🔮 Score a new IPO", "🔍 Explorer", "📈 Backtester", "✓ Validation & rules"])

# ---------------------------------------------------------------- Findings report
with tab_report:
    st.subheader("Descriptive findings (Part A)")
    st.caption("The full report — 20 findings, every caveat inline. Regenerate with `python run_layer3_report.py`.")
    p = ROOT / "report/layer3_partA.html"
    if p.exists():
        components.html(p.read_text(), height=820, scrolling=True)
    else:
        st.warning("report/layer3_partA.html not found — run `PYTHONPATH=. python run_layer3_report.py` first.")

# ---------------------------------------------------------------- Predictor
with tab_score:
    st.subheader("Score a new IPO against historical analogs")
    st.caption("Finds the most similar PAST IPOs and shows what they did + a transparent scorecard. "
               "No ML — it never forecasts this IPO's own number. **Fill in what you know; leave a field at 0 / "
               "'unknown' if you don't have it — it's dropped, not assumed.** Sector input is forgiving ('Finance' "
               "→ 'Financial Services').")
    with st.form("q"):
        c1, c2, c3, c4 = st.columns(4)
        typ = c1.selectbox("Type", ["MB", "SME"])
        sec = c2.selectbox("Sector", ["(any)"] + sectors())
        mcap = c3.selectbox("Market-cap class", ["(unknown)", "micro", "small", "mid", "large"])
        profile = c4.selectbox("Score profile", ["balanced", "conservative", "aggressive", "data_informed"])
        c5, c6, c7, c8 = st.columns(4)
        issue = c5.number_input("Issue size (₹cr)", min_value=0.0, value=0.0, step=10.0)
        ofs = c6.number_input("OFS %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
        sub = c7.number_input("Subscription (×)", min_value=0.0, value=0.0, step=1.0)
        pe = c8.number_input("P/E", min_value=0.0, value=0.0, step=1.0)
        c9, c10, c11, c12 = st.columns(4)
        roe = c9.number_input("Pre-IPO ROE %", value=0.0, step=1.0)
        de = c10.number_input("Pre-IPO Debt/Equity", min_value=0.0, value=0.0, step=0.1)
        profitable = c11.selectbox("Profitable at IPO?", ["unknown", "yes", "no"])
        revenue = c12.number_input("Pre-IPO revenue (₹cr)", min_value=0.0, value=0.0, step=5.0,
                                   help="Latest pre-IPO annual sales. <25cr is a validated wipeout red flag.")
        c13, c14 = st.columns([1, 3])
        lead_mgr = c13.text_input("Lead manager (optional)", "",
                                  help="An infrequent/obscure banker is a validated wipeout red flag.")
        name = c14.text_input("Name (optional)", "New IPO")
        go = st.form_submit_button("Score it →", type="primary")

    if go:
        q = {"type": typ, "name": name}
        if sec != "(any)": q["broad_sector"] = sec
        if mcap != "(unknown)": q["market_cap_class"] = mcap
        for k, v in [("issue_size_cr", issue), ("ofs_pct", ofs), ("sub_total_x", sub), ("pe_ratio", pe)]:
            if v: q[k] = v
        if roe: q["pre_ipo_roe_pct"] = roe
        if de: q["pre_ipo_debt_equity"] = de
        if profitable != "unknown": q["pre_ipo_pat"] = 1.0 if profitable == "yes" else -1.0
        if revenue: q["pre_ipo_net_sales"] = revenue
        if lead_mgr.strip(): q["lead_manager"] = lead_mgr.strip()

        r = predict(q, df=load_df(excl_lq), profile=profile)
        sc, ar, d, conf = r["scorecard"], r["analog"], r["distribution"], r["scorecard"]["confidence"]

        if ar["n_cohort"] < config.MIN_N_HINT:
            st.error(f"⚠ Only {ar['n_cohort']} analogs — INSUFFICIENT. Treat everything below as a weak hint.")
        st.markdown(f"**{ar['n_cohort']} analogs** · gate: *{ar['rung_label']}* "
                    f"{'· RELAXED' if ar['relaxed'] else ''} · confidence: **{conf['label'].upper()}**")
        if ar.get("sector_note"):
            st.caption("note: " + ar["sector_note"])

        cols = st.columns(8)
        names = {"return_potential": "Return", "multibagger_odds": "Multibagger",
                 "downside_safety": "Downside-safe", "liquidity": "Liquidity", "quality": "Quality",
                 "tradeable_upside": "Tradeable up", "wipeout_safety": "Wipeout-safe"}
        for col, (k, label) in zip(cols, names.items()):
            s = sc["components"][k].get("score")
            w = sc["weights"].get(k, 0)
            col.metric(label + ("" if w else " (w0)"), f"{s:.0f}" if s is not None else "n/a")
        cs = sc["combined_score"]
        cols[7].metric(f"COMBINED ({profile})", f"{cs:.0f}/100" if cs is not None else "n/a")
        mbc = sc["components"]["multibagger_odds"]
        if mbc.get("pct_ever_2x") is not None:
            st.caption(f"ℹ️ Multibagger: **{_p(mbc.get('pct_2x_from_listing'))}** of analogs *ended* ≥2x, but "
                       f"**{_p(mbc.get('pct_ever_2x'))}** *ever touched* 2x within the horizon (the gap = the timing/"
                       "exit tax). 'Tradeable up' (weight-0, context only) = chance the cohort ever reached +30%.")

        if cs is not None:
            if cs >= 60:
                st.success(f"🟢 **{cs:.0f}/100** — resembles the stronger historical cohort.")
            elif cs >= 40:
                st.warning(f"🟡 **{cs:.0f}/100** — middle of the pack.")
            else:
                st.error(f"🔴 **{cs:.0f}/100** — resembles the weaker historical cohort.")
        st.caption("ℹ️ The score *ranks* this IPO against history (in-sample / indicative) — NOT a buy signal. "
                   "The honest base rate is 'what similar IPOs did', below.")

        # --- WIPEOUT-RISK GAUGE (standalone, separate from the return score) ---
        ra = r.get("risk_assessment", {})
        rb = ra.get("risk_band")
        rcols = st.columns([1, 2])
        if ra.get("insufficient_inputs"):
            rcols[1].info("💀 Wipeout-risk **not assessed** — no risk inputs given. Provide revenue / "
                          "profitability / lead-manager to screen for the validated wipeout flags. (Unknown ≠ safe.)")
        elif ra.get("risk_score_0_100") is not None:
            rcols[0].metric("💀 Wipeout-risk", f"{ra['risk_score_0_100']:.0f}/100",
                            help="Standalone risk read (50 = typical for this segment), NOT part of the return score. "
                                 "Based on the validated pre-listing flags + the historical failure rate at this flag-load.")
            tag = {"HIGH": "🔴 HIGH", "ELEVATED": "🟠 ELEVATED", "LOW": "🟢 LOW"}.get(rb, rb)
            rcols[0].markdown(f"**{tag}** risk")
        if ra.get("n_flags"):
            rcols[1].error("🚩 **%d wipeout red flag(s):** %s" % (ra["n_flags"],
                           "; ".join(f"**{name}** ({why})" for name, why in ra["flags"])))
        elif ra.get("n_checked"):
            rcols[1].success("✅ No validated wipeout red flags among the %d checked." % ra["n_checked"])
        if ra.get("fail_rate_at_this_flag_load_%") is not None:
            rcols[1].caption(f"Historically, IPOs like this (basis: {ra.get('basis')}) FAILED "
                             f"(wiped out or dead-money) **{ra['fail_rate_at_this_flag_load_%']}%** of the time vs "
                             f"**{ra.get('segment_base_fail_%')}%** for a typical {ra.get('segment')} IPO.")
        # richer per-flag detail: of IPOs with this flag, how many failed vs passed
        if ra.get("per_flag"):
            pf = pd.DataFrame(ra["per_flag"]).rename(columns={"flag": "red flag", "failed_with_flag_%": "failed WITH %",
                                                              "failed_without_%": "failed WITHOUT %", "n_with": "N with flag"})
            rcols[1].dataframe(pf, hide_index=True, use_container_width=True)
        if ra.get("unknown"):
            rcols[1].caption("ℹ️ Not checked (no input): " + ", ".join(ra["unknown"]) + " — unknown ≠ safe.")

        # --- B1: the full-picture decision panel — what happened to IPOs like this (ALL outcomes) ---
        ob = r.get("outcome_breakdown", {})
        if ob.get("n"):
            st.markdown(f"**📊 The full picture — what happened to the {ob['n']} most-similar past IPOs "
                        f"(by {ob['horizon']}, from the issue price):**")
            bd = ob["horizon_buckets"]
            bc = st.columns(4)
            for col, (lab, key) in zip(bc, [("Doubled+ (≥2x)", "doubled+ (≥2x)_%"), ("Up 20–100%", "up (20–100%)_%"),
                                            ("≈Flat ±20%", "≈flat (±20%)_%"), ("Down <−20%", "down (<−20%)_%")]):
                col.metric(lab, f"{bd.get(key,'—')}%")
            wc = st.columns(3)
            wc[0].metric("🌟 Best case (P90)", _pp(ob.get("best_case_p90_%")),
                         help="The rosy outcome — top-decile return from issue.")
            wc[1].metric("⚖️ Base rate (median)", _pp(ob.get("base_rate_median_%")),
                         help="The typical outcome — the middle IPO.")
            wc[2].metric("💀 Worst case (P10)", _pp(ob.get("worst_case_p10_%")),
                         help="The disaster — bottom-decile return from issue.")
            wbb = ob.get("terminal_wipeout_band_%", (None, None))
            st.caption(f"💀 **Terminal risk** (did it die, lifetime): dead-money (alive but stuck/illiquid) "
                       f"**{ob.get('terminal_dead_money_%','—')}%** · confirmed wipeout band "
                       f"**{wbb[0]}–{wbb[1]}%**. Read best AND worst — IPO returns are barbell-shaped, so "
                       "the median (base rate) is what a typical buyer actually gets, not the rosy P90.")
            if q.get("type") == "SME" and (ob.get("terminal_dead_money_%") or 0) >= 5:
                st.warning("🔑 **SME dead-money rule:** in SME the dominant failure isn't −100%, it's *dead money* "
                           "(stuck, illiquid, un-sellable). Historically those names DID give an exit in year 1 "
                           "(~half traded +20% above issue) before the thin float closed the door — so if you hold "
                           "SME, **treat the first-year peak as your exit**; the second chance often never comes.")

        st.markdown(f"**What {ar['n_cohort']} similar IPOs did** (alpha {d['horizon']}, N={d['n']}): "
                    f"median **{_p(d['median'])}**, P10 {_p(d['p10'])} → P90 {_p(d['p90'])}; "
                    f"wipeout {_p(r['wipeout_band']['wipeout_lower_rate'])}–{_p(r['wipeout_band']['wipeout_upper_rate'])}.")
        av = spine.alpha_series(spine.maturity_gated(ar["cohort"], d["horizon"]), d["horizon"]).dropna()
        if len(av):
            vc = pd.cut(av.clip(-1, 2), bins=12).value_counts().sort_index()
            vc.index = vc.index.astype(str)          # Streamlit can't chart an Interval index
            st.caption("analog alpha distribution (−100% … +200%)")
            st.bar_chart(vc, height=180)
        op = r.get("outcome_profile", {})
        if op:
            st.markdown("**The journey those analogs took (median):**")
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Peaked at (from issue)", _pp(op.get("median_peak_gain_%")),
                      help="Highest point the median analog ever reached, vs its issue price.")
            o2.metric("Ever 2x / 5x", f"{op.get('pct_ever_2x','—')}% / {op.get('pct_ever_5x','—')}%")
            o3.metric("Fell to (from issue)", _pp(op.get("median_trough_from_issue_%")),
                      help="Lowest point the median analog reached, vs its issue price.")
            o4.metric("Worst drawdown", _pp(op.get("median_max_drawdown_%")),
                      help="Deepest peak-to-trough fall en route (what you'd have had to stomach).")
        cohort = r["analog"]["cohort"]
        st.markdown("**Exit discipline — what a 'sell at target' rule would have captured _within 1 year_,** "
                    "shown SEPARATELY for the two entry points (your point: it depends on how you got in):")
        ec = st.columns(2)
        for col, (ent, lab) in zip(ec, [("issue", "🎟️ Allottee — got it at issue"),
                                        ("listing", "📈 Secondary — bought at listing")]):
            es = spine.exit_strategy(cohort, entry=ent, horizon="1y")
            rc = spine.reach_curve(cohort, "1y", entry=ent)
            col.markdown(f"**{lab}**  · N={es['n']}")
            if ent == "listing":
                col.caption(f"only **{rc['pct_ended_positive']}%** *ended* year-1 positive "
                            "(the 'ever gave an exit' 100% is a listing-day tautology — ignore the break-even row)")
            else:
                col.caption(f"**{es['pct_ever_gave_an_exit']}%** ever gave an exit ≥ break-even · only "
                            f"**{rc['pct_ended_positive']}%** *ended* year-1 positive")
            col.dataframe(pd.DataFrame(es["ladder"]).rename(
                columns={"exit_rule": "sell at", "pct_got_the_exit": "% got it",
                         "median_captured_%": "median %", "mean_captured_%": "mean %"}),
                hide_index=True, use_container_width=True)
        st.caption("ℹ️ 'sell at +X%' = exit the first time it touches +X% (else hold to year-end). 'mean %' = the "
                   "discipline's average return. The allottee's higher hit-rates are the listing-pop head-start. "
                   "This is the pattern's *likelihood*, not a single-date snapshot.")
        st.markdown("**Closest comparables**")
        st.dataframe(r["named_analogs"], use_container_width=True, hide_index=True)
        with st.expander("Full text scorecard (analyst one-pager)"):
            st.code(format_text(r))

# ---------------------------------------------------------------- Explorer
with tab_explore:
    st.subheader("🔍 Explorer — does a pattern hold for a slice you pick?")
    st.warning("⚠ **EXPLORATORY.** Slicing many ways = data-dredging: try enough cuts and one looks great by luck. "
               "Treat results as **hypotheses**, mind the **N**, and confirm anything promising cross-regime / "
               "out-of-sample before trusting it.")
    dfx = load_df(excl_lq).copy()
    if excl_lq:
        st.caption("🔎 Sensitivity mode: 12 low-data-quality rows excluded (wipeouts retained — see sidebar).")
    dfx["_yr"] = pd.to_datetime(dfx["listing_date"], errors="coerce").dt.year
    e1, e2, e3, e4 = st.columns(4)
    seg = e1.selectbox("Segment", ["both", "MB", "SME"])
    coh = e2.selectbox("Cohort", ["both", "boom", "longterm"])
    sec = e3.selectbox("Sector", ["(any)"] + sectors())
    mc = e4.selectbox("Market-cap", ["(any)", "micro", "small", "mid", "large"])
    e5, e6, e7, e8 = st.columns(4)
    yr = e5.slider("Listing year range", 2006, 2025, (2006, 2025))
    hor = e6.selectbox("Outcome horizon", ["1y", "3y", "5y"], index=1)
    entry_lab = e7.selectbox("Entry point", ["secondary (bought at listing)", "allottee (got it at issue)"])
    entry = "listing" if entry_lab.startswith("secondary") else "issue"
    splitby = e8.selectbox("Split by — check if the pattern holds across this",
                           ["(none)", "ofs_pct", "pre_ipo_debt_equity", "pre_ipo_roe_pct", "sub_total_x",
                            "adj_listing_gain_open", "issue_size_cr", "pe_ratio"])
    excl_wipe = st.checkbox("⚠ Exclude wipeouts (survivorship-biased — comparison only)", value=False,
                            help="Drops wiped-out names from this slice. This is NOT the honest view — it's here so "
                                 "you can SEE how much rosier the numbers get when the dead are hidden (that gap is "
                                 "the survivorship-bias tax). Never use these figures as the real base rates.")
    s = dfx
    if seg != "both": s = s[s["type"] == seg]
    if coh != "both": s = s[s["cohort"] == coh]
    if sec != "(any)": s = s[s["broad_sector"] == sec]
    if mc != "(any)": s = s[s["market_cap_class"] == mc]
    s = s[(s["_yr"] >= yr[0]) & (s["_yr"] <= yr[1])]
    if excl_wipe:
        n_before = len(s)
        s = s[s["outcome_class"].astype(str) != "wipeout"]
        st.error(f"⚠ SURVIVORSHIP-BIASED VIEW: {n_before - len(s)} wipeouts hidden. These numbers are "
                 "deliberately too rosy — for comparison only, never the real base rate.")
    st.markdown(f"**Slice: {len(s)} IPOs**")
    if len(s) < config.MIN_N_HINT:
        st.error(f"Only {len(s)} IPOs in this slice — too few to say anything. Widen it.")
    elif splitby == "(none)":
        st.caption("Full outcome profile of the slice (peak / trough / multibagger-odds / wipeout):")
        st.dataframe(pd.DataFrame([spine.outcome_profile(s, hor)]), use_container_width=True, hide_index=True)
        rc = spine.reach_curve(s, hor, entry=entry)
        if rc["n"]:
            st.caption(f"**Reach-within-{hor} ladder** — chance the price touched each level (from {entry}), N={rc['n']}. "
                       f"Only {rc['pct_ended_positive']}% ended {hor} positive.")
            cc = st.columns(2)
            cc[0].dataframe(pd.DataFrame(rc["reach_up"]).rename(columns={"move": "upside", "pct_reached": "% reached"}),
                            hide_index=True, use_container_width=True)
            cc[1].dataframe(pd.DataFrame(rc["reach_down"]).rename(columns={"move": "downside", "pct_fell_to": "% fell to"}),
                            hide_index=True, use_container_width=True)
        es = spine.exit_strategy(s, entry=entry, horizon=hor)
        if es["n"] >= config.MIN_N_HINT:
            st.caption(f"**Exit discipline** ({entry}, {hor}) — {es['pct_ever_gave_an_exit']}% ever gave an exit ≥ "
                       "break-even. Take-profit ladder (exit at target if touched, else hold to end):")
            st.dataframe(pd.DataFrame(es["ladder"]).rename(
                columns={"exit_rule": "sell at", "pct_got_the_exit": "% got it",
                         "median_captured_%": "median %", "mean_captured_%": "mean %"}),
                hide_index=True, use_container_width=True)
            sl = spine.stop_loss_strategy(s, entry=entry, horizon=hor)
            st.caption(f"**Stop-loss** ({entry}, {hor}) — buy-and-hold mean **{sl['buy_hold_mean_%']}%**. "
                       "'recovered' = of those stopped, the % that ended UP anyway (the stop's cost):")
            st.dataframe(pd.DataFrame(sl["ladder"]).rename(
                columns={"stop_rule": "stop at", "pct_stopped_out": "% stopped",
                         "stopped_but_recovered_%": "recovered %", "stop_saved_%": "saved %",
                         "mean_with_stop_%": "mean w/stop %", "median_with_stop_%": "median w/stop %"}),
                hide_index=True, use_container_width=True)
            ce = spine.combined_exit_strategy(s, entry=entry, horizon=hor, tp=0.5, sl=0.3)
            if not ce.get("insufficient"):
                verdict = "BEATS hold" if ce["beats_hold_mean"] else "loses to hold"
                st.caption(f"**Combined +50% TP / −30% SL** (whichever first, timing-approximated): rule mean "
                           f"**{ce['rule_mean_%']}%** vs buy-and-hold **{ce['buy_hold_mean_%']}%** → {verdict}. "
                           f"(TP fired {ce['pct_took_profit']}% · stopped {ce['pct_stopped_out']}% · held "
                           f"{ce['pct_held_to_end']}%.) Order is approximated from peak/trough timing — exits "
                           "still cap the right tail, so this usually loses except in net-losing cohorts.")
    else:
        v = pd.to_numeric(s[splitby], errors="coerce"); s2 = s[v.notna()].copy(); s2["_v"] = v[v.notna()]
        if len(s2) < 3 * config.MIN_N_HINT:
            st.warning(f"Only {len(s2)} have '{splitby}' — too few to split into tertiles.")
        else:
            q1, q2 = s2["_v"].quantile([1 / 3, 2 / 3])
            rows = []
            for lab, lo, hi in [("low", -1e18, q1), ("mid", q1, q2), ("high", q2, 1e18)]:
                b = s2[(s2["_v"] > lo) & (s2["_v"] <= hi)] if lab != "low" else s2[s2["_v"] <= hi]
                rows.append({f"{splitby}_tertile": lab, "median_value": round(float(b["_v"].median()), 2),
                             **spine.outcome_profile(b, hor)})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption("Read **down the tertiles**: if the outcome moves steadily low→high, the pattern holds on this "
                       "slice. If it's noisy or flips, it doesn't. Watch the N on each tertile.")

    with st.expander("🔗 Relationships (exploratory) — feature COMBINATIONS that go hand-in-hand"):
        st.caption("Separate exploratory layer — these do NOT feed the score (per the 'evolve-only-if-robust' "
                   "policy). The interaction hunt was disciplined (theory-driven, min-N per cell, cross-regime).")
        st.markdown("**✅ The one validated UPSIDE interaction — the 'clean compounder' (low-debt × high-ROE):** "
                    "neither feature alone escapes a deep-negative base, but *together* they're the best cohort in "
                    "every era & segment (MB/longterm base −43% medα → BOTH +1%; SME/boom → +91%). High ROE that "
                    "isn't debt-juiced = real operating quality. *(3y; see finding N15.)*")
        from layer3.findings import n15_clean_compounder as _n15
        st.dataframe(_n15.compute(load_df()).tables[0][1], hide_index=True, use_container_width=True)
        st.markdown("**❌ RISK side — NO combination survived.** Stacking wipeout flags does *not* multiply risk — "
                    "single flags (tiny-sales / loss-making / obscure-banker) are the whole story; pairs overlap or "
                    "one flag selects a safer population. (high-debt × loss-making is dramatic but longterm-only.)")
        st.caption("Full interaction analysis: `docs/research/interactions_{risk,upside}.md`. Anything here only "
                   "graduates into the score if it later passes the out-of-sample-robust bar.")

# ---------------------------------------------------------------- Backtester
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
    st.markdown("**Holding-period sweep** — secondary buy-at-listing, exit at each horizon ('when do I sell?')")
    cc = st.columns(2)
    cc[0].caption("Mainboard"); cc[0].dataframe(bt["sweep_MB"], use_container_width=True, hide_index=True)
    cc[1].caption("SME"); cc[1].dataframe(bt["sweep_SME"], use_container_width=True, hide_index=True)
    st.markdown("**Portfolio basket** (equal-weight buy-every-IPO) vs do-nothing — dispersion-adjusted, NOT Sharpe")
    st.dataframe(bt["portfolio"], use_container_width=True, hide_index=True)
    st.markdown("**Flip allotment-realism EV** — what you ACTUALLY capture after allotment odds + adverse selection")
    for s in config.SEGMENTS:
        ev = bt["flip"][s]
        if ev:
            st.write(f"- **{s}**: naive flip {ev['naive_mean_flip_%']}% → allotment-weighted "
                     f"**{ev['allotment_weighted_flip_%']}%** (adverse-selection cost {ev['adverse_selection_cost_pp']}pp; "
                     f"median allotment prob {ev['median_allotment_prob']})")
    st.markdown("**Exit-discipline backtest** — does a take-profit rule beat just holding? (raw return, net of cost, "
                "1y, by entry point)")
    ed = bt["exit_disc"]
    st.dataframe(ed, use_container_width=True, hide_index=True)
    n_beat = int(ed["beats_hold"].sum()) if len(ed) else 0
    st.info(f"Take-profit beats buy-and-hold in only **{n_beat}/{len(ed)}** segment×cohort×entry×target cells — "
            "and NONE beat it in *both* cohorts (not cross-regime). Capping the upside sacrifices the right-tail "
            "winners that carry IPO returns. Stop-losses (see the M1 finding) similarly never beat holding on the "
            "mean. NB: a *combined* take-profit+stop-loss can't be backtested — MFE/MAE don't reveal which fired first.")
    st.markdown("**Combined-score loop-closer** — do top-quintile predictor-score IPOs beat the field?")
    st.dataframe(bt["combined"], use_container_width=True, hide_index=True)
    st.info("Verdict: " + bt["combined_verdict"])

# ---------------------------------------------------------------- Validation & rules
with tab_val:
    st.subheader("Cross-regime validation")
    st.caption("Does each directional claim hold the same sign in BOTH the boom (2020–25) and longterm (2006–19) "
               "cohorts, and within individual vintages?")
    st.dataframe(validation_table(), use_container_width=True, hide_index=True)

    st.subheader("Out-of-sample report card — the honest test of the predictor score")
    st.caption("Weights fit on IPOs listed ≤ cutoff, then tested on LATER IPOs never seen during fitting. "
               "Real edge at the 3-year horizon (+55pp); weak at 1 year (~+2–5pp). A ranking tool, not a flip signal.")
    st.dataframe(oos_table(), use_container_width=True, hide_index=True)
    with st.expander("🎚️ Try your own train/test split"):
        cc1, cc2, cc3 = st.columns([2, 1, 1])
        cutoff = cc1.slider("Train on IPOs listed up to…", 2017, 2023, 2021)
        hsel = cc2.selectbox("Test horizon", ["1y", "3y"], key="oos_cut_h")
        if cc3.button("Run split"):
            from layer3.predictor import weights as W
            rr = W.oos_evaluate(load_df(), cutoff, hsel)
            if rr.get("error"):
                st.warning(f"{rr['error']} (train N={rr['n_train']}, test N={rr['n_test']})")
            else:
                st.metric(f"OOS lift — train ≤{cutoff} → test {cutoff+1}+ @ {hsel}", f"{rr['oos_lift_pp']:+}pp",
                          help=f"top-quintile {rr['test_topquintile_median_%']}% vs field "
                               f"{rr['test_field_median_%']}% · test N={rr['n_test']}")

    st.subheader("Rules registry")
    rp = ROOT / "rules/index.md"
    if rp.exists():
        st.markdown(rp.read_text())
