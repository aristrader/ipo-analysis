# DONE — IPO Analysis Project

Completed items moved here to keep TODO.md lean. Most-recent first.

---

## DRHP fold-in decision — DO NOT FOLD (evidence-based)  (2026-06-02)
- Resolved the open "fold the 16 staged DRHP net_sales?" question via impact analysis on ground truth.
- **Finding:** all 16 staged net_sales fill NULL cells, but every value is **≥61.5cr** — and the ONLY downstream
  consumer of `pre_ipo_net_sales` (the wipeout `tiny-sales` flag) fires below **25cr**. So folding changes zero
  flags / scores / findings (16 large old MB IPOs, 16/2296 rows). Against that: only 2/16 independently
  cross-validated, weak P&L-page detection on some (score 3-4), observed parsing artifacts (stray array values,
  doubled year-headers), PAT unreliable (1 confirmed-bad).
- **Decision: do not fold** — folding 14 unvalidated values into the frozen substrate for zero analytical gain
  fails the rigor bar. Recorded in STATUS.md + docs/research/drhp_recovery.md with a concrete re-open bar
  (concrete need + per-value independent cross-validation + extractor array/PAT fixes). data/master untouched;
  `tools/drhp/` preserved. Docs-only change.

## scrapers/nse_session.py — shared NSE priming (broad http.py rejected)  (2026-06-02)
- Assessed the backlog's `scrapers/http.py` (shared session/UA/429): **rejected as scoped.** Ground truth — the
  scrapers are deliberately heterogeneous (curl_cffi / cloudscraper / requests / urllib, one anti-bot approach per
  source); unifying them = a network-unverifiable rewrite, not a dedup. Also caught a footgun: naming it `http.py`
  would SHADOW stdlib `http` (script dir on sys.path[0]) and break curl_cffi/requests/urllib.
- **Done instead:** consolidated the one genuinely-shared, byte-identical piece — NSE curl_cffi session priming —
  into `scrapers/nse_session.py` (`prime_nse_session(referer)`). corp_actions + nse_subscription keep a 1-line
  `prime_session()` shim binding their own `_REFERER` (call sites untouched → behavior-identical). Self-bootstrapping
  `from nse_session import` (lib.py convention) so importlib-loaded tests resolve it. +3 wiring tests (129→132).
  Registered in project_map.py (the workflow rule in action). Rejection recorded in STATUS so it's not re-litigated.

## Navigation + anti-drift system (single-source map, auto checkpoint)  (2026-06-02)
- **Problem:** structure lived as scattered prose (CLAUDE.md + run_all + docs) and drifted — e.g. `03f_sector_mcap.py`
  exists but was never wired into run_all; test/finding counts went stale; I kept re-deriving "what runs where" at
  runtime. Goal (user): make navigation, context-fetching, safe code-updates, and anti-hallucination *stay* solved.
- **Researched the pattern** (AGENTS.md / llms.txt / "agent meta-repo map"): single machine-readable source +
  generated human views + self-healing checkpoint; caution that bloated/auto-gen context can *hurt* — so keep it lean.
