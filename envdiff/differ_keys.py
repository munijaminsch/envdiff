"""Key-level diff: show which keys appear in one env but not another."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class KeyDiffError(Exception):
    """Raised when key-level diffing fails."""


@dataclass
class KeyOnlyEntry:
    key: str
    value: str
    side: str  # 'left' or 'right'

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "side": self.side}


@dataclass
class KeyDiffResult:
    left_source: str
    right_source: str
    only_in_left: List[KeyOnlyEntry] = field(default_factory=list)
    only_in_right: List[KeyOnlyEntry] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.only_in_left and not self.only_in_right

    @property
    def total_exclusive(self) -> int:
        return len(self.only_in_left) + len(self.only_in_right)

    def as_dict(self) -> dict:
        return {
            "left_source": self.left_source,
            "right_source": self.right_source,
            "only_in_left": [e.as_dict() for e in self.only_in_left],
            "only_in_right": [e.as_dict() for e in self.only_in_right],
            "total_exclusive": self.total_exclusive,
            "is_clean": self.is_clean,
        }


def diff_keys(
    left: Dict[str, str],
    right: Dict[str, str],
    left_source: str = "",
    right_source: str = "",
) -> KeyDiffResult:
    """Return keys that exist exclusively in left or right."""
    if left is None or right is None:
        raise KeyDiffError("Both left and right env dicts are required.")

    left_keys = set(left.keys())
    right_keys = set(right.keys())

    only_left = [
        KeyOnlyEntry(key=k, value=left[k], side="left")
        for k in sorted(left_keys - right_keys)
    ]
    only_right = [
        KeyOnlyEntry(key=k, value=right[k], side="right")
        for k in sorted(right_keys - left_keys)
    ]

    return KeyDiffResult(
        left_source=left_source,
        right_source=right_source,
        only_in_left=only_left,
        only_in_right=only_right,
    )
