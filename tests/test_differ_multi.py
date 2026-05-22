"""Unit tests for envdiff.differ_multi."""
from __future__ import annotations

import pytest

from envdiff.differ_multi import MultiDiffError, MultiDiffResult, PairDiff, diff_multi


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


def test_diff_multi_requires_two_files(env_dir):
    f = _write(env_dir / "a.env", "KEY=1\n")
    with pytest.raises(MultiDiffError, match="At least two"):
        diff_multi([f])


def test_diff_multi_returns_multi_diff_result(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    result = diff_multi([a, b])
    assert isinstance(result, MultiDiffResult)


def test_clean_files_is_clean(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\nFOO=bar\n")
    b = _write(env_dir / "b.env", "KEY=1\nFOO=bar\n")
    result = diff_multi([a, b])
    assert result.is_clean()


def test_missing_key_not_clean(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\nEXTRA=x\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    result = diff_multi([a, b])
    assert not result.is_clean()


def test_three_files_produces_three_pairs(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    c = _write(env_dir / "c.env", "KEY=1\n")
    result = diff_multi([a, b, c])
    assert result.total_pairs() == 3


def test_sources_stored(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=1\n")
    result = diff_multi([a, b])
    assert str(a) in result.sources
    assert str(b) in result.sources


def test_as_dict_contains_pairs(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=2\n")
    d = diff_multi([a, b]).as_dict()
    assert "pairs" in d
    assert len(d["pairs"]) == 1


def test_pair_diff_as_dict_keys(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    b = _write(env_dir / "b.env", "KEY=2\n")
    pair = diff_multi([a, b]).pairs[0]
    d = pair.as_dict()
    assert "left" in d and "right" in d
    assert "mismatched" in d


def test_missing_file_raises_multi_diff_error(env_dir):
    a = _write(env_dir / "a.env", "KEY=1\n")
    with pytest.raises(MultiDiffError):
        diff_multi([a, str(env_dir / "ghost.env")])


def test_mismatch_detected_in_pair(env_dir):
    a = _write(env_dir / "a.env", "KEY=hello\n")
    b = _write(env_dir / "b.env", "KEY=world\n")
    result = diff_multi([a, b])
    assert not result.is_clean()
    pair = result.pairs[0]
    assert "KEY" in [d.key for d in pair.result.mismatched_keys()]
