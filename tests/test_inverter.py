"""Tests for envdiff.inverter."""

import pytest

from envdiff.inverter import InvertError, InvertResult, InvertedKey, invert_env


def _env(**kwargs) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# basic structure
# ---------------------------------------------------------------------------

def test_returns_invert_result():
    result = invert_env(_env(KEY="value"))
    assert isinstance(result, InvertResult)


def test_source_stored():
    result = invert_env(_env(KEY="value"), source="prod.env")
    assert result.source == "prod.env"


def test_default_source_is_empty_string():
    result = invert_env(_env(KEY="value"))
    assert result.source == ""


def test_total_keys_count():
    result = invert_env(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


# ---------------------------------------------------------------------------
# inversion logic
# ---------------------------------------------------------------------------

def test_key_becomes_value():
    result = invert_env(_env(MY_KEY="my_value"))
    entry = result.entries[0]
    assert entry.new_key == "my_value"
    assert entry.new_value == "MY_KEY"


def test_original_fields_preserved():
    result = invert_env(_env(FOO="bar"))
    entry = result.entries[0]
    assert entry.original_key == "FOO"
    assert entry.original_value == "bar"


def test_empty_env_returns_empty_result():
    result = invert_env({})
    assert result.total_keys == 0
    assert result.entries == []


def test_clean_when_no_collisions():
    result = invert_env(_env(A="1", B="2"))
    assert result.is_clean is True
    assert result.collision_count == 0


# ---------------------------------------------------------------------------
# collision detection
# ---------------------------------------------------------------------------

def test_collision_detected_for_duplicate_values():
    result = invert_env(_env(KEY1="same", KEY2="same"))
    assert result.is_clean is False
    assert "same" in result.collisions


def test_collision_lists_original_keys():
    result = invert_env(_env(KEY1="dup", KEY2="dup", KEY3="dup"))
    assert set(result.collisions["dup"]) == {"KEY1", "KEY2", "KEY3"}


def test_collision_count():
    result = invert_env(_env(A="x", B="x", C="y", D="y"))
    assert result.collision_count == 2


def test_non_colliding_value_not_in_collisions():
    result = invert_env(_env(A="x", B="x", C="unique"))
    assert "unique" not in result.collisions


def test_last_key_wins_on_collision():
    # dict preserves insertion order; last key for value "dup" is KEY2
    env = {"KEY1": "dup", "KEY2": "dup"}
    result = invert_env(env)
    assert len(result.entries) == 1
    assert result.entries[0].new_value == "KEY2"


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_keys():
    result = invert_env(_env(A="1"), source="test.env")
    d = result.as_dict()
    assert set(d.keys()) == {
        "source", "total_keys", "is_clean",
        "collision_count", "collisions", "entries",
    }


def test_as_dict_entries_are_dicts():
    result = invert_env(_env(A="1"))
    assert isinstance(result.as_dict()["entries"][0], dict)


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------

def test_none_env_raises():
    with pytest.raises(InvertError):
        invert_env(None)  # type: ignore[arg-type]
