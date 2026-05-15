"""Tests for envdiff.formatter."""

import json
import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.formatter import JsonFormatter, TextFormatter, get_formatter


ENV_NAMES = ("staging", "production")


def _make_result(
    missing_left=None, missing_right=None, mismatches=None
) -> CompareResult:
    return CompareResult(
        missing_in_left=set(missing_left or []),
        missing_in_right=set(missing_right or []),
        value_mismatches=list(mismatches or []),
    )


# ---------------------------------------------------------------------------
# TextFormatter
# ---------------------------------------------------------------------------

class TestTextFormatter:
    def test_no_differences_message(self):
        result = _make_result()
        out = TextFormatter().format(result, ENV_NAMES)
        assert "No differences" in out
        assert "staging" in out
        assert "production" in out

    def test_missing_in_right_shown(self):
        result = _make_result(missing_right=["SECRET_KEY"])
        out = TextFormatter().format(result, ENV_NAMES)
        assert "SECRET_KEY" in out
        assert "PRODUCTION" in out

    def test_missing_in_left_shown(self):
        result = _make_result(missing_left=["NEW_VAR"])
        out = TextFormatter().format(result, ENV_NAMES)
        assert "NEW_VAR" in out
        assert "STAGING" in out

    def test_mismatch_shown(self):
        diff = KeyDiff(key="DB_HOST", left_value="localhost", right_value="db.prod.internal")
        result = _make_result(mismatches=[diff])
        out = TextFormatter().format(result, ENV_NAMES)
        assert "DB_HOST" in out
        assert "localhost" in out
        assert "db.prod.internal" in out
        assert "MISMATCH" in out

    def test_issue_count_in_summary(self):
        diff = KeyDiff(key="X", left_value="a", right_value="b")
        result = _make_result(missing_right=["Y"], mismatches=[diff])
        out = TextFormatter().format(result, ENV_NAMES)
        assert "2 issue(s)" in out


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    def test_valid_json_output(self):
        result = _make_result()
        raw = JsonFormatter().format(result, ENV_NAMES)
        data = json.loads(raw)
        assert data["left"] == "staging"
        assert data["right"] == "production"
        assert data["has_differences"] is False

    def test_missing_keys_serialised(self):
        result = _make_result(missing_right=["API_KEY"], missing_left=["LOG_LEVEL"])
        data = json.loads(JsonFormatter().format(result, ENV_NAMES))
        assert "API_KEY" in data["missing_in_right"]
        assert "LOG_LEVEL" in data["missing_in_left"]

    def test_mismatch_serialised(self):
        diff = KeyDiff(key="PORT", left_value="8080", right_value="80")
        result = _make_result(mismatches=[diff])
        data = json.loads(JsonFormatter().format(result, ENV_NAMES))
        assert data["value_mismatches"][0]["key"] == "PORT"


# ---------------------------------------------------------------------------
# get_formatter helper
# ---------------------------------------------------------------------------

def test_get_formatter_text():
    assert isinstance(get_formatter("text"), TextFormatter)


def test_get_formatter_json():
    assert isinstance(get_formatter("json"), JsonFormatter)


def test_get_formatter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown formatter"):
        get_formatter("xml")
