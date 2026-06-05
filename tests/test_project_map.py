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


def test_routing_patterns_and_fallback():
    # every concrete (non-glob) pattern must exist on disk; fallback must be last
    pats = [p for p, _ in M.TEST_ROUTING]
    assert pats[-1] == "*", "TEST_ROUTING must end with the '*' fallback"
    for p in pats[:-1]:
        if "*" not in p:
            assert verify._exists(p), f"TEST_ROUTING references missing path: {p}"
    # routing resolves: a pipeline change must route to the pipeline tests
    routed = verify.route(["pipeline/lib.py", "totally/unknown.xyz"])
    assert any("tests/pipeline" in c for c in routed["pipeline/lib.py"])
    assert any("fallback" in c for c in routed["totally/unknown.xyz"])
    # every test path mentioned in a routing command exists
    import re
    for _, cmds in M.TEST_ROUTING:
        for c in cmds:
            for t in re.findall(r"tests[/\w.]*", c):
                assert verify._exists(t), f"routing command references missing {t}"
