"""IPO DETAIL — the hub. One template for NEW and HISTORICAL IPOs. ?isin= query param or
session-state query dict (from the score form). Eight sections, vertical, decision-order.
"""
import altair as alt
import pandas as pd
import streamlit as st

from app import ui
from layer3 import config, spine

ui.inject_style()

df = ui.load_df()
ledger = ui.load_ledger()


# ---------------------------------------------------------------- resolve the subject
def _name_of(row):
    for c in ("company_name", "name_at_ipo", "official_isin_name"):
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            return v
    return row.get("isin", "(unnamed)")


qp = st.query_params
isin = (qp.get("isin") or "").strip().upper() or None     # case-insensitive (iter-1 P2 fix)
session_q = st.session_state.get("detail_query")

row = None
if isin:
    m = df[df["isin"] == isin]
    if not m.empty:
        row = m.iloc[0]
    else:
        # iter-1 P1/P2 fix: say WHY nothing came up (typo vs deliberately-excluded row)
        from layer3 import spine as _spine
        full = _spine.load_substrate(equity_only=False)
        if (full["isin"] == isin).any():
            r0 = full[full["isin"] == isin].iloc[0]
            st.warning(f"**{r0.get('company_name', isin)}** ({isin}) is in the dataset but "
                       f"EXCLUDED from the equity analysis (REIT/InvIT/FPO or unreliable price "
                       f"coverage) — no decision read is produced for it, by design.")
        else:
            st.error(f"No IPO found with ISIN **{isin}** — check for a typo, "
                     f"or search by name below.")

# ---------------------------------------------------------------- score-a-new-IPO entry (no isin & no session query)
if row is None and not session_q:
    st.title("🔎 Look up or score an IPO")
    ui.one_liner("What am I looking at? Either pick an existing IPO to see its full decision read, or "
                 "describe a new/upcoming IPO and score it against historical analogs (no ML — it shows "
                 "what similar past IPOs did). **Not financial advice.**")

    st.markdown("#### Pick an existing IPO")
    names = df.assign(_n=df.apply(_name_of, axis=1)).sort_values("_n")
    options = {f"{r['_n']} ({r['type']}, {r['isin']})": r["isin"] for _, r in names.iterrows()}
    pick = st.selectbox("Search by name", ["(choose)"] + list(options.keys()))
    if pick != "(choose)":
        st.query_params["isin"] = options[pick]
        st.rerun()

    st.divider()
    st.markdown("#### Or score a new / upcoming IPO")
    with st.form("scoreq"):
        c1, c2, c3, c4 = st.columns(4)
        typ = c1.selectbox("Type", ["MB", "SME"], help="Mainboard vs SME — never pooled; they behave differently.")
        sec = c2.selectbox("Sector", ["(any)"] + ui.sectors())
        mcap = c3.selectbox("Market-cap class", ["(unknown)", "micro", "small", "mid", "large"])
        profile = c4.selectbox("Score profile", ["data_informed", "balanced", "conservative", "aggressive"],
                               help="data_informed = weights fit on backtested lift (recommended).")
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
                                   help="<25cr is a validated wipeout red flag.")
        c13, c14 = st.columns([1, 3])
        lead = c13.text_input("Lead manager (optional)", "", help="An obscure banker is a validated wipeout flag.")
        nm = c14.text_input("Name (optional)", "New IPO")
        st.caption("Leave a field at 0 / 'unknown' if you don't have it — it's dropped, not assumed.")
        go = st.form_submit_button("Score it →", type="primary")
    if go:
        q = {"type": typ, "name": nm}
        if sec != "(any)": q["broad_sector"] = sec
        if mcap != "(unknown)": q["market_cap_class"] = mcap
        for k, v in [("issue_size_cr", issue), ("ofs_pct", ofs), ("sub_total_x", sub), ("pe_ratio", pe)]:
            if v: q[k] = v
        if roe: q["pre_ipo_roe_pct"] = roe
        if de: q["pre_ipo_debt_equity"] = de
        if profitable != "unknown": q["pre_ipo_pat"] = 1.0 if profitable == "yes" else -1.0
        if revenue: q["pre_ipo_net_sales"] = revenue
        if lead.strip(): q["lead_manager"] = lead.strip()
        q["_profile"] = profile
        st.session_state["detail_query"] = q
        st.rerun()
    st.stop()

