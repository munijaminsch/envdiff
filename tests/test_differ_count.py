"""Tests for envdiff.differ_count."""
import pytest

from envdiff.differ_count import (
    CountDiffError,
    CountDiffResult,
    CountEntry,
    diff_counts,
)


def _env(**kwargs):
    return dict(kwargs)


def test_returns_count_diff_result():
    result = diff_counts(_env(A="1"), _env(A="1"))
    assert isinstance(result, CountDiffResult)


def test_source_stored():
    result = diff_counts(_env(), _env(), left_source="l.env", right_source="r.env")
    assert result.left_source == "l.env"
    assert result.right_source == "r.env"


def test_left_total_count():
    result = diff_counts(_env(A="1", B="2"), _env())
    assert result.left_total == 2


def test_right_total_count():
    result = diff_counts(_env(), _env(X="1", Y="2", Z="3"))
    assert result.right_total == 3


def test_is_clean_when_same_count():
    result = diff_counts(_env(A="1", B="2"), _env(C="3", D="4"))
    assert result.is_clean is True


def test_not_clean_when_different_count():
    result = diff_counts(_env(A="1"), _env(A="1", B="2"))
    assert result.is_clean is False


def test_net_delta_positive():
    result = diff_counts(_env(A="1"), _env(A="1", B="2"))
    assert result.net_delta == 1


def test_net_delta_negative():
    result = diff_counts(_env(A="1", B="2"), _env(A="1"))
    assert result.net_delta == -1


def test_net_delta_zero():
    result = diff_counts(_env(A="1"), _env(B="2"))
    assert result.net_delta == 0


def test_entries_include_all_keys():
    result = diff_counts(_env(A="1"), _env(B="2"))
    keys = {e.key for e in result.entries}
    assert keys == {"A", "B"}


def test_entry_delta_for_left_only_key():
    result = diff_counts(_env(A="1"), _env())
    entry = next(e for e in result.entries if e.key == "A")
    assert entry.left_count == 1
    assert entry.right_count == 0
    assert entry.delta == -1


def test_entry_delta_for_right_only_key():
    result = diff_counts(_env(), _env(B="2"))
    entry = next(e for e in result.entries if e.key == "B")
    assert entry.left_count == 0
    assert entry.right_count == 1
    assert entry.delta == 1


def test_entry_delta_for_shared_key():
    result = diff_counts(_env(A="1"), _env(A="2"))
    entry = result.entries[0]
    assert entry.key == "A"
    assert entry.delta == 0


def test_entries_sorted_alphabetically():
    result = diff_counts(_env(Z="1", A="2"), _env(M="3"))
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_raises_on_non_dict_left():
    with pytest.raises(CountDiffError):
        diff_counts(None, {})


def test_raises_on_non_dict_right():
    with pytest.raises(CountDiffError):
        diff_counts({}, "bad")


def test_as_dict_structure():
    result = diff_counts(_env(A="1"), _env(A="1", B="2"), left_source="a", right_source="b")
    d = result.as_dict()
    assert d["left_source"] == "a"
    assert d["right_source"] == "b"
    assert d["left_total"] == 1
    assert d["right_total"] == 2
    assert d["net_delta"] == 1
    assert d["is_clean"] is False
    assert isinstance(d["entries"], list)


def test_count_entry_as_dict():
    e = CountEntry(key="FOO", left_count=1, right_count=0, delta=-1)
    d = e.as_dict()
    assert d == {"key": "FOO", "left_count": 1, "right_count": 0, "delta": -1}
