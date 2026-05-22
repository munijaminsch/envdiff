"""Compare values for keys that exist in both env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ValueDiffError(Exception):
    """Raised when value diffing fails."""


@dataclass
class ValueEntry:
    key: str
    left_value: str
    right_value: str
    changed: bool

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "left_value": self.left_value,
            "right_value": self.right_value,
            "changed": self.changed,
        }


@dataclass
class ValueDiffResult:
    left_source: str
    right_source: str
    entries: List[ValueEntry] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not any(e.changed for e in self.entries)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def changed_count(self) -> int:
        return sum(1 for e in self.entries if e.changed)

    @property
    def unchanged_count(self) -> int:
        return sum(1 for e in self.entries if not e.changed)

    def as_dict(self) -> dict:
        return {
            "left_source": self.left_source,
            "right_source": self.right_source,
            "is_clean": self.is_clean,
            "total_keys": self.total_keys,
            "changed_count": self.changed_count,
            "unchanged_count": self.unchanged_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def diff_values(
    left: Dict[str, str],
    right: Dict[str, str],
    *,
    left_source: str = "",
    right_source: str = "",
    keys_only: Optional[List[str]] = None,
) -> ValueDiffResult:
    """Compare values for shared keys between two env dicts.

    Only keys present in *both* dicts are included unless ``keys_only``
    is provided, in which case only those keys are considered.
    """
    if left is None or right is None:
        raise ValueDiffError("Both left and right env dicts are required.")

    shared = sorted(set(left) & set(right))
    if keys_only is not None:
        shared = [k for k in keys_only if k in shared]

    entries = [
        ValueEntry(
            key=k,
            left_value=left[k],
            right_value=right[k],
            changed=left[k] != right[k],
        )
        for k in shared
    ]
    return ValueDiffResult(
        left_source=left_source,
        right_source=right_source,
        entries=entries,
    )
