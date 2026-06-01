# STATUS — single live source of "where are we / what's next"

> **Rule:** this is the ONE status file. Update it as work happens; **verify state from GROUND TRUTH
> (files / command output), never from memory.** "What happened" (history) → `DONE.md`. "What is this /
> conventions" → `CLAUDE.md`. "Findings + tested-signal registry" → `rules/index.md`. Raw analyses →
> `docs/research/`. (Merged from TODO.md + EXECUTION_STATUS.md + NEEDS_YOUR_INPUT.md on 2026-06-02; the
> originals were drifting — finding counts read 20/28/29/62 across them — which is why they're now one file.)
>
> **Ground-truth checks:** findings `ls layer3/findings/*.py|grep -v __init__|wc -l` · tests
> `PYTHONPATH=. pytest tests/layer3 -q` · report `ls report/layer3_partA.html` · app
> `curl -s localhost:8501/_stcore/health` · data-untouched `diff data/master/ipo_analysis.csv archive/pre_drhp_20260601/ipo_analysis.csv`.

_Canonical facts (verify before quoting): **29 findings, 77 tests.** Substrate as-of date = `config.AS_OF_DATE` (2026-05-31)._

---

## ✅ DONE (full history in DONE.md)
All 3 layers built + reviewed; movement lens; full "Evaluate this IPO" report (outcome breakdown +
best/median/worst + standalone wipeout-risk gauge); 29 findings incl. N15 (the one validated interaction);
interaction layer; backtester; cross-regime validator; data-informed weights; Streamlit app (5 tabs);
adversarial-reviewed (latest round fixed the "unknown=safe" risk-gauge blocker). **77 tests, app verified,
data/master byte-identical to backup.**

## 🏃 IN PROGRESS / just-landed
- **DRHP financials recovery: COMPLETE (staging only)** — 16 verified rows (Coal India, DLF, Mundra,
  Varun Beverages, …) in `docs/research/drhp_recovered.csv`, 25 in `drhp_review_queue.csv`. **CAVEAT
  (from cross-validation): the PAT field = profit-BEFORE-tax (PBT), systematically wrong** (DLF PAT
  2,549.5 should be 1,941.3). net_sales cross-validates clean; **PAT must be fixed + re-validated before
  any fold-in.** Nothing folded. Backup at `archive/pre_drhp_20260601/`.

## ⏳ YOUR DECISIONS — all resolved this session (kept for the record)
1. **✅ DONE — wipeout-safety folded into `data_informed`** (you approved). Weight 0.13; OOS re-validated:
   3y lift 55→**77pp**, 1y +1.9→+3.6pp, holds across all splits. The first signal to earn its way in.
   Presets unchanged. 77 tests, app verified.
2. **DRHP fold-in** (your rule: validate→merge, else stage+record): handled in sub-project C below — fold
   the verified net_sales ONLY if it cross-validates cleanly, else stage + record review-needed.
3. **✅ git init done — LOCAL-ONLY** (your standing instruction: never connect to a remote). Baseline committed.

## 📋 BACKLOG / DEFERRED (real, not blocking — pick when ready)
- **DRHP full recovery** (16/425 done): fix the PAT/PBT extractor bug (require after-tax row label +
  PBT−tax reconciliation + flag operating_profit==pat), wire SEBI-URL-from-chittorgarh-anchors into the
  locator, then a semi-automated human-in-loop pass on the ~384 remaining. Tooling cached in `/tmp/`.
- **Microcap extension** — risk/movement screener MVP scoped (`docs/research/microcap_extension_thinking.md`).
- **Code refactors** (from `docs/research/CLEANUP_FINDINGS.md`, real maintainability debt, deferred — do
  with tests + after git): `pipeline/lib.py` (dedup fnum/num/last_pre_listing_fy), `scrapers/http.py`
  (shared session/UA/429-backoff), `compute()` split (07), `_p()` → `spine.pct()` across 19 findings,
  test hermeticity (synthetic fixture) + adversarial trap tests, scraper/pipeline test coverage.
- **`docs/research/` reorg** (structure audit #3): split active vs `archive/`; move staging CSVs out.
- **DEPS-2:** pin requirements versions. **Doc:** rename `docs/decisions.md` → `discussion.md` (mis-titled).
- Other NEEDS_YOUR_INPUT items now DONE: survivorship-lens (built), 5% thresholds (set), combined TP+SL (built).
