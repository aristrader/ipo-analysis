"""A1 — behaviour tests for the redefined 'obscure lead manager' wipeout flag.

The OLD rule fired on banker FREQUENCY (< 12 IPOs in our window) — quality-blind, so it
false-vetoed reputable-but-under-sampled banks (Nuvama, Morgan Stanley, Smart Horizon...).
The NEW rule (A1, 2026-06-09) is QUALITY-AWARE + POINT-IN-TIME: fire only when the banker's
PRIOR IPOs (>= MIN_PRIOR, listed strictly before this IPO) FAILED at >= BAD_RATE; ABSTAIN
(never fire) when the prior record is too thin. These tests pin that contract so a future edit
can't silently regress to the artifact.

Logic tests use small synthetic frames (deterministic, refresh-proof). A few real-substrate
sanity checks confirm the named reputable banks are exonerated on live data.
"""
import numpy as np
import pandas as pd
import pytest
from layer3 import spine
from layer3.predictor import scorecard


# ---------------------------------------------------------------------------------------------
# synthetic-frame helper: build a substrate-shaped mini-df where `_bad_outcome_mask` is fully
# controllable. bad = outcome_class=='wipeout'. We set delisted=False + liquidity ok so the
# dead-money branch never fires unexpectedly — only the explicit 'wipeout' rows count as bad.
# ---------------------------------------------------------------------------------------------
def _mini(rows):
    """rows = list of (lead_manager, listing_date 'YYYY-MM-DD', is_bad bool)."""
    return pd.DataFrame([{
        "isin": f"X{i:06d}",
        "lead_manager": lm,
        "listing_date": ld,
        "outcome_class": "wipeout" if bad else "winner",
        "delisted": False,
        "current_return_from_issue": -0.9 if bad else 0.5,
        "liquidity_flag": "ok",
        "type": "SME",
    } for i, (lm, ld, bad) in enumerate(rows)])


@pytest.fixture(autouse=True)
def _force_quality_def():
    """These tests pin the QUALITY (PIT bad-rate) definition's contract; restore the mode after."""
    prev = scorecard.OBSCURE_BANKER_MODE
    scorecard.OBSCURE_BANKER_MODE = "quality"
    yield
    scorecard.OBSCURE_BANKER_MODE = prev


# ---- 1a. reputable banker with a CLEAN (>=MIN_PRIOR, low-bad) prior record → NOT flagged -----
def test_clean_record_banker_not_flagged():
    # 6 prior clean IPOs by "GoodBank" (all winners) → prior bad-rate 0% → must NOT fire,
    # even though it is "under-sampled" (only 6 IPOs — the OLD freq<12 rule WOULD have fired).
    df = _mini([("GoodBank", f"2022-0{i+1}-01", False) for i in range(6)])
    q = {"lead_manager": "GoodBank", "listing_date": "2024-01-01"}
    fires, why = scorecard._obscure_banker_fires("GoodBank", df, q)
    assert fires is False, why
    # and the OLD rule really would have fired (proves the fix matters, not a no-op)
    scorecard.OBSCURE_BANKER_MODE = "legacy"
    old_fires, _ = scorecard._obscure_banker_fires("GoodBank", df, q)
    assert old_fires is True
    scorecard.OBSCURE_BANKER_MODE = "quality"


# ---- 1b. genuinely-poor small banker (>=MIN_PRIOR, high-bad) → flagged ------------------------
def test_bad_record_banker_flagged():
    # 6 prior IPOs by "BadShop", 4 of them wipeouts → 67% bad >= 40% → must fire.
    rows = [("BadShop", "2022-01-01", True), ("BadShop", "2022-02-01", True),
            ("BadShop", "2022-03-01", True), ("BadShop", "2022-04-01", True),
            ("BadShop", "2022-05-01", False), ("BadShop", "2022-06-01", False)]
    df = _mini(rows)
    q = {"lead_manager": "BadShop", "listing_date": "2024-01-01"}
    fires, why = scorecard._obscure_banker_fires("BadShop", df, q)
    assert fires is True, why
    assert "67%" in why or "%" in why


