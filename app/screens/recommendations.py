"""RECOMMENDATIONS — the DECIDE centerpiece. Pure reader of calls_ledger.csv + board.json.

Standing answer to "an IPO is in front of me — what do I do?", as a dated, graded ledger of calls.
No engine calls at render except cached predict() for upcoming previews.
"""
import pandas as pd
import streamlit as st

from app import ui

ui.inject_style()

st.title("🟢 Recommendations")
ui.one_liner("What am I looking at? Every IPO that is open or upcoming, the dated call the engine made "
             "(or a preview for upcoming), what to watch on listed names, fresh alerts, and the honest "
             "track record — all read from the calls ledger + live board. **Not financial advice.**")

ledger = ui.load_ledger()
board = ui.load_board()

# ---- header strip
hc1, hc2 = st.columns([3, 1])
hc1.markdown(
    f"<span class='asof'>ledger graded to {ui.as_of_ledger(ledger)} · "
    f"board fetched {ui.as_of_board(board)}</span>", unsafe_allow_html=True)
with hc2:
    with st.popover("🔄 Refresh"):
        st.caption("Pull the latest live board + grade matured calls. Copy-paste to run from a terminal:")
        st.code("python -m scrapers.live_board\npython run_calls.py", language="bash")
        if st.button("Run refresh now"):
            try:
                import run_refresh
                with st.spinner("Refreshing…"):
                    run_refresh.find_new()
                st.cache_data.clear()        # bust stale loaders so THIS page updates (iter-1 P2 fix)
                st.success("Refreshed.")
                st.rerun()
            except Exception as e:
                st.warning(f"Couldn't refresh ({type(e).__name__}). Needs network / pipeline access.")
        if st.button("Re-read data files (no network)"):
            st.cache_data.clear()
            st.rerun()

ui.render_regime_banner()

if ledger is None:
    st.error("Calls engine not yet run — `python run_calls.py`. No ledger to render.")
    st.stop()

today = pd.Timestamp.now().normalize()

# call_type -> chip status + note
_CHIP_FOR = {
    "APPLY": ("validated", None), "AVOID": ("validated", None), "NEUTRAL": ("validated", None),
    "EARLY_APPLY": ("thin", "forward-only"), "EARLY_AVOID": ("thin", "forward-only"),
    "EARLY_NEUTRAL": ("thin", "forward-only"),
    "PERSIST_HOLD": ("display", None), "PERSIST_EXIT_LEAN": ("display", None),
    "EXIT_REVIEW": ("validated", None), "CLEARED_ISSUE": ("validated", None),
    "TAKE_PROFITS": ("thin", "VALIDATED-THIN (n=31)"),
    "TRACK": ("display", None),
}


def call_chip(ct):
    status, note = _CHIP_FOR.get(ct, ("display", None))
    return ui.chip(status, note)


def isin_link(isin, label):
    if isin and not pd.isna(isin):
        ui.page_link_isin(isin, label)      # carries ?isin= (iter-1 P1 fix)
    else:
        st.caption(f"{label} — no ISIN yet (detail unavailable until it enters the substrate)")


st.divider()

# ====================================================== LIVE & UPCOMING BOARD
st.subheader("🔴🟢 Live & upcoming board")
if not board:
    st.info("Live board unavailable — fetched: never. Tracking / alerts / track-record below still render "
            "from the ledger. Refresh with `python -m scrapers.live_board`.")
else:
    open_ipos = board.get("open", [])
    up_ipos = board.get("upcoming", [])

    # OPEN now
    st.markdown("**OPEN now**")
    if not open_ipos:
        st.caption("none right now")
    else:
        # de-dupe by slug/name (board sometimes repeats)
        seen = set()
        for o in open_ipos:
            key = o.get("slug") or o.get("name")
            if key in seen:
                continue
            seen.add(key)
            isin = o.get("isin")
            cd = pd.to_datetime(o.get("close_date"), errors="coerce")
            dtc = (cd - today).days if pd.notna(cd) else None
            # look up the call for this issue in the ledger — live calls are keyed by
            # exchange ISIN when known, else the board slug/name (run_calls --live)
            call_row = None
            keys = {k for k in (isin, o.get("slug"), o.get("name")) if k}
            cands = ledger[ledger["isin"].isin(keys) & ledger["call_type"].isin(
                ["APPLY", "AVOID", "NEUTRAL", "EARLY_APPLY", "EARLY_AVOID", "EARLY_NEUTRAL"])]
            if not cands.empty:
                call_row = cands.sort_values("call_date").iloc[-1]
            with st.container(border=True):
                top = st.columns([3, 2])
                top[0].markdown(f"**{o['name']}** ({o['type']})")
                if call_row is not None:
                    early = str(call_row["call_type"]).startswith("EARLY_")
                    top[1].markdown(f"call: **{call_row['call_type']}** "
                                    f"{call_chip(call_row['call_type'])}", unsafe_allow_html=True)
                    st.caption(f"why: {call_row['rules_fired']}"
                               + (" · early call on partial window data — final verdict lands "
                                  "on the close date" if early else ""))
                else:
                    top[1].markdown(f"call: **pending** {ui.chip('thin', 'awaits close-date')}",
                                    unsafe_allow_html=True)
                    st.caption("No graded call until the close-date anchor — final subscription must publish first.")
                meta = []
                if dtc is not None:
                    meta.append("closes today" if dtc == 0 else f"closes in {dtc}d")
                if o.get("sub_total_x") is not None:
                    meta.append(f"sub {o['sub_total_x']}×")
                if o.get("gmp_pct") is not None:
                    meta.append(f"GMP {o['gmp_pct']}%")
                st.caption(" · ".join(meta) if meta else "—")
                isin_link(isin, "detail")

    # UPCOMING (preview only)
    st.markdown("**UPCOMING** — preview only, no call until the close-date anchor")
    if not up_ipos:
        st.caption("none right now")
    else:
        for o in up_ipos:
            with st.container(border=True):
                od = pd.to_datetime(o.get("open_date"), errors="coerce")
                # cached preview score from a minimal query (type only — board has no sector/fundamentals)
                q = {"type": o["type"], "name": o["name"]}
                try:
                    r = ui.predict_cached(q, profile="data_informed")
                    cs = r["scorecard"]["combined_score"]
                    n = r["analog"]["n_cohort"]
                    if n < ui.MIN_N:
                        score_txt = f"insufficient analogs (N={n})"
                    else:
                        score_txt = f"expected score ~{cs:.0f}/100 (preview, N={n})" if cs is not None else "n/a"
                except Exception:
                    score_txt = "preview unavailable"
                st.markdown(f"**{o['name']}** ({o['type']}) — {score_txt} "
                            f"{ui.chip('thin', 'preview')}", unsafe_allow_html=True)
                opens = f"opens {od.date()}" if pd.notna(od) else "open date TBD"
                st.caption(f"{opens} · band ₹{o.get('price_band_low','?')}–{o.get('price_band_high','?')} · "
                           f"{ui.money(o.get('issue_size_cr'))}")
                st.caption("Preview ranks against type-matched history only (board carries no sector/fundamentals). "
                           "Score it fully on the IPO Detail page.")

