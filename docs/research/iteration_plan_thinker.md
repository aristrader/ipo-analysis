# Iteration plan — THINKER (Phase 0, 2026-06-07)

Read: charter seed, app_screens_v1.md, app.py + app/screens/{home,recommendations,ipo_detail,evidence,registry,track_record,data}.py.
App runs at http://localhost:8597 (curl → HTTP 200). Substrate = data/master/ipo_analysis.csv, **2384 rows** (verify.py
invariant; CLAUDE.md's 2296 is stale — use 2384). I am the planner; I did NOT drive the browser.

## Proposed iteration set — I argue for **4**, not 3

The seed's 3 lenses (BREAK-IT, BE-THE-OWNER, FAST-AND-CALM) are sound but mis-ordered for this app's risk profile.
This is a single-user *research terminal* whose whole value proposition is "honest about uncertainty + numbers
correct." The biggest failure mode is therefore not friction or crashes — it's **a number that renders cleanly but
is wrong / mislabelled / mis-chipped** (a confidently-stated false statistic). That is exactly the candidate-4
DATA-HONESTY lens. It earns its own iteration because verifying numbers requires *cross-checking screen output
against the engine/ledger/CSV* — a different skill from walking links. I keep all 4; I do **not** add a 5th
(a11y/perf-deep would be gold-plating for a localhost tool). So: **4 iterations.**

Already-spotted hotspot (pre-walk, from reading code): `recommendations.py::isin_link()` calls
`st.page_link("app/screens/ipo_detail.py", …)` with **no `url=` and never passes the isin** → every "detail →" link
from the board/tracking/alerts lands on the bare lookup form, not the specific ISIN. Detail reads `?isin=` from
query params, but the links don't set it. This is the spine of journeys → seeded into Iter 1 & 2.

---

## ITERATION 1 — BREAK-IT (hostile / edge data)  ← run FIRST
**Why first:** find crashes/exceptions before journey or honesty work; a page that 500s makes later walks
meaningless. Full walker + full adversarial review (taper starts after this).

**Edge ISINs (real, from the substrate):**
- Delisted (liquidation, −100% terminal): `INE538H01016` (Shree Ashtavinayak Cine Vision, MB)
- Delisted, blank reason: `INE583L01014` (AGS Transact Technologies, MB)
- Longterm 2006 cohort, **no GMP**: `INE627H01017` (Cambridge Technology Enterprises, MB, 2006)
- listing_metrics_status = **blank/unpriced**: `INE1RQS01010` (Merritronix, SME)
- **unreliable_coverage** (must be excluded from listing reads): `INE2OVN25015` (Bagmane Prime Office REIT)
- SME **missing sector** (broad_sector + sector both blank): `INE0DRT01018` (Fabino Life Sciences, SME)

**Walk-script:**
1. navigate to `http://localhost:8597/` — wait for "Indian IPO Analysis"; confirm no Streamlit exception box.
2. navigate to `http://localhost:8597/ipo_detail?isin=INE538H01016` — expect a HEADER with the company name + a
   "① Verdict" section; expect delisting surfaced (terminal −100% / delisted badge) NOT a crash; screenshot.
3. navigate to `?isin=INE583L01014` — same; blank delist_reason must not render "None"/raw NaN.
4. navigate to `?isin=INE627H01017` — 2006 no-GMP: GMP/cluster sections must say "n/a" or "no data", never `nan`.
5. navigate to `?isin=INE1RQS01010` — unpriced SME: section ⑥ price chart must be hidden with "expected"/"no price
   file" copy, NOT an empty-axes Altair error.
6. navigate to `?isin=INE2OVN25015` — REIT/unreliable_coverage: listing-anchored reads excluded per convention;
   confirm no listing-pop number shown.
7. navigate to `?isin=INE0DRT01018` — SME no sector: scorecard/analog cohort renders; sector shows "unknown".
8. Hostile params: `?isin=` (empty), `?isin=NOTREAL99`, `?isin=INE538L01014%27`, `?foo=bar` — each must land on
   the lookup form or a clean "not found", never a traceback.
9. On every page in step 2–8 run a console-error / page-exception check (Streamlit red box, "KeyError",
   "ValueError", "nan"). Click the first "detail →" on Recommendations and note where it lands (expected bug).

**Exit criteria:** zero uncaught exceptions across all 8 edge ISINs + 4 hostile params; every degraded section shows
honest empty-state copy (no raw `nan`/`None`/`NaN`/empty-axes). All findings logged with ISIN + screenshot.

---

## ITERATION 2 — BE-THE-OWNER (the real journeys)  ← run SECOND
**Why second:** once nothing crashes, prove the *decision paths* work end-to-end. This is where the isin_link bug
bites hardest. Walker + lighter review (real/cosmetic/dupe).

**Walk-script:**
1. navigate to `http://localhost:8597/recommendations` — wait for "Live & upcoming board"; expect ≥1 call card OR
   an explicit "none right now". Note count of OPEN cards.
2. **Journey A — "an IPO closes tomorrow, apply?" in ≤2 clicks:** from the first OPEN card, read the call_type
   (APPLY/AVOID/NEUTRAL) + "why" inline; click its "detail →"; **expect to land on THAT ISIN's detail with a VERDICT
   bar** (not the bare lookup form). Record clicks-to-decision and whether the landed ISIN matches the card.