# ---- 2. point-in-time correctness: banker stats use PRIOR listings only -----------------------
def test_point_in_time_prior_only():
    # "PIT" banker: its first 5 IPOs (2021) are all BAD; then it cleans up — 2024 IPOs all good.
    # A query listing in 2022 should see the 5 bad priors → FIRE. The same banker queried with an
    # EARLY listing date (before it had >=MIN_PRIOR priors) should ABSTAIN, and a LATE query must
    # NOT be contaminated by IPOs that listed AFTER it.
    rows = ([("PIT", f"2021-0{i+1}-01", True) for i in range(5)]    # 5 bad priors in 2021
            + [("PIT", f"2024-0{i+1}-01", False) for i in range(6)])  # 6 good in 2024
    df = _mini(rows)
    # query in early 2022: 5 prior IPOs, all bad → fires
    f_2022, _ = scorecard._obscure_banker_fires("PIT", df, {"lead_manager": "PIT", "listing_date": "2022-01-01"})
    assert f_2022 is True
    # PIT correctness: stats from only-prior listings. As of 2021-03-01 only 2 priors exist (<MIN_PRIOR) → abstain.
    n_prior, bad = scorecard._banker_prior_badrate("PIT", df, asof="2021-03-01")
    assert n_prior == 2 and (n_prior < scorecard.OBSCURE_MIN_PRIOR)
    f_early, _ = scorecard._obscure_banker_fires("PIT", df, {"lead_manager": "PIT", "listing_date": "2021-03-01"})
    assert f_early is False                          # thin prior record → ABSTAIN, never false-fire
    # NO look-ahead: a query at the very end still sees only strictly-prior rows, and the count
    # never exceeds the rows that listed before it.
    n_end, _ = scorecard._banker_prior_badrate("PIT", df, asof="2024-03-01")
    assert n_end == 7                                # 5 (2021) + 2024-01,02 — NOT the 2024-03 row itself


# ---- 3. thin / unknown record → ABSTAIN (None / no fire), never a false veto ------------------
def test_thin_record_abstains():
    # banker with only 2 prior IPOs → below MIN_PRIOR → must ABSTAIN regardless of those 2 outcomes.
    df = _mini([("ThinShop", "2022-01-01", True), ("ThinShop", "2022-02-01", True)])  # both bad, but N<5
    q = {"lead_manager": "ThinShop", "listing_date": "2024-01-01"}
    fires, why = scorecard._obscure_banker_fires("ThinShop", df, q)
    assert fires is False, why
    assert "thin" in why.lower()
    # a banker never seen before → 0 priors → abstain (no crash, no fire)
    f2, _ = scorecard._obscure_banker_fires("NeverSeen", df, {"lead_manager": "NeverSeen"})
    assert f2 is False


# ---- 4. the vectorized series matches the per-query decision (consistency contract) -----------
def test_series_matches_per_query_and_abstains_as_nan():
    # one bad banker (>=5 priors, all-bad), one thin banker (2 priors). Build a pool that includes
    # a later IPO for each; the series must FIRE (1.0) for the bad-banker row and ABSTAIN (NaN) for
    # the thin one — identical to the per-query _obscure_banker_fires verdict.
    rows = ([("BadShop", f"2021-0{i+1}-01", True) for i in range(5)]
            + [("BadShop", "2023-01-01", False),            # the row we test (5 bad priors)
               ("ThinShop", "2022-01-01", True),
               ("ThinShop", "2023-02-01", False)])          # thin row (1 prior)
    df = _mini(rows)
    series = scorecard._obscure_banker_series(df, df)
    bad_row = df.index[(df["lead_manager"] == "BadShop") & (df["listing_date"] == "2023-01-01")][0]
    thin_row = df.index[(df["lead_manager"] == "ThinShop") & (df["listing_date"] == "2023-02-01")][0]
    assert series.loc[bad_row] == 1.0
    assert np.isnan(series.loc[thin_row])             # thin → NaN abstain, NOT 0/1
    # cross-check the series fire against the per-query path for the bad row
    fires, _ = scorecard._obscure_banker_fires("BadShop", df, {"lead_manager": "BadShop", "listing_date": "2023-01-01"})
    assert bool(fires) == bool(series.loc[bad_row] == 1.0)


# ---- 5. REAL-SUBSTRATE sanity: B1's named reputable banks are exonerated (no live false-veto) --
@pytest.fixture(scope="module")
def df_real():
    d = spine.load_substrate()
    if "listing_metrics_status" in d.columns:
        d = d[d["listing_metrics_status"] != "unreliable_coverage"].copy()
    return d


