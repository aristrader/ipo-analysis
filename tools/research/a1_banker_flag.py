"""A1 — banker-flag redefinition harness.

Evaluates 2-3 candidate redefinitions of the 'obscure lead manager' wipeout flag against:
  (1) PURPOSE PRESERVED: does the flag still discriminate bad outcomes (wipeout|dead-money)
      cross-regime (boom + longterm, MB + SME), with N + Wilson CI?
  (2) FALSE-VETO REDUCED: how many of B1's 34 obscure-only missed winners stop being flagged;
      does it stop tagging reputable under-sampled banks (Nuvama, Motilal, Morgan Stanley)?
  (3) PLACEBO / look-ahead: point-in-time only; shuffle-label placebo to confirm non-mechanical.

Candidates (see docstrings below):
  (a) SIZE-aware      — current freq<12, but DON'T fire on large MB issues.
  (b) QUALITY-aware   — banker's point-in-time PRIOR bad-outcome rate above a threshold (min-N, abstain).
  (c) HYBRID          — fire only if freq<12 AND small/SME issue AND NOT (clean PIT prior record above min-N).

No scipy. Wilson CI from spine. PIT banker stats computed from STRICTLY-PRIOR listings.
Run: PYTHONPATH=. .venv/bin/python tools/research/a1_banker_flag.py
"""
import numpy as np
import pandas as pd
from layer3 import spine, config

OBSCURE_CUTOFF = 12          # current rule's banker-IPO-count threshold
SMALL_ISSUE_CR = 50.0        # B1: deep-loss tail is the SME / small-issue (<50cr) phenomenon
MIN_PRIOR = 5                # min PIT prior IPOs before trusting a banker's track record
BANKER_BAD_RATE = 0.40       # PIT prior bad-outcome rate above which the banker is 'bad'


def bad_outcome_mask(df):
    """Lifetime 'did it fail' = confirmed wipeout OR dead-money (alive, <DEAD, illiquid).
    Same definition as scorecard._bad_outcome_mask / N14.bad_outcomes (pooled)."""
    wipe = df["outcome_class"].astype(str) == "wipeout"
    alive = df["delisted"].fillna(False) == False
    cr = pd.to_numeric(df.get("current_return_from_issue"), errors="coerce")
    dead = alive & (cr < config.DEAD_MONEY_RETURN) & (df.get("liquidity_flag") == "low")
    return (wipe | dead).astype(bool)


def _norm_lm(s):
    return s.astype(str).str.strip()


def banker_freq_full(df):
    """Full-window banker IPO count mapped to each row (the CURRENT rule's basis)."""
    lm = df["lead_manager"].where(_norm_lm(df["lead_manager"]) != "")
    freq = _norm_lm(lm.dropna()).value_counts()
    return _norm_lm(lm).map(freq)


def pit_banker_stats(df):
    """Point-in-time, per row: (prior_count, prior_bad_rate) using ONLY IPOs by the SAME banker
    that listed STRICTLY BEFORE this row. NaN where banker/date missing. No look-ahead."""
    d = df.copy()
    d["_lm"] = _norm_lm(d["lead_manager"])
    d["_ld"] = pd.to_datetime(d["listing_date"], errors="coerce")
    d["_bad"] = bad_outcome_mask(d)
    prior_count = pd.Series(np.nan, index=d.index)
    prior_bad = pd.Series(np.nan, index=d.index)
    for lm, grp in d.groupby("_lm"):
        if lm == "" or lm == "nan":
            continue
        g = grp.sort_values("_ld")
        ld = g["_ld"].values
        bad = g["_bad"].astype(float).values
        # for each i, count/mean over rows with _ld strictly < this _ld
        for pos, idx in enumerate(g.index):
            t = ld[pos]
            if pd.isna(t):
                continue
            mask = ld < t          # strictly earlier listings
            n = int(mask.sum())
            prior_count.loc[idx] = n
            if n > 0:
                prior_bad.loc[idx] = float(np.nanmean(bad[mask]))
    return prior_count, prior_bad


# ---------- candidate flag definitions (each returns a float series: 1/0/NaN) ----------

