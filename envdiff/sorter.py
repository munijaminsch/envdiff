"""Sort and group keys from a CompareResult by status or alphabetical order."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envdiff.comparator import CompareResult, KeyDiff


class SortError(Exception):
    """Raised when sorting fails due to invalid input."""


class SortOrder(str, Enum):
    ALPHA = "alpha"
    STATUS = "status"


@dataclass
class SortedResult:
    """A compare result with keys sorted according to a chosen strategy."""

    order: SortOrder
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return [d.key for d in self.diffs]

    def as_dict(self) -> dict:
        return {
            "order": self.order.value,
            "diffs": [
                {
                    "key": d.key,
                    "status": (
                        "missing_in_right"
                        if d.key in _missing_in_right_keys(self.diffs)
                        else "missing_in_left"
                        if d.key in _missing_in_left_keys(self.diffs)
                        else "mismatch"
                        if d.left != d.right
                        else "match"
                    ),
                }
                for d in self.diffs
            ],
        }


def _missing_in_right_keys(diffs: List[KeyDiff]) -> set:
    return {d.key for d in diffs if d.right is None}


def _missing_in_left_keys(diffs: List[KeyDiff]) -> set:
    return {d.key for d in diffs if d.left is None}


_STATUS_PRIORITY = {"missing_in_right": 0, "missing_in_left": 1, "mismatch": 2, "match": 3}


def _status_of(diff: KeyDiff) -> str:
    if diff.right is None:
        return "missing_in_right"
    if diff.left is None:
        return "missing_in_left"
    if diff.left != diff.right:
        return "mismatch"
    return "match"


def sort_result(result: CompareResult, order: SortOrder = SortOrder.ALPHA) -> SortedResult:
    """Return a SortedResult with diffs ordered by *order*."""
    if not isinstance(result, CompareResult):
        raise SortError(f"Expected CompareResult, got {type(result).__name__}")

    diffs = list(result.diffs)

    if order == SortOrder.ALPHA:
        diffs.sort(key=lambda d: d.key.lower())
    elif order == SortOrder.STATUS:
        diffs.sort(key=lambda d: (_STATUS_PRIORITY[_status_of(d)], d.key.lower()))
    else:
        raise SortError(f"Unknown sort order: {order!r}")

    return SortedResult(order=order, diffs=diffs)
