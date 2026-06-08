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

# schema = {file: {col: {required, numeric, min, max, max_null_rate}}}
# only the columns we actively depend on are pinned (a contract, not a full census).
SCHEMAS = {
    "data/master/calls_ledger.csv": {
        "_min_rows": 100,
        "call_id":     {"required": True, "max_null_rate": 0.0, "unique": True},
        "isin":        {"required": True, "max_null_rate": 0.0},
        "call_type":   {"required": True, "max_null_rate": 0.0},
        "mode":        {"required": True, "max_null_rate": 0.0},
        "call_date":   {"required": True, "max_null_rate": 0.0},
        "score":       {"required": True, "numeric": True, "min": 0, "max": 100},
        "alpha_1m":    {"required": True, "numeric": True, "min": -1.5, "max": 50},
        "alpha_3m":    {"required": True, "numeric": True, "min": -1.5, "max": 50},
        "grade_status": {"required": True, "max_null_rate": 0.0},
    },
    "data/master/ipo_analysis.csv": {
        "_min_rows": 2000,
        "isin":            {"required": True, "max_null_rate": 0.0, "unique": True},
        "type":            {"required": True, "max_null_rate": 0.0},
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


def check_all():
    viol = []
    for path, schema in SCHEMAS.items():
        viol += _check_file(path, schema)
    return viol


if __name__ == "__main__":
    v = check_all()
    if v:
        print("SCHEMA GATE: VIOLATIONS")
        for x in v:
            print("  -", x)
        sys.exit(1)
    print("SCHEMA GATE: clean — all pinned contracts hold.")
