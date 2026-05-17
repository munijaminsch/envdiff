"""Integration tests: parse real .env files -> compare -> build summary."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.comparator import compare
from envdiff.differ_summary import build_diff_summary


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_clean_pair_is_clean(env_dir):
    left = _write(env_dir, ".env.dev", "FOO=bar\nBAZ=qux\n")
    right = _write(env_dir, ".env.prod", "FOO=bar\nBAZ=qux\n")
    left_env = parse_env_file(str(left))
    right_env = parse_env_file(str(right))
    result = compare(left_env, right_env, str(left), str(right))
    summary = build_diff_summary(result)
    assert summary.is_clean
    assert summary.total_keys == 2


def test_missing_key_shows_in_summary(env_dir):
    left = _write(env_dir, ".env.dev", "FOO=bar\nSECRET=abc\n")
    right = _write(env_dir, ".env.prod", "FOO=bar\n")
    left_env = parse_env_file(str(left))
    right_env = parse_env_file(str(right))
    result = compare(left_env, right_env, str(left), str(right))
    summary = build_diff_summary(result)
    assert not summary.is_clean
    statuses = {ln.key: ln.status for ln in summary.lines}
    assert statuses["SECRET"] == "missing_right"
    assert statuses["FOO"] == "match"


def test_mismatch_detail_contains_values(env_dir):
    left = _write(env_dir, ".env.dev", "PORT=3000\n")
    right = _write(env_dir, ".env.prod", "PORT=8080\n")
    left_env = parse_env_file(str(left))
    right_env = parse_env_file(str(right))
    result = compare(left_env, right_env, str(left), str(right))
    summary = build_diff_summary(result)
    line = next(ln for ln in summary.lines if ln.key == "PORT")
    assert "3000" in line.detail
    assert "8080" in line.detail


def test_as_dict_round_trip(env_dir):
    left = _write(env_dir, ".env.a", "X=1\nY=2\n")
    right = _write(env_dir, ".env.b", "X=1\nZ=3\n")
    left_env = parse_env_file(str(left))
    right_env = parse_env_file(str(right))
    result = compare(left_env, right_env, str(left), str(right))
    summary = build_diff_summary(result)
    d = summary.as_dict()
    assert d["total_keys"] == summary.total_keys
    assert d["issue_count"] == summary.issue_count
    assert len(d["lines"]) == summary.total_keys
