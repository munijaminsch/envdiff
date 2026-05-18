"""Tests for envdiff.cli_inspect."""

import argparse
import pytest
from pathlib import Path

from envdiff.cli_inspect import add_inspect_subparser, run_inspect


@pytest.fixture()
def env_dir(tmp_path: Path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


class _Args:
    def __init__(self, file: str, fmt: str = "text", only_issues: bool = False):
        self.file = file
        self.fmt = fmt
        self.only_issues = only_issues


def test_clean_file_exits_zero(env_dir, capsys):
    p = _write(env_dir, ".env", "PORT=8080\nDEBUG=true\n")
    rc = run_inspect(_Args(str(p)))
    assert rc == 0


def test_output_contains_key(env_dir, capsys):
    p = _write(env_dir, ".env", "MY_KEY=hello\n")
    run_inspect(_Args(str(p)))
    out = capsys.readouterr().out
    assert "MY_KEY" in out


def test_json_format_is_valid_json(env_dir, capsys):
    import json
    p = _write(env_dir, ".env", "A=1\nB=two\n")
    rc = run_inspect(_Args(str(p), fmt="json"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "inspections" in data
    assert data["total_keys"] == 2


def test_missing_file_exits_one(env_dir, capsys):
    rc = run_inspect(_Args(str(env_dir / "missing.env")))
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err


def test_only_issues_hides_normal_keys(env_dir, capsys):
    p = _write(env_dir, ".env", "NORMAL=value\nEMPTY=\n")
    run_inspect(_Args(str(p), only_issues=True))
    out = capsys.readouterr().out
    assert "EMPTY" in out
    assert "NORMAL" not in out


def test_add_inspect_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_inspect_subparser(subs)
    args = parser.parse_args(["inspect", "some.env"])
    assert args.file == "some.env"
    assert args.fmt == "text"


def test_numeric_and_boolean_shown_in_text(env_dir, capsys):
    p = _write(env_dir, ".env", "PORT=3000\nFLAG=true\n")
    run_inspect(_Args(str(p)))
    out = capsys.readouterr().out
    assert "numeric" in out
    assert "boolean" in out
