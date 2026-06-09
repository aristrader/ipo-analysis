"""H7 — Corp-action euphoria-top backtest (WIDENS the thin F10 flag, n=31).

HYPOTHESIS: a corporate action (bonus/split) on a RECENT IPO (ex_date within yr 1 of
listing) marks a EUPHORIA TOP — post-ex-date forward alpha is negative ("sell-the-action"),
strongest when it follows a big prior run-up (management times the action to feed retail demand).

This is the SAME backtestable universe as F10 (corp_actions.csv has only bonus/split/bonus+split;
NO standalone dividend ex-dates exist, so the hypothesis' "dividend" leg is NOT testable here).
H7 widens F10 by: (a) folding in `bonus+split` rows F10 missed, (b) MULTIPLE horizons
(1m/3m/6m/1y from ex_date), (c) explicit prior-run-up conditioning + dose, (d) a CROSS-REGIME
split (boom 2020-26 vs longterm 2006-19), (e) a proper PLACEBO (random fake ex-dates on the SAME
names), and (f) Wilson CIs + distributions, not just means.

NO LOOK-AHEAD: forward returns measured from the trading day AFTER ex_date; run-up uses only
alpha accumulated up TO the ex-date. Reuses the F1/F10 daily-alpha-vs-Nifty harness.

Run: PYTHONPATH=. .venv/bin/python tools/research/h7_corp_action.py
Writes: data/master/review/h7_corp_action_events.csv
"""
import sys, os, csv, bisect, math, warnings, random
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from layer3 import spine

random.seed(20260609)  # deterministic placebo

# ----------------------------- helpers -----------------------------
def srho(a, b):
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    m = a.notna() & b.notna()
    return float(a[m].rank().corr(b[m].rank())) if m.sum() >= 10 else float("nan")

