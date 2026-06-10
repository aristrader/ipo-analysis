"""Forward-test module: structure + honesty rails (no network; uses real frames)."""
from layer3 import forward_test as ft


def test_cohort_is_never_seen_and_listed():
    old, new = ft.load_frames()
    c = ft.forward_cohort(old, new)
    assert len(c) > 0
    assert not set(c["isin"]) & set(old["isin"].astype(str)), "cohort leaked already-seen isins"


def test_analyze_carries_early_read_label():
    import pandas as pd
    scored = pd.DataFrame({"isin": ["A"] * 25, "score": range(25), "n_flags": [0] * 25,
                           "gmp_pct": [None] * 25, "pop": [0.1] * 25,
                           "ret_1m": [0.05] * 25, "ret_3m": [None] * 25})
    res = ft.analyze(scored)
    assert "EARLY READ" in res["label"]
    assert res["n_scored"] == 25


# ---- F2: durable were-we-right history (append-only, comparable per vintage) ------------------
def test_history_row_computes_spreads():
    res = {"n_cohort": 40, "n_scored": 30,
           "score_buckets": [
               {"score_bucket": "B1 (higher=better)", "median_pop_%": 2.0, "median_1m_%": -3.0, "median_3m_%": None},
               {"score_bucket": "B3 (higher=better)", "median_pop_%": 12.0, "median_1m_%": 5.0, "median_3m_%": 8.0}],
           "wipeout_flags": {"flagged": {"median_pop_%": 1.0}, "clean": {"median_pop_%": 9.0}},
           "gmp_pop": {"spearman": 0.42}}
    row = ft.history_row(res, "2026-06-06", "2026-06-10 12:00")
    assert row["spread_pop"] == 10.0          # 12 - 2 (top - bottom bucket): score ranks pop
    assert row["spread_1m"] == 8.0            # 5 - (-3)
    assert row["spread_3m"] is None           # bottom 3m missing -> no spread
    assert row["flag_pop_gap"] == 8.0         # clean(9) - flagged(1): flag separates
    assert row["gmp_pop_spearman"] == 0.42


def test_append_history_upserts_by_vintage(tmp_path):
    res = {"n_cohort": 5, "n_scored": 5, "score_buckets": [], "wipeout_flags": {}}
    p = tmp_path / "hist.csv"
    ft.append_history(res, as_of="2026-05-01", run_date="r1", path=p)
    ft.append_history(res, as_of="2026-06-06", run_date="r2", path=p)
    ft.append_history(res, as_of="2026-06-06", run_date="r3", path=p)  # same vintage re-run -> update
    import csv
    rows = list(csv.DictReader(open(p)))
    assert len(rows) == 2                              # two vintages, not three
    jun = [r for r in rows if r["as_of_date"] == "2026-06-06"][0]
    assert jun["run_date"] == "r3"                     # latest read for that vintage wins
    assert [r["as_of_date"] for r in rows] == sorted(r["as_of_date"] for r in rows)  # sorted
