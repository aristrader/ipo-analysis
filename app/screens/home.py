"""HOME — orient in one glance: market climate, the three journeys, what needs attention."""
import pandas as pd
import streamlit as st

from app import ui

ui.inject_style()

st.title("📈 Indian IPO Analysis — research terminal")
ui.one_liner(f"What am I looking at? A reader-only research terminal over {len(ui.load_df()):,} "
             "Indian IPOs (2006–2026, Mainboard + SME, incl. delisted). Free data only. "
             "**Not financial advice.**")

# ---- regime banner (persistent component)
ui.render_regime_banner()

st.divider()

# ---- journey cards
board = ui.load_board()
ledger = ui.load_ledger()
records = ui.load_records()

n_open = len(board.get("open", [])) if board else 0
n_up = len(board.get("upcoming", [])) if board else 0
n_records = len(records)
n_validated = sum(1 for r in records if ui.chip_status(r.get("status")) == "validated")
n_graded = int(ledger["grade_status"].isin(["final", "partial"]).sum()) if ledger is not None else 0  # partial included (iter-1 P1 fix)
n_calls = len(ledger) if ledger is not None else 0

st.subheader("Where do you want to go?")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 🟢 DECIDE")
    st.markdown(f"**Recommendations** — {n_open} live · {n_up} upcoming")
    st.caption("An IPO is in front of you. What do the dated, graded calls say?")
    st.page_link("app/screens/recommendations.py", label="Open Recommendations", icon="🟢")
    st.page_link("app/screens/ipo_detail.py", label="Score / look up an IPO", icon="🔎")
with c2:
    st.markdown("#### 📚 LEARN")
    if n_records:
        st.markdown(f"**Evidence** — {n_records} signals · {n_validated} validated")
    else:
        st.markdown("**Evidence** — records loading")
    st.caption("What does the research actually say? Families → hypotheses → 3 layers; graveyard included.")
    st.page_link("app/screens/evidence.py", label="Browse the evidence", icon="📚")
    st.page_link("app/screens/registry.py", label="Signal registry", icon="🗂")
with c3:
    st.markdown("#### 🛰 MONITOR")
    st.markdown(f"**Track record** — {n_graded} calls graded ({n_calls} total)")
    st.caption("Did the calls actually work? The honest forward record, split by evidence strength.")
    st.page_link("app/screens/track_record.py", label="Open track record", icon="🛰")

st.divider()

# ---- needs-attention strip
st.subheader("🔔 Needs attention this week")
st.caption("What am I looking at? Time-sensitive items pulled from the live board and the calls ledger "
           "(pure date math — no opinions added here).")

today = pd.Timestamp.now().normalize()
rows_shown = 0

# (1) windows OPEN / closing within 7d
if board and board.get("open"):
    closing = []
    for o in board["open"]:
        cd = pd.to_datetime(o.get("close_date"), errors="coerce")
        if pd.notna(cd) and 0 <= (cd - today).days <= 7:
            closing.append((o, (cd - today).days))
    if closing:
        st.markdown(f"**Windows closing in ≤7 days ({len(closing)})**")
        for o, days in sorted(closing, key=lambda x: x[1]):
            days_txt = "closes today" if days == 0 else f"closes in {days}d"
            st.markdown(f"- **{o['name']}** ({o['type']}) — {days_txt}  ·  "
                        f"band ₹{o.get('price_band_low','?')}–{o.get('price_band_high','?')}  ·  "
                        f"{ui.money(o.get('issue_size_cr'))}")
        rows_shown += len(closing)

# (2) ledger anchors (d21 / d90 / ex-date) within 14d ahead
if ledger is not None and not ledger.empty:
    upcoming_anchors = ledger[
        (ledger["call_date"] >= today) & (ledger["call_date"] <= today + pd.Timedelta(days=14))
        & (ledger["call_type"].isin(["PERSIST_HOLD", "PERSIST_EXIT_LEAN", "EXIT_REVIEW",
                                     "CLEARED_ISSUE", "TAKE_PROFITS"]))]
    if not upcoming_anchors.empty:
        st.markdown(f"**Persistence / capitulation / corp-action checks due in ≤14 days "
                    f"({len(upcoming_anchors)})**")
        for _, r in upcoming_anchors.sort_values("call_date").head(12).iterrows():
            st.markdown(f"- **{r['name']}** ({r['type']}) — {r['call_type']} on "
                        f"{r['call_date'].date()}")
        rows_shown += len(upcoming_anchors)

    # (3) oldest ungraded live/gap_filled call (forward-test age flag)
    pend = ledger[(ledger["grade_status"] == "pending")
                  & (ledger["mode"].isin(["live", "gap_filled"]))]
    if not pend.empty:
        oldest = pend.sort_values("call_date").iloc[0]
        st.markdown("**Forward-test age**")
        st.markdown(f"- oldest ungraded forward call: **{oldest['name']}** "
                    f"({oldest['call_type']}, {oldest['call_date'].date()}) — awaiting maturity")
        rows_shown += 1

if rows_shown == 0:
    st.info("Nothing needs attention right now.")

if not board:
    st.caption("Live board unavailable — fetched: never. Regime read above is from the substrate only. "
               "Refresh with: `python -m scrapers.live_board`")
