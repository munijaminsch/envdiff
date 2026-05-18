"""Tests for envdiff.flattener."""
import pytest

from envdiff.flattener import FlattenError, FlattenResult, flatten_env


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# flatten_env return type
# ---------------------------------------------------------------------------

def test_returns_flatten_result():
    result = flatten_env(_env(KEY="val"), source="test.env")
    assert isinstance(result, FlattenResult)


def test_source_stored():
    result = flatten_env(_env(KEY="val"), source="prod.env")
    assert result.source == "prod.env"


def test_separator_stored():
    result = flatten_env(_env(KEY="val"), separator="__")
    assert result.separator == "__"


# ---------------------------------------------------------------------------
# total_keys
# ---------------------------------------------------------------------------

def test_total_keys_count():
    result = flatten_env(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


def test_empty_env_total_keys_zero():
    result = flatten_env({})
    assert result.total_keys == 0


# ---------------------------------------------------------------------------
# flat passthrough
# ---------------------------------------------------------------------------

def test_flat_preserves_original_keys():
    env = _env(APP__HOST="localhost", APP__PORT="5432")
    result = flatten_env(env)
    assert result.flat == env


# ---------------------------------------------------------------------------
# nested structure
# ---------------------------------------------------------------------------

def test_single_segment_key_goes_to_top_level():
    result = flatten_env(_env(HOST="localhost"))
    assert result.nested == {"HOST": "localhost"}


def test_two_segment_key_creates_nested_dict():
    result = flatten_env(_env(APP__HOST="localhost"))
    assert result.nested == {"APP": {"HOST": "localhost"}}


def test_three_segment_key_creates_deep_nesting():
    result = flatten_env(_env(APP__DB__HOST="db.local"))
    assert result.nested["APP"]["DB"]["HOST"] == "db.local"


def test_multiple_keys_same_prefix_merged():
    result = flatten_env(_env(APP__HOST="localhost", APP__PORT="5432"))
    assert result.nested["APP"] == {"HOST": "localhost", "PORT": "5432"}


def test_mixed_depth_keys():
    result = flatten_env(_env(HOST="h", APP__PORT="9"))
    assert result.nested["HOST"] == "h"
    assert result.nested["APP"]["PORT"] == "9"


# ---------------------------------------------------------------------------
# custom separator
# ---------------------------------------------------------------------------

def test_custom_separator_single_underscore():
    result = flatten_env(_env(APP_HOST="localhost"), separator="_")
    assert result.nested["APP"]["HOST"] == "localhost"


def test_empty_separator_raises():
    with pytest.raises(FlattenError):
        flatten_env(_env(KEY="val"), separator="")


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_contains_expected_keys():
    result = flatten_env(_env(A="1"), source="a.env")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "separator", "total_keys", "flat", "nested"}


def test_as_dict_total_keys_matches():
    result = flatten_env(_env(A="1", B="2"))
    assert result.as_dict()["total_keys"] == 2
