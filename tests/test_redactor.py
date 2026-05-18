"""Tests for envdiff.redactor."""

import pytest

from envdiff.redactor import (
    REDACT_PLACEHOLDER,
    RedactError,
    RedactResult,
    RedactedKey,
    redact,
)


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Basic return type
# ---------------------------------------------------------------------------

def test_returns_redact_result():
    result = redact(_env(FOO="bar"), source="test.env")
    assert isinstance(result, RedactResult)


def test_source_stored():
    result = redact(_env(FOO="bar"), source="prod.env")
    assert result.source == "prod.env"


# ---------------------------------------------------------------------------
# Clean env
# ---------------------------------------------------------------------------

def test_non_sensitive_keys_unchanged():
    result = redact(_env(APP_NAME="myapp", PORT="8080"))
    assert result.redacted["APP_NAME"] == "myapp"
    assert result.redacted["PORT"] == "8080"


def test_clean_env_is_clean():
    result = redact(_env(HOST="localhost", PORT="5432"))
    assert result.is_clean is True
    assert result.redact_count == 0


# ---------------------------------------------------------------------------
# Sensitive key detection
# ---------------------------------------------------------------------------

def test_password_key_redacted():
    result = redact(_env(DB_PASSWORD="s3cr3t"))
    assert result.redacted["DB_PASSWORD"] == REDACT_PLACEHOLDER


def test_secret_key_redacted():
    result = redact(_env(APP_SECRET="abc123"))
    assert result.redacted["APP_SECRET"] == REDACT_PLACEHOLDER


def test_token_key_redacted():
    result = redact(_env(ACCESS_TOKEN="tok_xyz"))
    assert result.redacted["ACCESS_TOKEN"] == REDACT_PLACEHOLDER


def test_api_key_redacted():
    result = redact(_env(API_KEY="key_abc"))
    assert result.redacted["API_KEY"] == REDACT_PLACEHOLDER


def test_case_insensitive_match():
    result = redact(_env(db_password="hunter2"))
    assert result.redacted["db_password"] == REDACT_PLACEHOLDER


# ---------------------------------------------------------------------------
# RedactedKey metadata
# ---------------------------------------------------------------------------

def test_redacted_keys_list_populated():
    result = redact(_env(DB_PASSWORD="s3cr3t", HOST="localhost"))
    assert len(result.redacted_keys) == 1
    assert result.redacted_keys[0].key == "DB_PASSWORD"


def test_redacted_key_original_length():
    result = redact(_env(DB_PASSWORD="s3cr3t"))
    assert result.redacted_keys[0].original_length == len("s3cr3t")


def test_redact_count_matches_keys():
    result = redact(_env(DB_PASSWORD="x", APP_SECRET="y", HOST="z"))
    assert result.redact_count == 2


# ---------------------------------------------------------------------------
# Custom patterns and placeholder
# ---------------------------------------------------------------------------

def test_custom_pattern_redacts_matching_key():
    result = redact(_env(INTERNAL_CODE="1234"), patterns=[r"internal"])
    assert result.redacted["INTERNAL_CODE"] == REDACT_PLACEHOLDER


def test_custom_placeholder_used():
    result = redact(_env(DB_PASSWORD="secret"), placeholder="[hidden]")
    assert result.redacted["DB_PASSWORD"] == "[hidden]"


def test_none_env_raises():
    with pytest.raises(RedactError):
        redact(None)  # type: ignore


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    result = redact(_env(DB_PASSWORD="x", HOST="localhost"), source="a.env")
    d = result.as_dict()
    assert d["source"] == "a.env"
    assert d["redact_count"] == 1
    assert isinstance(d["redacted_keys"], list)
    assert isinstance(d["env"], dict)


def test_redacted_key_as_dict():
    rk = RedactedKey(key="DB_PASSWORD", original_length=6)
    assert rk.as_dict() == {"key": "DB_PASSWORD", "original_length": 6}
