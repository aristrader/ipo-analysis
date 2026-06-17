# `foundation/` — the rebuilt data foundation (plain-language guide)

This is the new, **clean / honest** core of the IPO dataset.
"Honest" means two things, enforced everywhere:

1. **Never invent a value.** If a source gives no number, we store *empty* (`None`) — never a fake `0`.
2. **Never lose the source's answer.** Every scraper saves the *raw* downloaded page before parsing it,
   so the data can always be re-processed offline.

It's built **beside** the old data, not on top of it — so we can compare, then swap.

---

## The pieces (read in this order)

| File | In one line | What it gives you |
|---|---|---|
| **`config.py`** | "Where does data go?" | One knob (`OUTPUT_ROOT`) — during the rebuild everything writes to `data_build/`; at the end you flip it to `data/`. Also the cohort/era date boundaries. |
| **`ingest.py`** | The honesty toolkit | `fetch()` tells apart success / site-failed / no-data; `save_raw()` keeps the original; `num()/text()/…` parse without ever minting a fake value. Every scraper uses these. |
| **`registry/columns.yaml`** | The column catalog | A plain, editable list of **every** column — its type, source, how it's parsed/validated, whether it's at-IPO vs current, its lifecycle. The dataset's self-describing schema. |
| **`registry/__init__.py`** | The catalog's loader + checker | Loads `columns.yaml`, maps parser/validator *names* to real functions, and validates the file each run (catches typos, bad values, duplicates). |
| **`refetch.py`** | The "pull everything" runner | Runs every scraper in order into `data_build/`, writing a **live progress file** you can watch. |

---

## How the data flows

```
scrapers/  (use ingest)        foundation/registry         (later phases)
   pull raw  ───────────►  save raw + parsed  ──guided by──►  assemble the spine
                            into data_build/      columns.yaml
```

## The big idea: build beside old, then swap

- The old `data/` stays **frozen** = the baseline we compare against.
- The new data is built in **`data_build/`** (set by `config.OUTPUT_ROOT`).
- We compare new-vs-old, then **swap** (one config flip) and retire the old.

## Run the full re-fetch + watch it

```bash
PYTHONPATH=. .venv/bin/python foundation/refetch.py            # pull everything (background-friendly)
cat data_build/logs/REFETCH_STATUS.txt                         # live: which step is done / running / pending
tail -f data_build/logs/<step>.log                             # full detail for one step
```

## Status

Phase 0 is done — `config`, `ingest` + honest scrapers, and the column `registry` are built, and a full
honest re-fetch has run. Next is **Phase 1 (provenance / missing-data)**.
The full plan + decisions live in `docs/research/FOUNDATION_PLAN.md`; the design reference is
`docs/research/FOUNDATION_ARCHITECTURE.md`.
