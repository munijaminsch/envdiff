"""Generates summary reports from CompareResult objects."""

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import CompareResult


@dataclass
class ReportSummary:
    """A structured summary of a comparison report."""

    left_file: str
    right_file: str
    total_keys: int
    missing_in_left: int
    missing_in_right: int
    mismatched: int
    matching: int
    warnings: List[str] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return self.missing_in_left + self.missing_in_right + self.mismatched

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0

    def as_dict(self) -> dict:
        return {
            "left_file": self.left_file,
            "right_file": self.right_file,
            "total_keys": self.total_keys,
            "missing_in_left": self.missing_in_left,
            "missing_in_right": self.missing_in_right,
            "mismatched": self.mismatched,
            "matching": self.matching,
            "total_issues": self.total_issues,
            "is_clean": self.is_clean,
            "warnings": self.warnings,
        }


def build_summary(
    result: CompareResult,
    left_file: str = "left",
    right_file: str = "right",
) -> ReportSummary:
    """Build a ReportSummary from a CompareResult."""
    all_keys = (
        set(result.missing_in_left)
        | set(result.missing_in_right)
        | set(d.key for d in result.mismatched)
        | set(result.matching)
    )

    warnings: List[str] = []
    if not all_keys:
        warnings.append("Both files appear to be empty.")

    return ReportSummary(
        left_file=left_file,
        right_file=right_file,
        total_keys=len(all_keys),
        missing_in_left=len(result.missing_in_left),
        missing_in_right=len(result.missing_in_right),
        mismatched=len(result.mismatched),
        matching=len(result.matching),
        warnings=warnings,
    )
