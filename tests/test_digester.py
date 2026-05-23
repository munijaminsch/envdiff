"""Tests for envdiff.digester."""
import pytest

from envdiff.digester import (
    DigestError,
    DigestResult,
    compare_digests,
    digest_env,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# digest_env
# ---------------------------------------------------------------------------

def test_returns_digest_result():
    result = digest_env(_env(KEY="value"))
    assert isinstance(result, DigestResult)


def test_source_stored():
    result = digest_env(_env(KEY="v"), source="prod.env")
    assert result.source == "prod.env"


def test_default_source_is_empty_string():
    result = digest_env(_env(KEY="v"))
    assert result.source == ""


def test_algorithm_stored():
    result = digest_env(_env(KEY="v"), algorithm="md5")
    assert result.algorithm == "md5"


def test_default_algorithm_is_sha256():
    result = digest_env(_env(KEY="v"))
    assert result.algorithm == "sha256"


def test_key_count_matches_env():
    env = _env(A="1", B="2", C="3")
    result = digest_env(env)
    assert result.key_count == 3


def test_empty_env_key_count_zero():
    result = digest_env({})
    assert result.key_count == 0


def test_hex_digest_is_string():
    result = digest_env(_env(KEY="v"))
    assert isinstance(result.hex_digest, str)
    assert len(result.hex_digest) == 64  # sha256 hex length


def test_key_digests_contains_all_keys():
    env = _env(FOO="bar", BAZ="qux")
    result = digest_env(env)
    assert set(result.key_digests.keys()) == {"FOO", "BAZ"}


def test_same_env_produces_same_digest():
    env = _env(X="1", Y="2")
    assert digest_env(env).hex_digest == digest_env(env).hex_digest


def test_different_values_produce_different_digest():
    a = digest_env(_env(KEY="hello"))
    b = digest_env(_env(KEY="world"))
    assert a.hex_digest != b.hex_digest


def test_unsupported_algorithm_raises():
    with pytest.raises(DigestError, match="Unsupported"):
        digest_env(_env(K="v"), algorithm="not_a_real_algo")


def test_as_dict_structure():
    result = digest_env(_env(KEY="val"), source="test.env")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "algorithm", "hex_digest", "key_count", "key_digests"}


def test_as_dict_values_match():
    env = _env(A="1")
    result = digest_env(env, source="x.env", algorithm="sha256")
    d = result.as_dict()
    assert d["source"] == "x.env"
    assert d["key_count"] == 1
    assert d["hex_digest"] == result.hex_digest


# ---------------------------------------------------------------------------
# compare_digests
# ---------------------------------------------------------------------------

def test_compare_identical_envs_returns_empty():
    env = _env(A="1", B="2")
    left = digest_env(env)
    right = digest_env(env)
    assert compare_digests(left, right) == {}


def test_compare_detects_value_change():
    left = digest_env(_env(KEY="old"))
    right = digest_env(_env(KEY="new"))
    diffs = compare_digests(left, right)
    assert "KEY" in diffs


def test_compare_missing_in_right_has_none():
    left = digest_env(_env(ONLY_LEFT="v"))
    right = digest_env({})
    diffs = compare_digests(left, right)
    assert diffs.get("ONLY_LEFT") is None


def test_compare_missing_in_left_has_digest():
    left = digest_env({})
    right = digest_env(_env(ONLY_RIGHT="v"))
    diffs = compare_digests(left, right)
    assert "ONLY_RIGHT" in diffs
    assert diffs["ONLY_RIGHT"] is not None
