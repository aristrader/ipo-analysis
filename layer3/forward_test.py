"""TRUE out-of-sample forward test (read-only).

The refresh ingests IPOs the system has NEVER seen (they listed after the freeze;
no weight, threshold, or finding ever saw them). This module scores each of them
with the frozen scorecard USING ONLY THE PRE-REFRESH SNAPSHOT as the analog pool
(exactly the information available at their IPO date), then compares the scores
against the realized EARLY outcomes from the refreshed substrate.

HONESTY RAILS (non-negotiable):
  * every output is labeled EARLY READ — the cohort is 0-5 months old; listing-pop /
    1m / 3m figures only. NO 1y/3y verdicts are possible yet.
  * min-N floors apply (config.MIN_N_HINT per cell); cells below floor say so.
  * the score is computed from AT-IPO features only (no outcome columns leak in).

Repeatable: run again as the cohort ages and the early read hardens.
"""
import csv
import os
from datetime import datetime

import pandas as pd

from layer3 import config, spine
from layer3.predictor import scorecard
from layer3.predictor.predict import predict

QUERY_FEATURES = ["type", "broad_sector", "market_cap_class", "ofs_pct", "sub_total_x", "sub_qib_x",
                  "gmp_pct", "pe_ratio", "issue_size_cr", "pre_ipo_roe_pct", "pre_ipo_debt_equity",
                  "pre_ipo_pat_margin_pct", "promoter_post_issue_pct", "pre_ipo_net_sales",
                  "lead_manager", "pre_ipo_pat"]


def _query_from_row(row):
    q = {"name": row.get("company_name")}
    for k in QUERY_FEATURES:
        v = row.get(k)
        if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
            continue
        q[k] = v
    return q


def load_frames():
    """(old substrate = pre-refresh snapshot, new substrate). Cohort = isins only in new."""
    meta = pd.io.json.read_json if False else None  # noqa — keep import surface tiny
    import json
    m = json.load(open(config.ROOT / "data/master/substrate_meta.json"))
    snap = config.ROOT / m["archive_pointer"] / "ipo_analysis.csv"
    old = pd.read_csv(snap)
    new = pd.read_csv(config.ROOT / "data/master/ipo_analysis.csv")
    return old, new


def forward_cohort(old, new):
    """Newly-ingested, already-LISTED equity rows (the never-seen holdout)."""
    seen = set(old["isin"].astype(str))
    c = new[~new["isin"].astype(str).isin(seen)].copy()
    ld = pd.to_datetime(c["listing_date"], errors="coerce")
    c = c[ld.notna() & (ld <= pd.Timestamp(config.AS_OF_DATE))]
    if "instrument_type" in c.columns:
        c = c[c["instrument_type"].fillna("equity") == "equity"]
    return c


def score_cohort(cohort, old):
    """Score every holdout IPO against the OLD frame only (as-if at IPO time)."""
    rows = []
    for _, r in cohort.iterrows():
        q = _query_from_row(r)
        try:
            res = predict(q, df=old, profile="data_informed")
            sc = res["scorecard"].get("combined_score") if isinstance(res.get("scorecard"), dict) else None
            flags = res.get("wipeout_flags", {})
            n_flags = flags.get("n_flags") if isinstance(flags, dict) else None
        except Exception:
            sc, n_flags = None, None
        rows.append({"isin": r["isin"], "company": r.get("company_name"), "type": r.get("type"),
                     "listing_date": r.get("listing_date"), "score": sc, "n_flags": n_flags,
                     "gmp_pct": pd.to_numeric(r.get("gmp_pct"), errors="coerce"),
                     "pop": pd.to_numeric(r.get("adj_listing_gain_open"), errors="coerce"),
                     "ret_1m": pd.to_numeric(r.get("return_from_listing_1m"), errors="coerce"),
                     "ret_3m": pd.to_numeric(r.get("return_from_listing_3m"), errors="coerce")})
    return pd.DataFrame(rows)


