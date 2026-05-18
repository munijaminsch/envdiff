"""Tests for envdiff.normalizer."""

import pytest

from envdiff.normalizer import (
    NormalizeChange,
    NormalizeError,
    NormalizeResult,
    normalize_env,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# normalize_env return type
# ---------------------------------------------------------------------------

def test_returns_normalize_result():
    result = normalize_env({"KEY": "value"}, source="test.env")
    assert isinstance(result, NormalizeResult)


def test_source_stored():
    result = normalize_env({}, source="prod.env")
    assert result.source == "prod.env"


# ---------------------------------------------------------------------------
# uppercase_keys
# ---------------------------------------------------------------------------

def test_lowercase_key_uppercased():
    result = normalize_env({"db_host": "localhost"})
    assert "DB_HOST" in result.env
    assert "db_host" not in result.env


def test_mixed_case_key_uppercased():
    result = normalize_env({"ApiKey": "abc123"})
    assert "APIKEY" in result.env


def test_already_uppercase_produces_no_change():
    result = normalize_env({"PORT": "8080"})
    assert result.is_clean


# ---------------------------------------------------------------------------
# strip_values
# ---------------------------------------------------------------------------

def test_value_with_trailing_space_stripped():
    result = normalize_env({"KEY": "value   "})
    assert result.env["KEY"] == "value"


def test_value_with_leading_space_stripped():
    result = normalize_env({"KEY": "   value"})
    assert result.env["KEY"] == "value"


def test_clean_value_produces_no_change():
    result = normalize_env({"KEY": "value"})
    assert result.is_clean
    assert result.change_count == 0


# ---------------------------------------------------------------------------
# replace_spaces_in_keys
# ---------------------------------------------------------------------------

def test_space_in_key_replaced_with_underscore():
    result = normalize_env({"my key": "val"})
    assert "MY_KEY" in result.env


def test_replace_spaces_disabled_keeps_spaces():
    result = normalize_env(
        {"my key": "val"},
        uppercase_keys=False,
        replace_spaces_in_keys=False,
    )
    assert "my key" in result.env


# ---------------------------------------------------------------------------
# change tracking
# ---------------------------------------------------------------------------

def test_changes_recorded_for_modified_key():
    result = normalize_env({"db_host": "localhost"})
    assert result.change_count == 1
    assert isinstance(result.changes[0], NormalizeChange)


def test_change_contains_original_and_normalized():
    result = normalize_env({"db_host": "localhost"})
    change = result.changes[0]
    assert "db_host" in change.original
    assert "DB_HOST" in change.normalized


def test_multiple_changes_all_recorded():
    result = normalize_env({"a": "  x  ", "b": "  y  "})
    assert result.change_count == 2


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_has_expected_keys():
    result = normalize_env({"KEY": "val"}, source="s.env")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "change_count", "is_clean", "changes", "env"}


def test_change_as_dict_has_expected_keys():
    result = normalize_env({"lower": "val"})
    d = result.changes[0].as_dict()
    assert set(d.keys()) == {"key", "original", "normalized"}


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_none_env_raises_normalize_error():
    with pytest.raises(NormalizeError):
        normalize_env(None)  # type: ignore


def test_empty_env_is_clean():
    result = normalize_env({})
    assert result.is_clean
    assert result.env == {}
