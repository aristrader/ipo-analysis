"""Paper-portfolio sim + per-stock 'growth of ₹1L' (spec 2026-06-08).

Two questions, one engine:
 - PORTFOLIO: ₹1L into every APPLY call → equity vs ₹1L into Nifty (allottee + secondary lenses,
   realistic allotment haircut, survivorship-honest, split by mode).
 - PER-STOCK: growth_of_1l(isin) → 3 aligned series (at-IPO if-allotted / at-listing / Nifty).

Pure reader over calls_ledger + substrate + adjusted prices + Nifty. No new data. Free, on-ethos.
HONEST NOTE on the allottee lens: simulate() deploys a FULL ₹1L at the issue price *if allotted*
(see CAPITAL + _position_value(ipx, ...)). It is a BEST-CASE 'you won the lottery and got a full
fill' curve — it is NOT weighted by allotment probability and is NOT blended toward the
no-allotment baseline. Allotment realism (≈3.5% median allotment prob + adverse selection, which
collapses naive flip EV +21% → ~+2% per strat-flip-ev) is handled separately in the flip-EV
analysis, not folded into this curve. Read the secondary ('bought on listing') lens as the
realistic one; treat 'if allotted' as the lottery-win upper bound."""
import os
import bisect

import pandas as pd

from layer3 import config, spine

CAPITAL = 100_000.0          # ₹1 lakh fully invested per call (no idle-cash haircut — owner call:
                             # assume full ₹1L deployed, whether allotted-at-issue or bought-at-listing)
_NIFTY = {}


def _nifty():
    if "d" not in _NIFTY:
        d, c = [], []
        with open(config.ROOT / "data/reference/indices/nifty50.csv") as f:
            import csv
            for r in csv.DictReader(f):
                try:
                    d.append(pd.Timestamp(r["date"])); c.append(float(r["close"]))
                except (ValueError, KeyError):
                    continue
        pairs = sorted(zip(d, c))
        _NIFTY["d"] = [p[0] for p in pairs]; _NIFTY["c"] = [p[1] for p in pairs]
    return _NIFTY["d"], _NIFTY["c"]


def _nifty_at(ts):
    d, c = _nifty()
    i = bisect.bisect_right(d, pd.Timestamp(ts)) - 1
    return c[i] if i >= 0 else None


# ---------------------------------------------------------------- primitives
def _position_value(entry, exit_px, capital=CAPITAL):
    """₹ value of the full `capital` deployed at `entry`, now worth `exit_px`.
    exit_px=0 → wipeout → ₹0 (stays a number, counts in the aggregate)."""
    if entry is None or entry <= 0 or exit_px is None or pd.isna(entry) or pd.isna(exit_px):
        return None
    return capital * (float(exit_px) / float(entry))


def _exit_price(isin, sub_row, prices_root="data/prices"):
    """(adjusted exit value, exit DATE) — 'to today' (live) or terminal (delisted: wipeout→0,
    else last close). The exit DATE is returned so the Nifty benchmark can be anchored to the
    SAME date (P0 fix: a delisted name's stock value is years-stale; the benchmark must match)."""
    delisted = str(sub_row.get("delisted")) in ("True", "true", "1")
    p = os.path.join(prices_root, f"{isin}.csv")
    last_date = None
    if os.path.exists(p):
        try:
            pr = pd.read_csv(p)
            pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
            pr = pr.dropna(subset=["date"]).sort_values("date")
            if len(pr):
                last_date = pr["date"].iloc[-1]
                if delisted and str(sub_row.get("outcome_class")) == "wipeout":
                    return 0.0, last_date
                return float(pr["close"].astype(float).iloc[-1]), last_date
        except Exception:
            pass
    if delisted and str(sub_row.get("outcome_class")) == "wipeout":
        return 0.0, None
    return None, None


