"""N15 · The clean compounder — low-debt × high-ROE is the one validated cross-regime INTERACTION.

Single fundamentals mostly failed cross-regime (profitable MIXED, debt not-robust, OFS MIXED). But a
COMBINATION survives: high return-on-equity that is NOT juiced by debt. The interaction is genuinely
super-additive — low-debt ALONE is often worse than the base (it selects slow, ungeared businesses),
high-ROE alone is mediocre, but TOGETHER they are the best cell in every segment×cohort. Mechanism:
high ROE without leverage = real operating quality, not financial engineering. This is the disciplined
output of the interaction hunt — almost nothing else combined survives both regimes (the risk-side
hunt found NO cross-regime interaction at all; see the tested-signal registry).

Built/kept as a SEPARATE exploratory signal — it does NOT feed the predictor score (per the locked
'evolve-only-if-robust' policy) until it passes an OOS-robust pass. Verified independently 2026-06-01.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

LOW_DEBT, HIGH_ROE = 0.5, 15.0


def _cell(g, h, mask, ok):
    a = spine.alpha_series(g, h)
    rfi = pd.to_numeric(g.get(f"return_from_issue_{h}"), errors="coerce")
    m = mask & ok
    n = int(m.sum())
    if n < config.MIN_N_HINT:
        return {"N": n, "median_alpha_%": None, "pct_positive": None, "pct_2x": None}
    s, r = a[m], rfi[m]
    return {"N": n, "median_alpha_%": round(100 * float(s.median()), 1),
            "pct_positive": round(100 * float((s > 0).mean()), 1),
            "pct_2x": round(100 * float((r >= 1.0).mean()), 1)}


def compute(df):
    tables, charts, caveats = [], [], []
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            g = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), "3y")
            de = pd.to_numeric(g["pre_ipo_debt_equity"], errors="coerce")
            roe = pd.to_numeric(g["pre_ipo_roe_pct"], errors="coerce")
            a = spine.alpha_series(g, "3y")
            ok = de.notna() & roe.notna() & a.notna()
            ld, hr = de < LOW_DEBT, roe > HIGH_ROE
            base = _cell(g, "3y", ok, ok)
            both = _cell(g, "3y", ld & hr, ok)
            if base["N"] < config.MIN_N_HINT or both["N"] < config.MIN_N_HINT:
                continue
            rows.append({"segment": seg, "cohort": cohort,
                         "base_N": base["N"], "base_medα_%": base["median_alpha_%"], "base_2x_%": base["pct_2x"],
                         "lowdebt_only_medα_%": _cell(g, "3y", ld & ~hr, ok)["median_alpha_%"],
                         "highROE_only_medα_%": _cell(g, "3y", ~ld & hr, ok)["median_alpha_%"],
                         "BOTH_N": both["N"], "BOTH_medα_%": both["median_alpha_%"],
                         "BOTH_P+_%": both["pct_positive"], "BOTH_2x_%": both["pct_2x"]})
    tables.append(("Low-debt (D/E<0.5) × high-ROE (>15%), 3y, maturity-gated. Read across: the BOTH cell beats the "
                   "base AND beats each feature alone in every segment×cohort — and low-debt ALONE is often WORSE "
                   "than base, so this is a true super-additive interaction, not two okay features added. "
                   "(MB/longterm: base −43% medα → BOTH +1%; SME/boom → +91%.)", pd.DataFrame(rows)))
    caveats += [
        "This is the ONE interaction that cleared the full bar (super-additive + cross-regime + N≥~30/cell). The "
        "risk-side interaction hunt found NONE — single wipeout flags are the whole story there. Logged in the "
        "tested-signal registry alongside the rejected/longterm-only candidates.",
        "SEPARATE exploratory signal: it does NOT feed the predictor score yet (locked 'evolve-only-if-robust' "
        "policy — it must pass an OOS-robust pass to graduate). Shown for insight + as a 'Relationships' lens.",
        "3y horizon (the upside signal is absent at 1y — all 1y cohort medians sit at ~0). Alpha is from-listing "
        "vs Nifty; 2x is from issue. BOTH-cell N is floor-level (~34–41) in some panels — robust in sign, modest in N.",
        "Mechanism: high ROE WITHOUT leverage = genuine operating quality; high ROE WITH high debt is financial "
        "engineering that doesn't survive. The conjunction is the signal; neither half alone is.",
        "N caveat (disclosure): the BOTH-cell is N≈34–41, but the 'beats each feature alone' comparison rests on "
        "single-alone cells that are hint-tier in Mainboard (N≈20–23, above the N≥10 floor but below the N≥30 "
        "claim floor). The super-additive SIGN holds in all 4 panels; the MB single-alone magnitudes are directional.",
    ]
    narrative = ("Almost no single pre-IPO fundamental predicts winners cross-regime — but one COMBINATION does: "
                 "a company with high return-on-equity that isn't propped up by debt. Low-debt alone is often a "
                 "laggard and high-ROE alone is mediocre, yet together they are the best cohort in every era and "
                 "segment — the 'clean compounder'. It's the disciplined prize from the interaction hunt (the only "
                 "combo, risk or upside, to survive the full cross-regime + super-additive test).")
    return Finding(id="n15", title="N15 · The clean compounder (low-debt × high-ROE — the one validated interaction)",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)
