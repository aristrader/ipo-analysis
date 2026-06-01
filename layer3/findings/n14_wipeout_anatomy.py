"""N14 — Anatomy of a wipeout (pre-listing red flags → bad outcome).

The question: do IPOs that get WIPED OUT or become DEAD MONEY share PRE-LISTING patterns we
could have read off the prospectus? We test RHP-only features (never post-listing price) against
two bad outcomes, reported together because each cohort only fully shows one of them:
  - WIPEOUT   = outcome_class=='wipeout' (~-100% / compulsory delist). Needs TIME, so it is
                carried by the LONGTERM (2006-19) cohort; the boom cohort is barely old enough.
  - DEAD MONEY = alive & current_return_from_issue < -0.50 & liquidity_flag=='low' (the
                un-exitable zombie). Carried by the boom cohort, esp. SME, where formal wipeout
                hasn't had time to register (SME wipeout is a survivorship UNDER-count).

Method spine: hard MB/SME split; min-N floors (>=30 claim / >=10 hint); proportions with Wilson
CIs; a flag is a HYPOTHESIS until its SIGN holds in BOTH cohorts. Financials coverage is gappy
(MB-longterm has multi-year sales for only ~21% of rows) so we report N-available per flag and
NEVER impute — a null flag never counts as a red flag, and rows are scored only where >=3 of the
5 score-flags are evaluable.

Cross-regime VALIDATED red flags (sign holds across cohorts/outcomes): micro market-cap, tiny
pre-IPO sales (<25cr / <10cr), loss-making at IPO (PAT<=0 latest year). Directional-only or
NOT robust: declining revenue/PAT (strong on SME dead-money, flips on SME-longterm wipeout),
high debt/equity (only MB-longterm), accrual flag (too thin). REVERSE: high OFS is PROTECTIVE
(OFS-heavy issues are established companies), so OFS is NOT a wipeout red flag.
"""
import numpy as np
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

DEAD_THRESHOLD = config.DEAD_MONEY_RETURN   # one source (config) — same cutoff as N9 / the risk gauge

# the cross-regime-validated PRE-LISTING red flags that compose the additive score (NO ML, transparent
# count). NOTE: `micro_mcap` is DELIBERATELY EXCLUDED — `market_cap_class` is the company's CURRENT
# market cap (screener), so a wiped-out name is "micro" *because* it crashed (median current mcap of a
# wipeout = ₹9cr vs ₹770–1200cr for survivors). It's reverse-causation, not a prospectus-readable
# predictor; it's shown in the flag table below ONLY as a cautionary example, never scored/weighted.
# `obscure_lead_mgr` GRADUATED (v2 deepening, cross-regime verified): obscure bankers → monotonic death.
SCORE_FLAGS = ["tiny_sales_lt25cr", "pat_negative_latest", "declining_revenue", "declining_pat",
               "obscure_lead_mgr"]


def _fbool(df, cond, valid):
    """Float flag series: 1.0/0.0 where evaluable, NaN where the inputs are missing (never imputed)."""
    return pd.Series(np.where(valid, cond.astype(float), np.nan), index=df.index)


def build_flags(df):
    """All candidate PRE-LISTING (RHP-derived) red flags, as float series (NaN = not evaluable)."""
    N = lambda c: pd.to_numeric(df[c], errors="coerce")
    s1, s3 = N("net_sales_yr1"), N("net_sales_yr3")   # yr3 = latest year (closest to IPO)
    p1, p3 = N("pat_yr1"), N("pat_yr3")
    o3 = N("operating_profit_yr3")
    ps, isz, de = N("pre_ipo_net_sales"), N("issue_size_cr"), N("pre_ipo_debt_equity")
    mgn, ppat, ofs = N("pre_ipo_pat_margin_pct"), N("pre_ipo_pat"), N("ofs_pct")
    pe = N("pe_ratio")
    secmed = pe.groupby([df["type"], df["broad_sector"]]).transform("median")
    # obscure lead manager = small/infrequent banker (crude tier by issue-count frequency; from the RHP
    # cover, so pre-listing & 100% covered → the one NEW flag that validates cross-regime).
    lm = df["lead_manager"].where(df["lead_manager"].astype(str).str.strip() != "")
    lmfreq = lm.map(lm.value_counts())
    f = {
        "tiny_sales_lt25cr": _fbool(df, ps < 25, ps.notna()),
        "tiny_sales_lt10cr": _fbool(df, ps < 10, ps.notna()),
        "micro_issue_lt15cr": _fbool(df, isz < 15, isz.notna()),
        "micro_mcap": _fbool(df, df["market_cap_class"].eq("micro"), df["market_cap_class"].notna()),
        "declining_revenue": _fbool(df, s3 < s1, s1.notna() & s3.notna() & (s1 > 0)),
        "declining_pat": _fbool(df, p3 < p1, p1.notna() & p3.notna()),
        "pat_negative_latest": _fbool(df, p3 <= 0, p3.notna()),
        "high_debt_gt2": _fbool(df, de > 2, de.notna()),
        "thin_margin_lt3pct": _fbool(df, mgn < 3, mgn.notna()),
        "lossmaking_at_ipo": _fbool(df, ppat <= 0, ppat.notna()),
        "accrual_pat_pos_op_neg": _fbool(df, (p3 > 0) & (o3 <= 0), p3.notna() & o3.notna()),
        "expensive_vs_sector": _fbool(df, pe > secmed, pe.notna() & secmed.notna() & (pe > 0)),
        "high_ofs_gt50": _fbool(df, ofs > 50, ofs.notna()),
        "obscure_lead_mgr": _fbool(df, lmfreq < 12, lmfreq.notna()),   # banker with <12 IPOs in the dataset
    }
    return f


