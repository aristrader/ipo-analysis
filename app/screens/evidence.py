"""EVIDENCE BROWSER — Family → Hypothesis → 3-layer tabs. Generic renderer over
app/records/signals.json + families.json. Graveyard first-class.
"""
import pandas as pd
import streamlit as st

from app import ui

ui.inject_style()

st.title("📚 Evidence Browser")
ui.one_liner("What am I looking at? Every tested hypothesis as a data record, grouped into families. "
             "For each: does the effect EXIST (with falsifier + placebo), how BIG is it (dose-response), "
             "and the PLAYBOOK (the whole pre-declared grid, failure cells included). Rejected ideas live "
             "in the graveyard — first-class and browsable. **Not financial advice.**")

import os as _os, datetime as _dt
_rec_m = _dt.date.fromtimestamp(_os.path.getmtime("app/records/signals.json")).isoformat() \
    if _os.path.exists("app/records/signals.json") else "never"
st.markdown(f"<span class='asof'>substrate as-of {ui.as_of_substrate()} · records regenerated {_rec_m} "
            f"(distilled from rules/index.md + verdict docs)</span>", unsafe_allow_html=True)


records = ui.load_records()
families = ui.load_families()

if not records:
    st.info("📭 Records not yet generated. The Evidence Browser renders `app/records/signals.json` "
            "(+ `families.json`) once the records agent has written them. The app runs fine without them.")
    st.caption("Until then, the canonical source is `rules/index.md` and `docs/research/*` verdict docs.")
    st.stop()

# index records by their own family field (the authoritative grouping)
recs_by_family = {}
for rec in records:
    recs_by_family.setdefault(rec.get("family", "(uncategorized)"), []).append(rec)
fam_names = sorted(recs_by_family.keys())


def rollup(recs):
    counts = {"validated": 0, "display": 0, "thin": 0, "rejected": 0}
    for rec in recs:
        counts[ui.chip_status(rec.get("status"))] += 1
    return counts


left, right = st.columns([1, 2.4])

with left:
    st.markdown("#### Families")
    labels = []
    for fn in fam_names:
        recs = recs_by_family.get(fn, [])
        c = rollup(recs)
        labels.append(f"{fn}  (✓{c['validated']} ~{c['display']} ⚠{c['thin']} ✗{c['rejected']})")
    sel = st.radio("Pick a family", labels, label_visibility="collapsed")
    fam = fam_names[labels.index(sel)]
    st.divider()
    tier_filter = st.selectbox("Tier filter", ["(all)"] + sorted(
        {str(r.get("tier")) for r in records if r.get("tier")}))
    status_filter = st.selectbox("Status filter",
                                 ["(all)", "✓ VALIDATED", "~ DISPLAY-ONLY", "⚠ THIN", "✗ REJECTED (graveyard)"])

_status_map = {"✓ VALIDATED": "validated", "~ DISPLAY-ONLY": "display",
               "⚠ THIN": "thin", "✗ REJECTED (graveyard)": "rejected"}

with right:
    fam_recs = recs_by_family.get(fam, [])
    if tier_filter != "(all)":
        fam_recs = [r for r in fam_recs if str(r.get("tier")) == tier_filter]
    if status_filter != "(all)":
        fam_recs = [r for r in fam_recs if ui.chip_status(r.get("status")) == _status_map[status_filter]]

    st.markdown(f"#### {fam}")
    if not fam_recs:
        st.caption("no hypotheses recorded for this family (under the current filter)")
        st.stop()

    titles = [f"{r.get('title', r.get('id'))}" for r in fam_recs]
    pick = st.selectbox("Hypothesis", titles)
    rec = fam_recs[titles.index(pick)]

    st.markdown(f"### {rec.get('title', rec.get('id'))} &nbsp; {ui.chip(rec.get('status'))}",
                unsafe_allow_html=True)
    if rec.get("mechanism"):
        st.caption("Mechanism: " + rec["mechanism"])

    is_rejected = ui.chip_status(rec.get("status")) == "rejected"
    tab_labels = ["EXISTENCE", "MAGNITUDE", "PLAYBOOK"] + (["WHY REJECTED"] if is_rejected else [])
    tabs = st.tabs(tab_labels)

    def render_layer(value, empty_msg):
        """A layer field may be a plain string, a dict, or a list — render generically."""
        if value is None or value == "":
            st.caption(empty_msg)
            return
        if isinstance(value, str):
            st.markdown(value)
        elif isinstance(value, dict):
            try:
                st.dataframe(pd.DataFrame([value]).T.rename(columns={0: "value"}),
                             use_container_width=True)
            except Exception:
                st.json(value)
        elif isinstance(value, list):
            try:
                st.dataframe(pd.DataFrame(value), hide_index=True, use_container_width=True)
            except Exception:
                st.write(value)
        else:
            st.write(value)

    # ---- EXISTENCE: plain-English verdict + falsifier/placebo discipline + numbers
    with tabs[0]:
        st.markdown(f"**Verdict:** {rec.get('verdict', '—')}")
        st.markdown("**Existence / falsifier & placebo read:**")
        render_layer(rec.get("existence"), "existence not recorded for this hypothesis")

    # ---- MAGNITUDE: the numbers (rank-IC / lift / weights / dose-response)
    with tabs[1]:
        nums = rec.get("numbers")
        if rec.get("magnitude"):
            render_layer(rec.get("magnitude"), "")
        elif nums:
            st.markdown("**Measured numbers:**")
            render_layer(nums, "not computed")
            st.caption("Distributions / N where available; cells under the min-N floor are suppressed upstream.")
        else:
            st.caption("not computed for this hypothesis")

    # ---- PLAYBOOK: the rule + failure cells
    with tabs[2]:
        render_layer(rec.get("playbook"), "no playbook recorded for this hypothesis")
        if rec.get("failure_cells"):
            st.error("**FAILURE CELLS** — where this does NOT work:")
            render_layer(rec.get("failure_cells"), "")
        if not is_rejected:
            st.page_link("app/screens/recommendations.py",
                         label="see live IPOs → Recommendations", icon="🟢")

    # ---- WHY REJECTED (graveyard)
    if is_rejected:
        with tabs[3]:
            st.error("✗ REJECTED — this idea is in the graveyard and never gets a recommendation surface.")
            st.markdown("**Why rejected:** " + str(rec.get("verdict") or rec.get("existence") or "—"))
            if rec.get("do_not_retest"):
                st.warning("🛑 DO NOT RE-TEST: " + str(rec["do_not_retest"]))
            if rec.get("source"):
                st.caption("source: " + str(rec["source"]))
