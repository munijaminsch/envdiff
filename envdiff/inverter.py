"""Inverts an env mapping: swaps keys and values, detecting collisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class InvertError(Exception):
    """Raised when inversion cannot be completed."""


@dataclass
class InvertedKey:
    original_key: str
    original_value: str
    new_key: str
    new_value: str

    def as_dict(self) -> dict:
        return {
            "original_key": self.original_key,
            "original_value": self.original_value,
            "new_key": self.new_key,
            "new_value": self.new_value,
        }


@dataclass
class InvertResult:
    source: str
    entries: List[InvertedKey] = field(default_factory=list)
    collisions: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def is_clean(self) -> bool:
        return len(self.collisions) == 0

    @property
    def collision_count(self) -> int:
        return len(self.collisions)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "is_clean": self.is_clean,
            "collision_count": self.collision_count,
            "collisions": {k: v for k, v in self.collisions.items()},
            "entries": [e.as_dict() for e in self.entries],
        }


def invert_env(
    env: Dict[str, str],
    source: str = "",
) -> InvertResult:
    """Swap keys and values in *env*.

    When multiple original keys share the same value, a collision is recorded
    and the *last* key wins in the resulting entries list.
    """
    if env is None:
        raise InvertError("env must not be None")

    # value -> [original_keys] for collision detection
    value_map: Dict[str, List[str]] = {}
    for k, v in env.items():
        value_map.setdefault(v, []).append(k)

    collisions = {v: keys for v, keys in value_map.items() if len(keys) > 1}

    entries: List[InvertedKey] = []
    seen: Dict[str, InvertedKey] = {}
    for original_key, original_value in env.items():
        entry = InvertedKey(
            original_key=original_key,
            original_value=original_value,
            new_key=original_value,
            new_value=original_key,
        )
        seen[original_value] = entry

    entries = list(seen.values())
    return InvertResult(source=source, entries=entries, collisions=collisions)
