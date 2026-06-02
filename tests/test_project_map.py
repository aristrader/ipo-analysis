"""Tests for the navigation/anti-drift machinery itself (project_map + verify).

If this suite is green, the map is internally consistent with the filesystem and
the DAG — so MAP.md (generated) and the per-turn checkpoint are trustworthy.
"""
import os

import project_map as M
import verify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_mapped_path_exists():
    missing = [p for p in M.all_referenced_paths() if not verify._exists(p)]
    assert missing == [], f"project_map references paths not on disk: {missing}"


def test_dag_is_single_sourced_into_run_all():
    import run_all
    assert run_all.STEPS == M.dag_steps()


def test_unwired_steps_exist_and_are_not_also_wired():
    wired = {path for _k, path, _r in M.PIPELINE}
    for path, _role in M.UNWIRED:
        assert verify._exists(path), f"UNWIRED step missing: {path}"
        assert path not in wired, f"step in both PIPELINE and UNWIRED: {path}"


def test_verify_reports_no_drift():
    assert verify.fast_drift() == []


def test_invariants_match_reality():
    assert verify.count_findings() == M.INVARIANTS["n_findings"]
    assert verify.count_substrate_rows() == M.INVARIANTS["substrate_rows"]
    assert verify.config_as_of_date() == M.INVARIANTS["as_of_date"]


def test_render_map_has_the_four_views():
    md = M.render_map()
    for section in ("## Navigate", "## Context index", "## Flow", "## Tree"):
        assert section in md
