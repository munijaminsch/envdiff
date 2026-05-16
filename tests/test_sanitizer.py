"""Tests for envdiff.sanitizer."""

import pytest

from envdiff.sanitizer import (
    REDACTED,
    SanitizeError,
    SanitizedEnv,
    sanitize,
)


def _env(**kwargs) -> dict:
    return dict(kwargs)


def test_returns_sanitized_env_instance():
    result = sanitize(_env(HOST="localhost"))
    assert isinstance(result, SanitizedEnv)


def test_non_sensitive_keys_are_unchanged():
    result = sanitize(_env(HOST="localhost", PORT="5432"))
    assert result.sanitized["HOST"] == "localhost"
    assert result.sanitized["PORT"] == "5432"


def test_password_key_is_redacted():
    result = sanitize(_env(DB_PASSWORD="s3cr3t"))
    assert result.sanitized["DB_PASSWORD"] == REDACTED
    assert "DB_PASSWORD" in result.redacted_keys


def test_secret_key_is_redacted():
    result = sanitize(_env(APP_SECRET="mysecret"))
    assert result.sanitized["APP_SECRET"] == REDACTED


def test_token_key_is_redacted():
    result = sanitize(_env(ACCESS_TOKEN="abc123"))
    assert result.sanitized["ACCESS_TOKEN"] == REDACTED


def test_api_key_is_redacted():
    result = sanitize(_env(STRIPE_API_KEY="pk_live_xxx"))
    assert result.sanitized["STRIPE_API_KEY"] == REDACTED


def test_multiple_sensitive_keys():
    env = _env(HOST="localhost", DB_PASSWORD="x", SECRET_KEY="y", PORT="80")
    result = sanitize(env)
    assert result.redacted_count == 2
    assert result.sanitized["HOST"] == "localhost"
    assert result.sanitized["PORT"] == "80"


def test_redacted_keys_are_sorted():
    env = _env(Z_TOKEN="a", A_PASSWORD="b", HOST="c")
    result = sanitize(env)
    assert result.redacted_keys == sorted(result.redacted_keys)


def test_original_is_preserved():
    env = _env(DB_PASSWORD="secret", HOST="localhost")
    result = sanitize(env)
    assert result.original["DB_PASSWORD"] == "secret"


def test_extra_patterns_redact_additional_keys():
    env = _env(INTERNAL_CERT="cert-data", HOST="localhost")
    result = sanitize(env, extra_patterns=[r"(?i)cert"])
    assert result.sanitized["INTERNAL_CERT"] == REDACTED
    assert result.sanitized["HOST"] == "localhost"


def test_custom_redact_value():
    result = sanitize(_env(DB_PASSWORD="x"), redact_value="[hidden]")
    assert result.sanitized["DB_PASSWORD"] == "[hidden]"


def test_empty_env_returns_empty_sanitized():
    result = sanitize({})
    assert result.sanitized == {}
    assert result.redacted_count == 0


def test_none_env_raises_sanitize_error():
    with pytest.raises(SanitizeError):
        sanitize(None)  # type: ignore


def test_invalid_extra_pattern_raises_sanitize_error():
    with pytest.raises(SanitizeError):
        sanitize(_env(KEY="val"), extra_patterns=["[invalid"])


def test_as_dict_contains_expected_keys():
    result = sanitize(_env(HOST="localhost", DB_PASSWORD="x"))
    d = result.as_dict()
    assert "sanitized" in d
    assert "redacted_keys" in d
    assert "redacted_count" in d
    assert d["redacted_count"] == 1
