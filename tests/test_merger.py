"""Tests for envdiff.merger."""

import pytest

from envdiff.merger import (
    MergeConflict,
    MergeError,
    MergeResult,
    merge_envs,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _named(*pairs):
    """Build a list of (name, dict) tuples from keyword-style args."""
    return list(pairs)


# ---------------------------------------------------------------------------
# MergeConflict.__str__
# ---------------------------------------------------------------------------

def test_conflict_str_contains_key():
    c = MergeConflict(key="DB_HOST", values={"a.env": "localhost", "b.env": "prod"})
    assert "DB_HOST" in str(c)


def test_conflict_str_contains_filenames():
    c = MergeConflict(key="X", values={"dev.env": "1", "prod.env": "2"})
    assert "dev.env" in str(c)
    assert "prod.env" in str(c)


# ---------------------------------------------------------------------------
# merge_envs — basic merging
# ---------------------------------------------------------------------------

def test_merge_single_env_returns_same_keys():
    result = merge_envs([("a.env", {"FOO": "bar", "BAZ": "qux"})])
    assert result.merged == {"FOO": "bar", "BAZ": "qux"}


def test_merge_no_conflicts_combines_keys():
    result = merge_envs([
        ("a.env", {"A": "1"}),
        ("b.env", {"B": "2"}),
    ])
    assert result.merged == {"A": "1", "B": "2"}
    assert not result.has_conflicts


def test_sources_recorded():
    result = merge_envs([("x.env", {}), ("y.env", {})])
    assert result.sources == ["x.env", "y.env"]


def test_merge_empty_list_raises():
    """merge_envs should raise MergeError when given no environments."""
    with pytest.raises(MergeError):
        merge_envs([])


# ---------------------------------------------------------------------------
# merge_envs — conflict detection
# ---------------------------------------------------------------------------

def test_detects_value_conflict():
    result = merge_envs([
        ("dev.env", {"HOST": "localhost"}),
        ("prod.env", {"HOST": "prod.example.com"}),
    ])
    assert result.has_conflicts
    assert "HOST" in result.conflict_keys


def test_no_conflict_for_identical_values():
    result = merge_envs([
        ("a.env", {"PORT": "5432"}),
        ("b.env", {"PORT": "5432"}),
    ])
    assert not result.has_conflicts


def test_conflict_count_matches():
    result = merge_envs([
        ("a.env", {"X": "1", "Y": "hello"}),
        ("b.env", {"X": "2", "Y": "hello"}),
    ])
    assert len(result.conflicts) == 1


# ---------------------------------------------------------------------------
# merge_envs — strategies
# ---------------------------------------------------------------------------

def test_strategy_first_keeps_first_value():
    result = merge_envs([
        ("a.env", {"KEY": "first"}),
        ("b.env", {"KEY": "second"}),
    ], strategy="first")
    assert result.merged["KEY"] == "first"


def test_strategy_last_keeps_last_value():
    result = merge_envs([
        ("a.env", {"KEY": "first"}),
        ("b.env", {"KEY": "second"}),
    ], strategy="last")
    assert result.merged["KEY"] == "second"


def test_invalid_strategy_raises():
    """An unrecognised strategy name should raise MergeError."""
    with pytest.raises(MergeError):
        merge_envs(
            [("a.env", {"KEY": "value"})],
            strategy="nonexistent_strategy",
        )
