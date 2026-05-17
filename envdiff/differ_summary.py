"""Produces a human-readable summary report for a diff between two env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import CompareResult


class SummaryError(Exception):
    """Raised when summary generation fails."""


@dataclass
class DiffSummaryLine:
    """A single line entry in the diff summary."""

    key: str
    status: str  # 'missing_left', 'missing_right', 'mismatch', 'match'
    detail: str

    def as_dict(self) -> dict:
        return {"key": self.key, "status": self.status, "detail": self.detail}


@dataclass
class DiffSummary:
    """Full summary of a comparison between two env files."""

    left_file: str
    right_file: str
    lines: List[DiffSummaryLine] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.lines)

    @property
    def issue_count(self) -> int:
        return sum(1 for ln in self.lines if ln.status != "match")

    @property
    def is_clean(self) -> bool:
        return self.issue_count == 0

    def as_dict(self) -> dict:
        return {
            "left_file": self.left_file,
            "right_file": self.right_file,
            "total_keys": self.total_keys,
            "issue_count": self.issue_count,
            "is_clean": self.is_clean,
            "lines": [ln.as_dict() for ln in self.lines],
        }


def build_diff_summary(result: CompareResult) -> DiffSummary:
    """Build a DiffSummary from a CompareResult."""
    if result is None:
        raise SummaryError("result must not be None")

    lines: List[DiffSummaryLine] = []

    for diff in result.diffs:
        if diff.left_value is None:
            status = "missing_left"
            detail = f"only in {result.right_file}: {diff.right_value!r}"
        elif diff.right_value is None:
            status = "missing_right"
            detail = f"only in {result.left_file}: {diff.left_value!r}"
        else:
            status = "mismatch"
            detail = (
                f"{result.left_file}={diff.left_value!r} "
                f"vs {result.right_file}={diff.right_value!r}"
            )
        lines.append(DiffSummaryLine(key=diff.key, status=status, detail=detail))

    for key in result.matching:
        lines.append(
            DiffSummaryLine(key=key, status="match", detail="identical in both files")
        )

    lines.sort(key=lambda ln: ln.key.lower())
    return DiffSummary(
        left_file=result.left_file,
        right_file=result.right_file,
        lines=lines,
    )
