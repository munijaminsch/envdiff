"""Tests for envdiff.cli_multi."""
from __future__ import annotations

import json
import pytest

from envdiff.cli_multi import run_multi


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


class _Args:
    def __init__(self, files, as_json=False, fail_on_diff=False):
        self.files = files
        self.as_json = as_json
        self.fail_on_diff = fail_on_diff


def test_clean_files_exits_zero(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    assert run_multi(_Args([a, b])) == 0


def test_differences_exits_zero_without_flag(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\nEXTRA=x\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    assert run_multi(_Args([a, b])) == 0


def test_differences_exits_one_with_flag(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\nEXTRA=x\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    assert run_multi(_Args([a, b], fail_on_diff=True)) == 1


def test_json_output_is_valid(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=2\n")
    run_multi(_Args([a, b], as_json=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "pairs" in data


def test_missing_file_exits_two(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    code = run_multi(_Args([a, str(env_dir / "ghost.env")]))
    assert code == 2


def test_text_output_clean(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    run_multi(_Args([a, b]))
    out = capsys.readouterr().out
    assert "no differences" in out


def test_text_output_shows_mismatch(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=hello\n")
    b = _write(env_dir / "b.env", "KEY=world\n")
    run_multi(_Args([a, b]))
    out = capsys.readouterr().out
    assert "MISMATCH" in out
