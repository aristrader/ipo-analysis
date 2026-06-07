"""Calls engine — events → calls → grades (pure; no ledger I/O here, run_calls.py owns that).

Spec: docs/superpowers/specs/2026-06-07-calls-engine-design.md. Every call is anchored to an
EVENT DATE (close/listing/+21td/+90td/ex-date), built point-in-time (price slices end at the
call date), deduped by call_id, and graded later from its own date. Only VALIDATED rules emit
calls; thresholds are module constants (owner-tunable)."""
import bisect
import csv
import os

import pandas as pd

from layer3 import config

# ---------------------------------------------------------------- constants
LEDGER_COLUMNS = [
    "call_id", "isin", "name", "type", "cohort", "call_date", "call_type", "mode",
    "rules_fired", "score", "score_quintile", "n14_flags", "tape_state", "crowding_pctl",
    "pop_pct", "alpha_1m", "alpha_3m", "alpha_1y", "early_final_agree",
    "grade_status", "graded_at",
]
APPLY_QUINTILE = 5          # top quintile within segment
AVOID_QUINTILE = 1          # bottom quintile
AVOID_FLAGS = 2             # >=2 N14 flags = avoid regardless of score
PERSIST_TD = 21             # month-1 anchor (trading days)
CAPIT_TD = 90               # F5e day-90 checkpoint
CA_WINDOW_DAYS = (30, 365)  # F10: ex-date 30..365 calendar days post-listing
GRADE_TD = {"alpha_1m": 21, "alpha_3m": 63, "alpha_1y": 250}

_CAL = {}


# ---------------------------------------------------------------- calendar
def _nifty():
    if "d" not in _CAL:
        dates, closes = [], []
        with open(config.ROOT / "data/reference/indices/nifty50.csv") as f:
            for r in csv.DictReader(f):
                try:
                    dates.append(pd.Timestamp(r["date"])); closes.append(float(r["close"]))
                except (ValueError, KeyError):
                    continue
        pairs = sorted(zip(dates, closes))
        _CAL["d"] = [p[0] for p in pairs]; _CAL["c"] = [p[1] for p in pairs]
    return _CAL["d"], _CAL["c"]


def td_offset(ts, n):
    """Trading day ts + n sessions on the Nifty calendar (None if off the end)."""
    if pd.isna(ts):
        return None
    d, _ = _nifty()
    i = bisect.bisect_left(d, ts)
    return d[i + n] if 0 <= i + n < len(d) else None


def _nifty_at(t):
    d, c = _nifty()
    i = bisect.bisect_right(d, t) - 1
    return c[i] if i >= 0 else None


# ---------------------------------------------------------------- events
def events_between(d0, d1, df, corp_actions):
    """Dated call events in [d0,d1] from the substrate + corp actions. Excludes
    unreliable_coverage rows. Returns sorted [{date,kind,isin,row}]."""
    d0, d1 = pd.Timestamp(d0), pd.Timestamp(d1)
    pool = df[df.get("listing_metrics_status").astype(str) != "unreliable_coverage"]
    out = []

    def add(ts, kind, row):
        if ts is not None and pd.notna(ts) and d0 <= ts <= d1:
            out.append({"date": ts.strftime("%Y-%m-%d"), "kind": kind,
                        "isin": row["isin"], "row": row})

    for _, r in pool.iterrows():
        ld = pd.to_datetime(r.get("listing_date"), errors="coerce")
        add(pd.to_datetime(r.get("close_date"), errors="coerce"), "verdict", r)
        add(ld, "track", r)
        if pd.notna(ld):
            add(td_offset(ld, PERSIST_TD), "persist", r)
            add(td_offset(ld, CAPIT_TD), "capit", r)
    if corp_actions is not None and len(corp_actions):
        sym_map = {}
        if "nse_symbol" in pool.columns:
            for _, r in pool.iterrows():
                s = r.get("nse_symbol")
                if isinstance(s, str) and s.strip():
                    sym_map[s.strip().upper()] = r["isin"]
        by_isin = {r["isin"]: r for _, r in pool.iterrows()}
        ca = corp_actions[corp_actions["action_type"].isin(("bonus", "split"))]
        for _, a in ca.iterrows():
            isin = a["isin"] if a["isin"] in by_isin else \
                sym_map.get(str(a.get("symbol", "")).strip().upper())
            if not isin:
                continue
            row = by_isin[isin]
            ld = pd.to_datetime(row.get("listing_date"), errors="coerce")
            ex = pd.to_datetime(a.get("ex_date"), errors="coerce")
            if pd.isna(ld) or pd.isna(ex):
                continue
            dd = (ex - ld).days
            if CA_WINDOW_DAYS[0] <= dd <= CA_WINDOW_DAYS[1]:
                add(ex, "corp_action", row)
    out.sort(key=lambda e: e["date"])
    return out


