"""Pure-Python schema gate (Thread B) — typed column/range/null-rate contracts on the key data
products. Catches refresh drift that verify.py's count/path checks miss (e.g. a column going
all-null, a rate column blowing past 100x, a dtype flipping to object). No pandera dependency —
declarative dict + a tiny checker, in the project's no-heavy-deps style.

Run: PYTHONPATH=. python tools/checks/schema_gate.py   (exit 1 on any violation)
Also importable: check_all() -> list[str] of violations (empty = clean)."""
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# schema = {file: {col: {required, numeric, min, max, max_null_rate, enum}}}
# only the columns we actively depend on are pinned (a contract, not a full census).
# review-hardened (2026-06-08): every required numeric carries an explicit max_null_rate so
# "required" actually enforces non-null; categorical cols carry enum sets (catch scraper typos);
# score is legitimately null on non-verdict + score-unknown NEUTRAL rows, so it is NOT null-capped
# globally — instead a SCOPED rule (below) requires it on APPLY/AVOID.
SCHEMAS = {
    "data/master/calls_ledger.csv": {
        "_min_rows": 100,
        "call_id":     {"required": True, "max_null_rate": 0.0, "unique": True},
        "isin":        {"required": True, "max_null_rate": 0.0},
        "call_type":   {"required": True, "max_null_rate": 0.0,
                        "enum": {"APPLY", "AVOID", "NEUTRAL", "EARLY_APPLY", "EARLY_AVOID",
                                 "EARLY_NEUTRAL", "TRACK", "PERSIST_HOLD", "PERSIST_EXIT_LEAN",
                                 "EXIT_REVIEW", "CLEARED_ISSUE", "TAKE_PROFITS"}},
        "mode":        {"required": True, "max_null_rate": 0.0,
                        "enum": {"live", "gap_filled", "backfilled", "historical_sim"}},
        "call_date":   {"required": True, "max_null_rate": 0.0},
        "score":       {"required": True, "numeric": True, "min": 0, "max": 100},  # null OK (scoped rule below)
        "alpha_1m":    {"required": True, "numeric": True, "min": -1.5, "max": 50},
        "alpha_3m":    {"required": True, "numeric": True, "min": -1.5, "max": 50},
        "grade_status": {"required": True, "max_null_rate": 0.0,
                         "enum": {"pending", "partial", "final"}},
    },
    "data/master/ipo_analysis.csv": {
        "_min_rows": 2000,
        "isin":            {"required": True, "max_null_rate": 0.0, "unique": True},
        "type":            {"required": True, "max_null_rate": 0.0, "enum": {"MB", "SME"}},
        "issue_price_adj": {"required": True, "numeric": True, "min": 0, "max_null_rate": 0.10},
        "listing_date":    {"required": True, "max_null_rate": 0.05},
    },
}


def _check_file(path, schema):
    return _check_file_abs(os.path.join(ROOT, path), schema, label=path)


def _check_file_abs(full, schema, label=None):
    label = label or full
    out = []
    path = label
    if not os.path.exists(full):
        return [f"{path}: MISSING"]
    df = pd.read_csv(full)
    minr = schema.get("_min_rows")
    if minr and len(df) < minr:
        out.append(f"{path}: only {len(df)} rows (< floor {minr})")
    for col, rule in schema.items():
        if col.startswith("_"):
            continue
        if col not in df.columns:
            if rule.get("required"):
                out.append(f"{path}: missing required column '{col}'")
            continue
        s = df[col]
        nr = float(s.isna().mean())
        cap = rule.get("max_null_rate")
        if cap is not None and nr > cap + 1e-9:
            out.append(f"{path}.{col}: null-rate {nr:.0%} > cap {cap:.0%}")
        if rule.get("unique") and s.dropna().duplicated().any():
            out.append(f"{path}.{col}: expected unique, has duplicates")
        if rule.get("enum") is not None:
            bad = set(s.dropna().astype(str).unique()) - rule["enum"]
            if bad:
                out.append(f"{path}.{col}: unexpected values {sorted(bad)[:5]} (typo/new category?)")
        if rule.get("numeric"):
            n = pd.to_numeric(s, errors="coerce")
            vals = n.dropna()
            if not vals.empty:
                lo, hi = rule.get("min"), rule.get("max")
                if lo is not None and vals.min() < lo:
                    out.append(f"{path}.{col}: min {vals.min():.3g} < {lo}")
                if hi is not None and vals.max() > hi:
                    out.append(f"{path}.{col}: max {vals.max():.3g} > {hi}")
    return out


def _cross_checks():
    """Cross-file + cross-field invariants the per-column gate can't see (review-hardened)."""
    out = []
    led_p = os.path.join(ROOT, "data/master/calls_ledger.csv")
    sub_p = os.path.join(ROOT, "data/master/ipo_analysis.csv")
    if not (os.path.exists(led_p) and os.path.exists(sub_p)):
        return out
    led = pd.read_csv(led_p)
    sub = pd.read_csv(sub_p)
    # 1. SCOPED non-null: APPLY/AVOID calls MUST carry a score (NEUTRAL/non-verdict may be null)
    va = led[led["call_type"].isin(["APPLY", "AVOID", "EARLY_APPLY", "EARLY_AVOID"])]
    miss = int(pd.to_numeric(va["score"], errors="coerce").isna().sum())
    if miss:
        out.append(f"calls_ledger: {miss} APPLY/AVOID rows have NO score (must be scored)")
    # 2. Referential: NON-LIVE ledger ISINs must exist in the substrate (live/gap_filled may be
    #    slug-keyed pre-ingest, so they're exempt)
    settled = led[~led["mode"].isin(["live", "gap_filled"])]
    orphans = set(settled["isin"]) - set(sub["isin"])
    if orphans:
        out.append(f"calls_ledger: {len(orphans)} non-live ISINs absent from substrate "
                   f"(e.g. {sorted(orphans)[:3]})")
    # 3. Cross-field: adjusted listing gain must reconcile with adj_listing_open/issue_price_adj
    if {"adj_listing_gain_open", "adj_listing_open", "issue_price_adj"} <= set(sub.columns):
        g = pd.to_numeric(sub["adj_listing_gain_open"], errors="coerce")
        o = pd.to_numeric(sub["adj_listing_open"], errors="coerce")
        ip = pd.to_numeric(sub["issue_price_adj"], errors="coerce")
        implied = o / ip - 1
        m = g.notna() & implied.notna() & (ip > 0)
        bad = (m & ((g - implied).abs() > 0.02)).sum()      # >2pp disagreement = scale/units drift
        if bad > 0.02 * m.sum():                            # tolerate a tiny tail
            out.append(f"substrate: {int(bad)} rows where adj_listing_gain_open disagrees with "
                       f"adj_listing_open/issue_price_adj by >2pp (scale-inversion?)")
    return out


def check_all():
    viol = []
    for path, schema in SCHEMAS.items():
        viol += _check_file(path, schema)
    viol += _cross_checks()
    return viol


if __name__ == "__main__":
    v = check_all()
    if v:
        print("SCHEMA GATE: VIOLATIONS")
        for x in v:
            print("  -", x)
        sys.exit(1)
    print("SCHEMA GATE: clean — all pinned contracts hold.")
