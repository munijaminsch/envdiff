"""Integration tests: parse real files then run multi-diff."""
from __future__ import annotations

import pytest

from envdiff.differ_multi import diff_multi


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


def test_three_identical_files_is_clean(env_dir):
    content = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n"
    a = _write(env_dir / "dev.env", content)
    b = _write(env_dir / "staging.env", content)
    c = _write(env_dir / "prod.env", content)
    result = diff_multi([a, b, c])
    assert result.is_clean()
    assert result.total_pairs() == 3


def test_one_file_missing_key_surfaces_in_pair(env_dir):
    base = "DB_HOST=localhost\nDB_PORT=5432\n"
    a = _write(env_dir / "dev.env", base + "DEBUG=true\n")
    b = _write(env_dir / "staging.env", base)
    c = _write(env_dir / "prod.env", base)
    result = diff_multi([a, b, c])
    assert not result.is_clean()
    # Only pairs involving 'a' should have differences
    clean_pairs = [p for p in result.pairs if not p.result.has_differences()]
    dirty_pairs = [p for p in result.pairs if p.result.has_differences()]
    assert len(dirty_pairs) == 2
    assert len(clean_pairs) == 1


def test_comments_ignored_in_multi_diff(env_dir):
    a = _write(env_dir / "a.env", "# comment\nKEY=val\n")
    b = _write(env_dir / "b.env", "KEY=val\n")
    result = diff_multi([a, b])
    assert result.is_clean()


def test_as_dict_round_trip(env_dir):
    a = _write(env_dir / "a.env", "X=1\n")
    b = _write(env_dir / "b.env", "X=2\n")
    d = diff_multi([a, b]).as_dict()
    assert d["total_pairs"] == 1
    assert d["is_clean"] is False
    assert d["pairs"][0]["mismatched"] == ["X"]
