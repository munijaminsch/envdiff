"""Tests for envdiff.tagger."""

import pytest

from envdiff.tagger import KeyTag, TagError, TagResult, tag_keys


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# tag_keys return type
# ---------------------------------------------------------------------------


def test_returns_tag_result():
    result = tag_keys({"FOO": "bar"}, {})
    assert isinstance(result, TagResult)


def test_source_stored():
    result = tag_keys({"A": "1"}, {}, source="prod.env")
    assert result.source == "prod.env"


def test_total_keys_count():
    env = _env(A="1", B="2", C="3")
    result = tag_keys(env, {})
    assert result.total_keys == 3


# ---------------------------------------------------------------------------
# tagging behaviour
# ---------------------------------------------------------------------------


def test_no_rules_produces_empty_tags():
    env = _env(SECRET="x", DB_HOST="localhost")
    result = tag_keys(env, {})
    for kt in result.tagged:
        assert kt.tags == []


def test_exact_pattern_matches_key():
    result = tag_keys({"SECRET": "s"}, {"SECRET": ["sensitive"]})
    assert "sensitive" in result.tags_for_key("SECRET")


def test_glob_pattern_matches_multiple_keys():
    env = _env(DB_HOST="h", DB_PORT="5432", APP_NAME="app")
    result = tag_keys(env, {"DB_*": ["database"]})
    assert "database" in result.tags_for_key("DB_HOST")
    assert "database" in result.tags_for_key("DB_PORT")
    assert "database" not in (result.tags_for_key("APP_NAME") or [])


def test_multiple_rules_accumulate_tags():
    env = _env(SECRET_KEY="k")
    rules = {"SECRET_*": ["sensitive"], "*_KEY": ["credential"]}
    result = tag_keys(env, rules)
    tags = result.tags_for_key("SECRET_KEY")
    assert "sensitive" in tags
    assert "credential" in tags


def test_duplicate_tags_not_added_twice():
    env = _env(SECRET_KEY="k")
    rules = {"SECRET_*": ["sensitive"], "*KEY": ["sensitive"]}
    result = tag_keys(env, rules)
    tags = result.tags_for_key("SECRET_KEY")
    assert tags.count("sensitive") == 1


# ---------------------------------------------------------------------------
# keys_with_tag helper
# ---------------------------------------------------------------------------


def test_keys_with_tag_returns_matching_keys():
    env = _env(DB_HOST="h", DB_PASS="p", APP_NAME="app")
    rules = {"DB_*": ["database"]}
    result = tag_keys(env, rules)
    db_keys = result.keys_with_tag("database")
    assert "DB_HOST" in db_keys
    assert "DB_PASS" in db_keys
    assert "APP_NAME" not in db_keys


def test_keys_with_tag_unknown_tag_returns_empty():
    env = _env(FOO="bar")
    result = tag_keys(env, {})
    assert result.keys_with_tag("nonexistent") == []


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_as_dict_structure():
    env = _env(FOO="1")
    result = tag_keys(env, {"FOO": ["demo"]}, source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["total_keys"] == 1
    assert isinstance(d["tagged"], list)
    assert d["tagged"][0]["key"] == "FOO"
    assert "demo" in d["tagged"][0]["tags"]


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


def test_invalid_rules_type_raises_tag_error():
    with pytest.raises(TagError):
        tag_keys({"A": "1"}, ["not", "a", "dict"])  # type: ignore


def test_tags_not_list_raises_tag_error():
    with pytest.raises(TagError, match="list"):
        tag_keys({"A": "1"}, {"A": "sensitive"})  # type: ignore
