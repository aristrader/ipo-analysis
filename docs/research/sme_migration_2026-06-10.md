# E3 — SME→Mainboard migration as an outcome class (owned-data; no scraping) — 2026-06-10

Resolves backlog **E3**. The backlog assumed this needed a dated external source (Chittorgarh r123 /
NSE/BSE circulars). It does **not** — the migration FACT + an approximate DATE are derivable from
reference data already in the repo, so the "needs network/scraping" framing was wrong. No pull was made.

## Derivation (owned data)
Tool: `tools/research/sme_migration.py`. An SME-listed IPO (`listing_at` contains "SME") has migrated to
the mainboard iff its ISIN now appears as a mainboard security:
- **NSE:** ISIN on `data/reference/nse_equity_list.csv` (the current MAINBOARD equity list). That file's
  `DATE OF LISTING` is the mainboard-admission date — **verified strictly later than the IPO date for all
  216 NSE migrants**, so it IS the migration date.
- **BSE:** ISIN in a NON-SME BSE group in `bse_master.csv` (group ∉ {M, MT}). BSE master carries no date.

## Result
- **333 of 1468 SME IPOs (22.7%) migrated to mainboard** (215 with an NSE migration date; dates span
  2015→2026, concentrated 2019–2023).
- **Migrated vs trapped (DESCRIPTIVE) — the gap holds in BOTH cohorts:**

| panel | group | n | bad% (loser\|wipeout) | multibagger% | median cur-return | median alpha_3y |
|---|---|---|---|---|---|---|
| ALL SME | migrated | 333 | 23.7 | 59.2 | +169.8% | +0.012 |
| ALL SME | trapped | 1135 | 43.2 | 22.5 | −6.0% | −0.452 |
| boom | migrated | 45 | 13.3 | 57.8 | +161.8% | +1.799 |
| boom | trapped | 903 | 40.4 | 22.4 | −1.7% | −0.053 |
| longterm | migrated | 288 | 25.3 | 59.4 | +170.5% | −0.096 |
| longterm | trapped | 232 | 53.9 | 22.8 | −35.3% | −0.638 |

The 22.7% that escape are overwhelmingly multibaggers (59% vs 22%) and rarely dead money (24% vs 43%);
the trapped 77% languish (median −6%, 43% loser/wipeout). This QUANTIFIES the SME "dead-money trap":
the segment is bimodal — a minority escape to the mainboard and compound, the majority stagnate.

## DISCIPLINE — this is an OUTCOME CLASS, NOT a predictor feature (do not score on it)
- **Selection-confounded:** migration REQUIRES growing into mainboard eligibility (profitability /
  market-cap / track-record thresholds). So "migrated SMEs outperform" is largely tautological — migration
  is a MARKER that the company already escaped, not a cause of the return. The median +170% is "they
  migrated *because* they grew."
- **Look-ahead-unsafe:** migration happens years post-IPO and is UNKNOWN at IPO. Using it to score a new
  IPO would leak the future. → It is a descriptive truth about the SME segment, **not a score input**.
- **Survivorship:** migrated names are alive-on-mainboard by construction (can't be wipeouts); the trap
  comparison is honest about this (the point is the bimodality, not a fair matched contrast).

## Where it could go next (NOT done here)
- The genuinely PREDICTIVE question: is there an EARLY, at-IPO marker of EVENTUAL migration (e.g. IPO-time
  profitability, subscription, issue size)? That would be a look-ahead-safe signal and is a clean future
  hypothesis (run through the 3-layer/placebo protocol). Out of scope for E3 (which was the outcome class).
- Could be added as a substrate column (`migrated_to_mainboard` / `migration_date`) at the next
  pipeline-build (NOT a post-hoc substrate edit — same discipline as I1), so findings can consume it.
- A formal layer3 descriptive finding (SME bimodality) is an easy follow-up if wanted.

Reproduce: `PYTHONPATH=. python tools/research/sme_migration.py`
