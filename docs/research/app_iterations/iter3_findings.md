# Iteration 3 — BE-THE-OWNER findings (2026-06-07)

Walker: iter-3 owner-walk (smart retail investor, not a quant), app @ :8597, all iter-1/2 fixes live.
Method: every task started from HOME, clicks counted, hesitation noted. Self-triaged (P1/P2/P3 ·
FIX-NOW vs IMPROVEMENT). Streamlit dataframes render to canvas (not in a11y tree) so registry/
track-record/comparable TABLES were read via screenshots; their CONTENTS are present and correct.

## Per-task results

### Task 1 — "Hexagon Nutrition closes tomorrow — should I apply?" · budget ≤2 · USED 2 · PASS
Home → "Open Recommendations" → Hexagon is the FIRST OPEN card. call: **EARLY_AVOID** with
why-string (live_score=29.2;n14_flags=1;day_n=3;gmp=22.22;sub=1.65) + "closes in 2d · sub 1.65× ·
GMP 22.22%". Answer reachable in budget.
Friction: (a) the call sits inline at the SAME visual weight as the company name, no color, no badge —
see DOMINANCE finding below; (b) the why-string is raw jargon (live_score / n14_flags / day_n) — an
owner can't decode WHY it's an avoid without help (iter-4 gloss scope, but it weakened the decision
here so noting it); (c) "detail — no ISIN yet" means Hexagon has NO drill-in (it's pre-substrate) — so
Task 2's "1 click to why" is impossible for THIS name specifically.

### Task 2 — "Why is this marked AVOID?" · budget ≤1 · USED 0 (on-card) / 1 (substrate detail) · PASS
The why is printed ON the card (0 clicks) — for Hexagon it's the live_score/flags string. For a
SUBSTRATE name (e.g. Aureate, opened from a Tracking "detail →"), IPO Detail ① Verdict shows
"Ledger call: AVOID ✓ VALIDATED · fired 2026-06-02 · why: score_q=1;n14_flags=1" in 1 click.
Friction: same jargon-only "why" (score_q, n14_flags). Plain-language reason is absent — owner sees
the codes, not "few buyers / loss-making / obscure banker".

### Task 3 — "What does 'alpha' mean here?" · budget 0 · PASS
Persistent sidebar caption on EVERY screen: "Returns = alpha vs Nifty 50, from the listing price."
0 clicks, present everywhere. (Deeper terms P10/P90/MFE are glossed via "Help for…" tooltips on the
detail page — good. Body-text jargon like score_q is still ungloss­ed → iter-4.)

### Task 4 — "How fresh is this board data?" · budget 0 · PASS
Header strip on Recommendations + Home + Track Record: "ledger graded to 2026-06-07 · board fetched
2026-06-07T18:29:17". Visible without any action. (Note: it's a passive STAMP, not an alarm — iter-4
L6 wants escalation past a threshold; data is fresh today so not triggered.)

### Task 5 — "Find that SME 'Aureate something'" · budget (find) · USED 2 · PASS
IPO Detail → "Search by name" combobox → type "Aureate" → top match "Aureate Tradde Ltd. (SME,
INE1KVL01010)" selected → click navigates to ?isin=. Partial-name findable.
Friction: fuzzy search also surfaces loosely-related names (Apeejay, Dhanuka, Samruddhi) above some
closer ones, but the exact prefix match ranks #1, so harmless.

### Task 6 — "Why is crowded_window in the score?" · budget ≤3 · USED 2 · PASS
Evidence → pick family "F2 wallet-competition / context" → record "Crowded IPO window
(ctx_ipo_heat_90d) ✓ VALIDATED": Mechanism + Verdict "FOLDED into the data-informed score after
passing the OOS fold gate (5/5 splits improved, +10..+56pp). NEGATIVE in all 4 regime cells
(rank-IC -0.13..-0.26)…". Fully answers the question.
Friction: (a) NO link from the Registry row "Crowded IPO window" to its Evidence record — owner must
know to go to Evidence and hunt the F2 family themselves (cross-surface gap); (b) in Registry table ①
the evidence/why columns are cut off to the right (horizontal scroll needed); (c) the Evidence record's
"Link to heading" anchor is STALE — still points to #banker-prior-alpha… from the previously-selected
record.

### Task 7 — "Did the system's calls actually work?" · USED 2 · PASS (with honesty caveat)
Home → Track Record → tab "Call track record": Table A splits call_type × mode; Chart D faceted by
mode (backfilled vs historical_sim — never pooled); thin rows read "N=0 — too few to say" (min-N floor
holds). Mode legend present.
Owner-truth finding (NOT a bug — honest framing): there is NO live / gap_filled (real forward) data
yet. The only populated mode is historical_sim (dress rehearsal, APPLY 53% win N=175) + backfilled
(N=0). So the honest answer is "the real forward record is still empty; what you see is a dress
rehearsal." The owner CAN read the mode split, but the page does not loudly headline "no live calls
have matured yet" — a casual owner could mistake the 53% historical_sim row for a real track record.

