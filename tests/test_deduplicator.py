"""Tests for envdiff.deduplicator."""
import pytest

from envdiff.deduplicator import (
    DeduplicateError,
    DeduplicateResult,
    RemovedEntry,
    deduplicate,
)


def _pairs(*items):
    """Helper: accept alternating key/value strings."""
    it = iter(items)
    return list(zip(it, it))


# ---------------------------------------------------------------------------
# Basic return type
# ---------------------------------------------------------------------------

def test_returns_deduplicate_result():
    result = deduplicate([("A", "1")])
    assert isinstance(result, DeduplicateResult)


def test_source_stored():
    result = deduplicate([("A", "1")], source="prod.env")
    assert result.source == "prod.env"


def test_default_source():
    result = deduplicate([("A", "1")])
    assert result.source == "<unknown>"


# ---------------------------------------------------------------------------
# Clean inputs
# ---------------------------------------------------------------------------

def test_no_duplicates_is_clean():
    result = deduplicate([("A", "1"), ("B", "2")])
    assert result.is_clean is True


def test_no_duplicates_removed_count_zero():
    result = deduplicate([("A", "1"), ("B", "2")])
    assert result.removed_count == 0


def test_no_duplicates_env_preserved():
    result = deduplicate([("A", "1"), ("B", "2")])
    assert result.env == {"A": "1", "B": "2"}


def test_empty_pairs_is_clean():
    result = deduplicate([])
    assert result.is_clean is True
    assert result.env == {}


# ---------------------------------------------------------------------------
# Duplicate handling
# ---------------------------------------------------------------------------

def test_duplicate_key_not_clean():
    result = deduplicate([("A", "1"), ("A", "2")])
    assert result.is_clean is False


def test_duplicate_key_keeps_last_value():
    result = deduplicate([("A", "1"), ("A", "2"), ("A", "3")])
    assert result.env["A"] == "3"


def test_duplicate_removed_count():
    result = deduplicate([("A", "1"), ("A", "2"), ("B", "x"), ("B", "y")])
    assert result.removed_count == 2


def test_removed_entry_type():
    result = deduplicate([("A", "1"), ("A", "2")])
    assert isinstance(result.removed[0], RemovedEntry)


def test_removed_entry_key():
    result = deduplicate([("A", "old"), ("A", "new")])
    assert result.removed[0].key == "A"


def test_removed_entry_kept_value():
    result = deduplicate([("A", "old"), ("A", "new")])
    assert result.removed[0].kept_value == "new"


def test_removed_entry_dropped_values():
    result = deduplicate([("A", "first"), ("A", "second"), ("A", "third")])
    assert result.removed[0].dropped_values == ["first", "second"]


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_keys():
    result = deduplicate([("A", "1")])
    d = result.as_dict()
    assert set(d.keys()) == {"source", "is_clean", "removed_count", "removed", "env"}


def test_removed_entry_as_dict():
    result = deduplicate([("X", "a"), ("X", "b")])
    entry_dict = result.removed[0].as_dict()
    assert entry_dict["key"] == "X"
    assert entry_dict["kept_value"] == "b"
    assert entry_dict["dropped_values"] == ["a"]


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_none_pairs_raises():
    with pytest.raises(DeduplicateError):
        deduplicate(None)


def test_non_string_key_raises():
    with pytest.raises(DeduplicateError):
        deduplicate([(1, "value")])


def test_non_iterable_raises():
    with pytest.raises(DeduplicateError):
        deduplicate(42)
