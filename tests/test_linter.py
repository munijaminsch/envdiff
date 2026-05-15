"""Tests for envdiff.linter."""

from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.linter import lint_file, LintResult, LintIssue, LintError


@pytest.fixture
def tmp_env(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_clean_file_returns_no_issues(tmp_env):
    p = tmp_env(".env", "KEY=value\nANOTHER=123\n")
    result = lint_file(p)
    assert result.is_clean
    assert result.issues == []


def test_ignores_comments_and_blanks(tmp_env):
    p = tmp_env(".env", "# comment\n\nKEY=value\n")
    result = lint_file(p)
    assert result.is_clean


def test_detects_missing_equals(tmp_env):
    p = tmp_env(".env", "BADLINE\n")
    result = lint_file(p)
    assert not result.is_clean
    assert result.issues[0].code == "E001"
    assert result.issues[0].line == 1


def test_detects_empty_key(tmp_env):
    p = tmp_env(".env", "=value\n")
    result = lint_file(p)
    assert any(i.code == "E002" for i in result.issues)


def test_detects_duplicate_key(tmp_env):
    p = tmp_env(".env", "KEY=one\nKEY=two\n")
    result = lint_file(p)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_duplicate_issue_references_first_line(tmp_env):
    p = tmp_env(".env", "KEY=one\nKEY=two\n")
    result = lint_file(p)
    w001 = next(i for i in result.issues if i.code == "W001")
    assert "line 1" in w001.message
    assert w001.line == 2


def test_detects_empty_value(tmp_env):
    p = tmp_env(".env", "KEY=\n")
    result = lint_file(p)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_detects_quoted_empty_value(tmp_env):
    p = tmp_env(".env", 'KEY=""\n')
    result = lint_file(p)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_lint_error_on_missing_file():
    with pytest.raises(LintError):
        lint_file("/nonexistent/path/.env")


def test_lint_issue_str():
    issue = LintIssue(line=3, code="W001", message="Duplicate key 'FOO'")
    assert "Line 3" in str(issue)
    assert "W001" in str(issue)
    assert "Duplicate key" in str(issue)


def test_result_path_stored(tmp_env):
    p = tmp_env(".env", "A=1\n")
    result = lint_file(p)
    assert result.path == str(p)
