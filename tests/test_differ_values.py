"""Tests for envdiff.differ_values."""
import pytest

from envdiff.differ_values import (
    ValueDiffError,
    ValueDiffResult,
    ValueEntry,
    diff_values,
)


def _env(**kwargs):
    return dict(kwargs)


def test_returns_value_diff_result():
    result = diff_values(_env(A="1"), _env(A="1"))
    assert isinstance(result, ValueDiffResult)


def test_source_stored():
    result = diff_values(_env(A="1"), _env(A="2"), left_source="a.env", right_source="b.env")
    assert result.left_source == "a.env"
    assert result.right_source == "b.env"


def test_clean_when_values_match():
    result = diff_values(_env(A="1", B="2"), _env(A="1", B="2"))
    assert result.is_clean is True


def test_not_clean_when_value_differs():
    result = diff_values(_env(A="1"), _env(A="2"))
    assert result.is_clean is False


def test_only_shared_keys_included():
    result = diff_values(_env(A="1", B="2"), _env(A="1", C="3"))
    keys = [e.key for e in result.entries]
    assert keys == ["A"]
    assert "B" not in keys
    assert "C" not in keys


def test_total_keys_count():
    result = diff_values(_env(A="1", B="2", C="3"), _env(A="1", B="x", C="3"))
    assert result.total_keys == 3


def test_changed_count():
    result = diff_values(_env(A="1", B="2", C="3"), _env(A="1", B="x", C="y"))
    assert result.changed_count == 2


def test_unchanged_count():
    result = diff_values(_env(A="1", B="2", C="3"), _env(A="1", B="x", C="y"))
    assert result.unchanged_count == 1


def test_entry_fields_populated():
    result = diff_values(_env(KEY="old"), _env(KEY="new"))
    entry = result.entries[0]
    assert entry.key == "KEY"
    assert entry.left_value == "old"
    assert entry.right_value == "new"
    assert entry.changed is True


def test_entry_unchanged_flag():
    result = diff_values(_env(KEY="same"), _env(KEY="same"))
    assert result.entries[0].changed is False


def test_keys_only_filters_entries():
    result = diff_values(
        _env(A="1", B="2", C="3"),
        _env(A="1", B="9", C="3"),
        keys_only=["B"],
    )
    assert result.total_keys == 1
    assert result.entries[0].key == "B"


def test_keys_only_ignores_missing_keys():
    result = diff_values(_env(A="1"), _env(A="1"), keys_only=["A", "MISSING"])
    keys = [e.key for e in result.entries]
    assert "MISSING" not in keys


def test_entries_sorted_alphabetically():
    result = diff_values(_env(Z="1", A="2", M="3"), _env(Z="1", A="2", M="3"))
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_none_left_raises():
    with pytest.raises(ValueDiffError):
        diff_values(None, _env(A="1"))


def test_none_right_raises():
    with pytest.raises(ValueDiffError):
        diff_values(_env(A="1"), None)


def test_as_dict_structure():
    result = diff_values(_env(A="1"), _env(A="2"), left_source="l", right_source="r")
    d = result.as_dict()
    assert d["left_source"] == "l"
    assert d["right_source"] == "r"
    assert "is_clean" in d
    assert "total_keys" in d
    assert "changed_count" in d
    assert "unchanged_count" in d
    assert isinstance(d["entries"], list)


def test_entry_as_dict_keys():
    result = diff_values(_env(X="a"), _env(X="b"))
    d = result.entries[0].as_dict()
    assert set(d.keys()) == {"key", "left_value", "right_value", "changed"}
