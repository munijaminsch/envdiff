"""Tests for envdiff.annotator."""
import pytest

from envdiff.annotator import (
    AnnotateError,
    AnnotationResult,
    KeyAnnotation,
    annotate,
)


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_returns_annotation_result():
    result = annotate(_env(FOO="bar"))
    assert isinstance(result, AnnotationResult)


def test_total_keys_count():
    result = annotate(_env(A="1", B="2", C="3"))
    assert result.total_keys == 3


def test_source_stored():
    result = annotate(_env(X="y"), source="prod.env")
    assert result.source == "prod.env"


def test_empty_value_flagged():
    result = annotate(_env(EMPTY=""))
    assert result.annotations["EMPTY"].is_empty is True


def test_non_empty_value_not_flagged():
    result = annotate(_env(FOO="bar"))
    assert result.annotations["FOO"].is_empty is False


def test_empty_keys_list():
    result = annotate(_env(A="", B="x", C=""))
    assert sorted(result.empty_keys) == ["A", "C"]


def test_whitespace_value_flagged():
    result = annotate({"PADDED": "  hello  "})
    assert result.annotations["PADDED"].has_whitespace_value is True


def test_clean_value_not_whitespace_flagged():
    result = annotate(_env(CLEAN="hello"))
    assert result.annotations["CLEAN"].has_whitespace_value is False


def test_whitespace_keys_list():
    result = annotate({"A": " x", "B": "y"})
    assert result.whitespace_keys == ["A"]


def test_char_count():
    result = annotate(_env(FOO="hello"))
    assert result.annotations["FOO"].char_count == 5


def test_sensitive_tag_on_password_key():
    result = annotate(_env(DB_PASSWORD="secret"))
    assert "sensitive" in result.annotations["DB_PASSWORD"].tags


def test_url_tag_on_http_value():
    result = annotate(_env(ENDPOINT="https://example.com"))
    assert "url" in result.annotations["ENDPOINT"].tags


def test_numeric_tag():
    result = annotate(_env(PORT="8080"))
    assert "numeric" in result.annotations["PORT"].tags


def test_boolean_tag():
    result = annotate(_env(DEBUG="true"))
    assert "boolean" in result.annotations["DEBUG"].tags


def test_no_tags_for_plain_value():
    result = annotate(_env(APP_NAME="myapp"))
    assert result.annotations["APP_NAME"].tags == []


def test_as_dict_structure():
    result = annotate(_env(FOO="bar"), source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["total_keys"] == 1
    assert "FOO" in d["annotations"]
    ann = d["annotations"]["FOO"]
    assert "key" in ann
    assert "value" in ann
    assert "tags" in ann


def test_raises_on_non_dict():
    with pytest.raises(AnnotateError):
        annotate(["not", "a", "dict"])  # type: ignore


def test_empty_env_returns_zero_keys():
    result = annotate({})
    assert result.total_keys == 0
    assert result.empty_keys == []
