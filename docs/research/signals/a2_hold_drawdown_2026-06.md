# A2 — hold-through-drawdown / post-listing conviction overlay (2026-06-10)

**Verdict: REJECT as an act-on EXIT overlay. The strength signal does NOT beat do-nothing
(always-hold) cross-regime, and where it has the right sign it still forfeits a positive-mean
right tail.** Same right-tail mechanism as M1 / A3 — this is a third application of that truth, not
a new exception. A faint *display-only* lean survives (strength → better *median* among underwater
names) but it is NOT regime/decision-day robust and must never become a sell.

Script: `tools/research/a2_hold_drawdown.py` · review CSV: `data/master/review/a2_hold_drawdown.csv`
Run: `PYTHONPATH=. .venv/bin/python tools/research/a2_hold_drawdown.py` · `as_of` 2026-06-06 substrate.

## The question & how A2 differs from A3
A2 (owner, Fujiyama case): for a name UNDERWATER post-listing, is there a point-in-time strength
signal that says "dull-but-building-strength → KEEP HOLDING" vs "dead money → EXIT" that beats
always-hold? This is a CONDITIONAL exit (exit the WEAK underwater names, hold the STRONG ones) —
**different from A3**, which tested a BLANKET sell on the F5e capitulation flag (and found selling
loses). A2 gives the exit rule the best possible chance: it only sells the underwater names that
*also* look technically weak.

## Overlay definition (point-in-time, no look-ahead)
- UNDERWATER at decision day D := `close[D] < issue_price_adj` (allottee in a drawdown). D = 90 td
  (the established F5e/A3 checkpoint); robustness re-run at D = 126 td.
- STRENGTH signal S from sessions 0..D ONLY (PIT): up-day ratio · reclaim off trough
  (close[D]/min(close[0..D]) − 1, the "higher-lows" proxy) · relative strength vs Nifty over the
  window · volume trend (last third vs first third). Composite S = mean of within-underwater-group
  percentile ranks of the four. STRONG = top half of S; WEAK = bottom half.
- Forward alpha vs Nifty measured FROM day D to {6m, 1y, terminal} = exactly what exiting forfeits /
  holding captures. Delisted → terminal = last close (0.0 if wipeout, decision A1); young-alive
  names dropped from that horizon. Exclude `unreliable_coverage`. Cross-regime boom vs longterm.
- The overlay **beats do-nothing** iff the held (STRONG) basket MEAN forward alpha > the HOLD-ALL
  mean — i.e. the WEAK basket you dropped was a reliable mean drag.

Sample: 2313 price files scanned; **768 underwater rows at D=90** (boom 448, longterm 320),
750 at D=126.

## The core table — EXIT-WEAK vs HOLD-ALL (forward alpha from day D; mean = what a portfolio compounds)

### D = 90 (primary checkpoint)
| cohort | horizon | HOLD-ALL mean / med | STRONG mean / med | WEAK mean / med | exit-weak per-name wins | overlay beats do-nothing (mean)? |
|--------|---------|---------------------|-------------------|-----------------|-------------------------|----------------------------------|
| boom | 6m | +7.3% / −11.3% | +19.3% / −8.5% | −5.1% / −16.5% | 72% | **yes** |
| boom | 1y | +9.8% / −16.2% | +22.9% / −4.4% | −4.0% / −28.3% | 75% | **yes** |
| boom | terminal | +33.8% / −9.8% | +64.1% / −1.2% | **+3.5% / −14.5%** | 70% | yes* |
| longterm | 6m | +3.5% / −16.4% | −6.7% / −20.6% | +13.5% / −13.4% | 68% | **NO (inverts)** |
| longterm | 1y | +14.5% / −26.9% | −3.1% / −30.2% | +31.8% / −24.8% | 71% | **NO (inverts)** |
| longterm | terminal | +115.3% / −125.1% | −67.5% / −120.9% | +298.0% / −133.2% | 69% | **NO (inverts)** |

\* boom-terminal "beats" on the mean, BUT the WEAK basket mean is **positive (+3.5%)** — exiting
still forfeits value (see right-tail check).

### D = 126 (robustness)
| cohort | horizon | STRONG mean | WEAK mean | beats do-nothing? | placebo |
|--------|---------|-------------|-----------|-------------------|---------|
| boom | terminal | +8.5% | **+43.9%** | NO | p=0.205 NOISE |
| longterm | terminal | +131.8% | +71.5% | yes | p=0.725 NOISE |

At D=126 the boom signal **flips to noise** (placebo p=0.205) and the WEAK basket terminal mean is
+43.9% (boot CI +3..+104%, excludes 0) — exiting the weak names forfeits a *statistically positive*
mean. The signal is not stable to the choice of decision day.

## Right-tail check (M1 — the kill)
Bootstrap of the WEAK basket's forward-terminal mean (what an exit-weak overlay forfeits):

