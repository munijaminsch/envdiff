"""Tests for envdiff.duplicator."""

import pytest

from envdiff.duplicator import (
    DuplicateError,
    DuplicateGroup,
    DuplicateResult,
    find_duplicates,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# DuplicateResult helpers
# ---------------------------------------------------------------------------

def test_is_clean_when_no_groups():
    result = DuplicateResult(source="test.env", groups=[])
    assert result.is_clean is True


def test_not_clean_when_groups_present():
    group = DuplicateGroup(value="x", keys=["A", "B"])
    result = DuplicateResult(source="test.env", groups=[group])
    assert result.is_clean is False


def test_total_keys_sums_all_groups():
    g1 = DuplicateGroup(value="x", keys=["A", "B"])
    g2 = DuplicateGroup(value="y", keys=["C", "D", "E"])
    result = DuplicateResult(source="", groups=[g1, g2])
    assert result.total_keys == 5


def test_as_dict_structure():
    group = DuplicateGroup(value="secret", keys=["TOKEN", "KEY"])
    result = DuplicateResult(source="a.env", groups=[group])
    d = result.as_dict()
    assert d["source"] == "a.env"
    assert d["is_clean"] is False
    assert len(d["duplicate_groups"]) == 1
    assert d["duplicate_groups"][0]["value"] == "secret"
    assert "TOKEN" in d["duplicate_groups"][0]["keys"]


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_clean_env_returns_no_groups():
    env = _env(A="1", B="2", C="3")
    result = find_duplicates(env, source="clean.env")
    assert result.is_clean
    assert result.groups == []


def test_detects_single_duplicate_group():
    env = _env(A="same", B="same", C="different")
    result = find_duplicates(env)
    assert len(result.groups) == 1
    assert set(result.groups[0].keys) == {"A", "B"}
    assert result.groups[0].value == "same"


def test_detects_multiple_duplicate_groups():
    env = _env(A="x", B="x", C="y", D="y", E="unique")
    result = find_duplicates(env)
    assert len(result.groups) == 2


def test_source_stored_in_result():
    result = find_duplicates({}, source="prod.env")
    assert result.source == "prod.env"


def test_groups_sorted_by_value():
    env = _env(A="zebra", B="zebra", C="apple", D="apple")
    result = find_duplicates(env)
    values = [g.value for g in result.groups]
    assert values == sorted(values)


def test_ignore_empty_excludes_empty_values():
    env = _env(A="", B="", C="real", D="real")
    result = find_duplicates(env, ignore_empty=True)
    assert len(result.groups) == 1
    assert result.groups[0].value == "real"


def test_empty_values_counted_when_flag_false():
    env = _env(A="", B="")
    result = find_duplicates(env, ignore_empty=False)
    assert len(result.groups) == 1


def test_none_env_raises_duplicate_error():
    with pytest.raises(DuplicateError):
        find_duplicates(None)  # type: ignore


def test_empty_env_returns_clean_result():
    result = find_duplicates({})
    assert result.is_clean
    assert result.total_keys == 0


def test_group_keys_are_sorted_in_as_dict():
    group = DuplicateGroup(value="v", keys=["Z", "A", "M"])
    d = group.as_dict()
    assert d["keys"] == ["A", "M", "Z"]
