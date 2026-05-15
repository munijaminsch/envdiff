"""Tests for envdiff.validator."""

import pytest

from envdiff.validator import (
    ValidateError,
    ValidationIssue,
    ValidationResult,
    validate_env,
)


def _env(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items()}


# ---------------------------------------------------------------------------
# ValidationResult helpers
# ---------------------------------------------------------------------------

def test_result_is_clean_when_no_issues():
    result = ValidationResult(file="test.env")
    assert result.is_clean is True


def test_result_not_clean_when_issues_present():
    result = ValidationResult(
        file="test.env",
        issues=[ValidationIssue(key="K", value="v", rule="numeric", message="bad")],
    )
    assert result.is_clean is False


def test_result_as_dict_structure():
    result = ValidationResult(file="a.env")
    d = result.as_dict()
    assert d["file"] == "a.env"
    assert d["is_clean"] is True
    assert d["issues"] == []


# ---------------------------------------------------------------------------
# validate_env – passing cases
# ---------------------------------------------------------------------------

def test_clean_env_returns_no_issues():
    env = _env(PORT="8080", DEBUG="true", URL="https://example.com")
    rules = {"PORT": "numeric", "DEBUG": "boolean", "URL": "url"}
    result = validate_env(env, rules, file="prod.env")
    assert result.is_clean
    assert result.file == "prod.env"


def test_missing_key_in_env_skips_rule():
    """Keys in rules but absent from env are silently skipped (not an issue)."""
    result = validate_env({}, rules={"PORT": "numeric"})
    assert result.is_clean


# ---------------------------------------------------------------------------
# validate_env – failing cases
# ---------------------------------------------------------------------------

def test_numeric_rule_fails_for_non_numeric():
    result = validate_env(_env(PORT="abc"), rules={"PORT": "numeric"})
    assert not result.is_clean
    assert result.issues[0].key == "PORT"
    assert result.issues[0].rule == "numeric"


def test_boolean_rule_fails_for_arbitrary_string():
    result = validate_env(_env(DEBUG="maybe"), rules={"DEBUG": "boolean"})
    assert not result.is_clean


def test_url_rule_fails_for_plain_string():
    result = validate_env(_env(API="not-a-url"), rules={"API": "url"})
    assert not result.is_clean


def test_custom_regex_rule_passes():
    result = validate_env(_env(HEX="deadbeef"), rules={"HEX": r"^[0-9a-f]+$"})
    assert result.is_clean


def test_custom_regex_rule_fails():
    result = validate_env(_env(HEX="ZZZZ"), rules={"HEX": r"^[0-9a-f]+$"})
    assert not result.is_clean


# ---------------------------------------------------------------------------
# required_keys
# ---------------------------------------------------------------------------

def test_required_key_present_no_issue():
    result = validate_env(_env(SECRET="abc"), rules={}, required_keys=["SECRET"])
    assert result.is_clean


def test_required_key_missing_adds_issue():
    result = validate_env({}, rules={}, required_keys=["SECRET"])
    assert not result.is_clean
    assert result.issues[0].key == "SECRET"
    assert result.issues[0].rule == "required"


def test_multiple_required_keys_all_missing():
    result = validate_env({}, rules={}, required_keys=["A", "B", "C"])
    assert len(result.issues) == 3


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_invalid_regex_raises_validate_error():
    with pytest.raises(ValidateError, match="Invalid rule pattern"):
        validate_env(_env(K="v"), rules={"K": "[unclosed"})


# ---------------------------------------------------------------------------
# ValidationIssue __str__
# ---------------------------------------------------------------------------

def test_issue_str_contains_key_and_rule():
    issue = ValidationIssue(key="PORT", value="abc", rule="numeric", message="bad")
    s = str(issue)
    assert "PORT" in s
    assert "numeric" in s