# ---------------------------------------------------------------- per-stock ₹1L
def growth_of_1l(isin, capital=CAPITAL, df=None, prices_root="data/prices"):
    """3 aligned series (long-form: date, series, value) from listing → today/terminal:
    at-IPO (if allotted) · at-listing · Nifty. Wipeout → goes to ₹0 and stays."""
    df = df if df is not None else spine.load_substrate()
    row = df[df["isin"] == isin]
    if row.empty:
        return None
    r = row.iloc[0]
    ld = pd.to_datetime(r.get("listing_date"), errors="coerce")
    ipx = pd.to_numeric(pd.Series([r.get("issue_price_adj")]), errors="coerce").iloc[0]
    lst = pd.to_numeric(pd.Series([r.get("adj_listing_close")]), errors="coerce").iloc[0]
    p = os.path.join(prices_root, f"{isin}.csv")
    if pd.isna(ld) or not os.path.exists(p):
        return None
    try:
        pr = pd.read_csv(p)
    except Exception:
        return None
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[pr["date"] >= ld].sort_values("date").reset_index(drop=True)
    if len(pr) < 5:
        return None
    wipe = str(r.get("delisted")) in ("True", "true", "1") and str(r.get("outcome_class")) == "wipeout"
    # I1 FIX: anchor at-listing on the ACTUAL first price row (not the substrate adj_listing_close,
    # which can be on a different adjustment basis / missing the listing-day row → bogus ₹4M starts).
    # This guarantees at-listing starts at exactly ₹1L. at-IPO is then the at-listing curve scaled by
    # the implied pop (close0/issue) — shown ONLY when that pop is sane (else the basis mismatched).
    base_close = float(pr["close"].iloc[0])
    if base_close <= 0:
        return None
    pop_factor = (base_close / float(ipx)) if (pd.notna(ipx) and ipx > 0) else None
    show_ipo = pop_factor is not None and 0.1 <= pop_factor <= 6.0   # sane implied pop band
    rows = []
    for _, d in pr.iterrows():
        px = 0.0 if wipe and d["date"] == pr["date"].iloc[-1] else float(d["close"])
        rows.append({"date": d["date"], "series": "at-listing", "value": capital * px / base_close})
        if show_ipo:
            # value if you'd entered at issue = at-listing value * pop_factor (same clean basis)
            rows.append({"date": d["date"], "series": "at-IPO (if allotted)",
                         "value": capital * (px / base_close) * pop_factor})
        n0, n1 = _nifty_at(pr["date"].iloc[0]), _nifty_at(d["date"])
        if n0 and n1:
            rows.append({"date": d["date"], "series": "Nifty", "value": capital * n1 / n0})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- portfolio
def simulate(ledger=None, df=None, capital=CAPITAL, prices_root="data/prices"):
    """Per-APPLY-call ₹1L outcome under both entry lenses + a per-call Nifty benchmark.
    Returns a per-position frame (mode-tagged). Aggregation/curves done by the caller/report."""
    led = ledger if ledger is not None else pd.read_csv("data/master/calls_ledger.csv")
    df = df if df is not None else spine.load_substrate()
    sub = {r["isin"]: r for _, r in df.iterrows()}
    buys = led[led["call_type"].isin(["APPLY", "EARLY_APPLY"])]
    rows = []
    for _, c in buys.iterrows():
        r = sub.get(c["isin"])
        if r is None:
            continue
        exit_px, exit_date = _exit_price(c["isin"], r, prices_root)
        if exit_px is None:
            continue
        ipx = pd.to_numeric(pd.Series([r.get("issue_price_adj")]), errors="coerce").iloc[0]
        lst = pd.to_numeric(pd.Series([r.get("adj_listing_close")]), errors="coerce").iloc[0]
        allottee = _position_value(ipx, exit_px, capital)          # full ₹1L at issue (if allotted)
        secondary = _position_value(lst, exit_px, capital)         # full ₹1L at listing (the HERO lens)
        ld = pd.to_datetime(r.get("listing_date"), errors="coerce")
        # P0 fix: anchor the Nifty leg to the SAME exit date as the stock (not now()), so a
        # delisted/stale position is compared over its OWN holding period, like-for-like.
        bench_end = exit_date if exit_date is not None else pd.Timestamp.now()
        n0, n1 = _nifty_at(ld), _nifty_at(bench_end)
        nifty_val = capital * n1 / n0 if (n0 and n1) else None
        rows.append({"isin": c["isin"], "name": c["name"], "type": c["type"], "mode": c["mode"],
                     "call_date": c["call_date"], "allottee_val": allottee,
                     "secondary_val": secondary, "nifty_val": nifty_val})
    return pd.DataFrame(rows)


