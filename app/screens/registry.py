"""SIGNAL REGISTRY — the navigable landscape of every tested signal & its verdict.
Generic renderer over app/records/signals.json; falls back to rules/index.md when records
aren't generated yet.
"""
import pandas as pd
import streamlit as st

from app import ui
from layer3 import config

ui.inject_style()

st.title("🗂 Signal Registry")
ui.one_liner("What am I looking at? Every signal we ever tested and its verdict — in-score / display-only / "
             "watchlist / rejected — so nothing gets re-tested blindly. This is a governance ledger, not a "
             "menu. **Not financial advice.**")
st.info("**SCORE POLICY (locked): evolve-only-if-robust** — a signal enters the weighted score only if it "
        "improves out-of-sample top-quintile lift robustly across splits; otherwise it stays display-only.")

import os as _os, datetime as _dt
_rec_m = _dt.date.fromtimestamp(_os.path.getmtime("app/records/signals.json")).isoformat() \
    if _os.path.exists("app/records/signals.json") else "never"
st.markdown(f"<span class='asof'>substrate as-of {ui.as_of_substrate()} · records regenerated {_rec_m} "
            f"(distilled from rules/index.md + verdict docs)</span>", unsafe_allow_html=True)


records = ui.load_records()


def weight_of(rec):
    n = rec.get("numbers") or {}
    for k in ("data_informed_weight", "weight", "score_weight"):
        if n.get(k) not in (None, ""):
            return n[k]
    return "—"


def evidence_of(rec):
    n = rec.get("numbers") or {}
    bits = []
    for k, v in n.items():
        if k in ("data_informed_weight", "weight"):
            continue
        bits.append(f"{k}={v}")
    return "; ".join(bits) if bits else "—"


if records:
    fc1, fc2 = st.columns(2)
    state_filter = fc1.multiselect(
        "State", ["IN-SCORE", "DISPLAY-ONLY", "WATCHLIST", "REJECTED"],
        default=["IN-SCORE", "DISPLAY-ONLY", "WATCHLIST", "REJECTED"])
    text_filter = fc2.text_input("Search signal / why", "")

    _state_of = {"validated": "IN-SCORE", "display": "DISPLAY-ONLY", "thin": "WATCHLIST",
                 "rejected": "REJECTED"}
    _badge = {"validated": "✓ IN-SCORE", "display": "~ DISPLAY", "thin": "⚠ WATCHLIST",
              "rejected": "✗ REJECTED"}

    def section(title, want_states, graveyard=False):
        st.subheader(title)
        rows = []
        for rec in records:
            cs = ui.chip_status(rec.get("status"))
            state = _state_of[cs]
            if state not in want_states or state not in state_filter:
                continue
            if graveyard != (state == "REJECTED"):
                continue
            why = str(rec.get("verdict") or rec.get("existence") or "—")
            sig = str(rec.get("title", rec.get("id")))
            if text_filter and text_filter.lower() not in (sig + why).lower():
                continue
            rows.append({
                "signal": sig, "family": rec.get("family", ""),
                "state": _badge[cs], "weight": weight_of(rec),
                "evidence": evidence_of(rec), "why": why,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.caption("no signals in this section under the current filter")

    section("① Score components (in-score + display-only)", ["IN-SCORE", "DISPLAY-ONLY"])
    section("② Context & watchlist signals", ["WATCHLIST"])
    section("③ GRAVEYARD (rejected — with the WHY)", ["REJECTED"], graveyard=True)
    st.page_link("app/screens/evidence.py", label="open full Evidence Browser →", icon="📚")
else:
    st.warning("Structured records not yet generated — rendering the canonical registry source "
               "(`rules/index.md`) directly. The filterable table appears once `app/records/signals.json` lands.")
    rp = config.ROOT / "rules/index.md"
    if rp.exists():
        st.markdown(rp.read_text())
    else:
        st.caption("rules/index.md not found")
