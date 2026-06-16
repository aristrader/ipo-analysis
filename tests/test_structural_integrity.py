"""Structural-integrity upgrade tests (STRUCT-1 + FILE_KINDS).

Three mechanisms guarded here:
  PART 1 — counts single-source-of-truth: MAP.md carries a generated CANONICAL FACTS
           block; verify.py's count guard fires if a hand-doc reintroduces a literal
           "<n> tests/findings/rows" token.
  PART 2 — FILE_KINDS classification + verify.py enforcement (GENERATED not stranded
           in archive/ & generator write-path agrees; ARCHIVED not cited as live by a
           CANONICAL doc).
  PART 3 — the clean repo passes all of the above (DD-1..DD-4 fixed).
"""
import os

import project_map as M
import verify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ----------------------------------------------------------- PART 1: counts guard
def test_map_has_canonical_facts_block():
    md = M.render_map()
    assert "CANONICAL FACTS" in md, "MAP.md must carry a generated CANONICAL FACTS block"
    # the live numbers must be interpolated, not placeholders
    assert str(M.INVARIANTS["substrate_rows"]) in md
    assert str(M.INVARIANTS["n_findings"]) + " findings" in md


def test_counts_guard_clean_on_real_repo():
    # the repo as-shipped must have NO hardcoded count tokens in the hand-docs
    assert verify.check_doc_counts() == [], (
        "hand-docs contain hardcoded count tokens: " + str(verify.check_doc_counts())
    )


def test_counts_guard_fires_on_planted_bad_count(tmp_path):
    bad = tmp_path / "FAKE_STATUS.md"
    bad.write_text("This release has 219 tests and 29 findings and 2384 rows.\n")
    hits = verify._scan_count_tokens(str(bad))
    assert hits, "the count guard must catch '<n> tests/findings/rows' tokens"
    # all three token classes should be detected
    joined = " ".join(hits).lower()
    assert "tests" in joined and "findings" in joined and "rows" in joined


def test_counts_guard_ignores_legit_prose(tmp_path):
    # weights, component counts, version-ish numbers must NOT false-positive
    ok = tmp_path / "PROSE.md"
    ok.write_text(
        "Score = 8 components; downside 0.269 weight. Run 00->09 steps. "
        "Smallcap-250 benchmark. Built in 2026.\n"
    )
    assert verify._scan_count_tokens(str(ok)) == []


# ----------------------------------------------------- PART 2: FILE_KINDS structure
def test_file_kinds_exists_and_well_formed():
    assert hasattr(M, "FILE_KINDS"), "project_map must define FILE_KINDS"
    valid = {"GENERATED", "GENERATED_INDEX", "CANONICAL", "ARCHIVED", "HISTORICAL"}
    for path, (kind, gen) in M.FILE_KINDS.items():
        assert kind in valid, f"{path}: unknown kind {kind}"
        if kind in ("GENERATED", "GENERATED_INDEX"):
            assert gen, f"{path}: GENERATED kinds must name a generator"


def test_file_kinds_classifier_archive_default():
    assert M.file_kind("docs/research/archive/anything.md")[0] == "ARCHIVED"
    assert M.file_kind("MAP.md")[0] == "GENERATED_INDEX"
    assert M.file_kind("CLAUDE.md")[0] == "CANONICAL"


# --------------------------------------------------- PART 2: enforcement (RULE A/B)
def test_file_kinds_rules_clean_on_real_repo():
    assert verify.check_file_kinds() == [], (
        "FILE_KINDS rules fire on the clean repo: " + str(verify.check_file_kinds())
    )


def test_rule_a_fires_on_generated_stranded_in_archive():
    # plant a violation: a GENERATED file mapped to a live path that doesn't exist,
    # whose only copy is in archive/, with a known generator write-path.
    planted = {
        "docs/research/__nonexistent_generated__.md": (
            "GENERATED", "tools/mutation/run_mutations.py"),
    }
    issues = verify.check_file_kinds(file_kinds=planted)
    assert any("RULE A" in i or "GENERATED" in i for i in issues), issues


