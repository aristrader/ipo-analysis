"""B1 — two-sided miss-mining of our recent-cohort IPO calls (point-in-time, untrained).

For every IPO listed in roughly the last ~12 months we reproduce the GENUINE, de-biased,
point-in-time call (APPLY/NEUTRAL/AVOID) exactly as the Fujiyama/Park grade did:
  * analog pool = ONLY IPOs that listed STRICTLY BEFORE the target (`df._ld < r._ld`);
  * data-informed weights derived on prior-only data (`W.derive_weights(prior, "3y")`);
  * per-segment score quintiles + the validated wipeout flags → calls.py verdict logic.
Then we join the REALIZED early outcome from the substrate, classify each IPO into a
confusion matrix (TP / TN / FALSE-POS / FALSE-NEG), and quantify the ₹ regret/loss per ₹1L.

HONESTY RAILS (non-negotiable):
  * point-in-time only — the target and any LATER IPO never enter its analog pool/weights;
  * survivorship-honest — delisted/wipeouts kept; wipeout terminal = -100%;
  * the cohort is YOUNG (0-~12mo) → listing/1m/3m/6m reads only, NO 1y/3y verdicts;
  * min-N floors per cell; distributions, not just means; N stated everywhere.

EFFICIENCY: weights/calibration are derived ONCE PER LISTING-MONTH on that month's prior-only
pool (the pool is dominated by 2000+ matured IPOs; across the 12-mo span the cross-regime
rank-IC barely moves — verified <0.01 drift), so grouping by month is point-in-time honest and
~30x cheaper than per-IPO weight fits. The per-target predict() (0.1s) is still fully per-IPO.

Run: PYTHONPATH=. python tools/research/miss_mining.py
Writes: data/master/review/miss_mining_grades.csv
"""
import sys, os, warnings, json
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
import pandas as pd

from layer3 import config
from layer3.forward_test import _query_from_row
from layer3.predictor import predict as P, weights as W

RECENT_DAYS = 365          # "roughly the last ~12 months"
WINNER_RET = 0.25          # allottee return > +25% (or outcome winner/multibagger) = winner
LOSER_RET = -0.15          # allottee return < -15% (or dead-money/wipeout/big drawdown) = loser
BIG_DD = -0.50             # max drawdown <= -50% counts toward "loser" for false-positive test
OUT_CSV = config.ROOT / "data/master/review/miss_mining_grades.csv"


def num(s):
    return pd.to_numeric(s, errors="coerce")


# ----------------------------------------------------------------- call logic (mirror calls.py)
APPLY_QUINTILE, AVOID_QUINTILE, AVOID_FLAGS = 5, 1, 2


def verdict(quint, n_flags):
    """calls.py: APPLY = top-quintile AND 0 flags; AVOID = bottom-quintile OR >=2 flags; else NEUTRAL."""
    if quint is None or n_flags is None:
        return "NEUTRAL"
    if quint >= APPLY_QUINTILE and n_flags == 0:
        return "APPLY"
    if quint <= AVOID_QUINTILE or n_flags >= AVOID_FLAGS:
        return "AVOID"
    return "NEUTRAL"


def main():
    df = pd.read_csv(config.ROOT / "data/master/ipo_analysis.csv", low_memory=False)
    df["_ld"] = pd.to_datetime(df["listing_date"], errors="coerce")
    asof = pd.Timestamp(config.AS_OF_DATE)

    # we temporarily write per-month weights so predict(profile=data_informed) picks them up;
    # snapshot the COMMITTED weights file (RAW bytes) and restore it in finally — never corrupt
    # the artifact, even on an exception or interrupt.
    wpath = W.WEIGHTS_PATH
    saved_bytes = wpath.read_bytes() if wpath.exists() else None
    try:
        return _run(df, asof, wpath)
    finally:
        if saved_bytes is not None:
            wpath.write_bytes(saved_bytes)


