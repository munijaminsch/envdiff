"""Tests for envdiff.sorter."""

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.sorter import SortError, SortOrder, SortedResult, sort_result


def _make_result(*diffs: KeyDiff) -> CompareResult:
    result = CompareResult(left_file="a.env", right_file="b.env")
    result.diffs = list(diffs)
    return result


def _diff(key, left=None, right=None):
    return KeyDiff(key=key, left=left, right=right)


# ---------------------------------------------------------------------------
# sort_result – alpha order
# ---------------------------------------------------------------------------

def test_alpha_order_sorts_keys():
    result = _make_result(_diff("ZEBRA", "1", "1"), _diff("ALPHA", "2", "2"), _diff("MANGO", "3", "3"))
    sorted_r = sort_result(result, SortOrder.ALPHA)
    assert sorted_r.keys == ["ALPHA", "MANGO", "ZEBRA"]


def test_alpha_order_is_case_insensitive():
    result = _make_result(_diff("b_KEY", "1", "1"), _diff("A_KEY", "2", "2"))
    sorted_r = sort_result(result, SortOrder.ALPHA)
    assert sorted_r.keys[0] == "A_KEY"


def test_alpha_order_is_default():
    result = _make_result(_diff("Z", "1", "1"), _diff("A", "1", "1"))
    sorted_r = sort_result(result)
    assert sorted_r.keys == ["A", "Z"]


# ---------------------------------------------------------------------------
# sort_result – status order
# ---------------------------------------------------------------------------

def test_status_order_missing_right_first():
    result = _make_result(
        _diff("MATCH", "v", "v"),
        _diff("GONE_RIGHT", "v", None),
        _diff("MISMATCH", "v", "w"),
        _diff("GONE_LEFT", None, "v"),
    )
    sorted_r = sort_result(result, SortOrder.STATUS)
    statuses = [_diff_status(d) for d in sorted_r.diffs]
    assert statuses == ["missing_in_right", "missing_in_left", "mismatch", "match"]


def _diff_status(d: KeyDiff) -> str:
    if d.right is None:
        return "missing_in_right"
    if d.left is None:
        return "missing_in_left"
    if d.left != d.right:
        return "mismatch"
    return "match"


def test_status_order_secondary_alpha_sort():
    result = _make_result(_diff("Z_MISS", "v", None), _diff("A_MISS", "v", None))
    sorted_r = sort_result(result, SortOrder.STATUS)
    assert sorted_r.keys == ["A_MISS", "Z_MISS"]


# ---------------------------------------------------------------------------
# SortedResult helpers
# ---------------------------------------------------------------------------

def test_sorted_result_keys_property():
    result = _make_result(_diff("FOO", "1", "1"), _diff("BAR", "2", "2"))
    sorted_r = sort_result(result, SortOrder.ALPHA)
    assert "FOO" in sorted_r.keys
    assert "BAR" in sorted_r.keys


def test_sorted_result_as_dict_contains_order():
    result = _make_result(_diff("KEY", "v", "v"))
    d = sort_result(result, SortOrder.STATUS).as_dict()
    assert d["order"] == "status"


def test_sorted_result_as_dict_diffs_list():
    result = _make_result(_diff("KEY", "v", None))
    d = sort_result(result, SortOrder.ALPHA).as_dict()
    assert d["diffs"][0]["key"] == "KEY"
    assert d["diffs"][0]["status"] == "missing_in_right"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_raises_for_non_compare_result():
    with pytest.raises(SortError, match="CompareResult"):
        sort_result({"not": "a result"})  # type: ignore


def test_empty_result_returns_empty_sorted():
    result = _make_result()
    sorted_r = sort_result(result)
    assert sorted_r.diffs == []
    assert sorted_r.keys == []
