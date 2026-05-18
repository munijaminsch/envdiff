"""Tests for envdiff.caster."""

import pytest

from envdiff.caster import CastEntry, CastError, CastResult, cast_env, _cast_value


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# --- _cast_value unit tests ---


@pytest.mark.parametrize("raw", ["true", "True", "TRUE", "yes", "YES", "1", "on"])
def test_cast_value_truthy(raw):
    assert _cast_value(raw) is True


@pytest.mark.parametrize("raw", ["false", "False", "FALSE", "no", "NO", "0", "off"])
def test_cast_value_falsy(raw):
    assert _cast_value(raw) is False


def test_cast_value_integer():
    assert _cast_value("42") == 42
    assert isinstance(_cast_value("42"), int)


def test_cast_value_negative_integer():
    assert _cast_value("-7") == -7


def test_cast_value_float():
    result = _cast_value("3.14")
    assert isinstance(result, float)
    assert abs(result - 3.14) < 1e-9


def test_cast_value_string_unchanged():
    assert _cast_value("hello") == "hello"
    assert isinstance(_cast_value("hello"), str)


def test_cast_value_empty_string():
    assert _cast_value("") == ""


# --- cast_env tests ---


def test_cast_env_returns_cast_result():
    result = cast_env(_env(KEY="value"), source="test.env")
    assert isinstance(result, CastResult)


def test_cast_env_source_stored():
    result = cast_env(_env(A="1"), source="prod.env")
    assert result.source == "prod.env"


def test_cast_env_total_keys():
    result = cast_env(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


def test_cast_env_bool_entry():
    result = cast_env(_env(FLAG="true"))
    entry = result.entries[0]
    assert entry.cast_value is True
    assert entry.cast_type == "bool"
    assert entry.raw == "true"


def test_cast_env_int_entry():
    result = cast_env(_env(PORT="8080"))
    entry = result.entries[0]
    assert entry.cast_value == 8080
    assert entry.cast_type == "int"


def test_cast_env_float_entry():
    result = cast_env(_env(RATIO="0.5"))
    entry = result.entries[0]
    assert entry.cast_type == "float"


def test_cast_env_str_entry():
    result = cast_env(_env(NAME="alice"))
    entry = result.entries[0]
    assert entry.cast_value == "alice"
    assert entry.cast_type == "str"


def test_cast_env_empty_dict():
    result = cast_env({}, source="empty.env")
    assert result.total_keys == 0
    assert result.entries == []


def test_cast_env_raises_on_none():
    with pytest.raises(CastError):
        cast_env(None)  # type: ignore


def test_as_dict_structure():
    result = cast_env(_env(DEBUG="false", PORT="3000"), source="dev.env")
    d = result.as_dict()
    assert d["source"] == "dev.env"
    assert d["total_keys"] == 2
    assert isinstance(d["entries"], list)
    keys_in_dict = {e["key"] for e in d["entries"]}
    assert keys_in_dict == {"DEBUG", "PORT"}


def test_cast_entry_as_dict_keys():
    entry = CastEntry(key="X", raw="1", cast_value=1, cast_type="int")
    d = entry.as_dict()
    assert set(d.keys()) == {"key", "raw", "cast_value", "cast_type"}
