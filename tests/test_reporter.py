"""Tests for envdiff.reporter."""

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.reporter import ReportSummary, build_summary


def _make_result(
    missing_in_left=None,
    missing_in_right=None,
    mismatched=None,
    matching=None,
):
    return CompareResult(
        missing_in_left=missing_in_left or [],
        missing_in_right=missing_in_right or [],
        mismatched=mismatched or [],
        matching=matching or [],
    )


def test_build_summary_returns_report_summary():
    result = _make_result(matching=["A", "B"])
    summary = build_summary(result, left_file="a.env", right_file="b.env")
    assert isinstance(summary, ReportSummary)


def test_summary_file_names():
    result = _make_result()
    summary = build_summary(result, left_file="prod.env", right_file="dev.env")
    assert summary.left_file == "prod.env"
    assert summary.right_file == "dev.env"


def test_summary_counts_matching():
    result = _make_result(matching=["KEY1", "KEY2", "KEY3"])
    summary = build_summary(result)
    assert summary.matching == 3
    assert summary.total_keys == 3


def test_summary_counts_missing_in_right():
    result = _make_result(missing_in_right=["ONLY_LEFT"])
    summary = build_summary(result)
    assert summary.missing_in_right == 1
    assert summary.total_issues == 1


def test_summary_counts_missing_in_left():
    result = _make_result(missing_in_left=["ONLY_RIGHT"])
    summary = build_summary(result)
    assert summary.missing_in_left == 1


def test_summary_counts_mismatched():
    diffs = [KeyDiff(key="DB_URL", left_value="sqlite", right_value="postgres")]
    result = _make_result(mismatched=diffs)
    summary = build_summary(result)
    assert summary.mismatched == 1
    assert summary.total_issues == 1


def test_is_clean_when_no_issues():
    result = _make_result(matching=["A"])
    summary = build_summary(result)
    assert summary.is_clean is True


def test_is_not_clean_when_issues_exist():
    result = _make_result(missing_in_right=["X"])
    summary = build_summary(result)
    assert summary.is_clean is False


def test_total_keys_counts_all_unique():
    diffs = [KeyDiff(key="PORT", left_value="8000", right_value="9000")]
    result = _make_result(
        missing_in_left=["A"],
        missing_in_right=["B"],
        mismatched=diffs,
        matching=["C"],
    )
    summary = build_summary(result)
    assert summary.total_keys == 4


def test_empty_files_produce_warning():
    result = _make_result()
    summary = build_summary(result)
    assert any("empty" in w.lower() for w in summary.warnings)


def test_as_dict_contains_expected_keys():
    result = _make_result(matching=["KEY"])
    summary = build_summary(result)
    d = summary.as_dict()
    for key in ("left_file", "right_file", "total_keys", "missing_in_left",
                "missing_in_right", "mismatched", "matching",
                "total_issues", "is_clean", "warnings"):
        assert key in d
