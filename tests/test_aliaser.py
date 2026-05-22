"""Tests for envdiff.aliaser."""
import pytest

from envdiff.aliaser import AliasError, AliasedKey, AliasResult, apply_aliases


def _env(**kwargs) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# apply_aliases basic behaviour
# ---------------------------------------------------------------------------

def test_returns_alias_result():
    result = apply_aliases({}, {})
    assert isinstance(result, AliasResult)


def test_source_stored():
    result = apply_aliases({}, {}, source="prod.env")
    assert result.source == "prod.env"


def test_empty_env_is_clean():
    result = apply_aliases({}, {})
    assert result.is_clean
    assert result.total_keys == 0


def test_mapped_key_appears_in_entries():
    env = _env(DB_HOST="localhost")
    result = apply_aliases(env, {"DB_HOST": "database_host"})
    assert result.mapped_count == 1
    assert result.entries[0].alias == "database_host"
    assert result.entries[0].original == "DB_HOST"
    assert result.entries[0].value == "localhost"


def test_unmapped_key_in_unmapped_list():
    env = _env(SECRET="abc")
    result = apply_aliases(env, {})
    assert "SECRET" in result.unmapped
    assert result.unmapped_count == 1


def test_partial_mapping():
    env = _env(A="1", B="2", C="3")
    result = apply_aliases(env, {"A": "alpha", "C": "gamma"})
    assert result.mapped_count == 2
    assert result.unmapped_count == 1
    assert "B" in result.unmapped


def test_is_clean_only_when_all_mapped():
    env = _env(X="1", Y="2")
    result = apply_aliases(env, {"X": "ex", "Y": "why"})
    assert result.is_clean


def test_not_clean_with_unmapped():
    env = _env(X="1", Y="2")
    result = apply_aliases(env, {"X": "ex"})
    assert not result.is_clean


def test_total_keys_counts_all():
    env = _env(A="1", B="2", C="3")
    result = apply_aliases(env, {"A": "alpha"})
    assert result.total_keys == 3


# ---------------------------------------------------------------------------
# strict mode
# ---------------------------------------------------------------------------

def test_strict_mode_raises_when_unmapped():
    env = _env(A="1", B="2")
    with pytest.raises(AliasError, match="strict mode"):
        apply_aliases(env, {"A": "alpha"}, strict=True)


def test_strict_mode_passes_when_all_mapped():
    env = _env(A="1")
    result = apply_aliases(env, {"A": "alpha"}, strict=True)
    assert result.is_clean


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    env = _env(FOO="bar")
    result = apply_aliases(env, {"FOO": "foo_alias"}, source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["mapped_count"] == 1
    assert d["unmapped_count"] == 0
    assert d["mapped"][0]["alias"] == "foo_alias"


def test_as_dict_unmapped_list():
    env = _env(A="1", B="2")
    result = apply_aliases(env, {})
    d = result.as_dict()
    assert set(d["unmapped"]) == {"A", "B"}


def test_aliased_key_as_dict():
    ak = AliasedKey(original="DB_URL", alias="database_url", value="postgres://")
    d = ak.as_dict()
    assert d == {"original": "DB_URL", "alias": "database_url", "value": "postgres://"}


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_none_mapping_raises():
    with pytest.raises(AliasError):
        apply_aliases({}, None)  # type: ignore[arg-type]
