"""linker.py — Cross-reference keys between two env dicts and produce a link map."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class LinkError(Exception):
    """Raised when linking fails."""


@dataclass
class LinkedKey:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]
    is_shared: bool
    values_match: bool

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "left_value": self.left_value,
            "right_value": self.right_value,
            "is_shared": self.is_shared,
            "values_match": self.values_match,
        }


@dataclass
class LinkResult:
    left_source: str
    right_source: str
    entries: List[LinkedKey] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def shared_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_shared]

    @property
    def exclusive_left(self) -> List[str]:
        return [e.key for e in self.entries if e.left_value is not None and not e.is_shared]

    @property
    def exclusive_right(self) -> List[str]:
        return [e.key for e in self.entries if e.right_value is not None and not e.is_shared]

    @property
    def is_clean(self) -> bool:
        return all(e.values_match for e in self.entries if e.is_shared)

    def as_dict(self) -> dict:
        return {
            "left_source": self.left_source,
            "right_source": self.right_source,
            "total_keys": self.total_keys,
            "shared_keys": self.shared_keys,
            "exclusive_left": self.exclusive_left,
            "exclusive_right": self.exclusive_right,
            "is_clean": self.is_clean,
            "entries": [e.as_dict() for e in self.entries],
        }


def link_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    left_source: str = "",
    right_source: str = "",
) -> LinkResult:
    """Build a LinkResult cross-referencing all keys from both dicts."""
    if left is None or right is None:
        raise LinkError("Both left and right env dicts are required.")

    all_keys = sorted(set(left) | set(right))
    entries: List[LinkedKey] = []

    for key in all_keys:
        lv = left.get(key)
        rv = right.get(key)
        shared = key in left and key in right
        match = shared and lv == rv
        entries.append(LinkedKey(
            key=key,
            left_value=lv,
            right_value=rv,
            is_shared=shared,
            values_match=match,
        ))

    return LinkResult(
        left_source=left_source,
        right_source=right_source,
        entries=entries,
    )