st.divider()

# ====================================================== TRACKING
st.subheader("👀 Tracking (recently listed)")
st.caption("Names listed within ~120 days, with the next milestone read (d21 persistence · d90 capitulation).")
track = ledger[ledger["call_type"] == "TRACK"].copy()
track = track[track["call_date"] >= today - pd.Timedelta(days=120)]
if track.empty:
    st.caption("none right now")
else:
    for _, t in track.sort_values("call_date", ascending=False).head(20).iterrows():
        listed = t["call_date"]
        age_d = (today - listed).days
        # next milestone on the TRADING-day calendar (iter-2 P3 fix; was calendar-day approx)
        from layer3 import calls as _calls
        t21 = _calls.td_offset(listed, 21)
        t90 = _calls.td_offset(listed, 90)
        if t21 is not None and today < t21:
            milestone = f"d21 persistence read in ~{(t21 - today).days}d {ui.chip('display')}"
        elif t90 is not None and today < t90:
            milestone = f"d90 capitulation check in ~{(t90 - today).days}d {ui.chip('validated')}"
        else:
            milestone = f"matured {ui.chip('validated')}"
        c = st.columns([3, 3])
        c[0].markdown(f"**{t['name']}** ({t['type']}) · listed {listed.date()} · d+{age_d}")
        c[1].markdown(milestone, unsafe_allow_html=True)
        isin_link(t["isin"], "detail")

st.divider()

# ====================================================== ALERTS
st.subheader("🚨 Alerts (≤30 days old)")
alert_types = ["EXIT_REVIEW", "CLEARED_ISSUE", "PERSIST_EXIT_LEAN", "TAKE_PROFITS"]
alerts = ledger[(ledger["call_type"].isin(alert_types))
                & (ledger["call_date"] >= today - pd.Timedelta(days=30))]
if alerts.empty:
    st.caption("none right now")
else:
    for _, a in alerts.sort_values("call_date", ascending=False).head(20).iterrows():
        st.markdown(f"**{a['call_type']}** · {a['name']} ({a['type']}) · fired {a['call_date'].date()} "
                    f"{call_chip(a['call_type'])}", unsafe_allow_html=True)
        st.caption(f"why: {a['rules_fired']}")
        isin_link(a["isin"], "detail")

st.divider()

# ====================================================== TRACK RECORD (recomputed)
st.subheader("📋 Track record")
st.caption("Recomputed from the ledger at render — never hardcoded. Split by MODE so evidence strength is "
           "visible (live / gap_filled = forward truth · backfilled = out-of-sample · historical_sim = "
           "dress rehearsal). Distributions, not means; thin rows show 'too few'.")


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


lg = ledger.copy()
lg["_win"] = lg.apply(win_flag, axis=1)
graded = lg[lg["call_type"].isin(["APPLY", "AVOID", "EARLY_APPLY", "EARLY_AVOID",
                                  "EXIT_REVIEW", "PERSIST_EXIT_LEAN", "TAKE_PROFITS"])]
rows = []
for (ct, mode), g in graded.groupby(["call_type", "mode"]):
    w = g["_win"].dropna()
    n = len(w)
    delta = pd.to_numeric(g.get("alpha_1y"), errors="coerce").dropna()
    floor = ui.n_floor(n)
    rows.append({
        "call_type": ct, "mode": mode, "n": n,
        "win_%": floor if floor else f"{100*w.mean():.0f}%",
        "median Δα 1y": "—" if floor else ui.frac(delta.median()) if len(delta) else "—",
        "IQR Δα 1y": "—" if floor or len(delta) < 4 else
                     f"{ui.frac(delta.quantile(.25))} … {ui.frac(delta.quantile(.75))}",
    })
if rows:
    st.dataframe(pd.DataFrame(rows).sort_values(["call_type", "mode"]),
                 hide_index=True, use_container_width=True)
else:
    st.caption("no graded calls yet — the ledger needs maturing")
st.page_link("app/screens/track_record.py", label="Full forward-test / track record →", icon="🛰")