| cohort | D | WEAK basket fwd-term mean | boot 95% CI |
|--------|---|---------------------------|-------------|
| boom | 90 | **+3.5%** | −12..+23% (straddles 0) |
| boom | 126 | **+43.9%** | **+3..+104% (POSITIVE)** |
| longterm | 90 | +298.0% | −24..+778% (outlier-driven) |
| longterm | 126 | +71.5% | −43..+200% (straddles) |

In NO cohort/decision-day is the WEAK basket mean reliably NEGATIVE. At D=126 boom it is reliably
POSITIVE. So selling the "weak underwater" names forfeits a flat-to-positive mean — the right tail
of recoverers sits inside the weak group too. This is M1/A3's mechanism: an exit that trades the
tail for the body loses where IPOs have tails.

## Placebo (shuffle STRONG/WEAK labels among underwater names, 1000×)
| cohort | D | real STRONG−WEAK gap | shuffle-null 95% | p | verdict |
|--------|---|----------------------|------------------|---|---------|
| boom | 90 | +60.5% | −54.7..+56.7% | 0.021 | survives |
| longterm | 90 | **−365.5%** | −343.9..+349.2% | 0.027 | survives **WRONG SIGN** |
| boom | 126 | −35.4% | −45.3..+45.9% | 0.205 | NOISE |
| longterm | 126 | +60.3% | −286.2..+285.4% | 0.725 | NOISE |

The gap "survives" the placebo at D=90 in both cohorts — but with **OPPOSITE signs** (boom +60%,
longterm −365%). A signal whose discrimination flips sign across regimes is not a usable rule; at
D=126 it collapses to noise. (The longterm sign-inversion is driven by extreme multi-year
multibaggers — Kavita Fabrics +24,494%, etc. — that happen to be classed "weak-at-day-90"; note the
longterm STRONG *median* −120.9% is still BETTER than WEAK −133.2%, so it is the same tail artifact,
not a genuine inversion of the typical name.)

## False exits — winners an exit-weak overlay forfeits
**242 "weak-but-recovered" rows** (strength-percentile <0.5 yet positive forward-terminal alpha)
written to `data/master/review/a2_hold_drawdown.csv`. The weak group is riddled with eventual
recoverers across both cohorts and both decision days — the exit would dump them.

## Relationship to F5e / M1 / A3 and the display-only residue
- **It largely re-discovers M1/A3.** The only consistent, sign-stable signal is a faint
  **median lean**: among underwater names, higher PIT strength → a less-negative *median* forward
  alpha (STRONG median beats WEAK median in 3/4 of the cohort×day cells, incl. longterm). That is
  the same family as the F5e/persistence lean ("dull lister still below water + technically weak =
  more likely to stay bad") — useful as a *display* read, NOT a new edge.
- **As an EXIT it fails the bar**: it does not beat do-nothing on the MEAN cross-regime, its
  discrimination sign flips boom↔longterm, it is not stable across decision days (D=90→126), and
  the WEAK basket it sells carries a flat-to-positive mean (right-tail trap). Score policy unchanged
  (post-listing signal → never a score input; here, not even an act-on exit).
- **For the Fujiyama case specifically:** Fujiyama was underwater at day 90 (max90/issue 0.987) yet
  ran to +44%. An exit-weak overlay offers no reliable way to have known to hold it that beats
  simply holding — consistent with A3's finding that the day-90 picture can't separate it.

## Falsifier (pre-declared) — outcome
FALSIFIER (what would have made the overlay act-on-able): WEAK basket forward MEAN reliably NEGATIVE
in BOTH cohorts AND below STRONG, with a same-sign placebo-surviving gap, stable across D. **None
held.** Boom-only at D=90 has the right sign but a non-negative WEAK mean; longterm inverts; D=126
is noise. Rejected as an exit overlay.

## Proposed `rules/index.md` line (controller integrates — A1 owns the file)
`A2 hold-through-drawdown conviction overlay (2026-06-10): among UNDERWATER (close[D]<issue_adj)
names, a PIT strength signal (up-day ratio + reclaim-off-trough + RS-vs-Nifty + volume-trend) to
EXIT the WEAK and HOLD the STRONG does NOT beat do-nothing cross-regime. Discrimination sign FLIPS
boom↔longterm (D=90 placebo p=0.021/0.027 but gaps +60.5%/−365.5%, opposite signs) and collapses to
NOISE at D=126 (p=0.205/0.725). The WEAK basket you'd sell carries a flat-to-POSITIVE mean fwd-term
alpha (boom +3.5% D90, +43.9% [boot +3..+104] D126) — exiting forfeits the right tail (242
weak-but-recovered names). Only a faint DISPLAY lean survives (strength → less-negative MEDIAN, same
family as F5e/persistence). VERDICT: REJECT as an exit/sell; display-only median lean at best.
Re-confirms M1/A3 (no exit beats hold where IPOs have tails). a2_hold_drawdown_2026-06.md.`
