# Iteration plan — UX-critic (Phase 0, 2026-06-07)

Adversary on the seed's 3 starting lenses, for a SINGLE non-quant owner using a 7-screen Streamlit
research terminal (Home/Recommendations/IPO-Detail/Evidence/Registry/Track-Record/Data, :8597).
Grounding note: app already built under `app/screens/` (NOT `app/pages/` as the spec text says) —
the IA-vs-spec drift itself is a thing to walk.

## 1. What the seed's lenses MISS

The three seed lenses (BREAK-IT / BE-THE-OWNER / FAST-AND-CALM, + candidate DATA-HONESTY) are
sound but cover correctness and journeys, not COMPREHENSION and TRUST. Gaps:

- **Jargon undefined for a non-quant.** "alpha", "P10/P90", "quintile", "MFE/MAE", "rank-IC",
  "counterfactual", "gap_filled", "path_ratio", "barbell", "capitulation" all appear ON SCREEN with
  zero inline definition. BE-THE-OWNER assumes the owner already speaks quant. He doesn't — he asked
  for "simple plain language". MISSING LENS: every number/term must be hover/caption self-defining.
- **Trust-at-a-glance.** Chips exist, but is the AGGREGATE trust legible in 5 seconds? A page can be
  all-amber and look as confident as all-green. No lens checks "does the screen telegraph how much to
  believe it WITHOUT reading every chip".
- **Decision speed under a deadline.** "Hexagon closes tomorrow — apply?" is in BE-THE-OWNER but only
  as a click-count test. It misses: is the ANSWER (APPLY/AVOID) visually dominant, or buried under
  caveats? Under time pressure caveats must inform, not paralyze.
- **Stale-data visibility as ALARM, not caption.** Spec puts "as-of" everywhere as a passive stamp.
  Failure mode: board is 3 days old, owner acts on a closed IPO. A timestamp he must read ≠ an alert
  he can't miss. MISSING: staleness must escalate to a visible warning past a threshold.
- **Error recovery.** Wrong/unknown ISIN in `?isin=`, deleted price file, malformed query dict,
  `predict()` raising — BREAK-IT covers hostile DATA but not hostile INPUT and exceptions. Does the
  app show a friendly "ISIN not found — did you mean…" or a red Streamlit traceback?
- **Empty-state honesty UNDER LOAD.** Spec mandates "none right now" copy. But if board.json is the
  ONLY live source and it's empty/stale, Recommendations (the centerpiece) is a ghost town — is that
  honestly framed ("no live IPOs this week — here's the track record") or does it read as broken?
- **Cross-screen state coherence.** `predict()` query handed via session_state + switch_page; "applies
  to N live IPOs" link filters Recommendations. No lens checks that these handoffs survive a refresh,
  a back-button, or a deep-linked `?isin=`.

## 2. Proposed additions/changes to the iteration lenses

- **L4 — FIRST-5-MINUTES (smart-friend-zero-context).** Walk every screen as someone who has never
  read the docs. Every undefined term is a finding. Exit: no on-screen jargon without an inline
  plain-language gloss (tooltip/caption/expander). Highest-value new lens — directly serves the
  owner's "plain language" need.
- **L5 — TRUST-LEGIBILITY.** At-a-glance, can the owner tell a VALIDATED card from a THIN one without
  reading text? Check chip color contrast, a per-screen trust summary, and that the headline verdict's
  confidence is visually proportional. Fold candidate-4 DATA-HONESTY into here: numbers correct AND
  their confidence honestly telegraphed.
- **L6 — STALENESS & RECOVERY.** Drive stale board (edit fetched_at back 3d), missing ledger, bad
  ISIN, missing price file, empty board. Exit: staleness past N days shows a banner-level warning (not
  just a stamp); every failure yields a plain recovery message, never a traceback.
- Keep BREAK-IT / BE-THE-OWNER / FAST-AND-CALM but RE-SCOPE BE-THE-OWNER to score the
  PROMINENCE/READABILITY of the answer, not just click count.
- Ordering suggestion: iter1 = L4+L5 (comprehension/trust — most owner-impactful, drives the most
  copy/layout fixes early); iter2 = BREAK-IT + L6 (hostile data/input/staleness); iter3 = FAST-AND-CALM
  + BE-THE-OWNER journeys (polish + decision-speed) once content is trustworthy. Comprehension before
  speed: a fast wrong-belief is worse than a slow correct one.

## 3. The 10 most diagnostic OWNER TASKS (task → expected path → max clicks)

