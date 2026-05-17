"""Scores .env file similarity based on key overlap and value matches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from envdiff.comparator import CompareResult


class ScoreError(Exception):
    """Raised when scoring cannot be performed."""


@dataclass
class SimilarityScore:
    left_file: str
    right_file: str
    total_keys: int
    matching_keys: int
    missing_in_right: int
    missing_in_left: int
    mismatched_values: int

    @property
    def key_overlap(self) -> float:
        """Fraction of keys present in both files (0.0 – 1.0)."""
        if self.total_keys == 0:
            return 1.0
        shared = self.total_keys - self.missing_in_right - self.missing_in_left
        return round(shared / self.total_keys, 4)

    @property
    def value_similarity(self) -> float:
        """Among shared keys, fraction whose values match (0.0 – 1.0)."""
        shared = self.total_keys - self.missing_in_right - self.missing_in_left
        if shared == 0:
            return 1.0
        return round(self.matching_keys / shared, 4)

    @property
    def overall(self) -> float:
        """Composite score: key_overlap * value_similarity (0.0 – 1.0)."""
        return round(self.key_overlap * self.value_similarity, 4)

    def as_dict(self) -> Dict[str, object]:
        return {
            "left_file": self.left_file,
            "right_file": self.right_file,
            "total_keys": self.total_keys,
            "matching_keys": self.matching_keys,
            "missing_in_right": self.missing_in_right,
            "missing_in_left": self.missing_in_left,
            "mismatched_values": self.mismatched_values,
            "key_overlap": self.key_overlap,
            "value_similarity": self.value_similarity,
            "overall": self.overall,
        }


def score_result(result: CompareResult) -> SimilarityScore:
    """Compute a SimilarityScore from a CompareResult."""
    if not isinstance(result, CompareResult):
        raise ScoreError("Expected a CompareResult instance.")

    all_keys = (
        set(result.missing_in_right)
        | set(result.missing_in_left)
        | set(result.mismatches)
        | set(result.matches)
    )
    total = len(all_keys)
    matching = len(result.matches)
    mir = len(result.missing_in_right)
    mil = len(result.missing_in_left)
    mismatched = len(result.mismatches)

    return SimilarityScore(
        left_file=result.left_file,
        right_file=result.right_file,
        total_keys=total,
        matching_keys=matching,
        missing_in_right=mir,
        missing_in_left=mil,
        mismatched_values=mismatched,
    )
