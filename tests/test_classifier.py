"""Tests for envdiff.classifier."""

import pytest

from envdiff.classifier import (
    ClassifyError,
    ClassifyResult,
    KeyClassification,
    classify_env,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_returns_classify_result():
    result = classify_env(_env(FOO="bar"))
    assert isinstance(result, ClassifyResult)


def test_source_stored():
    result = classify_env(_env(A="1"), source="prod.env")
    assert result.source == "prod.env"


def test_total_keys_count():
    result = classify_env(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


def test_empty_value_classified_as_empty():
    result = classify_env(_env(EMPTY=""))
    assert result.classifications[0].inferred_type == "empty"


def test_boolean_true_classified():
    result = classify_env(_env(FLAG="true"))
    assert result.classifications[0].inferred_type == "boolean"


def test_boolean_false_classified():
    result = classify_env(_env(FLAG="false"))
    assert result.classifications[0].inferred_type == "boolean"


def test_boolean_yes_no_classified():
    r1 = classify_env(_env(A="yes"))
    r2 = classify_env(_env(A="no"))
    assert r1.classifications[0].inferred_type == "boolean"
    assert r2.classifications[0].inferred_type == "boolean"


def test_integer_classified():
    result = classify_env(_env(PORT="8080"))
    assert result.classifications[0].inferred_type == "integer"


def test_negative_integer_classified():
    result = classify_env(_env(OFFSET="-5"))
    assert result.classifications[0].inferred_type == "integer"


def test_float_classified():
    result = classify_env(_env(RATIO="3.14"))
    assert result.classifications[0].inferred_type == "float"


def test_url_classified():
    result = classify_env(_env(API="https://example.com/api"))
    assert result.classifications[0].inferred_type == "url"


def test_http_url_classified():
    result = classify_env(_env(ENDPOINT="http://localhost:3000"))
    assert result.classifications[0].inferred_type == "url"


def test_path_classified():
    result = classify_env(_env(LOG_DIR="/var/log/app"))
    assert result.classifications[0].inferred_type == "path"


def test_string_fallback():
    result = classify_env(_env(NAME="my-app-v2"))
    assert result.classifications[0].inferred_type == "string"


def test_by_type_groups_correctly():
    env = _env(A="true", B="42", C="hello", D="")
    result = classify_env(env)
    groups = result.by_type()
    assert "boolean" in groups
    assert "integer" in groups
    assert "string" in groups
    assert "empty" in groups


def test_as_dict_structure():
    result = classify_env(_env(X="1"), source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["total_keys"] == 1
    assert isinstance(d["classifications"], list)
    assert d["classifications"][0]["key"] == "X"


def test_none_env_raises():
    with pytest.raises(ClassifyError):
        classify_env(None)  # type: ignore


def test_keys_sorted_in_result():
    result = classify_env(_env(Z="1", A="2", M="3"))
    keys = [c.key for c in result.classifications]
    assert keys == sorted(keys)
