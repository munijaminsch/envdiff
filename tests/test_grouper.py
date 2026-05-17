"""Tests for envdiff.grouper."""

import pytest

from envdiff.grouper import (
    EnvGroup,
    GroupError,
    GroupResult,
    group_by_prefix,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# group_by_prefix – basic behaviour
# ---------------------------------------------------------------------------


def test_returns_group_result():
    result = group_by_prefix({"DB_HOST": "localhost"})
    assert isinstance(result, GroupResult)


def test_single_prefix_grouped():
    result = group_by_prefix({"DB_HOST": "localhost", "DB_PORT": "5432"})
    assert "DB" in result.groups
    assert result.groups["DB"].count == 2


def test_multiple_prefixes():
    env = {"DB_HOST": "h", "AWS_KEY": "k", "AWS_SECRET": "s", "APP_DEBUG": "1"}
    result = group_by_prefix(env)
    assert set(result.group_names) == {"DB", "AWS", "APP"}


def test_key_without_separator_goes_to_ungrouped():
    result = group_by_prefix({"PLAIN": "value"})
    assert "PLAIN" in result.ungrouped
    assert result.total_grouped == 0


def test_prefix_is_uppercased():
    result = group_by_prefix({"db_host": "localhost"})
    assert "DB" in result.groups


def test_total_grouped_counts_all_grouped_keys():
    env = {"A_X": "1", "A_Y": "2", "B_Z": "3", "SOLO": "4"}
    result = group_by_prefix(env)
    assert result.total_grouped == 3


def test_ungrouped_count():
    env = {"A_X": "1", "SOLO": "4", "OTHER": "5"}
    result = group_by_prefix(env)
    assert len(result.ungrouped) == 2


# ---------------------------------------------------------------------------
# known_prefixes filter
# ---------------------------------------------------------------------------


def test_known_prefixes_restricts_groups():
    env = {"DB_HOST": "h", "AWS_KEY": "k", "APP_DEBUG": "1"}
    result = group_by_prefix(env, known_prefixes=["DB", "AWS"])
    assert set(result.group_names) == {"DB", "AWS"}
    assert "APP_DEBUG" in result.ungrouped


def test_known_prefixes_case_insensitive():
    result = group_by_prefix({"DB_HOST": "h"}, known_prefixes=["db"])
    assert "DB" in result.groups


# ---------------------------------------------------------------------------
# min_prefix_length
# ---------------------------------------------------------------------------


def test_min_prefix_length_excludes_short_prefix():
    # key "A_VALUE" has prefix "A" (length 1); with min=2 it should be ungrouped
    result = group_by_prefix({"A_VALUE": "x"}, min_prefix_length=2)
    assert "A_VALUE" in result.ungrouped


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_as_dict_structure():
    env = {"DB_HOST": "h", "SOLO": "s"}
    d = group_by_prefix(env).as_dict()
    assert "groups" in d
    assert "ungrouped" in d
    assert "total_grouped" in d
    assert "ungrouped_count" in d


def test_env_group_as_dict():
    g = EnvGroup(prefix="DB", keys=["DB_HOST", "DB_PORT"])
    d = g.as_dict()
    assert d["prefix"] == "DB"
    assert d["count"] == 2
    assert d["keys"] == ["DB_HOST", "DB_PORT"]


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------


def test_raises_for_non_dict():
    with pytest.raises(GroupError):
        group_by_prefix(["DB_HOST=localhost"])  # type: ignore[arg-type]


def test_raises_for_empty_sep():
    with pytest.raises(GroupError):
        group_by_prefix({"DB_HOST": "h"}, sep="")