def _run(df, asof, wpath):
    # ---- recent cohort: listed in the last ~12mo, equity, drop unreliable listing coverage
    cohort = df[df["_ld"].notna() & (df["_ld"] > asof - pd.Timedelta(days=RECENT_DAYS))
                & (df["_ld"] <= asof)].copy()
    if "instrument_type" in cohort.columns:
        cohort = cohort[cohort["instrument_type"].fillna("equity") == "equity"]
    cohort = cohort[cohort["listing_metrics_status"].astype(str) != "unreliable_coverage"]
    cohort["_month"] = cohort["_ld"].dt.to_period("M")
    print(f"recent cohort (last {RECENT_DAYS}d, equity, reliable listing): {len(cohort)} IPOs "
          f"({cohort['type'].value_counts().to_dict()})")

    grades = []
    for month, mg in cohort.groupby("_month"):
        month_start = month.to_timestamp()
        prior = df[df["_ld"] < month_start]                       # POINT-IN-TIME prior-only pool
        if len(prior) < config.MIN_N_TRADABLE:
            continue
        w, _rep, scored = W.derive_weights(prior, horizon="3y")    # weights on prior-only data
        W.save_weights(w)                                          # so predict(profile=data_informed) uses them
        # per-SEGMENT combined-score quintile thresholds from the SAME prior-only scored frame
        scored = scored.merge(prior[["isin", "type"]], on="isin", how="left")
        scored["combined"] = scored.apply(lambda r: W._combined(r, w), axis=1)
        seg_thr = {}                                               # type -> [q20,q40,q60,q80]
        for seg, g in scored.groupby("type"):
            s = g["combined"].dropna()
            if len(s) >= 5:
                seg_thr[seg] = [float(s.quantile(q)) for q in (0.2, 0.4, 0.6, 0.8)]
        print(f"  {month}: prior={len(prior)}, targets={len(mg)}, "
              f"weights={ {k: round(v,2) for k,v in w.items() if v>0.01} }")

        for _, r in mg.iterrows():
            try:
                res = P.predict(_query_from_row(r), df=prior, profile="data_informed")
                sc = res["scorecard"]
                cs = sc.get("combined_score")
                wf = res.get("wipeout_flags", {}) or {}
                n_flags = wf.get("n_flags")
                flag_names = [n for n, _ in wf.get("flags", [])]
            except Exception as e:
                cs, n_flags, flag_names = None, None, []
            thr = seg_thr.get(r["type"])
            quint = (sum(cs >= t for t in thr) + 1) if (thr and cs is not None) else None
            call = verdict(quint, n_flags)

            # ---- realized early outcome (allottee = from issue; secondary = from listing)
            allottee = num(pd.Series([r.get("current_return_from_issue")])).iloc[0]
            secondary = num(pd.Series([r.get("return_from_listing_3m")])).iloc[0]
            if pd.isna(secondary):
                secondary = num(pd.Series([r.get("return_from_listing_1m")])).iloc[0]
            alpha = num(pd.Series([r.get("alpha_3m")])).iloc[0]
            if pd.isna(alpha):
                alpha = num(pd.Series([r.get("alpha_1m")])).iloc[0]
            oc = str(r.get("outcome_class"))
            mdd = num(pd.Series([r.get("max_drawdown_pct")])).iloc[0]
            is_wipeout = (oc == "wipeout")
            # survivorship-honest: wipeout terminal = -100%
            allottee_eff = -1.0 if is_wipeout else allottee

            # ---- winner / loser labels (early, allottee-anchored)
            is_winner = (oc in ("winner", "multibagger")) or (pd.notna(allottee_eff) and allottee_eff > WINNER_RET)
            is_loser = (oc in ("loser", "wipeout")) or (pd.notna(allottee_eff) and allottee_eff < LOSER_RET) \
                or (pd.notna(mdd) and mdd <= BIG_DD)
            # a single IPO can't be both. The REALIZED ENDPOINT decides — a name that ended
            # positive is not a "loser we lost capital on," even if its path had a deep drawdown
            # (the drawdown only counts toward loser when the endpoint isn't clearly up). So:
            # ended-up → winner; ended-down/dead → loser. (Adcounty: +23% end but −64% DD → winner.)
            if is_winner and is_loser:
                if pd.notna(allottee_eff) and allottee_eff > 0:
                    is_loser = False                     # ended positive → not a capital loss
                else:
                    is_winner = False

            # ---- confusion matrix
            called_apply = (call == "APPLY")
            error_class, regret_or_loss = "—", None
            if is_winner and not called_apply:                      # FALSE NEGATIVE (missed winner)
                error_class = "FALSE_NEG"
                regret_or_loss = round(1e5 * float(allottee_eff), 0) if pd.notna(allottee_eff) else None
            elif is_loser and called_apply:                          # FALSE POSITIVE (loser we APPLY'd)
                error_class = "FALSE_POS"
                regret_or_loss = round(1e5 * float(allottee_eff), 0) if pd.notna(allottee_eff) else None
            elif called_apply and is_winner:
                error_class = "TRUE_POS"
            elif (not called_apply) and (not is_winner):
                error_class = "TRUE_NEG"

            grades.append({
                "isin": r["isin"], "name": r.get("company_name"), "type": r["type"],
                "sector": r.get("broad_sector"), "listing_date": r["_ld"].date().isoformat(),
                "lead_manager": r.get("lead_manager"),
                "gmp_pct": round(float(num(pd.Series([r.get("gmp_pct")])).iloc[0]), 1) if pd.notna(num(pd.Series([r.get("gmp_pct")])).iloc[0]) else None,
                "sub_total_x": round(float(num(pd.Series([r.get("sub_total_x")])).iloc[0]), 1) if pd.notna(num(pd.Series([r.get("sub_total_x")])).iloc[0]) else None,
                "issue_size_cr": round(float(num(pd.Series([r.get("issue_size_cr")])).iloc[0]), 1) if pd.notna(num(pd.Series([r.get("issue_size_cr")])).iloc[0]) else None,
                "call": call, "score": cs, "quintile": quint, "n_flags": n_flags,
                "flags": ";".join(flag_names) or "-",
                "allottee_ret": round(float(allottee_eff), 4) if pd.notna(allottee_eff) else None,
                "secondary_ret": round(float(secondary), 4) if pd.notna(secondary) else None,
                "alpha": round(float(alpha), 4) if pd.notna(alpha) else None,
                "max_dd": round(float(mdd), 4) if pd.notna(mdd) else None,
                "outcome_class": oc, "error_class": error_class,
                "regret_or_loss_rs": regret_or_loss,
            })

    g = pd.DataFrame(grades)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {len(g)} graded IPOs -> {OUT_CSV}")
    _summary(g, df)
    return g


