# Owner decisions — review walkthrough (running log, 2026-06-17)

> Captures the owner's answer per item as we walk File A (issue register §2/§3) then File B (design §0/§18).
> NOT FINAL — these are the owner's current decisions/leanings, re-derivable. One row per discussed item.
> Pairs with the checkbox HTML (`review_issues.html` / `review_design.html`).

---

## FILE B — design §0 (24 decisions)

### Quick-confirm batch — 11 decisions ALREADY settled by File A — ✅ CONFIRMED (owner: nothing to discuss)
- **D1** one spine + derived views (Option C) ← OD-6/OD-7 one-spine principle.
- **D6** `_prov` provenance encoding (replaces patchy `_src`) ← OD-1/OD-2.
- **D7** `quality` clean/dirty partition ← OD-7.
- **D8** as-of class (`at_ipo` vs `current`) for all time-varying fields ← OD-5.
- **D9** market-cap at-IPO source ← OD-5 → BL-1 (backlogged).
- **D11** honest-NULL default + gated refetch (no auto-network) ← OD-4.
- **D18** reconciliation campaign = first build action; fakes stay until it completes ← OD-8.
- **D19** validity-rule severity = field-level default, escalate to row when poisoning ← OD-7 part 2.
- **D22** EPS recompute A1/A2 ← OD-7 → BL-2 (backlogged).
- **D23** reserve future-universe seam now, don't build ← P-4.
- **D24** cross-field (multi-column) validity predicates ← OD-2.
**13 remaining to discuss:** 2,3,4,5 (schema) · 10,20,21 (registry) · 12,13,14 (identity) · 15,16,17 (overlay).

### D2 — rename `type` → `board` — ✅ DECIDED
Retire the vague/overloaded `type` (MB/SME) for an explicit `board` structural column; migrate consumers.
Removes the `type` vs `instrument_type` confusion; matches the 5 structural columns. (Owner: yes, rename.)

### D3 — `cohort` stored vs derived → CONFIG-DRIVEN VIEW (owner improved it) — ✅ DECIDED
**Decision: `cohort` is NOT a stored column. It's a config-driven derived view.**
- Define cohort (and ALL date-boundary classifications) in ONE **time-partition config** (env/config file);
  the cleanup-pipeline/view layer derives them. Change a boundary = edit one config line → everything updates.
- **Generalizes beyond cohort:** the same config governs **era buckets + train/test/validation date splits**
  ("before date X = train, after = test", point-in-time cutoffs) — single orchestration point.
- **Kills the scattered-magic-dates anti-pattern:** BUILD TASK — pull existing hardcoded cohort/split dates out
  of the pipeline/predictor/validation code into this one config (single auditable source of date boundaries).
- **Readability kept:** the view can be MATERIALIZED (generated CSV, like mainboard/sme views), but the SOURCE
  OF TRUTH is the config, not a stored column. Purest form of the one-spine-+-derived-views principle.

