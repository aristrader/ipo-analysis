# auto_memory/ — verbatim copy of the assistant's persistent memory

These four files are copied from `~/.claude/projects/.../memory/` (which lives OUTSIDE the repo and would
NOT travel to a new account). They are the assistant's cross-session memory for this project.

⚠ **Some content is HISTORICAL, not current.** In particular `project_ipo_state.md` records the early
rebuild (e.g. "1269 IPOs / 382 mainboard") which PREDATES the expansion to ~2,384 rows; it even says so
("CLAUDE.md is now the live brain — it supersedes the stale bits above"). **For current truth always use the
in-repo `CLAUDE.md` / `STATUS.md` / `rules/index.md`.** Treat these files as context + the durable lessons:
- `execution-pipeline-mandate.md` — the owner's standing way-of-working (full pipeline + independent review). STILL LIVE.
- `project_ipo_state.md` — the rebuild story, data lessons (ISIN-key, renames, BSE numeric .BO), movement-lens philosophy.
- `ticker-validation-price-source.md` — why Yahoo can't cover SME → bhavcopy is the Layer-2 price source. STILL LIVE.
- `MEMORY.md` — the index of the above.

To rehydrate memory on a new account: a fresh session can re-create equivalent memory files from these +
from `CLAUDE.md`, or just rely on the in-repo brain (which is more current anyway).
