"""N9 — Zombie / dead-money base rate (the missing THIRD competing-risks outcome).

T2 splits outcomes into wiped-out vs survived. But many IPOs neither die nor recover — they sit
ALIVE, deep below issue, and illiquid: dead money you can't even exit. zombie = not delisted AND
current return < −50% from issue AND liquidity_flag='low'. We report the zombie rate alongside
the wipeout band so the full 'bad outcome' picture (wipeout + zombie) is visible. MB/SME apart.
"""
import pandas as pd
from layer3 import spine, config
from layer3.report import Finding

ZOMBIE_THRESHOLD = config.DEAD_MONEY_RETURN   # one source (config) — same cutoff as N14 / the risk gauge


def _rows(df):
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.segment(df, segment=seg, cohort=cohort)
            if len(sub) < config.MIN_N_HINT:
                continue
            alive = sub["delisted"].fillna(False) == False
            cr = pd.to_numeric(sub["current_return_from_issue"], errors="coerce")
            zomb = alive & (cr < ZOMBIE_THRESHOLD) & (sub["liquidity_flag"] == "low")
            wb = spine.wipeout_band(sub)
            n = len(sub); nz = int(zomb.sum())
            wlr = wb["wipeout_lower_rate"] or 0
            rows.append({"segment": seg, "cohort": cohort, "N": n,
                         "dead_money_%": _p(nz / n if n else None),
                         "wipeout_lower_%": _p(wb["wipeout_lower_rate"]),
                         "dead:wipeout_ratio": (round((nz / n) / wlr, 1) if (n and wlr) else None),
                         "bad_outcome_%": _p((nz + wb["wipeout_lower"]) / n if n else None),
                         "median_dead_money_return_%": _p(cr[zomb].median() if nz else None)})
    return rows


def _gave_exit_rows(df):
    """The movement lens: did the CURRENTLY dead-money names ever give an exit? (reach-curve on the
    dead-money subset, maturity-gated 1y, from issue=allottee and listing=secondary)."""
    rows = []
    for seg in config.SEGMENTS:
        for cohort in config.COHORTS:
            sub = spine.maturity_gated(spine.segment(df, segment=seg, cohort=cohort), "1y")
            alive = sub["delisted"].fillna(False) == False
            cr = pd.to_numeric(sub["current_return_from_issue"], errors="coerce")
            dead = sub[alive & (cr < ZOMBIE_THRESHOLD) & (sub["liquidity_flag"] == "low")]
            if len(dead) < config.MIN_N_HINT:
                continue
            ri = spine.reach_curve(dead, "1y", entry="issue")
            up = {u["move"]: u["pct_reached"] for u in ri["reach_up"]}
            rows.append({"segment": seg, "cohort": cohort, "N_dead_money": ri["n"],
                         "ever +20% (issue) %": up.get("+20%"), "ever +50% (issue) %": up.get("+50%"),
                         "median_peak_yr1_%": ri["median_peak_pct"]})
    return rows


def compute(df):
    tables, charts, caveats = [], [], []
    tables.append(("HEADLINE — the real SME risk is DEAD MONEY, not the −100% wipeout. Rate of dead money (alive, "
                   ">50% below issue, illiquid) next to the wipeout rate, with their RATIO. For SME, dead money "
                   "dwarfs confirmed wipeout (boom ~16×); for Mainboard it inverts (wipeout dominates). 'bad_outcome' "
                   "= the combined share. Dead money is arguably worse than a wipeout: a loss you can't even exit.",
                   pd.DataFrame(_rows(df))))
    ge = _gave_exit_rows(df)
    if ge:
        tables.append(("Did the dead money EVER give an exit? Reach-curve (from issue) on the currently-dead-money "
                       "names, maturity-gated year 1: a large share traded well above issue at some point in the "
                       "FIRST YEAR — then the thin float closed the door. The actionable SME rule: treat the "
                       "first-year peak as the exit, because illiquidity removes the second chance.",
                       pd.DataFrame(ge)))

    from layer3 import charts as ch
    r = pd.DataFrame(_rows(df)); r = r[r.cohort == "longterm"]
    if len(r):
        charts.append(("Longterm: wipeout vs zombie vs combined 'bad outcome' by segment",
                       ch.bar_png([f"{x.segment}-wipe" for _, x in r.iterrows()] + [f"{x.segment}-bad" for _, x in r.iterrows()],
                                  list(r["wipeout_lower_%"].fillna(0)) + list(r["bad_outcome_%"].fillna(0)),
                                  ns=list(r["N"]) * 2, title="Bad-outcome share (longterm)", ylabel="%")))
    caveats += [
        "Uses current_return_from_issue (current STATE, the right field for 'is it dead money NOW' — not a "
        "maturity-gated horizon base rate).",
        "Zombie is heavily SME (illiquid by nature). SME wipeout is under-counted (T2 caveat), so for SME the "
        "zombie bucket captures much of the true 'bad outcome' the wipeout metric misses.",
        "Threshold = −50% from issue + liquidity_flag='low'; alive (not delisted).",
    ]
    narrative = ("Beyond 'multibagger or wiped-out', there's a third fate that gets ignored: the living dead — IPOs "
                 "that never formally delist but sit far below issue price and barely trade, so you can't even exit. "
                 "We measure this 'dead-money' rate and add it to the wipeout rate for the full downside picture.")
    return Finding(id="n9", title="N9 · Zombie / dead-money base rate",
                   narrative=narrative, tables=tables, charts=charts, caveats=caveats)


def _p(x):
    return spine.pct_num(x)   # delegated to the shared NaN-safe helper (was a copy-paste)
