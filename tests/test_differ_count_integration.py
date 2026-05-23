"""Integration tests for differ_count using real .env files."""
import pytest

from envdiff.parser import parse_env_file
from envdiff.differ_count import diff_counts


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content):
    path.write_text(content)
    return path


def test_clean_pair_is_clean(env_dir):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "C=3\nD=4\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_counts(l_env, r_env, left_source=str(left), right_source=str(right))
    assert result.is_clean is True
    assert result.net_delta == 0


def test_missing_key_shows_in_entries(env_dir):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_counts(l_env, r_env)
    assert result.is_clean is False
    b_entry = next(e for e in result.entries if e.key == "B")
    assert b_entry.delta == -1


def test_comments_not_included_in_count(env_dir):
    left = _write(env_dir / ".env.left", "# comment\nA=1\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_counts(l_env, r_env)
    assert result.left_total == 1
    assert result.is_clean is True


def test_as_dict_round_trip(env_dir):
    left = _write(env_dir / ".env.left", "X=foo\nY=bar\n")
    right = _write(env_dir / ".env.right", "X=foo\n")
    l_env = parse_env_file(str(left))
    r_env = parse_env_file(str(right))
    result = diff_counts(l_env, r_env, left_source="left", right_source="right")
    d = result.as_dict()
    assert d["left_total"] == 2
    assert d["right_total"] == 1
    assert len(d["entries"]) == 2
