"""Shared UI helpers for the Phase-2 multipage app.

Bloomberg-for-one-person: industrial/utilitarian terminal. Color is SIGNAL only.
Everything here is pure presentation + cached loaders over the engine, the ledger,
the live board, and the (optional) evidence records. NOT financial advice.

Contract:
- `chip(status)`  — the ONE trust-chip helper. Exactly four statuses.
- formatters `money`, `pct`, `pct_pp`, `frac`
- as-of stamps from substrate / ledger / board
- cached loaders (`load_df`, `load_ledger`, `load_board`, `load_records`, `load_families`)
- `predict_cached(query)` keyed on the query dict
- `load_prices(isin)` lazy per-ISIN, cached
- min-N display guard `n_floor(n)`
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from layer3 import config, spine

ROOT = config.ROOT
MIN_N = config.MIN_N_HINT            # the spec's min-N floor = config.MIN_N_HINT
MIN_N_FULL = config.MIN_N_TRADABLE   # >= this => a full claim

# ---------------------------------------------------------------- trust chips
# status -> (symbol, label, bg, fg). The contract: exactly four.
_CHIP = {
    "validated":     ("✓", "VALIDATED",        "#0f5132", "#d1e7dd"),
    "display":       ("~", "DISPLAY-ONLY",     "#664d03", "#fff3cd"),
    "thin":          ("⚠", "THIN / HYPOTHESIS", "#7a3e00", "#ffe1c2"),
    "rejected":      ("✗", "REJECTED",         "#41464b", "#e2e3e5"),
}
# friendly aliases so callers can pass record.status / verdict words
_ALIAS = {
    "in_score": "validated", "in-score": "validated", "validated_cross_regime": "validated",
    "✓": "validated", "ok": "validated",
    "display_only": "display", "display-only": "display", "watchlist": "thin",
    "~": "display",
    "hypothesis": "thin", "thin_n": "thin", "validated_thin": "thin", "⚠": "thin",
    "parked": "thin",
    "reject": "rejected", "graveyard": "rejected", "✗": "rejected",
}


def chip_status(status: str) -> str:
    """Normalize any incoming status string to one of the four canonical keys."""
    if status is None:
        return "display"
    s = str(status).strip().lower().replace(" ", "_")
    if s in _CHIP:
        return s
    return _ALIAS.get(s, "display")


def chip(status: str, note: str | None = None) -> str:
    """Return an inline HTML badge string. Use inside st.markdown(..., unsafe_allow_html=True).

    `status` may be a canonical key (validated/display/thin/rejected) or a friendly alias.
    `note` appends a short qualifier inside the chip (e.g. 'VALIDATED-THIN (n=31)').
    """
    key = chip_status(status)
    sym, label, fg, bg = _CHIP[key]
    text = f"{sym} {label}" + (f" — {note}" if note else "")
    return (f"<span style='background:{bg};color:{fg};border-radius:3px;padding:1px 6px;"
            f"font:600 11px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;"
            f"white-space:nowrap;letter-spacing:.02em;'>{text}</span>")


def chips(*items) -> str:
    """Join several chips with a small gap."""
    return " ".join(items)


# ---------------------------------------------------------------- formatters
def money(cr) -> str:
    """Rupees-crore formatter."""
    if cr is None or (isinstance(cr, float) and pd.isna(cr)):
        return "—"
    try:
        cr = float(cr)
    except (TypeError, ValueError):
        return "—"
    if cr >= 1000:
        return f"₹{cr/1000:,.2f}k cr"
    return f"₹{cr:,.0f} cr"


def frac(x, digits=0) -> str:
    """A fraction (0.12 -> +12%)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{100*x:+.{digits}f}%"


def pct(x, digits=0) -> str:
    """An already-percent value (12.0 -> +12%)."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{x:+.{digits}f}%"


def pct_pp(x, digits=0) -> str:
    """Percentage-points (lift), signed."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"{x:+.{digits}f}pp"


