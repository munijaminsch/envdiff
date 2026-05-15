"""Integration tests for the merge CLI sub-command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_merge import add_merge_subparser, run_merge


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


class _Args:
    """Minimal stand-in for argparse.Namespace."""

    def __init__(self, files, strategy="first", fmt="text",
                 fail_on_conflict=False, quiet=False):
        self.files = [str(f) for f in files]
        self.strategy = strategy
        self.format = fmt
        self.fail_on_conflict = fail_on_conflict
        self.quiet = quiet


# ---------------------------------------------------------------------------
# basic merging
# ---------------------------------------------------------------------------

def test_merge_no_conflicts_exits_zero(env_dir, capsys):
    a = _write(env_dir, "a.env", "FOO=1\nBAR=hello\n")
    b = _write(env_dir, "b.env", "BAZ=world\n")
    code = run_merge(_Args([a, b]))
    assert code == 0


def test_merge_output_contains_all_keys(env_dir, capsys):
    a = _write(env_dir, "a.env", "FOO=1\n")
    b = _write(env_dir, "b.env", "BAR=2\n")
    run_merge(_Args([a, b]))
    out = capsys.readouterr().out
    assert "FOO=1" in out
    assert "BAR=2" in out


# ---------------------------------------------------------------------------
# conflict handling
# ---------------------------------------------------------------------------

def test_conflicts_exit_zero_by_default(env_dir):
    a = _write(env_dir, "a.env", "HOST=localhost\n")
    b = _write(env_dir, "b.env", "HOST=prod\n")
    code = run_merge(_Args([a, b]))
    assert code == 0


def test_conflicts_exit_one_with_flag(env_dir):
    a = _write(env_dir, "a.env", "HOST=localhost\n")
    b = _write(env_dir, "b.env", "HOST=prod\n")
    code = run_merge(_Args([a, b], fail_on_conflict=True))
    assert code == 1


def test_strategy_error_returns_1_on_conflict(env_dir):
    a = _write(env_dir, "a.env", "X=1\n")
    b = _write(env_dir, "b.env", "X=2\n")
    code = run_merge(_Args([a, b], strategy="error"))
    assert code == 1


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_is_valid(env_dir, capsys):
    a = _write(env_dir, "a.env", "FOO=1\n")
    b = _write(env_dir, "b.env", "BAR=2\n")
    run_merge(_Args([a, b], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "merged" in data
    assert "conflicts" in data
    assert "sources" in data


def test_json_output_includes_conflict_info(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=v1\n")
    b = _write(env_dir, "b.env", "KEY=v2\n")
    run_merge(_Args([a, b], fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["key"] == "KEY"


# ---------------------------------------------------------------------------
# error paths
# ---------------------------------------------------------------------------

def test_missing_file_returns_2(env_dir):
    code = run_merge(_Args([env_dir / "nonexistent.env"]))
    assert code == 2


# ---------------------------------------------------------------------------
# subparser registration smoke-test
# ---------------------------------------------------------------------------

def test_add_merge_subparser_registers_command():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_merge_subparser(sub)
    args = root.parse_args(["merge", "a.env", "b.env"])
    assert args.files == ["a.env", "b.env"]
    assert args.strategy == "first"
