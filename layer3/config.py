"""Layer-3 configuration constants. Single source for floors, horizons, exclusions."""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBSTRATE = ROOT / "data/master/ipo_analysis.csv"
REPORT_DIR = ROOT / "report"

# The substrate's AS-OF / build date — maturity-gating in the dataset (pipeline/07_returns_summary.py
# TODAY) is anchored here, and age/survival findings (findings/t2_survival.py) MUST use the same date
# so they stay consistent with the gating. (NOT date.today(): the substrate is frozen at build time,
# so a live date would desync findings from the data.)
# SINGLE SOURCE: data/master/substrate_meta.json — written ONLY by `run_refresh.py --apply`, which
# rebuilds the substrate in the same run. The literal below is the pre-meta fallback.
SUBSTRATE_META = ROOT / "data/master/substrate_meta.json"


def _as_of_from_meta():
    import json
    try:
        meta = json.loads(SUBSTRATE_META.read_text())
        return date.fromisoformat(meta["as_of"])
    except (OSError, KeyError, ValueError):
        return date(2026, 5, 31)


AS_OF_DATE = _as_of_from_meta()

# the dead-money cutoff (alive but ≥50% below issue & illiquid = un-exitable zombie) — used by the
# zombie finding, the wipeout anatomy, and the risk gauge; one source so they can't drift apart.
DEAD_MONEY_RETURN = -0.50

# min-N floors (method spine §6)
MIN_N_TRADABLE = 30      # N>=30 -> a tradable claim
MIN_N_HINT = 10          # 10<=N<30 -> a directional hint; else "insufficient"

HORIZONS = ["1d", "1w", "1m", "3m", "6m", "1y", "2y", "3y", "5y", "10y"]
# Long horizons are carried by the LONGTERM cohort (boom is maturity-gated, tiny N).
# Findings reporting these default to longterm-only to avoid a cohort-swap "trend".
LONG_HORIZONS = ["3y", "5y", "10y"]
KEY_HORIZONS = ["1y", "3y", "5y"]        # the headline set most findings report

CORE_INSTRUMENT = "equity"               # core IPO analysis excludes fpo/reit/invit
SEGMENTS = ["MB", "SME"]
COHORTS = ["boom", "longterm"]
MCAP_ORDER = ["micro", "small", "mid", "large"]

# listing-pop (T3) analyses use only trustworthy listing-day metrics
TRUSTED_LISTING_STATUS = ["ok", "inferred_split", "recovered_bhavcopy"]
EXCLUDE_LISTING_STATUS = ["unreliable_coverage"]

# benchmark policy: small/micro caps use Smallcap-250 alpha where available (2017+),
# else fall back to Nifty-50. Mid/large always Nifty-50.
SMALLCAP_MCAP = ["micro", "small"]


def n_tier(n: int) -> str:
    if n >= MIN_N_TRADABLE:
        return "tradable"
    if n >= MIN_N_HINT:
        return "hint"
    return "insufficient"
