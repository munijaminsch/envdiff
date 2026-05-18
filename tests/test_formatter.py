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
        assert len(data["value_mismatches"]) == 1
        mismatch = data["value_mismatches"][0]
        assert mismatch["key"] == "PORT"
        assert mismatch["left_value"] == "8080"
        assert mismatch["right_value"] == "80"

    def test_has_differences_true_when_mismatches(self):
        diff = KeyDiff(key="TIMEOUT", left_value="30", right_value="60")
        result = _make_result(mismatches=[diff])
        data = json.loads(JsonFormatter().format(result, ENV_NAMES))
        assert data["has_differences"] is True


# ---------------------------------------------------------------------------
# get_formatter
# ---------------------------------------------------------------------------

class TestGetFormatter:
    def test_returns_text_formatter(self):
        assert isinstance(get_formatter("text"), TextFormatter)

    def test_returns_json_formatter(self):
        assert isinstance(get_formatter("json"), JsonFormatter)

    def test_unknown_format_raises(self):
        with pytest.raises((ValueError, KeyError)):
            get_formatter("xml")