# ---------------------------------------------------------------- build the predict() query
if row is not None:
    is_new = False
    query = row.to_dict()
    profile = "data_informed"
    name = _name_of(row)
    subj_isin = row["isin"]
    subj_type = row["type"]
else:
    is_new = True
    query = dict(session_q)
    profile = query.pop("_profile", "data_informed")
    name = query.get("name", "New IPO")
    subj_isin = None
    subj_type = query.get("type", "MB")

try:
    r = ui.predict_cached({k: v for k, v in query.items()
                           if k != "_profile" and v is not None and not (isinstance(v, float) and pd.isna(v))},
                          profile=profile)
except Exception as e:                       # iter-1 fix: friendly failure, never a traceback
    st.error(f"Couldn't build the evaluation for this query ({type(e).__name__}). "
             f"Usually this means too few comparable IPOs exist. Try fewer/looser inputs.")
    st.stop()
sc = r["scorecard"]
ar = r["analog"]
ra = r.get("risk_assessment", {})
ob = r.get("outcome_breakdown", {})

# ---------------------------------------------------------------- header
hdr = f"{name} · {subj_type}"
if not is_new:
    ld = pd.to_datetime(row.get("listing_date"), errors="coerce")
    if pd.notna(ld):
        hdr += f" · listed {ld.date()}"
    hdr += f" · {subj_isin}"
st.title(hdr)
ui.one_liner("What am I looking at? The full decision read for this one IPO — verdict, what happened to "
             "the most-similar past IPOs, the scorecard, its cluster, its calendar, its price path vs "
             "reference levels, the playbooks that apply, and the closest comparables. "
             + ("New IPO: realized values are shown as *expected* from analogs. " if is_new else "")
             + "**Not financial advice.**")
st.markdown(f"<span class='asof'>as-of {ui.as_of_substrate()} · profile: {profile}</span>",
            unsafe_allow_html=True)
ui.render_glossary()
st.page_link("app/screens/ipo_detail.py", label="← look up a different IPO", icon="🔎")
if not is_new and st.button("clear & search another"):
    st.query_params.clear()
    st.rerun()

if ar["n_cohort"] < ui.MIN_N:
    st.error(f"⚠ INSUFFICIENT analogs (N={ar['n_cohort']}) — treat everything below as a weak hint, not a read.")

st.divider()

# ====================================================== ① VERDICT BAR
st.subheader("① Verdict")
# iter-2 P1 fix: a dead stock must SAY SO before any forward-looking read
_dead = row is not None and str(row.get("delisted")) in ("True", "true", "1")
_oc = str(row.get("outcome_class") or "") if row is not None else ""
if _dead:
    if _oc == "wipeout":
        st.error("💀 **DELISTED — WIPEOUT (realized).** Compulsory delisting/liquidation; terminal "
                 "value −100%. Everything below is the historical read of what led here.")
    else:
        _why = row.get("delist_reason")
        _why = _why if isinstance(_why, str) and _why.strip() else "reason not recorded"
        st.warning(f"⚠️ **DELISTED** ({_why}). Terminal value = last traded price. "
                   "Everything below is the historical read.")
v1, v2, v3 = st.columns([1, 1, 2])
cs = sc["combined_score"]
v1.metric(f"COMBINED ({profile})", f"{cs:.0f}/100" if cs is not None else "n/a",
          help="A transparent RANKING vs history (in-sample / indicative) — NOT a proven buy signal.")