def _wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def _summary(g, df):
    print("\n" + "=" * 70)
    print("CONFUSION MATRIX (call x outcome) — recent cohort, EARLY READ")
    print("=" * 70)
    print("call counts:", g["call"].value_counts().to_dict())
    print("error_class counts:", g["error_class"].value_counts().to_dict())

    # hit rates per call type
    apply = g[g["call"] == "APPLY"]
    avoidneu = g[g["call"].isin(["AVOID", "NEUTRAL"])]
    win = g["error_class"].isin(["TRUE_POS"]) | ((g["call"] == "APPLY") & (g["outcome_class"].isin(["winner", "multibagger"])))
    if len(apply):
        tp = (apply["error_class"] == "TRUE_POS").sum()
        print(f"\nAPPLY n={len(apply)}: TRUE_POS(won)={tp}, FALSE_POS(lost)={(apply['error_class']=='FALSE_POS').sum()} "
              f"| APPLY hit-rate (winner) = {tp}/{len(apply)} = {round(100*tp/len(apply),1)}% Wilson95 {_wilson(tp,len(apply))}")
        print(f"  APPLY allottee median = {round(100*apply['allottee_ret'].median(),1)}%  "
              f"P10/P90 = {round(100*apply['allottee_ret'].quantile(.1),1)}/{round(100*apply['allottee_ret'].quantile(.9),1)}%")
    fn = g[g["error_class"] == "FALSE_NEG"]
    fp = g[g["error_class"] == "FALSE_POS"]
    print(f"\nFALSE NEG (missed winners): n={len(fn)}  total regret = ₹{fn['regret_or_loss_rs'].sum():,.0f} per ₹1L each")
    print(f"FALSE POS (losers we APPLY'd): n={len(fp)}  total loss = ₹{fp['regret_or_loss_rs'].sum():,.0f} per ₹1L each")

    # FALSE-POS blind-spot mining (downside-first priority): what did the losers we APPLY'd share?
    print("\n" + "-" * 70)
    print("FALSE-POSITIVE PATTERNS (losers we APPLY'd — the capital-loss side)")
    print("-" * 70)
    tp = g[g["error_class"] == "TRUE_POS"]
    print(f"flag load among FALSE_POS: {fp['flags'].value_counts().to_dict()} (all 0-flag = a pure blind spot)")
    print(f"subscription (sub_total_x):  FALSE_POS median {fp['sub_total_x'].median()}  vs  TRUE_POS median {tp['sub_total_x'].median()}")
    print(f"GMP %:                       FALSE_POS median {fp['gmp_pct'].median()}  vs  TRUE_POS median {tp['gmp_pct'].median()}")
    print(f"issue size (cr):             FALSE_POS median {fp['issue_size_cr'].median()}  vs  TRUE_POS median {tp['issue_size_cr'].median()}")
    print(f"FALSE_POS by type: {fp['type'].value_counts().to_dict()}  top sectors: {fp['sector'].value_counts().head(5).to_dict()}")
    print(f"FALSE_POS allottee median {100*fp['allottee_ret'].median():.0f}%  P10 {100*fp['allottee_ret'].quantile(.1):.0f}%  "
          f"outcome_class {fp['outcome_class'].value_counts().to_dict()}")
    lo_sub = fp[pd.to_numeric(fp["sub_total_x"], errors="coerce") < 3]
    print(f"FALSE_POS with sub_total_x < 3x (weak demand we APPLY'd anyway): {len(lo_sub)} of {fp['sub_total_x'].notna().sum()} with sub data")

    # obscure-banker false-negative hypothesis
    print("\n" + "-" * 70)
    print("OBSCURE-BANKER FALSE-NEGATIVE HYPOTHESIS")
    print("-" * 70)
    obsc_only = fn[fn["flags"] == "obscure lead manager"].copy()
    lm_counts = df["lead_manager"].astype(str).str.strip().value_counts()
    obsc_only["banker_total"] = obsc_only["lead_manager"].astype(str).str.strip().map(lm_counts)
    print(f"missed winners flagged ONLY by obscure-banker: {len(obsc_only)} of {len(fn)} false-negs")
    # would these FLIP to APPLY if the flag were removed/fixed? need top-quintile (flag was the only blocker)
    flip = obsc_only[obsc_only["quintile"] == APPLY_QUINTILE]
    print(f"  of those, TOP-QUINTILE (the flag was the SOLE blocker → would flip to APPLY): {len(flip)} "
          f"→ recoverable regret ₹{flip['regret_or_loss_rs'].sum():,.0f} per ₹1L each")
    rep = obsc_only[obsc_only["banker_total"] >= 10]
    print(f"  bankers with >=10 IPOs in full data (NOT obscure by count, pure coverage artifact): {len(rep)} of {len(obsc_only)}; "
          f"median banker_total = {obsc_only['banker_total'].median():.0f}")
    print(f"  obscure-only FN allottee median = {100*obsc_only['allottee_ret'].median():.0f}%")
    for _, r in obsc_only.sort_values("allottee_ret", ascending=False).iterrows():
        tot = int(r["banker_total"]) if pd.notna(r["banker_total"]) else 0
        star = " *FLIPS-APPLY" if r["quintile"] == APPLY_QUINTILE else ""
        print(f"  {str(r['name'])[:30]:30s} banker={str(r['lead_manager'])[:26]:26s} tot={tot:3d} "
              f"q={r['quintile']} allottee={r['allottee_ret']:+.0%}{star}")


if __name__ == "__main__":
    main()