# ---------------------------------------------------------------- pit scores
def add_quintiles(pit, df):
    """Per-segment score quintiles (1..5) on a PIT-scores frame {isin, score, n14_flags}."""
    pit = pit.merge(df[["isin", "type"]], on="isin", how="left")
    pit["score_quintile"] = None
    for seg, g in pit.groupby("type"):
        s = pd.to_numeric(g["score"], errors="coerce")
        if s.notna().sum() >= 5:
            pit.loc[g.index, "score_quintile"] = pd.qcut(
                s.rank(method="first"), 5, labels=False, duplicates="drop") + 1
        else:                                           # tiny pools: rank thirds -> 1/3/5
            r = s.rank(pct=True)
            pit.loc[g.index, "score_quintile"] = r.map(
                lambda p: 5 if p > 0.8 else (1 if p <= 0.2 else 3))
    return pit


# ---------------------------------------------------------------- context
def context_at(date, df):
    """Tape temp (trailing-60d median pop of PRIOR listers) + crowding (prior-90d listing
    count percentile). Point-in-time: priors strictly before `date`."""
    ts = pd.Timestamp(date)
    ld = pd.to_datetime(df["listing_date"], errors="coerce")
    pop = pd.to_numeric(df.get("adj_listing_gain_open"), errors="coerce")
    prior = ld < ts
    w = pop[prior & (ld >= ts - pd.Timedelta(days=60))].dropna()
    if len(w) < 5:
        return {"tape_state": "unknown", "crowding_pctl": None}
    cur = w.median()
    # history of trailing medians at each prior listing date -> percentile of current
    hist = []
    for t in ld[prior].dropna().sort_values().unique()[-250:]:
        t = pd.Timestamp(t)
        h = pop[(ld < t) & (ld >= t - pd.Timedelta(days=60))].dropna()
        if len(h) >= 5:
            hist.append(h.median())
    pctl = (pd.Series(hist) < cur).mean() * 100 if hist else None
    tape = "unknown" if pctl is None else ("hot" if pctl > 67 else "cold" if pctl < 33 else "neutral")
    cnt = int((prior & (ld >= ts - pd.Timedelta(days=90))).sum())
    cnt_hist = [int(((ld < t) & (ld >= t - pd.Timedelta(days=90))).sum())
                for t in ld[prior].dropna().sort_values().unique()[-250:]]
    crowd = float((pd.Series(cnt_hist) < cnt).mean() * 100) if cnt_hist else None
    return {"tape_state": tape, "crowding_pctl": round(crowd, 1) if crowd is not None else None}


# ---------------------------------------------------------------- prices
def _prices_to(isin, listing, call_date, prices_root):
    """Closes from listing..call_date INCLUSIVE — the point-in-time slice (never beyond)."""
    p = os.path.join(prices_root, f"{isin}.csv")
    if not os.path.exists(p):
        return None
    pr = pd.read_csv(p)
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[(pr["date"] >= pd.Timestamp(listing)) & (pr["date"] <= pd.Timestamp(call_date))]
    return pr.reset_index(drop=True) if len(pr) else None


# ---------------------------------------------------------------- make_call
def make_call(event, pit, df, prices_root="data/prices", mode="historical_sim", ctx=None):
    """One event -> one call dict (all LEDGER_COLUMNS; grades pending). Point-in-time:
    only prices dated <= event date are read. ctx: precomputed context_at result (optional)."""
    r = event["row"]
    kind, date, isin = event["kind"], event["date"], event["isin"]
    p = pit[pit["isin"] == isin]
    score = float(p["score"].iloc[0]) if len(p) and pd.notna(p["score"].iloc[0]) else None
    quint = int(p["score_quintile"].iloc[0]) if len(p) and pd.notna(p["score_quintile"].iloc[0]) else None
    flags = int(p["n14_flags"].iloc[0]) if len(p) and pd.notna(p["n14_flags"].iloc[0]) else None
    rules, call_type = [], None

    if kind == "verdict":
        if quint is not None and flags is not None:
            if quint >= APPLY_QUINTILE and flags == 0:
                call_type = "APPLY"
            elif quint <= AVOID_QUINTILE or flags >= AVOID_FLAGS:
                call_type = "AVOID"
            else:
                call_type = "NEUTRAL"
            rules += [f"score_q={quint}", f"n14_flags={flags}"]
        else:
            call_type = "NEUTRAL"
            rules.append("score=unknown")
    elif kind == "track":
        call_type = "TRACK"
    elif kind == "persist":
        pr = _prices_to(isin, r.get("listing_date"), date, prices_root)
        if pr is None or len(pr) < 10:
            return None
        rets = pr["close"].astype(float).pct_change().dropna()
        ratio = float((rets > 0).mean())
        call_type = "PERSIST_HOLD" if ratio >= 0.5 else "PERSIST_EXIT_LEAN"
        rules.append(f"up_day_ratio={ratio:.2f}")
    elif kind == "capit":
        pr = _prices_to(isin, r.get("listing_date"), date, prices_root)
        ipx = pd.to_numeric(pd.Series([r.get("issue_price_adj")]), errors="coerce").iloc[0]
        if pr is None or len(pr) < 60 or pd.isna(ipx) or ipx <= 0:
            return None
        # F5e window = sessions 1..90 exactly (index cap + the date slice = belt and braces)
        closes = pr["close"].astype(float).values[1:CAPIT_TD + 1]
        capit = bool(len(closes) and max(closes) < float(ipx))
        call_type = "EXIT_REVIEW" if capit else "CLEARED_ISSUE"
        rules.append(f"max_close_vs_issue={max(closes)/float(ipx):.2f}" if len(closes) else "no_px")
    elif kind == "corp_action":
        call_type = "TAKE_PROFITS"
        rules.append("early_corp_action=1")
    if call_type is None:
        return None

    ctx = ctx if ctx is not None else context_at(date, df)
    return {
        "call_id": f"{isin}|{call_type}|{date}", "isin": isin,
        "name": r.get("company_name"), "type": r.get("type"), "cohort": r.get("cohort"),
        "call_date": date, "call_type": call_type, "mode": mode,
        "rules_fired": ";".join(rules) or "-",
        "score": score, "score_quintile": quint, "n14_flags": flags,
        "tape_state": ctx["tape_state"], "crowding_pctl": ctx["crowding_pctl"],
        "pop_pct": None, "alpha_1m": None, "alpha_3m": None, "alpha_1y": None,
        "early_final_agree": None, "grade_status": "pending", "graded_at": None,
    }


