"""IPO Analysis — Streamlit app (Phase-2 multipage entry).

Bloomberg-for-one-person research terminal over ~2,296 Indian IPOs. Reader-only over the
engine, the calls ledger, the live board, and the evidence records. Three journeys
(DECIDE / LEARN / MONITOR) + DATA. NOT financial advice. Run:

    source .venv/bin/activate
    PYTHONPATH=. streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Indian IPO Analysis", layout="wide", page_icon="📈")

from app import ui  # noqa: E402

ui.inject_style()

# --- the six screens + DATA, grouped by journey ----------------------------------
home = st.Page("app/screens/home.py", title="Home", icon="🏠", default=True)
recommendations = st.Page("app/screens/recommendations.py", title="Recommendations", icon="🟢")
ipo_detail = st.Page("app/screens/ipo_detail.py", title="IPO Detail / Score", icon="🔎")
evidence = st.Page("app/screens/evidence.py", title="Evidence Browser", icon="📚")
registry = st.Page("app/screens/registry.py", title="Signal Registry", icon="🗂")
track_record = st.Page("app/screens/track_record.py", title="Track Record", icon="🛰")
data = st.Page("app/screens/data.py", title="Data & Methodology", icon="🗄")

nav = st.navigation({
    " ": [home],
    "DECIDE": [recommendations, ipo_detail],
    "LEARN": [evidence, registry],
    "MONITOR": [track_record],
    "DATA": [data],
})

with st.sidebar:
    st.caption("Indian IPO Analysis · 2006–2026 · MB + SME")
    st.caption("**Not financial advice.** Returns = alpha vs Nifty 50, from the listing price.")

    # Global IPO search (Fix E — findability from anywhere). Navigates to IPO Detail via ?isin=,
    # the exact convention ipo_detail.py reads (st.query_params.get("isin")).
    st.divider()
    st.markdown("**🔎 Find an IPO**")
    _opts = ui.name_options(ui.load_df())
    _pick = st.selectbox("Search by name", ["(choose)"] + list(_opts.keys()),
                         key="sidebar_ipo_search", label_visibility="collapsed")
    _isin = ui.resolve_label_to_isin(_pick, _opts)
    if _isin and st.query_params.get("isin") != _isin:
        st.query_params["isin"] = _isin
        st.switch_page(ipo_detail)

nav.run()
