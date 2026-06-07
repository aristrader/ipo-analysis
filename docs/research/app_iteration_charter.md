# App-iteration charter — LOCKED (synthesized from 3 Phase-0 reports, 2026-06-07)

Inputs: `iteration_plan_thinker.md` (4-iter plan, walk-scripts, edge ISINs) ·
`iteration_plan_uxcritic.md` (L4 comprehension / L5 trust-legibility / L6 staleness lenses,
10 owner tasks) · `iteration_plan_codeprophet.md` (13 predicted bugs w/ repros, cache map).
Synthesis verdicts: thinker's isin_link P1 CONFIRMED by main session (links never carry the
ISIN); uxcritic's "MIN_N_HINT missing" claim FALSE (layer3/config.py:35) but per-screen floor
enforcement IS unverified; prophet's "board cards show pending" may be stale (main session
fixed the key lookup post-read) — walker must verify in-browser.

## LOCKED: 4 iterations, order = crash → truth → decide → feel
Tapered ceremony: iter 1 walker+full triage; iter 2-3 walker+self-triage; iter 4 self-walked.
Findings rubric: P0 exception · P1 wrong-info · P2 friction · P3 polish. Fix P0/P1 always;
P2 if cheap; P3 → owner improvement list. Suite green + commit per iteration.

### ITER 1 — BREAK-IT (+ error-recovery & staleness alarms from L6)
Walk: thinker's script §iter1 — edge ISINs delisted INE538H01016 / INE583L01014, longterm
no-GMP INE627H01017, unpriced INE1RQS01010, unreliable REIT INE2OVN25015, no-sector
INE0DRT01018; hostile params ?isin=garbage/empty/lowercase; every link on every screen.
Plus prophet's 13 repros (esp: refresh-doesn't-bust-caches #1, ?isin=garbage silent form #3,
unguarded predict #4, HOME graded undercount #5, board KeyError on partial board.json).
Known fixes to make: isin_link carries ?isin=; cache busting on refresh buttons
(st.cache_data.clear()); friendly not-found message; guard predict; graded = final+partial.
Tests deliverable (frontend-test policy): tests/app/test_ui_logic.py (chip/chip_status,
n_floor, formatters, win_flag — extract the dupe to ui.py, match_cond, find_live_call
extraction) + smoke key-content asserts.
EXIT: all P0/P1 fixed, zero raw tracebacks reachable, tests green.

### ITER 2 — DATA-HONESTY (numbers true + L5 trust-legibility)
Reconcile on-screen vs ground truth: Track-Record table vs run_calls --report; detail-page
scorecard vs predict() direct call; HOME counts vs ledger; board cards vs board.json; records
counts vs signals.json. Audit: chip mapping complete (no unknown-status fallthrough), min-N
floor enforced on EVERY stat (recommendations/track_record/ipo_detail — not just data.py),
distributions-over-means, mode splits never pooled, as-of stamps on every screen, rejected
ideas reachable ONLY in graveyard. EXIT: zero wrong numbers; every display rule verifiably held.

### ITER 3 — BE-THE-OWNER (journeys, findability, decision dominance)
The 10 uxcritic owner tasks w/ click budgets (apply-tomorrow ≤2 · why-AVOID ≤1 · define-alpha 0
· board-freshness 0 · partial-name find · why-crowded_window ≤3 · did-calls-work · show-a-
rejected-idea · score-new-SME · open-delisted). Decision DOMINANCE: on Recommendations the
verdict must be the visually loudest element (uxcritic re-scope). Findability: name search
must work from anywhere. EXIT: all 10 tasks within budget, verdict dominant.

### ITER 4 — FAST-AND-CALM (L4 comprehension + polish + latency)
Glossary discipline: every term a non-quant wouldn't know (alpha, P10/P90, quintile, MFE/MAE,
IC, counterfactual, gap_filled, capitulation, OOS) gets an inline gloss/tooltip at FIRST use
per screen — the "smart friend with zero context" test. Staleness ALARM (not passive stamp):
board >24h old or ledger grade-date >7d → colored warning banner. Empty-state copy human.
Warm-cache latency per page <3s (detail <6s). Hierarchy: one dominant element per screen.
EXIT: friend-test pass on all screens, no unexplained jargon, latency budget met.

## Carry-through rails
Sequential fixes only (no parallel edits on screens). No new features mid-iteration (owner
improvement list instead). Suite + verify.py before each commit. Retro line per iteration
amends the NEXT iteration's plan. CLAUDE.md "~2,296" stale count → fix to substrate_meta-
sourced wording during iter 2 (it's a data-honesty item).
