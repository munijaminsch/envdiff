"""Tests for envdiff.exporter."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.exporter import ExportError, export_csv, export_json, export_result
from envdiff.reporter import build_summary


def _make_result() -> CompareResult:
    return CompareResult(
        left_file="a.env",
        right_file="b.env",
        diffs=[
            KeyDiff(key="DB_HOST", status="missing_in_right", left_value="localhost", right_value=None),
            KeyDiff(key="API_KEY", status="mismatch", left_value="abc", right_value="xyz"),
            KeyDiff(key="PORT", status="match", left_value="8080", right_value="8080"),
        ],
    )


def test_export_json_creates_file(tmp_path: Path) -> None:
    result = _make_result()
    summary = build_summary(result)
    dest = tmp_path / "report.json"
    export_json(result, summary, dest)
    assert dest.exists()


def test_export_json_content(tmp_path: Path) -> None:
    result = _make_result()
    summary = build_summary(result)
    dest = tmp_path / "report.json"
    export_json(result, summary, dest)
    data = json.loads(dest.read_text())
    assert data["summary"]["total_issues"] == 2
    assert len(data["differences"]) == 3
    keys = [d["key"] for d in data["differences"]]
    assert "DB_HOST" in keys
    assert "API_KEY" in keys


def test_export_csv_creates_file(tmp_path: Path) -> None:
    result = _make_result()
    dest = tmp_path / "report.csv"
    export_csv(result, dest)
    assert dest.exists()


def test_export_csv_content(tmp_path: Path) -> None:
    result = _make_result()
    dest = tmp_path / "report.csv"
    export_csv(result, dest)
    rows = list(csv.DictReader(dest.read_text().splitlines()))
    assert len(rows) == 3
    assert rows[0]["key"] == "DB_HOST"
    assert rows[0]["status"] == "missing_in_right"
    assert rows[0]["right_value"] == ""


def test_export_result_dispatches_json(tmp_path: Path) -> None:
    result = _make_result()
    summary = build_summary(result)
    dest = tmp_path / "out.json"
    export_result(result, summary, dest, fmt="json")
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert "summary" in data


def test_export_result_dispatches_csv(tmp_path: Path) -> None:
    result = _make_result()
    summary = build_summary(result)
    dest = tmp_path / "out.csv"
    export_result(result, summary, dest, fmt="csv")
    assert dest.exists()


def test_export_result_raises_for_unknown_format(tmp_path: Path) -> None:
    result = _make_result()
    summary = build_summary(result)
    with pytest.raises(ExportError, match="Unsupported export format"):
        export_result(result, summary, tmp_path / "out.xml", fmt="xml")


def test_export_json_raises_on_bad_path() -> None:
    result = _make_result()
    summary = build_summary(result)
    bad_path = Path("/nonexistent_dir/report.json")
    with pytest.raises(ExportError, match="Failed to write JSON export"):
        export_json(result, summary, bad_path)


def test_export_csv_raises_on_bad_path() -> None:
    result = _make_result()
    bad_path = Path("/nonexistent_dir/report.csv")
    with pytest.raises(ExportError, match="Failed to write CSV export"):
        export_csv(result, bad_path)
