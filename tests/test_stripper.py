"""Tests for envdiff.stripper."""

import pytest

from envdiff.stripper import StripError, StripResult, StrippedKey, strip_keys


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# StripResult helpers
# ---------------------------------------------------------------------------

def test_is_clean_when_nothing_removed():
    result = StripResult(source="a", reference="b", kept={"K": "v"}, removed=[])
    assert result.is_clean is True


def test_not_clean_when_keys_removed():
    result = StripResult(
        source="a",
        reference="b",
        kept={},
        removed=[StrippedKey(key="X", value="1")],
    )
    assert result.is_clean is False


def test_removed_count():
    result = StripResult(
        source="a",
        reference="b",
        kept={},
        removed=[StrippedKey("A", "1"), StrippedKey("B", "2")],
    )
    assert result.removed_count == 2


def test_as_dict_structure():
    result = strip_keys({"A": "1", "B": "2"}, {"A": "x"}, source="s", reference_name="r")
    d = result.as_dict()
    assert "source" in d
    assert "reference" in d
    assert "kept" in d
    assert "removed" in d
    assert "removed_count" in d
    assert "is_clean" in d


# ---------------------------------------------------------------------------
# strip_keys behaviour
# ---------------------------------------------------------------------------

def test_all_keys_kept_when_reference_is_superset():
    env = _env(A="1", B="2")
    ref = _env(A="x", B="y", C="z")
    result = strip_keys(env, ref)
    assert result.kept == {"A": "1", "B": "2"}
    assert result.removed == []


def test_extra_keys_removed():
    env = _env(A="1", ORPHAN="old")
    ref = _env(A="x")
    result = strip_keys(env, ref)
    assert "A" in result.kept
    assert "ORPHAN" not in result.kept
    assert len(result.removed) == 1
    assert result.removed[0].key == "ORPHAN"


def test_removed_keys_sorted_alphabetically():
    env = _env(Z="z", A="a", M="m", KEEP="k")
    ref = _env(KEEP="x")
    result = strip_keys(env, ref)
    removed_keys = [r.key for r in result.removed]
    assert removed_keys == sorted(removed_keys)


def test_empty_env_returns_clean_result():
    result = strip_keys({}, {"A": "1"})
    assert result.is_clean is True
    assert result.kept == {}


def test_empty_reference_removes_all_keys():
    env = _env(A="1", B="2")
    result = strip_keys(env, {})
    assert result.kept == {}
    assert result.removed_count == 2


def test_source_and_reference_labels_stored():
    result = strip_keys({}, {}, source="prod.env", reference_name="template.env")
    assert result.source == "prod.env"
    assert result.reference == "template.env"


def test_removed_key_value_preserved():
    env = _env(SECRET="hunter2")
    result = strip_keys(env, {})
    assert result.removed[0].value == "hunter2"


def test_none_env_raises():
    with pytest.raises(StripError):
        strip_keys(None, {})


def test_none_reference_raises():
    with pytest.raises(StripError):
        strip_keys({}, None)


def test_stripped_key_as_dict():
    sk = StrippedKey(key="FOO", value="bar")
    d = sk.as_dict()
    assert d == {"key": "FOO", "value": "bar"}