def summary(positions):
    """Aggregate per-position frame into headline numbers, SPLIT BY MODE (never pooled)."""
    out = {}
    for mode, g in positions.groupby("mode"):
        for lens, col in (("allottee", "allottee_val"), ("secondary", "secondary_val")):
            # P0 fix: portfolio mult and Nifty mult MUST be over the SAME matched basket
            # (rows that have BOTH the lens value and a Nifty value) — else it's apples-to-oranges.
            m = g[[col, "nifty_val"]].apply(pd.to_numeric, errors="coerce").dropna()
            if m.empty:
                continue
            v, nif = m[col], m["nifty_val"]
            mults = (v / CAPITAL).sort_values()
            # outlier decomposition (T1): the mean can be one-winner-driven — show the honest spread
            drop1 = float(mults.iloc[:-1].mean()) if len(mults) > 1 else float(mults.mean())
            drop3 = float(mults.iloc[:-3].mean()) if len(mults) > 3 else drop1
            top3_share = float(mults.iloc[-3:].sum() / mults.sum()) if mults.sum() else None
            out[f"{mode}/{lens}"] = {
                "n": len(v), "deployed": CAPITAL * len(v), "value_now": float(v.sum()),
                "mult": float(mults.mean()),                       # the MEAN (sum/deployed)
                "median_mult": float(mults.median()),              # the TYPICAL position (T1)
                "p10_mult": float(mults.quantile(0.10)),
                "p90_mult": float(mults.quantile(0.90)),
                "mult_drop_top1": drop1, "mult_drop_top3": drop3,  # one-winner sensitivity
                "top3_share": top3_share,
                "nifty_mult": float(nif.sum() / (CAPITAL * len(nif))),   # avg per-call vs index (NOT a portfolio curve — T2)
                "win_rate": float((v > CAPITAL).mean()),
            }
    return out


def bootstrap_ci(positions, lens="secondary_val", mode=None, b=2000, seed=7):
    """Pure-Python 5th/95th-pct CI on the mean multiple (T1/D3) — resample positions with
    replacement. No scipy. Honest 'the 2.09x is not precise' band."""
    import random
    g = positions if mode is None else positions[positions["mode"] == mode]
    vals = [float(x) / CAPITAL for x in pd.to_numeric(g[lens], errors="coerce").dropna()]
    if len(vals) < 10:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(b):
        s = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
        means.append(sum(s) / len(s))
    means.sort()
    return (means[int(0.05 * b)], means[int(0.95 * b)])


def attribution(positions, lens="secondary_val", mode="historical_sim", top=5):
    """Best/worst APPLY picks by ₹ P&L (D2) — which calls carried or sank the basket."""
    g = positions[positions["mode"] == mode].copy()
    g["pnl"] = pd.to_numeric(g[lens], errors="coerce") - CAPITAL
    g = g.dropna(subset=["pnl"]).sort_values("pnl")
    cols = ["name", "type", "call_date", "pnl"]
    return {"worst": g.head(top)[cols].to_dict("records"),
            "best": g.tail(top)[cols].sort_values("pnl", ascending=False).to_dict("records")}