v1.markdown(ui.chip("display"), unsafe_allow_html=True)
rscore = ra.get("risk_score_0_100")
if _dead and _oc == "wipeout":
    v2.metric("💀 Wipeout", "REALIZED", help="This is no longer a risk — it happened.")
    v2.markdown(ui.chip("validated"), unsafe_allow_html=True)
elif rscore is not None:
    band = ra.get("risk_band")
    tag = {"HIGH": "🔴 HIGH", "ELEVATED": "🟠 ELEVATED", "LOW": "🟢 LOW"}.get(band, band)
    v2.metric("💀 Wipeout-risk", f"{rscore:.0f}/100",
              help="Standalone risk read (50 = typical for the segment), NOT part of the return score.")
    v2.markdown(f"**{tag}** &nbsp; {ui.chip('validated')}", unsafe_allow_html=True)
else:
    v2.metric("💀 Wipeout-risk", "not assessed")
    v2.caption("no risk inputs given — unknown ≠ safe")
# ledger call line
if subj_isin and ledger is not None:
    lc = ledger[(ledger["isin"] == subj_isin)
                & (ledger["call_type"].isin(["APPLY", "AVOID", "NEUTRAL"]))]
    if not lc.empty:
        c = lc.sort_values("call_date").iloc[-1]
        v3.markdown(f"**Ledger call: {c['call_type']}** {ui.chip('validated')}", unsafe_allow_html=True)
        v3.caption(f"fired {c['call_date'].date()} · why: {ui.why_text(c['rules_fired'])}")
        v3.page_link("app/screens/recommendations.py", label="see all calls →", icon="🟢")
    else:
        v3.caption("no APPLY/AVOID/NEUTRAL call on file for this ISIN")

st.divider()

# ====================================================== ② THE FULL PICTURE
st.subheader("② The full picture")
st.markdown(ui.chip("validated"), unsafe_allow_html=True)
if ob.get("n"):
    st.markdown(f"**What happened to the {ob['n']} most-similar past IPOs (by {ob['horizon']}, from issue):**")
    bd = ob["horizon_buckets"]
    bc = st.columns(4)
    for col, (lab, key) in zip(bc, [("Doubled+ (≥2x)", "doubled+ (≥2x)_%"), ("Up 20–100%", "up (20–100%)_%"),
                                    ("≈Flat ±20%", "≈flat (±20%)_%"), ("Down <−20%", "down (<−20%)_%")]):
        col.metric(lab, f"{bd.get(key, '—')}%")
    wc = st.columns(3)
    wc[0].metric("🌟 Best case (P90)", ui.pct(ob.get("best_case_p90_%")), help="Top-decile return from issue.")
    wc[1].metric("⚖️ Base rate (median)", ui.pct(ob.get("base_rate_median_%")), help="The typical / middle IPO.")
    wc[2].metric("💀 Worst case (P10)", ui.pct(ob.get("worst_case_p10_%")), help="Bottom-decile return from issue.")
    wbb = ob.get("terminal_wipeout_band_%", (None, None))
    st.caption(f"💀 Terminal risk: dead-money **{ob.get('terminal_dead_money_%', '—')}%** · "
               f"confirmed wipeout band **{wbb[0]}–{wbb[1]}%**. IPO returns are barbell-shaped — read the median "
               "(what a typical buyer gets), not just the rosy P90.")
    # analog alpha distribution (native bar — does NOT count against the two Altair charts)
    d = r["distribution"]
    av = spine.alpha_series(spine.maturity_gated(ar["cohort"], d["horizon"]), d["horizon"]).dropna()
    if len(av):
        vc = pd.cut(av.clip(-1, 2), bins=12).value_counts().sort_index()
        vc.index = vc.index.astype(str)
        st.caption(f"analog alpha distribution ({d['horizon']}, −100%…+200%), N={len(av)}")
        st.bar_chart(vc, height=160)
    if subj_type == "SME" and (ob.get("terminal_dead_money_%") or 0) >= 5:
        st.warning("🔑 **SME dead-money rule:** the dominant SME failure isn't −100%, it's *dead money* (stuck, "
                   "illiquid). Those names historically gave a first-year exit before the float closed the door — "
                   "treat the first-year peak as your exit.")
