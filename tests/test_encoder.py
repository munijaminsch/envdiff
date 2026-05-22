"""Tests for envdiff.encoder."""
import json
import pytest

from envdiff.encoder import EncodeError, EncodeResult, encode_env


def _env(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# EncodeResult
# ---------------------------------------------------------------------------

def test_encode_result_as_dict_keys():
    result = encode_env({"A": "1"}, fmt="dotenv", source="test.env")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "format", "key_count", "content"}


def test_encode_result_source_stored():
    result = encode_env({}, source="prod.env")
    assert result.source == "prod.env"


def test_encode_result_fmt_stored():
    result = encode_env({}, fmt="json")
    assert result.fmt == "json"


def test_encode_result_key_count():
    result = encode_env({"A": "1", "B": "2"})
    assert result.key_count == 2


# ---------------------------------------------------------------------------
# dotenv format
# ---------------------------------------------------------------------------

def test_dotenv_simple_key_value():
    result = encode_env({"KEY": "value"})
    assert "KEY=value" in result.content


def test_dotenv_quotes_value_with_spaces():
    result = encode_env({"KEY": "hello world"})
    assert 'KEY="hello world"' in result.content


def test_dotenv_quotes_value_with_hash():
    result = encode_env({"KEY": "val#ue"})
    assert 'KEY="val#ue"' in result.content


def test_dotenv_keys_sorted():
    result = encode_env({"ZEBRA": "z", "ALPHA": "a"})
    lines = [l for l in result.content.splitlines() if l]
    assert lines[0].startswith("ALPHA")
    assert lines[1].startswith("ZEBRA")


def test_dotenv_empty_env_produces_empty_string():
    result = encode_env({})
    assert result.content == ""


def test_dotenv_trailing_newline():
    result = encode_env({"A": "1"})
    assert result.content.endswith("\n")


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_json_is_valid_json():
    result = encode_env({"A": "1", "B": "2"}, fmt="json")
    parsed = json.loads(result.content)
    assert parsed == {"A": "1", "B": "2"}


def test_json_keys_sorted():
    result = encode_env({"Z": "z", "A": "a"}, fmt="json")
    parsed = json.loads(result.content)
    assert list(parsed.keys()) == ["A", "Z"]


# ---------------------------------------------------------------------------
# TOML format
# ---------------------------------------------------------------------------

def test_toml_simple_key_value():
    result = encode_env({"KEY": "val"}, fmt="toml")
    assert 'KEY = "val"' in result.content


def test_toml_escapes_double_quotes():
    result = encode_env({"KEY": 'say "hi"'}, fmt="toml")
    assert '\\"' in result.content


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_unknown_format_raises():
    with pytest.raises(EncodeError, match="Unknown format"):
        encode_env({}, fmt="xml")  # type: ignore[arg-type]


def test_non_dict_raises():
    with pytest.raises(EncodeError):
        encode_env("not a dict")  # type: ignore[arg-type]
