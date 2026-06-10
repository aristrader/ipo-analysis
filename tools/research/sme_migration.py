"""E3 — SME→Mainboard migration as an OUTCOME CLASS, derived from OWNED DATA (no scraping).

The backlog framed E3 as needing a dated external migration source (Chittorgarh r123 / NSE/BSE).
It turns out the migration FACT + an approximate DATE are already derivable from reference data in
the repo, so no network pull is needed:
  - NSE: an SME-listed IPO whose ISIN now appears on `data/reference/nse_equity_list.csv` (the current
    MAINBOARD equity list) has migrated; that file's `DATE OF LISTING` is the mainboard-admission date
    (verified strictly later than every migrant's IPO date → it IS the migration date).
  - BSE: an SME-listed IPO whose ISIN now sits in a NON-SME BSE group (not M/MT) in `bse_master.csv`
    has migrated (BSE master carries no date).

KEY DISCIPLINE — this is an OUTCOME CLASS, NOT a predictor feature:
  Migration happens YEARS after the IPO and REQUIRES the company to have grown into mainboard
  eligibility (profitability / market-cap thresholds). So "migrated SMEs outperform" is largely a
  SELECTION effect (migration is a marker that the company already escaped), and migration status is
  UNKNOWN at IPO → using it to score a new IPO would be look-ahead. We report it descriptively only.

Run: PYTHONPATH=. python tools/research/sme_migration.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pandas as pd
from layer3 import config, spine

NSE_LIST = config.ROOT / "data/reference/nse_equity_list.csv"
BSE_MASTER = config.ROOT / "data/reference/bse_master.csv"
BSE_SME_GROUPS = {"M", "MT"}  # BSE SME platform groups; anything else (A/B/T/Z/...) = mainboard


def _nse_mainboard_dates():
    df = pd.read_csv(NSE_LIST)
    isin_col = next(c for c in df.columns if "ISIN" in c.upper())
    date_col = next(c for c in df.columns if "DATE OF LISTING" in c.upper())
    return {str(i).strip(): str(d).strip() for i, d in zip(df[isin_col], df[date_col])}


def _bse_groups():
    df = pd.read_csv(BSE_MASTER)
    return {str(i).strip(): str(g).strip() for i, g in zip(df["ISIN_NUMBER"], df["GROUP"])}


def derive_migration(df):
    """Add `migrated_to_mainboard` (bool) + `migration_date` (NSE date, may be NaN) to the SME rows.
    Returns the SME-only frame with the two columns added."""
    nse_dates = _nse_mainboard_dates()
    bse_grp = _bse_groups()
    sme = df[df["listing_at"].astype(str).str.contains("SME", na=False)].copy()
    isin = sme["isin"].astype(str).str.strip()
    on_nse = isin.map(lambda i: i in nse_dates)
    on_bse = isin.map(lambda i: bse_grp.get(i, "") not in BSE_SME_GROUPS and bse_grp.get(i, "") != "")
    sme["migrated_to_mainboard"] = on_nse | on_bse
    sme["migration_date"] = pd.to_datetime(isin.map(lambda i: nse_dates.get(i)), errors="coerce", format="mixed")
    return sme


def _dist(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) < config.MIN_N_HINT:
        return {"n": int(len(s)), "median": None, "p10": None, "p90": None}
    return {"n": int(len(s)), "median": round(float(s.median()), 3),
            "p10": round(float(s.quantile(0.1)), 3), "p90": round(float(s.quantile(0.9)), 3)}


def _bad_rate(g):
    """dead-money OR wipeout share (the trap)."""
    oc = g["outcome_class"].astype(str)
    return round(100 * float(((oc == "wipeout") | (oc == "loser")).mean()), 1) if len(g) else None


def _multibagger_rate(g):
    return round(100 * float((g["outcome_class"].astype(str) == "multibagger").mean()), 1) if len(g) else None


def compare(sme):
    """Migrated vs not, overall and by cohort: outcome-class mix + return distributions. DESCRIPTIVE."""
    out = []
    for label, sub in [("ALL SME", sme), ("boom", sme[sme["cohort"] == "boom"]),
                       ("longterm", sme[sme["cohort"] == "longterm"])]:
        for mig, g in [("migrated", sub[sub["migrated_to_mainboard"]]),
                       ("trapped (not migrated)", sub[~sub["migrated_to_mainboard"]])]:
            row = {"panel": label, "group": mig, "n": int(len(g)),
                   "bad%_(loser|wipeout)": _bad_rate(g), "multibagger%": _multibagger_rate(g),
                   "cur_return_median": _dist(g["current_return_from_issue"])["median"],
                   "alpha_3y_median": _dist(g["alpha_3y"])["median"]}
            out.append(row)
    return pd.DataFrame(out)


def main():
    df = spine.load_substrate()
    sme = derive_migration(df)
    n = len(sme)
    n_mig = int(sme["migrated_to_mainboard"].sum())
    print(f"SME-listed IPOs: {n}")
    print(f"migrated to mainboard: {n_mig} ({100*n_mig/n:.1f}%)  "
          f"[{int(sme['migration_date'].notna().sum())} with an NSE migration date]")
    yrs = sme.loc[sme["migration_date"].notna(), "migration_date"].dt.year.value_counts().sort_index()
    print(f"migration dates by year (NSE): {dict(yrs)}")
    print("\n=== Migrated vs trapped SMEs — DESCRIPTIVE outcome comparison (selection-confounded) ===")
    print(compare(sme).to_string(index=False))
    print("\nCAVEAT: migration is a post-IPO OUTCOME requiring growth into mainboard eligibility, so the gap")
    print("is a SELECTION marker, not a tradeable signal — and it is UNKNOWN at IPO (look-ahead). NOT a score input.")


if __name__ == "__main__":
    main()