else:
    st.caption("no analog outcome breakdown available for this query")

st.divider()

# ====================================================== ③ SCORECARD
st.subheader("③ Scorecard")
names = {"return_potential": ("Return", "validated"), "multibagger_odds": ("Multibagger", "validated"),
         "downside_safety": ("Downside-safe", "validated"), "wipeout_safety": ("Wipeout-safe", "validated"),
         "liquidity": ("Liquidity", "display"), "quality": ("Quality", "display"),
         "tradeable_upside": ("Tradeable up", "display")}
cols = st.columns(len(names))
for col, (k, (label, status)) in zip(cols, names.items()):
    comp = sc["components"].get(k, {})
    s = comp.get("score")
    w = sc["weights"].get(k, 0)
    col.metric(label + ("" if w else " (display)"), f"{s:.0f}" if s is not None else "n/a")
    col.markdown(ui.chip(status), unsafe_allow_html=True)
st.caption("Components tagged '(display)' carry weight 0 — shown for context, not in the combined score "
           "(the 'evolve-only-if-robust' policy). ✓ components are in-score and out-of-sample tested.")

# wipeout red-flag badges
if ra.get("n_flags"):
    st.error("🚩 **%d wipeout red flag(s):** %s" % (
        ra["n_flags"], "; ".join(f"**{nm}** ({why})" for nm, why in ra["flags"])))
    if ra.get("per_flag"):
        pf = pd.DataFrame(ra["per_flag"]).rename(columns={
            "flag": "red flag", "failed_with_flag_%": "failed WITH %",
            "failed_without_%": "failed WITHOUT %", "n_with": "N with flag"})
        st.dataframe(pf, hide_index=True, use_container_width=True)
elif ra.get("n_checked"):
    st.success("✅ No validated wipeout red flags among the %d checked." % ra["n_checked"])
if ra.get("unknown"):
    st.caption("ℹ️ Not checked (no input): " + ", ".join(ra["unknown"]) + " — unknown ≠ safe.")

st.divider()

# ====================================================== ④ CLUSTER CONTEXT
st.subheader("④ Cluster context")
st.markdown(ui.chip("display"), unsafe_allow_html=True)
st.caption("Its competitive window: same-segment IPOs opening within ±21 days, and this IPO's GMP rank "
           "within that cluster. Cluster framing is descriptive (display-only).")
WINDOW = 21
od = pd.to_datetime(query.get("open_date"), errors="coerce")
if pd.notna(od):
    dfo = df.copy()
    dfo["_od"] = pd.to_datetime(dfo["open_date"], errors="coerce")
    cluster = dfo[(dfo["type"] == subj_type) & dfo["_od"].notna()
                  & (abs((dfo["_od"] - od).dt.days) <= WINDOW)]
    if subj_isin:
        cluster = cluster[cluster["isin"] != subj_isin]
    if len(cluster):
        st.markdown(f"**{len(cluster)} same-segment peers** opened within ±{WINDOW} days.")
        gmp_col = "gmp_pct" if "gmp_pct" in df.columns else None
        my_gmp = query.get("gmp_pct")
        if gmp_col and my_gmp is not None and pd.notna(my_gmp):
            peers_gmp = pd.to_numeric(cluster[gmp_col], errors="coerce").dropna()
            if len(peers_gmp):
                rank = (peers_gmp < my_gmp).mean() * 100
                st.metric("GMP rank within cluster", f"{rank:.0f}th pctl",
                          help="Where this IPO's grey-market premium sits among its window peers.")
        show = cluster.assign(_n=cluster.apply(_name_of, axis=1))[["_n", "type", "open_date"]].head(15)
        st.dataframe(show.rename(columns={"_n": "name"}), hide_index=True, use_container_width=True)
    else:
        st.caption("no cluster peers in window")
