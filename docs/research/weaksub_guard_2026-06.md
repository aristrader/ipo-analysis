# Weak-subscription false-APPLY guard (B1 seed) — VERDICT: REJECT — 2026-06-10

Tests the B1 miss-mining seed: among **would-be-APPLY** IPOs (top-segment-quintile AND 0 wipeout
flags), does adding a **low-subscription veto** (`sub_total_x < ~3×`) cut false-APPLYs (losers we'd
APPLY) WITHOUT killing the winners — **cross-regime**? This is the conditional 2nd-order angle (a guard
ON the APPLY decision), distinct from the dead 1st-order "undersubscribed → bad" screen.

Script: `tools/research/weaksub_guard.py` · pool CSV: `data/master/review/weaksub_guard_apply_pool.csv`.

## Why this is NOT a re-tread (and what IS already settled)
Checked `rules/index.md` first. Already-settled subscription signals (do NOT re-test):
- **`undersubscribed` / `demand_per_size` — REJECTED** (mixed/thin cross-regime, hypothesis batch 2026-06-06).
- **`n2-subscription`, `n3-demand-skew`, `f-flip-trap` — reported BOOM-ONLY** (longterm subscription ≈ 0,
  cannot be cross-validated).
- **`qib_retail_ratio` — WATCHLIST** (lean-positive, display-only candidate).
- The existing **CANDIDATE line** "low-subscription veto on analog-top-quintile APPLYs (display-first,
  untested)" — THIS is the entry this test resolves.

