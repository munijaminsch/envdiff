"""Compare parsed .env dictionaries and produce structured diff results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyDiff:
    key: str
    status: str  # 'match' | 'mismatch' | 'missing_in_left' | 'missing_in_right'
    left_value: Optional[str]
    right_value: Optional[str]

    def __str__(self) -> str:  # noqa: D105
        if self.status == "missing_in_right":
            return f"  - {self.key}: missing in right"
        if self.status == "missing_in_left":
            return f"  - {self.key}: missing in left"
        if self.status == "mismatch":
            return f"  ~ {self.key}: {self.left_value!r} != {self.right_value!r}"
        return f"  = {self.key}: match"


@dataclass
class CompareResult:
    left_file: str
    right_file: str
    diffs: List[KeyDiff] = field(default_factory=list)

    def has_differences(self) -> bool:
        """Return True if any diff is not a match."""
        return any(d.status != "match" for d in self.diffs)

    def missing_in_left(self) -> List[KeyDiff]:
        """Keys present in right but absent in left."""
        return [d for d in self.diffs if d.status == "missing_in_left"]

    def missing_in_right(self) -> List[KeyDiff]:
        """Keys present in left but absent in right."""
        return [d for d in self.diffs if d.status == "missing_in_right"]

    def mismatches(self) -> List[KeyDiff]:
        """Keys present in both files but with differing values."""
        return [d for d in self.diffs if d.status == "mismatch"]

    def matches(self) -> List[KeyDiff]:
        """Keys present in both files with identical values."""
        return [d for d in self.diffs if d.status == "match"]


def compare(
    left: Dict[str, str],
    right: Dict[str, str],
    left_file: str = "left",
    right_file: str = "right",
) -> CompareResult:
    """Compare two env dicts and return a CompareResult."""
    all_keys = sorted(set(left) | set(right))
    diffs: List[KeyDiff] = []

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and in_right:
            if left[key] == right[key]:
                status = "match"
            else:
                status = "mismatch"
            diffs.append(
                KeyDiff(
                    key=key,
                    status=status,
                    left_value=left[key],
                    right_value=right[key],
                )
            )
        elif in_left:
            diffs.append(
                KeyDiff(
                    key=key,
                    status="missing_in_right",
                    left_value=left[key],
                    right_value=None,
                )
            )
        else:
            diffs.append(
                KeyDiff(
                    key=key,
                    status="missing_in_left",
                    left_value=None,
                    right_value=right[key],
                )
            )

    return CompareResult(left_file=left_file, right_file=right_file, diffs=diffs)