### Task 8 — "Show me something tested and REJECTED" · budget ≤3 · USED 2-3 · PASS
Two paths: (a) Evidence Browser families carry ✗ counts (e.g. Batch demand/allocation ✗8); selecting
a ✗ record exposes a "WHY REJECTED" tab with the verdict text (e.g. Banker prior alpha: "MIXED/WEAK…
subsumed by the in-score obscure-banker flag"). (b) Registry ③ GRAVEYARD section. Reachable +
informative. Rejected ideas correctly never appear on action surfaces (confirmed on detail ⑦:
"Rejected ideas never appear here").

### Task 9 — "Score a hypothetical new SME IPO" · USED ~3 · PASS
IPO Detail → set Type=SME → fill issue size 50 / sub 3 / revenue 80 → "Score it →" → full read for
"New IPO · SME": ① COMBINED 69/100 ~DISPLAY-ONLY, WIPEOUT-RISK 42/100 🟢 LOW ✓VALIDATED + analogs +
scorecard + playbooks. End-to-end journey works.
Friction: ~13 input fields, all default 0/unknown; mitigated by "Leave a field at 0/'unknown' if you
don't have it — it's dropped, not assumed." Acceptable but a bit form-heavy for a non-quant.

### Task 10 — "Open a delisted IPO (Ashtavinayak)" · budget ≤1 · USED 1 · PASS
?isin=INE538H01016 → "Shree Ashtavinayak Cine Vision Ltd. · MB · listed 2007-01-10". ① Verdict
dominated by a RED banner: "💀 DELISTED — WIPEOUT (realized). Compulsory delisting/liquidation;
terminal value −100%. Everything below is the historical read of what led here." + "no APPLY/AVOID/
NEUTRAL call on file for this ISIN." Also findable BY NAME (type "Ashtavinayak" → sole match).
Best-handled edge case of the walk — verdict here IS dominant (red, large, top).

## Dominance check (Recommendations cards)
FAIL (soft). On each OPEN/Tracking/Alert card the call (EARLY_AVOID / EARLY_APPLY / etc.) is rendered
as a **bold inline word at the same font size and same black color as the company name**, on the same
row. There is NO color coding (AVOID is not red, APPLY is not green), no large verdict badge. The
loudest visual element on the card is arguably the amber "⚠ THIN / HYPOTHESIS" chip, not the verdict.
Contrast with the IPO-Detail delisted banner (Task 10), which IS dominant (red, boxed, top). The
decision is legible but NOT the visually loudest element on the recommendation cards — caveats/chips
compete with it.

## Cross-screen detail reachability
Mostly GOOD: Tracking + Alerts rows each carry a "detail →" link to ?isin=. IPO Detail search reaches
any substrate name. Gaps:
- OPEN/UPCOMING live-board cards (Hexagon, Genxai, Vahh, UHM, Horizon) have NO detail link ("no ISIN
  yet") — correct (pre-substrate) but means the centerpiece DECIDE cards are dead-ends for drill-in.
- Registry rows (e.g. crowded_window) do NOT link to their Evidence record (Task 6 gap).
- "detail →" links open in a NEW TAB (target=_blank) → tab sprawl; owner loses the list context and
  back-button doesn't return him. Friction across the whole app.

## Findings list (self-triaged)

| # | Finding | Sev | FIX-NOW / IMPROVEMENT |
|---|---|---|---|
| F1 | Verdict not visually dominant on rec cards (no color/badge; same weight as name; chip louder) | P2 | IMPROVEMENT (layout/color decision) |
| F2 | "detail →" links open in a new tab (target=_blank) → tab sprawl, lost context, broken back-button | P2 | FIX-NOW (drop target=_blank) |
| F3 | No live/gap_filled track record yet; historical_sim 53% row could be mistaken for a real record — not headlined as "no matured live calls" | P2 | IMPROVEMENT (add an honest empty-state headline above Table A) |
| F4 | Registry rows have no link to their Evidence record (crowded_window etc.) | P2 | IMPROVEMENT (add per-row evidence link) |
| F5 | Why-strings are raw jargon (score_q, n14_flags, live_score) — no plain-language reason for AVOID/APPLY | P2 | IMPROVEMENT (mostly iter-4 gloss; weakened Tasks 1-2) |
| F6 | Evidence record "Link to heading" anchor is stale (points to previously-selected record's slug) | P3 | FIX-NOW (compute anchor from current record) |
| F7 | Registry table ① evidence/why columns cut off to the right (need horizontal scroll) | P3 | FIX-NOW (widen / reorder columns) |
| F8 | Live-board OPEN cards (the DECIDE centerpiece) are drill-in dead-ends (no ISIN) | P3 | IMPROVEMENT (acknowledged data limitation) |
| F9 | HOME shows "2,329 IPOs" vs CLAUDE.md "~2,296" — stale-count copy already flagged for iter-2 | P3 | (iter-2 item) |
| F10 | Score form is 13 fields, all defaulting 0/unknown — heavy for a non-quant (mitigated by caption) | P3 | IMPROVEMENT |

Note: console showed 2 errors on every page — both are benign Streamlit `_stcore/health` +
`host-config` 404s on deep-linked tabs, NOT app exceptions. Vega chart warnings are cosmetic. No P0/P1
wrong-info found.