def _med(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return (round(100 * float(s.median()), 1), int(len(s))) if len(s) >= config.MIN_N_HINT else (None, int(len(s)))


def analyze(scored):
    out = {"n_cohort": int(len(scored)), "label": "EARLY READ — cohort is 0-5 months old; "
           "listing-pop/1m/3m only, NO 1y/3y verdicts possible yet"}
    s = scored[scored["score"].notna()].copy()
    out["n_scored"] = int(len(s))
    if len(s) >= 2 * config.MIN_N_HINT:
        s["bucket"] = pd.qcut(s["score"], min(3, max(2, len(s) // config.MIN_N_HINT)),
                              labels=False, duplicates="drop")
        tbl = []
        for b, g in s.groupby("bucket"):
            pop, n_pop = _med(g["pop"]); r1, n1 = _med(g["ret_1m"]); r3, n3 = _med(g["ret_3m"])
            tbl.append({"score_bucket": f"B{int(b)+1} (higher=better)", "n": int(len(g)),
                        "median_score": round(float(g['score'].median()), 1),
                        "median_pop_%": pop, "median_1m_%": r1, "n_1m": n1,
                        "median_3m_%": r3, "n_3m": n3})
        out["score_buckets"] = tbl
    flagged = scored[pd.to_numeric(scored["n_flags"], errors="coerce") >= 1]
    clean = scored[pd.to_numeric(scored["n_flags"], errors="coerce") == 0]
    out["wipeout_flags"] = {
        "flagged": {"n": int(len(flagged)), "median_pop_%": _med(flagged["pop"])[0],
                    "median_1m_%": _med(flagged["ret_1m"])[0]},
        "clean": {"n": int(len(clean)), "median_pop_%": _med(clean["pop"])[0],
                  "median_1m_%": _med(clean["ret_1m"])[0]},
    }
    g = scored[scored["gmp_pct"].notna() & scored["pop"].notna()]
    if len(g) >= config.MIN_N_HINT:
        # spearman = pearson on ranks (avoids the scipy dependency)
        rho = g["gmp_pct"].rank().corr(g["pop"].rank())
        out["gmp_pop"] = {"n": int(len(g)),
                          "spearman": round(float(rho), 3),
                          "median_pop_when_gmp_ge_20": _med(g[g["gmp_pct"] >= 20]["pop"])[0],
                          "median_pop_when_gmp_lt_20": _med(g[g["gmp_pct"] < 20]["pop"])[0]}
    return out


# ---- F2: durable, append-only "were-we-right" history (the credibility spine) -----------------
# Each refresh vintage gets ONE row capturing whether the score RANKED outcomes (top−bottom bucket
# spreads) and whether the wipeout flag SEPARATED outcomes. Keyed on as_of_date (the cohort vintage),
# so re-running the same vintage updates its row and a new refresh appends — the row sequence is the
# maturation trajectory. Every figure is still an EARLY READ (pop/1m/3m only).
HISTORY_PATH = config.ROOT / "data/master/forward_test_history.csv"
HISTORY_COLS = ["as_of_date", "run_date", "n_cohort", "n_scored",
                "top_bucket_pop", "bot_bucket_pop", "spread_pop",
                "top_bucket_1m", "bot_bucket_1m", "spread_1m",
                "top_bucket_3m", "bot_bucket_3m", "spread_3m",
                "flagged_pop", "clean_pop", "flag_pop_gap", "gmp_pop_spearman"]


def _spread(top, bot):
    return round(top - bot, 1) if (top is not None and bot is not None) else None


def history_row(res, as_of, run_date):
    """Flatten an analyze() result into one comparable history row (the spreads ARE the verdict)."""
    row = {c: None for c in HISTORY_COLS}
    row.update({"as_of_date": as_of, "run_date": run_date,
                "n_cohort": res.get("n_cohort"), "n_scored": res.get("n_scored")})
    bk = res.get("score_buckets") or []
    if len(bk) >= 2:
        top, bot = bk[-1], bk[0]    # buckets are ordered B1..Bn with higher=better last
        for short, key in (("pop", "median_pop_%"), ("1m", "median_1m_%"), ("3m", "median_3m_%")):
            t, b = top.get(key), bot.get(key)
            row[f"top_bucket_{short}"], row[f"bot_bucket_{short}"] = t, b
            row[f"spread_{short}"] = _spread(t, b)
    wf = res.get("wipeout_flags") or {}
    fl, cl = (wf.get("flagged") or {}), (wf.get("clean") or {})
    row["flagged_pop"], row["clean_pop"] = fl.get("median_pop_%"), cl.get("median_pop_%")
    # clean−flagged: a working flag means clean names pop MORE → positive gap
    row["flag_pop_gap"] = _spread(cl.get("median_pop_%"), fl.get("median_pop_%"))
    row["gmp_pop_spearman"] = (res.get("gmp_pop") or {}).get("spearman")
    return row


def append_history(res, as_of=None, run_date=None, path=HISTORY_PATH):
    """Upsert this run's summary into the append-only history CSV, keyed on as_of_date (vintage).
    Returns (row, path). Idempotent within a vintage; comparable across vintages."""
    as_of = as_of or str(config.AS_OF_DATE)
    run_date = run_date or datetime.now().strftime("%Y-%m-%d %H:%M")
    row = history_row(res, as_of, run_date)
    existing = []
    if os.path.exists(path):
        with open(path, newline="") as f:
            existing = [r for r in csv.DictReader(f) if r.get("as_of_date") != as_of]
    existing.append({k: ("" if v is None else v) for k, v in row.items()})
    existing.sort(key=lambda r: str(r.get("as_of_date")))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(existing)
    return row, path