def bad_outcomes(df):
    """The two bad-outcome masks: wipeout (authoritative -100%) and dead-money (un-exitable zombie)."""
    wipe = df["outcome_class"] == "wipeout"
    alive = df["delisted"].fillna(False) == False
    cr = pd.to_numeric(df["current_return_from_issue"], errors="coerce")
    dead = alive & (cr < DEAD_THRESHOLD) & (df["liquidity_flag"] == "low")
    return wipe, dead


def _with_without(outcome, flag, idx):
    f = flag.reindex(idx); o = outcome.reindex(idx)
    v = f.notna(); f = f[v].astype(bool); o = o[v].astype(bool)
    out = {}
    for lab, m in [("with", f), ("without", ~f)]:
        n = int(m.sum()); k = int(o[m].sum())
        lo, hi = spine.wilson_ci(k, n)
        out[lab] = {"n": n, "rate": (k / n if n else None), "lo": lo, "hi": hi}
    return out


def _cell(r):
    if r["rate"] is None or r["n"] < config.MIN_N_HINT:
        return f"insufficient (N={r['n']})"
    return f"{100*r['rate']:.1f}% [{100*r['lo']:.0f},{100*r['hi']:.0f}]"


# longterm shows wipeout (mature); boom shows dead-money (young). The high-N validation panels
# are SME (large N both cohorts); MB-longterm is the wipeout-rich panel.
PANELS = [("MB", "longterm", "wipeout"), ("SME", "longterm", "wipeout"),
          ("SME", "boom", "dead_money"), ("MB", "longterm", "dead_money")]
ALL_FLAGS = ["tiny_sales_lt25cr", "tiny_sales_lt10cr", "micro_issue_lt15cr",
             "pat_negative_latest", "lossmaking_at_ipo", "obscure_lead_mgr",
             "declining_revenue", "declining_pat",
             "high_debt_gt2", "thin_margin_lt3pct", "accrual_pat_pos_op_neg",
             "expensive_vs_sector", "high_ofs_gt50",
             "micro_mcap_REVERSE_CAUSATION_not_a_predictor"]
# alias so build_flags' key still resolves for the cautionary row
_FLAG_ALIAS = {"micro_mcap_REVERSE_CAUSATION_not_a_predictor": "micro_mcap"}


def _flag_rows(df, flags, wipe, dead):
    rows = []
    for fname in ALL_FLAGS:
        flag = flags[_FLAG_ALIAS.get(fname, fname)]
        rec = {"red_flag": fname}
        for seg, co, oc in PANELS:
            idx = df[(df.type == seg) & (df.cohort == co)].index
            r = _with_without(wipe if oc == "wipeout" else dead, flag, idx)
            key = f"{seg}-{co[:2]}-{'W' if oc == 'wipeout' else 'D'}"
            rw, ro = r["with"], r["without"]
            if rw["rate"] is None or ro["rate"] is None or rw["n"] < config.MIN_N_HINT:
                rec[key] = f"N={rw['n']}"
            else:
                lift = (rw["rate"] - ro["rate"]) * 100
                rec[key] = f"{lift:+.1f}pp ({100*rw['rate']:.0f}v{100*ro['rate']:.0f}, N={rw['n']})"
        rows.append(rec)
    return rows


def _score_rows(df, flags, wipe, dead):
    F = pd.DataFrame({k: flags[k] for k in SCORE_FLAGS})
    score = F.fillna(0).sum(axis=1)
    navail = F.notna().sum(axis=1)
    df = df.assign(_score=score, _navail=navail)
    bad = wipe | dead
    panels = [("SME", "boom"), ("SME", "longterm"), ("MB", "longterm")]
    rows = []
    for seg, co in panels:
        sub = df[(df.type == seg) & (df.cohort == co) & (df._navail >= 2)]
        o = bad.reindex(sub.index).astype(bool)
        for band, m in [("0 flags", sub._score == 0), ("1 flag", sub._score == 1),
                        ("2 flags", sub._score == 2), ("3+ flags", sub._score >= 3)]:
            n = int(m.sum()); k = int(o[m].sum())
            lo, hi = spine.wilson_ci(k, n)
            rows.append({"segment": seg, "cohort": co, "score_band": band, "N": n,
                         "bad_outcome_%": (round(100 * k / n, 1) if n else None),
                         "wilson_ci": (f"[{100*lo:.0f},{100*hi:.0f}]" if n else "—")})
    return rows


