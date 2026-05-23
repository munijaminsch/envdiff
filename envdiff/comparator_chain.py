"""Chain multiple CompareResults into a unified pipeline result."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import CompareResult


class ChainError(Exception):
    """Raised when the comparator chain cannot be built."""


@dataclass
class ChainEntry:
    index: int
    left: str
    right: str
    result: CompareResult

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "left": self.left,
            "right": self.right,
            "missing_in_right": list(self.result.missing_in_right()),
            "missing_in_left": list(self.result.missing_in_left()),
            "mismatched": [
                {"key": d.key, "left": d.left_value, "right": d.right_value}
                for d in self.result.value_mismatches()
            ],
            "has_differences": self.result.has_differences(),
        }


@dataclass
class ChainResult:
    entries: List[ChainEntry] = field(default_factory=list)

    @property
    def total_pairs(self) -> int:
        return len(self.entries)

    @property
    def clean_pairs(self) -> int:
        return sum(1 for e in self.entries if not e.result.has_differences())

    @property
    def dirty_pairs(self) -> int:
        return self.total_pairs - self.clean_pairs

    def is_clean(self) -> bool:
        return self.dirty_pairs == 0

    def as_dict(self) -> dict:
        return {
            "total_pairs": self.total_pairs,
            "clean_pairs": self.clean_pairs,
            "dirty_pairs": self.dirty_pairs,
            "is_clean": self.is_clean(),
            "entries": [e.as_dict() for e in self.entries],
        }


def build_chain(pairs: List[tuple[str, str, CompareResult]]) -> ChainResult:
    """Build a ChainResult from a list of (left_name, right_name, CompareResult) tuples."""
    if not isinstance(pairs, list):
        raise ChainError("pairs must be a list")
    entries = []
    for idx, item in enumerate(pairs):
        if len(item) != 3:
            raise ChainError(f"Each pair must be a 3-tuple, got length {len(item)} at index {idx}")
        left, right, result = item
        if not isinstance(result, CompareResult):
            raise ChainError(f"Expected CompareResult at index {idx}, got {type(result).__name__}")
        entries.append(ChainEntry(index=idx, left=left, right=right, result=result))
    return ChainResult(entries=entries)
