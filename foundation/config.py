"""foundation/config.py — the ONE place that decides where data lives and how time is sliced.

Quick reference
---------------
    from foundation import config

    config.OUTPUT_ROOT          # where everything we BUILD is written  (default: <repo>/data_build)
    config.INPUT_ROOT           # the frozen OLD data, read-only         (default: <repo>/data)

    config.raw_dir("screener")  # -> OUTPUT_ROOT/raw/screener      (a source's scraped payloads)
    config.master_dir()         # -> OUTPUT_ROOT/master            (the assembled outputs)
    config.prices_dir()         # -> OUTPUT_ROOT/prices
    config.reference_dir()      # -> OUTPUT_ROOT/reference
    config.logs_dir()           # -> OUTPUT_ROOT/logs
    config.src("master", "x")   # -> INPUT_ROOT/master/x           (read the frozen baseline)
    config.ensure(path)         # mkdir -p for a dir or a file's parent; returns the path

    config.cohort_of(listing_date)   # -> "boom" | "longterm"

Why this file exists
--------------------
Paths used to be hardcoded ('data/raw/...') in every script. That made "build the new dataset
beside the old one, compare, then swap" painful. Now there is a single knob:

    BUILD phase  : OUTPUT_ROOT = data_build/   → fresh data lands BESIDE the frozen data/ (the
                   reconciliation baseline). Override per-run with the env var IPO_OUTPUT_ROOT.
    SWAP (at end): point OUTPUT_ROOT back at data/ (set IPO_OUTPUT_ROOT=data, or change the default
                   below) and retire the old tree.

Reads vs writes: a re-fetch WRITES into OUTPUT_ROOT; it never overwrites INPUT_ROOT. Code that needs
the frozen baseline (e.g. the reconciliation diff) reads it explicitly via config.src(...).
"""
import os
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# 1. THE ROOTS  (the only knobs — everything else is derived from these)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_OUTPUT_ROOT = "data_build"   # build beside the old data/; flip to "data" at the swap

# Where we WRITE (overridable per-run with IPO_OUTPUT_ROOT).
OUTPUT_ROOT = (REPO_ROOT / os.environ.get("IPO_OUTPUT_ROOT", _DEFAULT_OUTPUT_ROOT)).resolve()

# The frozen OLD data — read-only baseline (overridable with IPO_INPUT_ROOT).
INPUT_ROOT = (REPO_ROOT / os.environ.get("IPO_INPUT_ROOT", "data")).resolve()


# ─────────────────────────────────────────────────────────────────────────────
# 2. OUTPUT PATHS  (everything we build, under OUTPUT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────
def out(*parts):
    """A path under OUTPUT_ROOT, e.g. out('master', 'x.csv')."""
    return OUTPUT_ROOT.joinpath(*[str(p) for p in parts])


def raw_dir(source=None):
    """Scraped payloads. raw_dir() -> .../raw ; raw_dir('chittorgarh') -> .../raw/chittorgarh."""
    return out("raw", source) if source else out("raw")


def master_dir():
    """The assembled outputs (spine, universe, returns, ...)."""
    return out("master")


def prices_dir():
    """Per-ISIN daily price files."""
    return out("prices")


def reference_dir():
    """Reference data (corp actions, indices, bhavcopy cache, ...)."""
    return out("reference")


def logs_dir():
    """Run logs."""
    return out("logs")


# ─────────────────────────────────────────────────────────────────────────────
# 3. INPUT PATHS  (the frozen old baseline, read-only)
# ─────────────────────────────────────────────────────────────────────────────
def src(*parts):
    """A path under INPUT_ROOT, e.g. src('master', 'ipo_analysis.csv')."""
    return INPUT_ROOT.joinpath(*[str(p) for p in parts])


# ─────────────────────────────────────────────────────────────────────────────
# 4. SMALL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def ensure(path):
    """mkdir -p for a directory (or a file's parent dir). Returns the path unchanged."""
    p = Path(path)
    target = p if p.suffix == "" else p.parent
    target.mkdir(parents=True, exist_ok=True)
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 5. TIME PARTITIONS  (cohort/era boundaries — pulled out of hardcoded pipeline code)
# ─────────────────────────────────────────────────────────────────────────────
COHORT_BOUNDARY = date(2020, 1, 1)              # listing on/after this = "boom", before = "longterm"
COHORTS = ("boom", "longterm")
BOOM_RANGE = (date(2020, 1, 1), date(2026, 12, 31))
LONGTERM_RANGE = (date(2006, 1, 1), date(2019, 12, 31))


def cohort_of(listing_date):
    """Map a real datetime.date to its cohort: "boom" if on/after COHORT_BOUNDARY, else "longterm".

    Caller passes an actual date — this never guesses one.
    """
    return "boom" if listing_date >= COHORT_BOUNDARY else "longterm"


# Cross-regime validation = the cohort split itself: a boom-era finding must also hold on the longterm
# cohort (and vice versa). No random train/test split — small data + transparency (see CLAUDE.md).
