"""Tests for envdiff.filter module."""

from __future__ import annotations

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.filter import FilterError, filter_by_prefix, filter_keys


def _make_result(*keys: str, status: str = "missing_in_right") -> CompareResult:
    diffs = [
        KeyDiff(key=k, left_value="val", right_value=None, status=status)
        for k in keys
    ]
    return CompareResult(left_file="a.env", right_file="b.env", diffs=diffs)


# ---------------------------------------------------------------------------
# filter_keys – include
# ---------------------------------------------------------------------------

def test_include_pattern_keeps_matching_keys():
    result = _make_result("DB_HOST", "DB_PORT", "APP_NAME")
    filtered = filter_keys(result, include=["DB_*"])
    assert [d.key for d in filtered.diffs] == ["DB_HOST", "DB_PORT"]


def test_include_multiple_patterns():
    result = _make_result("DB_HOST", "APP_NAME", "REDIS_URL")
    filtered = filter_keys(result, include=["DB_*", "REDIS_*"])
    assert {d.key for d in filtered.diffs} == {"DB_HOST", "REDIS_URL"}


def test_include_no_match_returns_empty():
    result = _make_result("DB_HOST", "APP_NAME")
    filtered = filter_keys(result, include=["MISSING_*"])
    assert filtered.diffs == []


# ---------------------------------------------------------------------------
# filter_keys – exclude
# ---------------------------------------------------------------------------

def test_exclude_pattern_removes_matching_keys():
    result = _make_result("DB_HOST", "DB_PORT", "APP_NAME")
    filtered = filter_keys(result, exclude=["DB_*"])
    assert [d.key for d in filtered.diffs] == ["APP_NAME"]


def test_exclude_all_returns_empty():
    result = _make_result("DB_HOST", "APP_NAME")
    filtered = filter_keys(result, exclude=["*"])
    assert filtered.diffs == []


# ---------------------------------------------------------------------------
# filter_keys – include + exclude combined
# ---------------------------------------------------------------------------

def test_include_and_exclude_combined():
    result = _make_result("DB_HOST", "DB_PASSWORD", "APP_NAME")
    filtered = filter_keys(result, include=["DB_*"], exclude=["*PASSWORD*"])
    assert [d.key for d in filtered.diffs] == ["DB_HOST"]


# ---------------------------------------------------------------------------
# filter_keys – no filters
# ---------------------------------------------------------------------------

def test_no_filters_returns_all_diffs():
    result = _make_result("DB_HOST", "APP_NAME")
    filtered = filter_keys(result)
    assert len(filtered.diffs) == 2


# ---------------------------------------------------------------------------
# filter_keys – metadata preserved
# ---------------------------------------------------------------------------

def test_file_names_are_preserved():
    result = _make_result("DB_HOST")
    filtered = filter_keys(result, include=["DB_*"])
    assert filtered.left_file == "a.env"
    assert filtered.right_file == "b.env"


# ---------------------------------------------------------------------------
# filter_by_prefix
# ---------------------------------------------------------------------------

def test_filter_by_prefix_keeps_matching():
    result = _make_result("AWS_KEY", "AWS_SECRET", "DB_HOST")
    filtered = filter_by_prefix(result, "AWS_")
    assert {d.key for d in filtered.diffs} == {"AWS_KEY", "AWS_SECRET"}


def test_filter_by_prefix_case_insensitive():
    result = _make_result("aws_key", "DB_HOST")
    filtered = filter_by_prefix(result, "AWS_")
    assert [d.key for d in filtered.diffs] == ["aws_key"]


# ---------------------------------------------------------------------------
# FilterError
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises_filter_error():
    result = _make_result("DB_HOST")
    # Passing a raw regex special sequence that fnmatch.translate wraps safely
    # Use a deliberately broken approach: patch with an invalid regex string.
    with pytest.raises(FilterError):
        # Force an error by monkeypatching fnmatch.translate
        import envdiff.filter as fmod
        original = fmod.fnmatch.translate
        fmod.fnmatch.translate = lambda _: "[invalid"
        try:
            filter_keys(result, include=["*"])
        finally:
            fmod.fnmatch.translate = original