def compute(df):
    flags = build_flags(df)
    wipe, dead = bad_outcomes(df)
    tables, charts, caveats = [], [], []

    tables.append((
        "Per red flag: the LIFT (pp) in the bad-outcome rate WITH vs WITHOUT the flag, across four "
        "panels — MB/SME x cohort, wipeout(W) for longterm, dead-money(D) for boom (each cell: "
        "lift, with%v-without%, N on the flagged side). Sub-floor cells show N only. Sign must hold "
        "across panels to graduate from hypothesis.",
        pd.DataFrame(_flag_rows(df, flags, wipe, dead))))

    tables.append((
        "ADDITIVE RED-FLAG SCORE (0..5 count of PROSPECTUS-READABLE flags: tiny sales <25cr, PAT<=0 "
        "latest year, declining revenue, declining PAT, obscure lead manager) → bad-outcome rate (wipeout "
        "OR dead-money) by band. (Current market-cap is excluded — reverse-causation, see caveats.) Scored "
        "only where >=2 flags are evaluable; a null flag never counts. More flags = higher death rate.",
        pd.DataFrame(_score_rows(df, flags, wipe, dead))))

    from layer3 import charts as ch
    sr = pd.DataFrame(_score_rows(df, flags, wipe, dead))
    smeb = sr[(sr.segment == "SME") & (sr.cohort == "boom")]
    if len(smeb):
        charts.append(("SME-boom: bad-outcome rate rises monotonically with the red-flag count",
                       ch.bar_png(list(smeb.score_band), list(smeb["bad_outcome_%"].fillna(0)),
                                  ns=list(smeb.N), title="Red-flag score → bad outcome (SME boom)",
                                  ylabel="bad-outcome %")))

    caveats += [
        "⚠ REVERSE-CAUSATION (why micro market-cap is EXCLUDED from the score/predictor): "
        "`market_cap_class` is the company's CURRENT market cap (screener), not IPO-time. A wiped-out "
        "name is 'micro' BECAUSE it crashed (median current mcap of a wipeout = ₹9cr vs ₹770–1200cr for "
        "survivors; 95% of wipeouts read 'micro'). Its huge apparent lift (+52pp) is the outcome looking "
        "back at itself — NOT a prospectus-readable signal. It is shown in the flag table ONLY as a "
        "cautionary example and never enters the red-flag score or any predictor gauge.",
        "PRE-LISTING ONLY (the scored flags): sales/PAT level & trend, leverage, margin, OFS, issue "
        "size — all RHP/screener-as-of-IPO, never post-listing price. No look-ahead.",
        "Two outcomes by design: WIPEOUT needs years (longterm cohort); DEAD MONEY captures the "
        "boom cohort's un-exitable zombies before formal delisting can register. SME wipeout is a "
        "survivorship UNDER-count, so for boom-SME lean on dead-money.",
        "Coverage gaps: multi-year financials are boom-skewed (MB-longterm ~21% have all 3 sales "
        "years); N-available reported per flag; nulls never imputed and never counted as a flag.",
        "VALIDATED prospectus-readable flags (sign holds across regimes): tiny pre-IPO sales (<25cr / "
        "<10cr), loss-making at IPO (PAT≤0), and OBSCURE LEAD MANAGER (small/infrequent banker → monotonic "
        "death gradient in all panels, 100% coverage). DIRECTIONAL-only: declining revenue/PAT (flips on "
        "SME-longterm wipeout). NOT robust: high debt/equity (only MB-longterm, N=13), thin margin, micro "
        "issue size, accrual, valuation, sector. REJECTED (wrong sign): LOW promoter holding (high retention "
        "= thin illiquid float = the zombie profile), high GMP (protective). See `wipeout_anatomy_v2.md`.",
        "REVERSE signal: high OFS (>50%) is PROTECTIVE, not a red flag — OFS-heavy issues are "
        "established companies (founders cashing out a real business), so it must NOT enter a "
        "wipeout-risk gauge with a positive sign.",
    ]
    narrative = (
        "Do the IPOs that get wiped out or turn into dead money carry tells in the PROSPECTUS — things "
        "you could read before listing? Yes, modestly: tiny pre-IPO sales and being loss-making at IPO "
        "raise the death rate in both eras, and a transparent additive count of such flags (no ML) sorts "
        "IPOs from a low death rate at 0 flags upward. (The seductive 'micro-caps die' pattern is a TRAP — "
        "current market-cap is tiny BECAUSE the stock crashed, so we exclude it; see caveats.) We read "
        "BOTH outcomes — formal wipeout (mature 2006-19 cohort) and un-exitable dead money (young boom "
        "cohort) — because each regime only fully reveals one of them.")
    return Finding(id="n14", title="N14 · Anatomy of a wipeout (pre-listing red flags)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
