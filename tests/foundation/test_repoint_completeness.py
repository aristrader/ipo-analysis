"""Completeness guard: no scraper may contain a hardcoded data/(raw|reference|master|prices|live)
path literal in executable code (docstrings and comments are allowed — they are documentation).

After the repoint pass, every scraper either:
  - reads the frozen baseline via config.src(...)
  - writes to the output tree via config.raw_dir() / config.prices_dir() / etc.

If this test fails, find the offending scraper+line, classify the path (work-list input →
config.src, output write → config.*_dir / config.out, skip-check → config.*_dir), and
wire it correctly.

Excluded by design (assembly/merge steps repointed in a later phase):
  - screener_prices_merge.py
"""
import ast
import re
import tokenize
import io
from pathlib import Path

import pytest

SCRAPERS_DIR = Path(__file__).resolve().parent.parent.parent / "scrapers"
EXCLUDE = {"screener_prices_merge.py"}

# The pattern we are guarding against in non-documentation code.
# Form 1: path-joined string, e.g. 'data/raw/...' or 'data/master'
_HARDCODED_RE = re.compile(r"data/(raw|reference|master|prices|live)")

# Form 2: split-arg form — a 'data' or "data" string literal immediately followed
# (ignoring whitespace) by a comma and then a raw/master/reference/prices/live
# string literal, e.g. os.path.join(..., 'data', 'master', ...).
# Must NOT match dict access like .get('data', [...]) — those have a list/non-string
# after the comma.  We guard by requiring the second arg to be one of the known
# data-subdirectory names (quotes required).
_SPLIT_ARG_RE = re.compile(
    r"""['"]data['"]\s*,\s*['"](raw|master|reference|prices|live)['"]"""
)


def _code_string_literals(source: str):
    """Yield (lineno, value) for every string literal that appears in executable
    positions — i.e. NOT module/class/function docstrings and NOT comments.

    Strategy: tokenize to strip comments, then walk the AST to find Constant nodes
    that are NOT the first statement in a module/class/function body (those are
    docstrings).
    """
    # Collect line numbers of docstring nodes via AST
    docstring_lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return  # unparseable — skip silently

    for node in ast.walk(tree):
        # module, class, function bodies: first stmt if it is an Expr(Constant(str))
        body = getattr(node, "body", None)
        if body and isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstring_lines.add(first.lineno)

    # Now walk all string constants and skip docstring lines
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.lineno not in docstring_lines
        ):
            yield node.lineno, node.value


def _code_lines_stripped_comments(source: str):
    """Yield (lineno, stripped_line) for every source line that is not a pure comment
    and is not inside a multi-line string (docstring).  Used to scan for the split-arg
    form which spans a raw source substring rather than a single AST node value.

    We strip single-line comments (# ...) and skip the body of docstrings (collected
    from the AST the same way as _code_string_literals does).
    """
    # Collect (start_lineno, end_lineno) ranges of docstring nodes
    docstring_ranges: list[tuple[int, int]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if body and isinstance(body, list) and body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstring_ranges.append((first.lineno, first.end_lineno))

    def _in_docstring(lineno: int) -> bool:
        return any(start <= lineno <= end for start, end in docstring_ranges)

    for lineno, line in enumerate(source.splitlines(), start=1):
        if _in_docstring(lineno):
            continue
        # strip trailing inline comment
        stripped = line.split("#")[0]
        yield lineno, stripped


def collect_violations():
    """Return list of (filename, lineno, matched_string) for every violation."""
    violations = []
    for py_file in sorted(SCRAPERS_DIR.glob("*.py")):
        if py_file.name in EXCLUDE:
            continue
        source = py_file.read_text(encoding="utf-8")

        # Form 1: path-joined string literals  ('data/master', 'data/raw/...')
        for lineno, value in _code_string_literals(source):
            if _HARDCODED_RE.search(value):
                violations.append((py_file.name, lineno, value))

        # Form 2: split-arg form  ('data', 'master') in executable code lines
        for lineno, line in _code_lines_stripped_comments(source):
            if _SPLIT_ARG_RE.search(line):
                violations.append((py_file.name, lineno, line.strip()))

    return violations


def test_no_hardcoded_data_paths_in_scrapers():
    violations = collect_violations()
    if violations:
        lines = [f"  {fname}:{lineno}  {value!r}" for fname, lineno, value in violations]
        pytest.fail(
            "Hardcoded data/(raw|reference|master|prices|live) path literals found in scrapers"
            " (use config.src / config.*_dir / config.out instead):\n"
            + "\n".join(lines)
        )
