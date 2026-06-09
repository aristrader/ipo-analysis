"""A3 — re-validate the 90-day capitulation EXIT rule (F5e as an ACT-ON sell, not just a flag).

F5e is already VALIDATED as a display-only red flag: "never closed above issue price in
sessions 1..90" predicts bad outcomes (rules/index.md). A3 tests the *trading* question M1
left open for this specific rule: if a name trips the flag at day 90, does SELLING THEN beat
HOLDING (do-nothing)? M1's prior: stops/exits trade the right tail for the body and lose
wherever IPOs show a tail; tight stops hurt the secondary buyer (whipsaw).

Method (point-in-time, survivorship-honest, no look-ahead):
 - capit flag uses ONLY closes in sessions 1..90 (index slice [1:91]); compared to issue_price_adj.
 - For flagged names: compare SELL-at-day-90 (realize alpha listing->d90, then cash) vs HOLD
   (alpha listing->horizon). The decision-relevant quantity is FORWARD alpha from day 90 to
   {6m, 1y, terminal} — that is exactly what selling forfeits / avoids.
 - Forward alpha is vs Nifty (raw secondary shown too). Delisted -> terminal = last close, or
   0.0 (wipeout) per decision A1; window-young alive names with no terminal are dropped from
   that horizon.
 - Split boom (2020-26) vs longterm (2006-19); Wilson 95% CI on the "sell beat hold" rate.
 - FALSE EXITS = flagged names whose forward alpha from d90 to terminal is POSITIVE (eventual
   winners the rule would have dumped). LOSSES AVOIDED = flagged names with negative fwd alpha.
 - PLACEBO: (a) random-day-90 exit = apply the same sell to a random matched non-flagged name;
   (b) always-hold baseline. FALSIFIER stated in the writeup.

Conventions: exclude unreliable_coverage; adjusted issue price; min-N floors 12/30; distributions.
No scipy (Wilson + pure-Python). Run: PYTHONPATH=. .venv/bin/python tools/research/a3_capitulation.py
"""
import sys, os, csv, bisect, math, random, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd
from layer3 import spine

