"""foundation/config.py — central control-plane config for the data-foundation rebuild.

ONE source of truth for:
  * OUTPUT_ROOT — where ALL rebuilt outputs are written (the single "where data goes" knob that makes
    build-beside-old -> compare -> swap trivial).
  * path helpers — raw/master/prices/reference/logs dirs, all under OUTPUT_ROOT.
  * time-partition boundaries — cohort / era splits, pulled out of hardcoded pipeline code.

BUILD vs SWAP
  During the rebuild, OUTPUT_ROOT defaults to 'data_build/' so fresh data lands BESIDE the frozen old
  'data/' (the Phase-7 reconciliation baseline). Final swap = set env IPO_OUTPUT_ROOT=data (or change the
  default below) and retire the old tree. Override at runtime with IPO_OUTPUT_ROOT.

INPUT vs OUTPUT
  INPUT_ROOT points at the frozen old 'data/' (read-only baseline). A re-fetch WRITES raw into OUTPUT_ROOT
  (data_build/raw/), it does NOT overwrite the frozen INPUT_ROOT. Code that must read the old baseline
  (e.g. the reconciliation diff) reads INPUT_ROOT explicitly.
"""
import os
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- THE knob: where outputs go ---------------------------------------------------
_DEFAULT_OUTPUT_ROOT = "data_build"      # beside the frozen 'data'; swap to 'data' at the end
OUTPUT_ROOT = (REPO_ROOT / os.environ.get("IPO_OUTPUT_ROOT", _DEFAULT_OUTPUT_ROOT)).resolve()

# --- frozen baseline (old data), read-only ----------------------------------------
INPUT_ROOT = (REPO_ROOT / os.environ.get("IPO_INPUT_ROOT", "data")).resolve()


# --- output path helpers (all under OUTPUT_ROOT) ----------------------------------
def out(*parts):
    """A path under OUTPUT_ROOT (the write root)."""
    return OUTPUT_ROOT.joinpath(*[str(p) for p in parts])


def raw_dir(source=None):
    """Raw scraped payloads. raw_dir() -> .../raw ; raw_dir('chittorgarh') -> .../raw/chittorgarh."""
    return out("raw", source) if source else out("raw")


def master_dir():
    return out("master")


def prices_dir():
    return out("prices")


def reference_dir():
    return out("reference")


def logs_dir():
    return out("logs")


def ensure(path):
    """Create a dir (or a file's parent dir) if missing; return the path. Honest mkdir helper."""
    p = Path(path)
    target = p if p.suffix == "" else p.parent
    target.mkdir(parents=True, exist_ok=True)
    return p


# --- input (frozen baseline) path helper ------------------------------------------
def src(*parts):
    """A path under INPUT_ROOT (the frozen old baseline, read-only)."""
    return INPUT_ROOT.joinpath(*[str(p) for p in parts])


# --- time-partition boundaries (pulled out of hardcoded pipeline/validation code) --
COHORT_BOUNDARY = date(2020, 1, 1)       # listing_date >= this -> 'boom'; before -> 'longterm'
COHORTS = ("boom", "longterm")
LONGTERM_RANGE = (date(2006, 1, 1), date(2019, 12, 31))
BOOM_RANGE = (date(2020, 1, 1), date(2026, 12, 31))


def cohort_of(listing_date):
    """Map a listing date to its cohort: boom if on/after COHORT_BOUNDARY, else longterm.

    listing_date must be a datetime.date (caller passes a real date; no guessing here).
    """
    return "boom" if listing_date >= COHORT_BOUNDARY else "longterm"


# Cross-regime validation = the cohort split itself: boom-era findings are validated against the longterm
# cohort (and vice versa). No random train/test split — small data + transparency (see CLAUDE.md).
