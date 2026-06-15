# H-MVP — relative valuation via earlier-IPO peers (Theme H, owned-data MVP)  · 2026-06-10

Agent: hypothesis/research (auto/6hr-batch). Harness: `tools/research/hmvp_relative_valuation.py`.
Review CSV: `data/master/review/hmvp_relative_valuation_review.csv` (356 peer-matched rows, tagged by config).
Lineage / ember: `rules/index.md` → **n6 / pe_vs_sector** (DISPLAY-ONLY: rich issue-time P/E vs sector
median underperforms, MB −13pp / SME −48.9pp boom; blocked cross-regime on missing SME/longterm P/E).
This is Theme H's P0+P1 MVP (improvement_backlog.md §THEME H): peers = EARLIER IPOs in the same
industry/sector within a size band, valued with point-in-time data we already own. Did NOT build the
all-stocks panel (P4, gated).

---

## P0 — the precise hypotheses
- **(a) RE-RATING.** An IPO priced CHEAP on its issue-time P/E *relative to its earlier-IPO peers*
  (same industry/sector, similar issue size) earns higher forward alpha (it "catches up"); a
  rich-vs-peers IPO fades. Operationalised: `pe_pctl` = the fraction of prior peers cheaper than this
  IPO's P/E (0 = cheapest in its peer set, 1 = richest). **Falsifier (pre-declared):** cheap-tertile
  forward alpha ≤ rich-tertile (spread ≤ 0), or a label-shuffle placebo reproduces the spread.
- **(b) PEER-PROXIMITY DOSE.** The effect strengthens with a tighter / better-populated peer set
  (more prior comparables → a cleaner relative read). Falsifier: hi-peer-count cells show no larger
  spread than lo-peer-count.

## Peer-matcher design (LOOK-AHEAD CLEAN)
For each IPO `i` (sorted by `listing_date`): peers = IPOs that **listed STRICTLY BEFORE** `i`, SAME
segment (MB/SME never pooled), SAME bucket, with `issue_size` within a factor band, and a valid
issue-time P/E (≥ `MIN_PEERS=5` or the row ABSTAINS — no rank). P/E = `issue_price / eps_ttm`, falling
back to substrate `pe_ratio`; loss-makers (P/E≤0) excluded (no meaningful multiple). Size band uses
**`issue_size_cr`** (≈100 % covered, issue-time, look-ahead-safe) deliberately INSTEAD of
`market_cap_cr` (which the n14 work flagged as CURRENT mcap → reverse-causation). Forward windows are
`spine.maturity_gated` so an analog's outcome can't leak. Alpha = vs Nifty (issue/listing conventions).