else:
    st.caption("no open_date for this IPO — cluster window not computable")

st.divider()

# ====================================================== ⑤ EVENT CALENDAR
st.subheader("⑤ Event calendar")
st.caption("Pure date math: close → listing → d21 (persistence) → d90 (capitulation) → corp-action ex-dates.")
from layer3 import calls as _calls
cal_rows = []
close_d = pd.to_datetime(query.get("close_date"), errors="coerce")
list_d = pd.to_datetime(query.get("listing_date"), errors="coerce")
if pd.notna(close_d):
    cal_rows.append(("Close (apply-call anchor)", close_d.date(), "", ""))
if pd.notna(list_d):
    cal_rows.append(("Listing", list_d.date(), "", ""))
    d21 = _calls.td_offset(list_d, 21)
    d90 = _calls.td_offset(list_d, 90)
    if d21 is not None:
        cal_rows.append(("d+21 persistence read", d21.date(), "PERSIST", "display"))
    if d90 is not None:
        cal_rows.append(("d+90 capitulation check", d90.date(), "EXIT_REVIEW", "validated"))
# corp-action ex-dates within listing+365d
ca = ui.load_corp_actions()
if ca is not None and subj_isin and pd.notna(list_d):
    sym = row.get("nse_symbol") if not is_new else None
    mine = ca[(ca["isin"] == subj_isin)]
    if sym is not None and isinstance(sym, str):
        mine = pd.concat([mine, ca[ca["symbol"].astype(str).str.upper() == sym.upper()]]).drop_duplicates()
    for _, a in mine.iterrows():
        ex = pd.to_datetime(a.get("ex_date"), errors="coerce")
        if pd.notna(ex) and 0 <= (ex - list_d).days <= 365 and a.get("action_type") in ("bonus", "split"):
            cal_rows.append((f"Corp action ({a['action_type']}) ex-date · TAKE-PROFITS",
                             ex.date(), "TAKE_PROFITS", "thin"))
if cal_rows:
    for label, date, marker, status in cal_rows:
        line = f"**{date}** — {label}"
        if status:
            note = "VALIDATED-THIN (F10)" if marker == "TAKE_PROFITS" else None
            st.markdown(line + " &nbsp; " + ui.chip(status, note), unsafe_allow_html=True)
        else:
            st.markdown(line)
    st.caption("Anchor-unlock rows are INFORMATION ONLY (F1 anchor-unlock falsified — no edge). "
               "Corp-action ex-date rows carry a TAKE-PROFITS marker (thin, n=31).")
else:
    st.caption("no dated events available for this IPO")

st.divider()

# ====================================================== ⑥ PATH vs REFERENCE (Altair chart #1)
st.subheader("⑥ Path vs reference levels")
prices = ui.load_prices(subj_isin) if subj_isin else None
if prices is not None and len(prices) > 1:
    span_days = (prices["date"].max() - prices["date"].min()).days
    p = prices.copy()
    if span_days > 365:
        p = p.set_index("date").resample("W").last().dropna(subset=["close"]).reset_index()
    issue_adj = pd.to_numeric(pd.Series([row.get("issue_price_adj")]), errors="coerce").iloc[0] if not is_new else None
    # listing-day high
    lst_high = None
    if pd.notna(list_d):
        ld_rows = prices[prices["date"] == prices[prices["date"] >= list_d]["date"].min()]
        if len(ld_rows):
            lst_high = float(ld_rows["high"].iloc[0])
    base = alt.Chart(p).mark_line(color="#16181d").encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("close:Q", title="close (₹, adj)"),
        tooltip=["date:T", "close:Q"])
    layers = [base]
    if issue_adj is not None and pd.notna(issue_adj):
        layers.append(alt.Chart(pd.DataFrame({"y": [issue_adj]})).mark_rule(
            color="#0f5132", strokeDash=[4, 3]).encode(y="y:Q"))
    if lst_high is not None:
        layers.append(alt.Chart(pd.DataFrame({"y": [lst_high]})).mark_rule(
            color="#842029", strokeDash=[2, 2]).encode(y="y:Q"))
    st.altair_chart(alt.layer(*layers).properties(height=300), use_container_width=True)
    st.caption("Green dashed = issue price (adjusted) · red dotted = listing-day high. "
               "Above issue = reclaimed; above listing-high = broke out.")
    # capitulation badge (F5e): never closed above issue across td 1..90
    if issue_adj is not None and pd.notna(issue_adj) and pd.notna(list_d):
        first90 = prices[(prices["date"] >= list_d)].head(90)
        if len(first90) and (first90["close"] <= issue_adj).all():
            st.markdown(f"🚩 **CAPITULATION** — never closed above the issue price in trading days 1–90. "
                        f"{ui.chip('validated')}", unsafe_allow_html=True)
            st.caption("F5e (cross-regime, no look-ahead): ~12% of IPOs hit this — bad-outcome rate 55% vs 13%.")
