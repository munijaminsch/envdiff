"""Integration tests for differ_values with the parser."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.differ_values import diff_values


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text(content)
    return path


def test_diff_parsed_files_clean(env_dir):
    left = _write(env_dir / "left.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    right = _write(env_dir / "right.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_values(l_env, r_env, left_source=str(left), right_source=str(right))
    assert result.is_clean is True
    assert result.total_keys == 2


def test_diff_parsed_files_detects_change(env_dir):
    left = _write(env_dir / "left.env", "DB_HOST=localhost\nDB_PORT=5432\n")
    right = _write(env_dir / "right.env", "DB_HOST=remotehost\nDB_PORT=5432\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_values(l_env, r_env)
    assert result.is_clean is False
    assert result.changed_count == 1
    changed = [e for e in result.entries if e.changed]
    assert changed[0].key == "DB_HOST"


def test_comments_not_included_in_diff(env_dir):
    left = _write(env_dir / "left.env", "# comment\nKEY=val\n")
    right = _write(env_dir / "right.env", "KEY=val\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_values(l_env, r_env)
    keys = [e.key for e in result.entries]
    assert all(not k.startswith("#") for k in keys)
    assert "KEY" in keys


def test_as_dict_round_trip(env_dir):
    left = _write(env_dir / "a.env", "X=1\nY=2\n")
    right = _write(env_dir / "b.env", "X=1\nY=99\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_values(l_env, r_env, left_source="a.env", right_source="b.env")
    d = result.as_dict()
    assert d["changed_count"] == 1
    assert d["unchanged_count"] == 1
    entry_keys = [e["key"] for e in d["entries"]]
    assert "X" in entry_keys
    assert "Y" in entry_keys
