"""Integration tests: parse a real .env file then pivot it."""
from __future__ import annotations

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.pivotter import pivot_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_pivot_parsed_file_unique_values(env_dir):
    path = _write(env_dir, "a.env", "HOST=localhost\nPORT=5432\nDEBUG=false\n")
    env = parse_env_file(str(path))
    result = pivot_env(env, source=str(path))
    assert result.is_clean is True
    assert result.total_keys == 3


def test_pivot_detects_shared_value_after_parse(env_dir):
    path = _write(env_dir, "b.env", "DB_HOST=localhost\nCACHE_HOST=localhost\nPORT=5432\n")
    env = parse_env_file(str(path))
    result = pivot_env(env, source="b.env")
    assert result.is_clean is False
    shared = result.shared_entries
    assert len(shared) == 1
    assert shared[0].value == "localhost"
    assert set(shared[0].keys) == {"DB_HOST", "CACHE_HOST"}


def test_comments_not_included_after_parse(env_dir):
    path = _write(
        env_dir,
        "c.env",
        "# comment\nACTIVE=true\nFLAG=true\n",
    )
    env = parse_env_file(str(path))
    result = pivot_env(env)
    # comments are stripped by the parser; only ACTIVE and FLAG survive
    assert result.total_keys == 2


def test_as_dict_round_trip(env_dir):
    path = _write(env_dir, "d.env", "X=hello\nY=world\n")
    env = parse_env_file(str(path))
    result = pivot_env(env, source="d.env")
    d = result.as_dict()
    assert d["source"] == "d.env"
    assert isinstance(d["entries"], list)
    assert d["total_keys"] == 2
