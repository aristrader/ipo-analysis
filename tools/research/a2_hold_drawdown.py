"""A2 — hold-through-drawdown / post-listing CONVICTION overlay.

THE QUESTION (a HOLD/CONVICTION overlay, NOT a new buy trigger): for a name that is
UNDERWATER post-listing at decision day D, is there a point-in-time STRENGTH signal that
distinguishes "dull-but-building-strength -> KEEP HOLDING" from "dead money -> exit",
that BEATS do-nothing (always-hold) cross-regime?

This is DIFFERENT from A3 (which tested a BLANKET sell on the F5e capitulation flag and found
selling loses). A2 tests a CONDITIONAL exit: among underwater names, EXIT the WEAK ones and
HOLD the STRONG ones, where strength is a point-in-time price-path signal computed from sessions
1..D only. The decision the overlay makes is "exit the weak underwater names"; do-nothing = hold
all underwater names. If the strength signal carries information, the EXITED (weak) basket should
have reliably WORSE forward alpha than the KEPT (strong) basket AND than hold-all — and must beat
do-nothing on the MEAN (the right-tail trap from M1: an exit that trades the tail for the body
loses where IPOs have tails).

Method (point-in-time, survivorship-honest, no look-ahead):
 - UNDERWATER at day D := close[D] < issue_price_adj (the allottee is in a drawdown). Decision day
   D = 90 trading days (the established F5e/A3 checkpoint); robustness re-run at D=126.
 - STRENGTH signal S computed ONLY from sessions 0..D (closes, volumes, Nifty) — strictly PIT:
     * up_day_ratio    : fraction of up-closes in the window
     * reclaim         : close[D]/min(close[0..D]) - 1  (recovery off the trough; "higher lows")
     * rs_vs_nifty     : (close[D]/close[0]) / (nifty[D]/nifty[0]) - 1  (relative strength)
     * vol_trend       : mean(vol last third) / mean(vol first third) - 1
   A composite STRENGTH = mean of within-underwater-group percentile ranks of the four (each PIT).
   "STRONG" = top half of the composite among underwater names; "WEAK" = bottom half.
 - FORWARD alpha vs Nifty measured FROM day D to {6m, 1y, terminal} — exactly what exiting forfeits
   / holding captures. Delisted -> terminal = last close (0.0 if wipeout, decision A1); young-alive
   names with no full window are dropped from that horizon.
 - EXIT-WEAK overlay basket = forward alpha of WEAK names is forfeited (you sell), STRONG names held.
   do-nothing = hold ALL underwater names. The overlay BEATS do-nothing iff
   mean(STRONG-held basket, having dropped WEAK) > mean(all underwater) -> i.e. the WEAK basket
   mean forward alpha is reliably NEGATIVE and below the STRONG mean.
 - Cross-regime: boom (2020-26) vs longterm (2006-19), and MB/SME where N permits.
 - PLACEBO: shuffle the STRONG/WEAK labels among underwater names (1000x) -> if the real
   STRONG-minus-WEAK forward-alpha gap is inside the shuffled null, the signal is noise.
 - RIGHT-TAIL CHECK (M1): report MEAN (not just median); a per-name "exit wins" majority with a
   positive basket mean = the median trap. Bootstrap the WEAK basket mean.

Conventions: exclude unreliable_coverage; adjusted issue price; min-N 12/30; distributions;
Wilson + bootstrap; no scipy. Run: PYTHONPATH=. .venv/bin/python tools/research/a2_hold_drawdown.py
"""
import sys, os, csv, bisect, math, random, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd
from layer3 import spine

