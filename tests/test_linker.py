"""Tests for envdiff.linker."""
import pytest
from envdiff.linker import LinkError, LinkedKey, LinkResult, link_envs


def _env(**kwargs) -> dict:
    return dict(kwargs)


# --- link_envs ---

def test_returns_link_result():
    result = link_envs(_env(A="1"), _env(A="1"))
    assert isinstance(result, LinkResult)


def test_source_stored():
    result = link_envs(_env(), _env(), left_source="a.env", right_source="b.env")
    assert result.left_source == "a.env"
    assert result.right_source == "b.env"


def test_default_source_is_empty_string():
    result = link_envs(_env(), _env())
    assert result.left_source == ""
    assert result.right_source == ""


def test_empty_envs_produce_no_entries():
    result = link_envs(_env(), _env())
    assert result.total_keys == 0
    assert result.entries == []


def test_shared_key_detected():
    result = link_envs(_env(X="1"), _env(X="1"))
    assert "X" in result.shared_keys


def test_exclusive_left_detected():
    result = link_envs(_env(ONLY_LEFT="v"), _env())
    assert "ONLY_LEFT" in result.exclusive_left
    assert "ONLY_LEFT" not in result.shared_keys


def test_exclusive_right_detected():
    result = link_envs(_env(), _env(ONLY_RIGHT="v"))
    assert "ONLY_RIGHT" in result.exclusive_right
    assert "ONLY_RIGHT" not in result.shared_keys


def test_matching_shared_key_is_clean():
    result = link_envs(_env(A="1"), _env(A="1"))
    assert result.is_clean is True


def test_mismatched_shared_key_not_clean():
    result = link_envs(_env(A="1"), _env(A="2"))
    assert result.is_clean is False


def test_exclusive_keys_do_not_affect_is_clean():
    result = link_envs(_env(EXTRA="x"), _env())
    assert result.is_clean is True


def test_entry_values_populated():
    result = link_envs(_env(K="left_val"), _env(K="right_val"))
    entry = result.entries[0]
    assert entry.left_value == "left_val"
    assert entry.right_value == "right_val"


def test_entry_left_only_has_none_right():
    result = link_envs(_env(K="v"), _env())
    entry = result.entries[0]
    assert entry.left_value == "v"
    assert entry.right_value is None


def test_entry_right_only_has_none_left():
    result = link_envs(_env(), _env(K="v"))
    entry = result.entries[0]
    assert entry.left_value is None
    assert entry.right_value == "v"


def test_total_keys_counts_all_unique():
    result = link_envs(_env(A="1", B="2"), _env(B="2", C="3"))
    assert result.total_keys == 3


def test_entries_sorted_alphabetically():
    result = link_envs(_env(Z="1", A="2"), _env(M="3"))
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_none_left_raises():
    with pytest.raises(LinkError):
        link_envs(None, _env())


def test_none_right_raises():
    with pytest.raises(LinkError):
        link_envs(_env(), None)


def test_as_dict_structure():
    result = link_envs(_env(A="1"), _env(A="1"), left_source="l", right_source="r")
    d = result.as_dict()
    assert d["left_source"] == "l"
    assert d["right_source"] == "r"
    assert "entries" in d
    assert "shared_keys" in d
    assert "exclusive_left" in d
    assert "exclusive_right" in d
    assert "is_clean" in d


def test_linked_key_as_dict():
    lk = LinkedKey(key="X", left_value="a", right_value="b", is_shared=True, values_match=False)
    d = lk.as_dict()
    assert d["key"] == "X"
    assert d["left_value"] == "a"
    assert d["right_value"] == "b"
    assert d["is_shared"] is True
    assert d["values_match"] is False
