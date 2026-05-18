"""Tests for envdiff.splitter."""
import pytest

from envdiff.splitter import SplitError, SplitResult, split_by_prefix


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# split_by_prefix basics
# ---------------------------------------------------------------------------

def test_returns_split_result():
    result = split_by_prefix({}, [], source="test.env")
    assert isinstance(result, SplitResult)


def test_source_stored():
    result = split_by_prefix({}, [], source="prod.env")
    assert result.source == "prod.env"


def test_separator_stored():
    result = split_by_prefix({}, [], separator="__")
    assert result.separator == "__"


def test_empty_env_returns_empty_buckets():
    result = split_by_prefix({}, ["DB", "APP"])
    assert result.buckets == {"DB": {}, "APP": {}}
    assert result.unmatched == {}


def test_single_prefix_splits_matching_keys():
    env = _env(DB_HOST="localhost", DB_PORT="5432", APP_NAME="myapp")
    result = split_by_prefix(env, ["DB"])
    assert result.buckets["DB"] == {"HOST": "localhost", "PORT": "5432"}


def test_unmatched_keys_collected():
    env = _env(DB_HOST="localhost", APP_NAME="myapp", PLAIN="value")
    result = split_by_prefix(env, ["DB"])
    assert "APP_NAME" in result.unmatched
    assert "PLAIN" in result.unmatched


def test_multiple_prefixes_split_correctly():
    env = _env(DB_HOST="h", APP_PORT="8080", OTHER="x")
    result = split_by_prefix(env, ["DB", "APP"])
    assert result.buckets["DB"] == {"HOST": "h"}
    assert result.buckets["APP"] == {"PORT": "8080"}
    assert result.unmatched == {"OTHER": "x"}


def test_strip_prefix_false_keeps_full_key():
    env = _env(DB_HOST="localhost")
    result = split_by_prefix(env, ["DB"], strip_prefix=False)
    assert "DB_HOST" in result.buckets["DB"]


def test_custom_separator():
    env = {"DB.HOST": "localhost", "APP.PORT": "80"}
    result = split_by_prefix(env, ["DB", "APP"], separator=".")
    assert result.buckets["DB"] == {"HOST": "localhost"}
    assert result.buckets["APP"] == {"PORT": "80"}


def test_total_keys_counts_all():
    env = _env(DB_HOST="h", APP_PORT="p", PLAIN="v")
    result = split_by_prefix(env, ["DB", "APP"])
    assert result.total_keys == 3


def test_bucket_names_sorted():
    result = split_by_prefix({}, ["ZEBRA", "ALPHA", "MIDDLE"])
    assert result.bucket_names == ["ALPHA", "MIDDLE", "ZEBRA"]


def test_as_dict_structure():
    env = _env(DB_HOST="h")
    result = split_by_prefix(env, ["DB"], source="a.env")
    d = result.as_dict()
    assert d["source"] == "a.env"
    assert "buckets" in d
    assert "unmatched" in d
    assert "total_keys" in d


def test_raises_for_non_dict_env():
    with pytest.raises(SplitError, match="env must be a dict"):
        split_by_prefix("not-a-dict", [])  # type: ignore[arg-type]


def test_raises_for_empty_separator():
    with pytest.raises(SplitError, match="separator"):
        split_by_prefix({}, ["DB"], separator="")


def test_prefix_without_separator_not_matched():
    # Key "DBHOST" should NOT match prefix "DB" with separator "_"
    env = _env(DBHOST="val")
    result = split_by_prefix(env, ["DB"])
    assert result.unmatched == {"DBHOST": "val"}
    assert result.buckets["DB"] == {}
