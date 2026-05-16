"""Tests for envdiff.cli."""

import json
from pathlib import Path

import pytest

from envdiff.cli import run


@pytest.fixture()
def env_dir(tmp_path: Path):
    """Return a helper that writes a named .env file inside tmp_path."""

    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


def test_no_differences_exits_zero(env_dir):
    left = env_dir(".env.a", "KEY=value\nFOO=bar\n")
    right = env_dir(".env.b", "KEY=value\nFOO=bar\n")
    assert run([str(left), str(right)]) == 0


def test_differences_exits_zero_without_flag(env_dir):
    left = env_dir(".env.a", "KEY=value\n")
    right = env_dir(".env.b", "KEY=other\n")
    assert run([str(left), str(right)]) == 0


def test_differences_exits_one_with_flag(env_dir):
    left = env_dir(".env.a", "KEY=value\n")
    right = env_dir(".env.b", "KEY=other\n")
    assert run([str(left), str(right), "--exit-code"]) == 1


def test_missing_file_exits_two(env_dir):
    left = env_dir(".env.a", "KEY=value\n")
    assert run([str(left), "/nonexistent/.env.b"]) == 2


def test_text_output_contains_key(env_dir, capsys):
    left = env_dir(".env.a", "ONLY_LEFT=1\n")
    right = env_dir(".env.b", "")
    run([str(left), str(right)])
    captured = capsys.readouterr()
    assert "ONLY_LEFT" in captured.out


def test_json_output_is_valid_json(env_dir, capsys):
    left = env_dir(".env.a", "A=1\nB=2\n")
    right = env_dir(".env.b", "A=1\n")
    run([str(left), str(right), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "B" in data["missing_in_right"]


def test_json_no_diff_has_differences_false(env_dir, capsys):
    left = env_dir(".env.a", "X=1\n")
    right = env_dir(".env.b", "X=1\n")
    run([str(left), str(right), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["has_differences"] is False


def test_env_names_in_text_output(env_dir, capsys):
    left = env_dir(".env.staging", "PORT=8080\n")
    right = env_dir(".env.production", "PORT=80\n")
    run([str(left), str(right)])
    out = capsys.readouterr().out
    assert ".env.staging" in out
    assert ".env.production" in out


def test_json_output_has_differences_true_when_values_differ(env_dir, capsys):
    """Ensure has_differences is True when keys exist in both files but values differ."""
    left = env_dir(".env.a", "KEY=foo\n")
    right = env_dir(".env.b", "KEY=bar\n")
    run([str(left), str(right), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["has_differences"] is True
    assert "KEY" in data["differing_values"]
