"""Tests for envdiff.inspector."""

import pytest

from envdiff.inspector import (
    InspectError,
    InspectResult,
    KeyInspection,
    inspect_env,
)


def _env(**kwargs) -> dict:
    return dict(kwargs)


def test_returns_inspect_result():
    result = inspect_env({"KEY": "value"}, source="test.env")
    assert isinstance(result, InspectResult)


def test_source_stored():
    result = inspect_env({}, source="prod.env")
    assert result.source == "prod.env"


def test_total_keys_count():
    result = inspect_env({"A": "1", "B": "2", "C": "3"})
    assert result.total_keys == 3


def test_empty_value_detected():
    result = inspect_env({"EMPTY": "", "FULL": "hello"})
    assert "EMPTY" in result.empty_keys
    assert "FULL" not in result.empty_keys


def test_numeric_value_detected():
    result = inspect_env({"PORT": "8080", "HOST": "localhost"})
    assert "PORT" in result.numeric_keys
    assert "HOST" not in result.numeric_keys


def test_float_is_numeric():
    result = inspect_env({"RATIO": "3.14"})
    assert "RATIO" in result.numeric_keys


def test_boolean_value_detected():
    for val in ("true", "false", "yes", "no", "1", "0", "on", "off"):
        result = inspect_env({"FLAG": val})
        assert "FLAG" in result.boolean_keys, f"Expected {val!r} to be boolean"


def test_boolean_case_insensitive():
    result = inspect_env({"FLAG": "TRUE"})
    assert "FLAG" in result.boolean_keys


def test_whitespace_in_value():
    result = inspect_env({"MSG": "hello world"})
    insp = result.inspections[0]
    assert insp.has_whitespace is True


def test_no_whitespace_in_value():
    result = inspect_env({"KEY": "nospace"})
    assert result.inspections[0].has_whitespace is False


def test_uppercase_key():
    result = inspect_env({"MY_KEY": "v"})
    assert result.inspections[0].uppercase is True


def test_lowercase_key_not_uppercase():
    result = inspect_env({"my_key": "v"})
    assert result.inspections[0].uppercase is False


def test_none_env_raises():
    with pytest.raises(InspectError):
        inspect_env(None)  # type: ignore


def test_as_dict_structure():
    result = inspect_env({"DB_HOST": "localhost"}, source="dev.env")
    d = result.as_dict()
    assert d["source"] == "dev.env"
    assert d["total_keys"] == 1
    assert "inspections" in d
    assert isinstance(d["inspections"], list)


def test_key_inspection_as_dict():
    result = inspect_env({"PORT": "5432"})
    item = result.inspections[0].as_dict()
    assert item["key"] == "PORT"
    assert item["is_numeric"] is True
    assert item["length"] == 4


def test_empty_env_returns_zero_keys():
    result = inspect_env({})
    assert result.total_keys == 0
    assert result.empty_keys == []