3. **Journey B — "why is crowded_window in the score?" in ≤3 clicks:** Home → Signal registry → find
   `crowded_window` row → click through to its Evidence Browser entry (Existence/Magnitude/Playbook tabs). Confirm
   the chain resolves in ≤3 clicks and the verdict is readable.
4. **Journey C — half-remembered name findability:** navigate to `/ipo_detail`, in "Search by name" type "Cambr"
   → expect Cambridge Technology in the list; pick it → lands on its detail. Repeat typing "fabino" (lowercase) →
   expect Fabino Life Sciences (case-insensitivity check).
5. From a TRACKING row and an ALERTS row, click "detail →" — same landing-correctness check as step 2.
6. On a detail page, use "← look up a different IPO" and confirm query params clear and the form returns.

**Exit criteria:** Journeys A/B/C each complete within their click budget AND land on the correct target. Any
"detail →" that drops the ISIN = **P1**. Search is case-insensitive and finds partial names.

---

## ITERATION 3 — DATA-HONESTY-ON-SCREEN (numbers correct, not just rendered)  ← run THIRD
**Why third:** needs a stable, navigable app (Iters 1–2 fixed). The hardest, highest-value lens for a research
terminal. Walker cross-checks 4–5 screen numbers against the engine/CSV (via python in Bash, not the browser).

**Walk-script:**
1. navigate to `?isin=INE627H01017` — read ② "the full picture" outcome buckets (Doubled+/Up/Flat/Down) + N + P90/
   median/P10. Cross-check: recompute that cohort's analog distribution against `predict()` / spine for the same
   query; the screen N and median must match (±rounding).
2. Confirm **every** statistic on that page shows N and respects MIN_N_HINT — any cohort below the floor must read
   "too few — N=k", never a bare number. Test with the thin SME `INE0DRT01018`.
3. Chip audit: each claim-bearing element carries exactly one of the four chips (✓/~/⚠/✗); combined-score = `~`,
   wipeout-risk = `✓`, EARLY_*/TAKE_PROFITS = `⚠`. No REJECTED (`✗`) signal appears on any action surface (only the
   Evidence graveyard). Cross-check chip mapping against app/ui.py `chip()`.
4. navigate to `/track_record` — section A: spot-check one call_type×mode cell's n + win% by re-aggregating
   `data/master/calls_ledger.csv` in python; numbers must match (acceptance rule: recomputed at render, never
   hardcoded). Confirm mode-split is present (live/gap_filled/backfilled/historical_sim never pooled).
5. "As-of" stamps present on Home/Recommendations/Track (substrate AS_OF_DATE, ledger graded_at max, board
   fetched_at). Confirm no stamp says a future/empty date.
6. Means-vs-distributions: confirm no lone mean is shown without a median beside it.

**Exit criteria:** every spot-checked screen number reconciles with engine/CSV within rounding; min-N floor honored
everywhere; chip mapping 100% correct with no rejected signal on an action surface; as-of stamps real.

---

## ITERATION 4 — FAST-AND-CALM (latency, wording, hierarchy, consistency)  ← run LAST
**Why last:** polish only matters once correct + navigable + honest. Likely self-triaged (taper end-state).

**Walk-script:**
1. Cold-load each of the 7 screens once; note perceived latency + whether `@st.cache_data` warms the second visit
   (revisit Home → Recommendations → Home; second Home should be instant).
2. Wording pass: scan every screen for jargon that a tired owner can't parse cold (e.g. "path_ratio",
   "anchor unlock", "rank-IC") — each must have a one-liner or plain gloss nearby.
3. Hierarchy: on Recommendations and IPO Detail, confirm the decision (call_type / verdict) is the most visually
   prominent element, not buried under metadata.
4. Chip-consistency: same status → same glyph/colour/wording on every screen (cross-check Home vs Recommendations
   vs Registry vs Evidence).
5. Empty states read calm and human ("none right now", "nothing needs attention"), never blank padding or a spinner
   that never resolves.

**Exit criteria:** no screen feels broken-slow on warm cache; no un-glossed jargon on a decision surface; decision
is the visual focal point; chips identical across screens; all empty states are the spec's copy.

---

## Severity rubric (all iterations)
- **P0 — exception/blocker:** uncaught traceback, page won't render, app crash, a REJECTED signal shown as an action.
- **P1 — wrong information:** wrong/mislabelled number, wrong chip, link lands on wrong ISIN, stale/false as-of,
  min-N floor violated, raw `nan`/`None` shown as if it were data.
- **P2 — friction:** journey exceeds its click budget, search misses an obvious name, confusing wording on a
  decision surface, missing honest empty-state.
- **P3 — polish:** spacing, latency on a non-critical page, minor copy, chip cosmetic drift.

## Order rationale (one line)
**1 BREAK-IT → 2 BE-THE-OWNER → 3 DATA-HONESTY → 4 FAST-AND-CALM:** don't-crash before can-decide before
numbers-true before feels-good — each gate presupposes the previous one passed; honesty before polish because a
pretty wrong number is the worst outcome for a research terminal.
