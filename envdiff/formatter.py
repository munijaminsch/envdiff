"""Formatters for rendering comparison results and report summaries."""

from abc import ABC, abstractmethod
from typing import Union
import json

from envdiff.comparator import CompareResult
from envdiff.reporter import ReportSummary, build_summary


class Formatter(ABC):
    """Base class for all output formatters."""

    @abstractmethod
    def format(self, result: CompareResult, left_file: str = "left", right_file: str = "right") -> str:
        ...


class TextFormatter(Formatter):
    """Renders comparison results as human-readable text."""

    def format(self, result: CompareResult, left_file: str = "left", right_file: str = "right") -> str:
        summary = build_summary(result, left_file=left_file, right_file=right_file)
        lines = []

        if summary.is_clean:
            lines.append(f"No differences found between {left_file} and {right_file}.")
            return "\n".join(lines)

        lines.append(f"Comparing {left_file} <-> {right_file}")
        lines.append(f"  Total keys : {summary.total_keys}")
        lines.append(f"  Issues     : {summary.total_issues}")
        lines.append("")

        if result.missing_in_right:
            lines.append(f"Missing in {right_file}:")
            for key in sorted(result.missing_in_right):
                lines.append(f"  - {key}")

        if result.missing_in_left:
            lines.append(f"Missing in {left_file}:")
            for key in sorted(result.missing_in_left):
                lines.append(f"  - {key}")

        if result.mismatched:
            lines.append("Value mismatches:")
            for diff in sorted(result.mismatched, key=lambda d: d.key):
                lines.append(f"  ~ {diff.key}")
                lines.append(f"      {left_file}: {diff.left_value}")
                lines.append(f"      {right_file}: {diff.right_value}")

        if summary.warnings:
            lines.append("Warnings:")
            for w in summary.warnings:
                lines.append(f"  ! {w}")

        return "\n".join(lines)


class JsonFormatter(Formatter):
    """Renders comparison results as JSON, including a summary block."""

    def format(self, result: CompareResult, left_file: str = "left", right_file: str = "right") -> str:
        summary = build_summary(result, left_file=left_file, right_file=right_file)
        payload = {
            "summary": summary.as_dict(),
            "missing_in_left": sorted(result.missing_in_left),
            "missing_in_right": sorted(result.missing_in_right),
            "mismatched": [
                {
                    "key": d.key,
                    "left_value": d.left_value,
                    "right_value": d.right_value,
                }
                for d in sorted(result.mismatched, key=lambda d: d.key)
            ],
            "matching": sorted(result.matching),
        }
        return json.dumps(payload, indent=2)
