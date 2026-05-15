"""Integration tests: linter + parser pipeline."""

from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.linter import lint_file
from envdiff.parser import parse_env_file


@pytest.fixture
def env_dir(tmp_path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_lint_then_parse_clean_file(env_dir):
    """A file that passes lint should also parse without error."""
    p = _write(env_dir, ".env", "HOST=localhost\nPORT=5432\nDEBUG=false\n")
    result = lint_file(p)
    assert result.is_clean
    parsed = parse_env_file(p)
    assert parsed["HOST"] == "localhost"
    assert parsed["PORT"] == "5432"


def test_lint_detects_issues_parser_does_not_raise(env_dir):
    """Parser is lenient; linter catches what parser silently skips."""
    p = _write(env_dir, ".env", "GOOD=yes\nDUPLICATE=first\nDUPLICATE=second\n")
    result = lint_file(p)
    codes = [i.code for i in result.issues]
    assert "W001" in codes
    # Parser returns last-wins for duplicates — no exception
    parsed = parse_env_file(p)
    assert parsed["DUPLICATE"] == "second"


def test_multiple_issue_types_in_one_file(env_dir):
    content = "\n".join([
        "# header",
        "VALID=ok",
        "EMPTY_VAL=",
        "DUPLICATE=1",
        "DUPLICATE=2",
        "NOEQUALSSIGN",
        "",
    ])
    p = _write(env_dir, ".env", content)
    result = lint_file(p)
    codes = {i.code for i in result.issues}
    assert "W002" in codes
    assert "W001" in codes
    assert "E001" in codes