# ---------------------------------------------------------------- walk
def walk(df, pit, d0, d1, mode, ledger=None, prices_root="data/prices", corp_actions=None):
    """Generate calls for [d0,d1]; dedupe against `ledger` by call_id (idempotent;
    chunked walks == one-shot walk). Returns the combined ledger frame."""
    ca = corp_actions if corp_actions is not None else _load_corp_actions()
    have = set(ledger["call_id"]) if ledger is not None and len(ledger) else set()
    ctx_cache = {}
    rows = []
    for ev in events_between(d0, d1, df, ca):
        if ev["date"] not in ctx_cache:
            ctx_cache[ev["date"]] = context_at(ev["date"], df)
        c = make_call(ev, pit, df, prices_root=prices_root, mode=mode, ctx=ctx_cache[ev["date"]])
        if c and c["call_id"] not in have:
            have.add(c["call_id"])
            rows.append(c)
    new = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    if ledger is not None and len(ledger):
        return pd.concat([ledger, new], ignore_index=True)
    return new


def _load_corp_actions():
    p = config.ROOT / "data/reference/corp_actions.csv"
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


# ---------------------------------------------------------------- grading
def _alpha(closes_df, start_ts, n_td):
    """Alpha vs Nifty from the first close ON/AFTER start_ts over n_td sessions (None if young)."""
    pr = closes_df[closes_df["date"] >= start_ts].reset_index(drop=True)
    if len(pr) <= n_td:
        return None
    c0, c1 = float(pr.iloc[0]["close"]), float(pr.iloc[n_td]["close"])
    n0, n1 = _nifty_at(pr.iloc[0]["date"]), _nifty_at(pr.iloc[n_td]["date"])
    if not n0 or not n1 or c0 <= 0:
        return None
    return (c1 / c0 - 1) - (n1 / n0 - 1)


def grade_calls(ledger, df, prices_root="data/prices", today=None):
    """Fill alpha_1m/3m/1y + pop for pending/partial rows. `final` rows are NEVER touched.
    APPLY/AVOID/NEUTRAL/EARLY_*/TRACK grade from LISTING (allottee/owner view); the rest
    grade forward from their own call_date."""
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.now().normalize()
    led = ledger.copy()
    sub = {r["isin"]: r for _, r in df.iterrows()}
    px_cache = {}
    for i, row in led.iterrows():
        if row["grade_status"] == "final":
            continue
        isin = row["isin"]
        if isin not in px_cache:
            p = os.path.join(prices_root, f"{isin}.csv")
            if os.path.exists(p):
                pr = pd.read_csv(p)
                pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
                px_cache[isin] = pr.sort_values("date")
            else:
                px_cache[isin] = None
        pr = px_cache[isin]
        if pr is None:
            continue
        r = sub.get(isin, {})
        from_listing = str(row["call_type"]).split("_")[0] in ("APPLY", "AVOID", "NEUTRAL", "EARLY", "TRACK")
        anchor = pd.to_datetime(r.get("listing_date"), errors="coerce") if from_listing \
            else pd.Timestamp(row["call_date"])
        if pd.isna(anchor):
            continue
        done = 0
        for col, ntd in GRADE_TD.items():
            a = _alpha(pr, anchor, ntd)
            if a is not None:
                led.loc[i, col] = round(float(a), 4)
                done += 1
        if from_listing:
            pop = pd.to_numeric(pd.Series([r.get("adj_listing_gain_open")]), errors="coerce").iloc[0]
            if pd.notna(pop):
                led.loc[i, "pop_pct"] = round(float(pop) * 100, 2)
        led.loc[i, "grade_status"] = "final" if done == len(GRADE_TD) else \
            ("partial" if done else "pending")
        led.loc[i, "graded_at"] = today.strftime("%Y-%m-%d")
    return led
