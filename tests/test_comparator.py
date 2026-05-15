"""Tests for envdiff.comparator module."""

import pytest
from envdiff.comparator import compare_envs, CompareResult, KeyDiff


LEFT = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
RIGHT = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}


def test_returns_compare_result():
    result = compare_envs(LEFT, RIGHT)
    assert isinstance(result, CompareResult)


def test_detects_missing_in_right():
    result = compare_envs(LEFT, RIGHT)
    keys = [d.key for d in result.missing_in_right]
    assert "DEBUG" in keys


def test_detects_missing_in_left():
    result = compare_envs(LEFT, RIGHT)
    keys = [d.key for d in result.missing_in_left]
    assert "SECRET" in keys


def test_detects_value_mismatch():
    result = compare_envs(LEFT, RIGHT)
    keys = [d.key for d in result.mismatched]
    assert "HOST" in keys


def test_no_diff_for_equal_key():
    result = compare_envs(LEFT, RIGHT)
    all_keys = [d.key for d in result.diffs]
    assert "PORT" not in all_keys


def test_identical_envs_have_no_differences():
    env = {"A": "1", "B": "2"}
    result = compare_envs(env, env)
    assert not result.has_differences
    assert result.diffs == []


def test_empty_envs_have_no_differences():
    result = compare_envs({}, {})
    assert not result.has_differences


def test_left_empty():
    result = compare_envs({}, {"KEY": "val"})
    assert len(result.missing_in_left) == 1
    assert result.missing_in_left[0].key == "KEY"
    assert result.missing_in_left[0].right_value == "val"


def test_right_empty():
    result = compare_envs({"KEY": "val"}, {})
    assert len(result.missing_in_right) == 1
    assert result.missing_in_right[0].left_value == "val"


def test_custom_names_in_result():
    result = compare_envs(LEFT, RIGHT, left_name=".env.dev", right_name=".env.prod")
    assert result.left_name == ".env.dev"
    assert result.right_name == ".env.prod"


def test_summary_contains_names():
    result = compare_envs(LEFT, RIGHT, left_name="dev", right_name="prod")
    summary = result.summary()
    assert "dev" in summary
    assert "prod" in summary


def test_summary_no_differences():
    env = {"X": "1"}
    result = compare_envs(env, env)
    assert "No differences found." in result.summary()


def test_key_diff_str_missing_in_left():
    d = KeyDiff(key="FOO", status="missing_in_left", right_value="bar")
    assert "missing in left" in str(d)
    assert "FOO" in str(d)


def test_key_diff_str_value_mismatch():
    d = KeyDiff(key="BAR", status="value_mismatch", left_value="a", right_value="b")
    assert "mismatch" in str(d)
    assert "BAR" in str(d)
