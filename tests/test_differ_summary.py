"""Tests for envdiff.differ_summary."""

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.differ_summary import (
    DiffSummary,
    DiffSummaryLine,
    SummaryError,
    build_diff_summary,
)


def _make_result(
    diffs=None,
    matching=None,
    left="a.env",
    right="b.env",
) -> CompareResult:
    return CompareResult(
        left_file=left,
        right_file=right,
        diffs=diffs or [],
        matching=matching or [],
    )


def test_build_summary_returns_diff_summary():
    result = _make_result()
    summary = build_diff_summary(result)
    assert isinstance(summary, DiffSummary)


def test_none_result_raises():
    with pytest.raises(SummaryError):
        build_diff_summary(None)


def test_file_names_preserved():
    result = _make_result(left="dev.env", right="prod.env")
    summary = build_diff_summary(result)
    assert summary.left_file == "dev.env"
    assert summary.right_file == "prod.env"


def test_matching_keys_produce_match_status():
    result = _make_result(matching=["FOO", "BAR"])
    summary = build_diff_summary(result)
    statuses = {ln.key: ln.status for ln in summary.lines}
    assert statuses["FOO"] == "match"
    assert statuses["BAR"] == "match"


def test_missing_right_status():
    diffs = [KeyDiff(key="SECRET", left_value="abc", right_value=None)]
    result = _make_result(diffs=diffs)
    summary = build_diff_summary(result)
    line = summary.lines[0]
    assert line.status == "missing_right"
    assert "SECRET" in line.key


def test_missing_left_status():
    diffs = [KeyDiff(key="TOKEN", left_value=None, right_value="xyz")]
    result = _make_result(diffs=diffs)
    summary = build_diff_summary(result)
    line = summary.lines[0]
    assert line.status == "missing_left"


def test_mismatch_status():
    diffs = [KeyDiff(key="PORT", left_value="3000", right_value="8080")]
    result = _make_result(diffs=diffs)
    summary = build_diff_summary(result)
    line = summary.lines[0]
    assert line.status == "mismatch"
    assert "3000" in line.detail
    assert "8080" in line.detail


def test_total_keys_counts_all():
    diffs = [KeyDiff(key="A", left_value="1", right_value=None)]
    result = _make_result(diffs=diffs, matching=["B", "C"])
    summary = build_diff_summary(result)
    assert summary.total_keys == 3


def test_issue_count_excludes_matches():
    diffs = [
        KeyDiff(key="X", left_value="1", right_value=None),
        KeyDiff(key="Y", left_value=None, right_value="2"),
    ]
    result = _make_result(diffs=diffs, matching=["Z"])
    summary = build_diff_summary(result)
    assert summary.issue_count == 2


def test_is_clean_when_no_diffs():
    result = _make_result(matching=["FOO"])
    summary = build_diff_summary(result)
    assert summary.is_clean is True


def test_not_clean_when_diffs_present():
    diffs = [KeyDiff(key="K", left_value="v", right_value=None)]
    result = _make_result(diffs=diffs)
    summary = build_diff_summary(result)
    assert summary.is_clean is False


def test_lines_sorted_alphabetically():
    diffs = [
        KeyDiff(key="ZEBRA", left_value="z", right_value=None),
        KeyDiff(key="APPLE", left_value=None, right_value="a"),
    ]
    result = _make_result(diffs=diffs)
    summary = build_diff_summary(result)
    keys = [ln.key for ln in summary.lines]
    assert keys == sorted(keys, key=str.lower)


def test_as_dict_structure():
    result = _make_result(matching=["FOO"])
    summary = build_diff_summary(result)
    d = summary.as_dict()
    assert "left_file" in d
    assert "right_file" in d
    assert "total_keys" in d
    assert "issue_count" in d
    assert "is_clean" in d
    assert isinstance(d["lines"], list)


def test_line_as_dict_keys():
    line = DiffSummaryLine(key="K", status="match", detail="identical in both files")
    d = line.as_dict()
    assert set(d.keys()) == {"key", "status", "detail"}
