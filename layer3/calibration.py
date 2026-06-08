"""Thread A.2 — 'were-we-right' scorecard + honest small-sample stats (pure Python, no scipy).

Three honest-credibility tools over the calls ledger:
 - wilson(): 95% Wilson score interval on a proportion (the right small-N interval; never the
   naive sqrt(p(1-p)/n) which lies at the extremes / small n).
 - scorecard(): per call_type x mode — N, hit-rate (with Wilson CI), median alpha. The monthly
   'did the calls actually work' table.
 - score_reliability(): is the 0-100 score well-ORDERED? bucket APPLY/AVOID/NEUTRAL by score
   decile -> realized hit-rate per bucket (monotonic rising = the ranking means something).
 - brier(): mean squared error of probabilistic calls (kept for when calls carry a probability;
   today's score is a rank, so reliability/ordering is the honest check, not Brier).
"""
import math

import pandas as pd

Z95 = 1.959963985


def wilson(k, n, z=Z95):
    """95% Wilson score interval for k successes in n trials -> (lo, hi) in [0,1]. n=0 -> (0,1)."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def brier(probs, outcomes):
    """Mean squared error between predicted probabilities and 0/1 outcomes (lower = better)."""
    probs, outcomes = list(probs), list(outcomes)
    if not probs:
        return None
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


_GRADE_COL = {"1m": "alpha_1m", "3m": "alpha_3m", "1y": "alpha_1y"}
# what "right" means per call type (binary), graded on the stated horizon's alpha
_WIN_RULE = {
    "APPLY": lambda a: a > 0, "EARLY_APPLY": lambda a: a > 0,
    "AVOID": lambda a: a < 0, "EARLY_AVOID": lambda a: a < 0,    # avoid is "right" if it underperformed
    "PERSIST_HOLD": lambda a: a > 0, "PERSIST_EXIT_LEAN": lambda a: a < 0,
    "EXIT_REVIEW": lambda a: a < 0, "TAKE_PROFITS": lambda a: a < 0,
}


def scorecard(ledger, horizon="3m"):
    """The monthly 'were-we-right' table: per (call_type, mode) -> N, hit-rate + Wilson CI,
    median alpha. Only call types with a defined win-rule and a graded alpha are scored."""
    col = _GRADE_COL[horizon]
    rows = []
    for (ct, mode), g in ledger.groupby(["call_type", "mode"]):
        rule = _WIN_RULE.get(ct)
        if rule is None:
            continue
        a = pd.to_numeric(g[col], errors="coerce").dropna()
        if a.empty:
            continue
        wins = a.map(rule)
        lo, hi = wilson(int(wins.sum()), len(a))
        rows.append({"call_type": ct, "mode": mode, "n": len(a),
                     "hit_rate": round(float(wins.mean()), 3),
                     "ci_lo": round(lo, 3), "ci_hi": round(hi, 3),
                     "median_alpha_pct": round(100 * float(a.median()), 1)})
    return pd.DataFrame(rows).sort_values(["call_type", "mode"]) if rows else pd.DataFrame()


def score_reliability(ledger, horizon="3m", bins=5):
    """Is the score well-ordered? Among APPLY/NEUTRAL/AVOID rows with a score + graded alpha,
    bucket by score quantile -> realized P(alpha>0) per bucket (should rise with the score)."""
    col = _GRADE_COL[horizon]
    d = ledger[ledger["call_type"].isin(["APPLY", "NEUTRAL", "AVOID", "EARLY_APPLY", "EARLY_AVOID"])].copy()
    d["score"] = pd.to_numeric(d["score"], errors="coerce")
    d["a"] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=["score", "a"])
    if len(d) < bins * 3:
        return pd.DataFrame()
    d["bucket"] = pd.qcut(d["score"].rank(method="first"), bins, labels=False)
    rows = []
    for b, g in d.groupby("bucket"):
        wins = (g["a"] > 0)
        lo, hi = wilson(int(wins.sum()), len(g))
        rows.append({"score_bucket": int(b) + 1, "n": len(g),
                     "score_lo": round(g["score"].min(), 1), "score_hi": round(g["score"].max(), 1),
                     "p_up": round(float(wins.mean()), 3), "ci_lo": round(lo, 3), "ci_hi": round(hi, 3)})
    return pd.DataFrame(rows)
