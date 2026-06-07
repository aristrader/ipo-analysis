"""DATA — refresh & methodology. Ported sidebar refresh + the findings report + the explorer
(the LEARN journey's descriptive surfaces), plus how-to-read + data freshness.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from app import ui
from layer3 import config, spine

ui.inject_style()

st.title("🗄 Data, methodology & explorer")
ui.one_liner("What am I looking at? How the data is built, how to read the numbers, the full descriptive "
             "findings report, an exploratory slicer, and how to pull fresh IPOs. **Not financial advice.**")

df = ui.load_df()

tab_method, tab_report, tab_explore, tab_refresh = st.tabs(
    ["📖 How to read it", "📊 Findings report", "🔍 Explorer", "🔄 Refresh data"])

with tab_method:
    st.subheader("How to read everything in this app")
    st.markdown(
        "- **alpha** = your return *minus the market* (Nifty 50), measured from the **listing price** "
        "(what a public buyer actually pays). Positive = beat the market.\n"
        "- **SME and Mainboard are never mixed** — they behave very differently.\n"
        "- Every number shows **N** (how many IPOs it's based on); thin samples are hidden, not faked "
        f"(min-N floor = {config.MIN_N_HINT}).\n"
        "- **Distributions over means** — we show P10 / median / P90 or outcome buckets, never a lone average.\n"
        "- **Trust chips** label every claim: ✓ VALIDATED (cross-regime + OOS) · ~ DISPLAY-ONLY · "
        "⚠ THIN/HYPOTHESIS · ✗ REJECTED (graveyard only).")
    st.warning("⚠ The **predictor score** is a transparent *ranking* (in-sample / indicative) — **not** a "
               "proven money-maker. The **descriptive findings** are the solid, fact-based part.")
    c_a, c_b, c_c = st.columns(3)
    c_a.metric("IPOs", f"{len(df):,}")
    c_b.metric("MB / SME", f"{int((df['type']=='MB').sum())} / {int((df['type']=='SME').sum())}")
    c_c.metric("as-of", ui.as_of_substrate())

with tab_report:
    st.subheader("Descriptive findings (Part A)")
    st.caption("The full report — every caveat inline. Regenerate with `python run_layer3_report.py`.")
    p = config.ROOT / "report/layer3_partA.html"
    if p.exists():
        components.html(p.read_text(), height=820, scrolling=True)
    else:
        st.warning("report/layer3_partA.html not found — run `PYTHONPATH=. python run_layer3_report.py` first.")

with tab_explore:
    st.subheader("🔍 Explorer — does a pattern hold for a slice you pick?")
    st.warning("⚠ **EXPLORATORY.** Slicing many ways = data-dredging: try enough cuts and one looks great by "
               "luck. Treat results as **hypotheses**, mind the **N**, confirm cross-regime before trusting it.")
    dfx = df.copy()
    dfx["_yr"] = pd.to_datetime(dfx["listing_date"], errors="coerce").dt.year
    e1, e2, e3, e4 = st.columns(4)
    seg = e1.selectbox("Segment", ["both", "MB", "SME"])
    coh = e2.selectbox("Cohort", ["both", "boom", "longterm"])
    sec = e3.selectbox("Sector", ["(any)"] + ui.sectors())
    mc = e4.selectbox("Market-cap", ["(any)", "micro", "small", "mid", "large"])
    e5, e6, e7 = st.columns(3)
    yr = e5.slider("Listing year range", 2006, 2025, (2006, 2025))
    hor = e6.selectbox("Outcome horizon", ["1y", "3y", "5y"], index=1)
    entry_lab = e7.selectbox("Entry point", ["secondary (bought at listing)", "allottee (got it at issue)"])
    entry = "listing" if entry_lab.startswith("secondary") else "issue"
    s = dfx
    if seg != "both": s = s[s["type"] == seg]
    if coh != "both": s = s[s["cohort"] == coh]
    if sec != "(any)": s = s[s["broad_sector"] == sec]
    if mc != "(any)": s = s[s["market_cap_class"] == mc]
    s = s[(s["_yr"] >= yr[0]) & (s["_yr"] <= yr[1])]
    st.markdown(f"**Slice: {len(s)} IPOs**")
    floor = ui.n_floor(len(s))
    if floor:
        st.error(f"{floor} — widen the slice.")
    else:
        st.caption("Full outcome profile of the slice (peak / trough / multibagger-odds / wipeout):")
        st.dataframe(pd.DataFrame([spine.outcome_profile(s, hor)]), use_container_width=True, hide_index=True)
        rc = spine.reach_curve(s, hor, entry=entry)
        if rc["n"]:
            st.caption(f"**Reach-within-{hor} ladder** (from {entry}), N={rc['n']}. Only "
                       f"{rc['pct_ended_positive']}% ended {hor} positive.")
            cc = st.columns(2)
            cc[0].dataframe(pd.DataFrame(rc["reach_up"]).rename(columns={"move": "upside", "pct_reached": "% reached"}),
                            hide_index=True, use_container_width=True)
            cc[1].dataframe(pd.DataFrame(rc["reach_down"]).rename(columns={"move": "downside", "pct_fell_to": "% fell to"}),
                            hide_index=True, use_container_width=True)

with tab_refresh:
    st.subheader("Refresh data (pull new IPOs / live board)")
    st.caption("New IPOs enter as test/live (no track record yet) and roll into training as they age.")
    st.markdown("**Copy-paste to refresh from a terminal:**")
    st.code("source .venv/bin/activate\n"
            "python -m scrapers.live_board      # live & upcoming board\n"
            "python run_calls.py                # grade matured calls + new calls\n"
            "python run_refresh.py --commit     # stage newly-listed IPOs (then re-run the pipeline)",
            language="bash")
    if st.button("Check for new listings now"):
        try:
            import run_refresh
            with st.spinner("Fetching from Chittorgarh…"):
                nw = run_refresh.find_new()
            if len(nw):
                st.success(f"{len(nw)} new IPOs found")
                st.dataframe(nw, hide_index=True, use_container_width=True)
            else:
                st.info("No new IPOs since our last data date.")
        except Exception as e:
            st.warning(f"Couldn't reach the source ({type(e).__name__}). Needs network access.")