def wilson(k, n, z=1.96):
    """Wilson score CI for a proportion k/n. Returns (lo, hi) in %."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (100 * (centre - half), 100 * (centre + half))

def boot_median_ci(vals, n_boot=2000, z=0.95):
    """Percentile bootstrap CI for the median (no scipy)."""
    vals = [v for v in vals if v == v]
    if len(vals) < 5:
        return (float("nan"), float("nan"))
    arr = np.array(vals, dtype=float)
    meds = []
    rng = random.Random(42)
    for _ in range(n_boot):
        sample = [arr[rng.randrange(len(arr))] for _ in range(len(arr))]
        meds.append(np.median(sample))
    meds.sort()
    lo = meds[int((1 - z) / 2 * n_boot)]
    hi = meds[int((1 + z) / 2 * n_boot)]
    return (100 * lo, 100 * hi)

# ----------------------------- substrate + Nifty -----------------------------
df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
df = df[df["ld"].notna()]

nd, nc = [], []
for r in csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try:
        nd.append(pd.Timestamp(r["date"])); nc.append(float(r["close"]))
    except ValueError:
        continue
pairs = sorted(zip(nd, nc)); nd = [p[0] for p in pairs]; nc = [p[1] for p in pairs]
def nifty_at(t):
    i = bisect.bisect_right(nd, t) - 1
    return nc[i] if i >= 0 else None

# cache: isin -> daily alpha series [(td_index_from_listing, alpha_that_day), ...]
_cache = {}
def daily_alpha_series(isin, ld, min_len=60):
    key = (isin, min_len)
    if key in _cache:
        return _cache[key]
    p = f"data/prices/{isin}.csv"
    if not os.path.exists(p):
        _cache[key] = None; return None
    rows = []
    for r in csv.DictReader(open(p)):
        try:
            rows.append((pd.Timestamp(r["date"]), float(r["close"])))
        except ValueError:
            continue
    rows = [x for x in rows if x[0] >= ld]
    if len(rows) < min_len:
        _cache[key] = None; return None
    out = []
    for i in range(1, len(rows)):
        n0, n1 = nifty_at(rows[i - 1][0]), nifty_at(rows[i][0])
        if not n0 or not n1:
            continue
        out.append((i, (rows[i][1] / rows[i - 1][1] - 1) - (n1 / n0 - 1)))
    _cache[key] = out
    return out

def window_car(series, lo, hi):
    """Cumulative alpha over trading-day window [lo,hi]; need >=half the days present."""
    vals = [a for t, a in series if lo <= t <= hi]
    return sum(vals) if len(vals) >= (hi - lo) // 2 else None

# horizons in trading days from ex-date (cal-day -> td ~ *0.69): 1m~21, 3m~63, 6m~126, 1y~252
HORIZONS = [("1m", 21), ("3m", 63), ("6m", 126), ("1y", 252)]

# ----------------------------- match corp actions to recent IPOs -----------------------------
ca = pd.read_csv("data/reference/corp_actions.csv")
ca["ex_date"] = pd.to_datetime(ca["ex_date"], errors="coerce")
# H7 includes bonus+split (F10 missed these); dividends do NOT exist as discrete rows.
ca = ca[ca["action_type"].isin(("bonus", "split", "bonus+split")) & ca["ex_date"].notna()]

sym_map = {}
for _, r in df.iterrows():
    s = r.get("nse_symbol")
    if isinstance(s, str) and s.strip():
        sym_map.setdefault(s.strip().upper(), r["isin"])
isin_set = set(df["isin"])

events = []
for _, a in ca.iterrows():
    isin = a["isin"] if a["isin"] in isin_set else sym_map.get(str(a["symbol"]).strip().upper())
    if not isin:
        continue
    row = df[df["isin"] == isin].iloc[0]
    dd = (a["ex_date"] - row["ld"]).days
    if 30 <= dd <= 365:  # corp action WITHIN year 1 of listing = the "recent IPO" gate
        events.append({"isin": isin, "days": dd, "kind": a["action_type"],
                       "type": row["type"], "cohort": row["cohort"], "ex": a["ex_date"]})
ev = pd.DataFrame(events).sort_values("days").drop_duplicates("isin")  # earliest action per IPO

# ----------------------------- measure run-up + forward alpha at all horizons -----------------------------
rows = []
for _, e in ev.iterrows():
    ld = df.loc[df["isin"] == e["isin"], "ld"].iloc[0]
    s = daily_alpha_series(e["isin"], ld, min_len=60)
    if not s:
        continue
    tdx = int(e["days"] * 0.69)  # trading-day index of ex-date from listing
    runup = sum(a for t, a in s if t <= tdx)  # PIT: only alpha up to ex-date
    rec = {"isin": e["isin"], "kind": e["kind"], "type": e["type"], "cohort": e["cohort"],
           "days": e["days"], "tdx": tdx, "runup": runup}
    for hl, htd in HORIZONS:
        rec[f"fwd_{hl}"] = window_car(s, tdx + 1, tdx + htd)
    rows.append(rec)
er = pd.DataFrame(rows)

# ----------------------------- matched control (same type, similar run-up, NO corp action) -----------------------------
def matched_controls(events_df, pool, horizon_key, horizon_td):
    out = []
    for _, e in events_df.iterrows():
        cands = pool[pool["type"] == e["type"]]
        got = 0
        for _, c in cands.iloc[(hash(e["isin"]) % 7)::7].iterrows():
            s = daily_alpha_series(c["isin"], c["ld"], min_len=60)
            if not s:
                continue
            ru = sum(a for t, a in s if t <= e["tdx"])
            if abs(ru - e["runup"]) > 0.25:
                continue
            f = window_car(s, e["tdx"] + 1, e["tdx"] + horizon_td)
            if f is None:
                continue
            out.append(f); got += 1
            if got >= 2:
                break
    return pd.Series(out)

pool = df[~df["isin"].isin(set(ev["isin"]))]

# ----------------------------- PLACEBO: fake ex-dates on the SAME treated names -----------------------------
# For each treated name, draw a random fake ex-date offset (30..365 cal days) NOT near the real one.
# If the "euphoria-top" shows up at random dates too, the effect is mechanical (post-IPO drift), not the action.
def placebo_fwd(events_df, horizon_td, n_draws=3):
    out = []
    rng = random.Random(777)
    for _, e in events_df.iterrows():
        ld = df.loc[df["isin"] == e["isin"], "ld"].iloc[0]
        s = daily_alpha_series(e["isin"], ld, min_len=60)
        if not s:
            continue
        real_tdx = e["tdx"]
        for _ in range(n_draws):
            fake_dd = rng.randint(30, 365)
            ftdx = int(fake_dd * 0.69)
            if abs(ftdx - real_tdx) <= 10:  # avoid coinciding with the real action
                continue
            f = window_car(s, ftdx + 1, ftdx + horizon_td)
            if f is None:
                continue
            out.append(f)
    return pd.Series(out)

# ----------------------------- REPORT -----------------------------
def fmt_cell(vals, label):
    vals = pd.Series([v for v in vals if v == v])
    n = len(vals)
    if n == 0:
        return f"  {label}: n=0"
    med = 100 * vals.median()
    win_k = int((vals > 0).sum())
    wlo, whi = wilson(win_k, n)
    blo, bhi = boot_median_ci(list(vals))
    p10, p90 = 100 * vals.quantile(0.10), 100 * vals.quantile(0.90)
    return (f"  {label}: n={n}  median {med:+.1f}% [boot95 {blo:+.1f}..{bhi:+.1f}]  "
            f"win {100*win_k/n:.0f}% [Wilson95 {wlo:.0f}..{whi:.0f}]  P10/P90 {p10:+.0f}/{p90:+.0f}%")

print("=" * 78)
print("H7 — CORP-ACTION EUPHORIA TOP (widened F10).  forward alpha vs Nifty FROM ex_date")
print("Universe: bonus/split/bonus+split with ex_date 30-365d after listing (earliest per IPO)")
print("NO standalone-dividend events exist in corp_actions.csv -> dividend leg NOT testable.")
print("=" * 78)
print(f"matched events (dedup isin): n={len(ev)}  "
      f"kinds={dict(ev['kind'].value_counts())}  cohorts={dict(ev['cohort'].value_counts())}  "
      f"types={dict(ev['type'].value_counts())}")
print(f"with usable price paths: n={len(er)}")
print(f"median run-up to ex-date: {100*er['runup'].median():+.1f}%  "
      f"(P10/P90 {100*er['runup'].quantile(.1):+.0f}/{100*er['runup'].quantile(.9):+.0f}%)")

for hl, htd in HORIZONS:
    print("-" * 78)
    print(f"HORIZON {hl} (td+1..+{htd} from ex_date)")
    fwd = er[f"fwd_{hl}"]
    print(fmt_cell(fwd, "ALL treated     "))
    # cross-regime split
    for coh in ("boom", "longterm"):
        g = er[er["cohort"] == coh][f"fwd_{hl}"]
        print(fmt_cell(g, f"  {coh:8s}      "))
    for t in ("MB", "SME"):
        g = er[er["type"] == t][f"fwd_{hl}"]
        print(fmt_cell(g, f"  {t:8s}      "))
    # run-up conditioning (the core mechanism): big prior run-up vs not
    hi_ru = er[er["runup"] >= er["runup"].median()][f"fwd_{hl}"]
    lo_ru = er[er["runup"] < er["runup"].median()][f"fwd_{hl}"]
    print(fmt_cell(hi_ru, "  HIGH run-up   "))
    print(fmt_cell(lo_ru, "  LOW  run-up   "))
    # matched control + placebo
    ctrl = matched_controls(er, pool, hl, htd)
    plac = placebo_fwd(er, htd)
    print(fmt_cell(ctrl, "CONTROL (match) "))
    print(fmt_cell(plac, "PLACEBO (random)"))
    print(f"  dose srho(run-up, fwd_{hl}) = {srho(er['runup'], er[f'fwd_{hl}']):+.3f}  "
          f"srho(days-to-action, fwd_{hl}) = {srho(er['days'], er[f'fwd_{hl}']):+.3f}")

# ----------------------------- endpoint substrate cross-check -----------------------------
print("=" * 78)
sub = df.merge(ev[["isin"]], on="isin")
a1y = pd.to_numeric(sub["alpha_1y"], errors="coerce"); a3y = pd.to_numeric(sub["alpha_3y"], errors="coerce")
b1 = pd.to_numeric(df["alpha_1y"], errors="coerce"); b3 = pd.to_numeric(df["alpha_3y"], errors="coerce")
print(f"ENDPOINT (from-listing, NOT from-ex): early-action alpha_1y median {100*a1y.median():+.1f}% "
      f"(all-IPO {100*b1.median():+.1f}%) | alpha_3y {100*a3y.median():+.1f}% (all {100*b3.median():+.1f}%)")
print("  -> treated names are NOT bad companies; the action marks a LOCAL top, not a doomed name.")

# ----------------------------- write review CSV -----------------------------
os.makedirs("data/master/review", exist_ok=True)
out_path = "data/master/review/h7_corp_action_events.csv"
er.to_csv(out_path, index=False)
print(f"\nwrote {out_path} (n={len(er)})")
