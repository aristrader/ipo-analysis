# Rules Registry — the single navigable home for every rule / predicate / score-component / strategy

Goal: a human- AND AI-navigable registry so anyone (or any future AI) can see, at a glance, every pattern we
test, its exact logic, whether it held up, and where it came from — and add new ones in a consistent format.

## How it's organized
- **`rules/index.md`** — the master table (id · name · type · status · priority · result · file). Start here.
- **`rules/<id>.md`** — one structured file per rule (template below). id format: `<type>-<area>-<n>`,
  e.g. `pred-anchor-unlock`, `desc-survival-baserate`, `strat-flip-listing`, `score-multibagger-odds`.
- Categories (the `type` field): `descriptive` (a reported truth) · `predicate` (a conditional pattern, "IF X THEN
  outcome distribution") · `score-component` (a scorecard dimension) · `strategy` (a backtestable rule).

## Per-rule template (copy this for each new rule)
```yaml
id:            pred-anchor-unlock
name:          Anchor lock-in unlock dip
type:          predicate            # descriptive | predicate | score-component | strategy
status:        hypothesis           # hypothesis | validated | rejected | retired
priority:      high                 # high | med | low
source:        strategies.md#T4     # where the idea is catalogued
plain:         "Around the anchor lock-in expiry date, do prices show an abnormal dip as anchors sell?"
logic:         "event-study: alpha & volume in window [unlock_date-3, +5]; split by SEBI regime (pre/post Sep-2021)"
features_used: [anchor_lockin_expiry, anchor_allocation, daily prices, liquidity_flag, market_cap_class]
cohorts:       [boom, longterm]     # which cohorts it applies to
guardrails:    [min_N>=30, SME-split, liquidity-gate, placebo-window, cross-regime]
result:        ""                   # filled after backtest: lift / hit-rate / N / cross-regime stability
last_updated:  ""
```

## Conventions (so it stays trustworthy + machine-readable)
- Every rule states its **guardrails** (min-N, SME/Mainboard split, survivorship, liquidity, cross-regime) per
  `docs/strategies.md` §0 method spine.
- `status` lifecycle: **hypothesis** → (backtested) → **validated** (held cross-regime, N≥floor) or **rejected**.
- `result` records the actual numbers (lift/hit-rate/sample-size/cross-regime), so score-component WEIGHTS can be
  derived transparently from validated rules' lift (see `docs/layer3.md` — data-informed scoring).
- When a rule is implemented in code, link the script + the output column it produces.
- Keep `index.md` in sync (it's the table of contents an AI reads first).

## Status
Registry scaffolded; rules get populated as Layer 3 is built (Part A reports → predicates → score-components →
strategies), seeded from the prioritized catalog in `docs/strategies.md`. See `CLAUDE.md` for the project map.
