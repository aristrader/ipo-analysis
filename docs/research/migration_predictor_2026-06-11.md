# MIGRATION+ — at-IPO predictor of eventual SME→Mainboard migration: verdict (2026-06-11)

HYPOTHESIS path. Does an at-IPO (look-ahead-safe) feature predict which SMEs eventually migrate to the
mainboard? Built `tools/research/migration_predictor.py`; 3-lens-informed design; independent adversarial
review (agent a0860f7) reproduced everything and confirmed every call below.

## Verdict — **NO new live signal.** Two valuable byproducts (a methodological save + an E3 correction).

### 1. The strong-looking predictor was CIRCULAR — discarded (the key save)
`market_cap_cr` showed rank-IC **0.564** vs eventual migration (tertile 22%→64%→83%) — but it is the
**CURRENT** market cap (scraped live from Screener: `scrapers/screener.py` `page_marketcap` → `03f_sector_mcap`
→ `08_build_universe`), NOT at-IPO. A migrated SME *necessarily* grew into a high current mcap (migration
requires crossing the ~₹100cr mainboard threshold). Empirically: market_cap_cr corr **0.79 with post-IPO
growth** but only 0.35 with at-IPO issue size; migrants carry a mcap/issue-size ratio of **16.9× vs trapped
3.3×**. So the IC was measuring "did it grow," and migration *is* "did it grow." Textbook reverse-causation —
**DISCARDED.** (There is no at-IPO total-mcap column in the substrate; only issue_size/issue_price are at-IPO.)

### 2. The genuine at-IPO predictors are real-but-weak, pre-2020-only, and redundant → NOT scorable
`pre_ipo_net_sales` (IC 0.20), `pre_ipo_pat` (0.195), `issue_size_cr` (0.156) — all placebo p=0.0, and
positive in the well-powered longterm vintages (2012-16 ~+0.20, 2017-19 ~+0.18): bigger/more-profitable SMEs
at IPO are ~50% more likely to migrate (PAT high-tertile 67.6% vs low 44.6%; sales 67.3% vs 47.8%). Intuitive
(size/profit → mainboard eligibility), look-ahead-safe. BUT:
- **Cross-regime FAILS:** the boom-eligible set is only **n=40**, and within it the signal collapses/sign-flips
  (net_sales IC −0.03, pat 0.10). Migration eligibility concentrates pre-2022, so boom can't be validated.
  Per the project's cross-regime gate, this cannot graduate to a scored signal.
- **Redundant:** the scorecard already consumes pre_ipo_pat / pre_ipo_net_sales / issue_size (wipeout flags +
  analog dims). "Bigger/profitable SMEs do better" is not new information.
- **The profitable/loss BINARY is null** (56.8% vs 59.2%) — only the *magnitude* of sales/profit carries the
  weak signal, not the profit/loss flag.
→ DISPLAY-ONLY ceiling at best, and even then it should be hedged "weak, pre-2020 only." No score path.

### 3. BYPRODUCT — corrects E3's headline (censoring): the MAJORITY of surviving SMEs migrate
Migration takes median **3.7y** (p75 5.1y, p90 7.9y); **0% migrate in the first 3y**. E3's "22.7% migrated"
was therefore CENSORED by recent listings. On the mature, fair-chance set (**SMEs that SURVIVE ≥5y**, n=560),
the migration rate is **55.5%** — migration is the *majority* outcome for SMEs that last, not a rare escape.
(70/560 eligible are already delisted, correctly retained as true-negatives — no survivorship prune.) This
reframes the SME "dead-money trap": it's less "few escape" and more "survive-long-enough and most graduate;
the trap is the early years + the deaths."

## Net
No new live-score component (the honest, expected outcome — consistent with evolve-only-if-robust). The
falsifier earned its keep by catching the circular market_cap predictor before it could mislead. The censoring
reframe is the durable takeaway. FUTURE: re-run as the 2020-21 SME cohort matures past 5y (≈2026-27) to get a
real boom-eligible set — only then is a cross-regime migration-predictor testable. Reproduce:
`PYTHONPATH=. python tools/research/migration_predictor.py`.