def flag_current(df, freq, pcount, pbad):
    """CURRENT: freq < 12 (full-window). NaN where banker missing."""
    return pd.Series(np.where(freq.notna(), (freq < OBSCURE_CUTOFF).astype(float), np.nan), index=df.index)


def flag_a_size(df, freq, pcount, pbad):
    """(a) SIZE-aware: freq<12 AND NOT (large MB issue). A large Mainboard issue is never tagged
    obscure (banker under-sampling != wipeout risk there — B1). 'large MB' = type==MB & issue>=SMALL.
    Everything else keeps the freq<12 rule."""
    isz = pd.to_numeric(df.get("issue_size_cr"), errors="coerce")
    is_large_mb = (df["type"] == "MB") & (isz >= SMALL_ISSUE_CR)
    fire = (freq < OBSCURE_CUTOFF) & (~is_large_mb)
    return pd.Series(np.where(freq.notna(), fire.astype(float), np.nan), index=df.index)


def flag_b_quality(df, freq, pcount, pbad):
    """(b) QUALITY-aware: PIT prior bad-rate. Fire if the banker's prior IPOs (>=MIN_PRIOR, PIT)
    failed at >= BANKER_BAD_RATE. ABSTAIN (NaN) when prior record is too thin (<MIN_PRIOR) — we
    DON'T fall back to frequency there (that would re-introduce the artifact). So this flag only
    fires on bankers with an EVIDENCED bad track record."""
    fire = (pcount >= MIN_PRIOR) & (pbad >= BANKER_BAD_RATE)
    valid = (pcount >= MIN_PRIOR) & pbad.notna()
    return pd.Series(np.where(valid, fire.astype(float), np.nan), index=df.index)


def flag_c_hybrid(df, freq, pcount, pbad):
    """(c) HYBRID: fire only if low-frequency AND small/SME issue AND NOT (clean PIT prior record).
      - low freq: freq < 12
      - small/SME: type==SME OR issue < SMALL_ISSUE_CR
      - NOT clean record: NOT (pcount>=MIN_PRIOR AND pbad < BANKER_BAD_RATE)
        i.e. a banker with an evidenced CLEAN prior record (>=5 priors, <40% bad) is exonerated.
    This is the 'don't false-veto reputable, but still catch genuinely-tiny-shop small issues' rule."""
    isz = pd.to_numeric(df.get("issue_size_cr"), errors="coerce")
    small = (df["type"] == "SME") | (isz < SMALL_ISSUE_CR)
    clean_record = (pcount >= MIN_PRIOR) & (pbad < BANKER_BAD_RATE)
    fire = (freq < OBSCURE_CUTOFF) & small & (~clean_record.fillna(False))
    return pd.Series(np.where(freq.notna(), fire.astype(float), np.nan), index=df.index)


def flag_d_coverage_guard(df, freq, pcount, pbad):
    """(d) COVERAGE-GUARD HYBRID (A1b): split cleanly by whether the banker has a PIT track record.
      - record-bearing (pcount>=MIN_PRIOR): QUALITY def — fire iff prior bad-rate >= BANKER_BAD_RATE
        (exonerates reputable good-record banks; fires only on EVIDENCED-bad ones — same as (b) here).
      - thin-record (pcount<MIN_PRIOR): fire iff freq<12 AND type==SME.
        This is the recall-recovery leg: genuinely-obscure small-shop SME names still flag, but the
        thin-record MAINBOARD banks the freq rule false-vetoed (Nuvama, Morgan Stanley — they do MB)
        are NOT flagged. The MB/SME asymmetry is what lets us recover recall without the artifact.
    Evaluable wherever the banker is present (freq.notna)."""
    has_record = (pcount >= MIN_PRIOR) & pbad.notna()
    quality_fire = has_record & (pbad >= BANKER_BAD_RATE)
    is_sme = (df["type"] == "SME")
    thin_fire = (~has_record) & (freq < OBSCURE_CUTOFF) & is_sme
    fire = quality_fire.fillna(False) | thin_fire.fillna(False)
    return pd.Series(np.where(freq.notna(), fire.astype(float), np.nan), index=df.index)


