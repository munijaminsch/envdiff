"""Tests for envdiff.masker."""
import pytest

from envdiff.masker import (
    MaskError,
    MaskResult,
    MaskedKey,
    _mask_value,
    mask_env,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# _mask_value unit tests
# ---------------------------------------------------------------------------

def test_mask_value_full_mask():
    assert _mask_value("secret") == "******"


def test_mask_value_empty_string_unchanged():
    assert _mask_value("") == ""


def test_mask_value_visible_trailing_chars():
    assert _mask_value("password", visible=2) == "******rd"


def test_mask_value_visible_gte_length_returns_all_masked():
    assert _mask_value("ab", visible=5) == "**"


def test_mask_value_custom_symbol():
    assert _mask_value("hello", symbol="#") == "#####"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

def test_returns_mask_result():
    result = mask_env(_env(KEY="value"))
    assert isinstance(result, MaskResult)


def test_source_stored():
    result = mask_env(_env(KEY="value"), source="prod.env")
    assert result.source == "prod.env"


def test_total_keys_count():
    result = mask_env(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


def test_all_keys_masked_by_default():
    result = mask_env(_env(DB_PASS="secret", API_KEY="abc"))
    for entry in result.entries:
        assert entry.masked_value == "*" * entry.original_length


def test_empty_value_flagged():
    result = mask_env(_env(EMPTY=""))
    entry = result.entries[0]
    assert entry.was_empty is True
    assert entry.masked_value == ""


def test_non_empty_value_not_flagged():
    result = mask_env(_env(KEY="val"))
    assert result.entries[0].was_empty is False


def test_masked_count_excludes_empty():
    result = mask_env(_env(A="hello", B="", C="world"))
    assert result.masked_count == 2


def test_selective_keys_only_masks_specified():
    env = _env(SECRET="topsecret", PUBLIC="visible")
    result = mask_env(env, keys=["SECRET"])
    by_key = {e.key: e for e in result.entries}
    assert by_key["SECRET"].masked_value == "*********"
    assert by_key["PUBLIC"].masked_value == "visible"


def test_visible_trailing_applied():
    result = mask_env(_env(TOKEN="abcdef"), visible=2)
    assert result.entries[0].masked_value == "****ef"


def test_invalid_symbol_raises():
    with pytest.raises(MaskError, match="symbol"):
        mask_env(_env(K="v"), symbol="**")


def test_negative_visible_raises():
    with pytest.raises(MaskError, match="visible"):
        mask_env(_env(K="v"), visible=-1)


def test_as_dict_structure():
    result = mask_env(_env(KEY="hello"), source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["total_keys"] == 1
    assert "entries" in d
    assert d["entries"][0]["key"] == "KEY"


def test_entry_as_dict_fields():
    result = mask_env(_env(X="abc"))
    entry_dict = result.entries[0].as_dict()
    assert set(entry_dict.keys()) == {"key", "original_length", "masked_value", "was_empty"}


def test_original_length_recorded():
    result = mask_env(_env(PASS="hunter2"))
    assert result.entries[0].original_length == 7
