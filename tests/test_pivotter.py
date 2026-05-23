"""Tests for envdiff.pivotter."""
from __future__ import annotations

import pytest

from envdiff.pivotter import (
    PivotEntry,
    PivotError,
    PivotResult,
    pivot_env,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# pivot_env return type
# ---------------------------------------------------------------------------

def test_returns_pivot_result():
    result = pivot_env(_env(A="1"))
    assert isinstance(result, PivotResult)


def test_source_stored():
    result = pivot_env(_env(A="1"), source="prod.env")
    assert result.source == "prod.env"


def test_default_source_is_empty_string():
    result = pivot_env(_env(A="1"))
    assert result.source == ""


# ---------------------------------------------------------------------------
# counts
# ---------------------------------------------------------------------------

def test_total_values_unique():
    result = pivot_env(_env(A="1", B="2", C="3"))
    assert result.total_values == 3


def test_total_values_shared():
    result = pivot_env(_env(A="x", B="x", C="y"))
    assert result.total_values == 2


def test_total_keys():
    result = pivot_env(_env(A="x", B="x", C="y"))
    assert result.total_keys == 3


def test_empty_env_has_zero_values():
    result = pivot_env({})
    assert result.total_values == 0
    assert result.total_keys == 0


# ---------------------------------------------------------------------------
# is_clean / shared_entries
# ---------------------------------------------------------------------------

def test_is_clean_when_all_unique():
    result = pivot_env(_env(A="1", B="2"))
    assert result.is_clean is True


def test_not_clean_when_shared_value():
    result = pivot_env(_env(A="same", B="same"))
    assert result.is_clean is False


def test_shared_entries_returned():
    result = pivot_env(_env(A="dup", B="dup", C="unique"))
    assert len(result.shared_entries) == 1
    assert result.shared_entries[0].value == "dup"
    assert set(result.shared_entries[0].keys) == {"A", "B"}


def test_no_shared_entries_when_clean():
    result = pivot_env(_env(A="1", B="2"))
    assert result.shared_entries == []


# ---------------------------------------------------------------------------
# ignore_empty flag
# ---------------------------------------------------------------------------

def test_ignore_empty_excludes_blank_values():
    result = pivot_env(_env(A="", B="val"), ignore_empty=True)
    assert result.total_keys == 1


def test_ignore_empty_false_includes_blank_values():
    result = pivot_env(_env(A="", B="val"), ignore_empty=False)
    assert result.total_keys == 2


# ---------------------------------------------------------------------------
# entries ordering & structure
# ---------------------------------------------------------------------------

def test_entries_sorted_by_value():
    result = pivot_env(_env(A="zebra", B="apple"))
    values = [e.value for e in result.entries]
    assert values == sorted(values)


def test_entry_keys_are_list():
    result = pivot_env(_env(A="1"))
    assert isinstance(result.entries[0].keys, list)


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    result = pivot_env(_env(A="v"), source="test.env")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "total_values", "total_keys", "is_clean", "entries"}


def test_as_dict_entry_structure():
    result = pivot_env(_env(A="v"))
    entry_dict = result.as_dict()["entries"][0]
    assert set(entry_dict.keys()) == {"value", "keys"}


def test_entry_as_dict_keys_sorted():
    result = pivot_env(_env(Z="shared", A="shared"))
    entry_dict = result.as_dict()["entries"][0]
    assert entry_dict["keys"] == ["A", "Z"]


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_raises_pivot_error_for_non_dict():
    with pytest.raises(PivotError):
        pivot_env(["not", "a", "dict"])  # type: ignore[arg-type]
