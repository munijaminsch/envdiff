"""Tests for envdiff.cli_lint."""

from __future__ import annotations

import io
import pytest
from pathlib import Path

from envdiff.cli_lint import run_lint


@pytest.fixture
def env_dir(tmp_path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


class _Args:
    def __init__(self, files, strict=False):
        self.files = files
        self.strict = strict


def test_clean_file_exits_zero(env_dir):
    p = _write(env_dir, ".env", "KEY=value\n")
    out = io.StringIO()
    code = run_lint(_Args([str(p)]), out=out)
    assert code == 0
    assert "OK" in out.getvalue()


def test_issues_exits_zero_without_strict(env_dir):
    p = _write(env_dir, ".env", "BADLINE\n")
    out = io.StringIO()
    code = run_lint(_Args([str(p)], strict=False), out=out)
    assert code == 0


def test_issues_exits_one_with_strict(env_dir):
    p = _write(env_dir, ".env", "BADLINE\n")
    out = io.StringIO()
    code = run_lint(_Args([str(p)], strict=True), out=out)
    assert code == 1


def test_missing_file_exits_two(env_dir):
    err = io.StringIO()
    code = run_lint(_Args(["/no/such/.env"]), err=err)
    assert code == 2
    assert "ERROR" in err.getvalue()


def test_multiple_files_all_clean(env_dir):
    p1 = _write(env_dir, ".env.a", "A=1\n")
    p2 = _write(env_dir, ".env.b", "B=2\n")
    out = io.StringIO()
    code = run_lint(_Args([str(p1), str(p2)]), out=out)
    assert code == 0
    assert out.getvalue().count("OK") == 2


def test_output_shows_issue_details(env_dir):
    p = _write(env_dir, ".env", "KEY=\n")
    out = io.StringIO()
    run_lint(_Args([str(p)]), out=out)
    assert "W002" in out.getvalue()
