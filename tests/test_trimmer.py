"""Tests for envdiff.trimmer."""
import pytest

from envdiff.trimmer import TrimChange, TrimError, TrimResult, trim_values


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# TrimResult properties
# ---------------------------------------------------------------------------

def test_returns_trim_result():
    result = trim_values(_env(KEY="value"))
    assert isinstance(result, TrimResult)


def test_source_stored():
    result = trim_values(_env(KEY="v"), source="prod.env")
    assert result.source == "prod.env"


def test_is_clean_when_no_changes():
    result = trim_values(_env(A="clean", B="also_clean"))
    assert result.is_clean is True
    assert result.change_count == 0


def test_not_clean_when_changes_present():
    result = trim_values(_env(A=" padded "))
    assert result.is_clean is False
    assert result.change_count == 1


# ---------------------------------------------------------------------------
# Trimming behaviour
# ---------------------------------------------------------------------------

def test_leading_whitespace_trimmed():
    result = trim_values(_env(KEY="  hello"))
    assert result.env["KEY"] == "hello"


def test_trailing_whitespace_trimmed():
    result = trim_values(_env(KEY="hello   "))
    assert result.env["KEY"] == "hello"


def test_both_sides_trimmed():
    result = trim_values(_env(KEY="  hello  "))
    assert result.env["KEY"] == "hello"


def test_inner_whitespace_preserved():
    result = trim_values(_env(KEY="hello world"))
    assert result.env["KEY"] == "hello world"
    assert result.is_clean is True


def test_empty_value_unchanged():
    result = trim_values(_env(KEY=""))
    assert result.env["KEY"] == ""
    assert result.is_clean is True


def test_only_whitespace_becomes_empty():
    result = trim_values(_env(KEY="   "))
    assert result.env["KEY"] == ""
    assert result.change_count == 1


# ---------------------------------------------------------------------------
# TrimChange details
# ---------------------------------------------------------------------------

def test_change_records_original_and_trimmed():
    result = trim_values(_env(KEY=" val "))
    assert len(result.changes) == 1
    ch = result.changes[0]
    assert isinstance(ch, TrimChange)
    assert ch.key == "KEY"
    assert ch.original == " val "
    assert ch.trimmed == "val"


def test_change_as_dict_keys():
    result = trim_values(_env(KEY=" v "))
    d = result.changes[0].as_dict()
    assert set(d.keys()) == {"key", "original", "trimmed"}


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    result = trim_values(_env(A=" x ", B="y"), source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["change_count"] == 1
    assert d["is_clean"] is False
    assert "changes" in d
    assert "env" in d


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_raises_for_non_dict():
    with pytest.raises(TrimError):
        trim_values(["not", "a", "dict"])  # type: ignore


def test_empty_env_returns_clean_result():
    result = trim_values({})
    assert result.is_clean is True
    assert result.env == {}
