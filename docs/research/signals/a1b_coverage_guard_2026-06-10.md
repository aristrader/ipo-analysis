# A1b — obscure-lead-manager flag: coverage-guard hybrid + verdict (2026-06-10)

Resolves backlog **A1b** (the proper fix after A1's quality-aware def was downgraded to display-only by
adversarial review for HALVING recall). Built + tested under the locked **evolve-only-if-robust** policy.
Reproduce: `tools/research/a1_banker_flag.py` (discrimination + recall + false-veto + placebo) and
`tools/research/a1_fold_test.py [1y|3y] coverage_guard` (OOS top-quintile lift A/B vs legacy).

## The problem A1b had to solve
- **legacy (freq<12)** — recall 25.4%, but a COVERAGE ARTIFACT: false-vetoes reputable-but-undersampled
  banks (Nuvama, Morgan Stanley → the Park Medi miss). This is the current LIVE def.
- **quality (PIT bad-rate)** — artifact-free, but ABSTAINS on thin records → recall collapses to 13.2%
  (misses ~78 real small-shop SME wipeouts). Downgraded to display-only.
- **A1b bar:** recover recall WITHOUT re-introducing the false-veto. Promote to LIVE only if **recall does
  not regress** AND OOS fold lift holds.

## The candidate — (d) coverage-guard hybrid
Split cleanly by whether the banker has a point-in-time track record:
- **record-bearing** (`>=MIN_PRIOR=5` prior IPOs): use the QUALITY def — fire iff prior bad-rate `>=0.40`.
  (Exonerates reputable good-record banks; fires only on EVIDENCED-bad ones.)
- **thin-record** (`<MIN_PRIOR` priors): fire iff `freq<12` **AND `type==SME`**.
  The MB/SME asymmetry is the whole idea: the thin-record banks the freq rule false-vetoed (Nuvama,
  Morgan Stanley) are **Mainboard**; genuinely-obscure small shops are **SME**. Restricting the frequency
  leg to SME recovers small-shop recall without re-vetoing thin Mainboard names.

(Distinct from the original study's hybrid (c), which AND-ed small/SME onto the record-bearing case too and
went negative in SME-longterm. (d) keeps (b)'s clean record-bearing verdict untouched and only ADDS a
thin-record SME leg.)

## Evidence (full substrate, `listing_metrics_status != unreliable_coverage`)

### (1) Recall + precision — THE A1b bar (recall over all 394 bad outcomes; abstain = miss)
| candidate | fires | bad_caught | recall% | precision% |
|---|---|---|---|---|
| legacy (freq<12) | 430 | 100 | **25.4** | 23.3 |
| quality PIT | 177 | 52 | 13.2 | 29.4 |
| **(d) coverage-guard** | 365 | 97 | **24.6** | **26.6** |
→ coverage-guard recovers recall to **24.6%** (legacy 25.4; quality 13.2) — essentially flat (3 fewer of
394) — AND improves precision (26.6 vs 23.3). It catches nearly what legacy catches with fewer, better fires.

### (2) False-veto — reputable banks tagged
| banker | full-window IPOs | legacy | quality | **(d)** |
|---|---|---|---|---|
| Nuvama | 11 | 11 | 0 | **0** |
| Morgan Stanley | 8 | 8 | 0 | **0** |
| Arihant | 11 | 11 | 0 | **2** |
| Anand Rathi | 24 | 0 | 12 | 12 |
→ exonerates Nuvama/Morgan Stanley (the documented artifact). Anand-Rathi 12 = evidenced-bad PIT record
(intended, identical to quality). The artifact is fixed.

### (3) Cross-regime discrimination (bad% with vs without the flag, lift_pp)
| panel | (d) lift_pp |
|---|---|
| MB-boom | −0.3 (noise, ~0 base both sides) |
| MB-longterm | +2.2 |
| SME-boom | **+15.2** (CI-separated: 30.2 vs 14.9) |
| SME-longterm | +1.7 |
→ positive 3/4, strong + CI-separated only in SME-boom (the same panel that carries (b)). Longterm panels weak.

### (4) Placebo (shuffle banker labels, 100×, pooled lift)
(d): real 11.5pp, null 2.84±2.33, p(null≥real)=0.00 → clean excess ≈ 8.7pp, placebo-clean. (Null mean is
positive — part of the lift is segment-composition mechanical, same honesty caveat as A1.)

### (5) OOS top-quintile fold lift A/B vs legacy (evolve-only-if-robust)
**1y (high-N folds):** better 3 / same 0 / worse 0 (deltas +0.1, +1.5, +0.4) — never degrades.
**3y (thin folds, n=211/65):** better 1 / worse 1 (2021 −13.0; 2022 +54.6) — MIXED on tiny folds, same
ambiguity (b) had. The weight derivation down-weights wipeout_safety under (d) (e.g. 0.027 vs legacy 0.084).

## Caveats for the adversarial reviewer to scrutinize
- **Is 24.6 vs 25.4 a "regress"?** 3 fewer bad outcomes caught of 394. Reviewer should rule whether this
  clears the literal "recall must NOT regress" bar or is flat-within-noise (the intended outcome). Which 3?
- **Does the thin-record SME freq leg re-introduce a milder artifact?** It's `freq<12 & SME`. SME bankers
  are mostly small shops, so the over-fire risk is lower than the MB false-veto — but a reputable SME-focused
  banker with a thin in-window record (e.g. a newer SME arm of a big house) could still be caught. Check.
- **Look-ahead:** the thin-SME leg uses FULL-WINDOW frequency (not PIT), so in the fold/backtest it peeks at
  future IPO counts. The legacy live def has the SAME limitation (full-window freq) and is the A/B baseline,
  so the comparison is fair — but the thin-leg's fold numbers are mildly optimistic vs a strict-PIT version.
- **3y degradation at the 2021 fold (−13).** On 211 rows. Does it override the consistent 1y no-degrade?
- **Params (MIN_PRIOR=5, BAD_RATE=0.40, CUTOFF=12) un-swept** — confirm results aren't knife-edge.

## Decision pending review
Code is implemented behind `scorecard.OBSCURE_BANKER_MODE` (values: legacy | quality | coverage_guard).
**LIVE is still `legacy`** — coverage_guard is flipped on ONLY if the independent review confirms recall does
not materially regress AND the OOS evidence holds. Else it stays display-only (the conservative default).