CANDIDATES = {
    "current (freq<12)": flag_current,
    "(a) size-aware": flag_a_size,
    "(b) quality-aware PIT": flag_b_quality,
    "(c) hybrid": flag_c_hybrid,
    "(d) coverage-guard": flag_d_coverage_guard,
}


def wilson(k, n):
    return spine.wilson_ci(k, n)


def recall_table(df, flags_by_name, bad):
    """Bad-outcome RECALL + precision per candidate. THE A1b BAR: recall must NOT regress vs legacy.
    Recall is computed over ALL bad outcomes in df (abstain/NaN counts as a MISS — this is exactly
    what 'abstention halves recall' means), so it is directly comparable across candidates regardless
    of each one's evaluable coverage. Precision = of the IPOs a candidate fires on, the bad-rate."""
    o = bad.astype(bool)
    total_bad = int(o.sum())
    rows = []
    for name, fl in flags_by_name.items():
        fired = fl.fillna(0).astype(bool)
        n_fired = int(fired.sum())
        n_caught = int((fired & o).sum())
        recall = round(100 * n_caught / total_bad, 1) if total_bad else None
        prec = round(100 * n_caught / n_fired, 1) if n_fired else None
        rows.append({"candidate": name, "fires": n_fired, "bad_caught": n_caught,
                     "recall%": recall, "precision%": prec})
    return pd.DataFrame(rows), total_bad


def discrimination_table(df, flag, bad):
    """Per-panel bad-outcome rate WITH vs WITHOUT the flag. Panels mirror N14:
    MB/SME x cohort, wipeout(longterm) + dead-money(boom) pooled into the single `bad` mask
    (matching scorecard._bad_outcome_mask which is what risk_assessment base-rates use)."""
    rows = []
    panels = [("MB", "boom"), ("MB", "longterm"), ("SME", "boom"), ("SME", "longterm")]
    for seg, co in panels:
        idx = df[(df["type"] == seg) & (df["cohort"] == co)].index
        f = flag.reindex(idx); o = bad.reindex(idx).astype(bool)
        v = f.notna()
        f = f[v].astype(bool); o = o[v]
        nw = int(f.sum()); kw = int(o[f].sum())
        no = int((~f).sum()); ko = int(o[~f].sum())
        lw, hw = wilson(kw, nw); lo, ho = wilson(ko, no)
        rw = kw / nw if nw else None; ro = ko / no if no else None
        rows.append({
            "panel": f"{seg}-{co}",
            "N_flagged": nw, "bad%_flagged": (round(100 * rw, 1) if rw is not None else None),
            "ci_flagged": (f"[{100*lw:.0f},{100*hw:.0f}]" if nw else "—"),
            "N_clean": no, "bad%_clean": (round(100 * ro, 1) if ro is not None else None),
            "ci_clean": (f"[{100*lo:.0f},{100*ho:.0f}]" if no else "—"),
            "lift_pp": (round(100 * (rw - ro), 1) if (rw is not None and ro is not None) else None),
        })
    return pd.DataFrame(rows)


def placebo(df, flagfn, bad, freq, pcount, pbad, n_shuffle=200, seed=0):
    """Shuffle banker LABELS, recompute the flag's pooled lift, vs the real lift.
    A real signal should sit in the right tail of the shuffled-lift null distribution."""
    rng = np.random.default_rng(seed)
    real = flagfn(df, freq, pcount, pbad)
    o = bad.astype(bool)
    def pooled_lift(flag):
        f = flag.dropna().astype(bool)
        oi = o.reindex(f.index)
        nw, no = int(f.sum()), int((~f).sum())
        if nw == 0 or no == 0:
            return None
        return 100 * (oi[f].mean() - oi[~f].mean())
    real_lift = pooled_lift(real)
    null = []
    d = df.copy()
    base_lm = d["lead_manager"].values.copy()
    for _ in range(n_shuffle):
        perm = rng.permutation(base_lm)
        d["lead_manager"] = perm
        fr = banker_freq_full(d)
        pc, pb = pit_banker_stats(d) if flagfn in (flag_b_quality, flag_c_hybrid, flag_d_coverage_guard) else (pcount, pbad)
        fl = flagfn(d, fr, pc, pb)
        L = pooled_lift(fl)
        if L is not None:
            null.append(L)
    null = np.array(null)
    pval = float((null >= real_lift).mean()) if len(null) else None
    return real_lift, (float(null.mean()) if len(null) else None), (float(null.std()) if len(null) else None), pval