### D4 — schema source of truth — ✅ DECIDED
- **The column registry IS the schema** = the single source of truth for what columns exist. No separately
  hand-maintained `docs/schema.md` (that's how it rotted into documenting phantom columns). If a human-readable
  schema is wanted, GENERATE a view from the registry (zero-maintenance) — possibly folded into P-2's output.
- **Retire the old `docs/schema.md`** (→ BL-3 cleanup, or sooner) + the phantom columns.
- **Phantom/removed columns → registry status `retired` (with reason)** — explicitly dead, history kept, can't
  be silently re-added. The "included/not-included" lives IN the registry (no separate dead-columns file).
- Governed by the **COLUMN-LIFECYCLE POLICY** (active/planned/retired) — see that block. (`pre_ipo_eps` fate = D5.)

### D5 — `pre_ipo_eps` add or retire — ✅ DECIDED
**Retire it** (registry status `retired`) — it doesn't exist today, nothing consumes it, and adding it now would
import the deferred EPS share-base mess (per-year EPS values already cover the need).
- **Note (owner):** if EPS work is ever done under **BL-2** and per-year/TTM EPS (or a pre-IPO EPS) is deemed
  useful, reconsider it THEN (retired → planned → active via the proper channel). Until then it stays retired.

### D10 — registry physical form — ✅ DECIDED: declarative YAML + named-function refs + meta-validator
- **Declarative YAML config** (e.g. `data/registry/columns.yaml`): column metadata = data (name, dtype, ordered
  sources, status, as-of, applicability, parser/validator BY NAME). CSV rejected (can't express ordered sources/
  function refs/cross-field predicates); Python rejected (locks editing to coders, mixes what-vs-how, hard to gen from).
- **Logic lives in code**, in a named registry the YAML points to. Boundary: add a column reusing existing logic =
  config-only (non-coder); add a column needing new logic = config + one new named function (coder).
- **Serves D4 (schema-gen), P-2 (lineage-gen), OD-2 (cross-field predicates), column-lifecycle, non-coder-add goal (P-3).**
- **META-VALIDATOR (safeguard):** validate the registry file each run — required fields present, referenced
  functions exist, statuses valid — so "anyone can edit config" can't cause silent breakage.

### D20 — auto-apply confidence threshold — ✅ DECIDED: Option B (auto-apply HIGH only)
- **HIGH-confidence fixes auto-apply; MED + LOW both route to the dirty-review worklist** for human spot-check
  (vs auto-applying MED). Conservative — matches "correct over fast / flag rather than guess / no cheap fixes."
- Cost is review effort only, NOT data loss: MED rows sit flagged `dirty`, still usable via per-pipeline views (OD-7).
- **Calibration loop:** once a MED rule proves reliably correct on review, PROMOTE it to HIGH (auto). Auto-set
  grows by evidence, not optimism — same "evolve-only-if-robust" discipline as the scorecard.

### D21 — rule-applicability register: home + granularity — ✅ DECIDED
Mental model: the RULE is generic; applicability is an ON/OFF GATE deciding whether it fires for a given IPO.
**(a) HOME: a YAML rule registry (`rules.yaml`), parallel to the column registry (`columns.yaml`, D10), with the
same meta-validator.** NOT structured fields in markdown. The hand-maintained `rules/index.md` is REPLACED by a
view GENERATED from `rules.yaml` (generate-don't-hand-maintain, like the schema). (YAML chosen; JSON/TOML equivalent.)
**(b) A rule entry has THREE parts (the earlier 5-key list was wrong — sorted below):**
1. **GATE — per-IPO on/off, exactly 2 keys:** `board` (MB/SME) + `instrument_type` (equity/reit/invit/idr/fpo).
   Engine checks an IPO's board+instrument_type against each rule's gate → fires or not.
2. **REQUIRED FIELDS:** `required_fields` = columns the rule needs; the OD-7 per-pipeline view keeps a row only
   if those fields are valid. **This is how data-quality is handled — NOT a gate key, an automatic field-validity filter.**
3. **PROPERTIES (trust, recorded about the rule, NOT per-IPO gates):** `cross_regime_validated` (era's real role
   = trust signal), `min_n`/`n` (sample-size floor), plus existing status / backtest-lift / hit-rate / priority / source.
**Dropped as gate keys:** cohort/era (→ a trust PROPERTY; per-IPO-gate redundant since we score new IPOs only),
data_quality_tier (→ handled by OD-7 required-fields views), min-N (→ a trust PROPERTY).
**FIRING POLICY (owner-confirmed):** a rule contributes to a SCORE only if it passes BOTH (1) the relevance gate
(board+instrument_type) AND (2) the trust filter (status=validated, cross_regime_validated, min_n met). Relevant-
but-untrusted rules are DISPLAY-ONLY (shown as context, zero weight) — this IS the existing "evolve-only-if-robust"
/ in-score-vs-display-only policy. Recommendation is always built from trustworthy + relevant rules only.

---

## DATA-LAYER COMPLETION GATE (owner: we CANNOT move to upper layers until these are done + verified)
"Later" has TWO meanings — don't blur them:
- **GATE (must complete WITHIN the data-layer build, before Layer 2/3):** corp-action cleanup (OD-8) · the D12
  ISIN-less deep-dive · D13 slack calibration · the curated identity-history golden file · the reconciliation
  campaign + its §3 verification checklist · all the §0/OD data-layer decisions. "Later" here = a focused task
  later in THIS build, NOT punted past the foundation.
- **GENUINELY DEFERRED (does NOT gate upper layers):** BL-1 (market cap, needs external data) · BL-2 (EPS) ·
  BL-3 (post-dev cleanup) · P-4 (live data) · the OPTIONAL D14 official-NSE-ledger upgrade.

## FILE B §18 — the 6 review findings (R1–R6) → ALL RESOLVED via decisions — ✅
- **R1** provenance column explosion → resolved at **OD-2** (`_prov` only on genuinely-ambiguous fields, +1 col each).
- **R2** state (b) conflates fetch-fail vs source-placeholder → resolved at **OD-1** (split state 2 `Missing_data` vs 3 `error_out`).
- **R3** as-of cure + EPS both blocked on shares-outstanding → **BL-1 / BL-2** (backlogged with the shared blocker).
- **R4** whole-row quarantine too coarse → resolved at **OD-7** (per-pipeline field-scoped views + coarse clean/dirty).
- **R5** conflict-detection needs `old_value` baselines → **§3 safeguard + D15** (each fix records old value; reconciliation backfills baselines).
- **R6** counts are draft-grade → standing caveat (re-verify counts at build; not a decision).

## BUILD SEQUENCING CONSTRAINTS (accumulating — the eventual build plan MUST honor these)
> Ordering rules agreed during the walkthrough. The build plan reads from here so nothing runs out of order.

1. **Scraper review & fix → I1 field-aware encoding build.** (from OD-1) The scraper-honesty pre-task
   (3-point contract: no placeholders · distinguish no-value vs fetch-fail · surface the signal) must land
   BEFORE the I1 provenance encoding is built, because the state-2-vs-3 distinction originates at fetch time.
2. **Corp-action cleanup (D-1) = FIRST cleanup task in development** (from OD-8). Not backlog — a prioritized
   early build task: fix the over-counting/fake-multibaggers properly through the foundation (price-gap arbiter
   + source-reconcile dedup + golden catalog P-1 + reconciliation campaign) before broader analysis is rebuilt.
   Includes a DEDICATED deep-dive run on the ISIN-less yfinance case (D12 TODO — enumerate/handle all failure modes).
3. **P-2 (lineage map) + P-3 (data-change rulebook) → before any coding** (pre-coding finalization).

---

## BACKLOG (deferred — pick up later as a SEPARATE effort, with concrete data; owner: no cheap fixes)

### BL-1 — Source the at-IPO market cap (the proper D-3 cure) — from OD-5
Owner principle: **no cheap fix** (cheap fixes caused today's redesign). Backlog the proper sourcing; do it
later with concrete data. NO `issue_size_cr` proxy, NO salvage hack.
- **COLUMN POLICY (reconciled with D4 / column-lifecycle policy):** `market_cap_at_ipo_cr` and
  `shares_outstanding` = registry status `planned` (one-line stub pointing here); NOT materialized in the shipped
  substrate; findings/work-detail live in this BL-1. They materialize (status→active) only when picked up.
- **No data deleted:** "remove the column" = don't SURFACE it; the **90 existing real values** (all longterm,
  0% boom) stay in their underlying source files — note their location here when we start so they aren't lost.
- The **leak is already handled structurally** by the as-of rule (design decision 8): predictor consumes
  at-IPO fields only → market cap is honestly ABSENT from the predictor (no patch, no column needed now).
- Backlog steps when picked up: (1) value-audit Chittorgarh `kpi_market_cap_post_ipo` (investigation — is
  concrete data there? ≥1 gross error known: HDFC AMC ₹7.8cr) → (2) source **shares outstanding** (= review
  finding **R3**, add the column then) → (3) derive `market_cap_at_ipo_cr = issue_price × post-issue shares`,
  add the column then.
- **Shared blocker with OD-7 (EPS):** "shares outstanding" unblocks BOTH; source once.
- **FINDINGS TO CARRY (so we have context on pickup):** D-3 = current-cap leaked into predictor; at-IPO cap
  exists for only 90 rows (all longterm); Chittorgarh KPI has gross parse errors (HDFC AMC); clean derivation
  needs shares-outstanding which the substrate lacks (R3).

---

## FILE A §4 — full issue catalog (57 rows) → REVIEWED & CLOSED (no map, no links)
**§4 reviewed 2026-06-17: every issue is already subsumed by OD-1→OD-8 + the validity/cleaning-rules model
(per-field validity, as-of class, declarative CR-* rules). Only 2 needed their own handling (below). No coverage
map / cross-links created (owner: avoid maintenance surface that drifts). §4 is FROZEN build-spec — read once at
build, each row becomes its CR-* cleaning rule in the rules registry (permanent home), then `night_run/` is
archived (BL-3). We do NOT re-walk §4.**

Two items NOT covered by an earlier decision:
1. **Cat-2 "do-NOT-correct" protected list (67 ISINs)** — ✅ DECIDED: a THIRD golden reference list (P-1 family),
   sibling to corp-action-events + identity-history. Verified-genuine crashes with NO unrecorded corp action
   (e.g. Aster Silicates real −100% delisting; Inox real +604% via PVR merger). The corp-action fix MUST check
   it and never fabricate a split-correction for these. Distinguishes "genuine extreme path" from "genuine wipeout."
2. **O-12 wrong-entity join (Bajaj cap 36× too large, name-keyed match)** — ✅ DECIDED: NOT a one-off sweep —
   folded into the identity/matching FOUNDATION. It violated the existing rule "ISIN = the only auto-join key;
   name-matching never merges, only flags." Cure = enforce that rule concretely: (a) ISIN-only joins everywhere,
   (b) record matched entity id+name on every join (auditable), (c) THEN sweep existing data for violations
   (Bajaj + siblings). Past docs (CLAUDE.md conventions, docs/sources.md) inform per-source join correctness.
   **Discuss concretely at the File B identity/matching decision (§10 / decision 12).**

---

## FILE A §3 — "Fixed-but-regressed" items → VERIFICATION CHECKLIST (no new decisions) — ✅ HANDLED
These are NOT open issues to re-decide — they're the **proof-of-success checklist for the foundation.** All are
resolved by fixes already decided; we note them now and they become MUST-PASS verification targets. Failure class =
"applied-but-defeated-by-broken-join + lost-on-non-idempotent-rebuild" — exactly what the foundation kills.
- **D-1 / Cat-1 corp-action corrections defeated by the buggy join** (ROLEXRINGS +15,272%, NPST +16,127%,
  CANTABIL +3,968%; ROLEXRINGS even keyed differently in substrate vs overlay) → fixed by **OD-8** (proper
  corp-action fix + reconciliation).
- **e6053e7 O-3 category nulls (32 cells) clobbered by the non-idempotent rebuild** (re-introduced `0` for
  Jupiter/Cyient DLM/ideaForge) → fixed by the **idempotent overlay (design §11)**.
- **Orphaned fix: Indiabulls Power (INE399K01017) Cat-1 split correction was NEVER written to any overlay** →
  must be captured during the reconciliation campaign.
**SAFEGUARD (owner-confirmed):** the reconciliation campaign must (a) migrate EVERY existing hand-fix into the new
overlay incl. the orphaned Indiabulls Power one, and (b) VERIFY each actually LANDS in the rebuilt substrate (not
just exists in a file) — the missing check that let them silently fail before. (Ties to review finding R5 = baseline backfill.)
**VERIFIED TWICE:** during the foundation build (reconciliation = the verify step; foundation not "done" until these pass)
AND again before building upper layers.

---

## PARKED / CROSS-CUTTING TOPICS (owner-raised — discuss at the noted item)

### BL-2 — EPS comparability (A1 vs A2) + "is EPS-trend used anywhere?" check — from OD-7
Owner: backlog it, come to it later (likely not heavily used → verify usage then). No decision A1/A2 now.
- Proper fix **A1** (recompute EPS on a constant share base for cross-year comparability) is BLOCKED on the same
  **shares-outstanding** data as BL-1 → shared blocker, source once.
- Interim now: **no EPS-trend / EPS-CAGR feature shipped** (remove rather than ship a broken one). Per-year EPS
  values stay (each valid on its own); comparability/recompute deferred.
- On pickup: (1) check whether per-year/TTM EPS feeds any feature; if no → A2 null-and-flag suffices; if yes →
  A1 (needs shares-outstanding). (task_16 OQ1.)

### BL-3 — POST-DEVELOPMENT cleanup: retire the OLD data + OLD data docs (raised by owner at OD-8)
Pick up ONLY after the new foundation is fully built, verified, and PROVEN to supersede the old way (do not
start until everything is complete and trusted). Then:
- **Retire the old data section** — the old-way / dirty-data files that the new spine + views replace.
- **Delete/clean up the old data-related docs** — once the new way is the truth, we only keep docs for it
  (e.g. the old `docs/schema.md` shape, superseded pipeline/data docs).
- **Retire hand-maintained registries replaced by generated views:** old `docs/schema.md` (→ generated from
  `columns.yaml`, D4) and hand-maintained `rules/index.md` (→ generated from `rules.yaml`, D21).
- **SAFEGUARD (repo convention):** don't hard-delete prematurely — gate on the new foundation passing its
  verification + reconciliation; prefer moving superseded files to `archive/` (and git history) over destructive
  delete; look before deleting (no-deletion-default rule). Goal = one source of truth, no stale parallel copies.

### COLUMN-LIFECYCLE POLICY (the single rule — reconciles BL-1 + D4; owner: one place to maintain everything)
The **column registry is the catalog of EVERY column, ever** — the single source of truth for "does this column
exist and what's its state." Three states; **shipped data materializes only `active`:**
| status | in registry? | in shipped data? | detail lives where |
|---|---|---|---|
| **active** | yes | YES (materialized) | registry |
| **planned** (backlog) | yes — a one-line stub pointing to the backlog item | NO | the backlog item |
| **retired** (old/phantom) | yes — with a reason note | NO | registry |
- Symmetry rationale: retired stays in-registry so nobody re-adds it (e.g. `ticker_src`); by the same logic
  planned stays in-registry so nobody re-proposes it (e.g. `market_cap_at_ipo_cr`).
- **No duplication:** registry holds existence + status + pointer ONLY; findings/work-detail stay in the backlog.
- Net effect = backlog columns still NOT shipped, findings still in backlog — just a one-line `planned` stub added.

### P-1 — "Golden facts" locked verified-reference sheets (raised at OD-2) — ✅ RESOLVED at OD-8
**Decided at OD-8** → see the "P-1 — Golden verified-reference catalogs" decision in the FILE A section
(two files: corp-action events + identity-history; authoritative; append-only; overlay-carried; status model;
fallback order; fill 4-stock gap; mapped in P-2). Remaining design-side confirmations: overlay (§11) + identity
(§10 / decision 12) when we reach File B.

### P-4 — Live / upcoming data handling (raised by owner at OD-8) — SEPARATE TASK, design seam only now
Owner: live data is its own project; **each data source refreshes differently** (daily / event-driven / no live
feed) → can't pull them all the same way live; must walk EACH pipeline point separately. Matches design §16
(future-universe seams). 
- **Now:** design structures so they ALLOW a live future (e.g. catalog `upcoming`/`announced` status seam ready;
  `announcements` NSE feed seeds upcoming). DO NOT build live handling.
- **Later (separate live task):** upcoming corp-actions, live refresh, per-source live-pull strategy, the
  non-IPO/listed-stock universe. **DO AT: a dedicated live-data effort, after the foundation build.**

### P-2 — Human-readable pipeline + data-LINEAGE diagram (raised by owner at OD-4) — TODO: do BEFORE coding
Owner wants a clear, human-readable picture of all pipelines + data flow: where each datum comes from → goes
to, what columns are added/removed, which file each lands in. **Finalize once, just before coding.**
Key: this is **GENERATED, not hand-drawn** — it falls out of infrastructure we're already building:
- Extends `project_map.py` → `MAP.md` (already the machine-readable DAG → human-readable tree/flow).
- The COLUMN-LEVEL lineage (source→parser→destination→file→applicability) is auto-derivable from the **column
  registry (OD-2 / design §9)** — so it's a "render the registry as a diagram" step, can't drift.
- **MUST include the two golden reference files (P-1): corp-action events + identity-history — and what links to
  what** (owner reminder at OD-8). The map shows every file/datum: what's there, where it comes from, where it goes.
Prerequisite: column registry locked. **DO AT: pre-coding finalization.**

### P-3 — "Data-change protocol" entry/rule file for all future changes (raised by owner at OD-4) — TODO
Owner wants ONE authoritative rulebook that dictates how any future data/pipeline change is made, usable by
every AI + human to review and place each item correctly: e.g. declare in registry → run validity check →
design → implement → update pipeline → regenerate diagram/MAP → verify.
Extend, DON'T duplicate (repo anti-sprawl rule): builds on `docs/research/execution_pipeline.md` (per-task
process), `docs/WORKFLOWS.md` (what-to-do-when), `CLAUDE.md` (brain). New = the DATA-SPECIFIC change checklist,
wired into `project_map.py` CONTEXTS so it auto-surfaces (like the existing agent briefs). **DO AT: pre-coding.**

---

## FILE A — Issue register §2 (owner decisions)

### OD-1 — How to treat `0`/blank (the I1 problem) — ✅ DECIDED
**Decision: APPROVED — field-aware 4-state provenance; reject the global `0→NaN` shortcut.**
- Treat `0`/blank **field-by-field**, not with a blanket rule (the global `0→NaN` would corrupt 725 real
  `ofs_cr=0` fresh-issue rows + real debt-free `borrowings=0`).
- **4 states, value-vs-code split** (value=NULL for the missing ones so math skips them; label in a separate
  `_prov` column):
  | State | Meaning | prov code | numeric cell | retryable |
  |---|---|---|---|---|
  | 1 | real zero | `present` (real) | `0` | n/a |
  | 2 | source never published | `Missing_data` | NULL | no |
  | 3 | fetch/parse failed | `error_out` | NULL | yes (re-scrape can cure) |
  | 4 | not applicable | `N/A` | NULL | n/a |
- Splitting state 2 vs 3 **resolves review finding R2**.
- Exact code spelling is cosmetic → locked in the column registry under OD-2 / design-decision 6.

**NEW PRE-TASK added by owner: "Scraper review & fix" (prerequisite to the I1 build).**
Owner is OK changing scrapers — data honesty starts at the scraper. Bounded to a 3-point contract per scraper:
1. Never mint a placeholder (`0`/`""`) — emit nothing (null) when there's no value.
2. Distinguish "source had no value" (→ state 2) from "fetch/parse failed" (→ state 3).
3. Surface that signal downstream so parse/assemble stamps the correct `_prov` code.
Sequencing: **Scraper review → I1 field-aware encoding build.**

### OD-2 — Where the provenance codes physically live (the carrier) — ✅ DECIDED
**Decision: APPROVED — all three sub-questions.**
1. **One uniform, registry-driven provenance system** (consistent METHOD available to any column) — replaces
   today's patchwork (only 2 of ~7 fields have a `_src` column; 5 have none).
2. **Materialize a `_prov` companion column ONLY on genuinely-ambiguous fields.** Non-ambiguous fields get
   NO provenance column at all (not an empty one). Where a `_prov` column exists it is FULLY populated every
   row (`present`/`Missing_data`/`error_out`/`N/A`) — never blank. **+1 column per ambiguous field, not +2.**
   This is the chosen resolution of review finding **R1** (avoids ~100+ dead columns / file-doubling).
3. **Registry supports cross-field (multi-column) predicates** — needed to catch O-3 (Σ tranches vs total):
   32 rows all-tranches-0-with-positive-total + 218 rows positive-total-with-≥1-zero-tranche.
Principle (owner's framing): **capability everywhere, columns only where needed** (uniform method, selective use).

### OD-3 — Recover 88 subscription rows by arithmetic vs drop them — ✅ DECIDED
**Decision: APPROVED — Option D (recover), with a validation pre-check.**
- **Recover the 88 `_cr`-present rows**: compute `sub_total_x = sub_total_cr ÷ issue_size_cr`, stamp provenance
  `derived` (computed, not sourced) — vs lossy NULL. It's a definitional identity, not a guess.
- **Derive ONLY when `issue_size_cr` is itself valid** (passes its provenance check); else NULL (no garbage
  multiple from a bad denominator).
- **Consistency policy:** `_cr` real + `_x` missing → derive `_x`; both missing → both NULL. Never leave a pair
  where one says "missing" and the other shows real demand.
- **VALIDATION FIRST (owner add):** back-test the identity on rows that ALREADY have BOTH `_x` and `_cr` —
  confirm `sub_total_cr ÷ issue_size_cr ≈ sub_total_x` within tolerance before applying it to the 88 unknowns.
  If it doesn't hold on the known rows, don't apply the rule.

### OD-4 — Re-fetch over the network vs accept "missing" — ✅ DECIDED
**Decision: honest-NULL fallback (default) + a STANDING, reusable refetch mechanism (not one-off approvals).**
- **Default = honest NULL.** A gap is marked `Missing_data`/`error_out` (OD-1) — safe, not corrupting — so we
  never open the network just to feel complete.
- **The provenance marks ARE the refetch worklist.** `error_out` cells = the retry queue (data tells us what to
  refetch); `Missing_data` cells = excluded (never published → re-scrape is wasted). Only state-3/`error_out`
  is ever a refetch candidate.
- **Reuse what we trust — no parallel machinery.** A refetch rides the SAME pipeline as a first-time value:
  re-pull (trusted scraper) → same validity gate → same provenance stamp → clean → push. No special-casing.
- **Verified → promote → lock.** A passing refetched value promotes dirty→clean and can be locked into the
  overlay so a rebuild can't undo it (ties to **P-1** golden facts).
- **GUARDRAIL (network stays default-deny):** the mechanism EXISTS and is wired, but only RUNS on owner's
  manual approval (attended · allowlisted domains · read-only · zero downloads). "Button is there, only owner presses it."
- **First targets when run:** the 18 MB-subscription + 10 GMP rows (small, high-value, trusted source). The big
  long-term backfills (1,498 band/lot · 1,027 identity · 1,886 face_value · 1,487 anchor) are a SEPARATE later
  decision — many are likely state-2 (never published 2006–19), so honest-NULL for now.

### OD-5 — Source the at-IPO market cap (D-3 leak) — ✅ DECIDED
**Decision: BACKLOG the proper sourcing (no cheap fix). See BL-1.**
- Owner: no proxy / no cheap interim (cheap fixes caused today's redesign). Pick up later with concrete data.
- The **leak needs no patch** — it's killed structurally by the as-of rule (decision 8): predictor uses at-IPO
  fields only, so market cap is honestly ABSENT from the predictor until sourced.
- Proper cure deferred to **BL-1** (value-audit KPI → source shares-outstanding [R3] → derive). Shared
  shares-outstanding blocker with OD-7.
- **Column policy (reconciled with D4):** `market_cap_at_ipo_cr` + `shares_outstanding` = registry status
  `planned` (stub → BL-1), NOT materialized in shipped substrate; materialize only when picked up. No data
  deleted (90 longterm values preserved in source). Findings carried in BL-1. See COLUMN-LIFECYCLE POLICY.

### OD-6 — Non-equity handling (REIT/InvIT/IDR/FPO) — ✅ DECIDED
**Decision: tag with `instrument_type`, exclude from equity analyses via partition filter, keep in dataset.**
- **Tag every row** with `instrument_type` (equity/reit/invit/idr/fpo) — identity first. Fixes **O-16(a)** the
  Std Chartered IDR mislabel (currently tagged equity; it's an IDR — set `instrument_type=idr`).
- **Equity analyses/predictor filter to `instrument_type == equity`** via `WHERE` — no if/else (this is what
  the structural column is for). Governs **O-6** (REIT/InvIT have no real "sales") + the `x-nonequity` rule.
- **Keep them in the dataset — do NOT delete** (real listings; just excluded from equity analyses).
- **Separate non-equity analysis = optional backlog** only if N justifies (tiny count today).
- **STORAGE POLICY (owner Q):** tag-in-column on the ONE spine (single source of truth) → derive an equity
  view + a non-equity view as `WHERE` filters → optionally MATERIALIZE the non-equity view as a readable CSV.
  **NOT a separate source file** (a separate file re-splits the source of truth, breaks ISIN-uniqueness across
  files, and makes reclassification a brittle row-move; a tag = change one cell, all views update). Consistent
  with design decision 1 / Option C.

### OD-7 — EPS comparability + validity-rule severity — ✅ DECIDED
**Part 1 (EPS comparability): BACKLOG → BL-2** (shares-outstanding blocker, shared with BL-1; usage check on pickup).
**Part 2 (validity severity, = review finding R4): per-field validity + per-pipeline field-scoped views.**
- **Per-field validity is ground truth.** Keep a coarse `quality=dirty` flag = "row has ≥1 problem somewhere"
  → powers the quarantine worklist, refetch queue (OD-4), and issue/backlog surfacing. It does NOT gate every pipeline.
- **Real gating = per-pipeline field-scoped views:** each analysis/pipeline runs on `WHERE its-required-fields-valid`,
  so a row bad for EPS is still usable by the returns pipeline. Maximizes usable data; nothing over-discarded.
- **Requires:** each pipeline/analysis DECLARES its required fields ("input contract") → view auto-derived. Ties to
  rule-applicability gate (design §14) + the column registry (knows each field's validity). No new machinery.
- Refines design **decision 7** (`quality` partition): clean/dirty = coarse signal; real gating is field-scoped views.

### ESTABLISHED PRINCIPLE (confirmed by owner at OD-7) — ONE spine, everything else is a derived view
The "2 tables" (mainboard-clean + mainboard-dirty) collapses to **ONE table (spine) + derived views**. No stored
duplication, no separate dirty file, no row-moving between files. Two view flavors, both derived from spine +
per-field validity: (1) coarse `clean`/`dirty` (looks across ALL columns), (2) per-pipeline field-scoped views
(look only at the columns that pipeline needs). `clean`/`dirty`/`mainboard`/`sme`/`non-equity`/per-pipeline = all
`WHERE`-filter views. Reclassification = change one cell → all views update. **Governs OD-6 + OD-7 + design decision 1.**

### OD-8 — Corp-action fix: patch the join now vs fix through foundation — ✅ DECIDED
**Decision: fix PROPERLY through the foundation — NOT a quick join patch. And NOT an open backlog: it is a
PRIORITIZED, EARLY build task (first cleanup, first real case through the new foundation).**
- Rationale: D-1 corrupts RETURNS themselves (fake multibaggers e.g. ROLEXRINGS +15,272%, mis-valued delisted
  stocks) → poisons the core analysis. Unlike BL-1/BL-2 it cannot drift indefinitely.
- Held only during THIS design phase (nothing ships → the 3 known fakes sit dormant, no interim patch needed);
  cleaned up FIRST thing in development. Added to BUILD SEQUENCING CONSTRAINTS.
- Proper fix flows through the foundation: price-gap arbiter (source-agnostic) + source-reconcile dedup +
  golden catalog (P-1) authoritative override + reconciliation campaign (the step the buggy join failed at).

### D12 — trust of ISIN-less (symbol-only) yfinance corp-actions — ✅ DECIDED: corroboration-only
**Decision: the 354 symbol-only yfinance corp-action rows are CORROBORATION-ONLY — never create an adjustment
alone** (direct application of "ISIN = only auto-join key; symbol/name only flags, never merges"). Biggest single
lever on the fake-multibagger over-count class.
- Honored ONLY when confirmed by: the **price-gap arbiter** (actual price chart shows a split-shaped gap at the
  claimed ratio — the evidence is the PRICE, not yfinance's bare word) OR an **ISIN-keyed source**.
- Neither confirms (arbiter-blind: no price data / no ISIN source) → **flag unresolved → golden catalog manual
  verify.** Never auto-apply, never auto-drop a possibly-real split.
- Slots into the P-1 fallback order: golden catalog → price-gap arbiter → source-reconcile → flag.
- **TODO (owner) — dedicated deep-dive run for THIS case:** a specific focused design/thinking pass to enumerate
  and handle ALL failure modes (reused symbols, reverse-splits, coverage-start/end gaps, compound bonus+split,
  float-precision ratios, arbiter-blind multibaggers). High failure surface → don't fold into the generic
  corp-action build; give it its own case-by-case treatment. Part of the OD-8 corp-action cleanup.

### D13 — date-window slack for splits effective near listing — ✅ DECIDED: defer into the split deep-dive task
A magic-number calibration → NOT locked now. Folded into the **dedicated corp-action/split deep-dive task (with
D12)** — needs real research: back-test the actual ex-date↔first-trade gap distribution and pick a slack that
cleanly separates genuine near-listing events from the years-off bogus ones. When set, the value lives in the
**time-partition config (D3)**, not hardcoded. (Bad cases are years off, so the window isn't delicate — but research it.)
**GATE: this is a DATA-LAYER task (part of the deep-dive), must complete before upper layers — not open backlog.**

### D14 — official NSE symbol-change ledger vs date-window approximation — ✅ DECIDED: split (gate vs optional)
- **GATE (data-layer, required before upper layers):** the date-window approximation + the manually-curated
  **identity-history golden file (P-1)**. This part is NOT optional — it's part of completing the data layer.
- **OPTIONAL FUTURE (does NOT gate upper layers):** upgrading to an official vetted NSE symbol-change source.
- **Future enhancement (NOT committed):** if/when a TRUSTED NSE symbol-change source is found + vetted (network is
  default-deny; trusted-source registry is expand-only-if-safe), adopt it to replace the approximation — it removes
  guesswork from identity matching (helps O-12). The identity-history file is already the right shape to receive it.
- Same "design the seam, don't build now" pattern as P-4 (live data).

### D15 — consolidate hand-fixes into one overlay ledger — ✅ DECIDED (owner refined the model)
**Decision: one consolidated fixes-ledger applied on top of IMMUTABLE raw → recreatable substrate.**
- Merge the 3 scattered hand-fix files (corp-action audits 39 · Cat-1 splits 21 · DRHP-recovered 16) into ONE
  ledger. Three-way fragmentation literally caused the §3 regressions (fixes defeated/lost/orphaned).
- **Raw never hand-edited;** fixes live in the ledger (yaml/rule); `raw + overlay = substrate`, recomputed every
  run, idempotent, reconciliation-verified. One place, one reader.
- Coherent with P-1 golden catalogs (same store, not parallel systems).
- **Each fix records its OLD VALUE** (R5) → enables conflict detection so "source got fixed upstream" is handled
  right: source still broken → apply fix; source changed → CONFLICT, don't blindly apply (→ D17 policy); source now
  matches fix → fix redundant → retire.
- **Fetch-time recorded per value** (provenance/vintage; supports as-of D8 + change-detection). Fetch strategy =
  incremental for speed + PERIODIC FULL re-fetch/diff (incremental alone MISSES upstream corrections to old records;
  ties to OD-4 refetch + §12 reconciliation).

### D16 — overlay op vocabulary — ✅ CONFIRMED
The overlay needs **SET + DELETE-EVENT + ADD-EVENT + RECOMPUTE** — not SET-only. Required by OD-8/D15: you can't
remove a fake split (ROLEXRINGS triple-count) or add a missing one with SET alone. (`manual_overrides.csv` SET-only
shape was the limitation.)

### D17 — conflict policy when the source value has moved — ✅ DECIDED: Option B (HOLD for review)
On rebuild, compare current source value vs the fix's recorded old value:
- source still broken (= old value) → **apply fix** (automatic).
- source now matches the fix → **retire fix** as redundant (automatic).
- source moved to a THIRD value (≠ old, ≠ fix; e.g. yfinance refresh) → **CONFLICT → HOLD the row in dirty-review
  until owner re-confirms** (Option B). Do NOT auto-apply the old hand-fix (it may now be wrong).
- Rationale: conservative / flag-rather-than-guess / no silent override. Cost = review effort only (row stays
  flagged `dirty`, still usable via OD-7 views); fires rarely (only on a genuine unexpected move).
**Decision: TWO separate golden reference files (owner OK with two), authoritative + append-only + overlay-carried.**
1. **Corp-action events file** (`corp_action_external_evidence.csv` seed, 53 rows) — ISIN, ex-date, ratio,
   verified status → feeds PRICE ADJUSTMENT (D-1). Fill the 4-stock gap (D-cov-gap: SIKKO, RAJMET, MKPL, GICL).
2. **Identity-history file** — ISIN/symbol changes over time (renames, face-value-split ISIN changes) → feeds
   MATCHING/joins (design §10). Cross-references the corp-action file by ISIN.
3. **Cat-2 "do-NOT-correct" protected list** (67 ISINs) — verified-genuine crashes with NO unrecorded corp action
   → the corp-action fix checks this and NEVER fabricates a split-correction for them (added at §4 review).
- **Authoritative:** a hand-verified entry ALWAYS wins over scraped data.
- **Fallback order for any corp-action:** (1) golden catalog → (2) price-gap arbiter → (3) source-reconcile
  dedup → (4) unresolved → FLAG (never guess). Arbiter/human resolutions PROMOTE into the catalog (never re-litigated).
- **Status model:** verified / unverified-dirty / **upcoming** (the upcoming status is a SEAM designed now,
  populated later by the live task — see P-4).
- **Carried by the overlay** so a rebuild can't undo it.
- **MUST be mapped in P-2** (owner reminder): both files + what links to what go into the pre-development lineage map.
