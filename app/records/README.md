# app/records/ — structured signal records

These JSON files distill every tested signal/hypothesis into machine-readable records the app's Evidence Browser + Signal Registry render generically.
- `signals.json` — one record per tested signal/hypothesis/family-test (in-score components, validated display signals, watchlist, and the full graveyard).
- `families.json` — per-family rollups (mechanism, n_tested, n_validated, status).
They distill: `rules/index.md`, `docs/research/tier1_wave1_verdicts.md`, `docs/research/deep_hypotheses_2026-06.md`, `docs/research/hypothesis_batch_2026-06-06.md`, and `docs/research/context_signals_verdict.md`.
RULE: regenerate from the source docs; NEVER hand-edit the numbers (every stat must trace to a source doc).
