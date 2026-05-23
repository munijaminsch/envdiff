"""Tests for envdiff.comparator_chain."""

import pytest

from envdiff.comparator import compare
from envdiff.comparator_chain import (
    ChainEntry,
    ChainError,
    ChainResult,
    build_chain,
)


def _pair(left: dict, right: dict, lname="a.env", rname="b.env"):
    return (lname, rname, compare(left, right, left_name=lname, right_name=rname))


# ---------------------------------------------------------------------------
# build_chain input validation
# ---------------------------------------------------------------------------

def test_build_chain_raises_on_non_list():
    with pytest.raises(ChainError):
        build_chain("not a list")  # type: ignore


def test_build_chain_raises_on_bad_tuple_length():
    with pytest.raises(ChainError, match="3-tuple"):
        build_chain([("only", "two")])


def test_build_chain_raises_on_wrong_result_type():
    with pytest.raises(ChainError, match="CompareResult"):
        build_chain([("a", "b", {"not": "a result"})])


# ---------------------------------------------------------------------------
# ChainResult structure
# ---------------------------------------------------------------------------

def test_returns_chain_result():
    result = build_chain([_pair({"A": "1"}, {"A": "1"})])
    assert isinstance(result, ChainResult)


def test_empty_chain_is_clean():
    result = build_chain([])
    assert result.is_clean()
    assert result.total_pairs == 0


def test_total_pairs_count():
    pairs = [_pair({"A": "1"}, {"A": "1"}), _pair({"B": "2"}, {"B": "2"})]
    result = build_chain(pairs)
    assert result.total_pairs == 2


def test_clean_pairs_all_match():
    pairs = [_pair({"A": "1"}, {"A": "1"}), _pair({"B": "2"}, {"B": "2"})]
    result = build_chain(pairs)
    assert result.clean_pairs == 2
    assert result.dirty_pairs == 0


def test_dirty_pairs_detected():
    pairs = [
        _pair({"A": "1"}, {"A": "1"}),
        _pair({"B": "2"}, {"B": "9"}),
    ]
    result = build_chain(pairs)
    assert result.dirty_pairs == 1
    assert result.clean_pairs == 1


def test_is_clean_false_when_differences():
    pairs = [_pair({"A": "1"}, {"A": "2"})]
    result = build_chain(pairs)
    assert not result.is_clean()


# ---------------------------------------------------------------------------
# ChainEntry
# ---------------------------------------------------------------------------

def test_entry_index_assigned():
    result = build_chain([_pair({}, {}), _pair({}, {})])
    assert result.entries[0].index == 0
    assert result.entries[1].index == 1


def test_entry_stores_names():
    result = build_chain([_pair({}, {}, lname="dev.env", rname="prod.env")])
    entry = result.entries[0]
    assert entry.left == "dev.env"
    assert entry.right == "prod.env"


def test_entry_as_dict_has_differences_key():
    result = build_chain([_pair({"X": "1"}, {"X": "1"})])
    d = result.entries[0].as_dict()
    assert "has_differences" in d
    assert d["has_differences"] is False


def test_entry_as_dict_missing_in_right():
    result = build_chain([_pair({"A": "1", "B": "2"}, {"A": "1"})])
    d = result.entries[0].as_dict()
    assert "B" in d["missing_in_right"]


# ---------------------------------------------------------------------------
# ChainResult.as_dict
# ---------------------------------------------------------------------------

def test_as_dict_top_level_keys():
    result = build_chain([_pair({"K": "v"}, {"K": "v"})])
    d = result.as_dict()
    for key in ("total_pairs", "clean_pairs", "dirty_pairs", "is_clean", "entries"):
        assert key in d


def test_as_dict_entries_list_length():
    pairs = [_pair({}, {}), _pair({}, {})]
    result = build_chain(pairs)
    assert len(result.as_dict()["entries"]) == 2
