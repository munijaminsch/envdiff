"""Integration tests: exporter wired through resolver + comparator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.comparator import compare
from envdiff.exporter import export_result
from envdiff.parser import parse_env_file
from envdiff.reporter import build_summary


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_full_pipeline_json(env_dir: Path) -> None:
    left = _write(env_dir, ".env.staging", "DB=postgres\nPORT=5432\nSECRET=abc\n")
    right = _write(env_dir, ".env.prod", "DB=postgres\nPORT=5432\nDEBUG=false\n")

    left_data = parse_env_file(left)
    right_data = parse_env_file(right)
    result = compare(left_data, right_data, left_file=str(left), right_file=str(right))
    summary = build_summary(result)

    dest = env_dir / "report.json"
    export_result(result, summary, dest, fmt="json")

    data = json.loads(dest.read_text())
    assert data["summary"]["total_issues"] == 2
    statuses = {d["key"]: d["status"] for d in data["differences"]}
    assert statuses["SECRET"] == "missing_in_right"
    assert statuses["DEBUG"] == "missing_in_left"
    assert statuses["DB"] == "match"


def test_full_pipeline_csv(env_dir: Path) -> None:
    import csv

    left = _write(env_dir, ".env.a", "KEY1=val1\nKEY2=old\n")
    right = _write(env_dir, ".env.b", "KEY1=val1\nKEY2=new\nKEY3=extra\n")

    left_data = parse_env_file(left)
    right_data = parse_env_file(right)
    result = compare(left_data, right_data, left_file=str(left), right_file=str(right))
    summary = build_summary(result)

    dest = env_dir / "report.csv"
    export_result(result, summary, dest, fmt="csv")

    rows = list(csv.DictReader(dest.read_text().splitlines()))
    assert len(rows) == 3
    row_map = {r["key"]: r for r in rows}
    assert row_map["KEY2"]["status"] == "mismatch"
    assert row_map["KEY3"]["status"] == "missing_in_left"
    assert row_map["KEY3"]["left_value"] == ""


def test_clean_result_has_no_issues_in_export(env_dir: Path) -> None:
    left = _write(env_dir, ".env.x", "A=1\nB=2\n")
    right = _write(env_dir, ".env.y", "A=1\nB=2\n")

    left_data = parse_env_file(left)
    right_data = parse_env_file(right)
    result = compare(left_data, right_data, left_file=str(left), right_file=str(right))
    summary = build_summary(result)

    dest = env_dir / "clean.json"
    export_result(result, summary, dest, fmt="json")

    data = json.loads(dest.read_text())
    assert data["summary"]["is_clean"] is True
    assert data["summary"]["total_issues"] == 0