def test_rule_a_missing_generated_message_names_generator_command():
    # NIT-2: a GENERATED build-artifact legitimately absent (e.g. on a fresh clone, before
    # its generator runs) must still surface as visible drift — but ACTIONABLE: the message
    # must tell the user HOW to generate it (its generator command), not a bare "missing".
    planted = {
        "report/__nonexistent_artifact__.html": (
            "GENERATED", "scripts/run_layer3_report.py"),
    }
    issues = verify.check_file_kinds(file_kinds=planted)
    assert issues, "RULE A must still flag a missing GENERATED artifact (do not silence it)"
    msg = " ".join(issues)
    assert "GENERATED" in msg and "not present" in msg
    # the generator command must be named so the user can act on it
    assert "generate via:" in msg
    assert "PYTHONPATH=. python scripts/run_layer3_report.py" in msg, msg


def test_gen_cmd_maps_generator_to_runnable_hint():
    # verify.py-as-generator (MAP.md) -> plain `python verify.py`; scripts -> PYTHONPATH form;
    # the command is DERIVED from the generator path, never a second hand-maintained literal.
    assert verify._gen_cmd("verify.py") == "python verify.py"
    assert verify._gen_cmd("tools/mutation/run_mutations.py") == (
        "PYTHONPATH=. python tools/mutation/run_mutations.py")
    assert verify._gen_cmd(None) == "see project_map.FILE_KINDS"


def test_rule_b_clean_on_real_canonical_doc():
    # CLAUDE.md is CANONICAL; it mentions archive/ only as benign "superseded → archive"
    # pointers, never as a live source -> must be clean.
    issues = verify._canonical_cites_archive(
        canonical_docs=["CLAUDE.md"],
        archive_token="docs/research/archive/future_ideas.md",
    )
    assert issues == []


def test_rule_b_detects_live_source_citation(tmp_path):
    # the DANGEROUS form: archive path presented AS the current/live source
    citer = tmp_path / "CANON.md"
    citer.write_text(
        "The current registry is docs/research/archive/showdown_audit.md — read it.\n")
    issues = verify._canonical_cites_archive(
        canonical_docs=[str(citer)],
        archive_token="docs/research/archive/showdown_audit.md",
        roots=[str(tmp_path)],
    )
    assert issues, "RULE B must detect an ARCHIVED path cited as THE LIVE source"


def test_rule_b_ignores_benign_see_archive_pointer(tmp_path):
    # the BENIGN form (present in the real repo): "see/lives in archive" must NOT fire
    citer = tmp_path / "CANON.md"
    citer.write_text(
        "Superseded planning docs live in docs/research/archive/. "
        "See docs/research/archive/future_ideas.md for the someday list.\n")
    issues = verify._canonical_cites_archive(
        canonical_docs=[str(citer)],
        archive_token="docs/research/archive/future_ideas.md",
        roots=[str(tmp_path)],
    )
    assert issues == [], "benign 'see archive' pointers must not trip RULE B"


# --------------------------------------------------------- PART 3: DD instances fixed
def test_dd1_dd2_dd3_generated_files_live_not_archived():
    for live, arch in [
        ("docs/research/unresolved_88_mismatches_audit.md",
         "docs/research/archive/unresolved_88_mismatches_audit.md"),
        ("docs/research/enrichment_recovery_log.csv",
         "docs/research/archive/enrichment_recovery_log.csv"),
        ("docs/research/longterm_inwindow_log.csv",
         "docs/research/archive/longterm_inwindow_log.csv"),
    ]:
        assert os.path.exists(os.path.join(ROOT, live)), f"{live} must exist at live path"
        assert not os.path.exists(os.path.join(ROOT, arch)), (
            f"{arch} must not remain in archive (would be a two-homes drift)")


def test_dd4_task_log_path_fixed_in_code_and_docs():
    nodes = open(os.path.join(ROOT, "thinktank/orchestration/nodes.py")).read()
    assert '"docs" / "research" / "task_log.md"' not in nodes
    assert "tracker" in nodes and "task_log" in nodes
    claude = open(os.path.join(ROOT, "CLAUDE.md")).read()
    assert "docs/research/task_log.md" not in claude


def test_verify_fast_drift_still_clean():
    # the new checks are wired into fast_drift; repo must stay clean
    assert verify.fast_drift() == []