@pytest.mark.parametrize("banker", ["Nuvama Wealth Management", "Smart Horizon Capital",
                                    "Choice Capital", "Indorient Financial"])
def test_reputable_banks_not_flagged_on_real_data(df_real, banker):
    # live query (no listing_date) uses the banker's FULL real history; reputable banks have a
    # clean prior record so the NEW flag must not fire (the OLD freq<12 rule false-vetoed them).
    scorecard.OBSCURE_BANKER_MODE = "quality"
    fires, why = scorecard._obscure_banker_fires(banker, df_real, {"lead_manager": banker})
    assert fires is False, f"{banker} should be exonerated, got: {why}"


# ============================================================================================
# A1b coverage-guard (LIVE) — the thin-record leg the quality def abstained on. Pins the MB/SME
# asymmetry that recovers recall WITHOUT re-introducing the false-veto.
# ============================================================================================
def _mini_mb(rows):
    df = _mini(rows)
    df["type"] = "MB"
    return df


def test_coverage_guard_thin_sme_banker_fires():
    # a thin-record SME banker (2 priors < MIN_PRIOR, freq<12) FIRES under coverage_guard — the
    # recall-recovery leg that the quality def (abstain) missed.
    scorecard.OBSCURE_BANKER_MODE = "coverage_guard"
    df = _mini([("TinyShop", "2022-01-01", False), ("TinyShop", "2022-02-01", False)])  # type SME
    q = {"lead_manager": "TinyShop", "listing_date": "2024-01-01", "type": "SME"}
    fires, why = scorecard._obscure_banker_fires("TinyShop", df, q)
    assert fires is True, why
    assert "thin-record" in why.lower() or "small-shop" in why.lower()


def test_coverage_guard_thin_mainboard_banker_not_vetoed():
    # SAME thin record but a MAINBOARD query must NOT fire — this is the false-veto the freq<12 rule
    # caused (Nuvama/Morgan Stanley) and the asymmetry coverage_guard exists to fix.
    scorecard.OBSCURE_BANKER_MODE = "coverage_guard"
    df = _mini_mb([("BigBankThin", "2022-01-01", False), ("BigBankThin", "2022-02-01", False)])
    q = {"lead_manager": "BigBankThin", "listing_date": "2024-01-01", "type": "MB"}
    fires, why = scorecard._obscure_banker_fires("BigBankThin", df, q)
    assert fires is False, why


def test_coverage_guard_record_bearing_clean_bank_still_exonerated():
    # record-bearing path is shared with quality: a clean >=MIN_PRIOR SME banker is NOT flagged even
    # under coverage_guard (the thin-SME leg only applies when the prior record is thin).
    scorecard.OBSCURE_BANKER_MODE = "coverage_guard"
    df = _mini([("GoodSME", f"2022-0{i+1}-01", False) for i in range(6)])
    q = {"lead_manager": "GoodSME", "listing_date": "2024-01-01", "type": "SME"}
    fires, _ = scorecard._obscure_banker_fires("GoodSME", df, q)
    assert fires is False


def test_coverage_guard_series_thin_sme_decisive_not_nan():
    # the vectorized series must be DECISIVE (0/1) for thin records under coverage_guard, not NaN:
    # a thin-record SME row fires (1.0); a thin-record MB row does not (0.0).
    scorecard.OBSCURE_BANKER_MODE = "coverage_guard"
    df = _mini([("TinySME", "2022-01-01", False), ("TinySME", "2023-01-01", False)])  # SME, 1 prior for row2
    df.loc[1, "listing_date"] = "2023-01-01"
    series = scorecard._obscure_banker_series(df, df)
    row2 = df.index[df["listing_date"] == "2023-01-01"][0]
    assert series.loc[row2] == 1.0  # thin SME → decisive fire, not abstain
    # MB variant of the same thin record → decisive 0.0
    dmb = _mini_mb([("TinyMB", "2022-01-01", False), ("TinyMB", "2023-01-01", False)])
    smb = scorecard._obscure_banker_series(dmb, dmb)
    r2 = dmb.index[dmb["listing_date"] == "2023-01-01"][0]
    assert smb.loc[r2] == 0.0
