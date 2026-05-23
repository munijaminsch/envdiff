"""Tests for envdiff.cli_chain."""

import json
import os
import pytest

from envdiff.cli_chain import run_chain


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(directory, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


class _Args:
    def __init__(self, files, as_json=False, fail_on_diff=False):
        self.files = files
        self.as_json = as_json
        self.fail_on_diff = fail_on_diff


# ---------------------------------------------------------------------------
# Odd number of files
# ---------------------------------------------------------------------------

def test_odd_number_of_files_returns_2(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\n")
    args = _Args(files=[f1])
    assert run_chain(args) == 2


# ---------------------------------------------------------------------------
# Clean pairs
# ---------------------------------------------------------------------------

def test_clean_pair_exits_zero(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\nB=2\n")
    f2 = _write(env_dir, "b.env", "A=1\nB=2\n")
    assert run_chain(_Args(files=[f1, f2])) == 0


def test_multiple_clean_pairs_exits_zero(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=1\n")
    f3 = _write(env_dir, "c.env", "X=9\n")
    f4 = _write(env_dir, "d.env", "X=9\n")
    assert run_chain(_Args(files=[f1, f2, f3, f4])) == 0


# ---------------------------------------------------------------------------
# Dirty pairs
# ---------------------------------------------------------------------------

def test_dirty_pair_exits_zero_without_flag(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=2\n")
    assert run_chain(_Args(files=[f1, f2], fail_on_diff=False)) == 0


def test_dirty_pair_exits_one_with_flag(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=2\n")
    assert run_chain(_Args(files=[f1, f2], fail_on_diff=True)) == 1


def test_missing_file_returns_2(env_dir):
    f1 = _write(env_dir, "a.env", "A=1\n")
    args = _Args(files=[f1, "/nonexistent/path.env"])
    assert run_chain(args) == 2


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_is_valid(env_dir, capsys):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=1\n")
    run_chain(_Args(files=[f1, f2], as_json=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_pairs" in data
    assert data["total_pairs"] == 1


def test_json_output_entries_count(env_dir, capsys):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=1\n")
    f3 = _write(env_dir, "c.env", "B=2\n")
    f4 = _write(env_dir, "d.env", "B=2\n")
    run_chain(_Args(files=[f1, f2, f3, f4], as_json=True))
    data = json.loads(capsys.readouterr().out)
    assert len(data["entries"]) == 2


# ---------------------------------------------------------------------------
# Text output smoke test
# ---------------------------------------------------------------------------

def test_text_output_contains_ok(env_dir, capsys):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=1\n")
    run_chain(_Args(files=[f1, f2]))
    out = capsys.readouterr().out
    assert "OK" in out


def test_text_output_contains_diff(env_dir, capsys):
    f1 = _write(env_dir, "a.env", "A=1\n")
    f2 = _write(env_dir, "b.env", "A=2\n")
    run_chain(_Args(files=[f1, f2]))
    out = capsys.readouterr().out
    assert "DIFF" in out
