"""Integration tests: parse a real .env file then invert it."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.inverter import invert_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_invert_parsed_file(env_dir):
    p = _write(env_dir, "app.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    env = parse_env_file(str(p))
    result = invert_env(env, source=str(p))
    assert result.total_keys == 2
    keys = {e.new_key for e in result.entries}
    assert "localhost" in keys
    assert "5432" in keys


def test_comments_not_included_after_parse(env_dir):
    p = _write(env_dir, "app.env", "# comment\nKEY=value\n")
    env = parse_env_file(str(p))
    result = invert_env(env, source=str(p))
    # parser strips comments; only KEY=value should be present
    assert result.total_keys == 1


def test_collision_detected_from_real_file(env_dir):
    p = _write(env_dir, "app.env", "KEY1=shared\nKEY2=shared\nKEY3=unique\n")
    env = parse_env_file(str(p))
    result = invert_env(env, source=str(p))
    assert result.is_clean is False
    assert "shared" in result.collisions


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, "app.env", "FOO=bar\nBAZ=qux\n")
    env = parse_env_file(str(p))
    result = invert_env(env, source=str(p))
    d = result.as_dict()
    assert d["total_keys"] == 2
    assert d["is_clean"] is True
    entry_keys = {e["new_key"] for e in d["entries"]}
    assert "bar" in entry_keys
    assert "qux" in entry_keys
