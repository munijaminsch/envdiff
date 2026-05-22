import pytest
from envdiff.differ_keys import (
    KeyDiffError,
    KeyDiffResult,
    KeyOnlyEntry,
    diff_keys,
)


def _env(**kwargs):
    return dict(kwargs)


def test_returns_key_diff_result():
    result = diff_keys(_env(A="1"), _env(A="1"))
    assert isinstance(result, KeyDiffResult)


def test_clean_when_same_keys():
    result = diff_keys(_env(A="1", B="2"), _env(A="x", B="y"))
    assert result.is_clean
    assert result.total_exclusive == 0


def test_only_in_left_detected():
    result = diff_keys(_env(A="1", B="2"), _env(A="1"))
    assert len(result.only_in_left) == 1
    assert result.only_in_left[0].key == "B"
    assert result.only_in_left[0].side == "left"


def test_only_in_right_detected():
    result = diff_keys(_env(A="1"), _env(A="1", C="3"))
    assert len(result.only_in_right) == 1
    assert result.only_in_right[0].key == "C"
    assert result.only_in_right[0].side == "right"


def test_both_sides_have_exclusive_keys():
    result = diff_keys(_env(A="1", B="2"), _env(A="1", C="3"))
    assert len(result.only_in_left) == 1
    assert len(result.only_in_right) == 1
    assert result.total_exclusive == 2
    assert not result.is_clean


def test_sources_stored():
    result = diff_keys(_env(A="1"), _env(B="2"), left_source=".env.dev", right_source=".env.prod")
    assert result.left_source == ".env.dev"
    assert result.right_source == ".env.prod"


def test_empty_envs_is_clean():
    result = diff_keys({}, {})
    assert result.is_clean


def test_left_empty_all_in_right():
    result = diff_keys({}, _env(X="1", Y="2"))
    assert len(result.only_in_right) == 2
    assert result.only_in_left == []


def test_right_empty_all_in_left():
    result = diff_keys(_env(X="1", Y="2"), {})
    assert len(result.only_in_left) == 2
    assert result.only_in_right == []


def test_only_in_left_sorted():
    result = diff_keys(_env(Z="z", A="a", M="m"), {})
    keys = [e.key for e in result.only_in_left]
    assert keys == sorted(keys)


def test_only_in_right_sorted():
    result = diff_keys({}, _env(Z="z", A="a", M="m"))
    keys = [e.key for e in result.only_in_right]
    assert keys == sorted(keys)


def test_value_stored_in_entry():
    result = diff_keys(_env(SECRET="abc123"), {})
    assert result.only_in_left[0].value == "abc123"


def test_raises_on_none_left():
    with pytest.raises(KeyDiffError):
        diff_keys(None, {})


def test_raises_on_none_right():
    with pytest.raises(KeyDiffError):
        diff_keys({}, None)


def test_as_dict_structure():
    result = diff_keys(_env(A="1"), _env(B="2"), left_source="l", right_source="r")
    d = result.as_dict()
    assert "left_source" in d
    assert "right_source" in d
    assert "only_in_left" in d
    assert "only_in_right" in d
    assert "total_exclusive" in d
    assert "is_clean" in d


def test_entry_as_dict():
    entry = KeyOnlyEntry(key="FOO", value="bar", side="left")
    d = entry.as_dict()
    assert d == {"key": "FOO", "value": "bar", "side": "left"}
