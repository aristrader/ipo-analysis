# task_20 — Re-audit ALL already-"fixed" items (CONSOLIDATION + gap-check)

> **STATUS: NOT FINAL — design/think-only proposal for owner review.** No code, no pipeline run, no commits.
> All numbers below were re-derived read-only against the live repo on 2026-06-17.

## 1. Scope
**The single question:** For every data item ever *claimed* FIXED (the O-series O-1…O-16, the D-1 corp-action
family, the 88-audit Category-1 split corrections, plus the committed I1 / clamp / doc fixes), does the fix
**actually hold on the current data**, and was each one re-audited by *some* task? Per the charter's division of
labour, task_20 is a **CONSOLIDATION + coverage gap-check**, not a from-scratch re-audit.

> **CORRECTION (round-1 review):** an earlier draft of this task asserted "Group-B tasks 14-19 do not yet exist
> on disk" and on that basis performed a from-scratch re-audit. **That premise was FALSE/stale** — all six
> sibling files now exist and are authoritative: `docs/research/night_run/task_14_corp_actions.md`,
> `task_15_subscription_gmp.md`, `task_16_financials.md`, `task_17_market_cap.md`, `task_18_dates_identity_bands.md`,
> `task_19_returns_i1.md`. task_20 is therefore the CONSOLIDATION the charter mandates: it **reads those tasks'
> step-3 verdicts and reconciles each live verdict against the owning task**, doing only a spot ground-truth
> re-derivation to confirm/deny and to catch coverage gaps. Where the earlier draft's independent re-derivation
> CONTRADICTED a sibling (O-5/O-6/O-8/O-15 — see §3E), the contradiction was a **string-vs-float predicate bug**
> in this task (`x=='0'` missed the substrate's `'0.0'` encoding); the SIBLINGS ARE CORRECT and their verdicts
> are adopted here.

Also carries the **Category-2 verified-crash whitelist** so no downstream task "re-fixes" a genuine wipeout.

## 2. Ground-truth inputs (cited by path)
- `docs/research/alignment_audit_2026-06-16.md` — the O-series (O-1…O-16), D-1/D-2/D-3/D-4, T-1…T-5, DOC/STRUCT, Appendix A (Phase-0 buckets, Wave-1 evidence).
- `docs/research/unresolved_88_mismatches_audit.md` — Category-1 (21 splits-with-ratios) + Category-2 (67 verified-genuine crashes / the whitelist).
- `data/reference/corp_actions_merged.csv` — 1897 rows; sources: nse_corp_actions:equities 1341, yfinance 354, nse_corp_actions:sme 163, **manual_thinktank_audit 34**, **verification_2026-05-31 5**.
- `data/reference/manual_overrides.csv` — **3 rows, all `market_maker`** (NOT the corp-action overlay).
- `data/master/ipo_analysis.csv` — THE substrate; **2384 rows**; last touched by commit `26cd1fd` (the same commit that merged the corp-actions AND introduced D-1).
- `data/master/substrate_meta.json` — rows 2384, as_of 2026-06-06.
- `git log` — PR #1 (`6d6730c`/`26cd1fd`), PR #2 (`1bf15bc`), PR #3 (`5e323d4`); plus `e6053e7` (I1 category-null), `726b0bb` (clamp extend).
- **The six owning task files (the artifacts this consolidation reconciles against):**
  `docs/research/night_run/task_14_corp_actions.md` (D-1, Cat-1, T-2 whitelist; includes a completed review-log F1 correction),
  `task_15_subscription_gmp.md` (O-2/O-3/O-4), `task_16_financials.md` (O-5/O-6/O-7/O-9/O-10),
  `task_17_market_cap.md` (O-8/O-12/O-15), `task_18_dates_identity_bands.md` (O-11/O-13/O-14/O-16),
  `task_19_returns_i1.md` (returns, systemic I1, T-2/T-4). Every O-/D-/I1 verdict below is cross-checked against
  the owning task's step-3 number and cited.
- **`docs/research/night_run_2026-06-17_review_log.md` — ABSENT on disk** (the per-task review rounds have no
  logged evidence; see §7 coverage note).

**Method note (charter rule):** counts via the `csv` module, never `wc -l`. The substrate has NOT been
regenerated since `26cd1fd`, so it reflects the buggy corp-action merge — this is the single most important
ground-truth fact for this re-audit.

## 3. Reproduce + RE-AUDIT each "already-fixed" item against current data

### 3A. The headline reversal — "FIXED in the reference file" ≠ "FIXED in the substrate"
The corp-action manual corrections (34 `manual_thinktank_audit` rows in `corp_actions_merged.csv`) and the
Category-1 splits ARE present in the *reference* file — yet the fake multibaggers the fix was meant to kill are
**still live in the substrate**.

> **ROOT-CAUSE CORRECTION (round-1 adversarial review):** an earlier draft framed this as "the substrate was
> never rebuilt with the corrected dedup" (overlay-ahead-of-substrate). **git ground truth contradicts that:**
> the most-recent commit touching BOTH `data/master/ipo_analysis.csv` AND `data/reference/corp_actions_merged.csv`
> is the SAME commit `26cd1fd` ("merge missing corp actions", 2026-06-14). **The substrate WAS rebuilt at
> `26cd1fd`, in the same commit that merged the corrections.** The fake multibaggers persist NOT because the
> overlay is un-applied, but because the **merge/dedup JOIN in that rebuild is buggy** (it introduced D-1 — see
> the ROLEXRINGS ISIN-mismatch + duplicate-event evidence in §6). The correct architectural class is "the join
> is broken," not "an overlay is pending application." task_08/task_09 design must aim at the join/dedup bug, not
> at a non-existent "apply the overlay" gap. (See also the e6053e7 fix-reverted-by-rebuild evidence in §3D.)

**D-1 fake multibaggers — RE-AUDIT (read `current_return_from_issue`/`outcome_class` from substrate by `nse_symbol`):**
| symbol | current_return_from_issue | outcome_class | verdict |
|---|---|---|---|
| ROLEXRINGS | **152.72** (=+15,272%) | multibagger | **STILL BROKEN** |
| NPST | **161.27** (=+16,127%) | multibagger | **STILL BROKEN** |
| CANTABIL | **39.68** (=+3,968%) | multibagger | **STILL BROKEN** |
| GNA | 6.39 | multibagger | suspect (needs price-gap check) |
| MOS | 3.37 | multibagger | plausible-ish |
| PAVNAIND | 2.97 | multibagger | plausible |
| VISHWARAJ | 1.36 | multibagger | plausible |
| DIGIKORE | 0.33 | winner | ok |
| USASEEDS | 0.63 | winner | ok |
| CMMIPL | −0.999 | wipeout | ok (price-coverage-hole caveat) |
| ABHISHEK / RPEL | 0 / blank | (no outcome) | unpriced |

**Count:** of the 12 count-conflict symbols resolvable in-substrate, **7 are still `multibagger`; 3 are still
absurd (>+2000%)**. → D-1 is **NOT FIXED in the live data** — not because the overlay is un-applied (it is in
`corp_actions_merged.csv` and the substrate was rebuilt @26cd1fd), but because the corp-action join/dedup that
consumed it is buggy (§3A root-cause correction). (Re-audited authoritatively in task_14; this is the cross-check.)

### 3B. Category-1 splits (88-audit) — were they applied?
Re-audited all 21 Cat-1 ISINs against `corp_actions_merged.csv`:
- **20 of 21 ARE present** as `manual_thinktank_audit` rows with the expected factors (Aishwarya 2.0; Darshan
  5.0+2.1; 7NR 0.1+10.0+1.2; Sharika 2.0+2.0; Anisha 21.0; etc.).
- **1 MISSING: Indiabulls Power INE399K01017** (Cat-1 "bonus issue reported") — **zero events** in the file.
- **CHARTER CLAIM CORRECTION:** the charter (task_14 inputs + §A seed) states these are *"NOT yet in
  manual_overrides.csv — decided-but-unapplied."* That is **half-true and misleading**: they were applied, but
  via `corp_actions_merged.csv` (the `07` consumer), NOT `manual_overrides.csv` (the `09` consumer). So the
  *correction exists in the overlay* — yet the *substrate still shows the bug* (3A). The real story (per the §3A
  root-cause correction) is **NOT "written-but-not-materialised"**: the substrate WAS rebuilt at `26cd1fd` with
  the overlay present; the corrections **did not take effect because the corp-action JOIN/dedup is buggy** (the
  ISIN-vs-symbol mismatch + duplicate-event hazard exemplified by ROLEXRINGS in §6). task_08 (overlay enumeration)
  and task_09 (reconciliation) must treat **"applied-but-defeated-by-a-broken-join"** as a first-class state —
  distinct from a genuinely un-applied overlay.

### 3C. The clamp / envelope (T-2 / T-4) — RE-AUDIT
- T-2 envelope (`trough ≤ endpoint ≤ peak`, issue-anchored): **43 violations across 32 distinct stocks** still
  live (audit said "39 rows"; close — the difference is short-horizon cols added by `19e6158`). *(Predicate not
  pinned to columns/horizon in this draft — the substrate exposes `mfe_/mae_` at 1m/3m/6m/1y/3y/5y; the exact
  43/32 figure is NOT independently reproducible without the column+horizon spec and must be re-stated by task_19
  as the owning task. See §6 T-2 note.)* Offender set is
  dominated by **88-audit Category-2 verified-genuine crashes** (INE183H01011 XL Telecom, INE253N01010 Max
  Alert, INE218P01018 Amrapali, INE312H01016 Inox, INE364T01012, INE576P01019, …). → confirms the charter's
  T-4-decision-c warning: **these are REAL paths, the tripwire must NOT clamp them.** Inox INE312H01016 is in
  the offender set, as the charter predicted.
- T-4 clamp removal (`26cd1fd`): the silent clamp is gone; the loud-tripwire + explicit-delisting replacement
  was DESIGN-LOCKED but **NOT built** (depends on D-1, whose join/dedup is still buggy). → **NOT FIXED; correctly pending.**

### 3D. I1 / O-2 / O-3 subscription 0-vs-null — RE-AUDIT
- Commit `e6053e7` claims "null 32 uncaptured subscription-category cells (0→blank)."
- **O-2 (`sub_total_x == 0`): exactly 124 rows still present** — matches the audit's claim verbatim; **NOT
  FIXED** (the e6053e7 fix did not touch `sub_total_x`).
- **O-3 (sub_total_x>60 AND all of qib/nii/retail ==0): 14 rows still live** (INE682M01012, INE055S01018,
  INE349Y01013, INE0PDJ01013, INE0QFE01017, …). task_15 §3.2 authoritatively reproduces the audit's THREE NAMED
  cases — `INE682M01012` Jupiter Life Line (tot 64.8), `INE055S01018` Cyient DLM (tot 71.3), `INE349Y01013`
  ideaForge (tot 106.1) — all `src=sharescart`, all three category cells 0; these are confirmed in the 14-row set.
  **Category numeric-zero cells (`float(v)==0`, charter rule — string `=='0'` undercounts because zeros are stored
  as both `'0'` and `'0.0'`): qib 341 (338 as `'0'` + 3 as `'0.0'`), nii 156, retail 157 (156 + 1 as `'0.0'`).**
  → the e6053e7 "fix" was **narrow/partial** (a one-off CSV null of 32 specific cells), the systemic 0-as-missing
  pattern persists. **I1 = NOT systemically FIXED** (consistent with STATUS marking it HELD).
- **e6053e7 fix-REVERTED-by-rebuild (round-1 finding):** `git show e6053e7:…` shows e6053e7 (2026-06-10) blanked
  exactly the O-3 cells (`INE682M01012`/`INE055S01018`/`INE349Y01013` had qib/nii/retail `==''` after it). The
  LATER `26cd1fd` rebuild (2026-06-14) **re-introduced `0`** into those cells (current live values: `qib='0'
  nii='0' retail='0'`). So e6053e7 was **not merely "partial" — it was CLOBBERED by a non-idempotent rebuild.**
  This is direct, first-class evidence that the current pipeline DROPS hand-fix overlays on rebuild — promote it
  as a primary exhibit for task_08 (idempotency / hand-fix preservation).
- **Inconsistent zero-encoding across columns** (`'0'` for `sub_total_x`/`sub_nii_x`; `'0.0'` for
  `net_sales_yr3`/`market_cap_cr`/`gmp_pct`; a mix for `sub_qib_x`/`sub_retail_x`) is itself an **I1-class finding**
  — feed it to task_15/task_19: any zero-vs-missing predicate must parse numerically, never string-match.

### 3E. Other O-series — RE-AUDIT
> **PREDICATE-BUG CORRECTION (round-1 review — applies to all numeric-zero rows below).** An earlier draft tested
> string equality `x.get(col)=='0'` and reported **0 rows** for O-6/O-8/O-15, then declared them "unreproducible."
> That was a **measurement bug**: the substrate stores these zeros as the string `'0.0'`, not `'0'`. Re-derived
> read-only with **numeric parsing (`float(v)==0.0`)** on `data/master/ipo_analysis.csv` (2384 rows), every one
> REPRODUCES and matches the original audit AND the owning sibling task exactly. Verdicts below are corrected and
> reconciled to the siblings (task_16, task_17).

| ID | Claim | Re-audit on current substrate (numeric parse) | Verdict |
|---|---|---|---|
| O-1 | Udayshivakumar listing_open=0 raw, contained | `listing_open='0.00'`, `adj_listing_open='30.0'` | **As stated — contained, raw NOT repaired** |
| O-5 | eps_yr1/eps_yr2 ~1000× inflation | `\|eps_yr1\|>1000` = **51 rows**, `\|eps_yr2\|>1000` = **57** (`\|eps_yr3\|>1000` = 25; `\|eps_yr1\|>5000` = 23; max magnitude 1,306,098 Honasa INE0J5401028) | **REPRODUCES** (matches task_16: 51/57). The literal "~1000× cross-year ratio" framing was a strawman the earlier draft used → 0; the audit's COUNT holds. ROOT CAUSE per task_16 = **share-base discontinuity (95 rows), not a ÷1000 parse error** — a refinement of mechanism, NOT "unreproducible." |
| O-6 | net_sales_yr3=0 on 13 large cos | `net_sales_yr3 float==0.0` = **13 rows** (460 blank); `pre_ipo_net_sales float==0.0` = **17** | **REPRODUCES: 13 rows** (EXACT match to audit's "13 large cos" and to task_16's 13). By instrument_type (task_16): equity 5 / reit 4 / invit 4 — the 5 big offenders are REIT/InvIT non-equity contamination (INE0CCU25019 Mindspace, INE0NHL23019 Bharat Highways, INE183W23014 IRB InvIT, INE041025011 Embassy, INE2Q7823014 Citius). task_16 notes the "poisons margins" HALF does not hold (zero-guard works), but the count + NCD-contamination angle REPRODUCE → task_05b equity-table gate. |
| O-8 | market_cap_cr<issue_size + 12 zeros | `market_cap_cr float==0.0` = **7 rows**; `0 < mc < issue_size` = 169 (task_17) | **REPRODUCES** — the zeros are the SAME 7 as O-15 (task_17 resolves the audit's "12 vs 7" discrepancy to 7 actual zeros); the `mc<issue` band reproduces (169) → task_17 |
| O-12 | Bajaj Corp INE933K01021 mcap=292,355 wrong-entity | `market_cap_cr='292355.0'`, class large | **STILL BROKEN** → task_17 |
| O-15 | 7 micro rows market_cap_cr=0 | `market_cap_cr float==0.0` = **7 rows** (INE971P01012, INE668X01018, INE728W01012, INE650Z01011, INE301Z01011, INE418Y01016, INE00CO01016) | **REPRODUCES EXACTLY: 7 rows** (matches audit's "7 micro rows" and task_17 §O-15 verbatim) |

**Why the earlier draft mis-reported O-5/O-6/O-8/O-15 as "unreproducible":** a string-`=='0'` predicate that
missed the `'0.0'` encoding (O-6/O-8/O-15) plus a strawman "~1000× cross-year ratio" predicate the audit never
used (O-5). **All four reproduce and are confirmed by their owning sibling tasks.** The genuine finding here is
narrower: predicates must parse numerically and must match the audit's actual predicate before any "does not
reproduce" verdict is trusted. There is **no surviving "known issues rest on unreproducible evidence" class** —
that earlier conclusion is withdrawn (see §5).

### 3F. Doc / structural fixes (PR #2/#3) — RE-AUDIT (these genuinely landed)
- DOC-7/SR-6/SR-11 rules-path: `rules/` exists at repo root (git mv landed in PR #2). **FIXED.**
- DOC-3 project_map pointers + STRUCT-1 counts-SSOT + FILE_KINDS guard: landed in PR #3 (`5e323d4`). **FIXED**
  (these are structural/doc, independently verifiable; out of scope for *data* re-audit but logged for coverage).
- C-2 (WebFetch allowlist doc location): doc-only, **not data**; still listed UNVERIFIED in the audit — leave to a doc pass.

## 4. Options (how task_20 should position these findings) — ≥3, steelmanned
**Leaning (from charter):** task_20 = thin consolidation that trusts tasks 14-19's step-3 re-audits.

- **Option A — Pure consolidation, trust 14-19 blindly (the leaning).** *Steelman:* avoids duplicated work; keeps
  each fix's authoritative re-audit with its area expert; cheap. *Reject reason (tied to CORRECT + adversarial
  lens):* the siblings DO exist and are authoritative, but a *blind* copy of their verdicts forfeits the
  cross-check the consolidation is FOR — this very task's round-1 errors (O-5/O-6/O-8/O-15) show how a single
  unreviewed predicate can corrupt the register. Consolidation must independently spot-confirm, not blindly trust.
  *(Correction: an earlier draft rejected Option A on the false premise that "tasks 14-19 do not exist yet" — that
  premise was stale; the real objection is blind-copy risk, not empty inputs.)*
- **Option B — Full from-scratch re-audit of every item here.** *Steelman:* guarantees nothing is missed.
  *Reject reason (tied to CLEAN / no-duplication):* duplicates tasks 14-19's mandated step-3; the charter
  explicitly says task_20 "is NOT a from-scratch re-audit and does NOT excuse a thin step 3."
- **Option C — CONSOLIDATION-WITH-BACKSTOP (proposed).** task_20 maintains the **single coverage matrix**
  (every fix → which task owns its re-audit → current live verdict), AND performs a *spot* ground-truth
  re-derivation of each item (done above) sufficient to (i) confirm/deny the live state and (ii) catch
  unreproducible claims — but defers the *deep* per-item design to the owning task. *Why it wins:* satisfies
  CORRECT (every fix has a live verdict now), CLEAN (no deep duplication — the matrix points to the owner),
  and EXTENSIBLE (the matrix is the standing artifact tasks 14-19 fill in). It also surfaces the cross-cutting
  **applied-but-defeated-by-a-broken-join + lost-on-rebuild** class (D-1 join bug + the e6053e7 revert) that no
  single area-task would see in isolation.

## 5. Analysis
The dominant, repo-wide truth this re-audit exposes: **almost nothing claimed "fixed" for the *data* is fixed in
the *substrate*.** The corp-action corrections live in `corp_actions_merged.csv`; the I1 null touched 32 cells;
the clamp was removed — yet the substrate still shows the bugs. So:
1. The substrate **WAS rebuilt at `26cd1fd`** (the same commit that merged the corrections), but the fixes **did
   not take effect because the corp-action JOIN/dedup is buggy** (D-1), and at least one hand-fix (e6053e7's O-3
   null) was **reverted by that non-idempotent rebuild**. The correct class is "applied-but-defeated-by-a-broken-
   join + lost-on-rebuild," NOT "overlay written but never materialised." This is exactly the failure mode the
   reproducibility overlay (task_08, idempotency / hand-fix preservation) + reconciliation campaign (task_09) are
   designed to close, and it validates building those — with a correct join + idempotent reapplication — before
   declaring any fix done.
2. **WITHDRAWN.** The earlier "subset of known issues (O-5, O-6, O-8, O-15) do not reproduce" conclusion was an
   artifact of this task's own string-`=='0'` predicate bug (and an O-5 strawman). All four REPRODUCE and are
   confirmed by the owning sibling tasks (§3E). There is **no surviving need to re-ground genuinely-reproducing
   issues**; the only generalizable lesson is "parse numerically + use the audit's actual predicate."
3. The **Category-2 whitelist (67 verified-genuine crashes)** overlaps heavily with the T-2 envelope offenders
   → the cleaning model MUST carry this whitelist so the rebuild never manufactures a phantom split for a real
   wipeout (Inox INE312H01016 is the canonical case the charter calls out).

## 6. TEST / validate (numbers + ≥2 worked examples)
**Predicates run read-only on `data/master/ipo_analysis.csv` (2384 rows):**
- D-1 caught (still-broken): `outcome_class=='multibagger'` among the 12 count-conflict symbols → **7 caught**;
  `current_return_from_issue>20` → **3 caught** (ROLEXRINGS 152.72, NPST 161.27, CANTABIL 39.68). False-negatives
  (claimed-fixed but actually broken) = these 3+ rows. Over-caught (claimed-broken but actually fine) = DIGIKORE,
  USASEEDS, CMMIPL (4 of the 12 are NOT inflated).
- Cat-1 coverage: 20/21 ISINs present in overlay (caught), **1 missed = INE399K01017** (false-negative of the
  "all Cat-1 applied" claim).
- O-2: `sub_total_x` numeric `==0` → **124 rows** (matches audit exactly; 0 missed, 0 over-caught vs claim).
- O-3: sub_total>60 & all cats numeric `==0` → **14 rows** still live (the e6053e7 fix under-caught). Category
  numeric-zero cells: qib **341**, nii **156**, retail **157** (string `=='0'` undercounts qib/retail by 3/1).
- T-2 envelope: `not(mae≤endpoint≤mfe)` issue-anchored → **43 violations / 32 stocks** *(predicate not pinned to a
  specific mfe_/mae_ horizon in this draft → figure not independently reproducible; task_19 to re-state with the
  exact column+horizon)*; Inox present.
- **Numeric-zero claims that DO reproduce (corrected from the earlier draft's string-`=='0'` bug):** O-5
  (`\|eps_yr1\|>1000` → **51**, `\|eps_yr2\|>1000` → **57**), O-6 (`net_sales_yr3 float==0.0` → **13**),
  O-8/O-15 (`market_cap_cr float==0.0` → **7**). The earlier "0 rows / unreproducible" figures were the bug, not
  the data.

**Worked examples by ISIN:**
1. **ROLEXRINGS — corp-action overlay is NOT a clean single 10:1; it is a multi-source DUPLICATE on a
   pre-split ISIN.** `corp_actions_merged.csv` carries **3 split events** for symbol ROLEXRINGS, all ratio 10.0:
   one `nse_corp_actions:equities` row keyed to **INE645S01016** (ex 2025-10-17) + **two `yfinance` duplicates**
   (ex 2025-10-03 and 2025-09-19). The substrate keys the company under **INE645S01024** (the POST-split ISIN —
   a face-value split changes the ISIN). So an ISIN-keyed join MISSES the correction entirely (overlay key
   INE645S01016 ≠ substrate key INE645S01024), AND the 3-for-1 duplication is a dedup hazard. Substrate still
   shows `current_return_from_issue=152.72`, `outcome_class=multibagger`. → this single example exemplifies BOTH
   the D-1 dedup bug AND the pre/post-split ISIN-drift join the rebuild must reconcile (the CLAUDE.md
   "corp-actions-match-by-symbol" exception exists precisely for this). Feed to task_07 (identity/matching) +
   task_14 (corp-actions).
2. **INE399K01017 (Indiabulls Power):** Cat-1 says "bonus issue reported"; `corp_actions_merged.csv` has **zero**
   rows for it → the one Cat-1 correction that was never written to the overlay at all.
3. **INE933K01021 (Bajaj Corp):** `market_cap_cr=292355.0`, class `large` → O-12 wrong-entity join untouched.
4. **INE312H01016 (Inox):** in the T-2 offender set AND in Category-2 whitelist → REAL crash path; must not be
   clamped. *Note the per-horizon nuance task_19 must pin:* Inox is a genuine drawdown at the 3y horizon
   (`mfe_3y=1.108`, `mae_3y=-0.810`, `return_from_issue_3y=-0.643`) yet its `current_return_from_issue` is **+6.04
   (multibagger)** — so the "envelope violation" is horizon-specific. The cleaning model must whitelist the right
   horizon's path, not treat the positive current endpoint as the offender.

## 7. NON-FINAL proposal + open owner-questions

### Proposed coverage matrix (the standing artifact; live verdict as of 2026-06-17)
> **Verdicts are PROVISIONAL** — each is reconciled against the owning task's authoritative step-3 number, but
> tasks 14-19 must INDEPENDENTLY reproduce (not copy) each predicate before adopting it. Every audit ID O-1…O-16
> has its own row so the gap-check is real.
> **Doc/structural scope rule:** DOC/STRUCT/C-2 items are **non-data**; they are listed in a clearly-labelled
> "non-data, logged for completeness" sub-block below, NOT mixed into the data rows (avoids the in-scope/out-of-scope
> inconsistency of logging some doc fixes while omitting DOC-2/DOC-4).

**Data fix items:**
| Fix item | Owning task | Where the "fix" lives | LIVE substrate verdict (provisional) |
|---|---|---|---|
| D-1 count-conflict (ROLEXRINGS/NPST/CANTABIL +…) | task_14 | corp_actions_merged (manual_thinktank_audit ×34) | **NOT FIXED — overlay present but defeated by buggy join/dedup; substrate rebuilt @26cd1fd** |
| D-2 reverse-splits | task_14 | folded into D-1 plan | NOT FIXED |
| Cat-1 21 splits | task_14 | overlay 20/21; **INE399K01017 missing** | applied-but-defeated; 1 overlay gap |
| O-1 listing_open=0 raw | task_19 | contained (adj col) | contained, raw not repaired |
| O-2 sub_total_x=0 (124) | task_15 | none | NOT FIXED (reproduces 124) |
| O-3 category 0-as-missing (14) | task_15 | e6053e7 partial (32 cells), REVERTED by 26cd1fd | **partial+reverted — 14 still live** |
| O-4 gmp_pct=0 (10) | task_15 | none | **VERIFIED-LIVE: 10 rows** (task_15 §3.3 "reproduced exactly"; Krishna Defence INE0J5601015, Timescan INE0IJY01014) |
| O-5 EPS inflation | task_16 | none | **REPRODUCES: 51/57 rows** (root cause = share-base discontinuity, not ÷1000 — task_16) |
| O-6 net_sales_yr3=0 | task_16/05b | none | **REPRODUCES: 13 rows** (5 REIT/InvIT non-equity + 5 equity shells — task_16) |
| O-7 eps_ttm absurd | task_16 | none | **VERIFIED-LIVE** (3 rows, e.g. eps_ttm≈13927 INE1I1301016 — task_16) |
| O-8 market_cap < issue + zeros | task_17 | none | **REPRODUCES** (zeros = the same 7 as O-15; mc<issue band 169 — task_17) |
| O-9 debt-equity sign vs ROE | task_16 | none | open — sign-inconsistency (task_16 scopes ROE/DE; e.g. Indiqube INE06ST01018 ROE 1400%) |
| O-10 pat_margin absurd | task_16 | none | **VERIFIED-LIVE** (e.g. pre_ipo_pat_margin_pct≈983 INE334L01012 / Ujjivan — task_16) |
| O-12 Bajaj wrong-entity mcap | task_17 | none | **NOT FIXED (live)** |
| O-15 market_cap_cr=0 (7) | task_17 | none | **REPRODUCES EXACTLY: 7 rows** (task_17 §O-15) |
| O-11 date transposition (3) | task_18 | none | open (verify) |
| O-13 inverted bands (2) | task_18 | none | open (verify) |
| O-14 min_investment=0 (18) | task_18 | none | open (verify) |
| O-16 one-offs (Wakefit/IDR/…) | task_05b/18 | none | open |
| I1 systemic 0→NaN | task_19 | e6053e7 partial+reverted | **NOT systemically fixed** |
| T-2 envelope (43/32, predicate unpinned) | task_19 | clamp removed | live; many are Cat-2 real crashes (don't clamp); task_19 to pin horizon |
| T-4 delisting −100% explicit | task_19 | design-locked only | NOT built (pending D-1) |

**Non-data items (logged for completeness — out of *data* re-audit scope):**
| Fix item | Where | Verdict |
|---|---|---|
| DOC-2 "5-component"→"8-component" scorecard | (committed) | Fixed (per audit; doc-only) |
| DOC-3 project_map pointers + STRUCT-1 counts-SSOT | PR #3 (5e323d4) | **FIXED** |
| DOC-4 stale paths | (partial) | PARTIAL (per audit L80/L366-372) |
| DOC-7 rules-path | PR #2 (1bf15bc) | **FIXED** |
| C-2 allowlist doc location | doc pass | doc-only, not data — unverified |

### Category-2 verified-crash WHITELIST (carry into task_14/19 + cleaning model)
The 67 ISINs in `unresolved_88_mismatches_audit.md` Category-2 are **verified-genuine crashes with ZERO
unrecorded corp action** — the rebuild must NOT manufacture a split/bonus for any of them. Canonical examples:
INE900K01012 (Aster Silicates −91.6%), INE688I01017 (Future Capital), INE369I01014 (Maytas),
**INE312H01016 (Inox — the single T-2 envelope offender that is REAL data, not a bug to clamp)**.

### Open owner-questions
1. **The corrections are in the overlay but defeated by a broken join.** The substrate WAS rebuilt at `26cd1fd`
   with the overlay present, yet the corp-action corrections didn't take effect (buggy ISIN-vs-symbol join +
   duplicate-event dedup — ROLEXRINGS §6). Do we (a) fix the join/dedup and rebuild now, or (b) hold until the
   full overlay + reconciliation campaign (task_08/09) is designed — accepting the live substrate keeps the 3
   fake multibaggers in the interim? (Leaning per charter: hold; foundation-first. The real question is "fix the
   join," NOT "re-run to apply an un-applied overlay.")
2. **INE399K01017 (Indiabulls Power)** is the one Cat-1 correction never written to any overlay. Confirm the
   bonus ratio so it can be added, or mark it deferred?
3. **WITHDRAWN.** (Was: "treat O-5/O-6/O-8/O-15 as unreproducible — re-ground?") These all REPRODUCE and are
   confirmed by the owning sibling tasks (§3E); there is nothing to re-ground. The residual lesson is a process
   one: predicates must parse numerically and match the audit's actual predicate.
4. **e6053e7 was REVERTED by the 26cd1fd rebuild** (not merely partial — §3D). The question is not "retire a
   partial fix" but: how do we make such a hand-fix **survive a rebuild** (overlay idempotency / hand-fix
   preservation, task_08), and then fold all I1 zeros into the single systemic "0→NaN at load" policy?
5. **Coverage matrix ownership:** adopt the matrix above as the canonical cross-task coverage tracker in the
   issue register, so "every known fix re-audited by some task" is auditable? (Verdicts are provisional pending
   each owning task's independent re-derivation.)
6. **Missing review log.** `docs/research/night_run_2026-06-17_review_log.md` does NOT exist on disk. Per the
   charter PER-TASK METHOD step 7, every task's review rounds must be logged there for "quiet" to be auditable.
   task_14/task_19 already assert their stop rule satisfied, but **those claims are unverifiable without the
   log.** Owner item: the review_log must be created and back-filled before ANY task (including ones claiming
   "satisfied") can be called done.

---
## DONE CHECKLIST
- [x] all 8 steps present and non-empty
- [x] ground-truth inputs cited by FILE PATH
- [x] step-6 numbers present (caught/missed/over-caught + ≥2 ISIN examples)
- [ ] review-loop stop rule satisfied — **NOT YET MET.** ROUND 1 (correctness · completeness · context-pickup ·
  north-star · adversarial) has been RECEIVED and its findings APPLIED (see the inline CORRECTION blocks in §1,
  §3A, §3B, §3D, §3E, §5, §6, §7). Stop rule requires ≥2 consecutive CLEAN rounds → at minimum one more fresh
  round needed; and `night_run_2026-06-17_review_log.md` does not yet exist to log them.
- [x] NOT-FINAL marker + open-owner-questions block present

> **Review status:** Round-1 multi-lens review applied (it caught a string-vs-float predicate bug that had
> falsely declared O-5/O-6/O-8/O-15 "unreproducible," and a wrong overlay-not-rebuilt root cause). Verdicts are
> now reconciled to the authoritative sibling tasks 14-19. Per the per-task method this still needs ≥2
> consecutive CLEAN independent fresh-agent rounds, logged in `night_run_2026-06-17_review_log.md` (currently
> absent — owner-question #6), before it can be called done. Marking incomplete honestly.