random.seed(42)
DECISION_DS = (90, 126)          # primary decision day = 90 td; robustness = 126 td
HORIZONS = {"6m": 126, "1y": 250}
PRICES = "data/prices"
REVIEW_CSV = "data/master/review/a2_hold_drawdown.csv"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = (len(xs) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def median(xs):
    return pctl(xs, 0.5)


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


# ---- Nifty calendar (same convention as A3)
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


def fwd_alpha_from(closes, dates, d_idx, n_td, delisted, wipeout):
    """Forward alpha vs Nifty from day-D close over n_td sessions (terminal-aware for delisted)."""
    c0 = closes[d_idx]; t0 = dates[d_idx]
    n0 = nifty_at(t0)
    if not n0 or c0 <= 0:
        return None
    j = d_idx + n_td
    if j < len(closes):
        c1 = closes[j]; n1 = nifty_at(dates[j])
        if not n1:
            return None
        return (c1 / c0 - 1) - (n1 / n0 - 1)
    if not delisted:
        return None
    end = td_offset(t0, n_td)
    if end is None:
        return None
    n1 = nifty_at(end)
    if not n1:
        return None
    c1 = 0.0 if wipeout else closes[-1]
    return (c1 / c0 - 1) - (n1 / n0 - 1)


def terminal_alpha_from(closes, dates, d_idx, delisted, wipeout):
    c0 = closes[d_idx]; t0 = dates[d_idx]
    n0 = nifty_at(t0)
    if not n0 or c0 <= 0:
        return None
    c1 = 0.0 if (delisted and wipeout) else closes[-1]
    n1 = nifty_at(dates[-1])
    if not n1:
        return None
    return (c1 / c0 - 1) - (n1 / n0 - 1)


def strength_features(closes, dates, d_idx):
    """PIT strength features from sessions 0..d_idx ONLY. Returns dict or None."""
    w_close = closes[:d_idx + 1]
    if len(w_close) < d_idx + 1 or w_close[0] <= 0:
        return None
    # up-day ratio
    ups = sum(1 for a, b in zip(w_close[:-1], w_close[1:]) if b > a)
    up_ratio = ups / (len(w_close) - 1)
    # reclaim off trough (higher-lows proxy): current vs window min
    wmin = min(w_close)
    reclaim = (w_close[-1] / wmin - 1) if wmin > 0 else 0.0
    # relative strength vs nifty over the window
    n0 = nifty_at(dates[0]); nD = nifty_at(dates[d_idx])
    if not n0 or not nD:
        return None
    rs = (w_close[-1] / w_close[0]) / (nD / n0) - 1
    return {"up_ratio": up_ratio, "reclaim": reclaim, "rs": rs}


def vol_trend(volumes, d_idx):
    w = [v for v in volumes[:d_idx + 1] if pd.notna(v)]
    if len(w) < 9:
        return None
    third = len(w) // 3
    early = mean(w[:third]); late = mean(w[-third:])
    if early <= 0:
        return None
    return late / early - 1


# ---- one pass over price files, build per-decision-day records
records = {D: [] for D in DECISION_DS}
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
    closes = pr["close"].astype(float).tolist()
    dates = pr["date"].tolist()
    vols = pr["volume"].tolist() if "volume" in pr.columns else [float("nan")] * len(closes)
    n_files += 1
    ipx = float(r["ipx"])
    delisted = is_delisted(r)
    wipeout = str(r.get("outcome_class")) == "wipeout"
    for D in DECISION_DS:
        if len(closes) < D + 5:        # need a real day-D anchor + a little forward
            continue
        underwater = closes[D] < ipx
        if not underwater:
            continue
        feat = strength_features(closes, dates, D)
        if feat is None:
            continue
        vt = vol_trend(vols, D)
        rec = {
            "isin": r["isin"], "name": r.get("company_name"), "cohort": r.get("cohort"),
            "type": r.get("type"), "D": D,
            "dd_from_issue": closes[D] / ipx - 1,
            "up_ratio": feat["up_ratio"], "reclaim": feat["reclaim"], "rs": feat["rs"],
            "vol_trend": vt, "delisted": delisted, "outcome_class": r.get("outcome_class"),
        }
        for h, ntd in HORIZONS.items():
            rec[f"fwd_alpha_{h}"] = fwd_alpha_from(closes, dates, D, ntd, delisted, wipeout)
        rec["fwd_alpha_term"] = terminal_alpha_from(closes, dates, D, delisted, wipeout)
        records[D].append(rec)

print(f"scanned {n_files} price files")


def add_composite(g):
    """Composite STRENGTH = mean of within-group percentile ranks of up_ratio, reclaim, rs, vol_trend.
    Computed WITHIN the underwater group at this (cohort, D) — strictly PIT, no outcome leakage."""
    g = g.copy()
    feats = ["up_ratio", "reclaim", "rs", "vol_trend"]
    parts = []
    for f in feats:
        s = pd.to_numeric(g[f], errors="coerce")
        parts.append(s.rank(pct=True))      # NaNs -> NaN rank; mean(skipna) handles partial coverage
    g["strength"] = pd.concat(parts, axis=1).mean(axis=1, skipna=True)
    return g


def basket(xs):
    xs = [x for x in xs if pd.notna(x)]
    if not xs:
        return None
    pos = sum(1 for x in xs if x > 0)
    return {"n": len(xs), "median": median(xs), "mean": mean(xs),
            "p_pos": pos / len(xs), "p10": pctl(xs, 0.10), "p90": pctl(xs, 0.90)}


def boot_mean_ci(xs, n_boot=2000):
    xs = [x for x in xs if pd.notna(x)]
    if len(xs) < 12:
        return (float("nan"), float("nan"), float("nan"))
    means = []
    for _ in range(n_boot):
        s = [xs[random.randrange(len(xs))] for _ in range(len(xs))]
        means.append(mean(s))
    means.sort()
    return (mean(xs), means[int(0.025 * n_boot)], means[int(0.975 * n_boot)])


# =====================================================================
# CORE: EXIT-WEAK vs HOLD-ALL among UNDERWATER names, per decision day, cohort, horizon.
# =====================================================================
all_review = []
for D in DECISION_DS:
    data = pd.DataFrame(records[D])
    print("=" * 86)
    print(f"DECISION DAY D={D} td — underwater names only (close[D] < issue_price_adj)")
    print(f"  total underwater rows: {len(data)}  "
          f"(boom {int((data['cohort']=='boom').sum())}, longterm {int((data['cohort']=='longterm').sum())})")
    # composite strength computed WITHIN each cohort's underwater group (PIT, no pooling across regimes)
    pieces = []
    for cohort in ("boom", "longterm"):
        pieces.append(add_composite(data[data["cohort"] == cohort]))
    data = pd.concat(pieces, ignore_index=True)

    for cohort in ("boom", "longterm"):
        sub = data[(data["cohort"] == cohort) & data["strength"].notna()].copy()
        if len(sub) < 12:
            print(f"\n[{cohort}] underwater n={len(sub)} — SUPPRESS (<12)")
            continue
        med_s = sub["strength"].median()
        strong = sub[sub["strength"] >= med_s]
        weak = sub[sub["strength"] < med_s]
        print(f"\n[{cohort}] underwater n={len(sub)}  STRONG n={len(strong)}  WEAK n={len(weak)}  "
              f"(split at composite-strength median {med_s:.3f})")
        for h in ("6m", "1y", "term"):
            col = f"fwd_alpha_{h}"
            ball = basket(sub[col].tolist())
            bs = basket(strong[col].tolist())
            bw = basket(weak[col].tolist())
            if ball is None or bs is None or bw is None:
                continue
            tier = "thin" if min(ball["n"], bs["n"], bw["n"]) < 30 else ""
            # overlay = exit WEAK, hold STRONG => the held basket is STRONG.
            # beats do-nothing on the MEAN iff strong mean > all mean (i.e. weak mean drags it down).
            beats = bs["mean"] > ball["mean"]
            # right-tail / median trap: per-name "exit weak wins" = P(weak fwd alpha < 0)
            exit_wins = 1 - bw["p_pos"]
            print(f"  fwd_{h:>4}: HOLD-ALL N={ball['n']:<4} mean={100*ball['mean']:+.1f}% med={100*ball['median']:+.1f}% | "
                  f"STRONG mean={100*bs['mean']:+.1f}% med={100*bs['median']:+.1f}% | "
                  f"WEAK mean={100*bw['mean']:+.1f}% med={100*bw['median']:+.1f}% "
                  f"exit-weak-wins={100*exit_wins:.0f}% | overlay_beats_donothing(mean)={beats} {tier}")

        # ----- right-tail bootstrap: the WEAK basket terminal mean (what exiting forfeits) -----
        m, lo, hi = boot_mean_ci(weak["fwd_alpha_term"].tolist())
        print(f"  [right-tail] WEAK basket fwd-term mean={100*m:+.1f}% [boot95 {100*lo:+.0f}..{100*hi:+.0f}%] "
              f"-> if >0, EXITING the weak names FORFEITS a positive mean (right-tail trap)")

        # ----- PLACEBO: shuffle STRONG/WEAK labels among underwater, recompute STRONG-WEAK gap -----
        real_vals = sub[["strength", "fwd_alpha_term"]].dropna()
        if len(real_vals) >= 12:
            real_gap = (real_vals[real_vals["strength"] >= med_s]["fwd_alpha_term"].mean()
                        - real_vals[real_vals["strength"] < med_s]["fwd_alpha_term"].mean())
            fa = real_vals["fwd_alpha_term"].tolist()
            nstrong = int((real_vals["strength"] >= med_s).sum())
            null_gaps = []
            for _ in range(1000):
                idx = list(range(len(fa))); random.shuffle(idx)
                sg = mean([fa[i] for i in idx[:nstrong]])
                wg = mean([fa[i] for i in idx[nstrong:]])
                null_gaps.append(sg - wg)
            null_gaps.sort()
            # two-sided p: fraction of |null| >= |real|
            p = sum(1 for x in null_gaps if abs(x) >= abs(real_gap)) / len(null_gaps)
            nlo, nhi = pctl(null_gaps, 0.025), pctl(null_gaps, 0.975)
            print(f"  [PLACEBO] real STRONG-WEAK fwd-term gap={100*real_gap:+.1f}%  "
                  f"shuffle-null 95%=[{100*nlo:+.1f}..{100*nhi:+.1f}%]  p={p:.3f}  "
                  f"{'SURVIVES (real outside null)' if p < 0.05 else 'NOISE (inside null)'}")

    # review CSV: the WEAK underwater names that RECOVERED (forfeited by an exit-weak overlay)
    dd = data.copy()
    dd["strength_pctile"] = dd.groupby("cohort")["strength"].rank(pct=True)
    weak_recover = dd[(dd["strength_pctile"] < 0.5) & (dd["fwd_alpha_term"] > 0)]
    for _, x in weak_recover.iterrows():
        all_review.append({
            "D": D, "isin": x["isin"], "name": x["name"], "cohort": x["cohort"], "type": x["type"],
            "dd_from_issue": round(x["dd_from_issue"], 3),
            "strength_pctile": round(x["strength_pctile"], 3),
            "fwd_alpha_term": round(x["fwd_alpha_term"], 3), "outcome_class": x["outcome_class"],
        })

pd.DataFrame(all_review).to_csv(REVIEW_CSV, index=False)
print("=" * 86)
print(f"wrote {len(all_review)} 'weak-but-recovered' rows (winners an exit-weak overlay forfeits) -> {REVIEW_CSV}")
print("Interpretation: the overlay beats do-nothing ONLY if the WEAK basket forward-alpha mean is")
print("reliably NEGATIVE, the STRONG-WEAK gap SURVIVES the placebo, and it holds in BOTH cohorts.")