# B1's named reputable-but-undersampled bankers + the 17 top-quintile flip names (where matchable)
REPUTABLE = ["Nuvama", "Motilal Oswal", "Morgan Stanley", "Smart Horizon", "Choice", "Indorient",
             "Arihant", "Anand Rathi"]


def reputable_artifact_check(df, freq, flags_by_name):
    """For each named reputable banker, report full-window IPO count and how many of their IPOs
    each candidate flags. The goal: candidates (b)/(c) should NOT tag the clean reputable banks."""
    lm = _norm_lm(df["lead_manager"])
    rows = []
    for name in REPUTABLE:
        mask = lm.str.contains(name, case=False, na=False)
        n = int(mask.sum())
        if n == 0:
            continue
        rec = {"banker_contains": name, "full_window_IPOs": n}
        for cand, fl in flags_by_name.items():
            rec[cand] = int(fl[mask].fillna(0).sum())
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    df = spine.load_substrate()
    # honor the listing-coverage exclusion used everywhere
    if "listing_metrics_status" in df.columns:
        df = df[df["listing_metrics_status"] != "unreliable_coverage"].copy()
    df = df.reset_index(drop=True)
    bad = bad_outcome_mask(df)
    freq = banker_freq_full(df)
    print("computing PIT banker stats (strictly-prior) ...")
    pcount, pbad = pit_banker_stats(df)

    flags_by_name = {name: fn(df, freq, pcount, pbad) for name, fn in CANDIDATES.items()}

    print("\n=== (1) PURPOSE PRESERVED — bad-outcome discrimination per candidate, per panel ===")
    for name, fl in flags_by_name.items():
        print(f"\n--- {name} ---  (fires on {int(fl.fillna(0).sum())} IPOs; evaluable {int(fl.notna().sum())})")
        print(discrimination_table(df, fl, bad).to_string(index=False))

    print("\n=== (2) FALSE-VETO — reputable/undersampled bankers tagged by each candidate ===")
    print(reputable_artifact_check(df, freq, flags_by_name).to_string(index=False))

    # how many currently-flagged IPOs does each candidate UN-flag (and how do they perform)
    cur = flags_by_name["current (freq<12)"]
    print("\n=== (2b) Of IPOs the CURRENT rule flags, how many each candidate UN-flags + their bad-rate ===")
    cur_fired = cur.fillna(0).astype(bool)
    for name, fl in flags_by_name.items():
        if name.startswith("current"):
            continue
        unflag = cur_fired & (fl.fillna(0).astype(bool) == False)
        n = int(unflag.sum())
        br = round(100 * bad[unflag].mean(), 1) if n else None
        # compare to bad-rate of the IPOs that REMAIN flagged
        remain = cur_fired & fl.fillna(0).astype(bool)
        nr = int(remain.sum()); brr = round(100 * bad[remain].mean(), 1) if nr else None
        print(f"{name}: un-flags {n} (bad%={br}) | keeps-flagged {nr} (bad%={brr})")

    print("\n=== (2c) RECALL — bad-outcome recall + precision per candidate (A1b BAR: recall must NOT regress) ===")
    rt, total_bad = recall_table(df, flags_by_name, bad)
    print(f"(total bad outcomes in df = {total_bad}; abstain counts as a miss)")
    print(rt.to_string(index=False))

    print("\n=== (3) PLACEBO — pooled lift vs shuffled-banker-label null (real should be right-tail) ===")
    for name, fn in CANDIDATES.items():
        real, nmean, nstd, pval = placebo(df, fn, bad, freq, pcount, pbad, n_shuffle=100, seed=1)
        print(f"{name}: real_lift={real:.1f}pp  null_mean={nmean:.2f}±{nstd:.2f}  p(null>=real)={pval}")


if __name__ == "__main__":
    main()
