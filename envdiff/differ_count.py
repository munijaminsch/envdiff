"""Count-based diff: compare the number of keys across two env mappings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


class CountDiffError(Exception):
    """Raised when differ_count encounters invalid input."""


@dataclass
class CountEntry:
    key: str
    left_count: int
    right_count: int
    delta: int

    def as_dict(self) -> Dict:
        return {
            "key": self.key,
            "left_count": self.left_count,
            "right_count": self.right_count,
            "delta": self.delta,
        }


@dataclass
class CountDiffResult:
    left_source: str
    right_source: str
    left_total: int
    right_total: int
    entries: list = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return self.left_total == self.right_total

    @property
    def net_delta(self) -> int:
        return self.right_total - self.left_total

    def as_dict(self) -> Dict:
        return {
            "left_source": self.left_source,
            "right_source": self.right_source,
            "left_total": self.left_total,
            "right_total": self.right_total,
            "net_delta": self.net_delta,
            "is_clean": self.is_clean,
            "entries": [e.as_dict() for e in self.entries],
        }


def diff_counts(
    left: Dict[str, str],
    right: Dict[str, str],
    left_source: str = "",
    right_source: str = "",
) -> CountDiffResult:
    """Compare key counts between two env dicts and return a CountDiffResult."""
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise CountDiffError("Both left and right must be dicts.")

    all_keys = sorted(set(left) | set(right))
    entries = []
    for key in all_keys:
        lc = 1 if key in left else 0
        rc = 1 if key in right else 0
        delta = rc - lc
        entries.append(CountEntry(key=key, left_count=lc, right_count=rc, delta=delta))

    return CountDiffResult(
        left_source=left_source,
        right_source=right_source,
        left_total=len(left),
        right_total=len(right),
        entries=entries,
    )