def match_cond(query: dict, key: str, cond) -> bool:
    """Evaluate one applies_predicate condition against a query/row dict. Defensive:
    cond may be a literal (==), or a dict {op: value} with ops gte/lte/gt/lt/eq/in/neq."""
    val = query.get(key)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    try:
        if isinstance(cond, dict):
            for op, target in cond.items():
                if op in ("gte", ">="):
                    if not float(val) >= float(target): return False
                elif op in ("lte", "<="):
                    if not float(val) <= float(target): return False
                elif op in ("gt", ">"):
                    if not float(val) > float(target): return False
                elif op in ("lt", "<"):
                    if not float(val) < float(target): return False
                elif op in ("eq", "=="):
                    if not val == target: return False
                elif op in ("neq", "!="):
                    if val == target: return False
                elif op == "in":
                    if val not in target: return False
            return True
        return val == cond
    except (TypeError, ValueError):
        return False


def n_floor(n) -> str | None:
    """Min-N display guard. Returns a 'too few' string if below floor, else None
    (caller shows the real number)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "N unknown"
    if n < MIN_N:
        return f"N={n} — too few to say"
    return None


# ---------------------------------------------------------------- global style + nav helpers
_STYLE = """
<style>
/* Bloomberg-for-one-person: paper bg, near-black text, monospace numbers as signal. */
:root { --ink:#16181d; --paper:#fbfbf9; --rule:#e4e2da; }
html, body, [class*="css"] { color: var(--ink); }
.stApp { background: var(--paper); }
/* monospace face for numeric metrics + code/IDs */
[data-testid="stMetricValue"], [data-testid="stMetricDelta"], code, kbd, .mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, "Cascadia Mono", monospace !important;
    font-variant-numeric: tabular-nums;
}
[data-testid="stMetricLabel"] { letter-spacing:.02em; text-transform:uppercase; font-size:11px; opacity:.75; }
/* terminal density: tighter dataframes + dividers */
hr { border-color: var(--rule); margin: .6rem 0; }
[data-testid="stMetric"] { padding: 2px 0; }
/* the regime banner & section cards */
.term-banner { border:1px solid var(--rule); border-left:4px solid var(--ink);
    background:#fff; padding:10px 14px; border-radius:4px; margin-bottom:4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:13px; }
.term-card { border:1px solid var(--rule); background:#fff; padding:12px 14px;
    border-radius:5px; margin-bottom:8px; }
.term-card h4 { margin:0 0 4px 0; font-size:14px; }
.asof { font-family: ui-monospace, Menlo, monospace; font-size:11px; opacity:.6; }
.verdict-engage { color:#0f5132; font-weight:700; }
.verdict-selective { color:#664d03; font-weight:700; }
.verdict-wait { color:#842029; font-weight:700; }
</style>
"""


def inject_style():
    """Inject the one allowed CSS block. Idempotent within a run."""
    st.markdown(_STYLE, unsafe_allow_html=True)


def one_liner(text: str):
    """The 'what am I looking at' sentence at the top of every screen."""
    st.caption(text)


def asof_line(*parts) -> str:
    """Render an as-of stamp line from (label, value) pairs."""
    bits = [f"{lab} {val}" for lab, val in parts if val is not None]
    return " · ".join(bits)


def page_link_isin(isin, label, *, disabled=False):
    """Cross-link to the IPO Detail page for an ISIN (the universal drill-down)."""
    if not isin or (isinstance(isin, float) and pd.isna(isin)):
        st.caption(f"{label} (no ISIN on file — detail unavailable)")
        return
    try:
        st.page_link("app/screens/ipo_detail.py", label=f"→ {label}",
                     icon="🔎")
    except Exception:
        # query-param form fallback
        st.markdown(f"[→ {label}](?isin={isin})")


# ---------------------------------------------------------------- cached loaders
@st.cache_data(show_spinner=False)
def load_df(exclude_low_quality: bool = False) -> pd.DataFrame:
    return spine.load_substrate(exclude_low_quality=exclude_low_quality)


@st.cache_data(show_spinner=False)
def sectors() -> list:
    return sorted(load_df()["broad_sector"].dropna().unique())


@st.cache_data(show_spinner=False)
def load_ledger() -> pd.DataFrame | None:
    p = ROOT / "data/master/calls_ledger.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["call_date"] = pd.to_datetime(df["call_date"], errors="coerce")
    df["graded_at"] = pd.to_datetime(df["graded_at"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_board() -> dict | None:
    p = ROOT / "data/live/board.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (ValueError, OSError):
        return None


@st.cache_data(show_spinner=False)
def load_records() -> list:
    """Evidence-Browser signal records, written by the records agent. Empty if not yet generated."""
    p = ROOT / "app/records/signals.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, list) else data.get("records", [])
    except (ValueError, OSError):
        return []


@st.cache_data(show_spinner=False)
def load_families() -> list:
    p = ROOT / "app/records/families.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, list) else data.get("families", [])
    except (ValueError, OSError):
        return []


@st.cache_data(show_spinner=False)
def load_prices(isin: str) -> pd.DataFrame | None:
    """Lazy per-ISIN daily price load (cached). Detail page only."""
    if not isin:
        return None
    p = ROOT / "data/prices" / f"{isin}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_corp_actions() -> pd.DataFrame | None:
    p = ROOT / "data/reference/corp_actions.csv"
    if not p.exists():
        return None
    return pd.read_csv(p)


@st.cache_data(show_spinner="Scoring…")
def predict_cached(query: dict, profile: str = "data_informed", exclude_low_quality: bool = False):
    """predict() cached, keyed on the (hashable) query dict + profile."""
    from layer3.predictor.predict import predict
    return predict(dict(query), df=load_df(exclude_low_quality), profile=profile)


# ---------------------------------------------------------------- as-of stamps
def as_of_substrate() -> str:
    return str(config.AS_OF_DATE)


def as_of_ledger(ledger) -> str:
    if ledger is None or ledger.empty:
        return "never"
    m = ledger["graded_at"].max()
    return m.strftime("%Y-%m-%d") if pd.notna(m) else "never"


def as_of_board(board) -> str:
    if not board:
        return "never"
    return str(board.get("fetched_at", "never"))


# ---------------------------------------------------------------- regime banner
@st.cache_data(show_spinner=False)
def regime_read():
    """Compute the persistent regime banner read from substrate (point-in-time today).

    Returns dict: nifty_3m (frac|None), tape_state, crowding_pctl, verdict.
    Honest about missing data — never fabricates.
    """
    from layer3 import context, calls
    today = pd.Timestamp(datetime.now().date())
    df = load_df()
    try:
        nifty = context.nifty_mom_3m(today)
    except Exception:
        nifty = None
    try:
        ctx = calls.context_at(today, df)
    except Exception:
        ctx = {"tape_state": "unknown", "crowding_pctl": None}
    tape = ctx.get("tape_state", "unknown")
    crowd = ctx.get("crowding_pctl")
    # one-line verdict: cold tape => engage selectively; hot+crowded => wait
    if tape == "cold":
        verdict = "SELECTIVE"          # cold tape historically the better entry, but still selective
    elif tape == "hot" and (crowd or 0) > 67:
        verdict = "WAIT"
    elif tape == "hot":
        verdict = "SELECTIVE"
    else:
        verdict = "SELECTIVE"
    return {"nifty_3m": nifty, "tape_state": tape, "crowding_pctl": crowd, "verdict": verdict}


def render_regime_banner():
    """The persistent regime banner (HOME / Recommendations / Track-Record)."""
    r = regime_read()
    ledger = load_ledger()
    board = load_board()
    tape = r["tape_state"]
    tape_word = {"cold": "COLD", "hot": "HOT", "neutral": "NEUTRAL"}.get(tape, "UNKNOWN")
    vclass = {"ENGAGE": "verdict-engage", "SELECTIVE": "verdict-selective",
              "WAIT": "verdict-wait"}.get(r["verdict"], "verdict-selective")
    nifty_txt = frac(r["nifty_3m"], 1) if r["nifty_3m"] is not None else "n/a"
    crowd_txt = f"{r['crowding_pctl']:.0f}th pctl" if r["crowding_pctl"] is not None else "n/a"
    line1 = (f"Nifty 3m: <b>{nifty_txt}</b> &nbsp;|&nbsp; "
             f"IPO tape (F7): <b>{tape_word}</b> {chip('validated')} &nbsp;|&nbsp; "
             f"crowding: {crowd_txt} {chip('display')}")
    line2 = (f"→ verdict: <span class='{vclass}'>{r['verdict']}</span> &nbsp;&nbsp;"
             f"<span class='asof'>as-of {as_of_substrate()} · "
             f"ledger graded {as_of_ledger(ledger)} · board {as_of_board(board)}</span>")
    st.markdown(f"<div class='term-banner'>{line1}<br>{line2}</div>", unsafe_allow_html=True)
    st.caption("Nifty 3-month momentum is CONTEXT only (rejected as a stand-alone signal). "
               "Tape temperature (F7) is cross-regime validated; crowding is display-only.")
    return r