To separate "the signal is weak" from "the peer set is too sparse," three configs were run:
| config | bucket | size band |
|---|---|---|
| A_fine_ind_band3 | `industry` (174 fine buckets) | ×3 (size ∈ [i/3, i·3]) |
| B_broad_band3 | `broad_sector` (12 buckets) | ×3 |
| C_broad_noband | `broad_sector` | none (loosest fair def ≈ n6's sector pool) |

---

## THE STRUCTURAL WALLS (decisive, pre-data)
1. **P/E coverage is ZERO in the 2006–19 longterm cohort** (no `eps_ttm`, no `pe_ratio`):
   boom-MB 223 / boom-SME 631 / longterm-MB **0** / longterm-SME **0**. The valuation re-rating signal
   is therefore **structurally boom-only** — the cross-regime gate CANNOT be cleared with owned data.
   This is the same wall n6/pe_vs_sector and E2 hit. Any verdict is bounded to display-only at best.
2. **Fine-industry peer matching is catastrophically sparse.** With `industry`+size band (config A),
   only **13 boom-MB and 0 boom-SME** rows get ≥5 prior same-industry peers — most IPOs are the first
   (or near-first) in their fine industry within the boom window. Peer matching only POPULATES at
   `broad_sector` granularity — i.e. it collapses back onto **exactly n6's bucket.**

---

## Test table (boom only; longterm impossible). N + CI per cell

### Config C (broad_sector, no size band — the populated, fair definition)
| cell | horizon | N | IC(pe_pctl, α) | cheap med α | rich med α | spread (cheap−rich) | cheap CI | rich CI | placebo p |
|---|---|---|---|---|---|---|---|---|---|
| boom/MB | 1y | 94 | **−0.345** | +14.7 % | −23.2 % | **+37.9 pp** | [+1,+36] | [−33,−11] | **0.000** |
| boom/MB | 3y | 0 | — | — | — | — | — | — | (no matured peer-matched rows) |
| boom/SME | 1y | 26 (thin) | −0.401 | +72.8 % | −34.9 % | +107.6 pp | — | — | (N<36, no placebo) |
| boom/SME | 3y | 5 | suppressed | | | | | | |

### Config B (broad_sector, ×3 size band)
| cell | horizon | N | IC | spread | placebo p |
|---|---|---|---|---|---|
| boom/MB | 1y | 70 | −0.387 | +33.9 pp | **0.000** |
| boom/SME | 1y | 14 (thin) | +0.135 | −42.4 pp (sign flips, N=14 noise) | — |

### Config A (fine industry) — SUPPRESSED everywhere (N≤13) — peer set too sparse to test.

**Direction:** in the one well-populated, placebo-clean cell (boom/MB, N=94/70), CHEAP-vs-peers
beats RICH-vs-peers by ~34–38 pp at 1y, IC −0.35..−0.39 — the **same sign and magnitude as n6's
MB lean (−13..−43 pp)**. SME is directionally consistent at the loosest config (−0.40 IC) but always
thin (N=26 max) and sign-unstable under the size band (N=14). 3y is untestable (the prior-peer pool
fills late in boom → no matured 3y windows).

## Placebo (shuffle the peer-relative rank)
Boom/MB, both populated configs: real spread +33.9 / +37.9 pp vs a null centred at **0.1–0.2 pp**
(SD ~10–12 pp), one-sided **p = 0.000**. The relative-rank ordering carries real information — it is
NOT an artifact of the sort. (SME never reached the 3×MIN_N=36 floor required to run the shuffle.)

## Dose (peer-proximity)
**No dose.** Hi-peer-count vs lo-peer-count MB cells show essentially equal spreads (config C: +31.8 vs
+32.5 pp; config B: +26.1 vs +14.9 pp — if anything noisier, not larger, with fewer peers). Hypothesis
(b) is **not supported**: more/closer comparables do not sharpen the read. The signal is the rich/cheap
SORT, not the peer density.

## Incremental over the sector-median version (n6)? — the load-bearing question
On the SAME maturity-gated rows where both are defined (boom/MB, N=94, 1y):
- IC(peer-percentile, α) = **−0.345** vs IC(sector-median-rel, α) = **−0.309** — peer barely edges it.
- IC of the peer-rank RESIDUAL after removing the sector-rank = **−0.166** (same sign).
The residual is non-zero, but (i) the peer pool IS the sector pool (fine-industry matching was empty,
so "peer" = broad_sector by necessity), (ii) the gain is small and (iii) it costs huge coverage
(133–170 matched of 221 candidate MB; SME mostly lost). **Honest read: peer-matched is NOT meaningfully
incremental over n6 — it is the SAME signal, marginally sharper, at a large coverage and complexity
cost.** The "peer adds" auto-label in the harness is mechanical (a finer/PIT cut of the same
rich-vs-cheap sort), not evidence of a distinct edge.

---

## VERDICT — **REDUNDANT-WITH-n6 / display-only (no new score role)**
- **Re-rating (a): CONFIRMED but boom-MB-only and = n6.** Cheap-vs-peers outperforms rich-vs-peers
  (+38 pp, placebo-clean, CIs separate) — a genuine, falsifier-surviving boom-MB effect. But it is the
  n6/pe_vs_sector signal with a point-in-time, prior-only peer pool that — because fine-industry
  matching is empty — reduces to the broad_sector pool. Not incremental enough to graduate.
- **Dose (b): REJECTED** (no peer-proximity gradient).
- **Cross-regime: IMPOSSIBLE** (zero longterm P/E) → cannot clear the evolve-only-if-robust gate. Even
  the cleanest cell stays display-only by construction, exactly like n6.
- **Score policy:** does NOT enter the weighted score. At most it would refine n6's display-only badge
  with a PIT peer-relative percentile; given the redundancy + boom-MB-only confinement, recommend
  folding the verdict into the n6 lineage rather than standing up a new component.

### Coverage caveats (be honest)
- **P/E missing for ~36–43 % of boom IPOs** and **100 % of longterm** → the test universe is a biased
  subset (profitable, P/E-disclosing names; loss-makers excluded entirely).
- **Peer-matched subset is small:** boom-MB 170/221 candidate at the loosest config, SME ≤26.
  Fine-industry matching (the owner's "nearest-mcap / same-industry" intent) is essentially infeasible
  on owned IPO-only data — too few prior same-industry IPOs.
- **3y horizon untestable** — the prior-peer pool only fills in mid/late boom, so no 3y windows mature.
- **No intrinsic-value leg** (P3 Graham/EPV/residual-income) — out of MVP scope; would need the same
  clean-financials base and still be boom-confined for the P/E-anchored comparison.

### What WOULD move this (for the backlog, not now)
P2 (graduate via self-computed EV/Sales for loss-makers, unblock SME P/E — improvement_backlog E2) and
P4 (point-in-time all-stocks peer panel) are the only paths to (i) cross-regime coverage and (ii) true
non-IPO peers. Both are deliberately deferred / network-heavy. The MVP's job was to decide whether the
owned-data peer signal is worth that data tax: **it is not — it reproduces n6 and dies on the same
cross-regime wall.** Recommend NOT advancing to P4 on valuation grounds.

## Proposed rules/index.md line (controller to add — I did not edit the file)
`| H-MVP: relative valuation vs earlier-IPO peers | REDUNDANT-WITH-n6 / display-only | boom-MB cheap-vs-peers beats rich +37.9pp 1y (N=94, IC −0.345, placebo p=0.000, CIs separate) — but reduces to n6's broad_sector pool (fine-industry matching empty: 13 MB/0 SME), NOT incremental (resid-IC −0.166), no peer-proximity dose, and STRUCTURALLY boom-only (zero longterm P/E). SME thin (N≤26), 3y untestable. Same wall as n6/E2. Don't advance to P4 on valuation. tools/research/hmvp_relative_valuation.py + hmvp_relative_valuation_2026-06.md |`