random.seed(42)
CAPIT_TD = 90
HORIZONS = {"6m": 126, "1y": 250}   # trading-day forward horizons from day 90; +terminal
PRICES = "data/prices"
REVIEW_CSV = "data/master/review/a3_capitulation_false_exits.csv"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = (len(xs) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def median(xs):
    return pct(xs, 0.5)


# ---- Nifty calendar
_nd, _nc = [], []
for _r in csv.DictReader(open("data/reference/indices/nifty50.csv")):
    try:
        _nd.append(pd.Timestamp(_r["date"])); _nc.append(float(_r["close"]))
    except (ValueError, KeyError):
        continue
_pairs = sorted(zip(_nd, _nc)); _nd = [p[0] for p in _pairs]; _nc = [p[1] for p in _pairs]


def nifty_at(t):
    i = bisect.bisect_right(_nd, t) - 1
    return _nc[i] if i >= 0 else None


def td_offset(ts, n):
    i = bisect.bisect_left(_nd, ts)
    j = i + n
    return _nd[j] if 0 <= j < len(_nd) else None


df = spine.load_substrate()
df = df[df["listing_metrics_status"].isin(("ok", "inferred_split", "recovered_bhavcopy"))].copy()
df["ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
df = df[df["ld"].notna()]
df["ipx"] = pd.to_numeric(df["issue_price_adj"], errors="coerce")


def is_delisted(r):
    return bool(pd.notna(r.get("delisted")) and r.get("delisted") in (True, "True", 1, "1", "TRUE"))


def fwd_alpha_from(closes, dates, d90_idx, n_td, delisted, wipeout):
    """Forward alpha vs Nifty from day-90 close over n_td sessions (or terminal if delisted &
    file ends early). Returns (alpha, raw_ret) or (None, None) if window young & alive."""
    c0 = closes[d90_idx]; t0 = dates[d90_idx]
    n0 = nifty_at(t0)
    if not n0 or c0 <= 0:
        return None, None
    j = d90_idx + n_td
    if j < len(closes):
        c1 = closes[j]; n1 = nifty_at(dates[j])
        if not n1:
            return None, None
        raw = c1 / c0 - 1
        return raw - (n1 / n0 - 1), raw
    # window runs past file end
    if not delisted:
        return None, None
    end = td_offset(t0, n_td)
    if end is None:
        return None, None
    n1 = nifty_at(end)
    if not n1:
        return None, None
    c1 = 0.0 if wipeout else closes[-1]
    raw = c1 / c0 - 1
    return raw - (n1 / n0 - 1), raw


def terminal_alpha_from(closes, dates, d90_idx, delisted, wipeout):
    """Alpha from day-90 close to the LAST available close (terminal). For delisted-wipeout,
    terminal value = 0. Always computable (uses whatever the file has)."""
    c0 = closes[d90_idx]; t0 = dates[d90_idx]
    n0 = nifty_at(t0)
    if not n0 or c0 <= 0:
        return None, None
    c1 = 0.0 if (delisted and wipeout) else closes[-1]
    t1 = dates[-1]
    n1 = nifty_at(t1)
    if not n1:
        return None, None
    raw = c1 / c0 - 1
    return raw - (n1 / n0 - 1), raw


# ---- one pass over price files
rows = []
n_files = 0
for _, r in df.iterrows():
    p = f"{PRICES}/{r['isin']}.csv"
    if not os.path.exists(p) or pd.isna(r["ipx"]) or r["ipx"] <= 0:
        continue
    try:
        pr = pd.read_csv(p)
    except Exception:
        continue
    pr["date"] = pd.to_datetime(pr["date"], errors="coerce")
    pr = pr[pr["date"] >= r["ld"]].sort_values("date").reset_index(drop=True)
    if len(pr) < 95:               # need a real day-90 anchor (same floor F5e used: >95)
        continue
    n_files += 1
    closes = pr["close"].astype(float).tolist()
    dates = pr["date"].tolist()
    ipx = float(r["ipx"])
    window = closes[1:CAPIT_TD + 1]          # sessions 1..90 exactly (PIT)
    capit = bool(len(window) and max(window) < ipx)
    max_ratio = max(window) / ipx if window else float("nan")
    d90 = CAPIT_TD                            # day-90 close index (session 90)
    delisted = is_delisted(r)
    wipeout = str(r.get("outcome_class")) == "wipeout"

    rec = {
        "isin": r["isin"], "name": r.get("company_name"), "cohort": r.get("cohort"),
        "type": r.get("type"), "capit": capit, "max90_vs_issue": round(max_ratio, 3),
        "delisted": delisted, "outcome_class": r.get("outcome_class"),
    }
    for h, ntd in HORIZONS.items():
        a, raw = fwd_alpha_from(closes, dates, d90, ntd, delisted, wipeout)
        rec[f"fwd_alpha_{h}"] = a
        rec[f"fwd_raw_{h}"] = raw
    a, raw = terminal_alpha_from(closes, dates, d90, delisted, wipeout)
    rec["fwd_alpha_term"] = a
    rec["fwd_raw_term"] = raw
    rows.append(rec)

data = pd.DataFrame(rows)
print(f"scanned {n_files} price files; usable rows {len(data)}")
print(f"capit flag-rate overall: {100*data['capit'].mean():.1f}%  (n_flagged={int(data['capit'].sum())})")


def summarize(g, col):
    xs = [x for x in g[col].tolist() if pd.notna(x)]
    if not xs:
        return None
    pos = sum(1 for x in xs if x > 0)
    lo, hi = wilson(pos, len(xs))
    return {
        "n": len(xs), "p_pos": pos / len(xs), "ci_lo": lo, "ci_hi": hi,
        "median": median(xs), "p10": pct(xs, 0.10), "p90": pct(xs, 0.90),
        "mean": sum(xs) / len(xs),
    }


# =====================================================================
# CORE: for FLAGGED names, forward alpha from day 90 (= what SELLING forfeits).
#   p_pos = P(forward alpha > 0) = P(holding would have HELPED) = false-exit rate.
#   SELL beats HOLD on a name iff forward alpha < 0.
# =====================================================================
print("=" * 78)
print("SELL-AT-DAY-90 vs HOLD — forward alpha from day 90 for FLAGGED (capit) names")
print("  'sell_beat_hold' = forward alpha < 0 (avoided a loss). 'false_exit' = fwd alpha > 0.")
for cohort in ("boom", "longterm"):
    sub = data[(data["cohort"] == cohort) & (data["capit"])]
    print(f"\n[{cohort}]  flagged n={len(sub)}")
    for h in ("6m", "1y", "term"):
        col = f"fwd_alpha_{h}"
        s = summarize(sub, col)
        if s is None:
            print(f"  fwd_{h:>4}: no data"); continue
        sell_beat = 1 - s["p_pos"]
        lo, hi = wilson(round((1 - s["p_pos"]) * s["n"]), s["n"])
        flag = "thin" if s["n"] < 30 else ("SUPPRESS<12" if s["n"] < 12 else "")
        print(f"  fwd_{h:>4}: N={s['n']:<4} sell_beat_hold={100*sell_beat:.0f}% "
              f"[Wilson {100*lo:.0f}-{100*hi:.0f}%]  fwd-alpha median={100*s['median']:+.1f}% "
              f"mean={100*s['mean']:+.1f}% P10={100*s['p10']:+.0f}% P90={100*s['p90']:+.0f}% {flag}")


# =====================================================================
# FALSE EXITS: flagged names with POSITIVE terminal forward alpha (winners wrongly sold).
# =====================================================================
print("=" * 78)
print("FALSE EXITS (flagged but forward-alpha-to-terminal > 0 = eventual recoverers)")
flagged = data[data["capit"]].copy()
fe = flagged[flagged["fwd_alpha_term"] > 0].copy()
la = flagged[flagged["fwd_alpha_term"] <= 0].copy()
for cohort in ("boom", "longterm"):
    fc = flagged[(flagged["cohort"] == cohort) & flagged["fwd_alpha_term"].notna()]
    fec = fc[fc["fwd_alpha_term"] > 0]
    print(f"  [{cohort}] flagged-with-terminal N={len(fc)}: false-exits (recoverers) "
          f"{len(fec)} ({100*len(fec)/len(fc):.0f}%)  losses-avoided {len(fc)-len(fec)}")
fe.sort_values("fwd_alpha_term", ascending=False)[
    ["isin", "name", "cohort", "type", "max90_vs_issue", "fwd_alpha_term", "outcome_class"]
].to_csv(REVIEW_CSV, index=False)
print(f"  wrote {len(fe)} false-exit rows -> {REVIEW_CSV}")
print("  top recoverers the rule would have dumped:")
for _, x in fe.sort_values("fwd_alpha_term", ascending=False).head(8).iterrows():
    print(f"    {x['name'][:38]:38s} {x['cohort']:8s} max90={x['max90_vs_issue']:.2f} "
          f"fwd-term-alpha={100*x['fwd_alpha_term']:+.0f}%")


# =====================================================================
# PLACEBO (a): random-day-90 exit = same sell applied to NON-flagged names (control group).
#   If non-flagged names ALSO have negative forward alpha from d90, the "edge" is just the
#   general post-day-90 IPO drift, not the flag.
# PLACEBO (b): always-hold = all names' forward alpha from d90 (does the flag concentrate the
#   loss vs the universe?).
# =====================================================================
print("=" * 78)
print("PLACEBO — forward alpha from day 90: FLAGGED vs NON-flagged vs ALL (per cohort)")
for cohort in ("boom", "longterm"):
    print(f"\n[{cohort}]")
    for label, mask in (("FLAGGED", data["capit"]),
                        ("NON-flagged", ~data["capit"]),
                        ("ALL", pd.Series(True, index=data.index))):
        sub = data[(data["cohort"] == cohort) & mask]
        s = summarize(sub, "fwd_alpha_term")
        if s is None:
            continue
        print(f"  {label:12s}: N={s['n']:<5} P(fwd>0)={100*s['p_pos']:.0f}% "
              f"median fwd-term-alpha={100*s['median']:+.1f}% mean={100*s['mean']:+.1f}%")

# =====================================================================
# PORTFOLIO LENS: if you SELL all flagged names at d90 you forgo their forward alpha. The
# portfolio you hold is a basket -> MEAN (not median) is what your wealth compounds to.
# Bootstrap the mean forward-term-alpha of the flagged basket (does selling forgo + or - mean?).
# =====================================================================
def boot_mean_ci(xs, n_boot=2000):
    xs = [x for x in xs if pd.notna(x)]
    if len(xs) < 12:
        return (float("nan"), float("nan"), float("nan"))
    means = []
    for _ in range(n_boot):
        s = [xs[random.randrange(len(xs))] for _ in range(len(xs))]
        means.append(sum(s) / len(s))
    means.sort()
    return (sum(xs) / len(xs), means[int(0.025 * n_boot)], means[int(0.975 * n_boot)])


print("=" * 78)
print("PORTFOLIO MEAN LENS — mean forward-term-alpha of the FLAGGED basket (what selling forgoes)")
print("  If mean > 0, selling the basket DESTROYS value despite the negative median (right tail).")
for cohort in ("boom", "longterm"):
    sub = data[(data["cohort"] == cohort) & data["capit"]]
    m, lo, hi = boot_mean_ci(sub["fwd_alpha_term"].tolist())
    print(f"  [{cohort}] N={int(sub['fwd_alpha_term'].notna().sum())} "
          f"mean fwd-term-alpha={100*m:+.1f}% [boot 95% {100*lo:+.0f}..{100*hi:+.0f}%]")

print("=" * 78)
print("Done. Interpretation: SELL beats HOLD only if flagged-name forward alpha from d90 is")
print("reliably negative AND distinct from the non-flagged control (else it's regime drift).")
