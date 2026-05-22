"""Tests for envdiff.extractor."""
import pytest

from envdiff.extractor import (
    ExtractError,
    ExtractResult,
    ExtractedKey,
    extract_keys,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Basic return type
# ---------------------------------------------------------------------------

def test_returns_extract_result():
    result = extract_keys(_env(A="1"), ["A"])
    assert isinstance(result, ExtractResult)


def test_source_stored():
    result = extract_keys(_env(A="1"), ["A"], source="prod.env")
    assert result.source == "prod.env"


def test_default_source_is_empty_string():
    result = extract_keys(_env(A="1"), ["A"])
    assert result.source == ""


def test_keys_requested_stored():
    result = extract_keys(_env(A="1", B="2"), ["A", "B"])
    assert result.keys_requested == ["A", "B"]


# ---------------------------------------------------------------------------
# Successful extraction
# ---------------------------------------------------------------------------

def test_found_key_in_entries():
    result = extract_keys(_env(FOO="bar"), ["FOO"])
    assert len(result.entries) == 1
    assert result.entries[0].key == "FOO"
    assert result.entries[0].value == "bar"


def test_total_keys_matches_found_count():
    result = extract_keys(_env(A="1", B="2", C="3"), ["A", "C"])
    assert result.total_keys == 2


def test_is_complete_when_all_keys_found():
    result = extract_keys(_env(X="x", Y="y"), ["X", "Y"])
    assert result.is_complete is True


def test_entries_are_extracted_key_instances():
    result = extract_keys(_env(K="v"), ["K"])
    assert all(isinstance(e, ExtractedKey) for e in result.entries)


# ---------------------------------------------------------------------------
# Missing keys
# ---------------------------------------------------------------------------

def test_missing_key_recorded():
    result = extract_keys(_env(A="1"), ["A", "MISSING"])
    assert "MISSING" in result.missing


def test_missing_key_not_in_entries():
    result = extract_keys(_env(A="1"), ["A", "GHOST"])
    entry_keys = [e.key for e in result.entries]
    assert "GHOST" not in entry_keys


def test_is_complete_false_when_missing():
    result = extract_keys(_env(A="1"), ["A", "B"])
    assert result.is_complete is False


def test_all_keys_missing():
    result = extract_keys(_env(A="1"), ["X", "Y"])
    assert result.total_keys == 0
    assert len(result.missing) == 2


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_has_expected_keys():
    result = extract_keys(_env(A="1"), ["A"], source="s")
    d = result.as_dict()
    for k in ("source", "keys_requested", "total_keys", "is_complete", "entries", "missing"):
        assert k in d


def test_as_dict_entries_are_dicts():
    result = extract_keys(_env(A="1"), ["A"])
    assert all(isinstance(e, dict) for e in result.as_dict()["entries"])


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_raises_for_none_env():
    with pytest.raises(ExtractError):
        extract_keys(None, ["A"])  # type: ignore[arg-type]


def test_raises_for_empty_key_list():
    with pytest.raises(ExtractError):
        extract_keys(_env(A="1"), [])
