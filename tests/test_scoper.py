"""Tests for envdiff.scoper."""
import pytest

from envdiff.scoper import (
    ScopeError,
    ScopeResult,
    ScopedKey,
    scope_env,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# ScopeResult helpers
# ---------------------------------------------------------------------------

def test_returns_scope_result():
    result = scope_env({}, scope="prod")
    assert isinstance(result, ScopeResult)


def test_source_stored():
    result = scope_env({}, scope="prod", source="my.env")
    assert result.source == "my.env"


def test_scope_stored():
    result = scope_env({}, scope="staging")
    assert result.scope == "staging"


def test_empty_env_is_empty():
    result = scope_env({}, scope="prod")
    assert result.is_empty
    assert result.total_keys == 0


# ---------------------------------------------------------------------------
# Matching behaviour
# ---------------------------------------------------------------------------

def test_matching_key_included():
    env = _env(PROD__DB_HOST="localhost", DEV__DB_HOST="devhost")
    result = scope_env(env, scope="prod")
    keys = [k.key for k in result.keys]
    assert "DB_HOST" in keys


def test_non_matching_key_excluded():
    env = _env(PROD__DB_HOST="localhost", DEV__DB_HOST="devhost")
    result = scope_env(env, scope="prod")
    keys = [k.key for k in result.keys]
    assert "DEV__DB_HOST" not in keys


def test_strip_prefix_true_removes_scope():
    env = _env(PROD__SECRET="abc")
    result = scope_env(env, scope="prod", strip_prefix=True)
    assert result.keys[0].key == "SECRET"


def test_strip_prefix_false_keeps_full_key():
    env = _env(PROD__SECRET="abc")
    result = scope_env(env, scope="prod", strip_prefix=False)
    assert result.keys[0].key == "PROD__SECRET"


def test_match_is_case_insensitive():
    env = _env(prod__api_key="xyz")
    result = scope_env(env, scope="PROD")
    assert result.total_keys == 1


def test_value_preserved():
    env = _env(PROD__TOKEN="tok123")
    result = scope_env(env, scope="prod")
    assert result.keys[0].value == "tok123"


def test_custom_separator():
    env = {"PROD.HOST": "h1", "DEV.HOST": "h2"}
    result = scope_env(env, scope="prod", separator=".")
    assert result.total_keys == 1
    assert result.keys[0].key == "HOST"


def test_total_keys_count():
    env = _env(PROD__A="1", PROD__B="2", PROD__C="3", DEV__A="x")
    result = scope_env(env, scope="prod")
    assert result.total_keys == 3


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    env = _env(PROD__X="1")
    d = scope_env(env, scope="prod", source="test.env").as_dict()
    assert d["source"] == "test.env"
    assert d["scope"] == "prod"
    assert d["total_keys"] == 1
    assert isinstance(d["keys"], list)
    assert d["keys"][0]["key"] == "X"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_empty_scope_raises():
    with pytest.raises(ScopeError, match="scope must not be empty"):
        scope_env({}, scope="")


def test_empty_separator_raises():
    with pytest.raises(ScopeError, match="separator must not be empty"):
        scope_env({}, scope="prod", separator="")