| # | Task (owner's words) | Expected path | Max clicks |
|---|---|---|---|
| 1 | "An IPO closes tomorrow — apply?" | Home → Recommendations → read OPEN card verdict | 2 |
| 2 | "Why does this say AVOID?" | (on card) [detail →] → IPO Detail ① verdict + rules_fired | 1 |
| 3 | "What does 'alpha' / 'P10' mean here?" | hover/caption on the number, same screen | 0 |
| 4 | "Is this board fresh or stale?" | glance at header strip on any DECIDE screen | 0 |
| 5 | "Find that IPO — name started with 'Hex…'" | Explorer/Detail search by partial name | 2 |
| 6 | "Why is crowded_window in the score?" | Registry → row → [Evidence] entry | 3 |
| 7 | "Did the APPLY calls actually work?" | Home → Track Record → table A (by mode) | 2 |
| 8 | "Show me a rejected idea and WHY" | Evidence → Graveyard → record → why-rejected panel | 3 |
| 9 | "Score a brand-new SME IPO I'm eyeing" | IPO Detail/Score form → submit → verdict | 2 |
| 10 | "Open a delisted/2006 no-GMP IPO" (edge) | `?isin=` deep-link → Detail degrades gracefully | 1 |

Each task is scripted as a playwright walk ("open X, click Y, expect Z-content"); failure = exceeds
max-clicks, raw traceback, undefined term with no gloss, or missing expected content.

## 4. Top 5 risks of VIOLATING the project's own display rules — where to look first

1. **min-N floor leaks a number.** Track Record table A/B and Detail ②/④ recompute at render — any
   group with `n < MIN_N_HINT` must read "N=k — too few", not a stat. LOOK: `app/screens/track_record.py`
   + `recommendations.py` aggregation; `ipo_detail.py` cluster/outcome cells. Grep for raw `mean()`/
   `median()` not guarded by an n-floor check. (Note: I found NO `MIN_N_HINT` in `config.py` — confirm
   where the floor constant actually lives before trusting it's enforced.)
2. **Lone mean without its median/distribution.** Spec: means never alone. LOOK: any `st.metric` or
   caption emitting a single average in Detail ②, Track Record, OOS card.
3. **Rejected idea reaching an action surface.** A REJECTED signal must appear ONLY in the graveyard,
   never as a call/playbook/recommendation. LOOK: `recommendations.py` (does it ever render a call whose
   rule_id is in the rejected set?), `ipo_detail.py` ⑦ playbooks filter, `registry.py` linking.
4. **Mode-split collapsed / pooled.** Track Record D chart and table MUST facet/split by
   `mode` (live vs historical_sim never one line). LOOK: `track_record.py` chart spec + groupby keys —
   easy to accidentally pool when n is thin.
5. **Chip mismatch / missing chip.** Every claim-bearing element carries exactly one of 4 chips; the
   status→chip map is the contract. LOOK: `app/ui.py` `chip()` mapping + each screen's call sites —
   a card rendered without a chip, or wrong color (e.g. TAKE_PROFITS/F10 must be ⚠ not ✓; combined
   score must be ~ not ✓; wipeout ✓). Cross-check against the seed's unit-test list (chip mapping is
   named as "yesterday's bug class").

---

## 10-line summary

1. Seed's 3 lenses cover correctness + journeys but MISS comprehension and trust legibility.
2. Biggest gap: undefined quant jargon (alpha/P10/quintile/MFE) on screen — owner wanted plain language.
3. Add L4 FIRST-5-MINUTES: a zero-context smart friend must understand every term/number.
4. Add L5 TRUST-LEGIBILITY: confidence must be visible at a glance, not chip-by-chip reading.
5. Add L6 STALENESS & RECOVERY: stale board must ALARM (not just stamp); bad ISIN must recover gracefully.
6. Re-scope BE-THE-OWNER to judge answer PROMINENCE under deadline, not just click count.
7. Recommend iter order: comprehension/trust → break-it/staleness → speed/journeys.
8. 10 diagnostic owner tasks scripted as task→path→max-clicks (apply-tomorrow, why-AVOID, define-alpha…).
9. Top display-rule risks: min-N leak, lone means, rejected-idea on an action surface, pooled modes, chip mismatch.
10. First places to look: track_record.py + recommendations.py aggregations, ipo_detail.py cells, app/ui.py chip map; confirm where MIN_N_HINT actually lives (not in config.py).