- **Built:**
  - **`project_map.py`** — ONE source of truth: pipeline DAG (with roles), data products, layer3 modules, where
    rules live, an UNWIRED list (flags 03f-class gaps), INVARIANTS, and a **CONTEXT INDEX** ("working on X → these
    files"). `render_map()` generates MAP.md.
  - **`MAP.md`** — generated nav/tree/flow/context (never hand-edited).
  - **`run_all.py`** now derives `STEPS` from `project_map.dag_steps()` → the DAG has ONE source, can't drift.
    Verified `--list` shows the identical 18 steps.
  - **`verify.py`** — checkpoint: every mapped path exists, DAG consistent, invariants (29 findings / 2296 csv
    records [NOT wc -l] / AS_OF_DATE / data-vs-backup) match; regenerates MAP.md. `--quiet` (~0.1s) for the hook.
  - **`UserPromptSubmit` hook** in `.claude/settings.local.json` (PROJECT-LOCAL only; uses `.venv/bin/python`)
    runs `verify.py --quiet` before each of my turns; drift is injected into context. Never blocks. Chose
    UserPromptSubmit over Stop (Stop can loop). Confirmed schema via claude-code-guide.
  - **`docs/WORKFLOWS.md`** — "what to do when" rules + 3 standing principles (verify-before-relying; update the
    map on change; suggest improvements). Pointer block added to CLAUDE.md.
  - **6 tests** (`tests/test_project_map.py`): mapped paths exist, DAG single-sourced into run_all, no drift,
    invariants match reality, MAP has the four views. Full suite **123→129**.

## pipeline/lib.py dedup — copy-pasted helpers consolidated  (2026-06-02)
- Consolidated three helpers that were copy-pasted across numbered pipeline files into **`pipeline/lib.py`**
  (+3 unit tests, `tests/pipeline/test_lib.py`): `fnum` (was in 08/03b/03d/03e), `num` type-guard (08/03b),
  `last_pre_listing_fy` (08/03b). Each numbered sibling now does
  `sys.path.insert(0, dirname(__file__)); from lib import ...` (the convention step 07 already uses for
  `listing_remediation`). Full suite 120→**123**.
- **Verified safe:** AST-compared every copy's body before moving (all byte-identical); py_compile on all touched
  files; an import-convention probe that replicates run_all's subprocess sys.path. data/master byte-identical.
- **Trap avoided (the kind the user warned about):** `05_reconcile.py` defines a function ALSO named `num`, but it's
  a *different* function — `float(x)` coercion, not the `isinstance` type-guard. The CLEANUP_FINDINGS "dedup num"
  wording would have merged them and silently changed 05's behavior. Left 05 untouched.
- Did NOT re-run the full pipeline: the substrate is frozen/post-remediation, so a full-chain diff is noisy;
  behavior is preserved by construction and the only real risk (import resolution) was proven directly.

## TEST-1 — data-building safety net (scraper/pipeline test coverage)  (2026-06-02)
- **Round 2 (scraper normalizers, +12):** `tests/scrapers/test_scraper_normalizers.py` pins the scalar
  text→value helpers that silently corrupt data if wrong: `screener._num`/`_norm_tokens`/`name_match`/
  `page_marketcap`, `ipowatch._num` (strips the `2.5x` suffix)/`_to_iso`, `sharescart.parse_num`/`clean`/
  `_parse_year`, `chittorgarh._iso_to_date`/`_num`/`_cr_from_text`. Behaviors captured against live output first.
- The 77 existing tests covered only the analysis layer (`tests/layer3/`); the entire data-building half
  (`scrapers/`, `pipeline/`) had **zero** tests. Added **31 unit tests** → full suite **108 passing**, with
  `data/master` byte-identical to backup (test-only change, no production code touched).
  - `tests/pipeline/test_returns_math.py` (11): `pdate`/`pfloat`, `adj_factor_after` (split adjustment factor),
    `nearest_on_or_before` (benchmark lookup), `actions_for` (ISIN∪symbol dedup) — the core of step 07's returns.
  - `tests/pipeline/test_listing_remediation.py` (11): all four `remediate_listing` branches
    (ok / inferred_split / unreliable_coverage / recovered_bhavcopy) incl. the post-issue-reliable null logic,
    plus `_outcome_class` thresholds at the boundaries.
  - `tests/scrapers/test_corp_actions_parse.py` (9): `classify`, `parse_split_factor`, `parse_bonus_factor`,
    `iso_date`, `parse_row` — the NSE-text→ratio_factor chain that feeds the split math above.
- **How:** numbered pipeline files (`07_*`) can't be `import`ed (digit-leading module name) → loaded by file path
  via importlib in per-suite `conftest.py` (modules self-bootstrap their own sys.path). Conftests set
  `sys.dont_write_bytecode=True` after hitting a stale-`.pyc` footgun (sub-second edit/rerun served mutated
  bytecode whose source-mtime collided with the reverted file).
- **Rigor:** mutation-tested the suite — broke `parse_bonus_factor` (a+b)/b→a/b, `adj_factor_after` `>`→`>=`,
  and the wipeout threshold `-0.90`→`-0.99`; each mutation failed a test, confirming the tests bite.
- Unblocks the deferred `pipeline/lib.py` dedup (fnum/num/last_pre_listing_fy, copy-pasted across 5 files) and
  `scrapers/http.py` — both now have, or can get, a regression net before refactoring.

---

## Layer 3 — Streamlit app (interactive UI)  (2026-06-01)
- `app.py` — one-file Streamlit front-end over the engine: 4 tabs — **Findings report** (embeds the 20-finding
  HTML), **Score a new IPO** (predictor form → scorecard + analogs + distribution + confidence), **Backtester**
  (strategies + holding-sweep + portfolio + flip-EV + combined-score), **Validation & rules**. Engine untouched
  (UI-agnostic). Verified end-to-end with Playwright (all tabs render, zero exceptions) + screenshots.
  Run: `pip install streamlit; PYTHONPATH=. streamlit run app.py`. Open for user layout/UX refinement.

## Layer 3 — final data hunts + adversarial verification sweep  (2026-06-01)
- **Data hunts (multi-source verified):** 37/38 remaining SME listing pops recovered (35 from our own price files,
  which start on the listing date) → `recovered_bhavcopy`=153, **`unreliable_coverage`=1** (UNITEDPOLY only).
  24 renamed-company sectors recovered (boom-MB sector → **99%**). 61 longterm financials folded; the rest are
  DRHP-PDF-only (free structured path exhausted → deferred). 3 market-makers applied.
- **Verification sweep (2 skeptic agents) — caught REAL issues, all fixed:**
  - Findings: N3/N5/N6/N8 printed maturity-gated alpha on sub-floor N the guard missed (e.g. N6 +313% on N=2) →
    per-cell guard; N11 pooled MB+SME → split; guard erased band labels → fixed.
  - Predictor/backtest/validation: **a LOOK-AHEAD** in the point-in-time scoring (read analogs' future-matured
    outcomes) → gated by horizon-completion. This **corrected the combined-score headline from the inflated +38pp
    to an honest +11pp pooled / boom +76pp / longterm +5pp, labeled IN-SAMPLE / indicative (NOT OOS-validated)**.
    Removed the overstated "cross-regime validated" string; disclosed quality/liquidity get 0 weight under
    data-informed; refreshed stale weights; fixed validator mislabeling insufficient-N as FRAGILE.
- **Net: 62 tests pass, 20 findings, everything adversarially reviewed + honestly labeled.** Reviews in
  `docs/research/review_new_*.md`; full play-by-play in `docs/research/autonomous_session_log.md`.

## Layer 2 — price history + returns + analysis substrate  (2026-05-31)
- Daily prices for the full universe via official NSE/BSE bhavcopy (`scrapers/bhavcopy_ohlc.py`) — 2284/2296 stocks;
  old BSE-SME (339) filled from screener weekly (`scrapers/screener_prices.py` + `_merge.py`), split/bonus adjusted.
- Sources built: corp_actions (NSE, symbol-matched — a split changes the ISIN), Nifty50 index, delisting flags.
- `pipeline/07_returns_summary.py` → returns/alpha/drawdowns/liquidity/survival per IPO (A1 delisting rule).
- `pipeline/08_build_universe.py` → unified feature table (boom+longterm, +screener financials/sector/mcap, GMP, instrument_type).
- `pipeline/09_assemble.py` → **`data/master/ipo_analysis.csv`** (substrate) + data_quality score + cross-source checks.
- Reviewed by 2 adversarial agents; remediated: corp-action symbol-match (116→383 stocks; IRCTC +59%→+697%),
  issue_price adjustment, listing-coverage defect (`listing_metrics_status`), duplicate-column fix, instrument_type fix.
- Final: 2296 rows; multibagger 31% / wipeout 6.7%; CLAUDE.md + docs/layer2.md + rules/ registry established.

## Layer 3 — analysis engine (Part A report + Part B predictor + Part C backtester)  (2026-05-31)
- **Integration pass first** (refreshed substrate): applied 9 verified corrections + 5 missing splits + 79 recovered
  listing days + Tantia fix; recomputed alpha with Nifty-pre-2007 + added Smallcap-250 alpha; re-pulled boom
  sector/mcap (3%→94% MB). All backed up in `archive/pre_integration_20260531/`.
- **Part A** — `layer3/` engine: `spine.py` (maturity-gating, distributions+Wilson CI, competing-risks band,
  min-N guards, SME/MB split), 8 Tier-1 findings (`t1`base-rates…`t9`profitable), `report.py` (unbypassable
  N-guard) → `report/layer3_partA.html`. **Part B** — `layer3/predictor/` analog engine (hard-gate→Gower→widening
  ladder) + 5-component scorecard + confidence/honesty layer; CLI `predict_ipo.py`. **Part C** — `layer3/backtest/`
  strategies vs do-nothing baseline, point-in-time, net of costs; `run_backtest.py`.
- **Reviewed by 3 subagents** (code + statistical + B/C); all Critical/Important fixed (T5 OFS unit bug,
  per-cell N-guard, T9 segmentation, boom long-horizon, T2 re-framing, alpha-is-from-listing labeling). **39 tests pass.**
- Headline results (after cross-regime validation, `run_validation.py`): **VALIDATED both regimes** — MB IPOs
  underperform the index; big listing-pop → worse secondary-buyer forward return. **NOT regime-robust (sign flips):**
  "high-OFS-better" and "profitable premium" (both small-N — were single-regime artifacts). Naive buy-at-listing
  LOSES cross-regime; the profitable+OFS filter only REDUCES the loss, doesn't beat the index. Robust takeaway:
  IPOs are hard to beat the market with, especially as a secondary buyer. See `rules/index.md`.
- **Polish + ideation-build (2026-06-01):** cross-regime validator + data-informed scorecard weights + calibration.
  **20 findings** total (N2–N12: subscription, demand-skew, issue-size, anchor, valuation, fundamentals, accrual,
  zombie/dead-money, migration, Smallcap-divergence, banker-league + separate non-equity view). Predictor hardened:
  validated signals (accrual/debt flags + liquidity haircut) wired into the scorecard; calibration readout (quintile
  + validated lift); analog histogram + bimodal flag. Backtester: holding-period sweep, portfolio basket, **flip
  allotment-EV** (naive +21% → realistic +2%), Smallcap-250 benchmark, combined-score loop-closer (claimed +36pp
  here — later CORRECTED to +11pp in-sample by the 2026-06-01 verification round; see top entry). Validation:
  within-vintage check + fragility score + bootstrap CIs +
  confirmatory/exploratory tagging (within-vintage DOWNGRADED pop-fade; only lasting-wealth fully VALIDATED).
  Era-aware data_quality (low 210→12); integrated 37 more listing recoveries (recovered_bhavcopy=116) + 24
  renamed-company sectors (boom-MB sector 99%). Residuals reviewed/closed. **62 tests pass.** Ideas in `docs/research/ideas_*.md`.

## Layer 1 enrichment — subscription / GMP / financials / sector / mcap  (2026-05-31)
- **Subscription:** NSE Public Issues API (mainboard, `pipeline/03c`) + ipowatch (SME, `03d`). Mainboard ~92%.
- **GMP:** ipowatch (`03d`, 642) + investorgain webnodejs API (`03e`, +320) → 1017/1269 (was ~55).
- **Financials + sector + market-cap:** screener resolver — name-match fix recovered the SME gap
  (1065/1268 resolved; sector 1014, mcap 1039) — folded into `universe.csv`.
- **instrument_type** (equity/invit/reit/fpo) flagged; cross-source checks + per-row data_quality in assemble.
- Source-research sweep (parallel agents) validated every source; recorded in `docs/sources.md` + dead-ends listed.

## Layer 1 rebuild + validation + source research  (2026-05-30/31)

- ISIN-keyed rebuild: **1269 IPOs** (MB 382 + SME 887), 2020–2025, two files
  (`data/master/mainboard.csv`, `sme.csv`). Chittorgarh spine; all sources joined by ISIN only.
  Pipeline `01_build_base`→`05_reconcile`, validated by `pipeline/checks/`.
- Exchange-aware tickers (NSE `SYMBOL.NS` / BSE `numeric.BO`); fixed BSE-as-.NS bug (374 SME + 3 MB);
  0 rows without a ticker.
- Names canonicalised to latest official via `data/reference/name_overrides.csv` (15 verified renames);
  IPO-time name kept in `name_at_ipo`. 0 unresolved ticker conflicts / name reviews.
- Reconcile vs old 929-set: 15 HARD all explained, 262 BSE format-fixes, 62 SOFT numeric.
- Ticker validation (`pipeline/06_validate_tickers.py`): 1230/1269 confirmed via Yahoo (859) or
  bhavcopy (371); found Yahoo lacks SME → Layer 2 will use bhavcopy.
- Repo reorganised (scrapers/ per source, numbered pipeline/, data/{raw,reference,master}, archive/).
- **Source research for G1/G2 gaps (2026-05-31):** validated free sources via parallel test agents —
  NSE Public Issues API (MB subscription), ipowatch.in (GMP + SME subscription), screener.in (financials),
  investorgain.com (GMP, ISIN-keyed). All recorded in `docs/sources.md`. Integration pending (TODO G1/G2).

---

## Architecture & Design

- Architecture decision: 3-layer separation (raw events / price history / derived patterns)
- Tooling split: scrape with code (free), AI only on structured layer 3 data
- Language: Python (requests, BeautifulSoup, pandas)
- Storage: flat wide CSV per segment (mainboard_events.csv, sme_events.csv)
- Primary source confirmed: Sharescart (2023–2025)
- Schema finalised and revised (docs/design.md)
- Project structure created (.venv, data/raw, data/derived, scrapers/, analysis/)

## Documentation

- docs/patterns.md created — all pattern hypotheses live there
- README.md updated — quickstart guide (venv setup, commands, file map)
- docs/discussion.md — full decision log, source discovery, rejected options
- TODO.md / DONE.md split established

## Source & API Discovery

- Confirmed Sharescart list page is JS-rendered (requests returns empty shell)
- Found the list data API: POST to `/web-services/ipo-stocks-intermediary.php`
  with `action=getipodataAccord`, `status=Listed`, `year[]`, `limit=50`, `page_no`
- Confirmed detail pages ARE server-side rendered — direct GET + BeautifulSoup works
- Key finding: `type[]` filter is ignored server-side — always returns all types.
  Scraper must query by year only and split MB vs SME client-side using the `type` column.

## Steps 5 & 6 — Full scrape + cleaning pass

- Full run: 939 raw rows (260 MB + 679 SME) in 6.9 min, 0 errors, 2 workers at 0.5s delay
- After dedup: 929 unique IPOs (259 MB + 670 SME)
- Cleaned files in `data/derived/mainboard_clean.csv` + `sme_clean.csv`
- **Critical finding — post-IPO financials:** Sharescart updates historical IPOs with new annual reports. 62% MB and 68% SME now show post-listing financial years. Added `has_post_ipo_financials` flag and `latest_pre_ipo_yr_col` to guide correct usage in analysis.
- **Zero subscription:** 8% MB, 16% SME have sub_total_x=0 — Sharescart never captured subscription data for these older IPOs. Flagged as `zero_subscription=True`.
- **Rate limit discovery:** Tested 0.1s–1.5s delays, no blocking at any speed. Settled on 0.5s (safe buffer). Actual RTT ~0.15s/request.

## Steps 2 & 3 — Detail page scraping (SME: Q-Line Biotech + Mainboard: Dev Accelerator)

- Page structure is **identical** between SME and Mainboard — same 9 tables, same sections
- Financial tables sometimes have 4 years (Mar 2022–2025 + TTM). Strategy: always take the 3 most recent non-TTM year columns → yr1/yr2/yr3
- **Fresh Issue / OFS**: confirmed absent from both page types — removed from schema
- **S-HNI / B-HNI subscription x-times**: not in subscription table — only NII combined shown — removed sub_shni_x / sub_bhni_x from schema. (S-HNI / B-HNI only appear in the lot-size table as min investment amounts, not as subscription multiples.)
- **Subscription ₹Cr**: the "Bid" column is shares applied, not ₹Cr directly — marking sub_*_cr as null (derivable but not scraped directly)
- **Industry**: not available anywhere — API response doesn't include it per row, detail page doesn't show it. Stays null.
- **GMP**: can be "--" / empty for some listed IPOs — handled as null
- **Lead manager fix**: names are in sibling `<p>` tags inside `.info-box` div; skip first `<p class="h5">` which is a company header artifact
- **Registrar**: same structure — name is first `<p>`, followed by address and email
- Fields coming from list phase (not detail page): `type`, `sharescart_url`, `open_date`, `close_date`, `issue_price`, `min_investment_rs`, `listing_open`, `listing_gain_pct`, `exchange`
- Derived/computed at scrape time: `age_at_ipo_years`, `price_band_width_pct`, `book_built`, `listing_gain_pct`

## Step 1 — List API fully understood

- API returns JSON: `{ "table": "<HTML rows>", "pagination": "<HTML>" }`
- Each row has 12 cells: company name+URL, status, open date, close date, issue price,
  min_investment_rs, listing_open, listing_gain_pct, current_price, current_return_pct, type, exchange
- Pagination: `data-pageno` attribute in pagination HTML gives max page index
- Total dataset (Listed, 2023–2025): **939 IPOs — 260 Mainboard, 679 SME**
  - 2023: 232 total (60 MB, 172 SME) — 5 pages
  - 2024: 335 total (91 MB, 244 SME) — 7 pages
  - 2025: 372 total (109 MB, 263 SME) — 8 pages

## 2026-06-01 — Movement lens (built + V3-reviewed + remediated)
Reframed the tool around the MOVE + the LIKELIHOOD, split by entry (allottee/secondary). Added MFE/MAE
(within-horizon peak/trough, both entries) in step 07; spine reach_curve/exit_strategy/stop_loss_strategy;
finding M1 (exit-discipline & stop-losses); mv-multibagger-ever (P ever 2x vs ended 2x); T3 reach-by-pop-bucket;
T8 forward-recovery; exit_discipline_backtest; tradeable_upside scorecard component (weight-0/display). App:
dual-entry exit display + Explorer entry toggle + stop-loss + exit backtest. Adversarially reviewed (2 agents):
fixed a backtest sample mismatch, a truncated-window MFE bug, the multibagger denominator, unreliable_coverage
exclusion, and added an invariant clamp (peak>=endpoint>=trough, 0 violations) for split-remediated rows + the
secondary-buyer break-even tautology caveat. 70 tests, 21 findings. KEY TRUTH: no take-profit/stop-loss rule
beats buy-and-hold cross-regime. Deferred judgment calls → NEEDS_YOUR_INPUT.md.

## 2026-06-01 (cont.) — Headline-truth + wipeout hunts (3 subagent hunts, all verified)
Ran 3 read-only hunt subagents → I integrated the winners (controlling quality). New findings: F·partial-exit
paradox + F·basket-barbell (both HEADLINE, cross-regime), N13 fallen-angel (validated-NULL: no feature predicts
recovery), N9 sharpened (dead-money >> wipeout for SME + the zombie-gave-an-exit panel), F·lifecycle (timing:
median IPO peaks ~108d into yr1), N14 Anatomy-of-a-Wipeout. Time-to-peak prices re-pass built (greenlit):
days_to_mfe/mae/breakeven cols. Report = 26 findings, 70 tests.

**Caught two real correctness traps during integration (I verified the subagent code since I didn't write it):**
1. N14 micro-cap "headline" was REVERSE-CAUSATION — `market_cap_class` is CURRENT mcap, so a wipeout reads
   'micro' because it crashed (median wipeout mcap ₹9cr vs ₹770–1200cr survivors). Removed from the red-flag
   score + flagged in the table as a cautionary example. Validated pre-listing flags = tiny-sales + loss-making.
2. (Earlier V3) exit-backtest sample mismatch, truncated-window MFE, multibagger denominator, invariant clamp.

Docs: `docs/research/headlines_entry_exit.md`, `headlines_selection_survival.md`, `wipeout_anatomy.md` (carries
a correction banner). tradeable_upside rank-IC checked (predicts cross-regime; OOS with/without test pending).
Cleanup: archived dead scratch (`archive/research_scratch/`), refreshed TODO/DONE/NEEDS_YOUR_INPUT/rules.

## 2026-06-01 (autonomous window 2) — Eval report, wipeout deepening, score policy
- **B1 "Evaluate this IPO" report** (centerpiece, user's idea): `spine.outcome_breakdown` → Score tab shows, for the
  analog cohort, the full outcome breakdown (doubled+/up/flat/down) + best-case P90 / base-rate median / worst-case
  P10 + terminal dead-money & wipeout band. Shows ALL outcomes incl. failures (honest, not survivorship bias).
- **A2 wipeout red-flag badge**: `scorecard.wipeout_flags` checks a query against the VALIDATED pre-listing flags
  (tiny pre-IPO sales <25cr / loss-making / obscure lead manager) → 🚩 badge on the Score tab + CLI. Form + CLI gained
  revenue and lead-manager inputs.
- **Wipeout-anatomy deepened** (3rd hunt subagent, verified): `obscure_lead_mgr` GRADUATED into the N14 red-flag score
  (cross-regime, independently confirmed monotonic). REJECTED with the WRONG sign: low promoter holding (high retention
  = thin float = zombie), high GMP (protective). Promoter-data recovery assessed → not worth it (wrong sign anyway).
- **f_flip_trap** (boom: pop↔allotment inverse → flat capture-per-application) + **f_average_down** (the dip rarely
  recovers; 2nd tranche is a median loser) findings built + registered. 28 findings total.
- **A1 settled by data**: tradeable_upside HURTS the 3y OOS lift (55.1→47.4pp) though it helps 1y → fails the
  robustness bar → stays DISPLAY-ONLY. **Score policy LOCKED: "evolve-only-if-robust"** + a tested-signal registry
  (in-score / display-only / rejected) in `rules/index.md`.
- **Stop-loss cross-regime nuance**: "no stop beats hold" holds where IPOs have a right tail (boom + SME) but REVERSES
  in net-losing MB/longterm — same mechanism as the partial-exit paradox. Recorded honestly (not over-claimed).
- 73 tests; report 28 findings; app re-verified (Playwright). Archived dead scratch; docs refreshed.

## 2026-06-01 (autonomous window 3) — eval-report risk gauge, interaction layer, OOS promotion, verification
- **n15 clean-compounder** (low-debt × high-ROE — the ONE validated cross-regime interaction; super-additive, locked by a test). The risk-side interaction hunt found NONE (single flags are the whole story) — logged in the registry.
- **Standalone wipeout-risk gauge** (`scorecard.risk_assessment`): per-IPO 0–100 risk read (50=segment-typical) + per-flag with/without base rates, separate from the return score. App eval-report + CLI.
- **5%-step reach ladders** to +100% + multibagger tail. **Combined TP+SL** (timing-approximated; confirms no-exit-beats-hold except in net-losing cohorts). **Exclude-wipeouts lens** (labeled ⚠ biased) + **Relationships (exploratory)** section in the Explorer.
- **OOS wipeout-safety experiment**: folding it into the score IMPROVES the OOS lift in 14/18 cells — strong at 3y (all cutoffs +6 to +22pp), neutral MB-3y, mixed only at 1y. PASSES "evolve-only-if-robust". Banked as the #1 decision (recommend folding into data_informed); NOT silently applied (changes the headline number). Registry + NEEDS_YOUR_INPUT updated.
- **Adversarial verification agent** reviewed all new code → found 1 blocker + 2 honesty items, all FIXED: (1) "unknown=safe" — a no-input query was scored LOW → now suppressed (insufficient_inputs); (2) outcome_breakdown wipeout-band denominator now matches the gated base; (3) n15 single-alone N disclosed. Core confirmed sound (invariant 0 violations, partition sums 100%, n15 genuinely super-additive, reverse-causation fences intact). 77 tests.
- **DRHP financials**: cheap no-network path exhausted (screener lacks pre-2012 data → only 3 recoverable); real recovery needs the deferred DRHP-PDF pipeline (the agent stalled on it). Nothing folded; `data/master/` backed up at `archive/pre_drhp_20260601/`. See `drhp_recovery.md`.

## 2026-06-02 — Structure cleanup + workflow consolidation + acting on the audits
- **File-sprawl fixed → 4-file model:** merged TODO + EXECUTION_STATUS + NEEDS_YOUR_INPUT into ONE live `STATUS.md`
  (originals archived to `archive/superseded_status_20260602/`, reversible). Now: CLAUDE.md (brain) · STATUS.md
  (live state) · DONE.md (history) · rules/index.md (findings+registry). Killed the count-drift (files read 20/28/29/62).
- **Acted on `CLEANUP_FINDINGS.md` (code audit from another chat) — the correct/safe/high-value items:**
  - L3-1 LIVE date bug: `t2_survival` hardcoded `TODAY=2026-05-31`. Fixed via a single canonical `config.AS_OF_DATE`
    (used by t2_survival AND step-07 — note: the audit's literal `date.today()` fix would have DESYNCED the finding
    from the frozen substrate; applied the correct single-source fix instead).
  - L3-2: centralized the duplicated −0.50 dead-money cutoff → `config.DEAD_MONEY_RETURN` (n9, n14).
  - DEPS-1/INFRA-2: `requirements.txt` += streamlit/pytest/numpy/playwright/pdfplumber/curl_cffi; added `.gitignore`.
  - DOC-1..5: reconciled stale counts (CLAUDE.md 28/73 & 62 → 29/77; README 62 → 77); repointed CLAUDE refs to STATUS.md; added `03f` to the pipeline map.
  - Relocated CLEANUP_FINDINGS.md → docs/research/.
  - DEFERRED (real but large/risky — in STATUS backlog): the big de-dup refactors (pipeline/lib.py, scrapers/http.py,
    compute() split, _p()→spine.pct()), test hermeticity, docs/research reorg, git init, version-pinning.
- **Structure audit** (`docs/research/structure_audit.md`): foundation sound — all early decisions (ISIN-key, numbered
  pipeline, layer3 separation, survivorship-honesty, no-ML) STILL VALID, don't touch. Sprawl was only in tracking/docs.
- **DRHP recovery COMPLETE** (staging only): 16 verified rows; net_sales cross-validates clean; **PAT = PBT bug
  (systematic) → quarantined**; 25 in review queue. Nothing folded. Cross-validation + extra-source agents done
  (chittorgarh-React-render lead tested & closed; DRHP PDFs confirmed the only viable bulk source).
- Verified after all changes: 77 tests, 29 findings, app healthy, data/master byte-identical to backup.

## 2026-06-02 (autonomous 6h run) — E → git → wipeout-fold → C → D
- **E docs cleanup:** docs/research split active/archive (29 archived), README pointer, decisions.md→discussion.md.
- **git init — LOCAL-ONLY** (user standing instruction: never connect to a remote). Baseline + per-milestone commits.
- **Wipeout-safety folded into data_informed score (validated):** weight 0.13; OOS re-confirmed 3y 55→77pp,
  1y +1.9→+3.6pp, holds across splits. First signal to earn its way in under evolve-only-if-robust. Presets unchanged.
- **C DRHP:** productionized prototype into tools/drhp/ (was ephemeral /tmp) + pat==op PAT-suspect guard; DLF's
  suspect PAT withheld; staged NOT folded (only 2/16 net_sales independently validated → review-needed). Bulk deferred.
- **D (conservative):** _p()→spine.pct_num dedup across 19 findings, report byte-identical, 77 tests. pipeline/lib.py
  + scrapers/http.py dedup DEFERRED (need substrate-diff / scraper-test verification first).
- Also fixed L3-1 live date bug (config.AS_OF_DATE single source), L3-2 (config.DEAD_MONEY_RETURN), stale doc counts
  (29/77), requirements + .gitignore. Status files consolidated to STATUS.md.