else:
    st.caption("No price file for this IPO — showing the *expected* reach ladder from analogs instead.")
rch = r.get("reach_curve_h", {})
if rch.get("n"):
    st.markdown(f"**Reach ladder** ({'expected from analogs' if is_new or prices is None else 'realized'}, "
                f"{rch['horizon']}, N={rch['n']}):")
    cc = st.columns(2)
    cc[0].dataframe(pd.DataFrame(rch["reach_up"]).rename(columns={"move": "upside", "pct_reached": "% reached"}),
                    hide_index=True, use_container_width=True)
    cc[1].dataframe(pd.DataFrame(rch["reach_down"]).rename(columns={"move": "downside", "pct_fell_to": "% fell to"}),
                    hide_index=True, use_container_width=True)

st.divider()

# ====================================================== ⑦ PLAYBOOKS THAT APPLY
st.subheader("⑦ Playbooks that apply")
records = ui.load_records()
# Records carry a plain-English playbook string (no structured applicability predicate),
# so we surface the VALIDATED / in-score playbook library — rejected ideas are NEVER shown.
# Each carries its own trust chip; segment-specific ones are matched by mention of the segment.


def relevant(rec):
    if ui.chip_status(rec.get("status")) == "rejected":
        return False
    pb = rec.get("playbook")
    if not pb or not isinstance(pb, str):
        return False
    # only surface validated / in-score / watchlist playbooks as action-adjacent guidance
    return ui.chip_status(rec.get("status")) in ("validated", "thin")


applied = [r for r in records if relevant(r)]
# light relevance: prefer ones whose text doesn't name the OTHER segment
other = "SME" if subj_type == "MB" else "MB"
applied = [r for r in applied
           if not (other.lower() in (r.get("playbook") or "").lower()
                   and subj_type.lower() not in (r.get("playbook") or "").lower())]

if not records:
    st.caption("Evidence records not yet generated — playbooks populate once "
               "`app/records/signals.json` lands.")
elif applied:
    st.caption("Validated playbooks in the library (records carry no auto-match predicate, so judge "
               "applicability against this IPO's profile above). Rejected ideas never appear here.")
    for rec in applied[:12]:
        st.markdown(f"**{rec.get('title', rec.get('id'))}** {ui.chip(rec.get('status'))}",
                    unsafe_allow_html=True)
        st.caption(str(rec.get("playbook")))
        if rec.get("failure_cells"):
            st.caption("⚠ fails when: " + str(rec["failure_cells"]))
else:
    st.caption("no validated playbook in the library right now")

st.divider()

# ====================================================== ⑧ COMPARABLES
st.subheader("⑧ Closest comparables")
na = r.get("named_analogs")
if na is not None and len(na):
    st.dataframe(na, hide_index=True, use_container_width=True)
    st.caption("Each is a real past IPO closest to this query. Open any by ISIN: "
               "`?isin=<the ISIN>` in the address bar.")
else:
    st.caption("no comparables found")
