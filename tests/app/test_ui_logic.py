"""Frontend LOGIC tests (the agreed policy: logic gets tests, layout gets walked).
Targets app/ui.py pure functions — the part of the frontend that can lie:
chip mapping, min-N floor, formatters, predicate matching."""
import math

import pytest

from app import ui


# ---------------------------------------------------------------- chips
def test_chip_status_canonical_keys_pass_through():
    for k in ("validated", "display", "thin", "rejected"):
        assert ui.chip_status(k) == k


def test_chip_status_aliases_and_unknowns_never_crash():
    # every record status in app/records/signals.json must map somewhere sane
    assert ui.chip_status("in_score") in ("validated", "display", "thin", "rejected")
    assert ui.chip_status("IN-SCORE") in ("validated", "display", "thin", "rejected")
    assert ui.chip_status("watchlist") in ("validated", "display", "thin", "rejected")
    assert ui.chip_status("parked") in ("validated", "display", "thin", "rejected")
    # unknown / None / garbage -> safe fallback, never KeyError
    assert ui.chip_status("totally_new_status") == "display"
    assert ui.chip_status(None) == "display"
    assert ui.chip_status("  Display Only ") == "display"


def test_chip_renders_html_for_every_records_status():
    import json
    statuses = {r.get("status") for r in json.load(open("app/records/signals.json"))}
    for s in statuses:
        html = ui.chip(s)
        assert html.startswith("<span") and "</span>" in html


def test_rejected_chip_is_visually_distinct():
    assert ui.chip("rejected") != ui.chip("validated")


# ---------------------------------------------------------------- min-N floor
def test_n_floor_blocks_below_hint():
    assert ui.n_floor(ui.MIN_N - 1) is not None
    assert "too few" in ui.n_floor(0)


def test_n_floor_allows_at_and_above_hint():
    assert ui.n_floor(ui.MIN_N) is None
    assert ui.n_floor(500) is None


def test_n_floor_handles_garbage():
    assert ui.n_floor(None) == "N unknown"
    assert ui.n_floor("abc") == "N unknown"
    assert ui.n_floor(float("nan")) is not None     # nan -> unknown/too-few, never a pass


# ---------------------------------------------------------------- rate_with_ci (Fix B)
def test_rate_with_ci_below_full_floor_suppresses_point():
    # n < MIN_N_FULL -> NO point estimate, "too few", band may still trail
    s = ui.rate_with_ci(0.67, ui.MIN_N_FULL - 1, 0.20, 0.95)
    assert "too few to say" in s
    assert f"N={ui.MIN_N_FULL - 1}" in s
    assert "67%" not in s          # the point estimate must be gone
    assert "[20–95%]" in s         # but the honest band can show


def test_rate_with_ci_at_and_above_full_floor_shows_fused_point_and_band():
    s = ui.rate_with_ci(0.67, ui.MIN_N_FULL, 0.20, 0.95)
    assert s == "67% [20–95%]"     # point and band fused, inseparable
    s2 = ui.rate_with_ci(0.5, 100, 0.4, 0.6)
    assert s2 == "50% [40–60%]"


def test_rate_with_ci_missing_band_still_works():
    # above floor but no CI computed -> just the point
    assert ui.rate_with_ci(0.5, 100, None, None) == "50%"
    # below floor, no band -> bare "too few"
    s = ui.rate_with_ci(0.5, 3, None, None)
    assert s == "too few to say (N=3)"


def test_rate_with_ci_handles_garbage():
    assert ui.rate_with_ci(0.5, "abc", 0.1, 0.9) == "—"      # bad n
    assert ui.rate_with_ci(None, 100, None, None) == "—"     # above floor but no point


# ---------------------------------------------------------------- name resolver (Fix E)
def test_resolve_label_to_isin_basic():
    opts = {"Acme Ltd (MB, INE000A01001)": "INE000A01001",
            "Beta Co (SME, INE000B01002)": "INE000B01002"}
    assert ui.resolve_label_to_isin("Acme Ltd (MB, INE000A01001)", opts) == "INE000A01001"


def test_resolve_label_to_isin_sentinel_and_unknown():
    opts = {"Acme Ltd (MB, INE000A01001)": "INE000A01001"}
    assert ui.resolve_label_to_isin("(choose)", opts) is None
    assert ui.resolve_label_to_isin("", opts) is None
    assert ui.resolve_label_to_isin(None, opts) is None
    assert ui.resolve_label_to_isin("Not A Real Label", opts) is None


def test_name_options_unique_by_isin_and_skips_missing():
    import pandas as pd
    df = pd.DataFrame([
        {"company_name": "Acme Ltd", "type": "MB", "isin": "INE000A01001"},
        {"company_name": "Acme Ltd", "type": "SME", "isin": "INE000A01002"},   # same name, diff ISIN
        {"company_name": "NoIsin Co", "type": "MB", "isin": None},             # dropped
    ])
    opts = ui.name_options(df)
    assert len(opts) == 2                       # both Acmes kept (labels differ by ISIN), no-ISIN dropped
    assert set(opts.values()) == {"INE000A01001", "INE000A01002"}


# ---------------------------------------------------------------- formatters
@pytest.mark.parametrize("fn", [ui.money, ui.frac, ui.pct, ui.pct_pp])
def test_formatters_never_crash_on_none_or_nan(fn):
    assert fn(None) == "—"
    assert fn(float("nan")) == "—"


def test_money_scales():
    assert ui.money(54.27) == "₹54 cr"
    assert "k cr" in ui.money(12000)
    assert ui.money("garbage") == "—"


def test_frac_vs_pct_units_are_distinct():
    # frac takes 0.12, pct takes 12.0 — the classic silent-100x bug
    assert ui.frac(0.12) == "+12%"
    assert ui.pct(12.0) == "+12%"
    assert ui.frac(0.12) == ui.pct(12.0)
    assert ui.pct_pp(33.7, 1) == "+33.7pp"


# ---------------------------------------------------------------- match_cond
def test_match_cond_ops():
    q = {"score": 80.0, "type": "MB"}
    assert ui.match_cond(q, "score", {"gte": 70})
    assert not ui.match_cond(q, "score", {"lt": 70})
    assert ui.match_cond(q, "type", "MB")
    assert ui.match_cond(q, "type", {"in": ["MB", "SME"]})
    assert not ui.match_cond(q, "type", {"neq": "MB"})


def test_match_cond_missing_or_nan_is_false_never_crash():
    assert not ui.match_cond({}, "score", {"gte": 1})
    assert not ui.match_cond({"score": float("nan")}, "score", {"gte": 1})
    assert not ui.match_cond({"score": "abc"}, "score", {"gte": 1})


# ---------------------------------------------------------------- as-of stamps
def test_asof_line_joins_pairs_and_skips_none_values():
    s = ui.asof_line(("ledger", "2026-06-07"), ("board", None), ("as-of", "2026-06-06"))
    assert "ledger 2026-06-07" in s and "as-of 2026-06-06" in s and "board" not in s
