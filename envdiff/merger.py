"""Merge multiple .env files into a unified baseline with conflict detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


@dataclass
class MergeConflict:
    """Represents a key that has differing values across source files."""

    key: str
    values: Dict[str, Optional[str]]  # filename -> value

    def __str__(self) -> str:
        parts = ", ".join(f"{f}={v!r}" for f, v in self.values.items())
        return f"Conflict on '{self.key}': {parts}"


@dataclass
class MergeResult:
    """Result of merging multiple env dicts."""

    merged: Dict[str, Optional[str]] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def conflict_keys(self) -> List[str]:
        return [c.key for c in self.conflicts]


def merge_envs(
    named_envs: List[Tuple[str, Dict[str, Optional[str]]]],
    strategy: str = "first",
) -> MergeResult:
    """Merge a list of (name, env_dict) pairs into a single MergeResult.

    Args:
        named_envs: Ordered list of (filename, parsed_env) tuples.
        strategy: Conflict resolution — 'first' keeps the first value seen,
                  'last' keeps the last, 'error' raises MergeError on conflict.

    Returns:
        MergeResult with the merged dict and any detected conflicts.
    """
    if strategy not in ("first", "last", "error"):
        raise MergeError(f"Unknown merge strategy: {strategy!r}")

    merged: Dict[str, Optional[str]] = {}
    conflict_map: Dict[str, Dict[str, Optional[str]]] = {}
    sources = [name for name, _ in named_envs]

    for name, env in named_envs:
        for key, value in env.items():
            if key not in merged:
                merged[key] = value
                conflict_map[key] = {name: value}
            else:
                existing_value = merged[key]
                if existing_value != value:
                    if strategy == "error":
                        raise MergeError(
                            f"Conflict on key '{key}' between files: "
                            + ", ".join(conflict_map[key].keys()) + f" and {name}"
                        )
                    conflict_map[key][name] = value
                    if strategy == "last":
                        merged[key] = value
                else:
                    conflict_map[key][name] = value

    conflicts = [
        MergeConflict(key=k, values=v)
        for k, v in conflict_map.items()
        if len(set(v.values())) > 1
    ]

    return MergeResult(merged=merged, conflicts=conflicts, sources=sources)