The genuinely new angle tested here: the veto **conditioned on a would-be-APPLY** (the *disagreement* —
analog score says top-quintile, the IPO's own demand says weak). That is what B1 claimed was the shared
tell of the false-APPLYs. **It does not survive.**

## Method (point-in-time, mirrors miss_mining.py / calls.py)
- For every **matured** IPO (listed ≥365d before AS_OF 2026-06-06, equity, reliable listing,
  **2020+** — see longterm caveat), reproduce the genuine PIT would-be-APPLY: analog pool = ONLY IPOs
  listed strictly before its listing-month; data-informed weights derived per listing-month on
  prior-only data (the established cheap PIT pattern — pool is dominated by 2000+ matured IPOs, weights
  barely drift); per-SEGMENT combined-score quintiles from the same prior-only scored frame; wipeout
  flags. **would-be-APPLY = top-quintile AND 0 flags** (exactly `calls.py`). Pool = **437 APPLYs**
  (SME 246 / MB 191; sub coverage 388/437).
- Among APPLYs **with** sub data, split **LOW (<3×)** vs **ADEQUATE (≥3×)**; compare bad-outcome rate
  (Wilson95), forward `alpha_1y`/`return_1y` medians, win-rate, and **winners-lost if you veto**.
- **Survivorship-honest** (wipeout terminal −100%); exclude `unreliable_coverage`; min-N floors.
- **Bad** = loser/wipeout OR allottee < −15% OR drawdown ≤ −50% (ended-up breaks the tie → winner),
  allottee-anchored. **Winner** = winner/multibagger OR allottee > +25%.
- **Reverse-causation note:** subscription closes ~T-1, so it IS pre-listing-readable (legit ex-ante),
  but it is itself a demand OUTCOME and partly proxies what the analog score already captures.

## The would-be-APPLY split table (N + Wilson95)
| cohort | cell | N | bad % | Wilson95 | winner % | a1y med | ret1y med |
|---|---|---:|---:|---|---:|---:|---:|
| ALL-MATURED 2020-25 | LOW <3× | 74 | 44.6% | 33.8–55.9 | 43.2% | +0.4% | +18.2% |
| ALL-MATURED 2020-25 | ADEQUATE ≥3× | 314 | 36.9% | 31.8–42.4 | 51.0% | −11.1% | +37.0% |
| BOOM-MATURED 2020-23 | LOW <3× | 48 | 39.6% | 27.0–53.7 | 56.2% | **+23.8%** | +33.9% |
| BOOM-MATURED 2020-23 | ADEQUATE ≥3× | 147 | 34.0% | 26.8–42.0 | 57.8% | +1.2% | +57.1% |
| RECENT-MATURED 2024-25 | LOW <3× | 26 | 53.8% | 35.5–71.2 | 19.2% | −14.2% | −15.0% |
| RECENT-MATURED 2024-25 | ADEQUATE ≥3× | 167 | 39.5% | 32.4–47.1 | 44.9% | −13.7% | +19.7% |
| LONGTERM 2006-19 | — | 0 | — | — | — | — | — |

**Threshold sweep (ALL-MATURED, robustness):** gap (low−adeq bad%) = +5.5pp (<2×), +7.7pp (<3×),
+4.9pp (<5×), +6.4pp (<10×) — small and never cleanly separating; winners-dumped 22/32/43/55.

## Winners-lost if you veto the low-sub APPLYs
- **ALL-MATURED:** dumps 74 APPLYs → avoids 33 losers but **DUMPS 32 winners** (lost-winner median
  allottee **+119%**). Roughly one winner dumped per loser avoided, and the dumped winners are the
  fat right tail.
- **BOOM-MATURED:** dumps 48 → avoids 19 losers, **DUMPS 27 winners** (median **+134%**). The veto is
  net-destructive here: the low-sub APPLY cell has HIGHER alpha_1y (+23.8% vs +1.2%) and equal win-rate.
- **RECENT-MATURED:** dumps 26 → avoids 14 losers, dumps 5 winners. Only here does the veto look
  defensible — and these outcomes are the YOUNGEST/least-matured (winners haven't run yet).

## Placebo (shuffle sub label across the APPLY pool, 2000 iters, seed 20260609)
- **ALL-MATURED:** real bad-rate gap +7.7pp; shuffled ≥ real in **273/2000 (pseudo-p 0.137) → FAIL**.
- **BOOM-MATURED:** real gap +5.6pp; shuffled ≥ real in **609/2000 (pseudo-p 0.304) → FAIL**.
A genuine edge must not reproduce under a shuffled subscription label. It does, comfortably, in both
cohorts. The separation is within noise.

## Redundancy-with-existing check
- UNCONDITIONAL (the dead 1st-order screen): low-sub `alpha_1y` median −10.7% (n=176) vs adequate
  −11.7% (n=724) — essentially flat, consistent with `undersubscribed` being REJECTED.
- Conditioning on would-be-APPLY does NOT rescue it: the gap is small, placebo-reproducible, and
  cross-regime INVERTS (boom low-sub APPLYs *outperform*). So the guard adds no incremental signal over
  the already-rejected first-order screen.

## VERDICT — REJECT (does not survive cross-regime + placebo)
1. **Placebo fails in BOTH testable cohorts** (p 0.137 / 0.304) — the low-vs-adequate bad-rate gap is
   noise, not an edge.
2. **Cross-regime inversion** — in boom-matured (the matured cell B1 lacked), low-sub would-be-APPLYs
   had EQUAL win-rate and BETTER forward alpha (+23.8% vs +1.2%). B1's "weak sub = false APPLY" was
   driven by the **young recent cohort** (2024-25 unmatured outcomes), not a durable truth.
3. **It dumps winners ~1:1 with losers**, and the dumped winners are the fat tail (median allottee
   +119–134%) — exactly the "don't just dump winners" failure mode the brief warned about.
4. **Longterm NOT TESTABLE** (sub coverage ~9%) → no third cross-regime cell available regardless.

B1's seed was an honest read of a young cohort; matured + placebo evidence overturns it. The downside-
first instinct (a low-demand caution) is reasonable as *information*, but it is **not a defensible APPLY
veto** and must not enter the gate or the score.

## Honesty / uncertainties
- Recent-matured outcomes are 12–~18mo old; their winners may still develop (which would only weaken the
  guard further, since low-sub winners would grow). The boom-matured cell (3y+) is the load-bearing one.
- PIT quintiles use per-segment prior-pool thresholds (matches `calls.py`); ±a few borderline q4/q5 cases
  under a pooled-calibration alternative, but the placebo failure is far from any boundary.
- 437 would-be-APPLYs is a healthy pool; the LOW cells (74/48/26) clear the ≥12 min-N but the recent
  LOW cell (26) is thin — its lone "supportive" direction is the least trustworthy.

## Reproduce
`PYTHONPATH=. python tools/research/weaksub_guard.py` (~13 min: per-month PIT weight derivations +
per-IPO predicts; restores the committed `scorecard_weights.json` in a finally block). Writes the
APPLY-pool CSV; prints the split table, veto winners-lost, placebo, and the redundancy check.
