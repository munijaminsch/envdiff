"""Build human-readable summary reports from comparison results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from envdiff.comparator import CompareResult


@dataclass
class ReportSummary:
    left_file: str
    right_file: str
    total_keys: int
    matching: int
    missing_in_right: int
    missing_in_left: int
    mismatches: int

    @property
    def total_issues(self) -> int:
        """Sum of all non-matching differences."""
        return self.missing_in_right + self.missing_in_left + self.mismatches

    @property
    def is_clean(self) -> bool:
        """True when there are no issues."""
        return self.total_issues == 0

    def as_dict(self) -> Dict[str, object]:
        """Serialise summary to a plain dictionary."""
        return {
            "left_file": self.left_file,
            "right_file": self.right_file,
            "total_keys": self.total_keys,
            "matching": self.matching,
            "missing_in_right": self.missing_in_right,
            "missing_in_left": self.missing_in_left,
            "mismatches": self.mismatches,
            "total_issues": self.total_issues,
            "is_clean": self.is_clean,
        }


def build_summary(result: CompareResult) -> ReportSummary:
    """Derive a ReportSummary from a CompareResult."""
    return ReportSummary(
        left_file=result.left_file,
        right_file=result.right_file,
        total_keys=len(result.diffs),
        matching=len(result.matches()),
        missing_in_right=len(result.missing_in_right()),
        missing_in_left=len(result.missing_in_left()),
        mismatches=len(result.mismatches()),
    )
