# Market-Context Signals + Short-Horizon Study — Verdicts (2026-06-06)

Point-in-time features (pre-listing info only), tested vs 1y alpha across all four
regime cells (MB/SME × boom/longterm). Raw tables in the session study output.

## A. Context signal verdicts (per the locked evolve-only-if-robust policy)
| Signal | Verdict | Evidence |
|---|---|---|
| **ctx_ipo_heat_90d** (how many IPOs in the prior 90d) | **DISPLAY-ONLY now; FOLD-CANDIDATE** | The one robust find: NEGATIVE in all 4 cells (rank-IC −0.13…−0.26; top-vs-bottom tercile alpha −16 to −29pp). **Crowded IPO windows → worse 1-year alpha**, both eras, both boards. In-score only after an OOS fold test (pending). |
| ctx_nifty_mom_3m (market momentum at listing) | **REJECTED** | IC ≈ 0 in all 4 cells (−0.03…+0.03). The market's recent direction says nothing about the IPO's later alpha. |
| ctx_heat_pop_90d (how hot recent pops were) | **REJECTED (not robust)** | Sign flips by segment (MB boom +0.13, SME boom −0.17). |
| ctx_sector_heat_180d | **REJECTED (not robust)** | Sign flips by era (boom +, longterm −). |
| Gold / silver / crude / rupee | **EXCLUDED by design decision** | Weak general link; new source maintenance; revisit only sector-conditionally. |

## C1. The "hot IPOs pop then fade" hypothesis: NOT SUPPORTED — the opposite holds
Boom cohort, matured 1y, from-listing, by FIRST-MONTH peak (the new mfe_lst_1m):
- MB: cold(<+5%) ends year at −11.0% · warm −2.1% · hot(25-60%) **+13.9%** · blazing **+52.7%**
- SME: cold −15.1% · warm −19.9% · hot **+29.8%** · blazing **+81.9%**
- Median drift AFTER month 1 ≈ flat-to-positive in every bucket; P(1y below 1m) ≈ 50% (coin flip).
**Early strength PERSISTS; early weakness persists.** Consistent with the established truth that the
right tail carries returns and exit-timing rules don't beat holding. No flip-the-hot-ones edge.

## C2/C3. SHORT score (GMP+subscription demand percentiles): NO TRADABLE EDGE
- Train (≤2025): P(touch +25% in month 1) rises only 33%→39% low→high — a sliver — while the HIGH-short
  bucket's 1-YEAR median is NEGATIVE (−3.4%) vs low-short +7.1% (hot-demand names fade long-term).
- 2026 never-seen holdout: noisy/inverted (37% vs 32%, high-bucket n=2). → **REJECTED as a standalone
  short-entry signal.**
- Meanwhile the existing LONG score ordered even the SHORT-horizon outcomes monotonically on the same
  holdout (1m: −7.7%/+2.9%/+6.7%). **The quality score IS the better short-horizon predictor.**

## What this means for play-short / play-long / skip
A separate short-game model isn't supported by the data. The defensible categorization is:
- **PLAY (long-bias):** high LONG score, 0 red flags — these also led at 1m/3m on the holdout.
- **CAUTION:** crowded IPO window (high ctx_ipo_heat_90d) — robustly worse 1y alpha (display warning).
- **SKIP:** low LONG score or wipeout red-flags — these lost money at every horizon measured.
Re-test the SHORT idea when the 2026 cohort matures (more 1m/3m samples + first 1y reads).
