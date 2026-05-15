"""Export comparison results to various file formats."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Union

from envdiff.comparator import CompareResult
from envdiff.reporter import ReportSummary


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_json(result: CompareResult, summary: ReportSummary, dest: Path) -> None:
    """Write comparison result and summary to a JSON file."""
    payload = {
        "summary": summary.as_dict(),
        "differences": [
            {
                "key": diff.key,
                "status": diff.status,
                "left_value": diff.left_value,
                "right_value": diff.right_value,
            }
            for diff in result.diffs
        ],
    }
    try:
        dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"Failed to write JSON export to {dest}: {exc}") from exc


def export_csv(result: CompareResult, dest: Path) -> None:
    """Write comparison result differences to a CSV file."""
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=["key", "status", "left_value", "right_value"]
    )
    writer.writeheader()
    for diff in result.diffs:
        writer.writerow(
            {
                "key": diff.key,
                "status": diff.status,
                "left_value": diff.left_value if diff.left_value is not None else "",
                "right_value": diff.right_value if diff.right_value is not None else "",
            }
        )
    try:
        dest.write_text(buf.getvalue(), encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"Failed to write CSV export to {dest}: {exc}") from exc


def export_result(
    result: CompareResult,
    summary: ReportSummary,
    dest: Union[str, Path],
    fmt: str = "json",
) -> None:
    """Dispatch export to the appropriate format handler."""
    dest = Path(dest)
    fmt = fmt.lower()
    if fmt == "json":
        export_json(result, summary, dest)
    elif fmt == "csv":
        export_csv(result, dest)
    else:
        raise ExportError(f"Unsupported export format: {fmt!r}")
