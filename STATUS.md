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

_Canonical facts (verify before quoting — or just run `python verify.py`): **29 findings, 132 tests**
(77 layer3 + 25 pipeline + 24 scrapers + 6 map). Substrate as-of = `config.AS_OF_DATE` (2026-05-31), 2296 rows.
Navigation: `MAP.md` (generated) · structure source `project_map.py` · checkpoint `verify.py` (auto each turn)._

---

## ✅ DONE (full history in DONE.md)
All 3 layers built + reviewed; movement lens; full "Evaluate this IPO" report (outcome breakdown +
best/median/worst + standalone wipeout-risk gauge); 29 findings incl. N15 (the one validated interaction);
interaction layer; backtester; cross-regime validator; data-informed weights; Streamlit app (5 tabs);
adversarial-reviewed (latest round fixed the "unknown=safe" risk-gauge blocker). **77 tests, app verified,
data/master byte-identical to backup.**

## 🏃 IN PROGRESS
- Nothing running. The E→git→C→D queue is complete (all committed).

## ✅ TEST-1 (scraper/pipeline coverage) — DONE (data-building safety net) + pipeline/lib.py dedup
- **46 new tests** added, full suite now **123 passing** (was 77, all layer3). data/master untouched.
- **`pipeline/lib.py` dedup DONE (2026-06-02):** consolidated the copy-pasted `fnum` (×4: 08/03b/03d/03e),
  `num` type-guard (×2: 08/03b), and `last_pre_listing_fy` (×2: 08/03b) into `pipeline/lib.py` (+3 unit tests).
  AST-verified the bodies were byte-identical before moving. **Trap avoided:** `05_reconcile.py` also has a
  `num()` but it's a DIFFERENT function (`float()` coercion, not a type-guard) — left untouched (the cleanup
  note's "dedup num" wording would have silently broken it). Verified: py_compile + import-convention probe
  (matches step-07's proven `sys.path.insert`+sibling-import pattern) + data/master byte-identical. NOT re-run
  through the full pipeline on purpose — the substrate is frozen/post-remediation so a full-chain diff is noisy;
  behavior is preserved by construction (identical bodies) and the only risk (import resolution) is proven directly.
- Earlier slices (still true):
  - `tests/pipeline/test_returns_math.py` (11) — pure math in step 07: `pdate`/`pfloat`,
    `adj_factor_after` (split adjustment), `nearest_on_or_before` (benchmark lookup), `actions_for` (union/dedup).
  - `tests/pipeline/test_listing_remediation.py` (11) — every branch of `remediate_listing`
    (ok / inferred_split / unreliable_coverage / recovered_bhavcopy) + `_outcome_class` boundaries.
  - `tests/scrapers/test_corp_actions_parse.py` (9) — `classify`/`parse_split_factor`/`parse_bonus_factor`/
    `iso_date`/`parse_row` (the text→ratio_factor that feeds the split math above).
  - Numbered pipeline files loaded via importlib in conftest (can't `import` a `07_*` name); conftest sets
    `sys.dont_write_bytecode` to avoid stale-.pyc under rapid edit/rerun.
  - **Mutation-tested**: confirmed all three target functions, when broken, fail a test (tests bite, not vacuous).
- **Still deferred (next slice of TEST-1):** `fnum/num/last_pre_listing_fy` are copy-pasted across 5 pipeline
  files (08/03b/03d/03e/05) and live inside import-UNSAFE modules (top-level execution) — they should be
  pulled into `pipeline/lib.py` first, then tested; that dedup is the blocked refactor this unblocks.
  Also: `scrapers/http.py` shared-session refactor; more scraper parse coverage (sharescart/screener/ipowatch).

## ✅ DONE this run (E, git, wipeout-fold, C, D-safe) — see DONE.md
- **D (conservative) — DONE (the safe, verifiable part):** `_p()`→`spine.pct_num` dedup across 19 findings,
  VERIFIED report byte-identical (diff=0) + 77 tests. **Deferred** (need verification infra first — bundle with
  TEST-1): `pipeline/lib.py` dedup (touches the substrate builder; needs package setup + substrate-diff) and
  `scrapers/http.py` (untested code — can't verify safely without scraper tests). compute() split skipped (your call).
- **C — DRHP: productionized + gated, staged NOT folded (your "review" branch).** Prototype preserved into
  `tools/drhp/` (was ephemeral /tmp) with a new `pat==op` PAT-suspect guard. DLF's suspect PAT withheld.
  16 net_sales staged but only 2 INDEPENDENTLY cross-validated + PAT unreliable → **review-needed, not folded**
  (data/master untouched). Bulk (~384) + PAT-label hardening = deferred (recorded in Backlog). Docs:
  `docs/research/drhp_recovery.md`, `tools/drhp/README.md`.

## ⏳ YOUR DECISIONS — all resolved this session (kept for the record)
1. **✅ DONE — wipeout-safety folded into `data_informed`** (you approved). Weight 0.13; OOS re-validated:
   3y lift 55→**77pp**, 1y +1.9→+3.6pp, holds across all splits. The first signal to earn its way in.
   Presets unchanged. 77 tests, app verified.
2. **DRHP fold-in — ✅ DECIDED 2026-06-02: DO NOT FOLD (keep staged).** Evidence: all 16 staged net_sales fill
   NULL cells but every value is **≥61.5cr — none below the 25cr tiny-sales threshold**, the ONLY scorecard/flag/
   finding consumer of `pre_ipo_net_sales`. So folding changes ZERO flags/scores/findings (16 large old MB IPOs,
   16/2296 rows). Against that: only **2/16 independently cross-validated**, some have weak P&L-page detection
   (score 3-4), observed array parsing artifacts, and PAT is unreliable (1 confirmed-bad). Net: folding 14
   unvalidated values into the FROZEN substrate for **zero analytical gain** fails the rigor bar. PAT: never fold.
   **Re-open bar:** fold only if (a) a concrete downstream need for these old large-caps' sales appears, AND
   (b) each value is independently cross-validated, AND (c) the extractor's array-artifact + PAT-after-tax fixes
   land. Tool preserved in `tools/drhp/` for that future bulk pass. data/master untouched (verified).
3. **✅ git init done — LOCAL-ONLY** (your standing instruction: never connect to a remote). Baseline committed.

## 📋 BACKLOG / DEFERRED (real, not blocking — pick when ready)
- **DRHP full recovery** (16/425 done): fix the PAT/PBT extractor bug (require after-tax row label +
  PBT−tax reconciliation + flag operating_profit==pat), wire SEBI-URL-from-chittorgarh-anchors into the
  locator, then a semi-automated human-in-loop pass on the ~384 remaining. Tooling productionized in `tools/drhp/`.
  NOTE: net_sales has near-zero downstream impact for these old large-caps (all ≥25cr → no flag change; see the
  fold-in decision above) — only worth a bulk run if tied to a concrete new finding/need.
- **Microcap extension** — risk/movement screener MVP scoped (`docs/research/microcap_extension_thinking.md`).
- **Code refactors** (from `docs/research/CLEANUP_FINDINGS.md`, real maintainability debt, deferred — do
  with tests + after git): `compute()` split (07), test hermeticity (synthetic fixture) + adversarial trap tests.
  (DONE already: `_p()`→`spine.pct_num` dedup; scraper/pipeline test coverage [TEST-1]; **`pipeline/lib.py` dedup**.)
- **`scrapers/http.py` (broad shared HTTP) — REJECTED, do not retry.** Ground truth: the scrapers are deliberately
  heterogeneous (curl_cffi / cloudscraper / requests / urllib, one anti-bot approach per source); a unified HTTP
  layer would be a network-unverifiable rewrite, not a dedup. Also the name `http.py` would SHADOW stdlib `http`
  (script dir is on sys.path[0]) and break curl_cffi/requests/urllib. **Done instead:** the one genuinely-shared,
  byte-identical piece — NSE curl_cffi priming — was consolidated into **`scrapers/nse_session.py`**
  (`prime_nse_session(referer)`); corp_actions + nse_subscription keep a 1-line `prime_session()` shim. +3 tests.
- **`docs/research/` reorg** (structure audit #3): split active vs `archive/`; move staging CSVs out.
- **DEPS-2:** pin requirements versions. (Doc rename decisions.md→discussion.md = DONE.)
- Other NEEDS_YOUR_INPUT items now DONE: survivorship-lens (built), 5% thresholds (set), combined TP+SL (built).
