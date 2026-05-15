"""Tests for envdiff.resolver."""

from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.resolver import (
    ResolveError,
    find_env_files,
    load_envs,
    resolve_pair,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# find_env_files
# ---------------------------------------------------------------------------

def test_find_env_files_returns_sorted_env_files(env_dir):
    _write(env_dir, ".env.production", "A=1")
    _write(env_dir, ".env", "B=2")
    _write(env_dir, ".env.staging", "C=3")
    _write(env_dir, "not_an_env.txt", "D=4")

    found = find_env_files(env_dir)
    names = [p.name for p in found]
    assert names == [".env", ".env.production", ".env.staging"]


def test_find_env_files_raises_for_missing_directory(tmp_path):
    with pytest.raises(ResolveError, match="Not a directory"):
        find_env_files(tmp_path / "nonexistent")


def test_find_env_files_empty_dir_returns_empty(env_dir):
    assert find_env_files(env_dir) == []


# ---------------------------------------------------------------------------
# load_envs
# ---------------------------------------------------------------------------

def test_load_envs_parses_all_files(env_dir):
    p1 = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    p2 = _write(env_dir, ".env.test", "FOO=bar\n")

    result = load_envs([p1, p2])
    assert result[".env"] == {"FOO": "bar", "BAZ": "qux"}
    assert result[".env.test"] == {"FOO": "bar"}


def test_load_envs_raises_for_missing_file(env_dir):
    with pytest.raises(ResolveError, match="File not found"):
        load_envs([env_dir / ".env.ghost"])


def test_load_envs_raises_for_parse_error(env_dir):
    bad = _write(env_dir, ".env.bad", "===invalid===")
    with pytest.raises(ResolveError, match="Parse error"):
        load_envs([bad])


def test_load_envs_aggregates_multiple_errors(env_dir):
    with pytest.raises(ResolveError) as exc_info:
        load_envs([env_dir / ".env.a", env_dir / ".env.b"])
    message = str(exc_info.value)
    assert ".env.a" in message
    assert ".env.b" in message


# ---------------------------------------------------------------------------
# resolve_pair
# ---------------------------------------------------------------------------

def test_resolve_pair_returns_two_dicts(env_dir):
    left = _write(env_dir, ".env", "KEY=val1\nONLY_LEFT=yes\n")
    right = _write(env_dir, ".env.prod", "KEY=val2\n")

    left_dict, right_dict = resolve_pair(left, right)
    assert left_dict == {"KEY": "val1", "ONLY_LEFT": "yes"}
    assert right_dict == {"KEY": "val2"}
